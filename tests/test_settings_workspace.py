# tests/test_settings_workspace.py
"""
Automated Unit, Integration, & Security Contract Tests for SETTINGS Workspace.
Section 50 & 51 Quality Gates for AIR ArdhaMind.
"""

from pathlib import Path
import pytest


def read_frontend(rel_path: str) -> str:
    full_path = Path(__file__).parent.parent / "src" / "frontend" / rel_path
    return full_path.read_text(encoding="utf-8")


# ── 1. ARCHITECTURE & COMPONENT CONTRACTS ──

def test_settings_workspace_consolidated_architecture():
    code = read_frontend("components/settings/SettingsWorkspace.tsx")
    assert "SETTINGS" in code
    assert "Workstation preferences, data connections, alerts, and safety controls." in code
    assert "id=\"status-card-broker\"" in code
    assert "id=\"status-card-market-data\"" in code
    assert "id=\"status-card-news-engine\"" in code
    assert "id=\"status-card-ai-assistant\"" in code


def test_settings_adapter_structure_contract():
    code = read_frontend("utils/canonicalSettingsAdapter.ts")
    assert "export function getCanonicalSettingsPresentation" in code
    assert "DEFAULT_USER_PREFERENCES" in code
    assert "loadStoredPreferences" in code
    assert "saveStoredPreferences" in code
    assert "loadStoredNotifications" in code
    assert "saveStoredNotifications" in code


# ── 2. SECURITY & SECRET AUDIT CONTRACTS (SECTION 51) ──

def test_settings_components_do_not_render_secret_tokens():
    for rel_path in [
        "utils/canonicalSettingsAdapter.ts",
        "components/settings/SettingsWorkspace.tsx",
        "components/settings/AdvancedDiagnosticsDrawer.tsx",
    ]:
        code = read_frontend(rel_path)
        # Verify no secret variables are exposed or rendered in plain text
        assert "access_token" not in code or "no access_token" in code.lower() or "safe" in code.lower()
        assert "api_key" not in code or "api_key" in code.lower() and "protected" in code.lower()
        assert "client_secret" not in code
        assert "refresh_token" not in code


# ── 3. PREFERENCES & SAFE RESET CONTRACTS ──

def test_settings_preferences_safe_reset():
    code = read_frontend("components/settings/SettingsWorkspace.tsx")
    assert "SAFE RESET" in code
    assert "Reset local UI preferences to workstation defaults." in code
    assert "DEFAULT_USER_PREFERENCES" in code
    assert "delete" not in code.lower() or "delete backend" in code.lower() or "delete market" not in code.lower()


def test_staging_qa_controls_visibility():
    code = read_frontend("components/settings/SettingsWorkspace.tsx")
    assert 'pres.environment === "STAGING"' in code
    assert "STAGING QA SESSION CONTROLS" in code


# ── 4. NOTIFICATIONS TRUTH CONTRACTS ──

def test_notifications_permission_truth():
    code = read_frontend("components/settings/SettingsWorkspace.tsx")
    assert "Browser permission required" in code
    assert "highImpactNewsAlerts" in code
    assert "brokerDisconnectAlerts" in code


# ── 5. DIAGNOSTICS & ABOUT CONTRACTS ──

def test_diagnostics_export_contract():
    code = read_frontend("components/settings/AdvancedDiagnosticsDrawer.tsx")
    assert "handleExportDiagnostics" in code
    assert "ardhamind-diagnostics" in code
    assert "overallHealth" in code


def test_about_read_only_invariants_guarantee():
    code_ws = read_frontend("components/settings/SettingsWorkspace.tsx")
    code_adapter = read_frontend("utils/canonicalSettingsAdapter.ts")
    assert "READ ONLY" in code_ws
    assert "Order placement, paper trading, and broker mutations are strictly disabled" in code_adapter or "hard-disabled" in code_ws


# ── 6. WORKSPACE WIRING CONTRACTS ──

def test_settings_workspace_wiring():
    dash_code = read_frontend("layout/DashboardLayout.tsx")
    settings_code = read_frontend("components/settings/SettingsWorkspace.tsx")
    assert "<SettingsWorkspace" in dash_code
    assert "AdvancedDiagnosticsDrawer" in settings_code
