from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from src.opportunity_engine.domain import CanonicalOpportunity, OpportunityStatus


class ContinuousReEvaluator:
    """
    Evaluates active opportunities against current canonical market state,
    handling state transitions, invalidations, and transition history recording.
    """

    @staticmethod
    def re_evaluate(
        opp: CanonicalOpportunity,
        current_spot: float,
        freshness_state: str,
        market_state: str,
        state_sequence: int,
        timestamp: str,
    ) -> CanonicalOpportunity:
        prev_status = opp.status

        # 1. Invalidation Check (Price breaching invalidation level)
        if opp.direction == "BULLISH" and current_spot > 0 and opp.invalidation_level > 0:
            if current_spot <= opp.invalidation_level:
                opp.status = OpportunityStatus.INVALIDATED.value
                opp.status_reason = f"PRICE_INVALIDATED: Spot ({current_spot:.1f}) breached invalidation level ({opp.invalidation_level:.1f})"
                opp.invalidated_at = timestamp

        elif opp.direction == "BEARISH" and current_spot > 0 and opp.invalidation_level > 0:
            if current_spot >= opp.invalidation_level:
                opp.status = OpportunityStatus.INVALIDATED.value
                opp.status_reason = f"PRICE_INVALIDATED: Spot ({current_spot:.1f}) breached invalidation level ({opp.invalidation_level:.1f})"
                opp.invalidated_at = timestamp

        # 2. Market Stale Data Check
        if freshness_state == "STALE" and opp.status == OpportunityStatus.TRADE_READY.value:
            opp.status = OpportunityStatus.WATCHING.value
            opp.status_reason = "MARKET_DATA_STALE: Paused trade-readiness due to stale data feeds"

        # 3. Market Closed Check
        if market_state in ("CLOSED", "MARKET_CLOSED", "HOLIDAY", "WEEKEND") and opp.status in (
            OpportunityStatus.TRADE_READY.value,
            OpportunityStatus.QUALIFIED.value,
            OpportunityStatus.WATCHING.value,
        ):
            opp.status = OpportunityStatus.EXPIRED.value
            opp.status_reason = "SESSION_COMPLETE: Market session closed"

        # Record status transition if changed
        if opp.status != prev_status:
            opp.updated_at = timestamp
            opp.state_sequence = state_sequence
            opp.transition_history.append({
                "timestamp": timestamp,
                "previous_status": prev_status,
                "new_status": opp.status,
                "reason": opp.status_reason,
                "state_sequence": state_sequence,
            })

        return opp
