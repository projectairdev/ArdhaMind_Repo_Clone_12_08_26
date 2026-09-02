from __future__ import annotations

import inspect
import time
from datetime import date, datetime, timedelta, timezone
import pytest

from src.market_data.bus.events import MarketEvent, MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.quality_enums import CandleQuality, Timeframe
from src.market_data.services.candle_engine import CanonicalCandleEngine


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


def test_1_first_tick_creates_live_candle():
    engine = CanonicalCandleEngine()
    t = datetime(2026, 8, 28, 9, 15, 12, tzinfo=timezone.utc)
    engine.on_tick(_make_tick(price=24500.0, ts=t, volume=100))

    live = engine.get_live_candle("IDX:NSE:NIFTY_50", Timeframe.M1)
    assert live is not None
    assert live.open == 24500.0
    assert live.high == 24500.0
    assert live.low == 24500.0
    assert live.close == 24500.0
    assert live.start_timestamp == datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    assert live.end_timestamp == datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)


def test_2_same_minute_updates_ohlc():
    engine = CanonicalCandleEngine()
    t_base = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)

    engine.on_tick(_make_tick(price=24500.0, ts=t_base + timedelta(seconds=5)))
    engine.on_tick(_make_tick(price=24530.0, ts=t_base + timedelta(seconds=15)))
    engine.on_tick(_make_tick(price=24490.0, ts=t_base + timedelta(seconds=30)))
    engine.on_tick(_make_tick(price=24510.0, ts=t_base + timedelta(seconds=45)))

    live = engine.get_live_candle("IDX:NSE:NIFTY_50", Timeframe.M1)
    assert live.open == 24500.0
    assert live.high == 24530.0
    assert live.low == 24490.0
    assert live.close == 24510.0


def test_3_next_minute_finalizes_prior_candle():
    engine = CanonicalCandleEngine()
    t_min1 = datetime(2026, 8, 28, 9, 15, 10, tzinfo=timezone.utc)
    t_min2 = datetime(2026, 8, 28, 9, 16, 5, tzinfo=timezone.utc)

    # 1. Ticks in 9:15
    engine.on_tick(_make_tick(price=24500.0, ts=t_min1))
    engine.on_tick(_make_tick(price=24520.0, ts=t_min1 + timedelta(seconds=20)))

    # No finalized candles yet
    assert len(engine.get_candles("IDX:NSE:NIFTY_50", Timeframe.M1)) == 0

    # 2. Tick in 9:16 finalizes 9:15 candle
    engine.on_tick(_make_tick(price=24525.0, ts=t_min2))

    finalized = engine.get_candles("IDX:NSE:NIFTY_50", Timeframe.M1)
    assert len(finalized) == 1
    assert finalized[0].start_timestamp == datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    assert finalized[0].end_timestamp == datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)
    assert finalized[0].open == 24500.0
    assert finalized[0].close == 24520.0
    assert finalized[0].quality == CandleQuality.VALID

    # New live candle is 9:16
    live = engine.get_live_candle("IDX:NSE:NIFTY_50", Timeframe.M1)
    assert live.start_timestamp == datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)
    assert live.open == 24525.0


def test_4_5m_aggregation():
    engine = CanonicalCandleEngine()
    t_base = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)

    # Ingest 5 complete minutes of ticks (9:15 to 9:19)
    for m in range(5):
        t_m = t_base + timedelta(minutes=m)
        engine.on_tick(_make_tick(price=24500.0 + m * 5, ts=t_m + timedelta(seconds=10)))
        engine.on_tick(_make_tick(price=24502.0 + m * 5, ts=t_m + timedelta(seconds=40)))

    # Tick at 9:20 closes 9:19 minute and closes the 5m candle [9:15, 9:20)
    engine.on_tick(_make_tick(price=24530.0, ts=t_base + timedelta(minutes=5, seconds=2)))

    candles_1m = engine.get_candles("IDX:NSE:NIFTY_50", Timeframe.M1)
    assert len(candles_1m) == 5

    candles_5m = engine.get_candles("IDX:NSE:NIFTY_50", Timeframe.M5)
    assert len(candles_5m) == 1
    assert candles_5m[0].start_timestamp == datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    assert candles_5m[0].end_timestamp == datetime(2026, 8, 28, 9, 20, 0, tzinfo=timezone.utc)
    assert candles_5m[0].open == 24500.0


def test_5_gap_detection_without_fabrication():
    engine = CanonicalCandleEngine()
    t1 = datetime(2026, 8, 28, 9, 15, 10, tzinfo=timezone.utc)
    # Jump ahead 3 minutes (from 9:15 to 9:18)
    t2 = datetime(2026, 8, 28, 9, 18, 5, tzinfo=timezone.utc)

    engine.on_tick(_make_tick(price=24500.0, ts=t1))
    engine.on_tick(_make_tick(price=24550.0, ts=t2))

    gaps = engine.detect_gaps("IDX:NSE:NIFTY_50", Timeframe.M1)
    assert len(gaps) == 1
    gap_start, gap_end = gaps[0]
    # Expected gap between end of 9:15 candle and start of 9:18 candle
    assert gap_start == datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)
    assert gap_end == datetime(2026, 8, 28, 9, 18, 0, tzinfo=timezone.utc)


def test_6_hydration_from_bootstrap():
    engine = CanonicalCandleEngine()
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)

    c1 = CanonicalCandle(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        session_date=date(2026, 8, 28),
        timeframe=Timeframe.M1,
        start_timestamp=t1,
        end_timestamp=t2,
        open=24500.0,
        high=24520.0,
        low=24490.0,
        close=24510.0,
    )
    engine.hydrate_candles([c1])

    # Re-hydrating the same candle must not duplicate
    engine.hydrate_candles([c1])

    finalized = engine.get_candles("IDX:NSE:NIFTY_50", Timeframe.M1)
    assert len(finalized) == 1
    assert finalized[0] == c1


def test_7_eventbus_candle_events():
    bus = MarketEventBus(queue_capacity=100)
    bus.start()

    engine = CanonicalCandleEngine()
    engine.attach(bus)

    updated_events = []
    closed_events = []
    bus.subscribe(MarketEventType.CANDLE_UPDATED, lambda e: updated_events.append(e))
    bus.subscribe(MarketEventType.CANDLE_CLOSED, lambda e: closed_events.append(e))

    t1 = datetime(2026, 8, 28, 9, 15, 10, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 28, 9, 16, 10, tzinfo=timezone.utc)

    bus.publish(MarketEventType.TICK, _make_tick(price=24500.0, ts=t1))
    time.sleep(0.02)
    bus.publish(MarketEventType.TICK, _make_tick(price=24510.0, ts=t2))
    time.sleep(0.05)

    bus.stop(drain=True)

    assert len(updated_events) >= 2
    assert len(closed_events) == 1
    assert isinstance(closed_events[0].payload, CanonicalCandle)


def test_8_architectural_import_inspection():
    import src.market_data.services.candle_engine as ce_mod
    source = inspect.getsource(ce_mod)
    forbidden = ["kiteconnect", "dhanhq", "src.broker", "src.frontend", "src.controlled_execution"]
    for f in forbidden:
        assert f"import {f}" not in source
        assert f"from {f}" not in source
