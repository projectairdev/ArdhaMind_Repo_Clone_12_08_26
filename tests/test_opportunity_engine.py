from __future__ import annotations

import unittest
import datetime
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
    OpportunityContext,
    MarketBreadthContext,
    GlobalContext,
)
from src.opportunity_engine import (
    evaluate_opportunity_strength,
    evaluate_warnings,
    evaluate_invalidation_factors,
    evaluate_directional_bias,
    evaluate_strategy_suitability,
    evaluate_opportunity_classification,
    evaluate_market_breadth,
    evaluate_global_context,
    OpportunityContextBuilder,
)
from src.pipeline.opportunity_pipeline import OpportunityPipeline


class TestOpportunityEngine(unittest.TestCase):
    def setUp(self):
        # 1. Standard base Market Context
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

        # 2. Standard base Option Context
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
                "average_spread_pct": 0.15,
            },
            option_chain_summary={
                "total_calls_oi": 500000.0,
                "total_puts_oi": 600000.0,
            },
            top_candidate_strikes=[],
            market_option_bias="BULLISH"
        )

        # 3. Standard base Session Context
        self.session_ctx = SessionContext(
            session_type="MORNING",
            is_tradable_time=True,
            time_of_day="10:30:00",
            is_weekend=False,
            is_holiday=False,
            is_half_day=False,
        )

        # 4. Standard base Expiry Context
        self.expiry_ctx = ExpiryContext(
            expiry_date="2026-10-29",
            days_remaining=3,
            expiry_type="WEEKLY",
            is_expiry_day=False,
            is_expiry_eve=False,
            is_far_expiry=False,
            classification="WEEKLY_EXPIRY"
        )

        # 5. Standard base Confluence Context
        self.confluence_ctx = ConfluenceContext(
            trend_confluence=True,
            option_confluence=True,
            sr_alignment=True,
            volatility_alignment=True,
            liquidity_alignment=True,
            overall_confluence=True,
            description="All systems aligned"
        )

        # 6. Standard base Readiness
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

        # Base MarketScore Context
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

    def test_opportunity_strength(self):
        """Verify dynamic physical opportunity strength metrics evaluate properly under bullish setup."""
        strength = evaluate_opportunity_strength(self.trade_ctx)
        self.assertGreater(strength.trend_force, 50.0)
        self.assertGreater(strength.option_force, 50.0)
        self.assertGreater(strength.overall_strength, 60.0)
        self.assertGreater(strength.imbalance_magnitude, 0.0)

    def test_warnings_evaluation(self):
        """Verify warnings are generated for resistance proximity, low liquidity, high IV, and closing sessions."""
        # Test no warning base case
        warnings = evaluate_warnings(self.trade_ctx)
        self.assertEqual(len(warnings), 0)

        # Test resistance proximity warning
        close_res_market = MarketContext(
            current_spot=24490.0,  # resistance at 24500.0 (dist is 10 points which is ~0.04% < 0.4%)
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
        close_res_ctx = TradeContext(
            market=close_res_market,
            options=self.options_ctx,
            session=self.session_ctx,
            expiry=self.expiry_ctx,
            confluence=self.confluence_ctx,
            readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        warnings = evaluate_warnings(close_res_ctx)
        warning_types = [w.warning_type for w in warnings]
        self.assertIn("RESISTANCE_PROXIMITY", warning_types)

        # Test low liquidity warning
        illiquid_options = OptionContext(
            underlying_spot=24320.0, atm_strike=24300.0, strike_step=50.0,
            current_weekly_expiry="2026-10-29", current_monthly_expiry="2026-10-29",
            time_to_expiry=20.0, atm_iv=16.0, expected_move=350.0, pcr=1.2, max_pain=24300.0,
            highest_call_oi=10000.0, highest_put_oi=12000.0, highest_call_oi_change=100.0, highest_put_oi_change=120.0,
            support_strikes=[24200.0, 24100.0], resistance_strikes=[24400.0, 24500.0],
            liquidity_metrics={"overall_liquidity_score": 35.0, "average_spread_pct": 0.85},
            option_chain_summary={}, top_candidate_strikes=[], market_option_bias="BULLISH"
        )
        illiquid_ctx = TradeContext(
            market=self.market_ctx,
            options=illiquid_options,
            session=self.session_ctx,
            expiry=self.expiry_ctx,
            confluence=self.confluence_ctx,
            readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        warnings = evaluate_warnings(illiquid_ctx)
        self.assertTrue(any(w.warning_type == "LOW_LIQUIDITY" for w in warnings))

    def test_invalidation_factors(self):
        """Verify invalidations are accurately detected for trend failure, session changes, and breached technical structures."""
        # Base case
        factors = evaluate_invalidation_factors(self.trade_ctx, "BULLISH")
        for factor in factors:
            self.assertFalse(factor.is_invalidated)

        # Loss of trend alignment
        sideways_market = MarketContext(
            current_spot=24320.0, timestamp="2026-07-09 10:30:00", trading_session="INTRADAY",
            current_expiry="2026-10-29", market_regime="SIDEWAYS", trend_direction="SIDEWAYS",
            trend_strength=10.0, support_levels=[], resistance_levels=[], vwap=24320.0, atr=50.0,
            india_vix=12.0, volatility_state="NORMAL"
        )
        sideways_ctx = TradeContext(
            market=sideways_market, options=self.options_ctx, session=self.session_ctx,
            expiry=self.expiry_ctx, confluence=self.confluence_ctx, readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        factors = evaluate_invalidation_factors(sideways_ctx, "BULLISH")
        trend_factor = [f for f in factors if f.factor_type == "LOSS_OF_TREND_ALIGNMENT"][0]
        self.assertTrue(trend_factor.is_invalidated)

    def test_strategy_suitability_matrix(self):
        """Verify Strategy Suitability Matrix mappings for momentum, breakout, reversion, range, and trend strategies."""
        profile = evaluate_strategy_suitability(self.trade_ctx, self.market_score)
        self.assertEqual(profile.momentum_suitability, "SUITABLE")
        self.assertEqual(profile.trend_following_suitability, "SUITABLE")
        self.assertEqual(profile.range_suitability, "UNSUITABLE")
        self.assertEqual(profile.reversal_suitability, "UNSUITABLE")

    def test_opportunity_classification(self):
        """Verify opportunity classifications (EXCELLENT, GOOD, WATCHLIST, WAIT, POOR, AVOID) based on market quality."""
        # 1. Excellent
        warnings = evaluate_warnings(self.trade_ctx)
        classification = evaluate_opportunity_classification(self.trade_ctx, self.market_score, warnings)
        self.assertEqual(classification.value, "EXCELLENT")

        # 2. Avoid due to extreme volatility
        unstable_market = MarketContext(
            current_spot=24320.0, timestamp="2026-07-09 10:30:00", trading_session="INTRADAY",
            current_expiry="2026-10-29", market_regime="TRENDING", trend_direction="BULLISH",
            trend_strength=75.0, support_levels=[], resistance_levels=[], vwap=24300.0, atr=350.0,
            india_vix=35.0, volatility_state="EXTREME"
        )
        unstable_ctx = TradeContext(
            market=unstable_market, options=self.options_ctx, session=self.session_ctx,
            expiry=self.expiry_ctx, confluence=self.confluence_ctx, readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        warnings = evaluate_warnings(unstable_ctx)
        classification = evaluate_opportunity_classification(unstable_ctx, self.market_score, warnings)
        self.assertEqual(classification.value, "AVOID")

    def test_optional_contexts_graceful_degradation(self):
        """Verify that missing breadth and global context components degrade cleanly with defaults."""
        # 1. Missing Breadth
        resolved_breadth = evaluate_market_breadth(None)
        self.assertFalse(resolved_breadth.is_available)
        self.assertIsNone(resolved_breadth.advance_decline_ratio)

        # 2. Missing Global
        resolved_global = evaluate_global_context(None)
        self.assertFalse(resolved_global.is_available)
        self.assertIsNone(resolved_global.gift_nifty_status)

        # 3. Provided Breadth
        provided_breadth = MarketBreadthContext(advance_decline_ratio=1.8, is_available=True)
        resolved_breadth = evaluate_market_breadth(provided_breadth)
        self.assertTrue(resolved_breadth.is_available)
        self.assertEqual(resolved_breadth.advance_decline_ratio, 1.8)

    def test_pipeline_execution(self):
        """Verify that the OpportunityPipeline executes seamlessly and generates the OpportunityContext."""
        pipeline = OpportunityPipeline()
        opt_ctx = pipeline.run(self.trade_ctx, self.market_score)
        
        self.assertIsInstance(opt_ctx, OpportunityContext)
        self.assertTrue(opt_ctx.has_opportunity)
        self.assertEqual(opt_ctx.classification.value, "EXCELLENT")
        self.assertFalse(opt_ctx.breadth.is_available)
        self.assertFalse(opt_ctx.global_ctx.is_available)

    def test_immutability(self):
        """Verify that the assembled OpportunityContext and its properties are strictly immutable."""
        pipeline = OpportunityPipeline()
        opt_ctx = pipeline.run(self.trade_ctx, self.market_score)
        
        with self.assertRaises(AttributeError):
            opt_ctx.has_opportunity = False  # type: ignore

        with self.assertRaises(AttributeError):
            opt_ctx.classification.value = "AVOID"  # type: ignore
