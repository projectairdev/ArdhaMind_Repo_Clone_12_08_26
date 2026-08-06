from __future__ import annotations

import pandas as pd
from src.indicator_engine.indicators import ema, atr


def calculate_swing_highs(df: pd.DataFrame, left: int = 2, right: int = 2) -> list[float]:
    """
    Finds swing highs (local maxima) in the high series of a DataFrame.
    A bar is a swing high if its high is greater than or equal to the highs
    of 'left' bars before it and strictly greater than 'right' bars after it.
    """
    if df.empty or len(df) < (left + right + 1):
        return []
    highs = df["high"].astype(float).values
    swing_highs = []
    for i in range(left, len(highs) - right):
        val = highs[i]
        is_swing = True
        for j in range(i - left, i):
            if highs[j] > val:
                is_swing = False
                break
        if is_swing:
            for j in range(i + 1, i + right + 1):
                if highs[j] >= val:
                    is_swing = False
                    break
        if is_swing:
            swing_highs.append(float(val))
    return swing_highs


def calculate_swing_lows(df: pd.DataFrame, left: int = 2, right: int = 2) -> list[float]:
    """
    Finds swing lows (local minima) in the low series of a DataFrame.
    A bar is a swing low if its low is less than or equal to the lows
    of 'left' bars before it and strictly less than 'right' bars after it.
    """
    if df.empty or len(df) < (left + right + 1):
        return []
    lows = df["low"].astype(float).values
    swing_lows = []
    for i in range(left, len(lows) - right):
        val = lows[i]
        is_swing = True
        for j in range(i - left, i):
            if lows[j] < val:
                is_swing = False
                break
        if is_swing:
            for j in range(i + 1, i + right + 1):
                if lows[j] <= val:
                    is_swing = False
                    break
        if is_swing:
            swing_lows.append(float(val))
    return swing_lows


def calculate_prev_day_high(df: pd.DataFrame, include_last: bool = False) -> float | None:
    """
    Returns the high price of the previous day candle.
    If include_last is False, assumes the last row is the active day and uses second-to-last.
    """
    if df.empty:
        return None
    row = df.iloc[-1] if include_last or len(df) < 2 else df.iloc[-2]
    return float(row["high"])


def calculate_prev_day_low(df: pd.DataFrame, include_last: bool = False) -> float | None:
    """
    Returns the low price of the previous day candle.
    If include_last is False, assumes the last row is the active day and uses second-to-last.
    """
    if df.empty:
        return None
    row = df.iloc[-1] if include_last or len(df) < 2 else df.iloc[-2]
    return float(row["low"])


def calculate_weekly_high(df: pd.DataFrame, lookback_bars: int = 5) -> float | None:
    """
    Returns the maximum high over the last N daily bars (weekly high).
    """
    if df.empty:
        return None
    weekly_window = df.tail(min(lookback_bars, len(df)))
    return float(weekly_window["high"].max())


def calculate_weekly_low(df: pd.DataFrame, lookback_bars: int = 5) -> float | None:
    """
    Returns the minimum low over the last N daily bars (weekly low).
    """
    if df.empty:
        return None
    weekly_window = df.tail(min(lookback_bars, len(df)))
    return float(weekly_window["low"].min())


def calculate_dynamic_support(df: pd.DataFrame, ema_period: int = 50, atr_period: int = 14, multiplier: float = 1.5) -> float:
    """
    Calculates dynamic support as EMA minus a multiplier of ATR.
    """
    if df.empty:
        return 0.0
    ema_series = ema(df["close"], ema_period)
    atr_series = atr(df, atr_period)
    
    last_ema = ema_series.iloc[-1]
    last_atr = atr_series.iloc[-1] if len(df) >= atr_period else 0.0
    return float(last_ema - multiplier * last_atr)


def calculate_dynamic_resistance(df: pd.DataFrame, ema_period: int = 50, atr_period: int = 14, multiplier: float = 1.5) -> float:
    """
    Calculates dynamic resistance as EMA plus a multiplier of ATR.
    """
    if df.empty:
        return 0.0
    ema_series = ema(df["close"], ema_period)
    atr_series = atr(df, atr_period)
    
    last_ema = ema_series.iloc[-1]
    last_atr = atr_series.iloc[-1] if len(df) >= atr_period else 0.0
    return float(last_ema + multiplier * last_atr)
