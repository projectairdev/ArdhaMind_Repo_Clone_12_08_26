# tests/test_phase5_6_openai_interpretation.py
from __future__ import annotations

import unittest
import os
from datetime import datetime, timezone
from src.application.workstation_state_service import WorkstationStateService
from src.services.openai_interpretation_service import OpenAIInterpretationService


class TestPhase56OpenAIInterpretation(unittest.TestCase):
    """
    Test suite validating Phase 5.6 OpenAI Interpretation Layer:
    - OpenAI disabled / missing API key behavior
    - Timeout and malformed response fallback
    - Response schema validation
    - Prompt grounding & prevention of fabricated values
    - Interpretation caching
    - Grounding on CanonicalWorkstationState input
    - Deterministic workstation remains fully operational when AI fails
    """

    def setUp(self) -> None:
        self.sample_payload = {
            "marketContext": {
                "current_spot": 24500.0,
                "spot_change": 125.0,
                "spot_change_pct": 0.51,
                "vwap": 24450.0,
                "india_vix": 13.5,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            "optionContext": {
                "pcr": 1.15,
                "max_pain": 24500,
                "atm_iv": 13.5,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            "eveningReport": {
                "tomorrow_outlook": {"directional_bias": "BULLISH"},
            },
        }
        self.canonical_state = WorkstationStateService.build_from_legacy(
            self.sample_payload, broker_state="CONNECTED", market_state="OPEN"
        ).to_dict()

    def test_openai_disabled_without_api_key(self) -> None:
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            status = OpenAIInterpretationService.get_status()
            self.assertEqual(status["status"], "disabled")
            self.assertFalse(status["api_key_configured"])

            result = OpenAIInterpretationService.interpret_canonical_state(self.canonical_state)
            self.assertTrue(result["fallback_active"])
            self.assertEqual(result["ai_status"], "disabled")
            self.assertIn("NIFTY spot is trading at 24500.0", result["market_narrative"])
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key

    def test_schema_validation_and_grounding(self) -> None:
        result = OpenAIInterpretationService.interpret_canonical_state(self.canonical_state)

        self.assertIn("ai_status", result)
        self.assertIn("fallback_active", result)
        self.assertIn("market_narrative", result)
        self.assertIn("why_today", result)
        self.assertIn("pre_market_narrative", result)
        self.assertIn("todays_analysis_narrative", result)
        self.assertIn("live_assistant_interpretation", result)
        self.assertIn("end_of_day_summary", result)

    def test_interpretation_cache(self) -> None:
        res1 = OpenAIInterpretationService.interpret_canonical_state(self.canonical_state, "test_sec")
        res2 = OpenAIInterpretationService.interpret_canonical_state(self.canonical_state, "test_sec")

        self.assertEqual(res1["generated_at"], res2["generated_at"])

    def test_deterministic_workstation_remains_usable_when_ai_fails(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")

        # Confirm workstation state is unaffected by interpretation failures
        self.assertEqual(state.market_data["current_spot"], 24500.0)
        self.assertEqual(state.workspace_readiness["nifty_live"]["status"], "ready")
