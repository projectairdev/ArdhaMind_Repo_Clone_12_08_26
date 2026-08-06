from __future__ import annotations

import unittest
from datetime import datetime
from src.models import (
    EveningReport,
    MarketSummary,
    TomorrowOutlook,
    RecommendedCandidate,
    RiskWatchlist,
    EventWatchlist,
    PlannerChecklist,
    ReportSummary,
    MarketContext,
    OptionContext,
    ConfidenceReport,
    CandidateConfidence,
    ConfidenceSummary,
    RiskReport,
    CandidateRisk,
    RiskSummary,
    ExposureSummary,
    DecisionReport,
    CandidateDecision,
    DecisionSummary,
    DecisionStatistics,
    CapitalAllocation,
    PlanStatus,
    CandidateStatus,
    ActionRecommendation,
)
from src.intraday.report_builder import IntradayAssistant, format_intraday_report_cli
from src.pipeline.intraday_pipeline import IntradayPipeline


class TestIntradayAssistant(unittest.TestCase):
    def setUp(self) -> None:
        # Create a standard EveningReport helper mock
        market_summary = MarketSummary(
            spot_price=24200.0,
            vix_price=15.0,
            regime="TRENDING",
            trend_direction="BULLISH",
            market_score=85.0,
            market_grade="B",
            session_type="NORMAL",
        )

        tomorrow_outlook = TomorrowOutlook(
            directional_bias="BULLISH",
            outlook_classification="EXCELLENT",
            opportunity_strength=75.0,
            key_support_levels=[24100.0, 24000.0],
            key_resistance_levels=[24300.0, 24400.0],
            description="Strong bullish momentum expected.",
        )

        candidates = [
            RecommendedCandidate(
                candidate_id="SCALPING_NIFTY26NOV24200CE",
                tradingsymbol="NIFTY26NOV24200CE",
                strategy_name="SCALPING",
                decision="BUY",
                confidence_score=80.0,
                priority_score=85.0,
                allocated_capital=100000.0,
                allocated_lots=2,
                strike=24200.0,
                instrument_type="CE",
                expiry="2026-11-26",
            )
        ]

        risk_watchlist = RiskWatchlist(
            warnings=["[SCALPING_NIFTY26NOV24200CE] Spread is slightly wide"],
            portfolio_warnings=[],
            max_capital_limit=150000.0,
            allocated_capital=100000.0,
            portfolio_utilization_pct=66.6,
            risk_grade="LOW_RISK",
        )

        event_watchlist = EventWatchlist(
            events=[],
            expiry_days_remaining=14.0,
            expiry_type="NORMAL",
        )

        checklist = PlannerChecklist(
            checklist_items=[
                "Trend Aligned",
                "S/R Defined",
                "Volatility Checked",
                "Liquidity Verified",
                "Event Cleared",
                "Risk Limits OK",
                "Is Tradable",
            ]
        )

        summary = ReportSummary(
            best_candidate_id="SCALPING_NIFTY26NOV24200CE",
            best_strategy="SCALPING",
            total_accepted_candidates=1,
            total_rejected_candidates=0,
            action_type="BUY",
        )

        self.evening_report = EveningReport(
            report_id="EVENING_REPORT_MOCK",
            market_summary=market_summary,
            tomorrow_outlook=tomorrow_outlook,
            top_candidates=candidates,
            rejected_candidates=[],
            risk_watchlist=risk_watchlist,
            event_watchlist=event_watchlist,
            checklist=checklist,
            summary=summary,
        )

        # Create a standard real-time MarketContext
        self.live_market_context = MarketContext(
            current_spot=24210.0,
            timestamp="2026-07-10T09:15:00",
            trading_session="NORMAL",
            current_expiry="2026-11-26",
            market_regime="TRENDING",
            trend_direction="BULLISH",
            trend_strength=75.0,
            support_levels=[24100.0],
            resistance_levels=[24300.0],
            india_vix=15.1,
        )

        # Standard real-time OptionContext
        self.live_option_context = OptionContext(
            underlying_spot=24210.0,
            atm_strike=24200.0,
            strike_step=50.0,
            current_weekly_expiry="2026-11-26",
            current_monthly_expiry="2026-11-26",
            time_to_expiry=14.0,
            atm_iv=16.0,
            expected_move=150.0,
            pcr=1.05,
            max_pain=24200.0,
            highest_call_oi=1000000.0,
            highest_put_oi=1050000.0,
            highest_call_oi_change=10000.0,
            highest_put_oi_change=15000.0,
            liquidity_metrics={"avg_spread_pct": 0.05},
        )

        # Standard real-time ConfidenceReport
        self.live_confidence_report = ConfidenceReport(
            report_id="CONF_REP_LIVE_MOCK",
            trade_plan_id="TRADE_PLAN_MOCK",
            candidate_confidences=[
                CandidateConfidence(
                    candidate_id="SCALPING_NIFTY26NOV24200CE",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="SCALPING",
                    confidence_score=82.0,
                    raw_score=82.0,
                    positive_factors=[],
                    negative_factors=[],
                    bonuses=[],
                    penalties=[],
                )
            ],
            summary=ConfidenceSummary(
                highest_confidence_candidate_id="SCALPING_NIFTY26NOV24200CE",
                lowest_confidence_candidate_id="SCALPING_NIFTY26NOV24200CE",
                average_confidence=82.0,
                total_evaluated=1,
                conclusions=[],
            ),
        )

        # Standard real-time RiskReport
        self.live_risk_report = RiskReport(
            report_id="RISK_REPORT_LIVE_MOCK",
            confidence_report_id="CONF_REP_LIVE_MOCK",
            candidate_risks=[
                CandidateRisk(
                    candidate_id="SCALPING_NIFTY26NOV24200CE",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="SCALPING",
                    risk_grade="LOW_RISK",
                    capital_allocation=CapitalAllocation(
                        allocated_capital=100000.0,
                        allocated_lots=2,
                        risk_amount=1000.0,
                        utilization_pct=66.6,
                        confidence_score=82.0,
                        risk_multiplier=1.0,
                    ),
                    warnings=[],
                    constraints=[],
                    is_approved=True,
                )
            ],
            exposure_summary=ExposureSummary(
                total_capital_allocated=100000.0,
                portfolio_utilization_pct=66.6,
                sector_exposures=[],
                directional_exposures=[],
                expiry_exposures=[],
            ),
            summary=RiskSummary(
                highest_risk_candidate_id="SCALPING_NIFTY26NOV24200CE",
                lowest_risk_candidate_id="SCALPING_NIFTY26NOV24200CE",
                portfolio_risk_grade="CONSERVATIVE",
                total_warnings=0,
                conclusions=[],
            ),
        )

        # Standard real-time DecisionReport
        self.live_decision_report = DecisionReport(
            report_id="DECISION_REPORT_LIVE_MOCK",
            risk_report_id="RISK_REPORT_LIVE_MOCK",
            candidate_decisions=[
                CandidateDecision(
                    candidate_id="SCALPING_NIFTY26NOV24200CE",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="SCALPING",
                    decision="BUY",
                    priority_score=85.0,
                    execution_priority=1,
                    explanation="Trend and volume aligned.",
                    supporting_evidence=[],
                    blocking_factors=[],
                    warnings=[],
                    allocated_capital=100000.0,
                    allocated_lots=2,
                )
            ],
            priority_ranking=["SCALPING_NIFTY26NOV24200CE"],
            summary=DecisionSummary(
                overall_action="EXECUTE",
                highest_priority_candidate_id="SCALPING_NIFTY26NOV24200CE",
                portfolio_status_message="Portfolio is normal",
                conclusions=[],
            ),
            stats=DecisionStatistics(
                total_candidates_evaluated=1,
                buy_count=1,
                sell_count=0,
                watch_count=0,
                reject_count=0,
                no_trade_count=0,
                total_allocated_capital=100000.0,
            ),
        )

    def test_plan_validation_valid(self) -> None:
        report = IntradayAssistant.generate_report(
            evening_report=self.evening_report,
            current_market_context=self.live_market_context,
            current_option_context=self.live_option_context,
            current_confidence_report=self.live_confidence_report,
            current_risk_report=self.live_risk_report,
            current_decision_report=self.live_decision_report,
        )

        self.assertEqual(report.summary.plan_status, PlanStatus.VALID)
        self.assertEqual(report.summary.action_recommendation, ActionRecommendation.PROCEED)
        self.assertIn("Plan Still Valid", report.validation_reasons[0])

    def test_trend_reversal_invalidates_plan(self) -> None:
        # Reversing the trend from BULLISH to BEARISH
        reversal_market_context = MarketContext(
            current_spot=24210.0,
            timestamp="2026-07-10T09:15:00",
            trading_session="NORMAL",
            current_expiry="2026-11-26",
            market_regime="TRENDING",
            trend_direction="BEARISH",
            trend_strength=75.0,
            support_levels=[24100.0],
            resistance_levels=[24300.0],
            india_vix=15.1,
        )

        report = IntradayAssistant.generate_report(
            evening_report=self.evening_report,
            current_market_context=reversal_market_context,
            current_option_context=self.live_option_context,
            current_confidence_report=self.live_confidence_report,
            current_risk_report=self.live_risk_report,
            current_decision_report=self.live_decision_report,
        )

        self.assertEqual(report.summary.plan_status, PlanStatus.INVALIDATED)
        self.assertEqual(report.summary.action_recommendation, ActionRecommendation.CANCEL)
        self.assertTrue(any("Trend reversed" in r for r in report.validation_reasons))

    def test_gap_scenarios_needs_review(self) -> None:
        # Market gaps up significantly by > 0.5%
        # Previous spot: 24200.0. Gap spot: 24400.0 (+0.82%)
        gap_market_context = MarketContext(
            current_spot=24400.0,
            timestamp="2026-07-10T09:15:00",
            trading_session="NORMAL",
            current_expiry="2026-11-26",
            market_regime="TRENDING",
            trend_direction="BULLISH",
            trend_strength=75.0,
            support_levels=[24100.0],
            resistance_levels=[24300.0],
            india_vix=15.1,
        )

        report = IntradayAssistant.generate_report(
            evening_report=self.evening_report,
            current_market_context=gap_market_context,
            current_option_context=self.live_option_context,
            current_confidence_report=self.live_confidence_report,
            current_risk_report=self.live_risk_report,
            current_decision_report=self.live_decision_report,
        )

        self.assertEqual(report.summary.plan_status, PlanStatus.NEEDS_REVIEW)
        self.assertEqual(report.summary.action_recommendation, ActionRecommendation.REVIEW)
        self.assertTrue(any("Significant price gap" in r for r in report.validation_reasons))

    def test_candidate_invalidation(self) -> None:
        # Candidate rejected by Decision engine
        rejected_decision_report = DecisionReport(
            report_id="DEC_REP_REJECT_MOCK",
            risk_report_id="RISK_REPORT_LIVE_MOCK",
            candidate_decisions=[
                CandidateDecision(
                    candidate_id="SCALPING_NIFTY26NOV24200CE",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="SCALPING",
                    decision="REJECT",
                    priority_score=0.0,
                    execution_priority=-1,
                    explanation="OI concentration shifted, premium too expensive.",
                    supporting_evidence=[],
                    blocking_factors=[],
                    warnings=[],
                )
            ],
            priority_ranking=[],
            summary=DecisionSummary(
                overall_action="WATCH",
                highest_priority_candidate_id="NONE",
                portfolio_status_message="Candidates rejected",
                conclusions=[],
            ),
            stats=DecisionStatistics(
                total_candidates_evaluated=1,
                buy_count=0,
                sell_count=0,
                watch_count=0,
                reject_count=1,
                no_trade_count=0,
                total_allocated_capital=0.0,
            ),
        )

        report = IntradayAssistant.generate_report(
            evening_report=self.evening_report,
            current_market_context=self.live_market_context,
            current_option_context=self.live_option_context,
            current_confidence_report=self.live_confidence_report,
            current_risk_report=self.live_risk_report,
            current_decision_report=rejected_decision_report,
        )

        self.assertEqual(report.summary.plan_status, PlanStatus.INVALIDATED)
        self.assertEqual(report.summary.action_recommendation, ActionRecommendation.CANCEL)
        self.assertEqual(report.candidate_changes[0].status, CandidateStatus.INVALIDATED)
        self.assertIn("Rejected:", report.candidate_changes[0].explanation)

    def test_intraday_pipeline(self) -> None:
        pipeline = IntradayPipeline()
        report = pipeline.run(
            evening_report=self.evening_report,
            current_market_context=self.live_market_context,
            current_option_context=self.live_option_context,
            current_confidence_report=self.live_confidence_report,
            current_risk_report=self.live_risk_report,
            current_decision_report=self.live_decision_report,
        )

        self.assertIsNotNone(report)
        self.assertEqual(report.evening_report_id, "EVENING_REPORT_MOCK")
        self.assertEqual(report.summary.plan_status, PlanStatus.VALID)

    def test_cli_formatting(self) -> None:
        report = IntradayAssistant.generate_report(
            evening_report=self.evening_report,
            current_market_context=self.live_market_context,
            current_option_context=self.live_option_context,
            current_confidence_report=self.live_confidence_report,
            current_risk_report=self.live_risk_report,
            current_decision_report=self.live_decision_report,
        )

        cli_text = format_intraday_report_cli(report)
        self.assertIn("INTRADAY ASSISTANT MONITOR", cli_text)
        self.assertIn("Plan Validity Status:", cli_text)
        self.assertIn("Workflow Action:", cli_text)
        self.assertIn("CANDIDATE CHANGES", cli_text)
        self.assertIn("CONFIDENCE CHANGES", cli_text)
        self.assertIn("RISK CHANGES", cli_text)
