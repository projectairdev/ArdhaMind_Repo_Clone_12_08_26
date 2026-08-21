from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
import pytest

from src.proposal_engine.models import ProposalState, TradeProposal, OrderIntent
from src.proposal_engine.builder import ProposalBuilder, resolve_lot_size
from src.proposal_engine.audit_storage import ProposalAuditStorage


def test_proposal_models_serialization():
    intent = OrderIntent(
        proposal_id="PROP-12345",
        symbol="NIFTY24500CE",
        exchange="NFO",
        transaction_type="BUY",
        order_type="LIMIT",
        product="NRML",
        lots=2,
        lot_size=25,
        quantity=50,
        price=125.5,
        dry_run=True,
    )
    d = intent.to_dict()
    assert d["proposal_id"] == "PROP-12345"
    assert d["dry_run"] is True
    assert d["lots"] == 2
    assert d["quantity"] == 50

    prop = TradeProposal(
        proposal_id="PROP-12345",
        timestamp="2026-08-20T00:00:00Z",
        underlying="NIFTY",
        setup_type="MOMENTUM_BREAKOUT",
        direction="BULLISH",
        strike=24500,
        option_type="CE",
        contract_symbol="NIFTY 24500 CE",
        entry_price=125.0,
        stop_loss=95.0,
        target_1=170.0,
        target_2=200.0,
        risk_reward_ratio=1.5,
        confidence_score=85.0,
        priority_score=88.0,
        quality_score=82.0,
        max_loss_inr=1500.0,
        rationale=["Momentum breakout above VWAP", "PCR 1.25 confirms calls accumulation", "Favorable R:R"],
        invalidation_condition="Spot closes below 24450",
        state=ProposalState.PROPOSED.value,
        lots=2,
        lot_size=25,
        total_quantity=50,
        product="NRML",
        order_intent=d,
    )
    prop_dict = prop.to_dict()
    assert prop_dict["strike"] == 24500
    assert prop_dict["state"] == "PROPOSED"
    assert prop_dict["lots"] == 2
    assert prop_dict["total_quantity"] == 50
    assert prop_dict["order_intent"]["quantity"] == 50


def test_dynamic_lot_size_resolution():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_instruments.db"
        with sqlite3.connect(str(db_file)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE instruments (
                    instrument_token INTEGER PRIMARY KEY,
                    exchange_token INTEGER,
                    tradingsymbol TEXT,
                    name TEXT,
                    last_price REAL,
                    expiry TEXT,
                    strike REAL,
                    tick_size REAL,
                    lot_size INTEGER,
                    instrument_type TEXT,
                    segment TEXT,
                    exchange TEXT
                );
            """)
            cursor.execute("""
                INSERT INTO instruments (instrument_token, name, exchange, instrument_type, expiry, lot_size)
                VALUES (101, 'NIFTY', 'NFO', 'CE', '2026-08-27', 65);
            """)
            conn.commit()

        # Query test DB
        resolved = resolve_lot_size(underlying="NIFTY", default=25, db_path=db_file)
        assert resolved == 65

        # Fallback when underlying missing
        missing_res = resolve_lot_size(underlying="NONEXISTENT", default=25, db_path=db_file)
        assert missing_res == 25


def test_proposal_lot_scaling_and_max_loss():
    mock_opp = {
        "opportunity_id": "OPP-BULL-24500",
        "setup_type": "MOMENTUM_BREAKOUT",
        "direction": "BULLISH",
        "provisional_strike": 24500,
        "option_type": "CE",
        "priority_score": 82.0,
        "quality_score": 80.0,
        "confidence_score": 85.0,
        "reward_risk_ratio": 1.8,
        "estimated_risk": 20.0,
        "estimated_reward": 40.0,
        "suggested_levels": {
            "entry_reference": 100.0,
            "invalidation_level": 80.0,
            "target_zone_1": 140.0,
        },
    }

    # 1 Lot
    prop_1lot = ProposalBuilder.build_proposal(mock_opp, {}, lots=1)
    lot_sz = prop_1lot.lot_size
    assert prop_1lot.lots == 1
    assert prop_1lot.total_quantity == 1 * lot_sz
    assert prop_1lot.order_intent["lots"] == 1
    assert prop_1lot.order_intent["quantity"] == 1 * lot_sz

    # 5 Lots
    prop_5lots = ProposalBuilder.build_proposal(mock_opp, {}, lots=5)
    assert prop_5lots.lots == 5
    assert prop_5lots.total_quantity == 5 * lot_sz
    assert prop_5lots.order_intent["lots"] == 5
    assert prop_5lots.order_intent["quantity"] == 5 * lot_sz
    assert prop_5lots.max_loss_inr == pytest.approx(prop_1lot.max_loss_inr * 5, rel=1e-2)

    # Dynamic exposure recalculation method
    prop_1lot.recalculate_exposure(lots=3, product="MIS")
    assert prop_1lot.lots == 3
    assert prop_1lot.total_quantity == 3 * lot_sz
    assert prop_1lot.product == "MIS"
    assert prop_1lot.order_intent["product"] == "MIS"
    assert prop_1lot.max_loss_inr == pytest.approx(prop_5lots.max_loss_inr * (3 / 5), rel=1e-2)


def test_proposal_builder_no_trade_fallback():
    no_trade_opp = {
        "status": "NO_TRADE",
        "reason": "NO_HIGH_CONVICTION_SETUP",
        "message": "No setup meets minimum thresholds",
        "priority_score": 0,
    }
    prop = ProposalBuilder.build_proposal(no_trade_opp, {})
    assert prop.state == ProposalState.NO_TRADE.value
    assert prop.contract_symbol == "NO ACTIVE PROPOSAL"
    assert prop.direction == "NEUTRAL"
    assert prop.entry_price == 0.0


def test_audit_storage_lifecycle_with_margin_and_lots():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "proposals_audit.db"
        storage = ProposalAuditStorage(db_path=db_file)

        prop_data = {
            "proposal_id": "PROP-TEST-LOTS-001",
            "strike": 24500,
            "direction": "BULLISH",
            "state": "PROPOSED",
            "lots": 2,
            "lot_size": 25,
            "total_quantity": 50,
            "product": "NRML",
        }

        # 1. Insert Proposal
        saved = storage.record_proposal(
            proposal_id="PROP-TEST-LOTS-001",
            state="PROPOSED",
            payload=prop_data,
            risk_eval={
                "margin_required": 6250.0,
                "available_margin": 150000.0,
                "margin_sufficient": True,
                "lots": 2,
                "total_quantity": 50,
            },
        )
        assert saved is True

        # 2. Query Proposal
        rec = storage.get_proposal("PROP-TEST-LOTS-001")
        assert rec is not None
        assert rec["state"] == "PROPOSED"
        assert rec["payload"]["lots"] == 2
        assert rec["payload"]["total_quantity"] == 50
        assert rec["risk_evaluation"]["margin_sufficient"] is True
        assert rec["risk_evaluation"]["margin_required"] == 6250.0

        # 3. Update to Approved / Dry-Run Recorded
        prop_data["state"] = "DRY_RUN_RECORDED"
        updated = storage.record_proposal(
            proposal_id="PROP-TEST-LOTS-001",
            state="DRY_RUN_RECORDED",
            payload=prop_data,
            approval_timestamp="2026-08-20T04:15:00Z",
            risk_eval={
                "margin_required": 6250.0,
                "available_margin": 150000.0,
                "margin_sufficient": True,
                "lots": 2,
            }
        )
        assert updated is True

        rec_updated = storage.get_proposal("PROP-TEST-LOTS-001")
        assert rec_updated["state"] == "DRY_RUN_RECORDED"
        assert rec_updated["approval_timestamp"] == "2026-08-20T04:15:00Z"
