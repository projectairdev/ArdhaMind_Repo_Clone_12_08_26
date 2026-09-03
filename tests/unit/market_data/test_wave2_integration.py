from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import time
from typing import Sequence
import pytest

from src.market_data.bus.events import MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.interfaces.historical_data_provider import IHistoricalDataProvider
from src.market_data.interfaces.market_data_provider import IMarketDataProvider
from src.market_data.interfaces.option_chain_provider import IOptionChainProvider
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_option_chain import (
    CanonicalOptionChainSnapshot,
    CanonicalOptionLeg,
    CanonicalOptionStrike,
)
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import (
    CandleQuality,
    DataQualityStatus,
    Exchange,
    InstrumentType,
    OptionType,
    Segment,
    Timeframe,
)
from src.market_data.providers.dhan.dhan_historical_provider import DhanHistoricalProvider
from src.market_data.providers.dhan.dhan_instrument_mapper import DhanInstrumentMapper
from src.market_data.providers.dhan.dhan_market_data_provider import DhanMarketDataProvider
from src.market_data.providers.dhan.dhan_option_chain_provider import DhanOptionChainProvider
from src.market_data.services.candle_engine import CanonicalCandleEngine
from src.market_data.services.feed_health_engine import FeedHealthEngine, FeedHealthStatus
from src.market_data.services.historical_bootstrap_service import HistoricalBootstrapService
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


class SimulatedDhanTransport(IMarketDataProvider):
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

    def set_tick_handler(self, handler) -> None:
        self.tick_handler = handler

    def subscribe(self, instruments: Sequence[CanonicalInstrument]) -> None:
        self.subscribed.extend(instruments)

    def unsubscribe(self, instruments: Sequence[CanonicalInstrument]) -> None:
        self.subscribed = [i for i in self.subscribed if i not in instruments]

    def provider_name(self) -> str:
        return "DHAN"


class SimulatedDhanHistorical(IHistoricalDataProvider):
    def fetch_candles(
        self,
        instrument: CanonicalInstrument,
        timeframe: Timeframe | str,
        start: datetime,
        end: datetime,
    ) -> Sequence[CanonicalCandle]:
        return [
            CanonicalCandle(
                canonical_instrument_id=instrument.canonical_id,
                provider="DHAN",
                session_date=start.date(),
                timeframe=timeframe,
                start_timestamp=start,
                end_timestamp=end,
                open=24500.0,
                high=24525.0,
                low=24495.0,
                close=24515.0,
                volume=1500,
                quality=CandleQuality.VALID,
            )
        ]

    def provider_name(self) -> str:
        return "DHAN"


def test_wave2_full_dhan_lifecycle_recovery_and_reconciliation():
    """
    End-to-end simulation proving:
    1. Master Sync & Instrument Registration
    2. Realtime Provider Streaming (NIFTY, VIX, Options)
    3. Option Chain Snapshot
    4. Feed Stale Detection -> Automatic Recovery
    5. Reconnect & Desired Subscription Restoration
    6. REST Reconciliation
    7. Missing Candle Gap Detection & Backfill (quality=BACKFILLED)
    8. Sustained tick flow recovery to HEALTHY
    """
    # 1. Instrument Master
    master = InstrumentMasterService()
    mapper = DhanInstrumentMapper(master)
    nifty, vix = mapper.register_default_universe()

    opt_ce = mapper.map_and_register({
        "security_id": "45001",
        "exchange_segment": "NFO_OPT",
        "symbol": "NIFTY",
        "instrument_type": "OPTIDX",
        "expiry_date": "2026-09-03",
        "strike_price": 24500.0,
        "option_type": "CE",
    })

    # 2. Providers
    transport = SimulatedDhanTransport()
    historical = SimulatedDhanHistorical()
    option_provider = DhanOptionChainProvider(
        transport_fetcher=lambda p: {
            "data": {
                "last_price": 24500.0,
                "oc": {
                    "24500.0": {
                        "ce": {"last_price": 120.0, "oi": 5000, "volume": 2000, "delta": 0.5},
                        "pe": {"last_price": 80.0, "oi": 6000, "volume": 1500, "delta": -0.5},
                    }
                }
            }
        }
    )

    # 3. Stack components
    bus = MarketEventBus(queue_capacity=50_000)
    state_store = LiveMarketState(master)
    health_engine = FeedHealthEngine(
        healthy_threshold_seconds=1.0,
        delayed_threshold_seconds=2.0,
        recovery_confirmation_ticks=2,
    )
    candle_engine = CanonicalCandleEngine()
    reconciliation = ReconciliationService(state_store)

    orchestrator = MarketDataOrchestrator(
        market_data_provider=transport,
        historical_provider=historical,
        option_chain_provider=option_provider,
        instrument_master=master,
        event_bus=bus,
        live_market_state=state_store,
        feed_health_engine=health_engine,
        candle_engine=candle_engine,
        reconciliation_service=reconciliation,
        backoff_steps=[0.01, 0.02],
    )

    # 4. Startup
    instruments = [nifty, vix, opt_ce]
    started = orchestrator.start(instruments)
    assert started is True
    assert orchestrator.lifecycle_state == OrchestratorLifecycleState.RUNNING

    # 5. Normal tick streaming (9:15:00)
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    tick_nifty = CanonicalTick(
        canonical_instrument_id=nifty.canonical_id,
        provider="DHAN",
        exchange_timestamp=t1,
        received_at=t1,
        session_date=date(2026, 8, 28),
        last_price=24500.0,
    )
    tick_vix = CanonicalTick(
        canonical_instrument_id=vix.canonical_id,
        provider="DHAN",
        exchange_timestamp=t1,
        received_at=t1,
        session_date=date(2026, 8, 28),
        last_price=12.5,
    )
    tick_opt = CanonicalTick(
        canonical_instrument_id=opt_ce.canonical_id,
        provider="DHAN",
        exchange_timestamp=t1,
        received_at=t1,
        session_date=date(2026, 8, 28),
        last_price=120.0,
        volume=1000,
    )

    bus.publish(MarketEventType.TICK, tick_nifty)
    bus.publish(MarketEventType.TICK, tick_vix)
    bus.publish(MarketEventType.TICK, tick_opt)
    time.sleep(0.05)

    assert state_store.get_nifty().last_price == 24500.0
    assert state_store.get_vix().last_price == 12.5

    # 6. Option Chain Snapshot
    chain_snapshot = option_provider.fetch_option_chain(nifty, "2026-09-03")
    assert chain_snapshot.underlying_price == 24500.0
    assert len(chain_snapshot.strikes) == 1

    # 7. Simulate Stream Freeze (t1 + 5s) -> Evaluates STALE
    t_stale = t1 + timedelta(seconds=5)
    stale_report = health_engine.evaluate_health(nifty.canonical_id, current_time=t_stale)
    assert stale_report.status == FeedHealthStatus.STALE
    time.sleep(0.05)

    # 8. Trigger Automated Recovery
    orchestrator.trigger_recovery()
    assert orchestrator.lifecycle_state == OrchestratorLifecycleState.RUNNING
    assert nifty.canonical_id in orchestrator.subscriptions.active

    # 9. REST Reconciliation after reconnect
    t_recon = t1 + timedelta(minutes=3)
    rest_tick = CanonicalTick(
        canonical_instrument_id=nifty.canonical_id,
        provider="DHAN",
        exchange_timestamp=t_recon,
        received_at=t_recon,
        session_date=date(2026, 8, 28),
        last_price=24520.0,
    )
    recon_rep = reconciliation.reconcile_instrument(rest_tick)
    assert recon_rep.status == ReconciliationStatus.REST_NEWER
    assert recon_rep.applied_to_state is True

    # 10. Gap Backfill in CandleEngine: next tick arrives at 9:18 (leaves gap [9:16, 9:18))
    t_gap = datetime(2026, 8, 28, 9, 18, 5, tzinfo=timezone.utc)
    tick_after_gap = CanonicalTick(
        canonical_instrument_id=nifty.canonical_id,
        provider="DHAN",
        exchange_timestamp=t_gap,
        received_at=t_gap,
        session_date=date(2026, 8, 28),
        last_price=24530.0,
    )
    bus.publish(MarketEventType.TICK, tick_after_gap)
    time.sleep(0.05)

    backfilled_count = orchestrator.backfill_detected_gaps()
    assert backfilled_count == 1

    # 11. Sustained fresh ticks confirm HEALTHY (recovery_confirmation_ticks=2)
    t_healthy1 = t_gap + timedelta(seconds=1)
    t_healthy2 = t_gap + timedelta(seconds=2)
    bus.publish(MarketEventType.TICK, CanonicalTick(canonical_instrument_id=nifty.canonical_id, provider="DHAN", exchange_timestamp=t_healthy1, received_at=t_healthy1, session_date=date(2026, 8, 28), last_price=24532.0))
    bus.publish(MarketEventType.TICK, CanonicalTick(canonical_instrument_id=nifty.canonical_id, provider="DHAN", exchange_timestamp=t_healthy2, received_at=t_healthy2, session_date=date(2026, 8, 28), last_price=24535.0))
    time.sleep(0.05)

    final_health = health_engine.evaluate_health(nifty.canonical_id, current_time=t_healthy2 + timedelta(milliseconds=100))
    assert final_health.status == FeedHealthStatus.HEALTHY

    # 12. Diagnostics validation
    diag = orchestrator.get_diagnostics()
    assert diag["provider"] == "DHAN"
    assert diag["subscriptions"]["active_count"] == 3
    assert diag["total_reconnects"] >= 1
    assert diag["total_backfills"] >= 1

    orchestrator.stop()
