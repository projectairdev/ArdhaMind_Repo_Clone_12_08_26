from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass(frozen=True)
class StrategyPerformance:
    strategy_name: str
    total_candidates: int
    buy_count: int
    sell_count: int
    watch_count: int
    reject_count: int
    no_trade_count: int
    avg_confidence_score: float


@dataclass(frozen=True)
class DecisionPerformance:
    decision_type: str  # "BUY", "SELL", "WATCH", "REJECT", "NO TRADE"
    count: int
    percentage: float
    avg_confidence: float
    avg_allocated_capital: float


@dataclass(frozen=True)
class ConfidenceStatistics:
    avg_confidence: float
    max_confidence: float
    min_confidence: float
    std_confidence: float


@dataclass(frozen=True)
class RiskStatistics:
    avg_allocated_capital: float
    total_allocated_capital: float
    max_allocated_capital: float
    approved_count: int
    rejected_count: int


@dataclass(frozen=True)
class OutcomeValidation:
    evaluation_window: str  # "Same-day", "Next-day", "Expiry-day"
    success_count: int
    failure_count: int
    accuracy_pct: float
    total_profit_loss: float


@dataclass(frozen=True)
class DailyValidation:
    date: str
    market_score: float
    candidates_count: int
    buy_count: int
    sell_count: int
    watch_count: int
    reject_count: int
    no_trade_count: int
    total_allocated_capital: float
    decision_report_id: str
    outcome_summary: str  # Description of validation outcome for this day


@dataclass(frozen=True)
class SummaryStatistics:
    total_days_evaluated: int
    total_candidates_evaluated: int
    overall_buy_count: int
    overall_sell_count: int
    overall_watch_count: int
    overall_reject_count: int
    overall_no_trade_count: int
    decision_frequency_pct: float  # (BUY + SELL) / total_candidates
    avg_market_score: float


@dataclass(frozen=True)
class ValidationReport:
    report_id: str
    daily_validations: List[DailyValidation] = field(default_factory=list)
    strategy_performances: List[StrategyPerformance] = field(default_factory=list)
    decision_performances: List[DecisionPerformance] = field(default_factory=list)
    confidence_stats: ConfidenceStatistics = field(
        default_factory=lambda: ConfidenceStatistics(0.0, 0.0, 0.0, 0.0)
    )
    risk_stats: RiskStatistics = field(
        default_factory=lambda: RiskStatistics(0.0, 0.0, 0.0, 0, 0)
    )
    outcome_validations: List[OutcomeValidation] = field(default_factory=list)
    summary_stats: SummaryStatistics = field(
        default_factory=lambda: SummaryStatistics(0, 0, 0, 0, 0, 0, 0, 0.0, 0.0)
    )
    timestamp: str = ""
    schema_version: str = "1.0"
    engine_version: str = "1.0"
