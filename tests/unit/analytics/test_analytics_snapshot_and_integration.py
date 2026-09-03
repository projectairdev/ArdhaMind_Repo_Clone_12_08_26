from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import inspect
import time
import pytest

from src.analytics.breadth.models import ConstituentState
from src.analytics.market_analytics_engine import MarketAnalyticsEngine
from src.analytics.options.models import OptionsConfirmationBias
from src.analytics.price_structure.models import TrendDirection
from src.analytics.regime.models import MarketRegime
from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.market_data.bus.events import MarketEvent, MarketEventType
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_option_chain import (
    CanonicalOptionChainSnapshot,
    CanonicalOptionLeg,
    CanonicalOptionStrike,
)
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import (
    CandleQuality,
    DataQualityStatus,
    OptionType,
    Timeframe,
)
from src.market_data.providers.dhan.dhan_instrument_mapper import DhanInstrumentMapper
from src.market_data.services.candle_engine import CanonicalCandleEngine
from src.market_data.services.instrument_master_service import InstrumentMasterService
from src.market_data.session.session_authority import CanonicalSessionAuthority
from src.market_data.state.live_market_state import LiveMarketState


def _make_populated_stack():
    master = InstrumentMasterService()
    mapper = DhanInstrumentMapper(master)
    mapper.register_default_universe()

    state_store = LiveMarketState(master)
    candle_engine = CanonicalCandleEngine()
    session_authority = CanonicalSessionAuthority()

    t_now = datetime(2026, 8, 28, 10, 0, 0, tzinfo=timezone.utc)
    tick_nifty = CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        session_date=date(2026, 8, 28),
        exchange_timestamp=t_now,
        received_at=t_now,
        last_price=24550.0,
        open=24500.0,
        high=24580.0,
        low=24480.0,
        previous_close=24450.0,
    )
    tick_vix = CanonicalTick(
        canonical_instrument_id="IDX:NSE:INDIA_VIX",
        provider="DHAN",
        session_date=date(2026, 8, 28),
        exchange_timestamp=t_now,
        received_at=t_now,
        last_price=13.20,
    )
    state_store.apply_tick_event(MarketEvent(event_id="e1", event_type=MarketEventType.TICK, created_at=t_now, sequence=1, payload=tick_nifty))
    state_store.apply_tick_event(MarketEvent(event_id="e2", event_type=MarketEventType.TICK, created_at=t_now, sequence=2, payload=tick_vix))

    # Add candles
    for i in range(30):
        st = t_now - timedelta(minutes=30 - i)
        candle_engine.apply_tick(
            CanonicalTick(
                canonical_instrument_id="IDX:NSE:NIFTY_50",
                provider="DHAN",
                session_date=date(2026, 8, 28),
                exchange_timestamp=st,
                received_at=st,
                last_price=24500.0 + i * 1.5,
            )
        )

    return state_store, candle_engine, session_authority


def test_1_full_market_analytics_snapshot_generation():
    state_store, candle_engine, session_auth = _make_populated_stack()
    engine = MarketAnalyticsEngine(state_store, candle_engine, session_auth)

    # Make simulated option chain
    strikes = [
        CanonicalOptionStrike(
            strike=24500.0,
            call=CanonicalOptionLeg("OPT:NFO:NIFTY:2026-09-03:24500:CE", 24500.0, OptionType.CE, 120.0, oi=80000, volume=20000),
            put=CanonicalOptionLeg("OPT:NFO:NIFTY:2026-09-03:24500:PE", 24500.0, OptionType.PE, 65.0, oi=95000, volume=25000),
        )
    ]
    opt_snapshot = CanonicalOptionChainSnapshot(
        underlying_instrument_id="IDX:NSE:NIFTY_50",
        underlying_price=24550.0,
        expiry="2026-09-03",
        session_date=date(2026, 8, 28),
        captured_at=datetime.now(timezone.utc),
        provider="DHAN",
        strikes=strikes,
    )

    constituents = [
        ConstituentState("HDFCBANK", 1650.0, 1.2),
        ConstituentState("RELIANCE", 2950.0, 1.5),
        ConstituentState("ICICIBANK", 1250.0, 0.8),
    ]

    snapshot = engine.generate_snapshot(
        option_snapshot=opt_snapshot,
        constituents=constituents,
    )

    assert isinstance(snapshot, MarketAnalyticsSnapshot)
    assert snapshot.price_structure.last_price == 24550.0
    assert snapshot.vix_price == 13.20
    assert snapshot.market_regime.regime in (MarketRegime.TREND_UP, MarketRegime.RANGE, MarketRegime.COMPRESSION, MarketRegime.BREAKOUT_ATTEMPT, MarketRegime.CONFLICTED)
    assert snapshot.options_intelligence.atm_strike == 24500.0
    assert snapshot.quality in (DataQualityStatus.VALID, DataQualityStatus.DELAYED)


def test_2_quality_propagation_on_missing_live_state():
    empty_state = LiveMarketState()
    empty_candles = CanonicalCandleEngine()
    engine = MarketAnalyticsEngine(empty_state, empty_candles)

    snap = engine.generate_snapshot()
    assert snap.quality == DataQualityStatus.UNAVAILABLE
    assert snap.price_structure.quality == DataQualityStatus.UNAVAILABLE
    assert snap.market_regime.regime == MarketRegime.INSUFFICIENT_DATA


def test_3_performance_benchmark_1000_analytics_evaluations():
    state_store, candle_engine, session_auth = _make_populated_stack()
    engine = MarketAnalyticsEngine(state_store, candle_engine, session_auth)

    t0 = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        _ = engine.generate_snapshot()
    elapsed_s = time.perf_counter() - t0
    ops_per_sec = iterations / elapsed_s

    print(f"\n[ANALYTICS BENCHMARK] Computed {iterations} full analytics snapshots in {elapsed_s*1000:.2f} ms ({ops_per_sec:.0f} snapshots/sec)")
    assert ops_per_sec >= 1000.0


def test_4_architectural_import_inspection():
    import src.analytics.market_analytics_engine as mae_mod
    import src.analytics.price_structure.price_structure_engine as pse_mod
    import src.analytics.breadth.breadth_engine as be_mod
    import src.analytics.options.options_intelligence_engine as oie_mod
    import src.analytics.regime.market_regime_engine as mre_mod

    for mod in (mae_mod, pse_mod, be_mod, oie_mod, mre_mod):
        source = inspect.getsource(mod)
        forbidden = ["kiteconnect", "src.broker", "src.frontend", "src.controlled_execution"]
        for f in forbidden:
            assert f"import {f}" not in source
            assert f"from {f}" not in source
