from __future__ import annotations

from typing import Optional
from datetime import datetime
import uuid

from src.models import (
    DecisionReport,
    RiskReport,
    ConfidenceReport,
    TradePlan,
    StrategyEvaluation,
    OpportunityContext,
    MarketScore,
    EveningReport,
    IntradayReport,
    ExplanationReport,
)
from src.explanation_engine.decision_explainer import explain_decisions
from src.explanation_engine.confidence_explainer import explain_confidence
from src.explanation_engine.risk_explainer import explain_risk
from src.explanation_engine.strategy_explainer import explain_strategy
from src.explanation_engine.planner_explainer import explain_planner
from src.explanation_engine.intraday_explainer import explain_intraday
from src.explanation_engine.summary_explainer import explain_summary


class ExplanationBuilder:
    """
    Unified entry point for the Explanation Engine.
    Statelessly consumes existing reports and aggregates explanations into a single ExplanationReport.
    """

    @staticmethod
    def build(
        decision_report: Optional[DecisionReport] = None,
        risk_report: Optional[RiskReport] = None,
        confidence_report: Optional[ConfidenceReport] = None,
        trade_plan: Optional[TradePlan] = None,
        strategy_evaluation: Optional[StrategyEvaluation] = None,
        opportunity: Optional[OpportunityContext] = None,
        market_score: Optional[MarketScore] = None,
        evening_report: Optional[EveningReport] = None,
        intraday_report: Optional[IntradayReport] = None,
        report_id: Optional[str] = None,
    ) -> ExplanationReport:
        # 1. Generate unique report_id and timestamp if not provided
        r_id = report_id or f"EXP_REP_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().isoformat()

        # 2. Call individual explainers
        decision_exp = explain_decisions(
            decision_report=decision_report,
            risk_report=risk_report,
            confidence_report=confidence_report,
            trade_plan=trade_plan,
        )

        confidence_exp = explain_confidence(confidence_report=confidence_report)

        risk_exp = explain_risk(risk_report=risk_report)

        strategy_exp = explain_strategy(
            strategy_evaluation=strategy_evaluation,
            opportunity=opportunity,
            market_score=market_score,
        )

        planner_exp = explain_planner(evening_report=evening_report)

        intraday_exp = explain_intraday(intraday_report=intraday_report)

        summary_exp = explain_summary(
            decision_report=decision_report,
            intraday_report=intraday_report,
            strategy_evaluation=strategy_evaluation,
            market_score=market_score,
        )

        return ExplanationReport(
            report_id=r_id,
            timestamp=timestamp,
            summary=summary_exp,
            decision=decision_exp,
            risk=risk_exp,
            confidence=confidence_exp,
            strategy=strategy_exp,
            intraday=intraday_exp,
            planner=planner_exp,
        )
