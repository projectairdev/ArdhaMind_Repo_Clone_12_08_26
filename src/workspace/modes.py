from __future__ import annotations
from enum import Enum, unique

@unique
class MarketDataSource(str, Enum):
    MOCK = "MOCK"
    LIVE = "LIVE"

@unique
class ExecutionMode(str, Enum):
    READ_ONLY = "READ_ONLY"
    MOCK = "MOCK"
    PAPER_EXECUTION = "PAPER_EXECUTION"
    LIVE_BROKER = "LIVE_BROKER"

@unique
class PortfolioSource(str, Enum):
    READ_ONLY_BROKER = "READ_ONLY_BROKER"
    MOCK = "MOCK"
    PAPER_LEDGER = "PAPER_LEDGER"
    BROKER = "BROKER"

@unique
class AnalyticsMode(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"

@unique
class NotificationMode(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
