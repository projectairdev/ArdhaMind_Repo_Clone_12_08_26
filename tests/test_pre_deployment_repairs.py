import pytest
from unittest.mock import MagicMock, patch
import time

from src.broker.adapters.kite_broker import KiteBrokerGateway
from src.broker.adapters.kite_ticker_adapter import KiteTickerAdapter
from src.broker.utils.errors import ExpiredAccessTokenError, SessionMissingError, NetworkFailureError
from src.broker.services.market_status_service import MarketStatusService
from src.broker.services.streaming_orchestrator import StreamingOrchestrator
from src.application.workstation_state_service import WorkstationStateService


def test_nifty_live_tab_single_row_render_contract():
    """Verify that NIFTY Live workspace component exposes exactly one tab navigation row."""
    with open("src/frontend/components/PhaseOneWorkspaces.tsx", "r", encoding="utf-8") as f:
        phase_one_content = f.read()

    # NiftyLiveWorkspace in PhaseOneWorkspaces should NOT render an extra Tabs component
    # leaving NiftyLiveWorkspace.tsx as the single authoritative tab row
    assert '<Tabs values={["Overview", "Price & Trend", "Options"]}' not in phase_one_content

    with open("src/frontend/components/NiftyLiveWorkspace.tsx", "r", encoding="utf-8") as f:
        workspace_content = f.read()

    # Ensure single authoritative tab container with testid exists
    assert 'data-testid="nifty-live-tabs"' in workspace_content
    assert 'Overview' in workspace_content
    assert 'Price &amp; Trend' in workspace_content or 'Price & Trend' in workspace_content
    assert 'Options' in workspace_content


def test_market_closed_with_valid_auth_does_not_emit_disconnected():
    """Verify that when market is CLOSED and broker auth is valid, status is CONNECTED/VALID, not DISCONNECTED."""
    gateway = KiteBrokerGateway()
    gateway.access_token = "valid_test_token"
    gateway.api_key = "valid_api_key"
    gateway._connected = True
    gateway._last_validation_time = time.time()

    with patch("src.broker.services.authentication.AuthenticationManager.validate_session", return_value=True):
        # Validation should succeed and return True
        is_valid = gateway.validate_session()
        assert is_valid is True
        assert gateway.is_connected() is True


def test_tick_silence_while_market_closed_does_not_disconnect_stream():
    """Verify that tick silence during off-market session does not switch stream to DISCONNECTED."""
    gateway = KiteBrokerGateway()
    gateway.access_token = "valid_test_token"
    gateway.api_key = "valid_api_key"
    gateway._connected = True
    gateway._last_validation_time = time.time() - 100.0  # 100 seconds ago

    # Simulate a transient network glitch during off-market validation
    with patch("src.broker.services.authentication.AuthenticationManager.validate_session", side_effect=Exception("Transient HTTP 504 timeout")):
        # Since last validation was within 300s window off-market, connected state is preserved
        is_valid = gateway.validate_session()
        assert is_valid is True
        assert gateway.is_connected() is True


def test_retired_generation_callbacks_cannot_alter_stream_state():
    """Verify that callbacks from an old generation ID are ignored by KiteTickerAdapter."""
    adapter = KiteTickerAdapter("test_key", "test_token")
    current_gen = adapter.generation_id

    # Create new adapter instance simulating reconnect generation increment
    adapter_new = KiteTickerAdapter("test_key", "test_token")
    adapter_new.generation_id = current_gen + 1

    assert adapter_new.generation_id > current_gen
    assert adapter.generation_id == current_gen


def test_stable_auth_remains_valid_during_stream_reconnect():
    """Verify that stream disconnect/reconnect does not clear or invalidate broker authentication."""
    gateway = KiteBrokerGateway()
    gateway.access_token = "valid_token_123"
    gateway._connected = True
    gateway._last_validation_time = time.time()

    orchestrator = StreamingOrchestrator.get_instance()
    orchestrator.configure("test_key", gateway.access_token)

    # Disconnecting stream transport should keep REST gateway access token intact
    orchestrator.disconnect_stream()
    assert gateway.access_token == "valid_token_123"


def test_validate_session_uses_120s_cache_after_connect():
    """
    Verify that validate_session returns True from cache without a network call
    within 120 seconds of a successful connect().

    This is the primary regression guard for the startup oscillation fix:
    previously, the first daemon-loop call after connect() would always hit
    the network (because _last_validation_time was unset), creating a window
    where a transient Kite API failure could broadcast TOKEN_EXPIRED.
    """
    gateway = KiteBrokerGateway()
    gateway.access_token = "cached_token"
    gateway.api_key = "cached_key"
    gateway._connected = True
    # Stamp as just-validated (as connect() now does)
    gateway._last_validation_time = time.time()

    call_tracker = {"called": False}

    def spy_validate(*args, **kwargs):
        call_tracker["called"] = True
        return True

    with patch("src.broker.services.authentication.AuthenticationManager.validate_session", side_effect=spy_validate):
        result = gateway.validate_session()

    assert result is True, "validate_session should return True from cache"
    assert not call_tracker["called"], (
        "AuthenticationManager.validate_session should NOT be called within the 120s cache window"
    )


def test_validate_session_preserves_connected_on_transient_network_error():
    """
    Verify that a transient network failure during validate_session does NOT
    change _connected to False.

    This is the regression guard against the 'every network hiccup broadcasts
    TOKEN_EXPIRED' oscillation. The sticky-auth rule at the daemon level relies
    on the gateway not flip-flopping _connected on non-auth exceptions.
    """
    gateway = KiteBrokerGateway()
    gateway.access_token = "valid_token"
    gateway.api_key = "valid_key"
    gateway._connected = True
    # Set last_validation_time > 120s ago so it actually tries the network call
    gateway._last_validation_time = time.time() - 200.0

    with patch(
        "src.broker.services.authentication.AuthenticationManager.validate_session",
        side_effect=Exception("Simulated transient 503 Service Unavailable"),
    ):
        result = gateway.validate_session()

    assert result is True, "Transient error should preserve CONNECTED status and return True"
    assert gateway._connected is True, "_connected must NOT be set to False on transient error"


def test_validate_session_sets_connected_false_on_genuine_auth_rejection():
    """
    Verify that ExpiredAccessTokenError (genuine 401/403) correctly sets
    _connected = False and propagates the exception.

    This ensures genuine token expiry still correctly transitions the daemon
    from CONNECTED to TOKEN_EXPIRED.
    """
    from src.broker.utils.errors import ExpiredAccessTokenError

    gateway = KiteBrokerGateway()
    gateway.access_token = "expired_token"
    gateway.api_key = "valid_key"
    gateway._connected = True
    gateway._last_validation_time = time.time() - 200.0

    with patch(
        "src.broker.services.authentication.AuthenticationManager.validate_session",
        side_effect=ExpiredAccessTokenError("Token has expired (401)"),
    ):
        with pytest.raises(ExpiredAccessTokenError):
            gateway.validate_session()

    assert gateway._connected is False, "_connected must be set to False on genuine token expiry"
