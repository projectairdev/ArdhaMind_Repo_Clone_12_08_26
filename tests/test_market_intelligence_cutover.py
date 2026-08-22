# tests/test_market_intelligence_cutover.py
import pytest
import os
import re
import subprocess
import tempfile
import json

DASHBOARD_LAYOUT = "/opt/ardhamind/staging/src/frontend/layout/DashboardLayout.tsx"
NAV_CONTEXT = "/opt/ardhamind/staging/src/frontend/context/NavigationContext.tsx"

def test_primary_sidebar_modules_consolidated():
    """Verify PRIMARY_MODULES in DashboardLayout contains exactly the 6 official modules."""
    with open(DASHBOARD_LAYOUT, "r", encoding="utf8") as f:
        content = f.read()

    # Must contain MARKET INTELLIGENCE
    assert '{ id: "market_intelligence", label: "MARKET INTELLIGENCE", glyph: IntelligenceGlyph }' in content

    # Must NOT contain legacy separate INTELLIGENCE and MARKET INSIGHTS
    assert '{ id: "intelligence", label: "INTELLIGENCE"' not in content
    assert '{ id: "pre_market_briefing", label: "MARKET INSIGHTS"' not in content

def test_legacy_dead_files_retired():
    """Verify retired legacy files have been deleted."""
    retired_paths = [
        "/opt/ardhamind/staging/src/frontend/components/IntelligenceWorkspace.tsx",
        "/opt/ardhamind/staging/src/frontend/components/MarketInsightsWorkspace.tsx",
        "/opt/ardhamind/staging/src/frontend/components/PreMarketBriefingWorkspace.tsx",
        "/opt/ardhamind/staging/src/frontend/components/AIOpportunitiesWorkspace.tsx",
        "/opt/ardhamind/staging/src/frontend/components/MarketIntelligenceV2Workspace.tsx",
        "/opt/ardhamind/staging/src/frontend/utils/intelligenceDisplayAdapter.ts",
        "/opt/ardhamind/staging/src/frontend/utils/marketInsightsSessionResolver.ts",
    ]

    for p in retired_paths:
        assert not os.path.exists(p), f"Retired file still exists: {p}"

def test_legacy_saved_module_migration():
    """Test the normalizeModuleId function using Node with esbuild bundle."""
    os.makedirs("/opt/ardhamind/staging/dist_test", exist_ok=True)
    dist_path = "/opt/ardhamind/staging/dist_test/NavigationContext.cjs"
    subprocess.run(
        ["npx", "esbuild", "src/frontend/context/NavigationContext.tsx",
         "--bundle", "--platform=node", "--format=cjs", f"--outfile={dist_path}"],
        check=True,
        capture_output=True
    )

    cases = [
        # Case A: Saved module "intelligence" -> "market_intelligence"
        ("intelligence", "market_intelligence"),
        # Case B: Saved module "market_insights" -> "market_intelligence"
        ("market_insights", "market_intelligence"),
        ("pre_market_briefing", "market_intelligence"),
        # Case C: Saved module "market_intelligence_v2" -> "market_intelligence"
        ("market_intelligence_v2", "market_intelligence"),
        # Canonical "market_intelligence" remains "market_intelligence"
        ("market_intelligence", "market_intelligence"),
        # Other valid modules remain unchanged
        ("market", "market"),
        ("news", "news"),
        ("portfolio", "portfolio"),
        ("trading_cheatsheet", "market"),
        ("ardha_performance", "settings"),
        ("settings", "settings"),
        # Case D: Unknown / invalid -> "market"
        ("unknown_invalid_key", "market"),
        ("", "market"),
        (None, "market"),
    ]

    js_code = f"""
const {{ normalizeModuleId }} = require('{dist_path}');
const testCases = {json.dumps(cases)};
const results = testCases.map(([input, expected]) => {{
  const output = normalizeModuleId(input);
  return {{ input, expected, output, pass: output === expected }};
}});
console.log(JSON.stringify(results));
"""
    res = subprocess.run(["node", "-e", js_code], capture_output=True, text=True, check=True)
    results = json.loads(res.stdout)
    for r in results:
        assert r["pass"], f"Migration failed for input {r['input']}: expected {r['expected']}, got {r['output']}"
