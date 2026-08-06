from __future__ import annotations

import unittest
from src.models import (
    MarketContext,
    OptionContext,
    TradeContext,
    SessionContext,
    ExpiryContext,
    MarketReadiness,
    ConfluenceContext,
    MarketScore,
    TrendScore,
    OptionScore,
    VolatilityScore,
    LiquidityScore,
    SessionScore,
    ExpiryScore,
    ConfluenceScore,
    OpportunityClassification,
    DirectionalBias,
    OpportunityStrength,
    OpportunityContext,
    StrategyEvaluation,
    TradePlan,
    TradeCandidate,
    ConfidenceReport,
)
from src.confidence_engine import (
    BonusCalculator,
    PenaltyCalculator,
    ScoreNormalizer,
    ExplanationGenerator,
    ConfidenceBuilder,
)
from src.pipeline import ConfidencePipeline


class TestConfidenceEngine(unittest.TestCase):
    def setUp(self):
        # 1. Base Market Context: Strong Trending Bullish, Normal Volatility
        self.market_ctx = MarketContext(
            current_spot=24320.0,
            timestamp="2026-07-09 10:30:00",
            trading_session="INTRADAY",
            current_expiry="2026-10-29",
            market_regime="TRENDING",
            trend_direction="BULLISH",
            trend_strength=80.0,
            support_levels=[24100.0, 24200.0],
            resistance_levels=[24500.0, 24600.0],
            vwap=24300.0,
            atr=150.0,
            india_vix=15.0,
            volatility_state="NORMAL"
        )

        # 2. Base Option Context
        self.options_ctx = OptionContext(
            underlying_spot=24320.0,
            atm_strike=24300.0,
            strike_step=50.0,
            current_weekly_expiry="2026-10-29",
            current_monthly_expiry="2026-10-29",
            time_to_expiry=3.0,
            atm_iv=16.0,
            expected_move=350.0,
            pcr=1.2,
            max_pain=24300.0,
            highest_call_oi=100000.0,
            highest_put_oi=120000.0,
            highest_call_oi_change=1000.0,
            highest_put_oi_change=1200.0,
            support_strikes=[24200.0, 24100.0],
            resistance_strikes=[24400.0, 24500.0],
            liquidity_metrics={
                "overall_liquidity_score": 85.0,
                "average_spread_pct": 0.12,
            },
            option_chain_summary={
                "total_calls_oi": 500000.0,
                "total_puts_oi": 600000.0,
            },
            top_candidate_strikes=[],
            market_option_bias="BULLISH"
        )

        # 3. Base Session Context
        self.session_ctx = SessionContext(
            session_type="MORNING",
            is_tradable_time=True,
            time_of_day="10:30:00",
            is_weekend=False,
            is_holiday=False,
            is_half_day=False,
        )

        # 4. Base Expiry Context
        self.expiry_ctx = ExpiryContext(
            expiry_date="2026-10-29",
            days_remaining=3,
            expiry_type="WEEKLY",
            is_expiry_day=False,
            is_expiry_eve=False,
            is_far_expiry=False,
            classification="WEEKLY_EXPIRY"
        )

        # 5. Base Confluence Context
        self.confluence_ctx = ConfluenceContext(
            trend_confluence=True,
            option_confluence=True,
            sr_alignment=True,
            volatility_alignment=True,
            liquidity_alignment=True,
            overall_confluence=True,
            description="Aligned trend structure"
        )

        # 6. Base Readiness
        self.readiness_ctx = MarketReadiness(
            is_market_ready=True,
            suitability_score=100.0,
            reasons=[],
            session_suitable=True,
            volatility_suitable=True,
            liquidity_suitable=True,
            trend_suitable=True,
        )

        # Unified Trade Context
        self.trade_ctx = TradeContext(
            market=self.market_ctx,
            options=self.options_ctx,
            session=self.session_ctx,
            expiry=self.expiry_ctx,
            confluence=self.confluence_ctx,
            readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )

        # 7. Base MarketScore
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
            timestamp="2026-07-09 10:30:00"
        )

        # 8. Base OpportunityContext: Aligned Bullish
        self.opportunity_ctx = OpportunityContext(
            classification=OpportunityClassification("EXCELLENT", "Top tier setup"),
            profile=self.create_mock_profile(),
            strength=OpportunityStrength(1.5, 75.0, 80.0, 85.0, 80.0),
            directional_bias=DirectionalBias("BULLISH", "Strong aligned bias"),
            warnings=[],
            invalidation_factors=[],
            has_opportunity=True,
            timestamp="2026-07-09 10:30:00"
        )

        # Dummy Strategy Evaluation
        from src.models import StrategyScore, EvaluationSummary, StrategyEvaluation
        dummy_score = StrategyScore(
            strategy_name="MOMENTUM",
            suitability_score=90.0,
            suitability_level="HIGH",
            reasons=[],
            warnings=[],
            constraints=[],
            required_conditions_met=[],
            rejected_conditions_met=[]
        )
        dummy_summary = EvaluationSummary(
            top_strategies=["MOMENTUM"],
            suitable_strategies_count=1,
            unsuitable_strategies_count=0,
            conclusions=[]
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
            summary=dummy_summary,
            timestamp="2026-07-09 10:30:00"
        )

    def create_mock_profile(self):
        from src.models import OpportunityProfile
        return OpportunityProfile(
            opportunity_type="TREND_CONTINUATION",
            momentum_suitability="SUITABLE",
            breakout_suitability="SUITABLE",
            reversal_suitability="NEUTRAL",
            range_suitability="UNSUITABLE",
            scalping_suitability="SUITABLE",
            trend_following_suitability="SUITABLE",
            expiry_suitability="SUITABLE",
            suitability_reasons=["Trending market profile setup."]
        )

    def build_test_candidate(
        self,
        candidate_id="MOMENTUM_NIFTY_CE",
        instrument_type="CE",
        suitability_score=90.0,
        spread_pct=0.05,
        oi=60000,
        iv=15.0,
        distance_from_atm=0.0,
        atm_distance_class="ATM"
    ) -> TradeCandidate:
        return TradeCandidate(
            candidate_id=candidate_id,
            strategy_name="MOMENTUM",
            tradingsymbol="NIFTY26OCT24300CE" if instrument_type == "CE" else "NIFTY26OCT24300PE",
            strike=24300.0,
            instrument_type=instrument_type,
            expiry="2026-10-29",
            distance_from_atm=distance_from_atm,
            atm_distance_class=atm_distance_class,
            oi=oi,
            volume=20000,
            spread_pct=spread_pct,
            iv=iv,
            tradability_score=95.0,
            suitability_score=suitability_score,
            ranking_score=85.0,
            rank=1,
            reasons=[],
            warnings=[]
        )

    def test_bonus_calculations(self):
        """Verify that specific market and contract triggers award corresponding bonuses."""
        # 1. Premium Candidate with Ultra Tight Spread, Deep OI, High Suitability, and Trend alignment
        cand = self.build_test_candidate()
        bonuses = BonusCalculator.calculate_bonuses(cand, self.market_score, self.opportunity_ctx)
        
        bonus_types = [b.bonus_type for b in bonuses]
        self.assertIn("ULTRA_TIGHT_SPREAD", bonus_types)
        self.assertIn("DEEP_OI_SUPPORT", bonus_types)
        self.assertIn("HIGH_STRATEGY_SUITABILITY", bonus_types)
        self.assertIn("STRONG_TREND_CONFLUENCE", bonus_types)
        self.assertEqual(len(bonuses), 4)
        
        # 2. Lower suitability, wider spread, small OI candidate -> should get 0 bonuses
        poor_cand = self.build_test_candidate(
            suitability_score=55.0,
            spread_pct=0.20,
            oi=3000,
            instrument_type="PE" # No trend alignment since trend is BULLISH
        )
        no_bonuses = BonusCalculator.calculate_bonuses(poor_cand, self.market_score, self.opportunity_ctx)
        self.assertEqual(len(no_bonuses), 0)

    def test_penalty_calculations(self):
        """Verify that risk indicators (high IV, wide spread, low OI, far OTM) apply penalties."""
        # 1. Candidate with Elevated IV, Wide Spread, Low OI, and Far OTM
        risky_cand = self.build_test_candidate(
            iv=35.0,
            spread_pct=0.30,
            oi=2000,
            distance_from_atm=150.0,
            atm_distance_class="OTHER"
        )
        penalties = PenaltyCalculator.calculate_penalties(risky_cand, self.market_score, self.opportunity_ctx)
        
        penalty_types = [p.penalty_type for p in penalties]
        self.assertIn("ELEVATED_IV_PREMIUM", penalty_types)
        self.assertIn("FAR_OTM_STRIKE", penalty_types)
        self.assertIn("WIDE_SPREAD_FRICTION", penalty_types)
        self.assertIn("LOW_OI_LIQUIDITY_RISK", penalty_types)
        self.assertEqual(len(penalties), 4)

        # 2. Healthy candidate should get 0 penalties
        healthy_cand = self.build_test_candidate()
        no_penalties = PenaltyCalculator.calculate_penalties(healthy_cand, self.market_score, self.opportunity_ctx)
        self.assertEqual(len(no_penalties), 0)

    def test_normalization_boundaries(self):
        """Verify that score normalization bounds the final scores strictly between 0 and 100."""
        # Extremely high raw score with massive bonuses should top out at 100.0
        from src.models import ConfidenceBonus, ConfidencePenalty
        bonuses = [ConfidenceBonus("TEST_B1", "Msg", 45.0), ConfidenceBonus("TEST_B2", "Msg", 45.0)]
        norm_high = ScoreNormalizer.normalize_score(95.0, bonuses, [])
        self.assertEqual(norm_high, 100.0)

        # Extremely low raw score with major penalties should bottom out at 0.0
        penalties = [ConfidencePenalty("TEST_P1", "Msg", 40.0), ConfidencePenalty("TEST_P2", "Msg", 40.0)]
        norm_low = ScoreNormalizer.normalize_score(15.0, [], penalties)
        self.assertEqual(norm_low, 0.0)

    def test_explanation_generation(self):
        """Verify that positive/negative factor explanations are generated dynamically."""
        cand = self.build_test_candidate()
        sub_scores = {
            "strategy_suitability": 90.0,
            "opportunity_quality": 85.0,
            "market_score": 88.0,
            "liquidity": 95.0,
            "trend_agreement": 100.0,
        }
        weights = ConfidenceBuilder.DEFAULT_WEIGHTS
        pos, neg = ExplanationGenerator.generate_explanation(
            cand, self.market_score, self.opportunity_ctx, sub_scores, weights
        )
        
        self.assertGreater(len(pos), 0)
        self.assertEqual(len(neg), 0)
        
        pos_types = [p.reason_type for p in pos]
        self.assertIn("HIGH_STRATEGY_SUITABILITY", pos_types)
        self.assertIn("EXCELLENT_OPPORTUNITY_REGIME", pos_types)
        self.assertIn("FAVORABLE_MARKET_ENVIRONMENT", pos_types)
        self.assertIn("ROBUST_CONTRACT_LIQUIDITY", pos_types)
        self.assertIn("ALIGNMENT_WITH_BIAS", pos_types)

    def test_pipeline_end_to_end(self):
        """Verify that ConfidencePipeline processes a TradePlan and produces an immutable ConfidenceReport."""
        # Build TradePlan with accepted candidates
        cand1 = self.build_test_candidate("MOMENTUM_CE", "CE", suitability_score=95.0)
        cand2 = self.build_test_candidate("MOMENTUM_PE", "PE", suitability_score=75.0, spread_pct=0.28, oi=4000)
        
        from src.models import PlannerStatistics, PlannerSummary
        trade_plan = TradePlan(
            trade_plan_id="PLAN_2026_TEST",
            accepted_candidates=[cand1, cand2],
            rejected_candidates=[],
            statistics=PlannerStatistics(2, 2, 0, 2, 0, 0, 0, 0, 0, 0, 85.0),
            summary=PlannerSummary("MOMENTUM_CE", ["Evaluated"]),
            timestamp="2026-07-09 10:30:00"
        )
        
        pipeline = ConfidencePipeline()
        report = pipeline.run(
            trade_plan=trade_plan,
            strategy_evaluation=self.strategy_eval,
            opportunity_context=self.opportunity_ctx,
            market_score=self.market_score,
        )
        
        self.assertIsInstance(report, ConfidenceReport)
        self.assertEqual(report.trade_plan_id, "PLAN_2026_TEST")
        self.assertTrue(report.report_id.startswith("CONF_REP_"))
        
        # Summary checks
        summary = report.summary
        self.assertEqual(summary.total_evaluated, 2)
        self.assertEqual(summary.highest_confidence_candidate_id, "MOMENTUM_CE")
        self.assertEqual(summary.lowest_confidence_candidate_id, "MOMENTUM_PE")
        self.assertGreater(summary.average_confidence, 0.0)
        self.assertGreater(len(summary.conclusions), 0)
        
        # Verify sorting
        self.assertGreaterEqual(
            report.candidate_confidences[0].confidence_score,
            report.candidate_confidences[1].confidence_score
        )

    def test_empty_trade_plan(self):
        """Verify graceful handling when TradePlan contains no accepted candidates."""
        from src.models import PlannerStatistics, PlannerSummary
        trade_plan = TradePlan(
            trade_plan_id="PLAN_EMPTY",
            accepted_candidates=[],
            rejected_candidates=[],
            statistics=PlannerStatistics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0),
            summary=PlannerSummary("NONE", ["No candidates"]),
            timestamp="2026-07-09 10:30:00"
        )
        
        pipeline = ConfidencePipeline()
        report = pipeline.run(
            trade_plan=trade_plan,
            strategy_evaluation=self.strategy_eval,
            opportunity_context=self.opportunity_ctx,
            market_score=self.market_score,
        )
        
        self.assertEqual(report.summary.total_evaluated, 0)
        self.assertEqual(report.summary.highest_confidence_candidate_id, "NONE")
        self.assertEqual(report.summary.lowest_confidence_candidate_id, "NONE")
        self.assertEqual(report.summary.average_confidence, 0.0)
