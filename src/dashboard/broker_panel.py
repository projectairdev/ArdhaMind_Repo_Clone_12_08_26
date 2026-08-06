from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from src.models.execution_report import (
    BrokerFunds,
    BrokerPosition,
    BrokerOrder,
    BrokerAccount,
    ExecutionStatus
)

logger = logging.getLogger("BrokerPanel")


class BrokerPanel:
    """
    Dashboard Panel presenting the real-time manual broker integration state,
    funds, open positions, today's MTM, pending orders, and recent execution statuses.
    """

    def __init__(
        self,
        connection_status: Optional[Dict[str, Any]] = None,
        funds: Optional[BrokerFunds] = None,
        positions: Optional[List[BrokerPosition]] = None,
        pending_orders: Optional[List[BrokerOrder]] = None,
        execution_status: Optional[ExecutionStatus] = None,
        account: Optional[BrokerAccount] = None,
    ) -> None:
        self.connection_status = connection_status or {"connected": False, "client_id": "N/A", "client_name": "N/A"}
        self.funds = funds
        self.positions = positions or []
        self.pending_orders = pending_orders or []
        self.execution_status = execution_status
        self.account = account

    def to_dict(self) -> Dict[str, Any]:
        """
        Structured representation of broker panel metrics.
        """
        # Calculate today's MTM
        today_mtm = sum(pos.today_mtm for pos in self.positions) if self.positions else 0.0

        return {
            "connection": {
                "connected": self.connection_status.get("connected", False),
                "client_id": self.account.client_id if self.account else self.connection_status.get("client_id", "N/A"),
                "client_name": self.account.name if self.account else self.connection_status.get("client_name", "N/A"),
                "email": self.account.email if self.account else "N/A",
                "broker": self.account.broker if self.account else "Zerodha"
            },
            "funds": {
                "available_cash": self.funds.available_cash if self.funds else 0.0,
                "margins": self.funds.margins if self.funds else 0.0,
                "utilized_margin": self.funds.utilized_margin if self.funds else 0.0,
                "available_margin": self.funds.available_margin if self.funds else 0.0,
            },
            "positions_summary": {
                "total_positions_count": len(self.positions),
                "today_mtm": today_mtm,
            },
            "positions": [
                {
                    "tradingsymbol": pos.tradingsymbol,
                    "exchange": pos.exchange,
                    "product": pos.product,
                    "quantity": pos.quantity,
                    "average_price": pos.average_price,
                    "last_price": pos.last_price,
                    "pnl": pos.pnl,
                    "today_mtm": pos.today_mtm,
                }
                for pos in self.positions
            ],
            "pending_orders": [
                {
                    "order_id": o.order_id,
                    "tradingsymbol": o.tradingsymbol,
                    "exchange": o.exchange,
                    "transaction_type": o.transaction_type,
                    "quantity": o.quantity,
                    "product": o.product,
                    "order_type": o.order_type,
                    "status": o.status,
                    "price": o.price,
                }
                for o in self.pending_orders
            ],
            "execution_status": {
                "status": self.execution_status.status if self.execution_status else "IDLE",
                "message": self.execution_status.message if self.execution_status else "No active manual executions",
            }
        }

    def render_cli(self) -> str:
        """
        Renders a beautifully formatted ASCII text card representing the Broker Panel.
        """
        data = self.to_dict()
        conn = data["connection"]
        funds = data["funds"]
        pos_summary = data["positions_summary"]
        exec_status = data["execution_status"]

        lines = []
        lines.append("+- BROKER INTEGRATION PANEL ---------------------------------------------------+")
        
        # Connection Header
        status_str = "CONNECTED" if conn["connected"] else "DISCONNECTED"
        lines.append(
            f"| STATUS: {status_str:<12} | Client ID: {conn['client_id']:<10} | Name: {conn['client_name'][:25]:<25} |"
        )
        lines.append("|" + "-" * 78 + "|")

        # Funds / Margins Block
        lines.append(
            f"| Available Cash  : INR {funds['available_cash']:<12.2f} | Utilized Margin  : INR {funds['utilized_margin']:<12.2f} |"
        )
        lines.append(
            f"| Total Margin    : INR {funds['margins']:<12.2f} | Available Margin : INR {funds['available_margin']:<12.2f} |"
        )
        lines.append("|" + "-" * 78 + "|")

        # MTM Summary
        mtm_sign = "+" if pos_summary["today_mtm"] >= 0 else ""
        lines.append(
            f"| Open Positions  : {pos_summary['total_positions_count']:<3}          | Today's MTM      : INR {mtm_sign}{pos_summary['today_mtm']:<12.2f} |"
        )
        lines.append("|" + "-" * 78 + "|")

        # Open Positions list (top 3)
        if data["positions"]:
            lines.append("| OPEN POSITIONS (Top 3):                                                      |")
            for pos in data["positions"][:3]:
                qty_str = f"{pos['quantity']} shares"
                pnl_sign = "+" if pos['pnl'] >= 0 else ""
                lines.append(
                    f"|   * {pos['tradingsymbol'][:20]:<20} | {pos['product']:<5} | Qty: {qty_str:<10} | PnL: {pnl_sign}{pos['pnl']:<12.2f} |"
                )
            lines.append("|" + "-" * 78 + "|")

        # Pending Orders
        if data["pending_orders"]:
            lines.append("| PENDING ORDERS:                                                              |")
            for order in data["pending_orders"][:3]:
                lines.append(
                    f"|   # {order['order_id']:<10} | {order['tradingsymbol'][:18]:<18} | {order['transaction_type']:<4} | Qty: {order['quantity']:<5} | {order['status']:<11} |"
                )
            lines.append("|" + "-" * 78 + "|")
        else:
            lines.append("| PENDING ORDERS  : NONE                                                       |")
            lines.append("|" + "-" * 78 + "|")

        # Last Execution Status
        lines.append(
            f"| LAST EXECUTION  : {exec_status['status']:<10} | Msg: {exec_status['message'][:45]:<45} |"
        )
        lines.append("+------------------------------------------------------------------------------+")

        return "\n".join(lines)
