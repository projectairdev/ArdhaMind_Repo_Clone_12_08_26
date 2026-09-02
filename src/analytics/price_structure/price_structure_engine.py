from __future__ import annotations

from datetime import datetime, time, timezone
import math
from typing import List, Optional, Sequence

from src.analytics.price_structure.models import (
    ATRContext,
    BreakoutContext,
    BreakoutStatus,
    CompressionContext,
    GapContext,
    GapType,
    LevelInfo,
    OpeningRangeContext,
    PriceStructureContext,
    SwingPoint,
    TWAPContext,
    TrendDirection,
    VWAPContext,
)
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.quality_enums import DataQualityStatus
from src.market_data.state.live_market_state import InstrumentState, LiveMarketState


class PriceStructureEngine:
    """
    Deterministic provider-independent engine for price structure analysis.
    Consumes CanonicalCandles and LiveMarketState without external assumptions.
    """

    @staticmethod
    def analyze(
        instrument_state: Optional[InstrumentState],
        intraday_candles_1m: Sequence[CanonicalCandle],
        higher_tf_candles_15m: Optional[Sequence[CanonicalCandle]] = None,
        opening_range_minutes: int = 15,
    ) -> PriceStructureContext:
        """Computes complete price structure context."""
        if instrument_state is None or not intraday_candles_1m:
            return PriceStructureEngine._empty_context()

        last_price = instrument_state.last_price
        open_price = instrument_state.open or intraday_candles_1m[0].open
        prev_close = instrument_state.previous_close or open_price

        # 1. VWAP & TWAP Calculation
        vwap_ctx = PriceStructureEngine.calculate_vwap(intraday_candles_1m, last_price)
        twap_ctx = PriceStructureEngine.calculate_twap(intraday_candles_1m, last_price)

        # 2. Opening Range (09:15 to 09:15 + opening_range_minutes)
        or_ctx = PriceStructureEngine.calculate_opening_range(
            intraday_candles_1m,
            last_price,
            duration_minutes=opening_range_minutes,
        )

        # 3. Gap Analysis
        gap_ctx = PriceStructureEngine.calculate_gap(
            open_price=open_price,
            previous_close=prev_close,
            intraday_high=instrument_state.high or max(c.high for c in intraday_candles_1m),
            intraday_low=instrument_state.low or min(c.low for c in intraday_candles_1m),
        )

        # 4. Swings detection
        swings = PriceStructureEngine.detect_swings(intraday_candles_1m)

        # 5. Support & Resistance Levels
        supports, resistances = PriceStructureEngine.calculate_levels(
            last_price=last_price,
            prev_close=prev_close,
            prev_high=instrument_state.high,
            prev_low=instrument_state.low,
            opening_range=or_ctx,
            swings=swings,
        )

        # 6. Trend Determination
        trend = PriceStructureEngine.evaluate_trend(intraday_candles_1m, swings)

        # 7. ATR Context
        atr_ctx = PriceStructureEngine.calculate_atr(intraday_candles_1m)

        # 8. Compression Context
        compression_ctx = PriceStructureEngine.evaluate_compression(intraday_candles_1m, atr_ctx)

        # 9. Breakout Context
        breakout_ctx = PriceStructureEngine.evaluate_breakout(
            last_price=last_price,
            opening_range=or_ctx,
            supports=supports,
            resistances=resistances,
            candles=intraday_candles_1m,
        )

        return PriceStructureContext(
            last_price=last_price,
            trend=trend,
            vwap_context=vwap_ctx,
            twap_context=twap_ctx,
            opening_range=or_ctx,
            gap_context=gap_ctx,
            support_levels=supports,
            resistance_levels=resistances,
            swings=swings,
            breakout=breakout_ctx,
            compression=compression_ctx,
            atr=atr_ctx,
            quality=DataQualityStatus.VALID,
        )

    @staticmethod
    def calculate_vwap(candles: Sequence[CanonicalCandle], current_price: float) -> Optional[VWAPContext]:
        """
        Calculates Volume Weighted Average Price strictly when real volume exists.
        Returns None (UNAVAILABLE) if volume is missing or zero across all candles.
        Zero synthetic substitution.
        """
        if not candles:
            return None

        cum_pv = 0.0
        cum_vol = 0

        for c in candles:
            if c.volume is not None and c.volume > 0:
                typ_p = (c.high + c.low + c.close) / 3.0
                cum_pv += typ_p * c.volume
                cum_vol += c.volume

        if cum_vol == 0:
            return None

        vwap = round(cum_pv / cum_vol, 2)
        dist = round(current_price - vwap, 2)
        dist_pct = round((dist / vwap) * 100.0, 4) if vwap > 0 else 0.0

        pos = "AT_VWAP"
        if dist > 0.5:
            pos = "ABOVE"
        elif dist < -0.5:
            pos = "BELOW"

        return VWAPContext(
            vwap=vwap,
            current_price=current_price,
            distance_points=dist,
            distance_pct=dist_pct,
            price_position=pos,
            cumulative_volume=cum_vol,
            quality=DataQualityStatus.VALID,
        )

    @staticmethod
    def calculate_twap(candles: Sequence[CanonicalCandle], current_price: float) -> Optional[TWAPContext]:
        """Calculates Time Weighted Average Price (time-weighted typical price)."""
        if not candles:
            return None

        cum_p = sum((c.high + c.low + c.close) / 3.0 for c in candles)
        twap = round(cum_p / len(candles), 2)

        dist = round(current_price - twap, 2)
        dist_pct = round((dist / twap) * 100.0, 4) if twap > 0 else 0.0

        pos = "AT_TWAP"
        if dist > 0.5:
            pos = "ABOVE"
        elif dist < -0.5:
            pos = "BELOW"

        return TWAPContext(
            twap=twap,
            current_price=current_price,
            distance_points=dist,
            distance_pct=dist_pct,
            price_position=pos,
            quality=DataQualityStatus.VALID,
        )

    @staticmethod
    def calculate_opening_range(
        candles: Sequence[CanonicalCandle],
        current_price: float,
        duration_minutes: int = 15,
    ) -> OpeningRangeContext:
        """Extracts opening range from first N minutes of continuous trading."""
        if not candles:
            return OpeningRangeContext(
                duration_minutes=duration_minutes,
                high=None,
                low=None,
                range_size=None,
                is_established=False,
                status="FORMING",
            )

        or_candles = candles[:duration_minutes]
        or_high = max(c.high for c in or_candles)
        or_low = min(c.low for c in or_candles)
        or_range = round(or_high - or_low, 2)
        is_established = len(candles) >= duration_minutes

        if not is_established:
            status = "FORMING"
            direction = "NONE"
        elif current_price > or_high:
            status = "ABOVE"
            direction = "UP"
        elif current_price < or_low:
            status = "BELOW"
            direction = "DOWN"
        else:
            status = "INSIDE"
            direction = "NONE"

        return OpeningRangeContext(
            duration_minutes=duration_minutes,
            high=or_high,
            low=or_low,
            range_size=or_range,
            is_established=is_established,
            status=status,
            breakout_direction=direction,
        )

    @staticmethod
    def calculate_gap(
        open_price: float,
        previous_close: float,
        intraday_high: float,
        intraday_low: float,
    ) -> GapContext:
        """Determines gap type, gap size, and fill completion status."""
        gap_pts = round(open_price - previous_close, 2)
        gap_pct = round((gap_pts / previous_close) * 100.0, 4) if previous_close > 0 else 0.0

        if gap_pts >= 10.0:
            gap_type = GapType.GAP_UP
            is_filled = intraday_low <= previous_close
            fill_pct = 100.0 if is_filled else round(max(0.0, min(100.0, ((open_price - intraday_low) / gap_pts) * 100.0)), 2)
        elif gap_pts <= -10.0:
            gap_type = GapType.GAP_DOWN
            is_filled = intraday_high >= previous_close
            fill_pct = 100.0 if is_filled else round(max(0.0, min(100.0, ((intraday_high - open_price) / abs(gap_pts)) * 100.0)), 2)
        else:
            gap_type = GapType.FLAT
            is_filled = True
            fill_pct = 100.0

        return GapContext(
            gap_type=gap_type,
            gap_points=gap_pts,
            gap_pct=gap_pct,
            is_filled=is_filled,
            fill_pct=fill_pct,
            previous_close=previous_close,
            open_price=open_price,
        )

    @staticmethod
    def detect_swings(candles: Sequence[CanonicalCandle], window: int = 3) -> List[SwingPoint]:
        """Detects local peak (swing high) and trough (swing low) pivot points."""
        swings: List[SwingPoint] = []
        n = len(candles)
        if n < (window * 2 + 1):
            return swings

        for i in range(window, n - window):
            curr = candles[i]
            if all(curr.high >= candles[j].high for j in range(i - window, i + window + 1) if j != i):
                swings.append(SwingPoint(timestamp=curr.end_timestamp, price=curr.high, swing_type="HIGH"))
            elif all(curr.low <= candles[j].low for j in range(i - window, i + window + 1) if j != i):
                swings.append(SwingPoint(timestamp=curr.end_timestamp, price=curr.low, swing_type="LOW"))

        return swings

    @staticmethod
    def calculate_levels(
        last_price: float,
        prev_close: float,
        prev_high: Optional[float],
        prev_low: Optional[float],
        opening_range: OpeningRangeContext,
        swings: Sequence[SwingPoint],
    ) -> tuple[List[LevelInfo], List[LevelInfo]]:
        """Identifies support and resistance clusters relative to last_price."""
        raw_levels: List[LevelInfo] = []

        if prev_close > 0:
            raw_levels.append(LevelInfo(price=prev_close, level_type="PIVOT", source="PDC", strength=0.8))
        if prev_high and prev_high > 0:
            raw_levels.append(LevelInfo(price=prev_high, level_type="RESISTANCE", source="PDH", strength=0.9))
        if prev_low and prev_low > 0:
            raw_levels.append(LevelInfo(price=prev_low, level_type="SUPPORT", source="PDL", strength=0.9))

        if opening_range.is_established:
            if opening_range.high:
                raw_levels.append(LevelInfo(price=opening_range.high, level_type="RESISTANCE", source="ORH", strength=0.85))
            if opening_range.low:
                raw_levels.append(LevelInfo(price=opening_range.low, level_type="SUPPORT", source="ORL", strength=0.85))

        for s in swings:
            ltype = "RESISTANCE" if s.swing_type == "HIGH" else "SUPPORT"
            raw_levels.append(LevelInfo(price=s.price, level_type=ltype, source=f"SWING_{s.swing_type}", strength=0.7))

        base_rnd = math.floor(last_price / 100.0) * 100.0
        for offset in (-200.0, -100.0, 0.0, 100.0, 200.0):
            rnd_p = base_rnd + offset
            ltype = "SUPPORT" if rnd_p < last_price else ("RESISTANCE" if rnd_p > last_price else "PIVOT")
            raw_levels.append(LevelInfo(price=rnd_p, level_type=ltype, source="ROUND_NUMBER", strength=0.6))

        supports = [l for l in raw_levels if l.price < last_price]
        resistances = [l for l in raw_levels if l.price > last_price]

        supports.sort(key=lambda l: l.price, reverse=True)
        resistances.sort(key=lambda l: l.price)

        return supports[:5], resistances[:5]

    @staticmethod
    def evaluate_trend(candles: Sequence[CanonicalCandle], swings: Sequence[SwingPoint]) -> TrendDirection:
        """Determines price trend from candle slopes and swing structures."""
        if len(candles) < 10:
            return TrendDirection.SIDEWAYS

        recent_closes = [c.close for c in candles[-20:]]
        sma_short = sum(recent_closes[-5:]) / 5.0
        sma_long = sum(recent_closes) / len(recent_closes)

        high_swings = [s.price for s in swings if s.swing_type == "HIGH"]
        low_swings = [s.price for s in swings if s.swing_type == "LOW"]

        higher_highs = len(high_swings) >= 2 and high_swings[-1] > high_swings[-2]
        higher_lows = len(low_swings) >= 2 and low_swings[-1] > low_swings[-2]
        lower_highs = len(high_swings) >= 2 and high_swings[-1] < high_swings[-2]
        lower_lows = len(low_swings) >= 2 and low_swings[-1] < low_swings[-2]

        if (higher_highs and higher_lows) or (sma_short > sma_long + 5.0):
            return TrendDirection.BULLISH
        elif (lower_highs and lower_lows) or (sma_short < sma_long - 5.0):
            return TrendDirection.BEARISH
        else:
            return TrendDirection.SIDEWAYS

    @staticmethod
    def calculate_atr(candles: Sequence[CanonicalCandle], period: int = 14) -> ATRContext:
        """Calculates Average True Range over N periods."""
        if len(candles) < 2:
            return ATRContext(atr_value=15.0, current_range=15.0, expansion_ratio=1.0)

        tr_values: List[float] = []
        for i in range(1, len(candles)):
            c = candles[i]
            prev_c = candles[i - 1]
            tr = max(
                c.high - c.low,
                abs(c.high - prev_c.close),
                abs(c.low - prev_c.close),
            )
            tr_values.append(tr)

        atr_window = tr_values[-period:] if len(tr_values) >= period else tr_values
        atr = sum(atr_window) / len(atr_window) if atr_window else 15.0
        atr = round(atr, 2)

        curr_range = round(candles[-1].high - candles[-1].low, 2)
        expansion = round(curr_range / atr, 2) if atr > 0 else 1.0

        return ATRContext(
            atr_value=atr,
            current_range=curr_range,
            expansion_ratio=expansion,
        )

    @staticmethod
    def evaluate_compression(candles: Sequence[CanonicalCandle], atr_ctx: ATRContext) -> CompressionContext:
        """Determines if the asset is in a volatility squeeze / compression."""
        if len(candles) < 10:
            return CompressionContext(is_compressing=False, compression_ratio=1.0)

        recent_ranges = [c.high - c.low for c in candles[-5:]]
        avg_recent_range = sum(recent_ranges) / len(recent_ranges)
        ratio = round(avg_recent_range / atr_ctx.atr_value, 2) if atr_ctx.atr_value > 0 else 1.0

        is_compressing = ratio < 0.6

        return CompressionContext(
            is_compressing=is_compressing,
            compression_ratio=ratio,
        )

    @staticmethod
    def evaluate_breakout(
        last_price: float,
        opening_range: OpeningRangeContext,
        supports: Sequence[LevelInfo],
        resistances: Sequence[LevelInfo],
        candles: Sequence[CanonicalCandle],
    ) -> BreakoutContext:
        """Evaluates breakout, breakdown, retest, and failed breakout states."""
        if not opening_range.is_established or not opening_range.high or not opening_range.low:
            return BreakoutContext(status=BreakoutStatus.NONE, level_price=None, level_source=None, distance_pct=0.0)

        orh = opening_range.high
        orl = opening_range.low

        if last_price > orh:
            dist_pct = round(((last_price - orh) / orh) * 100.0, 2)
            retested = any(abs(c.low - orh) <= 5.0 and c.close > orh for c in candles[-5:])
            return BreakoutContext(
                status=BreakoutStatus.RETESTING if retested else BreakoutStatus.BREAKOUT_UP,
                level_price=orh,
                level_source="ORH",
                distance_pct=dist_pct,
                retest_confirmed=retested,
            )
        elif last_price < orl:
            dist_pct = round(((orl - last_price) / orl) * 100.0, 2)
            retested = any(abs(c.high - orl) <= 5.0 and c.close < orl for c in candles[-5:])
            return BreakoutContext(
                status=BreakoutStatus.RETESTING if retested else BreakoutStatus.BREAKDOWN,
                level_price=orl,
                level_source="ORL",
                distance_pct=dist_pct,
                retest_confirmed=retested,
            )

        return BreakoutContext(status=BreakoutStatus.NONE, level_price=None, level_source=None, distance_pct=0.0)

    @staticmethod
    def _empty_context() -> PriceStructureContext:
        return PriceStructureContext(
            last_price=0.0,
            trend=TrendDirection.UNAVAILABLE,
            vwap_context=None,
            twap_context=None,
            opening_range=OpeningRangeContext(15, None, None, None, False, "FORMING"),
            gap_context=GapContext(GapType.FLAT, 0.0, 0.0, True, 100.0, 0.0, 0.0),
            support_levels=[],
            resistance_levels=[],
            swings=[],
            breakout=BreakoutContext(BreakoutStatus.NONE, None, None, 0.0),
            compression=CompressionContext(False, 1.0),
            atr=ATRContext(0.0, 0.0, 1.0),
            quality=DataQualityStatus.UNAVAILABLE,
        )
