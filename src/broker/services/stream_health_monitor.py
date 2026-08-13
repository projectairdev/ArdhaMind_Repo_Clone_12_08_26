from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from src.broker.models.stream_health import StreamHealthReport
from src.broker.models.tick import TickModel
from src.configuration_engine.runtime import Config


class StreamHealthMonitor:
    """
    Tracks streaming health metrics and produces immutable StreamHealthReports.
    Distinguishes process heartbeat != socket heartbeat != source observation heartbeat != price change.
    """

    def __init__(self) -> None:
        self.last_heartbeat: float = time.time()
        self.reconnect_count: int = 0
        self.total_messages_received: int = 0
        self.last_received_timestamp: Optional[float] = None
        self.last_source_observation_at: Optional[float] = None
        self.stale_since_timestamp: Optional[float] = None
        self.auth_required_reason: Optional[str] = None
        self.reconnect_state: Optional[str] = None
        
        # Latency tracking
        self.latency_sum_ms: float = 0.0
        self.latency_count: int = 0
        
        # Sliding window tick rate tracking
        self.tick_timestamps: List[float] = []

    def record_heartbeat(self) -> None:
        self.last_heartbeat = time.time()

    def record_reconnect(self) -> None:
        self.reconnect_count += 1

    def set_auth_required(self, reason: Optional[str]) -> None:
        self.auth_required_reason = reason

    def set_reconnect_state(self, state: Optional[str]) -> None:
        self.reconnect_state = state

    def record_source_observation(self, timestamp: Optional[float] = None) -> None:
        now = timestamp if timestamp is not None else time.time()
        self.last_source_observation_at = now
        self.last_heartbeat = now
        self.stale_since_timestamp = None

    def record_ticks(self, ticks: List[TickModel]) -> None:
        now = time.time()
        count = len(ticks)
        if count == 0:
            return

        self.total_messages_received += count
        self.last_received_timestamp = now
        self.record_source_observation(now)
        
        # Record timestamps for tick rate
        for _ in range(count):
            self.tick_timestamps.append(now)
            
        # Prune timestamps older than 10 seconds
        ten_secs_ago = now - 10.0
        self.tick_timestamps = [t for t in self.tick_timestamps if t >= ten_secs_ago]

        # Calculate latency
        for tick in ticks:
            try:
                if tick.timestamp:
                    try:
                        tick_dt = datetime.fromisoformat(tick.timestamp.replace("Z", "+00:00"))
                        tick_time = tick_dt.timestamp()
                        latency = max(0.0, now - tick_time) * 1000.0 # in ms
                        self.latency_sum_ms += latency
                        self.latency_count += 1
                    except ValueError:
                        pass
            except Exception:
                pass

    def check_feed_liveness(
        self,
        now: Optional[float] = None,
        market_status: str = "MARKET_OPEN",
        freshness_tolerance_seconds: Optional[float] = None,
        connection_status: str = "CONNECTED"
    ) -> Dict[str, Any]:
        curr = now if now is not None else time.time()
        tolerance = (
            freshness_tolerance_seconds
            if freshness_tolerance_seconds is not None
            else getattr(Config, "MARKET_DATA_FRESHNESS_TOLERANCE_SECONDS", 15.0)
        )

        if self.auth_required_reason:
            status = "AUTH_REQUIRED"
        elif connection_status in ("RECONNECTING", "RESUBSCRIBING"):
            status = connection_status
        elif connection_status == "DISCONNECTED":
            status = "STALE" if market_status == "MARKET_OPEN" else "OFFLINE"
        elif market_status == "MARKET_OPEN":
            if self.last_source_observation_at is None:
                status = "STALE"
            else:
                age = curr - self.last_source_observation_at
                if age > tolerance:
                    status = "STALE"
                    if self.stale_since_timestamp is None:
                        self.stale_since_timestamp = self.last_source_observation_at
                else:
                    status = "HEALTHY"
                    self.stale_since_timestamp = None
        else:
            status = "CLOSED" if market_status in ("CLOSED", "POST_CLOSE") else "HEALTHY"

        obs_age = round(curr - self.last_source_observation_at, 3) if self.last_source_observation_at else 999.0
        stale_dur = round(curr - self.stale_since_timestamp, 3) if self.stale_since_timestamp else 0.0

        return {
            "status": status,
            "observation_age_seconds": obs_age,
            "stale_duration_seconds": stale_dur,
            "last_source_observation_at": self.last_source_observation_at,
            "stale_since_timestamp": self.stale_since_timestamp,
            "auth_required_reason": self.auth_required_reason,
            "reconnect_state": self.reconnect_state
        }

    def get_feed_bootstrap_state(
        self,
        is_connected: bool,
        is_stream_connected: bool,
        active_sub_count: int,
        has_nifty_tick: bool,
        obs_age: float
    ) -> str:
        if self.auth_required_reason:
            return "AUTH_REQUIRED"
        if not is_connected or not is_stream_connected:
            return "DISCONNECTED"
        if active_sub_count == 0:
            return "SUBSCRIBING"
        if not has_nifty_tick:
            return "WAITING_FOR_TICKS"
        if obs_age <= 15.0:
            return "LIVE"
        if obs_age <= 30.0:
            return "SYNCHRONIZING"
        return "STALE"

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
        fallback_active: bool = False,
        market_status: str = "MARKET_OPEN",
        freshness_tolerance_seconds: Optional[float] = None
    ) -> StreamHealthReport:
        """Generates an immutable health report."""
        last_hb_str = datetime.fromtimestamp(self.last_heartbeat, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        if self.last_received_timestamp:
            last_rcv_str = datetime.fromtimestamp(self.last_received_timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_rcv_str = "N/A"

        if self.last_source_observation_at:
            last_obs_str = datetime.fromtimestamp(self.last_source_observation_at, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_obs_str = "N/A"

        if self.stale_since_timestamp:
            stale_str = datetime.fromtimestamp(self.stale_since_timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        else:
            stale_str = None

        liveness = self.check_feed_liveness(
            market_status=market_status,
            freshness_tolerance_seconds=freshness_tolerance_seconds,
            connection_status=connection_status
        )

        return StreamHealthReport(
            connection_status=connection_status,
            last_heartbeat=last_hb_str,
            reconnect_count=self.reconnect_count,
            tick_rate=self.get_tick_rate(),
            average_latency_ms=self.get_average_latency(),
            message_throughput=self.total_messages_received,
            last_received_timestamp=last_rcv_str,
            active_subscriptions=active_subscriptions,
            fallback_active=fallback_active,
            feed_liveness_status=liveness["status"],
            observation_age_seconds=liveness["observation_age_seconds"],
            last_source_observation_at=last_obs_str,
            stale_since=stale_str,
            auth_required_reason=self.auth_required_reason,
            reconnect_state=self.reconnect_state
        )
