from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class OrderState:
    order_id: str
    tradingsymbol: str
    exchange: str
    transaction_type: str       # "BUY", "SELL"
    quantity: int
    filled_quantity: int
    pending_quantity: int
    status: str                 # "CREATED", "SUBMITTED", "ACCEPTED", "PENDING", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "REJECTED", "EXPIRED"
    average_price: float
    trigger_price: float
    product: str                # "MIS", "NRML", "CNC"
    order_type: str             # "MARKET", "LIMIT", "SL", "SL-M"
    status_message: str = ""
    timestamp: str = ""


@dataclass(frozen=True)
class LivePosition:
    tradingsymbol: str
    exchange: str
    product: str
    quantity: int               # Net open quantity
    average_price: float
    last_price: float
    pnl: float
    realized_pnl: float
    unrealized_pnl: float
    today_mtm: float


@dataclass(frozen=True)
class PositionContext:
    positions: List[LivePosition] = field(default_factory=list)
    total_positions_count: int = 0
    open_positions_count: int = 0
    today_mtm: float = 0.0


@dataclass(frozen=True)
class PortfolioContext:
    active_positions: List[LivePosition] = field(default_factory=list)
    closed_positions: List[LivePosition] = field(default_factory=list)
    capital_utilized: float = 0.0
    available_capital: float = 1000000.0
    portfolio_mtm: float = 0.0


@dataclass(frozen=True)
class ExecutionTimeline:
    order_id: str
    tradingsymbol: str
    events: List[Dict[str, Any]] = field(default_factory=list)  # [{"timestamp": "...", "event": "...", "details": "..."}]


@dataclass(frozen=True)
class ExecutionAudit:
    audit_id: str
    timestamp: str
    action: str                 # e.g., "SUBMIT_ORDER", "CANCEL_ORDER", "POSITION_SYNC"
    status: str                 # "SUCCESS", "FAILURE"
    request_payload: Dict[str, Any] = field(default_factory=dict)
    response_payload: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""


@dataclass(frozen=True)
class ExecutionStatistics:
    total_orders: int = 0
    filled_orders: int = 0
    cancelled_orders: int = 0
    rejected_orders: int = 0
    fill_rate: float = 0.0
    average_execution_time_ms: float = 0.0


@dataclass(frozen=True)
class ExecutionStateReport:
    report_id: str
    timestamp: str
    orders: List[OrderState] = field(default_factory=list)
    positions: PositionContext = field(default_factory=lambda: PositionContext())
    portfolio: PortfolioContext = field(default_factory=lambda: PortfolioContext())
    timelines: List[ExecutionTimeline] = field(default_factory=list)
    audits: List[ExecutionAudit] = field(default_factory=list)
    statistics: ExecutionStatistics = field(default_factory=lambda: ExecutionStatistics())
