from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging

@dataclass(frozen=True)
class PositionItem:
    symbol: str
    product: str
    exchange: str
    quantity: int
    buy_qty: int
    sell_qty: int
    average_price: float
    last_price: float
    mtm: float
    realized_pnl: float
    unrealized_pnl: float
    is_virtual: bool = False

@dataclass(frozen=True)
class AccountPositions:
    net: List[PositionItem]
    day: List[PositionItem]

class PositionsService:
    @staticmethod
    def get_positions(gateway) -> AccountPositions:
        """
        Retrieves active trading positions from the broker gateway and maps to AccountPositions.
        Separates into net and day positions.
        """
        raw_res = gateway.get_positions()
        
        net_list = []
        day_list = []
        
        if isinstance(raw_res, dict):
            net_list = raw_res.get("net", [])
            day_list = raw_res.get("day", [])
        elif isinstance(raw_res, list):
            # Safe fallback if gateway returned a flat list of items or objects (e.g. MockBrokerGateway)
            net_list = raw_res
            day_list = []
            
        def parse_item(item) -> Optional[PositionItem]:
            if hasattr(item, "tradingsymbol"):  # BrokerPosition object
                symbol = item.tradingsymbol
                product = item.product
                exchange = item.exchange
                quantity = int(item.quantity)
                buy_qty = quantity if quantity > 0 else 0
                sell_qty = -quantity if quantity < 0 else 0
                average_price = float(item.average_price)
                last_price = float(item.last_price)
                mtm = float(item.today_mtm)
                unrealized_pnl = float(item.pnl)
                realized_pnl = 0.0
            elif isinstance(item, dict):  # raw dict
                symbol = item.get("tradingsymbol", "N/A")
                product = item.get("product", "N/A")
                exchange = item.get("exchange", "N/A")
                quantity = int(item.get("quantity", 0))
                buy_qty = int(item.get("buy_quantity", 0))
                sell_qty = int(item.get("sell_quantity", 0))
                average_price = float(item.get("average_price", 0.0))
                last_price = float(item.get("last_price", 0.0))
                mtm = float(item.get("m2m", 0.0) or item.get("today_mtm", 0.0))
                unrealized_pnl = float(item.get("unrealised", 0.0) or item.get("pnl", 0.0))
                realized_pnl = float(item.get("realised", 0.0) or 0.0)
            else:
                return None
                
            return PositionItem(
                symbol=symbol,
                product=product,
                exchange=exchange,
                quantity=quantity,
                buy_qty=buy_qty,
                sell_qty=sell_qty,
                average_price=average_price,
                last_price=last_price,
                mtm=mtm,
                realized_pnl=realized_pnl,
                unrealized_pnl=unrealized_pnl,
                is_virtual=False
            )
            
        parsed_net = []
        for x in net_list:
            p = parse_item(x)
            if p:
                parsed_net.append(p)
                
        parsed_day = []
        for x in day_list:
            p = parse_item(x)
            if p:
                parsed_day.append(p)
                
        return AccountPositions(net=parsed_net, day=parsed_day)
