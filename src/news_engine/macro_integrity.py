"""Observation-time and identity invariants for E3 cross-market quotes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo


FUTURE_SKEW = timedelta(minutes=5)
FRESH_AGE = timedelta(minutes=15)
RECENT_AGE = timedelta(hours=6)
MAX_LAST_SESSION_AGE = timedelta(hours=96)


@dataclass(frozen=True)
class MacroFreshnessAssessment:
    observation_utc: Optional[datetime]
    freshness: str
    status: str
    current_eligible: bool
    age_seconds: Optional[int]
    reason: str = ""


def parse_observation_timestamp(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    try:
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def _business_days_elapsed(observed: datetime, now: datetime, timezone_name: str) -> int:
    try:
        zone = ZoneInfo(timezone_name)
    except (KeyError, ValueError):
        zone = timezone.utc
    start = observed.astimezone(zone).date()
    end = now.astimezone(zone).date()
    if end <= start:
        return 0
    elapsed = 0
    cursor = start + timedelta(days=1)
    while cursor <= end:
        if cursor.weekday() < 5:
            elapsed += 1
        cursor += timedelta(days=1)
    return elapsed


def assess_macro_observation(value: Any, now: datetime, exchange_timezone: str = "UTC") -> MacroFreshnessAssessment:
    now_utc = now.astimezone(timezone.utc)
    observed = parse_observation_timestamp(value)
    if observed is None:
        return MacroFreshnessAssessment(None, "unavailable", "UNAVAILABLE", False, None,
                                        "missing_malformed_or_timezone_naive_observation")
    delta = now_utc - observed
    if delta < -FUTURE_SKEW:
        return MacroFreshnessAssessment(observed, "unavailable", "UNAVAILABLE", False,
                                        int(delta.total_seconds()), "future_observation")
    age = max(0, int(delta.total_seconds()))
    if delta <= FRESH_AGE:
        return MacroFreshnessAssessment(observed, "fresh", "AVAILABLE", True, age)
    if delta <= RECENT_AGE:
        return MacroFreshnessAssessment(observed, "recent", "AVAILABLE", True, age)
    business_days = _business_days_elapsed(observed, now_utc, exchange_timezone)
    if delta <= MAX_LAST_SESSION_AGE and business_days <= 1:
        return MacroFreshnessAssessment(observed, "last_valid_session", "AVAILABLE", True, age)
    return MacroFreshnessAssessment(observed, "stale", "STALE", False, age,
                                    "observation_is_not_from_latest_valid_source_session")


def aggregate_quote_freshness(quotes: list[dict[str, Any]]) -> str:
    states = {str(quote.get("freshness_status") or "unavailable").lower() for quote in quotes}
    if not states or states == {"unavailable"}:
        return "unavailable"
    if "stale" in states or "unavailable" in states:
        return "degraded"
    if "fresh" in states:
        return "fresh"
    if "recent" in states:
        return "recent"
    return "last_valid_session"
