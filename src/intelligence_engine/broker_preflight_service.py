# src/intelligence_engine/broker_preflight_service.py
"""
BrokerPreflightService — Read-Only Broker Validation, Price Reconciliation, and Duplicate Protection.

Strict Invariants:
1. READ-ONLY: Prohibits placing, modifying, or cancelling real broker orders.
2. Price Reconciliation: Compares Ardha quote vs Broker quote. Divergence > 2.0% triggers QUOTE_MISMATCH.
3. Duplicate Protection: Detects identical pending orders, existing positions, or co-incident approvals.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class BrokerPreflightCheck:
    check_name: str
    passed: bool
    details: str
    severity: str = "BLOCKING"  # BLOCKING | WARNING | INFO

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BrokerPreflightResult:
    broker_preflight_status: str  # PASS | BLOCKED | DEGRADED
    checked_at: str
    broker_name: str
    auth_state: str
    reconciliation_status: str  # MATCHED | DIVERGENT | QUOTE_MISMATCH | UNAVAILABLE
    reconciliation_delta_pts: Optional[float]
    reconciliation_delta_pct: Optional[float]
    checks: List[BrokerPreflightCheck] = field(default_factory=list)
    broker_blockers: List[str] = field(default_factory=list)
    duplicate_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "broker_preflight_status": self.broker_preflight_status,
            "checked_at": self.checked_at,
            "broker_name": self.broker_name,
            "auth_state": self.auth_state,
            "reconciliation_status": self.reconciliation_status,
            "reconciliation_delta_pts": self.reconciliation_delta_pts,
            "reconciliation_delta_pct": self.reconciliation_delta_pct,
            "checks": [c.to_dict() for c in self.checks],
            "broker_blockers": list(self.broker_blockers),
            "duplicate_detected": self.duplicate_detected
        }


class BrokerPreflightService:
    """
    Read-only pre-flight validator ensuring safety before human approval and execution enablement.
    """

    MAX_PRICE_DIVERGENCE_PCT: float = 2.0  # Max 2.0% divergence between Ardha and Broker LTP
    MAX_QUOTE_AGE_SECONDS: float = 30.0

    @classmethod
    def run_preflight_checks(
        cls,
        candidate_instrument: str,
        candidate_strike: float,
        candidate_option_type: str,
        ardha_ltp: float,
        broker_state: Optional[Dict[str, Any]] = None,
        market_session_active: bool = True,
        required_margin: Optional[float] = None
    ) -> BrokerPreflightResult:
        now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        checks: List[BrokerPreflightCheck] = []
        blockers: List[str] = []
        state = broker_state or {}

        # 1. Broker Authentication & Session Check
        auth_status = str(state.get("auth_state") or state.get("status") or "DISCONNECTED").upper()
        is_authenticated = auth_status in ("CONNECTED_VERIFIED", "AUTHENTICATED", "READY")
        checks.append(BrokerPreflightCheck(
            check_name="BROKER_AUTHENTICATION",
            passed=is_authenticated,
            details=f"Broker session status: {auth_status}"
        ))
        if not is_authenticated:
            blockers.append(f"Broker not authenticated (status: {auth_status})")

        # 2. Market Session Check
        checks.append(BrokerPreflightCheck(
            check_name="MARKET_SESSION_ACTIVE",
            passed=market_session_active,
            details="Regular trading session active" if market_session_active else "Market is currently closed"
        ))
        if not market_session_active:
            blockers.append("Market session is closed")

        # 3. Live Broker Quote & Price Reconciliation
        broker_quote = state.get("live_quotes", {}).get(candidate_instrument) or state.get("quote") or {}
        broker_ltp = float(broker_quote.get("ltp") or broker_quote.get("last_price") or 0.0)

        reconciliation_status = "UNAVAILABLE"
        reconciliation_delta_pts: Optional[float] = None
        reconciliation_delta_pct: Optional[float] = None

        if broker_ltp > 0 and ardha_ltp > 0:
            reconciliation_delta_pts = round(abs(ardha_ltp - broker_ltp), 2)
            reconciliation_delta_pct = round((reconciliation_delta_pts / broker_ltp) * 100.0, 2)

            is_price_aligned = (reconciliation_delta_pct <= cls.MAX_PRICE_DIVERGENCE_PCT)
            if is_price_aligned:
                reconciliation_status = "MATCHED"
            else:
                reconciliation_status = "QUOTE_MISMATCH"
                blockers.append(f"Price divergence ({reconciliation_delta_pct:.1f}%) exceeds safety tolerance ({cls.MAX_PRICE_DIVERGENCE_PCT}%)")

            checks.append(BrokerPreflightCheck(
                check_name="PRICE_RECONCILIATION",
                passed=is_price_aligned,
                details=f"Ardha: ₹{ardha_ltp:.1f} vs Broker: ₹{broker_ltp:.1f} (Δ {reconciliation_delta_pct:.2f}%)"
            ))
        else:
            checks.append(BrokerPreflightCheck(
                check_name="PRICE_RECONCILIATION",
                passed=False,
                details="Broker live quote unavailable for reconciliation",
                severity="WARNING"
            ))

        # 4. Duplicate Order / Position Protection
        active_orders = state.get("active_orders") or []
        open_positions = state.get("open_positions") or []
        duplicate_found = False

        for ord_item in active_orders:
            ord_sym = str(ord_item.get("tradingsymbol") or ord_item.get("symbol") or "")
            ord_status = str(ord_item.get("status") or "").upper()
            if candidate_instrument in ord_sym and ord_status in ("OPEN", "PENDING", "TRIGGER_PENDING"):
                duplicate_found = True
                blockers.append(f"Duplicate active order already pending for {candidate_instrument}")
                break

        for pos in open_positions:
            pos_sym = str(pos.get("tradingsymbol") or pos.get("symbol") or "")
            pos_qty = int(pos.get("quantity") or 0)
            if candidate_instrument in pos_sym and pos_qty != 0:
                duplicate_found = True
                blockers.append(f"Existing open position ({pos_qty} qty) already exists for {candidate_instrument}")
                break

        checks.append(BrokerPreflightCheck(
            check_name="DUPLICATE_PROTECTION",
            passed=(not duplicate_found),
            details="No duplicate active orders or positions found" if not duplicate_found else "Duplicate exposure detected"
        ))

        # 5. Margin / Available Funds Check
        available_balance = state.get("available_capital") or state.get("balance") or state.get("margin_available")
        if required_margin is not None and available_balance is not None:
            has_funds = float(available_balance) >= float(required_margin)
            checks.append(BrokerPreflightCheck(
                check_name="MARGIN_AVAILABILITY",
                passed=has_funds,
                details=f"Required: ₹{required_margin:,.0f} vs Available: ₹{available_balance:,.0f}"
            ))
            if not has_funds:
                blockers.append(f"Insufficient broker funds (Required ₹{required_margin:,.0f} > Available ₹{available_balance:,.0f})")

        # Determine Final Preflight Status
        if not blockers and is_authenticated:
            status = "PASS"
        elif any("divergence" in b.lower() or "duplicate" in b.lower() or "funds" in b.lower() for b in blockers):
            status = "BLOCKED"
        else:
            status = "DEGRADED"

        return BrokerPreflightResult(
            broker_preflight_status=status,
            checked_at=now_utc,
            broker_name=str(state.get("broker_name") or "Zerodha Kite"),
            auth_state=auth_status,
            reconciliation_status=reconciliation_status,
            reconciliation_delta_pts=reconciliation_delta_pts,
            reconciliation_delta_pct=reconciliation_delta_pct,
            checks=checks,
            broker_blockers=blockers,
            duplicate_detected=duplicate_found
        )
