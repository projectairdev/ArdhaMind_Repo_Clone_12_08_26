from __future__ import annotations

from typing import Optional
import pandas as pd
from src.models import TrendSnapshot, MarketRegime
from src.data_engine.instruments import get_symbol_sector


def calc_confidence(
    trend: TrendSnapshot,
    market_regime: MarketRegime,
    opt_type: str,
    option_row: Optional[pd.Series] = None,
) -> float:
    score = 0.0

    if trend.trend == "BULLISH" and opt_type == "CE":
        score += 0.30
    elif trend.trend == "BEARISH" and opt_type == "PE":
        score += 0.30

    if market_regime.overall_bias == trend.trend:
        score += 0.20
    elif market_regime.overall_bias == "SIDEWAYS":
        score += 0.05

    if 55 <= trend.rsi <= 68 and opt_type == "CE":
        score += 0.15
    if 32 <= trend.rsi <= 45 and opt_type == "PE":
        score += 0.15

    if trend.volume_ratio >= 1.5:
        score += 0.20
    elif trend.volume_ratio >= 1.2:
        score += 0.12
    elif trend.volume_ratio >= 1.0:
        score += 0.06

    if 25 < trend.rsi < 75:
        score += 0.10

    sector_strength = float(market_regime.sector_scores.get(get_symbol_sector(trend.symbol), 0.0))
    if trend.trend == "BULLISH" and sector_strength > 0:
        score += min(0.10, sector_strength / 20.0)
    elif trend.trend == "BEARISH" and sector_strength < 0:
        score += min(0.10, abs(sector_strength) / 20.0)

    if option_row is not None:
        spread_pct = float(option_row.get("spread_pct", 99.0) or 99.0)
        option_oi = float(option_row.get("option_oi", 0.0) or 0.0)
        option_volume = float(option_row.get("option_volume", 0.0) or 0.0)

        if spread_pct <= 1.0:
            score += 0.08
        elif spread_pct <= 2.0:
            score += 0.05
        elif spread_pct >= 5.0:
            score -= 0.08

        if option_oi >= 100000:
            score += 0.06
        elif option_oi < 5000:
            score -= 0.05

        if option_volume >= 10000:
            score += 0.05
        elif option_volume < 500:
            score -= 0.05

    score += getattr(trend, "advanced_confidence_boost", 0.0)

    return round(min(score, 0.99), 2)


def calc_stock_confidence(trend: TrendSnapshot, market_regime: MarketRegime) -> float:
    score = 0.0

    if trend.trend in {"BULLISH", "BEARISH"}:
        score += 0.30

    if market_regime.overall_bias == trend.trend:
        score += 0.20
    elif market_regime.overall_bias == "SIDEWAYS":
        score += 0.05

    if trend.trend == "BULLISH" and 55 <= trend.rsi <= 68:
        score += 0.15
    elif trend.trend == "BEARISH" and 32 <= trend.rsi <= 45:
        score += 0.15

    if trend.volume_ratio >= 1.5:
        score += 0.20
    elif trend.volume_ratio >= 1.2:
        score += 0.12
    elif trend.volume_ratio >= 1.0:
        score += 0.06

    if 25 < trend.rsi < 75:
        score += 0.10

    return round(min(score, 0.99), 2)
