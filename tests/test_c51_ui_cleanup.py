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
    assert text.count("data-market-session-status") == 1
    assert "Feed {feed}" in text and "Market Feed {feed}" not in text
    assert 'aria-label="Settings"' not in text and "onOpenSettings" not in text
    for control in ('aria-label="Refresh canonical workstation"', "Notifications", "Kite"):
        assert control in text


def test_settings_remains_in_sidebar_and_redundant_read_only_block_is_removed():
    text = read("frontend/layout/DashboardLayout.tsx")
    assert '{ id: "settings", label: "Settings"' in text
    assert "Decision intelligence only. Execution and order management are unavailable." not in text


def test_provider_health_is_bounded_and_responsive():
    text = read("frontend/components/SettingsDashboard.tsx")
    assert "data-provider-health-scroll" in text
    assert "max-h-[28rem]" in text and "sm:max-h-[32rem]" in text
    assert "overflow-y-auto" in text and "overflow-x-hidden" in text


def test_four_workspaces_use_distinct_views_over_one_canonical_source():
    text = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "canonicalState?.unified_intelligence" in text
    for view in ("compact-command-center", "next-session-setup", "full-session-synthesis", "explanation-console"):
        assert f'data-intelligence-view="{view}"' in text
    assert "fetch(" not in text and "new WebSocket" not in text


def test_nifty_live_is_compact_and_premarket_is_opening_focused():
    text = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "Market intelligence" in text
    for label in ("Pre-market readiness", "Opening Context", "Global Context", "Institutional Context", "Confirmation"):
        assert label in text


def test_analysis_and_assistant_are_question_specific():
    text = read("frontend/components/UnifiedIntelligencePanel.tsx")
    for label in ("What confirms the view", "What contradicts it", "Session risk and invalidation", "What is the market state?", "Why?", "What is the current risk?", "What changed?", "What data is missing?"):
        assert label in text
    assert 'change.status || "UNAVAILABLE"' in text


def test_visible_context_label_changes_without_internal_engine_rename():
    text = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert ">NIFTY Decision Context<" in text
    assert "Canonical NIFTY Decision Context" not in text
    assert "data-intelligence-engine={intelligence.engine}" in text


def test_grid_is_quieter_and_c5_motion_survives():
    css = read("index.css")
    assert "var(--air-line) 55%" in css
    assert "air-flash-up" in css and "prefers-reduced-motion: reduce" in css


def test_notifications_are_derived_and_not_accumulated_on_refresh():
    text = read("frontend/components/WorkstationTopBar.tsx")
    assert 'id: "provider-summary"' in text and 'key={alert.id}' in text
    assert "setAlerts" not in text and "Math.random" not in text
    assert "await syncBroker(true)" in text and "fetch(" not in text


def test_cleanup_adds_no_frontend_reasoning_or_synthetic_values():
    text = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "score =" not in text.lower() and "threshold" not in text.lower()
    assert "synthetic" not in text.lower()
