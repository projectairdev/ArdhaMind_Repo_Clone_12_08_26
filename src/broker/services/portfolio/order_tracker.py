from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
from src.models import BrokerOrder, ExecutionRequest, OrderState, ExecutionStatistics

logger = logging.getLogger("OrderTracker")


class OrderTracker:
    """
    Tracks complete order lifecycle and maps broker order status to standardized OrderState.
    """

    @staticmethod
    def map_broker_status(status: str, filled_qty: int, total_qty: int) -> str:
        """
        Maps raw broker status to standardized OrderState status.
        """
        status = status.upper()
        if status == "COMPLETE":
            return "FILLED"
        elif status == "REJECTED":
            return "REJECTED"
        elif status == "CANCELLED":
            return "CANCELLED"
        elif status in ["OPEN", "TRIGGER PENDING", "VALIDATION PENDING", "PUT ORDER REQ RECEIVED"]:
            if 0 < filled_qty < total_qty:
                return "PARTIALLY_FILLED"
            return "PENDING"
        elif "PART" in status or status == "PARTIALLY FILLED":
            return "PARTIALLY_FILLED"
        elif "EXPIRED" in status:
            return "EXPIRED"
        elif status in ["ACCEPTED", "APPROVED"]:
            return "ACCEPTED"
        elif status in ["SUBMITTED", "SENT", "AMO SENT"]:
            return "SUBMITTED"
        else:
            if filled_qty == total_qty and total_qty > 0:
                return "FILLED"
            elif 0 < filled_qty < total_qty:
                return "PARTIALLY_FILLED"
            return "PENDING"

    @staticmethod
    def track_orders(
        broker_orders: List[BrokerOrder],
        execution_requests: Optional[List[ExecutionRequest]] = None
    ) -> List[OrderState]:
        """
        Translates BrokerOrder instances into standardized, immutable OrderState instances.
        Cross-references with execution requests to track full lifecycle (e.g., from CREATED onwards).
        """
        order_states: List[OrderState] = []
        
        # Build map of request/orders for cross-referencing if available
        request_map = {}
        if execution_requests:
            for req in execution_requests:
                for req_order in req.orders:
                    # Key by symbol, type, quantity to match broker order
                    key = (req_order.tradingsymbol, req_order.transaction_type, req_order.quantity)
                    request_map[key] = req_order

        for bo in broker_orders:
            # Determine quantities
            filled = bo.filled_quantity
            total = bo.quantity
            pending = max(0, total - filled)
            
            # Map status
            mapped_status = OrderTracker.map_broker_status(bo.status, filled, total)
            
            # Form OrderState
            os = OrderState(
                order_id=bo.order_id,
                tradingsymbol=bo.tradingsymbol,
                exchange=bo.exchange,
                transaction_type=bo.transaction_type,
                quantity=total,
                filled_quantity=filled,
                pending_quantity=pending,
                status=mapped_status,
                average_price=bo.price if mapped_status == "FILLED" else 0.0,  # Or use average_price if bo has it
                trigger_price=0.0,  # Kite orders do have trigger_price but it's optional
                product=bo.product,
                order_type=bo.order_type,
                status_message=bo.status_message,
                timestamp=bo.order_timestamp
            )
            order_states.append(os)
            
        # Add "CREATED" states from outstanding execution requests that haven't been placed on broker yet
        # (e.g. requests with status PENDING, not yet having an order_id assigned)
        if execution_requests:
            # Find which symbols/orders from execution requests do not appear in broker orders
            placed_keys = {(bo.tradingsymbol, bo.transaction_type, bo.quantity) for bo in broker_orders}
            for req in execution_requests:
                if req.status == "PENDING":
                    for req_order in req.orders:
                        key = (req_order.tradingsymbol, req_order.transaction_type, req_order.quantity)
                        if key not in placed_keys:
                            os = OrderState(
                                order_id=f"TEMP_{req_order.candidate_id}",
                                tradingsymbol=req_order.tradingsymbol,
                                exchange=req_order.exchange,
                                transaction_type=req_order.transaction_type,
                                quantity=req_order.quantity,
                                filled_quantity=0,
                                pending_quantity=req_order.quantity,
                                status="CREATED",
                                average_price=0.0,
                                trigger_price=req_order.trigger_price,
                                product=req_order.product,
                                order_type=req_order.order_type,
                                status_message="Created local execution request, pending operator confirmation",
                                timestamp=req.timestamp
                            )
                            order_states.append(os)
                            
        return order_states

    @staticmethod
    def calculate_statistics(orders: List[OrderState]) -> ExecutionStatistics:
        """
        Computes performance metrics from a list of standardized OrderStates.
        """
        total = len(orders)
        if total == 0:
            return ExecutionStatistics()
            
        filled = sum(1 for o in orders if o.status == "FILLED")
        cancelled = sum(1 for o in orders if o.status == "CANCELLED")
        rejected = sum(1 for o in orders if o.status == "REJECTED")
        
        fill_rate = (filled / total) * 100.0 if total > 0 else 0.0
        
        return ExecutionStatistics(
            total_orders=total,
            filled_orders=filled,
            cancelled_orders=cancelled,
            rejected_orders=rejected,
            fill_rate=fill_rate,
            average_execution_time_ms=0.0  # Optional/Not trackable without fine-grained milliseconds logs
        )
