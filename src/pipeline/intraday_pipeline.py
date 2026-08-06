from __future__ import annotations

from typing import Optional
from src.models import (
    EveningReport,
    MarketContext,
    OptionContext,
    MarketScore,
    OpportunityContext,
    ConfidenceReport,
    RiskReport,
    DecisionReport,
    IntradayReport,
)
from src.intraday.report_builder import IntradayAssistant
from src.utils import setup_logger

logger = setup_logger("IntradayPipeline")


class IntradayPipeline:
    """
    Coordinates live parameter monitoring, real-time comparisons,
    and plan validation to produce a final IntradayReport.
    """

    def __init__(self) -> None:
        pass

    def run(
        self,
        evening_report: EveningReport,
        current_market_context: MarketContext,
        current_option_context: Optional[OptionContext] = None,
        current_market_score: Optional[MarketScore] = None,
        current_opportunity_context: Optional[OpportunityContext] = None,
        current_confidence_report: Optional[ConfidenceReport] = None,
        current_risk_report: Optional[RiskReport] = None,
        current_decision_report: Optional[DecisionReport] = None,
        previous_option_context: Optional[OptionContext] = None,
    ) -> IntradayReport:
        logger.info(f"Executing Intraday Monitoring Pipeline comparing against EveningReport ID={evening_report.report_id}...")

        intraday_report = IntradayAssistant.generate_report(
            evening_report=evening_report,
            current_market_context=current_market_context,
            current_option_context=current_option_context,
            current_market_score=current_market_score,
            current_opportunity_context=current_opportunity_context,
            current_confidence_report=current_confidence_report,
            current_risk_report=current_risk_report,
            current_decision_report=current_decision_report,
            previous_option_context=previous_option_context,
        )

        logger.info(
            f"IntradayPipeline completed successfully. "
            f"Report ID={intraday_report.report_id}, "
            f"Validity Status={intraday_report.summary.plan_status.name}, "
            f"Action Recommendation={intraday_report.summary.action_recommendation.name}"
        )
        return intraday_report
