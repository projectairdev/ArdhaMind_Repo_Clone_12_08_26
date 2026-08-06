from __future__ import annotations

from typing import List, Tuple
from src.models import PlanStatus, MarketChange, CandidateStatusReport, CandidateStatus


def validate_plan(
    market_changes: List[MarketChange],
    candidate_changes: List[CandidateStatusReport],
) -> Tuple[PlanStatus, List[str]]:
    reasons = []
    is_invalidated = False
    needs_review = False

    # 1. Analyze Market Changes
    trend_reversed = False
    regime_shifted = False
    spot_gap_large = False
    vix_spike = False
    support_breached = False
    resistance_breached = False
    pcr_shifted = False

    for change in market_changes:
        if change.metric_name == "TREND_DIRECTION" and change.is_significant:
            trend_reversed = True
            reasons.append(f"Trend reversed from '{change.previous_value}' to '{change.current_value}'.")
        elif change.metric_name == "MARKET_REGIME" and change.is_significant:
            regime_shifted = True
            reasons.append(f"Regime shifted from '{change.previous_value}' to '{change.current_value}'.")
        elif change.metric_name == "SPOT_PRICE" and change.is_significant:
            spot_gap_large = True
            reasons.append(f"Significant price gap of {change.change_pct:+.2f}% detected.")
        elif change.metric_name == "INDIA_VIX" and change.is_significant:
            vix_spike = True
            reasons.append(f"India VIX shifted significantly to {change.current_value:.2f}.")
        elif change.metric_name == "SUPPORT_BREACH":
            support_breached = True
            reasons.append(f"Key support level at {change.previous_value:,.2f} was breached.")
        elif change.metric_name == "RESISTANCE_BREACH":
            resistance_breached = True
            reasons.append(f"Key resistance level at {change.previous_value:,.2f} was breached.")
        elif change.metric_name == "PCR" and change.is_significant:
            pcr_shifted = True
            reasons.append(f"Significant Put-Call Ratio (PCR) sentiment shift from {change.previous_value:.2f} to {change.current_value:.2f}.")

    # 2. Analyze Candidate Changes
    total_candidates = len(candidate_changes)
    invalidated_candidates = [c for c in candidate_changes if c.status == CandidateStatus.INVALIDATED]
    weakened_candidates = [c for c in candidate_changes if c.status == CandidateStatus.WEAKENED]

    # Invalidation rules
    if trend_reversed:
        is_invalidated = True
        reasons.append("Plan Invalidated: Critical trend reversal directly violates core strategy assumptions.")

    if total_candidates > 0 and len(invalidated_candidates) == total_candidates:
        is_invalidated = True
        reasons.append("Plan Invalidated: 100% of planned trade candidates have been rejected or invalidated.")

    # Needs Review rules
    if not is_invalidated:
        if regime_shifted:
            needs_review = True
            reasons.append("Plan Needs Review: Market regime changed, which might affect strategy suitability.")

        if spot_gap_large:
            needs_review = True
            reasons.append("Plan Needs Review: Large opening gap requires confirmation of breakout/reversal boundaries.")

        if vix_spike:
            needs_review = True
            reasons.append("Plan Needs Review: High volatility/VIX spikes may widen bid-ask spreads and increase slippage.")

        if pcr_shifted:
            needs_review = True
            reasons.append("Plan Needs Review: Options PCR shift suggests overnight sentiment realignment.")

        if support_breached or resistance_breached:
            needs_review = True
            reasons.append("Plan Needs Review: Major S/R levels breached, invalidating specific range S/R trade setups.")

        if total_candidates > 0 and 0 < len(invalidated_candidates) < total_candidates:
            needs_review = True
            reasons.append(f"Plan Needs Review: {len(invalidated_candidates)} out of {total_candidates} candidates were invalidated.")

        if len(weakened_candidates) > 0:
            needs_review = True
            reasons.append(f"Plan Needs Review: {len(weakened_candidates)} candidates show weakened confidence or downgraded decisions.")

    # Determine overall status
    if is_invalidated:
        status = PlanStatus.INVALIDATED
    elif needs_review:
        status = PlanStatus.NEEDS_REVIEW
    else:
        status = PlanStatus.VALID
        reasons.append("Plan Still Valid: Today's live market parameters remain highly aligned with yesterday's Evening Plan.")

    return status, reasons
