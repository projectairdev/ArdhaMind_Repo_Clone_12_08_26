from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import (
    MarketScore,
    OpportunityContext,
    TradePlan,
    ConfidenceReport,
    RiskReport,
    DecisionReport,
    EveningReport,
    IntradayReport,
    ValidationReport,
    OptimizationReport,
)

class SummaryPanel:
    """
    Stateless Summary Panel.
    Consumes existing reports and extracts key workstation metrics.
    Future-ready: provides a structured dict representation via to_dict().
    """

    def __init__(
        self,
        market_score: Optional[MarketScore] = None,
        opportunity: Optional[OpportunityContext] = None,
        trade_plan: Optional[TradePlan] = None,
        confidence: Optional[ConfidenceReport] = None,
        risk: Optional[RiskReport] = None,
        decision: Optional[DecisionReport] = None,
        evening_report: Optional[EveningReport] = None,
        intraday: Optional[IntradayReport] = None,
        validation: Optional[ValidationReport] = None,
        optimization: Optional[OptimizationReport] = None,
    ) -> None:
        self.market_score = market_score
        self.opportunity = opportunity
        self.trade_plan = trade_plan
        self.confidence = confidence
        self.risk = risk
        self.decision = decision
        self.evening_report = evening_report
        self.intraday = intraday
        self.validation = validation
        self.optimization = optimization

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured data for Web/Desktop/Mobile UI consumption.
        No business logic or calculations are performed here.
        """
        # Get market metrics
        spot = None
        vix = None
        regime = "N/A"
        bias = "N/A"
        if self.opportunity:
            bias = self.opportunity.directional_bias.value
        elif self.evening_report:
            bias = self.evening_report.tomorrow_outlook.directional_bias

        # Top candidate info
        best_candidate = "NONE"
        best_strategy = "NONE"
        if self.trade_plan and self.trade_plan.summary:
            best_candidate = self.trade_plan.summary.best_candidate_id
        elif self.evening_report and self.evening_report.summary:
            best_candidate = self.evening_report.summary.best_candidate_id
            best_strategy = self.evening_report.summary.best_strategy

        if self.trade_plan and self.trade_plan.accepted_candidates:
            for c in self.trade_plan.accepted_candidates:
                if c.candidate_id == best_candidate:
                    best_strategy = c.strategy_name
                    break

        # Capital allocations
        total_allocated = 0.0
        if self.decision and self.decision.stats:
            total_allocated = self.decision.stats.total_allocated_capital
        elif self.risk and self.risk.exposure_summary:
            total_allocated = self.risk.exposure_summary.total_capital_allocated

        # Intraday status
        intraday_status = "N/A"
        intraday_rec = "N/A"
        if self.intraday and self.intraday.summary:
            intraday_status = self.intraday.summary.plan_status.name if hasattr(self.intraday.summary.plan_status, 'name') else str(self.intraday.summary.plan_status)
            intraday_rec = self.intraday.summary.action_recommendation.name if hasattr(self.intraday.summary.action_recommendation, 'name') else str(self.intraday.summary.action_recommendation)

        # Validation info
        val_days = 0
        val_acc = 0.0
        if self.validation and self.validation.summary_stats:
            val_days = self.validation.summary_stats.total_days_evaluated
        if self.validation and self.validation.outcome_validations:
            # average of outcome validation accuracies
            accuracies = [ov.accuracy_pct for ov in self.validation.outcome_validations]
            if accuracies:
                val_acc = sum(accuracies) / len(accuracies)

        # Optimization adjustments
        opt_recs = 0
        if self.optimization and self.optimization.summary:
            opt_recs = self.optimization.summary.total_recommendations

        return {
            "workstation_status": {
                "market_grade": self.market_score.letter_grade if self.market_score else "N/A",
                "market_score": self.market_score.overall_score if self.market_score else 0.0,
                "opportunity_class": self.opportunity.classification.value if self.opportunity else "N/A",
                "directional_bias": bias,
                "top_candidate_id": best_candidate,
                "best_strategy": best_strategy,
                "total_allocated_capital": total_allocated,
                "risk_grade": self.risk.summary.portfolio_risk_grade if self.risk and self.risk.summary else "N/A",
                "overall_action": self.decision.summary.overall_action if self.decision and self.decision.summary else "N/A",
                "intraday_plan_status": intraday_status,
                "intraday_recommendation": intraday_rec,
                "validation_days": val_days,
                "validation_accuracy": val_acc,
                "optimization_recommendations_count": opt_recs,
            }
        }

    def render_cli(self) -> str:
        """
        Renders an ASCII text-based panel for terminal output.
        """
        data = self.to_dict()["workstation_status"]
        
        lines = []
        lines.append("================================================================================")
        lines.append("                         TRADING WORKSTATION OVERVIEW                           ")
        lines.append("================================================================================")
        lines.append(f" Market Grade   : {data['market_grade']:<15} | Portfolio Risk : {data['risk_grade']}")
        lines.append(f" Market Score   : {data['market_score']:<15.2f} | Execution Action: {data['overall_action']}")
        lines.append(f" Opportunity    : {data['opportunity_class']:<15} | Direction Bias : {data['directional_bias']}")
        lines.append(f" Best Candidate : {data['top_candidate_id']:<15} | Best Strategy  : {data['best_strategy']}")
        lines.append(f" Allocated Cap  : INR {data['total_allocated_capital']:<11.2f} | Intraday State : {data['intraday_plan_status']}")
        lines.append(f" Intraday Action: {data['intraday_recommendation']:<15} | Opt Recs Count : {data['optimization_recommendations_count']}")
        if data['validation_days'] > 0:
            lines.append(f" Validation Days: {data['validation_days']:<15} | Avg Accuracy   : {data['validation_accuracy']:.2f}%")
        lines.append("================================================================================")
        return "\n".join(lines)
