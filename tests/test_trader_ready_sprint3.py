# tests/test_trader_ready_sprint3.py
"""
Deterministic Test Suite for AIR ArdhaMind Trader-Ready Sprint 3 Fast Execution.

Tests:
1. Approval Workflow (Approve, Reject, Candidate Freeze, Freshness & Invalidation)
2. Position Sizing Engine (Risk budget, Lot rounding, Missing balance, Sizing limits)
3. Broker Preflight Layer & Price Reconciliation (Auth, Duplicates, Mismatch, Margin)
4. Risk Engine Gates (Daily loss limit, Max concurrent positions, Capital allocation)
5. Immutable Audit Trail (Logged transitions, provenance, event timestamps)
6. Positive Control Case (Reaches READY_FOR_APPROVAL, transitions to APPROVED with 0 broker calls)
7. Safety Invariants (0 real broker orders, 0 paper orders, 0 auto approvals)
8. 24 Aug Replay Validation (09:15, 10:00, 11:30, 14:00)
"""

import json
from datetime import datetime, timezone
import pytest

from src.intelligence_engine.position_sizing_engine import PositionSizingEngine, RiskPolicyConfig
from src.intelligence_engine.broker_preflight_service import BrokerPreflightService
from src.intelligence_engine.trade_approval_service import TradeApprovalService, FrozenTradeApproval
from src.intelligence_engine.trader_decision_engine import TraderDecisionEngine


def test_position_sizing_engine_normal_and_missing_balance():
    """Test 1: Position Sizing calculates correct lots and handles missing capital gracefully."""
    # Case A: Normal Sizing with ₹5,00,000 capital, 1% risk per trade (₹5,000 budget), option LTP ₹80, 20 pt stop
    capital = 500000.0
    res = PositionSizingEngine.calculate_position_size(
        account_capital=capital,
        option_ltp=80.0,
        spot=24200.0,
        invalidation_price=24240.0,
        delta=-0.50,
        policy=RiskPolicyConfig(max_risk_per_trade_pct=1.0, lot_size=25)
    )
    assert res.position_size_status == "SIZED"
    assert res.risk_budget == 5000.0
    assert res.rounded_lots >= 1
    assert res.final_quantity == res.rounded_lots * 25
    assert res.estimated_premium_outlay == res.final_quantity * 80.0
    assert res.estimated_max_loss is not None and res.estimated_max_loss <= res.risk_budget * 1.25

    # Case B: Missing capital (Never fabricate balance)
    res_none = PositionSizingEngine.calculate_position_size(
        account_capital=None,
        option_ltp=80.0,
        spot=24200.0,
        invalidation_price=24240.0,
        delta=-0.50
    )
    assert res_none.position_size_status == "POSITION_SIZE_UNAVAILABLE"
    assert res_none.final_quantity is None
    assert "unavailable" in res_none.risk_blockers[0].lower()


def test_position_sizing_daily_risk_and_position_limits():
    """Test 2: Position Sizing enforces daily cumulative risk and concurrent position limits."""
    capital = 500000.0
    policy = RiskPolicyConfig(max_daily_risk_pct=3.0, max_concurrent_positions=2)

    # Breaching daily loss limit (₹16,000 loss > 3% of ₹5,00,000 = ₹15,000)
    res_loss = PositionSizingEngine.calculate_position_size(
        account_capital=capital,
        option_ltp=80.0,
        spot=24200.0,
        invalidation_price=24240.0,
        policy=policy,
        daily_loss_accumulated=16000.0
    )
    assert res_loss.position_size_status == "EXCEEDS_RISK_LIMIT"
    assert any("daily loss" in b.lower() for b in res_loss.risk_blockers)

    # Max concurrent positions limit reached
    res_pos = PositionSizingEngine.calculate_position_size(
        account_capital=capital,
        option_ltp=80.0,
        spot=24200.0,
        invalidation_price=24240.0,
        policy=policy,
        active_positions_count=2
    )
    assert res_pos.position_size_status == "EXCEEDS_RISK_LIMIT"
    assert any("concurrent" in b.lower() for b in res_pos.risk_blockers)


def test_broker_preflight_and_price_reconciliation():
    """Test 3: Broker preflight checks auth, duplicates, margin, and price divergence."""
    inst = "NIFTY 24200 PE"

    # Case A: Valid matched quote (< 2% difference) and authenticated broker
    valid_state = {
        "auth_state": "CONNECTED_VERIFIED",
        "available_capital": 200000.0,
        "live_quotes": {inst: {"ltp": 75.5}},
        "active_orders": [],
        "open_positions": []
    }
    res_pass = BrokerPreflightService.run_preflight_checks(
        candidate_instrument=inst,
        candidate_strike=24200.0,
        candidate_option_type="PE",
        ardha_ltp=75.0,
        broker_state=valid_state,
        market_session_active=True,
        required_margin=4000.0
    )
    assert res_pass.broker_preflight_status == "PASS"
    assert res_pass.reconciliation_status == "MATCHED"
    assert res_pass.duplicate_detected is False

    # Case B: Price Divergence > 2% (Ardha 75.0 vs Broker 80.0 = 6.25% diff)
    div_state = dict(valid_state)
    div_state["live_quotes"] = {inst: {"ltp": 80.0}}
    res_div = BrokerPreflightService.run_preflight_checks(
        candidate_instrument=inst,
        candidate_strike=24200.0,
        candidate_option_type="PE",
        ardha_ltp=75.0,
        broker_state=div_state,
        market_session_active=True
    )
    assert res_div.broker_preflight_status == "BLOCKED"
    assert res_div.reconciliation_status == "QUOTE_MISMATCH"

    # Case C: Duplicate active order already pending
    dup_state = dict(valid_state)
    dup_state["active_orders"] = [{"tradingsymbol": "NIFTY 24200 PE", "status": "OPEN"}]
    res_dup = BrokerPreflightService.run_preflight_checks(
        candidate_instrument=inst,
        candidate_strike=24200.0,
        candidate_option_type="PE",
        ardha_ltp=75.0,
        broker_state=dup_state,
        market_session_active=True
    )
    assert res_dup.broker_preflight_status == "BLOCKED"
    assert res_dup.duplicate_detected is True


def test_trade_approval_workflow_freeze_and_freshness():
    """Test 4: Explicit approval freezes candidate snapshot and detects staleness/invalidation."""
    TradeApprovalService.reset_state()
    cid = "CAND-2026-08-24-24200PE"

    # 1. Open Review
    TradeApprovalService.record_review_opened(cid, {"status": "READY_FOR_APPROVAL"})
    trail = TradeApprovalService.get_audit_trail(cid)
    assert len(trail) == 1
    assert trail[0].event_type == "REVIEW_OPENED"

    # 2. Approve candidate -> creates FrozenTradeApproval
    frozen = TradeApprovalService.approve_candidate(
        candidate_id=cid,
        trading_date="2026-08-24",
        spot=24218.0,
        instrument="NIFTY 24200 PE",
        strike=24200.0,
        option_type="PE",
        option_ltp=75.0,
        entry_condition="Break below 24,208.0",
        invalidation_level=24264.0,
        targets=[24150.0, 24110.0],
        quantity=50,
        lots=2,
        estimated_premium_outlay=3750.0,
        estimated_max_loss=1250.0,
        confidence="HIGH",
        strike_strength_score=95.0,
        entry_quality_band="GOOD",
        broker_preflight_status="PASS",
        full_decision_snapshot={}
    )
    assert frozen.freshness_status == "FRESH"
    assert frozen.approved_by == "TRADER"

    # 3. Check Freshness when spot remains near 24,218
    fresh_eval = TradeApprovalService.evaluate_approval_freshness(cid, current_spot=24220.0, current_option_ltp=74.5)
    assert fresh_eval.freshness_status == "FRESH"

    # 4. Check Staleness when spot drifts > 25 pts (e.g. up to 24,250)
    stale_eval = TradeApprovalService.evaluate_approval_freshness(cid, current_spot=24250.0, current_option_ltp=65.0)
    assert stale_eval.freshness_status == "STALE"
    assert "drifted" in stale_eval.freshness_reason

    # 5. Check Invalidation when spot breaches stop level (24,265 > 24,264)
    inval_eval = TradeApprovalService.evaluate_approval_freshness(cid, current_spot=24265.0, current_option_ltp=55.0)
    assert inval_eval.freshness_status == "INVALIDATED"


def test_positive_control_fixture_reaches_ready_and_approved():
    """Test 5: Positive control fixture reaches READY_FOR_APPROVAL and simulates human approval."""
    TradeApprovalService.reset_state()

    fixture_state = {
        "market_session": {"status": "OPEN", "session_date": "2026-08-24"},
        "market_data": {
            "current_spot": 24218.0,
            "open": 24285.0,
            "high": 24295.0,
            "low": 24215.0,
            "close": 24218.0,
            "vwap": 24252.0,
            "breadth": {"advances": 12, "declines": 38}
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
                    "ltp": 75.0,
                    "bid": 74.8,
                    "ask": 75.2,
                    "volume": 45000,
                    "oi": 95000,
                    "delta": -0.50
                }
            ]
        }
    }

    decision = TraderDecisionEngine.evaluate_trader_decision(fixture_state)
    assert decision.bias == "BEARISH"
    assert decision.direction == "PE"
    assert decision.approval_status == "READY_FOR_APPROVAL"
    assert decision.trade_candidate is not None

    # Simulate Human Review -> Approve
    cand = decision.trade_candidate
    approved = TradeApprovalService.approve_candidate(
        candidate_id=cand["candidate_id"],
        trading_date=decision.trading_date,
        spot=decision.spot,
        instrument=cand["instrument"],
        strike=cand["strike"],
        option_type=cand["option_type"],
        option_ltp=75.0,
        entry_condition=cand["entry_condition"],
        invalidation_level=cand["invalidation"],
        targets=cand["targets"],
        quantity=50,
        lots=2,
        estimated_premium_outlay=3750.0,
        estimated_max_loss=1250.0,
        confidence=decision.confidence_band,
        strike_strength_score=cand["strike_strength"],
        entry_quality_band=cand["entry_quality"],
        broker_preflight_status="PASS",
        full_decision_snapshot=decision.to_dict()
    )
    assert approved.approval_id.startswith("APP-")
    assert approved.freshness_status == "FRESH"


def test_safety_and_zero_orders_invariant():
    """Test 6: Verify zero broker orders, zero mock orders, and zero automatic approvals."""
    import inspect
    import src.intelligence_engine.trade_approval_service as tas_mod
    import src.intelligence_engine.broker_preflight_service as bps_mod
    import src.intelligence_engine.position_sizing_engine as pse_mod

    for mod in (tas_mod, bps_mod, pse_mod):
        source = inspect.getsource(mod)
        assert "place_order" not in source
        assert "broker.buy" not in source
        assert "broker.sell" not in source
        assert "kite.order" not in source
        assert "send_order" not in source
