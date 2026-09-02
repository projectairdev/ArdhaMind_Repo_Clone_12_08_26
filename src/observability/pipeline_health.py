from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from src.market_data.models.quality_enums import DataQualityStatus


class PipelineHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    RECOVERING = "RECOVERING"
    BLOCKED = "BLOCKED"
    NOT_RUNNING = "NOT_RUNNING"


@dataclass(frozen=True)
class PipelineHealthSnapshot:
    """Holistic pipeline operational health snapshot."""
    overall_status: PipelineHealthStatus
    is_running: bool
    socket_connected: bool
    feed_health: str
    session_valid: bool
    event_bus_healthy: bool
    candles_progressing: bool
    analytics_quality: DataQualityStatus
    degraded_reasons: List[str]
    captured_at: datetime


class PipelineHealthEvaluator:
    """Evaluates holistic health from operational components."""

    @staticmethod
    def evaluate(
        is_running: bool,
        socket_connected: bool,
        feed_status: str,
        session_valid: bool,
        event_bus_overflow: bool,
        candles_count: int,
        analytics_quality: DataQualityStatus,
    ) -> PipelineHealthSnapshot:
        now_utc = datetime.now(timezone.utc)
        reasons: List[str] = []

        if not is_running:
            return PipelineHealthSnapshot(
                overall_status=PipelineHealthStatus.NOT_RUNNING,
                is_running=False,
                socket_connected=False,
                feed_health="NOT_RUNNING",
                session_valid=session_valid,
                event_bus_healthy=True,
                candles_progressing=False,
                analytics_quality=DataQualityStatus.UNAVAILABLE,
                degraded_reasons=["Pipeline runtime is stopped"],
                captured_at=now_utc,
            )

        if not session_valid:
            reasons.append("Session context invalid or mismatched")

        if not socket_connected:
            reasons.append("Provider WebSocket disconnected")

        if feed_status in ("STALE", "FROZEN"):
            reasons.append(f"Feed health is {feed_status}")

        if event_bus_overflow:
            reasons.append("EventBus queue backpressure / overflow detected")

        if analytics_quality == DataQualityStatus.UNAVAILABLE:
            reasons.append("Analytics data is UNAVAILABLE")

        # Resolve overall status
        if not session_valid or analytics_quality == DataQualityStatus.UNAVAILABLE or feed_status == "STALE":
            status = PipelineHealthStatus.BLOCKED if not session_valid else PipelineHealthStatus.STALE
        elif not socket_connected or feed_status == "RECOVERING" or len(reasons) > 0:
            status = PipelineHealthStatus.RECOVERING if feed_status == "RECOVERING" else PipelineHealthStatus.DEGRADED
        else:
            status = PipelineHealthStatus.HEALTHY

        return PipelineHealthSnapshot(
            overall_status=status,
            is_running=is_running,
            socket_connected=socket_connected,
            feed_health=feed_status,
            session_valid=session_valid,
            event_bus_healthy=not event_bus_overflow,
            candles_progressing=candles_count > 0,
            analytics_quality=analytics_quality,
            degraded_reasons=reasons,
            captured_at=now_utc,
        )
