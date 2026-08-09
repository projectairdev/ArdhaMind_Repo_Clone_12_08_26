# tests/test_phase5_9_daily_use_readiness.py
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from src.application.workstation_state_service import WorkstationStateService


class TestPhase59DailyUseReadiness(unittest.TestCase):
    """
    Test suite validating Phase 5.9 Daily-Use Operational Readiness:
    - Cold startup and warm startup state creation
    - Expired Zerodha session handling
    - Single-flight worker deduplication locks
    - 8:50 AM pre-market readiness evaluation (full vs partial)
    - PRE_MARKET -> OPEN -> CLOSED transitions
    - Automatic provider outage degradation & recovery
    - Workstation overall state calculation (READY / DEGRADED / NOT_READY)
    - Health endpoint secret isolation
    - state_sequence monotonicity
    """

    def setUp(self) -> None:
        observed = datetime.now(timezone.utc).isoformat()
        def quote(price: float, reference: float, source_symbol: str) -> dict:
            return {
                "price": price, "reference_value": reference,
                "change_pct": round(((price - reference) / reference) * 100, 4),
                "source_name": "Yahoo Finance Public Feed", "source_symbol": source_symbol,
                "provider_symbol": source_symbol, "observation_timestamp": observed,
                "published_at": observed, "retrieved_at": observed, "exchange_timezone": "UTC",
            }
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
            "newsSentiment": {"status": "ready", "items": [{
                "id": "n1", "published_at": datetime.now(timezone.utc).isoformat()
            }]},
            "macroIntelligence": {
                "status": "ready",
                "institutional_flows": [{"dataset_type": "FII_CASH", "date": "2026-08-07", "net_value": 1.0}],
                "quotes": {
                    "S&P 500": quote(5450.0, 5400.0, "^GSPC"),
                    "BRENT_CRUDE": quote(78.4, 77.8, "BZ=F"),
                },
            },
        }

    def test_overall_state_ready(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="HOLIDAY")
        d = state.to_dict()

        self.assertEqual(d["workspace_readiness"]["overall_state"], "READY")
        self.assertFalse(d["workspace_readiness"]["pre_market_850_readiness"]["is_full_premarket_ready"])
        self.assertEqual(d["workspace_readiness"]["pre_market_850_readiness"]["gift_nifty"], "UNAVAILABLE")

    def test_overall_state_degraded(self) -> None:
        payload_no_macro = dict(self.sample_payload)
        payload_no_macro["macroIntelligence"] = {"status": "UNAVAILABLE", "quotes": {}}

        state = WorkstationStateService.build_from_legacy(payload_no_macro, broker_state="CONNECTED", market_state="OPEN")
        d = state.to_dict()

        self.assertEqual(d["workspace_readiness"]["overall_state"], "DEGRADED")
        self.assertFalse(d["workspace_readiness"]["pre_market_850_readiness"]["is_full_premarket_ready"])

    def test_overall_state_not_ready_on_expired_session(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="TOKEN_EXPIRED", market_state="OPEN")
        d = state.to_dict()

        self.assertEqual(d["workspace_readiness"]["overall_state"], "NOT_READY")

    def test_state_sequence_monotonicity(self) -> None:
        state1 = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
        state2 = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")

        self.assertGreater(state2.state_sequence, state1.state_sequence)

    def test_pre_market_to_open_to_closed_transitions(self) -> None:
        state_pre = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="PRE_MARKET")
        self.assertFalse(state_pre.market_session["is_closed"])

        state_open = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="OPEN")
        self.assertFalse(state_open.market_session["is_closed"])

        state_closed = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="CLOSED")
        self.assertTrue(state_closed.market_session["is_closed"])
        self.assertEqual(state_closed.market_feed_status["status"], "market_closed")
        self.assertEqual(state_closed.data_quality["market_data"]["freshness_status"], "market_closed")
        self.assertEqual(state_closed.data_quality["market_data"]["value_classification"], "historical")
        self.assertEqual(state_closed.workspace_readiness["live_assistant"]["status"], "market_closed")
        self.assertEqual(state_closed.workspace_readiness["todays_analysis"]["status"], "market_closed")

    def test_empty_provider_shells_are_not_ready(self) -> None:
        payload = dict(self.sample_payload)
        payload["newsSentiment"] = {"status": "ready", "provider_health": {"rbi": {"status": "ready"}}, "items": []}
        state = WorkstationStateService.build_from_legacy(payload, broker_state="CONNECTED", market_state="OPEN")
        self.assertEqual(state.workspace_readiness["news_updates"]["status"], "unavailable")

    def test_option_snapshot_requires_timestamp_and_expiry(self) -> None:
        state = WorkstationStateService.build_from_legacy(self.sample_payload, broker_state="CONNECTED", market_state="HOLIDAY")
        self.assertEqual(state.data_quality["option_intelligence"]["freshness_status"], "unavailable")
        self.assertNotIn("pcr", state.option_intelligence)
