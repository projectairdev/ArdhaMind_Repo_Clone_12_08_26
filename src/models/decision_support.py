from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class DecisionSupportReport:
    market_interpretation: str = ""
    current_scenario_status: str = "unavailable"
    required_confirmations: list[str] = field(default_factory=list)
    missing_confirmations: list[str] = field(default_factory=list)
    invalidation_conditions: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    human_decision_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_legacy_dict(self) -> dict[str, Any]:
        """Phase 2 compatibility only; remove after legacy DecisionReport consumers migrate."""
        action = "HOLD" if self.blockers or self.missing_confirmations else "MONITOR"
        return {
            "reportId": "canonical-decision-support",
            "riskReportId": "canonical-deterministic-risk",
            "candidateDecisions": [],
            "priorityRanking": [],
            "summary": {"overallAction": action, "highestPriorityCandidateId": "NONE",
                        "portfolioStatusMessage": self.market_interpretation or self.current_scenario_status,
                        "conclusions": self.warnings},
            "stats": {"totalCandidatesEvaluated": 0, "buyCount": 0, "sellCount": 0,
                      "watchCount": 0, "rejectCount": 0, "noTradeCount": 0,
                      "totalAllocatedCapital": 0.0},
            "schemaVersion": "compat-1.0", "engineVersion": "canonical-adapter-1.0",
        }
