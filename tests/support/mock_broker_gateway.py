from __future__ import annotations
import logging
import time
from typing import List, Dict, Any, Optional

from src.broker.interfaces.broker_interface import IBrokerGateway
from src.broker.models.health import BrokerHealth
from src.models.execution_report import (
    BrokerAccount,
    BrokerFunds,
    BrokerPosition,
    BrokerHolding,
    BrokerOrder,
)
from src.broker.compat.connection import ConnectionManager
from src.broker.compat.account import AccountManager
from src.broker.compat.funds import FundsManager
from src.broker.compat.positions import PositionsManager
from src.broker.compat.holdings import HoldingsManager
from src.broker.compat.orders import OrdersManager

logger = logging.getLogger("MockBrokerGateway")


class MockBrokerGateway(IBrokerGateway):
    """
    Adapter implementation of IBrokerGateway for mock paper trading.
    Delegates to the existing connection and manager layers to maintain
    full state and backward compatibility.
    """

    def __init__(self) -> None:
        self.connection_manager = ConnectionManager()

    def connect(self, **kwargs) -> bool:
        """Establishes connection to the mock broker."""
        api_key = kwargs.get("api_key", "MOCK_API_KEY")
        request_token = kwargs.get("request_token", "MOCK_REQ_TOKEN")
        api_secret = kwargs.get("api_secret", "MOCK_SECRET")
        return self.connection_manager.connect(
            api_key=api_key,
            request_token=request_token,
            api_secret=api_secret
        )

    def connect_with_token(self, api_key: str, access_token: str) -> bool:
        """Initializes connection directly using an access token."""
        return self.connection_manager.connect_with_token(api_key, access_token)

    def disconnect(self) -> None:
        """Clears connection state."""
        self.connection_manager.disconnect()

    def is_connected(self) -> bool:
        """Checks if connection is active."""
        return self.connection_manager.is_connected()

    def get_profile(self) -> Dict[str, Any]:
        """Retrieves profile information from the mock broker."""
        try:
            acc = AccountManager.get_account_info()
            return {
                "client_id": acc.client_id,
                "user_name": acc.name,
                "email": acc.email,
                "broker": acc.broker,
                "pan": "ABCDE1234F",
                "user_type": "individual",
                "login_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            return {"client_id": "ERROR", "user_name": "ERROR", "email": "ERROR"}

    def get_funds(self) -> BrokerFunds:
        """Retrieves funds and margin details."""
        return FundsManager.get_funds_info()

    def get_holdings(self) -> List[BrokerHolding]:
        """Retrieves mock equity holdings."""
        return HoldingsManager.get_holdings()

    def get_positions(self) -> List[BrokerPosition]:
        """Retrieves active trading positions."""
        return PositionsManager.get_positions()

    def get_orders(self) -> List[BrokerOrder]:
        """Retrieves today's orders."""
        return OrdersManager.get_orders()

    def get_order_history(self, order_id: str) -> List[BrokerOrder]:
        """Retrieves history for a specific order ID."""
        return OrdersManager.get_order_history(order_id)

    def get_trades(self) -> List[Dict[str, Any]]:
        """Retrieves today's executed trades."""
        return [
            {
                "trade_id": "T10001",
                "order_id": "O10001",
                "tradingsymbol": "NIFTY26JUL22000CE",
                "exchange": "NFO",
                "transaction_type": "BUY",
                "quantity": 50,
                "average_price": 125.50,
                "fill_timestamp": time.strftime("%Y-%m-%d 10:15:30")
            },
            {
                "trade_id": "T10002",
                "order_id": "O10002",
                "tradingsymbol": "NIFTY26JUL22200PE",
                "exchange": "NFO",
                "transaction_type": "SELL",
                "quantity": 50,
                "average_price": 85.20,
                "fill_timestamp": time.strftime("%Y-%m-%d 14:22:15")
            }
        ]

    def get_quote(self, symbols: List[str]) -> Dict[str, Any]:
        """Retrieves quotes for a list of instruments."""
        if not self.is_connected():
            return {}
        client = self.connection_manager.get_client()
        try:
            # Map standard quotes
            quotes = {}
            for symbol in symbols:
                # Expecting exchange:symbol format
                resp = client.quote(symbol)
                if resp:
                    quotes.update(resp)
            return quotes
        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return {}

    def get_ltp(self, symbols: List[str]) -> Dict[str, Any]:
        """Retrieves Last Traded Price (LTP) map."""
        if not self.is_connected():
            return {}
        client = self.connection_manager.get_client()
        try:
            return client.ltp(symbols)
        except Exception as e:
            logger.error(f"Error fetching ltp: {e}")
            return {}

    def get_historical_data(
        self,
        instrument_token: int,
        from_date: Any,
        to_date: Any,
        interval: str,
        continuous: bool = False,
        oi: bool = False
    ) -> List[Dict[str, Any]]:
        """Retrieves historical candle data."""
        if not self.is_connected():
            return []
        client = self.connection_manager.get_client()
        try:
            return client.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
                continuous=continuous,
                oi=oi
            )
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []

    def get_instruments(self, exchange: Optional[str] = None) -> Any:
        """Retrieves instruments list."""
        if not self.is_connected():
            return []
        client = self.connection_manager.get_client()
        try:
            if exchange:
                return client.instruments(exchange)
            return client.instruments()
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            return []

    def place_order(self, **kwargs) -> Any:
        """Places a new order with the mock broker."""
        if not self.is_connected():
            raise Exception("Mock broker not connected.")
        client = self.connection_manager.get_client()
        return client.place_order(**kwargs)

    def modify_order(self, **kwargs) -> Any:
        """Modifies an existing pending order."""
        if not self.is_connected():
            raise Exception("Mock broker not connected.")
        client = self.connection_manager.get_client()
        return client.modify_order(**kwargs)

    def cancel_order(self, **kwargs) -> Any:
        """Cancels an existing pending order."""
        if not self.is_connected():
            raise Exception("Mock broker not connected.")
        client = self.connection_manager.get_client()
        return client.cancel_order(**kwargs)

    def health(self) -> BrokerHealth:
        """Retrieves mock connection and broker health status metrics."""
        connected = self.is_connected()
        profile_info = self.get_profile() if connected else {}
        client_id = profile_info.get("client_id", "N/A")
        
        return BrokerHealth(
            broker_name="Mock Broker (Paper)",
            connection_status="CONNECTED" if connected else "DISCONNECTED",
            trading_mode="PAPER_TRADING",
            latency=0.5 if connected else 0.0,
            authentication_state="AUTHENTICATED" if connected else "UNAUTHENTICATED",
            last_heartbeat=time.strftime("%Y-%m-%d %H:%M:%S"),
            instrument_cache_status="VALID",
            market_status="OPEN",
            health_score=100.0 if connected else 0.0,
            last_error=None,
            
            # Extended metrics (Sprint 28)
            authentication_status="AUTHENTICATED" if connected else "UNAUTHENTICATED",
            session_age_hours=0.1 if connected else 0.0,
            token_expiry="Never" if connected else "N/A",
            last_login_time=time.strftime("%Y-%m-%d %H:%M:%S") if connected else "N/A",
            session_valid=connected,
            broker_version="MockBroker v1.0",
            api_status="ONLINE"
        )

    def login(self, request_token: str) -> bool:
        """Exchanges request token for access token and establishes session (placeholder)."""
        logger.info(f"MockBrokerGateway: Exchanging request token {request_token}")
        return self.connect(request_token=request_token)

    def logout(self) -> bool:
        """Clears session and logs out (placeholder)."""
        logger.info("MockBrokerGateway: Logging out")
        self.disconnect()
        return True

    def validate_session(self) -> bool:
        """Validates current session (placeholder)."""
        return self.is_connected()

    def get_login_url(self) -> str:
        """Generates login URL for the broker (placeholder)."""
        return "https://kite.trade/connect/login?api_key=MOCK_API_KEY"

    def load_session(self) -> bool:
        """Loads and restores existing cached session (placeholder)."""
        logger.info("MockBrokerGateway: Loading session")
        return self.connect()

    def save_session(self, access_token: str) -> bool:
        """Saves current access token to local cache (placeholder)."""
        logger.info(f"MockBrokerGateway: Saving access token {access_token}")
        return True

