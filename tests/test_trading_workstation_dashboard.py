from __future__ import annotations

import unittest
from datetime import datetime
from src.models import (
    MarketScore,
    TrendScore,
    OptionScore,
    VolatilityScore,
    LiquidityScore,
    SessionScore,
    ExpiryScore,
    ConfluenceScore,
    OpportunityContext,
    OpportunityClassification,
    DirectionalBias,
    OpportunityStrength,
    OpportunityWarning,
    InvalidationFactor,
    OpportunityProfile,
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
    ValidationReport,
    SummaryStatistics,
    ConfidenceStatistics,
    RiskStatistics,
    OutcomeValidation,
    DailyValidation,
    StrategyPerformance,
    DecisionPerformance,
    OptimizationReport,
    OptimizationSummary,
    OptimizationRecommendation,
    RecommendationEvidence,
    StrategyOptimization,
    ThresholdRecommendation,
    WeightRecommendation,
)
from src.dashboard import (
    SummaryPanel,
    MarketPanel,
    StrategyPanel,
    TradePanel,
    RiskPanel,
    ValidationPanel,
    OptimizationPanel,
    PlannerPanel,
    IntradayPanel,
    TradingWorkstationDashboard,
)


class TestTradingWorkstationDashboard(unittest.TestCase):
    def setUp(self) -> None:
        # Mock MarketScore
        self.market_score = MarketScore(
            trend=TrendScore(80.0, 85.0, 90.0, 85.0, 80.0, 84.0),
            options=OptionScore(75.0, 80.0, 77.5, 80.0, 85.0, 75.0, 80.0, 78.0),
            volatility=VolatilityScore(90.0, 85.0, 87.5, 80.0, 85.0, 85.5),
            liquidity=LiquidityScore(95.0, 90.0, 85.0, 90.0, 90.0),
            session=SessionScore(100.0, 100.0, 100.0),
            expiry=ExpiryScore(80.0, 90.0, 85.0, 85.0),
            confluence=ConfluenceScore(85.0, 80.0, 85.0, 90.0, 90.0, 86.0),
            overall_score=85.0,
            letter_grade="B",
            classification="Good",
            timestamp="2026-11-09T17:30:00",
        )

        # Mock OpportunityContext
        self.opportunity = OpportunityContext(
            classification=OpportunityClassification("EXCELLENT", "Prime trending setup"),
            profile=OpportunityProfile(
                opportunity_type="TREND_CONTINUATION",
                momentum_suitability="SUITABLE",
                breakout_suitability="NEUTRAL",
                reversal_suitability="UNSUITABLE",
                range_suitability="UNSUITABLE",
                scalping_suitability="SUITABLE",
                trend_following_suitability="SUITABLE",
                expiry_suitability="NEUTRAL",
            ),
            strength=OpportunityStrength(85.0, 80.0, 90.0, 95.0, 87.5),
            directional_bias=DirectionalBias("BULLISH", "Strong trend alignment"),
            warnings=[
                OpportunityWarning("RESISTANCE_PROXIMITY", "Resistance nearby at 24300", "MEDIUM")
            ],
            invalidation_factors=[
                InvalidationFactor("LOSS_OF_TREND_ALIGNMENT", False, "Trend intact")
            ],
            has_opportunity=True,
            timestamp="2026-11-09T17:30:00",
        )

        # Mock StrategyEvaluation
        self.strategy_evaluation = StrategyEvaluation(
            overall_best_strategy="SCALPING",
            evaluations=[
                StrategyScore(
                    strategy_name="SCALPING",
                    suitability_score=92.0,
                    suitability_level="HIGH",
                ),
                StrategyScore(
                    strategy_name="TREND_FOLLOWING",
                    suitability_score=85.0,
                    suitability_level="HIGH",
                ),
            ],
            momentum_evaluation=StrategyScore("MOMENTUM", 70.0, "MEDIUM"),
            breakout_evaluation=StrategyScore("BREAKOUT", 60.0, "MEDIUM"),
            trend_following_evaluation=StrategyScore("TREND_FOLLOWING", 85.0, "HIGH"),
            mean_reversion_evaluation=StrategyScore("MEAN_REVERSION", 40.0, "LOW"),
            range_evaluation=StrategyScore("RANGE", 30.0, "LOW"),
            expiry_evaluation=StrategyScore("EXPIRY", 50.0, "MEDIUM"),
            scalping_evaluation=StrategyScore("SCALPING", 92.0, "HIGH"),
            summary=EvaluationSummary(
                top_strategies=["SCALPING", "TREND_FOLLOWING"],
                suitable_strategies_count=2,
                unsuitable_strategies_count=1,
                conclusions=["Scalping and Trend Following are highly suitable today."],
            ),
            timestamp="2026-11-09T17:30:00",
        )

        # Mock TradePlan
        self.trade_plan = TradePlan(
            trade_plan_id="PLAN_123",
            accepted_candidates=[
                TradeCandidate(
                    candidate_id="SCALPING_NIFTY26NOV24200CE",
                    strategy_name="SCALPING",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strike=24200.0,
                    instrument_type="CE",
                    expiry="2026-11-26",
                    distance_from_atm=0.0,
                    atm_distance_class="ATM",
                    oi=100000,
                    volume=50000,
                    spread_pct=0.02,
                    iv=16.0,
                    tradability_score=90.0,
                    suitability_score=92.0,
                    ranking_score=91.0,
                    rank=1,
                )
            ],
            rejected_candidates=[],
            statistics=PlannerStatistics(1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 91.0),
            summary=PlannerSummary("SCALPING_NIFTY26NOV24200CE", ["Execute Best Candidate"]),
            timestamp="2026-11-09T17:30:00",
        )

        # Mock ConfidenceReport
        self.confidence_report = ConfidenceReport(
            report_id="CONF_123",
            trade_plan_id="PLAN_123",
            candidate_confidences=[
                CandidateConfidence(
                    candidate_id="SCALPING_NIFTY26NOV24200CE",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="SCALPING",
                    confidence_score=85.0,
                    raw_score=85.0,
                )
            ],
            summary=ConfidenceSummary("SCALPING_NIFTY26NOV24200CE", "SCALPING_NIFTY26NOV24200CE", 85.0, 1),
        )

        # Mock RiskReport
        self.risk_report = RiskReport(
            report_id="RISK_123",
            confidence_report_id="CONF_123",
            candidate_risks=[
                CandidateRisk(
                    candidate_id="SCALPING_NIFTY26NOV24200CE",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="SCALPING",
                    risk_grade="LOW_RISK",
                    capital_allocation=CapitalAllocation(100000.0, 2, 1000.0, 66.6, 85.0, 1.0),
                    is_approved=True,
                )
            ],
            exposure_summary=ExposureSummary(100000.0, 66.6),
            summary=RiskSummary("SCALPING_NIFTY26NOV24200CE", "SCALPING_NIFTY26NOV24200CE", "CONSERVATIVE", 0, ["Approved"]),
        )

        # Mock DecisionReport
        self.decision_report = DecisionReport(
            report_id="DEC_123",
            risk_report_id="RISK_123",
            candidate_decisions=[
                CandidateDecision(
                    candidate_id="SCALPING_NIFTY26NOV24200CE",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="SCALPING",
                    decision="BUY",
                    priority_score=92.0,
                    execution_priority=1,
                    explanation="Solid momentum breakout.",
                    allocated_capital=100000.0,
                    allocated_lots=2,
                )
            ],
            priority_ranking=["SCALPING_NIFTY26NOV24200CE"],
            summary=DecisionSummary("EXECUTE", "SCALPING_NIFTY26NOV24200CE", "Portfolio ready"),
            stats=DecisionStatistics(1, 1, 0, 0, 0, 0, 100000.0),
        )

        # Mock EveningReport
        self.evening_report = EveningReport(
            report_id="EVENING_123",
            market_summary=MarketSummary(24200.0, 15.0, "TRENDING", "BULLISH", 85.0, "B", "NORMAL"),
            tomorrow_outlook=TomorrowOutlook("BULLISH", "EXCELLENT", 85.0, [24100.0], [24300.0], "Bullish run"),
            top_candidates=[
                RecommendedCandidate(
                    candidate_id="SCALPING_NIFTY26NOV24200CE",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="SCALPING",
                    decision="BUY",
                    confidence_score=85.0,
                    priority_score=92.0,
                    allocated_capital=100000.0,
                    allocated_lots=2,
                    strike=24200.0,
                    instrument_type="CE",
                    expiry="2026-11-26",
                )
            ],
            risk_watchlist=RiskWatchlist([], [], 150000.0, 100000.0, 66.6, "CONSERVATIVE"),
            event_watchlist=EventWatchlist([], 14.0, "NORMAL"),
            checklist=PlannerChecklist(["Check trend", "Check VIX"]),
            summary=ReportSummary("SCALPING_NIFTY26NOV24200CE", "SCALPING", 1, 0, "BUY"),
            timestamp="2026-11-09T18:00:00",
        )

        # Mock IntradayReport
        self.intraday_report = IntradayReport(
            report_id="INT_123",
            evening_report_id="EVENING_123",
            summary=IntradaySummary(PlanStatus.VALID, ActionRecommendation.PROCEED, 1, 0, 1, 0.0, 0.5),
            market_changes=[MarketChange("VIX", 15.0, 15.5, 3.33, False, "VIX is stable")],
            candidate_changes=[CandidateStatusReport("SCALPING_NIFTY26NOV24200CE", "NIFTY26NOV24200CE", CandidateStatus.UNCHANGED, "Unchanged details", "BUY", "BUY")],
            validation_reasons=["Trend remains bullish"],
            timestamp="2026-11-10T09:30:00",
        )

        # Mock ValidationReport
        self.validation_report = ValidationReport(
            report_id="VAL_123",
            summary_stats=SummaryStatistics(10, 100, 30, 0, 50, 20, 0, 0.3, 82.5),
            outcome_validations=[OutcomeValidation("Same-day", 8, 2, 80.0, 50000.0)],
            strategy_performances=[StrategyPerformance("SCALPING", 50, 20, 0, 20, 10, 0, 84.0)],
            daily_validations=[DailyValidation("2026-11-09", 85.0, 1, 1, 0, 0, 0, 0, 100000.0, "DEC_123", "Successful trade")],
        )

        # Mock OptimizationReport
        self.optimization_report = OptimizationReport(
            report_id="OPT_123",
            validation_report_id="VAL_123",
            summary=OptimizationSummary(3, 1, 120000.0, 88.0),
            recommendations=[
                OptimizationRecommendation(
                    recommendation_id="REC_1",
                    category="CONFIDENCE_THRESHOLD",
                    title="Increase Scalping Threshold",
                    description="Set Scalping entry threshold to 85%",
                    current_value="80.0",
                    recommended_value="85.0",
                    evidence=RecommendationEvidence(100, 15.0, ["SCALPING"], "Fewer trades but higher win rate", 90.0),
                    rationale="Increases accuracy based on last 10 days metrics",
                )
            ],
            strategy_optimizations=[StrategyOptimization("SCALPING", 0.78, "INCREASE_WEIGHT", "Strong current score")],
            threshold_recommendations=[ThresholdRecommendation("scalping_min_conf", 80.0, 85.0, "INCREASE", "Accuracy improvement")],
        )

    def test_summary_panel(self) -> None:
        panel = SummaryPanel(
            market_score=self.market_score,
            opportunity=self.opportunity,
            trade_plan=self.trade_plan,
            confidence=self.confidence_report,
            risk=self.risk_report,
            decision=self.decision_report,
            evening_report=self.evening_report,
            intraday=self.intraday_report,
            validation=self.validation_report,
            optimization=self.optimization_report,
        )

        data = panel.to_dict()["workstation_status"]
        self.assertEqual(data["market_grade"], "B")
        self.assertEqual(data["market_score"], 85.0)
        self.assertEqual(data["top_candidate_id"], "SCALPING_NIFTY26NOV24200CE")
        self.assertEqual(data["best_strategy"], "SCALPING")
        self.assertEqual(data["total_allocated_capital"], 100000.0)

        cli = panel.render_cli()
        self.assertIn("TRADING WORKSTATION OVERVIEW", cli)
        self.assertIn("INR 100000.00", cli)

        # test graceful none handling
        none_panel = SummaryPanel()
        none_data = none_panel.to_dict()["workstation_status"]
        self.assertEqual(none_data["market_grade"], "N/A")
        self.assertEqual(none_data["total_allocated_capital"], 0.0)
        none_cli = none_panel.render_cli()
        self.assertIn("TRADING WORKSTATION OVERVIEW", none_cli)

    def test_market_panel(self) -> None:
        panel = MarketPanel(self.market_score, self.opportunity)
        data = panel.to_dict()
        self.assertEqual(data["market_score"]["overall_score"], 85.0)
        self.assertEqual(data["opportunity"]["classification"], "EXCELLENT")

        cli = panel.render_cli()
        self.assertIn("MARKET & OPPORTUNITY CONTEXT", cli)
        self.assertIn("Trend:  84.0", cli)
        self.assertIn("Opportunity Assessment: EXCELLENT", cli)

        # test graceful none
        none_panel = MarketPanel()
        none_cli = none_panel.render_cli()
        self.assertIn("NOT AVAILABLE", none_cli)

    def test_strategy_panel(self) -> None:
        panel = StrategyPanel(self.strategy_evaluation)
        data = panel.to_dict()
        self.assertEqual(data["overall_best_strategy"], "SCALPING")
        self.assertEqual(len(data["evaluations"]), 2)

        cli = panel.render_cli()
        self.assertIn("STRATEGY EVALUATION SUMMARY", cli)
        self.assertIn("BEST OVERALL STRATEGY: SCALPING", cli)

        # test graceful none
        none_panel = StrategyPanel()
        none_cli = none_panel.render_cli()
        self.assertIn("NOT AVAILABLE", none_cli)

    def test_trade_panel(self) -> None:
        panel = TradePanel(self.trade_plan, self.confidence_report, self.decision_report)
        data = panel.to_dict()
        self.assertEqual(data["top_trade"]["candidate_id"], "SCALPING_NIFTY26NOV24200CE")
        self.assertEqual(data["overall_decision_summary"], "EXECUTE")

        cli = panel.render_cli()
        self.assertIn("TRADE PLAN, CONFIDENCE & DECISION PIPELINE", cli)
        self.assertIn("TOP TRADE RECOMMENDATION: SCALPING_NIFTY26NOV24200CE", cli)

        # test graceful none
        none_panel = TradePanel()
        none_cli = none_panel.render_cli()
        self.assertIn("TOP TRADE RECOMMENDATION: NONE", none_cli)

    def test_risk_panel(self) -> None:
        panel = RiskPanel(self.risk_report)
        data = panel.to_dict()
        self.assertEqual(data["summary"]["portfolio_risk_grade"], "CONSERVATIVE")
        self.assertEqual(data["exposure_summary"]["total_capital_allocated"], 100000.0)

        cli = panel.render_cli()
        self.assertIn("RISK WATCHLIST & PORTFOLIO EXPOSURE", cli)
        self.assertIn("PORTFOLIO RISK GRADE: CONSERVATIVE", cli)

        # test graceful none
        none_panel = RiskPanel()
        none_cli = none_panel.render_cli()
        self.assertIn("NOT AVAILABLE", none_cli)

    def test_validation_panel(self) -> None:
        panel = ValidationPanel(self.validation_report)
        data = panel.to_dict()
        self.assertEqual(data["summary_stats"]["total_days_evaluated"], 10)

        cli = panel.render_cli()
        self.assertIn("HISTORICAL VALIDATION STATISTICS", cli)
        self.assertIn("Days Evaluated : 10", cli)

        # test graceful none
        none_panel = ValidationPanel()
        none_cli = none_panel.render_cli()
        self.assertIn("NOT AVAILABLE", none_cli)

    def test_optimization_panel(self) -> None:
        panel = OptimizationPanel(self.optimization_report)
        data = panel.to_dict()
        self.assertEqual(data["summary"]["total_recommendations"], 3)

        cli = panel.render_cli()
        self.assertIn("SYSTEM OPTIMIZATION ADVISORY", cli)
        self.assertIn("Est PnL Boost  : INR 120,000.00", cli)

        # test graceful none
        none_panel = OptimizationPanel()
        none_cli = none_panel.render_cli()
        self.assertIn("NOT AVAILABLE", none_cli)

    def test_planner_panel(self) -> None:
        panel = PlannerPanel(self.evening_report)
        data = panel.to_dict()
        self.assertEqual(data["tomorrow_outlook"]["directional_bias"], "BULLISH")

        cli = panel.render_cli()
        self.assertIn("EVENING PLANNER & TOMORROW OUTLOOK", cli)
        self.assertIn("Tomorrow Bias: BULLISH", cli)

        # test graceful none
        none_panel = PlannerPanel()
        none_cli = none_panel.render_cli()
        self.assertIn("NOT AVAILABLE", none_cli)

    def test_intraday_panel(self) -> None:
        panel = IntradayPanel(self.intraday_report)
        data = panel.to_dict()
        self.assertEqual(data["summary"]["plan_status"], "Plan Still Valid")

        cli = panel.render_cli()
        self.assertIn("INTRADAY ASSISTANT MONITOR", cli)
        self.assertIn("Plan Validity Status: Plan Still Valid", cli)

        # test graceful none
        none_panel = IntradayPanel()
        none_cli = none_panel.render_cli()
        self.assertIn("NOT AVAILABLE", none_cli)

    def test_trading_workstation_dashboard_assembly(self) -> None:
        dashboard = TradingWorkstationDashboard(
            market_score=self.market_score,
            opportunity=self.opportunity,
            strategy_evaluation=self.strategy_evaluation,
            trade_plan=self.trade_plan,
            confidence_report=self.confidence_report,
            risk_report=self.risk_report,
            decision_report=self.decision_report,
            evening_report=self.evening_report,
            intraday_report=self.intraday_report,
            validation_report=self.validation_report,
            optimization_report=self.optimization_report,
        )

        dict_data = dashboard.to_dict()
        self.assertIsNotNone(dict_data["summary"])
        self.assertIsNotNone(dict_data["market_context"])
        self.assertIsNotNone(dict_data["strategy"])
        self.assertIsNotNone(dict_data["trade_pipeline"])

        cli_output = dashboard.render_cli()
        self.assertIn("UNIFIED TRADING WORKSTATION DASHBOARD", cli_output)
        self.assertIn("TRADING WORKSTATION OVERVIEW", cli_output)
        self.assertIn("MARKET & OPPORTUNITY CONTEXT", cli_output)
        self.assertIn("STRATEGY EVALUATION SUMMARY", cli_output)
        self.assertIn("TRADE PLAN, CONFIDENCE & DECISION PIPELINE", cli_output)
        self.assertIn("RISK WATCHLIST & PORTFOLIO EXPOSURE", cli_output)
        self.assertIn("INTRADAY ASSISTANT MONITOR", cli_output)
        self.assertIn("EVENING PLANNER & TOMORROW OUTLOOK", cli_output)
        self.assertIn("HISTORICAL VALIDATION STATISTICS", cli_output)
        self.assertIn("SYSTEM OPTIMIZATION ADVISORY", cli_output)
        self.assertIn("OPERATOR SESSION LIVE VIEW", cli_output)
