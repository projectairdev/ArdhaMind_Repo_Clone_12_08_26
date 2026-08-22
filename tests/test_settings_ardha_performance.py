# tests/test_settings_ardha_performance.py
import pytest
import os
import re

DASHBOARD_LAYOUT = "/opt/ardhamind/staging/src/frontend/layout/DashboardLayout.tsx"
NAVIGATION_CONTEXT = "/opt/ardhamind/staging/src/frontend/context/NavigationContext.tsx"
SETTINGS_DIAGNOSTICS = "/opt/ardhamind/staging/src/frontend/components/settings/SettingsDiagnostics.tsx"
ARDHA_PERF_PANEL = "/opt/ardhamind/staging/src/frontend/components/settings/ArdhaPerformancePanel.tsx"

def test_files_exist():
    assert os.path.exists(DASHBOARD_LAYOUT), "DashboardLayout.tsx must exist"
    assert os.path.exists(NAVIGATION_CONTEXT), "NavigationContext.tsx must exist"
    assert os.path.exists(SETTINGS_DIAGNOSTICS), "SettingsDiagnostics.tsx must exist"
    assert os.path.exists(ARDHA_PERF_PANEL), "ArdhaPerformancePanel.tsx must exist"

def test_primary_sidebar_contains_exact_four_modules():
    """Verify primary sidebar contains exactly the 4 official trading workspaces."""
    with open(DASHBOARD_LAYOUT, "r", encoding="utf8") as f:
        content = f.read()

    # PRIMARY_MODULES list check
    expected_modules = [
        '{ id: "market", label: "MARKET"',
        '{ id: "market_intelligence", label: "MARKET INTELLIGENCE"',
        '{ id: "news", label: "NEWS & UPDATES"',
        '{ id: "portfolio", label: "PORTFOLIO"',
    ]

    for mod in expected_modules:
        assert mod in content, f"Missing expected primary module in sidebar: {mod}"

    assert "trading_cheatsheet" not in content, "trading_cheatsheet must not be in PRIMARY_MODULES"

    # Verify ARDHA PERFORMANCE is removed from PRIMARY_MODULES
    primary_modules_block = re.search(r"export const PRIMARY_MODULES = \[(.*?)\] as const;", content, re.DOTALL)
    assert primary_modules_block is not None, "PRIMARY_MODULES array not found in DashboardLayout"
    primary_modules_str = primary_modules_block.group(1)

    assert "ardha_performance" not in primary_modules_str, "ardha_performance must not be in PRIMARY_MODULES"
    assert "ARDHA PERFORMANCE" not in primary_modules_str, "ARDHA PERFORMANCE label must not be in PRIMARY_MODULES"

def test_settings_diagnostics_renders_ardha_performance_panel():
    """Verify SettingsDiagnostics embeds ArdhaPerformancePanel in Section 5."""
    with open(SETTINGS_DIAGNOSTICS, "r", encoding="utf8") as f:
        content = f.read()

    assert "ArdhaPerformancePanel" in content, "SettingsDiagnostics must import ArdhaPerformancePanel"
    assert "<ArdhaPerformancePanel />" in content or "<ArdhaPerformancePanel" in content, "SettingsDiagnostics must render ArdhaPerformancePanel"
    assert "settings-diagnostics-ardha-performance" in content, "Must include section anchor id for deep linking"

def test_ardha_performance_panel_data_integrity():
    """Verify ArdhaPerformancePanel preserves evaluation contract and API endpoints."""
    with open(ARDHA_PERF_PANEL, "r", encoding="utf8") as f:
        content = f.read()

    assert "/api/performance/history" in content, "Must fetch from /api/performance/history"
    assert "/api/performance/records" in content, "Must fetch from /api/performance/records"
    assert "HITS" in content
    assert "NEAR" in content
    assert "MISSES" in content
    assert "PENDING" in content
    assert "PRE_MARKET" in content
    assert "LIVE_INTRADAY" in content

def test_navigation_migration_for_legacy_ardha_performance():
    """Verify normalizeModuleId and NavigationContext map legacy ardha_performance to settings diagnostics."""
    with open(NAVIGATION_CONTEXT, "r", encoding="utf8") as f:
        content = f.read()

    assert 'if (clean === "ardha_performance") return "settings";' in content, "normalizeModuleId must map ardha_performance to settings"
    assert 'rawClean === "ardha_performance"' in content, "setActiveModule and navigateTo must handle ardha_performance"
    assert 'setSettingsSubTabState("diagnostics")' in content, "Must activate diagnostics subtab on migration"

def test_ardha_performance_null_safe_formatting():
    """Regression test: verify ArdhaPerformancePanel handles null/undefined/NaN error_value without calling .toFixed on null."""
    with open(ARDHA_PERF_PANEL, "r", encoding="utf8") as f:
        content = f.read()

    # Must NOT have unsafe `r.error_value !== undefined ? r.error_value.toFixed(2)` which fails on null
    assert "r.error_value !== undefined ? `${r.error_value.toFixed(2)}" not in content, "Unsafe error_value check found"
    assert "r.error_value != null && !isNaN(Number(r.error_value))" in content, "Safe null check required for error_value"

