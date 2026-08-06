from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass(frozen=True)
class HoldingItem:
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    current_price: float
    current_value: float
    unrealized_pnl: float
    day_change: float
    day_change_pct: float

class HoldingsService:
    @staticmethod
    def get_holdings(gateway) -> List[HoldingItem]:
        """
        Retrieves live stock holdings from the broker gateway and maps to HoldingItem.
        Handles both dictionary formats and custom objects gracefully.
        """
        raw_list = gateway.get_holdings()

        if not raw_list:
            return []

        items = []
        for item in raw_list:
            if hasattr(item, "tradingsymbol"):  # BrokerHolding object
                symbol = item.tradingsymbol
                exchange = item.exchange
                quantity = int(item.quantity)
                average_price = float(item.average_price)
                current_price = float(item.last_price)
                unrealized_pnl = float(item.pnl)
                current_value = quantity * current_price
                day_change = 0.0
                day_change_pct = 0.0
            elif isinstance(item, dict):  # raw dict
                symbol = item.get("tradingsymbol", "N/A")
                exchange = item.get("exchange", "N/A")
                quantity = int(item.get("quantity", 0))
                average_price = float(item.get("average_price", 0.0))
                current_price = float(item.get("last_price", 0.0))
                unrealized_pnl = float(item.get("pnl", 0.0))
                current_value = quantity * current_price
                
                close_price = float(item.get("close_price", 0.0))
                if close_price > 0:
                    day_change = current_price - close_price
                    day_change_pct = (day_change / close_price) * 100.0
                else:
                    day_change = float(item.get("day_change", 0.0))
                    day_change_pct = float(item.get("day_change_percentage", 0.0))
            else:
                continue
            
            items.append(HoldingItem(
                symbol=symbol,
                exchange=exchange,
                quantity=quantity,
                average_price=average_price,
                current_price=current_price,
                current_value=current_value,
                unrealized_pnl=unrealized_pnl,
                day_change=day_change,
                day_change_pct=day_change_pct
            ))
        return items
