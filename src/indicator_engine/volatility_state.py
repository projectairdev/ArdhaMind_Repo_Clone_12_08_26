from __future__ import annotations

from dataclasses import dataclass
import pandas as pd
from src.indicator_engine.indicators import atr


@dataclass
class VolatilitySnapshot:
    atr: float
    atr_percentile: float
    daily_range: float
    daily_range_pct: float
    is_compressed: bool
    is_expanded: bool
    classification: str


def calculate_volatility_state(df: pd.DataFrame, atr_period: int = 14, lookback_percentile: int = 100) -> VolatilitySnapshot:
    """
    Analyzes historical and current volatility metrics to classify the volatility state.
    """
    if df.empty:
        return VolatilitySnapshot(
            atr=0.0,
            atr_percentile=50.0,
            daily_range=0.0,
            daily_range_pct=0.0,
            is_compressed=False,
            is_expanded=False,
            classification="NORMAL"
        )

    out = df.sort_values("date").copy()
    
    # 1. Calculate ATR
    out["atr"] = atr(out, atr_period)
    last_atr = float(out["atr"].iloc[-1]) if not out["atr"].empty and not pd.isna(out["atr"].iloc[-1]) else 0.0

    # 2. Calculate ATR Percentile
    atr_history = out["atr"].dropna().tail(lookback_percentile)
    if len(atr_history) > 1:
        if atr_history.max() == atr_history.min():
            atr_percentile = 0.0
        else:
            atr_percentile = float((atr_history <= last_atr).mean() * 100.0)
    else:
        atr_percentile = 50.0


    # 3. Daily Range
    last_row = out.iloc[-1]
    high = float(last_row["high"])
    low = float(last_row["low"])
    close = float(last_row["close"])
    daily_range = high - low
    daily_range_pct = (daily_range / close) * 100.0 if close > 0 else 0.0

    # 4. Compression / Expansion
    # Compare 5-period ATR (short) vs 20-period ATR (long)
    short_atr_series = atr(out, 5)
    long_atr_series = atr(out, 20)
    
    short_atr = float(short_atr_series.iloc[-1]) if len(short_atr_series) >= 5 else last_atr
    long_atr = float(long_atr_series.iloc[-1]) if len(long_atr_series) >= 20 else last_atr

    is_compressed = short_atr < long_atr * 0.9
    is_expanded = short_atr > long_atr * 1.15

    # 5. Volatility Classification
    if atr_percentile >= 75.0:
        classification = "HIGH"
    elif atr_percentile <= 25.0:
        classification = "LOW"
    else:
        classification = "NORMAL"

    return VolatilitySnapshot(
        atr=round(last_atr, 2),
        atr_percentile=round(atr_percentile, 2),
        daily_range=round(daily_range, 2),
        daily_range_pct=round(daily_range_pct, 2),
        is_compressed=is_compressed,
        is_expanded=is_expanded,
        classification=classification,
    )
