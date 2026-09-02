from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import threading
from typing import Any, Deque, Dict, List, Optional

from src.market_data.bus.events import MarketEvent, MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.models.canonical_tick import CanonicalTick


class FeedHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DELAYED = "DELAYED"
    STALE = "STALE"
    DISCONNECTED = "DISCONNECTED"
    RECOVERING = "RECOVERING"


@dataclass(frozen=True)
class FeedHealthReport:
    """
    Immutable health telemetry snapshot for an instrument feed.
    """
    canonical_instrument_id: str
    status: FeedHealthStatus
    socket_connected: bool
    last_tick_at: Optional[datetime]
    last_received_at: Optional[datetime]
    tick_age_ms: float
    provider_latency_ms: Optional[float]
    ticks_per_second: float
    update_count: int
    delayed_count: int
    stale_count: int
    recovery_count: int
    evaluated_at: datetime


class FeedHealthEngine:
    """
    Evaluates real-time feed liveness and latency independently from raw socket transport.
    Calculates dynamic tick age, requires sustained fresh tick confirmation for recovery,
    and publishes health transition events.
    """

    DEFAULT_HEALTHY_THRESHOLD_SEC: float = 3.0
    DEFAULT_DELAYED_THRESHOLD_SEC: float = 7.0
    DEFAULT_RECOVERY_CONFIRMATION_TICKS: int = 3

    def __init__(
        self,
        healthy_threshold_seconds: float = DEFAULT_HEALTHY_THRESHOLD_SEC,
        delayed_threshold_seconds: float = DEFAULT_DELAYED_THRESHOLD_SEC,
        recovery_confirmation_ticks: int = DEFAULT_RECOVERY_CONFIRMATION_TICKS,
    ) -> None:
        if healthy_threshold_seconds <= 0 or delayed_threshold_seconds <= healthy_threshold_seconds:
            raise ValueError("Thresholds must be positive with delayed_threshold > healthy_threshold.")
        if recovery_confirmation_ticks < 1:
            raise ValueError("recovery_confirmation_ticks must be at least 1.")

        self.healthy_threshold_seconds = healthy_threshold_seconds
        self.delayed_threshold_seconds = delayed_threshold_seconds
        self.recovery_confirmation_ticks = recovery_confirmation_ticks

        self._lock = threading.RLock()
        self._event_bus: Optional[MarketEventBus] = None
        self._subscription_id: Optional[str] = None
        self._socket_connected: bool = False

        # Per-instrument tracking metrics
        self._last_tick_at: Dict[str, datetime] = {}
        self._last_received_at: Dict[str, datetime] = {}
        self._provider_latency_ms: Dict[str, float] = {}
        self._update_counts: Dict[str, int] = {}
        self._delayed_counts: Dict[str, int] = {}
        self._stale_counts: Dict[str, int] = {}
        self._recovery_counts: Dict[str, int] = {}
        self._last_status: Dict[str, FeedHealthStatus] = {}

        # Consecutive fresh ticks tracking for recovery confirmation
        self._consecutive_fresh_ticks: Dict[str, int] = {}

        # Recent tick timestamps for throughput rate estimation (last 50 per instrument)
        self._recent_tick_times: Dict[str, Deque[float]] = {}

    def attach(self, event_bus: MarketEventBus) -> None:
        """Attaches to MarketEventBus to observe incoming ticks and publish health changes."""
        with self._lock:
            if self._event_bus is event_bus and self._subscription_id is not None:
                return
            if self._event_bus is not None and self._subscription_id is not None:
                self.detach()

            self._event_bus = event_bus
            self._subscription_id = event_bus.subscribe(
                MarketEventType.TICK,
                self._handle_tick_event,
            )

    def detach(self) -> None:
        """Detaches from MarketEventBus."""
        with self._lock:
            if self._event_bus and self._subscription_id:
                self._event_bus.unsubscribe(self._subscription_id)
            self._event_bus = None
            self._subscription_id = None

    def on_socket_connected(self) -> None:
        """Records socket connection established. Publishes FEED_CONNECTED."""
        with self._lock:
            self._socket_connected = True
            if self._event_bus and self._event_bus.is_running and self._event_bus.has_subscribers(MarketEventType.FEED_CONNECTED):
                self._event_bus.publish(
                    MarketEventType.FEED_CONNECTED,
                    {"status": FeedHealthStatus.HEALTHY.value, "socket_connected": True},
                )

    def on_socket_disconnected(self) -> None:
        """Records socket disconnected. Updates states to DISCONNECTED and publishes FEED_DISCONNECTED."""
        with self._lock:
            self._socket_connected = False
            for cid in list(self._last_status.keys()):
                self._last_status[cid] = FeedHealthStatus.DISCONNECTED
                self._consecutive_fresh_ticks[cid] = 0
            if self._event_bus and self._event_bus.is_running and self._event_bus.has_subscribers(MarketEventType.FEED_DISCONNECTED):
                self._event_bus.publish(
                    MarketEventType.FEED_DISCONNECTED,
                    {"status": FeedHealthStatus.DISCONNECTED.value, "socket_connected": False},
                )

    def on_tick(self, tick: CanonicalTick) -> None:
        """Ingests a validated CanonicalTick and evaluates recovery state."""
        if not isinstance(tick, CanonicalTick):
            return

        cid = tick.canonical_instrument_id
        now_dt = datetime.now(timezone.utc)
        now_sec = now_dt.timestamp()

        with self._lock:
            self._socket_connected = True
            is_initial = cid not in self._last_status
            prev_status = self._last_status.get(cid)

            self._last_tick_at[cid] = tick.exchange_timestamp
            self._last_received_at[cid] = tick.received_at

            latency_ms = (tick.received_at - tick.exchange_timestamp).total_seconds() * 1000.0
            self._provider_latency_ms[cid] = max(0.0, latency_ms)
            self._update_counts[cid] = self._update_counts.get(cid, 0) + 1

            times = self._recent_tick_times.setdefault(cid, deque(maxlen=50))
            times.append(now_sec)

            # Recovery confirmation state machine:
            if is_initial:
                # Cold start: first observed tick directly establishes healthy state
                self._last_status[cid] = FeedHealthStatus.HEALTHY
                self._consecutive_fresh_ticks[cid] = 1
            elif prev_status in (FeedHealthStatus.DELAYED, FeedHealthStatus.STALE, FeedHealthStatus.DISCONNECTED):
                # First fresh tick after degradation: enter RECOVERING
                self._consecutive_fresh_ticks[cid] = 1
                if self.recovery_confirmation_ticks == 1:
                    self._last_status[cid] = FeedHealthStatus.HEALTHY
                    self._recovery_counts[cid] = self._recovery_counts.get(cid, 0) + 1
                    self._publish_health_event(MarketEventType.FEED_RECOVERED, {"instrument": cid, "status": FeedHealthStatus.HEALTHY.value}, cid)
                else:
                    self._last_status[cid] = FeedHealthStatus.RECOVERING
                    self._publish_health_event(MarketEventType.FEED_RECOVERING, {"instrument": cid, "status": FeedHealthStatus.RECOVERING.value, "consecutive_ticks": 1}, cid)
            elif prev_status == FeedHealthStatus.RECOVERING:
                current_consecutive = self._consecutive_fresh_ticks.get(cid, 0) + 1
                self._consecutive_fresh_ticks[cid] = current_consecutive

                if current_consecutive >= self.recovery_confirmation_ticks:
                    self._last_status[cid] = FeedHealthStatus.HEALTHY
                    self._recovery_counts[cid] = self._recovery_counts.get(cid, 0) + 1
                    self._publish_health_event(MarketEventType.FEED_RECOVERED, {"instrument": cid, "status": FeedHealthStatus.HEALTHY.value}, cid)
            else:
                self._last_status[cid] = FeedHealthStatus.HEALTHY
                self._consecutive_fresh_ticks[cid] = self._consecutive_fresh_ticks.get(cid, 0) + 1

    def _publish_health_event(self, event_type: MarketEventType, payload: Any, cid: Optional[str] = None) -> None:
        if self._event_bus and self._event_bus.is_running and self._event_bus.has_subscribers(event_type):
            self._event_bus.publish(event_type, payload, canonical_instrument_id=cid)

    def _handle_tick_event(self, event: MarketEvent) -> None:
        if isinstance(event.payload, CanonicalTick):
            self.on_tick(event.payload)

    def evaluate_health(
        self,
        canonical_instrument_id: str,
        current_time: Optional[datetime] = None,
    ) -> FeedHealthReport:
        """
        Dynamically evaluates health status for the specified instrument against current_time.
        Emits transition events to the EventBus when status degrades or recovers.
        """
        eval_time = current_time or datetime.now(timezone.utc)
        if eval_time.tzinfo is None:
            eval_time = eval_time.replace(tzinfo=timezone.utc)

        with self._lock:
            cid = canonical_instrument_id.strip()
            last_rcv = self._last_received_at.get(cid)
            last_tick = self._last_tick_at.get(cid)
            prev_status = self._last_status.get(cid, FeedHealthStatus.DISCONNECTED if not self._socket_connected else FeedHealthStatus.STALE)

            if last_rcv is not None:
                tick_age_ms = max(0.0, (eval_time - last_rcv).total_seconds() * 1000.0)
            else:
                tick_age_ms = float("inf")

            # Determine Target Status
            if not self._socket_connected:
                new_status = FeedHealthStatus.DISCONNECTED
            elif tick_age_ms <= (self.healthy_threshold_seconds * 1000.0):
                # If currently recovering and hasn't satisfied sustained ticks, preserve RECOVERING
                if prev_status == FeedHealthStatus.RECOVERING:
                    new_status = FeedHealthStatus.RECOVERING
                else:
                    new_status = FeedHealthStatus.HEALTHY
            elif tick_age_ms <= (self.delayed_threshold_seconds * 1000.0):
                new_status = FeedHealthStatus.DELAYED
                self._consecutive_fresh_ticks[cid] = 0
            else:
                new_status = FeedHealthStatus.STALE
                self._consecutive_fresh_ticks[cid] = 0

            # Track transitions and publish events
            if new_status != prev_status:
                self._last_status[cid] = new_status
                if new_status == FeedHealthStatus.DELAYED:
                    self._delayed_counts[cid] = self._delayed_counts.get(cid, 0) + 1
                    self._publish_health_event(MarketEventType.FEED_DELAYED, {"instrument": cid, "tick_age_ms": tick_age_ms}, cid)
                elif new_status == FeedHealthStatus.STALE:
                    self._stale_counts[cid] = self._stale_counts.get(cid, 0) + 1
                    self._publish_health_event(MarketEventType.FEED_STALE, {"instrument": cid, "tick_age_ms": tick_age_ms}, cid)

            times = self._recent_tick_times.get(cid, deque())
            eval_sec = eval_time.timestamp()
            recent_in_window = [t for t in times if eval_sec - t <= 2.0]
            tps = len(recent_in_window) / 2.0 if recent_in_window else 0.0

            return FeedHealthReport(
                canonical_instrument_id=cid,
                status=new_status,
                socket_connected=self._socket_connected,
                last_tick_at=last_tick,
                last_received_at=last_rcv,
                tick_age_ms=round(tick_age_ms, 2),
                provider_latency_ms=round(self._provider_latency_ms.get(cid, 0.0), 2) if cid in self._provider_latency_ms else None,
                ticks_per_second=round(tps, 2),
                update_count=self._update_counts.get(cid, 0),
                delayed_count=self._delayed_counts.get(cid, 0),
                stale_count=self._stale_counts.get(cid, 0),
                recovery_count=self._recovery_counts.get(cid, 0),
                evaluated_at=eval_time,
            )

    def get_health_report(
        self,
        canonical_instrument_id: str,
        current_time: Optional[datetime] = None,
    ) -> FeedHealthReport:
        """Returns the evaluated FeedHealthReport for a single instrument."""
        return self.evaluate_health(canonical_instrument_id, current_time=current_time)

    def list_health_reports(
        self,
        current_time: Optional[datetime] = None,
    ) -> Dict[str, FeedHealthReport]:
        """Returns evaluated FeedHealthReports for all tracked instruments."""
        with self._lock:
            cids = list(self._last_received_at.keys())

        return {cid: self.evaluate_health(cid, current_time=current_time) for cid in cids}

    def stats(self) -> Dict[str, Any]:
        """Returns diagnostic telemetry summary."""
        with self._lock:
            return {
                "socket_connected": self._socket_connected,
                "tracked_instruments_count": len(self._last_received_at),
                "healthy_threshold_seconds": self.healthy_threshold_seconds,
                "delayed_threshold_seconds": self.delayed_threshold_seconds,
                "recovery_confirmation_ticks": self.recovery_confirmation_ticks,
                "total_updates": sum(self._update_counts.values()),
                "total_delayed_events": sum(self._delayed_counts.values()),
                "total_stale_events": sum(self._stale_counts.values()),
                "total_recoveries": sum(self._recovery_counts.values()),
                "attached_to_event_bus": self._event_bus is not None,
            }
