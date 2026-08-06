from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

from src.broker.interfaces.broker_interface import IBrokerGateway
from src.broker.models.trading_mode import TradingMode
from src.broker.adapters.mock_broker import MockBrokerGateway
from src.broker.adapters.kite_broker import KiteBrokerGateway
from src.config_engine import Config

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
        
        # Load trading mode from Config or fallback to PAPER_TRADING
        mode_str = getattr(Config, "TRADING_MODE", "PAPER_TRADING")
        try:
            self.trading_mode = TradingMode(mode_str)
        except ValueError:
            self.trading_mode = TradingMode.PAPER_TRADING

        self._init_gateway()
        self._initialized = True

    def _init_gateway(self) -> None:
        """Dynamically instantiates the adapter based on the active trading mode."""
        logger.info(f"Initializing BrokerService with mode: {self.trading_mode.value}")
        if self.trading_mode == TradingMode.LIVE_ZERODHA:
            self._gateway = KiteBrokerGateway()
        else:
            self._gateway = MockBrokerGateway()
        
        class_name = "LiveKiteBroker" if self.trading_mode == TradingMode.LIVE_ZERODHA else "MockBroker"
        import sys
        print(f"BrokerService initialized:\nClass:\n{class_name}", file=sys.stderr, flush=True)

    @classmethod
    def get_instance(cls) -> BrokerService:
        """Utility method to retrieve or instantiate the singleton."""
        return cls()

    def set_mode(self, mode: TradingMode) -> None:
        """Allows dynamic switching of the trading mode (primarily for testing)."""
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
        from src.workspace.workspace_mode import WorkspaceMode
        from src.workspace.workspace_manager import WorkspaceManager
        wm = WorkspaceManager.get_instance()
        if wm.current_mode == WorkspaceMode.LIVE_PRACTICE:
            logger.info("Virtual Execution: Simulating order placement")
            from src.broker.services.virtual_execution import VirtualExecutionManager
            return VirtualExecutionManager.get_instance().place_order(self, **kwargs)
        return self._gateway.place_order(**kwargs)

    def modify_order(self, **kwargs) -> Any:
        from src.workspace.workspace_mode import WorkspaceMode
        from src.workspace.workspace_manager import WorkspaceManager
        wm = WorkspaceManager.get_instance()
        if wm.current_mode == WorkspaceMode.LIVE_PRACTICE:
            logger.info("Virtual Execution: Simulating order modification")
            from src.broker.services.virtual_execution import VirtualExecutionManager
            return VirtualExecutionManager.get_instance().modify_order(**kwargs)
        return self._gateway.modify_order(**kwargs)

    def cancel_order(self, **kwargs) -> Any:
        from src.workspace.workspace_mode import WorkspaceMode
        from src.workspace.workspace_manager import WorkspaceManager
        wm = WorkspaceManager.get_instance()
        if wm.current_mode == WorkspaceMode.LIVE_PRACTICE:
            logger.info("Virtual Execution: Simulating order cancellation")
            from src.broker.services.virtual_execution import VirtualExecutionManager
            return VirtualExecutionManager.get_instance().cancel_order(**kwargs)
        return self._gateway.cancel_order(**kwargs)

    def exit_position(self, tradingsymbol: str, product: str) -> Optional[str]:
        """
        Exits an active position for the given symbol and product by placing an offsetting market order.
        """
        positions = self.get_positions()
        for pos in positions:
            symbol = pos.tradingsymbol if hasattr(pos, "tradingsymbol") else (pos.get("tradingsymbol") if isinstance(pos, dict) else None)
            prod = pos.product if hasattr(pos, "product") else (pos.get("product") if isinstance(pos, dict) else None)
            qty = pos.quantity if hasattr(pos, "quantity") else (pos.get("quantity", 0) if isinstance(pos, dict) else 0)
            exchange = pos.exchange if hasattr(pos, "exchange") else (pos.get("exchange", "NSE") if isinstance(pos, dict) else "NSE")
            
            if symbol == tradingsymbol and prod == product:
                if qty == 0:
                    logger.warning(f"Position for {tradingsymbol} ({product}) is already closed (qty=0).")
                    return None
                
                transaction_type = "SELL" if qty > 0 else "BUY"
                abs_qty = abs(qty)
                
                order_id = self.place_order(
                    tradingsymbol=tradingsymbol,
                    exchange=exchange,
                    transaction_type=transaction_type,
                    quantity=abs_qty,
                    product=product,
                    order_type="MARKET"
                )
                logger.info(f"Exited position for {tradingsymbol} with order {order_id} ({transaction_type} {abs_qty})")
                return order_id
        logger.warning(f"No active position found for {tradingsymbol} ({product})")
        return None


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
        orch = StreamingOrchestrator.get_instance(self._gateway)
        api_key = getattr(self._gateway, "api_key", "") or getattr(Config, "KITE_API_KEY", "")
        access_token = getattr(self._gateway, "access_token", None) or getattr(Config, "KITE_ACCESS_TOKEN", "")
        orch.configure(api_key, access_token or "MOCK_TOKEN")
        return orch

    def connect_stream(self) -> bool:
        """Connects the real-time WebSocket streaming feed."""
        return self._get_orchestrator().connect_stream()

    def disconnect_stream(self) -> None:
        """Disconnects the real-time WebSocket streaming feed."""
        self._get_orchestrator().disconnect_stream()

    def is_stream_connected(self) -> bool:
        """Checks if real-time streaming is active."""
        return self._get_orchestrator().is_connected()

    def is_fallback_active(self) -> bool:
        """Checks if HTTP fallback polling is active."""
        return self._get_orchestrator().is_fallback_active()

    def subscribe_stream(self, symbols: List[str]) -> List[int]:
        """Subscribes dynamically to symbol feeds."""
        return self._get_orchestrator().subscribe(symbols)

    def unsubscribe_stream(self, symbols: List[str]) -> List[int]:
        """Unsubscribes dynamically from symbol feeds."""
        return self._get_orchestrator().unsubscribe(symbols)

    def get_stream_health(self) -> Any:
        """Returns the current immutable StreamHealthReport."""
        return self._get_orchestrator().get_health_report()


