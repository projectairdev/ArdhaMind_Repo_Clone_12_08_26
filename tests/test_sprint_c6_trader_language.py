from pathlib import Path
import pytest

ROOT = Path("src")

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_nifty_live_strip_removed():
    text = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "<NiftyIntelligenceStrip" not in text
    assert "<OverviewPanel />" in text


def test_normal_ui_no_canonical_quality():
    text = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "Canonical quality" not in text
    assert "NIFTY 50" in text
    assert "Previous Session" in text


def test_normal_ui_no_kite_historical_api():
    text = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert 'Source: kite_historical_api' not in text
    assert 'dq.source === "kite_historical_api" ? "Kite Historical API"' in text


def test_normal_ui_no_unified_engine_id():
    changed_files = [
        "frontend/components/NiftyLiveWorkspace.tsx",
        "frontend/components/PhaseOneWorkspaces.tsx",
        "frontend/components/PreMarketPlannerWorkspace.tsx",
        "frontend/components/UnifiedIntelligencePanel.tsx",
        "frontend/components/NewsIntelligence.tsx"
    ]
    for rel_path in changed_files:
        content = read(rel_path)
        assert "UNIFIED_NIFTY_INTELLIGENCE_V1" not in content


def test_last_valid_session_trader_language():
    mapping = read("frontend/utils/traderTerminology.ts")
    assert "Previous Trading Session" in mapping


def test_market_closed_human_readable():
    mapping = read("frontend/utils/traderTerminology.ts")
    assert '"MARKET_CLOSED": "Market Closed"' in mapping
    assert "Market Closed" in mapping


def test_premarket_subtitle_no_canonical_inputs():
    text = read("frontend/components/PreMarketPlannerWorkspace.tsx")
    assert "Three purpose-specific preparation views backed by canonical inputs." not in text
    # C.8.1 replaced the static subtitle with TomorrowsOutlookCard rendering
    # the trader-facing outlook directly — verify trader-facing structure exists
    assert "TomorrowsOutlookCard" in text


def test_centralized_terminology_mapping():
    mapping_file = ROOT / "frontend/utils/traderTerminology.ts"
    assert mapping_file.exists()
    content = mapping_file.read_text(encoding="utf-8")
    assert "export function mapTraderEnum" in content
    assert "CONFLICTED" in content and "Mixed Signals" in content
    assert "UNCERTAIN" in content and "No Clear Direction" in content
    assert "ELEVATED" in content and "Higher Risk" in content


def test_context_sensitive_terminology():
    mapping = read("frontend/utils/traderTerminology.ts")
    assert 'if (domain === "confidence")' in mapping
    assert '"Low Conviction"' in mapping
    assert '"High Conviction"' in mapping
    assert 'if (domain === "risk")' in mapping
    assert '"Low Risk"' in mapping
    assert '"High Risk"' in mapping
    assert 'if (domain === "impact" || domain === "importance")' in mapping
    assert '"Low Impact"' in mapping
    assert '"High Impact"' in mapping


def test_semantic_distinctions_and_professional_positioning():
    mapping = read("frontend/utils/traderTerminology.ts")
    assert '"Evidence Coverage"' in mapping
    assert '"Short Positioning Dominant"' in mapping
    assert '"Long Positioning Dominant"' in mapping
    assert '"Net Short Bias"' in mapping
    assert '"Positive Global Cues"' in mapping
    assert '"Risk-On Environment"' in mapping
    assert '"Weak Global Cues"' in mapping
    assert '"Risk-Off Environment"' in mapping


def test_technical_diagnostics_retain_internal_identifiers():
    settings = read("frontend/components/SettingsDashboard.tsx")
    assert "schema_version" in settings
    assert "runtime_id" in settings
    assert "Export Diagnostics" in settings


def test_trader_formatting_preserves_numeric_values():
    helpers = read("frontend/utils/safeHelpers.ts")
    assert "formatNumber" in helpers
    assert "safeNumber" in helpers
    assert "Number(val)" in helpers


def test_distinct_readiness_semantics():
    mapping = read("frontend/utils/traderTerminology.ts")
    assert "NOT_CONFIGURED" in mapping and "Not Configured" in mapping
    assert "LICENSE_REQUIRED" in mapping and "Licensed Data Required" in mapping
    assert "UNAVAILABLE" in mapping and "Unavailable" in mapping


def test_financial_terminology_intact():
    nifty = read("frontend/components/NiftyLiveWorkspace.tsx")
    story = read("frontend/components/MarketStory.tsx")
    assert "PCR / Max Pain" in nifty
    assert "ATM Option IV" in nifty
    assert "VWAP" in nifty
    assert "EMA 20 / 50" in nifty
    assert "India VIX" in story or "VIX" in nifty
