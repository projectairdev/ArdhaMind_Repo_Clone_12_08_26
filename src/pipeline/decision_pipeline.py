from __future__ import annotations

from typing import Optional
from src.models import (
    RiskReport,
    ConfidenceReport,
    TradePlan,
    StrategyEvaluation,
    OpportunityContext,
    MarketScore,
    DecisionEngineConfig,
    DecisionReport,
)
from src.decision_engine import DecisionBuilder
from src.utils import setup_logger

logger = setup_logger("DecisionPipeline")


class DecisionPipeline:
    """
    Coordinates decision evaluations for all candidates based on the risk-safe CandidateRisks
    and produces a final, immutable DecisionReport.
    """

    def __init__(self) -> None:
        pass

    def run(
        self,
        risk_report: RiskReport,
        confidence_report: ConfidenceReport,
        trade_plan: TradePlan,
        strategy_evaluation: StrategyEvaluation,
        opportunity_context: OpportunityContext,
        market_score: Optional[MarketScore] = None,
        config: Optional[DecisionEngineConfig] = None,
    ) -> DecisionReport:
        logger.info(f"Executing Decision Pipeline for RiskReport ID={risk_report.report_id}...")

        # Build Decision Report
        decision_report = DecisionBuilder.build_decision_report(
            risk_report=risk_report,
            confidence_report=confidence_report,
            trade_plan=trade_plan,
            strategy_evaluation=strategy_evaluation,
            opportunity_context=opportunity_context,
            market_score=market_score,
            config=config,
        )

        logger.info(
            f"DecisionPipeline executed successfully. "
            f"Decision Report ID={decision_report.report_id}, "
            f"Overall Action={decision_report.summary.overall_action}, "
            f"BUY Count={decision_report.stats.buy_count}, "
            f"SELL Count={decision_report.stats.sell_count}, "
            f"WATCH Count={decision_report.stats.watch_count}"
        )
        return decision_report
