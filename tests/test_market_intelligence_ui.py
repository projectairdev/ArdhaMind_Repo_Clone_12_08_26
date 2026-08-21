# tests/test_market_intelligence_ui.py
import pytest
import os
import re

WORKSPACE_PATH = "/opt/ardhamind/staging/src/frontend/components/MarketIntelligenceWorkspace.tsx"
MORNING_PLAN_VIEW = "/opt/ardhamind/staging/src/frontend/components/intelligence/MorningPlanView.tsx"
LIVE_GUIDE_VIEW = "/opt/ardhamind/staging/src/frontend/components/intelligence/LiveGuideView.tsx"
TOMORROW_PLAN_VIEW = "/opt/ardhamind/staging/src/frontend/components/intelligence/TomorrowPlanView.tsx"

def test_market_intelligence_workspace_file_exists():
    assert os.path.exists(WORKSPACE_PATH), "MarketIntelligenceWorkspace.tsx must exist"
    assert os.path.exists(MORNING_PLAN_VIEW), "MorningPlanView.tsx must exist"
    assert os.path.exists(LIVE_GUIDE_VIEW), "LiveGuideView.tsx must exist"
    assert os.path.exists(TOMORROW_PLAN_VIEW), "TomorrowPlanView.tsx must exist"

def test_architectural_boundary_no_raw_canonical_property_hunting():
    """Verify that MarketIntelligenceWorkspace.tsx does NOT directly inspect raw canonical state branches in JSX."""
    with open(WORKSPACE_PATH, "r", encoding="utf8") as f:
        content = f.read()

    # Disallowed raw canonical property accesses in JSX/rendering
    disallowed_patterns = [
        r"canonicalState\.market_data",
        r"canonicalState\.options",
        r"canonicalState\.option_intelligence",
        r"canonicalState\.macro_intelligence",
        r"canonicalState\.unified_intelligence",
        r"canonicalState\.marketContext",
        r"canonicalState\.optionContext",
        r"lastValidState\.market_data",
        r"lastValidState\.options",
    ]

    for pattern in disallowed_patterns:
        matches = re.findall(pattern, content)
        assert len(matches) == 0, f"Disallowed raw canonical access found in MarketIntelligenceWorkspace.tsx: {pattern}"

def test_no_legacy_imports():
    """Audit imports in MarketIntelligenceWorkspace.tsx to ensure no legacy adapters or workspace imports exist."""
    with open(WORKSPACE_PATH, "r", encoding="utf8") as f:
        content = f.read()

    forbidden_patterns = [
        r"intelligenceDisplayAdapter",
        r"marketInsightsSessionResolver",
        r"(?<!Market)IntelligenceWorkspace",
        r"MarketInsightsWorkspace",
        r"PrimaryTradeHero",
        r"MarketIntelligenceV2Workspace",
    ]

    for pattern in forbidden_patterns:
        matches = re.findall(pattern, content)
        assert len(matches) == 0, f"Forbidden legacy import/symbol found in MarketIntelligenceWorkspace.tsx: {pattern}"

def test_no_execution_controls():
    """Verify no order execution controls (lot selector, approve, reject, SL, Target) exist in Market Intelligence UI."""
    paths = [WORKSPACE_PATH, MORNING_PLAN_VIEW, LIVE_GUIDE_VIEW, TOMORROW_PLAN_VIEW]

    execution_keywords = [
        "prepareOrderFromSetup",
        "OrderPreviewModal",
        "handleReviewTrade",
        "APPROVE TRADE",
        "REJECT TRADE",
        "lot_size",
        "stop_loss",
    ]

    for p in paths:
        with open(p, "r", encoding="utf8") as f:
            content = f.read()
        for kw in execution_keywords:
            assert kw not in content, f"Execution control found in {p}: {kw}"

def test_session_subtabs_and_preview_present():
    """Verify all 3 dynamic session subtabs and preview dropdown are present in MarketIntelligenceWorkspace."""
    with open(WORKSPACE_PATH, "r", encoding="utf8") as f:
        content = f.read()

    assert "MORNING PLAN" in content
    assert "LIVE GUIDE" in content
    assert "TOMORROW PLAN" in content
    assert "Preview:" in content
    assert 'value="AUTO"' in content
