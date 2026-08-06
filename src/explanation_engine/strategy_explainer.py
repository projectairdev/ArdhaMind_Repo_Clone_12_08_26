from __future__ import annotations

from typing import Optional, List
from src.models import StrategyEvaluation, OpportunityContext, MarketScore, StrategyExplanation


def explain_strategy(
    strategy_evaluation: Optional[StrategyEvaluation],
    opportunity: Optional[OpportunityContext] = None,
    market_score: Optional[MarketScore] = None,
) -> StrategyExplanation:
    """
    Explains the strategy recommendation by detailing suitability scores,
    comparing them, and explaining why the best overall strategy is chosen.
    """
    if not strategy_evaluation:
        return StrategyExplanation(
            overall_best_strategy="N/A",
            strategy_reasoning="No active strategy evaluation available to explain.",
            all_strategy_scores=[],
        )

    best_strat = strategy_evaluation.overall_best_strategy
    conclusions = strategy_evaluation.summary.conclusions

    all_scores: List[str] = []
    for es in strategy_evaluation.evaluations:
        all_scores.append(f"{es.strategy_name}: Score {es.suitability_score:.1f} ({es.suitability_level})")

    # Find the top evaluation details
    best_score_detail = None
    for es in strategy_evaluation.evaluations:
        if es.strategy_name == best_strat:
            best_score_detail = es
            break

    reasoning = (
        f"The system designated '{best_strat}' as the overall best trading strategy. "
    )

    if best_score_detail:
        reasoning += (
            f"This strategy scored {best_score_detail.suitability_score:.1f} ({best_score_detail.suitability_level} suitability). "
        )
        met_conds = best_score_detail.required_conditions_met
        reasons = [r.message for r in best_score_detail.reasons]
        if reasons:
            reasoning += "Key suitability drivers: " + "; ".join(reasons) + ". "
        if met_conds:
            reasoning += "Required conditions met: " + ", ".join(met_conds) + ". "

    # Integrate Market Context and Opportunity Context if provided
    if market_score or opportunity:
        ctx_desc = []
        if market_score:
            ctx_desc.append(f"market score of {market_score.overall_score:.1f} (Grade {market_score.letter_grade})")
        if opportunity:
            ctx_desc.append(f"opportunity bias of {opportunity.directional_bias.value} with {opportunity.classification.value} classification")
        
        reasoning += "This selection aligns with a " + " and ".join(ctx_desc) + ". "

    if conclusions:
        reasoning += "Evaluation summary conclusions: " + " ".join(conclusions)

    return StrategyExplanation(
        overall_best_strategy=best_strat,
        strategy_reasoning=reasoning,
        all_strategy_scores=all_scores,
    )
