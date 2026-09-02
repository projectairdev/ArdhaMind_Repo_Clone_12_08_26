from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Sequence

from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_tick import CanonicalTick


class IMarketDataProvider(ABC):
    """
    Abstract interface for real-time market data providers.
    Zero trading, broker authentication, or execution methods allowed.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Establishes real-time connection to the upstream market data feed."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Terminates the real-time market data connection."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Returns True if the feed transport is actively connected and authenticated."""
        pass

    @abstractmethod
    def subscribe(self, instruments: Sequence[CanonicalInstrument]) -> bool:
        """Subscribes to live market data ticks for the specified canonical instruments."""
        pass

    @abstractmethod
    def unsubscribe(self, instruments: Sequence[CanonicalInstrument]) -> bool:
        """Unsubscribes from live market data ticks for the specified canonical instruments."""
        pass

    @abstractmethod
    def set_tick_handler(self, handler: Callable[[CanonicalTick], None]) -> None:
        """Registers the callback handler invoked on every validated CanonicalTick."""
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """Returns the canonical provider identifier (e.g. 'DHAN', 'KITE')."""
        pass
