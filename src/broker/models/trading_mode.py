from __future__ import annotations
from enum import Enum


class TradingMode(Enum):
    PAPER_TRADING = "PAPER_TRADING"
    LIVE_ZERODHA = "LIVE_ZERODHA"
    LIVE_UPSTOX = "LIVE_UPSTOX"
    LIVE_DHAN = "LIVE_DHAN"
    LIVE_ANGELONE = "LIVE_ANGELONE"
    LIVE_FYERS = "LIVE_FYERS"


class BrokerType(Enum):
    MOCK = "MOCK"
    ZERODHA = "ZERODHA"
    UPSTOX = "UPSTOX"
    DHAN = "DHAN"
    ANGELONE = "ANGELONE"
    FYERS = "FYERS"
