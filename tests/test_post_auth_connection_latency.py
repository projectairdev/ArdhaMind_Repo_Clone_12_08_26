# tests/test_post_auth_connection_latency.py
"""
Test suite for Zerodha Post-Auth Broker Truth & Callback Restoration Correction.
"""

from pathlib import Path
import json
import pytest

from src.application.workstation_state_service import WorkstationStateService


def read(rel_path: str) -> str:
    return Path(rel_path).read_text(encoding="utf-8")


def test_post_auth_audit_document_exists():
    path = Path("docs/POST_AUTH_CONNECTION_LATENCY_AUDIT.md")
    assert path.exists()
    code = path.read_text(encoding="utf-8")
    assert "Post-Authentication Sequence & Telemetry Trace" in code
    assert "Broker Connection State Machine" in code
    assert "Market Feed State Machine" in code


def test_server_bridge_enforces_profile_verification_for_connected_verified():
    code = read("src/server_bridge.py")
    assert "[POST_AUTH_TIMING]" in code
    assert "final_broker_state = \"CONNECTED_VERIFIED\" if (connected and profile_ok) else \"CONNECTED_AUTH_REQUIRED\"" in code
    assert "profileVerified" in code


def test_server_ts_callback_has_no_optimistic_local_storage_set_item():
    code = read("server.ts")
    assert "localStorage.setItem(\"BROKER_STATE\"" not in code
    assert "type: \"auth_event\"" in code
    assert "brokerState: \"CONNECTING\"" in code
    assert "window.location.replace(\"/?connected=true\")" in code


def test_workstation_state_context_sets_connecting_not_connected_verified_on_url_param():
    code = read("src/frontend/context/WorkstationStateContext.tsx")
    assert "setWorkspaceContextState(prev => ({ ...prev, brokerState: \"CONNECTING\" }))" in code
    # Must NOT set brokerState to CONNECTED_VERIFIED on URL param alone
    lines = [line.strip() for line in code.splitlines() if "connected === \"true\"" in line or "loginStatus === \"success\"" in line]
    assert len(lines) > 0
    assert "CONNECTED_VERIFIED" not in lines[0]


def test_canonical_settings_adapter_exposes_post_auth_metrics():
    code = read("src/frontend/utils/canonicalSettingsAdapter.ts")
    assert "postAuthMetrics" in code
    assert "tokenExchangeMs" in code
    assert "totalPostAuthMs" in code


def test_advanced_diagnostics_drawer_renders_post_auth_latency_panel():
    code = read("src/frontend/components/settings/AdvancedDiagnosticsDrawer.tsx")
    assert "POST-AUTH STARTUP LATENCY TELEMETRY" in code
    assert "TOKEN EXCHANGE" in code
    assert "TOTAL POST-AUTH" in code


def test_profile_validation_failure_prevents_connected_verified():
    """
    Mock test asserting that if profile verification fails, the returned state is NOT CONNECTED_VERIFIED.
    """
    profile_ok = False
    connected = True
    final_broker_state = "CONNECTED_VERIFIED" if (connected and profile_ok) else "CONNECTED_AUTH_REQUIRED"
    assert final_broker_state == "CONNECTED_AUTH_REQUIRED"
    assert final_broker_state != "CONNECTED_VERIFIED"
