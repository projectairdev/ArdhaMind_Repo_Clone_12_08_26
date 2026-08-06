from __future__ import annotations

from typing import Optional
from src.models import (
    TradeContext,
    MarketScore,
    OpportunityContext,
    MarketBreadthContext,
    GlobalContext,
)
from src.opportunity_engine.context_builder import OpportunityContextBuilder
from src.utils import setup_logger

logger = setup_logger("OpportunityPipeline")


class OpportunityPipeline:
    """
    Stateless, modular pipeline that consumes TradeContext and MarketScore,
    optionally incorporating Market Breadth and Global contexts, to evaluate
    and produce the immutable OpportunityContext representing trading opportunities.
    """

    def __init__(self) -> None:
        pass

    def run(
        self,
        trade_context: TradeContext,
        market_score: MarketScore,
        breadth: Optional[MarketBreadthContext] = None,
        global_ctx: Optional[GlobalContext] = None,
    ) -> OpportunityContext:
        logger.info("Initializing NIFTY Opportunity Evaluation Pipeline...")
        
        opportunity_context = OpportunityContextBuilder.build(
            context=trade_context,
            score=market_score,
            breadth=breadth,
            global_ctx=global_ctx,
        )
        
        logger.info(
            f"NIFTY OpportunityContext evaluated successfully: Classification={opportunity_context.classification.value}, "
            f"HasOpportunity={opportunity_context.has_opportunity}, Strength={opportunity_context.strength.overall_strength:.2f}%"
        )
        return opportunity_context
