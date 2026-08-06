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
)
from src.strategy_engine import StrategyEvaluationBuilder
from src.planner_engine import (
    CandidateGenerator,
    CandidateFilter,
    CandidateRanker,
    PlannerBuilder,
)
from src.pipeline import TradePlannerPipeline


class TestTradePlanner(unittest.TestCase):
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

        # 2. Base Option Context with top candidate strikes pre-ranked
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
            top_candidate_strikes=[
                {
                    "tradingsymbol": "NIFTY26OCT24300CE",
                    "strike": 24300.0,
                    "instrument_type": "CE",
                    "distance_from_atm": 0.0,
                    "oi": 55000,
                    "volume": 25000,
                    "spread_pct": 0.08,
                    "iv": 15.5,
                    "tradability_score": 92.0,
                    "ranking_score": 92.0,
                    "rank": 1,
                },
                {
                    "tradingsymbol": "NIFTY26OCT24300PE",
                    "strike": 24300.0,
                    "instrument_type": "PE",
                    "distance_from_atm": 0.0,
                    "oi": 65000,
                    "volume": 30000,
                    "spread_pct": 0.06,
                    "iv": 16.2,
                    "tradability_score": 95.0,
                    "ranking_score": 95.0,
                    "rank": 2,
                },
                {
                    "tradingsymbol": "NIFTY26OCT24350CE",
                    "strike": 24350.0,
                    "instrument_type": "CE",
                    "distance_from_atm": 50.0,
                    "oi": 40000,
                    "volume": 12000,
                    "spread_pct": 0.15,
                    "iv": 15.8,
                    "tradability_score": 88.0,
                    "ranking_score": 88.0,
                    "rank": 3,
                },
                {
                    "tradingsymbol": "NIFTY26OCT24250PE",
                    "strike": 24250.0,
                    "instrument_type": "PE",
                    "distance_from_atm": 50.0,
                    "oi": 45000,
                    "volume": 15000,
                    "spread_pct": 0.14,
                    "iv": 16.5,
                    "tradability_score": 90.0,
                    "ranking_score": 90.0,
                    "rank": 4,
                },
            ],
            market_option_bias="BULLISH"
        )

        # 3. Base Session Context: Morning open
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
            trend=TrendScore(80.0, 100.0, 80.0, 100.0, 100.0, 90.0),
            options=OptionScore(100.0, 100.0, 100.0, 100.0, 85.0, 100.0, 100.0, 95.0),
            volatility=VolatilityScore(100.0, 90.0, 85.0, 100.0, 100.0, 95.0),
            liquidity=LiquidityScore(100.0, 85.0, 100.0, 100.0, 95.0),
            session=SessionScore(100.0, 100.0, 100.0),
            expiry=ExpiryScore(100.0, 100.0, 100.0, 100.0),
            confluence=ConfluenceScore(100.0, 100.0, 100.0, 100.0, 100.0, 100.0),
            overall_score=95.0,
            letter_grade="A+",
            classification="Excellent",
            timestamp="2026-07-09 10:30:00"
        )

        # 8. Base OpportunityContext: Aligned Bullish
        self.opportunity_ctx = OpportunityContext(
            classification=OpportunityClassification("EXCELLENT", "Top tier"),
            profile=self.create_mock_profile(),
            strength=OpportunityStrength(1.5, 75.0, 80.0, 85.0, 80.0),
            directional_bias=DirectionalBias("BULLISH", "Strong aligned bias"),
            warnings=[],
            invalidation_factors=[],
            has_opportunity=True,
            timestamp="2026-07-09 10:30:00"
        )

        # Build dynamic strategy evaluation using the existing StrategyBuilder
        self.strategy_eval = StrategyEvaluationBuilder.build(
            self.trade_ctx, self.market_score, self.opportunity_ctx
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

    def test_candidate_generation(self):
        """Verify that CandidateGenerator crosses all strategies with option contract strikes correctly."""
        raw_candidates = CandidateGenerator.generate_candidates(self.options_ctx, self.strategy_eval)
        
        # 7 strategies evaluated (MOMENTUM, BREAKOUT, TREND_FOLLOWING, MEAN_REVERSION, RANGE, EXPIRY, SCALPING)
        # 4 contracts in options_ctx.top_candidate_strikes
        # Expected: 7 * 4 = 28 candidates
        self.assertEqual(len(raw_candidates), 28)
        
        # Ensure classifications and offsets are mapped accurately
        atm_cands = [c for c in raw_candidates if c.atm_distance_class == "ATM"]
        self.assertGreater(len(atm_cands), 0)
        
        # Verify ids are populated correctly
        first_cand = raw_candidates[0]
        self.assertTrue(first_cand.candidate_id.startswith(first_cand.strategy_name))
        self.assertTrue(first_cand.candidate_id.endswith(first_cand.tradingsymbol))

    def test_candidate_filtering_directional_bias(self):
        """Verify that PE options are correctly filtered/rejected under active BULLISH bias for directional strategies."""
        raw_candidates = CandidateGenerator.generate_candidates(self.options_ctx, self.strategy_eval)
        
        accepted, rejected = CandidateFilter.filter_candidates(raw_candidates, self.opportunity_ctx)
        
        # In a BULLISH trend:
        # MOMENTUM, TREND_FOLLOWING, BREAKOUT, SCALPING should accept CE and reject PE
        directional_strategies = {"MOMENTUM", "TREND_FOLLOWING", "BREAKOUT", "SCALPING"}
        
        for cand in accepted:
            if cand.strategy_name in directional_strategies:
                self.assertEqual(cand.instrument_type, "CE")
                
        # Verify we logged directional misalignments in the rejections
        rejection_reasons = [r.reason_type for r in rejected]
        self.assertIn("DIRECTIONAL_MISALIGNMENT", rejection_reasons)

    def test_candidate_filtering_unsuitable_strategy(self):
        """Verify that strategies with low suitability score are filtered out."""
        raw_candidates = CandidateGenerator.generate_candidates(self.options_ctx, self.strategy_eval)
        
        # Filter where RANGE suitability is low (should be low in trending market)
        accepted, rejected = CandidateFilter.filter_candidates(raw_candidates, self.opportunity_ctx)
        
        range_accepted = [c for c in accepted if c.strategy_name == "RANGE"]
        self.assertEqual(len(range_accepted), 0)
        
        rejection_reasons = [r.reason_type for r in rejected if r.strategy_name == "RANGE"]
        self.assertIn("LOW_STRATEGY_SUITABILITY", rejection_reasons)

    def test_candidate_filtering_weak_opportunity(self):
        """Verify that when has_opportunity is False, all candidates are rejected."""
        no_opportunity_ctx = OpportunityContext(
            classification=OpportunityClassification("POOR", "No trend"),
            profile=self.create_mock_profile(),
            strength=OpportunityStrength(0.2, 20.0, 20.0, 20.0, 20.0),
            directional_bias=DirectionalBias("NEUTRAL", "No bias"),
            warnings=[],
            invalidation_factors=[],
            has_opportunity=False,
            timestamp="2026-07-09 10:30:00"
        )
        
        raw_candidates = CandidateGenerator.generate_candidates(self.options_ctx, self.strategy_eval)
        accepted, rejected = CandidateFilter.filter_candidates(raw_candidates, no_opportunity_ctx)
        
        self.assertEqual(len(accepted), 0)
        self.assertEqual(len(rejected), len(raw_candidates))
        self.assertTrue(all(r.reason_type == "WEAK_OPPORTUNITY" for r in rejected))

    def test_candidate_ranking(self):
        """Verify that accepted candidates are ranked based on weighted criteria and given sequential ranks."""
        raw_candidates = CandidateGenerator.generate_candidates(self.options_ctx, self.strategy_eval)
        accepted, _ = CandidateFilter.filter_candidates(raw_candidates, self.opportunity_ctx)
        
        ranked = CandidateRanker.rank_candidates(accepted, self.options_ctx)
        
        # Verify ranking structure
        self.assertGreater(len(ranked), 0)
        
        # Ranks must be sequential starting from 1
        ranks = [c.rank for c in ranked]
        self.assertEqual(ranks, list(range(1, len(ranked) + 1)))
        
        # Scores must be sorted descending
        scores = [c.ranking_score for c in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_planner_pipeline_end_to_end(self):
        """Verify the complete end-to-end execution of TradePlannerPipeline."""
        pipeline = TradePlannerPipeline()
        trade_plan = pipeline.run(
            strategy_evaluation=self.strategy_eval,
            option_context=self.options_ctx,
            opportunity_context=self.opportunity_ctx,
        )
        
        self.assertIsInstance(trade_plan, TradePlan)
        self.assertTrue(trade_plan.trade_plan_id.startswith("PLAN_"))
        
        # Verify statistics aggregation
        stats = trade_plan.statistics
        self.assertEqual(stats.total_candidates_generated, 28)
        self.assertGreater(stats.total_candidates_accepted, 0)
        self.assertGreater(stats.total_candidates_rejected, 0)
        self.assertEqual(stats.total_candidates_accepted + stats.total_candidates_rejected, 28)
        
        # Verify summary best candidate is filled
        self.assertNotEqual(trade_plan.summary.best_candidate_id, "NONE")
        self.assertGreater(len(trade_plan.summary.conclusions), 0)

    def test_immutability(self):
        """Verify that TradePlan and its sub-models are fully frozen and immutable."""
        pipeline = TradePlannerPipeline()
        trade_plan = pipeline.run(
            strategy_evaluation=self.strategy_eval,
            option_context=self.options_ctx,
            opportunity_context=self.opportunity_ctx,
        )
        
        with self.assertRaises(AttributeError):
            trade_plan.trade_plan_id = "NEW_ID"  # type: ignore

        with self.assertRaises(AttributeError):
            trade_plan.accepted_candidates[0].rank = 100  # type: ignore
