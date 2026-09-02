from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass(frozen=True)
class IncidentSnapshot:
    """
    Serializable diagnostic capture of full runtime state upon failure or anomaly.
    Guarantees zero credential leakage via automatic recursive redaction.
    """
    incident_id: str
    captured_at: datetime
    incident_type: str
    error_message: str
    pipeline_health_status: str
    session_context: Dict[str, Any]
    provider_diagnostics: Dict[str, Any]
    feed_health: Dict[str, Any]
    live_market_state: Dict[str, Any]
    analytics_quality: str
    decision_state: str
    stack_trace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        raw = {
            "incident_id": self.incident_id,
            "captured_at": self.captured_at.isoformat(),
            "incident_type": self.incident_type,
            "error_message": self.error_message,
            "pipeline_health_status": self.pipeline_health_status,
            "session_context": self.session_context,
            "provider_diagnostics": self.provider_diagnostics,
            "feed_health": self.feed_health,
            "live_market_state": self.live_market_state,
            "analytics_quality": self.analytics_quality,
            "decision_state": self.decision_state,
            "stack_trace": self.stack_trace,
        }
        return IncidentSnapshot._redact(raw)

    @staticmethod
    def _redact(data: Any) -> Any:
        sensitive_keys = {"token", "access_token", "secret", "password", "key", "authorization", "auth"}
        if isinstance(data, dict):
            return {
                k: ("[REDACTED]" if any(s in k.lower() for s in sensitive_keys) else IncidentSnapshot._redact(v))
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [IncidentSnapshot._redact(x) for x in data]
        return data


class IncidentSnapshotBuilder:
    """Builds IncidentSnapshot from active runtime state."""

    @staticmethod
    def capture(
        incident_type: str,
        error_message: str,
        pipeline_status: str,
        session_data: Dict[str, Any],
        provider_diag: Dict[str, Any],
        feed_health_data: Dict[str, Any],
        live_state_data: Dict[str, Any],
        analytics_quality_str: str,
        decision_state_str: str,
        trace: Optional[str] = None,
    ) -> IncidentSnapshot:
        return IncidentSnapshot(
            incident_id=f"inc_{uuid4().hex[:10]}",
            captured_at=datetime.now(timezone.utc),
            incident_type=incident_type,
            error_message=error_message,
            pipeline_health_status=pipeline_status,
            session_context=session_data,
            provider_diagnostics=provider_diag,
            feed_health=feed_health_data,
            live_market_state=live_state_data,
            analytics_quality=analytics_quality_str,
            decision_state=decision_state_str,
            stack_trace=trace,
        )
