from __future__ import annotations

from typing import List, Tuple
from src.models.validation_report import ValidationReport
from src.models.optimization_report import (
    OptimizationRecommendation,
    RecommendationEvidence,
    ThresholdRecommendation,
)


class ThresholdAnalyzer:
    """
    Analyzes confidence scores and decision-making thresholds to identify
    under-calibrated parameter limits and weak confidence bands.
    """

    def analyze(self, report: ValidationReport) -> Tuple[List[OptimizationRecommendation], List[ThresholdRecommendation]]:
        recommendations = []
        threshold_recs = []
        conf = report.confidence_stats
        summary = report.summary_stats

        # 1. Weak confidence bands / Low confidence threshold
        if conf.avg_confidence < 60.0:
            evidence = RecommendationEvidence(
                historical_sample_size=summary.total_candidates_evaluated,
                observed_improvement_potential=12.5,
                affected_strategies=[s.strategy_name for s in report.strategy_performances],
                expected_trade_off="Reduces total trade count (frequency) by ~15% while improving overall decision precision.",
                confidence_score=90.0,
            )
            rec = OptimizationRecommendation(
                recommendation_id="REC_LOW_CONF_THRESHOLD",
                category="CONFIDENCE_THRESHOLD",
                title="Increase Minimum Confidence Threshold",
                description="Elevate the baseline confidence score required for BUY/SELL decision execution.",
                current_value=f"Average Confidence: {conf.avg_confidence:.2f}",
                recommended_value="Raise minimum execution confidence to 65.0.",
                evidence=evidence,
                rationale=(
                    f"Average confidence of evaluated candidates is low ({conf.avg_confidence:.2f}). "
                    "Raising the minimum execution barrier prevents marginal setups from being filled, "
                    "thereby preserving capital for high-conviction structures."
                ),
            )
            recommendations.append(rec)

            threshold_recs.append(
                ThresholdRecommendation(
                    parameter_name="min_confidence_threshold",
                    current_value=conf.avg_confidence,
                    suggested_value=65.0,
                    direction="INCREASE",
                    impact="Filter out low-probability trades and enhance overall win rate.",
                )
            )

        # 2. Overly aggressive risk-rejection/approval balance
        total_risk_evaluated = report.risk_stats.approved_count + report.risk_stats.rejected_count
        if total_risk_evaluated > 0:
            rejection_rate = (report.risk_stats.rejected_count / total_risk_evaluated) * 100.0
            if rejection_rate < 10.0:
                evidence = RecommendationEvidence(
                    historical_sample_size=total_risk_evaluated,
                    observed_improvement_potential=10.0,
                    affected_strategies=[s.strategy_name for s in report.strategy_performances],
                    expected_trade_off="Increases candidate safety filtering at the risk of missing fast-moving momentum breakouts.",
                    confidence_score=85.0,
                )
                rec = OptimizationRecommendation(
                    recommendation_id="REC_WEAK_RISK_FILTER",
                    category="RISK_EXPOSURE",
                    title="Tighten Risk Engine Rejection Thresholds",
                    description="Increase the sensitivity of risk parameters to filter out marginal candidates.",
                    current_value=f"Rejection Rate: {rejection_rate:.2f}%",
                    recommended_value="Tighten VaR and portfolio correlation multipliers.",
                    evidence=evidence,
                    rationale=(
                        f"The risk engine is only rejecting {rejection_rate:.2f}% of candidates, "
                        "indicating that current risk parameters might be under-calibrated and overly permissive. "
                        "Tightening limits protects the portfolio against systematic correlation shocks."
                    ),
                )
                recommendations.append(rec)

                threshold_recs.append(
                    ThresholdRecommendation(
                        parameter_name="max_portfolio_correlation_limit",
                        current_value=0.85,
                        suggested_value=0.70,
                        direction="DECREASE",
                        impact="Reduces exposure to highly correlated simultaneous positions.",
                    )
                )

        return recommendations, threshold_recs
