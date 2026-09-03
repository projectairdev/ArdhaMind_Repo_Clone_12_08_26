from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from src.market_data.models.quality_enums import DataQualityStatus


class TrendDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"
    UNAVAILABLE = "UNAVAILABLE"


class GapType(str, Enum):
    GAP_UP = "GAP_UP"
    GAP_DOWN = "GAP_DOWN"
    FLAT = "FLAT"


class BreakoutStatus(str, Enum):
    NONE = "NONE"
    BREAKOUT_UP = "BREAKOUT_UP"
    BREAKDOWN = "BREAKDOWN"
    RETESTING = "RETESTING"
    FAILED_BREAKOUT = "FAILED_BREAKOUT"


@dataclass(frozen=True)
class LevelInfo:
    price: float
    level_type: str  # "SUPPORT" | "RESISTANCE" | "PIVOT"
    source: str      # "PDH" | "PDL" | "PDC" | "ORH" | "ORL" | "SWING_HIGH" | "SWING_LOW" | "ROUND_NUMBER"
    strength: float  # 0.0 to 1.0
    touch_count: int = 1


@dataclass(frozen=True)
class OpeningRangeContext:
    duration_minutes: int
    high: Optional[float]
    low: Optional[float]
    range_size: Optional[float]
    is_established: bool
    status: str  # "INSIDE" | "ABOVE" | "BELOW" | "FORMING"
    breakout_direction: Optional[str] = None  # "UP" | "DOWN" | "NONE"


@dataclass(frozen=True)
class GapContext:
    gap_type: GapType
    gap_points: float
    gap_pct: float
    is_filled: bool
    fill_pct: float
    previous_close: float
    open_price: float


@dataclass(frozen=True)
class SwingPoint:
    timestamp: datetime
    price: float
    swing_type: str  # "HIGH" | "LOW"
    strength: int = 1


@dataclass(frozen=True)
class BreakoutContext:
    status: BreakoutStatus
    level_price: Optional[float]
    level_source: Optional[str]
    distance_pct: float
    retest_confirmed: bool = False


@dataclass(frozen=True)
class CompressionContext:
    is_compressing: bool
    compression_ratio: float  # Current range / ATR or bandwidth
    bandwidth: Optional[float] = None


@dataclass(frozen=True)
class ATRContext:
    atr_value: float
    current_range: float
    expansion_ratio: float  # current_range / atr_value


@dataclass(frozen=True)
class VWAPContext:
    """Volume Weighted Average Price - strictly requires real volume."""
    vwap: float
    current_price: float
    distance_points: float
    distance_pct: float
    price_position: str  # "ABOVE" | "BELOW" | "AT_VWAP"
    cumulative_volume: int
    quality: DataQualityStatus = DataQualityStatus.VALID


@dataclass(frozen=True)
class TWAPContext:
    """Time Weighted Average Price - time-weighted typical price."""
    twap: float
    current_price: float
    distance_points: float
    distance_pct: float
    price_position: str  # "ABOVE" | "BELOW" | "AT_TWAP"
    quality: DataQualityStatus = DataQualityStatus.VALID


@dataclass(frozen=True)
class PriceStructureContext:
    """Immutable, comprehensive price structure analysis for NIFTY."""
    last_price: float
    trend: TrendDirection
    vwap_context: Optional[VWAPContext]
    twap_context: Optional[TWAPContext]
    opening_range: OpeningRangeContext
    gap_context: GapContext
    support_levels: List[LevelInfo]
    resistance_levels: List[LevelInfo]
    swings: List[SwingPoint]
    breakout: BreakoutContext
    compression: CompressionContext
    atr: ATRContext
    quality: DataQualityStatus = DataQualityStatus.VALID
