from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProposalState(str, Enum):
    PROPOSED = "PROPOSED"
    RISK_VALIDATED = "RISK_VALIDATED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    INTENT_PREPARED = "INTENT_PREPARED"
    SUBMITTED = "SUBMITTED"
    DRY_RUN_RECORDED = "DRY_RUN_RECORDED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    NO_TRADE = "NO_TRADE"


class BrokerOrderState(str, Enum):
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    CANCEL_OUTCOME_UNVERIFIED = "CANCEL_OUTCOME_UNVERIFIED"
    EXIT_REQUESTED = "EXIT_REQUESTED"
    EXIT_OUTCOME_UNVERIFIED = "EXIT_OUTCOME_UNVERIFIED"
    SUBMISSION_OUTCOME_UNVERIFIED = "SUBMISSION_OUTCOME_UNVERIFIED"
    REJECTED = "REJECTED"


class OperationType(str, Enum):
    ORDER_SUBMIT = "ORDER_SUBMIT"
    ORDER_CANCEL = "ORDER_CANCEL"
    POSITION_EXIT = "POSITION_EXIT"
    EMERGENCY_CLOSE_ALL = "EMERGENCY_CLOSE_ALL"


class OperationStatus(str, Enum):
    INITIATED = "INITIATED"
    SUBMITTED = "SUBMITTED"
    OUTCOME_UNVERIFIED = "OUTCOME_UNVERIFIED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ClosingReason(str, Enum):
    TARGET_1_EXIT = "TARGET_1_EXIT"
    TARGET_2_EXIT = "TARGET_2_EXIT"
    STOP_EXIT = "STOP_EXIT"
    MANUAL_EXIT = "MANUAL_EXIT"
    EMERGENCY_EXIT = "EMERGENCY_EXIT"
    BROKER_EXTERNAL_EXIT = "BROKER_EXTERNAL_EXIT"
    RMS_SQUAREOFF = "RMS_SQUAREOFF"
    SESSION_EXIT = "SESSION_EXIT"
    UNKNOWN = "UNKNOWN"


class TraderOverrideType(str, Enum):
    MODIFIED_LOTS = "MODIFIED_LOTS"
    MODIFIED_QUANTITY = "MODIFIED_QUANTITY"
    PRODUCT_OVERRIDE = "PRODUCT_OVERRIDE"
    ORDER_TYPE_OVERRIDE = "ORDER_TYPE_OVERRIDE"
    LIMIT_PRICE_OVERRIDE = "LIMIT_PRICE_OVERRIDE"
    MANUAL_EARLY_EXIT = "MANUAL_EARLY_EXIT"
    MANUAL_KITE_EXIT = "MANUAL_KITE_EXIT"
    EMERGENCY_EXIT = "EMERGENCY_EXIT"
    EXTERNAL_MODIFICATION = "EXTERNAL_MODIFICATION"


@dataclass
class ExecutionOperation:
    operation_id: str
    idempotency_key: str
    operation_type: str  # ORDER_SUBMIT / ORDER_CANCEL / POSITION_EXIT / EMERGENCY_CLOSE_ALL
    entity_type: str    # ORDER / POSITION / PORTFOLIO
    entity_id: str
    requested_at: str
    current_status: str  # INITIATED / SUBMITTED / OUTCOME_UNVERIFIED / COMPLETED / FAILED
    broker_order_id: Optional[str] = None
    result_payload: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OrderIntent:
    proposal_id: str
    symbol: str
    exchange: str
    transaction_type: str  # BUY / SELL
    order_type: str        # LIMIT / MARKET / SL
    product: str           # NRML / MIS
    lots: int
    lot_size: int
    quantity: int
    price: float
    trigger_price: Optional[float] = None
    dry_run: bool = True
    intent_id: str = ""
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OrderRecord:
    order_id: str
    proposal_id: str
    intent_id: str
    broker_order_id: Optional[str]
    contract_symbol: str
    exchange: str
    transaction_type: str
    order_type: str
    product: str
    quantity: int
    filled_quantity: int = 0
    remaining_quantity: int = 0
    price: float = 0.0
    average_price: float = 0.0
    status: str = BrokerOrderState.SUBMITTED.value
    rejection_reason: Optional[str] = None
    cancellation_reason: Optional[str] = None
    provenance: str = "ARDHAMIND"  # ARDHAMIND / BROKER_EXTERNAL / BROKER_RMS / UNKNOWN
    placed_at: str = ""
    updated_at: str = ""
    raw_payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.remaining_quantity == 0 and self.quantity > self.filled_quantity:
            self.remaining_quantity = self.quantity - self.filled_quantity

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PositionState:
    position_id: str
    order_id: str
    contract_symbol: str
    product: str
    quantity: int
    buy_price: float
    current_ltp: float
    unrealized_pnl: float
    stop_loss: float
    target: float
    realized_pnl_analytics: float = 0.0
    exit_price: Optional[float] = None
    exit_order_id: Optional[str] = None
    closed_at: Optional[str] = None
    provenance: str = "ARDHAMIND"  # ARDHAMIND / BROKER_EXTERNAL / BROKER_RMS / UNKNOWN
    status: str = "OPEN"           # OPEN / PARTIAL_EXIT / CLOSED / UNVERIFIED
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JournalNote:
    note_id: str
    journal_id: str
    note_text: str
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TradeJournalRecord:
    journal_id: str
    proposal_id: str
    source_opportunity_id: Optional[str] = None
    trading_session_date: str = ""
    underlying: str = "NIFTY"
    contract_symbol: str = ""
    expiry: Optional[str] = None
    strike: Optional[int] = None
    option_type: Optional[str] = None
    direction: str = "BULLISH"
    setup_type: str = ""
    proposal_created_at: str = ""
    approved_at: Optional[str] = None
    entry_submitted_at: Optional[str] = None
    opened_at: Optional[str] = None
    closed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    entry_order_ids: List[str] = field(default_factory=list)
    exit_order_ids: List[str] = field(default_factory=list)
    entry_fills: List[Dict[str, Any]] = field(default_factory=list)
    exit_fills: List[Dict[str, Any]] = field(default_factory=list)
    proposed_entry: float = 0.0
    weighted_average_entry: float = 0.0
    proposed_stop: float = 0.0
    proposed_target_1: float = 0.0
    proposed_target_2: float = 0.0
    weighted_average_exit: float = 0.0
    entry_quantity: int = 0
    exit_quantity: int = 0
    confidence_at_entry: float = 0.0
    priority_at_entry: float = 0.0
    market_regime_at_entry: Optional[str] = None
    briefing_id_at_entry: Optional[str] = None
    scenario_id_at_entry: Optional[str] = None
    prediction_snapshot_id_at_entry: Optional[str] = None
    closing_reason: str = ClosingReason.UNKNOWN.value
    trader_overrides: List[str] = field(default_factory=list)
    provenance: str = "ARDHAMIND"
    entry_slippage_pts: float = 0.0
    entry_slippage_pct: float = 0.0
    exit_slippage_pts: float = 0.0
    exit_slippage_pct: float = 0.0
    hold_duration: float = 0.0
    planned_risk: float = 0.0
    realized_trade_pnl: float = 0.0
    planned_rr: float = 0.0
    realized_r_multiple: float = 0.0
    status: str = "CLOSED"  # OPEN / CLOSED / CORRECTED
    notes_count: int = 0
    updated_at: str = ""

    def calculate_metrics(self) -> None:
        # Calculate fill-weighted entry price
        if self.entry_fills:
            total_qty = sum(int(f.get("quantity", 0)) for f in self.entry_fills)
            if total_qty > 0:
                weighted_sum = sum(float(f.get("price", 0.0)) * int(f.get("quantity", 0)) for f in self.entry_fills)
                self.weighted_average_entry = round(weighted_sum / total_qty, 2)
                self.entry_quantity = total_qty
        elif self.weighted_average_entry == 0.0 and self.proposed_entry > 0.0:
            self.weighted_average_entry = self.proposed_entry

        # Calculate fill-weighted exit price
        if self.exit_fills:
            total_exit_qty = sum(int(f.get("quantity", 0)) for f in self.exit_fills)
            if total_exit_qty > 0:
                weighted_exit_sum = sum(float(f.get("price", 0.0)) * int(f.get("quantity", 0)) for f in self.exit_fills)
                self.weighted_average_exit = round(weighted_exit_sum / total_exit_qty, 2)
                self.exit_quantity = total_exit_qty

        # Direction-Aware Slippage Calculations
        # For BUY: actual > intended is adverse (+ slippage pts), actual < intended is favorable (- slippage pts)
        # For SELL: actual < intended is adverse (+ slippage pts), actual > intended is favorable (- slippage pts)
        if self.proposed_entry > 0 and self.weighted_average_entry > 0:
            if self.direction.upper() == "BULLISH" or "BUY" in self.direction.upper():
                self.entry_slippage_pts = round(self.weighted_average_entry - self.proposed_entry, 2)
            else:
                self.entry_slippage_pts = round(self.proposed_entry - self.weighted_average_entry, 2)
            self.entry_slippage_pct = round((self.entry_slippage_pts / self.proposed_entry) * 100.0, 2)

        # Realized Trade PnL
        if self.weighted_average_exit > 0 and self.weighted_average_entry > 0 and self.entry_quantity > 0:
            effective_qty = min(self.entry_quantity, self.exit_quantity or self.entry_quantity)
            if self.direction.upper() == "BULLISH" or "BUY" in self.direction.upper():
                self.realized_trade_pnl = round((self.weighted_average_exit - self.weighted_average_entry) * effective_qty, 2)
            else:
                self.realized_trade_pnl = round((self.weighted_average_entry - self.weighted_average_exit) * effective_qty, 2)

        # Planned Risk & Realized R-Multiple
        risk_per_point = max(0.0, abs(self.proposed_entry - self.proposed_stop))
        self.planned_risk = round(risk_per_point * self.entry_quantity, 2)
        if self.planned_risk > 0:
            self.realized_r_multiple = round(self.realized_trade_pnl / self.planned_risk, 2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TradeProposal:
    proposal_id: str
    timestamp: str
    underlying: str
    setup_type: str
    direction: str  # BULLISH / BEARISH / NEUTRAL
    strike: int
    option_type: str  # CE / PE / NONE
    contract_symbol: str
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: float
    risk_reward_ratio: float
    confidence_score: float
    priority_score: float
    quality_score: float
    max_loss_inr: float
    rationale: List[str]
    invalidation_condition: str
    state: str = ProposalState.PROPOSED.value
    lots: int = 1
    lot_size: int = 25
    total_quantity: int = 25
    product: str = "NRML"
    margin_status: Optional[str] = "PENDING_CHECK"
    required_margin: Optional[float] = None
    available_margin: Optional[float] = None
    margin_sufficient: Optional[bool] = None
    order_intent: Optional[Dict[str, Any]] = None
    risk_evaluation: Optional[Dict[str, Any]] = None
    approval_timestamp: Optional[str] = None
    rejection_reason: Optional[str] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def recalculate_exposure(self, lots: int, product: Optional[str] = None) -> None:
        if lots < 1:
            lots = 1
        self.lots = lots
        self.total_quantity = lots * self.lot_size
        if product:
            self.product = product
        risk_per_unit = max(0.0, self.entry_price - self.stop_loss)
        self.max_loss_inr = round(risk_per_unit * self.total_quantity, 2)
        if self.order_intent:
            self.order_intent["lots"] = self.lots
            self.order_intent["quantity"] = self.total_quantity
            self.order_intent["product"] = self.product
            self.order_intent["price"] = round(self.entry_price, 2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
