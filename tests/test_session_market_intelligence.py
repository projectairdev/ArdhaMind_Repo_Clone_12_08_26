# tests/test_session_market_intelligence.py
import pytest
import os
import re
import json
import subprocess

RESOLVER_FILE = "/opt/ardhamind/staging/src/frontend/viewmodels/session/MarketIntelligenceSessionResolver.ts"
BUILDER_FILE = "/opt/ardhamind/staging/src/frontend/viewmodels/session/buildSessionViewModels.ts"
WORKSPACE_FILE = "/opt/ardhamind/staging/src/frontend/components/MarketIntelligenceWorkspace.tsx"
TOMORROW_PLAN_FILE = "/opt/ardhamind/staging/src/frontend/components/intelligence/TomorrowPlanView.tsx"

def test_session_resolver_files_exist():
    assert os.path.exists(RESOLVER_FILE)
    assert os.path.exists(BUILDER_FILE)
    assert os.path.exists(WORKSPACE_FILE)
    assert os.path.exists(TOMORROW_PLAN_FILE)

def test_auto_timing_model_boundaries():
    """Verify exact AUTO timing boundaries specified in prompt."""
    os.makedirs("/opt/ardhamind/staging/dist_test", exist_ok=True)
    dist_path = "/opt/ardhamind/staging/dist_test/MarketIntelligenceSessionResolver.cjs"
    subprocess.run(
        ["npx", "esbuild", RESOLVER_FILE,
         "--bundle", "--platform=node", "--format=cjs", f"--outfile={dist_path}"],
        check=True,
        capture_output=True
    )

    # Test cases in IST: [ISO_UTC_time, expected_stage, expected_subtab]
    test_cases = [
        ("2026-08-21T03:39:59Z", "PREPARING", "MORNING_PLAN"),
        ("2026-08-21T03:40:00Z", "MORNING_PLAN_ACTIVE", "MORNING_PLAN"),
        ("2026-08-21T03:44:58Z", "MORNING_PLAN_ACTIVE", "MORNING_PLAN"),
        ("2026-08-21T03:44:59Z", "LIVE_GUIDE_ACTIVE", "LIVE_GUIDE"),
        ("2026-08-21T09:54:59Z", "LIVE_GUIDE_ACTIVE", "LIVE_GUIDE"),
        ("2026-08-21T09:55:00Z", "LIVE_GUIDE_CLOSING_BUILD", "LIVE_GUIDE"),
        ("2026-08-21T09:59:59Z", "LIVE_GUIDE_CLOSING_BUILD", "LIVE_GUIDE"),
        ("2026-08-21T10:00:00Z", "TOMORROW_PLAN_ACTIVE", "TOMORROW_PLAN"),
        ("2026-08-21T12:00:00Z", "TOMORROW_PLAN_ACTIVE", "TOMORROW_PLAN"),
    ]

    js_code = f"""
const {{ resolveMarketIntelligenceSession }} = require('{dist_path}');
const testCases = {json.dumps(test_cases)};
const results = testCases.map(([utcStr, expStage, expSubTab]) => {{
  const d = new Date(utcStr);
  const res = resolveMarketIntelligenceSession({{ customDate: d }});
  return {{
    utcStr,
    expStage,
    actualStage: res.lifecycleStage,
    expSubTab,
    actualSubTab: res.autoResolvedSubTab,
    pass: res.lifecycleStage === expStage && res.autoResolvedSubTab === expSubTab
  }};
}});
console.log(JSON.stringify(results));
"""
    res = subprocess.run(["node", "-e", js_code], capture_output=True, text=True, check=True)
    results = json.loads(res.stdout)
    for r in results:
        assert r["pass"], f"Timing failed for {r['utcStr']}: Expected ({r['expStage']}, {r['expSubTab']}), got ({r['actualStage']}, {r['actualSubTab']})"

def test_preview_mode_preserves_auto_truth():
    """Verify manual preview mode overrides effective subtab without corrupting autoResolvedSubTab."""
    dist_path = "/opt/ardhamind/staging/dist_test/MarketIntelligenceSessionResolver.cjs"
    js_code = f"""
const {{ resolveMarketIntelligenceSession }} = require('{dist_path}');
const d = new Date("2026-08-21T05:30:00Z");
const autoRes = resolveMarketIntelligenceSession({{ customDate: d, previewMode: 'AUTO' }});
const previewMorning = resolveMarketIntelligenceSession({{ customDate: d, previewMode: 'MORNING_PLAN' }});
const previewTomorrow = resolveMarketIntelligenceSession({{ customDate: d, previewMode: 'TOMORROW_PLAN' }});

console.log(JSON.stringify({{
  autoPass: autoRes.effectiveSubTab === 'LIVE_GUIDE' && autoRes.autoResolvedSubTab === 'LIVE_GUIDE',
  morningPass: previewMorning.effectiveSubTab === 'MORNING_PLAN' && previewMorning.autoResolvedSubTab === 'LIVE_GUIDE',
  tomorrowPass: previewTomorrow.effectiveSubTab === 'TOMORROW_PLAN' && previewTomorrow.autoResolvedSubTab === 'LIVE_GUIDE'
}}));
"""
    res = subprocess.run(["node", "-e", js_code], capture_output=True, text=True, check=True)
    results = json.loads(res.stdout)
    assert results["autoPass"]
    assert results["morningPass"]
    assert results["tomorrowPass"]

def test_data_integrity_and_freshness_rules():
    """Verify sector return normalization, breadth deadband, missing VWAP handling, and closed session freshness labels."""
    dist_path = "/opt/ardhamind/staging/dist_test/buildSessionViewModels.cjs"
    subprocess.run(
        ["npx", "esbuild", BUILDER_FILE,
         "--bundle", "--platform=node", "--format=cjs", f"--outfile={dist_path}"],
        check=True,
        capture_output=True
    )

    js_code = f"""
const {{ normalizeSectorPercent, resolveBreadthBias, buildSessionViewModels }} = require('{dist_path}');

// 1. Sector unit normalization test (+0.0266 -> +2.66%, +2.66 -> +2.66%)
const sec1 = normalizeSectorPercent(0.0266);
const sec2 = normalizeSectorPercent(2.66);
const sec3 = normalizeSectorPercent(266.05);

// 2. Breadth deadband test (25 ADV / 24 DEC / 1 UNCH -> BALANCED)
const breadth1 = resolveBreadthBias(25, 24);
const breadth2 = resolveBreadthBias(35, 15);
const breadth3 = resolveBreadthBias(15, 35);

// 3. Missing VWAP / 0.00 VWAP test
const canonicalNoVwap = {{
  market_data: {{ current_spot: 24238.55, vwap: 0.00 }},
  technical_analysis: {{ vwap: null }}
}};
const vms = buildSessionViewModels(canonicalNoVwap);

// 4. Closed session freshness test (previewing Live Guide outside market hours)
const closedVm = buildSessionViewModels(
  {{ market_session: {{ status: "CLOSED", is_closed: true }}, market_data: {{ current_spot: 24250 }} }},
  {{ isClosedSession: true, previewMode: "LIVE_GUIDE" }}
);

const liveVm = buildSessionViewModels(
  {{ market_session: {{ status: "OPEN", is_closed: false }}, market_data: {{ current_spot: 24250 }} }},
  {{ isClosedSession: false, previewMode: "AUTO" }}
);

console.log(JSON.stringify({{
  sec1, sec2, sec3,
  breadth1, breadth2, breadth3,
  vwapMorning: vms.morningPlan.yesterdaysInfo.vwap,
  vwapLive: vms.liveGuide.currentMarketState.vwapStatus,
  strikeAvailability: vms.tomorrowPlan.bestStrikeSuggestions[0].availability,
  closedFreshness: closedVm.liveGuide.liveMetrics.freshnessLabel,
  closedIsLive: closedVm.liveGuide.liveMetrics.isLive,
  liveFreshness: liveVm.liveGuide.liveMetrics.freshnessLabel,
  liveIsLive: liveVm.liveGuide.liveMetrics.isLive
}}));
"""
    res = subprocess.run(["node", "-e", js_code], capture_output=True, text=True, check=True)
    results = json.loads(res.stdout)

    assert results["sec1"] == 2.66
    assert results["sec2"] == 2.66
    assert results["breadth1"] == "BALANCED"
    assert results["breadth2"] == "POSITIVE"
    assert results["breadth3"] == "NEGATIVE"
    assert results["vwapMorning"] == "UNAVAILABLE"
    assert results["vwapLive"] == "UNAVAILABLE"
    assert results["strikeAvailability"] == "UNAVAILABLE"
    assert results["closedFreshness"] == "PREVIEW", f"Expected PREVIEW freshness, got {results['closedFreshness']}"
    assert not results["closedIsLive"], "Closed session must have isLive=false"
    assert results["liveFreshness"] == "LIVE", f"Expected LIVE freshness, got {results['liveFreshness']}"
    assert results["liveIsLive"], "Live session must have isLive=true"

def test_tomorrow_plan_compact_tables_and_matrix():
    """Verify Tomorrow Plan uses compact grid/matrix layouts instead of tall vertical lists."""
    with open(TOMORROW_PLAN_FILE, "r", encoding="utf8") as f:
        content = f.read()

    # Overview must use grid structure
    assert "grid grid-cols-3 sm:grid-cols-6" in content, "Today's Market Overview must use 6-column grid"
    assert "Day Range" in content, "Today's Market Overview must expose Day Range cell"

    # Critical levels must use matrix grid
    assert "grid grid-cols-3 gap-1.5" in content, "Critical levels must use 3-column matrix rows"
    assert "Carry-Forward" in content, "Critical levels must display Carry-Forward cell"

def test_workspace_density_and_no_redundant_padding():
    """Verify MarketIntelligenceWorkspace has no excess outer padding or max-width container."""
    with open(WORKSPACE_FILE, "r", encoding="utf8") as f:
        content = f.read()

    assert "max-w-[1920px]" not in content, "Redundant max-w-[1920px] should be removed"
    assert 'className="space-y-2.5 font-sans text-left text-[#E6E8EB]"' in content, "Must use standard compact workspace wrapper"

def test_zero_execution_controls_across_all_views():
    """Verify zero order execution controls or modals exist across all Market Intelligence components."""
    paths = [
        WORKSPACE_FILE,
        "/opt/ardhamind/staging/src/frontend/components/intelligence/MorningPlanView.tsx",
        "/opt/ardhamind/staging/src/frontend/components/intelligence/LiveGuideView.tsx",
        TOMORROW_PLAN_FILE,
    ]

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
