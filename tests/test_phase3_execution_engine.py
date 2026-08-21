from __future__ import annotations

import os
import tempfile
from pathlib import Path
import pytest

from src.proposal_engine.models import (
    BrokerOrderState,
    ClosingReason,
    ExecutionOperation,
    JournalNote,
    OperationStatus,
    OperationType,
    OrderRecord,
    PositionState,
    ProposalState,
    TradeJournalRecord,
    TradeProposal,
)
from src.proposal_engine.audit_storage import ProposalAuditStorage
from src.proposal_engine.safety_policy import (
    BlockerCode,
    ExecutionSafetyPolicy,
    SafetyGatekeeper,
)


def test_order_record_and_position_serialization():
    order = OrderRecord(
        order_id="ORD-TEST-001",
        proposal_id="PROP-1001",
        intent_id="INTENT-1001",
        broker_order_id="240820000000001",
        contract_symbol="NIFTY 24500 CE",
        exchange="NFO",
        transaction_type="BUY",
        order_type="LIMIT",
        product="NRML",
        quantity=50,
        filled_quantity=50,
        remaining_quantity=0,
        price=125.0,
        average_price=124.8,
        status=BrokerOrderState.FILLED.value,
        rejection_reason=None,
        provenance="ARDHAMIND",
        placed_at="2026-08-20T04:20:00Z",
        updated_at="2026-08-20T04:20:02Z",
    )
    d = order.to_dict()
    assert d["order_id"] == "ORD-TEST-001"
    assert d["broker_order_id"] == "240820000000001"
    assert d["status"] == "FILLED"
    assert d["filled_quantity"] == 50
    assert d["remaining_quantity"] == 0
    assert d["provenance"] == "ARDHAMIND"

    pos = PositionState(
        position_id="POS-ORD-TEST-001",
        order_id="ORD-TEST-001",
        contract_symbol="NIFTY 24500 CE",
        product="NRML",
        quantity=50,
        buy_price=124.8,
        current_ltp=135.0,
        unrealized_pnl=510.0,
        stop_loss=95.0,
        target=170.0,
        provenance="ARDHAMIND",
        status="OPEN",
        updated_at="2026-08-20T04:20:05Z",
    )
    pos_d = pos.to_dict()
    assert pos_d["position_id"] == "POS-ORD-TEST-001"
    assert pos_d["unrealized_pnl"] == 510.0
    assert pos_d["status"] == "OPEN"
    assert pos_d["provenance"] == "ARDHAMIND"


def test_persistent_idempotency_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "proposals_audit.db"
        storage = ProposalAuditStorage(db_path=db_path)

        op = ExecutionOperation(
            operation_id="OP-001",
            idempotency_key="IDEMP-UNIQUE-KEY-123",
            operation_type=OperationType.ORDER_SUBMIT.value,
            entity_type="ORDER",
            entity_id="ORD-001",
            requested_at="2026-08-20T04:20:00Z",
            current_status=OperationStatus.INITIATED.value,
        )
        saved = storage.record_operation(op)
        assert saved is True

        # Query by Idempotency Key
        fetched = storage.get_operation_by_idempotency_key("IDEMP-UNIQUE-KEY-123")
        assert fetched is not None
        assert fetched["operation_id"] == "OP-001"
        assert fetched["current_status"] == "INITIATED"

        # Update Operation Status
        storage.update_operation_status(
            operation_id="OP-001",
            status=OperationStatus.SUBMITTED.value,
            broker_order_id="BK-98765",
            result_payload={"broker_order_id": "BK-98765"}
        )

        fetched_after = storage.get_operation_by_idempotency_key("IDEMP-UNIQUE-KEY-123")
        assert fetched_after["current_status"] == "SUBMITTED"
        assert fetched_after["broker_order_id"] == "BK-98765"


def test_order_cancellation_and_partial_fill_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "proposals_audit.db"
        storage = ProposalAuditStorage(db_path=db_path)

        order = OrderRecord(
            order_id="ORD-PARTIAL-001",
            proposal_id="PROP-001",
            intent_id="INTENT-PARTIAL-001",
            broker_order_id="BK-PARTIAL-1",
            contract_symbol="NIFTY 24500 CE",
            exchange="NFO",
            transaction_type="BUY",
            order_type="LIMIT",
            product="NRML",
            quantity=100,
            price=120.0,
            status=BrokerOrderState.SUBMITTED.value,
        )
        storage.record_order(order)

        # Partial fill of 40 units
        storage.update_order_status(
            order_id="ORD-PARTIAL-001",
            status=BrokerOrderState.PARTIALLY_FILLED.value,
            filled_quantity=40,
            average_price=120.0,
        )

        ord_updated = storage.get_order("ORD-PARTIAL-001")
        assert ord_updated["status"] == "PARTIALLY_FILLED"
        assert ord_updated["filled_quantity"] == 40
        assert ord_updated["remaining_quantity"] == 60

        # Cancel remaining 60 units
        storage.update_order_status(
            order_id="ORD-PARTIAL-001",
            status=BrokerOrderState.CANCELLED.value,
            cancellation_reason="Trader cancelled remaining quantity",
        )

        ord_cancelled = storage.get_order("ORD-PARTIAL-001")
        assert ord_cancelled["status"] == "CANCELLED"
        assert ord_cancelled["cancellation_reason"] == "Trader cancelled remaining quantity"
        assert ord_cancelled["filled_quantity"] == 40


def test_position_exit_and_closed_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "proposals_audit.db"
        storage = ProposalAuditStorage(db_path=db_path)

        pos = PositionState(
            position_id="POS-EXIT-001",
            order_id="ORD-EXIT-001",
            contract_symbol="NIFTY 24500 CE",
            product="NRML",
            quantity=50,
            buy_price=100.0,
            current_ltp=120.0,
            unrealized_pnl=1000.0,
            stop_loss=80.0,
            target=140.0,
            status="OPEN"
        )
        storage.record_position(pos)

        open_list = storage.get_open_positions()
        assert len(open_list) == 1
        assert open_list[0]["position_id"] == "POS-EXIT-001"

        # Update position exit
        storage.update_position_exit(
            position_id="POS-EXIT-001",
            exit_order_id="BK-EXIT-ORD-99",
            exit_price=125.0,
            realized_pnl=1250.0,
            closed_at="2026-08-20T04:30:00Z",
            status="CLOSED"
        )

        open_after = storage.get_open_positions()
        assert len(open_after) == 0

        closed_pos = storage.get_position("POS-EXIT-001")
        assert closed_pos["status"] == "CLOSED"
        assert closed_pos["exit_order_id"] == "BK-EXIT-ORD-99"
        assert closed_pos["exit_price"] == 125.0
        assert closed_pos["realized_pnl_analytics"] == 1250.0
        assert closed_pos["unrealized_pnl"] == 0.0


def test_journal_lineage_and_slippage_calculation():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "proposals_audit.db"
        storage = ProposalAuditStorage(db_path=db_path)

        # 1. Test Journal Record with multiple fills
        journal = TradeJournalRecord(
            journal_id="JRN-TEST-100",
            proposal_id="PROP-TEST-100",
            source_opportunity_id="OPP-999",
            trading_session_date="2026-08-20",
            underlying="NIFTY",
            contract_symbol="NIFTY 24500 CE",
            direction="BULLISH",
            setup_type="PVP_BREAKOUT",
            proposed_entry=100.0,
            proposed_stop=80.0,
            proposed_target_1=140.0,
            proposed_target_2=160.0,
            entry_fills=[
                {"quantity": 25, "price": 102.0},
                {"quantity": 25, "price": 104.0}
            ],
            exit_fills=[
                {"quantity": 50, "price": 138.0}
            ],
            closing_reason=ClosingReason.TARGET_1_EXIT.value
        )
        journal.calculate_metrics()

        # Weighted avg entry: (25*102 + 25*104) / 50 = 103.0
        assert journal.weighted_average_entry == 103.0
        assert journal.entry_quantity == 50

        # Direction-aware entry slippage (BUY): actual(103) > intended(100) => +3.0 pts adverse
        assert journal.entry_slippage_pts == 3.0
        assert journal.entry_slippage_pct == 3.0

        # Weighted avg exit: 138.0
        assert journal.weighted_average_exit == 138.0

        # Realized trade PnL: (138 - 103) * 50 = 1750.0
        assert journal.realized_trade_pnl == 1750.0

        # Planned risk: (100 - 80) * 50 = 1000.0
        assert journal.planned_risk == 1000.0

        # Realized R-multiple: 1750 / 1000 = 1.75R
        assert journal.realized_r_multiple == 1.75

        # Persist and query
        saved = storage.record_journal_entry(journal)
        assert saved is True

        fetched = storage.get_journal_entry("JRN-TEST-100")
        assert fetched is not None
        assert fetched["weighted_average_entry"] == 103.0
        assert fetched["realized_trade_pnl"] == 1750.0

        # 2. Add Mutable Trader Note
        note = JournalNote(
            note_id="NOTE-001",
            journal_id="JRN-TEST-100",
            note_text="Good trade execution, partial target hit smoothly.",
            tags=["DISCIPLINE", "TARGET_HIT"]
        )
        note_saved = storage.add_journal_note(note)
        assert note_saved is True

        notes = storage.get_journal_notes("JRN-TEST-100")
        assert len(notes) == 1
        assert notes[0]["tags"] == ["DISCIPLINE", "TARGET_HIT"]

        # 3. Analytics Summary
        summary = storage.get_journal_analytics_summary()
        assert summary["total_trades"] == 1
        assert summary["win_count"] == 1
        assert summary["total_realized_pnl"] == 1750.0


def test_safety_gatekeeper_circuit_breakers():
    gatekeeper = SafetyGatekeeper(
        policy=ExecutionSafetyPolicy(
            daily_loss_limit=10000.0,
            max_risk_per_trade=5000.0,
            max_open_positions=2,
            max_total_open_quantity=100,
            price_drift_tolerance_pct=3.0,
            kill_switch_active=False
        )
    )

    prop = TradeProposal(
        proposal_id="PROP-SAFE-1",
        timestamp="2026-08-20T04:00:00Z",
        underlying="NIFTY",
        setup_type="PVP_BREAKOUT",
        direction="BULLISH",
        strike=24500,
        option_type="CE",
        contract_symbol="NIFTY 24500 CE",
        entry_price=100.0,
        stop_loss=80.0,
        target_1=140.0,
        target_2=160.0,
        risk_reward_ratio=2.0,
        confidence_score=0.8,
        priority_score=0.8,
        quality_score=0.8,
        max_loss_inr=1000.0,
        rationale=["Good volume"],
        invalidation_condition="Below 24450",
        lots=1,
        lot_size=25,
        total_quantity=25
    )

    # 1. Normal Valid Entry
    res = gatekeeper.evaluate_entry_order(
        proposal=prop,
        fresh_quote={"last_price": 101.0},
        current_daily_realized_loss=2000.0,
        active_positions=[],
        active_orders=[],
        broker_connected=True,
        unresolved_operations=[]
    )
    assert res.passed is True

    # 2. Daily Loss Limit Breach
    res_daily_loss = gatekeeper.evaluate_entry_order(
        proposal=prop,
        fresh_quote={"last_price": 101.0},
        current_daily_realized_loss=12000.0,  # Exceeds 10000.0 limit
        active_positions=[],
        active_orders=[],
        broker_connected=True,
        unresolved_operations=[]
    )
    assert res_daily_loss.passed is False
    assert res_daily_loss.blocker_code == BlockerCode.DAILY_LOSS_LIMIT_REACHED.value

    # 3. Kill Switch Active
    res_ks = gatekeeper.evaluate_entry_order(
        proposal=prop,
        fresh_quote={"last_price": 101.0},
        current_daily_realized_loss=0.0,
        active_positions=[],
        active_orders=[],
        broker_connected=True,
        unresolved_operations=[],
        kill_switch_active=True
    )
    assert res_ks.passed is False
    assert res_ks.blocker_code == BlockerCode.KILL_SWITCH_ACTIVE.value

    # 4. Max Open Positions Reached
    res_pos = gatekeeper.evaluate_entry_order(
        proposal=prop,
        fresh_quote={"last_price": 101.0},
        current_daily_realized_loss=0.0,
        active_positions=[{"contract_symbol": "NIFTY 24400 CE", "quantity": 25}, {"contract_symbol": "NIFTY 24300 CE", "quantity": 25}],
        active_orders=[],
        broker_connected=True,
        unresolved_operations=[]
    )
    assert res_pos.passed is False
    assert res_pos.blocker_code == BlockerCode.MAX_POSITIONS_REACHED.value

    # 5. Price Drift Exceeded
    res_drift = gatekeeper.evaluate_entry_order(
        proposal=prop,
        fresh_quote={"last_price": 108.0},  # 8% drift > 3% tolerance
        current_daily_realized_loss=0.0,
        active_positions=[],
        active_orders=[],
        broker_connected=True,
        unresolved_operations=[]
    )
    assert res_drift.passed is False
    assert res_drift.blocker_code == BlockerCode.PRICE_DRIFT_REQUIRES_RECONFIRMATION.value

    # 6. Unresolved Operations Lockout
    res_unres = gatekeeper.evaluate_entry_order(
        proposal=prop,
        fresh_quote={"last_price": 101.0},
        current_daily_realized_loss=0.0,
        active_positions=[],
        active_orders=[],
        broker_connected=True,
        unresolved_operations=[{"operation_id": "OP-1", "current_status": "OUTCOME_UNVERIFIED"}]
    )
    assert res_unres.passed is False
    assert res_unres.blocker_code == BlockerCode.UNRESOLVED_OPERATION_LOCKOUT.value
