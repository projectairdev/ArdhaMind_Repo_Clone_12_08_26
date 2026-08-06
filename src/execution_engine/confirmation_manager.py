from __future__ import annotations
import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.models import (
    ExecutionRequest,
    ExecutionConfirmation,
)

logger = logging.getLogger("ConfirmationManager")

class ConfirmationManager:
    """
    Manages operator confirmations for manual executions.
    Ensures no trade can proceed without explicit CONFIRM action.
    """
    # Request ID -> ExecutionRequest
    _pending_requests: Dict[str, ExecutionRequest] = {}
    
    # Request ID -> ExecutionConfirmation
    _resolved_confirmations: Dict[str, ExecutionConfirmation] = {}

    @classmethod
    def register_request(cls, request: ExecutionRequest) -> None:
        """Registers a validated execution request that requires manual confirmation."""
        cls._pending_requests[request.request_id] = request
        logger.info(f"Registered manual confirmation request: {request.request_id}")

    @classmethod
    def get_pending_requests(cls) -> List[ExecutionRequest]:
        """Returns all registered requests currently waiting for operator confirmation."""
        return list(cls._pending_requests.values())

    @classmethod
    def get_pending_request(cls, request_id: str) -> Optional[ExecutionRequest]:
        """Retrieves a single pending request by ID."""
        return cls._pending_requests.get(request_id)

    @classmethod
    def confirm_request(
        cls, 
        request_id: str, 
        operator_name: str = "OPERATOR"
    ) -> Optional[ExecutionConfirmation]:
        """
        Confirms a pending execution request.
        Creates an immutable ExecutionConfirmation object.
        """
        request = cls._pending_requests.pop(request_id, None)
        if not request:
            logger.warning(f"Attempted to confirm non-existent or already processed request: {request_id}")
            return None
        
        confirmation = ExecutionConfirmation(
            confirmation_id=f"CONFIRM_{int(datetime.utcnow().timestamp())}_{request_id}",
            request_id=request_id,
            confirmed_by=operator_name,
            status="CONFIRMED",
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )
        cls._resolved_confirmations[request_id] = confirmation
        logger.info(f"Manual confirmation approved for request {request_id} by {operator_name}")
        return confirmation

    @classmethod
    def cancel_request(
        cls, 
        request_id: str, 
        operator_name: str = "OPERATOR"
    ) -> Optional[ExecutionConfirmation]:
        """
        Cancels/Rejects a pending execution request.
        Creates an immutable ExecutionConfirmation object with CANCELLED status.
        """
        request = cls._pending_requests.pop(request_id, None)
        if not request:
            logger.warning(f"Attempted to cancel non-existent or already processed request: {request_id}")
            return None
        
        confirmation = ExecutionConfirmation(
            confirmation_id=f"CONFIRM_{int(datetime.utcnow().timestamp())}_{request_id}",
            request_id=request_id,
            confirmed_by=operator_name,
            status="CANCELLED",
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )
        cls._resolved_confirmations[request_id] = confirmation
        logger.info(f"Manual confirmation cancelled for request {request_id} by {operator_name}")
        return confirmation

    @classmethod
    def get_confirmation(cls, request_id: str) -> Optional[ExecutionConfirmation]:
        """Retrieves confirmation status/result for a request."""
        return cls._resolved_confirmations.get(request_id)

    @classmethod
    def clear_all(cls):
        """Clears in-memory registers for test cleanliness."""
        cls._pending_requests.clear()
        cls._resolved_confirmations.clear()
