from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from src.models import OrderState, ExecutionTimeline

logger = logging.getLogger("TimelineGenerator")


class TimelineGenerator:
    """
    Generates chronological event timelines for order lifecycles.
    """

    @staticmethod
    def generate_timeline(
        order: OrderState,
        past_timeline: Optional[ExecutionTimeline] = None
    ) -> ExecutionTimeline:
        """
        Creates or appends to a timeline based on the order's current state and history.
        """
        events = list(past_timeline.events) if past_timeline else []
        existing_statuses = {evt["status"] for evt in events} if events else set()

        # Add initial CREATED event if not present and order status is beyond CREATED
        if "CREATED" not in existing_statuses:
            events.append({
                "timestamp": order.timestamp,
                "status": "CREATED",
                "details": f"Order local instance generated for {order.quantity} shares of {order.tradingsymbol}."
            })

        # Add SUBMITTED if status is SUBMITTED or higher and not already in timeline
        if order.status != "CREATED" and "SUBMITTED" not in existing_statuses:
            events.append({
                "timestamp": order.timestamp,
                "status": "SUBMITTED",
                "details": f"Order routed to {order.exchange}."
            })

        # Add intermediate or final state if it's new
        if order.status not in ["CREATED", "SUBMITTED"] and order.status not in existing_statuses:
            details_map = {
                "FILLED": f"Order fully filled at average price of INR {order.average_price:.2f}.",
                "PARTIALLY_FILLED": f"Order partially filled. Filled: {order.filled_quantity}, Pending: {order.pending_quantity}.",
                "CANCELLED": f"Order cancelled by operator or broker. Message: {order.status_message}",
                "REJECTED": f"Order rejected. Reason: {order.status_message}",
                "EXPIRED": f"Order expired on the exchange.",
                "PENDING": f"Order is active and pending execution on exchange.",
                "ACCEPTED": f"Order accepted by exchange and assigned broker order ID: {order.order_id}."
            }
            details = details_map.get(order.status, f"Order status changed to {order.status}.")
            events.append({
                "timestamp": order.timestamp,
                "status": order.status,
                "details": details
            })

        return ExecutionTimeline(
            order_id=order.order_id,
            tradingsymbol=order.tradingsymbol,
            events=events
        )

    @staticmethod
    def generate_all_timelines(
        orders: List[OrderState],
        past_timelines: Optional[List[ExecutionTimeline]] = None
    ) -> List[ExecutionTimeline]:
        """
        Helper to generate timelines for a batch of orders.
        """
        past_map = {t.order_id: t for t in past_timelines} if past_timelines else {}
        new_timelines: List[ExecutionTimeline] = []
        for order in orders:
            past = past_map.get(order.order_id)
            new_timelines.append(TimelineGenerator.generate_timeline(order, past))
        return new_timelines
