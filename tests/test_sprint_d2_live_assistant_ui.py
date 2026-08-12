# tests/test_sprint_d2_live_assistant_ui.py
"""Sprint D.2 — Productized Live Assistant UI & Acceptance Tests."""

from pathlib import Path

ROOT = Path("src/frontend/components")

def read_component(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")

class TestSprintD2LiveAssistantUI:

    def test_live_assistant_renderer_exists(self):
        code = read_component("IntradayAssistant.tsx")
        assert "export function IntradayAssistant" in code

    def test_what_to_do_now_visible(self):
        code = read_component("IntradayAssistant.tsx")
        assert "WHAT TO DO NOW" in code
        assert "WAIT FOR / REQUIRED CONDITIONS" in code
        assert "AVOID IF / FAILURE CONDITIONS" in code

    def test_setup_candidate_visible(self):
        code = read_component("IntradayAssistant.tsx")
        assert "SETUP CANDIDATE & ENTRY / INVALIDATION REFERENCE" in code

    def test_most_likely_path_visible(self):
        code = read_component("IntradayAssistant.tsx")
        assert "MOST LIKELY" in code


    def test_alternate_path_visible(self):
        code = read_component("IntradayAssistant.tsx")
        assert "ALTERNATE PATH" in code

    def test_what_to_watch_visible(self):
        code = read_component("IntradayAssistant.tsx")
        assert "WHAT TO WATCH (PRIORITY RANKED)" in code

    def test_if_then_monitor_visible(self):
        code = read_component("IntradayAssistant.tsx")
        assert "IF / THEN MONITOR" in code

    def test_confirmation_matrix_stance_and_trend(self):
        code = read_component("IntradayAssistant.tsx")
        assert "CONFIRMATION MATRIX" in code
        assert "arrowDirections" in code
        assert "trendDir" in code or "trend" in code

    def test_heavyweights_unavailable_truth(self):
        code = read_component("IntradayAssistant.tsx")
        assert "Authoritative weights unavailable" in code

    def test_1m_available_state(self):
        code = read_component("IntradayAssistant.tsx")
        assert '"1m"' in code or "'1m'" in code

    def test_5m_available_state(self):
        code = read_component("IntradayAssistant.tsx")
        assert '"5m"' in code or "'5m'" in code

    def test_15m_available_state(self):
        code = read_component("IntradayAssistant.tsx")
        assert '"15m"' in code or "'15m'" in code

    def test_15m_rebuilding_visible(self):
        code = read_component("IntradayAssistant.tsx")
        assert "REBUILDING" in code
        assert "rebuildingTimer" in code

    def test_15m_telemetry_gap_visible(self):
        code = read_component("IntradayAssistant.tsx")
        assert "TELEMETRY_GAP" in code or "TELEMETRY GAP" in code

    def test_since_open_gap_warning(self):
        code = read_component("IntradayAssistant.tsx")
        assert "Observations contain telemetry gaps" in code

    def test_setup_entry_rendering(self):
        code = read_component("IntradayAssistant.tsx")
        assert "ENTRY REFERENCE" in code

    def test_setup_invalidation_rendering(self):
        code = read_component("IntradayAssistant.tsx")
        assert "INVALIDATION REFERENCE" in code

    def test_profit_unavailable_rendering(self):
        code = read_component("IntradayAssistant.tsx")
        assert "No downstream canonical structural reference" in code

    def test_setup_status_rendering(self):
        code = read_component("IntradayAssistant.tsx")
        assert "setupStatusStyle" in code
        assert "CONFIRMED_CONTEXT" in code

    def test_structural_bias_rendering(self):
        code = read_component("IntradayAssistant.tsx")
        assert "structural_bias" in code

    def test_short_term_momentum_rendering(self):
        code = read_component("IntradayAssistant.tsx")
        assert "short_term_momentum" in code

    def test_material_events_rendering(self):
        code = read_component("IntradayAssistant.tsx")
        assert "MATERIAL EVENT STREAM" in code
        assert "familyFilter" in code

    def test_scenario_grid_rendered(self):
        code = read_component("IntradayAssistant.tsx")
        assert "ScenarioGrid" in code

    def test_no_full_decision_areas_duplication(self):
        code = read_component("IntradayAssistant.tsx")
        assert "<DecisionAreasPanel" not in code

    def test_no_full_option_chain_duplication(self):
        code = read_component("IntradayAssistant.tsx")
        assert "<OptionChainPanel" not in code

    def test_no_full_news_feed_duplication(self):
        code = read_component("IntradayAssistant.tsx")
        assert "<NewsIntelligence" not in code

    def test_no_react_side_trading_thresholds(self):
        code = read_component("IntradayAssistant.tsx")
        assert "BUY_CALL" not in code
        assert "BUY_PUT" not in code

    def test_read_only_boundary_preserved(self):
        code = read_component("IntradayAssistant.tsx")
        assert "fetch(" not in code
        assert "axios" not in code
        assert "placeOrder" not in code
