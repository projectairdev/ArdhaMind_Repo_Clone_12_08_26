# tests/test_live_intelligence_sync.py
"""
Test Suite: Live Intelligence Synchronization, Nearest Actionable Levels & Decision Engine Invariant.

Verifies:
1. Corridor Arithmetic Invariant: Spot is NEVER claimed to be inside a corridor unless corridor_low <= spot <= corridor_high.
2. Spot-Relative Nearest Actionable Levels: Immediate support <= spot <= immediate resistance.
3. Distant Structural Levels (e.g. 24,640) are not assigned as immediate resistance for spot ~24,200.
4. Forward Outlook (Next Day) uses PRE_CLOSE_PREVIEW during live market hours and SESSION_COMPLETE when closed.
5. Context isolation between PRE_MARKET reference and LIVE_INTRADAY dynamic state.
"""
import pytest
from datetime import datetime, timezone
from src.intelligence_engine.structural_level_engine import StructuralLevelEngine
from src.intelligence_engine.forward_outlook_engine import ForwardOutlookEngine


def test_spot_outside_corridor_arithmetic_invariant():
    """Verify that when spot is at 24,203.40, the pre-market corridor (24,284 - 24,291)
    correctly classifies spot as BELOW, not INSIDE."""
    state = {
        "market_data": {
            "current_spot": 24203.40,
            "previous_close": 24287.65,
            "high": 24287.65,
            "low": 24190.0,
            "open": 24280.0
        },
        "option_intelligence": {
            "highest_put_oi_strike": 24200.0,
            "highest_call_oi_strike": 24500.0,
            "max_pain": 24200.0,
            "pcr": 0.77
        }
    }

    result = StructuralLevelEngine.evaluate_levels(state)

    # Pre-market corridor check
    pre_corridor = result["pre_market_reference_corridor"]
    assert pre_corridor["low"] == 24284.0
    assert pre_corridor["high"] == 24291.0
    assert pre_corridor["is_inside"] is False
    assert pre_corridor["spot_relation"] == "BELOW"

    # Live decision zone check
    live_zone = result["live_decision_zone"]
    assert live_zone["low"] <= 24203.40
    assert live_zone["high"] >= 24203.40
    assert live_zone["is_inside"] is True
    assert live_zone["spot_relation"] == "INSIDE"


def test_nearest_actionable_levels_derivation():
    """Verify that immediate support and immediate resistance are closest to spot (~24,203),
    and distant structural levels like 24,500/24,640 are classified as major, not immediate."""
    state = {
        "market_data": {
            "current_spot": 24203.40,
            "previous_close": 24287.65,
            "high": 24287.65,
            "low": 24190.0,
        },
        "option_intelligence": {
            "highest_put_oi_strike": 24000.0,
            "highest_call_oi_strike": 24500.0,
            "max_pain": 24200.0,
            "pcr": 0.77
        }
    }

    result = StructuralLevelEngine.evaluate_levels(state)

    imm_sup = result["immediate_support"]
    imm_res = result["immediate_resistance"]

    # Immediate support must be <= spot
    assert imm_sup["price"] <= 24203.40
    # Immediate resistance must be >= spot
    assert imm_res["price"] >= 24203.40

    # Distance to immediate levels should be tight (< 100 points), not 400+ points away
    assert abs(24203.40 - imm_sup["price"]) < 100.0
    assert abs(imm_res["price"] - 24203.40) < 100.0

    # Distant call wall at 24,500 must be in major_resistance, not immediate
    maj_res = result["major_resistance"]
    assert maj_res["price"] >= imm_res["price"]


def test_forward_outlook_session_context_gating():
    """Verify ForwardOutlookEngine uses PRE_CLOSE_PREVIEW during open session
    and appropriate horizon labels."""
    ForwardOutlookEngine.reset_engine_state()

    # 1. Active Open Market
    open_state = {
        "market_session": {
            "status": "OPEN",
            "is_closed": False,
            "session_date": "2026-08-18"
        },
        "market_data": {
            "current_spot": 24203.40,
            "previous_close": 24287.65,
            "vwap": 24220.0,
            "high": 24287.65,
            "low": 24190.0,
            "breadth": {"advances": 16, "declines": 33, "unchanged": 1}
        },
        "option_intelligence": {
            "pcr": 0.77,
            "max_pain": 24200.0,
            "highest_call_oi_strike": 24500,
            "highest_put_oi_strike": 24000
        },
        "macro_intelligence": {
            "india_vix": {"value": 11.61, "change_pct": 0.43}
        }
    }

    report_open = ForwardOutlookEngine.evaluate_outlook(open_state)
    assert report_open.analysis_status == "PRE_CLOSE_PREVIEW"
    assert "PRE_CLOSE_PREVIEW" in report_open.horizon_label
    assert report_open.current_regime == "LIVE_SESSION"

    # 2. Closed Market
    ForwardOutlookEngine.reset_engine_state()
    closed_state = {
        "market_session": {
            "status": "CLOSED",
            "is_closed": True,
            "session_date": "2026-08-18"
        },
        "market_data": {
            "current_spot": 24202.05,
            "previous_close": 24287.65,
            "vwap": 24220.0,
            "high": 24287.65,
            "low": 24190.0,
            "breadth": {"advances": 16, "declines": 33, "unchanged": 1}
        },
        "option_intelligence": {
            "pcr": 0.77,
            "max_pain": 24200.0,
            "highest_call_oi_strike": 24500,
            "highest_put_oi_strike": 24000
        },
        "macro_intelligence": {
            "india_vix": {"value": 11.61, "change_pct": 0.43}
        }
    }

    report_closed = ForwardOutlookEngine.evaluate_outlook(closed_state)
    assert report_closed.analysis_status in ("SESSION_COMPLETE", "READY", "LOW_CONFIDENCE")
    assert report_closed.current_regime in ("SESSION_COMPLETE", "CLOSED")
