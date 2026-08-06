from __future__ import annotations

from typing import Dict, Optional
from src.models import (
    TradePlan,
    StrategyEvaluation,
    OpportunityContext,
    MarketScore,
    ConfidenceReport,
)
from src.confidence_engine import ConfidenceBuilder
from src.utils import setup_logger

logger = setup_logger("ConfidencePipeline")


class ConfidencePipeline:
    """
    Coordinates independent confidence evaluation for every TradeCandidate
    present within an active TradePlan, producing a comprehensive ConfidenceReport.
    """

    def __init__(self) -> None:
        pass

    def run(
        self,
        trade_plan: TradePlan,
        strategy_evaluation: StrategyEvaluation,
        opportunity_context: OpportunityContext,
        market_score: MarketScore,
        weights: Optional[Dict[str, float]] = None,
    ) -> ConfidenceReport:
        logger.info(f"Executing Confidence Pipeline for TradePlan ID={trade_plan.trade_plan_id}...")

        # Build Confidence Report
        confidence_report = ConfidenceBuilder.evaluate_all(
            trade_plan=trade_plan,
            strategy_evaluation=strategy_evaluation,
            opportunity_context=opportunity_context,
            market_score=market_score,
            weights=weights,
        )

        logger.info(
            f"ConfidencePipeline executed successfully. "
            f"Report ID={confidence_report.report_id}, "
            f"Evaluated Candidates Count={confidence_report.summary.total_evaluated}, "
            f"Highest Confidence Candidate={confidence_report.summary.highest_confidence_candidate_id}"
        )
        return confidence_report
