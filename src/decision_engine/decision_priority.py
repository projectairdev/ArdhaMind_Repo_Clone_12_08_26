from __future__ import annotations

from typing import List, Tuple
from src.models import (
    CandidateDecision,
    DecisionEngineConfig,
)


def calculate_priority_score(
    confidence_score: float,
    tradability_score: float,
    allocated_capital: float,
    config: DecisionEngineConfig,
) -> float:
    """
    Computes a deterministic priority score for ranking.
    """
    if config.tie_breaker_metric == "ALLOCATED_CAPITAL":
        return float(allocated_capital)
    elif config.tie_breaker_metric == "TRA_SCORE":
        return float(tradability_score)
    else:  # DEFAULT: CONFIDENCE_SCORE
        # Weighted combination of confidence score (80%) and tradability (20%)
        return float(confidence_score * 0.8 + tradability_score * 0.2)


def assign_execution_priorities(
    decisions: List[CandidateDecision],
    config: DecisionEngineConfig,
) -> List[CandidateDecision]:
    """
    Sorts and ranks executable decisions (BUY, SELL) and assigns 1-based execution priority.
    Applies the deterministic tie-breaker.
    If the number of executable candidates exceeds max_execution_slots,
    downgrades the overflow candidates to WATCH or NO TRADE with updated reasons/decisions.
    """
    # 1. Separate decisions by type
    executable = [d for d in decisions if d.decision in ("BUY", "SELL")]
    non_executable = [d for d in decisions if d.decision not in ("BUY", "SELL")]

    # 2. Sort executable decisions: priority_score DESC, then candidate_id ASC (tie-breaker)
    # Python's Timsort is stable: sort by primary key (candidate_id) ascending first,
    # then by secondary key (priority_score) descending.
    executable.sort(key=lambda d: d.candidate_id)
    executable.sort(key=lambda d: d.priority_score, reverse=True)

    final_decisions: List[CandidateDecision] = []
    
    for idx, d in enumerate(executable):
        rank = idx + 1
        if rank <= config.max_execution_slots:
            # Fully approved for execution
            updated_d = CandidateDecision(
                candidate_id=d.candidate_id,
                tradingsymbol=d.tradingsymbol,
                strategy_name=d.strategy_name,
                decision=d.decision,
                priority_score=d.priority_score,
                execution_priority=rank,
                explanation=f"{d.decision} execution approved. Rank {rank} priority slot.",
                supporting_evidence=d.supporting_evidence,
                blocking_factors=d.blocking_factors,
                warnings=d.warnings,
                allocated_capital=d.allocated_capital,
                allocated_lots=d.allocated_lots,
            )
            final_decisions.append(updated_d)
        else:
            # Downgraded because execution slots are full
            from src.models import DecisionReason
            new_blocking = list(d.blocking_factors)
            new_blocking.append(
                DecisionReason(
                    reason_type="EXECUTION_SLOTS_FULL",
                    message=f"Execution slots are full (limit: {config.max_execution_slots}). Trade downgraded to WATCH.",
                    metric_name="max_execution_slots",
                    metric_value=float(config.max_execution_slots),
                )
            )
            updated_d = CandidateDecision(
                candidate_id=d.candidate_id,
                tradingsymbol=d.tradingsymbol,
                strategy_name=d.strategy_name,
                decision="WATCH",  # Downgrade to WATCH
                priority_score=d.priority_score,
                execution_priority=-1,
                explanation="Trade downgraded to WATCH because maximum portfolio execution slots were exceeded.",
                supporting_evidence=d.supporting_evidence,
                blocking_factors=new_blocking,
                warnings=d.warnings,
                allocated_capital=d.allocated_capital,
                allocated_lots=d.allocated_lots,
            )
            final_decisions.append(updated_d)

    # 3. Add non-executable back with -1 execution priority
    for d in non_executable:
        final_decisions.append(d)

    return final_decisions
