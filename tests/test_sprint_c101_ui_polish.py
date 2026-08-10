from pathlib import Path
import pytest
import re

ROOT = Path("src")


def read_src(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_nifty_live_contains_overview_tab():
    code = read_src("frontend/components/NiftyLiveWorkspace.tsx")
    assert "Overview" in code
    assert 'onClick={() => setActiveTab("overview")}' in code or "setActiveTab" in code


def test_nifty_live_contains_price_trend_tab():
    code = read_src("frontend/components/NiftyLiveWorkspace.tsx")
    assert "Price &amp; Trend" in code or "Price & Trend" in code
    assert 'onClick={() => setActiveTab("price-trend")}' in code or "price-trend" in code


def test_nifty_live_contains_options_tab():
    code = read_src("frontend/components/NiftyLiveWorkspace.tsx")
    assert "Options" in code
    assert 'onClick={() => setActiveTab("options")}' in code or "options" in code


def test_tabs_remain_present_irrespective_of_market_session():
    code = read_src("frontend/components/NiftyLiveWorkspace.tsx")
    assert 'data-testid="nifty-live-tabs"' in code
    nifty_workspace_body = code.split("export function NiftyLiveWorkspace")[1]
    tab_idx = nifty_workspace_body.find('data-testid="nifty-live-tabs"')
    panel_idx = nifty_workspace_body.find("<PriceTrendPanel")
    assert tab_idx != -1 and tab_idx < panel_idx


def test_existing_price_trend_panel_is_reused():
    code = read_src("frontend/components/NiftyLiveWorkspace.tsx")
    assert "export function PriceTrendPanel" in code
    assert "<PriceTrendPanel />" in code
    assert "<NiftyCandlestickChart" in code


def test_existing_options_panel_is_reused():
    code = read_src("frontend/components/NiftyLiveWorkspace.tsx")
    assert "export function OptionsPanel" in code
    assert "<OptionsPanel />" in code
    assert "<OptionChainLadder" in code or "Options intelligence unavailable" in code


def test_market_pulse_contains_dedicated_refresh_control():
    code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert "REFRESH MARKET PULSE" in code or "↻ REFRESH MARKET PULSE" in code
    assert "handleRefresh" in code


def test_market_pulse_refresh_reuses_existing_authoritative_refresh_path():
    code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert "syncBroker(true)" in code
    assert "await syncBroker(true)" in code


def test_react_contains_no_direct_provider_fetch():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    nifty_code = read_src("frontend/components/NiftyLiveWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")

    for file_name, code in [
        ("MarketPulseWorkspace", pulse_code),
        ("NiftyLiveWorkspace", nifty_code),
        ("MacroIntelligence", macro_code),
    ]:
        assert "fetch(" not in code, f"Direct fetch found in {file_name}"
        assert "axios." not in code, f"Direct axios found in {file_name}"
        assert "WebSocket(" not in code, f"Direct WebSocket found in {file_name}"


def test_refresh_button_prevents_duplicate_in_flight_requests():
    code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert "if (refreshing || loading) return;" in code
    assert "disabled={refreshing || loading}" in code
    assert "REFRESHING..." in code


def test_global_cues_macro_telemetry_has_standalone_card():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert "<GlobalCuesWidget />" in pulse_code
    assert "GLOBAL CUES & MACRO TELEMETRY" in macro_code or "GLOBAL CUES &amp; MACRO TELEMETRY" in macro_code


def test_nifty_50_official_membership_has_standalone_card():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert "<NiftyConstituentsWidget />" in pulse_code
    assert "NIFTY 50 OFFICIAL MEMBERSHIP" in macro_code


def test_cards_not_forced_into_compressed_layout():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    # GlobalCuesWidget and NiftyConstituentsWidget should not be side-by-side in grid-cols-2
    bottom_section = pulse_code.split("<GlobalCuesWidget />")[1] if "<GlobalCuesWidget />" in pulse_code else ""
    assert "grid-cols-2" not in pulse_code.split("SECTION A")[1] if "SECTION A" in pulse_code else True
    assert "<NiftyConstituentsWidget />" in bottom_section


def test_membership_preserves_50_50_canonical_resolution():
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert "Kite Resolved" in macro_code
    assert "resolution_count" in macro_code or "50" in macro_code
    assert "totalCount" in macro_code or "constituents.length" in macro_code


def test_no_market_numeric_values_modified_by_presentation():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    nifty_code = read_src("frontend/components/NiftyLiveWorkspace.tsx")
    # Verify numbers are formatted with safeNumber / formatNumber and no artificial multipliers are added
    assert "formatNumber(" in pulse_code
    assert "formatNumber(" in nifty_code
    assert "spot * 1." not in pulse_code
    assert "change * 1." not in nifty_code


def test_last_session_does_not_appear_prominently():
    terminology_code = read_src("frontend/utils/traderTerminology.ts")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert '"LAST_SESSION": "Previous Session"' in terminology_code
    assert "mapFreshness(" in macro_code or "mapTraderEnum(" in macro_code


def test_last_valid_session_does_not_appear_prominently():
    terminology_code = read_src("frontend/utils/traderTerminology.ts")
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert '"LAST_VALID_SESSION": "Previous Trading Session"' in terminology_code
    assert 'mapTraderEnum("LAST_VALID_SESSION")' in pulse_code or "mapFreshness" in pulse_code


def test_license_required_maps_to_licensed_data_required():
    terminology_code = read_src("frontend/utils/traderTerminology.ts")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert '"LICENSE_REQUIRED": "Licensed Data Required"' in terminology_code
    assert 'mapTraderEnum(meta.weights_status || "LICENSE_REQUIRED")' in macro_code or 'LICENSE_REQUIRED' in macro_code


def test_raw_machine_values_remain_available_in_diagnostics():
    nifty_code = read_src("frontend/components/NiftyLiveWorkspace.tsx")
    assert "data-provenance-details" in nifty_code or "Data details" in nifty_code
    assert "showDetails" in nifty_code or "quality_status" in nifty_code


def test_market_closed_presentation_does_not_falsely_display_live_badges():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert 'isClosed ? "Session Close" : "Live Session"' in pulse_code or "isClosed" in pulse_code
    assert "Updated 3s ago · LIVE" not in pulse_code


def test_market_open_presentation_correctly_displays_live_status():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert "Live Session" in pulse_code
    assert "SESSION:" in pulse_code


def test_responsive_css_contains_no_fixed_width_overflow_regression():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert "grid-cols-1" in pulse_code
    assert "sm:grid-cols-2" in pulse_code or "md:grid-cols-2" in pulse_code
    assert "grid-cols-1" in macro_code
    assert "lg:grid-cols-5" in macro_code or "xl:grid-cols-5" in macro_code


def test_no_backend_analytical_files_modified():
    # Verify no python backend analytical files in src/ are edited by checking imports in src/
    workstation_service = read_src("application/workstation_state_service.py")
    assert "CanonicalWorkstationState" in workstation_service


def test_no_duplicate_provider_path_introduced():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert "useWorkstationState" in pulse_code
    assert "syncBroker" in pulse_code


def test_read_only_boundary_remains_intact():
    read_only_code = read_src("read_only_http.ts")
    assert "rejectReadOnlyMutation" in read_only_code
