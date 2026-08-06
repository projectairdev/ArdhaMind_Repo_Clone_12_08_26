from __future__ import annotations

import numpy as np
import pandas as pd
from src.models import TrendSnapshot, StructureMetrics
from src.indicator_engine.indicators import ema, rsi, atr
from src.indicator_engine.structure import detect_market_structure


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates the Average Directional Index (ADX) using Wilder's smoothing.
    """
    if len(df) < period + 1:
        return pd.Series(0.0, index=df.index)

    highs = df["high"].astype(float)
    lows = df["low"].astype(float)
    closes = df["close"].astype(float)

    prev_close = closes.shift(1)

    # True Range (TR)
    tr = pd.concat([
        (highs - lows).abs(),
        (highs - prev_close).abs(),
        (lows - prev_close).abs()
    ], axis=1).max(axis=1)

    plus_dm = highs.diff()
    minus_dm = -lows.diff()

    plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm), 0.0)
    minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > plus_dm), 0.0)

    # Wilde's smoothing (exponential moving average with alpha = 1 / period)
    smoothed_tr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    smoothed_plus_dm = plus_dm.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    smoothed_minus_dm = minus_dm.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    plus_di = 100 * (smoothed_plus_dm / smoothed_tr.replace(0, np.nan)).fillna(0.0)
    minus_di = 100 * (smoothed_minus_dm / smoothed_tr.replace(0, np.nan)).fillna(0.0)

    di_sum = plus_di + minus_di
    di_diff = (plus_di - minus_di).abs()

    dx = 100 * (di_diff / di_sum.replace(0, np.nan)).fillna(0.0)
    adx = dx.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    return adx.fillna(0.0)


def calculate_slope(series: pd.Series, lookback: int = 5) -> float:
    """
    Calculates the slope of a series using linear regression.
    """
    if len(series) < lookback:
        return 0.0
    y = series.tail(lookback).values
    x = np.arange(lookback)
    slope, _ = np.polyfit(x, y, 1)
    return float(slope)


def calculate_momentum_score(closes: pd.Series, period: int = 10) -> float:
    """
    Calculates a Momentum Score based on Rate of Change (ROC) and RSI deviation from 50.
    """
    if len(closes) < period:
        return 0.0
    
    # Rate of Change (percentage change over period)
    roc = ((closes.iloc[-1] - closes.iloc[-period]) / closes.iloc[-period]) * 100.0
    
    # RSI calculation
    rsi_series = rsi(closes, period)
    rsi_val = rsi_series.iloc[-1] if not rsi_series.empty else 50.0
    rsi_dev = (rsi_val - 50.0) / 10.0  # Normalized deviation (-5 to +5)
    
    # Combined Momentum Score
    return float(round(0.6 * roc + 0.4 * rsi_dev, 2))


def analyze_trend(
    df: pd.DataFrame,
    symbol: str,
    fast_period: int = 20,
    slow_period: int = 50,
    rsi_period: int = 14,
    atr_period: int = 14,
    vol_period: int = 20,
) -> TrendSnapshot:
    """
    Performs comprehensive trend strength analysis on a given candle DataFrame.
    """
    if df.empty:
        return TrendSnapshot(
            symbol=symbol,
            spot=0.0,
            close=0.0,
            ema_fast=0.0,
            ema_slow=0.0,
            rsi=50.0,
            atr=0.0,
            avg_volume=0.0,
            last_volume=0.0,
            volume_ratio=1.0,
            trend="SIDEWAYS",
            trigger_buy_above=0.0,
            trigger_sell_below=0.0,
            rationale="No data available",
        )

    out = df.sort_values("date").copy()
    out["ema_fast"] = ema(out["close"], fast_period)
    out["ema_slow"] = ema(out["close"], slow_period)
    out["rsi"] = rsi(out["close"], rsi_period)
    out["atr"] = atr(out, atr_period)
    out["avg_volume"] = out["volume"].rolling(vol_period).mean()
    out["adx"] = calculate_adx(out, rsi_period)

    last = out.iloc[-1]
    close = float(last["close"])
    ema_fast_v = float(last["ema_fast"])
    ema_slow_v = float(last["ema_slow"])
    rsi_v = float(last["rsi"])
    atr_v = float(last["atr"])
    avg_vol = float(last["avg_volume"]) if last["avg_volume"] > 0 else 1.0
    last_vol = float(last["volume"])
    vol_ratio = last_vol / avg_vol
    adx_v = float(last["adx"])

    # Structure detection
    structure_metrics = detect_market_structure(out)
    
    # Calculate indicators
    slope_v = calculate_slope(out["close"], 5)
    momentum_v = calculate_momentum_score(out["close"], 10)

    # Determine EMA Alignment
    if close > ema_fast_v > ema_slow_v:
        ema_align = "BULLISH"
    elif close < ema_fast_v < ema_slow_v:
        ema_align = "BEARISH"
    else:
        ema_align = "MIXED"

    # Define primary trend direction
    if ema_align == "BULLISH" and structure_metrics.trend == "BULLISH":
        trend_dir = "BULLISH"
    elif ema_align == "BEARISH" and structure_metrics.trend == "BEARISH":
        trend_dir = "BEARISH"
    elif ema_align == "BULLISH" and rsi_v > 55:
        trend_dir = "BULLISH"
    elif ema_align == "BEARISH" and rsi_v < 45:
        trend_dir = "BEARISH"
    else:
        trend_dir = "SIDEWAYS"

    # Calculate overall trend strength score
    # Scales ADX, EMA alignment, Slope, and Momentum (0.0 to 100.0)
    adx_contrib = min(40.0, (adx_v / 25.0) * 20.0 if adx_v < 25 else 20.0 + (min(25.0, adx_v - 25.0) / 25.0) * 20.0)
    
    if ema_align == trend_dir and trend_dir != "SIDEWAYS":
        ema_contrib = 30.0
    elif ema_align == "MIXED":
        ema_contrib = 10.0
    else:
        ema_contrib = 0.0

    slope_contrib = 15.0 if (trend_dir == "BULLISH" and slope_v > 0) or (trend_dir == "BEARISH" and slope_v < 0) else 0.0
    mom_contrib = 15.0 * min(1.0, abs(momentum_v) / 5.0) if trend_dir != "SIDEWAYS" and np.sign(momentum_v) == (1 if trend_dir == "BULLISH" else -1) else 0.0
    
    strength_score = float(round(adx_contrib + ema_contrib + slope_contrib + mom_contrib, 2))

    rationale = (
        f"Trend {trend_dir} (Strength: {strength_score}/100). "
        f"EMA Align: {ema_align}, ADX: {adx_v:.2f}, Slope: {slope_v:.2f}, "
        f"Momentum: {momentum_v:.2f}. "
        f"Structure: {structure_metrics.trend}."
    )

    # Buy and sell trigger levels
    recent_high = float(out["high"].tail(10).max())
    recent_low = float(out["low"].tail(10).min())
    trigger_buy = max(close, recent_high) + 0.5 * atr_v
    trigger_sell = min(close, recent_low) - 0.5 * atr_v

    return TrendSnapshot(
        symbol=symbol,
        spot=close,
        close=close,
        ema_fast=round(ema_fast_v, 2),
        ema_slow=round(ema_slow_v, 2),
        rsi=round(rsi_v, 2),
        atr=round(atr_v, 2),
        avg_volume=round(avg_vol, 2),
        last_volume=round(last_vol, 2),
        volume_ratio=round(vol_ratio, 2),
        trend=trend_dir,
        trigger_buy_above=round(trigger_buy, 2),
        trigger_sell_below=round(trigger_sell, 2),
        rationale=rationale,
        structure=structure_metrics.trend,
        higher_highs=structure_metrics.higher_highs,
        higher_lows=structure_metrics.higher_lows,
        lower_highs=structure_metrics.lower_highs,
        lower_lows=structure_metrics.lower_lows,
        ema_alignment=ema_align,
        adx=round(adx_v, 2),
        slope=round(slope_v, 2),
        momentum_score=round(momentum_v, 2),
        trend_strength_score=strength_score,
    )
