# tests/test_sprint_i2_intelligence_ui.py
"""
Automated Integration & Quality Gate Test Suite for Intelligence Sprint I2:
Trader-Facing Intelligence Workstation Rebuild & Phase 3 Action Handoff.
"""

import json
import subprocess
from datetime import datetime, timezone, timedelta
import pytest

from src.intelligence_engine.actionable_suggestion_engine import ActionableSuggestionEngine
from src.models.trade_suggestion import SuggestionState
from src.proposal_engine.builder import ProposalBuilder

IST = timezone(timedelta(hours=5, minutes=30))


def test_qualified_trade_hero_data_integrity():
    """Verify live QUALIFIED snapshot produces complete trade hero parameters."""
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
        "options": {"pcr": 1.30, "max_pain": 24200.0},
        "alignment": "BULLISH"
    }
    test_dt = datetime(2026, 8, 20, 10, 30, 0, tzinfo=IST) # Live session
    snapshot = ActionableSuggestionEngine.analyze_and_suggest(state, now_ist=test_dt)
    primary = snapshot["primary_suggestion"]

    assert primary["state"] == SuggestionState.QUALIFIED.value
    assert primary["entry_zone"] == "₹140.00 – ₹145.00"
    assert primary["stop_loss"] == 118.0
    assert primary["target_1"] == 175.0
    assert primary["confidence"] >= 65
    assert primary["conviction"] >= 70
    assert primary["contract_symbol"] is not None
    assert primary["provenance"]["policy_version"] == "I1-V1-STAGING"


def test_no_trade_off_hours_parameter_safety():
    """Verify off-hours snapshot clears executable premium parameters."""
    state = {
        "market_data": {
            "current_spot": 24152.05,
            "open": 24100.0,
            "high": 24180.0,
            "low": 24090.0,
            "previous_close": 24078.3,
            "breadth": {"advances": 38, "declines": 12},
            "status": "closed"
        },
        "options": {"pcr": 1.30, "max_pain": 24200.0},
        "alignment": "BULLISH"
    }
    test_dt = datetime(2026, 8, 20, 18, 0, 0, tzinfo=IST) # Off-hours
    snapshot = ActionableSuggestionEngine.analyze_and_suggest(state, now_ist=test_dt)
    primary = snapshot["primary_suggestion"]

    assert primary["state"] == SuggestionState.NO_TRADE.value
    assert primary["entry_zone"] is None
    assert primary["stop_loss"] is None
    assert primary["target_1"] is None
    assert primary["provenance"]["session_state"] == "CLOSED"


def test_phase3_proposal_handoff_contract():
    """Verify map_to_proposal constructs a valid Phase 3 TradeProposal from QUALIFIED suggestion."""
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
        "options": {"pcr": 1.30, "max_pain": 24200.0},
        "alignment": "BULLISH"
    }
    test_dt = datetime(2026, 8, 20, 10, 30, 0, tzinfo=IST)
    snapshot = ActionableSuggestionEngine.analyze_and_suggest(state, now_ist=test_dt)
    primary = snapshot["primary_suggestion"]

    proposal = ActionableSuggestionEngine.map_to_proposal(primary)
    assert proposal is not None
    assert proposal.state == "PROPOSED"
    assert proposal.contract_symbol == primary["contract_symbol"]
    assert proposal.lots == primary["lots"]


def test_production_directory_isolation():
    """Verify /opt/ArdhaMind production directory remains 100% untouched."""
    cmd = "git -C /opt/ArdhaMind status --porcelain"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert res.returncode == 0
    assert res.stdout.strip() == "", f"Production directory modified! Changes: {res.stdout}"
