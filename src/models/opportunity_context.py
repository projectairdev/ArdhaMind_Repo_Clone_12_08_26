from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass(frozen=True)
class OpportunityClassification:
    value: str  # "EXCELLENT", "GOOD", "WATCHLIST", "WAIT", "POOR", "AVOID"
    description: str


@dataclass(frozen=True)
class DirectionalBias:
    value: str  # "BULLISH", "BEARISH", "SIDEWAYS", "NEUTRAL"
    description: str


@dataclass(frozen=True)
class OpportunityStrength:
    imbalance_magnitude: float  # Physical measure of spot vs S/R and option OI imbalance
    trend_force: float          # Dynamic force based on ADX and Slope
    option_force: float         # Option PCR & OI shift imbalance force
    liquidity_force: float      # Liquidity stability measure
    overall_strength: float     # Aggregated physical strength of the imbalance (0-100)


@dataclass(frozen=True)
class OpportunityWarning:
    warning_type: str  # "RESISTANCE_PROXIMITY", "SUPPORT_PROXIMITY", "LOW_LIQUIDITY", "HIGH_IV", "EXTREME_VOLATILITY", "EXPIRY_RISK", "GAP_RISK", "WEAK_OPTION_CONFIRMATION", "CONFLICTING_MARKET_STRUCTURE"
    message: str
    severity: str      # "LOW", "MEDIUM", "HIGH"


@dataclass(frozen=True)
class InvalidationFactor:
    factor_type: str  # "LOSS_OF_TREND_ALIGNMENT", "LIQUIDITY_DETERIORATION", "VOLATILITY_REGIME_CHANGE", "SUPPORT_BREAK", "RESISTANCE_BREAK", "OPTION_STRUCTURE_COLLAPSE", "SESSION_CHANGE", "EXPIRY_TRANSITION"
    is_invalidated: bool
    reason: str


@dataclass(frozen=True)
class OpportunityProfile:
    opportunity_type: str            # "TREND_CONTINUATION", "BREAKOUT", "MEAN_REVERSION", "RANGE_BOUND", "SCALPING", "EXPIRY_DAY_PLAY", "NONE"
    momentum_suitability: str        # "SUITABLE", "UNSUITABLE", "NEUTRAL"
    breakout_suitability: str        # "SUITABLE", "UNSUITABLE", "NEUTRAL"
    reversal_suitability: str        # "SUITABLE", "UNSUITABLE", "NEUTRAL"
    range_suitability: str           # "SUITABLE", "UNSUITABLE", "NEUTRAL"
    scalping_suitability: str        # "SUITABLE", "UNSUITABLE", "NEUTRAL"
    trend_following_suitability: str # "SUITABLE", "UNSUITABLE", "NEUTRAL"
    expiry_suitability: str          # "SUITABLE", "UNSUITABLE", "NEUTRAL"
    suitability_reasons: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class MarketBreadthContext:
    advance_decline_ratio: Optional[float] = None
    sector_strength: Optional[Dict[str, float]] = None
    bank_nifty_confirmation: Optional[bool] = None
    fin_nifty_confirmation: Optional[bool] = None
    large_cap_participation: Optional[float] = None
    mid_cap_participation: Optional[float] = None
    is_available: bool = False


@dataclass(frozen=True)
class GlobalContext:
    gift_nifty_status: Optional[str] = None  # "POSITIVE", "NEGATIVE", "FLAT"
    us_markets_status: Optional[str] = None  # "BULLISH", "BEARISH", "NEUTRAL"
    european_markets_status: Optional[str] = None
    asian_markets_status: Optional[str] = None
    vix_trend: Optional[str] = None          # "RISING", "FALLING", "STABLE"
    usdinr_trend: Optional[str] = None
    crude_oil_trend: Optional[str] = None
    is_available: bool = False


@dataclass(frozen=True)
class OpportunityContext:
    classification: OpportunityClassification
    profile: OpportunityProfile
    strength: OpportunityStrength
    directional_bias: DirectionalBias
    warnings: List[OpportunityWarning]
    invalidation_factors: List[InvalidationFactor]
    has_opportunity: bool
    timestamp: str
    breadth: MarketBreadthContext = field(default_factory=MarketBreadthContext)
    global_ctx: GlobalContext = field(default_factory=GlobalContext)
    schema_version: str = "1.0"
    pipeline_version: str = "1.0"
