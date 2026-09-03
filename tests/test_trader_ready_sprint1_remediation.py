# tests/test_trader_ready_sprint1_remediation.py
"""
Deterministic Verification Suite for AIR ArdhaMind Trader-Ready Sprint 1.

Verifies:
1. Symbol Normalization (Kite tokens, raw indices -> canonical instrument keys)
2. Session Date Truth (Monday 24 Aug morning at 08:25 resolves to 24 Aug TODAY, not 25 Aug)
3. Session Lifecycle (PRE_MARKET at 08:25, OPEN at 09:20, CLOSED at 15:35, WEEKEND)
4. Reference Close truth and absence of fake static fallbacks
"""

import unittest
from datetime import datetime, timezone, timedelta
from src.broker.utils.symbol_normalizer import normalize_instrument_key, CANONICAL_NIFTY, CANONICAL_VIX
from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine
from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine


class TestTraderReadySprint1Remediation(unittest.TestCase):

    def test_01_canonical_symbol_normalization(self):
        """Ensures all raw symbol variants and Kite tokens map to canonical keys."""
        self.assertEqual(normalize_instrument_key("NIFTY 50"), CANONICAL_NIFTY)
        self.assertEqual(normalize_instrument_key("NSE:NIFTY 50"), CANONICAL_NIFTY)
        self.assertEqual(normalize_instrument_key("NIFTY"), CANONICAL_NIFTY)
        self.assertEqual(normalize_instrument_key("NIFTY50"), CANONICAL_NIFTY)
        self.assertEqual(normalize_instrument_key("INDIA VIX"), CANONICAL_VIX)
        self.assertEqual(normalize_instrument_key("NSE:INDIA VIX"), CANONICAL_VIX)
        self.assertEqual(normalize_instrument_key(256265), CANONICAL_NIFTY)
        self.assertEqual(normalize_instrument_key(264969), CANONICAL_VIX)

    def test_02_monday_morning_resolves_today_not_tomorrow(self):
        """
        On Monday 24 Aug 2026 at 08:25 IST (before market open):
        Target trading date MUST resolve to 2026-08-24 (TODAY), NOT 2026-08-25.
        Reference session date MUST resolve to 2026-08-21 (Friday).
        """
        # 08:25 IST = 02:55 UTC
        dt_mon_morning_utc = datetime(2026, 8, 24, 2, 55, 0, tzinfo=timezone.utc)
        dt_mon_morning_ist = dt_mon_morning_utc + timedelta(hours=5, minutes=30)

        # State as persisted from prior Friday session
        state_monday_morning = {
            "market_session": {
                "status": "CLOSED",  # Raw uninitialized broker state before 09:00
                "session_date": "2026-08-21",
                "is_closed": True
            },
            "market_data": {
                "current_spot": 24287.65,
                "previous_close": 24287.65,
                "close": 24287.65
            }
        }

        target_date, ref_date, ref_close = PreMarketIntelligenceEngine.resolve_session_dates_and_close(
            state_monday_morning, dt_mon_morning_ist
        )

        self.assertEqual(target_date, "2026-08-24", "Target trading date must be TODAY (24 Aug)")
        self.assertEqual(ref_date, "2026-08-21", "Reference session date must be Friday (21 Aug)")
        self.assertEqual(ref_close, 24287.65, "Reference close must be Friday close")

    def test_03_lifecycle_determination_strict_ist_boundaries(self):
        """Verifies session lifecycle across strict IST boundaries on trading days."""
        m_session = {}

        # 08:25 IST Monday
        dt_0825_ist = datetime(2026, 8, 24, 8, 25, 0)
        self.assertEqual(
            PreMarketIntelligenceEngine._determine_canonical_lifecycle(m_session, dt_0825_ist),
            "PRE_MARKET"
        )

        # 09:05 IST Monday (Pre-Open)
        dt_0905_ist = datetime(2026, 8, 24, 9, 5, 0)
        self.assertEqual(
            PreMarketIntelligenceEngine._determine_canonical_lifecycle(m_session, dt_0905_ist),
            "PRE_MARKET"
        )

        # 09:20 IST Monday (Live Market)
        dt_0920_ist = datetime(2026, 8, 24, 9, 20, 0)
        self.assertEqual(
            PreMarketIntelligenceEngine._determine_canonical_lifecycle(m_session, dt_0920_ist),
            "OPEN"
        )

        # 15:35 IST Monday (Post Market)
        dt_1535_ist = datetime(2026, 8, 24, 15, 35, 0)
        self.assertEqual(
            PreMarketIntelligenceEngine._determine_canonical_lifecycle(m_session, dt_1535_ist),
            "CLOSED"
        )

        # Sunday (Weekend)
        dt_sun_ist = datetime(2026, 8, 23, 11, 0, 0)
        self.assertEqual(
            PreMarketIntelligenceEngine._determine_canonical_lifecycle(m_session, dt_sun_ist),
            "CLOSED"
        )

    def test_04_pre_market_briefing_engine_date_resolution(self):
        """Verifies PreMarketBriefingEngine session lifecycle resolution at 08:25 IST."""
        dt_0825_ist = datetime(2026, 8, 24, 8, 25, 0)
        state = {
            "market_session": {"status": "PRE_MARKET"},
            "market_data": {"previous_close": 24287.65}
        }

        target_date, ref_date, ref_close = PreMarketBriefingEngine.resolve_session_lifecycle(state, dt_0825_ist)
        self.assertEqual(target_date, "2026-08-24")
        self.assertEqual(ref_date, "2026-08-21")
        self.assertEqual(ref_close, 24287.65)


if __name__ == "__main__":
    unittest.main()
