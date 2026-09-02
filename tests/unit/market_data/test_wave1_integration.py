from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone
import pytest

from src.market_data.bus.events import MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import Exchange, InstrumentType, Segment, Timeframe
from src.market_data.services.candle_engine import CanonicalCandleEngine
from src.market_data.services.feed_health_engine import FeedHealthEngine, FeedHealthStatus
from src.market_data.services.historical_bootstrap_service import HistoricalBootstrapService
from src.market_data.services.instrument_master_service import InstrumentMasterService
from src.market_data.state.live_market_state import LiveMarketState


def test_wave1_end_to_end_10000_tick_integration_benchmark():
    """
    Simulates high-throughput market data flow through the unified Wave 1 stack:
    EventBus -> [LiveMarketState, FeedHealthEngine, CanonicalCandleEngine].
    """
    # 1. Master & Instruments
    master = InstrumentMasterService()
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    vix = CanonicalInstrument(
        canonical_id="IDX:NSE:INDIA_VIX",
        symbol="INDIA VIX",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    master.register(nifty)
    master.register(vix)

    # 2. EventBus
    bus = MarketEventBus(queue_capacity=50_000)
    bus.start()

    # 3. Engines
    state_store = LiveMarketState(instrument_master=master)
    health_engine = FeedHealthEngine(healthy_threshold_seconds=5.0, delayed_threshold_seconds=10.0)
    candle_engine = CanonicalCandleEngine()

    # Attach all three engines to EventBus
    state_store.attach(bus)
    health_engine.attach(bus)
    candle_engine.attach(bus)

    # 4. Generate 10,000 ticks across a 15-minute trading window
    count = 10_000
    t_start = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    sess_date = date(2026, 8, 28)

    t0 = time.perf_counter()
    for i in range(count):
        # 10,000 ticks spread across 900 seconds (15 mins)
        offset_ms = int(i * 90)
        t_ex = t_start + timedelta(milliseconds=offset_ms)
        cid = "IDX:NSE:NIFTY_50" if i % 2 == 0 else "IDX:NSE:INDIA_VIX"
        price = 24500.0 + (i % 40) if cid == "IDX:NSE:NIFTY_50" else 12.0 + ((i % 20) * 0.05)

        tick = CanonicalTick(
            canonical_instrument_id=cid,
            provider="DHAN",
            exchange_timestamp=t_ex,
            received_at=t_ex + timedelta(milliseconds=15),
            session_date=sess_date,
            last_price=price,
            volume=100 + i,
        )
        bus.publish(MarketEventType.TICK, tick, canonical_instrument_id=cid)

    publish_duration = time.perf_counter() - t0

    # 5. Stop and drain EventBus cleanly
    bus.stop(drain=True, timeout=15.0)

    # 6. Verify assertions across all engines
    # A. LiveMarketState
    assert state_store.state_revision == count
    assert state_store.get_nifty() is not None
    assert state_store.get_vix() is not None

    # B. FeedHealthEngine
    health_nifty = health_engine.get_health_report("IDX:NSE:NIFTY_50", current_time=t_start + timedelta(minutes=15, seconds=1))
    assert health_nifty.update_count == count // 2
    assert health_nifty.status == FeedHealthStatus.HEALTHY

    # C. CandleEngine
    m1_candles = candle_engine.get_candles("IDX:NSE:NIFTY_50", Timeframe.M1)
    m5_candles = candle_engine.get_candles("IDX:NSE:NIFTY_50", Timeframe.M5)
    assert len(m1_candles) >= 13  # Closed 1-minute buckets across the 15-minute range
    assert len(m5_candles) >= 2   # Closed 5-minute buckets

    total_throughput = count / max(publish_duration, 0.0001)
    print(f"\n[WAVE 1 BENCHMARK] Published and dispatched {count} ticks across 3 engines in {publish_duration*1000:.2f} ms ({total_throughput:.0f} ticks/sec)")

    assert total_throughput > 1_000, f"Expected >1,000 ticks/sec, got {total_throughput:.0f}"
