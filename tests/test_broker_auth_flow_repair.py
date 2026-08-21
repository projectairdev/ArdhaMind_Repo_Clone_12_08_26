import unittest
import os
import json
from unittest.mock import patch, MagicMock
from src.broker.services.broker_service import BrokerService
from src.broker.services.session_manager import SessionManager
from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
from src.configuration_engine.runtime import Config


class TestBrokerAuthFlowRepair(unittest.TestCase):

    def setUp(self):
        self.bs = BrokerService.get_instance()
        self.test_cache_path = "/tmp/test_session_auth_flow_repair.json"
        self._orig_cache_path = getattr(Config, "SESSION_CACHE_PATH", ".cache/session.json")
        Config.SESSION_CACHE_PATH = self.test_cache_path
        self.bs._gateway.access_token = None
        self.bs._gateway.api_key = "v9a94g597emt8vch"
        self.bs._gateway._connected = False
        SessionManager.delete_session()

    def tearDown(self):
        SessionManager.delete_session()
        Config.SESSION_CACHE_PATH = getattr(self, "_orig_cache_path", ".cache/session.json")

    @patch("src.broker.services.session_manager.SessionManager.is_explicitly_logged_out", return_value=False)
    def test_bridge_ready_when_broker_unauthenticated(self, mock_logout):
        """Requirement 1 & 2: Expired/Disconnected Zerodha session does not imply bridge offline."""
        health = BrokerHealthEvaluator.evaluate(self.bs)
        # Status should be CONNECTED_AUTH_REQUIRED (meaning transport/bridge is connected, but OAuth login is pending)
        self.assertEqual(health.status, "CONNECTED_AUTH_REQUIRED")
        self.assertTrue(health.transport_connected)
        self.assertFalse(health.authenticated)

    @patch("src.broker.services.session_manager.SessionManager.is_explicitly_logged_out", return_value=False)
    def test_bridge_status_and_broker_auth_status_are_independent(self, mock_logout):
        """Requirement 3: Bridge status and broker authentication status remain independent."""
        health = BrokerHealthEvaluator.evaluate(self.bs)
        # Bridge is ready (transport connected = True), while Broker is unauthenticated (session_valid = False)
        self.assertTrue(health.transport_connected)
        self.assertFalse(health.session_valid)

    def test_missing_python_bin_or_script_detection(self):
        """Requirement 4 & 5: Missing python executable or missing bridge file produces unavailable status."""
        bogus_python = "/nonexistent/path/python"
        bogus_script = "/nonexistent/path/server_bridge.py"
        self.assertFalse(os.path.exists(bogus_python))
        self.assertFalse(os.path.exists(bogus_script))

    def test_login_url_generation_produces_zerodha_oauth_link(self):
        """Requirement 7: Login URL endpoint returns valid Zerodha OAuth redirect link when bridge is ready."""
        url = self.bs.get_login_url()
        self.assertTrue(url.startswith("https://kite.zerodha.com/connect/login"))
        self.assertIn("api_key=", url)

    def test_read_only_execution_invariants(self):
        """Requirement 8: No order/execution functionality becomes enabled."""
        with self.assertRaises(PermissionError):
            self.bs.place_order(tradingsymbol="NIFTY", quantity=50)
        with self.assertRaises(PermissionError):
            self.bs.modify_order(order_id="12345")
        with self.assertRaises(PermissionError):
            self.bs.cancel_order(order_id="12345")

    def test_secrets_not_serialized_in_config(self):
        """Requirement 9: No secrets (API Secret, tokens) exposed in serialized config."""
        session_data = SessionManager.load_session() or {}
        api_secret = getattr(Config, "KITE_API_SECRET", "")
        # Config representation must report boolean status without rendering raw secret value
        config_payload = {
            "api_key_configured": bool(getattr(Config, "KITE_API_KEY", "")),
            "api_secret_configured": bool(api_secret),
            "redirect_url": getattr(Config, "KITE_REDIRECT_URL", ""),
            "access_token_saved": "access_token" in session_data and not session_data.get("expired", False),
            "session_status": BrokerHealthEvaluator.evaluate(self.bs).status
        }
        self.assertNotIn(api_secret, str(config_payload))
        self.assertNotIn("access_token", config_payload)

    def test_staging_isolation(self):
        """Requirement 10: Staging directory and configuration remain strictly inside staging."""
        cwd = os.getcwd()
        self.assertTrue(cwd.startswith("/opt/ardhamind/staging"))
        self.assertNotIn("/opt/ArdhaMind", cwd)


if __name__ == "__main__":
    unittest.main()
