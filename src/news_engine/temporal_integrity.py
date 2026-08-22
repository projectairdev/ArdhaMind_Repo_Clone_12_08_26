"""Strict publication-time semantics for E2 current news intelligence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

from src.broker.services.market_status_service import MarketStatusService


IST = ZoneInfo("Asia/Kolkata")
FUTURE_SKEW_TOLERANCE = timedelta(minutes=5)
MAX_LIVE_WINDOW = timedelta(hours=96)


@dataclass(frozen=True)
class TemporalAssessment:
    published_at_utc: Optional[datetime]
    temporal_class: str
    timestamp_validity: str
    timestamp_source: str
    timestamp_confidence: str
    age_seconds: Optional[int]
    current_eligible: bool
    allowed_window_hours: int
    timestamp_verified: bool = False
    reason: str = ""


def strict_publication_timestamp(value: Any) -> Optional[datetime]:
    """Parse only timestamps with explicit timezone provenance."""
    if not value or not isinstance(value, str):
        return None
    raw = value.strip()
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    try:
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def last_valid_nse_close(now: datetime) -> datetime:
    """Return the most recent deterministic NSE 15:30 IST close boundary."""
    current = now.astimezone(IST)
    calendar = MarketStatusService.get_instance()
    candidate_date = current.date()
    close_today = datetime.combine(candidate_date, time(15, 30), IST)
    if current < close_today or calendar.is_holiday(current):
        candidate_date -= timedelta(days=1)
    for _ in range(10):
        candidate = datetime.combine(candidate_date, time(15, 30), IST)
        if not calendar.is_holiday(candidate):
            return candidate.astimezone(timezone.utc)
        candidate_date -= timedelta(days=1)
    return (current - MAX_LIVE_WINDOW).astimezone(timezone.utc)


def live_window(now: datetime, explicit_last_close: Optional[datetime] = None) -> tuple[timedelta, datetime]:
    now_utc = now.astimezone(timezone.utc)
    boundary = explicit_last_close.astimezone(timezone.utc) if explicit_last_close else last_valid_nse_close(now_utc)
    market = MarketStatusService.get_instance()
    holiday = market.is_holiday(now_utc.astimezone(IST))
    if not holiday:
        return timedelta(hours=24), boundary
    since_close = max(timedelta(0), now_utc - boundary)
    # Holidays/weekends get exactly 48 hours unless the actual gap from the
    # previous NSE close is longer. No pre-close padding may silently widen it.
    widened = max(timedelta(hours=48), since_close)
    return min(widened, MAX_LIVE_WINDOW), boundary


def assess_publication_time(value: Any, now: datetime,
                            explicit_last_close: Optional[datetime] = None,
                            timestamp_source: str = "published_at",
                            timestamp_verified: bool = True) -> TemporalAssessment:
    now_utc = now.astimezone(timezone.utc)
    window, _ = live_window(now_utc, explicit_last_close)
    observed = strict_publication_timestamp(value)
    if observed is None:
        return TemporalAssessment(None, "INVALID_TIMESTAMP", "INVALID", timestamp_source, "NONE", None,
                                  False, int(window.total_seconds() // 3600), timestamp_verified=False,
                                  reason="missing_malformed_or_timezone_naive")
    delta = now_utc - observed
    if delta < -FUTURE_SKEW_TOLERANCE:
        return TemporalAssessment(observed, "INVALID_TIMESTAMP", "INVALID_FUTURE", timestamp_source, "HIGH",
                                  int(delta.total_seconds()), False, int(window.total_seconds() // 3600),
                                  timestamp_verified=False,
                                  reason="publication_timestamp_beyond_clock_skew_tolerance")
    age = max(0, int(delta.total_seconds()))

    # If timestamp is from an aggregator discovery without verified publisher date,
    # mark as unverified discovery (discovery-only / background)
    if not timestamp_verified:
        temporal_class = "DISCOVERY_RECENT" if age <= 24 * 3600 else "DISCOVERY_OLDER"
        return TemporalAssessment(
            observed, temporal_class, "UNVERIFIED", timestamp_source, "LOW", age,
            current_eligible=False,
            allowed_window_hours=int(window.total_seconds() // 3600),
            timestamp_verified=False,
            reason="aggregator_discovery_timestamp_unverified",
        )

    if age <= 24 * 3600:
        temporal_class = "CURRENT"
    elif delta <= window:
        temporal_class = "RECENT"
    elif age <= 7 * 86400:
        temporal_class = "STALE"
    else:
        temporal_class = "HISTORICAL"
    return TemporalAssessment(observed, temporal_class, "VALID", timestamp_source, "HIGH", age,
                              temporal_class in {"CURRENT", "RECENT"}, int(window.total_seconds() // 3600),
                              timestamp_verified=True)
