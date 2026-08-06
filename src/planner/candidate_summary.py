from __future__ import annotations

from typing import List, Dict
from src.models.decision_report import DecisionReport
from src.models.confidence_report import ConfidenceReport
from src.models.trade_plan import TradePlan
from src.models.evening_report import RecommendedCandidate, RejectedCandidate


def compile_recommended_candidates(
    decision_report: DecisionReport,
    confidence_report: ConfidenceReport,
    trade_plan: TradePlan,
) -> List[RecommendedCandidate]:
    # Create lookup dictionaries
    confidence_map: Dict[str, float] = {}
    if confidence_report and confidence_report.candidate_confidences:
        confidence_map = {
            c.candidate_id: c.confidence_score
            for c in confidence_report.candidate_confidences
        }

    candidate_map = {}
    if trade_plan and trade_plan.accepted_candidates:
        candidate_map = {
            c.candidate_id: c for c in trade_plan.accepted_candidates
        }

    recommended = []
    if not decision_report or not decision_report.candidate_decisions:
        return recommended

    # Filter for executable/watch/buy/sell/no trade decisions
    valid_decisions = [
        d
        for d in decision_report.candidate_decisions
        if d.decision in ("BUY", "SELL", "WATCH", "NO TRADE")
    ]

    # Sort by priority_score descending (highest priority score is best)
    sorted_decisions = sorted(
        valid_decisions, key=lambda d: d.priority_score, reverse=True
    )

    for d in sorted_decisions:
        cand_info = candidate_map.get(d.candidate_id)
        strike = cand_info.strike if cand_info else 0.0
        instrument_type = cand_info.instrument_type if cand_info else ""
        expiry = cand_info.expiry if cand_info else ""

        confidence_score = confidence_map.get(d.candidate_id, 0.0)

        recommended.append(
            RecommendedCandidate(
                candidate_id=d.candidate_id,
                tradingsymbol=d.tradingsymbol,
                strategy_name=d.strategy_name,
                decision=d.decision,
                confidence_score=confidence_score,
                priority_score=d.priority_score,
                allocated_capital=d.allocated_capital,
                allocated_lots=d.allocated_lots,
                strike=strike,
                instrument_type=instrument_type,
                expiry=expiry,
            )
        )

    # Return top 5
    return recommended[:5]


def compile_rejected_candidates(
    trade_plan: TradePlan, decision_report: DecisionReport | None = None
) -> List[RejectedCandidate]:
    rejected = []
    if trade_plan and trade_plan.rejected_candidates:
        for r in trade_plan.rejected_candidates:
            rejected.append(
                RejectedCandidate(
                    tradingsymbol=r.tradingsymbol,
                    strategy_name=r.strategy_name,
                    reason_type=r.reason_type,
                    message=r.message,
                )
            )

    # Also check decision_report for candidates with "REJECT" decision
    if decision_report and decision_report.candidate_decisions:
        for d in decision_report.candidate_decisions:
            if d.decision == "REJECT":
                # Avoid duplicates
                exists = any(
                    rj.tradingsymbol == d.tradingsymbol
                    and rj.strategy_name == d.strategy_name
                    for rj in rejected
                )
                if not exists:
                    blocking_reason = "DECISION_REJECT"
                    blocking_msg = d.explanation
                    if d.blocking_factors:
                        blocking_reason = d.blocking_factors[0].reason_type
                        blocking_msg = d.blocking_factors[0].message
                    rejected.append(
                        RejectedCandidate(
                            tradingsymbol=d.tradingsymbol,
                            strategy_name=d.strategy_name,
                            reason_type=blocking_reason,
                            message=blocking_msg,
                        )
                    )
    return rejected
