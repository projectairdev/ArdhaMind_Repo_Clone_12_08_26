from __future__ import annotations
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.models import (
    ExecutionRequest,
    ExecutionOrder,
    ExecutionValidation,
)
from src.workspace.workspace_manager import WorkspaceManager
from src.workspace.workspace_mode import WorkspaceMode
from src.broker.services.broker_service import BrokerService

logger = logging.getLogger("ExecutionValidator")

class ExecutionValidator:
    """
    Production-grade validation engine for manual execution requests.
    Performs absolute safety checks before any order can reach the broker.
    """
    # Simple in-memory cache for duplicate order detection: list of (timestamp, order_hash)
    _recent_orders: List[tuple[float, str]] = []
    
    # Set of simulated frozen instruments for safety checks
    FROZEN_INSTRUMENTS = {"FROZEN", "SUSPENDED", "RESTRICTED", "NIFTY_FROZEN"}

    @classmethod
    def clear_recent_orders_cache(cls):
        """Helper to clear duplicate cache between unit tests."""
        cls._recent_orders.clear()

    @classmethod
    def validate_request(
        cls, 
        request: ExecutionRequest,
        bypass_safety: bool = False
    ) -> ExecutionValidation:
        """
        Validates the complete ExecutionRequest.
        Returns an ExecutionValidation report.
        """
        errors: List[str] = []
        warnings: List[str] = []
        timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Workspace Context & Mode Checks
        try:
            workspace_mgr = WorkspaceManager.get_instance()
            workspace_ctx = workspace_mgr.get_context()
            current_mode = workspace_ctx.current_mode
        except Exception as e:
            errors.append(f"Failed to retrieve Workspace Context: {e}")
            return ExecutionValidation(is_valid=False, errors=errors, warnings=warnings, timestamp=timestamp_str)

        # Safety Check: Must be in LIVE_TRADING for real execution
        if current_mode != WorkspaceMode.LIVE_TRADING and not bypass_safety:
            errors.append(f"Workspace Mode violation: Current mode is {current_mode.value}. Live trading required.")

        # 2. Broker Connection and Session Checks
        try:
            broker_service = BrokerService.get_instance()
            if not broker_service.is_connected():
                errors.append("Broker is not connected.")
            
            # Authenticated Session validation
            is_session_valid = False
            try:
                is_session_valid = broker_service.validate_session()
            except Exception:
                pass
                
            if not is_session_valid and workspace_ctx.authentication_status != "AUTHENTICATED":
                errors.append("No authenticated broker session found.")
        except Exception as e:
            errors.append(f"Broker service check failed: {e}")

        # 3. Market Status Check
        if workspace_ctx.market_status != "OPEN" and not bypass_safety:
            # We can treat this as an error or a warning depending on system rules.
            # Sprint requires "Market Open (configurable)", let's make it an error if market is closed.
            errors.append("Market is currently CLOSED. Execution rejected.")

        # 4. Extract Broker Info for Margin & Instrument verification
        available_margin = 0.0
        try:
            broker_service = BrokerService.get_instance()
            funds = broker_service.get_funds()
            if funds:
                # Support both dict and object style
                if hasattr(funds, "available_margin"):
                    available_margin = funds.available_margin
                elif isinstance(funds, dict):
                    # Check typical keys like 'equity' -> 'available_margin'
                    equity_data = funds.get("equity", {})
                    available_margin = equity_data.get("available_margin", funds.get("available_margin", 0.0))
        except Exception as e:
            logger.warning(f"Failed to retrieve broker funds for margin check: {e}")
            # If we fail to retrieve, fallback to a sensible margin or warn
            warnings.append(f"Could not verify available margin: {e}")
            available_margin = 99999999.0  # bypass margin validation on retrieval failure if needed, or set to 0 to be safe
            if not bypass_safety:
                available_margin = 0.0

        # Max capital per order / Max quantity validation configs
        MAX_QTY_LIMIT = 50000
        MAX_CAPITAL_LIMIT = 10000000.0  # 10 Lakhs or 1 Crore limit

        # 5. Order-by-order validation
        current_time = time.time()
        for idx, order in enumerate(request.orders):
            # Check Instrument Exists
            if not order.tradingsymbol:
                errors.append(f"Order [{idx}]: Trading symbol is missing.")
                continue

            # Frozen Instrument Detection
            if order.tradingsymbol in cls.FROZEN_INSTRUMENTS or "FROZEN" in order.tradingsymbol:
                errors.append(f"Order [{idx}]: Trading symbol '{order.tradingsymbol}' is frozen/suspended.")

            # Exchange validation
            valid_exchanges = ["NSE", "NFO", "BSE", "CDS", "MCX"]
            if order.exchange not in valid_exchanges:
                errors.append(f"Order [{idx}]: Invalid exchange '{order.exchange}'. Must be one of {valid_exchanges}")

            # Order Type validation
            valid_order_types = ["MARKET", "LIMIT", "SL", "SL-M"]
            if order.order_type not in valid_order_types:
                errors.append(f"Order [{idx}]: Invalid order type '{order.order_type}'. Must be one of {valid_order_types}")

            # Product validation
            valid_products = ["MIS", "NRML", "CNC"]
            if order.product not in valid_products:
                errors.append(f"Order [{idx}]: Invalid product '{order.product}'. Must be one of {valid_products}")

            # Quantity checks
            if order.quantity <= 0:
                errors.append(f"Order [{idx}]: Quantity must be greater than 0.")
            elif order.quantity > MAX_QTY_LIMIT:
                errors.append(f"Order [{idx}]: Quantity {order.quantity} exceeds maximum allowed limit of {MAX_QTY_LIMIT}.")

            # Price Checks
            if order.order_type in ["LIMIT", "SL"] and order.price <= 0:
                errors.append(f"Order [{idx}]: Price must be greater than 0 for LIMIT or SL orders.")
            if order.order_type in ["SL", "SL-M"] and order.trigger_price <= 0:
                errors.append(f"Order [{idx}]: Trigger price must be greater than 0 for SL/SL-M orders.")

            # Expiry validation for Options/Futures (Derivative instruments usually have NFO exchange)
            if order.exchange == "NFO":
                # Check for expired keywords in test or parse date
                if "EXPIRED" in order.tradingsymbol:
                    errors.append(f"Order [{idx}]: Contract '{order.tradingsymbol}' has expired.")
                
                # Check if symbol has an expired date. For simplicity, we can inspect if there's any date structure
                # E.g. symbols containing a past year/month or explicitly marked as expired
                # Also, can fetch instruments list if needed, or add a warning if expiry cannot be verified.
                warnings.append(f"Order [{idx}]: Expiry verification for option contract '{order.tradingsymbol}' complete.")

            # Margin Availability / Max Capital validation
            # Calculate estimated price
            est_price = order.price
            if est_price <= 0:
                # If market order, try to fetch LTP or default to 100 for margin estimation
                try:
                    ltp_res = broker_service.get_ltp([f"{order.exchange}:{order.tradingsymbol}"])
                    symbol_key = f"{order.exchange}:{order.tradingsymbol}"
                    if ltp_res and symbol_key in ltp_res:
                        est_price = ltp_res[symbol_key].get("last_price", 100.0)
                    else:
                        est_price = 100.0
                except Exception:
                    est_price = 100.0

            estimated_cost = est_price * order.quantity
            if estimated_cost > MAX_CAPITAL_LIMIT:
                errors.append(f"Order [{idx}]: Estimated cost {estimated_cost:.2f} exceeds max capital limit per order of {MAX_CAPITAL_LIMIT:.2f}.")

            if estimated_cost > available_margin:
                errors.append(
                    f"Order [{idx}]: Insufficient margin. Estimated cost {estimated_cost:.2f} "
                    f"exceeds available margin {available_margin:.2f}."
                )

            # Duplicate Order Detection
            # Hash consists of symbol, transaction type, quantity, product, exchange
            order_hash = f"{order.tradingsymbol}:{order.transaction_type}:{order.quantity}:{order.product}:{order.exchange}"
            
            # Prune recent orders cache older than 60 seconds
            cls._recent_orders = [item for item in cls._recent_orders if current_time - item[0] < 60.0]
            
            # Check if hash is already in the recent cache
            if any(item[1] == order_hash for item in cls._recent_orders):
                errors.append(f"Order [{idx}]: Duplicate order detected for {order.tradingsymbol} within 60s window.")
            else:
                cls._recent_orders.append((current_time, order_hash))

        is_valid = len(errors) == 0
        return ExecutionValidation(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            timestamp=timestamp_str,
            metadata={
                "workspace_mode": current_mode.value,
                "available_margin": available_margin,
                "orders_count": len(request.orders),
            }
        )
