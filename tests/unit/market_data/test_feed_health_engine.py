from __future__ import annotations

import inspect
from datetime import date, datetime, timedelta, timezone
import pytest

from src.market_data.bus.events import MarketEvent, MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.services.feed_health_engine import (
    FeedHealthEngine,
    FeedHealthReport,
    FeedHealthStatus,
)


def _make_tick(
    canonical_id: str = "IDX:NSE:NIFTY_50",
    price: float = 24500.0,
    ts: Optional[datetime] = None,
    rcv_ts: Optional[datetime] = None,
) -> CanonicalTick:
    t_ex = ts or datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    t_rcv = rcv_ts or t_ex + timedelta(milliseconds=25)
    return CanonicalTick(
        canonical_instrument_id=canonical_id,
        provider="DHAN",
        exchange_timestamp=t_ex,
        received_at=t_rcv,
        session_date=date(2026, 8, 28),
        last_price=price,
    )


def test_1_healthy_tick_flow():
    engine = FeedHealthEngine(healthy_threshold_seconds=3.0, delayed_threshold_seconds=7.0, recovery_confirmation_ticks=1)
    engine.on_socket_connected()

    t_now = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    tick = _make_tick(ts=t_now, rcv_ts=t_now)
    engine.on_tick(tick)

    # Evaluate 1 second after tick
    eval_time = t_now + timedelta(seconds=1.0)
    report = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=eval_time)

    assert report.status == FeedHealthStatus.HEALTHY
    assert report.socket_connected is True
    assert report.tick_age_ms == 1000.0
    assert report.update_count == 1


def test_2_delayed_transition():
    engine = FeedHealthEngine(healthy_threshold_seconds=3.0, delayed_threshold_seconds=7.0, recovery_confirmation_ticks=1)
    t_now = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    engine.on_tick(_make_tick(ts=t_now, rcv_ts=t_now))

    # Evaluate 4.5 seconds after tick (> 3.0s, <= 7.0s)
    eval_time = t_now + timedelta(seconds=4.5)
    report = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=eval_time)

    assert report.status == FeedHealthStatus.DELAYED
    assert report.delayed_count == 1


def test_3_stale_transition():
    engine = FeedHealthEngine(healthy_threshold_seconds=3.0, delayed_threshold_seconds=7.0, recovery_confirmation_ticks=1)
    t_now = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    engine.on_tick(_make_tick(ts=t_now, rcv_ts=t_now))

    # Evaluate 8 seconds after tick (> 7.0s)
    eval_time = t_now + timedelta(seconds=8.0)
    report = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=eval_time)

    assert report.status == FeedHealthStatus.STALE
    assert report.stale_count == 1


def test_4_recovery_after_fresh_tick():
    engine = FeedHealthEngine(healthy_threshold_seconds=3.0, delayed_threshold_seconds=7.0, recovery_confirmation_ticks=1)
    t1 = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    engine.on_tick(_make_tick(ts=t1, rcv_ts=t1))

    # Force stale
    t_stale = t1 + timedelta(seconds=10.0)
    rep_stale = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=t_stale)
    assert rep_stale.status == FeedHealthStatus.STALE

    # Fresh tick arrives
    t2 = t1 + timedelta(seconds=11.0)
    engine.on_tick(_make_tick(ts=t2, rcv_ts=t2))

    rep_fresh = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=t2 + timedelta(milliseconds=100))
    assert rep_fresh.status == FeedHealthStatus.HEALTHY
    assert rep_fresh.recovery_count == 1


def test_5_connected_socket_with_no_ticks_becomes_stale():
    engine = FeedHealthEngine(healthy_threshold_seconds=3.0, delayed_threshold_seconds=7.0, recovery_confirmation_ticks=1)
    engine.on_socket_connected()

    # Evaluated with no ticks ever received
    now = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    report = engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=now)
    assert report.status == FeedHealthStatus.STALE


def test_6_provider_latency_tracking():
    engine = FeedHealthEngine(recovery_confirmation_ticks=1)
    t_ex = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    t_rcv = t_ex + timedelta(milliseconds=45)
    tick = _make_tick(ts=t_ex, rcv_ts=t_rcv)

    engine.on_tick(tick)
    report = engine.get_health_report("IDX:NSE:NIFTY_50", current_time=t_rcv)
    assert report.provider_latency_ms == 45.0


def test_7_eventbus_health_publication():
    bus = MarketEventBus(queue_capacity=100)
    bus.start()

    engine = FeedHealthEngine(healthy_threshold_seconds=1.0, delayed_threshold_seconds=2.0, recovery_confirmation_ticks=1)
    engine.attach(bus)

    health_events = []
    bus.subscribe(MarketEventType.FEED_STALE, lambda e: health_events.append(e))
    bus.subscribe(MarketEventType.FEED_RECOVERED, lambda e: health_events.append(e))

    # Send tick through bus
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    bus.publish(MarketEventType.TICK, _make_tick(ts=t1, rcv_ts=t1))

    # Evaluate stale
    import time
    time.sleep(0.02)
    engine.evaluate_health("IDX:NSE:NIFTY_50", current_time=t1 + timedelta(seconds=5.0))

    # Send recovering tick
    t2 = t1 + timedelta(seconds=6.0)
    bus.publish(MarketEventType.TICK, _make_tick(ts=t2, rcv_ts=t2))
    time.sleep(0.05)

    bus.stop(drain=True)

    event_types = [e.event_type for e in health_events]
    assert MarketEventType.FEED_STALE in event_types
    assert MarketEventType.FEED_RECOVERED in event_types


def test_8_architectural_import_inspection():
    import src.market_data.services.feed_health_engine as fhe_mod
    source = inspect.getsource(fhe_mod)
    forbidden = ["kiteconnect", "dhanhq", "src.broker", "src.frontend", "src.controlled_execution"]
    for f in forbidden:
        assert f"import {f}" not in source
        assert f"from {f}" not in source
