from __future__ import annotations

from typing import Mapping
from src.models import PriceLevelMetrics, RelativeStrengthMetrics, RegimeMetrics, TimeframeMetrics
from src.indicator_engine.volatility import compute_volatility_score
from src.indicator_engine.trend import summarize_multi_timeframe


def detect_market_regime(
    timeframe_metrics: Mapping[str, TimeframeMetrics],
    market_breadth: float = 0.0,
    snapshot_score: float = 0.0,
    benchmark_return_pct: float = 0.0,
) -> RegimeMetrics:
    summary = summarize_multi_timeframe(
        timeframe_metrics=timeframe_metrics,
        price_levels=PriceLevelMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        relative_strength=RelativeStrengthMetrics(
            0.0, benchmark_return_pct, 0.0, 0.0, 0.0, "Benchmark-only regime analysis."
        ),
        market_regime_label="SIDEWAYS",
    )

    volatility_score = compute_volatility_score(timeframe_metrics)

    def _trend_to_score(trend: str) -> float:
        if trend == "BULLISH":
            return 1.0
        if trend == "BEARISH":
            return -1.0
        return 0.0

    trend_score = round(
        _trend_to_score(summary.daily_trend) * 0.45
        + _trend_to_score(summary.hourly_trend) * 0.35
        + _trend_to_score(summary.fifteen_min_trend) * 0.20,
        2,
    )
    overall_bias = summary.overall_trend

    if volatility_score >= 1.8 and abs(trend_score) < 0.55:
        regime_label = "HIGH_VOLATILITY"
    elif volatility_score <= 0.6 and abs(trend_score) < 0.25:
        regime_label = "LOW_VOLATILITY"
    elif trend_score >= 0.35 and market_breadth >= -0.05:
        regime_label = "TRENDING_BULLISH"
    elif trend_score <= -0.35 and market_breadth <= 0.05:
        regime_label = "TRENDING_BEARISH"
    else:
        regime_label = "SIDEWAYS"

    rationale = (
        f"Trend score {trend_score:+.2f}, breadth {market_breadth:+.2f}, "
        f"snapshot {snapshot_score:+.2f}, volatility {volatility_score:.2f}%."
    )

    return RegimeMetrics(
        overall_bias=overall_bias,
        regime_label=regime_label,
        trend_score=trend_score,
        volatility_score=volatility_score,
        benchmark_return_pct=benchmark_return_pct,
        rationale=rationale,
    )


def classify_market_regime(
    trend_snapshot: any,
    vol_snapshot: any,
) -> str:
    """
    Classifies the NIFTY market regime based on trend and volatility snapshots.
    Output is strictly one of:
    - TRENDING
    - RANGING
    - BREAKOUT
    - REVERSAL
    - HIGH VOLATILITY
    - LOW VOLATILITY
    """
    # 1. REVERSAL: Extreme RSI suggesting overextended move
    if trend_snapshot.rsi >= 75.0 or trend_snapshot.rsi <= 25.0:
        return "REVERSAL"

    # 2. BREAKOUT: High volume expansion and breaking yesterday's extreme levels
    if trend_snapshot.volume_ratio >= 1.5 and (
        trend_snapshot.close > trend_snapshot.prev_day_high or 
        trend_snapshot.close < trend_snapshot.prev_day_low
    ):
        return "BREAKOUT"

    # 3. HIGH VOLATILITY: Highly elevated ATR percentile
    if vol_snapshot.classification == "HIGH" or vol_snapshot.is_expanded:
        return "HIGH VOLATILITY"

    # 4. TRENDING: High ADX and established direction
    if trend_snapshot.adx >= 25.0 and trend_snapshot.trend != "SIDEWAYS":
        return "TRENDING"

    # 5. LOW VOLATILITY: Volatility compression
    if vol_snapshot.classification == "LOW" or vol_snapshot.is_compressed:
        return "LOW VOLATILITY"

    # 6. RANGING: Default state when no strong trend or volatility expansion exists
    return "RANGING"

