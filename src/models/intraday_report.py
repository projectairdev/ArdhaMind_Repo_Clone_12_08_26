from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


class PlanStatus(Enum):
    VALID = "Plan Still Valid"
    NEEDS_REVIEW = "Plan Needs Review"
    INVALIDATED = "Plan Invalidated"


class CandidateStatus(Enum):
    UNCHANGED = "UNCHANGED"
    IMPROVED = "IMPROVED"
    WEAKENED = "WEAKENED"
    INVALIDATED = "INVALIDATED"


class ActionRecommendation(Enum):
    PROCEED = "PROCEED"
    WAIT = "WAIT"
    REVIEW = "REVIEW"
    CANCEL = "CANCEL"


@dataclass(frozen=True)
class MarketChange:
    metric_name: str
    previous_value: float | str
    current_value: float | str
    change_pct: Optional[float] = None
    is_significant: bool = False
    message: str = ""


@dataclass(frozen=True)
class ConfidenceChange:
    candidate_id: str
    previous_confidence: float
    current_confidence: float
    change_amt: float
    status: CandidateStatus
    explanation: str = ""


@dataclass(frozen=True)
class RiskChange:
    candidate_id: str
    previous_risk_grade: str
    current_risk_grade: str
    is_risk_increased: bool
    triggered_new_warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CandidateStatusReport:
    candidate_id: str
    tradingsymbol: str
    status: CandidateStatus
    explanation: str
    previous_decision: str
    suggested_decision: str


@dataclass(frozen=True)
class IntradaySummary:
    plan_status: PlanStatus
    action_recommendation: ActionRecommendation
    total_candidates_monitored: int
    invalidated_candidates_count: int
    significant_market_changes_count: int
    overall_pcr_shift: float
    overall_vix_shift: float


@dataclass(frozen=True)
class IntradayReport:
    report_id: str
    evening_report_id: str
    summary: IntradaySummary
    market_changes: List[MarketChange] = field(default_factory=list)
    candidate_changes: List[CandidateStatusReport] = field(default_factory=list)
    confidence_changes: List[ConfidenceChange] = field(default_factory=list)
    risk_changes: List[RiskChange] = field(default_factory=list)
    validation_reasons: List[str] = field(default_factory=list)
    timestamp: str = ""
    engine_version: str = "1.0"
