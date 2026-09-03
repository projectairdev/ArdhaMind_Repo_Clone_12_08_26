from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Sequence

from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_option_chain import CanonicalOptionChainSnapshot


class IOptionChainProvider(ABC):
    """
    Abstract interface for fetching option chain universe and contract snapshots.
    """

    @abstractmethod
    def get_available_expiries(self, underlying: CanonicalInstrument) -> Sequence[str]:
        """
        Returns sorted list of available expiry dates (YYYY-MM-DD) for the given underlying index/equity.
        """
        pass

    @abstractmethod
    def fetch_option_chain(self, underlying: CanonicalInstrument, expiry: str) -> CanonicalOptionChainSnapshot:
        """
        Fetches the complete option chain snapshot for the given underlying and expiry date.
        """
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """Returns the canonical provider identifier (e.g. 'DHAN', 'KITE')."""
        pass
