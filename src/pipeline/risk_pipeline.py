from __future__ import annotations

from typing import Optional
from src.models import (
    TradePlan,
    ConfidenceReport,
    TradeContext,
    MarketScore,
    RiskEngineConfig,
    RiskReport,
)
from src.risk_engine_v2 import RiskBuilder
from src.utils import setup_logger

logger = setup_logger("RiskPipeline")


class RiskPipeline:
    """
    Coordinates exposure evaluation, portfolio constraints verification,
    and capital allocation to produce a final RiskReport.
    """

    def __init__(self) -> None:
        pass

    def run(
        self,
        confidence_report: ConfidenceReport,
        trade_plan: TradePlan,
        trade_context: TradeContext,
        market_score: MarketScore,
        config: Optional[RiskEngineConfig] = None,
    ) -> RiskReport:
        logger.info(f"Executing Risk Pipeline for ConfidenceReport ID={confidence_report.report_id}...")

        # Build Risk Report
        risk_report = RiskBuilder.build_risk_report(
            trade_plan=trade_plan,
            confidence_report=confidence_report,
            trade_context=trade_context,
            market_score=market_score,
            config=config,
        )

        logger.info(
            f"RiskPipeline executed successfully. "
            f"Risk Report ID={risk_report.report_id}, "
            f"Approved Candidates Count={sum(1 for r in risk_report.candidate_risks if r.is_approved)}, "
            f"Total Capital Allocated={risk_report.exposure_summary.total_capital_allocated:.2f}"
        )
        return risk_report
