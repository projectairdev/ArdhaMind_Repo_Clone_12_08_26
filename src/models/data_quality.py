from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, List, Optional


class FreshnessStatus(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    MARKET_CLOSED = "market_closed"


class QualityStatus(str, Enum):
    VALID = "valid"
    PARTIAL = "partial"
    INVALID = "invalid"
    UNVERIFIED = "unverified"


class ValueClassification(str, Enum):
    LIVE = "live"
    DELAYED = "delayed"
    HISTORICAL = "historical"
    CALCULATED = "calculated"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


class SectionStatus(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    MARKET_CLOSED = "market_closed"


@dataclass(frozen=True)
class ValueMetadata:
    source: str
    instrument: Optional[str] = None
    observed_at: Optional[str] = None
    received_at: Optional[str] = None
    generated_at: Optional[str] = None
    age_seconds: Optional[float] = None
    freshness_status: FreshnessStatus = FreshnessStatus.UNAVAILABLE
    quality_status: QualityStatus = QualityStatus.UNVERIFIED
    value_classification: ValueClassification = ValueClassification.UNAVAILABLE
    calculation_method: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
