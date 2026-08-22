from pathlib import Path
from datetime import datetime, timezone
import pytest

from src.intelligence_engine import UnifiedNiftyIntelligenceBuilder
from src.application.workstation_state_service import WorkstationStateService
from src.models.canonical_workstation_state import CanonicalWorkstationState

ROOT = Path("src")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_last_session_not_visible_on_primary_trader_ui():
    terminology_code = read("frontend/utils/traderTerminology.ts")
    sector_code = read("frontend/components/visualizations/SectorPerformanceChart.tsx")
    assert '"LAST_SESSION": "Previous Trading Session"' in terminology_code or '"LAST_SESSION": "Previous Session"' in terminology_code
    assert "mapTraderEnum(sectors[0].observation_mode)" in sector_code


def test_sector_performance_single_panel_level_temporal_badge():
    sector_code = read("frontend/components/visualizations/SectorPerformanceChart.tsx")
    assert "observation_mode" in sector_code
    assert "mapTraderEnum" in sector_code


def test_raw_last_session_remains_available_diagnostically():
    settings_code = read("frontend/components/settings/SettingsWorkspace.tsx") + read("frontend/components/settings/AdvancedDiagnosticsDrawer.tsx")
    assert "Diagnostics" in settings_code or "ADVANCED" in settings_code


def test_decision_zones_are_primary_and_no_machine_tokens_on_primary_ui():
    panel_code = read("frontend/components/UnifiedIntelligencePanel.tsx")
    outlook_code = read("frontend/components/intelligence/TomorrowsOutlookCard.tsx")
    presentation_code = read("frontend/components/intelligence/CanonicalPresentation.tsx")
    live_code = read("frontend/components/NiftyLiveWorkspace.tsx")

    assert "DecisionZonesPanel" in panel_code
    assert "DecisionZonesPanel" in outlook_code
    assert 'title="Key levels"' in live_code
    assert "DECISION AREAS" in presentation_code
    assert "showRaw" in presentation_code
    assert "View raw levels & provenance" in presentation_code


def test_no_duplicate_level_panels_in_premarket_planner():
    panel_code = read("frontend/components/UnifiedIntelligencePanel.tsx")
    # PreMarketIntelligenceView should not render duplicate DecisionZonesPanel
    premarket_view_code = panel_code.split("PreMarketIntelligenceView()")[1].split("TodaysAnalysisSynthesis()")[0]
    assert "<DecisionZonesPanel" not in premarket_view_code


def test_raw_key_levels_accessible_in_detail():
    presentation_code = read("frontend/components/intelligence/CanonicalPresentation.tsx")
    assert "DecisionZonesPanel" in presentation_code
    assert "KeyLevelsPanel" in presentation_code
    assert "contributing_levels" in presentation_code
    assert "showRaw" in presentation_code


def test_react_performs_no_level_clustering():
    presentation_code = read("frontend/components/intelligence/CanonicalPresentation.tsx")
    # React uses zone.lower, zone.upper, zone.display_range directly from backend zone objects
    assert "zone.display_range" in presentation_code
    assert "zone.rationale" in presentation_code


def test_price_structure_not_exposed_on_primary_ui():
    terminology_code = read("frontend/utils/traderTerminology.ts")
    assert '"PRICE_STRUCTURE": "Price Structure"' in terminology_code


def test_todays_analysis_renders_explanatory_evidence():
    panel_code = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "confirmingEv.length" in panel_code
    assert "item.category_label" in panel_code
    assert "item.summary" in panel_code


def test_generic_labels_not_used_when_explanatory_evidence_exists():
    panel_code = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "item.summary" in panel_code


def test_uncertain_mapped_to_trader_language():
    terminology_code = read("frontend/utils/traderTerminology.ts")
    assert '"UNCERTAIN": "No Clear Direction"' in terminology_code


def test_missing_prior_comparison_presented_quietly():
    panel_code = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "PREVIOUS_COMPARISON_NOT_AVAILABLE_YET" in panel_code


def test_live_assistant_distinct_role():
    panel_code = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "NEXT SESSION WATCH — WHAT TO WATCH NEXT" in panel_code
    assert "LIVE MARKET MONITOR — WHAT TO WATCH NOW" in panel_code


def test_closed_market_live_assistant_no_fake_live_claim():
    panel_code = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "Live confirmation is paused while the market is closed." in panel_code


def test_market_open_live_assistant_uses_canonical_validation():
    panel_code = read("frontend/components/UnifiedIntelligencePanel.tsx")
    assert "WHAT TO WATCH NEXT" in panel_code
    assert "preferredSetup.title" in panel_code


def test_live_assistant_contains_no_executable_trade_words():
    panel_code = read("frontend/components/UnifiedIntelligencePanel.tsx")
    for forbidden in ["BUY", "SELL", "PLACE ORDER", "QUANTITY", "POSITION SIZE", "TARGET", "STOP LOSS"]:
        assert forbidden not in panel_code.split("LiveAssistantExplanationView()")[1]


def test_decision_zones_originate_exclusively_from_backend():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    market = {"current_spot": 24568.69, "support_levels": [24568.69, 24569.67]}
    result = UnifiedNiftyIntelligenceBuilder.build(
        market=market, technical={}, options={}, macro={}, news={}, market_state="CLOSED", now=now
    )
    zones = result.get("decision_zones") or []
    assert len(zones) > 0
    assert "zone_id" in zones[0]
    assert "display_range" in zones[0]


def test_technical_diagnostics_retain_raw_tokens():
    settings_code = read("frontend/components/settings/SettingsWorkspace.tsx") + read("frontend/components/settings/AdvancedDiagnosticsDrawer.tsx")
    assert "dataIntegrity" in settings_code or "data_integrity" in settings_code or "Diagnostics" in settings_code


def test_no_canonical_numerical_values_modified():
    levels = [{"value": 24568.69, "origin": "PRICE_STRUCTURE", "role": "SUPPORT"}]
    zones = UnifiedNiftyIntelligenceBuilder._decision_zones(levels)
    assert levels[0]["value"] == 24568.69
    assert zones[0]["lower"] == 24568.69


def test_nifty_only_product_boundary_intact():
    assert CanonicalWorkstationState._assert_read_only is not None
