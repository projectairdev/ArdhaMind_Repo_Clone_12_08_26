from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass(frozen=True)
class TradeItem:
    trade_id: str
    order_id: str
    symbol: str
    exchange: str
    side: str
    quantity: int
    execution_price: float
    execution_time: str

class TradesService:
    @staticmethod
    def get_trades(gateway) -> List[TradeItem]:
        """
        Retrieves today's executed trades from the broker gateway and maps to TradeItem.
        """
        raw_list = gateway.get_trades()

        if not raw_list:
            return []

        trades = []
        for item in raw_list:
            if isinstance(item, dict):
                trades.append(TradeItem(
                    trade_id=item.get("trade_id", "N/A"),
                    order_id=item.get("order_id", "N/A"),
                    symbol=item.get("tradingsymbol", "N/A"),
                    exchange=item.get("exchange", "N/A"),
                    side=item.get("transaction_type", "BUY"),
                    quantity=int(item.get("quantity", 0)),
                    execution_price=float(item.get("average_price") or item.get("price") or 0.0),
                    execution_time=str(item.get("fill_timestamp") or item.get("trade_timestamp", ""))
                ))
        return trades
