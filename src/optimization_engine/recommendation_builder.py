from __future__ import annotations

import uuid
from src.models.validation_report import ValidationReport
from src.models.optimization_report import (
    OptimizationReport,
    OptimizationSummary,
)
from src.optimization_engine.performance_analyzer import PerformanceAnalyzer
from src.optimization_engine.threshold_analyzer import ThresholdAnalyzer
from src.optimization_engine.weight_analyzer import WeightAnalyzer
from src.optimization_engine.strategy_analyzer import StrategyAnalyzer
from src.utils import now_str


class RecommendationBuilder:
    """
    Coordinates sub-analyzers to run stateless heuristic analysis of a
    ValidationReport and builds a complete, unified, immutable OptimizationReport.
    """

    def __init__(self) -> None:
        self.performance_analyzer = PerformanceAnalyzer()
        self.threshold_analyzer = ThresholdAnalyzer()
        self.weight_analyzer = WeightAnalyzer()
        self.strategy_analyzer = StrategyAnalyzer()

    def build_report(
        self, report: ValidationReport, report_id: str | None = None
    ) -> OptimizationReport:
        if report_id is None:
            report_id = f"OPT_{uuid.uuid4().hex[:8].upper()}"

        # 1. Run all sub-analyzers
        perf_recs = self.performance_analyzer.analyze(report)
        thresh_recs, threshold_details = self.threshold_analyzer.analyze(report)
        weight_recs, weight_details = self.weight_analyzer.analyze(report)
        strat_recs, strategy_details = self.strategy_analyzer.analyze(report)

        # 2. Collect and de-duplicate recommendations
        all_recommendations = []
        seen_ids = set()

        for rec in perf_recs + thresh_recs + weight_recs + strat_recs:
            if rec.recommendation_id not in seen_ids:
                all_recommendations.append(rec)
                seen_ids.add(rec.recommendation_id)

        # 3. Calculate summary metrics
        total_recs = len(all_recommendations)

        # Critical adjustments: those with confidence >= 90.0 or category = CONFIDENCE_THRESHOLD / RISK_EXPOSURE
        critical_adjustments = sum(
            1
            for r in all_recommendations
            if r.evidence.confidence_score >= 90.0
            or r.category in ("CONFIDENCE_THRESHOLD", "RISK_EXPOSURE")
        )

        potential_pnl_improvement = sum(
            r.evidence.observed_improvement_potential for r in all_recommendations
        )

        avg_confidence = (
            sum(r.evidence.confidence_score for r in all_recommendations) / total_recs
            if total_recs > 0
            else 0.0
        )

        summary = OptimizationSummary(
            total_recommendations=total_recs,
            critical_adjustments=critical_adjustments,
            potential_pnl_improvement=round(potential_pnl_improvement, 2),
            recommendation_confidence_avg=round(avg_confidence, 2),
        )

        # 4. Construct immutable report
        return OptimizationReport(
            report_id=report_id,
            validation_report_id=report.report_id,
            summary=summary,
            recommendations=all_recommendations,
            strategy_optimizations=strategy_details,
            threshold_recommendations=threshold_details,
            weight_recommendations=weight_details,
            timestamp=now_str(),
        )
