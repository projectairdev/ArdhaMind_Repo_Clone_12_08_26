from __future__ import annotations
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from kiteconnect import KiteTicker

logger = logging.getLogger("KiteTickerAdapter")


class KiteTickerAdapter:
    """
    WebSocket adapter implementing the KiteTicker connection lifecycle
    for real-time market streaming.
    """

    def __init__(self, api_key: str, access_token: str) -> None:
        self.api_key = api_key
        self.access_token = access_token
        self.ticker: Optional[KiteTicker] = None
        self._connected = False
        
        # Diagnostics
        self.last_heartbeat: float = 0.0
        self.reconnect_count: int = 0
        self.last_received_timestamp: float = 0.0
        self.last_error: Optional[str] = None
        
        # Callbacks
        self.on_tick_received: Optional[Callable[[List[Dict[str, Any]]], None]] = None
        self.on_status_changed: Optional[Callable[[str], None]] = None

    def connect(self) -> bool:
        """
        Initializes and starts the KiteTicker connection.
        """
        if not self.api_key or not self.access_token:
            self.last_error = "Missing credentials for streaming"
            logger.error(self.last_error)
            return False

        try:
            logger.info("Initializing KiteTicker client...")
            self.ticker = KiteTicker(
                api_key=self.api_key,
                access_token=self.access_token,
                reconnect=True,
                reconnect_max_delay=10,
                reconnect_max_tries=5
            )

            # Bind KiteTicker events
            self.ticker.on_ticks = self._on_kite_ticks
            self.ticker.on_connect = self._on_kite_connect
            self.ticker.on_close = self._on_kite_close
            self.ticker.on_error = self._on_kite_error
            self.ticker.on_reconnect = self._on_kite_reconnect
            self.ticker.on_noreconnect = self._on_kite_noreconnect

            # Establish connection in a non-blocking threaded mode
            self.ticker.connect(threaded=True)
            self._connected = True
            self.last_heartbeat = time.time()
            if self.on_status_changed:
                self.on_status_changed("CONNECTED")
            return True
        except Exception as e:
            self.last_error = str(e)
            self._connected = False
            logger.error(f"Failed to connect KiteTicker: {e}")
            if self.on_status_changed:
                self.on_status_changed("DISCONNECTED")
            return False

    def disconnect(self) -> None:
        """
        Gracefully closes the active KiteTicker connection.
        """
        if self.ticker:
            try:
                logger.info("Closing KiteTicker client...")
                self.ticker.close()
            except Exception as e:
                logger.error(f"Error closing KiteTicker: {e}")
        self._connected = False
        if self.on_status_changed:
            self.on_status_changed("DISCONNECTED")

    def is_connected(self) -> bool:
        """
        Returns connection state.
        """
        if self.ticker:
            return self.ticker.is_connected() and self._connected
        return self._connected

    def subscribe(self, tokens: List[int]) -> bool:
        """
        Subscribes to a list of instrument tokens.
        """
        if not self.is_connected() or not self.ticker:
            logger.warning("KiteTicker is not connected. Cannot subscribe.")
            return False
        try:
            logger.info(f"Subscribing to instrument tokens: {tokens}")
            self.ticker.subscribe(tokens)
            self.ticker.set_mode(self.ticker.MODE_FULL, tokens)
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")
            return False

    def unsubscribe(self, tokens: List[int]) -> bool:
        """
        Unsubscribes from a list of instrument tokens.
        """
        if not self.is_connected() or not self.ticker:
            logger.warning("KiteTicker is not connected. Cannot unsubscribe.")
            return False
        try:
            logger.info(f"Unsubscribing from instrument tokens: {tokens}")
            self.ticker.unsubscribe(tokens)
            return True
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {e}")
            return False

    def trigger_heartbeat(self) -> None:
        """
        Manual heartbeat indicator for keeping the connection diagnostics updated.
        """
        self.last_heartbeat = time.time()

    # --- KiteTicker Callback Mappings ---

    def _on_kite_ticks(self, ws, ticks: List[Dict[str, Any]]) -> None:
        self.last_received_timestamp = time.time()
        self.last_heartbeat = time.time()
        logger.debug(f"Received ticks: {len(ticks)} packets")
        if self.on_tick_received:
            self.on_tick_received(ticks)

    def _on_kite_connect(self, ws, response) -> None:
        self._connected = True
        self.last_heartbeat = time.time()
        logger.info("KiteTicker connected successfully.")
        if self.on_status_changed:
            self.on_status_changed("CONNECTED")

    def _on_kite_close(self, ws, code, reason) -> None:
        self._connected = False
        logger.warning(f"KiteTicker connection closed. Code: {code}, Reason: {reason}")
        if self.on_status_changed:
            self.on_status_changed("DISCONNECTED")

    def _on_kite_error(self, ws, code, reason) -> None:
        self.last_error = f"Error {code}: {reason}"
        logger.error(f"KiteTicker error: {self.last_error}")

    def _on_kite_reconnect(self, ws, attempts_count) -> None:
        self.reconnect_count = attempts_count
        logger.info(f"KiteTicker reconnecting. Attempt: {attempts_count}")
        if self.on_status_changed:
            self.on_status_changed("RECONNECTING")

    def _on_kite_noreconnect(self, ws) -> None:
        self._connected = False
        logger.error("KiteTicker reconnect attempts exhausted.")
        if self.on_status_changed:
            self.on_status_changed("DISCONNECTED")
