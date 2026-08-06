from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional
from src.models import DecisionReport, CandidateDecision
from src.models.execution_report import ExecutionRequest, ExecutionOrder

logger = logging.getLogger("ExecutionBuilder")


class ExecutionBuilder:
    """
    Responsible for generating immutable ExecutionRequests from DecisionReports.
    Maps trading decisions into structured broker orders with correct parameters (lot sizes, exchange).
    """
    @staticmethod
    def build_execution_request(
        decision_report: DecisionReport,
        lot_size: int = 25,
        default_product: str = "NRML",
        default_order_type: str = "MARKET"
    ) -> ExecutionRequest:
        """
        Translates executable decisions (BUY/SELL) from a DecisionReport into an ExecutionRequest.
        """
        orders: List[ExecutionOrder] = []
        
        for candidate in decision_report.candidate_decisions:
            # We only generate orders for explicit BUY or SELL decisions
            if candidate.decision not in ["BUY", "SELL"]:
                continue
                
            # Deduce exchange: NSE for equity, NFO for options (which contain CE/PE or have more complex symbols)
            symbol = candidate.tradingsymbol
            is_option = any(symbol.endswith(suffix) for suffix in ["CE", "PE"])
            exchange = "NFO" if is_option else "NSE"
            
            # Map lots to quantities: quantity = lots * lot_size
            lots = candidate.allocated_lots if candidate.allocated_lots > 0 else 1
            quantity = lots * lot_size if is_option else lots
            
            order = ExecutionOrder(
                candidate_id=candidate.candidate_id,
                tradingsymbol=symbol,
                exchange=exchange,
                transaction_type=candidate.decision,
                quantity=quantity,
                product=default_product,
                order_type=default_order_type,
                price=0.0,
                trigger_price=0.0
            )
            orders.append(order)
            
        request_id = f"REQ_{decision_report.report_id}_{int(datetime.utcnow().timestamp())}"
        
        return ExecutionRequest(
            request_id=request_id,
            decision_report_id=decision_report.report_id,
            orders=orders,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            status="PENDING"
        )
