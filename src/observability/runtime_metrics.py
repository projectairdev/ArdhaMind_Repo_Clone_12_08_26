from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import threading
from typing import Any, Dict


@dataclass
class RuntimeMetricsCollector:
    """
    Central collector for canonical runtime telemetry.
    Tracks Provider, EventBus, StateStore, FeedHealth, Candles, and Engine metrics.
    """
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # Provider metrics
    provider_connected: bool = False
    provider_reconnects: int = 0
    provider_packets_received: int = 0
    provider_malformed_packets: int = 0
    desired_subscriptions: int = 0
    active_subscriptions: int = 0

    # EventBus metrics
    events_published: int = 0
    events_dispatched: int = 0
    queue_depth: int = 0
    queue_overflows: int = 0
    subscriber_errors: int = 0

    # LiveMarketState metrics
    state_revision: int = 0
    accepted_updates: int = 0
    rejected_updates: int = 0
    out_of_order_rejects: int = 0
    session_rejects: int = 0

    # Feed metrics
    feed_status: str = "HEALTHY"
    tick_age_ms: float = 0.0
    ticks_per_sec: float = 0.0
    provider_latency_ms: float = 0.0

    # Candles metrics
    closed_candles_count: int = 0
    missing_intervals_detected: int = 0
    backfills_completed: int = 0

    # Decisions & Analytics
    analytics_revision: int = 0
    latest_decision_state: str = "BLOCKED"

    def record_tick_accepted(self) -> None:
        with self._lock:
            self.accepted_updates += 1
            self.state_revision += 1

    def record_tick_rejected(self, reason: str = "GENERIC") -> None:
        with self._lock:
            self.rejected_updates += 1
            if "ORDER" in reason.upper():
                self.out_of_order_rejects += 1
            elif "SESSION" in reason.upper():
                self.session_rejects += 1

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "provider": {
                    "connected": self.provider_connected,
                    "reconnect_count": self.provider_reconnects,
                    "packets_received": self.provider_packets_received,
                    "malformed_packets": self.provider_malformed_packets,
                    "desired_subscriptions": self.desired_subscriptions,
                    "active_subscriptions": self.active_subscriptions,
                },
                "event_bus": {
                    "published": self.events_published,
                    "dispatched": self.events_dispatched,
                    "queue_depth": self.queue_depth,
                    "overflows": self.queue_overflows,
                    "subscriber_errors": self.subscriber_errors,
                },
                "live_state": {
                    "revision": self.state_revision,
                    "accepted": self.accepted_updates,
                    "rejected": self.rejected_updates,
                    "out_of_order": self.out_of_order_rejects,
                    "session_rejects": self.session_rejects,
                },
                "feed": {
                    "status": self.feed_status,
                    "tick_age_ms": self.tick_age_ms,
                    "ticks_per_sec": self.ticks_per_sec,
                    "provider_latency_ms": self.provider_latency_ms,
                },
                "candles": {
                    "closed_count": self.closed_candles_count,
                    "missing_intervals": self.missing_intervals_detected,
                    "backfills": self.backfills_completed,
                },
            }
