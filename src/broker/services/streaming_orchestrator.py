from __future__ import annotations
import logging
import time
import threading
from typing import List, Dict, Any, Optional

from src.broker.adapters.kite_ticker_adapter import KiteTickerAdapter
from src.broker.services.streaming_service import StreamingService
from src.broker.services.subscription_manager import SubscriptionManager
from src.broker.services.stream_health_monitor import StreamHealthMonitor
from src.broker.models.stream_health import StreamHealthReport

logger = logging.getLogger("StreamingOrchestrator")


class StreamingOrchestrator:
    """
    Orchestrates the real-time market streaming layer, coordinating
    the KiteTicker WebSocket connection, SubscriptionManager,
    StreamHealthMonitor, and FallbackStrategy.
    """

    _instance: Optional[StreamingOrchestrator] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StreamingOrchestrator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, broker_gateway: Any = None) -> None:
        if getattr(self, "_initialized", False):
            return
        
        self.broker_gateway = broker_gateway
        self.adapter: Optional[KiteTickerAdapter] = None
        self.subscription_manager = SubscriptionManager()
        self.health_monitor = StreamHealthMonitor()
        
        # Connection parameters
        self.api_key: str = ""
        self.access_token: str = ""
        
        # Fallback & Reconnect states
        self.fallback_active = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.base_backoff_seconds = 1.0
        self._reconnect_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Active streaming cache (stores latest tick received per symbol)
        self.latest_ticks: Dict[str, Any] = {}

        self._initialized = True

    @classmethod
    def get_instance(cls, broker_gateway: Any = None) -> StreamingOrchestrator:
        return cls(broker_gateway)

    def configure(self, api_key: str, access_token: str) -> None:
        self.api_key = api_key
        self.access_token = access_token

    def connect_stream(self) -> bool:
        """
        Connects to the real-time WebSocket.
        """
        if self._running:
            logger.info("Streaming layer already running.")
            return True

        self._running = True
        self.fallback_active = False
        self.reconnect_attempts = 0

        # Build Adapter
        self.adapter = KiteTickerAdapter(self.api_key, self.access_token)
        self.adapter.on_tick_received = self._on_tick_received
        self.adapter.on_status_changed = self._on_status_changed
        self.subscription_manager.set_ticker_adapter(self.adapter)

        # Attempt to connect
        success = self.adapter.connect()
        if not success:
            logger.warning("Initial WebSocket connection failed. Activating HTTP fallback.")
            self._activate_fallback()
            self._start_reconnect_loop()
        return success

    def disconnect_stream(self) -> None:
        """
        Disconnects from the real-time WebSocket and shuts down.
        """
        self._running = False
        if self.adapter:
            self.adapter.disconnect()
        self.subscription_manager.clear()
        self.fallback_active = False

    def is_connected(self) -> bool:
        if self.adapter:
            return self.adapter.is_connected()
        return False

    def is_fallback_active(self) -> bool:
        return self.fallback_active

    def subscribe(self, symbols: List[str]) -> List[int]:
        """Subscribes dynamically to symbols."""
        return self.subscription_manager.subscribe(symbols)

    def unsubscribe(self, symbols: List[str]) -> List[int]:
        """Unsubscribes dynamically from symbols."""
        return self.subscription_manager.unsubscribe(symbols)

    def get_health_report(self) -> StreamHealthReport:
        status = "DISCONNECTED"
        if self.is_connected():
            status = "CONNECTED"
        elif self.fallback_active:
            status = "RECONNECTING" # Fallback mode acts as connecting

        active_subs = self.subscription_manager.get_active_subscriptions()
        return self.health_monitor.generate_report(
            connection_status=status,
            active_subscriptions=active_subs,
            fallback_active=self.fallback_active
        )

    def get_latest_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Returns the latest quote. If fallback is active or tick is missing,
        falls back to HTTP polling.
        """
        if self.fallback_active or symbol not in self.latest_ticks:
            # Fall back to HTTP gateway if possible
            if self.broker_gateway:
                try:
                    logger.debug(f"Streaming fallback: fetching HTTP quote for {symbol}")
                    res = self.broker_gateway.get_quote([symbol])
                    if res and symbol in res:
                        return res[symbol]
                except Exception as e:
                    logger.error(f"HTTP fallback quote fetch failed: {e}")
            return None

        return self.latest_ticks.get(symbol)

    # --- Callbacks & Internal Methods ---

    def _on_tick_received(self, raw_ticks: List[Dict[str, Any]]) -> None:
        """
        Ingests and routes ticks.
        """
        tick_models = StreamingService.ingest_ticks(raw_ticks)
        self.health_monitor.record_ticks(tick_models)

        # Map raw ticks by instrument token for easy depth retrieval
        raw_map = {r.get("instrument_token"): r for r in raw_ticks if r.get("instrument_token")}

        # Update in-memory cache
        for tick in tick_models:
            raw = raw_map.get(tick.instrument_token, {})
            depth = raw.get("depth", {})
            buy_depth = depth.get("buy") or []
            sell_depth = depth.get("sell") or []
            bid = float(buy_depth[0].get("price", 0.0)) if buy_depth else tick.last_price
            ask = float(sell_depth[0].get("price", 0.0)) if sell_depth else tick.last_price

            self.latest_ticks[tick.symbol] = {
                "instrument_token": tick.instrument_token,
                "last_price": tick.last_price,
                "volume": tick.volume,
                "oi": tick.oi,
                "ohlc": {
                    "open": tick.open,
                    "high": tick.high,
                    "low": tick.low,
                    "close": tick.close
                },
                "timestamp": tick.timestamp,
                "bid": bid,
                "ask": ask
            }


    def _on_status_changed(self, status: str) -> None:
        logger.info(f"Stream Status changed: {status}")
        if status == "CONNECTED":
            self.fallback_active = False
            self.reconnect_attempts = 0
            # Resubscribe to previous active subscriptions
            active_subs = self.subscription_manager.get_active_subscriptions()
            if active_subs:
                # Direct subscribe to tokens again
                tokens = self.subscription_manager.get_active_tokens()
                if self.adapter:
                    self.adapter.subscribe(tokens)
        elif status == "DISCONNECTED" and self._running:
            self._activate_fallback()
            self._start_reconnect_loop()

    def _activate_fallback(self) -> None:
        self.fallback_active = True
        logger.info("HTTP Polling fallback activated.")

    def _start_reconnect_loop(self) -> None:
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
        self._reconnect_thread = threading.Thread(target=self._run_reconnect_loop, daemon=True)
        self._reconnect_thread.start()

    def _run_reconnect_loop(self) -> None:
        while self._running and self.fallback_active:
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.error("Max reconnection attempts exhausted. Streaming remaining in fallback.")
                break

            self.reconnect_attempts += 1
            self.health_monitor.record_reconnect()
            
            # Exponential Backoff calculation (capped at 16 seconds for testing responsiveness)
            sleep_time = min(16.0, self.base_backoff_seconds * (2 ** (self.reconnect_attempts - 1)))
            logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} in {sleep_time}s...")
            time.sleep(sleep_time)

            if not self._running:
                break

            logger.info("Retrying WebSocket connection...")
            if self.adapter and self.adapter.connect():
                logger.info("Reconnection successful!")
                self.fallback_active = False
                break
