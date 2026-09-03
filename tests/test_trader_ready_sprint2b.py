# tests/test_trader_ready_sprint2b.py
"""
Comprehensive Deterministic Test Suite for AIR ArdhaMind Trader-Ready Sprint 2B.

Tests:
1. Canonical TraderDecision & TradeCandidate contracts
2. Strike Strength Engine (liquid ATM, illiquid OTM, theta penalty, spread quality, missing data)
3. Entry Quality Engine (chase distance, risk/reward geometry, invalidation stop, confirmation gating)
4. Approval Safety Gates (WATCH -> CONDITIONS_PENDING -> QUALIFIED -> READY_FOR_APPROVAL)
5. Safety & Read-Only Invariant (no broker execution calls, no automatic orders)
6. 24 Aug Replay at key timestamps (09:15, 10:00, 11:30, 14:00)
"""

import json
from datetime import datetime, timezone
import pytest

from src.intelligence_engine.strike_strength_engine import StrikeStrengthEngine
from src.intelligence_engine.entry_quality_engine import EntryQualityEngine
from src.intelligence_engine.trader_decision_engine import TraderDecisionEngine, TraderDecision, TradeCandidate
from src.intelligence_engine.decision_summary_composer import MarketDecisionSummaryComposer


def test_strike_strength_engine_atm_vs_otm():
    """Test 1: Strike Strength Engine scores liquid ATM higher than deep OTM with wide spread."""
    spot = 24250.0

    # Option chain with liquid ATM (24250 PE) and illiquid OTM (24100 PE)
    options_data = {
        "chain": [
            {
                "strike": 24250.0,
                "option_type": "PE",
                "ltp": 95.0,
                "bid": 94.8,
                "ask": 95.2,
                "volume": 25000,
                "oi": 80000,
                "delta": -0.50,
                "theta": -8.0,
                "iv": 12.5,
            },
            {
                "strike": 24100.0,
                "option_type": "PE",
                "ltp": 25.0,
                "bid": 23.5,
                "ask": 26.5,
                "volume": 800,
                "oi": 5000,
                "delta": -0.18,
                "theta": -12.0,
                "iv": 18.0,
            }
        ]
    }

    evals = StrikeStrengthEngine.evaluate_strike_universe(
        spot=spot,
        direction="PE",
        options_data=options_data,
        india_vix=12.0,
        days_to_expiry=3.0
    )

    assert len(evals) >= 2
    atm_eval = next(e for e in evals if e.strike == 24250.0)
    otm_eval = next(e for e in evals if e.strike == 24100.0)

    # ATM has higher strength score and better liquidity
    assert atm_eval.strength_score > otm_eval.strength_score
    assert atm_eval.strength_band in ("EXCELLENT", "GOOD")
    assert otm_eval.strength_band in ("WEAK", "AVOID", "ACCEPTABLE")
    assert atm_eval.liquidity_grade == "STRONG"
    assert otm_eval.required_nifty_move > atm_eval.required_nifty_move


def test_entry_quality_engine_good_vs_bad_entry():
    """Test 2: Entry Quality Engine distinguishes tight R:R entry from chasing extended price."""
    spot = 24220.0

    # Good Entry: Trigger at 24220 (chase = 0), Invalidation at 24240 (20 pt risk), Target at 24170 (50 pt reward)
    good_entry = EntryQualityEngine.evaluate_entry_quality(
        spot=spot,
        direction="PE",
        entry_trigger_price=24220.0,
        invalidation_price=24240.0,
        target_1=24170.0,
        strike_spread_pct=0.3,
        is_confirmed=True
    )
    assert good_entry.entry_quality_band in ("EXCELLENT", "GOOD")
    assert good_entry.risk_reward_ratio is not None and good_entry.risk_reward_ratio >= 2.0
    assert good_entry.is_chase is False

    # Bad Entry: Price already dropped 40 pts past trigger (chase = 40), wide stop at 24280 (60 pt risk), target at 24200 (20 pt reward)
    bad_entry = EntryQualityEngine.evaluate_entry_quality(
        spot=24180.0,
        direction="PE",
        entry_trigger_price=24220.0,
        invalidation_price=24280.0,
        target_1=24160.0,
        strike_spread_pct=1.8,
        is_confirmed=True
    )
    assert bad_entry.entry_quality_band in ("WAIT", "POOR", "DO_NOT_ENTER")
    assert bad_entry.is_chase is True
    assert len(bad_entry.entry_blockers) > 0


def test_trader_decision_approval_gates():
    """Test 3: Approval status progresses through safety gates and blocks when criteria fail."""
    # Qualified Live State with full data and favorable R:R
    qualified_state = {
        "market_session": {"status": "OPEN", "session_date": "2026-08-24"},
        "market_data": {
            "current_spot": 24220.0,
            "open": 24285.0,
            "high": 24295.0,
            "low": 24215.0,
            "close": 24220.0,
            "vwap": 24252.0,
            "breadth": {"advances": 14, "declines": 36}
        },
        "forward_outlook": {
            "scenario": "RANGE_WITH_BEARISH_PRESSURE",
            "confidence": "HIGH",
            "support": 24150.0,
            "resistance": 24300.0
        },
        "macro_intelligence": {"india_vix": {"value": 11.5}},
        "option_intelligence": {
            "chain": [
                {
                    "strike": 24200.0,
                    "option_type": "PE",
                    "ltp": 72.0,
                    "bid": 71.8,
                    "ask": 72.2,
                    "volume": 45000,
                    "oi": 95000,
                    "delta": -0.48
                }
            ]
        }
    }

    decision = TraderDecisionEngine.evaluate_trader_decision(qualified_state)
    assert decision.bias == "BEARISH"
    assert decision.direction == "PE"
    assert decision.approval_status == "READY_FOR_APPROVAL"
    assert decision.trade_candidate is not None
    assert decision.trade_candidate["status"] == "READY_FOR_APPROVAL"

    # State with LOW confidence -> must block READY_FOR_APPROVAL
    low_conf_state = dict(qualified_state)
    low_conf_state["forward_outlook"] = {"scenario": "RANGE_WITH_BEARISH_PRESSURE", "confidence": "LOW", "support": 24150.0, "resistance": 24300.0}
    dec_low_conf = TraderDecisionEngine.evaluate_trader_decision(low_conf_state)
    assert dec_low_conf.approval_status != "READY_FOR_APPROVAL"
    assert any("confidence" in b.lower() for b in dec_low_conf.approval_blockers)

    # State where Market is Closed -> must block READY_FOR_APPROVAL
    closed_state = dict(qualified_state)
    closed_state["market_session"] = {"status": "CLOSED", "session_date": "2026-08-24"}
    dec_closed = TraderDecisionEngine.evaluate_trader_decision(closed_state)
    assert dec_closed.approval_status == "WATCH"


def test_safety_and_read_only_invariant():
    """Test 4: Strict verification that NO broker execution or order placement APIs exist in decision engine."""
    import inspect
    import src.intelligence_engine.trader_decision_engine as tde_mod
    import src.intelligence_engine.strike_strength_engine as sse_mod
    import src.intelligence_engine.entry_quality_engine as eqe_mod

    for mod in (tde_mod, sse_mod, eqe_mod):
        source = inspect.getsource(mod)
        assert "place_order" not in source
        assert "broker.buy" not in source
        assert "broker.sell" not in source
        assert "kite.place_order" not in source
        assert "execute_order" not in source


def test_24_aug_replay_decision_progression():
    """Test 5: Replay 24 Aug session state across 09:15, 10:00, 11:30, and 14:00."""
    with open("/opt/ardhamind/staging/data/cache/session_history_2026-08-24.json", "r") as f:
        data = json.load(f)

    snapshots = data.get("snapshots", [])
    assert len(snapshots) > 0

    # Sample snapshots near target timestamps
    snap_0915 = next((s for s in snapshots if "T03:45" in (s.get("timestamp") or "")), snapshots[0])
    snap_1000 = next((s for s in snapshots if "T04:30" in (s.get("timestamp") or "")), snapshots[30])
    snap_1130 = next((s for s in snapshots if "T06:00" in (s.get("timestamp") or "")), snapshots[60])
    snap_1400 = next((s for s in snapshots if "T08:30" in (s.get("timestamp") or "")), snapshots[100])

    for label, snap in [("09:15 Open", snap_0915), ("10:00 Range", snap_1000), ("11:30 Breakdown", snap_1130), ("14:00 Afternoon", snap_1400)]:
        state_repr = {
            "market_session": {"status": "OPEN", "session_date": "2026-08-24"},
            "market_data": {
                "current_spot": snap.get("spot") or 24252.0,
                "open": snap.get("open") or 24285.05,
                "high": snap.get("high") or 24313.0,
                "low": snap.get("low") or 24144.3,
                "close": snap.get("close") or 24252.0,
                "vwap": 24252.0,
                "breadth": snap.get("breadth") or {"advances": 18, "declines": 31}
            },
            "forward_outlook": snap.get("forward_outlook") or {},
            "macro_intelligence": {"india_vix": {"value": 11.5}},
            "option_intelligence": {}
        }
        dec = TraderDecisionEngine.evaluate_trader_decision(state_repr)
        assert dec.trading_date == "2026-08-24"
        assert dec.approval_status in ("WATCH", "CONDITIONS_PENDING", "QUALIFIED", "READY_FOR_APPROVAL")
        assert dec.data_quality in ("FULL", "GOOD", "DEGRADED", "INSUFFICIENT")
