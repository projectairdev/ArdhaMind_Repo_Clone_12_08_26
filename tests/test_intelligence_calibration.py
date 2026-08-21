import pytest
from src.application.workstation_state_service import WorkstationStateService
from src.proposal_engine.builder import ProposalBuilder
from src.proposal_engine.models import ProposalState

def test_breadth_classification_negative():
    legacy = {
        "marketContext": {
            "current_spot": 24237.85,
            "breadth": {"advances": 20, "declines": 30, "unchanged": 0}
        }
    }
    state = WorkstationStateService.build_from_legacy(legacy)
    s_dict = state.to_dict()
    brd = s_dict["market_data"]["breadth"]
    assert brd["advances"] == 20
    assert brd["declines"] == 30
    assert brd["advances"] < brd["declines"]

def test_missing_options_null_semantics():
    legacy = {
        "marketContext": {"current_spot": 24237.85},
        "optionContext": {}
    }
    state = WorkstationStateService.build_from_legacy(legacy)
    s_dict = state.to_dict()
    opts = s_dict.get("options") or {}
    assert opts.get("pcr") is None or opts.get("pcr") == 0
    assert opts.get("put_wall") is None or opts.get("put_wall") == 0

def test_proposal_expiration_no_trade():
    no_trade_opp = {"status": "NO_TRADE", "priority_score": 0}
    proposal = ProposalBuilder.build_proposal(no_trade_opp)
    assert proposal.state == ProposalState.NO_TRADE.value
    assert proposal.direction == "NEUTRAL"
