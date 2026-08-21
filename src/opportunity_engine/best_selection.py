from __future__ import annotations

from typing import Any, Dict, List, Optional
from src.opportunity_engine.domain import CanonicalOpportunity, OpportunityStatus


class BestOpportunitySelector:
    """
    Deterministically ranks active candidates and selects the single best
    TRADE_READY opportunity, or returns an explicit NO_TRADE state.
    """

    @staticmethod
    def select_best(
        trade_ready_opportunities: List[CanonicalOpportunity],
        watching_opportunities: List[CanonicalOpportunity],
        market_state: str = "LIVE",
    ) -> Dict[str, Any]:
        if market_state in ("CLOSED", "MARKET_CLOSED", "HOLIDAY", "WEEKEND"):
            return {
                "has_trade": False,
                "reason": "MARKET_CLOSED",
                "message": "MARKET CLOSED — Live opportunity scanning is paused.",
                "opportunity": None,
            }

        if not trade_ready_opportunities:
            watching_count = len(watching_opportunities)
            message = (
                f"NO HIGH-QUALITY TRADE RIGHT NOW: {watching_count} candidate(s) watching, but risk/reward or confidence thresholds not met."
                if watching_count > 0
                else "NO HIGH-QUALITY TRADE RIGHT NOW: Market structure neutral; no actionable setup detected."
            )
            return {
                "has_trade": False,
                "reason": "THRESHOLD_NOT_MET",
                "message": message,
                "opportunity": None,
            }

        # Deterministic sorting formula:
        # Sort by priority_score descending, then quality_score descending, then R:R descending
        sorted_candidates = sorted(
            trade_ready_opportunities,
            key=lambda opp: (
                opp.priority_score,
                opp.quality_score,
                opp.confidence_score,
                opp.reward_risk_ratio,
            ),
            reverse=True,
        )

        best = sorted_candidates[0]

        return {
            "has_trade": True,
            "reason": "HIGH_CONVICTION_QUALIFIED",
            "message": f"{best.setup_type} setup in NIFTY ({best.direction}) with {best.confidence_score:.0f}% confidence",
            "opportunity": best.to_dict(),
        }
