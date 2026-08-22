# tests/test_temporal_provenance_sync.py
"""
Test suite for Dashboard-Wide Temporal Provenance & Session Context Sync.
"""

from pathlib import Path
import pytest

from src.application.workstation_state_service import WorkstationStateService


def read(rel_path: str) -> str:
    return Path(rel_path).read_text(encoding="utf-8")


def test_temporal_session_resolver_utility_exists():
    path = Path("src/frontend/utils/temporalSessionResolver.ts")
    assert path.exists()
    code = path.read_text(encoding="utf-8")
    assert "getTemporalSessionContext" in code
    assert "formatDateIST" in code
    assert "formatTimeIST" in code
    assert "formatFullIST" in code
    assert "NSE_HOLIDAYS_2026" in code
    assert "getNextTradingDay" in code
    assert "getPreviousTradingDay" in code


def test_temporal_context_strip_component_exists():
    path = Path("src/frontend/components/ui/TemporalContextStrip.tsx")
    assert path.exists()
    code = path.read_text(encoding="utf-8")
    assert "TemporalContextStrip" in code
    assert "Last Valid Session:" in code
    assert "Next Session:" in code
    assert "Validated:" in code


def test_nifty_workspace_renders_temporal_strip_and_date_labels():
    code = read("src/frontend/components/NiftyLiveWorkspace.tsx")
    assert "TemporalContextStrip" in code
    assert "OPENING BIAS (" in code
    assert "EXPECTED NEXT-SESSION OPEN" in code
    assert "LATEST GIFT NIFTY OBSERVATION" in code
    assert "INSTITUTIONAL POSITIONING · Cash Market (" in code
    assert "Reference Close (" in code


def test_market_pulse_workspace_renders_temporal_strip():
    code = read("src/frontend/components/MarketPulseWorkspace.tsx")
    assert "TemporalContextStrip" in code
    assert 'customTitle="Market Metrics & Benchmark Telemetry"' in code


def test_options_workspace_renders_temporal_strip():
    code = read("src/frontend/components/OptionsWorkspace.tsx")
    assert "TemporalContextStrip" in code
    assert 'customTitle="NIFTY Derivatives & Option Chain Telemetry"' in code


def test_unified_intelligence_panel_renders_temporal_strip():
    code = read("src/frontend/components/UnifiedIntelligencePanel.tsx")
    assert "TemporalContextStrip" in code


def test_market_intelligence_workspace_renders_temporal_strip():
    code = read("src/frontend/components/MarketIntelligenceWorkspace.tsx")
    assert "TemporalContextStrip" in code


def test_news_workspace_renders_temporal_strip():
    code = read("src/frontend/components/news/NewsWorkspace.tsx")
    assert "TemporalContextStrip" in code


def test_workstation_state_service_publishes_valid_session_metadata():
    service_state = WorkstationStateService.build_from_legacy(
        {},
        broker_state="CONNECTED",
        market_state="POST_CLOSE"
    ).to_dict()

    assert service_state["schema_version"] == "2.0.0"
    assert "market_session" in service_state
    assert "runtime_id" in service_state
    assert "state_sequence" in service_state


def test_market_pulse_workspace_has_no_undeclared_state_obj_references():
    code = read("src/frontend/components/MarketPulseWorkspace.tsx")
    assert "stateObj" not in code
    assert "canonicalState={state}" in code
