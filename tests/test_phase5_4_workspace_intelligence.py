# tests/test_phase5_4_workspace_intelligence.py
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from src.application.workstation_state_service import WorkstationStateService
from src.models.canonical_workstation_state import CanonicalWorkstationState
from src.models.data_quality import SectionStatus


class TestPhase54WorkspaceIntelligence(unittest.TestCase):
    """
    Test suite validating Phase 5.4 workspace intelligence:
    - Workspace readiness across all 6 primary workspaces
    - Partial provider degradation & stale data handling
    - Missing macro/news inputs fallback
    - Pre-market scenario generation
    - Morning vs live market comparison
    - Confirmation and invalidation tracking logic
    - Canonical frontend rendering contracts
    """

    def setUp(self) -> None:
        self.sample_payload = {
            "marketContext": {
                "current_spot": 24500.0,
                "spot_change": 125.0,
                "spot_change_pct": 0.51,
                "vwap": 24450.0,
                "atr": 180.0,
                "india_vix": 13.5,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            "optionContext": {
                "pcr": 1.15,
                "max_pain": 24500,
                "atm_iv": 13.5,
                "straddle_width": 180,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            "newsSentiment": {
                "status": "ready",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "items": [{"id": "news-1", "headline": "RBI keeps repo rate unchanged"}],
            },
            "macroIntelligence": {
                "status": "ready",
                "quotes": {"GIFT_NIFTY": {"symbol": "GIFT_NIFTY", "price": 24550.0}},
                "domain_freshness": {"global_quotes": "fresh"},
            },
            "eveningReport": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tomorrow_outlook": {
                    "directional_bias": "BULLISH",
                    "expected_trading_range": {"min_limit": 24420, "max_limit": 24650},
                },
            },
            "intradayReport": {
                "summary": {"plan_status": "PLAN_VALID", "overall_pcr_shift": 0.05, "overall_vix_shift": -0.02},
            },
        }

    def test_workspace_readiness_all_six_workspaces(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
        readiness = state.workspace_readiness

        self.assertIn("nifty_live", readiness)
        self.assertIn("pre_market_planner", readiness)
        self.assertIn("todays_analysis", readiness)
        self.assertIn("news_updates", readiness)
        self.assertIn("live_assistant", readiness)
        self.assertIn("settings", readiness)

        self.assertTrue(readiness["nifty_live"]["accessible"])
        self.assertTrue(readiness["settings"]["accessible"])

    def test_partial_provider_degradation(self) -> None:
        # Simulate missing news provider payload
        payload_degraded = dict(self.sample_payload)
        payload_degraded["newsSentiment"] = {"status": "UNAVAILABLE", "items": []}

        state = WorkstationStateService.build_from_legacy(payload_degraded, broker_state="CONNECTED", market_state="OPEN")
        self.assertEqual(state.workspace_readiness["news_updates"]["status"], SectionStatus.UNAVAILABLE.value)
        self.assertTrue(state.workspace_readiness["nifty_live"]["accessible"])

    def test_missing_macro_news_inputs_fallback(self) -> None:
        payload_empty = {
            "marketContext": {"current_spot": 24500.0, "observed_at": datetime.now(timezone.utc).isoformat()},
            "optionContext": {"pcr": 1.0, "observed_at": datetime.now(timezone.utc).isoformat()},
        }
        state = WorkstationStateService.build_from_legacy(payload_empty, broker_state="CONNECTED", market_state="OPEN")
        state_dict = state.to_dict()

        self.assertIsInstance(state_dict, dict)
        self.assertIn("macro_intelligence", state_dict)
        self.assertEqual(state_dict["macro_intelligence"]["quotes"], {})
        self.assertEqual(state_dict["macro_intelligence"]["quote_status"]["GIFT_NIFTY"]["reason"], "GENUINE_PROVIDER_NOT_CONFIGURED")

    def test_pre_market_scenario_generation(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
        evening = state.evening_report

        self.assertEqual(evening["tomorrow_outlook"]["directional_bias"], "BULLISH")
        self.assertEqual(evening["tomorrow_outlook"]["expected_trading_range"]["min_limit"], 24420)

    def test_morning_vs_live_comparison_logic(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
        spot = state.market_data.get("current_spot", 0)
        vwap = state.market_data.get("vwap", 0)

        # Morning expectations vs actual VWAP relationship
        self.assertGreaterEqual(spot, vwap)

    def test_confirmation_and_invalidation_logic(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
        decision = state.decision_support

        self.assertEqual(decision["current_scenario_status"], "monitor")
        self.assertIn("required_confirmations", decision)

    def test_canonical_frontend_rendering_contracts(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
        d = state.to_dict()

        self.assertEqual(d["schema_version"], "2.0.0")
        self.assertIn("runtime_id", d)
        self.assertIn("state_sequence", d)
        self.assertIn("market_data", d)
        self.assertIn("option_intelligence", d)
        self.assertIn("news_intelligence", d)
        self.assertIn("macro_intelligence", d)
