from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Sequence

from src.market_data.models.quality_enums import DataQualityStatus, OptionType


@dataclass(frozen=True)
class CanonicalOptionLeg:
    """
    Immutable representation of a single Call or Put option contract in an option chain.
    """
    canonical_instrument_id: str
    strike: float
    option_type: OptionType | str
    last_price: Optional[float] = None
    oi: Optional[int] = None
    oi_change: Optional[int] = None
    volume: Optional[int] = None
    iv: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    greeks_source: str = "PROVIDER"

    def __post_init__(self) -> None:
        if not self.canonical_instrument_id or not isinstance(self.canonical_instrument_id, str):
            raise ValueError("CanonicalOptionLeg 'canonical_instrument_id' must be a non-empty string.")
        if self.strike <= 0:
            raise ValueError(f"CanonicalOptionLeg 'strike' must be positive, got {self.strike}.")
        if self.last_price is not None and self.last_price <= 0:
            raise ValueError(f"CanonicalOptionLeg 'last_price' must be positive, got {self.last_price}.")
        if self.oi is not None and self.oi < 0:
            raise ValueError(f"CanonicalOptionLeg 'oi' cannot be negative, got {self.oi}.")
        if self.volume is not None and self.volume < 0:
            raise ValueError(f"CanonicalOptionLeg 'volume' cannot be negative, got {self.volume}.")
        if self.bid is not None and self.ask is not None and self.bid > 0 and self.ask > 0:
            if self.ask < self.bid:
                raise ValueError(f"CanonicalOptionLeg 'ask' ({self.ask}) cannot be less than 'bid' ({self.bid}).")


@dataclass(frozen=True)
class CanonicalOptionStrike:
    """
    Combines CE and PE legs at a single strike level.
    """
    strike: float
    call: Optional[CanonicalOptionLeg] = None
    put: Optional[CanonicalOptionLeg] = None

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValueError(f"CanonicalOptionStrike 'strike' must be positive, got {self.strike}.")
        if self.call is None and self.put is None:
            raise ValueError("CanonicalOptionStrike must contain at least one leg (call or put).")


@dataclass(frozen=True)
class CanonicalOptionChainSnapshot:
    """
    Immutable, provider-independent snapshot of an entire option chain for an underlying and expiry.
    """
    underlying_instrument_id: str
    underlying_price: float
    expiry: str
    session_date: date
    captured_at: datetime
    provider: str
    strikes: Sequence[CanonicalOptionStrike]
    quality: DataQualityStatus = DataQualityStatus.VALID

    def __post_init__(self) -> None:
        if not self.underlying_instrument_id:
            raise ValueError("CanonicalOptionChainSnapshot 'underlying_instrument_id' is required.")
        if self.underlying_price <= 0:
            raise ValueError(f"CanonicalOptionChainSnapshot 'underlying_price' must be positive, got {self.underlying_price}.")
        if not self.expiry:
            raise ValueError("CanonicalOptionChainSnapshot 'expiry' is required.")
        if not isinstance(self.session_date, date):
            raise TypeError("CanonicalOptionChainSnapshot 'session_date' must be a date instance.")
        if not isinstance(self.captured_at, datetime) or self.captured_at.tzinfo is None:
            raise ValueError("CanonicalOptionChainSnapshot 'captured_at' must be a timezone-aware datetime.")
        if not self.provider:
            raise ValueError("CanonicalOptionChainSnapshot 'provider' is required.")
