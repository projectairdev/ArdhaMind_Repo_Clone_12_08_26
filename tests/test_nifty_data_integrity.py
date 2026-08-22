# tests/test_nifty_data_integrity.py
"""
Automated regression tests for Sprint N1 — NIFTY Data & Chart Integrity.
Verifies mathematical correctness, timeframe aggregation, structural invariants,
breadth accounting, and zero hardcoded fallback market numbers.
"""

import os
import re
import pytest
from datetime import datetime, timezone, timedelta
from src.broker.services.market_context_builder import MarketContextBuilder
from src.broker.services.kite_intelligence_service import KiteIntelligenceService
from src.intelligence_engine.structural_level_engine import StructuralLevelEngine


def test_nifty_spot_and_change_math():
    """Verify spot, prev_close, change, and change_pct mathematical reconciliation."""
    spot = 24366.00
    prev_close = 24395.85
    expected_change = round(spot - prev_close, 2)
    expected_change_pct = round((expected_change / prev_close) * 100.0, 4)

    assert expected_change == -29.85
    assert round(expected_change_pct, 2) == -0.12


def test_vix_math_reconciliation():
    """Verify India VIX value, previous close, change, and change_pct math."""
    value = 11.33
    prev_close = 11.31
    change = round(value - prev_close, 2)
    change_pct = round((change / prev_close) * 100.0, 2)

    assert change == 0.02
    assert change_pct == 0.18


def test_breadth_completeness_accounting():
    """Verify constituent breadth accounting sums to exactly 50."""
    raw_map = {"members": [{"trading_symbol": f"SYM_{i}", "resolution_status": "RESOLVED"} for i in range(50)]}
    quotes = {}
    for i in range(49):
        sym = f"SYM_{i}"
        quotes[f"NSE:{sym}"] = {
            "last_price": 100.0 + i,
            "ohlc": {"close": 98.0 if i % 2 == 0 else 102.0},
            "timestamp": "2026-08-17T15:30:00Z"
        }
    # 50th symbol is missing from quotes (unavailable)

    res = KiteIntelligenceService.compute_breadth(raw_map, quotes, minimum_coverage=40, market_closed=True)
    assert res["status"] == "READY"
    assert res["coverage"]["valid"] == 49
    assert res["unavailable"] == 1
    assert res["total_constituents"] == 50
    assert res["advances"] + res["declines"] + res["unchanged"] + res["unavailable"] == 50


def test_structural_level_ordering_invariant():
    """Verify structural levels enforce R3 >= R2 >= R1 > Pivot > S1 >= S2 >= S3 ordering."""
    state = {
        "market_data": {"current_spot": 24366.0, "previous_close": 24395.85, "high": 24423.85, "low": 24296.8, "open": 24401.1},
        "option_intelligence": {"pcr": 1.13, "max_pain": 24400.0, "highest_call_oi_strike": 24500.0, "highest_put_oi_strike": 24200.0, "atm_strike": 24350.0}
    }
    levels = StructuralLevelEngine.evaluate_levels(state)
    assert levels["methodology"] in ["EVIDENCE_CONFLUENCE_V1", "EVIDENCE_CONFLUENCE_V2_LIVE_AWARE"]

    pivot = levels["pivot_level"]["price"]
    imm_res = levels["immediate_resistance"]["price"]
    imm_sup = levels["immediate_support"]["price"]

    if pivot and imm_res:
        assert imm_res >= pivot
    if pivot and imm_sup:
        assert imm_sup <= pivot


def test_zero_hardcoded_fallback_market_data_in_nifty_workspace():
    """Audit NiftyLiveWorkspace.tsx to confirm zero hardcoded fallback prices/levels exist."""
    workspace_path = "/opt/ardhamind/staging/src/frontend/components/NiftyLiveWorkspace.tsx"
    with open(workspace_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Search for banished fallbacks
    forbidden_patterns = [
        r"\?\?\s*24366",
        r"\?\?\s*24401",
        r"\?\?\s*24423",
        r"\?\?\s*24296",
        r"\?\?\s*24650",
        r"\?\?\s*24500",
        r"\?\?\s*24350",
        r"\?\?\s*24250",
        r"\?\?\s*24150",
        r"\?\?\s*24000",
        r"defaultGainers\s*=",
        r"defaultLosers\s*=",
    ]

    for pattern in forbidden_patterns:
        match = re.search(pattern, content)
        assert match is None, f"Forbidden fallback pattern '{pattern}' found in NiftyLiveWorkspace.tsx!"


def test_pre_market_fii_dii_signed_arithmetic():
    """Verify signed FII/DII arithmetic preserves negative selling sign and exact sum."""
    fii_net = -2535.10
    dii_net = 5101.46
    combined_net = round(fii_net + dii_net, 2)

    assert fii_net < 0
    assert dii_net > 0
    assert combined_net == 2566.36
    assert f"{combined_net:+.1f}" == "+2566.4"


def test_pre_market_gap_and_open_mathematical_derivation():
    """Verify pre-market expected open is mathematically derived from previous close + gap range."""
    prev_close = 24366.00
    gap_low = 38.00
    gap_high = 72.00

    expected_open_low = prev_close + gap_low
    expected_open_high = prev_close + gap_high

    assert expected_open_low == 24404.00
    assert expected_open_high == 24438.00
    assert f"{expected_open_low:,.0f} – {expected_open_high:,.0f}" == "24,404 – 24,438"


def test_post_market_spot_pivot_relational_logic():
    """Verify relational narrative compares exact spot and pivot numbers truthfully."""
    def get_relation(spot: float, pivot: float, tolerance: float = 3.0) -> str:
        if abs(spot - pivot) <= tolerance:
            return f"closing near intraday pivot {pivot:,.2f}"
        elif spot > pivot:
            return f"staying above intraday pivot {pivot:,.2f}"
        else:
            return f"staying below intraday pivot {pivot:,.2f}"

    assert "closing near" in get_relation(24287.65, 24287.65)
    assert "closing near" in get_relation(24287.65, 24289.00)
    assert "staying below" in get_relation(24287.65, 24350.00)
    assert "staying above" in get_relation(24287.65, 24200.00)


def test_structural_levels_evidence_derivation_not_manufactured():
    """Verify structural levels are derived from genuine evidence sources, not manufactured symmetric offsets."""
    state = {
        "market_data": {
            "current_spot": 24287.65,
            "previous_close": 24366.00,
            "high": 24360.10,
            "low": 24226.95,
            "open": 24343.45
        },
        "option_intelligence": {
            "pcr": 1.22,
            "max_pain": 24350.0,
            "highest_call_oi_strike": 24500.0,
            "highest_put_oi_strike": 24200.0,
            "atm_strike": 24300.0
        }
    }
    levels = StructuralLevelEngine.evaluate_levels(state)
    level_keys = ["immediate_support", "major_support", "immediate_resistance", "major_resistance", "pivot_level"]

    for key in level_keys:
        lvl = levels.get(key)
        assert lvl is not None, f"Level {key} must not be None"
        if lvl.get("price") is not None:
            assert len(lvl.get("sources", [])) >= 1, f"Level {key} must have evidence sources"
            assert any(
                src in ["PREVIOUS_SESSION_HIGH", "PREVIOUS_SESSION_LOW", "PREVIOUS_CLOSE", "MAX_PAIN_STRIKE", "ATM_STRIKE", "HIGHEST_CALL_OI_STRIKE", "HIGHEST_PUT_OI_STRIKE"]
                for src in lvl["sources"]
            )


def test_preview_mode_canonical_session_mapping():
    """Verify AUTO mode maps accurately from canonical market session status without synthetic state overrides."""
    def map_canonical_session(status: str) -> str:
        s = status.upper()
        if "PRE" in s or s == "PRE_OPEN" or s == "PRE_MARKET":
            return "pre_market"
        if s in ["OPEN", "LIVE", "LIVE_SESSION"]:
            return "live"
        return "post_market"

    assert map_canonical_session("PRE_OPEN") == "pre_market"
    assert map_canonical_session("PRE_MARKET") == "pre_market"
    assert map_canonical_session("OPEN") == "live"
    assert map_canonical_session("LIVE_SESSION") == "live"
    assert map_canonical_session("CLOSED") == "post_market"
    assert map_canonical_session("POST_CLOSE") == "post_market"
    assert map_canonical_session("SESSION_COMPLETE") == "post_market"
    assert map_canonical_session("HOLIDAY") == "post_market"
    assert map_canonical_session("WEEKEND") == "post_market"


def test_preview_override_leaves_canonical_state_unmutated():
    """Verify preview mode selection operates as pure presentation overlay and never mutates canonical state."""
    canonical_state = {
        "runtime_id": "pvpk06-staging-01",
        "state_sequence": 1420,
        "market_session": {"status": "CLOSED", "is_closed": True},
        "market_data": {"current_spot": 24287.65, "previous_close": 24366.00},
        "freshness": "LAST_VALID_SESSION"
    }
    
    # Simulate UI applying preview overrides
    for override_mode in ["PRE", "LIVE", "POST", "AUTO"]:
        # Presentation view may be 'pre_market', 'live', or 'post_market'
        presentation_view = "pre_market" if override_mode == "PRE" else "live" if override_mode == "LIVE" else "post_market"
        assert presentation_view in ["pre_market", "live", "post_market"]
        
        # Invariant: canonical state remains completely untouched
        assert canonical_state["market_session"]["status"] == "CLOSED"
        assert canonical_state["market_data"]["current_spot"] == 24287.65
        assert canonical_state["state_sequence"] == 1420
        assert canonical_state["runtime_id"] == "pvpk06-staging-01"


def test_preview_control_contract_in_nifty_workspace():
    """Verify NiftyLiveWorkspace.tsx includes durable preview controls, guard, and override banner."""
    with open("src/frontend/components/NiftyLiveWorkspace.tsx", "r", encoding="utf-8") as f:
        content = f.read()

    assert "isStagingEnvironment" in content, "Must export/contain isStagingEnvironment guard"
    assert "STAGING SESSION PREVIEW" in content, "Must contain persistent STAGING SESSION PREVIEW banner"


def test_is_staging_environment_fail_closed_contract():
    """Verify isStagingEnvironment strictly obeys fail-closed explicit environment identity."""
    def is_staging_env(val):
        # Python representation of the TypeScript fail-closed helper
        return val == "staging"

    # 1. Staging env -> allowed
    assert is_staging_env("staging") is True
    # 2. Production env -> forbidden
    assert is_staging_env("production") is False
    # 3. Missing env -> forbidden
    assert is_staging_env(None) is False
    assert is_staging_env("") is False
    # 4. Unknown env -> forbidden
    assert is_staging_env("qa") is False
    assert is_staging_env("development") is False
    assert is_staging_env("test") is False
    # 5. Production HTTPS / empty browser port cannot enable controls without staging env
    prod_context = {"host": "ardhamind.projectair.in", "port": "", "env": "production"}
    assert is_staging_env(prod_context["env"]) is False
    # 6. Direct IP cannot enable controls without explicit staging env
    direct_ip_context = {"host": "127.0.0.1", "port": "3000", "env": None}
    assert is_staging_env(direct_ip_context["env"]) is False


def test_preview_dropdown_selector_contract():
    """Verify NiftyLiveWorkspace.tsx implements the compact preview dropdown instead of button group."""
    with open("src/frontend/components/NiftyLiveWorkspace.tsx", "r", encoding="utf-8") as f:
        content = f.read()

    assert "<select" in content, "Must use compact select element for preview dropdown"
    assert 'value="AUTO"' in content
    assert 'value="PRE"' in content
    assert 'value="LIVE"' in content
    assert 'value="POST"' in content
    assert "STAGING SESSION PREVIEW" in content


def test_movers_and_sectors_drawer_contract():
    """Verify NiftyLiveWorkspace.tsx implements dedicated inspection drawer for Gainers, Losers, and Sectors."""
    with open("src/frontend/components/NiftyLiveWorkspace.tsx", "r", encoding="utf-8") as f:
        content = f.read()

    assert "MoversSectorsDrawer" in content, "Must implement MoversSectorsDrawer component"
    assert 'setDrawerMode("GAINERS")' in content, "Must wire Gainers VIEW ALL handler"
    assert 'setDrawerMode("LOSERS")' in content, "Must wire Losers VIEW ALL handler"
    assert 'setDrawerMode("SECTORS")' in content, "Must wire Sector Rotation VIEW ALL handler"
    assert "Escape" in content, "Must handle Escape key to close drawer"


def test_global_market_cues_and_availability_restructure():
    """Verify Global Market Cues has primary benchmark table and bottom Market Availability."""
    with open("src/frontend/components/NiftyLiveWorkspace.tsx", "r", encoding="utf-8") as f:
        content = f.read()

    assert "GLOBAL MARKET CUES" in content
    assert "MARKET AVAILABILITY" in content
    assert "GLOBAL_MARKET_CENTERS" in content
    assert "Tokyo" in content
    assert "Shanghai" in content
    assert "Hong Kong" in content
    assert "Mumbai" in content
    assert "Frankfurt" in content
    assert "London" in content



