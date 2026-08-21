from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = (ROOT / "src/frontend/layout/DashboardLayout.tsx").read_text(encoding="utf-8")
NAV_CTX = (ROOT / "src/frontend/context/NavigationContext.tsx").read_text(encoding="utf-8")

def test_settings_navigation_state_transition_clears_settings_open():
    """Requirement 11: Switching between NIFTY, METRICS, OPTIONS when Settings is active must clear settingsOpen via navigateTo."""
    assert "const navigateMarketSubTab = (tab: MarketSubTab) => {" in LAYOUT
    subtab_fn = LAYOUT.split("const navigateMarketSubTab = (tab: MarketSubTab) => {", 1)[1].split("};", 1)[0]
    assert 'navigateTo({ workspace: "market", tab })' in subtab_fn, "navigateMarketSubTab must call navigateTo with market workspace"
    assert "setSettingsOpenState(false)" in NAV_CTX, "navigateTo must reset settingsOpen to false when transitioning to market"

def test_module_navigation_clears_settings_open():
    assert "const navigateModule = (id: PrimaryModuleId) => {" in LAYOUT
    module_fn = LAYOUT.split("const navigateModule = (id: PrimaryModuleId) => {", 1)[1].split("};", 1)[0]
    assert "navigateTo({ workspace: id })" in module_fn, "navigateModule must call navigateTo with target module"
    assert "setSettingsOpenState(false)" in NAV_CTX, "navigateTo must reset settingsOpen to false when transitioning module"
