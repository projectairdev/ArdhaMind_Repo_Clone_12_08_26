from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.models import ExecutionAudit, ExecutionRequest, ExecutionReport

logger = logging.getLogger("ExecutionAuditLog")


class ExecutionAuditLog:
    """
    Maintains and appends to an immutable audit history of broker interactions.
    """

    @staticmethod
    def create_audit_record(
        action: str,
        request_payload: Dict[str, Any],
        response_payload: Dict[str, Any],
        status: str,
        error_message: str = ""
    ) -> ExecutionAudit:
        """
        Creates a single, immutable ExecutionAudit record.
        """
        timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        audit_id = f"AUD_{int(datetime.utcnow().timestamp())}_{hash(f'{action}_{timestamp_str}') % 10000}"
        
        return ExecutionAudit(
            audit_id=audit_id,
            timestamp=timestamp_str,
            action=action,
            request_payload=request_payload,
            response_payload=response_payload,
            status=status,
            error_message=error_message
        )

    @staticmethod
    def audit_execution_request(
        request: ExecutionRequest,
        report: ExecutionReport
    ) -> ExecutionAudit:
        """
        Converts an execution request and its final broker report into an immutable audit record.
        """
        req_payload = {
            "request_id": request.request_id,
            "orders_count": len(request.orders),
            "orders": [
                {
                    "symbol": o.tradingsymbol,
                    "qty": o.quantity,
                    "exchange": o.exchange,
                    "transaction_type": o.transaction_type,
                    "product": o.product
                } for o in request.orders
            ]
        }
        
        resp_payload = {
            "report_id": report.report_id,
            "status": report.status,
            "broker_order_id": report.broker_order_id,
            "exchange_order_id": report.exchange_order_id,
            "accepted_count": len(report.accepted_orders),
            "rejected_count": len(report.rejected_orders)
        }

        status = "SUCCESS" if report.status in ["COMPLETED", "PARTIAL"] else "FAILURE"
        
        return ExecutionAuditLog.create_audit_record(
            action="ORDER_EXECUTION",
            request_payload=req_payload,
            response_payload=resp_payload,
            status=status,
            error_message=report.failure_reason
        )
