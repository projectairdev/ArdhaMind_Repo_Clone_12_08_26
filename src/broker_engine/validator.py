from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from src.models.execution_report import ExecutionRequest, ExecutionOrder
from src.broker_engine.connection import ConnectionManager
from src.broker_engine.funds import FundsManager

logger = logging.getLogger("BrokerValidator")


class BrokerValidationError(Exception):
    """Custom exception for Broker pre-execution validation errors."""
    pass


class BrokerValidator:
    """
    Validates Broker Connection, Funds, Trading symbol, Exchange, Quantity,
    Product, and Order Type before any order is submitted.
    """
    @staticmethod
    def validate_request(request: ExecutionRequest) -> List[str]:
        """
        Validates the entire ExecutionRequest and returns a list of validation error messages.
        If the list is empty, validation has succeeded.
        """
        errors: List[str] = []
        
        # 1. Validate Connection
        conn = ConnectionManager()
        if not conn.is_connected():
            errors.append("Broker not connected.")
            return errors  # Cannot validate further without connection
            
        client = conn.get_client()

        # 2. Retrieve funds for margin validation
        try:
            funds = FundsManager.get_funds_info()
            available_margin = funds.available_margin
        except Exception as e:
            errors.append(f"Failed to retrieve funds for validation: {e}")
            available_margin = 0.0

        # Validate each order in the request
        for idx, order in enumerate(request.orders):
            # 3. Validate Trading Symbol
            if not order.tradingsymbol or not isinstance(order.tradingsymbol, str):
                errors.append(f"Order [{idx}]: Invalid trading symbol '{order.tradingsymbol}'")
                
            # 4. Validate Exchange
            if order.exchange not in ["NSE", "NFO", "BSE", "CDS", "MCX"]:
                errors.append(f"Order [{idx}]: Invalid exchange '{order.exchange}'. Expected NSE, NFO, etc.")
                
            # 5. Validate Quantity
            if order.quantity <= 0:
                errors.append(f"Order [{idx}]: Quantity must be greater than 0, got {order.quantity}")
                
            # 6. Validate Product
            if order.product not in ["MIS", "NRML", "CNC"]:
                errors.append(f"Order [{idx}]: Invalid product '{order.product}'. Expected MIS, NRML, CNC")
                
            # 7. Validate Order Type
            if order.order_type not in ["MARKET", "LIMIT", "SL", "SL-M"]:
                errors.append(f"Order [{idx}]: Invalid order type '{order.order_type}'. Expected MARKET, LIMIT, SL, SL-M")

            # 8. Validate Funds / Margin
            # Attempt to estimate margin requirements.
            # If price is specified (or we fetch quote), require that available margin is sufficient.
            try:
                price = order.price
                # If market order and price is 0, try to fetch last price from quote as an estimate
                if price <= 0 and order.order_type == "MARKET":
                    try:
                        quote = client.quote(f"{order.exchange}:{order.tradingsymbol}")
                        if quote and f"{order.exchange}:{order.tradingsymbol}" in quote:
                            instrument_quote = quote[f"{order.exchange}:{order.tradingsymbol}"]
                            price = instrument_quote.get("last_price", 0.0)
                    except Exception:
                        pass
                
                estimated_cost = price * order.quantity
                if estimated_cost > available_margin:
                    errors.append(
                        f"Order [{idx}]: Insufficient funds. Estimated cost {estimated_cost:.2f} "
                        f"exceeds available margin {available_margin:.2f}"
                    )
            except Exception as e:
                logger.warning(f"Failed to perform detailed fund validation for order [{idx}]: {e}")

        return errors
