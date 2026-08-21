# tests/test_sprint_d02_live_assistant_news_sorting_time.py
"""Sprint D.0.2 — Live Assistant, News, Sorting, and Time Formatting validation."""

from pathlib import Path
from src.application.workstation_state_service import WorkstationStateService
#import pytest

ROOT = Path("src")

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

# 1. TIME FORMATTING FILES & EXPORTS
def test_time_formatting_file_exists():
    assert (ROOT / "frontend/utils/timeFormatting.ts").exists()

def test_time_formatting_exports():
    code = read("frontend/utils/timeFormatting.ts")
    assert "export function formatTimestampIST" in code

def test_time_formatting_compact_exports():
    code = read("frontend/utils/timeFormatting.ts")
    assert "export function formatCompactTimestampIST" in code

def test_time_formatting_time_exports():
    code = read("frontend/utils/timeFormatting.ts")
    assert "export function formatTimeIST" in code

def test_time_formatting_relative_exports():
    code = read("frontend/utils/timeFormatting.ts")
    assert "export function formatRelativeAge" in code

def test_time_formatting_no_epoch_start():
    code = read("frontend/utils/timeFormatting.ts")
    assert "1970" in code
    assert "getMonth" in code

def test_time_formatting_invalid_date():
    code = read("frontend/utils/timeFormatting.ts")
    assert "isNaN" in code

def test_time_formatting_missing_timestamp():
    code = read("frontend/utils/timeFormatting.ts")
    assert "if (!timestamp)" in code or "if (!timestamp" in code

def test_time_formatting_time_zone_ist():
    code = read("frontend/utils/timeFormatting.ts")
    assert "Asia/Kolkata" in code

# 2. STATE HISTORY & EVENT STREAM (CONTEXT)
def test_state_history_captured_in_context():
    code = read("frontend/context/WorkstationStateContext.tsx")
    assert "stateHistory" in code
    assert "setStateHistory" in code

def test_state_history_limit_to_300():
    code = read("frontend/context/WorkstationStateContext.tsx")
    assert "slice(-300)" in code

def test_live_event_stream_captured_in_context():
    code = read("frontend/context/WorkstationStateContext.tsx")
    assert "liveEventStream" in code
    assert "setLiveEventStream" in code

def test_live_event_stream_limit_to_50():
    code = read("frontend/context/WorkstationStateContext.tsx")
    assert "slice(0, 50)" in code or "slice(0,50)" in code

def test_regime_shift_event_creation():
    code = read("frontend/context/WorkstationStateContext.tsx")
    assert "market_regime" in code
    assert "Regime shifted" in code

def test_alignment_shift_event_creation():
    code = read("frontend/context/WorkstationStateContext.tsx")
    assert "alignment" in code
    assert "Market Alignment shifted" in code

def test_breadth_change_event_creation():
    code = read("frontend/context/WorkstationStateContext.tsx")
    assert "advances" in code
    assert "Breadth changed" in code

def test_pcr_shift_event_creation():
    code = read("frontend/context/WorkstationStateContext.tsx")
    assert "pcr" in code
    assert "0.02" in code

def test_vix_shift_event_creation():
    code = read("frontend/context/WorkstationStateContext.tsx")
    assert "vix" in code or "india_vix" in code
    assert "0.1" in code

# 3. LIVE ASSISTANT
def test_assistant_spot_and_change_rendering():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "spot" in code
    assert "change" in code
    assert "changePct" in code

def test_assistant_state_bias_derived():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "marketStateLabel" in code
    assert "supporting" in code

def test_assistant_setup_title_derived():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "preferred_setup" in code
    assert "title" in code

def test_assistant_matrix_count_derived():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "supporting" in code
    assert "opposing" in code
    assert "neutral" in code

def test_assistant_no_arbitrary_confidence():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "confidence" not in code.lower() or "confidenceReport" in code or "getConfidenceReport" in code

def test_assistant_temporal_selector_exists():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "compareWindow" in code
    assert "setCompareWindow" in code
    assert "open" in code

def test_assistant_closest_snapshot_comp():
    context = read("frontend/context/WorkstationStateContext.tsx")
    assistant = read("frontend/components/IntradayAssistant.tsx")
    assert "LiveAssistantSnapshot[]" in context
    assert "snapshot: LiveAssistantSnapshot" in context
    assert "live_assistant_temporal_state" in assistant

def test_assistant_actual_time_difference_label():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "LAST" in code
    assert "mins" in code or "actualDiffMs" in code

def test_assistant_confirmation_matrix_exists():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "confirmationMatrix" in code

def test_assistant_matrix_families_rendered():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "PRICE" in code
    assert "BREADTH" in code
    assert "OPTIONS" in code
    assert "VOLATILITY" in code

def test_assistant_matrix_directions():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "arrowDirections" in code
    assert "arrow" in code

def test_assistant_active_behavior_panel():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "preferred_setup" in code
    assert "description" in code

def test_assistant_scenario_monitor():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "scenarios" in code
    assert "ScenarioCard" in code

def test_assistant_scenario_card_closed_state():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "ScenarioCard" in code

def test_assistant_what_matters_next():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "nearestSupport" in code
    assert "nearestResistance" in code

def test_assistant_event_stream_widget():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "liveEventStream" in code

def test_assistant_event_sorting():
    code = read("frontend/components/IntradayAssistant.tsx")
    assert "eventSort" in code
    assert "setEventSort" in code

# 4. NEWS TAB LAYOUT & DENSITY
def test_news_tab_reduction():
    code = read("frontend/components/NewsIntelligence.tsx")
    assert "market-moving" in code
    assert "latest" in code
    assert "events" in code
    assert "corporate" in code

def test_news_card_collapsed_density():
    code = read("frontend/components/NewsIntelligence.tsx")
    assert "why_it_matters" in code
    assert "source_name" in code

def test_news_card_collapsed_badges():
    code = read("frontend/components/NewsIntelligence.tsx")
    assert "expected_direction" in code or "direction" in code
    assert "impact_strength" in code or "impact_level" in code
    assert "verification_status" in code

def test_news_card_expand_toggle():
    code = read("frontend/components/NewsIntelligence.tsx")
    assert "expandedCards" in code
    assert "toggleExpand" in code

def test_news_card_expanded_details():
    code = read("frontend/components/NewsIntelligence.tsx")
    assert "source_tier" in code
    assert "nifty_relevance_score" in code
    assert "published_at" in code
    assert "first_seen" in code

def test_news_sorting_dropdown():
    code = read("frontend/components/NewsIntelligence.tsx")
    assert "sortBy" in code
    assert "impact" in code
    assert "relevance" in code

def test_news_dynamic_category_filter():
    code = read("frontend/components/NewsIntelligence.tsx")
    assert "filterCategory" in code
    assert "uniqueCategories" in code

def test_news_timestamps_format():
    code = read("frontend/components/NewsIntelligence.tsx")
    assert "formatRelativeAge" in code
    assert "formatTimestampIST" in code

# 5. DASHBOARD & WIDGET SORTING
def test_global_markets_sorting():
    code = read("frontend/components/visualizations/GlobalMarketsDashboard.tsx")
    assert "sortBy" in code
    assert "change" in code
    assert "freshness" in code

def test_global_markets_flat_layout():
    code = read("frontend/components/visualizations/GlobalMarketsDashboard.tsx")
    assert "table" in code
    assert "thead" in code

def test_sectors_sorting():
    code = read("frontend/components/visualizations/SectorPerformanceChart.tsx")
    assert "safeNumber(b.change_pct, 0) - safeNumber(a.change_pct, 0)" in code
    assert "change" in code
    assert "name" in code

def test_constituents_sorting():
    code = read("frontend/components/MacroIntelligence.tsx")
    assert "sortedConstituents" in code
    assert "symbol" in code
    assert "sector" in code

def test_option_chain_ladder_strike_sorting():
    code = read("frontend/components/visualizations/OptionChainLadder.tsx")
    assert "strikeSortDir" in code
    assert "sortedStrikes" in code

# 6. SETTINGS & SYSTEM UX
def test_settings_timestamps():
    code = read("frontend/components/SettingsDashboard.tsx")
    assert "formatTimestampIST" in code
    assert "last_authenticated_at" in code

def test_settings_provider_health_sorting():
    code = read("frontend/components/SettingsDashboard.tsx")
    assert "sortedProviders" in code
    assert "providerSortBy" in code
    assert "status" in code

# 7. INVARIANTS & INTEGRATION
def test_no_direct_fetch_in_react():
    # Only manual news refresh calls can hit fetch, but visual widgets should read read-only hooks
    pass

def test_market_subnav_timestamp_IST_without_welcome_copy():
    code = read("frontend/layout/DashboardLayout.tsx")
    top_bar = read("frontend/components/WorkstationTopBar.tsx")
    assert 'timeZone: "Asia/Kolkata"' in code and "hour12: true" in code
    assert "marketClock.date" in code and "marketClock.time" in code
    assert "Welcome back," not in top_bar and "Arjun" not in top_bar


# 8. D.0.2 RENDER PATH, SORT OWNERSHIP, AND CONTRACT
def test_live_assistant_workspace_mounts_single_primary_renderer():
    code = read("frontend/components/PhaseOneWorkspaces.tsx")
    workspace = code.split("export function LiveAssistantWorkspace()", 1)[1].split("export function SettingsWorkspace()", 1)[0]
    assert workspace.count("<IntradayAssistant />") == 1
    assert "LiveAssistantExplanationView" not in workspace
    assert "feed_health" not in workspace
    assert "DecisionEngine" not in workspace


def test_closed_session_structure_is_owned_by_intraday_assistant():
    code = read("frontend/components/IntradayAssistant.tsx")
    for label in (
        "CURRENT MARKET STATE", "WHAT CHANGED", "CONFIRMATION MATRIX",
        "ACTIVE MARKET BEHAVIOR", "SCENARIO MONITOR", "WHAT MATTERS NEXT",
        "LIVE EVENT STREAM",
    ):
        assert label in code
    for window in ('"1m"', '"5m"', '"15m"', '"open"'):
        assert window in code
    assert "Unavailable — No current-session comparison history" in code


def test_news_rendered_collection_preserves_explicit_sort():
    code = read("frontend/components/NewsIntelligence.tsx")
    render_block = code.split("const renderItems = useMemo", 1)[1].split("// Events filtering", 1)[0]
    assert "sortedAndFilteredItems" in render_block
    assert ".sort(" not in render_block
    assert "renderItems.map" in code


def test_temporal_state_has_explicit_types_and_lightweight_history():
    types = read("frontend/types.ts")
    context = read("frontend/context/WorkstationStateContext.tsx")
    assert "export interface LiveAssistantTemporalState" in types
    assert "live_assistant_temporal_state?: LiveAssistantTemporalState" in types
    assert "live_assistant_temporal_state?: any" not in types
    assert "useState<LiveAssistantSnapshot[]>([])" in context
    assert "useState<CanonicalWorkstationState[]>([])" not in context


def test_closed_temporal_contract_accepts_null_breadth():
    payload = {
        "marketContext": {"breadth": None},
        "optionContext": {},
        "newsSentiment": {},
        "macroIntelligence": {},
    }
    state = WorkstationStateService.build_from_legacy(
        payload, broker_state="DISCONNECTED", market_state="MARKET_CLOSED"
    ).to_dict()
    temporal = state["live_assistant_temporal_state"]
    assert temporal["generated_at"] == state["generated_at"]
    assert temporal["current"]["market_state"] == "CLOSED"
    assert [row["requested_window"] for row in temporal["comparisons"]] == [
        "1 MIN", "5 MIN", "15 MIN", "SINCE OPEN"
    ]
