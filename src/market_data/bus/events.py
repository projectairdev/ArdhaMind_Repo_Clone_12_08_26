from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence, Set


class MarketEventType(str, Enum):
    """
    Standardized taxonomy of market data and feed lifecycle events for Ardha.
    Symbol-specific events (e.g. NIFTY_TICK) are intentionally avoided;
    instrument identity is carried by canonical_instrument_id.
    """
    TICK = "TICK"
    CANDLE_UPDATED = "CANDLE_UPDATED"
    CANDLE_CLOSED = "CANDLE_CLOSED"
    OPTION_CHAIN_UPDATED = "OPTION_CHAIN_UPDATED"
    BREADTH_UPDATED = "BREADTH_UPDATED"
    FEED_CONNECTED = "FEED_CONNECTED"
    FEED_DELAYED = "FEED_DELAYED"
    FEED_STALE = "FEED_STALE"
    FEED_RECOVERING = "FEED_RECOVERING"
    FEED_RECOVERED = "FEED_RECOVERED"
    FEED_DISCONNECTED = "FEED_DISCONNECTED"
    SESSION_OPENED = "SESSION_OPENED"
    SESSION_CLOSED = "SESSION_CLOSED"


class EventBusBackpressureError(RuntimeError):
    """Raised when the MarketEventBus queue capacity is exceeded."""
    pass


class EventBusStoppedError(RuntimeError):
    """Raised when attempting to publish to a stopped MarketEventBus."""
    pass


def freeze_payload(obj: Any) -> Any:
    """
    Recursively transforms mutable containers (dict, list, set) into immutable equivalents
    (MappingProxyType, tuple, frozenset).
    Leaves primitives and known immutable objects intact.
    Deep copies during transformation to guarantee isolation from source mutations.
    """
    if isinstance(obj, (dict, Mapping)):
        frozen_dict = {
            freeze_payload(k): freeze_payload(v)
            for k, v in obj.items()
        }
        return MappingProxyType(frozen_dict)
    elif isinstance(obj, list):
        return tuple(freeze_payload(item) for item in obj)
    elif isinstance(obj, tuple):
        return tuple(freeze_payload(item) for item in obj)
    elif isinstance(obj, (set, frozenset)):
        return frozenset(freeze_payload(item) for item in obj)
    return obj


@dataclass(frozen=True)
class MarketEvent:
    """
    Immutable, provider-independent market event envelope.
    Carries a monotonically sequenced payload with strict timestamp guarantees.
    """
    event_id: str
    event_type: MarketEventType
    created_at: datetime
    sequence: int
    payload: Any
    canonical_instrument_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.event_id or not isinstance(self.event_id, str):
            raise ValueError("MarketEvent 'event_id' must be a non-empty string.")
        if not isinstance(self.event_type, MarketEventType):
            if isinstance(self.event_type, str):
                try:
                    object.__setattr__(self, "event_type", MarketEventType(self.event_type))
                except ValueError:
                    raise ValueError(f"Invalid MarketEventType '{self.event_type}'.")
            else:
                raise TypeError(f"MarketEvent 'event_type' must be MarketEventType, got {type(self.event_type)}.")
        if not isinstance(self.created_at, datetime) or self.created_at.tzinfo is None:
            raise ValueError("MarketEvent 'created_at' must be a timezone-aware datetime.")
        if not isinstance(self.sequence, int) or self.sequence <= 0:
            raise ValueError(f"MarketEvent 'sequence' must be a positive integer, got {self.sequence}.")

        # Recursively freeze payload containers to guarantee deep immutability & isolation
        object.__setattr__(self, "payload", freeze_payload(self.payload))
