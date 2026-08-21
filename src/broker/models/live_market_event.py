# src/broker/models/live_market_event.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time
from datetime import datetime, timezone


@dataclass(frozen=True)
class LiveMarketEvent:
    runtime_id: str
    state_sequence: int
    instrument_token: int
    symbol: str
    event_type: str  # "TICK", "SNAPSHOT", "STATUS"
    price: float
    open: float
    high: float
    low: float
    previous_close: float
    change_points: float
    change_pct: float
    volume: int
    oi: int
    bid: float
    ask: float
    provider_observed_at: str
    backend_received_at: str
    canonical_committed_at: str
    freshness: str  # "FRESH", "DELAYED", "STALE", "UNAVAILABLE"
    source: str = "ZERODHA_KITE"
    raw_depth: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "state_sequence": self.state_sequence,
            "instrument_token": self.instrument_token,
            "symbol": self.symbol,
            "event_type": self.event_type,
            "price": self.price,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "previous_close": self.previous_close,
            "change_points": round(self.change_points, 2),
            "change_pct": round(self.change_pct, 2),
            "volume": self.volume,
            "oi": self.oi,
            "bid": self.bid,
            "ask": self.ask,
            "provider_observed_at": self.provider_observed_at,
            "backend_received_at": self.backend_received_at,
            "canonical_committed_at": self.canonical_committed_at,
            "freshness": self.freshness,
            "source": self.source
        }
