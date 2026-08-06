from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrendScore:
    trend_strength_score: float
    ema_alignment_score: float
    adx_score: float
    slope_score: float
    momentum_score: float
    overall_trend_score: float


@dataclass(frozen=True)
class OptionScore:
    pcr_score: float
    max_pain_score: float
    oi_structure_score: float
    oi_buildup_score: float
    liquidity_score: float
    iv_score: float
    expected_move_score: float
    overall_option_score: float


@dataclass(frozen=True)
class VolatilityScore:
    atr_score: float
    compression_score: float
    expansion_score: float
    iv_env_score: float
    expected_move_score: float
    overall_volatility_score: float


@dataclass(frozen=True)
class LiquidityScore:
    spread_score: float
    volume_score: float
    oi_score: float
    tradability_score: float
    overall_liquidity_score: float


@dataclass(frozen=True)
class SessionScore:
    session_type_score: float
    is_tradable_score: float
    overall_session_score: float


@dataclass(frozen=True)
class ExpiryScore:
    days_remaining_score: float
    expiry_type_score: float
    classification_score: float
    overall_expiry_score: float


@dataclass(frozen=True)
class ConfluenceScore:
    trend_confluence_score: float
    support_resistance_score: float
    option_bias_score: float
    volatility_score: float
    liquidity_score: float
    overall_confluence_score: float


@dataclass(frozen=True)
class MarketScore:
    trend: TrendScore
    options: OptionScore
    volatility: VolatilityScore
    liquidity: LiquidityScore
    session: SessionScore
    expiry: ExpiryScore
    confluence: ConfluenceScore
    overall_score: float
    letter_grade: str
    classification: str
    timestamp: str
    schema_version: str = "1.0"
    pipeline_version: str = "1.0"
