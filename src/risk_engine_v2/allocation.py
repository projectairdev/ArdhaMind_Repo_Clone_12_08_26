from __future__ import annotations

import math
from src.models import (
    TradeCandidate,
    OptionContext,
    CapitalAllocation,
    RiskEngineConfig,
)


def get_option_premium(candidate: TradeCandidate, option_context: OptionContext) -> float:
    """
    Retrieves or estimates the premium for an option candidate.
    First tries to look up in option_context.top_candidate_strikes, then falls back to a realistic estimation.
    """
    for strike_dict in option_context.top_candidate_strikes:
        if strike_dict.get("tradingsymbol") == candidate.tradingsymbol:
            for field_name in ["option_ltp", "ltp", "ask_price", "bid_price", "price"]:
                if field_name in strike_dict and strike_dict[field_name] is not None:
                    val = float(strike_dict[field_name])
                    if val > 0:
                        return val

    for strike_dict in option_context.top_candidate_strikes:
        if (
            abs(float(strike_dict.get("strike", 0.0)) - candidate.strike) < 0.01
            and strike_dict.get("instrument_type") == candidate.instrument_type
        ):
            for field_name in ["option_ltp", "ltp", "ask_price", "bid_price", "price"]:
                if field_name in strike_dict and strike_dict[field_name] is not None:
                    val = float(strike_dict[field_name])
                    if val > 0:
                        return val

    # Mathematical fallback based on spot price and ATM distance
    spot = option_context.underlying_spot if option_context.underlying_spot > 0 else candidate.strike
    if spot <= 0:
        return 0.0

    base_premium = spot * 0.008  # roughly 195 for NIFTY at 24300
    dist_pct = candidate.distance_from_atm / spot
    decay = math.exp(-15.0 * dist_pct)
    premium = max(10.0, base_premium * decay)
    return float(round(premium, 2))


def get_option_lot_size(candidate: TradeCandidate, option_context: OptionContext) -> int:
    """
    Determines the lot size for the given candidate.
    """
    for strike_dict in option_context.top_candidate_strikes:
        if strike_dict.get("tradingsymbol") == candidate.tradingsymbol:
            if "lot_size" in strike_dict and strike_dict["lot_size"] is not None:
                return int(strike_dict["lot_size"])

    sym = candidate.tradingsymbol.upper()
    if "BANKNIFTY" in sym:
        return 15
    elif "FINNIFTY" in sym:
        return 40
    elif "MIDCPNIFTY" in sym:
        return 75
    else:
        return 50  # standard default for NIFTY


def calculate_allocation(
    candidate: TradeCandidate,
    confidence_score: float,
    option_context: OptionContext,
    config: RiskEngineConfig,
) -> CapitalAllocation:
    """
    Determines capital allocation and recommended lot count for a single trade candidate.
    """
    premium = get_option_premium(candidate, option_context)
    lot_size = get_option_lot_size(candidate, option_context)
    cost_per_lot = premium * lot_size

    # Scale the maximum capital by the confidence multiplier if scaling is enabled
    multiplier = (confidence_score / 100.0) if config.risk_scaling_enabled else 1.0
    scaled_max_capital = config.max_capital_per_trade * multiplier

    # Option lots must be non-negative integers
    allocated_lots = int(scaled_max_capital // cost_per_lot) if cost_per_lot > 0 else 0
    allocated_capital = float(allocated_lots * cost_per_lot)

    # Option premium is the total risk of the trade
    risk_amount = allocated_capital
    utilization_pct = (allocated_capital / config.total_portfolio_value) * 100.0 if config.total_portfolio_value > 0 else 0.0

    return CapitalAllocation(
        allocated_capital=float(round(allocated_capital, 2)),
        allocated_lots=allocated_lots,
        risk_amount=float(round(risk_amount, 2)),
        utilization_pct=float(round(utilization_pct, 4)),
        confidence_score=confidence_score,
        risk_multiplier=float(round(multiplier, 4)),
    )


def determine_risk_grade(
    candidate: TradeCandidate,
    allocation: CapitalAllocation,
    is_approved: bool,
) -> str:
    """
    Assigns a risk grade ("LOW_RISK", "MODERATE_RISK", "HIGH_RISK", "REJECTED") to the candidate.
    """
    if not is_approved:
        return "REJECTED"

    if allocation.utilization_pct > 8.0 or candidate.iv > 30.0:
        return "HIGH_RISK"
    elif allocation.utilization_pct > 4.0 or candidate.iv > 20.0:
        return "MODERATE_RISK"
    else:
        return "LOW_RISK"
