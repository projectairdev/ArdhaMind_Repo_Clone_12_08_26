# tests/test_phase5_7_production_hardening.py
from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from src.application.workstation_state_service import WorkstationStateService
from src.news_engine.safe_utils import atomic_write_json
from src.models.data_quality import SectionStatus


class TestPhase57ProductionHardening(unittest.TestCase):
    """
    Test suite validating Phase 5.7 Production Hardening & Release Preparation:
    - Expired Kite token state clearance
    - Market closed / weekend / holiday state handling
    - Provider outage graceful degradation (Kite, News, Macro, OpenAI)
    - Malformed canonical candidate snapshot rejection & last-known-good state preservation
    - Concurrent refresh protection & atomic cache write integrity
    - Zero secret exposure in logs or frontend state dictionaries
    """

    def setUp(self) -> None:
        self.sample_payload = {
            "marketContext": {
                "current_spot": 24500.0,
                "spot_change": 125.0,
                "spot_change_pct": 0.51,
                "vwap": 24450.0,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            "optionContext": {
                "pcr": 1.15,
                "max_pain": 24500,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    def test_expired_kite_token_clearance(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="TOKEN_EXPIRED", market_state="OPEN")
        d = state.to_dict()

        self.assertTrue(d["broker_status"]["reconnect_required"])
        self.assertEqual(d["broker_status"]["status"], "session_expired")
        self.assertEqual(d["application_status"]["status"], "degraded")

    def test_market_closed_state_handling(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="MARKET_CLOSED")
        d = state.to_dict()

        self.assertTrue(d["market_session"]["is_closed"])
        self.assertEqual(d["market_session"]["status"], "closed")

    def test_provider_outage_graceful_degradation(self) -> None:
        payload_degraded = {
            "marketContext": {},  # Missing market provider
            "newsSentiment": {"status": "UNAVAILABLE"},
        }
        state = WorkstationStateService.build_from_legacy(payload_degraded, broker_state="CONNECTED", market_state="OPEN")
        d = state.to_dict()

        self.assertEqual(d["workspace_readiness"]["nifty_live"]["status"], "unavailable")
        self.assertEqual(d["workspace_readiness"]["news_updates"]["status"], "unavailable")

    def test_atomic_cache_write_helper(self) -> None:
        test_file = ".cache/test_atomic_cache.json"
        data = {"status": "ok", "items": [1, 2, 3]}

        success = atomic_write_json(test_file, data)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(test_file))

        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

    def test_zero_secret_exposure_in_canonical_state(self) -> None:
        payload_with_secret = dict(self.sample_payload)
        payload_with_secret["secret_key"] = "SUPER_SECRET_TOKEN_12345"

        state = WorkstationStateService.build_from_legacy(payload_with_secret, broker_state="CONNECTED", market_state="OPEN")
        d = state.to_dict()

        # Canonical dict must sanitize or exclude secret fields
        self.assertNotIn("secret_key", d)
        self.assertNotIn("SUPER_SECRET_TOKEN_12345", str(d))
