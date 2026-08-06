from __future__ import annotations

from typing import Mapping
import numpy as np
import pandas as pd

from src.models import (
    StructureMetrics,
    PriceLevelMetrics,
    RelativeStrengthMetrics,
    TimeframeMetrics,
    MultiTimeframeSummary,
)
from src.indicator_engine.indicators import ema, rsi, atr
from src.indicator_engine.structure import detect_market_structure


def _trend_to_score(trend: str) -> float:
    if trend == "BULLISH":
        return 1.0
    if trend == "BEARISH":
        return -1.0
    return 0.0


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def compute_timeframe_metrics(
    df: pd.DataFrame,
    timeframe: str,
    ema_fast_span: int,
    ema_slow_span: int,
    rsi_period: int,
    atr_period: int,
    vol_avg_period: int,
    breakout_vol_mult: float,
    entry_buffer_atr: float,
) -> TimeframeMetrics:
    out = df.sort_values("date").copy()
    out["ema_fast"] = ema(out["close"], ema_fast_span)
    out["ema_slow"] = ema(out["close"], ema_slow_span)
    out["rsi"] = rsi(out["close"], rsi_period)
    out["atr"] = atr(out, atr_period)
    out["avg_volume"] = out["volume"].rolling(vol_avg_period).mean()

    last = out.iloc[-1]
    close = _safe_float(last["close"])
    ema_fast_v = _safe_float(last["ema_fast"])
    ema_slow_v = _safe_float(last["ema_slow"])
    rsi_v = _safe_float(last["rsi"], 50.0)
    atr_v = _safe_float(last["atr"])
    avg_vol = _safe_float(last["avg_volume"])
    last_vol = _safe_float(last["volume"])
    vol_ratio = (last_vol / avg_vol) if avg_vol > 0 else 1.0

    structure = detect_market_structure(out)
    recent_high = _safe_float(out["high"].tail(10).max(), close)
    recent_low = _safe_float(out["low"].tail(10).min(), close)

    trigger_buy_above = max(close, recent_high) + entry_buffer_atr * atr_v
    trigger_sell_below = min(close, recent_low) - entry_buffer_atr * atr_v

    bullish_stack = close > ema_fast_v > ema_slow_v
    bearish_stack = close < ema_fast_v < ema_slow_v

    if rsi_v >= 75:
        trend = "SIDEWAYS"
        rationale = f"{timeframe} overbought RSI {rsi_v:.1f}."
    elif rsi_v <= 25:
        trend = "SIDEWAYS"
        rationale = f"{timeframe} oversold RSI {rsi_v:.1f}."
    elif structure.trend == "BULLISH" and bullish_stack and rsi_v >= 52 and vol_ratio >= breakout_vol_mult:
        trend = "BULLISH"
        rationale = f"{timeframe} bullish: EMA stack, RSI {rsi_v:.1f}, volume ratio {vol_ratio:.2f}, {structure.rationale}"
    elif structure.trend == "BEARISH" and bearish_stack and rsi_v <= 48 and vol_ratio >= breakout_vol_mult:
        trend = "BEARISH"
        rationale = f"{timeframe} bearish: EMA stack, RSI {rsi_v:.1f}, volume ratio {vol_ratio:.2f}, {structure.rationale}"
    elif bullish_stack and rsi_v >= 55:
        trend = "BULLISH"
        rationale = f"{timeframe} bullish alignment with RSI {rsi_v:.1f}; {structure.rationale}"
    elif bearish_stack and rsi_v <= 45:
        trend = "BEARISH"
        rationale = f"{timeframe} bearish alignment with RSI {rsi_v:.1f}; {structure.rationale}"
    elif structure.trend == "BULLISH" and close >= ema_slow_v and rsi_v >= 50:
        trend = "BULLISH"
        rationale = f"{timeframe} structure-led bullish continuation; {structure.rationale}"
    elif structure.trend == "BEARISH" and close <= ema_slow_v and rsi_v <= 50:
        trend = "BEARISH"
        rationale = f"{timeframe} structure-led bearish continuation; {structure.rationale}"
    else:
        trend = "SIDEWAYS"
        rationale = f"{timeframe} mixed: RSI {rsi_v:.1f}, volume ratio {vol_ratio:.2f}, {structure.rationale}"

    return TimeframeMetrics(
        timeframe=timeframe,
        close=round(close, 2),
        ema_fast=round(ema_fast_v, 2),
        ema_slow=round(ema_slow_v, 2),
        rsi=round(rsi_v, 2),
        atr=round(atr_v, 2),
        avg_volume=round(avg_vol, 2),
        last_volume=round(last_vol, 2),
        volume_ratio=round(vol_ratio, 2),
        trend=trend,
        structure=structure,
        trigger_buy_above=round(trigger_buy_above, 2),
        trigger_sell_below=round(trigger_sell_below, 2),
        rationale=rationale,
    )


def compute_price_levels(intraday_df: pd.DataFrame, daily_df: pd.DataFrame) -> PriceLevelMetrics:
    intraday_sorted = intraday_df.sort_values("date").copy()
    daily_sorted = daily_df.sort_values("date").copy()

    if intraday_sorted.empty and daily_sorted.empty:
        return PriceLevelMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    if intraday_sorted.empty:
        latest_close = _safe_float(daily_sorted.iloc[-1]["close"]) if not daily_sorted.empty else 0.0
        return PriceLevelMetrics(latest_close, latest_close, latest_close, latest_close, latest_close, latest_close)

    intraday_sorted["session_date"] = intraday_sorted["date"].dt.date
    latest_session = intraday_sorted["session_date"].max()
    latest_intraday = intraday_sorted[intraday_sorted["session_date"] == latest_session].copy()

    typical_price = (latest_intraday["high"] + latest_intraday["low"] + latest_intraday["close"]) / 3.0
    cumulative_volume = latest_intraday["volume"].replace(0, np.nan).cumsum()
    vwap_series = (typical_price * latest_intraday["volume"]).cumsum() / cumulative_volume
    intraday_vwap = _safe_float(vwap_series.iloc[-1], _safe_float(latest_intraday.iloc[-1]["close"]))

    if daily_sorted.empty:
        daily_sorted = (
            intraday_sorted.groupby("session_date", as_index=False)
            .agg(
                high=("high", "max"),
                low=("low", "min"),
                close=("close", "last"),
            )
            .rename(columns={"session_date": "date"})
        )
        daily_sorted["date"] = pd.to_datetime(daily_sorted["date"])

    prev_bar = daily_sorted.iloc[-2] if len(daily_sorted) >= 2 else daily_sorted.iloc[-1]
    weekly_window = daily_sorted.tail(min(5, len(daily_sorted)))

    return PriceLevelMetrics(
        intraday_vwap=round(intraday_vwap, 2),
        prev_day_high=round(_safe_float(prev_bar["high"]), 2),
        prev_day_low=round(_safe_float(prev_bar["low"]), 2),
        prev_day_close=round(_safe_float(prev_bar["close"]), 2),
        weekly_high=round(_safe_float(weekly_window["high"].max()), 2),
        weekly_low=round(_safe_float(weekly_window["low"].min()), 2),
    )


def summarize_multi_timeframe(
    timeframe_metrics: Mapping[str, TimeframeMetrics],
    price_levels: PriceLevelMetrics,
    relative_strength: RelativeStrengthMetrics,
    market_regime_label: str,
) -> MultiTimeframeSummary:
    daily = timeframe_metrics.get("day")
    hourly = timeframe_metrics.get("60minute")
    fifteen = timeframe_metrics.get("15minute")
    five = timeframe_metrics.get("5minute")

    weighted_score = (
        _trend_to_score(daily.trend if daily else "SIDEWAYS") * 0.45
        + _trend_to_score(hourly.trend if hourly else "SIDEWAYS") * 0.35
        + _trend_to_score(fifteen.trend if fifteen else "SIDEWAYS") * 0.20
    )

    if weighted_score >= 0.30:
        overall_trend = "BULLISH"
    elif weighted_score <= -0.30:
        overall_trend = "BEARISH"
    else:
        overall_trend = "SIDEWAYS"

    matching_weight = 0.0
    if overall_trend != "SIDEWAYS":
        for weight, metrics in zip([0.45, 0.35, 0.20], [daily, hourly, fifteen]):
            if metrics is not None and metrics.trend == overall_trend:
                matching_weight += weight
    alignment_score = round(
        float(
            np.clip(
                matching_weight
                + (
                    0.10
                    if five
                    and five.trend == overall_trend
                    and overall_trend != "SIDEWAYS"
                    else 0.0
                ),
                0.0,
                1.0,
            )
        ),
        2,
    )

    if daily is not None:
        structure = daily.structure
    elif hourly is not None:
        structure = hourly.structure
    elif fifteen is not None:
        structure = fifteen.structure
    else:
        structure = StructureMetrics("SIDEWAYS", 0, 0, 0, 0, "No higher-timeframe structure.")

    structure_score = 0.0
    if overall_trend != "SIDEWAYS" and structure.trend == overall_trend:
        structure_score += 0.08
    elif (
        overall_trend != "SIDEWAYS"
        and structure.trend != "SIDEWAYS"
        and structure.trend != overall_trend
    ):
        structure_score -= 0.06

    price_level_score = 0.0
    latest_close = (
        five.close
        if five is not None
        else (fifteen.close if fifteen is not None else 0.0)
    )
    if overall_trend == "BULLISH":
        if latest_close >= price_levels.intraday_vwap:
            price_level_score += 0.05
        if latest_close >= price_levels.prev_day_close:
            price_level_score += 0.03
        if latest_close >= price_levels.prev_day_high:
            price_level_score += 0.05
        elif latest_close <= price_levels.prev_day_low:
            price_level_score -= 0.05
    elif overall_trend == "BEARISH":
        if latest_close <= price_levels.intraday_vwap:
            price_level_score += 0.05
        if latest_close <= price_levels.prev_day_close:
            price_level_score += 0.03
        if latest_close <= price_levels.prev_day_low:
            price_level_score += 0.05
        elif latest_close >= price_levels.prev_day_high:
            price_level_score -= 0.05

    regime_score = 0.0
    if market_regime_label == "TRENDING_BULLISH" and overall_trend == "BULLISH":
        regime_score += 0.08
    elif market_regime_label == "TRENDING_BEARISH" and overall_trend == "BEARISH":
        regime_score += 0.08
    elif market_regime_label == "SIDEWAYS" and overall_trend != "SIDEWAYS":
        regime_score -= 0.04
    elif market_regime_label == "HIGH_VOLATILITY":
        regime_score -= 0.06
    elif market_regime_label == "LOW_VOLATILITY" and overall_trend != "SIDEWAYS":
        regime_score -= 0.03

    if overall_trend != "SIDEWAYS" and five is not None and five.trend != overall_trend:
        regime_score -= 0.05

    alignment_component = 0.0
    if alignment_score >= 0.90:
        alignment_component += 0.18
    elif alignment_score >= 0.70:
        alignment_component += 0.10
    elif alignment_score <= 0.35:
        alignment_component -= 0.08

    advanced_confidence_boost = round(
        alignment_component
        + structure_score
        + price_level_score
        + relative_strength.score
        + regime_score,
        2,
    )

    rationale = (
        f"MTF {overall_trend}: day/hour/15m/5m = "
        f"{daily.trend if daily else 'NA'}/{hourly.trend if hourly else 'NA'}/"
        f"{fifteen.trend if fifteen else 'NA'}/{five.trend if five else 'NA'}; "
        f"alignment {alignment_score:.2f}; structure {structure.trend}; "
        f"price score {price_level_score:+.2f}; RS {relative_strength.score:+.2f}; "
        f"regime score {regime_score:+.2f}."
    )

    return MultiTimeframeSummary(
        overall_trend=overall_trend,
        daily_trend=daily.trend if daily else "SIDEWAYS",
        hourly_trend=hourly.trend if hourly else "SIDEWAYS",
        fifteen_min_trend=fifteen.trend if fifteen else "SIDEWAYS",
        five_min_trend=five.trend if five else "SIDEWAYS",
        structure=structure,
        price_levels=price_levels,
        relative_strength=relative_strength,
        timeframe_alignment_score=alignment_score,
        price_level_score=round(price_level_score, 2),
        regime_score=round(regime_score, 2),
        advanced_confidence_boost=advanced_confidence_boost,
        rationale=rationale,
        timeframes=dict(timeframe_metrics),
    )
