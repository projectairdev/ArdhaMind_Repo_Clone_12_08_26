from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from src.market_data.models.quality_enums import DataQualityStatus


class BuildupType(str, Enum):
    FRESH_CALL_WRITING = "FRESH_CALL_WRITING"
    FRESH_PUT_WRITING = "FRESH_PUT_WRITING"
    CALL_UNWINDING = "CALL_UNWINDING"
    PUT_UNWINDING = "PUT_UNWINDING"
    LONG_BUILDUP = "LONG_BUILDUP"
    SHORT_BUILDUP = "SHORT_BUILDUP"
    SHORT_COVERING = "SHORT_COVERING"
    LONG_UNWINDING = "LONG_UNWINDING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class GreeksProvenance(str, Enum):
    PROVIDER_SUPPLIED = "PROVIDER_SUPPLIED"
    ARDHA_DERIVED = "ARDHA_DERIVED"
    UNAVAILABLE = "UNAVAILABLE"


class OptionLiquidityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNAVAILABLE = "UNAVAILABLE"


class StrikeStrengthClass(str, Enum):
    STRONG_CALL_RESISTANCE = "STRONG_CALL_RESISTANCE"
    STRONG_PUT_SUPPORT = "STRONG_PUT_SUPPORT"
    BULLISH_STRIKE_CONFIRMATION = "BULLISH_STRIKE_CONFIRMATION"
    BEARISH_STRIKE_CONFIRMATION = "BEARISH_STRIKE_CONFIRMATION"
    WEAK = "WEAK"
    MIXED = "MIXED"
    UNAVAILABLE = "UNAVAILABLE"


class OptionsConfirmationBias(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    CONFLICTED = "CONFLICTED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class GreeksContext:
    iv: Optional[float]
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]
    provenance: GreeksProvenance = GreeksProvenance.PROVIDER_SUPPLIED


@dataclass(frozen=True)
class StrikeIntelligence:
    """Detailed intelligence per strike level."""
    strike: float
    call_buildup: BuildupType
    put_buildup: BuildupType
    call_oi: int
    put_oi: int
    call_oi_change: Optional[int]
    put_oi_change: Optional[int]
    call_volume: int
    put_volume: int
    call_greeks: Optional[GreeksContext]
    put_greeks: Optional[GreeksContext]
    liquidity: OptionLiquidityLevel
    strike_bias: StrikeStrengthClass
    strength_score: float  # -1.0 (strong bearish/resistance) to +1.0 (strong bullish/support)


@dataclass(frozen=True)
class OptionsConfirmationContext:
    """Authoritative options intelligence confirmation."""
    bias: OptionsConfirmationBias
    confirmation_score: float  # -1.0 to +1.0
    atm_strike: float
    pcr: float
    max_pain: float
    call_wall: float
    put_wall: float
    strike_universe: List[StrikeIntelligence]
    supporting_factors: List[str]
    contradicting_factors: List[str]
    quality: DataQualityStatus = DataQualityStatus.VALID
