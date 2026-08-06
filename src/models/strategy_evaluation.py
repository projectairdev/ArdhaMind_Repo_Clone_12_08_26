from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class StrategyReason:
    reason_type: str
    message: str


@dataclass(frozen=True)
class StrategyWarning:
    warning_type: str
    message: str
    severity: str  # "LOW", "MEDIUM", "HIGH"


@dataclass(frozen=True)
class StrategyConstraint:
    constraint_type: str
    message: str
    is_violated: bool


@dataclass(frozen=True)
class StrategyScore:
    strategy_name: str  # "MOMENTUM", "BREAKOUT", "TREND_FOLLOWING", "MEAN_REVERSION", "RANGE", "EXPIRY", "SCALPING"
    suitability_score: float  # 0 to 100
    suitability_level: str  # "HIGH", "MEDIUM", "LOW", "NONE"
    reasons: List[StrategyReason] = field(default_factory=list)
    warnings: List[StrategyWarning] = field(default_factory=list)
    constraints: List[StrategyConstraint] = field(default_factory=list)
    required_conditions_met: List[str] = field(default_factory=list)
    rejected_conditions_met: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvaluationSummary:
    top_strategies: List[str]
    suitable_strategies_count: int
    unsuitable_strategies_count: int
    conclusions: List[str]


@dataclass(frozen=True)
class StrategyEvaluation:
    overall_best_strategy: str
    evaluations: List[StrategyScore]
    momentum_evaluation: StrategyScore
    breakout_evaluation: StrategyScore
    trend_following_evaluation: StrategyScore
    mean_reversion_evaluation: StrategyScore
    range_evaluation: StrategyScore
    expiry_evaluation: StrategyScore
    scalping_evaluation: StrategyScore
    summary: EvaluationSummary
    timestamp: str
    schema_version: str = "1.0"
    pipeline_version: str = "1.0"
