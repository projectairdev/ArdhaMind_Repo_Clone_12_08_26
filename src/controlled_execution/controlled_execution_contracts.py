# src/execution_engine/controlled_execution_contracts.py
"""
Controlled Execution Contracts — Canonical Data Models for Trader-Ready Execution in AIR ArdhaMind.

Defines:
1. OrderIntent: Immutable, broker-independent order specification generated from FrozenTradeApproval.
2. LivePosition: Canonical position tracking underlying thesis, invalidation, targets, and broker fills.
3. FillReconciliation: Reconciles approved plan vs executed reality and measures slippage.
4. ExecutionRecord: Tracks the complete execution lifecycle.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ExecutionState:
    NOT_EXECUTABLE = "NOT_EXECUTABLE"
    APPROVED = "APPROVED"
    EXECUTION_REVALIDATING = "EXECUTION_REVALIDATING"
    READY_TO_SUBMIT = "READY_TO_SUBMIT"
    SUBMITTING = "SUBMITTING"
    BROKER_ACCEPTED = "BROKER_ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    POSITION_OPEN = "POSITION_OPEN"
    EXIT_RECOMMENDED = "EXIT_RECOMMENDED"
    EXIT_REVIEWING = "EXIT_REVIEWING"
    EXIT_APPROVED = "EXIT_APPROVED"
    EXIT_SUBMITTING = "EXIT_SUBMITTING"
    EXITED = "EXITED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


@dataclass
class OrderIntent:
    execution_id: str
    approval_id: str
    candidate_id: str
    instrument_token: int
    tradingsymbol: str
    exchange: str  # NFO
    transaction_type: str  # BUY | SELL
    quantity: int
    order_type: str  # MARKET | LIMIT
    price: Optional[float]
    product: str  # NRML | MIS
    validity: str  # DAY
    expected_ltp: float
    max_allowed_slippage_pts: float
    generated_at: str
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FillReconciliation:
    execution_id: str
    approval_id: str
    expected_entry_price: float
    actual_average_fill_price: float
    requested_quantity: int
    filled_quantity: int
    pending_quantity: int
    slippage_pts: float
    slippage_pct: float
    expected_outlay: float
    actual_outlay: float
    risk_geometry_changed: bool
    reconciled_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LivePosition:
    position_id: str
    execution_id: str
    approval_id: str
    candidate_id: str
    instrument: str
    side: str  # LONG_CE | LONG_PE
    quantity: int
    average_entry_price: float
    current_ltp: float
    unrealized_pnl: float
    realized_pnl: float
    underlying_entry_spot: float
    current_underlying_spot: float
    invalidation_level: Optional[float]
    target_1: Optional[float]
    target_2: Optional[float]
    stop_state: str  # ACTIVE | THESIS_INVALIDATED | BREACH_WARNING
    target_state: str  # TARGET_1_PENDING | TARGET_1_REACHED | TARGET_2_REACHED
    risk_state: str  # NORMAL | RISK_WARNING | EMERGENCY_EXIT_REQUIRED
    broker_position_state: str  # OPEN | CLOSED | SYNCED | MISMATCH
    opened_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionRecord:
    execution_id: str
    approval_id: str
    candidate_id: str
    state: str
    created_at: str
    updated_at: str
    order_intent: Optional[OrderIntent] = None
    broker_order_id: Optional[str] = None
    reconciliation: Optional[FillReconciliation] = None
    position: Optional[LivePosition] = None
    revalidation_blockers: List[str] = field(default_factory=list)
    failure_reason: Optional[str] = None
    audit_events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "approval_id": self.approval_id,
            "candidate_id": self.candidate_id,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "order_intent": self.order_intent.to_dict() if self.order_intent else None,
            "broker_order_id": self.broker_order_id,
            "reconciliation": self.reconciliation.to_dict() if self.reconciliation else None,
            "position": self.position.to_dict() if self.position else None,
            "revalidation_blockers": list(self.revalidation_blockers),
            "failure_reason": self.failure_reason,
            "audit_events": list(self.audit_events)
        }
