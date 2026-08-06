from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class OHLCModel:
    open: float
    high: float
    low: float
    close: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OHLCModel:
        return cls(
            open=float(data.get("open", 0.0) or 0.0),
            high=float(data.get("high", 0.0) or 0.0),
            low=float(data.get("low", 0.0) or 0.0),
            close=float(data.get("close", 0.0) or 0.0),
        )


@dataclass(frozen=True)
class QuoteModel:
    symbol: str
    instrument_token: int
    last_price: float
    volume: int
    net_change: float
    ohlc: OHLCModel
    timestamp: str
    oi: int = 0
    buy_quantity: int = 0
    sell_quantity: int = 0

    @classmethod
    def from_dict(cls, symbol: str, data: Dict[str, Any]) -> QuoteModel:
        ohlc_data = data.get("ohlc", {})
        return cls(
            symbol=symbol,
            instrument_token=int(data.get("instrument_token", 0) or 0),
            last_price=float(data.get("last_price", 0.0) or 0.0),
            volume=int(data.get("volume", 0) or 0),
            net_change=float(data.get("net_change", 0.0) or 0.0),
            ohlc=OHLCModel.from_dict(ohlc_data),
            timestamp=str(data.get("timestamp", "") or data.get("last_trade_time", "") or ""),
            oi=int(data.get("oi", 0) or 0),
            buy_quantity=int(data.get("buy_quantity", 0) or 0),
            sell_quantity=int(data.get("sell_quantity", 0) or 0),
        )


@dataclass(frozen=True)
class LTPModel:
    symbol: str
    instrument_token: int
    last_price: float

    @classmethod
    def from_dict(cls, symbol: str, data: Dict[str, Any]) -> LTPModel:
        return cls(
            symbol=symbol,
            instrument_token=int(data.get("instrument_token", 0) or 0),
            last_price=float(data.get("last_price", 0.0) or 0.0),
        )
