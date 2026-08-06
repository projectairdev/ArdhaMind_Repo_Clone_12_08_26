from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass(frozen=True)
class OrderLifecycleEvent:
    event_id: str
    timestamp: str
    previous_state: str
    new_state: str
    trigger_source: str
    operator: str
    broker_response: Optional[str] = None
    reason: Optional[str] = None

@dataclass(frozen=True)
class ExecutionFill:
    fill_id: str
    timestamp: str
    filled_quantity: int
    price: float
    exchange_order_id: str

@dataclass(frozen=True)
class ExecutionProgress:
    requested_quantity: int
    filled_quantity: int
    remaining_quantity: int
    average_fill_price: float
    weighted_average: float
    completion_percentage: float

@dataclass(frozen=True)
class ExecutionTimeline:
    order_id: str
    tradingsymbol: str
    events: List[OrderLifecycleEvent] = field(default_factory=list)

@dataclass(frozen=True)
class ExecutionStatusSummary:
    order_id: str
    current_state: str
    progress: ExecutionProgress
    timeline: ExecutionTimeline
    broker_remarks: str = ""

@dataclass(frozen=True)
class ExecutionStatistics:
    average_fill_time: float = 0.0          # seconds
    broker_latency: float = 0.0             # milliseconds
    exchange_latency: float = 0.0           # milliseconds
    fill_efficiency: float = 0.0            # percentage
    slippage: float = 0.0                   # INR slippage amount
    partial_fill_percentage: float = 0.0    # percentage of orders with partial fills
    modification_count: int = 0
    cancellation_rate: float = 0.0          # percentage of orders cancelled
    execution_success_rate: float = 0.0     # percentage of orders filled

@dataclass(frozen=True)
class OrderModificationHistory:
    modification_id: str
    timestamp: str
    previous_quantity: int
    previous_price: float
    new_quantity: int
    new_price: float
    status: str

@dataclass(frozen=True)
class OrderCancellationRecord:
    cancellation_id: str
    timestamp: str
    requested_by: str
    reason: str
    status: str

@dataclass(frozen=True)
class OrderLifecycleReport:
    order_id: str
    tradingsymbol: str
    exchange: str
    transaction_type: str
    quantity: int
    product: str
    order_type: str
    current_state: str
    progress: ExecutionProgress
    timeline: ExecutionTimeline
    modification_history: List[OrderModificationHistory] = field(default_factory=list)
    cancellation_record: Optional[OrderCancellationRecord] = None
    broker_remarks: str = ""
    timestamp: str = ""

@dataclass(frozen=True)
class BrokerExecutionSnapshot:
    timestamp: str
    orders: List[OrderLifecycleReport] = field(default_factory=list)
    system_health_score: float = 100.0
