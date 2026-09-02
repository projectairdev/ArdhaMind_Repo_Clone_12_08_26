from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class CanonicalTick:
    """
    Immutable normalized market tick packet directly produced by raw ingestors.
    All timestamps must be explicit and timezone-aware. Prices must be strictly valid.
    """
    canonical_instrument_id: str
    provider: str
    exchange_timestamp: datetime
    received_at: datetime
    session_date: date
    last_price: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    previous_close: Optional[float] = None
    volume: Optional[int] = None
    oi: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    internal_sequence: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.canonical_instrument_id or not isinstance(self.canonical_instrument_id, str) or not self.canonical_instrument_id.strip():
            raise ValueError("CanonicalTick 'canonical_instrument_id' must be a non-empty string.")
        if not self.provider or not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError("CanonicalTick 'provider' must be a non-empty string.")
        if not isinstance(self.exchange_timestamp, datetime) or self.exchange_timestamp.tzinfo is None:
            raise ValueError("CanonicalTick 'exchange_timestamp' must be a timezone-aware datetime.")
        if not isinstance(self.received_at, datetime) or self.received_at.tzinfo is None:
            raise ValueError("CanonicalTick 'received_at' must be a timezone-aware datetime.")
        if not isinstance(self.session_date, date):
            raise TypeError("CanonicalTick 'session_date' must be a date instance.")
        if not isinstance(self.last_price, (int, float)) or self.last_price <= 0.0:
            raise ValueError(f"CanonicalTick 'last_price' must be a positive number, got {self.last_price}.")

        # Optional numeric OHLC validations
        for name, val in [("open", self.open), ("high", self.high), ("low", self.low), ("previous_close", self.previous_close)]:
            if val is not None and (not isinstance(val, (int, float)) or val <= 0.0):
                raise ValueError(f"CanonicalTick '{name}' must be positive when provided, got {val}.")

        if self.high is not None and self.low is not None and self.high < self.low:
            raise ValueError(f"CanonicalTick 'high' ({self.high}) cannot be less than 'low' ({self.low}).")

        # Optional volume / OI checks
        if self.volume is not None and (not isinstance(self.volume, int) or self.volume < 0):
            raise ValueError(f"CanonicalTick 'volume' cannot be negative, got {self.volume}.")
        if self.oi is not None and (not isinstance(self.oi, int) or self.oi < 0):
            raise ValueError(f"CanonicalTick 'oi' cannot be negative, got {self.oi}.")

        # Bid / Ask checks
        if self.bid is not None:
            if not isinstance(self.bid, (int, float)) or self.bid < 0.0:
                raise ValueError(f"CanonicalTick 'bid' cannot be negative, got {self.bid}.")
        if self.ask is not None:
            if not isinstance(self.ask, (int, float)) or self.ask < 0.0:
                raise ValueError(f"CanonicalTick 'ask' cannot be negative, got {self.ask}.")
        if self.bid is not None and self.ask is not None and self.bid > 0 and self.ask > 0:
            if self.ask < self.bid:
                raise ValueError(f"CanonicalTick 'ask' ({self.ask}) cannot be less than 'bid' ({self.bid}).")
