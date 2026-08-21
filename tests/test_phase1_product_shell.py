from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAYOUT = (ROOT / "src/frontend/layout/DashboardLayout.tsx").read_text(encoding="utf-8")
WORKSPACES = (ROOT / "src/frontend/components/PhaseOneWorkspaces.tsx").read_text(encoding="utf-8")
TOP_BAR = (ROOT / "src/frontend/components/WorkstationTopBar.tsx").read_text(encoding="utf-8")
READINESS = (ROOT / "src/frontend/services/workspaceReadiness.ts").read_text(encoding="utf-8")
SERVER = (ROOT / "server.ts").read_text(encoding="utf-8")
BRIDGE = (ROOT / "src/server_bridge.py").read_text(encoding="utf-8")


def test_exact_primary_navigation_order():
    labels = ["MARKET", "INTELLIGENCE", "PORTFOLIO", "JOURNAL"]
    positions = [LAYOUT.index(f'label: "{label}"') for label in labels]
    assert positions == sorted(positions)
    primary = LAYOUT.split("export const PRIMARY_MODULES", 1)[1].split("] as const", 1)[0]
    assert primary.count("label:") == 4


def test_removed_surfaces_are_not_in_active_import_graph():
    forbidden_imports = ["TradeCenter", "LivePortfolio", "ExecutionWorkspace", "PerformanceAnalytics", "TradingJournal", "mockData", "order_lifecycle"]
    active_source = LAYOUT + WORKSPACES + TOP_BAR
    for name in forbidden_imports:
        assert name not in active_source


def test_top_bar_has_only_product_status_categories():
    for required in ["Market:", "Broker:", "Live Assistant", "Settings"]:
        assert required in TOP_BAR
    assert "Welcome back," not in TOP_BAR and "Arjun" not in TOP_BAR
    assert "Refresh canonical workstation" not in TOP_BAR and "Notifications" not in TOP_BAR
    assert "disabled title=\"Live Assistant — Phase 3, coming soon\"" in TOP_BAR
    for forbidden in ["Portfolio Value", "Today’s P&L", "Practice Mode", "workspace rotation", "user email"]:
        assert forbidden not in TOP_BAR


def test_readiness_and_failure_states_are_explicit():
    for state in ["initializing", "unavailable", "stale", "blocked", "closed", "expired", "partial", "error"]:
        assert state in WORKSPACES
    assert "SettingsWorkspace" in LAYOUT
    assert "No fallback price is shown" in WORKSPACES
    assert 'workspace === "nifty-live" || workspace === "settings"' in READINESS
    assert "Waiting for validated market context" in READINESS


def test_execution_http_and_daemon_paths_reject_actions():
    assert 'app.post("/api/orders/place"' in SERVER
    assert 'app.post("/api/positions/exit"' in SERVER
    assert SERVER.count("rejectReadOnlyMutation(") >= 5
    for action in ["place_order", "modify_order", "cancel_order", "exit_position"]:
        assert f'args.action == "{action}"' not in BRIDGE


def test_no_fabricated_option_spot_fallback():
    source = (ROOT / "src/pipeline/option_intelligence_pipeline.py").read_text(encoding="utf-8")
    assert "spot_price = 24000.0" not in source
    assert "option intelligence is blocked" in source
