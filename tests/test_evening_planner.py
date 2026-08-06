from __future__ import annotations

import unittest
from datetime import datetime
from src.models import (
    DecisionReport,
    CandidateDecision,
    DecisionSummary,
    DecisionStatistics,
    DecisionWarning,
    RiskReport,
    CandidateRisk,
    RiskSummary,
    ExposureSummary,
    PortfolioConstraint,
    RiskWarning,
    CapitalAllocation,
    ConfidenceReport,
    CandidateConfidence,
    ConfidenceSummary,
    TradePlan,
    TradeCandidate,
    PlannerStatistics,
    PlannerSummary,
    CandidateRejection,
    StrategyEvaluation,
    StrategyScore,
    StrategyReason,
    StrategyWarning,
    StrategyConstraint,
    EvaluationSummary,
    OpportunityContext,
    OpportunityClassification,
    OpportunityProfile,
    OpportunityStrength,
    DirectionalBias,
    OpportunityWarning,
    InvalidationFactor,
    MarketScore,
    TrendScore,
    OptionScore,
    VolatilityScore,
    LiquidityScore,
    SessionScore,
    ExpiryScore,
    ConfluenceScore,
    OptimizationReport,
    OptimizationSummary,
    OptimizationRecommendation,
    RecommendationEvidence,
    MarketContext,
    EveningReport,
)
from src.planner import (
    EveningPlanner,
    format_evening_report_cli,
    compile_market_summary,
    compile_tomorrow_outlook,
    compile_strategy_summary,
    compile_recommended_candidates,
    compile_rejected_candidates,
    compile_risk_watchlist,
    compile_event_watchlist,
    generate_checklist,
)


class TestEveningPlanner(unittest.TestCase):
    def setUp(self) -> None:
        # 1. MarketScore
        trend_score = TrendScore(80.0, 85.0, 75.0, 70.0, 80.0, 78.0)
        option_score = OptionScore(
            75.0, 70.0, 80.0, 85.0, 90.0, 60.0, 70.0, 75.7
        )
        vol_score = VolatilityScore(65.0, 70.0, 60.0, 80.0, 70.0, 69.0)
        liq_score = LiquidityScore(90.0, 95.0, 85.0, 90.0, 90.0)
        session_score = SessionScore(100.0, 100.0, 100.0)
        exp_score = ExpiryScore(80.0, 70.0, 90.0, 80.0)
        conf_score = ConfluenceScore(80.0, 85.0, 75.0, 80.0, 90.0, 82.0)

        self.market_score = MarketScore(
            trend=trend_score,
            options=option_score,
            volatility=vol_score,
            liquidity=liq_score,
            session=session_score,
            expiry=exp_score,
            confluence=conf_score,
            overall_score=82.5,
            letter_grade="A",
            classification="Excellent",
            timestamp="2026-11-09T15:30:00",
        )

        # 2. OpportunityContext
        self.opp_classification = OpportunityClassification(
            value="EXCELLENT",
            description="Strong trend alignment with heavy option open interest support.",
        )
        self.opp_strength = OpportunityStrength(
            imbalance_magnitude=75.0,
            trend_force=80.0,
            option_force=85.0,
            liquidity_force=90.0,
            overall_strength=82.5,
        )
        self.opp_profile = OpportunityProfile(
            opportunity_type="TREND_CONTINUATION",
            momentum_suitability="SUITABLE",
            breakout_suitability="SUITABLE",
            reversal_suitability="UNSUITABLE",
            range_suitability="UNSUITABLE",
            scalping_suitability="SUITABLE",
            trend_following_suitability="SUITABLE",
            expiry_suitability="NEUTRAL",
            suitability_reasons=["Strong momentum", "No structural blocks"],
        )
        self.opportunity_context = OpportunityContext(
            classification=self.opp_classification,
            profile=self.opp_profile,
            strength=self.opp_strength,
            directional_bias=DirectionalBias("BULLISH", "Strong upward bias"),
            warnings=[
                OpportunityWarning(
                    "GAP_RISK", "Potential morning gap risk.", "LOW"
                )
            ],
            invalidation_factors=[
                InvalidationFactor(
                    "LOSS_OF_TREND_ALIGNMENT",
                    False,
                    "No trend invalidation signs.",
                )
            ],
            has_opportunity=True,
            timestamp="2026-11-09T15:30:00",
        )

        # 3. MarketContext
        self.market_context = MarketContext(
            current_spot=24200.0,
            timestamp="2026-11-09T15:30:00",
            trading_session="NORMAL",
            current_expiry="2026-11-26",
            market_regime="TRENDING",
            trend_direction="BULLISH",
            trend_strength=75.0,
            support_levels=[24100.0, 24000.0],
            resistance_levels=[24300.0, 24400.0],
            vwap=24180.0,
            atr=150.0,
            india_vix=19.5,  # High VIX to trigger alert
            volatility_state="NORMAL",
        )

        # 4. StrategyEvaluation
        reasons = [StrategyReason("ACCURACY", "Historical success is high.")]
        warnings = [
            StrategyWarning(
                "VOLATILITY", "Higher volatility might widen stops", "LOW"
            )
        ]
        self.strategy_evaluation = StrategyEvaluation(
            overall_best_strategy="TREND_FOLLOWING",
            evaluations=[
                StrategyScore(
                    strategy_name="TREND_FOLLOWING",
                    suitability_score=90.0,
                    suitability_level="HIGH",
                    reasons=reasons,
                    warnings=warnings,
                ),
                StrategyScore(
                    strategy_name="SCALPING",
                    suitability_score=75.0,
                    suitability_level="HIGH",
                    reasons=reasons,
                ),
                StrategyScore(
                    strategy_name="MEAN_REVERSION",
                    suitability_score=30.0,
                    suitability_level="LOW",
                ),
            ],
            momentum_evaluation=StrategyScore(
                "MOMENTUM", 50.0, "MEDIUM", reasons=reasons
            ),
            breakout_evaluation=StrategyScore(
                "BREAKOUT", 50.0, "MEDIUM", reasons=reasons
            ),
            trend_following_evaluation=StrategyScore(
                "TREND_FOLLOWING", 90.0, "HIGH", reasons=reasons
            ),
            mean_reversion_evaluation=StrategyScore(
                "MEAN_REVERSION", 30.0, "LOW"
            ),
            range_evaluation=StrategyScore("RANGE", 40.0, "LOW"),
            expiry_evaluation=StrategyScore("EXPIRY", 40.0, "LOW"),
            scalping_evaluation=StrategyScore(
                "SCALPING", 75.0, "HIGH", reasons=reasons
            ),
            summary=EvaluationSummary(
                top_strategies=["TREND_FOLLOWING", "SCALPING"],
                suitable_strategies_count=2,
                unsuitable_strategies_count=5,
                conclusions=["Trend following is optimal today."],
            ),
            timestamp="2026-11-09T15:30:00",
        )

        # 5. TradePlan
        self.accepted_candidates = [
            TradeCandidate(
                candidate_id="TREND_FOLLOWING_NIFTY26NOV24200CE",
                strategy_name="TREND_FOLLOWING",
                tradingsymbol="NIFTY26NOV24200CE",
                strike=24200.0,
                instrument_type="CE",
                expiry="2026-11-26",
                distance_from_atm=0.0,
                atm_distance_class="ATM",
                oi=1200000,
                volume=450000,
                spread_pct=0.02,
                iv=15.5,
                tradability_score=92.0,
                suitability_score=95.0,
                ranking_score=94.0,
                rank=1,
            ),
            TradeCandidate(
                candidate_id="SCALPING_NIFTY26NOV24150CE",
                strategy_name="SCALPING",
                tradingsymbol="NIFTY26NOV24150CE",
                strike=24150.0,
                instrument_type="CE",
                expiry="2026-11-26",
                distance_from_atm=-50.0,
                atm_distance_class="ATM_MINUS_1",
                oi=800000,
                volume=300000,
                spread_pct=0.03,
                iv=15.2,
                tradability_score=88.0,
                suitability_score=85.0,
                ranking_score=86.5,
                rank=2,
            ),
        ]
        self.rejected_candidates = [
            CandidateRejection(
                strategy_name="MEAN_REVERSION",
                tradingsymbol="NIFTY26NOV24300CE",
                reason_type="STRATEGY_UNSUITABLE",
                message="Mean reversion strategy suitability score too low.",
            )
        ]
        self.trade_plan = TradePlan(
            trade_plan_id="PLAN_MOCK_123",
            accepted_candidates=self.accepted_candidates,
            rejected_candidates=self.rejected_candidates,
            statistics=PlannerStatistics(3, 2, 1, 0, 0, 1, 0, 0, 0, 1, 90.25),
            summary=PlannerSummary("TREND_FOLLOWING_NIFTY26NOV24200CE", ["Plan looks good"]),
            timestamp="2026-11-09T15:30:00",
        )

        # 6. ConfidenceReport
        self.confidence_report = ConfidenceReport(
            report_id="CONF_REP_MOCK_123",
            trade_plan_id="PLAN_MOCK_123",
            candidate_confidences=[
                CandidateConfidence(
                    "TREND_FOLLOWING_NIFTY26NOV24200CE",
                    "NIFTY26NOV24200CE",
                    "TREND_FOLLOWING",
                    88.0,
                    85.0,
                ),
                CandidateConfidence(
                    "SCALPING_NIFTY26NOV24150CE",
                    "NIFTY26NOV24150CE",
                    "SCALPING",
                    78.2,
                    75.0,
                ),
            ],
            summary=ConfidenceSummary(
                "TREND_FOLLOWING_NIFTY26NOV24200CE",
                "SCALPING_NIFTY26NOV24150CE",
                83.1,
                2,
            ),
            timestamp="2026-11-09T15:30:00",
        )

        # 7. RiskReport
        self.risk_report = RiskReport(
            report_id="RISK_REP_MOCK_123",
            confidence_report_id="CONF_REP_MOCK_123",
            candidate_risks=[
                CandidateRisk(
                    candidate_id="TREND_FOLLOWING_NIFTY26NOV24200CE",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="TREND_FOLLOWING",
                    risk_grade="LOW_RISK",
                    capital_allocation=CapitalAllocation(
                        40000.0, 8, 3200.0, 26.67, 88.0, 1.0
                    ),
                    warnings=[
                        RiskWarning(
                            "EXPOSURE_WARNING",
                            "Nearing individual position limits",
                            "MEDIUM",
                        )
                    ],
                    constraints=[
                        PortfolioConstraint(
                            "MAX_CONCURRENT_TRADES", 4.0, 2.0, False
                        ),
                        PortfolioConstraint(
                            "MAX_PORTFOLIO_EXPOSURE",
                            150000.0,
                            160000.0,
                            True,  # Trigger violation
                        ),
                    ],
                    is_approved=True,
                )
            ],
            exposure_summary=ExposureSummary(
                total_capital_allocated=40000.0,
                portfolio_utilization_pct=26.67,
            ),
            summary=RiskSummary(
                "TREND_FOLLOWING_NIFTY26NOV24200CE",
                "TREND_FOLLOWING_NIFTY26NOV24200CE",
                "MODERATE",
                1,
                ["Exposure is within tolerance except max portfolio warning."],
            ),
            timestamp="2026-11-09T15:30:00",
        )

        # 8. DecisionReport
        self.decision_report = DecisionReport(
            report_id="DECISION_REP_MOCK_123",
            risk_report_id="RISK_REP_MOCK_123",
            candidate_decisions=[
                CandidateDecision(
                    candidate_id="TREND_FOLLOWING_NIFTY26NOV24200CE",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="TREND_FOLLOWING",
                    decision="BUY",
                    priority_score=94.0,
                    execution_priority=1,
                    explanation="Strong momentum buy candidate.",
                    allocated_capital=40000.0,
                    allocated_lots=8,
                    warnings=[
                        DecisionWarning(
                            "SPREAD_RISK",
                            "Spread slightly wide but acceptable.",
                            "LOW",
                        )
                    ],
                )
            ],
            priority_ranking=["TREND_FOLLOWING_NIFTY26NOV24200CE"],
            summary=DecisionSummary(
                "EXECUTE",
                "TREND_FOLLOWING_NIFTY26NOV24200CE",
                "Portfolio has capacity for deployment.",
                ["Execute high priority buys"],
            ),
            stats=DecisionStatistics(2, 1, 0, 0, 0, 1, 40000.0),
            timestamp="2026-11-09T15:30:00",
        )

        # 9. OptimizationReport
        self.optimization_report = OptimizationReport(
            report_id="OPT_REP_MOCK_123",
            validation_report_id="VAL_REP_MOCK_123",
            summary=OptimizationSummary(1, 0, 5.5, 80.0),
            recommendations=[
                OptimizationRecommendation(
                    recommendation_id="REC_1",
                    category="CONFIDENCE_THRESHOLD",
                    title="Lower Trend Following Entry Threshold",
                    description="Lowering entry confidence threshold improves capture rate.",
                    current_value="70.0",
                    recommended_value="65.0",
                    evidence=RecommendationEvidence(50, 12.5, ["TREND_FOLLOWING"], "Slight drawdown increase", 85.0),
                    rationale="Captures strong trending sessions early.",
                )
            ],
            timestamp="2026-11-09T15:30:00",
        )

    def test_market_summary_generation(self) -> None:
        ms = compile_market_summary(
            self.market_score, self.opportunity_context, self.market_context
        )
        self.assertEqual(ms.spot_price, 24200.0)
        self.assertEqual(ms.vix_price, 19.5)
        self.assertEqual(ms.regime, "TRENDING")
        self.assertEqual(ms.trend_direction, "BULLISH")
        self.assertEqual(ms.market_score, 82.5)
        self.assertEqual(ms.market_grade, "A")

    def test_tomorrow_outlook_generation(self) -> None:
        out = compile_tomorrow_outlook(
            self.opportunity_context, self.market_context
        )
        self.assertEqual(out.directional_bias, "BULLISH")
        self.assertEqual(out.outlook_classification, "EXCELLENT")
        self.assertEqual(out.opportunity_strength, 82.5)
        self.assertIn(24100.0, out.key_support_levels)
        self.assertIn(24300.0, out.key_resistance_levels)

    def test_strategy_summary_generation(self) -> None:
        strategies = compile_strategy_summary(self.strategy_evaluation)
        self.assertEqual(len(strategies), 2)
        self.assertEqual(strategies[0].strategy_name, "TREND_FOLLOWING")
        self.assertEqual(strategies[0].suitability_level, "HIGH")
        self.assertEqual(strategies[0].suitability_score, 90.0)

    def test_candidate_summary_generation(self) -> None:
        rec_candidates = compile_recommended_candidates(
            self.decision_report, self.confidence_report, self.trade_plan
        )
        self.assertEqual(len(rec_candidates), 1)
        self.assertEqual(
            rec_candidates[0].candidate_id, "TREND_FOLLOWING_NIFTY26NOV24200CE"
        )
        self.assertEqual(rec_candidates[0].decision, "BUY")
        self.assertEqual(rec_candidates[0].confidence_score, 88.0)
        self.assertEqual(rec_candidates[0].strike, 24200.0)

        rej_candidates = compile_rejected_candidates(
            self.trade_plan, self.decision_report
        )
        self.assertTrue(len(rej_candidates) >= 1)
        self.assertEqual(rej_candidates[0].strategy_name, "MEAN_REVERSION")

    def test_risk_watchlist_generation(self) -> None:
        rw = compile_risk_watchlist(self.risk_report, self.decision_report)
        self.assertEqual(rw.risk_grade, "MODERATE")
        self.assertEqual(rw.allocated_capital, 40000.0)
        # Check for constraint violation message
        violation_triggered = any(
            "MAX_PORTFOLIO_EXPOSURE" in warning for warning in rw.portfolio_warnings
        )
        self.assertTrue(violation_triggered)

    def test_event_watchlist_generation(self) -> None:
        ev = compile_event_watchlist(
            self.market_score, self.opportunity_context, self.market_context
        )
        self.assertTrue(len(ev.events) > 0)
        self.assertIn("Upcoming Expiry Date: 2026-11-26", ev.events)
        self.assertIn("High VIX Warning: India VIX is at 19.50. Expect wider swings.", ev.events)

    def test_checklist_generation(self) -> None:
        checklist = generate_checklist(
            self.opportunity_context,
            self.market_context,
            best_strategy="BREAKOUT",
            has_portfolio_warnings=True,
        )
        self.assertTrue(len(checklist.checklist_items) > 0)
        # Verify dynamic checklist items
        self.assertTrue(
            any(
                "Confirm opening gap direction aligns with BULLISH bias" in item
                for item in checklist.checklist_items
            )
        )
        self.assertTrue(
            any(
                "Confirm breakout level of 24300.0" in item
                for item in checklist.checklist_items
            )
        )
        self.assertTrue(
            any(
                "India VIX is high" in item
                for item in checklist.checklist_items
            )
        )
        self.assertTrue(
            any(
                "Review and resolve active portfolio constraint" in item
                for item in checklist.checklist_items
            )
        )

    def test_end_to_end_evening_report_generation(self) -> None:
        report = EveningPlanner.generate_report(
            decision_report=self.decision_report,
            risk_report=self.risk_report,
            confidence_report=self.confidence_report,
            trade_plan=self.trade_plan,
            strategy_evaluation=self.strategy_evaluation,
            opportunity_context=self.opportunity_context,
            market_score=self.market_score,
            optimization_report=self.optimization_report,
            market_context=self.market_context,
        )

        self.assertIsInstance(report, EveningReport)
        self.assertEqual(report.summary.best_strategy, "TREND_FOLLOWING")
        self.assertEqual(
            report.summary.best_candidate_id, "TREND_FOLLOWING_NIFTY26NOV24200CE"
        )
        self.assertEqual(report.summary.total_accepted_candidates, 2)
        self.assertEqual(report.summary.total_rejected_candidates, 1)

        # Test CLI formatting does not crash
        cli_output = format_evening_report_cli(report)
        self.assertIn("EVENING PLANNER REPORT", cli_output)
        self.assertIn("[ MARKET SUMMARY ]", cli_output)
        self.assertIn("[ TOMORROW OUTLOOK ]", cli_output)
        self.assertIn("[ RECOMMENDED STRATEGIES ]", cli_output)
        self.assertIn("[ TOP CANDIDATES ]", cli_output)
        self.assertIn("[ REJECTED CANDIDATES ]", cli_output)
        self.assertIn("[ RISK WATCHLIST ]", cli_output)
        self.assertIn("[ MORNING CHECKLIST ]", cli_output)
        self.assertIn("[ OPTIMIZATION NOTES ]", cli_output)
        self.assertIn("[ SUMMARY ]", cli_output)


if __name__ == "__main__":
    unittest.main()
