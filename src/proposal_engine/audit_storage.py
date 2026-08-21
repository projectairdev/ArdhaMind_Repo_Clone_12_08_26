from __future__ import annotations

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.proposal_engine.models import (
    BrokerOrderState,
    ClosingReason,
    ExecutionOperation,
    JournalNote,
    OperationStatus,
    OperationType,
    OrderRecord,
    PositionState,
    TradeJournalRecord,
)

logger = logging.getLogger("ProposalAuditStorage")

DEFAULT_DB_PATH = Path("/opt/ardhamind/staging/data/proposals_audit.db")


class ProposalAuditStorage:
    """
    SQLite audit log persistence for Phase 3 Trade Proposals, Approvals, Orders,
    Positions, Idempotent Execution Operations, and the Trade Journal Lineage.
    """

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._ensure_db()

    def _ensure_db(self) -> None:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                # Proposals Table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS proposals_audit (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        proposal_id TEXT UNIQUE NOT NULL,
                        state TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        risk_eval_json TEXT,
                        approval_timestamp TEXT,
                        rejection_reason TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_proposals_audit_proposal_id
                    ON proposals_audit(proposal_id)
                    """
                )

                # Execution Operations Table (Persistent Idempotency)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS execution_operations (
                        operation_id TEXT PRIMARY KEY,
                        idempotency_key TEXT UNIQUE NOT NULL,
                        operation_type TEXT NOT NULL,
                        entity_type TEXT,
                        entity_id TEXT,
                        requested_at TEXT NOT NULL,
                        current_status TEXT NOT NULL,
                        broker_order_id TEXT,
                        result_payload TEXT,
                        error_message TEXT
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_exec_ops_idempotency
                    ON execution_operations(idempotency_key)
                    """
                )

                # Orders Table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id TEXT PRIMARY KEY,
                        proposal_id TEXT NOT NULL,
                        intent_id TEXT UNIQUE NOT NULL,
                        broker_order_id TEXT,
                        contract_symbol TEXT NOT NULL,
                        exchange TEXT NOT NULL,
                        transaction_type TEXT NOT NULL,
                        order_type TEXT NOT NULL,
                        product TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        filled_quantity INTEGER DEFAULT 0,
                        remaining_quantity INTEGER DEFAULT 0,
                        price REAL NOT NULL,
                        average_price REAL DEFAULT 0.0,
                        status TEXT NOT NULL,
                        rejection_reason TEXT,
                        cancellation_reason TEXT,
                        provenance TEXT DEFAULT 'ARDHAMIND',
                        placed_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        raw_payload TEXT
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_orders_intent_id ON orders(intent_id)
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_orders_broker_order_id ON orders(broker_order_id)
                    """
                )

                # Order Events Table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS order_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT UNIQUE NOT NULL,
                        order_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT,
                        raw_data TEXT,
                        timestamp TEXT NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_order_events_order_id ON order_events(order_id)
                    """
                )

                # Positions Table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS positions (
                        position_id TEXT PRIMARY KEY,
                        order_id TEXT NOT NULL,
                        contract_symbol TEXT NOT NULL,
                        product TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        buy_price REAL NOT NULL,
                        current_ltp REAL NOT NULL,
                        unrealized_pnl REAL NOT NULL,
                        stop_loss REAL NOT NULL,
                        target REAL NOT NULL,
                        realized_pnl_analytics REAL DEFAULT 0.0,
                        exit_price REAL,
                        exit_order_id TEXT,
                        closed_at TEXT,
                        provenance TEXT DEFAULT 'ARDHAMIND',
                        status TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )

                # Trade Journal Table (Milestone 5)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trade_journal (
                        journal_id TEXT PRIMARY KEY,
                        proposal_id TEXT UNIQUE NOT NULL,
                        source_opportunity_id TEXT,
                        trading_session_date TEXT NOT NULL,
                        underlying TEXT NOT NULL,
                        contract_symbol TEXT NOT NULL,
                        expiry TEXT,
                        strike INTEGER,
                        option_type TEXT,
                        direction TEXT NOT NULL,
                        setup_type TEXT NOT NULL,
                        proposal_created_at TEXT NOT NULL,
                        approved_at TEXT,
                        entry_submitted_at TEXT,
                        opened_at TEXT,
                        closed_at TEXT,
                        duration_seconds REAL,
                        entry_order_ids_json TEXT,
                        exit_order_ids_json TEXT,
                        entry_fills_json TEXT,
                        exit_fills_json TEXT,
                        proposed_entry REAL NOT NULL,
                        weighted_average_entry REAL NOT NULL,
                        proposed_stop REAL NOT NULL,
                        proposed_target_1 REAL NOT NULL,
                        proposed_target_2 REAL NOT NULL,
                        weighted_average_exit REAL DEFAULT 0.0,
                        entry_quantity INTEGER NOT NULL,
                        exit_quantity INTEGER DEFAULT 0,
                        confidence_at_entry REAL,
                        priority_at_entry REAL,
                        market_regime_at_entry TEXT,
                        briefing_id_at_entry TEXT,
                        scenario_id_at_entry TEXT,
                        prediction_snapshot_id_at_entry TEXT,
                        closing_reason TEXT DEFAULT 'UNKNOWN',
                        trader_overrides_json TEXT,
                        provenance TEXT DEFAULT 'ARDHAMIND',
                        entry_slippage_pts REAL DEFAULT 0.0,
                        entry_slippage_pct REAL DEFAULT 0.0,
                        exit_slippage_pts REAL DEFAULT 0.0,
                        exit_slippage_pct REAL DEFAULT 0.0,
                        hold_duration REAL DEFAULT 0.0,
                        planned_risk REAL DEFAULT 0.0,
                        realized_trade_pnl REAL DEFAULT 0.0,
                        planned_rr REAL DEFAULT 0.0,
                        realized_r_multiple REAL DEFAULT 0.0,
                        status TEXT DEFAULT 'CLOSED',
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_trade_journal_session
                    ON trade_journal(trading_session_date)
                    """
                )

                # Journal Notes Table (Milestone 5)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS journal_notes (
                        note_id TEXT PRIMARY KEY,
                        journal_id TEXT NOT NULL,
                        note_text TEXT NOT NULL,
                        tags_json TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_journal_notes_jid
                    ON journal_notes(journal_id)
                    """
                )

                # Journal Corrections Table (Milestone 5)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS journal_corrections (
                        correction_id TEXT PRIMARY KEY,
                        journal_id TEXT NOT NULL,
                        correction_type TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        prior_data_json TEXT NOT NULL,
                        new_data_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )

                # Perform dynamic column upgrades if tables existed previously
                try:
                    cursor.execute("ALTER TABLE orders ADD COLUMN remaining_quantity INTEGER DEFAULT 0")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE orders ADD COLUMN cancellation_reason TEXT")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE orders ADD COLUMN provenance TEXT DEFAULT 'ARDHAMIND'")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE positions ADD COLUMN realized_pnl_analytics REAL DEFAULT 0.0")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE positions ADD COLUMN exit_price REAL")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE positions ADD COLUMN exit_order_id TEXT")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE positions ADD COLUMN closed_at TEXT")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE positions ADD COLUMN provenance TEXT DEFAULT 'ARDHAMIND'")
                except Exception:
                    pass

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize proposal audit database at {self.db_path}: {e}")

    # ── PROPOSALS MANAGEMENT ──

    def record_proposal(
        self,
        proposal_id: str,
        state: str,
        payload: Dict[str, Any],
        risk_eval: Optional[Dict[str, Any]] = None,
        approval_timestamp: Optional[str] = None,
        rejection_reason: Optional[str] = None,
    ) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO proposals_audit (
                        proposal_id, state, payload_json, risk_eval_json,
                        approval_timestamp, rejection_reason, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(proposal_id) DO UPDATE SET
                        state=excluded.state,
                        payload_json=excluded.payload_json,
                        risk_eval_json=COALESCE(excluded.risk_eval_json, proposals_audit.risk_eval_json),
                        approval_timestamp=COALESCE(excluded.approval_timestamp, proposals_audit.approval_timestamp),
                        rejection_reason=COALESCE(excluded.rejection_reason, proposals_audit.rejection_reason),
                        updated_at=excluded.updated_at
                    """,
                    (
                        proposal_id,
                        state,
                        json.dumps(payload),
                        json.dumps(risk_eval) if risk_eval else None,
                        approval_timestamp,
                        rejection_reason,
                        now_iso,
                        now_iso,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error persisting proposal audit for {proposal_id}: {e}")
            return False

    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT proposal_id, state, payload_json, risk_eval_json, approval_timestamp, rejection_reason, created_at, updated_at
                    FROM proposals_audit
                    WHERE proposal_id = ?
                    """,
                    (proposal_id,),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "proposal_id": row[0],
                        "state": row[1],
                        "payload": json.loads(row[2]) if row[2] else {},
                        "risk_evaluation": json.loads(row[3]) if row[3] else {},
                        "approval_timestamp": row[4],
                        "rejection_reason": row[5],
                        "created_at": row[6],
                        "updated_at": row[7],
                    }
        except Exception as e:
            logger.error(f"Error fetching proposal {proposal_id}: {e}")
        return None

    def get_recent_audits(self, limit: int = 50) -> List[Dict[str, Any]]:
        results = []
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT proposal_id, state, payload_json, risk_eval_json, approval_timestamp, rejection_reason, created_at, updated_at
                    FROM proposals_audit
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                for row in cursor.fetchall():
                    results.append(
                        {
                            "proposal_id": row[0],
                            "state": row[1],
                            "payload": json.loads(row[2]) if row[2] else {},
                            "risk_evaluation": json.loads(row[3]) if row[3] else {},
                            "approval_timestamp": row[4],
                            "rejection_reason": row[5],
                            "created_at": row[6],
                            "updated_at": row[7],
                        }
                    )
        except Exception as e:
            logger.error(f"Error fetching recent audits: {e}")
        return results

    # ── PERSISTENT IDEMPOTENCY (EXECUTION OPERATIONS) ──

    def record_operation(self, op: ExecutionOperation) -> bool:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO execution_operations (
                        operation_id, idempotency_key, operation_type, entity_type, entity_id,
                        requested_at, current_status, broker_order_id, result_payload, error_message
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(idempotency_key) DO UPDATE SET
                        current_status=excluded.current_status,
                        broker_order_id=COALESCE(excluded.broker_order_id, execution_operations.broker_order_id),
                        result_payload=COALESCE(excluded.result_payload, execution_operations.result_payload),
                        error_message=COALESCE(excluded.error_message, execution_operations.error_message)
                    """,
                    (
                        op.operation_id,
                        op.idempotency_key,
                        op.operation_type,
                        op.entity_type,
                        op.entity_id,
                        op.requested_at,
                        op.current_status,
                        op.broker_order_id,
                        json.dumps(op.result_payload) if op.result_payload else None,
                        op.error_message,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording operation {op.operation_id}: {e}")
            return False

    def get_operation_by_idempotency_key(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT operation_id, idempotency_key, operation_type, entity_type, entity_id,
                           requested_at, current_status, broker_order_id, result_payload, error_message
                    FROM execution_operations
                    WHERE idempotency_key = ?
                    """,
                    (idempotency_key,),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "operation_id": row[0],
                        "idempotency_key": row[1],
                        "operation_type": row[2],
                        "entity_type": row[3],
                        "entity_id": row[4],
                        "requested_at": row[5],
                        "current_status": row[6],
                        "broker_order_id": row[7],
                        "result_payload": json.loads(row[8]) if row[8] else {},
                        "error_message": row[9],
                    }
        except Exception as e:
            logger.error(f"Error fetching operation by idempotency key {idempotency_key}: {e}")
        return None

    def update_operation_status(
        self,
        operation_id: str,
        status: str,
        broker_order_id: Optional[str] = None,
        result_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE execution_operations
                    SET current_status = ?,
                        broker_order_id = COALESCE(?, broker_order_id),
                        result_payload = COALESCE(?, result_payload),
                        error_message = COALESCE(?, error_message)
                    WHERE operation_id = ?
                    """,
                    (
                        status,
                        broker_order_id,
                        json.dumps(result_payload) if result_payload else None,
                        error_message,
                        operation_id,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating operation status for {operation_id}: {e}")
            return False

    def get_unresolved_operations(self) -> List[Dict[str, Any]]:
        results = []
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT operation_id, idempotency_key, operation_type, entity_type, entity_id,
                           requested_at, current_status, broker_order_id, result_payload, error_message
                    FROM execution_operations
                    WHERE current_status IN ('INITIATED', 'SUBMITTED', 'OUTCOME_UNVERIFIED')
                    ORDER BY requested_at DESC
                    """
                )
                for row in cursor.fetchall():
                    results.append(
                        {
                            "operation_id": row[0],
                            "idempotency_key": row[1],
                            "operation_type": row[2],
                            "entity_type": row[3],
                            "entity_id": row[4],
                            "requested_at": row[5],
                            "current_status": row[6],
                            "broker_order_id": row[7],
                            "result_payload": json.loads(row[8]) if row[8] else {},
                            "error_message": row[9],
                        }
                    )
        except Exception as e:
            logger.error(f"Error fetching unresolved operations: {e}")
        return results

    # ── ORDERS MANAGEMENT ──

    def record_order(self, order: OrderRecord) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO orders (
                        order_id, proposal_id, intent_id, broker_order_id, contract_symbol,
                        exchange, transaction_type, order_type, product, quantity, filled_quantity,
                        remaining_quantity, price, average_price, status, rejection_reason,
                        cancellation_reason, provenance, placed_at, updated_at, raw_payload
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(order_id) DO UPDATE SET
                        broker_order_id=COALESCE(excluded.broker_order_id, orders.broker_order_id),
                        filled_quantity=excluded.filled_quantity,
                        remaining_quantity=excluded.remaining_quantity,
                        average_price=excluded.average_price,
                        status=excluded.status,
                        rejection_reason=COALESCE(excluded.rejection_reason, orders.rejection_reason),
                        cancellation_reason=COALESCE(excluded.cancellation_reason, orders.cancellation_reason),
                        provenance=COALESCE(excluded.provenance, orders.provenance),
                        updated_at=excluded.updated_at,
                        raw_payload=excluded.raw_payload
                    """,
                    (
                        order.order_id,
                        order.proposal_id,
                        order.intent_id,
                        order.broker_order_id,
                        order.contract_symbol,
                        order.exchange,
                        order.transaction_type,
                        order.order_type,
                        order.product,
                        order.quantity,
                        order.filled_quantity,
                        order.remaining_quantity or max(0, order.quantity - order.filled_quantity),
                        order.price,
                        order.average_price,
                        order.status,
                        order.rejection_reason,
                        order.cancellation_reason,
                        order.provenance or "ARDHAMIND",
                        order.placed_at or now_iso,
                        now_iso,
                        json.dumps(order.raw_payload),
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording order {order.order_id}: {e}")
            return False

    def update_order_status(
        self,
        order_id: str,
        status: str,
        filled_quantity: int = 0,
        average_price: float = 0.0,
        broker_order_id: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        cancellation_reason: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE orders
                    SET status = ?,
                        filled_quantity = MAX(filled_quantity, ?),
                        remaining_quantity = MAX(0, quantity - MAX(filled_quantity, ?)),
                        average_price = CASE WHEN ? > 0 THEN ? ELSE average_price END,
                        broker_order_id = COALESCE(?, broker_order_id),
                        rejection_reason = COALESCE(?, rejection_reason),
                        cancellation_reason = COALESCE(?, cancellation_reason),
                        raw_payload = COALESCE(?, raw_payload),
                        updated_at = ?
                    WHERE order_id = ?
                    """,
                    (
                        status,
                        filled_quantity,
                        filled_quantity,
                        average_price,
                        average_price,
                        broker_order_id,
                        rejection_reason,
                        cancellation_reason,
                        json.dumps(raw_payload) if raw_payload else None,
                        now_iso,
                        order_id,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {e}")
            return False

    def record_order_event(
        self,
        order_id: str,
        event_type: str,
        status: str,
        message: str = "",
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        event_id = f"EVT-{uuid.uuid4().hex[:12]}"
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO order_events (
                        event_id, order_id, event_type, status, message, raw_data, timestamp
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        order_id,
                        event_type,
                        status,
                        message,
                        json.dumps(raw_data) if raw_data else None,
                        now_iso,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording order event for {order_id}: {e}")
            return False

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT order_id, proposal_id, intent_id, broker_order_id, contract_symbol,
                           exchange, transaction_type, order_type, product, quantity, filled_quantity,
                           remaining_quantity, price, average_price, status, rejection_reason,
                           cancellation_reason, provenance, placed_at, updated_at, raw_payload
                    FROM orders
                    WHERE order_id = ?
                    """,
                    (order_id,),
                )
                row = cursor.fetchone()
                if row:
                    return self._map_order_row(row)
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}")
        return None

    def get_order_by_broker_id(self, broker_order_id: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT order_id, proposal_id, intent_id, broker_order_id, contract_symbol,
                           exchange, transaction_type, order_type, product, quantity, filled_quantity,
                           remaining_quantity, price, average_price, status, rejection_reason,
                           cancellation_reason, provenance, placed_at, updated_at, raw_payload
                    FROM orders
                    WHERE broker_order_id = ?
                    """,
                    (str(broker_order_id),),
                )
                row = cursor.fetchone()
                if row:
                    return self._map_order_row(row)
        except Exception as e:
            logger.error(f"Error fetching order by broker_order_id {broker_order_id}: {e}")
        return None

    def get_order_by_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT order_id, proposal_id, intent_id, broker_order_id, contract_symbol,
                           exchange, transaction_type, order_type, product, quantity, filled_quantity,
                           remaining_quantity, price, average_price, status, rejection_reason,
                           cancellation_reason, provenance, placed_at, updated_at, raw_payload
                    FROM orders
                    WHERE intent_id = ?
                    """,
                    (intent_id,),
                )
                row = cursor.fetchone()
                if row:
                    return self._map_order_row(row)
        except Exception as e:
            logger.error(f"Error fetching order by intent {intent_id}: {e}")
        return None

    def get_order_by_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT order_id, proposal_id, intent_id, broker_order_id, contract_symbol,
                           exchange, transaction_type, order_type, product, quantity, filled_quantity,
                           remaining_quantity, price, average_price, status, rejection_reason,
                           cancellation_reason, provenance, placed_at, updated_at, raw_payload
                    FROM orders
                    WHERE proposal_id = ?
                    ORDER BY updated_at DESC LIMIT 1
                    """,
                    (proposal_id,),
                )
                row = cursor.fetchone()
                if row:
                    return self._map_order_row(row)
        except Exception as e:
            logger.error(f"Error fetching order by proposal {proposal_id}: {e}")
        return None

    def get_active_orders(self) -> List[Dict[str, Any]]:
        results = []
        non_terminal = (
            BrokerOrderState.SUBMITTING.value,
            BrokerOrderState.SUBMITTED.value,
            BrokerOrderState.ACKNOWLEDGED.value,
            BrokerOrderState.OPEN.value,
            BrokerOrderState.PARTIALLY_FILLED.value,
            BrokerOrderState.CANCEL_REQUESTED.value,
            BrokerOrderState.CANCEL_OUTCOME_UNVERIFIED.value,
            BrokerOrderState.EXIT_REQUESTED.value,
            BrokerOrderState.EXIT_OUTCOME_UNVERIFIED.value,
            BrokerOrderState.SUBMISSION_OUTCOME_UNVERIFIED.value,
        )
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    SELECT order_id, proposal_id, intent_id, broker_order_id, contract_symbol,
                           exchange, transaction_type, order_type, product, quantity, filled_quantity,
                           remaining_quantity, price, average_price, status, rejection_reason,
                           cancellation_reason, provenance, placed_at, updated_at, raw_payload
                    FROM orders
                    WHERE status IN ({','.join(['?']*len(non_terminal))})
                    ORDER BY placed_at DESC
                    """,
                    non_terminal,
                )
                for row in cursor.fetchall():
                    results.append(self._map_order_row(row))
        except Exception as e:
            logger.error(f"Error fetching active orders: {e}")
        return results

    def get_recent_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        results = []
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT order_id, proposal_id, intent_id, broker_order_id, contract_symbol,
                           exchange, transaction_type, order_type, product, quantity, filled_quantity,
                           remaining_quantity, price, average_price, status, rejection_reason,
                           cancellation_reason, provenance, placed_at, updated_at, raw_payload
                    FROM orders
                    ORDER BY placed_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                for row in cursor.fetchall():
                    results.append(self._map_order_row(row))
        except Exception as e:
            logger.error(f"Error fetching recent orders: {e}")
        return results

    def get_order_events(self, order_id: str) -> List[Dict[str, Any]]:
        events = []
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT event_id, order_id, event_type, status, message, raw_data, timestamp
                    FROM order_events
                    WHERE order_id = ?
                    ORDER BY timestamp ASC
                    """,
                    (order_id,),
                )
                for row in cursor.fetchall():
                    events.append(
                        {
                            "event_id": row[0],
                            "order_id": row[1],
                            "event_type": row[2],
                            "status": row[3],
                            "message": row[4],
                            "raw_data": json.loads(row[5]) if row[5] else {},
                            "timestamp": row[6],
                        }
                    )
        except Exception as e:
            logger.error(f"Error fetching order events for {order_id}: {e}")
        return events

    # ── POSITIONS MANAGEMENT ──

    def record_position(self, position: PositionState) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO positions (
                        position_id, order_id, contract_symbol, product, quantity,
                        buy_price, current_ltp, unrealized_pnl, stop_loss, target,
                        realized_pnl_analytics, exit_price, exit_order_id, closed_at,
                        provenance, status, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(position_id) DO UPDATE SET
                        quantity=excluded.quantity,
                        buy_price=excluded.buy_price,
                        current_ltp=excluded.current_ltp,
                        unrealized_pnl=excluded.unrealized_pnl,
                        realized_pnl_analytics=excluded.realized_pnl_analytics,
                        exit_price=COALESCE(excluded.exit_price, positions.exit_price),
                        exit_order_id=COALESCE(excluded.exit_order_id, positions.exit_order_id),
                        closed_at=COALESCE(excluded.closed_at, positions.closed_at),
                        provenance=COALESCE(excluded.provenance, positions.provenance),
                        status=excluded.status,
                        updated_at=excluded.updated_at
                    """,
                    (
                        position.position_id,
                        position.order_id,
                        position.contract_symbol,
                        position.product,
                        position.quantity,
                        position.buy_price,
                        position.current_ltp,
                        position.unrealized_pnl,
                        position.stop_loss,
                        position.target,
                        position.realized_pnl_analytics or 0.0,
                        position.exit_price,
                        position.exit_order_id,
                        position.closed_at,
                        position.provenance or "ARDHAMIND",
                        position.status,
                        position.updated_at or now_iso,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording position {position.position_id}: {e}")
            return False

    def update_position_exit(
        self,
        position_id: str,
        exit_order_id: str,
        exit_price: float,
        realized_pnl: float,
        closed_at: str,
        status: str = "CLOSED",
    ) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE positions
                    SET status = ?,
                        exit_order_id = ?,
                        exit_price = ?,
                        realized_pnl_analytics = ?,
                        unrealized_pnl = 0.0,
                        closed_at = ?,
                        updated_at = ?
                    WHERE position_id = ?
                    """,
                    (
                        status,
                        exit_order_id,
                        exit_price,
                        realized_pnl,
                        closed_at,
                        now_iso,
                        position_id,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating position exit for {position_id}: {e}")
            return False

    def get_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT position_id, order_id, contract_symbol, product, quantity,
                           buy_price, current_ltp, unrealized_pnl, stop_loss, target,
                           realized_pnl_analytics, exit_price, exit_order_id, closed_at,
                           provenance, status, updated_at
                    FROM positions
                    WHERE position_id = ?
                    """,
                    (position_id,),
                )
                row = cursor.fetchone()
                if row:
                    return self._map_position_row(row)
        except Exception as e:
            logger.error(f"Error fetching position {position_id}: {e}")
        return None

    def get_open_positions(self) -> List[Dict[str, Any]]:
        results = []
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT position_id, order_id, contract_symbol, product, quantity,
                           buy_price, current_ltp, unrealized_pnl, stop_loss, target,
                           realized_pnl_analytics, exit_price, exit_order_id, closed_at,
                           provenance, status, updated_at
                    FROM positions
                    WHERE status IN ('OPEN', 'PARTIAL_EXIT', 'EXIT_REQUESTED', 'UNVERIFIED')
                    ORDER BY updated_at DESC
                    """
                )
                for row in cursor.fetchall():
                    results.append(self._map_position_row(row))
        except Exception as e:
            logger.error(f"Error fetching open positions: {e}")
        return results

    def get_all_positions(self, limit: int = 50) -> List[Dict[str, Any]]:
        results = []
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT position_id, order_id, contract_symbol, product, quantity,
                           buy_price, current_ltp, unrealized_pnl, stop_loss, target,
                           realized_pnl_analytics, exit_price, exit_order_id, closed_at,
                           provenance, status, updated_at
                    FROM positions
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                for row in cursor.fetchall():
                    results.append(self._map_position_row(row))
        except Exception as e:
            logger.error(f"Error fetching all positions: {e}")
        return results

    # ── TRADE JOURNAL & PERFORMANCE LINEAGE (MILESTONE 5) ──

    def record_journal_entry(self, entry: TradeJournalRecord) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        entry.calculate_metrics()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO trade_journal (
                        journal_id, proposal_id, source_opportunity_id, trading_session_date,
                        underlying, contract_symbol, expiry, strike, option_type, direction,
                        setup_type, proposal_created_at, approved_at, entry_submitted_at,
                        opened_at, closed_at, duration_seconds, entry_order_ids_json,
                        exit_order_ids_json, entry_fills_json, exit_fills_json, proposed_entry,
                        weighted_average_entry, proposed_stop, proposed_target_1, proposed_target_2,
                        weighted_average_exit, entry_quantity, exit_quantity, confidence_at_entry,
                        priority_at_entry, market_regime_at_entry, briefing_id_at_entry,
                        scenario_id_at_entry, prediction_snapshot_id_at_entry, closing_reason,
                        trader_overrides_json, provenance, entry_slippage_pts, entry_slippage_pct,
                        exit_slippage_pts, exit_slippage_pct, hold_duration, planned_risk,
                        realized_trade_pnl, planned_rr, realized_r_multiple, status, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(journal_id) DO UPDATE SET
                        closed_at=COALESCE(excluded.closed_at, trade_journal.closed_at),
                        duration_seconds=COALESCE(excluded.duration_seconds, trade_journal.duration_seconds),
                        entry_order_ids_json=excluded.entry_order_ids_json,
                        exit_order_ids_json=excluded.exit_order_ids_json,
                        entry_fills_json=excluded.entry_fills_json,
                        exit_fills_json=excluded.exit_fills_json,
                        weighted_average_entry=excluded.weighted_average_entry,
                        weighted_average_exit=excluded.weighted_average_exit,
                        entry_quantity=excluded.entry_quantity,
                        exit_quantity=excluded.exit_quantity,
                        closing_reason=excluded.closing_reason,
                        trader_overrides_json=excluded.trader_overrides_json,
                        provenance=COALESCE(excluded.provenance, trade_journal.provenance),
                        entry_slippage_pts=excluded.entry_slippage_pts,
                        entry_slippage_pct=excluded.entry_slippage_pct,
                        exit_slippage_pts=excluded.exit_slippage_pts,
                        exit_slippage_pct=excluded.exit_slippage_pct,
                        hold_duration=excluded.hold_duration,
                        planned_risk=excluded.planned_risk,
                        realized_trade_pnl=excluded.realized_trade_pnl,
                        planned_rr=excluded.planned_rr,
                        realized_r_multiple=excluded.realized_r_multiple,
                        status=excluded.status,
                        updated_at=excluded.updated_at
                    """,
                    (
                        entry.journal_id,
                        entry.proposal_id,
                        entry.source_opportunity_id,
                        entry.trading_session_date or now_iso[:10],
                        entry.underlying,
                        entry.contract_symbol,
                        entry.expiry,
                        entry.strike,
                        entry.option_type,
                        entry.direction,
                        entry.setup_type,
                        entry.proposal_created_at or now_iso,
                        entry.approved_at,
                        entry.entry_submitted_at,
                        entry.opened_at,
                        entry.closed_at,
                        entry.duration_seconds,
                        json.dumps(entry.entry_order_ids),
                        json.dumps(entry.exit_order_ids),
                        json.dumps(entry.entry_fills),
                        json.dumps(entry.exit_fills),
                        entry.proposed_entry,
                        entry.weighted_average_entry,
                        entry.proposed_stop,
                        entry.proposed_target_1,
                        entry.proposed_target_2,
                        entry.weighted_average_exit,
                        entry.entry_quantity,
                        entry.exit_quantity,
                        entry.confidence_at_entry,
                        entry.priority_at_entry,
                        entry.market_regime_at_entry,
                        entry.briefing_id_at_entry,
                        entry.scenario_id_at_entry,
                        entry.prediction_snapshot_id_at_entry,
                        entry.closing_reason,
                        json.dumps(entry.trader_overrides),
                        entry.provenance or "ARDHAMIND",
                        entry.entry_slippage_pts,
                        entry.entry_slippage_pct,
                        entry.exit_slippage_pts,
                        entry.exit_slippage_pct,
                        entry.hold_duration,
                        entry.planned_risk,
                        entry.realized_trade_pnl,
                        entry.planned_rr,
                        entry.realized_r_multiple,
                        entry.status,
                        now_iso,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording journal entry {entry.journal_id}: {e}")
            return False

    def get_journal_entry(self, journal_id: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM trade_journal WHERE journal_id = ?
                    """,
                    (journal_id,),
                )
                row = cursor.fetchone()
                if row:
                    item = self._map_journal_row(row)
                    item["notes"] = self.get_journal_notes(journal_id)
                    return item
        except Exception as e:
            logger.error(f"Error fetching journal entry {journal_id}: {e}")
        return None

    def get_journal_by_proposal_id(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM trade_journal WHERE proposal_id = ?
                    """,
                    (proposal_id,),
                )
                row = cursor.fetchone()
                if row:
                    item = self._map_journal_row(row)
                    item["notes"] = self.get_journal_notes(item["journal_id"])
                    return item
        except Exception as e:
            logger.error(f"Error fetching journal for proposal {proposal_id}: {e}")
        return None

    def get_journal_entries(
        self,
        limit: int = 50,
        offset: int = 0,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        symbol: Optional[str] = None,
        setup_type: Optional[str] = None,
        result_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        results = []
        total_count = 0
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM trade_journal WHERE 1=1"
                params: List[Any] = []

                if date_from:
                    query += " AND trading_session_date >= ?"
                    params.append(date_from)
                if date_to:
                    query += " AND trading_session_date <= ?"
                    params.append(date_to)
                if symbol:
                    query += " AND contract_symbol LIKE ?"
                    params.append(f"%{symbol}%")
                if setup_type:
                    query += " AND setup_type = ?"
                    params.append(setup_type)
                if result_filter == "WIN":
                    query += " AND realized_trade_pnl > 0"
                elif result_filter == "LOSS":
                    query += " AND realized_trade_pnl < 0"

                # Count query
                count_query = query.replace("SELECT *", "SELECT COUNT(*)")
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]

                # Data query
                query += " ORDER BY proposal_created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)
                for row in cursor.fetchall():
                    item = self._map_journal_row(row)
                    item["notes"] = self.get_journal_notes(item["journal_id"])
                    results.append(item)
        except Exception as e:
            logger.error(f"Error fetching journal entries: {e}")

        return {
            "entries": results,
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }

    def get_journal_analytics_summary(self) -> Dict[str, Any]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN realized_trade_pnl > 0 THEN 1 ELSE 0 END) as win_count,
                        SUM(CASE WHEN realized_trade_pnl < 0 THEN 1 ELSE 0 END) as loss_count,
                        SUM(realized_trade_pnl) as total_realized_pnl,
                        AVG(realized_trade_pnl) as avg_trade_pnl,
                        AVG(entry_slippage_pts) as avg_entry_slippage,
                        AVG(exit_slippage_pts) as avg_exit_slippage,
                        AVG(realized_r_multiple) as avg_r_multiple,
                        AVG(hold_duration) as avg_hold_duration_sec,
                        MAX(realized_trade_pnl) as max_profit,
                        MIN(realized_trade_pnl) as max_loss
                    FROM trade_journal
                    WHERE status = 'CLOSED'
                    """
                )
                row = cursor.fetchone()
                total_trades = row[0] or 0
                win_count = row[1] or 0
                loss_count = row[2] or 0
                win_rate = round((win_count / total_trades) * 100.0, 1) if total_trades > 0 else 0.0

                return {
                    "total_trades": total_trades,
                    "win_count": win_count,
                    "loss_count": loss_count,
                    "win_rate_pct": win_rate,
                    "total_realized_pnl": round(row[3] or 0.0, 2),
                    "avg_trade_pnl": round(row[4] or 0.0, 2),
                    "avg_entry_slippage_pts": round(row[5] or 0.0, 2),
                    "avg_exit_slippage_pts": round(row[6] or 0.0, 2),
                    "avg_r_multiple": round(row[7] or 0.0, 2),
                    "avg_hold_duration_sec": round(row[8] or 0.0, 1),
                    "max_profit": round(row[9] or 0.0, 2),
                    "max_loss": round(row[10] or 0.0, 2),
                }
        except Exception as e:
            logger.error(f"Error computing journal analytics summary: {e}")
            return {
                "total_trades": 0,
                "win_count": 0,
                "loss_count": 0,
                "win_rate_pct": 0.0,
                "total_realized_pnl": 0.0,
            }

    # ── JOURNAL NOTES (MILESTONE 5) ──

    def add_journal_note(self, note: JournalNote) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO journal_notes (
                        note_id, journal_id, note_text, tags_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(note_id) DO UPDATE SET
                        note_text=excluded.note_text,
                        tags_json=excluded.tags_json,
                        updated_at=excluded.updated_at
                    """,
                    (
                        note.note_id,
                        note.journal_id,
                        note.note_text,
                        json.dumps(note.tags),
                        note.created_at or now_iso,
                        now_iso,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving journal note {note.note_id}: {e}")
            return False

    def get_journal_notes(self, journal_id: str) -> List[Dict[str, Any]]:
        results = []
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT note_id, journal_id, note_text, tags_json, created_at, updated_at
                    FROM journal_notes
                    WHERE journal_id = ?
                    ORDER BY created_at ASC
                    """,
                    (journal_id,),
                )
                for row in cursor.fetchall():
                    results.append(
                        {
                            "note_id": row[0],
                            "journal_id": row[1],
                            "note_text": row[2],
                            "tags": json.loads(row[3]) if row[3] else [],
                            "created_at": row[4],
                            "updated_at": row[5],
                        }
                    )
        except Exception as e:
            logger.error(f"Error fetching notes for journal {journal_id}: {e}")
        return results

    # ── JOURNAL CORRECTIONS (IMMUTABILITY PRESERVATION) ──

    def record_journal_correction(
        self,
        journal_id: str,
        correction_type: str,
        reason: str,
        prior_data: Dict[str, Any],
        new_data: Dict[str, Any],
    ) -> bool:
        corr_id = f"CORR-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO journal_corrections (
                        correction_id, journal_id, correction_type, reason,
                        prior_data_json, new_data_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        corr_id,
                        journal_id,
                        correction_type,
                        reason,
                        json.dumps(prior_data),
                        json.dumps(new_data),
                        now_iso,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording journal correction for {journal_id}: {e}")
            return False

    # ── DERIVED JOURNAL LINEAGE PROJECTION BUILDER ──

    def reconstruct_journal_for_proposal(self, proposal_id: str) -> Optional[TradeJournalRecord]:
        """
        Reconstructs the authoritative TradeJournalRecord projection from the
        immutable proposal, order, event, position, and execution lineages.
        """
        prop = self.get_proposal(proposal_id)
        if not prop:
            return None

        payload = prop.get("payload", {})
        orders = []
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT order_id, proposal_id, intent_id, broker_order_id, contract_symbol,
                           exchange, transaction_type, order_type, product, quantity, filled_quantity,
                           remaining_quantity, price, average_price, status, rejection_reason,
                           cancellation_reason, provenance, placed_at, updated_at, raw_payload
                    FROM orders
                    WHERE proposal_id = ?
                    ORDER BY placed_at ASC
                    """,
                    (proposal_id,),
                )
                for row in cursor.fetchall():
                    orders.append(self._map_order_row(row))
        except Exception as e:
            logger.warning(f"Failed to query orders for proposal {proposal_id}: {e}")

        # Distinguish entry vs exit orders
        entry_orders = [o for o in orders if o.get("transaction_type") == "BUY"]
        exit_orders = [o for o in orders if o.get("transaction_type") == "SELL"]

        entry_order_ids = [o.get("order_id") for o in entry_orders]
        exit_order_ids = [o.get("order_id") for o in exit_orders]

        # Extract fills
        entry_fills = []
        for o in entry_orders:
            if o.get("filled_quantity", 0) > 0:
                entry_fills.append({
                    "order_id": o.get("order_id"),
                    "broker_order_id": o.get("broker_order_id"),
                    "quantity": o.get("filled_quantity"),
                    "price": o.get("average_price") or o.get("price"),
                    "timestamp": o.get("updated_at")
                })

        exit_fills = []
        for o in exit_orders:
            if o.get("filled_quantity", 0) > 0:
                exit_fills.append({
                    "order_id": o.get("order_id"),
                    "broker_order_id": o.get("broker_order_id"),
                    "quantity": o.get("filled_quantity"),
                    "price": o.get("average_price") or o.get("price"),
                    "timestamp": o.get("updated_at")
                })

        now_iso = datetime.now(timezone.utc).isoformat()
        journal_id = f"JRN-{proposal_id}"

        # Determine closing reason
        closing_reason = ClosingReason.UNKNOWN.value
        pos_id = f"POS-{entry_orders[0].get('order_id')}" if entry_orders else None
        pos = self.get_position(pos_id) if pos_id else None
        closed_at = None
        if pos and pos.get("status") == "CLOSED":
            closed_at = pos.get("closed_at") or now_iso
            exit_pr = pos.get("exit_price", 0.0)
            target1 = payload.get("target_1", 0.0)
            stop_loss = payload.get("stop_loss", 0.0)
            if exit_pr >= target1 and target1 > 0:
                closing_reason = ClosingReason.TARGET_1_EXIT.value
            elif exit_pr <= stop_loss and stop_loss > 0:
                closing_reason = ClosingReason.STOP_EXIT.value
            elif pos.get("exit_order_id") == "EMERGENCY_CLOSE_ALL":
                closing_reason = ClosingReason.EMERGENCY_EXIT.value
            else:
                closing_reason = ClosingReason.MANUAL_EXIT.value

        overrides = []
        if payload.get("lots", 1) > 1:
            overrides.append("MODIFIED_LOTS")
        if payload.get("product") and payload.get("product") != "NRML":
            overrides.append("PRODUCT_OVERRIDE")

        record = TradeJournalRecord(
            journal_id=journal_id,
            proposal_id=proposal_id,
            source_opportunity_id=payload.get("raw_metadata", {}).get("opportunity_id"),
            trading_session_date=prop.get("created_at", now_iso)[:10],
            underlying=payload.get("underlying", "NIFTY"),
            contract_symbol=payload.get("contract_symbol", ""),
            expiry=payload.get("raw_metadata", {}).get("expiry"),
            strike=payload.get("strike"),
            option_type=payload.get("option_type"),
            direction=payload.get("direction", "BULLISH"),
            setup_type=payload.get("setup_type", ""),
            proposal_created_at=prop.get("created_at", now_iso),
            approved_at=prop.get("approval_timestamp"),
            entry_submitted_at=entry_orders[0].get("placed_at") if entry_orders else None,
            opened_at=entry_orders[0].get("updated_at") if entry_orders and entry_orders[0].get("filled_quantity", 0) > 0 else None,
            closed_at=closed_at,
            entry_order_ids=entry_order_ids,
            exit_order_ids=exit_order_ids,
            entry_fills=entry_fills,
            exit_fills=exit_fills,
            proposed_entry=float(payload.get("entry_price", 0.0)),
            weighted_average_entry=0.0,
            proposed_stop=float(payload.get("stop_loss", 0.0)),
            proposed_target_1=float(payload.get("target_1", 0.0)),
            proposed_target_2=float(payload.get("target_2", 0.0)),
            entry_quantity=int(payload.get("total_quantity", 0)),
            confidence_at_entry=float(payload.get("confidence_score", 0.0)),
            priority_at_entry=float(payload.get("priority_score", 0.0)),
            market_regime_at_entry=payload.get("raw_metadata", {}).get("regime"),
            briefing_id_at_entry=payload.get("raw_metadata", {}).get("briefing_id"),
            scenario_id_at_entry=payload.get("raw_metadata", {}).get("scenario_id"),
            prediction_snapshot_id_at_entry=payload.get("raw_metadata", {}).get("prediction_id"),
            closing_reason=closing_reason,
            trader_overrides=overrides,
            provenance=entry_orders[0].get("provenance", "ARDHAMIND") if entry_orders else "ARDHAMIND",
            status="CLOSED" if closed_at else "OPEN"
        )
        record.calculate_metrics()
        self.record_journal_entry(record)
        return record

    def _map_order_row(self, row: tuple) -> Dict[str, Any]:
        return {
            "order_id": row[0],
            "proposal_id": row[1],
            "intent_id": row[2],
            "broker_order_id": row[3],
            "contract_symbol": row[4],
            "exchange": row[5],
            "transaction_type": row[6],
            "order_type": row[7],
            "product": row[8],
            "quantity": row[9],
            "filled_quantity": row[10],
            "remaining_quantity": row[11],
            "price": row[12],
            "average_price": row[13],
            "status": row[14],
            "rejection_reason": row[15],
            "cancellation_reason": row[16],
            "provenance": row[17],
            "placed_at": row[18],
            "updated_at": row[19],
            "raw_payload": json.loads(row[20]) if row[20] else {},
        }

    def _map_position_row(self, row: tuple) -> Dict[str, Any]:
        return {
            "position_id": row[0],
            "order_id": row[1],
            "contract_symbol": row[2],
            "product": row[3],
            "quantity": row[4],
            "buy_price": row[5],
            "current_ltp": row[6],
            "unrealized_pnl": row[7],
            "stop_loss": row[8],
            "target": row[9],
            "realized_pnl_analytics": row[10],
            "exit_price": row[11],
            "exit_order_id": row[12],
            "closed_at": row[13],
            "provenance": row[14],
            "status": row[15],
            "updated_at": row[16],
        }

    def _map_journal_row(self, row: tuple) -> Dict[str, Any]:
        return {
            "journal_id": row[0],
            "proposal_id": row[1],
            "source_opportunity_id": row[2],
            "trading_session_date": row[3],
            "underlying": row[4],
            "contract_symbol": row[5],
            "expiry": row[6],
            "strike": row[7],
            "option_type": row[8],
            "direction": row[9],
            "setup_type": row[10],
            "proposal_created_at": row[11],
            "approved_at": row[12],
            "entry_submitted_at": row[13],
            "opened_at": row[14],
            "closed_at": row[15],
            "duration_seconds": row[16],
            "entry_order_ids": json.loads(row[17]) if row[17] else [],
            "exit_order_ids": json.loads(row[18]) if row[18] else [],
            "entry_fills": json.loads(row[19]) if row[19] else [],
            "exit_fills": json.loads(row[20]) if row[20] else [],
            "proposed_entry": row[21],
            "weighted_average_entry": row[22],
            "proposed_stop": row[23],
            "proposed_target_1": row[24],
            "proposed_target_2": row[25],
            "weighted_average_exit": row[26],
            "entry_quantity": row[27],
            "exit_quantity": row[28],
            "confidence_at_entry": row[29],
            "priority_at_entry": row[30],
            "market_regime_at_entry": row[31],
            "briefing_id_at_entry": row[32],
            "scenario_id_at_entry": row[33],
            "prediction_snapshot_id_at_entry": row[34],
            "closing_reason": row[35],
            "trader_overrides": json.loads(row[36]) if row[36] else [],
            "provenance": row[37],
            "entry_slippage_pts": row[38],
            "entry_slippage_pct": row[39],
            "exit_slippage_pts": row[40],
            "exit_slippage_pct": row[41],
            "hold_duration": row[42],
            "planned_risk": row[43],
            "realized_trade_pnl": row[44],
            "planned_rr": row[45],
            "realized_r_multiple": row[46],
            "status": row[47],
            "updated_at": row[48],
        }
