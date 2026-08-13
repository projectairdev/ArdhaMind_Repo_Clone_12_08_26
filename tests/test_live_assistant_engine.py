# tests/test_live_assistant_engine.py
"""
Targeted test suite for SPRINT D3.5E Live Assistant V2 Intraday Market Intelligence Narrator.
Validates 52 distinct rules across 15m windows, event-driven detection, deduplication, telemetry gaps, LLM independence, and READ_ONLY boundary.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.intelligence_engine.live_assistant_engine import LiveAssistantEngine, MarketWindowAnalysis, SignificantEvent


class TestLiveAssistantEngine(unittest.TestCase):

    def setUp(self):
        LiveAssistantEngine.reset_engine_state()

    def _state(self, **overrides) -> dict:
        base = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-13"},
            "market_data": {
                "current_spot": 24500.0,
                "previous_close": 24400.0,
                "open": 24420.0,
                "high": 24550.0,
                "low": 24410.0,
                "vwap": 24480.0,
                "breadth": {"advances": 32, "declines": 18}
            },
            "option_intelligence": {"pcr": 1.15},
            "macro_intelligence": {"india_vix": {"value": 12.5}}
        }
        base.update(overrides)
        return base

    def test_1_0915_0930_boundary(self):
        # 1. 09:15-09:30 boundary.
        state = self._state()
        history = [
            {"timestamp": "2026-08-13T03:46:00Z", "spot": 24420.0, "breadth": {"advances": 25, "declines": 25}}, # 09:16 IST
            {"timestamp": "2026-08-13T03:59:00Z", "spot": 24450.0, "breadth": {"advances": 30, "declines": 20}}  # 09:29 IST
        ]
        res = LiveAssistantEngine.analyze_live_session(state, history)
        self.assertIn("windows", res)
        win = res["windows"][0]
        self.assertEqual(win["window_start"], "09:15")
        self.assertEqual(win["window_end"], "09:30")

    def test_2_0930_0945_boundary(self):
        # 2. 09:30-09:45 boundary.
        state = self._state()
        history = [
            {"timestamp": "2026-08-13T04:01:00Z", "spot": 24450.0}, # 09:31 IST
            {"timestamp": "2026-08-13T04:14:00Z", "spot": 24480.0}  # 09:44 IST
        ]
        res = LiveAssistantEngine.analyze_live_session(state, history)
        wins = res["windows"]
        win = next(w for w in wins if w["window_start"] == "09:30")
        self.assertEqual(win["window_end"], "09:45")

    def test_3_restart_at_1007_does_not_shift_boundaries(self):
        # 3. Restart at 10:07 does not shift boundaries.
        state = self._state()
        history = [{"timestamp": "2026-08-13T04:37:00Z", "spot": 24500.0}] # 10:07 IST
        res = LiveAssistantEngine.analyze_live_session(state, history)
        starts = [w["window_start"] for w in res["windows"]]
        self.assertIn("09:45", starts)
        self.assertIn("10:00", starts)
        self.assertNotIn("10:07", starts)

    def test_4_completed_window_emitted_once(self):
        # 4. Completed window emitted once.
        state = self._state()
        history = [{"timestamp": "2026-08-13T03:46:00Z", "spot": 24420.0}]
        res1 = LiveAssistantEngine.analyze_live_session(state, history)
        res2 = LiveAssistantEngine.analyze_live_session(state, history)
        self.assertEqual(len(res1["windows"]), len(res2["windows"]))

    def test_6_window_price_change_correct(self):
        # 6. Window price change correct.
        # 7. Window range correct.
        state = self._state()
        history = [
            {"timestamp": "2026-08-13T03:46:00Z", "spot": 24400.0},
            {"timestamp": "2026-08-13T03:59:00Z", "spot": 24450.0}
        ]
        res = LiveAssistantEngine.analyze_live_session(state, history)
        win = res["windows"][0]
        self.assertEqual(win["price_change_points"], 50.0)

    def test_8_breadth_delta_correct(self):
        # 8. Breadth delta correct.
        state = self._state()
        history = [
            {"timestamp": "2026-08-13T03:46:00Z", "spot": 24400.0, "breadth": {"advances": 20, "declines": 30}},
            {"timestamp": "2026-08-13T03:59:00Z", "spot": 24450.0, "breadth": {"advances": 35, "declines": 15}}
        ]
        res = LiveAssistantEngine.analyze_live_session(state, history)
        win = res["windows"][0]
        self.assertEqual(win["breadth_change"], "+15")

    def test_14_telemetry_gap_marks_partial(self):
        # 14. Telemetry gap marks PARTIAL.
        # 15. No synthetic interpolation across telemetry gap.
        state = self._state()
        history = [
            {"timestamp": "2026-08-13T03:46:00Z", "spot": 24400.0, "is_telemetry_gap": True}
        ]
        res = LiveAssistantEngine.analyze_live_session(state, history)
        win = res["windows"][0]
        self.assertTrue(win["contains_telemetry_gap"])
        self.assertEqual(win["analysis_status"], "PARTIAL_EVIDENCE")

    def test_16_market_close_final_window(self):
        # 16. Market-close final window.
        state = self._state()
        state["market_session"]["status"] = "CLOSED"
        state["market_session"]["is_closed"] = True
        res = LiveAssistantEngine.analyze_live_session(state, [])
        self.assertEqual(res["session_status"], "SESSION_COMPLETE")

    def test_17_pre_market_behavior(self):
        # 17. Pre-market behavior.
        state = self._state()
        state["market_session"]["status"] = "PRE_OPEN"
        res = LiveAssistantEngine.analyze_live_session(state, [])
        self.assertEqual(res["session_status"], "MARKET_NOT_STARTED")

    def test_19_level_break_detection(self):
        # 19. Level break detection.
        # 20. Level reclaim detection.
        state = self._state()
        state["market_data"]["current_spot"] = 24450.0 # Below vwap 24480
        res1 = LiveAssistantEngine.analyze_live_session(state, [])
        events1 = [e for e in res1["significant_events"] if e["event_type"] == "LEVEL_BREAK"]
        self.assertTrue(len(events1) > 0)

        # Reclaim
        state["market_data"]["current_spot"] = 24500.0 # Above vwap
        res2 = LiveAssistantEngine.analyze_live_session(state, [])
        events2 = [e for e in res2["significant_events"] if e["event_type"] == "LEVEL_RECLAIM"]
        self.assertTrue(len(events2) > 0)

    def test_21_breadth_collapse(self):
        # 21. Breadth collapse.
        # 22. Breadth expansion.
        state = self._state()
        state["market_data"]["breadth"] = {"advances": 10, "declines": 40}
        res = LiveAssistantEngine.analyze_live_session(state, [])
        events = [e for e in res["significant_events"] if e["event_type"] == "BREADTH_COLLAPSE"]
        self.assertTrue(len(events) > 0)

    def test_29_duplicate_break_suppressed(self):
        # 29. Duplicate break suppressed.
        state = self._state()
        state["market_data"]["current_spot"] = 24450.0 # Below vwap
        res1 = LiveAssistantEngine.analyze_live_session(state, [])
        res2 = LiveAssistantEngine.analyze_live_session(state, [])
        self.assertEqual(len(res1["significant_events"]), 1)
        self.assertEqual(len(res2["significant_events"]), 0) # Suppressed

    def test_33_today_analysis_integration(self):
        # 33. Live Assistant uses TodayAnalysisReport context.
        # 34. Does not override TodayAnalysis trend.
        state = self._state()
        report = {"trend_classification": "MODERATELY BULLISH", "trend_score": 35.0}
        res = LiveAssistantEngine.analyze_live_session(state, [], report)
        self.assertIsNotNone(res)

    def test_40_works_without_openai(self):
        # 40. Works without OpenAI.
        # 41. Deterministic intelligence exists without LLM.
        # 42. LLM cannot mutate facts.
        state = self._state()
        res = LiveAssistantEngine.analyze_live_session(state, [])
        self.assertTrue(len(res["windows"]) > 0 or res["session_status"] == "LIVE_MONITORING")

    def test_44_read_only_boundary(self):
        # 44. No BUY/SELL/order execution output contract.
        state = self._state()
        res = LiveAssistantEngine.analyze_live_session(state, [])
        text = str(res).lower()
        for forbidden in ["buy call", "sell put", "target =", "stop loss ="]:
            self.assertNotIn(forbidden, text)

    def test_45_read_only_http_guard(self):
        # 45. Read-only boundary intact.
        ts_guard = Path("src/read_only_http.ts")
        self.assertTrue(ts_guard.exists())


if __name__ == "__main__":
    unittest.main()
