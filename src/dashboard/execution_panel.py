from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from src.models import ExecutionStateReport

logger = logging.getLogger("ExecutionPanel")


class ExecutionPanel:
    """
    Dashboard Panel presenting the real-time order states, synchronized positions,
    portfolio tracking, execution timeline history, and overall audit metrics.
    """

    def __init__(self, report: Optional[ExecutionStateReport] = None) -> None:
        self.report = report

    def to_dict(self) -> Dict[str, Any]:
        """
        Structured representation of execution panel metrics.
        """
        if not self.report:
            return {
                "orders": [],
                "positions": [],
                "portfolio": {
                    "active_positions_count": 0,
                    "closed_positions_count": 0,
                    "capital_utilized": 0.0,
                    "available_capital": 1000000.0,
                    "portfolio_mtm": 0.0,
                    "today_mtm": 0.0
                },
                "timelines": [],
                "statistics": {
                    "total_orders": 0,
                    "filled_orders": 0,
                    "cancelled_orders": 0,
                    "rejected_orders": 0,
                    "fill_rate": 0.0
                }
            }

        orders_data = [
            {
                "order_id": o.order_id,
                "tradingsymbol": o.tradingsymbol,
                "exchange": o.exchange,
                "transaction_type": o.transaction_type,
                "quantity": o.quantity,
                "filled_quantity": o.filled_quantity,
                "pending_quantity": o.pending_quantity,
                "status": o.status,
                "average_price": o.average_price,
                "product": o.product,
                "order_type": o.order_type,
                "status_message": o.status_message,
                "timestamp": o.timestamp
            }
            for o in self.report.orders
        ]

        positions_data = [
            {
                "tradingsymbol": p.tradingsymbol,
                "exchange": p.exchange,
                "product": p.product,
                "quantity": p.quantity,
                "average_price": p.average_price,
                "last_price": p.last_price,
                "pnl": p.pnl,
                "realized_pnl": p.realized_pnl,
                "unrealized_pnl": p.unrealized_pnl,
                "today_mtm": p.today_mtm
            }
            for p in self.report.positions.positions
        ]

        timelines_data = [
            {
                "order_id": t.order_id,
                "tradingsymbol": t.tradingsymbol,
                "events": t.events
            }
            for t in self.report.timelines
        ]

        stats = self.report.statistics

        return {
            "orders": orders_data,
            "positions": positions_data,
            "portfolio": {
                "active_positions_count": len(self.report.portfolio.active_positions),
                "closed_positions_count": len(self.report.portfolio.closed_positions),
                "capital_utilized": self.report.portfolio.capital_utilized,
                "available_capital": self.report.portfolio.available_capital,
                "portfolio_mtm": self.report.portfolio.portfolio_mtm,
                "today_mtm": self.report.positions.today_mtm
            },
            "timelines": timelines_data,
            "statistics": {
                "total_orders": stats.total_orders,
                "filled_orders": stats.filled_orders,
                "cancelled_orders": stats.cancelled_orders,
                "rejected_orders": stats.rejected_orders,
                "fill_rate": stats.fill_rate
            }
        }

    def render_cli(self) -> str:
        """
        Renders a beautifully formatted ASCII text card representing the Execution & Position Lifecycle.
        """
        data = self.to_dict()
        portfolio = data["portfolio"]
        stats = data["statistics"]

        lines = []
        lines.append("+- EXECUTION & POSITION LIFECYCLE PANEL ---------------------------------------+")
        
        # Portfolio Status header
        mtm_sign = "+" if portfolio["today_mtm"] >= 0 else ""
        lines.append(
            f"| Portfolio MTM : INR {mtm_sign}{portfolio['portfolio_mtm']:<12.2f} | Today's MTM    : INR {mtm_sign}{portfolio['today_mtm']:<12.2f} |"
        )
        lines.append(
            f"| Capital Used  : INR {portfolio['capital_utilized']:<12.2f} | Capital Avail  : INR {portfolio['available_capital']:<12.2f} |"
        )
        lines.append(
            f"| Active Pos    : {portfolio['active_positions_count']:<3}                 | Closed Pos     : {portfolio['closed_positions_count']:<3}                  |"
        )
        lines.append("|" + "-" * 78 + "|")

        # Order Statistics
        lines.append(
            f"| Total Orders  : {stats['total_orders']:<4}  | Filled: {stats['filled_orders']:<4}  | Cancelled: {stats['cancelled_orders']:<4}  | Fill Rate: {stats['fill_rate']:.1f}% |"
        )
        lines.append("|" + "-" * 78 + "|")

        # Live Orders list (Top 3)
        lines.append("| LIVE ORDERS & STATES:                                                        |")
        if data["orders"]:
            for order in data["orders"][:3]:
                qty_str = f"{order['filled_quantity']}/{order['quantity']}"
                lines.append(
                    f"|   * [{order['status']:<14}] {order['tradingsymbol'][:18]:<18} | {order['transaction_type']:<4} | Qty: {qty_str:<8} | ID: {order['order_id'][:12]:<12} |"
                )
        else:
            lines.append("|   No active orders tracked.                                                  |")
        lines.append("|" + "-" * 78 + "|")

        # Open Positions list (Top 3)
        lines.append("| SYNCHRONIZED POSITIONS (Active):                                             |")
        active_positions = [p for p in data["positions"] if p["quantity"] != 0]
        if active_positions:
            for pos in active_positions[:3]:
                qty_str = f"{pos['quantity']} sh"
                pnl_sign = "+" if pos['pnl'] >= 0 else ""
                lines.append(
                    f"|   # {pos['tradingsymbol'][:20]:<20} | {pos['product']:<5} | Qty: {qty_str:<10} | PnL: {pnl_sign}{pos['pnl']:<12.2f} |"
                )
        else:
            lines.append("|   No active open positions.                                                  |")
        lines.append("|" + "-" * 78 + "|")

        # Order Execution Timeline (Last 3 events)
        lines.append("| CHRONOLOGICAL EXECUTION TIMELINE:                                            |")
        events_found = False
        event_count = 0
        for timeline in data["timelines"]:
            for evt in timeline["events"]:
                if event_count >= 3:
                    break
                lines.append(
                    f"|   [{evt['timestamp']}] {timeline['tradingsymbol'][:12]} -> {evt['status']:<10} | {evt['details'][:35]:<35} |"
                )
                events_found = True
                event_count += 1
            if event_count >= 3:
                break
        if not events_found:
            lines.append("|   No timeline events recorded.                                               |")

        lines.append("+------------------------------------------------------------------------------+")

        return "\n".join(lines)
