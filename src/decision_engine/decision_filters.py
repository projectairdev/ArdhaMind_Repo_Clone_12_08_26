from __future__ import annotations

from typing import List
from src.models import (
    CandidateDecision,
    MarketScore,
    OpportunityContext,
)


def check_global_market_blockers(
    market_score: MarketScore,
    opportunity_context: OpportunityContext,
) -> List[str]:
    """
    Evaluates global macro or regime blockers that might prevent any trading.
    Returns a list of blocker messages if any exist.
    """
    blockers = []

    # 1. Extreme low market score
    if market_score.overall_score < 30.0:
        blockers.append(f"Global Market Score is extremely unfavorable: {market_score.overall_score:.1f}")

    # 2. Market readiness failure
    if hasattr(opportunity_context, "readiness") and opportunity_context.readiness is not None:
        if not opportunity_context.readiness.is_market_ready:
            blockers.append("Global Market Readiness status is set to NOT READY.")

    return blockers


def filter_by_decision_type(
    decisions: List[CandidateDecision],
    decision_type: str,
) -> List[CandidateDecision]:
    """
    Filters a list of candidate decisions by their active decision type.
    """
    return [d for d in decisions if d.decision == decision_type]
