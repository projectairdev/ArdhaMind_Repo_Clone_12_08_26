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
        self._reconnect_lock = threading.Lock()
        self._connect_lock = threading.Lock()
        self._running = False

        # Active streaming cache (stores latest tick received per symbol)
        self.latest_ticks: Dict[str, Any] = {}
        self._last_tick_timestamps: Dict[int, float] = {}

        # Telemetry & Diagnostics Counters
        self.ticks_received: int = 0
        self.ticks_processed: int = 0
        self.duplicates_rejected: int = 0
        self.out_of_order_rejected: int = 0
        self.stale_response_rejected: int = 0
        self.last_atm_strike: Optional[int] = None

        # Stream Telemetry
        self.connection_started_at: Optional[float] = None
        self.last_subscription_time: Optional[float] = None

        self._initialized = True

    @classmethod
    def get_instance(cls, broker_gateway: Any = None) -> StreamingOrchestrator:
        return cls(broker_gateway)

    def configure(self, api_key: str, access_token: str) -> None:
        self.api_key = api_key
        self.access_token = access_token

    def connect_stream(self, force_reconnect: bool = False) -> bool:
        """
        Connects to the real-time WebSocket.
        If credentials have changed or force_reconnect is True, safely terminates any existing adapter
        before establishing the new connection.
        """
        with self._connect_lock:
            credentials_changed = (
                self.adapter is not None and
                (getattr(self.adapter, "api_key", None) != self.api_key or getattr(self.adapter, "access_token", None) != self.access_token)
            )

            if self._running and not credentials_changed and not force_reconnect and self.is_connected():
                logger.info("Streaming layer already running with active valid adapter.")
                return True

            # Safely terminate existing adapter if replacing
            if self.adapter:
                logger.info("Safely terminating existing KiteTickerAdapter before establishing new stream connection...")
                old_adapter = self.adapter
                old_adapter.on_status_changed = None
                old_adapter.on_tick_received = None
                try:
                    old_adapter.disconnect()
                except Exception as e:
                    logger.error("Error disconnecting old adapter: %s", e)
                self.adapter = None

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
            if success:
                self.connection_started_at = time.time()
            else:
                if getattr(self.adapter, "auth_required", False):
                    self.health_monitor.set_auth_required(getattr(self.adapter, "auth_required_reason", "Missing/Invalid credentials"))
                    logger.error("Authentication required for Kite stream. Disabling auto reconnect.")
                else:
                    logger.warning("Initial WebSocket connection failed. Activating HTTP fallback.")
                    self._activate_fallback()
                    self._start_reconnect_loop()
            return success

    def disconnect_stream(self) -> None:
        """
        Disconnects from the real-time WebSocket and shuts down.
        """
        self._running = False
        self.connection_started_at = None
        if self.adapter:
            self.adapter.on_status_changed = None
            self.adapter.on_tick_received = None
            try:
                self.adapter.disconnect()
            except Exception as e:
                logger.error("Error disconnecting adapter: %s", e)
            self.adapter = None
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
        if symbols:
            self.last_subscription_time = time.time()
        return self.subscription_manager.subscribe(symbols)

    def unsubscribe(self, symbols: List[str]) -> List[int]:
        """Unsubscribes dynamically from symbols."""
        return self.subscription_manager.unsubscribe(symbols)

    def get_bootstrap_telemetry(self, market_status: str = "MARKET_OPEN") -> Dict[str, Any]:
        is_conn = self.is_connected()
        active_subs = self.subscription_manager.get_active_subscriptions()
        active_sub_count = len(active_subs)
        nifty_tick = self.latest_ticks.get("NSE:NIFTY 50") or self.latest_ticks.get("NIFTY 50")
        has_nifty = nifty_tick is not None and float(nifty_tick.get("last_price", 0.0)) > 0
        liveness = self.check_feed_liveness(market_status=market_status)
        obs_age = float(liveness["observation_age_seconds"]) if liveness.get("observation_age_seconds") is not None else None

        bootstrap_state = self.health_monitor.get_feed_bootstrap_state(
            is_connected=True,  # Gateway authenticated
            is_stream_connected=is_conn,
            active_sub_count=active_sub_count,
            has_nifty_tick=has_nifty,
            obs_age=obs_age
        )

        now = time.time()
        uptime = round(now - self.connection_started_at, 1) if (self.connection_started_at and is_conn) else 0.0
        last_tick_time = self.health_monitor.last_received_timestamp
        last_nifty_time = nifty_tick.get("timestamp") if nifty_tick else None

        from datetime import datetime as dt_cls, timezone as tz_cls
        def _iso(ts: Optional[float]) -> Optional[str]:
            return dt_cls.fromtimestamp(ts, tz=tz_cls.utc).isoformat() if ts else None

        telemetry_events = self.adapter.get_telemetry_events() if self.adapter else []
        gen_id = self.adapter.generation_id if self.adapter else 1

        return {
            "bootstrap_state": bootstrap_state,
            "stream_status": "CONNECTED" if is_conn else ("RECONNECTING" if self.fallback_active else "DISCONNECTED"),
            "connection_started_at": _iso(self.connection_started_at),
            "connection_uptime_seconds": uptime,
            "generation_id": gen_id,
            "reconnect_count": self.health_monitor.reconnect_count,
            "last_reconnect_time": self.health_monitor.reconnect_state,
            "subscribed_symbol_count": active_sub_count,
            "last_subscription_time": _iso(self.last_subscription_time),
            "last_valid_tick_time": _iso(last_tick_time),
            "last_valid_nifty_time": last_nifty_time,
            "tick_age_seconds": obs_age if (obs_age is not None and obs_age < 900) else None,
            "ticks_received": self.ticks_received,
            "ticks_processed": self.ticks_processed,
            "duplicates_rejected": self.duplicates_rejected,
            "out_of_order_rejected": self.out_of_order_rejected,
            "stale_response_rejected": self.stale_response_rejected,
            "connection_telemetry": telemetry_events
        }

    def check_feed_liveness(
        self,
        now: Optional[float] = None,
        market_status: str = "MARKET_OPEN",
        freshness_tolerance_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        conn_status = "DISCONNECTED"
        if self.is_connected():
            conn_status = "CONNECTED"
        elif self.fallback_active:
            conn_status = "RECONNECTING"

        return self.health_monitor.check_feed_liveness(
            now=now,
            market_status=market_status,
            freshness_tolerance_seconds=freshness_tolerance_seconds,
            connection_status=conn_status
        )

    def get_health_report(self, market_status: str = "MARKET_OPEN", freshness_tolerance_seconds: Optional[float] = None) -> StreamHealthReport:
        status = "DISCONNECTED"
        if self.is_connected():
            status = "CONNECTED"
        elif self.fallback_active:
            status = "RECONNECTING" # Fallback mode acts as connecting

        active_subs = self.subscription_manager.get_active_subscriptions()
        return self.health_monitor.generate_report(
            connection_status=status,
            active_subscriptions=active_subs,
            fallback_active=self.fallback_active,
            market_status=market_status,
            freshness_tolerance_seconds=freshness_tolerance_seconds
        )

    def get_latest_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Returns the latest quote. If fallback is active or tick is missing,
        falls back to HTTP polling.
        """
        if self.fallback_active or symbol not in self.latest_ticks:
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
        Ingests, validates, orders, and routes ticks.
        Guarantees:
        - Out-of-order rejection
        - Zero is not fallback (does not overwrite positive price with 0.0)
        - Latency tracking & counter increments
        """
        if not raw_ticks:
            return

        self.ticks_received += len(raw_ticks)
        tick_models = StreamingService.ingest_ticks(raw_ticks)
        self.health_monitor.record_ticks(tick_models)

        # Map raw ticks by instrument token for depth retrieval
        raw_map = {r.get("instrument_token"): r for r in raw_ticks if r.get("instrument_token")}

        # Update in-memory cache
        for tick in tick_models:
            token = tick.instrument_token
            # Timestamp ordering check
            try:
                from datetime import datetime as dt
                if isinstance(tick.timestamp, str):
                    ts_val = dt.fromisoformat(tick.timestamp.replace("Z", "+00:00")).timestamp()
                elif isinstance(tick.timestamp, (int, float)):
                    ts_val = float(tick.timestamp)
                else:
                    ts_val = time.time()
            except Exception:
                ts_val = time.time()

            last_ts = self._last_tick_timestamps.get(token)
            if last_ts is not None and ts_val < last_ts:
                self.out_of_order_rejected += 1
                logger.debug(f"Rejected out-of-order tick for token {token} ({ts_val} < {last_ts})")
                continue

            existing = self.latest_ticks.get(tick.symbol)
            # Duplicate check
            if existing and existing.get("last_price") == tick.last_price and existing.get("timestamp") == tick.timestamp and existing.get("volume") == tick.volume:
                self.duplicates_rejected += 1
                continue

            # Zero-value guard: 0.0 price must not erase an existing valid price
            final_price = tick.last_price
            if final_price <= 0.0 and existing and float(existing.get("last_price", 0.0)) > 0.0:
                final_price = existing["last_price"]

            self._last_tick_timestamps[token] = ts_val

            raw = raw_map.get(token, {})
            depth = raw.get("depth", {})
            buy_depth = depth.get("buy") or []
            sell_depth = depth.get("sell") or []
            bid = float(buy_depth[0].get("price", 0.0)) if buy_depth else final_price
            ask = float(sell_depth[0].get("price", 0.0)) if sell_depth else final_price

            tick_dict = {
                "instrument_token": token,
                "last_price": final_price,
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
            self.latest_ticks[tick.symbol] = tick_dict
            if tick.symbol == "NIFTY 50":
                self.latest_ticks["NSE:NIFTY 50"] = tick_dict
                self.latest_ticks["NIFTY"] = tick_dict
            elif tick.symbol == "INDIA VIX":
                self.latest_ticks["NSE:INDIA VIX"] = tick_dict

            self.ticks_processed += 1

            # Dynamic ATM subscription check when NIFTY moves
            if tick.symbol in ("NSE:NIFTY 50", "NIFTY 50", "NIFTY") and final_price > 0:
                current_atm = int(round(final_price / 50.0) * 50)
                if self.last_atm_strike is None or abs(current_atm - self.last_atm_strike) >= 50:
                    self.last_atm_strike = current_atm
                    self._adjust_option_subscriptions_around_atm(current_atm)

    def _adjust_option_subscriptions_around_atm(self, atm_strike: int) -> None:
        """
        Dynamically adjusts active option subscriptions around the new ATM strike (+- 3 strikes).
        Preserves active contracts without dropping ticks.
        """
        try:
            from src.broker.services.instrument_service import InstrumentService
            inst_service = InstrumentService.get_instance()
            # Subscribe to strikes [atm-150, atm-100, atm-50, atm, atm+50, atm+100, atm+150]
            strike_range = [atm_strike + (i * 50) for i in range(-3, 4)]
            new_symbols = []
            for st in strike_range:
                # Find matching CE and PE
                ce_inst = inst_service.get_option_contract("NIFTY", st, "CE")
                pe_inst = inst_service.get_option_contract("NIFTY", st, "PE")
                if ce_inst and ce_inst.get("tradingsymbol"):
                    new_symbols.append(ce_inst["tradingsymbol"])
                if pe_inst and pe_inst.get("tradingsymbol"):
                    new_symbols.append(pe_inst["tradingsymbol"])

            if new_symbols:
                self.subscribe(new_symbols)
        except Exception as e:
            logger.debug(f"ATM option subscription adjustment skipped/failed: {e}")

    def _on_status_changed(self, status: str) -> None:
        logger.info(f"Stream Status changed: {status}")
        self.health_monitor.set_reconnect_state(status)

        if status == "CONNECTED":
            self.fallback_active = False
            self.reconnect_attempts = 0
            # Resubscribe to previous active subscriptions
            active_subs = self.subscription_manager.get_active_subscriptions()
            if active_subs:
                tokens = self.subscription_manager.get_active_tokens()
                if self.adapter:
                    self.adapter.subscribe(tokens)
        elif status == "AUTH_REQUIRED":
            reason = getattr(self.adapter, "auth_required_reason", "Broker authentication required")
            self.health_monitor.set_auth_required(reason)
            self.fallback_active = False
            logger.error(f"Stream halted: {reason}")
        elif status == "DISCONNECTED" and self._running:
            market_closed = False
            try:
                from src.broker.services.market_status_service import MarketStatusService
                m_stat = MarketStatusService.get_instance().get_market_status()
                m_status_str = str(getattr(m_stat, "status", None) or (m_stat.get("status") if isinstance(m_stat, dict) else "closed")).lower()
                market_closed = m_status_str in ("closed", "holiday", "post_close", "weekend")
            except Exception:
                pass

            if market_closed:
                logger.info("Market is closed; WebSocket stream is idle. Reconnection suppressed.")
                self.fallback_active = False
            elif not self.health_monitor.auth_required_reason:
                self._activate_fallback()
                self._start_reconnect_loop()

    def _activate_fallback(self) -> None:
        self.fallback_active = True
        logger.info("HTTP Polling fallback activated.")

    def _start_reconnect_loop(self) -> None:
        with self._reconnect_lock:
            if self._reconnect_thread and self._reconnect_thread.is_alive():
                return
            self._reconnect_thread = threading.Thread(target=self._run_reconnect_loop, daemon=True)
            self._reconnect_thread.start()

    def _run_reconnect_loop(self) -> None:
        while self._running and self.fallback_active:
            if self.health_monitor.auth_required_reason:
                logger.error("Authentication required. Aborting reconnect loop.")
                break

            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.error("Max reconnection attempts exhausted. Streaming remaining in fallback.")
                break

            self.reconnect_attempts += 1
            self.health_monitor.record_reconnect()

            sleep_time = min(16.0, self.base_backoff_seconds * (2 ** (self.reconnect_attempts - 1)))
            logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} in {sleep_time}s...")
            time.sleep(sleep_time)

            if not self._running or self.health_monitor.auth_required_reason:
                break

            logger.info("Retrying WebSocket connection...")
            if self.adapter and self.adapter.connect():
                logger.info("Reconnection transport established.")
                self.fallback_active = False
                break
