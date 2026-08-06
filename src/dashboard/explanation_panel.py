from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import ExplanationReport

class ExplanationPanel:
    """
    Stateless Explanation Panel.
    Visualizes the immutable ExplanationReport containing detailed explanations of workstation states.
    """

    def __init__(self, explanation_report: Optional[ExplanationReport] = None) -> None:
        self.explanation_report = explanation_report

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured presentation data for explanation insights.
        """
        if not self.explanation_report:
            return {}

        rep = self.explanation_report

        candidates = []
        for ce in rep.decision.candidate_explanations:
            candidates.append({
                "candidate_id": ce.candidate_id,
                "tradingsymbol": ce.tradingsymbol,
                "strategy_name": ce.strategy_name,
                "decision": ce.decision,
                "decision_reasoning": ce.decision_reasoning,
                "lots_reasoning": ce.lots_reasoning,
                "confidence_reasoning": ce.confidence_reasoning,
                "risk_reasoning": ce.risk_reasoning,
            })

        return {
            "report_id": rep.report_id,
            "timestamp": rep.timestamp,
            "summary": {
                "title": rep.summary.title,
                "brief_overview": rep.summary.brief_overview,
                "key_findings": rep.summary.key_findings,
            },
            "decision": {
                "overall_action": rep.decision.overall_action,
                "highest_priority_candidate_id": rep.decision.highest_priority_candidate_id,
                "portfolio_status_message": rep.decision.portfolio_status_message,
                "overall_decision_reasoning": rep.decision.overall_decision_reasoning,
                "candidate_explanations": candidates,
            },
            "risk": {
                "portfolio_risk_grade": rep.risk.portfolio_risk_grade,
                "total_capital_allocated": rep.risk.total_capital_allocated,
                "portfolio_utilization_pct": rep.risk.portfolio_utilization_pct,
                "portfolio_risk_reasoning": rep.risk.portfolio_risk_reasoning,
                "warnings_explanations": rep.risk.warnings_explanations,
            },
            "confidence": {
                "highest_confidence_candidate_id": rep.confidence.highest_confidence_candidate_id,
                "confidence_reasoning": rep.confidence.confidence_reasoning,
            },
            "strategy": {
                "overall_best_strategy": rep.strategy.overall_best_strategy,
                "strategy_reasoning": rep.strategy.strategy_reasoning,
                "all_strategy_scores": rep.strategy.all_strategy_scores,
            },
            "intraday": {
                "plan_status": rep.intraday.plan_status,
                "action_recommendation": rep.intraday.action_recommendation,
                "explanation": rep.intraday.explanation,
                "market_change_reasons": rep.intraday.market_change_reasons,
                "candidate_change_reasons": rep.intraday.candidate_change_reasons,
            } if rep.intraday else None,
            "planner": {
                "directional_bias": rep.planner.directional_bias,
                "outlook_classification": rep.planner.outlook_classification,
                "explanation": rep.planner.explanation,
            } if rep.planner else None,
        }

    def render_cli(self) -> str:
        """
        Renders a beautifully formatted terminal-friendly text panel of the AI explanations.
        """
        data = self.to_dict()
        lines = []
        lines.append("+- AI EXPLANATION ENGINE REPORT -----------------------------------------------+")

        if not data:
            lines.append("| AI Explanations: NOT AVAILABLE                                               |")
            lines.append("+------------------------------------------------------------------------------+")
            return "\n".join(lines)

        sum_d = data["summary"]
        lines.append(f"| TITLE        : {sum_d['title']:<61} |")
        lines.append(f"| OVERVIEW     : {sum_d['brief_overview'][:70]:<70} |")
        if len(sum_d['brief_overview']) > 70:
            lines.append(f"|                {sum_d['brief_overview'][70:140]:<70} |")
        
        lines.append("| " + "-"*76 + " |")
        
        # Strategy
        strat_d = data["strategy"]
        lines.append(f"| Strategy Suitability Decision:                                               |")
        lines.append(f"|   Best Choice: {strat_d['overall_best_strategy']:<61} |")
        lines.append(f"|   Reasoning  : {strat_d['strategy_reasoning'][:70]:<70} |")
        if len(strat_d['strategy_reasoning']) > 70:
            lines.append(f"|                {strat_d['strategy_reasoning'][70:140]:<70} |")
        
        lines.append("| " + "-"*76 + " |")

        # Decisions and candidate explanations
        dec_d = data["decision"]
        lines.append(f"| Pipeline Decisions Overview:                                                 |")
        lines.append(f"|   Overall Action: {dec_d['overall_action']:<14} | Portfolio Status: {dec_d['portfolio_status_message'][:36]:<36} |")
        lines.append(f"|   Reasoning     : {dec_d['overall_decision_reasoning'][:70]:<70} |")
        if len(dec_d['overall_decision_reasoning']) > 70:
            lines.append(f"|                   {dec_d['overall_decision_reasoning'][70:140]:<70} |")

        if dec_d["candidate_explanations"]:
            lines.append("|                                                                              |")
            lines.append("|   Detailed Candidate Explanations (Top 2):                                    |")
            for ce in dec_d["candidate_explanations"][:2]:
                lines.append(f"|   * [{ce['decision']}] {ce['candidate_id'][:32]:<32} Symbol: {ce['tradingsymbol']:<18} |")
                lines.append(f"|     - Decision Reason  : {ce['decision_reasoning'][:64]:<64} |")
                lines.append(f"|     - Position Size Lot: {ce['lots_reasoning'][:64]:<64} |")
                lines.append(f"|     - Confidence Reason: {ce['confidence_reasoning'][:64]:<64} |")
                lines.append(f"|     - Risk Assessment  : {ce['risk_reasoning'][:64]:<64} |")

        # Intraday
        intra_d = data.get("intraday")
        if intra_d:
            lines.append("| " + "-"*76 + " |")
            lines.append(f"| Live Intraday Plan Alignment:                                                |")
            lines.append(f"|   Plan Validity: {intra_d['plan_status']:<15} | Workflow Action: {intra_d['action_recommendation']:<23} |")
            lines.append(f"|   Assessment   : {intra_d['explanation'][:70]:<70} |")
            if len(intra_d['explanation']) > 70:
                lines.append(f"|                  {intra_d['explanation'][70:140]:<70} |")

        # Planner
        plan_d = data.get("planner")
        if plan_d:
            lines.append("| " + "-"*76 + " |")
            lines.append(f"| Evening Planning Tomorrow Outlook:                                           |")
            lines.append(f"|   Bias: {plan_d['directional_bias']:<18} | Classification: {plan_d['outlook_classification']:<28} |")
            lines.append(f"|   Outlook Info: {plan_d['explanation'][:70]:<70} |")
            if len(plan_d['explanation']) > 70:
                lines.append(f"|                 {plan_d['explanation'][70:140]:<70} |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
