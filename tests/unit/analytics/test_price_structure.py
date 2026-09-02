from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import pytest

from src.analytics.price_structure.models import (
    BreakoutStatus,
    GapType,
    TrendDirection,
)
from src.analytics.price_structure.price_structure_engine import PriceStructureEngine
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.quality_enums import CandleQuality, Timeframe
from src.market_data.state.live_market_state import InstrumentState


def _make_candles(
    count: int = 30,
    base_price: float = 24500.0,
    trend_step: float = 2.0,
    has_volume: bool = True,
) -> list[CanonicalCandle]:
    t0 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    candles = []
    p = base_price
    for i in range(count):
        st = t0 + timedelta(minutes=i)
        et = st + timedelta(minutes=1)
        o = p
        c = p + trend_step
        h = max(o, c) + 3.0
        l = min(o, c) - 3.0
        v = 1000 if has_volume else None
        candles.append(
            CanonicalCandle(
                canonical_instrument_id="IDX:NSE:NIFTY_50",
                provider="DHAN",
                session_date=date(2026, 8, 28),
                timeframe=Timeframe.M1,
                start_timestamp=st,
                end_timestamp=et,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=v,
                quality=CandleQuality.VALID,
            )
        )
        p = c
    return candles


def test_1_vwap_calculation_with_volume_and_twap():
    # 1. With Volume: VWAP computed correctly
    candles_vol = _make_candles(10, base_price=24500.0, trend_step=5.0, has_volume=True)
    vwap_res = PriceStructureEngine.calculate_vwap(candles_vol, current_price=24550.0)
    assert vwap_res is not None
    assert vwap_res.vwap > 24500.0
    assert vwap_res.price_position == "ABOVE"
    assert vwap_res.cumulative_volume > 0

    # 2. Without Volume: VWAP MUST be None (UNAVAILABLE) - zero fake fallback!
    candles_no_vol = _make_candles(10, base_price=24500.0, trend_step=5.0, has_volume=False)
    vwap_none = PriceStructureEngine.calculate_vwap(candles_no_vol, current_price=24550.0)
    assert vwap_none is None

    # 3. TWAP is calculated separately and explicitly
    twap_res = PriceStructureEngine.calculate_twap(candles_no_vol, current_price=24550.0)
    assert twap_res is not None
    assert twap_res.twap > 24500.0
    assert twap_res.price_position == "ABOVE"


def test_2_opening_range_states():
    # Case 1: First 15 min forming
    candles_short = _make_candles(10, base_price=24500.0)
    or1 = PriceStructureEngine.calculate_opening_range(candles_short, current_price=24520.0, duration_minutes=15)
    assert or1.is_established is False
    assert or1.status == "FORMING"

    # Case 2: 15 min established, price inside range
    candles_full = _make_candles(20, base_price=24500.0, trend_step=0.5)
    or_high = max(c.high for c in candles_full[:15])
    or_low = min(c.low for c in candles_full[:15])
    mid_price = (or_high + or_low) / 2.0

    or2 = PriceStructureEngine.calculate_opening_range(candles_full, current_price=mid_price, duration_minutes=15)
    assert or2.is_established is True
    assert or2.status == "INSIDE"
    assert or2.breakout_direction == "NONE"

    # Case 3: Price above opening range high
    or3 = PriceStructureEngine.calculate_opening_range(candles_full, current_price=or_high + 10.0, duration_minutes=15)
    assert or3.status == "ABOVE"
    assert or3.breakout_direction == "UP"


def test_3_gap_analysis_and_fill_status():
    # Gap Up
    gap_up = PriceStructureEngine.calculate_gap(
        open_price=24550.0,
        previous_close=24500.0,
        intraday_high=24580.0,
        intraday_low=24520.0,
    )
    assert gap_up.gap_type == GapType.GAP_UP
    assert gap_up.gap_points == 50.0
    assert gap_up.is_filled is False
    assert gap_up.fill_pct > 0.0

    # Gap Up Filled
    gap_up_filled = PriceStructureEngine.calculate_gap(
        open_price=24550.0,
        previous_close=24500.0,
        intraday_high=24580.0,
        intraday_low=24495.0,  # Below previous_close
    )
    assert gap_up_filled.is_filled is True
    assert gap_up_filled.fill_pct == 100.0


def test_4_trend_and_swings_detection():
    # Uptrending candles
    candles_up = _make_candles(30, base_price=24500.0, trend_step=3.0)
    swings = PriceStructureEngine.detect_swings(candles_up)
    trend = PriceStructureEngine.evaluate_trend(candles_up, swings)

    assert trend == TrendDirection.BULLISH


def test_5_atr_and_compression():
    candles = _make_candles(30, base_price=24500.0, trend_step=1.0)
    atr_ctx = PriceStructureEngine.calculate_atr(candles, period=14)
    assert atr_ctx.atr_value > 0.0

    comp_ctx = PriceStructureEngine.evaluate_compression(candles, atr_ctx)
    assert isinstance(comp_ctx.is_compressing, bool)


def test_6_full_price_structure_integration():
    t_now = datetime(2026, 8, 28, 10, 0, 0, tzinfo=timezone.utc)
    state = InstrumentState(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY",
        session_date=date(2026, 8, 28),
        exchange_timestamp=t_now,
        received_at=t_now,
        last_price=24580.0,
        open=24500.0,
        high=24600.0,
        low=24480.0,
        previous_close=24450.0,
        provider="DHAN",
    )
    candles = _make_candles(45, base_price=24500.0, trend_step=1.8)
    ctx = PriceStructureEngine.analyze(state, candles)

    assert ctx.last_price == 24580.0
    assert ctx.trend == TrendDirection.BULLISH
    assert len(ctx.support_levels) > 0
    assert len(ctx.resistance_levels) > 0
    assert ctx.gap_context.gap_type == GapType.GAP_UP
