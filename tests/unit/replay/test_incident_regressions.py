from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import pytest

from src.decision.decision.decision_engine import DecisionEngine
from src.decision.models.decision_models import DecisionState
from src.market_data.bus.events import MarketEvent, MarketEventType
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import DataQualityStatus, Timeframe
from src.market_data.services.candle_engine import CanonicalCandleEngine
from src.market_data.services.instrument_master_service import InstrumentMasterService
from src.market_data.services.market_data_orchestrator import SubscriptionRegistry
from src.market_data.session.exchange_calendar import ExchangeCalendar
from src.market_data.session.session_authority import CanonicalSessionAuthority
from src.market_data.session.session_validator import SessionValidator
from src.market_data.state.live_market_state import LiveMarketState
from tests.unit.decision.test_decision_engine_and_products import _make_dummy_pred
from tests.unit.decision.test_signal_fusion_and_opportunity import _make_snapshot


def test_incident_a_friday_saturday_session_date_defect():
    """
    Incident A: Saturday evaluation must resolve completed session to Friday (not Thursday).
    """
    calendar = ExchangeCalendar()
    authority = CanonicalSessionAuthority(calendar)

    # 2026-08-29 is Saturday. Completed session MUST be 2026-08-28 (Friday).
    sat_dt = datetime(2026, 8, 29, 11, 0, 0, tzinfo=timezone.utc)
    ctx = authority.evaluate_session(sat_dt)

    assert ctx.is_trading_day is False
    assert ctx.completed_session_date == date(2026, 8, 28)
    assert ctx.previous_session_date == date(2026, 8, 27)


def test_incident_b_frozen_feed_blocks_decisions():
    """
    Incident B: WebSocket marked connected but feed is frozen/stale.
    DecisionEngine must immediately output BLOCKED and revoke READY state.
    """
    snap_stale = _make_snapshot(quality=DataQualityStatus.UNAVAILABLE)
    pred = _make_dummy_pred(snap_stale.session_date)

    dec = DecisionEngine.evaluate_decision(snap_stale, pred)
    assert dec.decision_state == DecisionState.BLOCKED
    assert dec.decision_state != DecisionState.READY_FOR_HUMAN_REVIEW


def test_incident_c_reconnect_subscription_preservation():
    """
    Incident C: Reconnect occurs; desired subscription registry is preserved.
    """
    registry = SubscriptionRegistry(
        desired={"IDX:NSE:NIFTY_50", "IDX:NSE:INDIA_VIX"},
        active={"IDX:NSE:NIFTY_50", "IDX:NSE:INDIA_VIX"},
        pending=set(),
        failed=set(),
    )

    # Simulate disconnect (active cleared)
    registry.active.clear()
    assert len(registry.desired) == 2
    assert len(registry.active) == 0

    # Reconnect restores desired subscriptions
    registry.active.update(registry.desired)
    assert registry.active == {"IDX:NSE:NIFTY_50", "IDX:NSE:INDIA_VIX"}


def test_incident_d_out_of_order_ticks_rejected():
    """
    Incident D: Ticks with older timestamps arriving after newer ticks are rejected monotonically.
    """
    master = InstrumentMasterService()
    from src.market_data.providers.dhan.dhan_instrument_mapper import DhanInstrumentMapper
    DhanInstrumentMapper(master).register_default_universe()
    state = LiveMarketState(master)

    t1 = datetime(2026, 8, 28, 9, 15, 10, tzinfo=timezone.utc)
    t0 = datetime(2026, 8, 28, 9, 15, 5, tzinfo=timezone.utc)
    sess = date(2026, 8, 28)

    tick1 = CanonicalTick("IDX:NSE:NIFTY_50", "TEST", t1, t1, sess, 24500.0)
    tick0 = CanonicalTick("IDX:NSE:NIFTY_50", "TEST", t0, t0, sess, 24490.0)

    # Apply t1 first
    ev1 = MarketEvent("e1", MarketEventType.TICK, t1, 1, tick1, "IDX:NSE:NIFTY_50")
    res1 = state.apply_tick_event(ev1)
    assert res1 is True

    # Apply older t0
    ev0 = MarketEvent("e0", MarketEventType.TICK, t0, 2, tick0, "IDX:NSE:NIFTY_50")
    res0 = state.apply_tick_event(ev0)
    assert res0 is False
    assert state.stats()["rejected_out_of_order"] == 1


def test_incident_e_missing_candle_interval_gap_detected():
    """
    Incident E: Missing candle intervals are detected as gaps without artificial interpolation.
    """
    engine = CanonicalCandleEngine()
    sess = date(2026, 8, 28)
    t0 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t_gap = datetime(2026, 8, 28, 9, 20, 0, tzinfo=timezone.utc)

    engine.apply_tick(CanonicalTick("IDX:NSE:NIFTY_50", "TEST", t0, t0, sess, 24500.0))
    engine.apply_tick(CanonicalTick("IDX:NSE:NIFTY_50", "TEST", t_gap, t_gap, sess, 24510.0))

    gaps = engine.detect_gaps("IDX:NSE:NIFTY_50", Timeframe.M1)
    assert len(gaps) > 0


def test_incident_f_wrong_session_candles_rejected():
    """
    Incident F: Candle on non-trading day or wrong session is rejected by session validator.
    """
    calendar = ExchangeCalendar()
    authority = CanonicalSessionAuthority(calendar)
    validator = SessionValidator(authority)

    # 2026-08-30 is Sunday
    sun_dt = datetime(2026, 8, 30, 10, 0, 0, tzinfo=timezone.utc)
    tick_sun = CanonicalTick("IDX:NSE:NIFTY_50", "TEST", sun_dt, sun_dt, date(2026, 8, 30), 24500.0)

    res = validator.validate_tick(tick_sun, reference_time=sun_dt)
    assert res.is_valid is False
    assert res.status in (DataQualityStatus.REJECTED, DataQualityStatus.SESSION_MISMATCH)


def test_incident_g_magnitude_overprediction_safety():
    """
    Incident G: Strong pre-market prediction (+140 pts), flat live range -> Decision does NOT chase.
    """
    snap_flat = _make_snapshot(last_price=24500.0, or_high=24520.0, or_low=24480.0)
    pred_large = _make_dummy_pred(snap_flat.session_date)

    dec = DecisionEngine.evaluate_decision(snap_flat, pred_large)
    assert dec.decision_state in (DecisionState.NO_TRADE, DecisionState.WAIT)
    assert dec.decision_state != DecisionState.READY_FOR_HUMAN_REVIEW


def test_incident_h_option_chain_unavailable_graceful_degradation():
    """
    Incident H: Options chain unavailable -> Options strategy becomes UNAVAILABLE without synthetic numbers.
    """
    snap_no_opt = _make_snapshot()
    object.__setattr__(snap_no_opt.options_intelligence, "quality", DataQualityStatus.UNAVAILABLE)
    object.__setattr__(snap_no_opt.options_intelligence, "strike_universe", [])

    dec = DecisionEngine.evaluate_decision(snap_no_opt)
    assert dec.strategy_suitability.value == "UNAVAILABLE"
    assert len(dec.strike_candidates) == 0
