from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import time

@dataclass(frozen=True)
class TickModel:
    instrument_token: int
    symbol: str
    last_price: float
    volume: int
    oi: int
    open: float
    high: float
    low: float
    close: float
    change: float
    timestamp: str  # Normalized ISO timestamp

    @classmethod
    def from_dict(cls, symbol: str, data: Dict[str, Any]) -> TickModel:
        # Normalize timestamp to ISO format
        raw_ts = data.get("timestamp") or data.get("last_trade_time")
        if not raw_ts:
            ts_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        elif isinstance(raw_ts, (int, float)):
            # convert Unix epoch to string
            ts_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(raw_ts))
        else:
            ts_str = str(raw_ts)

        ohlc = data.get("ohlc", {})
        return cls(
            instrument_token=int(data.get("instrument_token", 0) or 0),
            symbol=symbol,
            last_price=float(data.get("last_price", 0.0) or data.get("last_traded_price", 0.0) or 0.0),
            volume=int(data.get("volume", 0) or data.get("volume_traded", 0) or 0),
            oi=int(data.get("oi", 0) or 0),
            open=float(ohlc.get("open", 0.0) or 0.0),
            high=float(ohlc.get("high", 0.0) or 0.0),
            low=float(ohlc.get("low", 0.0) or 0.0),
            close=float(ohlc.get("close", 0.0) or 0.0),
            change=float(data.get("change", 0.0) or 0.0),
            timestamp=ts_str
        )
