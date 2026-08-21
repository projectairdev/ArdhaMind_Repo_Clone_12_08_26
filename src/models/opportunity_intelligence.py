from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OpportunityIntelligence:
    best_opportunity: Dict[str, Any]
    trade_ready: List[Dict[str, Any]] = field(default_factory=list)
    watching: List[Dict[str, Any]] = field(default_factory=list)
    blocked_recent: List[Dict[str, Any]] = field(default_factory=list)
    rejected_recent: List[Dict[str, Any]] = field(default_factory=list)
    invalidated_recent: List[Dict[str, Any]] = field(default_factory=list)
    expired_recent: List[Dict[str, Any]] = field(default_factory=list)
    detector_health: Dict[str, Any] = field(default_factory=dict)
    scan_metrics: Dict[str, Any] = field(default_factory=dict)
    acceptance_status: str = "NOT_ACCEPTED"
    staging_mode_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "best_opportunity": self.best_opportunity,
            "trade_ready": self.trade_ready,
            "watching": self.watching,
            "blocked_recent": self.blocked_recent,
            "rejected_recent": self.rejected_recent,
            "invalidated_recent": self.invalidated_recent,
            "expired_recent": self.expired_recent,
            "detector_health": self.detector_health,
            "scan_metrics": self.scan_metrics,
            "acceptance_status": self.acceptance_status,
            "staging_mode_only": self.staging_mode_only,
        }
