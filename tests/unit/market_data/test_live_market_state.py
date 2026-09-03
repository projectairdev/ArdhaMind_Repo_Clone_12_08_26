from __future__ import annotations

import inspect
import sys
import threading
import time
from datetime import date, datetime, timedelta, timezone
import pytest

from src.market_data.bus.events import MarketEvent, MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import (
    DataQualityStatus,
    Exchange,
    InstrumentType,
    Segment,
)
from src.market_data.services.instrument_master_service import InstrumentMasterService
from src.market_data.state.live_market_state import InstrumentState, LiveMarketState


def _make_tick(
    canonical_id: str = "IDX:NSE:NIFTY_50",
    price: float = 24500.0,
    session_date: date = date(2026, 8, 28),
    ts: Optional[datetime] = None,
    provider: str = "DHAN",
    open_p: Optional[float] = None,
    high_p: Optional[float] = None,
    low_p: Optional[float] = None,
    prev_close: Optional[float] = None,
    volume: Optional[int] = None,
    oi: Optional[int] = None,
    bid: Optional[float] = None,
    ask: Optional[float] = None,
    seq: Optional[int] = None,
) -> CanonicalTick:
    t = ts or datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    return CanonicalTick(
        canonical_instrument_id=canonical_id,
        provider=provider,
        exchange_timestamp=t,
        received_at=t,
        session_date=session_date,
        last_price=price,
        open=open_p,
        high=high_p,
        low=low_p,
        previous_close=prev_close,
        volume=volume,
        oi=oi,
        bid=bid,
        ask=ask,
        internal_sequence=seq,
    )


def _make_event(
    tick: CanonicalTick,
    sequence: int = 1,
    event_type: MarketEventType = MarketEventType.TICK,
    event_canonical_id: Optional[str] = None,
) -> MarketEvent:
    return MarketEvent(
        event_id=f"EVT-{sequence}",
        event_type=event_type,
        created_at=datetime.now(timezone.utc),
        sequence=sequence,
        payload=tick,
        canonical_instrument_id=event_canonical_id or tick.canonical_instrument_id,
    )


def test_1_empty_initial_state():
    state_store = LiveMarketState()
    assert state_store.state_revision == 0
    assert len(state_store.list_states()) == 0
    assert state_store.get_nifty() is None
    assert state_store.get_vix() is None
    assert state_store.snapshot() == {}


def test_2_apply_valid_nifty_tick_and_3_retrieve_nifty():
    store = LiveMarketState()
    tick = _make_tick(canonical_id="IDX:NSE:NIFTY_50", price=24500.0, prev_close=24400.0)
    evt = _make_event(tick, sequence=1)

    accepted = store.apply_tick_event(evt)
    assert accepted is True
    assert store.state_revision == 1

    nifty = store.get_nifty()
    assert nifty is not None
    assert nifty.canonical_instrument_id == "IDX:NSE:NIFTY_50"
    assert nifty.last_price == 24500.0
    assert nifty.change == 100.0
    assert nifty.change_pct == round((100.0 / 24400.0) * 100.0, 4)


def test_4_apply_vix_tick_and_5_multiple_instruments_coexist():
    store = LiveMarketState()
    tick_nifty = _make_tick(canonical_id="IDX:NSE:NIFTY_50", price=24500.0)
    tick_vix = _make_tick(canonical_id="IDX:NSE:INDIA_VIX", price=12.5)

    store.apply_tick_event(_make_event(tick_nifty, sequence=1))
    store.apply_tick_event(_make_event(tick_vix, sequence=2))

    assert store.state_revision == 2
    assert store.get_nifty().last_price == 24500.0
    assert store.get_vix().last_price == 12.5
    assert len(store.list_states()) == 2


def test_6_same_session_price_update_and_7_preserve_ohlc_and_8_preserve_prev_close():
    store = LiveMarketState()
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    tick1 = _make_tick(
        canonical_id="IDX:NSE:NIFTY_50",
        price=24500.0,
        ts=t1,
        open_p=24480.0,
        high_p=24520.0,
        low_p=24470.0,
        prev_close=24400.0,
        volume=1000,
    )
    store.apply_tick_event(_make_event(tick1, sequence=1))

    # Tick 2 has updated price, but omits open, high, low, previous_close
    t2 = t1 + timedelta(seconds=1)
    tick2 = _make_tick(
        canonical_id="IDX:NSE:NIFTY_50",
        price=24510.0,
        ts=t2,
        open_p=None,
        high_p=None,
        low_p=None,
        prev_close=None,
        volume=1500,
    )
    store.apply_tick_event(_make_event(tick2, sequence=2))

    nifty = store.get_nifty()
    assert nifty.last_price == 24510.0
    # Preserved from same session
    assert nifty.open == 24480.0
    assert nifty.high == 24520.0
    assert nifty.low == 24470.0
    assert nifty.previous_close == 24400.0
    assert nifty.volume == 1500
    assert nifty.update_count == 2
    assert nifty.change == 110.0


def test_9_derive_change_10_change_pct_11_spread():
    store = LiveMarketState()
    tick = _make_tick(
        canonical_id="IDX:NSE:NIFTY_50",
        price=24600.0,
        prev_close=24500.0,
        bid=24599.50,
        ask=24600.50,
    )
    store.apply_tick_event(_make_event(tick, sequence=1))

    state = store.get_nifty()
    assert state.change == 100.0
    assert state.change_pct == round((100.0 / 24500.0) * 100.0, 4)
    assert state.spread == 1.0


def test_12_missing_prev_close_gives_none_change():
    store = LiveMarketState()
    tick = _make_tick(canonical_id="IDX:NSE:NIFTY_50", price=24500.0, prev_close=None)
    store.apply_tick_event(_make_event(tick, sequence=1))

    state = store.get_nifty()
    assert state.change is None
    assert state.change_pct is None


def test_13_reject_older_session():
    store = LiveMarketState()
    tick_aug28 = _make_tick(session_date=date(2026, 8, 28), price=24500.0)
    store.apply_tick_event(_make_event(tick_aug28, sequence=1))

    # Incoming tick for August 27 must be rejected
    tick_aug27 = _make_tick(session_date=date(2026, 8, 27), price=24400.0)
    accepted = store.apply_tick_event(_make_event(tick_aug27, sequence=2))

    assert accepted is False
    assert store.state_revision == 1
    assert store.stats()["rejected_older_session"] == 1
    assert store.get_nifty().last_price == 24500.0


def test_14_reject_older_exchange_timestamp():
    store = LiveMarketState()
    t_now = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    tick_now = _make_tick(ts=t_now, price=24500.0)
    store.apply_tick_event(_make_event(tick_now, sequence=1))

    # Incoming tick with timestamp from 5 seconds ago must be rejected
    t_past = t_now - timedelta(seconds=5)
    tick_past = _make_tick(ts=t_past, price=24490.0)
    accepted = store.apply_tick_event(_make_event(tick_past, sequence=2))

    assert accepted is False
    assert store.state_revision == 1
    assert store.stats()["rejected_out_of_order"] == 1
    assert store.get_nifty().last_price == 24500.0


def test_15_equal_timestamp_resolved_by_eventbus_sequence():
    store = LiveMarketState()
    t = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    tick1 = _make_tick(ts=t, price=24500.0)
    store.apply_tick_event(_make_event(tick1, sequence=10))

    # Same timestamp, but higher sequence (20 > 10) -> accepted
    tick2 = _make_tick(ts=t, price=24505.0)
    acc2 = store.apply_tick_event(_make_event(tick2, sequence=20))
    assert acc2 is True
    assert store.get_nifty().last_price == 24505.0

    # Same timestamp, but lower sequence (5 <= 20) -> rejected
    tick3 = _make_tick(ts=t, price=24495.0)
    acc3 = store.apply_tick_event(_make_event(tick3, sequence=5))
    assert acc3 is False
    assert store.get_nifty().last_price == 24505.0


def test_16_rejected_update_does_not_increment_state_revision_and_17_accepted_does():
    store = LiveMarketState()
    t = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    store.apply_tick_event(_make_event(_make_tick(ts=t, price=24500.0), sequence=1))
    assert store.state_revision == 1

    # Rejected tick
    store.apply_tick_event(_make_event(_make_tick(ts=t - timedelta(seconds=1), price=24400.0), sequence=2))
    assert store.state_revision == 1

    # Accepted tick
    store.apply_tick_event(_make_event(_make_tick(ts=t + timedelta(seconds=1), price=24510.0), sequence=3))
    assert store.state_revision == 2


def test_18_new_session_clears_prior_session_intraday_and_19_no_prev_close_leakage():
    store = LiveMarketState()
    # Day 1: Aug 28
    tick_day1 = _make_tick(
        session_date=date(2026, 8, 28),
        price=24175.0,
        open_p=24122.0,
        high_p=24188.0,
        low_p=24076.0,
        prev_close=24100.0,
        volume=50000,
        oi=10000000,
    )
    store.apply_tick_event(_make_event(tick_day1, sequence=1))
    assert store.get_nifty().volume == 50000

    # Day 2: Aug 31 (Monday). First tick lacks open, high, low, volume, prev_close
    tick_day2 = _make_tick(
        session_date=date(2026, 8, 31),
        price=24220.0,
        open_p=None,
        high_p=None,
        low_p=None,
        prev_close=None,
        volume=None,
        oi=None,
    )
    store.apply_tick_event(_make_event(tick_day2, sequence=2))

    day2_state = store.get_nifty()
    assert day2_state.session_date == date(2026, 8, 31)
    assert day2_state.last_price == 24220.0
    # ZERO leakage from Aug 28
    assert day2_state.open is None
    assert day2_state.high is None
    assert day2_state.low is None
    assert day2_state.volume is None
    assert day2_state.oi is None
    assert day2_state.previous_close is None
    assert day2_state.update_count == 1


def test_20_provider_recorded_and_21_provider_switch_accepted():
    store = LiveMarketState()
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=1)

    store.apply_tick_event(_make_event(_make_tick(provider="KITE", ts=t1, price=24500.0), sequence=1))
    assert store.get_nifty().provider == "KITE"

    store.apply_tick_event(_make_event(_make_tick(provider="DHAN", ts=t2, price=24505.0), sequence=2))
    assert store.get_nifty().provider == "DHAN"
    assert store.get_nifty().last_price == 24505.0


def test_22_snapshot_immutable_and_23_external_mutation_safe():
    store = LiveMarketState()
    store.apply_tick_event(_make_event(_make_tick(price=24500.0), sequence=1))

    snap = store.snapshot()
    assert "IDX:NSE:NIFTY_50" in snap
    snap["IDX:NSE:NIFTY_50"] = None

    # Internal state is untouched
    assert store.get_nifty() is not None
    assert store.get_nifty().last_price == 24500.0


def test_24_concurrent_readers_and_25_concurrent_writers_and_26_no_partial_state():
    store = LiveMarketState()
    stop_event = threading.Event()
    errors = []

    def writer():
        seq = 1
        t_base = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
        while not stop_event.is_set():
            t = t_base + timedelta(milliseconds=seq)
            tick = _make_tick(price=24500.0 + (seq % 100), ts=t)
            store.apply_tick_event(_make_event(tick, sequence=seq))
            seq += 1
            if seq > 500:
                break

    def reader():
        while not stop_event.is_set():
            n = store.get_nifty()
            if n is not None:
                if n.last_price <= 0 or n.session_date is None:
                    errors.append("Observed corrupted partial state!")
            snap = store.snapshot()
            if len(snap) > 0 and "IDX:NSE:NIFTY_50" not in snap:
                errors.append("Snapshot inconsistent!")

    writers = [threading.Thread(target=writer) for _ in range(4)]
    readers = [threading.Thread(target=reader) for _ in range(4)]

    for t in readers:
        t.start()
    for t in writers:
        t.start()

    for t in writers:
        t.join()
    stop_event.set()
    for t in readers:
        t.join()

    assert len(errors) == 0


def test_27_unknown_instrument_rejected_when_master_supplied_and_28_allowed_without_master():
    master = InstrumentMasterService()
    master.register(
        CanonicalInstrument(
            canonical_id="IDX:NSE:NIFTY_50",
            symbol="NIFTY 50",
            exchange=Exchange.NSE,
            segment=Segment.INDEX,
            instrument_type=InstrumentType.INDEX,
        )
    )

    store_with_master = LiveMarketState(instrument_master=master)
    # Unknown instrument
    tick_unknown = _make_tick(canonical_id="IDX:NSE:UNKNOWN_INDEX")
    acc = store_with_master.apply_tick_event(_make_event(tick_unknown, sequence=1))
    assert acc is False

    # Allowed without master
    store_no_master = LiveMarketState(instrument_master=None)
    acc2 = store_no_master.apply_tick_event(_make_event(tick_unknown, sequence=1))
    assert acc2 is True


def test_29_event_instrument_id_mismatch_rejected():
    store = LiveMarketState()
    tick = _make_tick(canonical_id="IDX:NSE:NIFTY_50")
    # Event envelope specifies a different ID than the tick payload
    evt = _make_event(tick, sequence=1, event_canonical_id="IDX:NSE:INDIA_VIX")

    acc = store.apply_tick_event(evt)
    assert acc is False
    assert store.stats()["rejected_invalid_event"] == 1


def test_30_non_tick_event_rejected_and_31_wrong_payload_rejected():
    store = LiveMarketState()
    evt_wrong_type = MarketEvent(
        event_id="EVT-1",
        event_type=MarketEventType.FEED_CONNECTED,
        created_at=datetime.now(timezone.utc),
        sequence=1,
        payload={"status": "CONNECTED"},
    )
    assert store.apply_tick_event(evt_wrong_type) is False

    evt_wrong_payload = MarketEvent(
        event_id="EVT-2",
        event_type=MarketEventType.TICK,
        created_at=datetime.now(timezone.utc),
        sequence=2,
        payload="INVALID_PAYLOAD_NOT_CANONICAL_TICK",
    )
    assert store.apply_tick_event(evt_wrong_payload) is False


def test_32_attach_and_33_detach_and_34_no_updates_after_detach_and_35_repeated_attach():
    bus = MarketEventBus(queue_capacity=100)
    bus.start()
    store = LiveMarketState()

    # Repeated attach is idempotent
    store.attach(bus)
    store.attach(bus)
    assert store.stats()["attached_to_event_bus"] is True

    # Publish tick on bus
    tick = _make_tick(canonical_id="IDX:NSE:NIFTY_50", price=24500.0)
    bus.publish(MarketEventType.TICK, tick, canonical_instrument_id="IDX:NSE:NIFTY_50")

    time.sleep(0.05)
    assert store.get_nifty() is not None
    assert store.get_nifty().last_price == 24500.0

    # Detach
    store.detach()
    assert store.stats()["attached_to_event_bus"] is False

    # Publish another tick
    t2 = datetime(2026, 8, 28, 9, 15, 40, tzinfo=timezone.utc)
    tick2 = _make_tick(canonical_id="IDX:NSE:NIFTY_50", price=24550.0, ts=t2)
    bus.publish(MarketEventType.TICK, tick2, canonical_instrument_id="IDX:NSE:NIFTY_50")

    time.sleep(0.05)
    # State must NOT update after detach
    assert store.get_nifty().last_price == 24500.0

    bus.stop(drain=True)


def test_36_stats_correct():
    store = LiveMarketState()
    tick = _make_tick(price=24500.0)
    store.apply_tick_event(_make_event(tick, sequence=1))

    stats = store.stats()
    assert stats["instrument_count"] == 1
    assert stats["state_revision"] == 1
    assert stats["accepted_updates"] == 1
    assert stats["rejected_updates"] == 0
    assert stats["last_applied_event_sequence"] == 1


def test_37_state_revision_contiguous():
    store = LiveMarketState()
    t_base = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    for i in range(1, 21):
        t = t_base + timedelta(seconds=i)
        store.apply_tick_event(_make_event(_make_tick(price=24500.0 + i, ts=t), sequence=i))

    assert store.state_revision == 20


def test_38_no_tick_age_ms_persisted():
    store = LiveMarketState()
    tick = _make_tick(price=24500.0)
    store.apply_tick_event(_make_event(tick, sequence=1))

    state = store.get_nifty()
    assert not hasattr(state, "tick_age_ms")
    assert not hasattr(state, "age_ms")


def test_39_no_fabricated_fields():
    store = LiveMarketState()
    # Tick without open/high/low
    tick = _make_tick(price=24500.0, open_p=None, high_p=None, low_p=None)
    store.apply_tick_event(_make_event(tick, sequence=1))

    state = store.get_nifty()
    assert state.open is None
    assert state.high is None
    assert state.low is None


def test_40_architectural_import_inspection():
    """Verifies that LiveMarketState does not import any broker/provider SDKs or runtime engines."""
    import src.market_data.state.live_market_state as state_mod

    source = inspect.getsource(state_mod)
    forbidden_modules = [
        "kiteconnect",
        "dhanhq",
        "src.broker",
        "src.controlled_execution",
        "src.proposal_engine",
        "src.server_bridge",
        "src.frontend",
        "src.options_engine",
        "src.intelligence_engine",
    ]

    for forbidden in forbidden_modules:
        assert f"import {forbidden}" not in source, f"LiveMarketState violates architectural boundary with: import {forbidden}"
        assert f"from {forbidden}" not in source, f"LiveMarketState violates architectural boundary with: from {forbidden}"


def test_41_options_lookup():
    store = LiveMarketState()
    opt1 = _make_tick(canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:CE", price=120.0)
    opt2 = _make_tick(canonical_id="OPT:NFO:NIFTY:2026-09-03:24500:PE", price=80.0)
    opt3 = _make_tick(canonical_id="OPT:NFO:NIFTY:2026-09-10:24500:CE", price=160.0)

    store.apply_tick_event(_make_event(opt1, sequence=1))
    store.apply_tick_event(_make_event(opt2, sequence=2))
    store.apply_tick_event(_make_event(opt3, sequence=3))

    opts_sep3 = store.get_options(underlying="NIFTY", expiry="2026-09-03")
    assert len(opts_sep3) == 2
    assert [o.canonical_instrument_id for o in opts_sep3] == [
        "OPT:NFO:NIFTY:2026-09-03:24500:CE",
        "OPT:NFO:NIFTY:2026-09-03:24500:PE",
    ]

    all_nifty_opts = store.get_options(underlying="NIFTY")
    assert len(all_nifty_opts) == 3


def test_42_10000_tick_ingestion_benchmark():
    """Benchmark applying 10,000 tick events into LiveMarketState."""
    store = LiveMarketState()
    t_base = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    count = 10_000

    events = [
        _make_event(
            _make_tick(
                canonical_id="IDX:NSE:NIFTY_50" if i % 2 == 0 else "IDX:NSE:INDIA_VIX",
                price=24500.0 + (i % 50),
                ts=t_base + timedelta(milliseconds=i),
                prev_close=24400.0,
            ),
            sequence=i,
        )
        for i in range(1, count + 1)
    ]

    t0 = time.perf_counter()
    for evt in events:
        store.apply_tick_event(evt)
    duration = time.perf_counter() - t0

    throughput = count / max(duration, 0.0001)
    print(f"\n[BENCHMARK] Applied {count} ticks into LiveMarketState in {duration*1000:.2f} ms ({throughput:.0f} ticks/sec)")

    assert store.state_revision == count
    assert throughput > 10_000, f"Expected >10,000 ticks/sec, got {throughput:.0f}"


def test_43_instrument_state_timestamps_required_and_tz_aware():
    now_utc = datetime.now(timezone.utc)
    sess_date = date.today()

    # Valid construction
    state = InstrumentState(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        session_date=sess_date,
        last_price=24500.0,
        exchange_timestamp=now_utc,
        received_at=now_utc,
    )
    assert state.exchange_timestamp == now_utc
    assert state.received_at == now_utc

    # Missing / None exchange_timestamp must raise ValueError/TypeError
    with pytest.raises((ValueError, TypeError)):
        InstrumentState(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            symbol="NIFTY 50",
            session_date=sess_date,
            last_price=24500.0,
            exchange_timestamp=None,  # Invalid
            received_at=now_utc,
        )

    # Naive exchange_timestamp must raise ValueError
    naive_ts = datetime(2026, 8, 28, 9, 15, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        InstrumentState(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            symbol="NIFTY 50",
            session_date=sess_date,
            last_price=24500.0,
            exchange_timestamp=naive_ts,
            received_at=now_utc,
        )


def test_44_same_session_ohlc_monotonicity():
    store = LiveMarketState()
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=1)
    t3 = t1 + timedelta(seconds=2)

    # 1. First tick sets Open=24450, High=24500, Low=24400
    tick1 = _make_tick(ts=t1, price=24480.0, open_p=24450.0, high_p=24500.0, low_p=24400.0)
    store.apply_tick_event(_make_event(tick1, sequence=1))
    s1 = store.get_nifty()
    assert s1.open == 24450.0
    assert s1.high == 24500.0
    assert s1.low == 24400.0

    # 2. Second tick reports conflicting lower High=24490, higher Low=24420, conflicting Open=24460
    tick2 = _make_tick(ts=t2, price=24485.0, open_p=24460.0, high_p=24490.0, low_p=24420.0)
    store.apply_tick_event(_make_event(tick2, sequence=2))
    s2 = store.get_nifty()
    # High cannot regress (max(24500, 24490) = 24500)
    assert s2.high == 24500.0
    # Low cannot regress (min(24400, 24420) = 24400)
    assert s2.low == 24400.0
    # Open remains authoritative first known open (24450)
    assert s2.open == 24450.0

    # 3. Third tick reports expanded High=24550 and expanded Low=24350
    tick3 = _make_tick(ts=t3, price=24540.0, open_p=None, high_p=24550.0, low_p=24350.0)
    store.apply_tick_event(_make_event(tick3, sequence=3))
    s3 = store.get_nifty()
    assert s3.high == 24550.0
    assert s3.low == 24350.0
    assert s3.open == 24450.0


def test_45_missing_initial_open_populated_later():
    store = LiveMarketState()
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=1)

    # Initial tick has no open
    tick1 = _make_tick(ts=t1, price=24480.0, open_p=None)
    store.apply_tick_event(_make_event(tick1, sequence=1))
    assert store.get_nifty().open is None

    # Later tick in same session provides open
    tick2 = _make_tick(ts=t2, price=24485.0, open_p=24450.0)
    store.apply_tick_event(_make_event(tick2, sequence=2))
    assert store.get_nifty().open == 24450.0


def test_46_no_last_price_derived_high_low_fabrication():
    store = LiveMarketState()
    # Price is 24600, but tick has no High/Low metadata
    tick = _make_tick(price=24600.0, high_p=None, low_p=None)
    store.apply_tick_event(_make_event(tick, sequence=1))

    state = store.get_nifty()
    assert state.last_price == 24600.0
    assert state.high is None
    assert state.low is None


def test_47_bid_only_update_preserving_compatible_old_ask():
    store = LiveMarketState()
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=1)

    # 1. Existing: Bid=100, Ask=105
    tick1 = _make_tick(ts=t1, price=102.0, bid=100.0, ask=105.0)
    store.apply_tick_event(_make_event(tick1, sequence=1))

    # 2. Incoming: Bid=102, Ask=None (compatible since 105 >= 102)
    tick2 = _make_tick(ts=t2, price=103.0, bid=102.0, ask=None)
    store.apply_tick_event(_make_event(tick2, sequence=2))

    s2 = store.get_nifty()
    assert s2.bid == 102.0
    assert s2.ask == 105.0
    assert s2.spread == 3.0


def test_48_bid_only_update_clearing_incompatible_stale_ask():
    store = LiveMarketState()
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=1)

    # 1. Existing: Bid=100, Ask=101
    tick1 = _make_tick(ts=t1, price=100.5, bid=100.0, ask=101.0)
    store.apply_tick_event(_make_event(tick1, sequence=1))

    # 2. Incoming: Bid=103, Ask=None (crossed with existing ask 101 < 103)
    tick2 = _make_tick(ts=t2, price=103.0, bid=103.0, ask=None)
    store.apply_tick_event(_make_event(tick2, sequence=2))

    s2 = store.get_nifty()
    assert s2.bid == 103.0
    # Incompatible stale ask must be cleared to None, spread None
    assert s2.ask is None
    assert s2.spread is None


def test_49_ask_only_update_preserving_compatible_old_bid():
    store = LiveMarketState()
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=1)

    # 1. Existing: Bid=100, Ask=105
    tick1 = _make_tick(ts=t1, price=102.0, bid=100.0, ask=105.0)
    store.apply_tick_event(_make_event(tick1, sequence=1))

    # 2. Incoming: Ask=104, Bid=None (compatible since 104 >= 100)
    tick2 = _make_tick(ts=t2, price=103.0, bid=None, ask=104.0)
    store.apply_tick_event(_make_event(tick2, sequence=2))

    s2 = store.get_nifty()
    assert s2.bid == 100.0
    assert s2.ask == 104.0
    assert s2.spread == 4.0


def test_50_ask_only_update_clearing_incompatible_stale_bid():
    store = LiveMarketState()
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=1)

    # 1. Existing: Bid=100, Ask=101
    tick1 = _make_tick(ts=t1, price=100.5, bid=100.0, ask=101.0)
    store.apply_tick_event(_make_event(tick1, sequence=1))

    # 2. Incoming: Ask=98, Bid=None (crossed with existing bid 100 > 98)
    tick2 = _make_tick(ts=t2, price=98.0, bid=None, ask=98.0)
    store.apply_tick_event(_make_event(tick2, sequence=2))

    s2 = store.get_nifty()
    assert s2.ask == 98.0
    # Incompatible stale bid must be cleared to None, spread None
    assert s2.bid is None
    assert s2.spread is None


def test_51_canonical_tick_rejects_non_positive_ohlc_and_inverted_bounds():
    ts = datetime.now(timezone.utc)
    sess = date.today()

    # Zero open
    with pytest.raises(ValueError, match="open' must be positive"):
        CanonicalTick(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            exchange_timestamp=ts,
            received_at=ts,
            session_date=sess,
            last_price=24500.0,
            open=0.0,
        )

    # Negative high
    with pytest.raises(ValueError, match="high' must be positive"):
        CanonicalTick(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            exchange_timestamp=ts,
            received_at=ts,
            session_date=sess,
            last_price=24500.0,
            high=-10.0,
        )

    # High < Low inverted bounds
    with pytest.raises(ValueError, match="cannot be less than 'low'"):
        CanonicalTick(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            exchange_timestamp=ts,
            received_at=ts,
            session_date=sess,
            last_price=24500.0,
            high=24400.0,
            low=24500.0,
        )

