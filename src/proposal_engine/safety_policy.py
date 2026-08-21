from __future__ import annotations

import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ExecutionSafetyPolicy")


class BlockerCode(str, Enum):
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
    DAILY_LOSS_LIMIT_REACHED = "DAILY_LOSS_LIMIT_REACHED"
    RISK_LIMIT_REACHED = "RISK_LIMIT_REACHED"
    MAX_POSITIONS_REACHED = "MAX_POSITIONS_REACHED"
    MAX_EXPOSURE_REACHED = "MAX_EXPOSURE_REACHED"
    DUPLICATE_CONTRACT_EXPOSURE = "DUPLICATE_CONTRACT_EXPOSURE"
    PRICE_DRIFT_REQUIRES_RECONFIRMATION = "PRICE_DRIFT_REQUIRES_RECONFIRMATION"
    BROKER_STATE_UNVERIFIED = "BROKER_STATE_UNVERIFIED"
    FEED_STALE = "FEED_STALE"
    OPTION_QUOTE_STALE = "OPTION_QUOTE_STALE"
    UNRESOLVED_OPERATION_LOCKOUT = "UNRESOLVED_OPERATION_LOCKOUT"
    SESSION_RESTRICTION = "SESSION_RESTRICTION"


@dataclass
class ExecutionSafetyPolicy:
    """
    Central, versioned Phase 3 Execution Safety Policy.
    Configurable defaults marked clearly as policy defaults.
    """
    policy_version: str = "v3.1-staging"
    daily_loss_limit: float = 25000.0             # INR max realized daily loss before blocking new entries
    max_risk_per_trade: float = 10000.0           # INR max loss on single trade
    max_open_positions: int = 3                   # Max active positions simultaneously
    max_total_open_quantity: int = 500            # Max open units aggregated
    max_concurrent_pending_orders: int = 5        # Max unfilled pending orders
    max_slippage_pct: float = 5.0                 # Max allowable slippage percentage
    price_drift_tolerance_pct: float = 3.0        # Max price drift between proposal and execution
    market_freshness_seconds: int = 60            # Maximum age for market data tick
    option_freshness_seconds: int = 60            # Maximum age for option quote tick
    kill_switch_active: bool = False              # Server-authoritative entry block
    new_entries_allowed: bool = True              # General toggle

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyEvaluationResult:
    passed: bool
    blocker_code: Optional[str] = None
    failure_reason: Optional[str] = None
    policy_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SafetyGatekeeper:
    """
    Evaluates new entry proposals and live order submissions against
    centralized Execution Safety Policy.
    """

    def __init__(self, policy: Optional[ExecutionSafetyPolicy] = None) -> None:
        self.policy = policy or ExecutionSafetyPolicy()

    def evaluate_entry_order(
        self,
        proposal: Any,
        fresh_quote: Optional[Dict[str, Any]],
        current_daily_realized_loss: float,
        active_positions: List[Dict[str, Any]],
        active_orders: List[Dict[str, Any]],
        broker_connected: bool,
        unresolved_operations: List[Dict[str, Any]],
        kill_switch_active: Optional[bool] = None,
    ) -> SafetyEvaluationResult:
        """
        Server-authoritative check for NEW ENTRY order submissions.
        Returns SafetyEvaluationResult with explicit blocker codes.
        """
        ks_active = self.policy.kill_switch_active if kill_switch_active is None else kill_switch_active
        
        # 1. Kill Switch Check
        if ks_active:
            return SafetyEvaluationResult(
                passed=False,
                blocker_code=BlockerCode.KILL_SWITCH_ACTIVE.value,
                failure_reason="Emergency Kill Switch is active. All new entry submissions are blocked.",
                policy_metrics={"kill_switch_active": True}
            )

        # 2. Broker Connection Verification
        if not broker_connected:
            return SafetyEvaluationResult(
                passed=False,
                blocker_code=BlockerCode.BROKER_STATE_UNVERIFIED.value,
                failure_reason="Zerodha Kite broker session is disconnected or unverified.",
                policy_metrics={"broker_connected": False}
            )

        # 3. Unresolved Operation Lockout
        unresolved_for_entity = [
            op for op in unresolved_operations
            if op.get("current_status") in ("OUTCOME_UNVERIFIED", "SUBMISSION_OUTCOME_UNVERIFIED", "INITIATED")
        ]
        if len(unresolved_for_entity) > 0:
            return SafetyEvaluationResult(
                passed=False,
                blocker_code=BlockerCode.UNRESOLVED_OPERATION_LOCKOUT.value,
                failure_reason=f"Found {len(unresolved_for_entity)} unresolved execution operations. Reconciliation required before new orders.",
                policy_metrics={"unresolved_count": len(unresolved_for_entity)}
            )

        # 4. Daily Loss Circuit Breaker
        # current_daily_realized_loss is a positive number representing loss (e.g. 26000.0) or negative for profit
        if current_daily_realized_loss >= self.policy.daily_loss_limit:
            return SafetyEvaluationResult(
                passed=False,
                blocker_code=BlockerCode.DAILY_LOSS_LIMIT_REACHED.value,
                failure_reason=f"Daily realized loss (₹{current_daily_realized_loss:.2f}) reached or exceeded policy circuit breaker (₹{self.policy.daily_loss_limit:.2f}). New entries blocked.",
                policy_metrics={
                    "daily_realized_loss": current_daily_realized_loss,
                    "daily_loss_limit": self.policy.daily_loss_limit,
                }
            )

        # 5. Max Open Positions Check
        open_pos_count = len(active_positions)
        if open_pos_count >= self.policy.max_open_positions:
            return SafetyEvaluationResult(
                passed=False,
                blocker_code=BlockerCode.MAX_POSITIONS_REACHED.value,
                failure_reason=f"Maximum open positions limit ({self.policy.max_open_positions}) reached. Currently holding {open_pos_count} active positions.",
                policy_metrics={"open_positions": open_pos_count, "limit": self.policy.max_open_positions}
            )

        # 6. Aggregate Open Quantity Check
        total_open_qty = sum(int(p.get("quantity", 0)) for p in active_positions)
        requested_qty = getattr(proposal, "total_quantity", 0) or (getattr(proposal, "lots", 1) * getattr(proposal, "lot_size", 25))
        if (total_open_qty + requested_qty) > self.policy.max_total_open_quantity:
            return SafetyEvaluationResult(
                passed=False,
                blocker_code=BlockerCode.MAX_EXPOSURE_REACHED.value,
                failure_reason=f"Total open quantity ({total_open_qty + requested_qty} units) exceeds maximum portfolio limit ({self.policy.max_total_open_quantity} units).",
                policy_metrics={"total_quantity": total_open_qty + requested_qty, "limit": self.policy.max_total_open_quantity}
            )

        # 7. Duplicate Contract Exposure Check
        target_symbol = getattr(proposal, "contract_symbol", "").replace(" ", "").upper()
        matching_open_pos = [
            p for p in active_positions
            if p.get("contract_symbol", "").replace(" ", "").upper() == target_symbol
        ]
        if len(matching_open_pos) > 0:
            return SafetyEvaluationResult(
                passed=False,
                blocker_code=BlockerCode.DUPLICATE_CONTRACT_EXPOSURE.value,
                failure_reason=f"An active open position for {target_symbol} already exists in portfolio.",
                policy_metrics={"contract_symbol": target_symbol}
            )

        # 8. Per-Trade Risk Gate
        planned_loss = getattr(proposal, "max_loss_inr", 0.0)
        if planned_loss > self.policy.max_risk_per_trade:
            return SafetyEvaluationResult(
                passed=False,
                blocker_code=BlockerCode.RISK_LIMIT_REACHED.value,
                failure_reason=f"Planned trade risk (₹{planned_loss:.2f}) exceeds per-trade limit of ₹{self.policy.max_risk_per_trade:.2f}.",
                policy_metrics={"planned_risk": planned_loss, "limit": self.policy.max_risk_per_trade}
            )

        # 9. Fresh Quote & Price Drift Check
        if fresh_quote:
            quote_ltp = float(fresh_quote.get("last_price", 0.0) or fresh_quote.get("price", 0.0))
            approved_entry = float(getattr(proposal, "entry_price", 0.0))
            if approved_entry > 0 and quote_ltp > 0:
                drift_pts = abs(quote_ltp - approved_entry)
                drift_pct = (drift_pts / approved_entry) * 100.0
                if drift_pct > self.policy.price_drift_tolerance_pct:
                    return SafetyEvaluationResult(
                        passed=False,
                        blocker_code=BlockerCode.PRICE_DRIFT_REQUIRES_RECONFIRMATION.value,
                        failure_reason=f"Price drift ({drift_pct:.1f}%) exceeds tolerance ({self.policy.price_drift_tolerance_pct}%). Reference: ₹{approved_entry:.2f}, Live Quote: ₹{quote_ltp:.2f}. Trader re-confirmation required.",
                        policy_metrics={
                            "approved_entry": approved_entry,
                            "live_quote": quote_ltp,
                            "drift_pct": round(drift_pct, 2),
                            "tolerance_pct": self.policy.price_drift_tolerance_pct
                        }
                    )

        return SafetyEvaluationResult(
            passed=True,
            policy_metrics={
                "daily_loss_limit": self.policy.daily_loss_limit,
                "current_daily_realized_loss": current_daily_realized_loss,
                "open_positions": open_pos_count,
                "max_open_positions": self.policy.max_open_positions,
                "kill_switch_active": ks_active
            }
        )
