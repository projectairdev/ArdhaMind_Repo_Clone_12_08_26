from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import StrategyEvaluation

class StrategyPanel:
    """
    Stateless Strategy Panel.
    Displays Strategy Evaluations, suitability rankings, warnings, and conclusions.
    """

    def __init__(self, strategy_evaluation: Optional[StrategyEvaluation] = None) -> None:
        self.strategy_evaluation = strategy_evaluation

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured presentation data for strategy evaluation.
        """
        if not self.strategy_evaluation:
            return {}

        se = self.strategy_evaluation
        eval_list = []
        for score in se.evaluations:
            eval_list.append({
                "strategy_name": score.strategy_name,
                "suitability_score": score.suitability_score,
                "suitability_level": score.suitability_level,
                "reasons": [{"type": r.reason_type, "message": r.message} for r in score.reasons],
                "warnings": [{"type": w.warning_type, "message": w.message, "severity": w.severity} for w in score.warnings],
                "constraints": [{"type": c.constraint_type, "message": c.message, "is_violated": c.is_violated} for c in score.constraints],
            })

        return {
            "overall_best_strategy": se.overall_best_strategy,
            "timestamp": se.timestamp,
            "summary": {
                "top_strategies": se.summary.top_strategies,
                "suitable_count": se.summary.suitable_strategies_count,
                "unsuitable_count": se.summary.unsuitable_strategies_count,
                "conclusions": se.summary.conclusions,
            },
            "evaluations": eval_list,
        }

    def render_cli(self) -> str:
        """
        Renders an ASCII text-based representation of the Strategy Panel.
        """
        data = self.to_dict()
        lines = []
        lines.append("+- STRATEGY EVALUATION SUMMARY ------------------------------------------------+")

        if not data:
            lines.append("| Strategy Evaluation: NOT AVAILABLE                                           |")
            lines.append("+------------------------------------------------------------------------------+")
            return "\n".join(lines)

        lines.append(f"| BEST OVERALL STRATEGY: {data['overall_best_strategy']:<18} | Suitable Count: {data['summary']['suitable_count']:<3} | Unsuitable: {data['summary']['unsuitable_count']:<3} |")
        lines.append("| " + "-"*76 + " |")

        # Table of strategy evaluations
        lines.append("| STRATEGY NAME      | SCORE | SUITABILITY LEVEL | CONSTRAINTS STATUS          |")
        lines.append("| " + "-"*18 + "+" + "-"*7 + "+" + "-"*19 + "+" + "-"*28 + " |")
        
        for eval_item in data["evaluations"]:
            # Find if any constraints are violated
            violated = [c["type"] for c in eval_item["constraints"] if c["is_violated"]]
            constraint_str = f"VIOLATED: {','.join(violated[:2])}" if violated else "All Constraints OK"
            lines.append(
                f"| {eval_item['strategy_name']:<18} | {eval_item['suitability_score']:>5.1f} | {eval_item['suitability_level']:<17} | {constraint_str[:26]:<26} |"
            )

        # Conclusions
        if data["summary"]["conclusions"]:
            lines.append("| " + "-"*76 + " |")
            lines.append("| Strategic Conclusions:                                                       |")
            for conc in data["summary"]["conclusions"][:3]:
                lines.append(f"|   * {conc[:70]:<70} |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
