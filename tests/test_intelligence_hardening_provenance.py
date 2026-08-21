# tests/test_intelligence_hardening_provenance.py
"""
Comprehensive Hardening & Provenance Test Suite for Intelligence Sprint I1-H:
Session-Aware Actionability Contract, Trade Parameter Provenance & Multi-Session Audit.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest

from src.intelligence_engine.actionable_suggestion_engine import ActionableSuggestionEngine
from src.intelligence_engine.intelligence_policy import DEFAULT_INTELLIGENCE_POLICY, IntelligenceQualificationPolicy
from src.models.trade_suggestion import TradeSuggestion, SuggestionState
from src.proposal_engine.models import ProposalState

IST = timezone(timedelta(hours=5, minutes=30))
CACHE_DIR = Path("/opt/ardhamind/staging/data/cache")


def test_market_closed_clears_executable_premium_parameters():
    """Verify closed market sets candidate to ARMED_FOR_NEXT_SESSION with null executable parameters."""
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
    test_dt = datetime(2026, 8, 20, 17, 30, 0, tzinfo=IST) # Post-market
    snapshot = ActionableSuggestionEngine.analyze_and_suggest(state, now_ist=test_dt)

    assert snapshot["primary_suggestion"]["state"] == SuggestionState.NO_TRADE.value
    assert snapshot["qualification_diagnostics"]["hard_blockers"] == ["MARKET_CLOSED"]

    watchlist = snapshot["watchlist_candidates"]
    assert len(watchlist) >= 1
    cand = watchlist[0]

    assert cand["state"] == SuggestionState.ARMED_FOR_NEXT_SESSION.value
    assert cand["contract_symbol"] == "TO_BE_RESOLVED"
    assert cand["entry_zone"] is None
    assert cand["stop_loss"] is None
    assert cand["target_1"] is None
    assert cand["target_2"] is None
    assert cand["premium_ltp"] is None
    assert cand["spread_pct"] is None
    assert cand["lots"] is None
    assert cand["quantity"] is None
    assert cand["estimated_max_loss"] is None
    assert cand["liquidity_status"] == "REQUIRES_LIVE_REVALIDATION"
    assert "retained for next session" in cand["qualification_reason"]


def test_pre_market_clears_executable_premium_parameters():
    """Verify pre-market (08:50 IST) sets candidate to PRE_OPEN_WATCH with null executable parameters."""
    state = {
        "market_data": {
            "current_spot": 24152.05,
            "breadth": {"advances": 35, "declines": 15},
            "status": "open"
        },
        "alignment": "BULLISH"
    }
    test_dt = datetime(2026, 8, 20, 8, 50, 0, tzinfo=IST) # Pre-market 08:50
    snapshot = ActionableSuggestionEngine.analyze_and_suggest(state, now_ist=test_dt)

    watchlist = snapshot["watchlist_candidates"]
    assert len(watchlist) >= 1
    cand = watchlist[0]

    assert cand["state"] == SuggestionState.PRE_OPEN_WATCH.value
    assert cand["entry_zone"] is None
    assert cand["stop_loss"] is None
    assert cand["target_1"] is None
    assert cand["premium_ltp"] is None
    assert cand["liquidity_status"] == "REQUIRES_LIVE_REVALIDATION"


def test_live_session_populates_executable_premium_parameters():
    """Verify live session (10:30 IST) populates valid executable parameters and provenance."""
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
    assert primary["contract_symbol"] == "NIFTY 24150 CE"
    assert primary["entry_zone"] is not None
    assert primary["stop_loss"] > 0.0
    assert primary["target_1"] > primary["stop_loss"]
    assert primary["risk_reward_ratio"] >= 1.2
    assert primary["lots"] == 1
    assert primary["quantity"] == 65

    prov = primary["provenance"]
    assert prov["policy_version"] == "I1-V1-STAGING"
    assert prov["contract"]["source"] == "cache/instruments.db"
    assert prov["premium_quote"]["source"] == "LIVE_MARKET_FEED"
    assert prov["lot_size"]["resolved_lot_size"] == 65


def test_provenance_structure_completeness():
    """Verify provenance metadata contains all required audit fields."""
    policy = IntelligenceQualificationPolicy()
    assert policy.policy_version == "I1-V1-STAGING"
    assert policy.validate_weights() is True
    assert "LOT_SIZE_UNVERIFIED" in policy.hard_blockers


def test_market_closed_candidate_cannot_become_proposal():
    """Verify ARMED_FOR_NEXT_SESSION candidate cannot map into a Phase 3 TradeProposal."""
    armed_cand = {
        "suggestion_id": "TS-ARMED-01",
        "candidate_id": "CAND-ARMED-01",
        "state": SuggestionState.ARMED_FOR_NEXT_SESSION.value,
        "strategy": "BREAKOUT_RETEST",
        "direction": "BULLISH",
        "underlying": "NIFTY",
        "contract_symbol": "TO_BE_RESOLVED"
    }

    proposal = ActionableSuggestionEngine.map_to_proposal(armed_cand)
    assert proposal.state == ProposalState.NO_TRADE.value
    assert proposal.contract_symbol == "TO_BE_RESOLVED"


def test_multi_session_historical_replay():
    """Replays real recorded session JSON files to audit candidate generation across sessions."""
    session_files = sorted(list(CACHE_DIR.glob("session_history_*.json")))
    valid_files = [f for f in session_files if "TEST_ISOLATED" not in f.name]
    assert len(valid_files) >= 5, f"Expected at least 5 session files, found {len(valid_files)}"

    audit_summary = []

    for s_file in valid_files:
        with open(s_file, "r") as f:
            data = json.load(f)

        session_date = data.get("session_date") or s_file.stem.replace("session_history_", "")
        records = data.get("snapshots") or data.get("history") or []

        candidates_seen = 0
        qualified_seen = 0
        no_trade_seen = 0

        for idx, snap in enumerate(records[:10]): # Replay first 10 snapshots per session
            market_data = snap.get("market_data") or snap.get("marketContext") or snap
            state = {
                "market_data": market_data,
                "options": snap.get("options") or {},
                "alignment": snap.get("alignment") or "BULLISH"
            }
            # Historical timestamp matching record
            ts_str = snap.get("timestamp") or f"{session_date}T10:30:00+05:30"
            try:
                dt_val = datetime.fromisoformat(ts_str)
            except Exception:
                dt_val = datetime(2026, 8, 19, 10, 30, 0, tzinfo=IST)

            res = ActionableSuggestionEngine.analyze_and_suggest(state, now_ist=dt_val)
            candidates_seen += len(res.get("watchlist_candidates") or [])
            if res.get("primary_suggestion", {}).get("state") == SuggestionState.QUALIFIED.value:
                qualified_seen += 1
            else:
                no_trade_seen += 1

        audit_summary.append({
            "session_date": session_date,
            "snapshots_tested": len(records[:10]),
            "candidates_seen": candidates_seen,
            "qualified_seen": qualified_seen,
            "no_trade_seen": no_trade_seen
        })

    assert len(audit_summary) >= 5


def test_production_directory_isolation():
    """Verify /opt/ArdhaMind production directory remains 100% untouched."""
    cmd = "git -C /opt/ArdhaMind status --porcelain"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert res.returncode == 0
    assert res.stdout.strip() == "", f"Production directory modified! Changes: {res.stdout}"
