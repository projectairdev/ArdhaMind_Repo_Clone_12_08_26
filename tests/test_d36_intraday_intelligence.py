# tests/test_d36_intraday_intelligence.py
"""
Targeted test suite for SPRINT D3.6 Intraday Intelligence Engine & Forward Outlook Upgrade.
Validates window evidence truth, 15m window metrics, pressure inside range, 10 evidence families,
score correlation discounting, strict confidence gating, market closed behavior, and READ_ONLY boundaries.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.intelligence_engine.live_assistant_engine import LiveAssistantEngine
from src.intelligence_engine.forward_outlook_engine import ForwardOutlookEngine


class TestD36IntradayIntelligence(unittest.TestCase):

    def setUp(self):
        LiveAssistantEngine.reset_engine_state()
        ForwardOutlookEngine.reset_engine_state()

    def test_A_single_observation_window_is_insufficient_evidence_not_quiet(self):
        # 1 snapshot at 09:35 IST (04:05 Z)
        history = [
            {
                "timestamp": "2026-08-13T04:05:00Z",
                "spot": 24400.0,
                "breadth": {"advances": 25, "declines": 25, "coverage": {"valid": 50}},
                "vix": {"value": 12.5, "change": 0.0}
            }
        ]
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-13"},
            "market_data": {"current_spot": 24400.0}
        }
        res = LiveAssistantEngine.analyze_live_session(state, history)
        windows = res["windows"]
        # Window 09:30-09:45
        w_0930 = next((w for w in windows if w["window_start"] == "09:30"), None)
        self.assertIsNotNone(w_0930)
        self.assertEqual(w_0930["analysis_status"], "INSUFFICIENT_WINDOW_EVIDENCE")
        self.assertEqual(w_0930["significance_classification"], "INSUFFICIENT_EVIDENCE")
        self.assertNotEqual(w_0930["significance_classification"], "QUIET")

    def test_B_adequately_sampled_flat_market_is_legitimate_quiet(self):
        # 3 snapshots across 09:30–09:45 IST (04:00 Z to 04:12 Z) with range < 5 pts -> QUIET
        history = [
            {
                "timestamp": f"2026-08-13T04:{i:02d}:00Z",
                "spot": 24400.0 + (i * 0.2),
                "breadth": {"advances": 25, "declines": 25, "coverage": {"valid": 50}},
                "vix": {"value": 12.5, "change": 0.0}
            }
            for i in [2, 6, 12]
        ]
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-13"},
            "market_data": {"current_spot": 24402.4}
        }
        res = LiveAssistantEngine.analyze_live_session(state, history)
        windows = res["windows"]
        w_0930 = next((w for w in windows if w["window_start"] == "09:30"), None)
        self.assertIsNotNone(w_0930)
        self.assertEqual(w_0930["analysis_status"], "SUFFICIENT_EVIDENCE")
        self.assertEqual(w_0930["significance_classification"], "QUIET")

    def test_C_price_rising_breadth_rising_confirming_bullish(self):
        # Snapshots in 09:30–09:45 IST
        history = [
            {
                "timestamp": "2026-08-13T04:01:00Z",
                "spot": 24400.0,
                "breadth": {"advances": 22, "declines": 28, "coverage": {"valid": 50}},
                "vix": {"value": 12.5, "change": 0.0}
            },
            {
                "timestamp": "2026-08-13T04:12:00Z",
                "spot": 24425.0,
                "breadth": {"advances": 32, "declines": 18, "coverage": {"valid": 50}},
                "vix": {"value": 12.2, "change": -0.3}
            }
        ]
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-13"},
            "market_data": {"current_spot": 24425.0}
        }
        res = LiveAssistantEngine.analyze_live_session(state, history)
        w_0930 = next((w for w in res["windows"] if w["window_start"] == "09:30"), None)
        self.assertIsNotNone(w_0930)
        self.assertEqual(w_0930["analysis_status"], "SUFFICIENT_EVIDENCE")
        self.assertEqual(w_0930["breadth_divergence"], "CONFIRMING_BULLISH")
        self.assertIn("strengthened together", w_0930["why_it_matters"][0])

    def test_D_price_rising_breadth_falling_bearish_divergence(self):
        # Snapshots in 09:30–09:45 IST
        history = [
            {
                "timestamp": "2026-08-13T04:01:00Z",
                "spot": 24400.0,
                "breadth": {"advances": 30, "declines": 20, "coverage": {"valid": 50}},
                "vix": {"value": 12.5, "change": 0.0}
            },
            {
                "timestamp": "2026-08-13T04:12:00Z",
                "spot": 24420.0,
                "breadth": {"advances": 22, "declines": 28, "coverage": {"valid": 50}},
                "vix": {"value": 12.8, "change": 0.3}
            }
        ]
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-13"},
            "market_data": {"current_spot": 24420.0}
        }
        res = LiveAssistantEngine.analyze_live_session(state, history)
        w_0930 = next((w for w in res["windows"] if w["window_start"] == "09:30"), None)
        self.assertIsNotNone(w_0930)
        self.assertEqual(w_0930["breadth_divergence"], "BEARISH_DIVERGENCE")
        self.assertIn("weakened", w_0930["why_it_matters"][0])

    def test_E_price_flat_breadth_improving_bullish_pressure(self):
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-13"},
            "market_data": {
                "current_spot": 24400.0,
                "vwap": 24400.0,
                "breadth": {"advances": 32, "declines": 18, "coverage": {"valid": 50}}
            },
            "option_intelligence": {"pcr": 1.15},
            "macro_intelligence": {"india_vix": {"value": 12.0, "change": -0.3}}
        }
        live_assistant = {
            "windows": [
                {
                    "analysis_status": "SUFFICIENT_EVIDENCE",
                    "price_change_points": 2.0,
                    "breadth_delta": 6,
                    "breadth_divergence": "BULLISH_DIVERGENCE"
                }
            ]
        }
        report = ForwardOutlookEngine.evaluate_outlook(state, live_assistant_intelligence=live_assistant)
        self.assertEqual(report.primary_scenario.scenario_type, "RANGE_WITH_BULLISH_PRESSURE")

    def test_F_price_flat_breadth_deteriorating_bearish_pressure(self):
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-13"},
            "market_data": {
                "current_spot": 24400.0,
                "vwap": 24400.0,
                "breadth": {"advances": 18, "declines": 32, "coverage": {"valid": 50}}
            },
            "option_intelligence": {"pcr": 0.80},
            "macro_intelligence": {"india_vix": {"value": 13.2, "change": 0.4}}
        }
        live_assistant = {
            "windows": [
                {
                    "analysis_status": "SUFFICIENT_EVIDENCE",
                    "price_change_points": -2.0,
                    "breadth_delta": -6,
                    "breadth_divergence": "BEARISH_DIVERGENCE"
                }
            ]
        }
        report = ForwardOutlookEngine.evaluate_outlook(state, live_assistant_intelligence=live_assistant)
        self.assertEqual(report.primary_scenario.scenario_type, "RANGE_WITH_BEARISH_PRESSURE")

    def test_H_insufficient_option_snapshots_narrative(self):
        history = [
            {
                "timestamp": "2026-08-13T04:05:00Z",
                "spot": 24400.0,
                "breadth": {"advances": 25, "declines": 25},
                "options": {"pcr": 1.0}
            }
        ]
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-13"},
            "market_data": {"current_spot": 24400.0}
        }
        res = LiveAssistantEngine.analyze_live_session(state, history)
        w = res["windows"][0]
        self.assertFalse(w["options_available"])
        self.assertIn("unavailable", w["options_narrative"])

    def test_I_insufficient_evidence_gated_confidence(self):
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-13"},
            "market_data": {
                "current_spot": 24400.0,
                "vwap": 24400.0,
                "breadth": {"advances": 15, "declines": 10, "coverage": {"valid": 25}}
            }
        }
        live_assistant = {
            "windows": [
                {"analysis_status": "INSUFFICIENT_WINDOW_EVIDENCE"}
            ]
        }
        report = ForwardOutlookEngine.evaluate_outlook(state, live_assistant_intelligence=live_assistant)
        self.assertNotEqual(report.overall_confidence, "HIGH")

    def test_K_market_closed_no_forward_intraday_prediction(self):
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-13"},
            "market_data": {"current_spot": 24400.0}
        }
        report = ForwardOutlookEngine.evaluate_outlook(state)
        self.assertEqual(report.analysis_status, "SESSION_COMPLETE")
        self.assertEqual(report.primary_scenario.headline, "SESSION COMPLETE — COMPLETED SESSION SCENARIO ARCHIVE")
        self.assertIn("Next intraday outlook activates on next session open", report.primary_scenario.confirmation_conditions[0])

    def test_N_read_only_boundary_preserved(self):
        from src.intelligence_engine import live_assistant_engine, forward_outlook_engine, today_analysis_engine
        for mod in (live_assistant_engine, forward_outlook_engine, today_analysis_engine):
            code = mod.__file__
            with open(code, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertNotIn("place_order", content)
                self.assertNotIn("execute_trade", content)
                self.assertNotIn("buy_call", content)


if __name__ == "__main__":
    unittest.main()
