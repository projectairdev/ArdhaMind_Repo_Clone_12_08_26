from __future__ import annotations

from datetime import date, datetime, timezone
import inspect
import time
from typing import Sequence
import pytest

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
    Exchange,
    InstrumentType,
    OptionType,
    Segment,
    Timeframe,
)
from src.market_data.runtime.canonical_runtime import CanonicalBackendRuntime
from src.market_data.runtime.cutover_gates import CutoverGateEvaluator, CutoverReadinessReport
from src.market_data.services.option_chain_aggregator import OptionChainAggregator, OptionChainSummary
from src.market_data.services.shadow_comparison_service import (
    ShadowComparisonReport,
    ShadowComparisonService,
    ShadowComparisonStatus,
)


class MockShadowMarketData(IMarketDataProvider):
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
        return "MOCK_SHADOW"


class MockShadowHistorical(IHistoricalDataProvider):
    def fetch_candles(
        self,
        instrument: CanonicalInstrument,
        timeframe: Timeframe | str,
        start: datetime,
        end: datetime,
    ) -> Sequence[CanonicalCandle]:
        return []

    def provider_name(self) -> str:
        return "MOCK_SHADOW"


class MockShadowOptions(IOptionChainProvider):
    def get_available_expiries(self, underlying: CanonicalInstrument) -> Sequence[str]:
        return ["2026-09-03"]

    def fetch_option_chain(self, underlying: CanonicalInstrument, expiry: str) -> CanonicalOptionChainSnapshot:
        return CanonicalOptionChainSnapshot(
            underlying_instrument_id=underlying.canonical_id,
            underlying_price=24500.0,
            expiry=expiry,
            session_date=date.today(),
            captured_at=datetime.now(timezone.utc),
            provider="MOCK_SHADOW",
            strikes=[
                CanonicalOptionStrike(
                    strike=24400.0,
                    call=CanonicalOptionLeg("OPT:NFO:NIFTY:2026-09-03:24400:CE", 24400.0, OptionType.CE, 180.0, oi=40000, volume=10000),
                    put=CanonicalOptionLeg("OPT:NFO:NIFTY:2026-09-03:24400:PE", 24400.0, OptionType.PE, 40.0, oi=120000, volume=35000),
                ),
                CanonicalOptionStrike(
                    strike=24500.0,
                    call=CanonicalOptionLeg("OPT:NFO:NIFTY:2026-09-03:24500:CE", 24500.0, OptionType.CE, 120.0, oi=80000, volume=25000),
                    put=CanonicalOptionLeg("OPT:NFO:NIFTY:2026-09-03:24500:PE", 24500.0, OptionType.PE, 65.0, oi=95000, volume=30000),
                ),
                CanonicalOptionStrike(
                    strike=24600.0,
                    call=CanonicalOptionLeg("OPT:NFO:NIFTY:2026-09-03:24600:CE", 24600.0, OptionType.CE, 70.0, oi=150000, volume=45000),
                    put=CanonicalOptionLeg("OPT:NFO:NIFTY:2026-09-03:24600:PE", 24600.0, OptionType.PE, 110.0, oi=30000, volume=8000),
                ),
            ],
        )

    def provider_name(self) -> str:
        return "MOCK_SHADOW"


def test_1_canonical_runtime_lifecycle_and_shadow_export():
    transport = MockShadowMarketData()
    historical = MockShadowHistorical()
    options = MockShadowOptions()

    runtime = CanonicalBackendRuntime(
        market_data_provider=transport,
        historical_provider=historical,
        option_chain_provider=options,
    )

    started = runtime.start()
    assert started is True
    assert runtime.is_running is True

    # 1. Export canonical market state
    mkt_state = runtime.export_canonical_market_state()
    assert mkt_state["source"] == "CANONICAL_SHADOW"
    assert "session" in mkt_state
    assert "nifty" in mkt_state
    assert "vix" in mkt_state

    # 2. Export feed health
    health = runtime.export_canonical_feed_health()
    assert health["source"] == "CANONICAL_SHADOW"
    assert "nifty_feed" in health

    # 3. Export session
    sess = runtime.export_canonical_session()
    assert "calendar_date" in sess
    assert "market_phase" in sess

    # 4. Export option summary
    opt_summary = runtime.export_canonical_options("2026-09-03")
    assert opt_summary["underlying_price"] == 24500.0
    assert opt_summary["atm_strike"] == 24500.0
    assert opt_summary["max_call_oi_strike"] == 24600.0  # Call Wall
    assert opt_summary["max_put_oi_strike"] == 24400.0   # Put Wall
    assert opt_summary["pcr"] > 0.8

    runtime.stop()
    assert runtime.is_running is False


def test_2_shadow_comparison_semantics():
    service = ShadowComparisonService(price_tolerance_pct=0.05)

    legacy_state = {
        "session_date": "2026-08-28",
        "nifty_price": 24500.0,
        "vix_price": 12.50,
        "previous_close": 24450.0,
        "nifty_open": 24480.0,
        "nifty_high": 24550.0,
        "nifty_low": 24460.0,
    }

    # Case 1: Exact Match
    rep1 = service.compare_states(legacy_state, legacy_state)
    assert rep1.overall_status == ShadowComparisonStatus.MATCH

    # Case 2: Within tolerance (0.01% diff)
    tolerated_state = dict(legacy_state)
    tolerated_state["nifty_price"] = 24502.0  # ~0.008% diff
    rep2 = service.compare_states(legacy_state, tolerated_state)
    assert rep2.overall_status == ShadowComparisonStatus.WITHIN_TOLERANCE

    # Case 3: Diverged price (>0.05% diff)
    diverged_state = dict(legacy_state)
    diverged_state["nifty_price"] = 24600.0  # ~0.4% diff
    rep3 = service.compare_states(legacy_state, diverged_state)
    assert rep3.overall_status == ShadowComparisonStatus.DIVERGED

    # Case 4: Session mismatch
    mismatch_state = dict(legacy_state)
    mismatch_state["session_date"] = "2026-08-27"
    rep4 = service.compare_states(legacy_state, mismatch_state)
    assert rep4.overall_status == ShadowComparisonStatus.SESSION_MISMATCH


def test_3_cutover_gates_readiness_evaluation():
    evaluator = CutoverGateEvaluator()

    # Case 1: Failing state (missing live ticks, disconnected)
    failing_inputs = {
        "dhan_auth_verified": False,
        "websocket_connected": False,
        "desired_subscriptions_count": 2,
        "active_subscriptions_count": 0,
        "nifty_ticks_observed_count": 0,
        "feed_health_status": "STALE",
    }
    rep_failing = evaluator.evaluate_gates(failing_inputs)
    assert rep_failing.is_ready is False
    assert len(rep_failing.failing_gates) > 0
    assert "1_dhan_auth_verified" in rep_failing.failing_gates
    assert "4_real_nifty_ticks_observed" in rep_failing.failing_gates

    # Case 2: All 13 gates passing
    all_passing_inputs = {
        "dhan_auth_verified": True,
        "websocket_connected": True,
        "desired_subscriptions_count": 3,
        "active_subscriptions_count": 3,
        "nifty_ticks_observed_count": 500,
        "feed_health_status": "HEALTHY",
        "session_authority_valid": True,
        "has_session_mismatch": False,
        "candles_count": 120,
        "reconciliation_functioning": True,
        "historical_bootstrap_functioning": True,
        "option_chain_functioning": True,
        "shadow_comparison_status": "MATCH",
        "fabricated_values_count": 0,
    }
    rep_passing = evaluator.evaluate_gates(all_passing_inputs)
    assert rep_passing.is_ready is True
    assert len(rep_passing.failing_gates) == 0


def test_4_architectural_import_inspection():
    import src.market_data.runtime.canonical_runtime as cr_mod
    import src.market_data.services.shadow_comparison_service as scs_mod
    import src.market_data.services.option_chain_aggregator as oca_mod
    import src.market_data.session.session_authority as sa_mod

    for mod in (cr_mod, scs_mod, oca_mod, sa_mod):
        source = inspect.getsource(mod)
        forbidden = ["kiteconnect", "src.broker", "src.frontend", "src.controlled_execution"]
        for f in forbidden:
            assert f"import {f}" not in source
            assert f"from {f}" not in source
