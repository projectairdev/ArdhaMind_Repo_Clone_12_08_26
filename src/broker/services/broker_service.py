from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

from src.broker.interfaces.broker_interface import IBrokerGateway
from src.broker.models.trading_mode import TradingMode
from src.broker.adapters.kite_broker import KiteBrokerGateway
from src.configuration_engine.runtime import Config

logger = logging.getLogger("BrokerService")


class BrokerService(IBrokerGateway):
    """
    Unified entry point for the workstation's broker interactions.
    Acts as a singleton proxy that instantiates the correct broker gateway adapter
    based on the configured TRADING_MODE (PAPER_TRADING vs LIVE_ZERODHA).
    """

    _instance: Optional[BrokerService] = None
    _gateway: IBrokerGateway

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BrokerService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self.trading_mode = TradingMode.LIVE_ZERODHA

        self._init_gateway()
        self._initialized = True

    def _init_gateway(self) -> None:
        """Dynamically instantiates the adapter based on the active trading mode."""
        logger.info(f"Initializing BrokerService with mode: {self.trading_mode.value}")
        if self.trading_mode != TradingMode.LIVE_ZERODHA:
            raise ValueError("AIR ArdhaMind supports only the read-only Zerodha gateway")
        self._gateway = KiteBrokerGateway()

        class_name = "LiveKiteBroker"
        import sys
        print(f"BrokerService initialized:\nClass:\n{class_name}", file=sys.stderr, flush=True)

    @classmethod
    def get_instance(cls) -> BrokerService:
        """Utility method to retrieve or instantiate the singleton."""
        return cls()

    def set_mode(self, mode: TradingMode) -> None:
        """Retained compatibility method; non-canonical broker modes are rejected."""
        if mode != TradingMode.LIVE_ZERODHA:
            raise ValueError("Paper and alternate broker modes are unavailable")
        self.trading_mode = mode
        self._init_gateway()

    def get_gateway(self) -> IBrokerGateway:
        """Returns the active gateway adapter."""
        return self._gateway

    # Proxy implementation of IBrokerGateway interface
    def connect(self, **kwargs) -> bool:
        return self._gateway.connect(**kwargs)

    def disconnect(self) -> None:
        self._gateway.disconnect()

    def is_connected(self) -> bool:
        return self._gateway.is_connected()

    def get_profile(self) -> Dict[str, Any]:
        return self._gateway.get_profile()

    def get_funds(self) -> Any:
        return self._gateway.get_funds()

    def get_holdings(self) -> List[Any]:
        return self._gateway.get_holdings()

    def get_positions(self) -> List[Any]:
        return self._gateway.get_positions()

    def get_orders(self) -> List[Any]:
        return self._gateway.get_orders()

    def get_order_history(self, order_id: str) -> List[Any]:
        return self._gateway.get_order_history(order_id)

    def get_trades(self) -> List[Any]:
        return self._gateway.get_trades()

    def get_quote(self, symbols: List[str]) -> Dict[str, Any]:
        return self._gateway.get_quote(symbols)

    def get_ltp(self, symbols: List[str]) -> Dict[str, Any]:
        return self._gateway.get_ltp(symbols)

    def get_historical_data(
        self,
        instrument_token: int,
        from_date: Any,
        to_date: Any,
        interval: str,
        continuous: bool = False,
        oi: bool = False
    ) -> List[Dict[str, Any]]:
        return self._gateway.get_historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=interval,
            continuous=continuous,
            oi=oi
        )

    def get_instruments(self, exchange: Optional[str] = None) -> Any:
        return self._gateway.get_instruments(exchange)

    def place_order(self, **kwargs) -> Any:
        return self._gateway.place_order(**kwargs)

    def modify_order(self, **kwargs) -> Any:
        return self._gateway.modify_order(**kwargs)

    def cancel_order(self, **kwargs) -> Any:
        return self._gateway.cancel_order(**kwargs)

    def get_order_status(self, broker_order_id: str) -> Dict[str, Any]:
        return self._gateway.get_order_status(broker_order_id)

    def exit_position(self, **kwargs) -> Any:
        """
        Exits an active position for the given symbol and product by placing an offsetting market order.
        """
        return self._gateway.exit_position(**kwargs)

    def get_live_net_positions(self) -> List[Dict[str, Any]]:
        return self._gateway.get_live_net_positions()


    def calculate_order_margins(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self._gateway.calculate_order_margins(orders)

    def health(self) -> Any:
        return self._gateway.health()

    def login(self, request_token: str) -> bool:
        return self._gateway.login(request_token)

    def logout(self) -> bool:
        return self._gateway.logout()

    def validate_session(self) -> bool:
        return self._gateway.validate_session()

    def get_login_url(self) -> str:
        return self._gateway.get_login_url()

    def load_session(self) -> bool:
        return self._gateway.load_session()

    def save_session(self, access_token: str) -> bool:
        return self._gateway.save_session(access_token)

    # Immutable models wrappers for Task 3 & Task 4

    def get_quotes(self, symbols: List[str]) -> Dict[str, QuoteModel]:
        """
        Gets quotes for a list of instruments and returns them mapped to immutable QuoteModels.
        Gracefully handles missing symbols, expired contracts, and session/network failures.
        """
        from src.broker.models.quote import QuoteModel
        try:
            raw_quotes = self.get_quote(symbols)
            mapped: Dict[str, QuoteModel] = {}
            for sym in symbols:
                q_data = raw_quotes.get(sym)
                if q_data:
                    mapped[sym] = QuoteModel.from_dict(sym, q_data)
            return mapped
        except Exception as e:
            logger.error(f"Error in get_quotes: {e}")
            raise

    def get_quote_model(self, symbol: str) -> Optional[QuoteModel]:
        """
        Gets a single quote mapped to an immutable QuoteModel.
        """
        quotes = self.get_quotes([symbol])
        return quotes.get(symbol)

    def get_ltp_models(self, symbols: List[str]) -> Dict[str, LTPModel]:
        """
        Gets Last Traded Price (LTP) mapped to immutable LTPModels.
        """
        from src.broker.models.quote import LTPModel
        try:
            raw_ltps = self.get_ltp(symbols)
            mapped: Dict[str, LTPModel] = {}
            for sym in symbols:
                ltp_data = raw_ltps.get(sym)
                if ltp_data:
                    mapped[sym] = LTPModel.from_dict(sym, ltp_data)
            return mapped
        except Exception as e:
            logger.error(f"Error in get_ltp_models: {e}")
            raise

    def get_historical_candle_models(
        self,
        instrument_token: int,
        from_date: Any,
        to_date: Any,
        interval: str,
        continuous: bool = False,
        oi: bool = False
    ) -> List[CandleModel]:
        """
        Gets historical data mapped to a list of immutable CandleModels.
        """
        from src.broker.models.candle import CandleModel
        try:
            raw_data = self.get_historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
                continuous=continuous,
                oi=oi
            )
            return [CandleModel.from_dict(candle) for candle in raw_data]
        except Exception as e:
            logger.error(f"Error in get_historical_candle_models: {e}")
            raise

    # Real-Time Market Streaming Layer (WebSocket) Proxies

    def _get_orchestrator(self):
        from src.broker.services.streaming_orchestrator import StreamingOrchestrator
        api_key = getattr(self._gateway, "api_key", "") or getattr(Config, "KITE_API_KEY", "")
        access_token = getattr(self._gateway, "access_token", None) or getattr(Config, "KITE_ACCESS_TOKEN", "")
        if not api_key or not access_token:
            raise PermissionError("A genuine authenticated Kite session is required for market streaming")
        orch = StreamingOrchestrator.get_instance(self._gateway)
        orch.configure(api_key, access_token)
        return orch

    def connect_stream(self) -> bool:
        """Connects the real-time WebSocket streaming feed."""
        return self._get_orchestrator().connect_stream()

    def disconnect_stream(self) -> None:
        """Disconnects the real-time WebSocket streaming feed."""
        try:
            self._get_orchestrator().disconnect_stream()
        except PermissionError:
            pass

    def is_stream_connected(self) -> bool:
        """Checks if real-time streaming is active."""
        try:
            return self._get_orchestrator().is_connected()
        except PermissionError:
            return False

    def is_fallback_active(self) -> bool:
        """Checks if HTTP fallback polling is active."""
        try:
            return self._get_orchestrator().is_fallback_active()
        except PermissionError:
            return False

    def subscribe_stream(self, symbols: List[str]) -> List[int]:
        """Subscribes dynamically to symbol feeds."""
        try:
            return self._get_orchestrator().subscribe(symbols)
        except PermissionError:
            return []

    def unsubscribe_stream(self, symbols: List[str]) -> List[int]:
        """Unsubscribes dynamically from symbol feeds."""
        try:
            return self._get_orchestrator().unsubscribe(symbols)
        except PermissionError:
            return []

    def get_stream_health(self) -> Any:
        """Returns the current immutable StreamHealthReport."""
        try:
            return self._get_orchestrator().get_health_report()
        except PermissionError:
            from src.broker.models.stream_health import StreamHealthReport
            from src.broker.services.session_manager import SessionManager
            state = "DISCONNECTED" if SessionManager.is_explicitly_logged_out() else "AUTH_REQUIRED"
            return StreamHealthReport(
                connection_status="DISCONNECTED",
                last_heartbeat="",
                reconnect_count=0,
                tick_rate=0.0,
                average_latency_ms=0.0,
                message_throughput=0,
                last_received_timestamp="",
                active_subscriptions=[],
                fallback_active=False,
                feed_liveness_status=state,
                observation_age_seconds=None,
                last_source_observation_at=None,
                stale_since=None,
                auth_required_reason="Broker authentication required" if state == "AUTH_REQUIRED" else None,
                reconnect_state="IDLE"
            )

    def get_bootstrap_telemetry(self) -> Dict[str, Any]:
        """Returns stream operational telemetry and feed bootstrap status."""
        try:
            return self._get_orchestrator().get_bootstrap_telemetry()
        except PermissionError:
            from src.broker.services.session_manager import SessionManager
            state = "DISCONNECTED" if SessionManager.is_explicitly_logged_out() else "AUTH_REQUIRED"
            return {
                "bootstrap_state": state,
                "stream_status": "DISCONNECTED",
                "connection_started_at": None,
                "connection_uptime_seconds": 0.0,
                "generation_id": 1,
                "reconnect_count": 0,
                "last_reconnect_time": "IDLE",
                "subscribed_symbol_count": 0,
                "last_subscription_time": None,
                "last_valid_tick_time": None,
                "last_valid_nifty_time": None,
                "tick_age_seconds": None,
                "connection_telemetry": []
            }
