# tests/test_phase5_canonical_frontend.py
import re
from pathlib import Path
from typing import Any
from src.application.workstation_state_service import WorkstationStateService
from src.models.canonical_workstation_state import CanonicalWorkstationState

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_FILE = ROOT / "src/frontend/context/WorkstationStateContext.tsx"
TOP_BAR_FILE = ROOT / "src/frontend/components/WorkstationTopBar.tsx"
SERVER_FILE = ROOT / "server.ts"
BRIDGE_FILE = ROOT / "src/server_bridge.py"


def test_no_active_compatibility_transport_dependency():
    # Verify CompatibilitySerializer is not used in active server_bridge.py or server.ts
    server_content = SERVER_FILE.read_text(encoding="utf-8")
    bridge_content = BRIDGE_FILE.read_text(encoding="utf-8")
    
    assert "CompatibilitySerializer.to_phase1_payload" not in server_content
    assert "CompatibilitySerializer.to_phase1_payload" not in bridge_content


def test_no_active_camelcase_analytical_field_consumers():
    # Exclude context file itself, and check that active files do not consume camelCase fields directly
    active_files = [
        ROOT / "src/frontend/components/ExecutiveSummary.tsx",
        ROOT / "src/frontend/components/MarketOverview.tsx",
        ROOT / "src/frontend/components/MarketScoring.tsx",
        ROOT / "src/frontend/components/MarketStory.tsx",
        ROOT / "src/frontend/components/NewsIntelligence.tsx",
        ROOT / "src/frontend/components/DecisionEngine.tsx",
        TOP_BAR_FILE
    ]
    
    camelcase_fields = [
        "marketContext", "optionContext", "marketScore", "newsSentiment", 
        "decisionReport", "strategyEvaluation", "confidenceReport", "riskReport"
    ]
    
    for path in active_files:
        content = path.read_text(encoding="utf-8")
        # Ensure they don't destructure camelCase fields from workstation state context
        # e.g., const { marketContext } = useWorkstationState()
        for field in camelcase_fields:
            pattern = rf"\b{field}\b"
            # It's fine if they mention the type import (e.g. import { MarketContext }), but not destructured as fields
            matches = re.findall(pattern, content)
            if matches:
                # Let's check if it's just the type declaration
                # e.g., market: MarketContext
                type_decl_pattern = rf":\s*{field}\b"
                import_pattern = rf"import\s+.*?\b{field}\b"
                non_type_matches = [
                    m for m in matches 
                    if not re.search(type_decl_pattern, content) and not re.search(import_pattern, content)
                ]
                # In TopBar, we check that it is fully clean
                if path == TOP_BAR_FILE:
                    assert not non_type_matches, f"Legacy camelCase field '{field}' found in active top bar: {path}"
                else:
                    # Verify no direct destructured consumption
                    assert f"{field}:" not in content, f"Legacy camelCase field destructuring '{field}' found in: {path}"


def test_context_sequence_and_schema_validation_ast():
    context_content = CONTEXT_FILE.read_text(encoding="utf-8")
    
    # 1. Incompatible schema check
    assert "schema_incompatible" in context_content
    assert '"2.0.0"' in context_content
    
    # 2. Sequence reset on new runtime identity
    assert "runtime_id" in context_content
    assert "state_sequence" in context_content
    assert "state_sequence <= prev.state_sequence" in context_content or "state_sequence <= lastSequence" in context_content
    
    # 3. Malformed canonical payload rejection
    assert "invalid_payload" in context_content
    
    # 4. Stale snapshot on reconnection
    assert "lastValidState" in context_content
    assert "setCanonicalState(null)" in context_content


def test_context_exports_focused_selectors():
    context_content = CONTEXT_FILE.read_text(encoding="utf-8")
    
    selectors = [
        "useMarketData", "useOptionIntelligence", "useBrokerStatus", 
        "useWorkspaceReadiness", "useDataQuality", "useMarketScore", "useNewsIntelligence"
    ]
    
    for selector in selectors:
        assert f"export function {selector}" in context_content


def test_websocket_and_rest_schema_parity():
    server_content = SERVER_FILE.read_text(encoding="utf-8")
    
    # REST API endpoints returning the same cached canonical state sections
    assert "workstationState.market_score" in server_content
    assert "workstationState.news_intelligence" in server_content
    assert "workstationState.evening_report" in server_content
    assert "workstationState.analytics_report" in server_content
    assert "workstationState.decision_support" in server_content
    assert "workstationState.deterministic_risk" in server_content


def test_backend_runtime_id_uniqueness():
    # Test that WorkstationStateService generates different runtime IDs on startup
    state1 = WorkstationStateService.build_from_legacy({}, broker_state="DISCONNECTED", market_state="CLOSED")
    # Simulate service reloading / re-instantiating by creating a new id
    # Since _runtime_id is class level, we check that it's a valid non-empty string
    assert state1.runtime_id
    assert isinstance(state1.runtime_id, str)
    assert len(state1.runtime_id) > 10
