from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass(frozen=True)
class PerformanceMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float            # 0.0 to 100.0 or 0.0 to 1.0 (let's use 0.0 to 100.0)
    average_profit: float      # average pnl of winning trades
    average_loss: float        # average pnl of losing trades (negative)
    profit_factor: float       # gross profits / gross losses
    expectancy: float          # average expected outcome per trade
    average_holding_time: float # in seconds
    largest_winner: float      # max positive pnl
    largest_loser: float       # min pnl (most negative)
    maximum_drawdown: float    # peak-to-valley absolute drawdown
    recovery_factor: float     # total_pnl / maximum_drawdown if drawdown > 0 else total_pnl

@dataclass(frozen=True)
class AnalyticsStrategyPerformance:
    strategy_name: str
    total_trades: int
    win_rate: float
    average_return: float      # average pnl of trades under this strategy
    profit_factor: float
    expectancy: float
    capital_utilization: float # average capital allocated per trade

@dataclass(frozen=True)
class AnalyticsRegimePerformance:
    market_regime: str
    total_trades: int
    win_rate: float
    average_return: float      # average pnl of trades
    profit_factor: float
    expectancy: float

@dataclass(frozen=True)
class OpportunityPerformance:
    opportunity_classification: str
    total_trades: int
    win_rate: float
    average_return: float
    profit_factor: float
    expectancy: float

@dataclass(frozen=True)
class GradePerformance:
    market_score_grade: str
    total_trades: int
    win_rate: float
    average_return: float
    profit_factor: float
    expectancy: float

@dataclass(frozen=True)
class BiasPerformance:
    directional_bias: str
    total_trades: int
    win_rate: float
    average_return: float
    profit_factor: float
    expectancy: float

@dataclass(frozen=True)
class MarketPerformance:
    by_regime: List[AnalyticsRegimePerformance] = field(default_factory=list)
    by_opportunity: List[OpportunityPerformance] = field(default_factory=list)
    by_grade: List[GradePerformance] = field(default_factory=list)
    by_bias: List[BiasPerformance] = field(default_factory=list)

@dataclass(frozen=True)
class ConfidencePerformance:
    confidence_band: str  # e.g., "50–60", "60–70", "70–80", "80–90", "90–100"
    total_trades: int
    win_rate: float
    average_return: float

@dataclass(frozen=True)
class RiskPerformance:
    risk_grade: str
    total_trades: int
    win_rate: float
    average_return: float
    capital_allocation_avg: float
    portfolio_utilization: float # average of (entry_capital / total_capital)

@dataclass(frozen=True)
class TimePerformance:
    by_entry_hour: Dict[int, float] = field(default_factory=dict) # hour -> total pnl
    by_day_of_week: Dict[str, float] = field(default_factory=dict) # day -> total pnl
    avg_holding_time: float = 0.0

@dataclass(frozen=True)
class PortfolioPerformance:
    initial_capital: float
    final_capital: float
    total_pnl: float
    return_on_capital: float
    maximum_drawdown: float
    sharpe_ratio: float
    profit_factor: float

@dataclass(frozen=True)
class AnalyticsSummary:
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class AnalyticsReport:
    report_id: str
    overall_metrics: PerformanceMetrics
    strategy_metrics: List[AnalyticsStrategyPerformance]
    market_metrics: MarketPerformance
    confidence_metrics: List[ConfidencePerformance]
    risk_metrics: List[RiskPerformance]
    time_metrics: TimePerformance
    portfolio_metrics: PortfolioPerformance
    summary: AnalyticsSummary
    timestamp: str
