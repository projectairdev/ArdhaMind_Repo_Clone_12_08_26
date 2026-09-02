from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from src.market_data.bus.events import (
    EventBusBackpressureError,
    EventBusStoppedError,
    MarketEvent,
    MarketEventType,
)

logger = logging.getLogger("MarketEventBus")

_STOP_SENTINEL = object()


@dataclass(frozen=True)
class Subscription:
    subscription_id: str
    event_type: MarketEventType
    callback: Callable[[MarketEvent], None]
    canonical_instrument_id: Optional[str] = None


class MarketEventBus:
    """
    High-throughput, bounded, thread-safe in-process event bus for Ardha market data.
    Guarantees deterministic FIFO delivery via a dedicated single dispatcher thread.
    Features subscriber failure isolation, slow subscriber detection, and strict backpressure.
    """

    DEFAULT_QUEUE_CAPACITY: int = 50_000
    DEFAULT_SLOW_CALLBACK_THRESHOLD_MS: float = 10.0

    def __init__(
        self,
        queue_capacity: int = DEFAULT_QUEUE_CAPACITY,
        slow_callback_threshold_ms: float = DEFAULT_SLOW_CALLBACK_THRESHOLD_MS,
    ) -> None:
        if queue_capacity <= 0:
            raise ValueError(f"queue_capacity must be a positive integer, got {queue_capacity}")

        self.queue_capacity = queue_capacity
        self.slow_callback_threshold_ms = slow_callback_threshold_ms

        self._lock = threading.RLock()
        self._queue: queue.Queue = queue.Queue(maxsize=self.queue_capacity)
        self._dispatcher_thread: Optional[threading.Thread] = None
        self._running = False
        self._stop_requested = threading.Event()
        self._drain_requested = False

        # Monotonic sequence owned by this bus instance
        self._sequence = 0

        # Subscriptions storage: subscription_id -> Subscription
        self._subscriptions: Dict[str, Subscription] = {}
        # Fast lookup: event_type -> set of subscription_ids
        self._type_index: Dict[MarketEventType, Set[str]] = {}

        # Observability & Metrics Counters
        self._published_total: int = 0
        self._dispatched_total: int = 0
        self._overflow_count: int = 0
        self._subscriber_call_count: int = 0
        self._subscriber_error_count: int = 0
        self._slow_subscriber_count: int = 0
        self._last_subscriber_error: Optional[str] = None
        self._last_event_at: Optional[str] = None
        self._last_dispatch_duration_ms: float = 0.0
        self._max_dispatch_duration_ms: float = 0.0

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running and self._dispatcher_thread is not None and self._dispatcher_thread.is_alive()

    def start(self) -> None:
        """Starts the dedicated dispatcher thread. Idempotent if already running."""
        with self._lock:
            if self._running and self._dispatcher_thread and self._dispatcher_thread.is_alive():
                return

            self._running = True
            self._stop_requested.clear()
            self._drain_requested = False

            self._dispatcher_thread = threading.Thread(
                target=self._run_dispatcher,
                name="market-event-bus-dispatcher",
                daemon=True,
            )
            self._dispatcher_thread.start()
            logger.info("MarketEventBus dispatcher started successfully.")

    def stop(self, drain: bool = True, timeout: float = 5.0) -> None:
        """
        Gracefully terminates the dispatcher thread.
        If drain=True (default), all currently enqueued events are processed before termination.
        If drain=False, the queue is abandoned immediately.
        """
        with self._lock:
            if not self._running:
                return

            self._running = False
            self._drain_requested = drain
            self._stop_requested.set()

            # Enqueue sentinel to unblock queue.get() immediately
            try:
                self._queue.put_nowait(_STOP_SENTINEL)
            except queue.Full:
                pass

        if self._dispatcher_thread and self._dispatcher_thread.is_alive():
            self._dispatcher_thread.join(timeout=timeout)
            if self._dispatcher_thread.is_alive():
                logger.warning("MarketEventBus dispatcher thread did not terminate within timeout.")
            else:
                logger.info("MarketEventBus dispatcher stopped cleanly.")

    def has_subscribers(self, event_type: MarketEventType | str) -> bool:
        """Returns True if there is at least one active subscriber for the given event type."""
        if not isinstance(event_type, MarketEventType):
            try:
                event_type = MarketEventType(event_type)
            except ValueError:
                return False
        with self._lock:
            s_set = self._type_index.get(event_type)
            return bool(s_set and len(s_set) > 0)

    def subscribe(
        self,
        event_type: MarketEventType | str,
        callback: Callable[[MarketEvent], None],
        canonical_instrument_id: Optional[str] = None,
    ) -> str:
        """
        Registers a callback subscription for a specific MarketEventType.
        Optionally filters by canonical_instrument_id.
        Returns an opaque subscription_id string.
        """
        if not callable(callback):
            raise TypeError("Subscriber callback must be callable.")

        if not isinstance(event_type, MarketEventType):
            try:
                event_type = MarketEventType(event_type)
            except ValueError:
                raise ValueError(f"Invalid MarketEventType '{event_type}'.")

        sub_id = f"SUB-{uuid4().hex[:12]}"
        filter_inst = canonical_instrument_id.strip() if canonical_instrument_id else None

        sub = Subscription(
            subscription_id=sub_id,
            event_type=event_type,
            callback=callback,
            canonical_instrument_id=filter_inst,
        )

        with self._lock:
            self._subscriptions[sub_id] = sub
            if event_type not in self._type_index:
                self._type_index[event_type] = set()
            self._type_index[event_type].add(sub_id)

        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unregisters a subscription by ID. Idempotent.
        Returns True if a subscription was removed, False if it was not found.
        """
        if not subscription_id:
            return False

        with self._lock:
            sub = self._subscriptions.pop(subscription_id, None)
            if sub:
                type_set = self._type_index.get(sub.event_type)
                if type_set and subscription_id in type_set:
                    type_set.remove(subscription_id)
                return True
            return False

    def publish(
        self,
        event_type: MarketEventType | str,
        payload: Any,
        canonical_instrument_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> MarketEvent:
        """
        Allocates a sequence number, constructs an immutable MarketEvent,
        and enqueues it for asynchronous dispatch.
        Raises EventBusStoppedError if the bus is not running.
        Raises EventBusBackpressureError if the queue is full.
        """
        with self._lock:
            if not self._running:
                raise EventBusStoppedError("Cannot publish event: MarketEventBus is stopped.")

            if not isinstance(event_type, MarketEventType):
                try:
                    event_type = MarketEventType(event_type)
                except ValueError:
                    raise ValueError(f"Invalid MarketEventType '{event_type}'.")

            # Backpressure guard: check queue space before consuming sequence
            if self._queue.full():
                self._overflow_count += 1
                raise EventBusBackpressureError(
                    f"EventBus queue capacity ({self.queue_capacity}) exceeded. Backpressure active."
                )

            # Atomically allocate sequence for accepted event
            self._sequence += 1
            seq = self._sequence

            now_utc = datetime.now(timezone.utc)
            event_id = f"EVT-{uuid4().hex}"

            event = MarketEvent(
                event_id=event_id,
                event_type=event_type,
                created_at=now_utc,
                sequence=seq,
                payload=payload,
                canonical_instrument_id=canonical_instrument_id.strip() if canonical_instrument_id else None,
                correlation_id=correlation_id.strip() if correlation_id else None,
            )

            self._queue.put_nowait(event)
            self._published_total += 1
            self._last_event_at = now_utc.isoformat().replace("+00:00", "Z")
            return event

    def stats(self) -> Dict[str, Any]:
        """Returns an immutable/copy-safe diagnostic telemetry snapshot."""
        with self._lock:
            dispatcher_alive = bool(
                self._dispatcher_thread and self._dispatcher_thread.is_alive()
            )
            return {
                "running": self._running,
                "dispatcher_alive": dispatcher_alive,
                "queue_depth": self._queue.qsize(),
                "queue_capacity": self.queue_capacity,
                "published_total": self._published_total,
                "dispatched_total": self._dispatched_total,
                "last_sequence": self._sequence,
                "overflow_count": self._overflow_count,
                "subscriber_count": len(self._subscriptions),
                "subscriber_call_count": self._subscriber_call_count,
                "subscriber_error_count": self._subscriber_error_count,
                "slow_subscriber_count": self._slow_subscriber_count,
                "last_subscriber_error": self._last_subscriber_error,
                "last_event_at": self._last_event_at,
                "last_dispatch_duration_ms": round(self._last_dispatch_duration_ms, 3),
                "max_dispatch_duration_ms": round(self._max_dispatch_duration_ms, 3),
                "slow_callback_threshold_ms": self.slow_callback_threshold_ms,
            }

    # --- Internal Dispatcher Loop ---

    def _run_dispatcher(self) -> None:
        """Single-threaded FIFO event delivery loop."""
        logger.debug("Dispatcher worker entered loop.")

        while True:
            try:
                # Block with small timeout to allow checking stop_requested periodically
                item = self._queue.get(timeout=0.05)
            except queue.Empty:
                if self._stop_requested.is_set() and (not self._drain_requested or self._queue.empty()):
                    break
                continue

            if item is _STOP_SENTINEL:
                if self._drain_requested and not self._queue.empty():
                    continue
                break

            event: MarketEvent = item
            self._dispatch_single_event(event)

        # If drain was requested, drain any remaining events in queue
        if self._drain_requested:
            while not self._queue.empty():
                try:
                    item = self._queue.get_nowait()
                    if item is not _STOP_SENTINEL:
                        self._dispatch_single_event(item)
                except queue.Empty:
                    break

        logger.debug("Dispatcher worker exited loop.")

    def _dispatch_single_event(self, event: MarketEvent) -> None:
        """Dispatches an event to all matching subscribers with failure isolation."""
        t_start = time.perf_counter()

        # Copy matching subscription snapshot under lock
        with self._lock:
            sub_ids = list(self._type_index.get(event.event_type, set()))
            matching_subs: List[Subscription] = []
            for sid in sub_ids:
                sub = self._subscriptions.get(sid)
                if sub:
                    # Filter by canonical_instrument_id if subscription has a filter
                    if sub.canonical_instrument_id is not None:
                        if event.canonical_instrument_id != sub.canonical_instrument_id:
                            continue
                    matching_subs.append(sub)

        # Execute callbacks outside lock
        for sub in matching_subs:
            cb_start = time.perf_counter()
            self._subscriber_call_count += 1
            try:
                sub.callback(event)
            except Exception as ex:
                self._subscriber_error_count += 1
                self._last_subscriber_error = f"Subscription {sub.subscription_id} error: {ex}"
                logger.error(
                    "Subscriber '%s' raised unhandled exception during event dispatch: %s",
                    sub.subscription_id,
                    ex,
                    exc_info=True,
                )

            cb_duration_ms = (time.perf_counter() - cb_start) * 1000.0
            if cb_duration_ms >= self.slow_callback_threshold_ms:
                self._slow_subscriber_count += 1
                logger.debug(
                    "Slow subscriber detected: %s took %.2f ms (threshold: %.2f ms)",
                    sub.subscription_id,
                    cb_duration_ms,
                    self.slow_callback_threshold_ms,
                )

        total_dispatch_ms = (time.perf_counter() - t_start) * 1000.0
        with self._lock:
            self._dispatched_total += 1
            self._last_dispatch_duration_ms = total_dispatch_ms
            if total_dispatch_ms > self._max_dispatch_duration_ms:
                self._max_dispatch_duration_ms = total_dispatch_ms
