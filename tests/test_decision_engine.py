from __future__ import annotations

import unittest
from datetime import datetime
from src.models import (
    TradeCandidate,
    CandidateRisk,
    CapitalAllocation,
    RiskReport,
    ExposureSummary,
    RiskSummary,
    ConfidenceReport,
    CandidateConfidence,
    TradePlan,
    StrategyEvaluation,
    StrategyScore,
    EvaluationSummary,
    OpportunityContext,
    OpportunityClassification,
    OpportunityProfile,
    OpportunityStrength,
    DirectionalBias,
    MarketScore,
    TrendScore,
    OptionScore,
    VolatilityScore,
    LiquidityScore,
    SessionScore,
    ExpiryScore,
    ConfluenceScore,
    DecisionEngineConfig,
    CandidateDecision,
    DecisionReport,
)
from src.decision_engine.decision_rules import evaluate_candidate_decision
from src.decision_engine.decision_priority import calculate_priority_score, assign_execution_priorities
from src.decision_engine.decision_explanations import generate_explanations
from src.decision_engine.decision_builder import DecisionBuilder
from src.pipeline.decision_pipeline import DecisionPipeline


class TestDecisionEngine(unittest.TestCase):
    def setUp(self):
        # 1. Create standard candidates
        self.candidate_ce = TradeCandidate(
            candidate_id="CE_CANDIDATE_1",
            strategy_name="MOMENTUM",
            tradingsymbol="NIFTY26OCT24300CE",
            strike=24300.0,
            instrument_type="CE",
            expiry="2026-10-29",
            distance_from_atm=0.0,
            atm_distance_class="ATM",
            oi=50000,
            volume=10000,
            spread_pct=0.15,
            iv=16.5,
            tradability_score=85.0,
            suitability_score=90.0,
            ranking_score=85.0,
            rank=1,
            reasons=[],
            warnings=[],
        )

        self.candidate_pe = TradeCandidate(
            candidate_id="PE_CANDIDATE_1",
            strategy_name="BREAKOUT",
            tradingsymbol="NIFTY26OCT24300PE",
            strike=24300.0,
            instrument_type="PE",
            expiry="2026-10-29",
            distance_from_atm=0.0,
            atm_distance_class="ATM",
            oi=45000,
            volume=9000,
            spread_pct=0.18,
            iv=17.2,
            tradability_score=80.0,
            suitability_score=85.0,
            ranking_score=80.0,
            rank=2,
            reasons=[],
            warnings=[],
        )

        # 2. Risk Candidate Allocations
        self.risk_ce_approved = CandidateRisk(
            candidate_id="CE_CANDIDATE_1",
            tradingsymbol="NIFTY26OCT24300CE",
            strategy_name="MOMENTUM",
            risk_grade="LOW_RISK",
            capital_allocation=CapitalAllocation(
                allocated_capital=12000.0,
                allocated_lots=2,
                risk_amount=12000.0,
                utilization_pct=2.4,
                confidence_score=85.0,
                risk_multiplier=1.0,
            ),
            warnings=[],
            constraints=[],
            is_approved=True,
        )

        self.risk_pe_approved = CandidateRisk(
            candidate_id="PE_CANDIDATE_1",
            tradingsymbol="NIFTY26OCT24300PE",
            strategy_name="BREAKOUT",
            risk_grade="LOW_RISK",
            capital_allocation=CapitalAllocation(
                allocated_capital=15000.0,
                allocated_lots=3,
                risk_amount=15000.0,
                utilization_pct=3.0,
                confidence_score=80.0,
                risk_multiplier=1.0,
            ),
            warnings=[],
            constraints=[],
            is_approved=True,
        )

        # 3. Strategy Evaluation Mock setup
        dummy_score = StrategyScore(
            strategy_name="MOMENTUM",
            suitability_score=80.0,
            suitability_level="HIGH",
        )
        self.strategy_eval = StrategyEvaluation(
            overall_best_strategy="MOMENTUM",
            evaluations=[dummy_score],
            momentum_evaluation=dummy_score,
            breakout_evaluation=dummy_score,
            trend_following_evaluation=dummy_score,
            mean_reversion_evaluation=dummy_score,
            range_evaluation=dummy_score,
            expiry_evaluation=dummy_score,
            scalping_evaluation=dummy_score,
            summary=EvaluationSummary(["MOMENTUM"], 1, 0, ["Good conditions"]),
            timestamp="2026-07-09 10:30:00",
        )

        # 4. Opportunity Context Mock setup
        self.opportunity_ctx = OpportunityContext(
            classification=OpportunityClassification("EXCELLENT", "Great buying opportunity"),
            profile=OpportunityProfile("TREND_CONTINUATION", "SUITABLE", "SUITABLE", "NEUTRAL", "NEUTRAL", "NEUTRAL", "SUITABLE", "NEUTRAL"),
            strength=OpportunityStrength(85.0, 80.0, 90.0, 85.0, 85.0),
            directional_bias=DirectionalBias("BULLISH", "Strong market bias"),
            warnings=[],
            invalidation_factors=[],
            has_opportunity=True,
            timestamp="2026-07-09 10:30:00",
        )

        # 5. Market Score Mock setup
        self.market_score = MarketScore(
            trend=TrendScore(80.0, 100.0, 80.0, 100.0, 100.0, 85.0),
            options=OptionScore(100.0, 100.0, 100.0, 100.0, 85.0, 100.0, 100.0, 95.0),
            volatility=VolatilityScore(100.0, 90.0, 85.0, 100.0, 100.0, 95.0),
            liquidity=LiquidityScore(100.0, 85.0, 100.0, 100.0, 95.0),
            session=SessionScore(100.0, 100.0, 100.0),
            expiry=ExpiryScore(100.0, 100.0, 100.0, 80.0),
            confluence=ConfluenceScore(100.0, 100.0, 100.0, 100.0, 100.0, 90.0),
            overall_score=88.0,
            letter_grade="A",
            classification="Favorable",
            timestamp="2026-07-09 10:30:00",
        )

        self.config = DecisionEngineConfig(
            buy_confidence_threshold=70.0,
            sell_confidence_threshold=70.0,
            watch_confidence_threshold=50.0,
            max_execution_slots=2,
        )

    def test_decision_rules_mapping(self):
        # 1. Approved Call Option with high confidence -> BUY
        decision = evaluate_candidate_decision(
            self.candidate_ce, 85.0, self.risk_ce_approved, self.config
        )
        self.assertEqual(decision, "BUY")

        # 2. Approved Put Option with high confidence -> SELL
        decision_pe = evaluate_candidate_decision(
            self.candidate_pe, 80.0, self.risk_pe_approved, self.config
        )
        self.assertEqual(decision_pe, "SELL")

        # 3. Approved with moderate confidence -> WATCH
        decision_watch = evaluate_candidate_decision(
            self.candidate_ce, 60.0, self.risk_ce_approved, self.config
        )
        self.assertEqual(decision_watch, "WATCH")

        # 4. Rejected by Risk Engine -> REJECT
        risk_rejected = CandidateRisk(
            candidate_id="CE_CANDIDATE_1",
            tradingsymbol="NIFTY26OCT24300CE",
            strategy_name="MOMENTUM",
            risk_grade="REJECTED",
            capital_allocation=CapitalAllocation(0.0, 0, 0.0, 0.0, 0.0, 1.0),
            warnings=[],
            constraints=[],
            is_approved=False,
        )
        decision_rejected = evaluate_candidate_decision(
            self.candidate_ce, 85.0, risk_rejected, self.config
        )
        self.assertEqual(decision_rejected, "REJECT")

        # 5. Low confidence -> REJECT
        decision_low_conf = evaluate_candidate_decision(
            self.candidate_ce, 40.0, self.risk_ce_approved, self.config
        )
        self.assertEqual(decision_low_conf, "REJECT")

    def test_priority_score_and_tie_breaking(self):
        # CE priority score at 85 confidence, 85 tradability
        # Expected: 85 * 0.8 + 85 * 0.2 = 85.0
        score_ce = calculate_priority_score(85.0, 85.0, 12000.0, self.config)
        self.assertEqual(score_ce, 85.0)

        # Create multiple candidates to verify slot limiting and ranking order
        decisions = [
            CandidateDecision(
                candidate_id="CAND_A",
                tradingsymbol="NIFTY26OCT24300CE",
                strategy_name="MOMENTUM",
                decision="BUY",
                priority_score=90.0,
                execution_priority=-1,
                explanation="",
            ),
            CandidateDecision(
                candidate_id="CAND_B",
                tradingsymbol="NIFTY26OCT24350CE",
                strategy_name="MOMENTUM",
                decision="BUY",
                priority_score=90.0,  # Tie score
                execution_priority=-1,
                explanation="",
            ),
            CandidateDecision(
                candidate_id="CAND_C",
                tradingsymbol="NIFTY26OCT24400CE",
                strategy_name="MOMENTUM",
                decision="BUY",
                priority_score=80.0,
                execution_priority=-1,
                explanation="",
            ),
        ]

        # Max execution slots = 2
        ranked = assign_execution_priorities(decisions, self.config)

        # Deterministic tie-breaking on tied priority_score (A-Z alphabetically on candidate_id)
        # CAND_A (priority_score=90.0, candidate_id="CAND_A") gets Rank 1
        # CAND_B (priority_score=90.0, candidate_id="CAND_B") gets Rank 2
        # CAND_C (priority_score=80.0) gets downgraded to WATCH since max slots is 2

        self.assertEqual(ranked[0].candidate_id, "CAND_A")
        self.assertEqual(ranked[0].execution_priority, 1)
        self.assertEqual(ranked[0].decision, "BUY")

        self.assertEqual(ranked[1].candidate_id, "CAND_B")
        self.assertEqual(ranked[1].execution_priority, 2)
        self.assertEqual(ranked[1].decision, "BUY")

        self.assertEqual(ranked[2].candidate_id, "CAND_C")
        self.assertEqual(ranked[2].execution_priority, -1)
        self.assertEqual(ranked[2].decision, "WATCH")

    def test_explanation_generation(self):
        explanation, supporting, blocking, warnings = generate_explanations(
            self.candidate_ce, 85.0, self.risk_ce_approved, "BUY"
        )
        self.assertTrue(any(r.reason_type == "HIGH_CONFIDENCE" for r in supporting))
        self.assertTrue(any(r.reason_type == "RISK_ENGINE_APPROVED" for r in supporting))
        self.assertEqual(len(blocking), 0)

        # Try a high IV warning trigger
        volatile_candidate = TradeCandidate(
            candidate_id="CE_HIGH_IV",
            strategy_name="MOMENTUM",
            tradingsymbol="NIFTY26OCT24300CE",
            strike=24300.0,
            instrument_type="CE",
            expiry="2026-10-29",
            distance_from_atm=0.0,
            atm_distance_class="ATM",
            oi=50000,
            volume=10000,
            spread_pct=0.15,
            iv=30.0,  # > 25
            tradability_score=85.0,
            suitability_score=90.0,
            ranking_score=85.0,
            rank=1,
            reasons=[],
            warnings=[],
        )
        _, _, _, warnings = generate_explanations(volatile_candidate, 85.0, self.risk_ce_approved, "BUY")
        self.assertTrue(any(w.warning_type == "HIGH_IV_WARNING" for w in warnings))

    def test_global_blockers(self):
        extreme_market_score = MarketScore(
            trend=TrendScore(80.0, 100.0, 80.0, 100.0, 100.0, 85.0),
            options=OptionScore(100.0, 100.0, 100.0, 100.0, 85.0, 100.0, 100.0, 95.0),
            volatility=VolatilityScore(100.0, 90.0, 85.0, 100.0, 100.0, 95.0),
            liquidity=LiquidityScore(100.0, 85.0, 100.0, 100.0, 95.0),
            session=SessionScore(100.0, 100.0, 100.0),
            expiry=ExpiryScore(100.0, 100.0, 100.0, 80.0),
            confluence=ConfluenceScore(100.0, 100.0, 100.0, 100.0, 100.0, 90.0),
            overall_score=25.0,  # Extreme low (< 30)
            letter_grade="F",
            classification="Extreme Risk-Off",
            timestamp="2026-07-09 10:30:00",
        )

        risk_report = RiskReport(
            report_id="RISK_123",
            confidence_report_id="CONF_123",
            candidate_risks=[self.risk_ce_approved],
            exposure_summary=ExposureSummary(
                total_capital_allocated=12000.0,
                portfolio_utilization_pct=2.4,
                sector_exposures=[],
                directional_exposures=[],
                expiry_exposures=[],
                option_concentration_pct=100.0,
                capital_concentration_pct=100.0,
            ),
            summary=RiskSummary("CE_CANDIDATE_1", "CE_CANDIDATE_1", "CONSERVATIVE", 0, []),
            timestamp="2026-07-09 10:30:00",
        )

        confidence_report = ConfidenceReport(
            report_id="CONF_123",
            trade_plan_id="PLAN_123",
            candidate_confidences=[
                CandidateConfidence("CE_CANDIDATE_1", "NIFTY26OCT24300CE", "MOMENTUM", 85.0, 85.0)
            ]
        )

        trade_plan = TradePlan(
            trade_plan_id="PLAN_123",
            accepted_candidates=[self.candidate_ce],
            rejected_candidates=[],
        )

        report = DecisionBuilder.build_decision_report(
            risk_report=risk_report,
            confidence_report=confidence_report,
            trade_plan=trade_plan,
            strategy_evaluation=self.strategy_eval,
            opportunity_context=self.opportunity_ctx,
            market_score=extreme_market_score,
            config=self.config,
        )

        # Because of global blockers, CE candidate is forced to WATCH
        self.assertEqual(report.candidate_decisions[0].decision, "WATCH")
        self.assertTrue(any(f.reason_type == "GLOBAL_MARKET_BLOCKER" for f in report.candidate_decisions[0].blocking_factors))

    def test_pipeline_end_to_end(self):
        risk_report = RiskReport(
            report_id="RISK_123",
            confidence_report_id="CONF_123",
            candidate_risks=[self.risk_ce_approved, self.risk_pe_approved],
            exposure_summary=ExposureSummary(
                total_capital_allocated=27000.0,
                portfolio_utilization_pct=5.4,
                sector_exposures=[],
                directional_exposures=[],
                expiry_exposures=[],
                option_concentration_pct=100.0,
                capital_concentration_pct=100.0,
            ),
            summary=RiskSummary("PE_CANDIDATE_1", "CE_CANDIDATE_1", "CONSERVATIVE", 0, []),
            timestamp="2026-07-09 10:30:00",
        )

        confidence_report = ConfidenceReport(
            report_id="CONF_123",
            trade_plan_id="PLAN_123",
            candidate_confidences=[
                CandidateConfidence("CE_CANDIDATE_1", "NIFTY26OCT24300CE", "MOMENTUM", 85.0, 85.0),
                CandidateConfidence("PE_CANDIDATE_1", "NIFTY26OCT24300PE", "BREAKOUT", 80.0, 80.0),
            ]
        )

        trade_plan = TradePlan(
            trade_plan_id="PLAN_123",
            accepted_candidates=[self.candidate_ce, self.candidate_pe],
            rejected_candidates=[],
        )

        pipeline = DecisionPipeline()
        report = pipeline.run(
            risk_report=risk_report,
            confidence_report=confidence_report,
            trade_plan=trade_plan,
            strategy_evaluation=self.strategy_eval,
            opportunity_context=self.opportunity_ctx,
            market_score=self.market_score,
            config=self.config,
        )

        self.assertEqual(report.stats.buy_count, 1)
        self.assertEqual(report.stats.sell_count, 1)
        self.assertEqual(report.stats.total_allocated_capital, 27000.0)
        self.assertEqual(len(report.priority_ranking), 2)
        self.assertEqual(report.priority_ranking[0], "CE_CANDIDATE_1")  # Score 85.0 > 80.0
