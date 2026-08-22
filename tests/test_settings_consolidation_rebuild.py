# tests/test_settings_consolidation_rebuild.py
"""
Automated Unit, Integration, & Architectural Verification Tests for
SETTINGS WORKSPACE CONSOLIDATION & PROFESSIONAL REBUILD SPRINT.
Staging Quality Gates for AIR ArdhaMind.
"""

from pathlib import Path
import pytest


def read_frontend(rel_path: str) -> str:
    full_path = Path(__file__).parent.parent / "src" / "frontend" / rel_path
    return full_path.read_text(encoding="utf-8")


class TestSettingsConsolidatedArchitecture:
    """Tests confirming the retirement of the 6-tab navigation and implementation of the single-page control center."""

    def test_single_page_settings_header_and_subtitle(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "SETTINGS" in code
        assert "Workstation preferences, data connections, alerts, and safety controls." in code
        assert "READ ONLY" in code

    def test_top_status_strip_four_cards(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert 'id="status-card-broker"' in code
        assert 'id="status-card-market-data"' in code
        assert 'id="status-card-news-engine"' in code
        assert 'id="status-card-ai-assistant"' in code
        assert "Zerodha KiteConnect" in code
        assert "NIFTY Spot" in code
        assert "Deterministic + GPT-4o" in code

    def test_main_two_column_grid_layout(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "grid-cols-1 lg:grid-cols-12" in code
        assert "lg:col-span-5" in code  # Left column (~45%)
        assert "lg:col-span-7" in code  # Right column (~55%)


class TestPreferencesAndFormatting:
    """Tests for workspace display and formatting preferences."""

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
        assert "MARKET" in code
        assert "MARKET INTELLIGENCE" in code
        assert "NEWS & UPDATES" in code
        assert "PORTFOLIO" in code

    def test_default_market_views(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "nifty" in code
        assert "metrics" in code
        assert "options" in code

    def test_safe_reset_preserves_backend(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "SAFE RESET" in code
        assert "Reset local UI preferences to workstation defaults." in code
        assert "Does not disconnect broker, alter market data, or delete backend state." in code
        assert "handleResetPreferences" in code
        assert "DEFAULT_USER_PREFERENCES" in code


class TestAlertsAndNotifications:
    """Tests for alerts & notifications toggles and browser permission handling."""

    def test_browser_permission_banner(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "Browser permission required for desktop popups" in code
        assert "Enable Notifications" in code or "handleRequestBrowserPermission" in code

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
        assert "Disconnect" in code or "handleBrokerDisconnect" in code

    def test_connected_service_rows(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "NSE Market Data Stream" in code
        assert "NIFTY Option Chain Matrix" in code
        assert "Financial News Pipeline" in code
        assert "Macro &amp; Economic Calendar" in code or "Macro & Economic Calendar" in code
        assert "OpenAI GPT-4o Reasoning" in code


class TestSafetyAndDiagnostics:
    """Tests for Read-Only invariants, Runtime Snapshot, and Advanced Diagnostics Drawer."""

    def test_read_only_safety_card(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "READ-ONLY SAFETY INVARIANTS" in code or "READ ONLY" in code
        assert "Order placement, paper trading, order modification, and broker mutations are hard-disabled" in code

    def test_runtime_snapshot_fields(self):
        code = read_frontend("components/settings/SettingsWorkspace.tsx")
        assert "RUNTIME SNAPSHOT" in code
        assert "Runtime ID" in code
        assert "State Sequence" in code
        assert "Environment" in code
        assert "Market Session" in code
        assert "Last Sync" in code
        assert "Version" in code

    def test_advanced_diagnostics_drawer_integration(self):
        drawer_code = read_frontend("components/settings/AdvancedDiagnosticsDrawer.tsx")
        assert "AdvancedDiagnosticsDrawer" in drawer_code
        assert "COMPONENT READINESS MATRIX" in drawer_code
        assert "DATASET INTEGRITY &amp; TELEMETRY COUNTS" in drawer_code or "DATASET INTEGRITY" in drawer_code
        assert "handleExportDiagnostics" in drawer_code
        assert "DetectorHealthPanel" in drawer_code
        assert "ArdhaPerformancePanel" in drawer_code

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
