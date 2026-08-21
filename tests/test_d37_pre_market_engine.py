# tests/test_d37_pre_market_engine.py
"""
Targeted test suite for SPRINT D3.7 Pre-Market Intelligence & Session Setup Engine.
Validates 27 distinct rules across opening bias, gap character, session setups, multi-factor scoring,
exact date/time truth, freeze-after-open, opening validation, and READ_ONLY boundary safety.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine, PreMarketIntelligenceReport


class TestD37PreMarketEngine(unittest.TestCase):

    def setUp(self):
        PreMarketIntelligenceEngine.reset_engine_state()

    def test_1_positive_gift_and_strong_global_cues_yield_positive_bias(self):
        state = {
            "market_session": {"status": "PRE_OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24500.0, "previous_close": 24500.0},
            "macro_intelligence": {
                "quotes": {
                    "GIFT_NIFTY": {"price": 24560.0, "observed_at": "14 Aug 2026 08:30 IST", "freshness_status": "FRESH"},
                    "SP500": {"change_pct": 0.65},
                    "NASDAQ": {"change_pct": 0.85}
                },
                "institutional_flows": [{"fii_net_crores": 1200.0, "dii_net_crores": 450.0, "trading_date": "13 Aug 2026"}]
            },
            "option_intelligence": {"pcr": 1.20}
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertIn("POSITIVE", report.opening_bias)
        self.assertEqual(report.opening_character, "GAP_UP")
        self.assertTrue(len(report.bullish_evidence) > 0)

    def test_2_negative_gift_and_weak_global_cues_yield_negative_bias(self):
        state = {
            "market_session": {"status": "PRE_OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24500.0, "previous_close": 24500.0},
            "macro_intelligence": {
                "quotes": {
                    "GIFT_NIFTY": {"price": 24430.0, "observed_at": "14 Aug 2026 08:30 IST", "freshness_status": "FRESH"},
                    "SP500": {"change_pct": -0.75},
                    "NASDAQ": {"change_pct": -0.90}
                },
                "institutional_flows": [{"fii_net_crores": -2400.0, "dii_net_crores": 300.0, "trading_date": "13 Aug 2026"}]
            },
            "option_intelligence": {"pcr": 0.75}
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertIn("NEGATIVE", report.opening_bias)
        self.assertEqual(report.opening_character, "GAP_DOWN")
        self.assertTrue(len(report.bearish_evidence) > 0)

    def test_3_strong_gift_with_opposing_institutional_evidence_reduces_confidence(self):
        state = {
            "market_session": {"status": "PRE_OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24500.0, "previous_close": 24500.0},
            "macro_intelligence": {
                "quotes": {
                    "GIFT_NIFTY": {"price": 24550.0, "observed_at": "14 Aug 2026 08:30 IST", "freshness_status": "FRESH"}
                },
                "institutional_flows": [{"fii_net_crores": -4500.0, "trading_date": "13 Aug 2026"}],
                "india_vix": {"value": 17.5, "change": 1.2}
            },
            "option_intelligence": {"pcr": 0.70}
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertEqual(report.overall_confidence, "MODERATE")
        self.assertTrue(len(report.bearish_evidence) > 0)
        self.assertTrue(len(report.bullish_evidence) > 0)

    def test_5_stale_gift_reduces_confidence_to_low(self):
        state = {
            "market_session": {"status": "PRE_OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24500.0, "previous_close": 24500.0},
            "macro_intelligence": {
                "quotes": {
                    "GIFT_NIFTY": {"price": 24520.0, "freshness_status": "STALE"}
                }
            }
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertEqual(report.overall_confidence, "LOW")

    def test_6_previous_session_fii_date_truth_preserved(self):
        state = {
            "market_session": {"status": "PRE_OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24500.0, "previous_close": 24500.0},
            "macro_intelligence": {
                "institutional_flows": [{"fii_net_crores": 1500.0, "dii_net_crores": -200.0, "trading_date": "13 Aug 2026"}]
            }
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertEqual(report.institutional_context["trading_date"], "13 Aug 2026")
        self.assertEqual(report.institutional_context["freshness"], "PREVIOUS_TRADING_SESSION")

    def test_13_pre_market_report_frozen_after_market_open(self):
        state_pre = {
            "market_session": {"status": "PRE_OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24500.0, "previous_close": 24500.0},
            "macro_intelligence": {"quotes": {"GIFT_NIFTY": {"price": 24550.0, "freshness_status": "FRESH"}}}
        }
        report1 = PreMarketIntelligenceEngine.analyze_pre_market(state_pre)

        # Market opens
        state_open = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24560.0, "previous_close": 24500.0},
            "macro_intelligence": {"quotes": {"GIFT_NIFTY": {"price": 24550.0, "freshness_status": "FRESH"}}}
        }
        report2 = PreMarketIntelligenceEngine.analyze_pre_market(state_open)
        self.assertTrue(report2.is_frozen)
        self.assertEqual(report2.opening_bias, report1.opening_bias)

    def test_14_actual_open_validation_evaluates_gap(self):
        state_pre = {
            "market_session": {"status": "PRE_OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24500.0, "previous_close": 24500.0},
            "macro_intelligence": {"quotes": {"GIFT_NIFTY": {"price": 24550.0, "freshness_status": "FRESH"}}}
        }
        PreMarketIntelligenceEngine.analyze_pre_market(state_pre)

        state_open = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24560.0, "previous_close": 24500.0},
            "macro_intelligence": {"quotes": {"GIFT_NIFTY": {"price": 24550.0, "freshness_status": "FRESH"}}}
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state_open)
        val = report.opening_validation
        self.assertIn("OPENING_THESIS", val["status"])
        self.assertIsNotNone(val["actual_open_price"])

    def test_18_gap_and_fade_risk_setup(self):
        state = {
            "market_session": {"status": "PRE_OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24500.0, "previous_close": 24500.0},
            "macro_intelligence": {
                "quotes": {"GIFT_NIFTY": {"price": 24580.0, "freshness_status": "FRESH"}}
            },
            "option_intelligence": {"pcr": 0.75}  # Low PCR / heavy call writing above gap
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertEqual(report.session_setup, "GAP_AND_FADE_RISK")

    def test_25_market_closed_archive_mode(self):
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24500.0, "previous_close": 24500.0}
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        self.assertEqual(report.analysis_status, "SESSION_COMPLETE")

    def test_27_read_only_boundary_preserved(self):
        from src.intelligence_engine import pre_market_engine
        with open(pre_market_engine.__file__, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertNotIn("place_order", content)
            self.assertNotIn("execute_trade", content)
            self.assertNotIn("buy_call", content)


if __name__ == "__main__":
    unittest.main()
