from __future__ import annotations
import os
import time
import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from src.broker.models.trading_mode import TradingMode, BrokerType
from src.broker.models.health import BrokerHealth
from src.broker.utils.cache_manager import InstrumentCacheManager
import src.broker.utils.cache_manager as cache_manager
from tests.support.mock_broker_gateway import MockBrokerGateway
from tests.support.fake_kiteconnect import FakeKiteConnect
from src.broker.adapters.kite_broker import KiteBrokerGateway
from src.broker.services.broker_service import BrokerService
from src.broker.services.authentication import AuthenticationManager
from src.broker.services.session_manager import SessionManager
from src.broker.utils.errors import (
    BrokerError,
    InvalidAPIKeyError,
    InvalidAPISecretError,
    ExpiredRequestTokenError,
    ExpiredAccessTokenError,
    NetworkFailureError,
    SessionMissingError,
    AuthenticationFailureError,
)
from src.configuration_engine.runtime import Config


class TestBrokerFoundationLayer(unittest.TestCase):
    """
    Unit tests for the production-grade Broker Foundation Layer (Sprint 27 & 28).
    """

    def setUp(self) -> None:
        # Save original config
        self._orig_api_key = getattr(Config, "KITE_API_KEY", "")
        self._orig_api_secret = getattr(Config, "KITE_API_SECRET", "")
        self._orig_cache_path = getattr(Config, "SESSION_CACHE_PATH", ".cache/session.json")
        self._orig_trading_mode = getattr(Config, "TRADING_MODE", "PAPER_TRADING")
        self._orig_instrument_db_path = cache_manager.DB_PATH

        # Configure temporary test credentials
        Config.KITE_API_KEY = "test_api_key"
        Config.KITE_API_SECRET = "test_api_secret"
        Config.SESSION_CACHE_PATH = ".cache/test_session.json"
        Config.TRADING_MODE = "PAPER_TRADING"
        cache_manager.DB_PATH = ".cache/test_instruments.db"

        # Reset BrokerService singleton for isolation
        BrokerService._instance = None

        # Ensure clean session cache state and instrument cache state
        SessionManager.delete_session()
        if os.path.exists(cache_manager.DB_PATH):
            try:
                os.remove(cache_manager.DB_PATH)
            except Exception:
                pass

    def tearDown(self) -> None:
        # Delete temporary test session
        SessionManager.delete_session()
        if os.path.exists(cache_manager.DB_PATH):
            try:
                os.remove(cache_manager.DB_PATH)
            except Exception:
                pass

        # Restore original config
        Config.KITE_API_KEY = self._orig_api_key
        Config.KITE_API_SECRET = self._orig_api_secret
        Config.SESSION_CACHE_PATH = self._orig_cache_path
        Config.TRADING_MODE = self._orig_trading_mode
        cache_manager.DB_PATH = self._orig_instrument_db_path
        BrokerService._instance = None

    def test_enums(self):
        """Verifies that TradingMode and BrokerType enums are correctly configured."""
        self.assertEqual(TradingMode.PAPER_TRADING.value, "PAPER_TRADING")
        self.assertEqual(TradingMode.LIVE_ZERODHA.value, "LIVE_ZERODHA")
        self.assertEqual(BrokerType.MOCK.value, "MOCK")
        self.assertEqual(BrokerType.ZERODHA.value, "ZERODHA")

    def test_broker_health_model(self):
        """Verifies the frozen dataclass fields for BrokerHealth, including extended fields."""
        health = BrokerHealth(
            broker_name="Mock Broker (Paper)",
            connection_status="CONNECTED",
            trading_mode="PAPER_TRADING",
            latency=0.5,
            authentication_state="AUTHENTICATED",
            last_heartbeat="2026-07-11 12:00:00",
            instrument_cache_status="VALID",
            market_status="OPEN",
            health_score=100.0,
            last_error=None,

            # Extended fields
            authentication_status="AUTHENTICATED",
            session_age_hours=1.5,
            token_expiry="2026-07-12 06:00:00",
            last_login_time="2026-07-11 11:00:00",
            session_valid=True,
            broker_version="KiteConnect v5.2",
            api_status="ONLINE"
        )
        self.assertEqual(health.broker_name, "Mock Broker (Paper)")
        self.assertEqual(health.connection_status, "CONNECTED")
        self.assertEqual(health.health_score, 100.0)
        self.assertEqual(health.authentication_status, "AUTHENTICATED")
        self.assertEqual(health.session_age_hours, 1.5)
        self.assertTrue(health.session_valid)
        self.assertEqual(health.broker_version, "KiteConnect v5.2")
        self.assertIsNone(health.last_error)

        # Assert frozen property
        with self.assertRaises(Exception):
            health.latency = 1.0

    def test_instrument_cache_manager(self):
        """Verifies stateless cache manager placeholders."""
        InstrumentCacheManager.invalidate_cache("MOCK")
        self.assertIsNone(InstrumentCacheManager.load_cache("MOCK"))
        self.assertTrue(InstrumentCacheManager.save_cache("MOCK", {}))
        self.assertTrue(InstrumentCacheManager.cache_exists("MOCK"))
        self.assertEqual(InstrumentCacheManager.cache_age("MOCK"), 0.0)
        self.assertTrue(InstrumentCacheManager.cache_validation("MOCK"))
        self.assertTrue(InstrumentCacheManager.invalidate_cache("MOCK"))

    def test_kite_broker_gateway_auth_flow(self):
        """Verifies KiteBrokerGateway authentication and session loading behaviour."""
        gateway = KiteBrokerGateway()
        self.assertFalse(gateway.is_connected())

        # Try connect with no active session or credentials
        connected = gateway.connect()
        self.assertFalse(connected)

        # Read-only actions should raise SessionMissingError when not connected
        from src.broker.utils.errors import SessionMissingError
        with self.assertRaises(SessionMissingError):
            gateway.get_funds()

        # Write actions remain strictly prohibited by the product boundary.
        with self.assertRaises(PermissionError):
            gateway.place_order(symbol="NIFTY")

        # Health report should represent disconnected state
        health = gateway.health()
        self.assertEqual(health.broker_name, "Zerodha KiteConnect")
        self.assertIn(health.connection_status, ("DISCONNECTED", "ERROR"))
        self.assertEqual(health.trading_mode, "LIVE_ZERODHA")
        self.assertEqual(health.health_score, 0.0)
        self.assertFalse(health.session_valid)

    @patch("src.broker.services.authentication.KiteConnect")
    def test_authentication_manager(self, mock_kite_class):
        """Tests AuthenticationManager generation of login URL and session extraction."""
        # Config verification
        self.assertEqual(Config.KITE_API_KEY, "test_api_key")

        mock_instance = mock_kite_class.return_value
        mock_instance.login_url.return_value = "https://kite.zerodha.com/connect/login?api_key=test_api_key&v=3"

        # Test generation of login URL
        url = AuthenticationManager.generate_login_url()
        self.assertIn("api_key=test_api_key", url)
        self.assertIn("https://kite.zerodha.com/connect/login", url)

        # Test exchanging request token
        mock_instance = mock_kite_class.return_value
        mock_instance.generate_session.return_value = {
            "access_token": "valid_mock_access_token",
            "user_id": "test_user"
        }

        session = AuthenticationManager.generate_access_token("mock_request_token")
        self.assertEqual(session["access_token"], "valid_mock_access_token")
        mock_instance.generate_session.assert_called_with("mock_request_token", api_secret="test_api_secret")

    def test_session_manager_persistence(self):
        """Tests that SessionManager correctly saves, loads, validates, and deletes sessions."""
        with self.assertRaises(SessionMissingError):
            SessionManager.validate_session()


        # Save a valid session
        success = SessionManager.save_session("my_test_access_token")
        self.assertTrue(success)

        # Ensure session.json exists
        self.assertTrue(os.path.exists(Config.SESSION_CACHE_PATH))

        # Load session
        session = SessionManager.load_session()
        self.assertIsNotNone(session)
        self.assertEqual(session["access_token"], "my_test_access_token")
        self.assertFalse(session["expired"])

        # Validate session (should return True without raising exceptions)
        valid = SessionManager.validate_session()
        self.assertTrue(valid)

        deleted = SessionManager.delete_session()
        self.assertTrue(deleted)
        self.assertIsNone(SessionManager.load_session())
        self.assertTrue(SessionManager.is_explicitly_logged_out())

    def test_error_handling_immutability(self):
        """Verifies that custom BrokerErrors are structured, frozen/immutable and have codes."""
        err = InvalidAPIKeyError("Check API key failed")
        self.assertEqual(err.error_code, "INVALID_API_KEY")
        self.assertEqual(err.message, "Check API key failed")

        with self.assertRaises(AttributeError):
            err._message = "Mutation attempt"

        err2 = ExpiredAccessTokenError("Expired token")
        self.assertEqual(err2.error_code, "EXPIRED_ACCESS_TOKEN")

    def test_mock_broker_gateway(self):
        """Verifies MockBrokerGateway adapter wrapping ConnectionManager."""
        gateway = MockBrokerGateway()
        # Explicit test-only client: production resolution remains the official package.
        import src.broker.compat.connection as connection_module
        original = connection_module.KiteConnect
        connection_module.KiteConnect = FakeKiteConnect

        # Test connection cycle
        try:
            connected = gateway.connect(api_key="TEST_API_KEY")
        finally:
            connection_module.KiteConnect = original
        self.assertTrue(connected)
        self.assertTrue(gateway.is_connected())

        # Profile fetch
        profile = gateway.get_profile()
        self.assertEqual(profile["client_id"], "MOCK_CLIENT")

        # Health metrics
        health = gateway.health()
        self.assertEqual(health.connection_status, "CONNECTED")
        self.assertEqual(health.trading_mode, "PAPER_TRADING")
        self.assertEqual(health.health_score, 100.0)

    def test_broker_service_singleton_and_proxy(self):
        """Verifies BrokerService proxy behaviour, switching, and delegation of auth commands."""
        service = BrokerService.get_instance()
        self.assertIsInstance(service, BrokerService)

        # Confirm singleton behavior
        service2 = BrokerService.get_instance()
        self.assertEqual(id(service), id(service2))

        # Product runtime is permanently read-only Zerodha.
        self.assertEqual(service.trading_mode, TradingMode.LIVE_ZERODHA)
        self.assertIsInstance(service.get_gateway(), KiteBrokerGateway)

        # Dynamic mode switching
        service.set_mode(TradingMode.LIVE_ZERODHA)
        self.assertEqual(service.trading_mode, TradingMode.LIVE_ZERODHA)
        self.assertIsInstance(service.get_gateway(), KiteBrokerGateway)

        # Verify delegated login URL call
        self.assertIn("https://", service.get_login_url())

        with self.assertRaises(ValueError):
            service.set_mode(TradingMode.PAPER_TRADING)
        with self.assertRaises(PermissionError):
            service.place_order(tradingsymbol="NIFTY", quantity=1)


if __name__ == "__main__":
    unittest.main()
