from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StructureMetrics:
    trend: str
    higher_highs: int
    higher_lows: int
    lower_highs: int
    lower_lows: int
    rationale: str


@dataclass
class PriceLevelMetrics:
    intraday_vwap: float
    prev_day_high: float
    prev_day_low: float
    prev_day_close: float
    weekly_high: float
    weekly_low: float


@dataclass
class RelativeStrengthMetrics:
    stock_return_pct: float
    benchmark_return_pct: float
    stock_vs_nifty_pct: float
    sector_vs_nifty_pct: float
    score: float
    rationale: str


@dataclass
class TimeframeMetrics:
    timeframe: str
    close: float
    ema_fast: float
    ema_slow: float
    rsi: float
    atr: float
    avg_volume: float
    last_volume: float
    volume_ratio: float
    trend: str
    structure: StructureMetrics
    trigger_buy_above: float
    trigger_sell_below: float
    rationale: str


@dataclass
class MultiTimeframeSummary:
    overall_trend: str
    daily_trend: str
    hourly_trend: str
    fifteen_min_trend: str
    five_min_trend: str
    structure: StructureMetrics
    price_levels: PriceLevelMetrics
    relative_strength: RelativeStrengthMetrics
    timeframe_alignment_score: float
    price_level_score: float
    regime_score: float
    advanced_confidence_boost: float
    rationale: str
    timeframes: Dict[str, TimeframeMetrics] = field(default_factory=dict)


@dataclass
class RegimeMetrics:
    overall_bias: str
    regime_label: str
    trend_score: float
    volatility_score: float
    benchmark_return_pct: float
    rationale: str


@dataclass
class MarketRegime:
    nifty_trend: str
    banknifty_trend: str
    overall_bias: str
    scanned_at: str
    regime_score: float
    market_breadth: float
    sector_scores: Dict[str, float]
    strong_sectors: List[str]
    weak_sectors: List[str]
    rationale: str
    regime_label: str = "SIDEWAYS"
    volatility_score: float = 0.0
    benchmark_return_pct: float = 0.0
    sector_relative_strengths: Dict[str, float] = field(default_factory=dict)


@dataclass
class TrendSnapshot:
    symbol: str
    spot: float
    close: float
    ema_fast: float
    ema_slow: float
    rsi: float
    atr: float
    avg_volume: float
    last_volume: float
    volume_ratio: float
    trend: str
    trigger_buy_above: float
    trigger_sell_below: float
    rationale: str
    structure: str = "SIDEWAYS"
    higher_highs: int = 0
    higher_lows: int = 0
    lower_highs: int = 0
    lower_lows: int = 0
    daily_trend: str = "SIDEWAYS"
    hourly_trend: str = "SIDEWAYS"
    fifteen_min_trend: str = "SIDEWAYS"
    five_min_trend: str = "SIDEWAYS"
    timeframe_alignment_score: float = 0.0
    advanced_confidence_boost: float = 0.0
    price_level_score: float = 0.0
    relative_strength_score: float = 0.0
    regime_score_adjustment: float = 0.0
    strategy_regime: str = "SIDEWAYS"
    intraday_vwap: float = 0.0
    prev_day_high: float = 0.0
    prev_day_low: float = 0.0
    prev_day_close: float = 0.0
    weekly_high: float = 0.0
    weekly_low: float = 0.0
    stock_vs_nifty_return: float = 0.0
    sector_vs_nifty_return: float = 0.0
    ema_alignment: str = "MIXED"
    adx: float = 0.0
    slope: float = 0.0
    momentum_score: float = 0.0
    trend_strength_score: float = 0.0

