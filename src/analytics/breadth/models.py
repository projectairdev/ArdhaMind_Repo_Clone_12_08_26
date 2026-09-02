from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from src.market_data.models.quality_enums import DataQualityStatus


class DivergenceType(str, Enum):
    NONE = "NONE"
    BULLISH_DIVERGENCE = "BULLISH_DIVERGENCE"  # Index down but breadth expanding up
    BEARISH_DIVERGENCE = "BEARISH_DIVERGENCE"  # Index up but breadth narrowing down


class LeadershipBias(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    MIXED = "MIXED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ConstituentState:
    symbol: str
    last_price: float
    change_pct: float
    weight: float = 1.0
    is_fresh: bool = True


@dataclass(frozen=True)
class MarketBreadthSummary:
    """Deterministic market breadth computed directly from constituent states."""
    total_constituents: int
    observed_constituents: int
    advances: int
    declines: int
    unchanged: int
    advance_decline_ratio: float
    advance_pct: float
    weighted_breadth_score: float  # -1.0 (all down) to +1.0 (all up)
    coverage_pct: float
    quality: DataQualityStatus = DataQualityStatus.VALID


@dataclass(frozen=True)
class BreadthDivergenceContext:
    divergence: DivergenceType
    index_change_pct: float
    breadth_advance_pct: float
    note: str


@dataclass(frozen=True)
class SectorParticipationContext:
    sector_changes: Dict[str, float]
    leading_sectors: List[str]
    lagging_sectors: List[str]
    participation_score: float  # -1.0 to +1.0
    quality: DataQualityStatus = DataQualityStatus.VALID


@dataclass(frozen=True)
class HeavyweightLeadershipContext:
    heavyweight_symbols: List[str]
    advances: int
    declines: int
    leadership_bias: LeadershipBias
    contribution_score: float  # -1.0 to +1.0
    quality: DataQualityStatus = DataQualityStatus.VALID


@dataclass(frozen=True)
class MarketBreadthContext:
    breadth_summary: MarketBreadthSummary
    divergence: BreadthDivergenceContext
    sector_context: SectorParticipationContext
    leadership: HeavyweightLeadershipContext
    quality: DataQualityStatus = DataQualityStatus.VALID
