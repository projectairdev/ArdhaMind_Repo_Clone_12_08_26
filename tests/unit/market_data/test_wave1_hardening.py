from __future__ import annotations

from datetime import date, datetime, time as dtime, timedelta, timezone
import pytest

from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import Timeframe
from src.market_data.services.candle_engine import CanonicalCandleEngine
from src.market_data.services.feed_health_engine import FeedHealthEngine, FeedHealthStatus


def _make_tick(
    canonical_id: str = "IDX:NSE:NIFTY_50",
    price: float = 24500.0,
    ts: Optional[datetime] = None,
    volume: Optional[int] = None,
    session_date: date = date(2026, 8, 28),
) -> CanonicalTick:
    t_ex = ts or datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    return CanonicalTick(
        canonical_instrument_id=canonical_id,
        provider="DHAN",
        exchange_timestamp=t_ex,
        received_at=t_ex,
        session_date=session_date,
        last_price=price,
        volume=volume,
    )


# ----------------------------------------------------
# 0A. CANDLE VOLUME SEMANTICS
# ----------------------------------------------------

def test_0a_index_missing_volume_is_not_fabricated():
    engine = CanonicalCandleEngine()
    t = datetime(2026, 8, 28, 9, 15, 10, tzinfo=timezone.utc)

    # NIFTY Index tick without volume
    engine.on_tick(_make_tick(canonical_id="IDX:NSE:NIFTY_50", price=24500.0, ts=t, volume=None))

    live = engine.get_live_candle("IDX:NSE:NIFTY_50", Timeframe.M1)
    assert live is not None
    assert live.volume is None  # Missing remains None, not 0


def test_0a_cumulative_volume_normalized_to_incremental_candle_volume():
    engine = CanonicalCandleEngine()
    t_base = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)

    # Ingest option ticks with cumulative session volume: 1000 -> 1050 -> 1120
    engine.on_tick(_make_tick(canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:CE", price=120.0, ts=t_base + timedelta(seconds=5), volume=1000))
    engine.on_tick(_make_tick(canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:CE", price=122.0, ts=t_base + timedelta(seconds=30), volume=1050))
    engine.on_tick(_make_tick(canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:CE", price=121.0, ts=t_base + timedelta(seconds=55), volume=1120))

    # Next minute tick finalizes 9:15 candle (cumulative 1120 - start 1000 = 120 volume in this 1m candle)
    engine.on_tick(_make_tick(canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:CE", price=123.0, ts=t_base + timedelta(minutes=1, seconds=5), volume=1150))

    closed = engine.get_candles("OPT:NFO:NIFTY:2026-09-03:24500:CE", Timeframe.M1)
    assert len(closed) == 1
    assert closed[0].volume == 120


# ----------------------------------------------------
# 0B. SESSION-ANCHORED HIGHER TIMEFRAMES
# ----------------------------------------------------

def test_0b_session_anchored_60m_boundaries():
    # NSE session anchor: 09:15
    engine = CanonicalCandleEngine(session_anchor_time=dtime(9, 15))
    t_base = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)

    # Ingest ticks across the hour (9:15 to 10:14)
    for m in range(60):
        t_m = t_base + timedelta(minutes=m)
        engine.on_tick(_make_tick(price=24500.0 + m, ts=t_m + timedelta(seconds=10)))

    # Tick at 10:15 closes the 60m candle [9:15, 10:15)
    engine.on_tick(_make_tick(price=24600.0, ts=t_base + timedelta(hours=1, seconds=2)))

    candles_60m = engine.get_candles("IDX:NSE:NIFTY_50", Timeframe.M60)
    assert len(candles_60m) == 1
    assert candles_60m[0].start_timestamp == datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    assert candles_60m[0].end_timestamp == datetime(2026, 8, 28, 10, 15, 0, tzinfo=timezone.utc)
    assert candles_60m[0].open == 24500.0


# ----------------------------------------------------
# 0C. RECOVERING -> HEALTHY CONFIRMATION
# ----------------------------------------------------

def test_0c_stale_to_recovering_to_healthy_confirmation():
    # Require 3 sustained fresh ticks for recovery
    engine = FeedHealthEngine(
        healthy_threshold_seconds=2.0,
        delayed_threshold_seconds=5.0,
        recovery_confirmation_ticks=3,
    )
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    engine.on_tick(_make_tick(ts=t1))

    # Force stale (> 5s)
    t_stale = t1 + timedelta(seconds=8.0)
    rep_stale = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=t_stale)
    assert rep_stale.status == FeedHealthStatus.STALE

    # 1. First fresh tick -> Transitions to RECOVERING
    t2 = t1 + timedelta(seconds=9.0)
    engine.on_tick(_make_tick(ts=t2))
    rep1 = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=t2 + timedelta(milliseconds=100))
    assert rep1.status == FeedHealthStatus.RECOVERING

    # 2. Second fresh tick -> Remains RECOVERING
    t3 = t2 + timedelta(seconds=0.5)
    engine.on_tick(_make_tick(ts=t3))
    rep2 = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=t3 + timedelta(milliseconds=100))
    assert rep2.status == FeedHealthStatus.RECOVERING

    # 3. Third fresh tick -> Confirms HEALTHY
    t4 = t3 + timedelta(seconds=0.5)
    engine.on_tick(_make_tick(ts=t4))
    rep3 = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=t4 + timedelta(milliseconds=100))
    assert rep3.status == FeedHealthStatus.HEALTHY
    assert rep3.recovery_count == 1


def test_0c_recovering_feed_freezes_again_transitions_to_stale():
    engine = FeedHealthEngine(
        healthy_threshold_seconds=2.0,
        delayed_threshold_seconds=5.0,
        recovery_confirmation_ticks=3,
    )
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    engine.on_tick(_make_tick(ts=t1))

    # Stale
    t_stale = t1 + timedelta(seconds=8.0)
    engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=t_stale)

    # 1 fresh tick -> RECOVERING
    t2 = t1 + timedelta(seconds=9.0)
    engine.on_tick(_make_tick(ts=t2))
    assert engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=t2 + timedelta(milliseconds=100)).status == FeedHealthStatus.RECOVERING

    # Feed freezes again (> 5s without more ticks)
    t_freeze = t2 + timedelta(seconds=6.0)
    rep_re_stale = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=t_freeze)
    assert rep_re_stale.status == FeedHealthStatus.STALE
