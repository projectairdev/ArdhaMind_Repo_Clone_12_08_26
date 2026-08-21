from __future__ import annotations

from typing import Any, Dict, Optional
from src.opportunity_engine.models import CanonicalOpportunity, OpportunityStatus


def select_best_opportunity(
    candidates: list[CanonicalOpportunity],
    market_closed: bool = False
) -> dict[str, Any]:
    """
    Ranks qualified & trade-ready opportunities deterministically.
    If no candidate passes the high-conviction threshold or if market is closed,
    returns a explicit NO_TRADE canonical payload.
    """
    if market_closed:
        return {
            "status": "NO_TRADE",
            "reason": "MARKET_CLOSED",
            "message": "Market is closed. No live opportunity scanning active.",
            "priority_score": 0,
            "quality_score": 0,
            "confidence_score": 0,
        }

    ready_candidates = [
        opp for opp in candidates
        if opp.status == OpportunityStatus.TRADE_READY.value and opp.priority_score >= 65
    ]

    if not ready_candidates:
        # Fall back to best qualified if high quality
        ready_candidates = [
            opp for opp in candidates
            if opp.status == OpportunityStatus.QUALIFIED.value and opp.priority_score >= 70
        ]

    if not ready_candidates:
        return {
            "status": "NO_TRADE",
            "reason": "NO_HIGH_CONVICTION_SETUP",
            "message": "No setup currently meets minimum qualification and priority thresholds (Priority >= 65).",
            "priority_score": 0,
            "quality_score": 0,
            "confidence_score": 0,
        }

    # Rank deterministically by priority_score -> quality_score -> reward_risk_ratio -> confidence_score
    best = max(
        ready_candidates,
        key=lambda x: (x.priority_score, x.quality_score, x.reward_risk_ratio, x.confidence_score)
    )

    return best.to_dict()
