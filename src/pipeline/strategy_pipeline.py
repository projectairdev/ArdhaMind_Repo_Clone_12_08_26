from __future__ import annotations

from src.models import (
    TradeContext,
    MarketScore,
    OpportunityContext,
    StrategyEvaluation,
)
from src.strategy_engine.strategy_builder import StrategyEvaluationBuilder
from src.utils import setup_logger

logger = setup_logger("StrategyPipeline")


class StrategyPipeline:
    """
    Stateless pipeline that consumes TradeContext, MarketScore, and OpportunityContext
    to evaluate the suitability of multiple trading strategies.
    """

    def __init__(self) -> None:
        pass

    def run(
        self,
        trade_context: TradeContext,
        market_score: MarketScore,
        opportunity_context: OpportunityContext,
    ) -> StrategyEvaluation:
        logger.info("Initializing NIFTY Strategy Evaluation Pipeline...")
        
        evaluation = StrategyEvaluationBuilder.build(
            trade_context=trade_context,
            market_score=market_score,
            opportunity_context=opportunity_context,
        )
        
        logger.info(
            f"NIFTY StrategyEvaluation completed: BestStrategy={evaluation.overall_best_strategy}, "
            f"SuitableCount={evaluation.summary.suitable_strategies_count}"
        )
        return evaluation
