"""Regression coverage for the D.0.2 runtime hydration lifecycle."""

from pathlib import Path

from src.application.workstation_state_service import WorkstationStateService


CONTEXT = Path("src/frontend/context/WorkstationStateContext.tsx")
SETTINGS = Path("src/frontend/components/SettingsDashboard.tsx")
ASSISTANT = Path("src/frontend/components/IntradayAssistant.tsx")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def closed_state(temporal: object = "default") -> dict:
    state = WorkstationStateService.build_from_legacy(
        {"marketContext": {}, "optionContext": {}, "newsSentiment": {}, "macroIntelligence": {}},
        broker_state="DISCONNECTED",
        market_state="MARKET_CLOSED",
    ).to_dict()
    if temporal != "default":
        state["live_assistant_temporal_state"] = temporal
    return state


def test_closed_session_publishes_core_state_without_global_skeleton():
    state = closed_state()
    assert state["application_status"]["status"] in {"ready", "degraded"}
    assert state["market_session"]["is_closed"] is True


def test_missing_temporal_state_remains_a_valid_core_state():
    state = closed_state(None)
    assert state["schema_version"] == "2.0.0"
    assert state["live_assistant_temporal_state"] is None


def test_empty_temporal_collections_are_valid():
    state = closed_state({"comparisons": [], "confirmation_families": [], "material_events": []})
    assert state["live_assistant_temporal_state"]["comparisons"] == []
    assert state["live_assistant_temporal_state"]["material_events"] == []


def test_settings_gate_depends_only_on_core_canonical_state():
    code = read(SETTINGS)
    gate = code.split("if (!canonicalState && !lastValidState)", 1)[1].split("const stateObj", 1)[0]
    assert "live_assistant_temporal_state" not in gate
    assert "market_session" not in gate


def test_settings_renders_disconnected_and_closed_states():
    code = read(SETTINGS)
    assert '|| "DISCONNECTED"' in code
    assert '|| "CLOSED"' in code


def test_socket_disconnect_preserves_validated_state():
    code = read(CONTEXT)
    onclose = code.split("ws.onclose = () =>", 1)[1].split("};", 1)[0]
    assert "setCanonicalState(null)" not in onclose
    assert "setLastValidState(null)" not in onclose


def test_initial_rest_bootstrap_precedes_socket_connection():
    code = read(CONTEXT)
    assert 'fetch("/api/workspace")' in code
    assert "syncBroker(true).finally(connect)" in code


def test_loading_resets_after_bootstrap_success_or_failure():
    code = read(CONTEXT)
    sync = code.split("const syncBroker", 1)[1].split("// Switch workspace", 1)[0]
    assert "finally" in sync
    assert "setLoading(false)" in sync


def test_workspace_mode_loading_has_finally_cleanup():
    code = read(CONTEXT)
    mode = code.split("const setWorkspaceMode", 1)[1].split("// Logout", 1)[0]
    assert "finally" in mode
    assert "setLoading(false)" in mode


def test_optional_temporal_arrays_default_without_throwing():
    code = read(ASSISTANT)
    assert "tempState?.confirmation_families || []" in code
    assert "if (!tempState || !tempState.comparisons)" in code
    assert "liveEventStream || []" in code
