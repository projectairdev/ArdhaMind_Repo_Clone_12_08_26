# tests/test_live_analytics_input_contract_repair.py
"""
Targeted regression test suite for Post-Session Analytics Failure Repair (14-Aug-2026).

Validates:
A. Live canonical input contract (WorkstationStateService -> TodayAnalysisEngine & ForwardOutlookEngine)
B. Forward Outlook live input contract & spot reception
C. Integer breadth coverage (coverage = 50)
D. Dict breadth coverage compatibility (coverage = {"valid": 50})
E. Missing-data safety (when current_spot is absent, INSUFFICIENT_DATA / PARTIAL_EVIDENCE is returned)
F. Recorded 14-Aug session non-mutating reprocessing regression
"""
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.application.workstation_state_service import WorkstationStateService
from src.intelligence_engine.today_analysis_engine import TodayAnalysisEngine
from src.intelligence_engine.forward_outlook_engine import ForwardOutlookEngine


class TestLiveAnalyticsInputContractRepair(unittest.TestCase):

    def _sample_market_data(self, **overrides):
        base = {
            "current_spot": 24366.0,
            "previous_close": 24395.85,
            "open": 24361.9,
            "high": 24404.05,
            "low": 24309.1,
            "trading_session": "OPEN",
            "breadth": {"advances": 11, "declines": 39, "coverage": 50},
            "heavyweights": [
                {"symbol": "RELIANCE", "change": -5.0},
                {"symbol": "HDFCBANK", "change": -2.0}
            ],
            "vwap": 24350.0
        }
        base.update(overrides)
        return base

    def _sample_options(self, **overrides):
        base = {
            "pcr": 1.143,
            "atm_strike": 24350,
            "max_pain": 24400,
            "atm_iv": 8.62,
            "ce_pe_iv_difference": 0.2
        }
        base.update(overrides)
        return base

    def _sample_macro(self, **overrides):
        base = {
            "india_vix": {"value": 11.26, "change": -0.1, "status": "AVAILABLE", "regime": "LOW_VOLATILITY"},
            "quotes": {}
        }
        base.update(overrides)
        return base

    def test_A_live_canonical_input_contract(self):
        """Test WorkstationStateService.build_from_legacy supplies market_data to Today's Analysis."""
        market = self._sample_market_data()
        options = self._sample_options()
        macro = self._sample_macro()

        payload = {
            "marketContext": market,
            "optionContext": options,
            "macroIntelligence": macro,
            "technicalAnalysis": {"trend": "BEARISH", "atr": 120.0},
            "newsSentiment": {},
            "tradeScenarios": []
        }

        state = WorkstationStateService.build_from_legacy(
            payload,
            broker_state="AUTHENTICATED",
            market_state="OPEN"
        )

        today_rep = state.todays_analysis
        self.assertIsNotNone(today_rep)
        self.assertNotIn(today_rep.get("analysis_status"), ["INSUFFICIENT_DATA", "PARTIAL_EVIDENCE"])
        self.assertNotIn(today_rep.get("trend_classification"), ["INSUFFICIENT_DATA", "PARTIAL_EVIDENCE"])
        self.assertEqual(today_rep.get("session_statistics", {}).get("spot"), 24366.0)

    def test_B_forward_outlook_live_input_contract(self):
        """Test Forward Outlook receives spot and does not output 'telemetry unavailable'."""
        market = self._sample_market_data()
        options = self._sample_options()
        macro = self._sample_macro()

        payload = {
            "marketContext": market,
            "optionContext": options,
            "macroIntelligence": macro,
            "technicalAnalysis": {"trend": "BEARISH", "atr": 120.0},
            "newsSentiment": {},
            "tradeScenarios": []
        }

        state = WorkstationStateService.build_from_legacy(
            payload,
            broker_state="AUTHENTICATED",
            market_state="OPEN"
        )

        outlook = state.forward_outlook
        self.assertIsNotNone(outlook)
        self.assertNotEqual(outlook.get("analysis_status"), "INSUFFICIENT_DATA")
        self.assertNotEqual(outlook.get("current_trend"), "INSUFFICIENT_DATA")

        primary_headline = outlook.get("primary_scenario", {}).get("headline", "")
        self.assertNotIn("INSUFFICIENT MARKET DATA", primary_headline)
        self.assertNotIn("telemetry is currently unavailable", outlook.get("primary_scenario", {}).get("description", ""))

    def test_C_integer_breadth_coverage(self):
        """Test integer coverage=50 does not crash TodayAnalysisEngine or ForwardOutlookEngine."""
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": self._sample_market_data(breadth={"advances": 11, "declines": 39, "coverage": 50}),
            "option_intelligence": self._sample_options(),
            "macro_intelligence": self._sample_macro()
        }

        today_rep = TodayAnalysisEngine.analyze(state).to_dict()
        self.assertEqual(today_rep.get("analysis_status"), "READY")

        forward_rep = ForwardOutlookEngine.evaluate_outlook(state, today_rep, {}, []).to_dict()
        self.assertEqual(forward_rep.get("analysis_status"), "READY")

    def test_D_dict_breadth_coverage_compatibility(self):
        """Test dict coverage={'valid': 50} continues working for both engines."""
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": self._sample_market_data(breadth={"advances": 11, "declines": 39, "coverage": {"valid": 50}}),
            "option_intelligence": self._sample_options(),
            "macro_intelligence": self._sample_macro()
        }

        today_rep = TodayAnalysisEngine.analyze(state).to_dict()
        self.assertEqual(today_rep.get("analysis_status"), "READY")

        forward_rep = ForwardOutlookEngine.evaluate_outlook(state, today_rep, {}, []).to_dict()
        self.assertEqual(forward_rep.get("analysis_status"), "READY")

    def test_E_missing_data_safety(self):
        """Test that when current_spot is genuinely absent, fallback non-READY status is preserved."""
        no_spot_market = self._sample_market_data(current_spot=None, breadth={})
        state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": no_spot_market,
            "option_intelligence": self._sample_options(),
            "macro_intelligence": self._sample_macro()
        }

        today_rep = TodayAnalysisEngine.analyze(state).to_dict()
        self.assertIn(today_rep.get("analysis_status"), ["INSUFFICIENT_DATA", "PARTIAL_EVIDENCE"])
        self.assertIsNone(today_rep.get("session_statistics", {}).get("spot"))

        forward_rep = ForwardOutlookEngine.evaluate_outlook(state, today_rep, {}, []).to_dict()
        self.assertEqual(forward_rep.get("analysis_status"), "INSUFFICIENT_DATA")

    def test_F_recorded_session_regression(self):
        """Offline reprocessing of preserved 14-Aug-2026 recorded session history."""
        session_file = Path("/opt/ArdhaMind/data/cache/session_history_2026-08-14.json")
        self.assertTrue(session_file.exists(), "Session history file for 14-Aug-2026 must exist")

        with open(session_file, "r") as f:
            data = json.load(f)

        snapshots = data.get("snapshots", [])
        self.assertGreater(len(snapshots), 0)

        snap = snapshots[-1]
        eval_state = {
            "market_session": {"status": "OPEN", "is_closed": False, "session_date": "2026-08-14"},
            "market_data": {
                "current_spot": snap.get("spot"),
                "previous_close": 24395.85,
                "open": 24361.9,
                "high": 24404.05,
                "low": 24309.1,
                "breadth": snap.get("breadth") or {"advances": 11, "declines": 39, "coverage": 50},
                "trading_session": "OPEN"
            },
            "option_intelligence": snap.get("options") or {"pcr": 1.143, "atm_strike": 24350, "max_pain": 24400},
            "macro_intelligence": {"india_vix": {"value": snap.get("vix"), "change": -0.1}}
        }

        today_rep = TodayAnalysisEngine.analyze(eval_state, snapshots).to_dict()
        self.assertIn(today_rep.get("analysis_status"), ("READY", "PARTIAL"))
        self.assertNotEqual(today_rep.get("trend_classification"), "INSUFFICIENT_DATA")

        forward_rep = ForwardOutlookEngine.evaluate_outlook(eval_state, today_rep, {}, snapshots).to_dict()
        self.assertEqual(forward_rep.get("analysis_status"), "READY")
        self.assertNotEqual(forward_rep.get("current_trend"), "INSUFFICIENT_DATA")


if __name__ == "__main__":
    unittest.main()
