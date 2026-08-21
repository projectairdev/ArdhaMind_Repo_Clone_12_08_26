from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class EvaluationEvent:
    timestamp: str
    detector_id: str
    event_type: str  # "DETECTION" | "REJECTION" | "BLOCKED" | "QUALIFICATION" | "INVALIDATION" | "DATA_BLOCK"
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


class MissedOpportunityTracker:
    """
    Observability engine recording evaluation logs, threshold failures, data quality blocks,
    rejections, and late confirmations.
    Persists session-level evaluation data to measure detection recall, false-positive rate,
    detection latency, rejected-good-setups, late confirmations, and detector-specific misses
    strictly without hindsight profit optimization.
    """

    def __init__(self, max_events: int = 300) -> None:
        self.max_events = max_events
        self.events: List[EvaluationEvent] = []
        self.total_evaluations: int = 0
        self.total_detections: int = 0
        self.total_rejections: int = 0
        self.total_blocked: int = 0
        self.rejected_good_setups: List[Dict[str, Any]] = []
        self.late_confirmations: List[Dict[str, Any]] = []
        self.detector_misses: Dict[str, int] = {}

    def record_event(
        self,
        timestamp: str,
        detector_id: str,
        event_type: str,
        reason: str,
        details: Dict[str, Any] | None = None,
    ) -> None:
        self.total_evaluations += 1
        if event_type == "DETECTION":
            self.total_detections += 1
        elif event_type == "REJECTION":
            self.total_rejections += 1
            self.detector_misses[detector_id] = self.detector_misses.get(detector_id, 0) + 1
            if details and details.get("raw_score", 0) >= 50:
                self.rejected_good_setups.append({
                    "timestamp": timestamp,
                    "detector_id": detector_id,
                    "reason": reason,
                    "details": details,
                })
        elif event_type == "BLOCKED":
            self.total_blocked += 1

        event = EvaluationEvent(
            timestamp=timestamp,
            detector_id=detector_id,
            event_type=event_type,
            reason=reason,
            details=details or {},
        )
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events.pop(0)

    def compute_session_metrics(self) -> Dict[str, Any]:
        """Calculates observable detection metrics without hindsight profit optimization."""
        evals = max(1, self.total_evaluations)
        recall_rate = round((self.total_detections / evals) * 100.0, 1)
        fp_rate = round((len(self.rejected_good_setups) / evals) * 100.0, 1)

        return {
            "total_evaluations": self.total_evaluations,
            "total_detections": self.total_detections,
            "total_rejections": self.total_rejections,
            "total_blocked": self.total_blocked,
            "detection_recall_rate_pct": recall_rate,
            "false_positive_rate_pct": fp_rate,
            "rejected_good_setups_count": len(self.rejected_good_setups),
            "late_confirmations_count": len(self.late_confirmations),
            "detector_specific_misses": self.detector_misses,
        }

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": e.timestamp,
                "detector_id": e.detector_id,
                "event_type": e.event_type,
                "reason": e.reason,
                "details": e.details,
            }
            for e in self.events
        ]
