from __future__ import annotations

from typing import List, Tuple
from src.models import (
    TradeCandidate,
    PortfolioConstraint,
    RiskEngineConfig,
)


def evaluate_candidate_constraints(
    candidate: TradeCandidate,
    confidence_score: float,
    allocated_capital: float,
    config: RiskEngineConfig,
) -> Tuple[List[PortfolioConstraint], bool]:
    """
    Evaluates individual constraints on a trade candidate.
    Returns a list of PortfolioConstraint objects and an approval boolean.
    """
    constraints: List[PortfolioConstraint] = []
    is_approved = True

    # 1. Minimum Confidence Threshold Constraint
    conf_violated = confidence_score < config.min_confidence_threshold
    constraints.append(
        PortfolioConstraint(
            constraint_type="MIN_CONFIDENCE_THRESHOLD",
            limit_value=float(config.min_confidence_threshold),
            current_value=float(confidence_score),
            is_violated=conf_violated,
        )
    )
    if conf_violated:
        is_approved = False

    # 2. Maximum Capital Per Trade Constraint
    cap_violated = allocated_capital > config.max_capital_per_trade
    constraints.append(
        PortfolioConstraint(
            constraint_type="MAX_CAPITAL_PER_TRADE",
            limit_value=float(config.max_capital_per_trade),
            current_value=float(allocated_capital),
            is_violated=cap_violated,
        )
    )
    # Note: Even if cap_violated, we might scale/cap it, but we can flag it.

    # 3. Spread constraint (liquidity warning constraint)
    # Max spread threshold is typically 0.5% for highly liquid, let's say 1.0% is a constraint
    spread_limit = 1.0
    spread_violated = candidate.spread_pct > spread_limit
    constraints.append(
        PortfolioConstraint(
            constraint_type="SPREAD_LIMIT",
            limit_value=spread_limit,
            current_value=float(candidate.spread_pct),
            is_violated=spread_violated,
        )
    )

    return constraints, is_approved
