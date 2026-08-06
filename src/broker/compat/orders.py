from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.models.execution_report import (
    BrokerOrder,
    ExecutionRequest,
    ExecutionOrder,
    ExecutionReport,
    ExecutionResponse
)
from src.broker.compat.connection import ConnectionManager
from src.broker.compat.validator import BrokerValidator

logger = logging.getLogger("BrokerOrders")


class OrdersManager:
    """
    Manages retrieving broker orders, filtering order lists, and executing orders
    after explicit manual operator confirmation.
    """
    @staticmethod
    def get_orders() -> List[BrokerOrder]:
        """
        Retrieves all orders from Zerodha KiteConnect for today and maps to BrokerOrder list.
        """
        try:
            client = ConnectionManager().get_client()
            raw_orders = client.orders()
            
            if not raw_orders:
                return []
                
            broker_orders = []
            for o in raw_orders:
                # Safely extract values
                order_id = str(o.get("order_id", ""))
                exchange_order_id = str(o.get("exchange_order_id", "")) if o.get("exchange_order_id") else ""
                tradingsymbol = str(o.get("tradingsymbol", ""))
                exchange = str(o.get("exchange", "NFO"))
                transaction_type = str(o.get("transaction_type", "BUY"))
                quantity = int(o.get("quantity", 0))
                product = str(o.get("product", "NRML"))
                order_type = str(o.get("order_type", "MARKET"))
                status = str(o.get("status", "OPEN"))
                price = float(o.get("price", 0.0))
                filled_quantity = int(o.get("filled_quantity", 0))
                order_timestamp = str(o.get("order_timestamp", ""))
                status_message = str(o.get("status_message", "")) if o.get("status_message") else ""
                
                broker_orders.append(
                    BrokerOrder(
                        order_id=order_id,
                        exchange_order_id=exchange_order_id,
                        tradingsymbol=tradingsymbol,
                        exchange=exchange,
                        transaction_type=transaction_type,
                        quantity=quantity,
                        product=product,
                        order_type=order_type,
                        status=status,
                        price=price,
                        filled_quantity=filled_quantity,
                        order_timestamp=order_timestamp,
                        status_message=status_message
                    )
                )
            return broker_orders
        except Exception as e:
            logger.error(f"Error fetching broker orders: {e}")
            return []

    @staticmethod
    def get_pending_orders() -> List[BrokerOrder]:
        """Filters and returns pending/open orders."""
        all_orders = OrdersManager.get_orders()
        pending_statuses = {"OPEN", "TRIGGER PENDING", "VALIDATION PENDING", "PUT ORDER REQ RECEIVED"}
        return [o for o in all_orders if o.status in pending_statuses]

    @staticmethod
    def get_executed_orders() -> List[BrokerOrder]:
        """Filters and returns successfully executed orders."""
        all_orders = OrdersManager.get_orders()
        return [o for o in all_orders if o.status == "COMPLETE"]

    @staticmethod
    def get_rejected_orders() -> List[BrokerOrder]:
        """Filters and returns rejected orders."""
        all_orders = OrdersManager.get_orders()
        return [o for o in all_orders if o.status == "REJECTED"]

    @staticmethod
    def get_cancelled_orders() -> List[BrokerOrder]:
        """Filters and returns cancelled orders."""
        all_orders = OrdersManager.get_orders()
        return [o for o in all_orders if o.status == "CANCELLED"]

    @staticmethod
    def get_order_history(order_id: str) -> List[BrokerOrder]:
        """
        Retrieves history for a specific order ID.
        """
        try:
            client = ConnectionManager().get_client()
            raw_history = client.order_history(order_id)
            if not raw_history:
                return []
                
            broker_orders = []
            for o in raw_history:
                broker_orders.append(
                    BrokerOrder(
                        order_id=str(o.get("order_id", "")),
                        exchange_order_id=str(o.get("exchange_order_id", "")) if o.get("exchange_order_id") else "",
                        tradingsymbol=str(o.get("tradingsymbol", "")),
                        exchange=str(o.get("exchange", "NFO")),
                        transaction_type=str(o.get("transaction_type", "BUY")),
                        quantity=int(o.get("quantity", 0)),
                        product=str(o.get("product", "NRML")),
                        order_type=str(o.get("order_type", "MARKET")),
                        status=str(o.get("status", "OPEN")),
                        price=float(o.get("price", 0.0)),
                        filled_quantity=int(o.get("filled_quantity", 0)),
                        order_timestamp=str(o.get("order_timestamp", "")),
                        status_message=str(o.get("status_message", "")) if o.get("status_message") else ""
                    )
                )
            return broker_orders
        except Exception as e:
            logger.error(f"Error fetching order history for {order_id}: {e}")
            return []

    @staticmethod
    def execute_request(request: ExecutionRequest, confirmed: bool = False) -> ExecutionReport:
        """
        Processes an ExecutionRequest. 
        CRITICAL: Requires explicit confirmed=True parameter to execute order.
        """
        timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        report_id = f"REP_{request.request_id}_{int(datetime.utcnow().timestamp())}"
        
        # 1. Force manual operator confirmation requirement
        if not confirmed:
            logger.warning(f"BLOCK: Execution request {request.request_id} rejected due to missing manual operator confirmation.")
            return ExecutionReport(
                report_id=report_id,
                request_id=request.request_id,
                submitted_orders=[],
                accepted_orders=[],
                rejected_orders=list(request.orders),
                exchange_order_id="",
                broker_order_id="",
                timestamp=timestamp_str,
                failure_reason="MANUAL_CONFIRMATION_REQUIRED: Operator must confirm YES to execute broker transactions.",
                status="FAILED"
            )

        # 2. Pre-execution verification
        errors = BrokerValidator.validate_request(request)
        if errors:
            logger.error(f"BLOCK: Pre-execution validation failed for request {request.request_id}. Errors: {errors}")
            return ExecutionReport(
                report_id=report_id,
                request_id=request.request_id,
                submitted_orders=[],
                accepted_orders=[],
                rejected_orders=list(request.orders),
                exchange_order_id="",
                broker_order_id="",
                timestamp=timestamp_str,
                failure_reason=f"VALIDATION_FAILED: {'; '.join(errors)}",
                status="FAILED"
            )

        # 3. Execution of individual orders
        client = ConnectionManager().get_client()
        submitted: List[ExecutionOrder] = []
        accepted: List[ExecutionOrder] = []
        rejected: List[ExecutionOrder] = []
        
        broker_order_id = ""
        exchange_order_id = ""
        failure_reason = ""
        
        for order in request.orders:
            submitted.append(order)
            try:
                # Map product and variety
                variety = "regular"
                
                # Execute order placement via KiteConnect
                resp_order_id = client.place_order(
                    variety=variety,
                    exchange=order.exchange,
                    tradingsymbol=order.tradingsymbol,
                    transaction_type=order.transaction_type,
                    quantity=order.quantity,
                    product=order.product,
                    order_type=order.order_type,
                    price=order.price if order.price > 0 else None,
                    trigger_price=order.trigger_price if order.trigger_price > 0 else None
                )
                
                if resp_order_id:
                    broker_order_id = resp_order_id
                    accepted.append(order)
                    logger.info(f"Order placed successfully. Broker Order ID: {broker_order_id}")
                else:
                    rejected.append(order)
                    failure_reason = "Broker returned empty order ID"
                    
            except Exception as e:
                logger.error(f"Failed to place order {order.tradingsymbol} with broker: {e}")
                rejected.append(order)
                failure_reason = str(e)

        # Determine overall report status
        if len(accepted) == len(submitted) and len(submitted) > 0:
            status = "COMPLETED"
        elif len(accepted) > 0:
            status = "PARTIAL"
        else:
            status = "FAILED"

        return ExecutionReport(
            report_id=report_id,
            request_id=request.request_id,
            submitted_orders=submitted,
            accepted_orders=accepted,
            rejected_orders=rejected,
            exchange_order_id=exchange_order_id,
            broker_order_id=broker_order_id,
            timestamp=timestamp_str,
            failure_reason=failure_reason,
            status=status
        )
