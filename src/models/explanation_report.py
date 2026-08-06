from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class CandidateExplanation:
    candidate_id: str
    tradingsymbol: str
    strategy_name: str
    decision: str  # e.g., "BUY", "SELL", "WATCH", "REJECT", "NO TRADE"
    decision_reasoning: str
    lots_reasoning: str
    confidence_reasoning: str
    risk_reasoning: str


@dataclass(frozen=True)
class DecisionExplanation:
    overall_action: str
    highest_priority_candidate_id: str
    portfolio_status_message: str
    overall_decision_reasoning: str
    candidate_explanations: List[CandidateExplanation] = field(default_factory=list)


@dataclass(frozen=True)
class RiskExplanation:
    portfolio_risk_grade: str
    total_capital_allocated: float
    portfolio_utilization_pct: float
    portfolio_risk_reasoning: str
    warnings_explanations: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConfidenceExplanation:
    highest_confidence_candidate_id: str
    confidence_reasoning: str


@dataclass(frozen=True)
class StrategyExplanation:
    overall_best_strategy: str
    strategy_reasoning: str
    all_strategy_scores: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class IntradayExplanation:
    plan_status: str
    action_recommendation: str
    explanation: str
    market_change_reasons: List[str] = field(default_factory=list)
    candidate_change_reasons: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PlannerExplanation:
    directional_bias: str
    outlook_classification: str
    explanation: str


@dataclass(frozen=True)
class ExplanationSummary:
    title: str
    brief_overview: str
    key_findings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExplanationReport:
    report_id: str
    timestamp: str
    summary: ExplanationSummary
    decision: DecisionExplanation
    risk: RiskExplanation
    confidence: ConfidenceExplanation
    strategy: StrategyExplanation
    intraday: Optional[IntradayExplanation] = None
    planner: Optional[PlannerExplanation] = None
    schema_version: str = "1.0"
    engine_version: str = "1.0"
