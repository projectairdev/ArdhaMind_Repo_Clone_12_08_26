from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence

from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.quality_enums import Timeframe


class IHistoricalDataProvider(ABC):
    """
    Abstract interface for fetching historical candle data from market data providers.
    """

    @abstractmethod
    def fetch_candles(
        self,
        instrument: CanonicalInstrument,
        timeframe: Timeframe | str,
        start: datetime,
        end: datetime,
    ) -> Sequence[CanonicalCandle]:
        """
        Fetches historical candles for an instrument within the [start, end] window.
        Returns a sequence of validated CanonicalCandle instances.
        """
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """Returns the canonical provider identifier (e.g. 'DHAN', 'KITE')."""
        pass
