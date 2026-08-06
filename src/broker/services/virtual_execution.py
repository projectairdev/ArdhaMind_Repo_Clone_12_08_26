from __future__ import annotations
import os
import json
import time
import logging
from typing import List, Dict, Any

logger = logging.getLogger("VirtualExecutionManager")

class VirtualExecutionManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VirtualExecutionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, file_path: str = ".cache/virtual_portfolio.json") -> None:
        if getattr(self, "_initialized", False):
            return
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self.load_portfolio()
        self._initialized = True

    @classmethod
    def get_instance(cls) -> VirtualExecutionManager:
        return cls()

    def load_portfolio(self) -> None:
        if not os.path.exists(self.file_path):
            self.total_capital = 1000000.0
            self.available_cash = 1000000.0
            self.open_positions = {}
            self.orders = []
            return

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
            self.total_capital = float(data.get("total_capital", 1000000.0))
            self.available_cash = float(data.get("available_cash", 1000000.0))
            self.open_positions = data.get("open_positions", {})
            self.orders = data.get("orders", [])
        except Exception as e:
            logger.error(f"Failed to load virtual portfolio: {e}")
            self.total_capital = 1000000.0
            self.available_cash = 1000000.0
            self.open_positions = {}
            self.orders = []

    def save_portfolio(self) -> None:
        try:
            with open(self.file_path, "w") as f:
                json.dump({
                    "total_capital": self.total_capital,
                    "available_cash": self.available_cash,
                    "open_positions": self.open_positions,
                    "orders": self.orders
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save virtual portfolio: {e}")

    def clear_portfolio(self) -> None:
        self.total_capital = 1000000.0
        self.available_cash = 1000000.0
        self.open_positions = {}
        self.orders = []
        self.save_portfolio()

    def place_order(self, gateway, **kwargs) -> str:
        symbol = kwargs.get("tradingsymbol")
        exchange = kwargs.get("exchange", "NSE")
        tx_type = kwargs.get("transaction_type", "BUY").upper()
        quantity = int(kwargs.get("quantity", 0))
        product = kwargs.get("product", "NRML").upper()
        order_type = kwargs.get("order_type", "MARKET").upper()
        price = kwargs.get("price")

        order_id = f"VIRT_{int(time.time() * 1000)}"

        # Try to resolve LTP
        fill_price = price
        if not fill_price or order_type == "MARKET":
            try:
                ltps = gateway.get_ltp([f"{exchange}:{symbol}"])
                if ltps and f"{exchange}:{symbol}" in ltps:
                    fill_price = float(ltps[f"{exchange}:{symbol}"]["last_price"])
            except Exception:
                pass
        
        if not fill_price:
            fill_price = 100.0  # Fallback dummy price

        # Deduct / Add to cash
        cost = fill_price * quantity
        if tx_type == "BUY":
            self.available_cash -= cost
        else:
            self.available_cash += cost

        # Construct order
        order = {
            "order_id": order_id,
            "exchange_order_id": f"EXCH_{order_id}",
            "symbol": symbol,
            "exchange": exchange,
            "transaction_type": tx_type,
            "quantity": quantity,
            "filled_quantity": quantity,
            "product": product,
            "order_type": order_type,
            "status": "COMPLETE",
            "price": fill_price,
            "average_price": fill_price,
            "order_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "validity": "DAY",
            "status_message": "Virtual order filled immediately.",
            "is_virtual": True
        }
        self.orders.append(order)

        # Update position
        pos_key = f"{symbol}:{product}"
        current_pos = self.open_positions.get(pos_key)

        qty_delta = quantity if tx_type == "BUY" else -quantity
        if current_pos:
            old_qty = int(current_pos["quantity"])
            new_qty = old_qty + qty_delta
            if new_qty == 0:
                # Position closed - calculate realized P&L
                realized = (fill_price - float(current_pos["average_price"])) * old_qty
                if tx_type == "BUY":  # Short cover
                    realized = (float(current_pos["average_price"]) - fill_price) * abs(old_qty)
                self.total_capital += realized
                del self.open_positions[pos_key]
            else:
                # Update average price if increasing position in same direction
                if (old_qty > 0 and qty_delta > 0) or (old_qty < 0 and qty_delta < 0):
                    old_avg = float(current_pos["average_price"])
                    new_avg = ((old_qty * old_avg) + (qty_delta * fill_price)) / new_qty
                    current_pos["average_price"] = round(new_avg, 2)
                current_pos["quantity"] = new_qty
                current_pos["last_price"] = fill_price
                current_pos["unrealized_pnl"] = round((fill_price - float(current_pos["average_price"])) * new_qty, 2)
                current_pos["mtm"] = current_pos["unrealized_pnl"]
        else:
            if qty_delta != 0:
                self.open_positions[pos_key] = {
                    "symbol": symbol,
                    "product": product,
                    "exchange": exchange,
                    "quantity": qty_delta,
                    "buy_qty": quantity if tx_type == "BUY" else 0,
                    "sell_qty": quantity if tx_type == "SELL" else 0,
                    "average_price": fill_price,
                    "last_price": fill_price,
                    "mtm": 0.0,
                    "realized_pnl": 0.0,
                    "unrealized_pnl": 0.0,
                    "is_virtual": True
                }

        self.save_portfolio()
        return order_id

    def modify_order(self, **kwargs) -> str:
        return f"VIRT_{int(time.time() * 1000)}"

    def cancel_order(self, **kwargs) -> str:
        return f"VIRT_{int(time.time() * 1000)}"

    def update_market_prices(self, gateway) -> None:
        if not self.open_positions:
            return
        symbols = [f"{pos['exchange']}:{pos['symbol']}" for pos in self.open_positions.values()]
        try:
            ltps = gateway.get_ltp(symbols)
            if ltps:
                for pos in self.open_positions.values():
                    sym_key = f"{pos['exchange']}:{pos['symbol']}"
                    if sym_key in ltps:
                        ltp = float(ltps[sym_key]["last_price"])
                        pos["last_price"] = ltp
                        qty = int(pos["quantity"])
                        pos["unrealized_pnl"] = round((ltp - float(pos["average_price"])) * qty, 2)
                        pos["mtm"] = pos["unrealized_pnl"]
                self.save_portfolio()
        except Exception:
            pass
