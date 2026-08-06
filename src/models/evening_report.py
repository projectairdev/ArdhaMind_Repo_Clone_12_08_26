from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MarketSummary:
    spot_price: float
    vix_price: float
    regime: str
    trend_direction: str
    market_score: float
    market_grade: str
    session_type: str


@dataclass(frozen=True)
class TomorrowOutlook:
    directional_bias: str
    outlook_classification: str
    opportunity_strength: float
    key_support_levels: List[float] = field(default_factory=list)
    key_resistance_levels: List[float] = field(default_factory=list)
    description: str = ""


@dataclass(frozen=True)
class RecommendedStrategy:
    strategy_name: str
    suitability_score: float
    suitability_level: str
    rationale: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RecommendedCandidate:
    candidate_id: str
    tradingsymbol: str
    strategy_name: str
    decision: str
    confidence_score: float
    priority_score: float
    allocated_capital: float
    allocated_lots: int
    strike: float
    instrument_type: str
    expiry: str


@dataclass(frozen=True)
class RejectedCandidate:
    tradingsymbol: str
    strategy_name: str
    reason_type: str
    message: str


@dataclass(frozen=True)
class RiskWatchlist:
    warnings: List[str] = field(default_factory=list)
    portfolio_warnings: List[str] = field(default_factory=list)
    max_capital_limit: float = 0.0
    allocated_capital: float = 0.0
    portfolio_utilization_pct: float = 0.0
    risk_grade: str = "CONSERVATIVE"


@dataclass(frozen=True)
class EventWatchlist:
    events: List[str] = field(default_factory=list)
    expiry_days_remaining: float = 0.0
    expiry_type: str = "NORMAL"


@dataclass(frozen=True)
class PlannerChecklist:
    checklist_items: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReportSummary:
    best_candidate_id: str
    best_strategy: str
    total_accepted_candidates: int
    total_rejected_candidates: int
    action_type: str


@dataclass(frozen=True)
class EveningReport:
    report_id: str
    market_summary: MarketSummary
    tomorrow_outlook: TomorrowOutlook
    recommended_strategies: List[RecommendedStrategy] = field(default_factory=list)
    top_candidates: List[RecommendedCandidate] = field(default_factory=list)
    rejected_candidates: List[RejectedCandidate] = field(default_factory=list)
    risk_watchlist: RiskWatchlist = field(default_factory=RiskWatchlist)
    event_watchlist: EventWatchlist = field(default_factory=EventWatchlist)
    checklist: PlannerChecklist = field(default_factory=PlannerChecklist)
    summary: ReportSummary = field(default_factory=lambda: ReportSummary("NONE", "NONE", 0, 0, "HOLD"))
    timestamp: str = ""
    engine_version: str = "1.0"
    optimization_notes: List[str] = field(default_factory=list)
