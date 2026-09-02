from __future__ import annotations
import inspect
import sys
import threading
import time
from datetime import date, datetime, timezone
from types import MappingProxyType
import pytest

from src.market_data.bus.events import (
    EventBusBackpressureError,
    EventBusStoppedError,
    MarketEvent,
    MarketEventType,
)
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.models.canonical_tick import CanonicalTick


def test_1_bus_initial_state():
    bus = MarketEventBus(queue_capacity=100)
    assert not bus.is_running
    stats = bus.stats()
    assert not stats["running"]
    assert stats["queue_depth"] == 0
    assert stats["published_total"] == 0
    assert stats["dispatched_total"] == 0
    assert stats["subscriber_count"] == 0


def test_2_start_and_3_stop():
    bus = MarketEventBus(queue_capacity=100)
    bus.start()
    assert bus.is_running
    assert bus.stats()["dispatcher_alive"]

    bus.stop(drain=True)
    assert not bus.is_running
    assert not bus.stats()["dispatcher_alive"]


def test_4_restart():
    bus = MarketEventBus(queue_capacity=100)
    bus.start()
    evt1 = bus.publish(MarketEventType.FEED_CONNECTED, {"status": "ONLINE"})
    bus.stop(drain=True)

    assert not bus.is_running
    # Restart
    bus.start()
    assert bus.is_running
    evt2 = bus.publish(MarketEventType.FEED_CONNECTED, {"status": "RECONNECTED"})
    # Sequence must continue monotonically, not reset
    assert evt2.sequence > evt1.sequence
    bus.stop(drain=True)


def test_5_subscribe_and_6_7_unsubscribe():
    bus = MarketEventBus(queue_capacity=100)
    received = []

    sub_id = bus.subscribe(MarketEventType.TICK, lambda e: received.append(e))
    assert sub_id.startswith("SUB-")
    assert bus.stats()["subscriber_count"] == 1

    # Unsubscribe
    assert bus.unsubscribe(sub_id) is True
    assert bus.stats()["subscriber_count"] == 0

    # Idempotent unsubscribe
    assert bus.unsubscribe(sub_id) is False
    assert bus.unsubscribe("NON_EXISTENT") is False


def test_8_publish_while_stopped_rejected():
    bus = MarketEventBus(queue_capacity=100)
    with pytest.raises(EventBusStoppedError, match="MarketEventBus is stopped"):
        bus.publish(MarketEventType.TICK, {"price": 100})


def test_9_tick_event_delivery():
    bus = MarketEventBus(queue_capacity=100)
    bus.start()

    delivered = []
    bus.subscribe(MarketEventType.TICK, lambda e: delivered.append(e))

    now_utc = datetime.now(timezone.utc)
    tick = CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=now_utc,
        received_at=now_utc,
        session_date=date.today(),
        last_price=24500.0,
    )

    evt = bus.publish(MarketEventType.TICK, tick, canonical_instrument_id="IDX:NSE:NIFTY_50")
    bus.stop(drain=True)

    assert len(delivered) == 1
    assert delivered[0].event_id == evt.event_id
    assert delivered[0].payload == tick
    assert delivered[0].canonical_instrument_id == "IDX:NSE:NIFTY_50"


def test_10_instrument_filter_and_11_wrong_instrument_not_delivered():
    bus = MarketEventBus(queue_capacity=100)
    bus.start()

    nifty_events = []
    vix_events = []

    bus.subscribe(
        MarketEventType.TICK,
        lambda e: nifty_events.append(e),
        canonical_instrument_id="IDX:NSE:NIFTY_50",
    )
    bus.subscribe(
        MarketEventType.TICK,
        lambda e: vix_events.append(e),
        canonical_instrument_id="IDX:NSE:INDIA_VIX",
    )

    now_utc = datetime.now(timezone.utc)
    tick_nifty = CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=now_utc,
        received_at=now_utc,
        session_date=date.today(),
        last_price=24500.0,
    )
    tick_vix = CanonicalTick(
        canonical_instrument_id="IDX:NSE:INDIA_VIX",
        provider="DHAN",
        exchange_timestamp=now_utc,
        received_at=now_utc,
        session_date=date.today(),
        last_price=12.5,
    )

    bus.publish(MarketEventType.TICK, tick_nifty, canonical_instrument_id="IDX:NSE:NIFTY_50")
    bus.publish(MarketEventType.TICK, tick_vix, canonical_instrument_id="IDX:NSE:INDIA_VIX")
    bus.stop(drain=True)

    assert len(nifty_events) == 1
    assert nifty_events[0].canonical_instrument_id == "IDX:NSE:NIFTY_50"

    assert len(vix_events) == 1
    assert vix_events[0].canonical_instrument_id == "IDX:NSE:INDIA_VIX"


def test_12_event_immutability():
    now_utc = datetime.now(timezone.utc)
    evt = MarketEvent(
        event_id="EVT-TEST",
        event_type=MarketEventType.FEED_CONNECTED,
        created_at=now_utc,
        sequence=1,
        payload={"status": "CONNECTED", "latency": 15},
    )

    # Payload dict wrapped in MappingProxyType
    assert isinstance(evt.payload, MappingProxyType)
    with pytest.raises(TypeError):
        evt.payload["status"] = "MUTATED"

    with pytest.raises(AttributeError):
        evt.sequence = 99


def test_13_sequence_monotonicity():
    bus = MarketEventBus(queue_capacity=500)
    bus.start()

    events = [bus.publish(MarketEventType.FEED_CONNECTED, {"i": i}) for i in range(100)]
    bus.stop(drain=True)

    sequences = [e.sequence for e in events]
    assert sequences == list(range(1, 101))


def test_14_10000_event_ordering_benchmark():
    """Publishes 10,000 events and verifies strictly ordered sequential FIFO delivery."""
    event_count = 10_000
    bus = MarketEventBus(queue_capacity=event_count + 1000)
    bus.start()

    received_sequences = []
    bus.subscribe(MarketEventType.TICK, lambda e: received_sequences.append(e.sequence))

    t0 = time.perf_counter()
    for i in range(event_count):
        bus.publish(MarketEventType.TICK, {"idx": i})
    publish_duration = time.perf_counter() - t0

    bus.stop(drain=True, timeout=10.0)

    assert len(received_sequences) == event_count
    # Verify strict FIFO sequence ordering
    assert received_sequences == list(range(1, event_count + 1))

    publish_throughput = event_count / max(publish_duration, 0.0001)
    print(f"\n[BENCHMARK] Published {event_count} events in {publish_duration*1000:.2f} ms ({publish_throughput:.0f} events/sec)")
    assert publish_throughput > 10_000, f"Expected >10,000 events/sec, got {publish_throughput:.0f}"


def test_15_concurrent_publishers_and_16_unique_event_ids():
    event_count_per_thread = 1_000
    thread_count = 8
    total_events = event_count_per_thread * thread_count

    bus = MarketEventBus(queue_capacity=total_events + 500)
    bus.start()

    published_events = []
    lock = threading.Lock()

    def producer():
        for i in range(event_count_per_thread):
            evt = bus.publish(MarketEventType.TICK, {"thread": threading.get_ident(), "i": i})
            with lock:
                published_events.append(evt)

    threads = [threading.Thread(target=producer) for _ in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    bus.stop(drain=True, timeout=10.0)

    assert len(published_events) == total_events

    # All sequence numbers must be distinct
    seqs = {e.sequence for e in published_events}
    assert len(seqs) == total_events
    assert seqs == set(range(1, total_events + 1))

    # All event IDs must be distinct
    event_ids = {e.event_id for e in published_events}
    assert len(event_ids) == total_events


def test_17_subscriber_exception_isolation_and_18_dispatcher_survives():
    bus = MarketEventBus(queue_capacity=100)
    bus.start()

    delivered_a = []
    delivered_c = []

    def sub_a(e):
        delivered_a.append(e)

    def sub_b_failing(e):
        raise ValueError("Deliberate failure in subscriber B")

    def sub_c(e):
        delivered_c.append(e)

    bus.subscribe(MarketEventType.TICK, sub_a)
    bus.subscribe(MarketEventType.TICK, sub_b_failing)
    bus.subscribe(MarketEventType.TICK, sub_c)

    bus.publish(MarketEventType.TICK, {"p": 100})
    bus.publish(MarketEventType.TICK, {"p": 200})
    bus.stop(drain=True)

    # Subscriber A and C must receive both events
    assert len(delivered_a) == 2
    assert len(delivered_c) == 2

    # Error counters must reflect subscriber B's failures
    stats = bus.stats()
    assert stats["subscriber_error_count"] == 2
    assert "Deliberate failure in subscriber B" in stats["last_subscriber_error"]


def test_19_slow_subscriber_detection():
    # Configure 5ms threshold
    bus = MarketEventBus(queue_capacity=100, slow_callback_threshold_ms=5.0)
    bus.start()

    def slow_subscriber(e):
        time.sleep(0.015)  # 15ms > 5ms threshold

    bus.subscribe(MarketEventType.TICK, slow_subscriber)
    bus.publish(MarketEventType.TICK, {"p": 100})
    bus.stop(drain=True)

    stats = bus.stats()
    assert stats["slow_subscriber_count"] >= 1
    assert stats["dispatched_total"] == 1


def test_20_queue_backpressure_and_21_bounded_capacity():
    # Small queue capacity = 5
    bus = MarketEventBus(queue_capacity=5)
    bus.start()

    # Pause dispatcher by subscribing a blocking callback
    block_event = threading.Event()

    def blocking_sub(e):
        block_event.wait(timeout=2.0)

    bus.subscribe(MarketEventType.TICK, blocking_sub)

    # First event is picked up by dispatcher and enters blocking_sub
    bus.publish(MarketEventType.TICK, {"init": True})
    time.sleep(0.02)

    # Remaining 5 events fill the queue up to capacity (5)
    for i in range(5):
        bus.publish(MarketEventType.TICK, {"i": i})

    # Next event must exceed capacity and trigger backpressure error
    with pytest.raises(EventBusBackpressureError, match="EventBus queue capacity .* exceeded"):
        bus.publish(MarketEventType.TICK, {"overflow": True})

    stats = bus.stats()
    assert stats["overflow_count"] >= 1

    # Unblock dispatcher and drain cleanly
    block_event.set()
    bus.stop(drain=True)


def test_22_stats_copy_safety():
    bus = MarketEventBus(queue_capacity=100)
    stats1 = bus.stats()
    stats1["queue_depth"] = 9999
    stats2 = bus.stats()
    assert stats2["queue_depth"] == 0


def test_23_clean_thread_shutdown_and_24_no_thread_leak_repeated_start_stop():
    initial_thread_count = threading.active_count()
    bus = MarketEventBus(queue_capacity=100)

    for _ in range(5):
        bus.start()
        bus.publish(MarketEventType.FEED_CONNECTED, {"k": 1})
        bus.stop(drain=True)
        assert not bus.is_running

    time.sleep(0.05)
    final_thread_count = threading.active_count()
    assert final_thread_count == initial_thread_count


def test_25_architectural_import_inspection():
    """Verifies that MarketEventBus does not import any broker/provider SDKs or runtime engines."""
    import src.market_data.bus.event_bus as bus_mod
    import src.market_data.bus.events as evt_mod

    source_bus = inspect.getsource(bus_mod)
    source_evt = inspect.getsource(evt_mod)
    combined = source_bus + "\n" + source_evt

    forbidden_modules = [
        "kiteconnect",
        "dhanhq",
        "src.broker",
        "src.controlled_execution",
        "src.proposal_engine",
        "src.server_bridge",
        "src.frontend",
        "src.options_engine",
    ]

    for forbidden in forbidden_modules:
        assert f"import {forbidden}" not in combined, f"MarketEventBus violates architectural boundary with: import {forbidden}"
        assert f"from {forbidden}" not in combined, f"MarketEventBus violates architectural boundary with: from {forbidden}"


def test_26_rejected_publish_does_not_consume_sequence():
    """Verifies that events rejected by backpressure do not create sequence holes."""
    bus = MarketEventBus(queue_capacity=3)
    bus.start()

    block_event = threading.Event()
    received_sequences = []

    def blocking_sub(e):
        received_sequences.append(e.sequence)
        block_event.wait(timeout=2.0)

    bus.subscribe(MarketEventType.TICK, blocking_sub)

    # 1. First event is picked up by dispatcher and enters blocking callback (seq: 1)
    evt1 = bus.publish(MarketEventType.TICK, {"n": 1})
    assert evt1.sequence == 1
    time.sleep(0.02)

    # 2. Fill queue capacity with 3 items (seq: 2, 3, 4)
    evt2 = bus.publish(MarketEventType.TICK, {"n": 2})
    evt3 = bus.publish(MarketEventType.TICK, {"n": 3})
    evt4 = bus.publish(MarketEventType.TICK, {"n": 4})
    assert [evt2.sequence, evt3.sequence, evt4.sequence] == [2, 3, 4]

    # 3. Next 3 attempts must be rejected by backpressure
    for _ in range(3):
        with pytest.raises(EventBusBackpressureError):
            bus.publish(MarketEventType.TICK, {"rejected": True})

    # 4. Unblock dispatcher and allow queue to drain
    block_event.set()
    time.sleep(0.05)

    # 5. Now publish next accepted event - sequence MUST be contiguous (5, not 8!)
    evt5 = bus.publish(MarketEventType.TICK, {"n": 5})
    assert evt5.sequence == 5

    bus.stop(drain=True)


def test_27_concurrent_publishers_and_backpressure_no_sequence_holes():
    """Verifies that under heavy concurrent contention and backpressure, accepted sequences remain strictly contiguous."""
    capacity = 100
    bus = MarketEventBus(queue_capacity=capacity)
    bus.start()

    accepted_events = []
    lock = threading.Lock()

    def producer():
        for i in range(100):
            try:
                evt = bus.publish(MarketEventType.TICK, {"thread": threading.get_ident(), "i": i})
                with lock:
                    accepted_events.append(evt)
            except EventBusBackpressureError:
                # Expected when queue is saturated
                pass
            except Exception:
                pass

    threads = [threading.Thread(target=producer) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    bus.stop(drain=True, timeout=10.0)

    accepted_count = len(accepted_events)
    assert accepted_count > 0
    accepted_sequences = sorted([e.sequence for e in accepted_events])

    # Sequence numbers must be strictly contiguous 1..accepted_count with ZERO gaps
    expected_sequences = list(range(1, accepted_count + 1))
    assert accepted_sequences == expected_sequences, f"Sequence gap detected! Found {accepted_sequences[:20]}... expected {expected_sequences[:20]}..."


def test_28_deep_mapping_and_sequence_immutability():
    """Verifies that nested mappings and sequences in event payloads are deeply frozen."""
    raw_payload = {
        "feed": {
            "status": "HEALTHY",
            "subscriptions": ["NIFTY", "VIX"],
            "depth": {"bids": [24500.0, 24495.0]},
        }
    }

    evt = MarketEvent(
        event_id="EVT-DEEP-TEST",
        event_type=MarketEventType.FEED_CONNECTED,
        created_at=datetime.now(timezone.utc),
        sequence=1,
        payload=raw_payload,
    )

    # Top-level mapping is immutable
    assert isinstance(evt.payload, MappingProxyType)
    with pytest.raises(TypeError):
        evt.payload["new_key"] = "test"

    # Nested mapping is immutable
    assert isinstance(evt.payload["feed"], MappingProxyType)
    with pytest.raises(TypeError):
        evt.payload["feed"]["status"] = "DEGRADED"

    # Deeply nested mapping is immutable
    assert isinstance(evt.payload["feed"]["depth"], MappingProxyType)
    with pytest.raises(TypeError):
        evt.payload["feed"]["depth"]["bids"] = [1.0]

    # Nested sequence is tuple (immutable)
    assert isinstance(evt.payload["feed"]["subscriptions"], tuple)
    with pytest.raises(AttributeError):
        evt.payload["feed"]["subscriptions"].append("BANKNIFTY")


def test_29_publisher_mutation_isolation():
    """Verifies that mutating source data structures after publication does not affect the event payload."""
    source_list = ["NIFTY", "VIX"]
    source_dict = {
        "metrics": {
            "count": 10,
            "symbols": source_list,
        }
    }

    bus = MarketEventBus(queue_capacity=50)
    bus.start()

    delivered = []
    bus.subscribe(MarketEventType.FEED_CONNECTED, lambda e: delivered.append(e))

    bus.publish(MarketEventType.FEED_CONNECTED, source_dict)

    # Publisher mutates original structures afterward
    source_list.append("BANKNIFTY")
    source_dict["metrics"]["count"] = 999
    source_dict["metrics"]["new_field"] = "HACKED"

    bus.stop(drain=True)

    assert len(delivered) == 1
    delivered_payload = delivered[0].payload

    # Event payload must remain completely untouched
    assert delivered_payload["metrics"]["count"] == 10
    assert delivered_payload["metrics"]["symbols"] == ("NIFTY", "VIX")
    assert "new_field" not in delivered_payload["metrics"]

