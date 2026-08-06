from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OptionContract:
    tradingsymbol: str
    strike: float
    expiry: str
    lot_size: int
    instrument_type: str


@dataclass
class OptionChainMetrics:
    option_ltp: float
    option_volume: int
    option_oi: int
    bid_price: float
    ask_price: float
    spread_pct: float
