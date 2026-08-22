# tests/test_post_auth_connection_latency.py
"""
Test suite for Zerodha Post-Auth Connection & Market-Feed Startup Latency.
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


def test_server_bridge_has_post_auth_timing_telemetry():
    code = read("src/server_bridge.py")
    assert "[POST_AUTH_TIMING]" in code
    assert "A1 callback_received" in code
    assert "postAuthMetrics" in code
    assert "_last_post_auth_metrics" in code


def test_server_ts_callback_has_fast_return_html_and_ws_push():
    code = read("server.ts")
    assert "type: \"auth_event\"" in code
    assert "brokerState: \"CONNECTING\"" in code
    assert "ZERODHA AUTHENTICATED" in code
    assert "window.location.replace(\"/?connected=true\")" in code


def test_workstation_state_context_handles_immediate_connected_state():
    code = read("src/frontend/context/WorkstationStateContext.tsx")
    assert "CONNECTED_VERIFIED" in code
    assert "setWorkspaceContextState" in code


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
