from __future__ import annotations

import pandas as pd
from src.models import MarketContext
from src.utils import setup_logger, now_str
from src.data_engine import (
    fetch_nifty_spot,
    fetch_india_vix,
    resolve_current_expiry,
    load_nifty_candles,
    determine_trading_session,
)
from src.indicator_engine import (
    calculate_swing_highs,
    calculate_swing_lows,
    calculate_prev_day_high,
    calculate_prev_day_low,
    calculate_weekly_high,
    calculate_weekly_low,
    calculate_dynamic_support,
    calculate_dynamic_resistance,
    analyze_trend,
    calculate_volatility_state,
    classify_market_regime,
)

logger = setup_logger("MarketIntelligencePipeline")


class MarketIntelligencePipeline:
    """
    Modular, stateless pipeline that acts as the single source of truth for NIFTY Market Intelligence.
    Assembles and returns a complete, robust MarketContext.
    """

    def __init__(self) -> None:
        pass

    def run(self, kite, instruments_df: pd.DataFrame) -> MarketContext:
        """
        Runs the full market intelligence data gathering and calculation sequence.
        Returns a single unified MarketContext object.
        """
        logger.info("Initializing NIFTY Market Intelligence Pipeline...")

        # 1. Fetch raw data from the data engine
        spot_price = fetch_nifty_spot(kite)
        expiry_str = resolve_current_expiry(instruments_df)
        india_vix = fetch_india_vix(kite)
        session_str = determine_trading_session()
        timestamp = now_str()

        candles_dict = load_nifty_candles(kite, instruments_df)
        daily_candles = candles_dict.get("day")
        if daily_candles is None or daily_candles.empty:
            raise RuntimeError("NIFTY daily candles are required for the Market Intelligence Pipeline.")

        # 2. Support & Resistance level calculations
        swing_highs = calculate_swing_highs(daily_candles, left=2, right=2)
        swing_lows = calculate_swing_lows(daily_candles, left=2, right=2)

        pdh = calculate_prev_day_high(daily_candles, include_last=False)
        pdl = calculate_prev_day_low(daily_candles, include_last=False)

        wh = calculate_weekly_high(daily_candles, lookback_bars=5)
        wl = calculate_weekly_low(daily_candles, lookback_bars=5)

        dyn_support = calculate_dynamic_support(daily_candles, ema_period=50, atr_period=14, multiplier=1.5)
        dyn_resistance = calculate_dynamic_resistance(daily_candles, ema_period=50, atr_period=14, multiplier=1.5)

        # Assemble robust support levels list
        support_levels = []
        if pdl is not None:
            support_levels.append(pdl)
        if wl is not None:
            support_levels.append(wl)
        if dyn_support > 0:
            support_levels.append(dyn_support)
        support_levels.extend(swing_lows[-3:])  # Use the last 3 swing lows
        support_levels = sorted(list(set([round(float(level), 2) for level in support_levels])))

        # Assemble robust resistance levels list
        resistance_levels = []
        if pdh is not None:
            resistance_levels.append(pdh)
        if wh is not None:
            resistance_levels.append(wh)
        if dyn_resistance > 0:
            resistance_levels.append(dyn_resistance)
        resistance_levels.extend(swing_highs[-3:])  # Use the last 3 swing highs
        resistance_levels = sorted(list(set([round(float(level), 2) for level in resistance_levels])))

        # 3. Calculate Trend snapshot (ADX, EMAs, Slope, Momentum, Trend strength)
        trend_snapshot = analyze_trend(daily_candles, symbol="NIFTY")

        # 4. Calculate Volatility snapshot (ATR, compression, expansion, classification)
        vol_snapshot = calculate_volatility_state(daily_candles)

        # 5. Classify final Market Regime based on trend + volatility Snapshots
        market_regime_str = classify_market_regime(trend_snapshot, vol_snapshot)

        # 6. Extract/Calculate VWAP from Intraday candles if available
        vwap_val = spot_price
        five_min_candles = candles_dict.get("5minute")
        if five_min_candles is not None and not five_min_candles.empty:
            five_min_candles = five_min_candles.copy()
            five_min_candles["session_date"] = pd.to_datetime(five_min_candles["date"]).dt.date
            latest_session = five_min_candles["session_date"].max()
            latest_intraday = five_min_candles[five_min_candles["session_date"] == latest_session].copy()
            if not latest_intraday.empty:
                typical_price = (latest_intraday["high"] + latest_intraday["low"] + latest_intraday["close"]) / 3.0
                volume_sum = latest_intraday["volume"].sum()
                if volume_sum > 0:
                    vwap_val = float(round((typical_price * latest_intraday["volume"]).sum() / volume_sum, 2))

        # 7. Compile into cohesive, immutable MarketContext object
        market_context = MarketContext(
            current_spot=round(spot_price, 2),
            timestamp=timestamp,
            trading_session=session_str,
            current_expiry=expiry_str,
            market_regime=market_regime_str,
            trend_direction=trend_snapshot.trend,
            trend_strength=trend_snapshot.trend_strength_score,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            vwap=vwap_val,
            atr=vol_snapshot.atr,
            india_vix=india_vix,
            volatility_state=vol_snapshot.classification,
        )

        logger.info(f"NIFTY MarketContext assembled successfully: Regime={market_regime_str}, Trend={trend_snapshot.trend}")
        return market_context
