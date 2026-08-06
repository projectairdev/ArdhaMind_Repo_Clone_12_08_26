from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class RiskWarning:
    warning_type: str  # e.g., "MAX_EXPOSURE_EXCEEDED", "SECTOR_CONCENTRATION", etc.
    message: str
    severity: str  # "LOW", "MEDIUM", "HIGH"


@dataclass(frozen=True)
class PortfolioConstraint:
    constraint_type: str  # e.g., "MAX_CONCURRENT_TRADES", "MIN_CONFIDENCE_THRESHOLD", etc.
    limit_value: float
    current_value: float
    is_violated: bool


@dataclass(frozen=True)
class CapitalAllocation:
    allocated_capital: float
    allocated_lots: int
    risk_amount: float
    utilization_pct: float
    confidence_score: float
    risk_multiplier: float


@dataclass(frozen=True)
class CandidateRisk:
    candidate_id: str
    tradingsymbol: str
    strategy_name: str
    risk_grade: str  # "LOW_RISK", "MODERATE_RISK", "HIGH_RISK", "REJECTED"
    capital_allocation: CapitalAllocation
    warnings: List[RiskWarning] = field(default_factory=list)
    constraints: List[PortfolioConstraint] = field(default_factory=list)
    is_approved: bool = True


@dataclass(frozen=True)
class SectorExposureDetail:
    sector_name: str
    allocated_capital: float
    percentage: float


@dataclass(frozen=True)
class DirectionalExposureDetail:
    direction: str  # "BULLISH", "BEARISH", "NEUTRAL"
    allocated_capital: float
    percentage: float


@dataclass(frozen=True)
class ExpiryExposureDetail:
    expiry_date: str
    allocated_capital: float
    percentage: float


@dataclass(frozen=True)
class ExposureSummary:
    total_capital_allocated: float
    portfolio_utilization_pct: float
    sector_exposures: List[SectorExposureDetail] = field(default_factory=list)
    directional_exposures: List[DirectionalExposureDetail] = field(default_factory=list)
    expiry_exposures: List[ExpiryExposureDetail] = field(default_factory=list)
    option_concentration_pct: float = 0.0
    capital_concentration_pct: float = 0.0


@dataclass(frozen=True)
class RiskSummary:
    highest_risk_candidate_id: str
    lowest_risk_candidate_id: str
    portfolio_risk_grade: str  # "CONSERVATIVE", "MODERATE", "AGGRESSIVE", "HIGH_EXPOSURE"
    total_warnings: int
    conclusions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RiskEngineConfig:
    max_capital_per_trade: float = 40000.0
    max_portfolio_exposure: float = 150000.0
    max_daily_exposure: float = 200000.0
    max_concurrent_trades: int = 4
    min_confidence_threshold: float = 50.0  # 0 to 100
    risk_scaling_enabled: bool = True
    total_portfolio_value: float = 500000.0


@dataclass(frozen=True)
class RiskReport:
    report_id: str
    confidence_report_id: str
    candidate_risks: List[CandidateRisk] = field(default_factory=list)
    exposure_summary: ExposureSummary = field(default_factory=lambda: ExposureSummary(0.0, 0.0))
    summary: RiskSummary = field(default_factory=lambda: RiskSummary("NONE", "NONE", "CONSERVATIVE", 0))
    timestamp: str = ""
    schema_version: str = "1.0"
    engine_version: str = "1.0"
