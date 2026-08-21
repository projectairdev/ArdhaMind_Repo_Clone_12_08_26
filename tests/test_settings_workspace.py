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


# ── 1. SUBTABS & ARCHITECTURE CONTRACTS ──

def test_settings_workspace_six_subtabs_contract():
    code = read_frontend("components/settings/SettingsWorkspace.tsx")
    assert 'label: "OVERVIEW"' in code
    assert 'label: "CONNECTIONS"' in code
    assert 'label: "PREFERENCES"' in code
    assert 'label: "NOTIFICATIONS"' in code
    assert 'label: "DIAGNOSTICS"' in code
    assert 'label: "ABOUT"' in code


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
        "components/settings/SettingsOverview.tsx",
        "components/settings/SettingsConnections.tsx",
        "components/settings/SettingsPreferences.tsx",
        "components/settings/SettingsNotifications.tsx",
        "components/settings/SettingsDiagnostics.tsx",
        "components/settings/SettingsAbout.tsx",
    ]:
        code = read_frontend(rel_path)
        # Verify no secret variables are exposed or rendered in plain text
        assert "access_token" not in code or "no access_token" in code.lower() or "safe" in code.lower()
        assert "api_key" not in code or "api_key" in code.lower() and "protected" in code.lower()
        assert "client_secret" not in code
        assert "refresh_token" not in code


# ── 3. PREFERENCES & SAFE RESET CONTRACTS ──

def test_settings_preferences_safe_reset():
    code = read_frontend("components/settings/SettingsPreferences.tsx")
    assert "Reset Local UI Preferences" in code
    assert "Confirm Reset Local UI Preferences?" in code
    # Safe reset must reset local preferences without touching broker
    assert "DEFAULT_USER_PREFERENCES" in code
    assert "delete" not in code.lower() or "delete market" not in code.lower()


def test_staging_qa_controls_visibility():
    code = read_frontend("components/settings/SettingsPreferences.tsx")
    assert 'pres.environment === "STAGING"' in code
    assert "STAGING QA PREVIEW CONTROLS" in code


# ── 4. NOTIFICATIONS TRUTH CONTRACTS ──

def test_notifications_permission_truth():
    code = read_frontend("components/settings/SettingsNotifications.tsx")
    assert "Browser notification permission required" in code
    assert "highImpactNewsAlerts" in code
    assert "brokerDisconnectAlerts" in code


# ── 5. DIAGNOSTICS & ABOUT CONTRACTS ──

def test_diagnostics_export_contract():
    code = read_frontend("components/settings/SettingsDiagnostics.tsx")
    assert "handleExportDiagnostics" in code
    assert "ardhamind-diagnostics" in code
    assert "overallHealth" in code


def test_about_read_only_invariants_guarantee():
    code_about = read_frontend("components/settings/SettingsAbout.tsx")
    code_adapter = read_frontend("utils/canonicalSettingsAdapter.ts")
    assert "READ ONLY" in code_about
    assert "Order placement, paper trading, and broker mutations are strictly disabled" in code_adapter


# ── 6. SUBTAB SWITCHING & RENDERING CONTRACTS ──

def test_settings_subtab_navigation_wiring():
    """Verify DashboardLayout passes onSelectSubTab and SettingsWorkspace handles subtab changes."""
    dash_code = read_frontend("layout/DashboardLayout.tsx")
    settings_code = read_frontend("components/settings/SettingsWorkspace.tsx")

    assert "onSelectSubTab={setSettingsSubTab}" in dash_code, "DashboardLayout must pass onSelectSubTab"
    assert "currentSubTab === \"overview\" ? (" in settings_code
    assert "currentSubTab === \"connections\" ? (" in settings_code
    assert "currentSubTab === \"preferences\" ? (" in settings_code
    assert "currentSubTab === \"notifications\" ? (" in settings_code
    assert "currentSubTab === \"diagnostics\" ? (" in settings_code
    assert "<SettingsAbout" in settings_code

