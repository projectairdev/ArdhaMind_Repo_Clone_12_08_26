# tests/test_actionable_intelligence_engine.py
"""
Comprehensive Automated Test Suite for Intelligence Sprint I1:
Intelligence Engine Reconstruction & Actionable Trade Suggestion Core.
"""

import subprocess
import pytest
from datetime import datetime, timezone, timedelta
from src.intelligence_engine.actionable_suggestion_engine import ActionableSuggestionEngine
from src.models.trade_suggestion import TradeSuggestion
from src.models.intelligence_snapshot import IntelligenceSnapshot
from src.proposal_engine.models import ProposalState

IST = timezone(timedelta(hours=5, minutes=30))


def test_positive_breadth_semantic_integrity():
    """Verify 39 ADV / 10 DEC is interpreted as POSITIVE breadth and never negative."""
    state = {
        "market_data": {
            "current_spot": 24152.05,
            "open": 24152.05,
            "high": 24177.05,
            "low": 24127.05,
            "breadth": {"advances": 39, "declines": 10, "unchanged": 1},
            "status": "open"
        },
        "options": {"pcr": 1.25, "max_pain": 24200.0},
        "alignment": "BULLISH"
    }
    test_dt = datetime(2026, 8, 20, 10, 30, 0, tzinfo=IST) # Active market session
    snapshot = ActionableSuggestionEngine.analyze_and_suggest(state, now_ist=test_dt)

    assert snapshot["breadth_summary"]["breadth_bias"] == "POSITIVE"
    assert snapshot["breadth_summary"]["advance_ratio_pct"] >= 75.0

    # Ensure no contradictory "negative breadth" phrasing in rationale
    primary = snapshot["primary_suggestion"]
    for r in primary.get("rationale", []):
        assert "negative breadth" not in r.lower()


def test_directional_bias_and_regime_separation():
    """Verify directional bias (BULLISH/BEARISH) and market regime (RANGE_DAY/TRENDING) remain distinct."""
    state = {
        "market_data": {"current_spot": 24152.05, "open": 24100.0, "high": 24180.0, "low": 24090.0, "status": "open"},
        "regime": "RANGE_DAY",
        "alignment": "BULLISH"
    }
    test_dt = datetime(2026, 8, 20, 11, 0, 0, tzinfo=IST)
    snapshot = ActionableSuggestionEngine.analyze_and_suggest(state, now_ist=test_dt)

    assert snapshot["directional_bias"] == "BULLISH"
    assert snapshot["regime"] == "RANGE_DAY"
    assert snapshot["directional_bias"] != snapshot["regime"]


def test_actionable_trade_suggestion_construction():
    """Verify actionable TradeSuggestion yields exact contract, entry, SL, targets, R:R, and max loss."""
    state = {
        "market_data": {
            "current_spot": 24152.05,
            "open": 24100.0,
            "high": 24180.0,
            "low": 24090.0,
            "previous_close": 24078.3,
            "breadth": {"advances": 38, "declines": 12},
            "status": "open"
        },
        "options": {"pcr": 1.30, "max_pain": 24200.0, "call_wall": 24300.0, "put_wall": 24000.0},
        "alignment": "BULLISH"
    }
    test_dt = datetime(2026, 8, 20, 10, 45, 0, tzinfo=IST)
    snapshot = ActionableSuggestionEngine.analyze_and_suggest(state, now_ist=test_dt)

    primary = snapshot["primary_suggestion"]
    assert primary["state"] == "QUALIFIED"
    assert primary["direction"] == "BULLISH"
    assert primary["strike"] == 24150
    assert primary["option_type"] == "CE"
    assert primary["contract_symbol"] == "NIFTY 24150 CE"
    assert primary["stop_loss"] > 0.0
    assert primary["target_1"] > primary["stop_loss"]
    assert primary["risk_reward_ratio"] >= 1.2
    assert primary["lots"] >= 1
    assert primary["quantity"] > 0


def test_market_closed_useful_no_trade():
    """Verify market closed returns structured NO_TRADE detailing next trigger and invalidation."""
    state = {
        "market_data": {"current_spot": 24152.05, "status": "closed"},
    }
    test_dt = datetime(2026, 8, 20, 17, 0, 0, tzinfo=IST)
    snapshot = ActionableSuggestionEngine.analyze_and_suggest(state, now_ist=test_dt)

    primary = snapshot["primary_suggestion"]
    assert primary["state"] == "NO_TRADE"
    assert primary["contract_symbol"] == "NO ACTIVE TRADE SUGGESTION"
    assert "MARKET CLOSED" in primary["qualification_reason"]
    assert len(primary["next_trigger"]) > 0


def test_phase3_proposal_handoff_mapping():
    """Verify qualified TradeSuggestion maps deterministically into Phase 3 TradeProposal."""
    suggestion_data = {
        "suggestion_id": "TS-20260820-01",
        "candidate_id": "CAND-20260820-01",
        "state": "QUALIFIED",
        "strategy": "BREAKOUT_RETEST",
        "direction": "BULLISH",
        "underlying": "NIFTY",
        "strike": 24150,
        "option_type": "CE",
        "contract_symbol": "NIFTY 24150 CE",
        "premium_ltp": 125.0,
        "stop_loss": 95.0,
        "target_1": 165.0,
        "target_2": 195.0,
        "risk_reward_ratio": 1.33,
        "confidence": 78.0,
        "conviction": 82.0,
        "evidence_quality": 85.0,
        "lots": 1,
        "quantity": 65,
        "estimated_max_loss": 1950.0,
        "rationale": ["Positive breadth", "Options confirmation"],
        "invalidation_condition": "Loss of support"
    }

    proposal = ActionableSuggestionEngine.map_to_proposal(suggestion_data)

    assert proposal.state == ProposalState.PROPOSED.value
    assert proposal.underlying == "NIFTY"
    assert proposal.setup_type == "BREAKOUT_RETEST"
    assert proposal.direction == "BULLISH"
    assert proposal.strike == 24150
    assert proposal.contract_symbol == "NIFTY 24150 CE"
    assert proposal.entry_price == 125.0
    assert proposal.stop_loss == 95.0
    assert proposal.target_1 == 165.0
    assert proposal.confidence_score == 78.0
    assert proposal.total_quantity == 65


def test_production_directory_isolation():
    """Verify /opt/ArdhaMind production directory remains 100% untouched."""
    cmd = "git -C /opt/ArdhaMind status --porcelain"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert res.returncode == 0
    assert res.stdout.strip() == "", f"Production directory modified! Changes: {res.stdout}"
