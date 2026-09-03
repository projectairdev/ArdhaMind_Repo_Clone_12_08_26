from __future__ import annotations
from enum import Enum


class DataQualityStatus(str, Enum):
    VALID = "VALID"
    DELAYED = "DELAYED"
    STALE = "STALE"
    SESSION_MISMATCH = "SESSION_MISMATCH"
    UNAVAILABLE = "UNAVAILABLE"
    REJECTED = "REJECTED"
    BACKFILLED = "BACKFILLED"


class CandleQuality(str, Enum):
    VALID = "VALID"
    BACKFILLED = "BACKFILLED"
    MISSING = "MISSING"


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"
    NFO = "NFO"
    MCX = "MCX"
    BFO = "BFO"


class Segment(str, Enum):
    INDEX = "INDEX"
    EQUITY = "EQUITY"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"
    COMMODITY = "COMMODITY"
    CURRENCY = "CURRENCY"


class InstrumentType(str, Enum):
    INDEX = "INDEX"
    EQUITY = "EQUITY"
    FUT = "FUT"
    CE = "CE"
    PE = "PE"


class OptionType(str, Enum):
    CE = "CE"
    PE = "PE"


class Timeframe(str, Enum):
    S1 = "1s"
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M60 = "60m"
    D1 = "1D"
