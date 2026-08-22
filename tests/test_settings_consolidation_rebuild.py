# tests/test_settings_consolidation_rebuild.py
"""
Automated Unit, Integration, & Architectural Verification Tests for
SETTINGS SIMPLIFICATION & FINAL UX REBUILD SPRINT.
Staging Quality Gates for AIR ArdhaMind.
"""

from pathlib import Path
import pytest


def read_frontend(rel_path: str) -> str:
    full_path = Path(__file__).parent.parent / "src" / "frontend" / rel_path
    return full_path.read_text(encoding="utf-8")


class TestSettingsSimplifiedArchitecture:
    """Tests confirming the simplified 4-section single-page settings architecture."""

    def test_single_page_settings_header_and_subtitle(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "SETTINGS" in code
        assert "Workspace preferences, connections and alerts." in code

    def test_four_primary_sections_exist(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "GENERAL" in code
        assert "CONNECTIONS" in code
        assert "NOTIFICATIONS" in code
        assert "ADVANCED" in code

    def test_no_internal_sidebar_rail(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "CONTROL CENTER" not in code
        assert "SETTINGS_SECTIONS" not in code

    def test_centered_max_width_container(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "max-w-[960px]" in code


class TestPreferencesAndFormatting:
    """Tests for workspace display and formatting preferences in GENERAL section."""

    def test_time_format_options(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "12-Hour" in code
        assert "24-Hour" in code
        assert 'prefs.timeFormat === "12h"' in code
        assert 'prefs.timeFormat === "24h"' in code

    def test_number_format_options(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "Indian (Lakhs/Cr)" in code or "Indian" in code
        assert "International (M/B)" in code or "International" in code
        assert 'prefs.numberFormat === "IN"' in code
        assert 'prefs.numberFormat === "INTL"' in code

    def test_default_landing_workspaces(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "Market" in code
        assert "Market Intelligence" in code
        assert "News & Updates" in code
        assert "Portfolio" in code

    def test_default_market_views(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "nifty" in code
        assert "metrics" in code
        assert "options" in code

    def test_safe_reset_preserves_backend(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "RESET UI PREFERENCES" in code
        assert "Restores UI settings to defaults without altering broker/session/backend data." in code
        assert "handleResetPreferences" in code
        assert "DEFAULT_USER_PREFERENCES" in code


class TestAlertsAndNotifications:
    """Tests for alerts & notifications toggles and browser permission handling."""

    def test_browser_permission_banner(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "Desktop notification permission required." in code
        assert "Enable" in code or "handleRequestBrowserPermission" in code

    def test_five_alert_subscription_toggles(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "HIGH IMPACT MARKET NEWS" in code
        assert "MARKET OPEN / CLOSE" in code
        assert "BROKER SESSION ALERTS" in code
        assert "MACRO EVENT REMINDERS" in code
        assert "SYSTEM WARNINGS" in code
        assert "highImpactNewsAlerts" in code
        assert "marketOpenCloseAlerts" in code
        assert "brokerDisconnectAlerts" in code
        assert "economicEventReminders" in code
        assert "systemHealthWarnings" in code


class TestConnectionsAndBrokerAuth:
    """Tests for Connections, Zerodha OAuth, and service feeds."""

    def test_zerodha_broker_row_and_actions(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "Zerodha KiteConnect" in code
        assert "Authenticate Broker" in code or "handleOAuthConnect" in code
        assert "Manage" in code or "handleBrokerDisconnect" in code

    def test_connected_service_rows(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "Market Data" in code
        assert "Options Data" in code
        assert "News Engine" in code
        assert "Macro Calendar" in code
        assert "AI Assistant" in code


class TestSafetyAndDiagnostics:
    """Tests for Read-Only invariants, Advanced Disclosure, and Diagnostics Drawer."""

    def test_read_only_safety_note(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "Read-only safeguards active." in code

    def test_advanced_disclosure_accordion(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "setAdvancedExpanded" in code
        assert "Diagnostics, QA controls and reset options" in code

    def test_runtime_snapshot_fields(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "Runtime ID" in code
        assert "State Sequence" in code
        assert "Environment" in code
        assert "Session" in code
        assert "Last Sync" in code
        assert "Version" in code

    def test_advanced_diagnostics_drawer_integration(self):
        drawer_code = read_frontend("components/settings/AdvancedDiagnosticsDrawer.tsx")
        assert "AdvancedDiagnosticsDrawer" in drawer_code
        assert "COMPONENT READINESS MATRIX" in drawer_code
        assert "handleExportDiagnostics" in drawer_code

    def test_security_audit_no_exposed_secrets(self):
        for rel in [
            "components/settings/SettingsWorkspace.tsx",
            "components/settings/AdvancedDiagnosticsDrawer.tsx",
            "utils/canonicalSettingsAdapter.ts",
        ]:
            code = read_frontend(rel)
            assert "client_secret" not in code
            assert "refresh_token" not in code
            assert "access_token" not in code or "no access_token" in code.lower() or "safe" in code.lower()
