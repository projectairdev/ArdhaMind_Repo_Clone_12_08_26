from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ConfidenceReason:
    reason_type: str
    message: str
    impact: float


@dataclass(frozen=True)
class ConfidenceBonus:
    bonus_type: str
    message: str
    value: float


@dataclass(frozen=True)
class ConfidencePenalty:
    penalty_type: str
    message: str
    value: float


@dataclass(frozen=True)
class CandidateConfidence:
    candidate_id: str
    tradingsymbol: str
    strategy_name: str
    confidence_score: float  # Normalized to 0-100
    raw_score: float
    positive_factors: List[ConfidenceReason] = field(default_factory=list)
    negative_factors: List[ConfidenceReason] = field(default_factory=list)
    bonuses: List[ConfidenceBonus] = field(default_factory=list)
    penalties: List[ConfidencePenalty] = field(default_factory=list)


@dataclass(frozen=True)
class ConfidenceSummary:
    highest_confidence_candidate_id: str
    lowest_confidence_candidate_id: str
    average_confidence: float
    total_evaluated: int
    conclusions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConfidenceReport:
    report_id: str
    trade_plan_id: str
    candidate_confidences: List[CandidateConfidence] = field(default_factory=list)
    summary: ConfidenceSummary = field(default_factory=lambda: ConfidenceSummary("NONE", "NONE", 0.0, 0))
    timestamp: str = ""
    schema_version: str = "1.0"
    engine_version: str = "1.0"
