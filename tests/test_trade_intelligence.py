from __future__ import annotations

import datetime
import unittest
from src.models.market_context import MarketContext
from src.models.option_context import OptionContext
from src.models.trade_context import (
    TradeContext,
    SessionContext,
    ExpiryContext,
    MarketReadiness,
    ConfluenceContext,
)
from src.trade_engine.session import analyze_session
from src.trade_engine.expiry import analyze_expiry
from src.trade_engine.market_readiness import evaluate_market_readiness
from src.trade_engine.confluence import analyze_confluence
from src.trade_engine.context_builder import TradeContextBuilder


class TestTradeIntelligence(unittest.TestCase):
    def setUp(self):
        # 1. Base Market Context
        self.market_ctx = MarketContext(
            current_spot=24320.0,
            timestamp="2026-07-09 15:15:00",
            trading_session="INTRADAY",
            current_expiry="2026-10-29",
            market_regime="TRENDING",
            trend_direction="BULLISH",
            trend_strength=25.0,
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
                "average_spread_pct": 0.5,
            },
            option_chain_summary={
                "total_calls_oi": 500000,
                "total_puts_oi": 600000,
            },
            top_candidate_strikes=[],
            market_option_bias="BULLISH"
        )

    def test_session_analysis(self):
        """Verify session classification for weekends, holidays, half-days, and standard market phases."""
        # Weekend
        sat_dt = datetime.datetime(2026, 10, 3, 10, 30, 0)  # Saturday
        sat_res = analyze_session(sat_dt)
        self.assertEqual(sat_res.session_type, "WEEKEND")
        self.assertFalse(sat_res.is_tradable_time)
        self.assertTrue(sat_res.is_weekend)

        # Holiday
        gandhi_dt = datetime.datetime(2026, 10, 2, 10, 30, 0)  # Gandhi Jayanti (Holiday)
        gandhi_res = analyze_session(gandhi_dt)
        self.assertEqual(gandhi_res.session_type, "HOLIDAY")
        self.assertFalse(gandhi_res.is_tradable_time)
        self.assertTrue(gandhi_res.is_holiday)

        # Standard market open phase (09:15 to 09:30)
        open_dt = datetime.datetime(2026, 10, 1, 9, 20, 0)  # Thursday
        open_res = analyze_session(open_dt)
        self.assertEqual(open_res.session_type, "MARKET_OPEN")
        self.assertTrue(open_res.is_tradable_time)

        # Morning phase (09:30 to 11:30)
        morning_dt = datetime.datetime(2026, 10, 1, 10, 30, 0)
        morning_res = analyze_session(morning_dt)
        self.assertEqual(morning_res.session_type, "MORNING")
        self.assertTrue(morning_res.is_tradable_time)

        # Mid-session (11:30 to 13:30)
        mid_dt = datetime.datetime(2026, 10, 1, 12, 15, 0)
        mid_res = analyze_session(mid_dt)
        self.assertEqual(mid_res.session_type, "MID_SESSION")
        self.assertTrue(mid_res.is_tradable_time)

        # Afternoon (13:30 to 15:00)
        aft_dt = datetime.datetime(2026, 10, 1, 14, 20, 0)
        aft_res = analyze_session(aft_dt)
        self.assertEqual(aft_res.session_type, "AFTERNOON")
        self.assertTrue(aft_res.is_tradable_time)

        # Closing Session (15:00 to 15:30)
        close_dt = datetime.datetime(2026, 10, 1, 15, 10, 0)
        close_res = analyze_session(close_dt)
        self.assertEqual(close_res.session_type, "CLOSING_SESSION")
        self.assertTrue(close_res.is_tradable_time)

        # Post Market (after 15:30)
        post_dt = datetime.datetime(2026, 10, 1, 16, 0, 0)
        post_res = analyze_session(post_dt)
        self.assertEqual(post_res.session_type, "POST_MARKET")
        self.assertFalse(post_res.is_tradable_time)

    def test_expiry_analysis(self):
        """Verify expiry classifications, remaining days, and far-expiry flagging."""
        today = datetime.date(2026, 10, 1)

        # Expiry Day (days remaining = 0)
        exp_day_res = analyze_expiry(datetime.date(2026, 10, 1), today_date=today)
        self.assertEqual(exp_day_res.days_remaining, 0)
        self.assertTrue(exp_day_res.is_expiry_day)
        self.assertEqual(exp_day_res.classification, "EXPIRY_DAY")

        # Expiry Eve (days remaining = 1)
        exp_eve_res = analyze_expiry(datetime.date(2026, 10, 2), today_date=today)
        self.assertEqual(exp_eve_res.days_remaining, 1)
        self.assertTrue(exp_eve_res.is_expiry_eve)
        self.assertEqual(exp_eve_res.classification, "EXPIRY_EVE")

        # Far Expiry (days remaining > 7)
        far_exp_res = analyze_expiry(datetime.date(2026, 10, 29), today_date=today)
        self.assertEqual(far_exp_res.days_remaining, 28)
        self.assertTrue(far_exp_res.is_far_expiry)
        self.assertEqual(far_exp_res.classification, "FAR_EXPIRY")

    def test_confluence_analysis(self):
        """Verify detection of trend, option, support/resistance, volatility, and liquidity confluence."""
        # Complete aligned bullish case
        res = analyze_confluence(self.market_ctx, self.options_ctx)
        self.assertTrue(res.trend_confluence)
        self.assertTrue(res.option_confluence)
        self.assertTrue(res.sr_alignment)
        self.assertTrue(res.volatility_alignment)
        self.assertTrue(res.liquidity_alignment)
        self.assertTrue(res.overall_confluence)

        # Conflicting/misaligned case
        misaligned_options = OptionContext(
            underlying_spot=24320.0,
            atm_strike=24300.0,
            strike_step=50.0,
            current_weekly_expiry="2026-10-29",
            current_monthly_expiry="2026-10-29",
            time_to_expiry=20.0,
            atm_iv=45.0,  # Extreme IV mismatch with "NORMAL" market volatility
            expected_move=350.0,
            pcr=1.5,  # Bullish PCR (contradicting Bearish market_option_bias)
            max_pain=24300.0,
            highest_call_oi=100000.0,
            highest_put_oi=120000.0,
            highest_call_oi_change=1000.0,
            highest_put_oi_change=1200.0,
            support_strikes=[23000.0],  # Way below technical supports
            resistance_strikes=[26000.0],
            liquidity_metrics={
                "overall_liquidity_score": 10.0,  # Horrible liquidity
                "average_spread_pct": 5.0,        # Wide spread
            },
            option_chain_summary={},
            top_candidate_strikes=[],
            market_option_bias="BEARISH"  # Opposite of "BULLISH" market trend
        )

        misaligned_res = analyze_confluence(self.market_ctx, misaligned_options)
        self.assertFalse(misaligned_res.trend_confluence)
        self.assertFalse(misaligned_res.option_confluence)
        self.assertFalse(misaligned_res.sr_alignment)
        self.assertFalse(misaligned_res.volatility_alignment)
        self.assertFalse(misaligned_res.liquidity_alignment)
        self.assertFalse(misaligned_res.overall_confluence)

    def test_market_readiness(self):
        """Verify market readiness evaluation across session, volatility, and liquidity bounds."""
        # 1. Perfectly healthy case
        session = analyze_session(datetime.datetime(2026, 10, 1, 10, 30, 0))  # Morning
        expiry = analyze_expiry(datetime.date(2026, 10, 29), today_date=datetime.date(2026, 10, 1))
        
        readiness = evaluate_market_readiness(self.market_ctx, self.options_ctx, session, expiry)
        self.assertTrue(readiness.is_market_ready)
        self.assertEqual(readiness.suitability_score, 100.0)

        # 2. Closed market (weekend)
        weekend_session = analyze_session(datetime.datetime(2026, 10, 3, 10, 30, 0))  # Saturday
        readiness_weekend = evaluate_market_readiness(self.market_ctx, self.options_ctx, weekend_session, expiry)
        self.assertFalse(readiness_weekend.is_market_ready)
        self.assertFalse(readiness_weekend.session_suitable)

        # 3. High volatility extreme case
        panic_market = MarketContext(
            current_spot=24320.0,
            timestamp="2026-07-09 15:15:00",
            trading_session="INTRADAY",
            current_expiry="2026-10-29",
            market_regime="TRENDING",
            trend_direction="BULLISH",
            trend_strength=25.0,
            support_levels=[],
            resistance_levels=[],
            vwap=24300.0,
            atr=150.0,
            india_vix=32.0,  # Panic VIX
            volatility_state="EXTREME"
        )
        readiness_vol = evaluate_market_readiness(panic_market, self.options_ctx, session, expiry)
        self.assertFalse(readiness_vol.volatility_suitable)

    def test_trade_context_builder(self):
        """Verify final assembly, immutability, timestamps, and schema version."""
        session = analyze_session(datetime.datetime(2026, 10, 1, 10, 30, 0))
        expiry = analyze_expiry(datetime.date(2026, 10, 29), today_date=datetime.date(2026, 10, 1))
        confluence = analyze_confluence(self.market_ctx, self.options_ctx)
        readiness = evaluate_market_readiness(self.market_ctx, self.options_ctx, session, expiry)

        trade_ctx = TradeContextBuilder.build(
            market=self.market_ctx,
            options=self.options_ctx,
            session=session,
            expiry=expiry,
            confluence=confluence,
            readiness=readiness,
            schema_version="2.1",
            pipeline_version="1.5"
        )

        self.assertIsInstance(trade_ctx, TradeContext)
        self.assertEqual(trade_ctx.schema_version, "2.1")
        self.assertEqual(trade_ctx.pipeline_version, "1.5")
        self.assertIsNotNone(trade_ctx.timestamp)
        self.assertEqual(trade_ctx.session.session_type, "MORNING")
        self.assertEqual(trade_ctx.expiry.days_remaining, 28)
        self.assertTrue(trade_ctx.confluence.overall_confluence)
        self.assertTrue(trade_ctx.readiness.is_market_ready)

        # Test immutability (frozen=True)
        with self.assertRaises(AttributeError):
            trade_ctx.timestamp = "modified"  # type: ignore
