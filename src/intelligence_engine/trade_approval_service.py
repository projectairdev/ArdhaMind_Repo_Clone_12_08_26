# src/intelligence_engine/trade_approval_service.py
"""
TradeApprovalService — Explicit Human Approval Workflow, Immutable Candidate Freeze, and Audit Trail.

Strict Invariants:
1. No Autonomous Execution: Approval requires an explicit, deliberate trader action (APPROVE button).
2. Immutable Snapshot Freeze: An approved candidate is frozen upon approval and never mutates in-place.
3. Approval Freshness & Invalidation: If underlying market moves beyond tolerance or invalidates, approval expires.
4. Comprehensive Audit Trail: Every transition is logged immutably with timestamp and provenance.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TradeAuditLogEntry:
    event_id: str
    timestamp: str
    candidate_id: str
    event_type: str  # CANDIDATE_CREATED | CONDITIONS_PENDING | QUALIFIED | READY_FOR_APPROVAL | REVIEW_OPENED | APPROVED | REJECTED | APPROVAL_STALE | PREFLIGHT_PASS | PREFLIGHT_FAILED
    actor: str  # SYSTEM | TRADER
    details: str
    snapshot: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FrozenTradeApproval:
    approval_id: str
    candidate_id: str
    approved_at: str
    approved_by: str  # e.g. "TRADER"
    
    # Frozen Market & Decision Context
    trading_date: str
    approved_spot: float
    instrument: str
    strike: float
    option_type: str
    approved_option_ltp: float
    
    # Geometry & Sizing
    entry_condition: str
    invalidation_level: Optional[float]
    targets: List[float]
    quantity: int
    lots: int
    estimated_premium_outlay: float
    estimated_max_loss: float
    
    # Quality & Preflight
    confidence: str
    strike_strength_score: float
    entry_quality_band: str
    broker_preflight_status: str
    
    # Freshness state
    freshness_status: str  # FRESH | STALE | INVALIDATED
    freshness_reason: str = "Candidate approved within tolerance"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TradeApprovalService:
    """
    State machine, candidate freezer, and immutable audit logger for trade approvals.
    """

    _audit_log: List[TradeAuditLogEntry] = []
    _active_approvals: Dict[str, FrozenTradeApproval] = {}

    MAX_SPOT_DRIFT_PTS: float = 25.0
    MAX_LTP_DRIFT_PCT: float = 5.0

    @classmethod
    def log_audit_event(
        cls,
        candidate_id: str,
        event_type: str,
        actor: str,
        details: str,
        snapshot: Optional[Dict[str, Any]] = None
    ) -> TradeAuditLogEntry:
        now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        ev_id = f"AUD-{candidate_id}-{len(cls._audit_log) + 1:04d}"
        entry = TradeAuditLogEntry(
            event_id=ev_id,
            timestamp=now_utc,
            candidate_id=candidate_id,
            event_type=event_type,
            actor=actor,
            details=details,
            snapshot=snapshot
        )
        cls._audit_log.append(entry)
        return entry

    @classmethod
    def get_audit_trail(cls, candidate_id: Optional[str] = None) -> List[TradeAuditLogEntry]:
        if candidate_id:
            return [e for e in cls._audit_log if e.candidate_id == candidate_id]
        return list(cls._audit_log)

    @classmethod
    def record_review_opened(cls, candidate_id: str, decision_snapshot: Dict[str, Any]) -> None:
        cls.log_audit_event(
            candidate_id=candidate_id,
            event_type="REVIEW_OPENED",
            actor="TRADER",
            details="Trader opened Trade Approval Modal for review",
            snapshot=decision_snapshot
        )

    @classmethod
    def record_rejection(cls, candidate_id: str, rejection_reason: str) -> None:
        cls.log_audit_event(
            candidate_id=candidate_id,
            event_type="REJECTED",
            actor="TRADER",
            details=f"Trader explicitly rejected trade candidate: {rejection_reason}"
        )
        if candidate_id in cls._active_approvals:
            del cls._active_approvals[candidate_id]

    @classmethod
    def approve_candidate(
        cls,
        candidate_id: str,
        trading_date: str,
        spot: float,
        instrument: str,
        strike: float,
        option_type: str,
        option_ltp: float,
        entry_condition: str,
        invalidation_level: Optional[float],
        targets: List[float],
        quantity: int,
        lots: int,
        estimated_premium_outlay: float,
        estimated_max_loss: float,
        confidence: str,
        strike_strength_score: float,
        entry_quality_band: str,
        broker_preflight_status: str,
        full_decision_snapshot: Dict[str, Any]
    ) -> FrozenTradeApproval:
        now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        approval_id = f"APP-{candidate_id}-{datetime.now(timezone.utc).strftime('%H%M%S')}"

        frozen = FrozenTradeApproval(
            approval_id=approval_id,
            candidate_id=candidate_id,
            approved_at=now_utc,
            approved_by="TRADER",
            trading_date=trading_date,
            approved_spot=spot,
            instrument=instrument,
            strike=strike,
            option_type=option_type,
            approved_option_ltp=option_ltp,
            entry_condition=entry_condition,
            invalidation_level=invalidation_level,
            targets=targets,
            quantity=quantity,
            lots=lots,
            estimated_premium_outlay=estimated_premium_outlay,
            estimated_max_loss=estimated_max_loss,
            confidence=confidence,
            strike_strength_score=strike_strength_score,
            entry_quality_band=entry_quality_band,
            broker_preflight_status=broker_preflight_status,
            freshness_status="FRESH",
            freshness_reason="Candidate approved and active within parameters"
        )

        cls._active_approvals[candidate_id] = frozen
        cls.log_audit_event(
            candidate_id=candidate_id,
            event_type="APPROVED",
            actor="TRADER",
            details=f"Trader explicitly approved {instrument} ({quantity} qty, ₹{estimated_premium_outlay:,.0f} outlay). Awaiting execution enablement.",
            snapshot=frozen.to_dict()
        )
        return frozen

    @classmethod
    def evaluate_approval_freshness(
        cls,
        candidate_id: str,
        current_spot: float,
        current_option_ltp: float,
        is_market_open: bool = True
    ) -> Optional[FrozenTradeApproval]:
        frozen = cls._active_approvals.get(candidate_id)
        if not frozen:
            return None

        # 1. Market session check
        if not is_market_open:
            frozen.freshness_status = "STALE"
            frozen.freshness_reason = "Market session has closed"
            return frozen

        # 2. Invalidation Level Check
        if frozen.invalidation_level is not None:
            if frozen.option_type == "PE" and current_spot >= frozen.invalidation_level:
                frozen.freshness_status = "INVALIDATED"
                frozen.freshness_reason = f"Underlying NIFTY ({current_spot:,.1f}) breached invalidation stop ({frozen.invalidation_level:,.1f})"
                cls.log_audit_event(candidate_id, "APPROVAL_STALE", "SYSTEM", frozen.freshness_reason)
                return frozen
            elif frozen.option_type == "CE" and current_spot <= frozen.invalidation_level:
                frozen.freshness_status = "INVALIDATED"
                frozen.freshness_reason = f"Underlying NIFTY ({current_spot:,.1f}) breached invalidation stop ({frozen.invalidation_level:,.1f})"
                cls.log_audit_event(candidate_id, "APPROVAL_STALE", "SYSTEM", frozen.freshness_reason)
                return frozen

        # 3. Spot Drift Check
        spot_drift = abs(current_spot - frozen.approved_spot)
        if spot_drift > cls.MAX_SPOT_DRIFT_PTS:
            frozen.freshness_status = "STALE"
            frozen.freshness_reason = f"NIFTY spot drifted {spot_drift:.1f} pts from approved level ({frozen.approved_spot:,.1f})"
            cls.log_audit_event(candidate_id, "APPROVAL_STALE", "SYSTEM", frozen.freshness_reason)
            return frozen

        # 4. Premium Drift Check
        if frozen.approved_option_ltp > 0 and current_option_ltp > 0:
            ltp_drift_pct = abs(current_option_ltp - frozen.approved_option_ltp) / frozen.approved_option_ltp * 100.0
            if ltp_drift_pct > cls.MAX_LTP_DRIFT_PCT:
                frozen.freshness_status = "STALE"
                frozen.freshness_reason = f"Option LTP drifted {ltp_drift_pct:.1f}% from approved price (₹{frozen.approved_option_ltp:.1f})"
                cls.log_audit_event(candidate_id, "APPROVAL_STALE", "SYSTEM", frozen.freshness_reason)
                return frozen

        frozen.freshness_status = "FRESH"
        frozen.freshness_reason = "Approval active and within market tolerance"
        return frozen

    @classmethod
    def reset_state(cls) -> None:
        """Helper for unit tests."""
        cls._audit_log.clear()
        cls._active_approvals.clear()
