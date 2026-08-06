from __future__ import annotations

from typing import Dict, Optional
from src.models import (
    TradePlan,
    StrategyEvaluation,
    OptionContext,
    OpportunityContext,
)
from src.planner_engine import (
    CandidateGenerator,
    CandidateFilter,
    CandidateRanker,
    PlannerBuilder,
)
from src.utils import setup_logger

logger = setup_logger("TradePlannerPipeline")


class TradePlannerPipeline:
    """
    Coordinates candidate generation, filtering, ranking, and final
    assembly of the TradePlan based on StrategyEvaluation and OptionContext.
    """

    def __init__(self) -> None:
        pass

    def run(
        self,
        strategy_evaluation: StrategyEvaluation,
        option_context: OptionContext,
        opportunity_context: OpportunityContext,
        weights: Optional[Dict[str, float]] = None,
    ) -> TradePlan:
        logger.info("Executing Trade Planner Pipeline...")

        # 1. Candidate Generation
        raw_candidates = CandidateGenerator.generate_candidates(
            option_context=option_context,
            strategy_evaluation=strategy_evaluation,
        )
        logger.debug(f"Generated {len(raw_candidates)} raw candidate-strategy pairs.")

        # 2. Candidate Filtering
        accepted_candidates, rejected_candidates = CandidateFilter.filter_candidates(
            candidates=raw_candidates,
            opportunity_context=opportunity_context,
            option_context=option_context,
        )
        logger.debug(f"Filtered raw candidates: {len(accepted_candidates)} accepted, {len(rejected_candidates)} rejected.")

        # 3. Candidate Ranking
        ranked_candidates = CandidateRanker.rank_candidates(
            candidates=accepted_candidates,
            option_context=option_context,
            weights=weights,
        )

        # 4. Assembly & Metric Aggregation
        trade_plan = PlannerBuilder.build_trade_plan(
            raw_candidates=raw_candidates,
            accepted_candidates=ranked_candidates,
            rejected_candidates=rejected_candidates,
        )

        logger.info(
            f"TradePlannerPipeline completed successfully. "
            f"Plan ID={trade_plan.trade_plan_id}, "
            f"Accepted={trade_plan.statistics.total_candidates_accepted}, "
            f"Rejected={trade_plan.statistics.total_candidates_rejected}, "
            f"Best Candidate={trade_plan.summary.best_candidate_id}"
        )
        return trade_plan
