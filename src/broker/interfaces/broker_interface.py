from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IBrokerGateway(ABC):
    """
    Abstract Base Class representing a common interface for multiple brokers.
    All adapters must implement these methods.
    """

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """Establishes connection to the broker."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Clears active connection state."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Validates if connection is active."""
        pass

    @abstractmethod
    def get_profile(self) -> Dict[str, Any]:
        """Retrieves user profile information."""
        pass

    @abstractmethod
    def get_funds(self) -> Any:
        """Retrieves funds and margin details."""
        pass

    @abstractmethod
    def get_holdings(self) -> List[Any]:
        """Retrieves equity holdings."""
        pass

    @abstractmethod
    def get_positions(self) -> List[Any]:
        """Retrieves active trading positions."""
        pass

    @abstractmethod
    def get_orders(self) -> List[Any]:
        """Retrieves today's orders."""
        pass

    @abstractmethod
    def get_order_history(self, order_id: str) -> List[Any]:
        """Retrieves history for a specific order ID."""
        pass

    @abstractmethod
    def get_trades(self) -> List[Any]:
        """Retrieves executed trades for today."""
        pass

    @abstractmethod
    def get_quote(self, symbols: List[str]) -> Dict[str, Any]:
        """Retrieves quotes for a list of instruments."""
        pass

    @abstractmethod
    def get_ltp(self, symbols: List[str]) -> Dict[str, Any]:
        """Retrieves Last Traded Price (LTP) map for a list of instruments."""
        pass

    @abstractmethod
    def get_historical_data(
        self,
        instrument_token: int,
        from_date: Any,
        to_date: Any,
        interval: str,
        continuous: bool = False,
        oi: bool = False
    ) -> List[Dict[str, Any]]:
        """Retrieves historical candle/OHLC data."""
        pass

    @abstractmethod
    def get_instruments(self, exchange: Optional[str] = None) -> Any:
        """Retrieves master list of instruments."""
        pass

    @abstractmethod
    def place_order(self, **kwargs) -> Any:
        """Places a new order with the broker."""
        pass

    @abstractmethod
    def modify_order(self, **kwargs) -> Any:
        """Modifies an existing pending order."""
        pass

    @abstractmethod
    def cancel_order(self, **kwargs) -> Any:
        """Cancels an existing pending order."""
        pass

    @abstractmethod
    def health(self) -> Any:
        """Retrieves connection and broker health status metrics."""
        pass

    @abstractmethod
    def login(self, request_token: str) -> bool:
        """Exchanges request token for access token and establishes session."""
        pass

    @abstractmethod
    def logout(self) -> bool:
        """Clears session and logs out."""
        pass

    @abstractmethod
    def validate_session(self) -> bool:
        """Validates current session."""
        pass

    @abstractmethod
    def get_login_url(self) -> str:
        """Generates login URL for the broker."""
        pass

    @abstractmethod
    def load_session(self) -> bool:
        """Loads and restores existing cached session."""
        pass

    @abstractmethod
    def save_session(self, access_token: str) -> bool:
        """Saves current access token to local cache."""
        pass

