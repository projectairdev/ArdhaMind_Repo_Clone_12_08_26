from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass(frozen=True)
class RecommendationEvidence:
    historical_sample_size: int
    observed_improvement_potential: float  # e.g., potential accuracy increase or P&L increase
    affected_strategies: List[str]
    expected_trade_off: str
    confidence_score: float  # Scale of 0.0 to 100.0


@dataclass(frozen=True)
class OptimizationRecommendation:
    recommendation_id: str
    category: str  # e.g., "CONFIDENCE_THRESHOLD", "RISK_EXPOSURE", "CLASSIFICATION_BOUNDARIES", "STRATEGY_WEIGHTS"
    title: str
    description: str
    current_value: str
    recommended_value: str
    evidence: RecommendationEvidence
    rationale: str


@dataclass(frozen=True)
class StrategyOptimization:
    strategy_name: str
    current_accuracy: float
    recommended_action: str  # e.g., "REDUCE_WEIGHT", "INCREASE_WEIGHT", "SUSPEND"
    rationale: str


@dataclass(frozen=True)
class ThresholdRecommendation:
    parameter_name: str
    current_value: float
    suggested_value: float
    direction: str  # "INCREASE" or "DECREASE"
    impact: str


@dataclass(frozen=True)
class WeightRecommendation:
    strategy_or_factor: str
    current_weight: float
    suggested_weight: float
    rationale: str


@dataclass(frozen=True)
class OptimizationSummary:
    total_recommendations: int
    critical_adjustments: int
    potential_pnl_improvement: float
    recommendation_confidence_avg: float


@dataclass(frozen=True)
class OptimizationReport:
    report_id: str
    validation_report_id: str
    summary: OptimizationSummary
    recommendations: List[OptimizationRecommendation] = field(default_factory=list)
    strategy_optimizations: List[StrategyOptimization] = field(default_factory=list)
    threshold_recommendations: List[ThresholdRecommendation] = field(default_factory=list)
    weight_recommendations: List[WeightRecommendation] = field(default_factory=list)
    timestamp: str = ""
    engine_version: str = "1.0"
