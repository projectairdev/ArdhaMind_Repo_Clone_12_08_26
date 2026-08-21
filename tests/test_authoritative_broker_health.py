import pytest
from unittest.mock import MagicMock, patch
from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator, AuthoritativeBrokerHealth


class DummyGateway:
    def __init__(self, access_token="TEST_TOKEN", session_valid=True):
        self.access_token = access_token
        self._session_valid = session_valid

    def validate_session(self):
        return self._session_valid


class DummyBrokerService:
    def __init__(self, gateway=None):
        self._gateway = gateway

    def get_gateway(self):
        return self._gateway


def test_scenario_1_transport_connected_auth_invalid():
    """Scenario 1: Transport connected but auth token is missing -> CONNECTED_AUTH_REQUIRED."""
    BrokerHealthEvaluator.set_reconciliation_status(complete=False)
    with patch("src.broker.services.session_manager.SessionManager.is_explicitly_logged_out", return_value=False):
        bs = DummyBrokerService(gateway=DummyGateway(access_token=None))
        health = BrokerHealthEvaluator.evaluate(bs)
        assert health.status == "CONNECTED_AUTH_REQUIRED"
        assert health.authenticated is False
        assert health.session_valid is False
        assert health.execution_verified is False
        assert health.blocker_code == "AUTH_REQUIRED"


def test_scenario_2_auth_valid_reconciliation_pending():
    """Scenario 2: Auth valid but reconciliation is pending -> BROKER_STATE_UNVERIFIED."""
    BrokerHealthEvaluator.set_reconciliation_status(complete=False, in_progress=True)
    with patch("src.broker.services.session_manager.SessionManager.is_explicitly_logged_out", return_value=False):
        bs = DummyBrokerService(gateway=DummyGateway(access_token="VALID_TOKEN", session_valid=True))
        health = BrokerHealthEvaluator.evaluate(bs)
        assert health.status == "BROKER_STATE_UNVERIFIED"
        assert health.authenticated is True
        assert health.session_valid is True
        assert health.execution_verified is False
        assert health.reconciliation_complete is False
        assert health.blocker_code == "RECONCILIATION_PENDING"


def test_scenario_3_auth_valid_reconciliation_successful():
    """Scenario 3: Auth valid and reconciliation complete -> CONNECTED_VERIFIED."""
    BrokerHealthEvaluator.set_reconciliation_status(complete=True, in_progress=False, unresolved_count=0)
    with patch("src.broker.services.session_manager.SessionManager.is_explicitly_logged_out", return_value=False):
        bs = DummyBrokerService(gateway=DummyGateway(access_token="VALID_TOKEN", session_valid=True))
        health = BrokerHealthEvaluator.evaluate(bs)
        assert health.status == "CONNECTED_VERIFIED"
        assert health.authenticated is True
        assert health.session_valid is True
        assert health.execution_verified is True
        assert health.reconciliation_complete is True
        assert health.blocker_code is None


def test_scenario_4_token_expiry():
    """Scenario 4: Token exists but validate_session returns False -> CONNECTED_AUTH_REQUIRED."""
    BrokerHealthEvaluator.set_reconciliation_status(complete=True)
    with patch("src.broker.services.session_manager.SessionManager.is_explicitly_logged_out", return_value=False):
        bs = DummyBrokerService(gateway=DummyGateway(access_token="EXPIRED_TOKEN", session_valid=False))
        health = BrokerHealthEvaluator.evaluate(bs)
        assert health.status == "CONNECTED_AUTH_REQUIRED"
        assert health.authenticated is False
        assert health.session_valid is False
        assert health.execution_verified is False
        assert health.blocker_code == "TOKEN_EXPIRED"


def test_scenario_5_explicitly_logged_out():
    """Scenario 5: Explicit logout -> DISCONNECTED."""
    with patch("src.broker.services.session_manager.SessionManager.is_explicitly_logged_out", return_value=True):
        bs = DummyBrokerService(gateway=DummyGateway(access_token="SOME_TOKEN", session_valid=True))
        health = BrokerHealthEvaluator.evaluate(bs)
        assert health.status == "DISCONNECTED"
        assert health.authenticated is False
        assert health.execution_verified is False
        assert health.blocker_code == "EXPLICITLY_LOGGED_OUT"


def test_scenario_6_unresolved_operations_lockout():
    """Scenario 6: Unresolved operations exist -> BROKER_STATE_UNVERIFIED."""
    BrokerHealthEvaluator.set_reconciliation_status(complete=True, in_progress=False, unresolved_count=2)
    with patch("src.broker.services.session_manager.SessionManager.is_explicitly_logged_out", return_value=False):
        bs = DummyBrokerService(gateway=DummyGateway(access_token="VALID_TOKEN", session_valid=True))
        health = BrokerHealthEvaluator.evaluate(bs)
        assert health.status == "BROKER_STATE_UNVERIFIED"
        assert health.execution_verified is False
        assert health.blocker_code == "UNRESOLVED_OPERATION_LOCKOUT"


def test_scenario_7_broker_service_none():
    """Scenario 7: Broker service unavailable -> DISCONNECTED."""
    health = BrokerHealthEvaluator.evaluate(None)
    assert health.status == "DISCONNECTED"
    assert health.execution_verified is False
    assert health.blocker_code == "BROKER_SERVICE_UNAVAILABLE"


def test_scenario_8_plain_connected_cannot_become_execution_verified():
    """Scenario 8: Plain legacy CONNECTED string in canonical state mapping does not yield execution_verified=True."""
    from src.application.workstation_state_service import WorkstationStateService
    payload = {"workspaceContext": {"currentMode": "READ_ONLY"}}
    c_state = WorkstationStateService.build_canonical_state(payload, broker_state="CONNECTED", market_state="CLOSED")
    b_status = c_state.broker_status
    assert b_status["execution_verified"] is False
    assert b_status["normalized_status"] == "BROKER_STATE_UNVERIFIED"


def test_scenario_9_auth_required_propagates_without_becoming_disconnected():
    """Scenario 9: CONNECTED_AUTH_REQUIRED propagates as CONNECTED_AUTH_REQUIRED in canonical state."""
    from src.application.workstation_state_service import WorkstationStateService
    payload = {"workspaceContext": {"currentMode": "READ_ONLY"}}
    c_state = WorkstationStateService.build_canonical_state(payload, broker_state="CONNECTED_AUTH_REQUIRED", market_state="CLOSED")
    b_status = c_state.broker_status
    assert b_status["normalized_status"] == "CONNECTED_AUTH_REQUIRED"
    assert b_status["authenticated"] is False
    assert b_status["execution_verified"] is False


def test_scenario_10_broker_state_unverified_survives_context_mapping():
    """Scenario 10: BROKER_STATE_UNVERIFIED survives mapping in canonical state."""
    from src.application.workstation_state_service import WorkstationStateService
    payload = {"workspaceContext": {"currentMode": "READ_ONLY"}}
    c_state = WorkstationStateService.build_canonical_state(payload, broker_state="BROKER_STATE_UNVERIFIED", market_state="CLOSED")
    b_status = c_state.broker_status
    assert b_status["normalized_status"] == "BROKER_STATE_UNVERIFIED"
    assert b_status["execution_verified"] is False
    assert b_status["authenticated"] is True
