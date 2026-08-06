from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class DecisionReason:
    reason_type: str  # e.g., "HIGH_CONFIDENCE", "TREND_ALIGNMENT", "RISK_REJECTED", "LOW_LIQUIDITY"
    message: str
    metric_name: str
    metric_value: float


@dataclass(frozen=True)
class DecisionWarning:
    warning_type: str
    message: str
    severity: str  # "LOW", "MEDIUM", "HIGH"


@dataclass(frozen=True)
class CandidateDecision:
    candidate_id: str
    tradingsymbol: str
    strategy_name: str
    decision: str  # "BUY", "SELL", "WATCH", "REJECT", "NO TRADE"
    priority_score: float  # Deterministic score for ranking executable decisions
    execution_priority: int  # 1-based order (1 = highest), -1 if not executable
    explanation: str
    supporting_evidence: List[DecisionReason] = field(default_factory=list)
    blocking_factors: List[DecisionReason] = field(default_factory=list)
    warnings: List[DecisionWarning] = field(default_factory=list)
    allocated_capital: float = 0.0
    allocated_lots: int = 0
    expiry_reason: str = ""


@dataclass(frozen=True)
class DecisionSummary:
    overall_action: str  # e.g., "EXECUTE", "MONITOR", "HOLD"
    highest_priority_candidate_id: str
    portfolio_status_message: str
    conclusions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionStatistics:
    total_candidates_evaluated: int
    buy_count: int
    sell_count: int
    watch_count: int
    reject_count: int
    no_trade_count: int
    total_allocated_capital: float


@dataclass(frozen=True)
class DecisionEngineConfig:
    buy_confidence_threshold: float = 70.0
    sell_confidence_threshold: float = 70.0
    watch_confidence_threshold: float = 50.0
    max_execution_slots: int = 3
    tie_breaker_metric: str = "CONFIDENCE_SCORE"  # "CONFIDENCE_SCORE", "ALLOCATED_CAPITAL", "TRA_SCORE"


@dataclass(frozen=True)
class DecisionReport:
    report_id: str
    risk_report_id: str
    candidate_decisions: List[CandidateDecision] = field(default_factory=list)
    priority_ranking: List[str] = field(default_factory=list)  # List of candidate_ids in priority order
    summary: DecisionSummary = field(default_factory=lambda: DecisionSummary("HOLD", "NONE", "No decisions made"))
    stats: DecisionStatistics = field(default_factory=lambda: DecisionStatistics(0, 0, 0, 0, 0, 0, 0.0))
    timestamp: str = ""
    schema_version: str = "1.0"
    engine_version: str = "1.0"
