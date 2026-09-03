from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from src.market_data.models.quality_enums import DataQualityStatus


class MarketRegime(str, Enum):
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    COMPRESSION = "COMPRESSION"
    BREAKOUT_ATTEMPT = "BREAKOUT_ATTEMPT"
    CONFLICTED = "CONFLICTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class RegimeContext:
    regime: MarketRegime
    confidence_score: float  # 0.0 to 1.0
    primary_factors: List[str]
    caution_factors: List[str]
    quality: DataQualityStatus = DataQualityStatus.VALID
