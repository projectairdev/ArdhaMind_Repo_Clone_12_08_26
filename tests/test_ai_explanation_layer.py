from __future__ import annotations

import unittest
from src.models import (
    MarketScore,
    OpportunityContext,
    OpportunityClassification,
    DirectionalBias,
    OpportunityStrength,
    StrategyEvaluation,
    StrategyScore,
    EvaluationSummary,
    TradePlan,
    TradeCandidate,
    PlannerStatistics,
    PlannerSummary,
    ConfidenceReport,
    CandidateConfidence,
    ConfidenceSummary,
    RiskReport,
    CandidateRisk,
    CapitalAllocation,
    ExposureSummary,
    RiskSummary,
    DecisionReport,
    CandidateDecision,
    DecisionSummary,
    DecisionStatistics,
    DecisionReason,
    DecisionWarning,
    EveningReport,
    MarketSummary,
    TomorrowOutlook,
    RecommendedStrategy,
    RecommendedCandidate,
    RiskWatchlist,
    EventWatchlist,
    PlannerChecklist,
    ReportSummary,
    IntradayReport,
    IntradaySummary,
    PlanStatus,
    ActionRecommendation,
    MarketChange,
    CandidateStatusReport,
    CandidateStatus,
    ConfidenceChange,
    RiskChange,
    ExplanationReport,
)
from src.explanation_engine import ExplanationBuilder
from src.dashboard.explanation_panel import ExplanationPanel


class TestAIExplanationLayer(unittest.TestCase):
    """
    Unit test suite covering the stateless AI Explanation Layer.
    Ensures zero calculations, correct mapping of fields, and rich CLI reporting.
    """

    def setUp(self) -> None:
        # 1. Mock Market Score & Opportunity Context
        self.market_score = MarketScore(
            overall_score=78.5,
            letter_grade="B",
            classification="TRENDING",
            timestamp="2026-07-09T12:00:00",
            trend=None,
            options=None,
            volatility=None,
            liquidity=None,
            session=None,
            expiry=None,
            confluence=None,
        )
        self.opportunity = OpportunityContext(
            classification=OpportunityClassification(value="GOOD", description="Good breakout setup"),
            directional_bias=DirectionalBias(value="BULLISH", description="Bullish bias"),
            has_opportunity=True,
            strength=OpportunityStrength(75.0, 80.0, 70.0, 60.0, 90.0),
            warnings=[],
            invalidation_factors=[],
            profile=None,
            timestamp="2026-07-09T12:00:00",
        )

        # 2. Mock Strategy Evaluation
        dummy_score = StrategyScore(
            strategy_name="SCALPING",
            suitability_score=92.0,
            suitability_level="HIGH",
            required_conditions_met=["High Volatility", "Tight Spreads"],
        )
        self.strategy_evaluation = StrategyEvaluation(
            overall_best_strategy="SCALPING",
            evaluations=[dummy_score],
            momentum_evaluation=dummy_score,
            breakout_evaluation=dummy_score,
            trend_following_evaluation=dummy_score,
            mean_reversion_evaluation=dummy_score,
            range_evaluation=dummy_score,
            expiry_evaluation=dummy_score,
            scalping_evaluation=dummy_score,
            summary=EvaluationSummary(["SCALPING"], 1, 0, ["Scalping matches today's fast momentum."]),
            timestamp="2026-07-09T12:00:00",
        )

        # 3. Mock Trade Plan & Candidate
        self.candidate_id = "SCALPING_NIFTY26NOV24200CE"
        self.tradingsymbol = "NIFTY26NOV24200CE"
        self.candidate = TradeCandidate(
            candidate_id=self.candidate_id,
            strategy_name="SCALPING",
            tradingsymbol=self.tradingsymbol,
            strike=24200.0,
            instrument_type="CE",
            expiry="2026-11-26",
            distance_from_atm=10.0,
            atm_distance_class="ATM",
            oi=500000,
            volume=25000,
            spread_pct=0.02,
            iv=15.5,
            tradability_score=85.0,
            suitability_score=90.0,
            ranking_score=88.0,
            rank=1,
        )
        self.trade_plan = TradePlan(
            trade_plan_id="TP_001",
            accepted_candidates=[self.candidate],
            rejected_candidates=[],
            statistics=PlannerStatistics(1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 88.0),
            summary=PlannerSummary("SCALPING_NIFTY26NOV24200CE", ["Execute Best Candidate"]),
            timestamp="2026-07-09T12:00:00",
        )

        # 4. Mock Confidence Report
        self.confidence_report = ConfidenceReport(
            report_id="CR_001",
            trade_plan_id="TP_001",
            candidate_confidences=[
                CandidateConfidence(
                    candidate_id=self.candidate_id,
                    tradingsymbol=self.tradingsymbol,
                    strategy_name="SCALPING",
                    confidence_score=85.0,
                    raw_score=82.0,
                )
            ],
            summary=ConfidenceSummary(self.candidate_id, self.candidate_id, 85.0, 1, ["High confidence CE option."]),
        )

        # 5. Mock Risk Report
        self.risk_report = RiskReport(
            report_id="RR_001",
            confidence_report_id="CR_001",
            candidate_risks=[
                CandidateRisk(
                    candidate_id=self.candidate_id,
                    tradingsymbol=self.tradingsymbol,
                    strategy_name="SCALPING",
                    risk_grade="LOW_RISK",
                    capital_allocation=CapitalAllocation(
                        allocated_capital=40000.0,
                        allocated_lots=2,
                        risk_amount=1000.0,
                        utilization_pct=8.0,
                        confidence_score=85.0,
                        risk_multiplier=1.2,
                    ),
                    is_approved=True,
                )
            ],
            exposure_summary=ExposureSummary(40000.0, 8.0),
            summary=RiskSummary(self.candidate_id, self.candidate_id, "CONSERVATIVE", 0, ["Portfolio is well diversified."]),
        )

        # 6. Mock Decision Report
        self.decision_report = DecisionReport(
            report_id="DR_001",
            risk_report_id="RR_001",
            candidate_decisions=[
                CandidateDecision(
                    candidate_id=self.candidate_id,
                    tradingsymbol=self.tradingsymbol,
                    strategy_name="SCALPING",
                    decision="BUY",
                    priority_score=92.0,
                    execution_priority=1,
                    allocated_capital=40000.0,
                    allocated_lots=2,
                    explanation="Top-ranked candidate with premium confidence and low risk.",
                    supporting_evidence=[
                        DecisionReason("HIGH_CONFIDENCE", "Candidate had confidence of 85.0%", "confidence", 85.0)
                    ],
                    blocking_factors=[],
                    warnings=[],
                )
            ],
            summary=DecisionSummary("EXECUTE", self.candidate_id, "Portfolio parameters within green bands.", []),
            stats=DecisionStatistics(1, 1, 0, 0, 0, 0, 40000.0),
        )

        # 7. Mock Evening Report
        self.evening_report = EveningReport(
            report_id="ER_001",
            market_summary=MarketSummary(24200.0, 15.5, "VOLATILE", "UPTREND", 78.5, "B", "REGULAR"),
            tomorrow_outlook=TomorrowOutlook("BULLISH", "BREAKOUT", 75.0, [24100.0], [24300.0], "Expecting positive open."),
            recommended_strategies=[RecommendedStrategy("SCALPING", 92.0, "HIGH", ["Premium momentum"])],
            top_candidates=[RecommendedCandidate(self.candidate_id, self.tradingsymbol, "SCALPING", "BUY", 85.0, 92.0, 40000.0, 2, 24200.0, "CE", "2026-11-26")],
            checklist=PlannerChecklist(["Check VIX open"]),
            summary=ReportSummary(self.candidate_id, "SCALPING", 1, 0, "BUY"),
        )

        # 8. Mock Intraday Report
        self.intraday_report = IntradayReport(
            report_id="IR_001",
            evening_report_id="ER_001",
            summary=IntradaySummary(PlanStatus.VALID, ActionRecommendation.PROCEED, 1, 0, 1, 0.0, 0.5),
            market_changes=[MarketChange("VIX", 15.5, 16.0, 3.2, False, "VIX is stable.")],
            candidate_changes=[CandidateStatusReport(self.candidate_id, self.tradingsymbol, CandidateStatus.UNCHANGED, "Maintains strength", "BUY", "BUY")],
            confidence_changes=[ConfidenceChange(self.candidate_id, 85.0, 85.0, 0.0, CandidateStatus.UNCHANGED, "No confidence changes")],
            risk_changes=[RiskChange(self.candidate_id, "LOW_RISK", "LOW_RISK", False, [])],
            validation_reasons=["Spot is above support level."],
        )

    def test_decision_explanations(self) -> None:
        """
        Tests the decision explainer on BUY, SELL, WATCH, REJECT, and NO TRADE decisions.
        """
        # Create decisions with different recommendations
        decisions = [
            CandidateDecision(
                candidate_id="C1", tradingsymbol="SYM1", strategy_name="SCALPING",
                decision="BUY", priority_score=95.0, execution_priority=1, allocated_capital=20000.0, allocated_lots=1,
                explanation="BUY reason", supporting_evidence=[DecisionReason("TEST", "Supported by trend", "trend", 1.0)]
            ),
            CandidateDecision(
                candidate_id="C2", tradingsymbol="SYM2", strategy_name="SCALPING",
                decision="SELL", priority_score=90.0, execution_priority=2, allocated_capital=20000.0, allocated_lots=1,
                explanation="SELL reason"
            ),
            CandidateDecision(
                candidate_id="C3", tradingsymbol="SYM3", strategy_name="SCALPING",
                decision="WATCH", priority_score=70.0, execution_priority=3, allocated_capital=0.0, allocated_lots=0,
                explanation="WATCH reason", blocking_factors=[DecisionReason("TEST_BLOCK", "Spread is wide", "spread", 2.0)]
            ),
            CandidateDecision(
                candidate_id="C4", tradingsymbol="SYM4", strategy_name="SCALPING",
                decision="REJECT", priority_score=30.0, execution_priority=4, allocated_capital=0.0, allocated_lots=0,
                explanation="REJECT reason", blocking_factors=[DecisionReason("TEST_REJECT", "Risk limit exceeded", "risk", 2.0)]
            ),
            CandidateDecision(
                candidate_id="C5", tradingsymbol="SYM5", strategy_name="SCALPING",
                decision="NO TRADE", priority_score=10.0, execution_priority=5, allocated_capital=0.0, allocated_lots=0,
                explanation="NO TRADE reason"
            ),
        ]
        dr = DecisionReport(
            report_id="DR_TEST", risk_report_id="RR_TEST", candidate_decisions=decisions,
            summary=DecisionSummary("HOLD", "C1", "System overall hold.", []),
            stats=DecisionStatistics(5, 1, 1, 1, 1, 1, 40000.0)
        )

        from src.explanation_engine.decision_explainer import explain_decisions
        explanation = explain_decisions(dr, self.risk_report, self.confidence_report, self.trade_plan)

        self.assertEqual(explanation.overall_action, "HOLD")
        self.assertEqual(len(explanation.candidate_explanations), 5)

        # Assert correct decision reasoning formats
        buy_exp = next(ce for ce in explanation.candidate_explanations if ce.candidate_id == "C1")
        self.assertIn("BUY", buy_exp.decision_reasoning)
        self.assertIn("Supported by trend", buy_exp.decision_reasoning)

        sell_exp = next(ce for ce in explanation.candidate_explanations if ce.candidate_id == "C2")
        self.assertIn("SELL", sell_exp.decision_reasoning)

        watch_exp = next(ce for ce in explanation.candidate_explanations if ce.candidate_id == "C3")
        self.assertIn("WATCH", watch_exp.decision_reasoning)
        self.assertIn("Spread is wide", watch_exp.decision_reasoning)

        reject_exp = next(ce for ce in explanation.candidate_explanations if ce.candidate_id == "C4")
        self.assertIn("REJECTED", reject_exp.decision_reasoning)
        self.assertIn("Risk limit exceeded", reject_exp.decision_reasoning)

        nt_exp = next(ce for ce in explanation.candidate_explanations if ce.candidate_id == "C5")
        self.assertIn("NO TRADE", nt_exp.decision_reasoning)

    def test_risk_explanation(self) -> None:
        """
        Tests the risk explainer mapped constraints, capital allocations, and portfolio utilization.
        """
        from src.explanation_engine.risk_explainer import explain_risk
        risk_exp = explain_risk(self.risk_report)

        self.assertEqual(risk_exp.portfolio_risk_grade, "CONSERVATIVE")
        self.assertEqual(risk_exp.total_capital_allocated, 40000.0)
        self.assertEqual(risk_exp.portfolio_utilization_pct, 8.0)
        self.assertIn("CONSERVATIVE", risk_exp.portfolio_risk_reasoning)

    def test_confidence_explanation(self) -> None:
        """
        Tests the confidence explainer high convict choices and findings.
        """
        from src.explanation_engine.confidence_explainer import explain_confidence
        conf_exp = explain_confidence(self.confidence_report)

        self.assertEqual(conf_exp.highest_confidence_candidate_id, self.candidate_id)
        self.assertIn("85.0%", conf_exp.confidence_reasoning)
        self.assertIn("High confidence CE option.", conf_exp.confidence_reasoning)

    def test_strategy_explanation(self) -> None:
        """
        Tests strategy explainer prioritization based on regime.
        """
        from src.explanation_engine.strategy_explainer import explain_strategy
        strat_exp = explain_strategy(self.strategy_evaluation, self.opportunity, self.market_score)

        self.assertEqual(strat_exp.overall_best_strategy, "SCALPING")
        self.assertIn("SCALPING", strat_exp.strategy_reasoning)
        self.assertIn("market score of 78.5", strat_exp.strategy_reasoning)
        self.assertTrue(any("SCALPING" in s for s in strat_exp.all_strategy_scores))

    def test_planner_explanation(self) -> None:
        """
        Tests planner tomorrow outlook description and key levels.
        """
        from src.explanation_engine.planner_explainer import explain_planner
        planner_exp = explain_planner(self.evening_report)

        self.assertEqual(planner_exp.directional_bias, "BULLISH")
        self.assertEqual(planner_exp.outlook_classification, "BREAKOUT")
        self.assertIn("Expecting positive open", planner_exp.explanation)
        self.assertIn("24100", planner_exp.explanation)

    def test_intraday_explanation_plan_validations(self) -> None:
        """
        Tests intraday assistant deviations, plan statuses, and recommendations.
        """
        from src.explanation_engine.intraday_explainer import explain_intraday
        intraday_exp = explain_intraday(self.intraday_report)

        self.assertEqual(intraday_exp.plan_status, "Plan Still Valid")
        self.assertEqual(intraday_exp.action_recommendation, "PROCEED")
        self.assertIn("PROCEED", intraday_exp.explanation)
        self.assertTrue(any("UNCHANGED" in c for c in intraday_exp.candidate_change_reasons))

    def test_builder_aggregates_into_report(self) -> None:
        """
        Tests that ExplanationBuilder statelessly assembles everything.
        """
        report = ExplanationBuilder.build(
            decision_report=self.decision_report,
            risk_report=self.risk_report,
            confidence_report=self.confidence_report,
            trade_plan=self.trade_plan,
            strategy_evaluation=self.strategy_evaluation,
            opportunity=self.opportunity,
            market_score=self.market_score,
            evening_report=self.evening_report,
            intraday_report=self.intraday_report,
        )

        self.assertIsInstance(report, ExplanationReport)
        self.assertTrue(report.report_id.startswith("EXP_REP_"))
        self.assertIsNotNone(report.summary)
        self.assertIsNotNone(report.decision)
        self.assertIsNotNone(report.risk)
        self.assertIsNotNone(report.confidence)
        self.assertIsNotNone(report.strategy)
        self.assertIsNotNone(report.intraday)
        self.assertIsNotNone(report.planner)

        # Confirm zero calculation rule: output matches source fields precisely
        self.assertEqual(report.decision.overall_action, "EXECUTE")
        self.assertEqual(report.strategy.overall_best_strategy, "SCALPING")

    def test_explanation_panel_render(self) -> None:
        """
        Tests presentation data mapping and visual terminal output in ExplanationPanel.
        """
        report = ExplanationBuilder.build(
            decision_report=self.decision_report,
            risk_report=self.risk_report,
            confidence_report=self.confidence_report,
            trade_plan=self.trade_plan,
            strategy_evaluation=self.strategy_evaluation,
            opportunity=self.opportunity,
            market_score=self.market_score,
            evening_report=self.evening_report,
            intraday_report=self.intraday_report,
        )

        panel = ExplanationPanel(report)
        p_dict = panel.to_dict()

        # Check dictionary presentation mapping
        self.assertEqual(p_dict["report_id"], report.report_id)
        self.assertEqual(p_dict["summary"]["title"], "Trading Workstation Explanation Report")
        self.assertEqual(p_dict["decision"]["overall_action"], "EXECUTE")

        # Check visual CLI output
        cli_output = panel.render_cli()
        self.assertIn("AI EXPLANATION ENGINE REPORT", cli_output)
        self.assertIn("TITLE        : Trading Workstation Explanation Report", cli_output)
        self.assertIn("Best Choice: SCALPING", cli_output)
        self.assertIn("Overall Action: EXECUTE", cli_output)


if __name__ == "__main__":
    unittest.main()
