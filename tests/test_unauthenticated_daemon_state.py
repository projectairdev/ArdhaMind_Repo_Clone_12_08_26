import unittest
from unittest.mock import patch, MagicMock
from src.broker.services.broker_service import BrokerService
from src.broker.services.session_manager import SessionManager
from src.broker.services.streaming_orchestrator import StreamingOrchestrator
from src.broker.models.stream_health import StreamHealthReport
from src.configuration_engine.runtime import Config


class TestUnauthenticatedDaemonState(unittest.TestCase):

    def setUp(self):
        self.bs = BrokerService.get_instance()
        # Use temporary session cache path for testing to preserve live production session
        self.test_cache_path = "/tmp/test_session_unauth_daemon.json"
        self._orig_cache_path = getattr(Config, "SESSION_CACHE_PATH", ".cache/session.json")
        Config.SESSION_CACHE_PATH = self.test_cache_path
        # Reset gateway credentials for unauthenticated state test
        self.bs._gateway.access_token = None
        self.bs._gateway.api_key = ""
        self.bs._gateway._connected = False
        SessionManager.delete_session()

    def tearDown(self):
        SessionManager.delete_session()
        Config.SESSION_CACHE_PATH = getattr(self, "_orig_cache_path", ".cache/session.json")

    def test_get_bootstrap_telemetry_unauthenticated_does_not_throw(self):
        """Unauthenticated telemetry call returns explicit state without PermissionError."""
        telemetry = self.bs.get_bootstrap_telemetry()
        self.assertIsInstance(telemetry, dict)
        self.assertIn("bootstrap_state", telemetry)
        self.assertIn(telemetry["bootstrap_state"], ["AUTH_REQUIRED", "DISCONNECTED"])
        self.assertEqual(telemetry["stream_status"], "DISCONNECTED")
        self.assertEqual(telemetry["subscribed_symbol_count"], 0)
        self.assertIsNone(telemetry.get("tick_age_seconds"))

    def test_get_stream_health_unauthenticated_does_not_throw(self):
        """Unauthenticated stream health call returns StreamHealthReport without PermissionError."""
        report = self.bs.get_stream_health()
        self.assertIsInstance(report, StreamHealthReport)
        self.assertEqual(report.connection_status, "DISCONNECTED")
        self.assertIn(report.feed_liveness_status, ["AUTH_REQUIRED", "DISCONNECTED"])
        self.assertIsNone(report.observation_age_seconds)

    def test_get_orchestrator_protection_boundary_intact(self):
        """Calling _get_orchestrator() directly without auth STILL raises PermissionError."""
        with self.assertRaises(PermissionError) as ctx:
            self.bs._get_orchestrator()
        self.assertIn("A genuine authenticated Kite session is required", str(ctx.exception))

    def test_no_orchestrator_or_kiteticker_created_when_unauthenticated(self):
        """Ensure no StreamingOrchestrator instance is constructed when getting telemetry unauthenticated."""
        with patch.object(StreamingOrchestrator, "get_instance") as mock_get_inst:
            telemetry = self.bs.get_bootstrap_telemetry()
            health = self.bs.get_stream_health()
            connected = self.bs.is_stream_connected()
            mock_get_inst.assert_not_called()

    def test_explicit_logout_remains_disconnected(self):
        """Explicit logout sets SessionManager state to DISCONNECTED and telemetry reflects DISCONNECTED."""
        SessionManager.delete_session()
        self.assertTrue(SessionManager.is_explicitly_logged_out())
        telemetry = self.bs.get_bootstrap_telemetry()
        self.assertEqual(telemetry["bootstrap_state"], "DISCONNECTED")
        self.assertEqual(telemetry["stream_status"], "DISCONNECTED")

    def test_authenticated_path_returns_real_bootstrap_telemetry(self):
        """When genuine credentials exist, _get_orchestrator succeeds and real telemetry is returned."""
        self.bs._gateway.api_key = "valid_api_key"
        self.bs._gateway.access_token = "valid_access_token"
        self.bs._gateway._connected = True

        with patch("src.broker.services.streaming_orchestrator.StreamingOrchestrator.get_bootstrap_telemetry") as mock_telemetry:
            mock_telemetry.return_value = {
                "bootstrap_state": "LIVE",
                "stream_status": "CONNECTED",
                "connection_started_at": "2026-08-14T00:00:00Z",
                "connection_uptime_seconds": 120.0,
                "generation_id": 1,
                "reconnect_count": 0,
                "last_reconnect_time": None,
                "subscribed_symbol_count": 12,
                "last_subscription_time": "2026-08-14T00:00:00Z",
                "last_valid_tick_time": "2026-08-14T00:01:00Z",
                "last_valid_nifty_time": "2026-08-14T00:01:00Z",
                "tick_age_seconds": 1.2,
                "connection_telemetry": []
            }
            res = self.bs.get_bootstrap_telemetry()
            self.assertEqual(res["bootstrap_state"], "LIVE")
            self.assertEqual(res["stream_status"], "CONNECTED")

    def test_read_only_invariants_intact(self):
        """Verify order mutations remain disabled."""
        with self.assertRaises(PermissionError):
            self.bs.place_order()
        with self.assertRaises(PermissionError):
            self.bs.modify_order()
        with self.assertRaises(PermissionError):
            self.bs.cancel_order()


if __name__ == "__main__":
    unittest.main()
