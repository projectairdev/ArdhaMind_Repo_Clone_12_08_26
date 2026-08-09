from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.broker.adapters.kite_broker import KiteBrokerGateway
from src.broker.services.broker_service import BrokerService
from src.configuration_engine.runtime import Config
from src.models.canonical_workstation_state import sanitize_read_only
from src.server_bridge import handle_daemon_command
from src.workspace.mode_guard import InvalidModeTransitionError
from src.workspace.workspace_manager import WorkspaceManager
from src.workspace.workspace_mode import WorkspaceMode


ROOT = Path(__file__).resolve().parents[1]
READ_ONLY_ACTIONS = (
    "place_order",
    "modify_order",
    "cancel_order",
    "exit_position",
    "paper_trade",
    "simulate_execution",
)


@pytest.mark.parametrize("action", READ_ONLY_ACTIONS)
def test_daemon_rejects_every_execution_action_before_service_access(action: str) -> None:
    response = handle_daemon_command(action, {}, None, None)
    assert response["code"] == 410
    assert response["status"] == "GONE"
    assert response["success"] is False


@pytest.mark.parametrize("action", READ_ONLY_ACTIONS)
def test_cli_rejects_every_execution_action(action: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "src.server_bridge", "--action", action],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    response = json.loads(completed.stdout.strip())
    assert response["code"] == 410
    assert response["status"] == "GONE"


def test_http_mutation_handler_returns_410_at_runtime() -> None:
    script = (
        'import { readOnlyRejection } from "./src/read_only_policy.mjs"; '
        'console.log(JSON.stringify({status: 410, body: readOnlyRejection("Order placement")}));'
    )
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    response = json.loads(completed.stdout.strip())
    assert response["status"] == 410
    assert response["body"]["code"] == "READ_ONLY_PRODUCT"


@pytest.mark.parametrize("method", ("place_order", "modify_order", "cancel_order"))
def test_authoritative_broker_service_rejects_mutations(method: str) -> None:
    service = BrokerService.get_instance()
    with pytest.raises(PermissionError, match="read only"):
        getattr(service, method)()


@pytest.mark.parametrize("method", ("place_order", "modify_order", "cancel_order"))
def test_kite_gateway_rejects_mutations_without_calling_client(method: str) -> None:
    gateway = KiteBrokerGateway()
    with pytest.raises(PermissionError, match="read only"):
        getattr(gateway, method)()


def test_canonical_state_strips_actionable_execution_fields() -> None:
    sanitized = sanitize_read_only({
        "decision_support": {"summary": "advisory only", "place_order": {"quantity": 50}},
        "execution_mode": "LIVE_BROKER",
        "paper_portfolio": {"pnl": 123.0},
    })
    assert sanitized == {"decision_support": {"summary": "advisory only"}}


def test_supported_configuration_cannot_activate_trading_or_paper_mode() -> None:
    assert Config.ALLOW_LIVE_TRADING is False
    assert Config.WORKSPACE_MODE == "READ_ONLY"
    manager = WorkspaceManager.get_instance()
    manager._current_mode = WorkspaceMode.READ_ONLY
    with pytest.raises(InvalidModeTransitionError, match="fixed read-only product mode"):
        manager.set_mode(WorkspaceMode.LIVE_TRADING, operator_confirmed=True)
    with pytest.raises(InvalidModeTransitionError, match="fixed read-only product mode"):
        manager.set_mode(WorkspaceMode.LIVE_PRACTICE)


def test_canonical_frontend_routes_only_six_read_only_workspaces() -> None:
    layout = (ROOT / "src/frontend/layout/DashboardLayout.tsx").read_text(encoding="utf-8")
    for workspace in (
        "NiftyLiveWorkspace", "PreMarketPlannerWorkspace", "TodaysAnalysisWorkspace",
        "NewsUpdatesWorkspace", "LiveAssistantWorkspace", "SettingsWorkspace",
    ):
        assert workspace in layout
    for retired in ("ExecutionWorkspace", "TradingJournal", "BrokerIntegration", "OperationsManager"):
        assert retired not in layout
