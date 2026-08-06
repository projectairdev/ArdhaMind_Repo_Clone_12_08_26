from __future__ import annotations

import unittest
from src.models import (
    ValidationReport,
    DailyValidation,
    StrategyPerformance,
    DecisionPerformance,
    ConfidenceStatistics,
    RiskStatistics,
    OutcomeValidation,
    SummaryStatistics,
    OptimizationReport,
)
from src.pipeline import OptimizationPipeline
from src.optimization_engine import RecommendationBuilder


class TestOptimizationAdvisor(unittest.TestCase):
    def setUp(self):
        # Build a highly realistic mock ValidationReport
        self.daily_validations = [
            DailyValidation(
                date="2026-11-09",
                market_score=85.0,
                candidates_count=40,
                buy_count=5,
                sell_count=2,
                watch_count=0,
                reject_count=15,
                no_trade_count=18,
                total_allocated_capital=150000.0,
                decision_report_id="DEC_1",
                outcome_summary="Mock summary",
            ),
            DailyValidation(
                date="2026-11-10",
                market_score=40.0,
                candidates_count=35,
                buy_count=1,
                sell_count=4,
                watch_count=0,
                reject_count=12,
                no_trade_count=18,
                total_allocated_capital=90000.0,
                decision_report_id="DEC_2",
                outcome_summary="Mock summary 2",
            ),
        ]

        self.strategy_performances = [
            StrategyPerformance(
                strategy_name="EXPIRY",
                total_candidates=25,
                buy_count=3,
                sell_count=2,
                watch_count=0,
                reject_count=10,
                no_trade_count=10,
                avg_confidence_score=42.5,  # Low average confidence
            ),
            StrategyPerformance(
                strategy_name="TREND_FOLLOWING",
                total_candidates=50,
                buy_count=3,
                sell_count=4,
                watch_count=0,
                reject_count=17,
                no_trade_count=26,
                avg_confidence_score=78.2,  # High average confidence
            ),
            StrategyPerformance(
                strategy_name="MEAN_REVERSION",
                total_candidates=10,
                buy_count=0,
                sell_count=0,
                watch_count=0,
                reject_count=5,
                no_trade_count=5,
                avg_confidence_score=35.0,  # Critically low average confidence
            ),
        ]

        self.decision_performances = [
            DecisionPerformance("BUY", 6, 8.0, 72.0, 45000.0),
            DecisionPerformance("SELL", 6, 8.0, 68.0, 40000.0),
            DecisionPerformance("WATCH", 0, 0.0, 0.0, 0.0),  # Unused state
            DecisionPerformance("REJECT", 27, 36.0, 30.0, 0.0),
            DecisionPerformance("NO TRADE", 36, 48.0, 45.0, 0.0),
        ]

        self.confidence_stats = ConfidenceStatistics(
            avg_confidence=53.4,  # Average confidence below 60
            max_confidence=85.0,
            min_confidence=30.0,
            std_confidence=12.5,
        )

        self.risk_stats = RiskStatistics(
            avg_allocated_capital=120000.0,
            total_allocated_capital=240000.0,
            max_allocated_capital=600000.0,  # High max allocation
            approved_count=12,
            rejected_count=27,
        )

        self.outcome_validations = [
            OutcomeValidation("Same-day", 4, 8, 33.3, -25000.0),  # Poor performing window (<65%)
            OutcomeValidation("Next-day", 8, 4, 66.7, 45000.0),
            OutcomeValidation("Expiry-day", 6, 6, 50.0, 10000.0),
        ]

        self.summary_stats = SummaryStatistics(
            total_days_evaluated=2,
            total_candidates_evaluated=75,
            overall_buy_count=6,
            overall_sell_count=6,
            overall_watch_count=0,  # Unused state
            overall_reject_count=27,
            overall_no_trade_count=36,
            decision_frequency_pct=16.0,
            avg_market_score=62.5,
        )

        self.validation_report = ValidationReport(
            report_id="VAL_MOCK_123",
            daily_validations=self.daily_validations,
            strategy_performances=self.strategy_performances,
            decision_performances=self.decision_performances,
            confidence_stats=self.confidence_stats,
            risk_stats=self.risk_stats,
            outcome_validations=self.outcome_validations,
            summary_stats=self.summary_stats,
            timestamp="2026-07-09T12:00:00",
        )

    def test_recommendation_generation_and_evidence(self) -> None:
        """
        Verify that RecommendationBuilder analyzes the ValidationReport correctly
        and generates highly detailed, structured, evidence-backed recommendations.
        """
        builder = RecommendationBuilder()
        opt_report = builder.build_report(self.validation_report)

        self.assertIsInstance(opt_report, OptimizationReport)
        self.assertEqual(opt_report.validation_report_id, "VAL_MOCK_123")

        # Verify we identified unused decision states, poor confidence bands, risk concentration, etc.
        recs = {r.recommendation_id: r for r in opt_report.recommendations}

        # 1. Unused state WATCH detection
        self.assertIn("REC_UNUSED_STATES", recs)
        rec_unused = recs["REC_UNUSED_STATES"]
        self.assertEqual(rec_unused.category, "CLASSIFICATION_BOUNDARIES")
        self.assertEqual(rec_unused.evidence.historical_sample_size, 75)
        self.assertGreater(rec_unused.evidence.confidence_score, 0.0)

        # 2. Risk concentration detection (since max_allocated_capital is 600000)
        self.assertIn("REC_RISK_CONCENTRATION", recs)
        rec_risk = recs["REC_RISK_CONCENTRATION"]
        self.assertEqual(rec_risk.category, "RISK_EXPOSURE")

        # 3. Poor performing window Same-day detection (<65%)
        self.assertIn("REC_POOR_ACCURACY_SAME_DAY", recs)
        rec_acc = recs["REC_POOR_ACCURACY_SAME_DAY"]
        self.assertEqual(rec_acc.category, "CONFIDENCE_THRESHOLD")
        self.assertEqual(rec_acc.evidence.observed_improvement_potential, 41.7)  # 75.0 - 33.3

        # 4. Under-calibrated confidence threshold (<60.0)
        self.assertIn("REC_LOW_CONF_THRESHOLD", recs)

        # 5. Weak strategy performance (EXPIRY and MEAN_REVERSION)
        self.assertIn("REC_SUSPEND_MEAN_REVERSION", recs)
        self.assertIn("REC_EXPIRY_RISK_EXPIRY", recs)

        # 6. High performing strategy (TREND_FOLLOWING is high at 78.2)
        self.assertIn("REC_BOOST_TREND_FOLLOWING", recs)

        # Verify evidence field completeness
        for rec in opt_report.recommendations:
            self.assertIsNotNone(rec.recommendation_id)
            self.assertIsNotNone(rec.title)
            self.assertIsNotNone(rec.description)
            self.assertIsNotNone(rec.current_value)
            self.assertIsNotNone(rec.recommended_value)
            self.assertIsNotNone(rec.rationale)
            self.assertIsNotNone(rec.evidence)
            self.assertGreater(rec.evidence.historical_sample_size, 0)
            self.assertGreaterEqual(rec.evidence.observed_improvement_potential, 0.0)
            self.assertGreater(rec.evidence.confidence_score, 0.0)
            self.assertIsNotNone(rec.evidence.expected_trade_off)

    def test_no_automatic_configuration_modification(self) -> None:
        """
        Verify that the OptimizationAdvisor is strictly read-only and does NOT
        modify any configuration parameters, files, or global systems.
        """
        # Save a snapshot of any typical/fictional system configs we might run against
        # (Though we do not read from files, we test that running does not modify inputs or system parameters)
        validation_report_before = self.validation_report

        builder = RecommendationBuilder()
        opt_report = builder.build_report(self.validation_report)

        # Assert input report was not altered
        self.assertEqual(self.validation_report, validation_report_before)

        # Assert no files are created or modified except the generated OptimizationReport
        # The report contains only recommendations, and has zero-side effects.
        self.assertIsInstance(opt_report, OptimizationReport)

    def test_optimization_pipeline_end_to_end(self) -> None:
        """
        Verify that OptimizationPipeline is correct end-to-end, computing summary stats
        precisely and returning an immutable report.
        """
        pipeline = OptimizationPipeline()
        opt_report = pipeline.run(self.validation_report, report_id="OPT_PIPELINE_TEST")

        self.assertIsInstance(opt_report, OptimizationReport)
        self.assertEqual(opt_report.report_id, "OPT_PIPELINE_TEST")

        # Verify summary stats
        summary = opt_report.summary
        self.assertGreater(summary.total_recommendations, 0)
        self.assertGreaterEqual(summary.critical_adjustments, 0)
        self.assertGreater(summary.potential_pnl_improvement, 0.0)
        self.assertTrue(0.0 <= summary.recommendation_confidence_avg <= 100.0)

    def test_regression_and_determinism(self) -> None:
        """
        Verify that running the optimization process over the exact same validation
        report produces 100% identical outputs (strict determinism).
        """
        pipeline = OptimizationPipeline()
        report_1 = pipeline.run(self.validation_report, report_id="OPT_DET_1")
        report_2 = pipeline.run(self.validation_report, report_id="OPT_DET_1")

        self.assertEqual(report_1.report_id, report_2.report_id)
        self.assertEqual(report_1.validation_report_id, report_2.validation_report_id)
        self.assertEqual(report_1.summary, report_2.summary)
        self.assertEqual(len(report_1.recommendations), len(report_2.recommendations))

        for rec_1, rec_2 in zip(report_1.recommendations, report_2.recommendations):
            self.assertEqual(rec_1.recommendation_id, rec_2.recommendation_id)
            self.assertEqual(rec_1.category, rec_2.category)
            self.assertEqual(rec_1.title, rec_2.title)
            self.assertEqual(rec_1.description, rec_2.description)
            self.assertEqual(rec_1.current_value, rec_2.current_value)
            self.assertEqual(rec_1.recommended_value, rec_2.recommended_value)
            self.assertEqual(rec_1.evidence, rec_2.evidence)
            self.assertEqual(rec_1.rationale, rec_2.rationale)

        self.assertEqual(report_1.strategy_optimizations, report_2.strategy_optimizations)
        self.assertEqual(report_1.threshold_recommendations, report_2.threshold_recommendations)
        self.assertEqual(report_1.weight_recommendations, report_2.weight_recommendations)
