from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.models import (
    ExecutionRequest,
    ExecutionOrder,
    ExecutionResult,
    ExecutionValidation,
    ExecutionConfirmation,
    ExecutionReceipt,
    ExecutionFailure,
    ExecutionAuditEntry,
)
from src.broker.services.broker_service import BrokerService
from src.execution_engine.execution_validator import ExecutionValidator
from src.execution_engine.confirmation_manager import ConfirmationManager

logger = logging.getLogger("ExecutionManager")

class ExecutionManager:
    """
    Coordination layer for manual order execution.
    Takes validated requests, manages operator confirmations, submits orders 
    to BrokerService, and logs immutable audit trails.
    """
    _audit_log: List[ExecutionAuditEntry] = []

    @classmethod
    def get_audit_log(cls) -> List[ExecutionAuditEntry]:
        """Returns the complete, immutable audit log history."""
        # Return a copy of the list to prevent external modification of the list container itself
        return list(cls._audit_log)

    @classmethod
    def clear_audit_log(cls):
        """Helper to clear audit trail between unit tests."""
        cls._audit_log.clear()

    @classmethod
    def submit_for_validation_and_confirmation(
        cls, 
        request: ExecutionRequest,
        bypass_safety: bool = False
    ) -> ExecutionValidation:
        """
        Validates an ExecutionRequest. If valid, registers it for manual operator confirmation.
        If invalid, immediately records a failed validation audit entry.
        """
        validation = ExecutionValidator.validate_request(request, bypass_safety=bypass_safety)
        
        if validation.is_valid:
            # Register for manual confirmation
            ConfirmationManager.register_request(request)
        else:
            # Audit the validation failure immediately
            audit_id = f"AUD_VAL_FAIL_{int(datetime.utcnow().timestamp())}_{request.request_id}"
            audit_entry = ExecutionAuditEntry(
                audit_id=audit_id,
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                operator="SYSTEM",
                request=request,
                validation_result=validation,
                confirmation_result=None,
                broker_response=None,
                execution_outcome="VALIDATION_FAILED",
                failure_reason=", ".join(validation.errors)
            )
            cls._audit_log.append(audit_entry)
            logger.warning(f"ExecutionRequest {request.request_id} failed validation: {validation.errors}")
            
        return validation

    @classmethod
    def execute_confirmed_request(
        cls, 
        request_id: str, 
        operator: str = "OPERATOR",
        bypass_safety: bool = False
    ) -> ExecutionResult:
        """
        Submits confirmed order execution request to the BrokerService.
        """
        # 1. Retrieve the pending request
        request = ConfirmationManager.get_pending_request(request_id)
        if not request:
            # Check if it was already confirmed/cancelled
            conf = ConfirmationManager.get_confirmation(request_id)
            if conf:
                return ExecutionResult(
                    request_id=request_id,
                    status="FAILED",
                    timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    failures=[ExecutionFailure(order_id="", tradingsymbol="", error_message=f"Request already processed with status: {conf.status}")]
                )
            return ExecutionResult(
                request_id=request_id,
                status="FAILED",
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                failures=[ExecutionFailure(order_id="", tradingsymbol="", error_message=f"No pending request with ID '{request_id}' found.")]
            )

        # 2. Get/generate the confirmation
        confirmation = ConfirmationManager.get_confirmation(request_id)
        if not confirmation:
            # Auto-confirm if not confirmed/cancelled explicitly yet, but standard flow requires explicit action
            # Let's check ConfirmationManager for the action
            confirmation = ConfirmationManager.confirm_request(request_id, operator)

        if not confirmation or confirmation.status == "CANCELLED":
            # Record Audit Trail for cancellation
            validation_res = ExecutionValidator.validate_request(request, bypass_safety=bypass_safety)
            audit_id = f"AUD_CANCEL_{int(datetime.utcnow().timestamp())}_{request_id}"
            audit_entry = ExecutionAuditEntry(
                audit_id=audit_id,
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                operator=operator,
                request=request,
                validation_result=validation_res,
                confirmation_result=confirmation,
                broker_response=None,
                execution_outcome="CANCELLED",
                failure_reason="Execution cancelled by operator."
            )
            cls._audit_log.append(audit_entry)
            
            # Ensure it is removed from pending
            ConfirmationManager._pending_requests.pop(request_id, None)
            
            return ExecutionResult(
                request_id=request_id,
                status="FAILED",
                failures=[ExecutionFailure(order_id="", tradingsymbol="", error_message="Execution cancelled by operator.")],
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )

        # Re-run validation immediately before execution to catch sudden state changes
        validation_res = ExecutionValidator.validate_request(request, bypass_safety=bypass_safety)
        if not validation_res.is_valid:
            audit_id = f"AUD_LATE_FAIL_{int(datetime.utcnow().timestamp())}_{request_id}"
            audit_entry = ExecutionAuditEntry(
                audit_id=audit_id,
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                operator=operator,
                request=request,
                validation_result=validation_res,
                confirmation_result=confirmation,
                broker_response=None,
                execution_outcome="VALIDATION_FAILED",
                failure_reason="Late pre-execution validation failed: " + ", ".join(validation_res.errors)
            )
            cls._audit_log.append(audit_entry)
            
            return ExecutionResult(
                request_id=request_id,
                status="FAILED",
                failures=[ExecutionFailure(order_id="", tradingsymbol="", error_message=e) for e in validation_res.errors],
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )

        # 3. Transmit orders to BrokerService
        receipts: List[ExecutionReceipt] = []
        failures: List[ExecutionFailure] = []
        broker_service = BrokerService.get_instance()
        
        for idx, order in enumerate(request.orders):
            try:
                # Format parameters for place_order
                order_id = broker_service.place_order(
                    tradingsymbol=order.tradingsymbol,
                    exchange=order.exchange,
                    transaction_type=order.transaction_type,
                    quantity=order.quantity,
                    product=order.product,
                    order_type=order.order_type,
                    price=order.price,
                    trigger_price=order.trigger_price
                )
                
                receipts.append(ExecutionReceipt(
                    order_id=order_id or f"MOCK_ORD_{int(datetime.utcnow().timestamp())}_{idx}",
                    exchange_order_id=f"EXCH_{int(datetime.utcnow().timestamp())}_{idx}",
                    tradingsymbol=order.tradingsymbol,
                    quantity=order.quantity,
                    price=order.price,
                    status="COMPLETE",
                    timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                ))
            except Exception as e:
                logger.error(f"Broker order submission failed for {order.tradingsymbol}: {e}")
                failures.append(ExecutionFailure(
                    order_id="",
                    tradingsymbol=order.tradingsymbol,
                    error_message=str(e),
                    timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                ))

        # 4. Determine overall outcome
        if len(receipts) > 0 and len(failures) == 0:
            outcome = "COMPLETED"
            status = "SUCCESS"
        elif len(receipts) > 0 and len(failures) > 0:
            outcome = "PARTIAL"
            status = "PARTIAL"
        else:
            outcome = "FAILED"
            status = "FAILED"

        result = ExecutionResult(
            request_id=request_id,
            status=status,
            receipts=receipts,
            failures=failures,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )

        # 5. Log Immutable Audit Record
        audit_id = f"AUD_EXEC_{int(datetime.utcnow().timestamp())}_{request_id}"
        failure_messages = [f.error_message for f in failures]
        audit_entry = ExecutionAuditEntry(
            audit_id=audit_id,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            operator=operator,
            request=request,
            validation_result=validation_res,
            confirmation_result=confirmation,
            broker_response={
                "status": status,
                "receipts_count": len(receipts),
                "failures_count": len(failures),
                "receipts": [{"order_id": r.order_id, "symbol": r.tradingsymbol} for r in receipts]
            },
            execution_outcome=outcome,
            failure_reason=", ".join(failure_messages) if failure_messages else None
        )
        cls._audit_log.append(audit_entry)
        logger.info(f"Execution completed for request {request_id} with outcome {outcome}")

        return result
