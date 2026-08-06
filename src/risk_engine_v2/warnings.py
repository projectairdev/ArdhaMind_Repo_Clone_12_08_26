from __future__ import annotations

from typing import List
from src.models import (
    RiskWarning,
    ExposureSummary,
    CandidateRisk,
    RiskEngineConfig,
)


def generate_portfolio_warnings(
    exposure: ExposureSummary,
    config: RiskEngineConfig,
) -> List[RiskWarning]:
    """
    Analyzes aggregated portfolio exposure and generates warnings when safety thresholds are breached.
    """
    warnings: List[RiskWarning] = []

    # 1. Total Portfolio Exposure Warning
    if exposure.total_capital_allocated > config.max_portfolio_exposure:
        warnings.append(
            RiskWarning(
                warning_type="PORTFOLIO_EXPOSURE_BREACH",
                message=f"Total allocated capital ({exposure.total_capital_allocated:.2f}) exceeds configured max portfolio exposure ({config.max_portfolio_exposure:.2f})",
                severity="HIGH",
            )
        )
    elif exposure.total_capital_allocated > config.max_portfolio_exposure * 0.85:
        warnings.append(
            RiskWarning(
                warning_type="PORTFOLIO_EXPOSURE_NEAR_LIMIT",
                message=f"Total allocated capital ({exposure.total_capital_allocated:.2f}) is approaching max portfolio exposure limit ({config.max_portfolio_exposure:.2f})",
                severity="MEDIUM",
            )
        )

    # 2. Sector Concentration Warning (> 40% of allocated capital in a single sector)
    for sector in exposure.sector_exposures:
        if sector.percentage > 40.0 and sector.allocated_capital > 0:
            warnings.append(
                RiskWarning(
                    warning_type="SECTOR_CONCENTRATION",
                    message=f"High sector concentration in {sector.sector_name}: {sector.percentage:.1f}% of allocated capital",
                    severity="MEDIUM" if sector.percentage < 60.0 else "HIGH",
                )
            )

    # 3. Directional Concentration Warning (> 70% of allocated capital in one direction)
    for direction in exposure.directional_exposures:
        if direction.percentage > 70.0 and direction.allocated_capital > 0:
            warnings.append(
                RiskWarning(
                    warning_type="DIRECTIONAL_CONCENTRATION",
                    message=f"High directional skew in {direction.direction}: {direction.percentage:.1f}% of allocated capital",
                    severity="HIGH",
                )
            )

    # 4. Capital Concentration Warning (> 50% in a single trade)
    if exposure.capital_concentration_pct > 50.0 and exposure.total_capital_allocated > 0:
        warnings.append(
            RiskWarning(
                warning_type="CAPITAL_CONCENTRATION",
                message=f"A single trade accounts for {exposure.capital_concentration_pct:.1f}% of total allocated capital",
                severity="HIGH",
            )
        )

    # 5. High Portfolio Utilization (> 80% of portfolio value utilized)
    if exposure.portfolio_utilization_pct > 80.0:
        warnings.append(
            RiskWarning(
                warning_type="PORTFOLIO_UTILIZATION_BREACH",
                message=f"Portfolio utilization ({exposure.portfolio_utilization_pct:.1f}%) exceeds safety threshold of 80%",
                severity="HIGH",
            )
        )
    elif exposure.portfolio_utilization_pct > 50.0:
        warnings.append(
            RiskWarning(
                warning_type="PORTFOLIO_UTILIZATION_HIGH",
                message=f"Portfolio utilization is high: {exposure.portfolio_utilization_pct:.1f}% of total portfolio value",
                severity="MEDIUM",
            )
        )

    return warnings


def generate_candidate_warnings(
    candidate_risk: CandidateRisk,
) -> List[RiskWarning]:
    """
    Generates risk warnings for an individual trade candidate based on its properties.
    """
    warnings: List[RiskWarning] = []
    
    # 1. High IV Warning
    if candidate_risk.capital_allocation.allocated_lots > 0:
        if candidate_risk.capital_allocation.confidence_score < 60.0:
            warnings.append(
                RiskWarning(
                    warning_type="MODERATE_CONFIDENCE_WARNING",
                    message=f"Candidate has moderate confidence of {candidate_risk.capital_allocation.confidence_score:.1f}%",
                    severity="LOW",
                )
            )

    return warnings
