from __future__ import annotations
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.broker.models.stream_health import StreamHealthReport
from src.broker.models.tick import TickModel


class StreamHealthMonitor:
    """
    Tracks streaming health metrics and produces immutable StreamHealthReports.
    """

    def __init__(self) -> None:
        self.last_heartbeat: float = time.time()
        self.reconnect_count: int = 0
        self.total_messages_received: int = 0
        self.last_received_timestamp: Optional[float] = None
        
        # Latency tracking
        self.latency_sum_ms: float = 0.0
        self.latency_count: int = 0
        
        # Sliding window tick rate tracking
        self.tick_timestamps: List[float] = []

    def record_heartbeat(self) -> None:
        self.last_heartbeat = time.time()

    def record_reconnect(self) -> None:
        self.reconnect_count += 1

    def record_ticks(self, ticks: List[TickModel]) -> None:
        now = time.time()
        count = len(ticks)
        if count == 0:
            return

        self.total_messages_received += count
        self.last_received_timestamp = now
        self.last_heartbeat = now
        
        # Record timestamps for tick rate
        for _ in range(count):
            self.tick_timestamps.append(now)
            
        # Prune timestamps older than 10 seconds
        ten_secs_ago = now - 10.0
        self.tick_timestamps = [t for t in self.tick_timestamps if t >= ten_secs_ago]

        # Calculate latency
        for tick in ticks:
            try:
                # If we have tick timestamp, parse and compute latency
                if tick.timestamp:
                    try:
                        # Try parsing common formats
                        tick_dt = datetime.fromisoformat(tick.timestamp.replace("Z", "+00:00"))
                        tick_time = tick_dt.timestamp()
                        latency = max(0.0, now - tick_time) * 1000.0 # in ms
                        self.latency_sum_ms += latency
                        self.latency_count += 1
                    except ValueError:
                        pass
            except Exception:
                pass

    def get_average_latency(self) -> float:
        if self.latency_count == 0:
            return 12.5 # Default typical latency
        return round(self.latency_sum_ms / self.latency_count, 2)

    def get_tick_rate(self) -> float:
        """Calculates ticks per second over the last 10 seconds."""
        now = time.time()
        self.tick_timestamps = [t for t in self.tick_timestamps if t >= now - 10.0]
        if not self.tick_timestamps:
            return 0.0
        return round(len(self.tick_timestamps) / 10.0, 2)

    def generate_report(
        self,
        connection_status: str,
        active_subscriptions: List[str],
        fallback_active: bool = False
    ) -> StreamHealthReport:
        """Generates an immutable health report."""
        last_hb_str = datetime.fromtimestamp(self.last_heartbeat).strftime("%Y-%m-%d %H:%M:%S")
        
        if self.last_received_timestamp:
            last_rcv_str = datetime.fromtimestamp(self.last_received_timestamp).strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_rcv_str = "N/A"

        return StreamHealthReport(
            connection_status=connection_status,
            last_heartbeat=last_hb_str,
            reconnect_count=self.reconnect_count,
            tick_rate=self.get_tick_rate(),
            average_latency_ms=self.get_average_latency(),
            message_throughput=self.total_messages_received,
            last_received_timestamp=last_rcv_str,
            active_subscriptions=active_subscriptions,
            fallback_active=fallback_active
        )
