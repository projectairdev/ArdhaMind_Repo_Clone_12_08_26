from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass(frozen=True)
class ExecutionOrder:
    candidate_id: str
    tradingsymbol: str
    exchange: str               # e.g., "NFO", "NSE"
    transaction_type: str       # "BUY", "SELL"
    quantity: int
    product: str                # "MIS", "NRML", "CNC"
    order_type: str             # "MARKET", "LIMIT", "SL", "SL-M"
    price: float = 0.0
    trigger_price: float = 0.0


@dataclass(frozen=True)
class ExecutionRequest:
    request_id: str
    decision_report_id: str
    orders: List[ExecutionOrder] = field(default_factory=list)
    timestamp: str = ""
    status: str = "PENDING"      # "PENDING", "CONFIRMED", "REJECTED", "CANCELLED"


@dataclass(frozen=True)
class ExecutionResponse:
    order_id: str               # Broker order ID
    status: str                 # e.g., "COMPLETE", "REJECTED", "OPEN", "CANCELLED"
    exchange_order_id: str = ""
    failure_reason: str = ""


@dataclass(frozen=True)
class ExecutionStatus:
    status: str                 # "PENDING", "SUBMITTED", "COMPLETED", "FAILED", "PARTIAL"
    message: str = ""


@dataclass(frozen=True)
class ExecutionReport:
    report_id: str
    request_id: str
    submitted_orders: List[ExecutionOrder] = field(default_factory=list)
    accepted_orders: List[ExecutionOrder] = field(default_factory=list)
    rejected_orders: List[ExecutionOrder] = field(default_factory=list)
    exchange_order_id: str = ""
    broker_order_id: str = ""
    timestamp: str = ""
    failure_reason: str = ""
    status: str = "PENDING"      # "PENDING", "COMPLETED", "FAILED", "PARTIAL"


@dataclass(frozen=True)
class BrokerAccount:
    client_id: str
    name: str
    email: str
    broker: str = "Zerodha"


@dataclass(frozen=True)
class BrokerFunds:
    available_cash: float
    margins: float
    utilized_margin: float
    available_margin: float


@dataclass(frozen=True)
class BrokerPosition:
    tradingsymbol: str
    exchange: str
    product: str
    quantity: int
    average_price: float
    last_price: float
    pnl: float
    today_mtm: float


@dataclass(frozen=True)
class BrokerHolding:
    tradingsymbol: str
    exchange: str
    product: str
    quantity: int
    average_price: float
    last_price: float
    pnl: float


@dataclass(frozen=True)
class BrokerOrder:
    order_id: str
    exchange_order_id: str
    tradingsymbol: str
    exchange: str
    transaction_type: str
    quantity: int
    product: str
    order_type: str
    status: str                 # "COMPLETE", "REJECTED", "OPEN", "CANCELLED"
    price: float
    filled_quantity: int
    order_timestamp: str
    status_message: str = ""


@dataclass(frozen=True)
class ExecutionSummary:
    total_submitted: int
    total_accepted: int
    total_rejected: int
    total_capital_utilized: float


@dataclass(frozen=True)
class ExecutionValidation:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionConfirmation:
    confirmation_id: str
    request_id: str
    confirmed_by: str = "OPERATOR"
    status: str = "CONFIRMED" # "CONFIRMED", "CANCELLED"
    timestamp: str = ""


@dataclass(frozen=True)
class ExecutionReceipt:
    order_id: str
    exchange_order_id: str
    tradingsymbol: str
    quantity: int
    price: float
    status: str = "COMPLETE" # "COMPLETE", "REJECTED", "OPEN"
    timestamp: str = ""


@dataclass(frozen=True)
class ExecutionFailure:
    order_id: str
    tradingsymbol: str
    error_message: str
    timestamp: str = ""


@dataclass(frozen=True)
class ExecutionResult:
    request_id: str
    status: str # "SUCCESS", "FAILED", "PARTIAL"
    receipts: List[ExecutionReceipt] = field(default_factory=list)
    failures: List[ExecutionFailure] = field(default_factory=list)
    timestamp: str = ""


@dataclass(frozen=True)
class ExecutionAuditEntry:
    audit_id: str
    timestamp: str
    operator: str
    request: ExecutionRequest
    validation_result: ExecutionValidation
    confirmation_result: Optional[ExecutionConfirmation] = None
    broker_response: Optional[Any] = None
    execution_outcome: str = "PENDING" # e.g. "COMPLETED", "FAILED", "CANCELLED", "VALIDATION_FAILED"
    failure_reason: Optional[str] = None
