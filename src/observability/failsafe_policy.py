from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.decision.models.decision_models import DecisionState
from src.market_data.models.quality_enums import DataQualityStatus


@dataclass(frozen=True)
class LastKnownValueRecord:
    """
    Explicit representation of a historical or stale value.
    Prevents stale data from masquerading as current live truth.
    """
    instrument_id: str
    last_price: float
    observed_at: datetime
    age_seconds: float
    quality: DataQualityStatus
    is_stale: bool
    display_label: str


class FailSafePolicy:
    """
    Enforces canonical fail-safe policies and last-known-value display labeling.
    """

    @staticmethod
    def format_last_known_value(
        instrument_id: str,
        price: float,
        observed_at: datetime,
        current_time: Optional[datetime] = None,
        stale_threshold_seconds: float = 3.0,
    ) -> LastKnownValueRecord:
        now = current_time or datetime.now(timezone.utc)
        age_s = max(0.0, (now - observed_at).total_seconds())
        is_stale = (age_s > stale_threshold_seconds)

        if is_stale:
            label = f"{price:,.1f} — STALE ({age_s:.0f}s old)"
            quality = DataQualityStatus.STALE
        else:
            label = f"{price:,.1f} — LIVE"
            quality = DataQualityStatus.VALID

        return LastKnownValueRecord(
            instrument_id=instrument_id,
            last_price=price,
            observed_at=observed_at,
            age_seconds=round(age_s, 1),
            quality=quality,
            is_stale=is_stale,
            display_label=label,
        )

    @staticmethod
    def resolve_decision_failsafe(
        feed_status: str,
        current_state: DecisionState,
    ) -> DecisionState:
        """Revokes READY state if the live feed is STALE or FROZEN."""
        if feed_status in ("STALE", "FROZEN"):
            return DecisionState.BLOCKED
        return current_state
