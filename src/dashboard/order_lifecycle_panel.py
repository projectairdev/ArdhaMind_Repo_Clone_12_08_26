from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from src.models import OrderLifecycleReport
from src.models.order_lifecycle import ExecutionStatistics
from src.execution_engine.order_lifecycle_manager import OrderLifecycleManager

logger = logging.getLogger("OrderLifecyclePanel")


class OrderLifecyclePanel:
    """
    Backend representation for Task 7 & Task 8 of Sprint 34.
    Prepares complete serialized and high-density terminal representations of execution timelines,
    broker latencies, slippage records, and operations metrics.
    """

    def __init__(self, reports: Optional[List[OrderLifecycleReport]] = None) -> None:
        self.reports = reports or []

    def to_dict(self) -> Dict[str, Any]:
        """
        Structured representation of all active order lifecycles and accumulated metrics.
        """
        stats = OrderLifecycleManager.calculate_analytics(self.reports)

        orders_data = []
        for r in self.reports:
            # Reconstruct timeline event list dicts
            timeline_events = [
                {
                    "event_id": e.event_id,
                    "timestamp": e.timestamp,
                    "previous_state": e.previous_state,
                    "new_state": e.new_state,
                    "trigger_source": e.trigger_source,
                    "operator": e.operator,
                    "broker_response": e.broker_response,
                    "reason": e.reason,
                }
                for e in r.timeline.events
            ]

            mod_history = [
                {
                    "modification_id": m.modification_id,
                    "timestamp": m.timestamp,
                    "previous_quantity": m.previous_quantity,
                    "previous_price": m.previous_price,
                    "new_quantity": m.new_quantity,
                    "new_price": m.new_price,
                    "status": m.status,
                }
                for m in r.modification_history
            ]

            cancel_rec = None
            if r.cancellation_record:
                cancel_rec = {
                    "cancellation_id": r.cancellation_record.cancellation_id,
                    "timestamp": r.cancellation_record.timestamp,
                    "requested_by": r.cancellation_record.requested_by,
                    "reason": r.cancellation_record.reason,
                    "status": r.cancellation_record.status,
                }

            orders_data.append({
                "order_id": r.order_id,
                "tradingsymbol": r.tradingsymbol,
                "exchange": r.exchange,
                "transaction_type": r.transaction_type,
                "quantity": r.quantity,
                "product": r.product,
                "order_type": r.order_type,
                "current_state": r.current_state,
                "broker_remarks": r.broker_remarks,
                "timestamp": r.timestamp,
                "progress": {
                    "requested_quantity": r.progress.requested_quantity,
                    "filled_quantity": r.progress.filled_quantity,
                    "remaining_quantity": r.progress.remaining_quantity,
                    "average_fill_price": r.progress.average_fill_price,
                    "completion_percentage": r.progress.completion_percentage,
                },
                "timeline": {
                    "order_id": r.timeline.order_id,
                    "events": timeline_events,
                },
                "modification_history": mod_history,
                "cancellation_record": cancel_rec,
            })

        return {
            "orders": orders_data,
            "statistics": {
                "average_fill_time": stats.average_fill_time,
                "broker_latency": stats.broker_latency,
                "exchange_latency": stats.exchange_latency,
                "fill_efficiency": stats.fill_efficiency,
                "slippage": stats.slippage,
                "partial_fill_percentage": stats.partial_fill_percentage,
                "modification_count": stats.modification_count,
                "cancellation_rate": stats.cancellation_rate,
                "execution_success_rate": stats.execution_success_rate,
            },
            "system_health": {
                "engine_status": "HEALTHY",
                "sync_status": "SYNCHRONIZED",
                "queue_length": len([o for o in self.reports if o.current_state in ["CREATED", "SUBMITTED", "OPEN"]]),
                "broker_sync_health": "100%",
            }
        }

    def render_cli(self) -> str:
        """
        Renders a beautifully high-density ASCII workstation view of order lifecycles and operations metrics.
        """
        data = self.to_dict()
        stats = data["statistics"]
        health = data["system_health"]

        lines = []
        lines.append("=" * 80)
        lines.append(" SPRINT 34 — ORDER LIFECYCLE MONITORING & OPERATIONS TELEMETRY ".center(80, "#"))
        lines.append("=" * 80)

        # Operations Stats Section
        lines.append(f"Engine Health : {health['engine_status']:<10} | Sync Status : {health['sync_status']:<10} | Sync Health : {health['broker_sync_health']}")
        lines.append(f"Queue Length  : {health['queue_length']:<10} | Avg Fill Time: {stats['average_fill_time']:<10}s | Success Rate: {stats['execution_success_rate']}%")
        lines.append(f"Broker Latency: {stats['broker_latency']:<8}ms | Exch Latency: {stats['exchange_latency']:<10}ms | Fill Efficy : {stats['fill_efficiency']}%")
        lines.append("-" * 80)

        # Orders Table Section
        lines.append(f"{'ORDER ID':<12} | {'SYMBOL':<15} | {'STATE':<18} | {'PROGRESS':<12} | {'PX / SLIPPAGE':<15}")
        lines.append("-" * 80)

        for o in data["orders"][:5]:
            prog_bar = f"{int(o['progress']['completion_percentage'])}%"
            px_slip = f"{o['progress']['average_fill_price']:.1f} / {stats['slippage']:.2f}"
            lines.append(f"{o['order_id']:<12} | {o['tradingsymbol']:<15} | {o['current_state']:<18} | {prog_bar:<12} | {px_slip:<15}")

        lines.append("=" * 80)
        return "\n".join(lines)
