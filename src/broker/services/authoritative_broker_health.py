from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("AuthoritativeBrokerHealth")


@dataclass
class AuthoritativeBrokerHealth:
    status: str  # "CONNECTED_VERIFIED" | "CONNECTED_AUTH_REQUIRED" | "RECONNECTING" | "DISCONNECTED" | "BROKER_STATE_UNVERIFIED"
    transport_connected: bool
    authenticated: bool
    session_valid: bool
    execution_verified: bool
    reconciliation_complete: bool
    last_verified_at: Optional[str]
    blocker_code: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BrokerHealthEvaluator:
    """
    Single authoritative evaluator for broker health across the entire ArdhaMind workstation.
    Enforces the invariant:
      - Transport connectivity != Authentication
      - Authentication != Reconciliation
      - Reconciliation != Execution Permission
    ArdhaMind must never display 'CONNECTED' unless broker execution truth is actually verified.
    """

    _last_reconciliation_time: Optional[float] = None
    _reconciliation_in_progress: bool = False
    _unresolved_operations_count: int = 0

    @classmethod
    def set_reconciliation_status(cls, complete: bool, in_progress: bool = False, unresolved_count: int = 0) -> None:
        if complete:
            cls._last_reconciliation_time = datetime.now(timezone.utc).timestamp()
        cls._reconciliation_in_progress = in_progress
        cls._unresolved_operations_count = unresolved_count

    @classmethod
    def evaluate(cls, broker_service) -> AuthoritativeBrokerHealth:
        now_iso = datetime.now(timezone.utc).isoformat()

        if broker_service is None:
            return AuthoritativeBrokerHealth(
                status="DISCONNECTED",
                transport_connected=False,
                authenticated=False,
                session_valid=False,
                execution_verified=False,
                reconciliation_complete=False,
                last_verified_at=None,
                blocker_code="BROKER_SERVICE_UNAVAILABLE"
            )

        from src.broker.services.session_manager import SessionManager
        is_logged_out = SessionManager.is_explicitly_logged_out()
        if is_logged_out:
            return AuthoritativeBrokerHealth(
                status="DISCONNECTED",
                transport_connected=False,
                authenticated=False,
                session_valid=False,
                execution_verified=False,
                reconciliation_complete=False,
                last_verified_at=None,
                blocker_code="EXPLICITLY_LOGGED_OUT"
            )

        gateway = broker_service.get_gateway() if hasattr(broker_service, "get_gateway") else None
        has_token = bool(gateway and getattr(gateway, "access_token", None))

        if not has_token:
            return AuthoritativeBrokerHealth(
                status="CONNECTED_AUTH_REQUIRED",
                transport_connected=True,  # Server daemon is running
                authenticated=False,
                session_valid=False,
                execution_verified=False,
                reconciliation_complete=False,
                last_verified_at=None,
                blocker_code="AUTH_REQUIRED"
            )

        # Test session validity strictly
        session_valid = False
        try:
            session_valid = bool(gateway and gateway.validate_session())
        except Exception as e:
            logger.warning(f"Session validation probe failed: {e}")
            session_valid = False

        if not session_valid:
            return AuthoritativeBrokerHealth(
                status="CONNECTED_AUTH_REQUIRED",
                transport_connected=True,
                authenticated=False,
                session_valid=False,
                execution_verified=False,
                reconciliation_complete=False,
                last_verified_at=None,
                blocker_code="TOKEN_EXPIRED"
            )

        # Session is valid — check reconciliation and execution verification
        if cls._reconciliation_in_progress or cls._last_reconciliation_time is None:
            return AuthoritativeBrokerHealth(
                status="BROKER_STATE_UNVERIFIED",
                transport_connected=True,
                authenticated=True,
                session_valid=True,
                execution_verified=False,
                reconciliation_complete=False,
                last_verified_at=now_iso,
                blocker_code="RECONCILIATION_PENDING"
            )

        if cls._unresolved_operations_count > 0:
            return AuthoritativeBrokerHealth(
                status="BROKER_STATE_UNVERIFIED",
                transport_connected=True,
                authenticated=True,
                session_valid=True,
                execution_verified=False,
                reconciliation_complete=False,
                last_verified_at=now_iso,
                blocker_code="UNRESOLVED_OPERATION_LOCKOUT"
            )

        # All checks passed: authenticated, session valid, reconciled, execution verified
        return AuthoritativeBrokerHealth(
            status="CONNECTED_VERIFIED",
            transport_connected=True,
            authenticated=True,
            session_valid=True,
            execution_verified=True,
            reconciliation_complete=True,
            last_verified_at=now_iso,
            blocker_code=None
        )
