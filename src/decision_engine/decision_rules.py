from __future__ import annotations

from src.models import (
    TradeCandidate,
    CandidateRisk,
    DecisionEngineConfig,
)


def evaluate_candidate_decision(
    candidate: TradeCandidate,
    confidence_score: float,
    risk_cand: CandidateRisk,
    config: DecisionEngineConfig,
) -> str:
    """
    Applies configuration-driven decision rules to map a candidate to one of the supported actions:
    BUY, SELL, WATCH, REJECT, NO TRADE.
    """
    # Rule 1: Risk Engine Rejections
    if risk_cand is None or not risk_cand.is_approved or risk_cand.risk_grade == "REJECTED":
        return "REJECT"

    # Rule 2: Risk Capital Allocation validation
    if risk_cand.capital_allocation.allocated_lots <= 0:
        return "NO TRADE"

    # Rule 3: Below minimum watch threshold
    if confidence_score < config.watch_confidence_threshold:
        return "REJECT"

    # Rule 4: Between WATCH and BUY/SELL threshold
    if confidence_score < config.buy_confidence_threshold:
        return "WATCH"

    # Rule 5: High confidence, determine directional action (BUY vs SELL)
    # If the trade is bearish or instrument is PE, we can trigger a "SELL" action
    # Otherwise, we trigger a "BUY" action.
    if candidate.instrument_type == "PE" or "PE" in candidate.tradingsymbol:
        return "SELL"
    
    return "BUY"
