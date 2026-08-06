from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
import logging

@dataclass(frozen=True)
class OrderItem:
    order_id: str
    exchange_order_id: str
    symbol: str
    exchange: str
    transaction_type: str
    quantity: int
    filled_quantity: int
    product: str
    order_type: str
    status: str
    price: float
    average_price: float
    order_timestamp: str
    validity: str
    status_message: str = ""
    is_virtual: bool = False

@dataclass(frozen=True)
class AccountOrders:
    all_orders: List[OrderItem]
    pending: List[OrderItem]
    open_orders: List[OrderItem]
    cancelled: List[OrderItem]
    rejected: List[OrderItem]
    completed: List[OrderItem]

class OrdersService:
    @staticmethod
    def get_orders(gateway) -> AccountOrders:
        """
        Retrieves today's orders from the broker gateway and maps to AccountOrders.
        Categorizes orders by status.
        """
        raw_list = gateway.get_orders()

        all_orders = []
        for item in raw_list:
            if hasattr(item, "order_id"):  # BrokerOrder object
                order_id = item.order_id
                exchange_order_id = item.exchange_order_id
                symbol = item.tradingsymbol
                exchange = item.exchange
                transaction_type = item.transaction_type
                quantity = int(item.quantity)
                filled_quantity = int(item.filled_quantity)
                product = item.product
                order_type = item.order_type
                status = item.status
                price = float(item.price)
                average_price = float(item.price)  # BrokerOrder mock has only price
                order_timestamp = str(item.order_timestamp)
                validity = "DAY"
                status_message = getattr(item, "status_message", "")
            elif isinstance(item, dict):  # raw dict
                order_id = item.get("order_id", "N/A")
                exchange_order_id = item.get("exchange_order_id", "N/A") or "N/A"
                symbol = item.get("tradingsymbol", "N/A")
                exchange = item.get("exchange", "N/A")
                transaction_type = item.get("transaction_type", "BUY")
                quantity = int(item.get("quantity", 0))
                filled_quantity = int(item.get("filled_quantity", 0))
                product = item.get("product", "N/A")
                order_type = item.get("order_type", "N/A")
                status = item.get("status", "N/A")
                price = float(item.get("price", 0.0))
                average_price = float(item.get("average_price", 0.0))
                order_timestamp = str(item.get("order_timestamp") or "")
                validity = item.get("validity", "DAY")
                status_message = item.get("status_message", "")
            else:
                continue
                
            all_orders.append(OrderItem(
                order_id=order_id,
                exchange_order_id=exchange_order_id,
                symbol=symbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                filled_quantity=filled_quantity,
                product=product,
                order_type=order_type,
                status=status,
                price=price,
                average_price=average_price,
                order_timestamp=order_timestamp,
                validity=validity,
                status_message=status_message,
                is_virtual=False
            ))

        pending = [o for o in all_orders if o.status in ("TRIGGER PENDING", "PENDING", "PUT ORDER REQ RECEIVED")]
        open_list = [o for o in all_orders if o.status in ("OPEN", "MODIFY PENDING", "VALIDATION PENDING")]
        cancelled = [o for o in all_orders if o.status == "CANCELLED"]
        rejected = [o for o in all_orders if o.status == "REJECTED"]
        completed = [o for o in all_orders if o.status == "COMPLETE"]
        
        return AccountOrders(
            all_orders=all_orders,
            pending=pending,
            open_orders=open_list,
            cancelled=cancelled,
            rejected=rejected,
            completed=completed
        )
