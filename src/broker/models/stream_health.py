from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class StreamHealthReport:
    connection_status: str  # "CONNECTED", "DISCONNECTED", "RECONNECTING"
    last_heartbeat: str     # ISO Timestamp or human-readable format
    reconnect_count: int
    tick_rate: float        # Ticks per second
    average_latency_ms: float
    message_throughput: int # Total ticks processed
    last_received_timestamp: str # ISO Timestamp of last received tick
    active_subscriptions: List[str]
    fallback_active: bool
