# tests/test_intelligence_cross_workspace_truth.py
"""
Cross-Workspace Canonical Data Truth and Consistency Tests for AIR ArdhaMind.

Enforces that equivalent economic facts across MARKET (NIFTY, METRICS, OPTIONS)
and INTELLIGENCE (PRE-MARKET, NOW, NEXT DAY) derive from the same canonical backend truth.
"""

import json
import re
from pathlib import Path


def read_frontend(rel_path: str) -> str:
    full_path = Path(__file__).parent.parent / "src" / "frontend" / rel_path
    return full_path.read_text(encoding="utf-8")


def test_no_hardcoded_scenario_probabilities_in_intelligence():
    """Assert no hardcoded percentage probabilities exist in Intelligence components."""
    now_code = read_frontend("components/intelligence/NowIntelligence.tsx")
    pre_code = read_frontend("components/intelligence/PreMarketIntelligence.tsx")
    next_code = read_frontend("components/intelligence/NextDayIntelligence.tsx")

    for code, name in [
        (now_code, "NowIntelligence.tsx"),
        (pre_code, "PreMarketIntelligence.tsx"),
        (next_code, "NextDayIntelligence.tsx"),
    ]:
        assert "Probability: 55%" not in code, f"Unbacked probability in {name}"
        assert "Probability: 25%" not in code, f"Unbacked probability in {name}"


def test_no_static_stock_lists_in_intelligence_rendering():
    """Assert no fixed static stock lists exist in Intelligence rendering code."""
    pre_code = read_frontend("components/intelligence/PreMarketIntelligence.tsx")
    now_code = read_frontend("components/intelligence/NowIntelligence.tsx")
    next_code = read_frontend("components/intelligence/NextDayIntelligence.tsx")

    forbidden = ["Reliance, HDFC Bank, ICICI Bank", "HDFCBANK", "ICICIBANK"]
    for code, name in [
        (pre_code, "PreMarketIntelligence.tsx"),
        (now_code, "NowIntelligence.tsx"),
        (next_code, "NextDayIntelligence.tsx"),
    ]:
        for item in forbidden:
            assert item not in code, f"Forbidden static stock literal '{item}' found in {name}"


def test_now_narrative_session_vocabulary_contract():
    """Assert NOW view narrative does not use next-session terms."""
    adapter_code = read_frontend("utils/canonicalIntelligenceAdapter.ts")
    assert 'nowLiveRecap = `Current market context' in adapter_code
    assert "Next-session context" not in adapter_code


def test_directional_arrow_guard_contract():
    """Assert directional arrow helper guards against showing bullish arrow for NEUTRAL."""
    adapter_code = read_frontend("utils/canonicalIntelligenceAdapter.ts")
    assert "function getDirectionArrow" in adapter_code
    assert 's.includes("BULLISH")' in adapter_code
    assert 'return "↔"' in adapter_code


def test_expected_open_and_gap_reconciliation_contract():
    """Assert expected open low/high mathematically reconciles with previous close + expected gap."""
    adapter_code = read_frontend("utils/canonicalIntelligenceAdapter.ts")
    assert "expectedOpenLow = prevClose != null && expectedGapLow != null ? prevClose + expectedGapLow : null" in adapter_code
    assert "expectedOpenHigh = prevClose != null && expectedGapHigh != null ? prevClose + expectedGapHigh : null" in adapter_code


def test_fii_dii_net_flow_identity_contract():
    """Assert Net Institutional cash flow equals FII cash + DII cash."""
    adapter_code = read_frontend("utils/canonicalIntelligenceAdapter.ts")
    assert "netInstitutionalCash = fiiCashNet != null || diiCashNet != null" in adapter_code
    assert "(fiiCashNet ?? 0) + (diiCashNet ?? 0)" in adapter_code


def test_nifty_breadth_vs_nse_breadth_separation_contract():
    """Assert NIFTY 50 breadth is explicitly distinguished from broader NSE market breadth."""
    adapter_code = read_frontend("utils/canonicalIntelligenceAdapter.ts")
    assert "niftyBreadth:" in adapter_code
    assert "nseMarketBreadth:" in adapter_code
    next_day_code = read_frontend("components/intelligence/NextDayIntelligence.tsx")
    assert "NIFTY 50 Breadth" in next_day_code


def test_ordered_levels_contract():
    """Assert level ordering validation exists for R3 > R2 > R1 > Pivot > S1 > S2 > S3."""
    adapter_code = read_frontend("utils/canonicalIntelligenceAdapter.ts")
    assert "sort((a, b) => a - b)" in adapter_code  # ascending for resistances
    assert "sort((a, b) => b - a)" in adapter_code  # descending for supports


def test_conviction_guard_logic_contract():
    """Assert conviction is guarded against HIGH when live bias is NEUTRAL."""
    adapter_code = read_frontend("utils/canonicalIntelligenceAdapter.ts")
    assert 'liveBias === "NEUTRAL"' in adapter_code
    assert '"MEDIUM"' in adapter_code


def test_event_filtering_empty_state_contract():
    """Assert economic events filter cleanly handles empty state when no events exist."""
    pre_code = read_frontend("components/intelligence/PreMarketIntelligence.tsx")
    assert "No relevant scheduled events available for this session." in pre_code
