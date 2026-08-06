from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import OptimizationReport

class OptimizationPanel:
    """
    Stateless Optimization Panel.
    Displays critical adjustments, weight modifications, parameter thresholds, and P&L potential.
    """

    def __init__(self, optimization_report: Optional[OptimizationReport] = None) -> None:
        self.optimization_report = optimization_report

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured presentation data for system parameter and strategy weights optimization.
        """
        if not self.optimization_report:
            return {}

        or_rep = self.optimization_report

        recs = []
        for r in or_rep.recommendations:
            recs.append({
                "recommendation_id": r.recommendation_id,
                "category": r.category,
                "title": r.title,
                "description": r.description,
                "current_value": r.current_value,
                "recommended_value": r.recommended_value,
                "rationale": r.rationale,
                "evidence": {
                    "historical_sample_size": r.evidence.historical_sample_size,
                    "observed_improvement_potential": r.evidence.observed_improvement_potential,
                    "affected_strategies": r.evidence.affected_strategies,
                    "expected_trade_off": r.evidence.expected_trade_off,
                    "confidence_score": r.evidence.confidence_score,
                } if r.evidence else None
            })

        strategies = []
        for s in or_rep.strategy_optimizations:
            strategies.append({
                "strategy_name": s.strategy_name,
                "current_accuracy": s.current_accuracy,
                "recommended_action": s.recommended_action,
                "rationale": s.rationale,
            })

        thresholds = []
        for t in or_rep.threshold_recommendations:
            thresholds.append({
                "parameter_name": t.parameter_name,
                "current_value": t.current_value,
                "suggested_value": t.suggested_value,
                "direction": t.direction,
                "impact": t.impact,
            })

        weights = []
        for w in or_rep.weight_recommendations:
            weights.append({
                "strategy_or_factor": w.strategy_or_factor,
                "current_weight": w.current_weight,
                "suggested_weight": w.suggested_weight,
                "rationale": w.rationale,
            })

        return {
            "report_id": or_rep.report_id,
            "validation_report_id": or_rep.validation_report_id,
            "summary": {
                "total_recommendations": or_rep.summary.total_recommendations,
                "critical_adjustments": or_rep.summary.critical_adjustments,
                "potential_pnl_improvement": or_rep.summary.potential_pnl_improvement,
                "recommendation_confidence_avg": or_rep.summary.recommendation_confidence_avg,
            },
            "recommendations": recs,
            "strategy_optimizations": strategies,
            "threshold_recommendations": thresholds,
            "weight_recommendations": weights,
        }

    def render_cli(self) -> str:
        """
        Renders an ASCII text-based representation of the Optimization Panel.
        """
        data = self.to_dict()
        lines = []
        lines.append("+- SYSTEM OPTIMIZATION ADVISORY -----------------------------------------------+")

        if not data:
            lines.append("| Optimization Report: NOT AVAILABLE                                           |")
            lines.append("+------------------------------------------------------------------------------+")
            return "\n".join(lines)

        sum_d = data["summary"]
        lines.append(f"| Key Recs Count : {sum_d['total_recommendations']:<3} | Critical Adjustments: {sum_d['critical_adjustments']:<2} | Confidence Avg: {sum_d['recommendation_confidence_avg']:>5.1f}% |")
        lines.append(f"| Est PnL Boost  : INR {sum_d['potential_pnl_improvement']:<13,.2f}                                           |")
        lines.append("| " + "-"*76 + " |")

        # Strategy weight adjustments
        if data["strategy_optimizations"]:
            lines.append("| Strategy Performance Optimizations:                                          |")
            lines.append("| STRATEGY           | CURR ACCURACY | SUGGESTED ACTION | RATIONALE            |")
            lines.append("| " + "-"*18 + "+" + "-"*13 + "+" + "-"*16 + "+" + "-"*23 + " |")
            for so in data["strategy_optimizations"][:3]:
                lines.append(
                    f"| {so['strategy_name']:<18} | {so['current_accuracy']*100:>11.1f}% | {so['recommended_action']:<16} | {so['rationale'][:21]:<21} |"
                )
            lines.append("| " + "-"*76 + " |")

        # Threshold recommendations
        if data["threshold_recommendations"]:
            lines.append("| Threshold/Parameter Adjustments:                                             |")
            for tr in data["threshold_recommendations"][:2]:
                lines.append(f"|   * Parameter: {tr['parameter_name']:<15} {tr['current_value']:>6} -> {tr['suggested_value']:<6} Direction: {tr['direction']:<8} |")
                lines.append(f"|     Impact   : {tr['impact'][:65]:<66} |")
            lines.append("| " + "-"*76 + " |")

        # Top concrete recommendation
        if data["recommendations"]:
            rec = data["recommendations"][0]
            lines.append(f"| FEATURED RECOMMENDATION: [{rec['category']}]                                 |")
            lines.append(f"| Title : {rec['title'][:68]:<68} |")
            lines.append(f"| Action: {rec['current_value']} -> {rec['recommended_value']}                                              |")
            lines.append(f"| Reason: {rec['rationale'][:68]:<68} |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
