from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class CandidateReason:
    reason_type: str
    message: str


@dataclass(frozen=True)
class CandidateWarning:
    warning_type: str
    message: str
    severity: str  # "LOW", "MEDIUM", "HIGH"


@dataclass(frozen=True)
class CandidateRejection:
    strategy_name: str
    tradingsymbol: str
    reason_type: str
    message: str


@dataclass(frozen=True)
class TradeCandidate:
    candidate_id: str  # Format: {strategy_name}_{tradingsymbol}
    strategy_name: str
    tradingsymbol: str
    strike: float
    instrument_type: str  # "CE" or "PE"
    expiry: str
    distance_from_atm: float
    atm_distance_class: str  # "ATM", "ATM_PLUS_1", "ATM_MINUS_1", "ATM_PLUS_2", "ATM_MINUS_2", "OTHER"
    oi: int
    volume: int
    spread_pct: float
    iv: float
    tradability_score: float
    suitability_score: float
    ranking_score: float
    rank: int
    reasons: List[CandidateReason] = field(default_factory=list)
    warnings: List[CandidateWarning] = field(default_factory=list)
    expiry_reason: str = ""


@dataclass(frozen=True)
class PlannerStatistics:
    total_candidates_generated: int
    total_candidates_accepted: int
    total_candidates_rejected: int
    momentum_accepted_count: int
    breakout_accepted_count: int
    trend_following_accepted_count: int
    mean_reversion_accepted_count: int
    range_accepted_count: int
    expiry_accepted_count: int
    scalping_accepted_count: int
    average_ranking_score: float


@dataclass(frozen=True)
class PlannerSummary:
    best_candidate_id: str
    conclusions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TradePlan:
    trade_plan_id: str
    accepted_candidates: List[TradeCandidate] = field(default_factory=list)
    rejected_candidates: List[CandidateRejection] = field(default_factory=list)
    statistics: PlannerStatistics = field(default_factory=lambda: PlannerStatistics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0))
    summary: PlannerSummary = field(default_factory=lambda: PlannerSummary("NONE"))
    timestamp: str = ""
    schema_version: str = "1.0"
    pipeline_version: str = "1.0"
