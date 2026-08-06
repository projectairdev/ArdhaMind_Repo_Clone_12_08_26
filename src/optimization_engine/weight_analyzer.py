from __future__ import annotations

from typing import List, Tuple
from src.models.validation_report import ValidationReport
from src.models.optimization_report import (
    OptimizationRecommendation,
    RecommendationEvidence,
    WeightRecommendation,
)


class WeightAnalyzer:
    """
    Analyzes strategy performance metrics to recommend re-weighting
    strategy suitability factors and portfolio allocations.
    """

    def analyze(self, report: ValidationReport) -> Tuple[List[OptimizationRecommendation], List[WeightRecommendation]]:
        recommendations = []
        weight_recs = []

        # Find underperforming or dominant strategies from strategy_performances
        strategies = report.strategy_performances
        if not strategies:
            return recommendations, weight_recs

        total_candidates_all = sum(s.total_candidates for s in strategies)

        for s in strategies:
            # Calculate concentration of candidates
            concentration = (s.total_candidates / total_candidates_all * 100.0) if total_candidates_all > 0 else 0.0

            # 1. Underperforming strategy (avg_confidence_score is low < 55)
            if s.avg_confidence_score < 55.0 and s.total_candidates > 0:
                evidence = RecommendationEvidence(
                    historical_sample_size=s.total_candidates,
                    observed_improvement_potential=15.0,
                    affected_strategies=[s.strategy_name],
                    expected_trade_off="Lower drawdowns in unfavorable market structures with minimal effect on winning strategies.",
                    confidence_score=85.0,
                )
                rec = OptimizationRecommendation(
                    recommendation_id=f"REC_REDUCE_WEIGHT_{s.strategy_name.upper()}",
                    category="STRATEGY_WEIGHTS",
                    title=f"De-emphasize Strategy: {s.strategy_name}",
                    description=f"Reduce suitability weight for {s.strategy_name} due to low conviction scores.",
                    current_value=f"Average Confidence: {s.avg_confidence_score:.2f}",
                    recommended_value="Reduce strategy suitability multiplier by 0.25.",
                    evidence=evidence,
                    rationale=(
                        f"Strategy {s.strategy_name} represents {concentration:.1f}% of evaluated candidates "
                        f"but has a low average confidence of {s.avg_confidence_score:.2f}. "
                        "Over-allocation to low-conviction signals dilutes edge and incurs transaction overhead."
                    ),
                )
                recommendations.append(rec)

                weight_recs.append(
                    WeightRecommendation(
                        strategy_or_factor=f"{s.strategy_name}_suitability_weight",
                        current_weight=1.0,
                        suggested_weight=0.75,
                        rationale=f"Reduce suitability weight to restrict {s.strategy_name} activation in sub-optimal regimes.",
                    )
                )

            # 2. Risk over-concentration in a single strategy
            elif concentration > 50.0 and s.avg_confidence_score < 75.0:
                evidence = RecommendationEvidence(
                    historical_sample_size=s.total_candidates,
                    observed_improvement_potential=8.0,
                    affected_strategies=[s.strategy_name],
                    expected_trade_off="Improves asset and style diversification at the cost of lower single-day peak profits.",
                    confidence_score=78.0,
                )
                rec = OptimizationRecommendation(
                    recommendation_id=f"REC_CONCENTRATION_{s.strategy_name.upper()}",
                    category="STRATEGY_WEIGHTS",
                    title="Mitigate Single-Strategy Style Concentration",
                    description=f"Scale down portfolio allocation weights for {s.strategy_name} to diversify styles.",
                    current_value=f"Portfolio Concentration: {concentration:.2f}%",
                    recommended_value="Apply a dynamic dampening multiplier when style concentration exceeds 40%.",
                    evidence=evidence,
                    rationale=(
                        f"Strategy {s.strategy_name} dominates the pipeline with {concentration:.1f}% of all "
                        "evaluated candidates. Diversification across multiple independent styles (e.g., mean reversion, "
                        "trend following) is vital for multi-regime resilience."
                    ),
                )
                recommendations.append(rec)

                weight_recs.append(
                    WeightRecommendation(
                        strategy_or_factor=f"{s.strategy_name}_allocation_cap",
                        current_weight=1.0,
                        suggested_weight=0.80,
                        rationale="Scale down the relative allocation weight to balance the portfolio style mix.",
                    )
                )

        return recommendations, weight_recs
