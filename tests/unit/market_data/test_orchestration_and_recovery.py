from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import inspect
import time
from typing import Sequence
import pytest

from src.market_data.bus.events import MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.interfaces.historical_data_provider import IHistoricalDataProvider
from src.market_data.interfaces.market_data_provider import IMarketDataProvider
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import CandleQuality, Exchange, InstrumentType, Segment, Timeframe
from src.market_data.services.candle_engine import CanonicalCandleEngine
from src.market_data.services.feed_health_engine import FeedHealthEngine, FeedHealthStatus
from src.market_data.services.instrument_master_service import InstrumentMasterService
from src.market_data.services.market_data_orchestrator import (
    MarketDataOrchestrator,
    OrchestratorLifecycleState,
)
from src.market_data.services.reconciliation_service import (
    ReconciliationReport,
    ReconciliationService,
    ReconciliationStatus,
)
from src.market_data.state.live_market_state import LiveMarketState


class MockTransportProvider(IMarketDataProvider):
    def __init__(self):
        self._connected = False
        self.subscribed = []
        self.tick_handler = None

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def set_tick_handler(self, handler: Any) -> None:
        self.tick_handler = handler

    def subscribe(self, instruments: Sequence[CanonicalInstrument]) -> None:
        self.subscribed.extend(instruments)

    def unsubscribe(self, instruments: Sequence[CanonicalInstrument]) -> None:
        self.subscribed = [i for i in self.subscribed if i not in instruments]

    def provider_name(self) -> str:
        return "MOCK_TRANSPORT"


class MockHistoricalGapProvider(IHistoricalDataProvider):
    def fetch_candles(
        self,
        instrument: CanonicalInstrument,
        timeframe: Timeframe | str,
        start: datetime,
        end: datetime,
    ) -> Sequence[CanonicalCandle]:
        # Synthesize backfilled candle for the requested gap
        return [
            CanonicalCandle(
                canonical_instrument_id=instrument.canonical_id,
                provider="MOCK_HIST",
                session_date=start.date(),
                timeframe=timeframe,
                start_timestamp=start,
                end_timestamp=end,
                open=24500.0,
                high=24520.0,
                low=24490.0,
                close=24510.0,
                volume=1000,
                quality=CandleQuality.VALID,
            )
        ]

    def provider_name(self) -> str:
        return "MOCK_HIST"


@pytest.fixture
def nifty_instrument():
    return CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )


def test_1_orchestrator_startup_and_subscription_registry(nifty_instrument: CanonicalInstrument):
    mock_md = MockTransportProvider()
    orchestrator = MarketDataOrchestrator(market_data_provider=mock_md)

    assert orchestrator.lifecycle_state == OrchestratorLifecycleState.INITIALIZING

    success = orchestrator.start([nifty_instrument])
    assert success is True
    assert orchestrator.lifecycle_state == OrchestratorLifecycleState.RUNNING

    # Subscriptions registry
    assert nifty_instrument.canonical_id in orchestrator.subscriptions.desired
    assert nifty_instrument.canonical_id in orchestrator.subscriptions.active

    orchestrator.stop()
    assert orchestrator.lifecycle_state == OrchestratorLifecycleState.STOPPED


def test_2_reconnect_and_resubscription_from_desired(nifty_instrument: CanonicalInstrument):
    mock_md = MockTransportProvider()
    master = InstrumentMasterService()
    master.register(nifty_instrument)

    orchestrator = MarketDataOrchestrator(
        market_data_provider=mock_md,
        instrument_master=master,
        backoff_steps=[0.01],  # fast test backoff
    )
    orchestrator.start([nifty_instrument])

    # Simulate disconnect and recovery trigger
    recovered = orchestrator.trigger_recovery()
    assert recovered is True
    assert orchestrator.lifecycle_state == OrchestratorLifecycleState.RUNNING
    assert nifty_instrument.canonical_id in orchestrator.subscriptions.active

    orchestrator.stop()


def test_3_rest_reconciliation_semantics():
    state_store = LiveMarketState()
    recon_service = ReconciliationService(state_store)

    t1 = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=1)

    # Populate WS state: 24500.0 at t1
    ws_tick = CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=t1,
        received_at=t1,
        session_date=date(2026, 8, 28),
        last_price=24500.0,
    )
    from src.market_data.bus.events import MarketEvent
    state_store.apply_tick_event(MarketEvent(event_id="e1", event_type=MarketEventType.TICK, payload=ws_tick, sequence=1, created_at=t1))

    # 1. IN_SYNC case: REST reports same price and timestamp
    rest_in_sync = CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=t1,
        received_at=t1,
        session_date=date(2026, 8, 28),
        last_price=24500.0,
    )
    rep1 = recon_service.reconcile_instrument(rest_in_sync)
    assert rep1.status == ReconciliationStatus.IN_SYNC

    # 2. REST_NEWER case: REST has newer exchange timestamp t2
    rest_newer = CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=t2,
        received_at=t2,
        session_date=date(2026, 8, 28),
        last_price=24520.0,
    )
    rep2 = recon_service.reconcile_instrument(rest_newer)
    assert rep2.status == ReconciliationStatus.REST_NEWER
    assert rep2.applied_to_state is True

    # 3. WS_NEWER case: REST has older exchange timestamp
    rest_older = CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=t1 - timedelta(seconds=5),
        received_at=t1,
        session_date=date(2026, 8, 28),
        last_price=24480.0,
    )
    rep3 = recon_service.reconcile_instrument(rest_older)
    assert rep3.status == ReconciliationStatus.WS_NEWER
    assert rep3.applied_to_state is False


def test_4_gap_detection_and_historical_backfill(nifty_instrument: CanonicalInstrument):
    mock_md = MockTransportProvider()
    mock_hist = MockHistoricalGapProvider()
    master = InstrumentMasterService()
    master.register(nifty_instrument)

    candle_engine = CanonicalCandleEngine()
    orchestrator = MarketDataOrchestrator(
        market_data_provider=mock_md,
        historical_provider=mock_hist,
        instrument_master=master,
        candle_engine=candle_engine,
    )
    orchestrator.start([nifty_instrument])

    # Inject ticks that leave a 2-minute gap (9:15 to 9:18)
    t1 = datetime(2026, 8, 28, 9, 15, 10, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 28, 9, 18, 10, tzinfo=timezone.utc)

    candle_engine.on_tick(CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=t1,
        received_at=t1,
        session_date=date(2026, 8, 28),
        last_price=24500.0,
    ))
    candle_engine.on_tick(CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=t2,
        received_at=t2,
        session_date=date(2026, 8, 28),
        last_price=24550.0,
    ))

    # Gap [9:16, 9:18) detected
    gaps = candle_engine.detect_gaps("IDX:NSE:NIFTY_50", Timeframe.M1)
    assert len(gaps) == 1

    # Execute backfill
    backfilled_count = orchestrator.backfill_detected_gaps()
    assert backfilled_count == 1

    # Verify backfilled candle has quality=BACKFILLED
    candles = candle_engine.get_candles("IDX:NSE:NIFTY_50", Timeframe.M1)
    backfilled_candle = [c for c in candles if c.quality == CandleQuality.BACKFILLED]
    assert len(backfilled_candle) == 1

    orchestrator.stop()


def test_5_broker_independence_and_diagnostics(nifty_instrument: CanonicalInstrument):
    mock_md = MockTransportProvider()
    orchestrator = MarketDataOrchestrator(market_data_provider=mock_md)
    orchestrator.start([nifty_instrument])

    diag = orchestrator.get_diagnostics()
    assert diag["orchestrator_state"] == "RUNNING"
    assert diag["provider"] == "MOCK_TRANSPORT"
    assert diag["subscriptions"]["active_count"] == 1

    orchestrator.stop()


def test_6_architectural_import_inspection():
    import src.market_data.services.market_data_orchestrator as mdo_mod
    import src.market_data.services.reconciliation_service as rs_mod
    for mod in (mdo_mod, rs_mod):
        source = inspect.getsource(mod)
        forbidden = ["kiteconnect", "src.broker", "src.frontend", "src.controlled_execution"]
        for f in forbidden:
            assert f"import {f}" not in source
            assert f"from {f}" not in source
