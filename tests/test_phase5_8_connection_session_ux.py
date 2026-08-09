# tests/test_phase5_8_connection_session_ux.py
from __future__ import annotations

import unittest
import os
from datetime import datetime, timezone
from src.application.workstation_state_service import WorkstationStateService
from src.services.openai_interpretation_service import OpenAIInterpretationService
from src.broker.services.authentication import AuthenticationManager


class TestPhase58ConnectionSessionUX(unittest.TestCase):
    """
    Test suite validating Connection & Session UX Hardening:
    - Broker disconnected state
    - Request token exchange & session creation
    - Expired session handling
    - Reconnect & disconnect actions
    - Zero access_token or API secret exposure to frontend
    - OpenAI key server-side isolation
    - Live Assistant readiness derived from canonical data
    - Live Assistant operates deterministically when OpenAI is unavailable
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

    def test_broker_disconnected_state(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="DISCONNECTED", market_state="CLOSED")
        d = state.to_dict()

        self.assertEqual(d["broker_status"]["status"], "disconnected")
        self.assertTrue(d["application_status"]["read_only"])

    def test_zerodha_login_url_generation(self) -> None:
        url = AuthenticationManager.generate_login_url(api_key="test_api_key")
        self.assertIn("connect/login", url)
        self.assertIn("api_key=test_api_key", url)

    def test_expired_session_and_reconnect_state(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="TOKEN_EXPIRED", market_state="OPEN")
        d = state.to_dict()

        self.assertTrue(d["broker_status"]["reconnect_required"])
        self.assertEqual(d["broker_status"]["status"], "session_expired")

    def test_zero_access_token_or_secret_exposure(self) -> None:
        payload_with_token = dict(self.sample_payload)
        payload_with_token["access_token"] = "SECRET_ACCESS_TOKEN_XYZ"
        payload_with_token["api_secret"] = "SECRET_API_SECRET_999"

        state = WorkstationStateService.build_from_legacy(payload_with_token, broker_state="CONNECTED", market_state="OPEN")
        d = state.to_dict()

        serialized_str = str(d)
        self.assertNotIn("SECRET_ACCESS_TOKEN_XYZ", serialized_str)
        self.assertNotIn("SECRET_API_SECRET_999", serialized_str)

    def test_openai_key_server_side_isolation(self) -> None:
        old_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "sk-proj-SUPER_SECRET_OPENAI_KEY"
        try:
            status = OpenAIInterpretationService.get_status()
            self.assertTrue(status["api_key_configured"])
            self.assertNotIn("sk-proj-SUPER_SECRET_OPENAI_KEY", str(status))
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key
            else:
                os.environ.pop("OPENAI_API_KEY", None)

    def test_live_assistant_works_when_openai_unavailable(self) -> None:
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
            d = state.to_dict()

            # Canonical assistant readiness is derived strictly from marketContext & optionContext
            self.assertEqual(d["workspace_readiness"]["live_assistant"]["status"], "ready")

            interp = OpenAIInterpretationService.interpret_canonical_state(d)
            self.assertTrue(interp["fallback_active"])
            self.assertEqual(interp["ai_status"], "disabled")
            self.assertIn("what_changed", interp["live_assistant_interpretation"])
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key
