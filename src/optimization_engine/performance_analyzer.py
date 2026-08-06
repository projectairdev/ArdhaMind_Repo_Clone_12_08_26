from __future__ import annotations

from typing import List
from src.models.validation_report import ValidationReport
from src.models.optimization_report import (
    OptimizationRecommendation,
    RecommendationEvidence,
    ThresholdRecommendation,
)


class PerformanceAnalyzer:
    """
    Analyzes high-level validation results, detecting risk concentration,
    unused decision states, and overall performance bottlenecks.
    """

    def analyze(self, report: ValidationReport) -> List[OptimizationRecommendation]:
        recommendations = []
        summary = report.summary_stats
        risk = report.risk_stats
        outcomes = report.outcome_validations

        # 1. Unused Decision States
        unused_states = []
        if summary.overall_watch_count == 0:
            unused_states.append("WATCH")
        if summary.overall_no_trade_count == 0:
            unused_states.append("NO TRADE")

        if unused_states:
            evidence = RecommendationEvidence(
                historical_sample_size=summary.total_candidates_evaluated,
                observed_improvement_potential=15.0,
                affected_strategies=[s.strategy_name for s in report.strategy_performances],
                expected_trade_off="Higher granularity of trade decisions with lower execution noise at the cost of higher latency in state transitions.",
                confidence_score=80.0,
            )
            rec = OptimizationRecommendation(
                recommendation_id="REC_UNUSED_STATES",
                category="CLASSIFICATION_BOUNDARIES",
                title="Establish Active Decision State Thresholds",
                description=f"Enable utilization of under-utilized decision states: {', '.join(unused_states)}.",
                current_value="0.0% utilization for inactive states",
                recommended_value="Introduce symmetric boundaries for WATCH and NO TRADE to absorb market noise.",
                evidence=evidence,
                rationale=(
                    f"Out of {summary.total_candidates_evaluated} evaluated candidates, the decision states "
                    f"{', '.join(unused_states)} were never utilized. This suggests binary decision boundary "
                    "clipping, converting potential wait-and-watch setups into aggressive executions."
                ),
            )
            recommendations.append(rec)

        # 2. Risk Concentration
        # If a single window or overall risk has high max exposure vs average or extremely high capital allocation
        if risk.total_allocated_capital > 500000.0 or risk.max_allocated_capital > 500000.0 or (risk.approved_count > 0 and (risk.total_allocated_capital / risk.approved_count) > 50000.0):
            evidence = RecommendationEvidence(
                historical_sample_size=risk.approved_count + risk.rejected_count,
                observed_improvement_potential=20.0,
                affected_strategies=[s.strategy_name for s in report.strategy_performances],
                expected_trade_off="Lower drawdown risks with potential minor reductions in peak absolute profit.",
                confidence_score=85.0,
            )
            rec = OptimizationRecommendation(
                recommendation_id="REC_RISK_CONCENTRATION",
                category="RISK_EXPOSURE",
                title="De-escalate Capital Exposure per Position",
                description="Reduce maximum allocated capital limit to enforce sector and position diversification.",
                current_value=f"Max capital allocated: {risk.max_allocated_capital:.2f}",
                recommended_value="Reduce per-position exposure threshold by 20-30%.",
                evidence=evidence,
                rationale=(
                    f"Peak single-position capital allocation reached {risk.max_allocated_capital:.2f}. "
                    "Enforcing a strict limit prevents tail-risk and severe drawdowns during erratic intraday spikes."
                ),
            )
            recommendations.append(rec)

        # 3. Poor outcome validation accuracy
        for outcome in outcomes:
            if outcome.accuracy_pct < 65.0 and outcome.evaluation_window != "Expiry-day":
                evidence = RecommendationEvidence(
                    historical_sample_size=outcome.success_count + outcome.failure_count,
                    observed_improvement_potential=round(75.0 - outcome.accuracy_pct, 2),
                    affected_strategies=[s.strategy_name for s in report.strategy_performances],
                    expected_trade_off="Slightly fewer trades executed, but higher win rate and win-to-loss ratio.",
                    confidence_score=75.0,
                )
                rec = OptimizationRecommendation(
                    recommendation_id=f"REC_POOR_ACCURACY_{outcome.evaluation_window.upper().replace('-', '_')}",
                    category="CONFIDENCE_THRESHOLD",
                    title=f"Tighten Execution Rules for {outcome.evaluation_window} Window",
                    description=f"Elevate confirmation standards to repair underperforming {outcome.evaluation_window} accuracy.",
                    current_value=f"Accuracy: {outcome.accuracy_pct:.2f}%",
                    recommended_value="Introduce dual-timeframe verification filtering before final signal emission.",
                    evidence=evidence,
                    rationale=(
                        f"The {outcome.evaluation_window} evaluation window exhibits an unacceptable accuracy of "
                        f"{outcome.accuracy_pct:.2f}% (Successes: {outcome.success_count}, Failures: {outcome.failure_count}). "
                        "High-noise intraday sessions require more rigid confirmation signals."
                    ),
                )
                recommendations.append(rec)

        return recommendations
