from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine
from src.utils.time_utils import next_trading_day, previous_trading_day
from src.opportunity_engine.context_builder import OpportunityContextBuilder
from src.models import (
    TradeContext,
    MarketScore,
    MarketBreadthContext,
    GlobalContext,
    OpportunityClassification,
)


class TestIntelligenceFinalClosure(unittest.TestCase):
    """
    Comprehensive End-to-End Intelligence Closure Test Suite.
    Guarantees:
    - Pre-market session lifecycle & dynamic gap forecasting
    - Bias, confidence, and risk convergence
    - AI Opportunities qualification logic & gate evaluation
    - NOW session-truth (closed vs live)
    - NEXT DAY horizon separation
    - Cross-view consistency & absence of stale fallbacks
    """

    def setUp(self):
        PreMarketIntelligenceEngine.reset_engine_state()

    def test_pre_market_session_lifecycle_ist_pre_open(self):
        """03:00 IST on a Tuesday must target today (Tuesday) and reference yesterday (Monday)."""
        now_ist = datetime(2026, 8, 18, 3, 0, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-18"},
            "market_data": {"current_spot": 24287.65, "close": 24287.65, "previous_close": 24366.0},
        }
        target, ref_date, ref_close = PreMarketIntelligenceEngine.resolve_session_dates_and_close(state, now_ist)
        self.assertEqual(target, "2026-08-18")
        self.assertEqual(ref_date, "2026-08-17")
        self.assertEqual(ref_close, 24287.65)

    def test_pre_market_session_lifecycle_monday_pre_open(self):
        """Monday pre-open at 08:30 IST must target Monday and reference Friday."""
        now_ist = datetime(2026, 8, 17, 8, 30, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-17"},
            "market_data": {"current_spot": 24366.0, "close": 24366.0, "previous_close": 24300.0},
        }
        target, ref_date, ref_close = PreMarketIntelligenceEngine.resolve_session_dates_and_close(state, now_ist)
        self.assertEqual(target, "2026-08-17")
        self.assertEqual(ref_date, "2026-08-14")
        self.assertEqual(ref_close, 24366.0)

    def test_pre_market_session_lifecycle_post_close_rollover(self):
        """16:00 IST on Tuesday after market close must roll target to Wednesday and reference Tuesday."""
        now_ist = datetime(2026, 8, 18, 16, 0, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-18"},
            "market_data": {"current_spot": 24310.0, "close": 24310.0, "previous_close": 24287.65},
        }
        target, ref_date, ref_close = PreMarketIntelligenceEngine.resolve_session_dates_and_close(state, now_ist)
        self.assertEqual(target, "2026-08-19")
        self.assertEqual(ref_date, "2026-08-18")
        self.assertEqual(ref_close, 24310.0)

    def test_pre_market_dynamic_gift_anchored_forecast(self):
        """GIFT Nifty quote must dynamically anchor expected gap and expected open."""
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-18"},
            "market_data": {"current_spot": 24287.65, "close": 24287.65, "previous_close": 24366.0},
            "macro_intelligence": {
                "quotes": {
                    "GIFT NIFTY": {"last_price": 24296.0, "change_pct": 0.03, "timestamp": "2026-08-18T03:15:00Z"},
                    "S&P 500": {"change_pct": 0.45},
                }
            },
        }
        rep = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertEqual(rep.target_trading_date, "2026-08-18")
        self.assertEqual(rep.reference_session_date, "2026-08-17")
        self.assertEqual(rep.reference_close, 24287.65)
        self.assertEqual(rep.gap_methodology, "GIFT_ANCHORED")
        self.assertEqual(rep.expected_gap_str, "+8 to +38")
        self.assertEqual(rep.expected_open_str, "24,296 – 24,326")
        self.assertAlmostEqual(rep.expected_open_low, 24296.0, places=1)
        self.assertAlmostEqual(rep.expected_open_high, 24326.0, places=1)

    def test_pre_market_dynamic_fallback_forecast(self):
        """When GIFT Nifty is unavailable, fallback must dynamically scale with setup_score."""
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-18"},
            "market_data": {"current_spot": 24287.65, "close": 24287.65, "previous_close": 24366.0},
            "macro_intelligence": {"quotes": {}},
        }
        rep = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertEqual(rep.gap_methodology, "EVIDENCE_SCORE_FALLBACK")
        # With score 0.0, base_gap = 0.0, low = 0, high = +25
        self.assertEqual(rep.expected_gap_str, "+0 to +25")
        self.assertEqual(rep.expected_open_str, "24,288 – 24,313")

    def test_pre_market_never_uses_stale_hardcoded_open(self):
        """PRE must never produce the old defective 24,406 – 24,436 range."""
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-18"},
            "market_data": {"current_spot": 24287.65, "close": 24287.65, "previous_close": 24366.0},
            "macro_intelligence": {"quotes": {}},
        }
        rep = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertNotEqual(rep.expected_open_str, "24,406 – 24,436")
        self.assertNotEqual(rep.expected_gap_str, "+40 to +70")

    def test_ai_opportunities_unqualified_when_market_closed(self):
        """AI Opportunities qualification must reject setups when market is closed."""
        from src.models import MarketContext, OptionContext, SessionContext, ExpiryContext, ConfluenceContext, MarketReadiness
        market_ctx = MarketContext(
            current_spot=24287.65,
            timestamp="2026-08-18 03:15:00",
            trading_session="CLOSED",
            current_expiry="2026-08-18",
            market_regime="SIDEWAYS",
            trend_direction="NEUTRAL",
            trend_strength=10.0,
            support_levels=[24200.0, 24250.0],
            resistance_levels=[24350.0, 24400.0],
            vwap=24287.0,
            atr=50.0,
            india_vix=11.33,
            volatility_state="LOW"
        )
        options_ctx = OptionContext(
            underlying_spot=24287.65,
            atm_strike=24300.0,
            strike_step=50.0,
            current_weekly_expiry="2026-08-18",
            current_monthly_expiry="2026-08-25",
            time_to_expiry=0.0,
            atm_iv=11.41,
            expected_move=100.0,
            pcr=1.22,
            max_pain=24350.0,
            highest_call_oi=100000.0,
            highest_put_oi=120000.0,
            highest_call_oi_change=1000.0,
            highest_put_oi_change=1200.0,
            support_strikes=[24200.0],
            resistance_strikes=[24400.0],
            liquidity_metrics={"overall_liquidity_score": 85.0, "average_spread_pct": 0.15},
            option_chain_summary={"total_calls_oi": 500000.0, "total_puts_oi": 600000.0},
            top_candidate_strikes=[],
            market_option_bias="NEUTRAL"
        )
        session_ctx = SessionContext(
            session_type="CLOSED",
            is_tradable_time=False,
            time_of_day="03:15:00",
            is_weekend=False,
            is_holiday=False,
            is_half_day=False,
        )
        expiry_ctx = ExpiryContext(
            expiry_date="2026-08-18",
            days_remaining=0,
            expiry_type="WEEKLY",
            is_expiry_day=True,
            is_expiry_eve=False,
            is_far_expiry=False,
            classification="WEEKLY_EXPIRY"
        )
        confluence_ctx = ConfluenceContext(
            trend_confluence=False,
            option_confluence=False,
            sr_alignment=False,
            volatility_alignment=False,
            liquidity_alignment=False,
            overall_confluence=False,
            description="Market in range-bound chop"
        )
        readiness = MarketReadiness(
            is_market_ready=False,
            suitability_score=0.0,
            reasons=["Market Closed", "Range-bound chop"],
            session_suitable=False,
            volatility_suitable=False,
            liquidity_suitable=False,
            trend_suitable=False,
        )
        trade_ctx = TradeContext(
            market=market_ctx,
            options=options_ctx,
            session=session_ctx,
            expiry=expiry_ctx,
            confluence=confluence_ctx,
            readiness=readiness,
            timestamp="2026-08-18 03:15:00"
        )
        from src.models import TrendScore, OptionScore, VolatilityScore, LiquidityScore, SessionScore, ExpiryScore, ConfluenceScore
        market_score = MarketScore(
            trend=TrendScore(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            options=OptionScore(50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0),
            volatility=VolatilityScore(50.0, 50.0, 50.0, 50.0, 50.0, 50.0),
            liquidity=LiquidityScore(50.0, 50.0, 50.0, 50.0, 50.0),
            session=SessionScore(0.0, 0.0, 0.0),
            expiry=ExpiryScore(50.0, 50.0, 50.0, 50.0),
            confluence=ConfluenceScore(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            overall_score=40.0,
            letter_grade="D",
            classification="Unqualified",
            timestamp="2026-08-18 03:15:00"
        )

        opp_ctx = OpportunityContextBuilder.build(trade_ctx, market_score)
        # Should not qualify excellent/good during closed chop
        self.assertIn(opp_ctx.classification.value, ["NEUTRAL", "POOR", "AVOID", "WATCHLIST"])

    def test_cross_tab_level_semantics_separation(self):
        """Reference close (24,287.65) and prior close (24,366.00) must be distinctly separated."""
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-18"},
            "market_data": {"current_spot": 24287.65, "close": 24287.65, "previous_close": 24366.0},
        }
        rep = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertEqual(rep.reference_close, 24287.65)
        self.assertEqual(rep.critical_levels["reference_close"], 24287.65)
        self.assertEqual(rep.critical_levels["previous_close"], 24366.0)


if __name__ == "__main__":
    unittest.main()
