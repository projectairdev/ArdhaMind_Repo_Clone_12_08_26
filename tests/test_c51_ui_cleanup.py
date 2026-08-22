from pathlib import Path


ROOT = Path("src")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_global_market_closed_banner_is_removed_without_session_logic_changes():
    layout = read("frontend/layout/DashboardLayout.tsx")
    assert "Showing only the final validated snapshot" not in layout
    assert 'workspaceContext.marketState === "CLOSED"' not in layout


def test_top_bar_has_one_session_status_and_only_operational_controls():
    text = read("frontend/components/WorkstationTopBar.tsx")
    for control in ("Market:", "Broker:", "Live Assistant", "Settings"):
        assert control in text
    assert "Welcome back," not in text and "Arjun" not in text
    assert "Notifications" not in text and "Refresh canonical workstation" not in text


def test_settings_remains_in_sidebar_and_redundant_read_only_block_is_removed():
    text = read("frontend/layout/DashboardLayout.tsx")
    assert "settingsOpen ?" in text and "<SettingsWorkspace />" in text
    assert "Settings Modal" not in text
    assert "Decision intelligence only. Execution and order management are unavailable." not in text


def test_provider_health_is_bounded_and_responsive():
    text = read("frontend/components/settings/SettingsWorkspace.tsx")
    assert "CONNECTIONS" in text


def test_four_workspaces_use_distinct_views_over_one_canonical_source():
    text = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "canonicalState?.unified_intelligence" in text
    for view in ("compact-command-center", "next-session-setup", "full-session-synthesis", "explanation-console"):
        assert f'data-intelligence-view="{view}"' in text
    assert "fetch(" not in text and "new WebSocket" not in text


def test_nifty_live_is_compact_and_premarket_is_opening_focused():
    text = read("frontend/components/UnifiedIntelligencePanel.tsx")
    for label in ("Tomorrow's Market Setup", "Expected Opening", "Global Cues", "FII / DII Positioning", "What Supports the Setup"):
        assert label in text


def test_analysis_and_assistant_are_question_specific():
    text = read("frontend/components/UnifiedIntelligencePanel.tsx")
    for label in ("What Supports This View", "What Goes Against It", "What Could Change This View", "Current Market State", "Why?", "What is the Risk?", "What Changed?", "What Data is Missing?"):
        assert label in text
    assert 'change.status || "UNAVAILABLE"' in text


def test_visible_context_label_changes_without_internal_engine_rename():
    text = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "SESSION INTELLIGENCE" in text
    assert "Canonical NIFTY Decision Context" not in text
    assert "data-intelligence-engine={intelligence.engine}" in text


def test_grid_is_quieter_and_c5_motion_survives():
    css = read("index.css")
    assert ".air-grid { background: var(--air-bg); }" in css
    assert "fonts.googleapis.com" not in css
    assert "air-flash-up" in css and "prefers-reduced-motion: reduce" in css


def test_notifications_are_derived_and_not_accumulated_on_refresh():
    text = read("frontend/components/WorkstationTopBar.tsx")
    assert "Notifications" not in text and "setAlerts" not in text
    assert "Refresh canonical workstation" not in text and "fetch(" not in text


def test_cleanup_adds_no_frontend_reasoning_or_synthetic_values():
    text = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "score =" not in text.lower() and "threshold" not in text.lower()
    assert "synthetic" not in text.lower()
