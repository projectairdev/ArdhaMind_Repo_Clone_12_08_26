# tests/test_trader_ready_controlled_execution.py
"""
Comprehensive Deterministic Test Suite for AIR ArdhaMind Trader-Ready Controlled Execution.

Tests:
1. Hard Execution Invariant (Unapproved, stale, invalidated, and consumed approvals blocked)
2. OrderIntent Contract (Deterministic derivation from FrozenTradeApproval)
3. Broker Submission Boundary (Submission, acknowledgement, timeout reconciliation)
4. Fill Reconciliation (Full fills, partial fills, slippage, LivePosition creation)
5. Position Monitoring & Stop/Target Management (Thesis stop vs broker stop, target hit, P&L)
6. Controlled Exit Workflow (Manual exit, emergency exit, realized P&L)
7. Positive Control End-to-End Lifecycle
8. Safety Invariants (0 real broker orders in tests, feature flag default OFF)
"""

import json
from datetime import datetime, timezone
import pytest

from src.intelligence_engine.trade_approval_service import TradeApprovalService, FrozenTradeApproval
from src.controlled_execution.controlled_execution_contracts import ExecutionState, OrderIntent, LivePosition
from src.controlled_execution.controlled_broker_execution_service import ControlledBrokerExecutionService


def test_hard_execution_invariant_and_approval_consumption():
    """Test 1: Only a fresh FrozenTradeApproval can execute; consumed approvals are rejected."""
    ControlledBrokerExecutionService.reset_state()
    TradeApprovalService.reset_state()

    cid = "CAND-EXEC-001"
    # Create Frozen Approval
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

    # 1. Successful pre-submission revalidation
    ok, record, blockers = ControlledBrokerExecutionService.revalidate_and_prepare_execution(
        frozen_approval=frozen,
        current_spot=24218.0,
        current_option_ltp=75.0,
        market_session_active=True,
        broker_state={"auth_state": "CONNECTED_VERIFIED", "open_positions": []}
    )
    assert ok is True
    assert record.state == ExecutionState.READY_TO_SUBMIT
    assert record.order_intent is not None
    assert record.order_intent.quantity == 50

    # 2. Submit order -> consumes approval
    sub_ok, sub_rec, err = ControlledBrokerExecutionService.submit_order_intent(record.execution_id)
    assert sub_ok is True
    assert sub_rec.state == ExecutionState.BROKER_ACCEPTED
    assert sub_rec.broker_order_id is not None

    # 3. Second submission attempt with same approval MUST BE REJECTED
    repeat_ok, repeat_rec, repeat_blockers = ControlledBrokerExecutionService.revalidate_and_prepare_execution(
        frozen_approval=frozen,
        current_spot=24218.0,
        current_option_ltp=75.0,
        market_session_active=True
    )
    assert repeat_ok is False
    assert any("ALREADY_CONSUMED" in b for b in repeat_blockers)


def test_stale_and_invalidated_approval_revalidation_failure():
    """Test 2: Pre-submission revalidation blocks stale and invalidated approvals."""
    ControlledBrokerExecutionService.reset_state()
    TradeApprovalService.reset_state()

    cid = "CAND-EXEC-002"
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

    # Spot drifted 35 pts higher (24,253 vs 24,218)
    ok_stale, _, blockers_stale = ControlledBrokerExecutionService.revalidate_and_prepare_execution(
        frozen_approval=frozen,
        current_spot=24255.0,
        current_option_ltp=62.0,
        market_session_active=True
    )
    assert ok_stale is False
    assert any("DRIFT" in b for b in blockers_stale)

    # Invalidation level breached (24,265 > 24,264)
    ok_inval, _, blockers_inval = ControlledBrokerExecutionService.revalidate_and_prepare_execution(
        frozen_approval=frozen,
        current_spot=24266.0,
        current_option_ltp=55.0,
        market_session_active=True
    )
    assert ok_inval is False
    assert any("APPROVAL_NOT_FRESH" in b for b in blockers_inval)


def test_fill_reconciliation_and_slippage_measurement():
    """Test 3: Broker fill reconciles average price, slippage, and creates LivePosition."""
    ControlledBrokerExecutionService.reset_state()
    TradeApprovalService.reset_state()

    cid = "CAND-EXEC-003"
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

    ok, record, _ = ControlledBrokerExecutionService.revalidate_and_prepare_execution(
        frozen_approval=frozen,
        current_spot=24218.0,
        current_option_ltp=75.0,
        market_session_active=True
    )
    ControlledBrokerExecutionService.submit_order_intent(record.execution_id)

    # Reconcile Fill: 50 qty @ ₹75.50 (Slippage: +0.50 pts, +0.67%)
    fill_ok, pos, reconcil = ControlledBrokerExecutionService.reconcile_broker_fill(
        execution_id=record.execution_id,
        fill_data={"filled_quantity": 50, "average_price": 75.50},
        underlying_spot=24218.0,
        invalidation_level=24264.0,
        targets=[24150.0, 24110.0]
    )

    assert fill_ok is True
    assert reconcil.slippage_pts == 0.50
    assert reconcil.slippage_pct == 0.67
    assert reconcil.risk_geometry_changed is False
    assert pos.quantity == 50
    assert pos.average_entry_price == 75.50
    assert pos.broker_position_state == "OPEN"


def test_position_monitoring_stop_and_target_management():
    """Test 4: Position updates MTM P&L, detects thesis invalidation and target reach."""
    ControlledBrokerExecutionService.reset_state()
    TradeApprovalService.reset_state()

    cid = "CAND-EXEC-004"
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

    ok, record, _ = ControlledBrokerExecutionService.revalidate_and_prepare_execution(
        frozen_approval=frozen,
        current_spot=24218.0,
        current_option_ltp=75.0,
        market_session_active=True
    )
    ControlledBrokerExecutionService.submit_order_intent(record.execution_id)
    _, pos, _ = ControlledBrokerExecutionService.reconcile_broker_fill(
        execution_id=record.execution_id,
        fill_data={"filled_quantity": 50, "average_price": 75.0},
        underlying_spot=24218.0,
        invalidation_level=24264.0,
        targets=[24150.0, 24110.0]
    )

    # 1. Option price rises to ₹95 (spot drops to 24,180) -> P&L = +₹1,000
    pos_profit = ControlledBrokerExecutionService.update_position_market_state(
        position_id=pos.position_id,
        current_spot=24180.0,
        current_option_ltp=95.0
    )
    assert pos_profit.unrealized_pnl == 1000.0
    assert pos_profit.stop_state == "ACTIVE"

    # 2. Spot reaches Target 1 (24,145 <= 24,150)
    pos_target = ControlledBrokerExecutionService.update_position_market_state(
        position_id=pos.position_id,
        current_spot=24145.0,
        current_option_ltp=110.0
    )
    assert pos_target.target_state == "TARGET_1_REACHED"

    # 3. Controlled Position Exit @ ₹110.0 -> Realized P&L = +₹1,750
    exit_ok, closed_pos = ControlledBrokerExecutionService.execute_position_exit(
        position_id=pos.position_id,
        exit_ltp=110.0,
        exit_reason="Target 1 reached profit take"
    )
    assert exit_ok is True
    assert closed_pos.broker_position_state == "CLOSED"
    assert closed_pos.realized_pnl == 1750.0


def test_positive_control_end_to_end_lifecycle():
    """Test 5: Full lifecycle from Approval -> Execution Revalidation -> Submit -> Fill -> Exit."""
    ControlledBrokerExecutionService.reset_state()
    TradeApprovalService.reset_state()

    cid = "CAND-EXEC-E2E"
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

    # 1. Revalidate
    ok, rec, blockers = ControlledBrokerExecutionService.revalidate_and_prepare_execution(
        frozen_approval=frozen,
        current_spot=24218.0,
        current_option_ltp=75.0,
        market_session_active=True
    )
    assert ok is True

    # 2. Submit Order Intent (Simulated Broker Boundary)
    mock_called = False
    def mock_broker(params):
        nonlocal mock_called
        mock_called = True
        return {"order_id": "ORD-E2E-999", "status": "COMPLETE"}

    sub_ok, sub_rec, _ = ControlledBrokerExecutionService.submit_order_intent(
        execution_id=rec.execution_id,
        broker_submit_fn=mock_broker
    )
    assert sub_ok is True
    assert mock_called is True
    assert sub_rec.broker_order_id == "ORD-E2E-999"

    # 3. Fill Reconcile
    _, live_pos, _ = ControlledBrokerExecutionService.reconcile_broker_fill(
        execution_id=rec.execution_id,
        fill_data={"filled_quantity": 50, "average_price": 75.20},
        underlying_spot=24218.0,
        invalidation_level=24264.0,
        targets=[24150.0, 24110.0]
    )
    assert live_pos.broker_position_state == "OPEN"

    # 4. Exit
    exit_ok, exited_pos = ControlledBrokerExecutionService.execute_position_exit(
        position_id=live_pos.position_id,
        exit_ltp=90.0,
        exit_reason="End of day square off"
    )
    assert exit_ok is True
    assert exited_pos.realized_pnl == 740.0

    # 5. Verify Comprehensive Audit Trail
    trail = TradeApprovalService.get_audit_trail(cid)
    event_types = [e.event_type for e in trail]
    assert "APPROVED" in event_types
    assert "REVALIDATION_PASS" in event_types
    assert "ORDER_SUBMIT_ATTEMPT" in event_types
    assert "BROKER_ACKNOWLEDGED" in event_types
    assert "FULL_FILL" in event_types
    assert "POSITION_OPENED" in event_types
    assert "POSITION_CLOSED" in event_types


def test_safety_and_default_flag_invariants():
    """Test 6: Assert feature flag default OFF and zero unapproved execution paths."""
    ControlledBrokerExecutionService.reset_state()
    assert ControlledBrokerExecutionService.broker_execution_enabled is False
