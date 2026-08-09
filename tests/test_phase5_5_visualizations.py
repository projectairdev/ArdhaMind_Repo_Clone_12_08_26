# tests/test_phase5_5_visualizations.py
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from src.application.workstation_state_service import WorkstationStateService


class TestPhase55Visualizations(unittest.TestCase):
    """
    Test suite validating Phase 5.5 Professional Market Visualizations:
    - Rendering contracts
    - Empty datasets handling
    - Stale data fallback
    - Partial provider degradation
    - Chart data mapping
    - Canonical state integration
    """

    def setUp(self) -> None:
        self.sample_payload = {
            "marketContext": {
                "current_spot": 24500.0,
                "spot_change": 125.0,
                "spot_change_pct": 0.51,
                "vwap": 24450.0,
                "ema_20": 24430.0,
                "ema_50": 24380.0,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            "optionContext": {
                "pcr": 1.15,
                "max_pain": 24500,
                "atm_iv": 13.5,
                "straddle_width": 180,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            "macroIntelligence": {
                "status": "ready",
                "quotes": {
                    "GIFT_NIFTY": {"symbol": "GIFT_NIFTY", "price": 24550.0, "category": "GLOBAL_INDEX"},
                    "S&P 500": {"symbol": "S&P 500", "price": 5450.0, "category": "GLOBAL_INDEX"},
                },
                "domain_freshness": {"global_quotes": "fresh"},
            },
        }

    def test_rendering_contracts(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
        d = state.to_dict()

        self.assertIn("market_data", d)
        self.assertEqual(d["market_data"]["current_spot"], 24500.0)
        self.assertEqual(d["option_intelligence"]["pcr"], 1.15)

    def test_empty_datasets_handling(self) -> None:
        payload_empty = {}
        state = WorkstationStateService.build_from_legacy(payload_empty, broker_state="DISCONNECTED", market_state="CLOSED")
        d = state.to_dict()

        self.assertIsInstance(d, dict)
        self.assertIn("market_data", d)
        self.assertIn("option_intelligence", d)

    def test_stale_data_fallback(self) -> None:
        payload_stale = dict(self.sample_payload)
        payload_stale["marketContext"]["observed_at"] = "2026-08-01T00:00:00Z"  # Old timestamp

        state = WorkstationStateService.build_from_legacy(payload_stale, broker_state="CONNECTED", market_state="OPEN")
        d = state.to_dict()

        self.assertIn("data_quality", d)

    def test_partial_provider_degradation(self) -> None:
        payload_partial = dict(self.sample_payload)
        payload_partial["macroIntelligence"] = {"status": "DEGRADED", "quotes": {}}

        state = WorkstationStateService.build_from_legacy(payload_partial, broker_state="CONNECTED", market_state="OPEN")
        d = state.to_dict()

        self.assertIn("macro_intelligence", d)
        self.assertEqual(d["macro_intelligence"]["status"], "DEGRADED")

    def test_chart_data_mapping(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
        spot = state.market_data.get("current_spot")
        vwap = state.market_data.get("vwap")

        self.assertEqual(spot, 24500.0)
        self.assertEqual(vwap, 24450.0)

    def test_canonical_state_integration(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
        self.assertEqual(state.schema_version, "2.0.0")
        self.assertIsNotNone(state.generated_at)
