from __future__ import annotations

from typing import List, Dict
from src.models import (
    CandidateRisk,
    ExposureSummary,
    SectorExposureDetail,
    DirectionalExposureDetail,
    ExpiryExposureDetail,
    RiskEngineConfig,
)
from src.data_engine.instruments import get_symbol_sector


def calculate_portfolio_exposures(
    candidate_risks: List[CandidateRisk],
    config: RiskEngineConfig,
) -> ExposureSummary:
    """
    Aggregates risk and capital exposures across all approved candidate risks.
    """
    approved_risks = [r for r in candidate_risks if r.is_approved]
    total_capital = sum(r.capital_allocation.allocated_capital for r in approved_risks)

    # 1. Sector exposure calculation
    sector_map: Dict[str, float] = {}
    for r in approved_risks:
        sector = get_symbol_sector(r.tradingsymbol) or "OTHER"
        sector_map[sector] = sector_map.get(sector, 0.0) + r.capital_allocation.allocated_capital

    sector_exposures = [
        SectorExposureDetail(
            sector_name=sec,
            allocated_capital=float(round(cap, 2)),
            percentage=float(round((cap / total_capital) * 100.0, 2)) if total_capital > 0 else 0.0,
        )
        for sec, cap in sector_map.items()
    ]
    # Sort sector exposures by allocated capital descending
    sector_exposures.sort(key=lambda x: x.allocated_capital, reverse=True)

    # 2. Directional exposure calculation
    directional_map: Dict[str, float] = {"BULLISH": 0.0, "BEARISH": 0.0, "NEUTRAL": 0.0}
    for r in approved_risks:
        # Check strategy or option type
        if "PE" in r.tradingsymbol or "PE" in r.candidate_id:
            direction = "BEARISH"
        elif "CE" in r.tradingsymbol or "CE" in r.candidate_id:
            direction = "BULLISH"
        else:
            direction = "NEUTRAL"
        directional_map[direction] = directional_map.get(direction, 0.0) + r.capital_allocation.allocated_capital

    directional_exposures = [
        DirectionalExposureDetail(
            direction=dir_name,
            allocated_capital=float(round(cap, 2)),
            percentage=float(round((cap / total_capital) * 100.0, 2)) if total_capital > 0 else 0.0,
        )
        for dir_name, cap in directional_map.items()
    ]

    # 3. Expiry exposure calculation
    expiry_map: Dict[str, float] = {}
    for r in approved_risks:
        # Try to infer expiry date from the trade candidate or code it dynamically
        # Since candidate_risks does not explicitly store expiry, we can infer it or parse it.
        # Let's extract any expiry date or key, we can find it in candidate_id or fallback to standard expiry.
        # Let's search if there's any simple pattern, but if we have the candidate objects we can pass them or parse from id.
        parts = r.candidate_id.split("_")
        expiry = "WEEKLY"
        if len(parts) > 1:
            # Let's see if we can find something like NIFTY26OCT24 or similar,
            # or we can pass the actual expiry of the candidate. To keep it simple,
            # let's map by tradingsymbol's expiry if we have it, otherwise "FRONT_MONTH".
            expiry = r.candidate_id.split("_")[-1]  # or tradingsymbol
        expiry_map[expiry] = expiry_map.get(expiry, 0.0) + r.capital_allocation.allocated_capital

    expiry_exposures = [
        ExpiryExposureDetail(
            expiry_date=exp_date,
            allocated_capital=float(round(cap, 2)),
            percentage=float(round((cap / total_capital) * 100.0, 2)) if total_capital > 0 else 0.0,
        )
        for exp_date, cap in expiry_map.items()
    ]

    # 4. Option Concentration
    # Since these are all options, option concentration is 100.0% of allocated capital
    option_concentration_pct = 100.0 if total_capital > 0 else 0.0

    # 5. Capital Concentration
    max_single_allocation = max([r.capital_allocation.allocated_capital for r in approved_risks]) if approved_risks else 0.0
    capital_concentration_pct = float(round((max_single_allocation / total_capital) * 100.0, 2)) if total_capital > 0 else 0.0

    portfolio_utilization_pct = float(round((total_capital / config.total_portfolio_value) * 100.0, 4)) if config.total_portfolio_value > 0 else 0.0

    return ExposureSummary(
        total_capital_allocated=float(round(total_capital, 2)),
        portfolio_utilization_pct=portfolio_utilization_pct,
        sector_exposures=sector_exposures,
        directional_exposures=directional_exposures,
        expiry_exposures=expiry_exposures,
        option_concentration_pct=option_concentration_pct,
        capital_concentration_pct=capital_concentration_pct,
    )
