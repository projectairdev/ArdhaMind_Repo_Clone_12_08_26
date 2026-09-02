from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from src.market_data.models.quality_enums import CandleQuality, Timeframe


@dataclass(frozen=True)
class CanonicalCandle:
    """
    Immutable, validated candlestick price series element.
    Candles must strictly conform to mathematical OHLC bounds and start < end timestamp ordering.
    """
    canonical_instrument_id: str
    provider: str
    session_date: date
    timeframe: Timeframe | str
    start_timestamp: datetime
    end_timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None
    oi: Optional[int] = None
    quality: CandleQuality = CandleQuality.VALID

    def __post_init__(self) -> None:
        if not self.canonical_instrument_id or not isinstance(self.canonical_instrument_id, str) or not self.canonical_instrument_id.strip():
            raise ValueError("CanonicalCandle 'canonical_instrument_id' must be a non-empty string.")
        if not self.provider or not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError("CanonicalCandle 'provider' must be a non-empty string.")
        if not isinstance(self.session_date, date):
            raise TypeError("CanonicalCandle 'session_date' must be a date instance.")
        if not self.timeframe:
            raise ValueError("CanonicalCandle 'timeframe' is required.")
        if not isinstance(self.start_timestamp, datetime) or self.start_timestamp.tzinfo is None:
            raise ValueError("CanonicalCandle 'start_timestamp' must be a timezone-aware datetime.")
        if not isinstance(self.end_timestamp, datetime) or self.end_timestamp.tzinfo is None:
            raise ValueError("CanonicalCandle 'end_timestamp' must be a timezone-aware datetime.")
        if self.start_timestamp >= self.end_timestamp:
            raise ValueError(f"CanonicalCandle 'start_timestamp' ({self.start_timestamp}) must be strictly before 'end_timestamp' ({self.end_timestamp}).")

        # OHLC numeric positivity checks
        for name, val in [("open", self.open), ("high", self.high), ("low", self.low), ("close", self.close)]:
            if not isinstance(val, (int, float)) or val <= 0.0:
                raise ValueError(f"CanonicalCandle '{name}' must be a positive number, got {val}.")

        # OHLC Invariants: low <= open <= high, low <= close <= high
        if not (self.low <= self.open <= self.high):
            raise ValueError(f"CanonicalCandle OHLC invariant violation: low ({self.low}) <= open ({self.open}) <= high ({self.high}) is false.")
        if not (self.low <= self.close <= self.high):
            raise ValueError(f"CanonicalCandle OHLC invariant violation: low ({self.low}) <= close ({self.close}) <= high ({self.high}) is false.")

        # Volume / OI non-negativity
        if self.volume is not None and (not isinstance(self.volume, int) or self.volume < 0):
            raise ValueError(f"CanonicalCandle 'volume' cannot be negative, got {self.volume}.")
        if self.oi is not None and (not isinstance(self.oi, int) or self.oi < 0):
            raise ValueError(f"CanonicalCandle 'oi' cannot be negative, got {self.oi}.")

        # Quality validation
        if not isinstance(self.quality, CandleQuality):
            if isinstance(self.quality, str):
                try:
                    object.__setattr__(self, "quality", CandleQuality(self.quality))
                except ValueError:
                    raise ValueError(f"Invalid CandleQuality '{self.quality}'. Permitted values: {[q.value for q in CandleQuality]}")
            else:
                raise TypeError(f"CanonicalCandle 'quality' must be a CandleQuality enum, got {type(self.quality)}.")
