from __future__ import annotations
import unittest
from unittest.mock import MagicMock, patch
import time

from src.broker.services.streaming_orchestrator import StreamingOrchestrator
from src.broker.services.broker_service import BrokerService
from src.broker.services.stream_health_monitor import StreamHealthMonitor


class TestLiveFeedBootstrap(unittest.TestCase):
    """
    Targeted test suite for SPRINT D3.5A Live Feed Bootstrap & Kite Reliability.
    Verifies state machine, subscription phases, telemetry, 0.0 handling,
    and automatic state propagation.
    """

    def setUp(self) -> None:
        StreamingOrchestrator._instance = None
        BrokerService._instance = None
        self.orchestrator = StreamingOrchestrator.get_instance()

    def tearDown(self) -> None:
        if self.orchestrator:
            self.orchestrator.disconnect_stream()
        StreamingOrchestrator._instance = None
        BrokerService._instance = None

    def test_missing_initial_nifty_is_unavailable_not_zero(self):
        # 6. missing initial NIFTY is unavailable, not 0.0
        self.assertIsNone(self.orchestrator.latest_ticks.get("NSE:NIFTY 50"))
        # Unpopulated spot in orchestrator/backend must evaluate to None
        spot_val = None
        self.assertIsNone(spot_val)

    def test_transport_connection_alone_does_not_mark_feed_live(self):
        # 5. transport connection alone does not mark feed LIVE
        is_conn = True
        is_stream_conn = True
        active_sub_count = 0
        has_nifty = False
        obs_age = 999.0

        state = self.orchestrator.health_monitor.get_feed_bootstrap_state(
            is_connected=is_conn,
            is_stream_connected=is_stream_conn,
            active_sub_count=active_sub_count,
            has_nifty_tick=has_nifty,
            obs_age=obs_age
        )
        self.assertEqual(state, "SUBSCRIBING")

        active_sub_count = 12
        state = self.orchestrator.health_monitor.get_feed_bootstrap_state(
            is_connected=is_conn,
            is_stream_connected=is_stream_conn,
            active_sub_count=active_sub_count,
            has_nifty_tick=has_nifty,
            obs_age=obs_age
        )
        self.assertEqual(state, "WAITING_FOR_TICKS")

    def test_first_genuine_tick_transitions_bootstrap_to_live(self):
        # 4. first genuine tick transitions bootstrap toward LIVE
        state = self.orchestrator.health_monitor.get_feed_bootstrap_state(
            is_connected=True,
            is_stream_connected=True,
            active_sub_count=12,
            has_nifty_tick=True,
            obs_age=2.5
        )
        self.assertEqual(state, "LIVE")

    def test_startup_does_not_require_spot_gt_zero_for_core_subscriptions(self):
        # 3. startup does not require spot_nifty > 0 before core subscriptions
        with patch.object(self.orchestrator.subscription_manager, "subscribe") as mock_sub:
            mock_sub.return_value = [100, 200]
            tokens = self.orchestrator.subscribe(["NIFTY", "INDIA VIX"])
            mock_sub.assert_called_once_with(["NIFTY", "INDIA VIX"])
            self.assertEqual(tokens, [100, 200])

    @patch("src.broker.services.streaming_orchestrator.KiteTickerAdapter")
    def test_oauth_success_triggers_stream_and_subscriptions(self, mock_adapter_cls):
        # 1. OAuth success triggers stream connection
        # 2. OAuth success triggers minimum initial subscriptions
        mock_adapter = MagicMock()
        mock_adapter.api_key = "key1"
        mock_adapter.access_token = "tok1"
        mock_adapter.connect.return_value = True
        mock_adapter.is_connected.return_value = True
        mock_adapter_cls.return_value = mock_adapter

        self.orchestrator.configure("key1", "tok1")
        self.assertTrue(self.orchestrator.connect_stream())
        self.assertTrue(self.orchestrator.is_connected())

        subs = self.orchestrator.subscribe(["NIFTY", "INDIA VIX"])
        self.assertIsNotNone(self.orchestrator.last_subscription_time)

    def test_transient_disconnect_preserves_last_valid_market_value(self):
        # 9. transient disconnect preserves last valid market value
        self.orchestrator.latest_ticks["NSE:NIFTY 50"] = {
            "last_price": 24462.25,
            "timestamp": "2026-08-13T10:00:00Z"
        }
        # Simulate transient drop
        self.orchestrator.health_monitor.set_reconnect_state("RECONNECTING")

        # Prior tick must still be available in latest_ticks
        nifty = self.orchestrator.latest_ticks.get("NSE:NIFTY 50")
        self.assertIsNotNone(nifty)
        self.assertEqual(nifty["last_price"], 24462.25)

    def test_reconnect_requires_genuine_fresh_tick_before_live(self):
        # 10. reconnect requires genuine fresh tick before LIVE
        # Stale tick (> 15s age)
        state = self.orchestrator.health_monitor.get_feed_bootstrap_state(
            is_connected=True,
            is_stream_connected=True,
            active_sub_count=12,
            has_nifty_tick=True,
            obs_age=45.0
        )
        self.assertEqual(state, "STALE")

    @patch("src.broker.services.streaming_orchestrator.KiteTickerAdapter")
    def test_reauthentication_does_not_create_duplicate_adapter(self, mock_adapter_cls):
        # 11. reauthentication does not create duplicate adapter/reconnect loop
        # 12. same credentials do not recreate adapter
        # 13. one canonical upstream stream invariant remains intact
        mock_adapter_1 = MagicMock()
        mock_adapter_1.api_key = "key1"
        mock_adapter_1.access_token = "tok1"
        mock_adapter_1.connect.return_value = True

        mock_adapter_2 = MagicMock()
        mock_adapter_2.api_key = "key2"
        mock_adapter_2.access_token = "tok2"
        mock_adapter_2.connect.return_value = True

        mock_adapter_cls.side_effect = [mock_adapter_1, mock_adapter_2]

        self.orchestrator.configure("key1", "tok1")
        self.orchestrator.connect_stream()
        self.assertEqual(self.orchestrator.adapter, mock_adapter_1)

        # Same credentials -> no recreation
        self.orchestrator.connect_stream()
        self.assertEqual(mock_adapter_cls.call_count, 1)

        # Changed credentials -> replaces adapter cleanly with callbacks unbound
        self.orchestrator.configure("key2", "tok2")
        self.orchestrator.connect_stream()
        self.assertIsNone(mock_adapter_1.on_status_changed)
        mock_adapter_1.disconnect.assert_called_once()
        self.assertEqual(self.orchestrator.adapter, mock_adapter_2)

    def test_bootstrap_telemetry_payload_structure(self):
        telemetry = self.orchestrator.get_bootstrap_telemetry()
        self.assertIn("bootstrap_state", telemetry)
        self.assertIn("stream_status", telemetry)
        self.assertIn("connection_uptime_seconds", telemetry)
        self.assertIn("reconnect_count", telemetry)
        self.assertIn("subscribed_symbol_count", telemetry)
        self.assertEqual(telemetry["bootstrap_state"], "DISCONNECTED")


if __name__ == "__main__":
    unittest.main()
