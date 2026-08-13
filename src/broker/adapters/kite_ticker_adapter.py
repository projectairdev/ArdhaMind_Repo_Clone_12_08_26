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
        
        # Diagnostics & Feed Liveness Tracking
        self.last_heartbeat: float = 0.0
        self.reconnect_count: int = 0
        self.last_received_timestamp: float = 0.0
        self.last_fresh_tick_at: Optional[float] = None
        self.last_error: Optional[str] = None
        self.auth_required: bool = False
        self.auth_required_reason: Optional[str] = None
        self.reconnect_state: str = "DISCONNECTED" # "DISCONNECTED", "RECONNECTING", "CONNECTED", "RESUBSCRIBING", "VERIFYING", "RECOVERED", "HEALTHY", "AUTH_REQUIRED"
        
        # Diagnostic Telemetry Ring Buffer (max 50 events)
        self.generation_id: int = 1
        self._telemetry_events: List[Dict[str, Any]] = []

        # Callbacks
        self.on_tick_received: Optional[Callable[[List[Dict[str, Any]]], None]] = None
        self.on_status_changed: Optional[Callable[[str], None]] = None

    def _record_telemetry(self, event_type: str, reason: Optional[str] = None, close_code: Optional[int] = None, initiator: str = "SYSTEM"):
        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        evt = {
            "timestamp": now_str,
            "event_type": event_type,
            "generation_id": self.generation_id,
            "reason": reason or "N/A",
            "close_code": close_code,
            "initiator": initiator,
            "reconnect_count": self.reconnect_count,
            "last_error": self.last_error
        }
        self._telemetry_events.append(evt)
        if len(self._telemetry_events) > 50:
            self._telemetry_events.pop(0)

    def get_telemetry_events(self) -> List[Dict[str, Any]]:
        return list(self._telemetry_events)

    def connect(self) -> bool:
        """
        Initializes and starts the KiteTicker connection.
        Safely detaches any existing internal KiteTicker callbacks first.
        """
        if not self.api_key or not self.access_token:
            self.last_error = "Missing credentials for streaming"
            self.auth_required = True
            self.auth_required_reason = self.last_error
            self.reconnect_state = "AUTH_REQUIRED"
            self._record_telemetry("AUTH_REPLACEMENT", reason=self.last_error)
            logger.error(self.last_error)
            if self.on_status_changed:
                self.on_status_changed("AUTH_REQUIRED")
            return False

        if self.ticker:
            try:
                logger.info("Detaching callbacks from existing KiteTicker client before new connect...")
                self.ticker.on_ticks = None
                self.ticker.on_connect = None
                self.ticker.on_close = None
                self.ticker.on_error = None
                self.ticker.on_reconnect = None
                self.ticker.on_noreconnect = None
                self.ticker.close()
            except Exception as ex:
                logger.warning("Warning closing old KiteTicker client: %s", ex)
            self.ticker = None
            self.generation_id += 1

        try:
            logger.info(f"Initializing KiteTicker client (Gen #{self.generation_id})...")
            self._record_telemetry("CONNECT_REQUESTED", reason="Stream startup")
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
            self.reconnect_state = "CONNECTED"
            self._record_telemetry("CONNECTED", reason="Transport initiated")
            if self.on_status_changed:
                self.on_status_changed("CONNECTED")
            return True
        except Exception as e:
            self.last_error = str(e)
            self._connected = False
            err_msg = str(e).lower()
            if any(term in err_msg for term in ("tokenexception", "userexception", "403", "invalid token", "token expired", "access_token")):
                self.auth_required = True
                self.auth_required_reason = str(e)
                self.reconnect_state = "AUTH_REQUIRED"
                self._record_telemetry("AUTH_REPLACEMENT", reason=str(e))
                logger.error(f"KiteTicker authentication failure: {e}")
                if self.on_status_changed:
                    self.on_status_changed("AUTH_REQUIRED")
            else:
                self.reconnect_state = "DISCONNECTED"
                self._record_telemetry("DISCONNECTED", reason=str(e))
                logger.error(f"Failed to connect KiteTicker (network/transport): {e}")
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
                self.ticker.on_ticks = None
                self.ticker.on_connect = None
                self.ticker.on_close = None
                self.ticker.on_error = None
                self.ticker.on_reconnect = None
                self.ticker.on_noreconnect = None
                self.ticker.close()
            except Exception as e:
                logger.error(f"Error closing KiteTicker: {e}")
            self.ticker = None
        self._connected = False
        self.reconnect_state = "DISCONNECTED"
        self._record_telemetry("SHUTDOWN", reason="Graceful disconnect")
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
            self.reconnect_state = "RESUBSCRIBING"
            self.ticker.subscribe(tokens)
            self.ticker.set_mode(self.ticker.MODE_FULL, tokens)
            self.reconnect_state = "VERIFYING"
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
        now = time.time()
        self.last_received_timestamp = now
        self.last_heartbeat = now
        self.last_fresh_tick_at = now
        logger.debug(f"Received ticks: {len(ticks)} packets")

        if self.reconnect_state in ("RESUBSCRIBING", "VERIFYING", "CONNECTED"):
            self.reconnect_state = "RECOVERED"
            if self.on_status_changed:
                self.on_status_changed("RECOVERED")
            self.reconnect_state = "HEALTHY"
            if self.on_status_changed:
                self.on_status_changed("HEALTHY")

        if self.on_tick_received:
            self.on_tick_received(ticks)

    def _on_kite_connect(self, ws, response) -> None:
        self._connected = True
        self.last_heartbeat = time.time()
        self.reconnect_state = "CONNECTED"
        logger.info("KiteTicker transport connected successfully.")
        if self.on_status_changed:
            self.on_status_changed("CONNECTED")

    def _on_kite_close(self, ws, code, reason) -> None:
        self._connected = False
        self.reconnect_state = "DISCONNECTED"
        logger.warning(f"KiteTicker connection closed. Code: {code}, Reason: {reason}")
        if self.on_status_changed:
            self.on_status_changed("DISCONNECTED")

    def _on_kite_error(self, ws, code, reason) -> None:
        self.last_error = f"Error {code}: {reason}"
        err_msg = str(reason).lower() if reason else ""
        if any(term in err_msg for term in ("tokenexception", "userexception", "403", "invalid token", "token expired", "access_token")):
            self.auth_required = True
            self.auth_required_reason = f"Error {code}: {reason}"
            self.reconnect_state = "AUTH_REQUIRED"
            logger.error(f"KiteTicker auth error: {self.last_error}")
            if self.on_status_changed:
                self.on_status_changed("AUTH_REQUIRED")
        else:
            logger.error(f"KiteTicker error: {self.last_error}")

    def _on_kite_reconnect(self, ws, attempts_count) -> None:
        self.reconnect_count = attempts_count
        self.reconnect_state = "RECONNECTING"
        logger.info(f"KiteTicker reconnecting. Attempt: {attempts_count}")
        if self.on_status_changed:
            self.on_status_changed("RECONNECTING")

    def _on_kite_noreconnect(self, ws) -> None:
        self._connected = False
        self.reconnect_state = "DISCONNECTED"
        logger.error("KiteTicker reconnect attempts exhausted.")
        if self.on_status_changed:
            self.on_status_changed("DISCONNECTED")
