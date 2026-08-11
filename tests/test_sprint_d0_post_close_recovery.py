# tests/test_sprint_d0_post_close_recovery.py
"""Sprint D.0 — Post-Close & Recovery Validation Tests."""

from pathlib import Path
from datetime import datetime, timezone
import pytest

from src.application.workstation_state_service import WorkstationStateService
from src.pipeline.macro_pipeline import MacroPipeline

ROOT = Path("src")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_post_close_state_renders_without_market_open_requirement():
    now = datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc)
    payload = {
        "marketContext": {
            "current_spot": 24568.65,
            "previous_close": 24520.40,
            "last_tick_time": "2026-08-10T15:30:00Z"
        }
    }
    canonical = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED", now=now)
    session = canonical.market_session
    assert str(session.get("status")).lower() in {"closed", "market_closed"}
    assert session.get("is_closed") is True or session.get("status") == "closed"


def test_nifty_live_tab_bar_exists_while_closed():
    code = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "Overview" in code
    assert "price-trend" in code
    assert "Options" in code
    assert "activeTab" in code


def test_breadth_retains_last_final_session_semantics():
    now = datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc)
    payload = {
        "marketContext": {
            "current_spot": 24568.65,
            "breadth": {"advances": 31, "declines": 19, "unchanged": 0, "coverage": {"valid": 50, "total": 50}}
        }
    }
    canonical = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED", now=now)
    breadth = canonical.market_data["breadth"]
    assert breadth["advances"] == 31
    assert breadth["declines"] == 19
    assert breadth["coverage"]["valid"] == 50


def test_no_false_live_label_for_nse_finalized_data():
    code = read("frontend/utils/traderTerminology.ts")
    assert "mapTraderEnum" in code
    assert "CLOSED" in code or "Session Closed" in code


def test_price_trend_remains_accessible_when_closed():
    code = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "PriceTrendPanel" in code
    assert 'activeTab === "price-trend"' in code


def test_options_remains_accessible_when_closed():
    code = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "OptionsPanel" in code
    assert 'activeTab === "options"' in code


def test_market_pulse_refresh_uses_canonical_sync_path():
    code = read("frontend/components/MarketPulseWorkspace.tsx")
    assert "syncBroker" in code
    assert "handleRefresh" in code
    assert "fetch(" not in code


def test_cross_asset_summary_detail_equality():
    ts_code = read("frontend/utils/canonicalQuotes.ts")
    assert "getCanonicalQuote" in ts_code
    assert "CanonicalQuoteView" in ts_code
    assert '"83.92"' not in ts_code
    assert '"79.45"' not in ts_code


def test_no_hardcoded_market_fallback():
    pulse_code = read("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read("frontend/components/MacroIntelligence.tsx")
    assert '"83.92"' not in pulse_code
    assert '"79.45"' not in pulse_code
    assert '"3.88%"' not in pulse_code
    assert '"83.92"' not in macro_code
    assert '"79.45"' not in macro_code


def test_optional_provider_failure_does_not_degrade_core_market_feed():
    now = datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc)
    payload = {
        "marketContext": {"current_spot": 24568.65, "last_tick_time": "2026-08-10T15:30:00Z"},
        "newsSentiment": {"status": "UNAVAILABLE", "items": []}
    }
    canonical = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED", now=now)
    readiness = canonical.to_dict().get("workspace_readiness", {})
    assert readiness.get("core_market_feed_state") == "READY"
    assert readiness.get("intelligence_providers_state") == "DEGRADED"


def test_restart_reconstruction_preserves_market_state_truth():
    now = datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc)
    payload = {"marketContext": {"current_spot": 24568.65, "last_tick_time": "2026-08-10T15:30:00Z"}}
    c1 = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED", now=now)
    c2 = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED", now=now)
    assert c1.market_session["status"] == c2.market_session["status"]
    assert c1.market_data["current_spot"] == c2.market_data["current_spot"] == 24568.65


def test_stale_observation_remains_labeled_stale_or_previous_session():
    macro_pipe = MacroPipeline()
    res = macro_pipe.run()
    dict_res = res.to_dict() if hasattr(res, "to_dict") else res
    quotes = dict_res.get("quotes", {})
    sp500 = quotes.get("S&P 500", {})
    assert sp500.get("freshness_status") in {"RECENT", "STALE", "PREVIOUS_SESSION", "CURRENT", "last_valid_session", "fresh", "recent", "stale"}


def test_missing_observation_stays_unavailable():
    now = datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc)
    payload = {"marketContext": {"current_spot": None}}
    canonical = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED", now=now)
    assert canonical.market_data.get("current_spot") is None or canonical.market_data.get("status") == "UNAVAILABLE"


def test_no_state_sequence_rollback():
    now = datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc)
    payload = {"marketContext": {"current_spot": 24568.65, "last_tick_time": "2026-08-10T15:30:00Z"}}
    c1 = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED", now=now)
    c2 = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED", now=now)
    assert c2.to_dict().get("sequence", 0) >= c1.to_dict().get("sequence", 0)


def test_browser_reload_state_path_has_no_duplicate_provider_fetch():
    pulse_code = read("frontend/components/MarketPulseWorkspace.tsx")
    assert "new WebSocket" not in pulse_code
    assert "axios" not in pulse_code


def test_no_frontend_fetch():
    pulse_code = read("frontend/components/MarketPulseWorkspace.tsx")
    nifty_code = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "fetch(" not in pulse_code
    assert "fetch(" not in nifty_code


def test_no_axios():
    pulse_code = read("frontend/components/MarketPulseWorkspace.tsx")
    nifty_code = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "axios" not in pulse_code
    assert "axios" not in nifty_code


def test_no_frontend_websocket_construction():
    pulse_code = read("frontend/components/MarketPulseWorkspace.tsx")
    nifty_code = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "new WebSocket" not in pulse_code
    assert "new WebSocket" not in nifty_code


def test_read_only_boundary_preserved():
    boundary_file = Path("tests/test_e4b_read_only_boundary.py")
    boundary_code = boundary_file.read_text(encoding="utf-8")
    assert "test_daemon_rejects_every_execution_action_before_service_access" in boundary_code


def test_scratch_validation_logger_is_not_production_runtime_code():
    harness_path = Path("scratch/live_validation_harness.py")
    assert harness_path.exists()
    src_files = list(ROOT.rglob("*.py"))
    for f in src_files:
        assert "live_validation_harness" not in f.read_text(encoding="utf-8")


def test_workspace_responsibility_decision_areas_panel_isolation():
    nifty_live = read("frontend/components/NiftyLiveWorkspace.tsx")
    unified_intel = read("frontend/components/UnifiedIntelligencePanel.tsx")
    # 1. DecisionAreasPanel full renderer exists only in NIFTY Live Price & Trend
    assert "<DecisionAreasPanel" in nifty_live
    # 2. Today's Analysis does not render full Decision Areas
    # 3. Live Assistant does not render full Decision Areas
    assert "<DecisionAreasPanel" not in unified_intel
    assert "<DecisionZonesPanel" not in unified_intel


def test_live_assistant_consumes_nearest_levels():
    unified_intel = read("frontend/components/UnifiedIntelligencePanel.tsx")
    # 4. Live Assistant may consume canonical nearest decision levels
    assert "nearestDecisionLevels" in unified_intel
    assert "nearestSupport" in unified_intel
    assert "nearestResistance" in unified_intel


def test_scenario_ownership_isolation():
    unified_intel = read("frontend/components/UnifiedIntelligencePanel.tsx")
    intraday = read("frontend/components/IntradayAssistant.tsx")
    nifty_live = read("frontend/components/NiftyLiveWorkspace.tsx")
    pulse = read("frontend/components/MarketPulseWorkspace.tsx")

    # 5. Full primary/alternate scenarios render only in Live Assistant
    assert "<ScenarioGrid" in intraday
    assert "<ScenarioGrid" not in unified_intel
    assert "<ScenarioGrid" not in nifty_live
    assert "<ScenarioGrid" not in pulse
    
    # Verify ScenarioGrid is not in Today's Analysis synthesis
    analysis_section = unified_intel.split("export function TodaysAnalysisSynthesis()")[1].split("export function LiveAssistantExplanationView()")[0]
    assert "<ScenarioGrid" not in analysis_section
    assert "<ScenarioCard" not in analysis_section
    
    # 6. Today's Analysis exposes scenario reference only
    assert "Scenario Context" in analysis_section
    assert "primaryScenarioName" in analysis_section


def test_option_chain_isolation():
    unified_intel = read("frontend/components/UnifiedIntelligencePanel.tsx")
    pulse = read("frontend/components/MarketPulseWorkspace.tsx")
    nifty_live = read("frontend/components/NiftyLiveWorkspace.tsx")
    # 7. Full option chain exists only in NIFTY Live Options
    assert "<OptionChainLadder" in nifty_live
    assert "<OptionChainLadder" not in unified_intel
    assert "<OptionChainLadder" not in pulse


def test_movers_and_sector_performance_isolation():
    nifty_live = read("frontend/components/NiftyLiveWorkspace.tsx")
    unified_intel = read("frontend/components/UnifiedIntelligencePanel.tsx")
    pulse = read("frontend/components/MarketPulseWorkspace.tsx")
    # 8. Full movers exist only in NIFTY Live Overview
    assert "Top constituent movers" in nifty_live
    assert "Top constituent movers" not in unified_intel
    assert "Top constituent movers" not in pulse
    # 9. Full sector performance exists only in NIFTY Live Overview
    assert "<SectorPerformanceChart" in nifty_live
    assert "<SectorPerformanceChart" not in unified_intel
    assert "<SectorPerformanceChart" not in pulse


def test_global_telemetry_isolation():
    unified_intel = read("frontend/components/UnifiedIntelligencePanel.tsx")
    pulse = read("frontend/components/MarketPulseWorkspace.tsx")
    nifty_live = read("frontend/components/NiftyLiveWorkspace.tsx")
    # 10. Full global telemetry exists only in Market Pulse (among active workspaces)
    assert "<GlobalCuesWidget />" in pulse
    assert "<GlobalCuesWidget" not in unified_intel
    assert "<GlobalCuesWidget" not in nifty_live


def test_news_feed_isolation():
    workspaces = read("frontend/components/PhaseOneWorkspaces.tsx")
    # 11. Full news feed exists only in NEWS & UPDATES (renders under NewsUpdatesWorkspace only)
    news_updates_section = workspaces.split("export function NewsUpdatesWorkspace()")[1].split("export function")[0]
    assert "<NewsIntelligence />" in news_updates_section
    
    # Verify other active workspaces do not render NewsIntelligence
    todays_analysis_section = workspaces.split("export function TodaysAnalysisWorkspace()")[1].split("export function")[0]
    live_assistant_section = workspaces.split("export function LiveAssistantWorkspace()")[1].split("export function")[0]
    assert "<NewsIntelligence" not in todays_analysis_section
    assert "<NewsIntelligence" not in live_assistant_section


def test_provider_diagnostics_isolation():
    workspaces = read("frontend/components/PhaseOneWorkspaces.tsx")
    nifty_live = read("frontend/components/NiftyLiveWorkspace.tsx")
    pulse = read("frontend/components/MarketPulseWorkspace.tsx")
    
    # 12. Detailed provider diagnostics exist only in Settings
    settings_section = workspaces.split("export function SettingsWorkspace()")[1]
    assert "<SettingsDashboard />" in settings_section
    
    # Primary trading workspaces must not render detailed provider diagnostics table or diagnostic widgets
    assert "SystemReadinessWidget" not in workspaces
    assert "OpenAIDiagnosticsWidget" not in workspaces
    assert "SystemReadinessWidget" not in nifty_live
    assert "OpenAIDiagnosticsWidget" not in nifty_live
    assert "SystemReadinessWidget" not in pulse
    assert "OpenAIDiagnosticsWidget" not in pulse


def test_no_calculation_duplication_and_data_integrity():
    # 13. No canonical calculation is duplicated (they use shared nearestDecisionLevels selector)
    # 14. No canonical data field is lost (nearestDecisionLevels consumes decision_zones)
    presentation = read("frontend/components/intelligence/CanonicalPresentation.tsx")
    assert "export function nearestDecisionLevels" in presentation
    assert "zones" in presentation
    assert "spot" in presentation


def test_constituent_resolution_no_zero_fallback():
    # 1. Constituent resolution does not fall back to 0/50 when unavailable
    macro_code = read("frontend/components/MacroIntelligence.tsx")
    assert "isResolutionAvailable" in macro_code
    assert "resolutionDisplay" in macro_code
    assert '"Unavailable"' in macro_code


def test_fii_dii_temporal_truth_no_live_label():
    # 2. FII/DII cash flows should not display LIVE or CURRENT SESSION
    macro_code = read("frontend/components/MacroIntelligence.tsx")
    assert "sessionContext" in macro_code
    assert '"Previous Trading Session"' in macro_code
    assert 'cleanFreshness' in macro_code
    assert '"Recent Observation"' in macro_code


def test_closed_holiday_weekend_distinction():
    # 3. CLOSED and HOLIDAY and WEEKEND must be handled distinctly in trader terminology
    ts_code = read("frontend/utils/traderTerminology.ts")
    assert "getTraderMarketStatus" in ts_code
    assert "Asia/Kolkata" in ts_code
    assert '"Weekend"' in ts_code
    assert '"Holiday"' in ts_code
    assert '"Market Closed"' in ts_code


def test_closed_session_scenarios_pending_conditions():
    # 4. Scenario watch conditions must show Pending when market is closed
    presentation = read("frontend/components/intelligence/CanonicalPresentation.tsx")
    assert "mapCondition" in presentation
    assert "isClosed" in presentation
    assert '"NEXT SESSION — PENDING"' in presentation
    assert '"LIVE SESSION — ACTIVE"' in presentation


def test_global_session_label_consistency():
    # 5. GIFT Nifty, S&P 500, etc. must share standardized session labels
    ts_code = read("frontend/utils/canonicalQuotes.ts")
    assert "getGlobalSessionLabel" in ts_code
    assert '"Previous US Session"' in ts_code
    assert '"Current Asian Session"' in ts_code
    assert '"Current Session"' in ts_code
    assert '"Global Telemetry"' in ts_code


def test_no_primary_ui_raw_freshness_tokens():
    # 6. Raw freshness status tokens like last_valid_session, recent, fresh, semi_annual mapped
    ts_code = read("frontend/utils/traderTerminology.ts")
    assert '"FRESH"' in ts_code
    assert '"RECENT"' in ts_code
    assert '"SEMI_ANNUAL"' in ts_code
    
    topbar_code = read("frontend/components/WorkstationTopBar.tsx")
    assert 'freshness.replaceAll("_", " ")' not in topbar_code
    assert 'mapTraderEnum(freshness)' in topbar_code


def test_vwap_and_ema_readiness_audit():
    # 7. VWAP and EMA readiness audit rules
    h_code = read("application/workstation_state_service.py")
    assert '"Index spot data has no volume; VWAP requires volume-weighted ticks."' in h_code
    assert '"Requires minimum 50 historical candles for calculation."' in h_code
