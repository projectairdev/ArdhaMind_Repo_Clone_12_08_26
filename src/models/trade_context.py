from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from src.models.market_context import MarketContext
from src.models.option_context import OptionContext


@dataclass(frozen=True)
class SessionContext:
    session_type: str  # "MARKET_OPEN", "MORNING", "MID_SESSION", "AFTERNOON", "CLOSING_SESSION", "POST_MARKET", "HOLIDAY", "WEEKEND", "HALF_DAY"
    is_tradable_time: bool
    time_of_day: str
    is_weekend: bool
    is_holiday: bool
    is_half_day: bool


@dataclass(frozen=True)
class ExpiryContext:
    expiry_date: str
    days_remaining: int
    expiry_type: str  # "WEEKLY", "MONTHLY"
    is_expiry_day: bool
    is_expiry_eve: bool
    is_far_expiry: bool
    classification: str  # "WEEKLY_EXPIRY", "MONTHLY_EXPIRY", "EXPIRY_EVE", "EXPIRY_DAY", "FAR_EXPIRY"


@dataclass(frozen=True)
class MarketReadiness:
    is_market_ready: bool
    suitability_score: float
    reasons: List[str] = field(default_factory=list)
    session_suitable: bool = False
    volatility_suitable: bool = False
    liquidity_suitable: bool = False
    trend_suitable: bool = False


@dataclass(frozen=True)
class ConfluenceContext:
    trend_confluence: bool
    option_confluence: bool
    sr_alignment: bool
    volatility_alignment: bool
    liquidity_alignment: bool
    overall_confluence: bool
    description: str


@dataclass(frozen=True)
class TradeContext:
    market: MarketContext
    options: OptionContext
    session: SessionContext
    expiry: ExpiryContext
    confluence: ConfluenceContext
    readiness: MarketReadiness
    timestamp: str
    schema_version: str = "1.0"
    pipeline_version: str = "1.0"
