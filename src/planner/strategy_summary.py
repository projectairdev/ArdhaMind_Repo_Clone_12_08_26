from __future__ import annotations

from typing import List
from src.models.strategy_evaluation import StrategyEvaluation
from src.models.evening_report import RecommendedStrategy


def compile_strategy_summary(
    strategy_evaluation: StrategyEvaluation,
) -> List[RecommendedStrategy]:
    recommended = []
    if not strategy_evaluation or not strategy_evaluation.evaluations:
        return recommended

    # Sort strategy scores by suitability_score descending
    evaluations = sorted(
        strategy_evaluation.evaluations,
        key=lambda s: s.suitability_score,
        reverse=True,
    )
    for s in evaluations:
        # Include strategies that have MEDIUM or HIGH suitability
        if s.suitability_level in ("HIGH", "MEDIUM"):
            rationale = [r.message for r in s.reasons]
            recommended.append(
                RecommendedStrategy(
                    strategy_name=s.strategy_name,
                    suitability_score=s.suitability_score,
                    suitability_level=s.suitability_level,
                    rationale=rationale,
                )
            )
    return recommended
