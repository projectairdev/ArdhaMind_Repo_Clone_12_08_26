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
    OpportunityWarning,
    InvalidationFactor,
    OpportunityProfile,
    OpportunityContext,
    StrategyEvaluation,
    StrategyScore,
)
from src.strategy_engine import (
    evaluate_momentum,
    evaluate_breakout,
    evaluate_trend_following,
    evaluate_mean_reversion,
    evaluate_range,
    evaluate_expiry,
    evaluate_scalping,
    StrategyEvaluationBuilder,
)
from src.pipeline.strategy_pipeline import StrategyPipeline


class TestStrategyEvaluation(unittest.TestCase):
    def setUp(self):
        # Base Market Context: Trending Bullish, Normal Volatility
        self.market_ctx = MarketContext(
            current_spot=24320.0,
            timestamp="2026-07-09 10:30:00",
            trading_session="INTRADAY",
            current_expiry="2026-10-29",
            market_regime="TRENDING",
            trend_direction="BULLISH",
            trend_strength=75.0,
            support_levels=[24100.0, 24200.0],
            resistance_levels=[24500.0, 24600.0],
            vwap=24300.0,
            atr=150.0,
            india_vix=15.0,
            volatility_state="NORMAL"
        )

        # Base Option Context: Bullish alignment, excellent liquidity
        self.options_ctx = OptionContext(
            underlying_spot=24320.0,
            atm_strike=24300.0,
            strike_step=50.0,
            current_weekly_expiry="2026-10-29",
            current_monthly_expiry="2026-10-29",
            time_to_expiry=20.0,
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

        # Base Session Context: Morning open
        self.session_ctx = SessionContext(
            session_type="MORNING",
            is_tradable_time=True,
            time_of_day="10:30:00",
            is_weekend=False,
            is_holiday=False,
            is_half_day=False,
        )

        # Base Expiry Context: Weekly contract with 3 days to expiry
        self.expiry_ctx = ExpiryContext(
            expiry_date="2026-10-29",
            days_remaining=3,
            expiry_type="WEEKLY",
            is_expiry_day=False,
            is_expiry_eve=False,
            is_far_expiry=False,
            classification="WEEKLY_EXPIRY"
        )

        # Base Confluence Context
        self.confluence_ctx = ConfluenceContext(
            trend_confluence=True,
            option_confluence=True,
            sr_alignment=True,
            volatility_alignment=True,
            liquidity_alignment=True,
            overall_confluence=True,
            description="Aligned trend structure"
        )

        # Base Readiness
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

        # Base MarketScore
        self.market_score = MarketScore(
            trend=TrendScore(75.0, 100.0, 75.0, 100.0, 100.0, 90.0),
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

        # Base OpportunityContext
        self.opportunity_ctx = OpportunityContext(
            classification=OpportunityClassification("EXCELLENT", "Top tier"),
            profile=OpportunityProfile("TREND_CONTINUATION", "SUITABLE", "SUITABLE", "NEUTRAL", "UNSUITABLE", "SUITABLE", "SUITABLE", "NEUTRAL"),
            strength=OpportunityStrength(1.5, 75.0, 80.0, 85.0, 80.0),
            directional_bias=DirectionalBias("BULLISH", "Strong aligned bias"),
            warnings=[],
            invalidation_factors=[],
            has_opportunity=True,
            timestamp="2026-07-09 10:30:00"
        )

    def test_momentum_suitability(self):
        """Verify momentum strategy scores high in strong aligned trending markets."""
        score = evaluate_momentum(self.trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(score.strategy_name, "MOMENTUM")
        self.assertGreaterEqual(score.suitability_score, 80.0)
        self.assertEqual(score.suitability_level, "HIGH")
        self.assertTrue(any("Trend strength is elevated" in r.message for r in score.reasons))

    def test_breakout_compressed_suitability(self):
        """Verify breakout strategy scores high when volatility state is compressed."""
        compressed_market = MarketContext(
            current_spot=24320.0, timestamp="2026-07-09 10:30:00", trading_session="INTRADAY",
            current_expiry="2026-10-29", market_regime="TRENDING", trend_direction="BULLISH",
            trend_strength=75.0, support_levels=[24100.0, 24200.0], resistance_levels=[24350.0],  # Close to resistance (distance ~0.12%)
            vwap=24300.0, atr=80.0, india_vix=11.0, volatility_state="COMPRESSED"
        )
        compressed_trade_ctx = TradeContext(
            market=compressed_market, options=self.options_ctx, session=self.session_ctx,
            expiry=self.expiry_ctx, confluence=self.confluence_ctx, readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        score = evaluate_breakout(compressed_trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(score.strategy_name, "BREAKOUT")
        self.assertGreaterEqual(score.suitability_score, 80.0)
        self.assertEqual(score.suitability_level, "HIGH")

    def test_trend_following_suitability(self):
        """Verify trend-following strategy suitability under ideal conditions."""
        score = evaluate_trend_following(self.trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(score.strategy_name, "TREND_FOLLOWING")
        self.assertEqual(score.suitability_level, "HIGH")
        self.assertTrue(any(r.reason_type == "ESTABLISHED_TREND" for r in score.reasons))

    def test_mean_reversion_suitability(self):
        """Verify mean reversion is unsuitable during low-deviation strong trends, but suitable when stretched."""
        # Base case (unsuitable)
        score = evaluate_mean_reversion(self.trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(score.suitability_level, "NONE")

        # Stretched case (suitable)
        stretched_market = MarketContext(
            current_spot=24500.0,  # VWAP at 24300, spot deviation is ~0.82%
            timestamp="2026-07-09 10:30:00", trading_session="INTRADAY",
            current_expiry="2026-10-29", market_regime="SIDEWAYS", trend_direction="SIDEWAYS",
            trend_strength=25.0, support_levels=[24200.0], resistance_levels=[24600.0],
            vwap=24300.0, atr=150.0, india_vix=18.0, volatility_state="EXPANDED"
        )
        stretched_trade_ctx = TradeContext(
            market=stretched_market, options=self.options_ctx, session=self.session_ctx,
            expiry=self.expiry_ctx, confluence=self.confluence_ctx, readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        score = evaluate_mean_reversion(stretched_trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(score.suitability_level, "HIGH")

    def test_range_suitability(self):
        """Verify range-trading is highly suitable in sideways regimes with low trend strength."""
        sideways_market = MarketContext(
            current_spot=24350.0, timestamp="2026-07-09 10:30:00", trading_session="INTRADAY",
            current_expiry="2026-10-29", market_regime="SIDEWAYS", trend_direction="SIDEWAYS",
            trend_strength=20.0, support_levels=[24200.0], resistance_levels=[24500.0],
            vwap=24350.0, atr=60.0, india_vix=12.0, volatility_state="NORMAL"
        )
        sideways_trade_ctx = TradeContext(
            market=sideways_market, options=self.options_ctx, session=self.session_ctx,
            expiry=self.expiry_ctx, confluence=self.confluence_ctx, readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        score = evaluate_range(sideways_trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(score.strategy_name, "RANGE")
        self.assertEqual(score.suitability_level, "HIGH")

    def test_expiry_plays_suitability(self):
        """Verify expiry-day play triggers suitability strictly based on days remaining."""
        # 1. Day of Expiry
        expiry_day_ctx = ExpiryContext(
            expiry_date="2026-10-29", days_remaining=0, expiry_type="WEEKLY",
            is_expiry_day=True, is_expiry_eve=False, is_far_expiry=False, classification="EXPIRY_DAY"
        )
        expiry_trade_ctx = TradeContext(
            market=self.market_ctx, options=self.options_ctx, session=self.session_ctx,
            expiry=expiry_day_ctx, confluence=self.confluence_ctx, readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        score = evaluate_expiry(expiry_trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(score.suitability_level, "HIGH")

        # 2. Far from Expiry (should have suitability NONE/LOW)
        far_expiry_ctx = ExpiryContext(
            expiry_date="2026-11-20", days_remaining=15, expiry_type="MONTHLY",
            is_expiry_day=False, is_expiry_eve=False, is_far_expiry=True, classification="FAR_EXPIRY"
        )
        far_trade_ctx = TradeContext(
            market=self.market_ctx, options=self.options_ctx, session=self.session_ctx,
            expiry=far_expiry_ctx, confluence=self.confluence_ctx, readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        score = evaluate_expiry(far_trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(score.suitability_level, "NONE")

    def test_scalping_suitability(self):
        """Verify scalping suitability is gated by spreads and liquid morning sessions."""
        # 1. Ideal Scalping Setup
        score = evaluate_scalping(self.trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(score.suitability_level, "HIGH")

        # 2. Wide spreads should make it unsuitable
        unscalable_options = OptionContext(
            underlying_spot=24320.0, atm_strike=24300.0, strike_step=50.0,
            current_weekly_expiry="2026-10-29", current_monthly_expiry="2026-10-29",
            time_to_expiry=20.0, atm_iv=16.0, expected_move=350.0, pcr=1.2, max_pain=24300.0,
            highest_call_oi=100000.0, highest_put_oi=120000.0, highest_call_oi_change=1000.0, highest_put_oi_change=1200.0,
            support_strikes=[24200.0, 24100.0], resistance_strikes=[24400.0, 24500.0],
            liquidity_metrics={"overall_liquidity_score": 50.0, "average_spread_pct": 0.45},  # wide spread
            option_chain_summary={}, top_candidate_strikes=[], market_option_bias="BULLISH"
        )
        unscalable_trade_ctx = TradeContext(
            market=self.market_ctx, options=unscalable_options, session=self.session_ctx,
            expiry=self.expiry_ctx, confluence=self.confluence_ctx, readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        score = evaluate_scalping(unscalable_trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(score.suitability_level, "NONE")

    def test_unsuitable_and_disabled_markets(self):
        """Verify non-tradable sessions or poor liquidity result in zero suitability scores across strategies."""
        # Non-tradable weekend session
        weekend_session = SessionContext(
            session_type="WEEKEND", is_tradable_time=False, time_of_day="12:00:00",
            is_weekend=True, is_holiday=False, is_half_day=False
        )
        weekend_trade_ctx = TradeContext(
            market=self.market_ctx, options=self.options_ctx, session=weekend_session,
            expiry=self.expiry_ctx, confluence=self.confluence_ctx, readiness=self.readiness_ctx,
            timestamp="2026-07-12 12:00:00"
        )
        
        evaluation = StrategyEvaluationBuilder.build(weekend_trade_ctx, self.market_score, self.opportunity_ctx)
        self.assertEqual(evaluation.overall_best_strategy, "NONE")
        self.assertEqual(evaluation.summary.suitable_strategies_count, 0)
        for eval_score in evaluation.evaluations:
            self.assertEqual(eval_score.suitability_level, "NONE")

    def test_pipeline_execution(self):
        """Verify that the StrategyPipeline executes successfully and yields correct StrategyEvaluation output."""
        pipeline = StrategyPipeline()
        evaluation = pipeline.run(self.trade_ctx, self.market_score, self.opportunity_ctx)
        
        self.assertIsInstance(evaluation, StrategyEvaluation)
        self.assertEqual(evaluation.overall_best_strategy, "TREND_FOLLOWING")
        self.assertGreater(evaluation.summary.suitable_strategies_count, 0)
        self.assertTrue(len(evaluation.summary.conclusions) > 0)

    def test_immutability(self):
        """Verify that StrategyEvaluation context and its components are completely immutable."""
        pipeline = StrategyPipeline()
        evaluation = pipeline.run(self.trade_ctx, self.market_score, self.opportunity_ctx)
        
        with self.assertRaises(AttributeError):
            evaluation.overall_best_strategy = "SCALPING"  # type: ignore

        with self.assertRaises(AttributeError):
            evaluation.momentum_evaluation.suitability_level = "LOW"  # type: ignore
