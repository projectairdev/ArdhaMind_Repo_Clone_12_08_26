from __future__ import annotations

from dataclasses import dataclass


from typing import Union

@dataclass
class OptionSignal:
    scanned_at: str
    option_quote_time: str
    underlying_quote_time: str
    market_bias: str
    setup_type: str
    confidence: float

    underlying: str
    underlying_spot: float
    underlying_trigger: float
    trigger_distance_abs: float
    trigger_distance_pct: float

    trend: str
    sector: str
    sector_strength: float
    option_symbol: str
    option_type: str
    strike: float
    expiry: str
    days_to_expiry: int

    option_ltp: float
    option_volume: int
    option_oi: int
    bid_price: float
    ask_price: float
    spread_pct: float
    option_quality_score: float
    lot_size: int
    capital_required: float
    rupee_risk: float
    rupee_reward: float
    reward_risk_ratio: float

    entry_when_underlying: str
    suggested_entry_option: float
    stop_loss_option: float
    target_option: float
    exit_rule: str
    rationale: str
    strategy_regime: str = "SIDEWAYS"
    daily_trend: str = "SIDEWAYS"
    hourly_trend: str = "SIDEWAYS"
    fifteen_min_trend: str = "SIDEWAYS"
    five_min_trend: str = "SIDEWAYS"
    timeframe_alignment_score: float = 0.0
    structure: str = "SIDEWAYS"
    intraday_vwap: float = 0.0
    prev_day_high: float = 0.0
    prev_day_low: float = 0.0
    prev_day_close: float = 0.0
    weekly_high: float = 0.0
    weekly_low: float = 0.0
    stock_vs_nifty_return: float = 0.0
    sector_vs_nifty_return: float = 0.0


@dataclass
class StockSignal:
    scanned_at: str
    quote_time: str
    market_bias: str
    setup_type: str
    confidence: float

    symbol: str
    side: str
    spot_price: float
    trigger_price: float
    trigger_distance_abs: float
    trigger_distance_pct: float

    trend: str
    quantity: int
    capital_required: float
    rupee_risk: float
    rupee_reward: float
    reward_risk_ratio: float

    suggested_entry: float
    stop_loss: float
    target: float
    exit_rule: str
    rationale: str
    strategy_regime: str = "SIDEWAYS"
    daily_trend: str = "SIDEWAYS"
    hourly_trend: str = "SIDEWAYS"
    fifteen_min_trend: str = "SIDEWAYS"
    five_min_trend: str = "SIDEWAYS"
    timeframe_alignment_score: float = 0.0
    structure: str = "SIDEWAYS"
    intraday_vwap: float = 0.0
    prev_day_high: float = 0.0
    prev_day_low: float = 0.0
    prev_day_close: float = 0.0
    weekly_high: float = 0.0
    weekly_low: float = 0.0
    stock_vs_nifty_return: float = 0.0
    sector_vs_nifty_return: float = 0.0


@dataclass
class TradeRecommendation:
    symbol: str
    action: str  # BUY / WATCHLIST / AVOID / SELL
    asset_type: str  # OPTION / STOCK
    primary_signal: OptionSignal | StockSignal | None
    watchlist_signals: list[OptionSignal | StockSignal]
    confidence_score: float
    rationale: str


TradeSignal = Union[OptionSignal, StockSignal]
