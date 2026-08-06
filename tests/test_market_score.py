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
)
from src.configuration_engine.runtime import Config
from src.scoring_engine import MarketScoreBuilder
from src.scoring_engine.trend_score import evaluate_trend_score
from src.scoring_engine.option_score import evaluate_option_score
from src.scoring_engine.volatility_score import evaluate_volatility_score
from src.scoring_engine.liquidity_score import evaluate_liquidity_score
from src.scoring_engine.session_score import evaluate_session_score
from src.scoring_engine.expiry_score import evaluate_expiry_score
from src.scoring_engine.confluence_score import evaluate_confluence_score
from src.pipeline.market_scoring_pipeline import MarketScoringPipeline


class TestMarketScore(unittest.TestCase):
    def setUp(self):
        # 1. Base Market Context
        self.market_ctx = MarketContext(
            current_spot=24320.0,
            timestamp="2026-07-09 15:15:00",
            trading_session="INTRADAY",
            current_expiry="2026-10-29",
            market_regime="TRENDING",
            trend_direction="BULLISH",
            trend_strength=75.0,
            support_levels=[24200.0, 24100.0],
            resistance_levels=[24400.0, 24500.0],
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
            description="All systems aligned"
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

    def test_configuration_loading(self):
        """Verify that scoring configuration weights load correctly from config."""
        self.assertIn("overall_weights", Config.SCORING)
        self.assertIn("trend_weights", Config.SCORING)
        self.assertIn("option_weights", Config.SCORING)
        
        overall = Config.SCORING["overall_weights"]
        self.assertGreater(overall.get("trend", 0), 0)
        self.assertGreater(overall.get("options", 0), 0)

    def test_trend_scoring(self):
        """Verify Trend score sub-components evaluate correctly based on alignment."""
        trend_score = evaluate_trend_score(self.trade_ctx)
        self.assertEqual(trend_score.trend_strength_score, 75.0)
        self.assertGreaterEqual(trend_score.ema_alignment_score, 90.0)
        self.assertGreater(trend_score.overall_trend_score, 50.0)

        # Test sideways scenario
        sideways_market = MarketContext(
            current_spot=24320.0,
            timestamp="2026-07-09 15:15:00",
            trading_session="INTRADAY",
            current_expiry="2026-10-29",
            market_regime="SIDEWAYS",
            trend_direction="SIDEWAYS",
            trend_strength=10.0,
            support_levels=[],
            resistance_levels=[],
            vwap=24320.0,
            atr=50.0,
            india_vix=12.0,
            volatility_state="NORMAL"
        )
        sideways_ctx = TradeContext(
            market=sideways_market,
            options=self.options_ctx,
            session=self.session_ctx,
            expiry=self.expiry_ctx,
            confluence=self.confluence_ctx,
            readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        sideways_score = evaluate_trend_score(sideways_ctx)
        self.assertEqual(sideways_score.trend_strength_score, 10.0)
        self.assertEqual(sideways_score.ema_alignment_score, 40.0)
        self.assertLess(sideways_score.overall_trend_score, 50.0)

    def test_option_scoring(self):
        """Verify Option score evaluations for PCR, Max Pain, and option alignments."""
        option_score = evaluate_option_score(self.trade_ctx)
        self.assertEqual(option_score.pcr_score, 100.0)  # PCR is 1.2 which is healthy
        self.assertGreater(option_score.max_pain_score, 80.0)
        self.assertEqual(option_score.oi_structure_score, 100.0)  # Bullish market + Bullish options bias

    def test_volatility_scoring(self):
        """Verify Volatility score evaluations for ATR, compression, and expansion."""
        vol_score = evaluate_volatility_score(self.trade_ctx)
        self.assertGreater(vol_score.atr_score, 0.0)
        self.assertEqual(vol_score.compression_score, 90.0)  # "NORMAL" state

        # Test compressed state
        compressed_market = MarketContext(
            current_spot=24320.0,
            timestamp="2026-07-09 15:15:00",
            trading_session="INTRADAY",
            current_expiry="2026-10-29",
            market_regime="SIDEWAYS",
            trend_direction="SIDEWAYS",
            trend_strength=10.0,
            support_levels=[],
            resistance_levels=[],
            vwap=24320.0,
            atr=50.0,
            india_vix=12.0,
            volatility_state="COMPRESSED"
        )
        compressed_ctx = TradeContext(
            market=compressed_market,
            options=self.options_ctx,
            session=self.session_ctx,
            expiry=self.expiry_ctx,
            confluence=self.confluence_ctx,
            readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        compressed_score = evaluate_volatility_score(compressed_ctx)
        self.assertEqual(compressed_score.compression_score, 100.0)

    def test_liquidity_scoring(self):
        """Verify Liquidity score evaluations with respect to spread and open interest thresholds."""
        liq_score = evaluate_liquidity_score(self.trade_ctx)
        self.assertGreater(liq_score.spread_score, 0.0)
        self.assertEqual(liq_score.volume_score, 85.0)
        self.assertEqual(liq_score.oi_score, 100.0)

    def test_session_scoring(self):
        """Verify Session score evaluates based on time of day and tradability status."""
        session_score = evaluate_session_score(self.trade_ctx)
        self.assertEqual(session_score.session_type_score, 100.0)  # "MORNING"
        self.assertEqual(session_score.is_tradable_score, 100.0)
        self.assertEqual(session_score.overall_session_score, 100.0)

        # Off hours session
        closed_session = SessionContext(
            session_type="POST_MARKET",
            is_tradable_time=False,
            time_of_day="18:00:00",
            is_weekend=False,
            is_holiday=False,
            is_half_day=False,
        )
        closed_ctx = TradeContext(
            market=self.market_ctx,
            options=self.options_ctx,
            session=closed_session,
            expiry=self.expiry_ctx,
            confluence=self.confluence_ctx,
            readiness=self.readiness_ctx,
            timestamp="2026-07-09 18:00:00"
        )
        closed_score = evaluate_session_score(closed_ctx)
        self.assertEqual(closed_score.session_type_score, 0.0)
        self.assertEqual(closed_score.is_tradable_score, 0.0)
        self.assertEqual(closed_score.overall_session_score, 0.0)

    def test_expiry_scoring(self):
        """Verify Expiry suitability scores relative to days remaining."""
        expiry_score = evaluate_expiry_score(self.trade_ctx)
        self.assertEqual(expiry_score.days_remaining_score, 100.0)  # 3 days is optimal
        self.assertEqual(expiry_score.expiry_type_score, 100.0)  # Weekly

        # Expiry Day scenario
        expiry_day = ExpiryContext(
            expiry_date="2026-10-29",
            days_remaining=0,
            expiry_type="WEEKLY",
            is_expiry_day=True,
            is_expiry_eve=False,
            is_far_expiry=False,
            classification="EXPIRY_DAY"
        )
        expiry_day_ctx = TradeContext(
            market=self.market_ctx,
            options=self.options_ctx,
            session=self.session_ctx,
            expiry=expiry_day,
            confluence=self.confluence_ctx,
            readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        expiry_day_score = evaluate_expiry_score(expiry_day_ctx)
        self.assertEqual(expiry_day_score.days_remaining_score, 35.0)

    def test_confluence_scoring(self):
        """Verify Confluence score translates alignment booleans to scores."""
        confluence_score = evaluate_confluence_score(self.trade_ctx)
        self.assertEqual(confluence_score.trend_confluence_score, 100.0)
        self.assertEqual(confluence_score.overall_confluence_score, 100.0)

        # Partial confluence
        partial_confluence = ConfluenceContext(
            trend_confluence=True,
            option_confluence=False,
            sr_alignment=True,
            volatility_alignment=False,
            liquidity_alignment=True,
            overall_confluence=False,
            description="Partial alignment"
        )
        partial_ctx = TradeContext(
            market=self.market_ctx,
            options=self.options_ctx,
            session=self.session_ctx,
            expiry=self.expiry_ctx,
            confluence=partial_confluence,
            readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )
        partial_score = evaluate_confluence_score(partial_ctx)
        self.assertEqual(partial_score.trend_confluence_score, 100.0)
        self.assertEqual(partial_score.option_bias_score, 0.0)
        self.assertLess(partial_score.overall_confluence_score, 100.0)

    def test_market_score_builder_and_grades(self):
        """Verify full assembly of MarketScore, normalization, and grade mappings."""
        score = MarketScoreBuilder.build(self.trade_ctx)
        self.assertIsInstance(score, MarketScore)
        self.assertGreaterEqual(score.overall_score, 0.0)
        self.assertLessEqual(score.overall_score, 100.0)
        
        # Test grading boundaries
        # A+ boundary (>= 95)
        self.assertEqual(score.letter_grade, "A" if score.overall_score < 95 else "A+")
        
        # Let's verify grading system mappings directly
        # Weak environment
        weak_ctx = TradeContext(
            market=MarketContext(
                current_spot=24320.0, timestamp="2026-07-09 15:15:00", trading_session="INTRADAY",
                current_expiry="2026-10-29", market_regime="SIDEWAYS", trend_direction="SIDEWAYS",
                trend_strength=5.0, vwap=24320.0, atr=300.0, india_vix=35.0, volatility_state="EXTREME"
            ),
            options=OptionContext(
                underlying_spot=24320.0, atm_strike=24300.0, strike_step=50.0,
                current_weekly_expiry="2026-10-29", current_monthly_expiry="2026-10-29",
                time_to_expiry=20.0, atm_iv=45.0, expected_move=800.0, pcr=0.4, max_pain=24300.0,
                highest_call_oi=100000.0, highest_put_oi=20000.0, highest_call_oi_change=1000.0, highest_put_oi_change=100.0,
                liquidity_metrics={"overall_liquidity_score": 20.0, "average_spread_pct": 2.5},
                option_chain_summary={}, top_candidate_strikes=[], market_option_bias="BEARISH"
            ),
            session=SessionContext(
                session_type="POST_MARKET", is_tradable_time=False, time_of_day="18:00:00",
                is_weekend=True, is_holiday=False, is_half_day=False
            ),
            expiry=ExpiryContext(
                expiry_date="2026-10-29", days_remaining=0, expiry_type="WEEKLY",
                is_expiry_day=True, is_expiry_eve=False, is_far_expiry=False, classification="EXPIRY_DAY"
            ),
            confluence=ConfluenceContext(
                trend_confluence=False, option_confluence=False, sr_alignment=False,
                volatility_alignment=False, liquidity_alignment=False, overall_confluence=False,
                description="Terrible alignment"
            ),
            readiness=self.readiness_ctx,
            timestamp="2026-07-09 18:00:00"
        )
        weak_score = MarketScoreBuilder.build(weak_ctx)
        self.assertEqual(weak_score.letter_grade, "F")
        self.assertEqual(weak_score.classification, "Weak")

    def test_immutability(self):
        """Verify that the assembled MarketScore and its sub-scores are completely immutable."""
        score = MarketScoreBuilder.build(self.trade_ctx)
        with self.assertRaises(AttributeError):
            score.overall_score = 99.0  # type: ignore

        with self.assertRaises(AttributeError):
            score.trend.overall_trend_score = 99.0  # type: ignore

    def test_pipeline_integration(self):
        """Verify that the MarketScoringPipeline works seamlessly with the scoring builder."""
        pipeline = MarketScoringPipeline()
        score = pipeline.run(self.trade_ctx)
        self.assertIsInstance(score, MarketScore)
        self.assertGreater(score.overall_score, 0.0)
