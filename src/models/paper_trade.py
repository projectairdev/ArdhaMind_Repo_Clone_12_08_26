from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class TradeLifecycle:
    status: str  # "ENTRY", "ACTIVE", "EXITED"
    description: str


@dataclass(frozen=True)
class TradeOutcome:
    outcome: str  # "WIN", "LOSS", "FLAT"
    profit_loss: float


@dataclass(frozen=True)
class PaperTrade:
    trade_id: str
    decision_id: str
    candidate_id: str
    tradingsymbol: str
    entry_time: str
    premium: float
    lots: int
    capital: float
    strategy_name: str
    confidence_score: float
    risk_grade: str
    action: str  # "BUY" or "SELL"


@dataclass(frozen=True)
class PaperPosition:
    position_id: str
    trade: PaperTrade
    current_mtm: float
    peak_mtm: float
    drawdown: float
    holding_time_seconds: float
    status: str  # "OPEN" or "CLOSED"
    current_premium: float


@dataclass(frozen=True)
class TradeJournalEntry:
    entry_id: str
    trade_id: str
    candidate_id: str
    tradingsymbol: str
    decision_summary: str
    explanation_summary: str
    market_score_val: float
    market_score_grade: str
    confidence_score: float
    risk_grade: str
    strategy_name: str
    
    # Entry Details
    entry_time: str
    entry_premium: float
    entry_capital: float
    entry_lots: int
    
    # Exit Details
    exit_time: str
    exit_premium: float
    exit_reason: str  # e.g., "TARGET", "STOP_LOSS", "TIME_EXIT", "EXPIRY_EXIT", "MANUAL", "PLAN_INVALIDATED"
    
    # Metrics
    pnl: float
    pnl_pct: float
    duration_seconds: float
    outcome: str  # "WIN", "LOSS", "FLAT"
    market_regime: str = "VOLATILE"
    confidence_band: str = "MEDIUM"
    notes: str = ""


@dataclass(frozen=True)
class PortfolioSnapshot:
    timestamp: str
    total_capital: float
    allocated_capital: float
    available_capital: float
    open_positions_count: int
    closed_trades_count: int
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float


@dataclass(frozen=True)
class PaperStrategyPerformance:
    strategy_name: str
    total_trades: int
    win_rate: float
    total_pnl: float


@dataclass(frozen=True)
class RegimePerformance:
    market_regime: str
    total_trades: int
    win_rate: float
    total_pnl: float


@dataclass(frozen=True)
class ConfidenceBandPerformance:
    confidence_band: str  # e.g., "HIGH" (>=80), "MEDIUM" (50-79), "LOW" (<50)
    total_trades: int
    win_rate: float
    total_pnl: float


@dataclass(frozen=True)
class PerformanceReport:
    total_trades: int
    win_rate: float
    loss_rate: float
    average_profit: float
    average_loss: float
    profit_factor: float
    expectancy: float
    average_holding_time_seconds: float
    by_strategy: List[PaperStrategyPerformance] = field(default_factory=list)
    by_regime: List[RegimePerformance] = field(default_factory=list)
    by_confidence_band: List[ConfidenceBandPerformance] = field(default_factory=list)
