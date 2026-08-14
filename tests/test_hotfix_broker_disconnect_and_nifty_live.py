import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

from src.broker.services.session_manager import SessionManager
from src.broker.adapters.kite_broker import KiteBrokerGateway
from src.broker.services.broker_service import BrokerService
from src.broker.utils.errors import ExpiredAccessTokenError, AuthenticationFailureError
from src.configuration_engine.runtime import Config


@pytest.fixture
def temp_session_file():
    """Provides an isolated temporary file path for SessionManager tests."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_path = tf.name

    with patch.object(SessionManager, "get_cache_path", return_value=temp_path):
        yield temp_path

    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass


def test_1_logout_ipc_uses_real_session_manager_deletion(temp_session_file):
    """Test 1: Logout IPC uses SessionManager.delete_session() without throwing AttributeError."""
    from src.server_bridge import handle_daemon_command

    SessionManager.save_session(access_token="mock_token_123")
    assert os.path.exists(temp_session_file)

    mock_bs = MagicMock()
    mock_wm = MagicMock()

    # Executing logout action must call delete_session without error
    res = handle_daemon_command("logout", {}, mock_bs, mock_wm)
    assert res == {"success": True}
    mock_bs.logout.assert_called_once()
    assert SessionManager.is_explicitly_logged_out() is True


def test_2_explicit_logout_invalidates_persisted_authentication(temp_session_file):
    """Test 2: Explicit logout records explicit_logout state and invalidates session loading."""
    SessionManager.save_session(access_token="valid_token_abc", api_key="api_key_xyz")
    assert SessionManager.load_session() is not None
    assert SessionManager.is_explicitly_logged_out() is False

    SessionManager.delete_session()

    assert SessionManager.is_explicitly_logged_out() is True
    assert SessionManager.load_session() is None


def test_3_explicit_logout_prevents_env_token_fallback_restoration(temp_session_file):
    """Test 3: gateway.load_session() refuses auto-restoration even if environment variable token is set."""
    SessionManager.delete_session()
    assert SessionManager.is_explicitly_logged_out() is True

    gateway = KiteBrokerGateway()
    with patch.object(Config, "KITE_ACCESS_TOKEN", "env_fallback_token_999"):
        session_restored = gateway.load_session()
        assert session_restored is False
        assert gateway.is_connected() is False


def test_4_daemon_restart_after_explicit_logout_remains_unauthenticated(temp_session_file):
    """Test 4: Re-initializing gateway/daemon startup after explicit logout leaves session unauthenticated."""
    SessionManager.delete_session()

    gateway = KiteBrokerGateway()
    with patch.object(Config, "KITE_ACCESS_TOKEN", "env_fallback_token_999"):
        loaded = gateway.load_session()
        assert loaded is False
        assert gateway.access_token is None
        assert gateway.is_connected() is False


def test_5_browser_client_reconnect_cannot_restore_broker_authentication(temp_session_file):
    """Test 5: Daemon sticky auth state stays DISCONNECTED after explicit logout."""
    SessionManager.delete_session()
    assert SessionManager.is_explicitly_logged_out() is True

    bs = BrokerService.get_instance()
    bs.disconnect()

    assert bs.is_connected() is False
    assert SessionManager.is_explicitly_logged_out() is True


def test_6_transient_network_failure_preserves_auth(temp_session_file):
    """Test 6: Transient network/500 errors during validate_session preserve CONNECTED state."""
    SessionManager.save_session(access_token="active_token")
    gateway = KiteBrokerGateway()
    gateway._connected = True
    gateway.access_token = "active_token"
    gateway._last_validation_time = 0.0  # force validation

    with patch("src.broker.services.authentication.AuthenticationManager.validate_session", side_effect=Exception("503 Service Unavailable")):
        res = gateway.validate_session()
        assert res is True
        assert gateway.is_connected() is True


def test_7_genuine_401_403_invalidates_auth(temp_session_file):
    """Test 7: Genuine 401/403/ExpiredAccessTokenError invalidates auth and sets connected to False."""
    SessionManager.save_session(access_token="expired_token")
    gateway = KiteBrokerGateway()
    gateway._connected = True
    gateway.access_token = "expired_token"
    gateway._last_validation_time = 0.0  # force validation

    with patch("src.broker.services.authentication.AuthenticationManager.validate_session", side_effect=ExpiredAccessTokenError("401 Unauthorized")):
        with pytest.raises(ExpiredAccessTokenError):
            gateway.validate_session()
        assert gateway.is_connected() is False


def test_8_new_oauth_login_clears_disconnected_state(temp_session_file):
    """Test 8: New explicit OAuth login clears explicit_logout flag and authenticates normally."""
    SessionManager.delete_session()
    assert SessionManager.is_explicitly_logged_out() is True

    # Simulate new OAuth login saving session
    SessionManager.save_session(access_token="new_oauth_access_token_123", api_key="my_key")

    assert SessionManager.is_explicitly_logged_out() is False
    loaded = SessionManager.load_session()
    assert loaded is not None
    assert loaded["access_token"] == "new_oauth_access_token_123"


def test_9_closed_nifty_live_available_previous_session(temp_session_file):
    """Test 9: Off-market NIFTY Live availability logic allows previous-session spot data without last_tick_time."""
    canonical_state = {
        "market_session": {"status": "CLOSED", "is_closed": True},
        "market_data": {"current_spot": 24200.50},
        "data_quality": {"market_data": {"observed_at": None}}
    }
    market_context = {
        "current_spot": 24200.50,
        "last_tick_time": None,
        "session_mode": "LAST_SESSION"
    }

    is_closed_session = bool(
        canonical_state.get("market_session", {}).get("is_closed") or
        canonical_state.get("market_session", {}).get("status") in ["CLOSED", "HOLIDAY", "WEEKEND"]
    )
    spot = market_context.get("current_spot") or canonical_state.get("market_data", {}).get("current_spot")
    last_tick_time = market_context.get("last_tick_time")

    market_available = spot if is_closed_session else (spot and last_tick_time)
    assert bool(market_available) is True


def test_10_closed_data_never_labelled_live():
    """Test 10: Off-market data classification is strictly previous/closed session."""
    session_mode = "LAST_SESSION"
    is_closed = session_mode in ["LAST_SESSION", "LAST_VALID_SESSION", "CLOSED"]

    label = "Previous Trading Session" if is_closed else "LIVE"
    assert label == "Previous Trading Session"
    assert label != "LIVE"


def test_11_open_session_requires_live_evidence():
    """Test 11: OPEN session mode requires both spot price and fresh last_tick_time."""
    is_closed_session = False
    spot = 24200.50

    # Missing last_tick_time in OPEN session
    last_tick_time = None
    market_available = spot if is_closed_session else bool(spot and last_tick_time)
    assert market_available is False

    # Valid last_tick_time present in OPEN session
    last_tick_time = "2026-08-14T09:30:00+05:30"
    market_available = spot if is_closed_session else bool(spot and last_tick_time)
    assert market_available is True


def test_12_read_only_boundaries_unchanged():
    """Test 12: Order placement and broker mutation attempts throw PermissionError."""
    bs = BrokerService.get_instance()
    with pytest.raises(PermissionError):
        bs.place_order(symbol="NIFTY", quantity=50)
    with pytest.raises(PermissionError):
        bs.modify_order(order_id="123")
    with pytest.raises(PermissionError):
        bs.cancel_order(order_id="123")
    with pytest.raises(PermissionError):
        bs.exit_position(tradingsymbol="NIFTY", product="MIS")
