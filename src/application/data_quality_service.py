from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any, Optional

from src.models.data_quality import (
    FreshnessStatus, QualityStatus, ValueClassification, ValueMetadata,
)


class DataQualityService:
    """Applies the approved Phase 2 freshness policy without inventing values."""

    THRESHOLDS = {
        "nifty_spot": (5, 15),
        "option_quote": (10, 30),
        "option_aggregate": (15, 45),
        "breadth": (15, 45),
        "india_vix": (30, 90),
        "broker_account": (30, 120),
        "news": (600, 1800),
    }

    @staticmethod
    def parse_time(value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            result = value
        elif isinstance(value, str) and value:
            try:
                result = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        else:
            return None
        return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)

    @classmethod
    def classify(cls, kind: str, observed_at: Any, *, now: Optional[datetime] = None,
                 market_closed: bool = False, available: bool = True) -> tuple[FreshnessStatus, Optional[float]]:
        if not available:
            return FreshnessStatus.UNAVAILABLE, None
        observed = cls.parse_time(observed_at)
        if observed is None:
            return FreshnessStatus.BLOCKED, None
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        age = max(0.0, (current - observed).total_seconds())
        if market_closed:
            return FreshnessStatus.MARKET_CLOSED, age
        fresh, blocked = cls.THRESHOLDS[kind]
        if age <= fresh:
            return FreshnessStatus.FRESH, age
        if age <= blocked:
            return FreshnessStatus.STALE, age
        return FreshnessStatus.BLOCKED, age

    @classmethod
    def historical(cls, observed_at: Any, interval_seconds: int, *, now: Optional[datetime] = None,
                   market_closed: bool = False) -> tuple[FreshnessStatus, Optional[float]]:
        observed = cls.parse_time(observed_at)
        if observed is None or interval_seconds <= 0:
            return FreshnessStatus.BLOCKED, None
        current = now or datetime.now(timezone.utc)
        age = max(0.0, (current - observed).total_seconds())
        if market_closed:
            return FreshnessStatus.MARKET_CLOSED, age
        return (FreshnessStatus.FRESH if age <= interval_seconds else
                FreshnessStatus.STALE if age <= interval_seconds * 2 else FreshnessStatus.BLOCKED), age

    @staticmethod
    def is_valid_number(value: Any, *, positive: bool = False) -> bool:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
            return False
        return not positive or value > 0

    @classmethod
    def metadata(cls, kind: str, source: str, observed_at: Any, *, instrument: Optional[str] = None,
                 received_at: Any = None, generated_at: Any = None, market_closed: bool = False,
                 available: bool = True, classification: ValueClassification = ValueClassification.LIVE,
                 quality: QualityStatus = QualityStatus.VALID, dependencies: Optional[list[str]] = None,
                 warnings: Optional[list[str]] = None, error: Optional[str] = None,
                 now: Optional[datetime] = None) -> ValueMetadata:
        freshness, age = cls.classify(kind, observed_at, now=now, market_closed=market_closed, available=available)
        if not available:
            classification, quality = ValueClassification.UNAVAILABLE, QualityStatus.UNVERIFIED
        elif market_closed:
            classification = ValueClassification.HISTORICAL
        return ValueMetadata(source, instrument, cls._iso(observed_at), cls._iso(received_at),
            cls._iso(generated_at), age, freshness, quality, classification,
            dependencies=dependencies or [], warnings=warnings or [], error=error)

    @classmethod
    def instrument_master_status(cls, trading_day: str, validated_day: Optional[str], *, consistent: bool = True) -> FreshnessStatus:
        if not validated_day or not consistent:
            return FreshnessStatus.BLOCKED
        return FreshnessStatus.FRESH if validated_day == trading_day else FreshnessStatus.STALE

    @staticmethod
    def _iso(value: Any) -> Optional[str]:
        parsed = DataQualityService.parse_time(value)
        return parsed.isoformat().replace("+00:00", "Z") if parsed else None
