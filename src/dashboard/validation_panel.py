from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import ValidationReport

class ValidationPanel:
    """
    Stateless Validation Panel.
    Displays Validation reports, historical outcomes, and performance statistics.
    """

    def __init__(self, validation_report: Optional[ValidationReport] = None) -> None:
        self.validation_report = validation_report

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured presentation data for backtest or forward validation statistics.
        """
        if not self.validation_report:
            return {}

        vr = self.validation_report

        strategies = []
        for sp in vr.strategy_performances:
            strategies.append({
                "strategy_name": sp.strategy_name,
                "total_candidates": sp.total_candidates,
                "buy_count": sp.buy_count,
                "sell_count": sp.sell_count,
                "watch_count": sp.watch_count,
                "reject_count": sp.reject_count,
                "no_trade_count": sp.no_trade_count,
                "avg_confidence_score": sp.avg_confidence_score,
            })

        decisions = []
        for dp in vr.decision_performances:
            decisions.append({
                "decision_type": dp.decision_type,
                "count": dp.count,
                "percentage": dp.percentage,
                "avg_confidence": dp.avg_confidence,
                "avg_allocated_capital": dp.avg_allocated_capital,
            })

        outcomes = []
        for ov in vr.outcome_validations:
            outcomes.append({
                "evaluation_window": ov.evaluation_window,
                "success_count": ov.success_count,
                "failure_count": ov.failure_count,
                "accuracy_pct": ov.accuracy_pct,
                "total_profit_loss": ov.total_profit_loss,
            })

        daily = []
        for dv in vr.daily_validations:
            daily.append({
                "date": dv.date,
                "market_score": dv.market_score,
                "candidates_count": dv.candidates_count,
                "buy_count": dv.buy_count,
                "total_allocated_capital": dv.total_allocated_capital,
                "outcome_summary": dv.outcome_summary,
            })

        return {
            "report_id": vr.report_id,
            "summary_stats": {
                "total_days_evaluated": vr.summary_stats.total_days_evaluated,
                "total_candidates_evaluated": vr.summary_stats.total_candidates_evaluated,
                "overall_buy_count": vr.summary_stats.overall_buy_count,
                "overall_sell_count": vr.summary_stats.overall_sell_count,
                "overall_watch_count": vr.summary_stats.overall_watch_count,
                "overall_reject_count": vr.summary_stats.overall_reject_count,
                "overall_no_trade_count": vr.summary_stats.overall_no_trade_count,
                "decision_frequency_pct": vr.summary_stats.decision_frequency_pct,
                "avg_market_score": vr.summary_stats.avg_market_score,
            },
            "confidence_stats": {
                "avg_confidence": vr.confidence_stats.avg_confidence if vr.confidence_stats else 0.0,
                "max_confidence": vr.confidence_stats.max_confidence if vr.confidence_stats else 0.0,
                "min_confidence": vr.confidence_stats.min_confidence if vr.confidence_stats else 0.0,
            },
            "risk_stats": {
                "avg_allocated_capital": vr.risk_stats.avg_allocated_capital if vr.risk_stats else 0.0,
                "total_allocated_capital": vr.risk_stats.total_allocated_capital if vr.risk_stats else 0.0,
                "approved_count": vr.risk_stats.approved_count if vr.risk_stats else 0,
                "rejected_count": vr.risk_stats.rejected_count if vr.risk_stats else 0,
            },
            "strategy_performances": strategies,
            "decision_performances": decisions,
            "outcome_validations": outcomes,
            "daily_validations": daily,
        }

    def render_cli(self) -> str:
        """
        Renders an ASCII text-based representation of the Validation Panel.
        """
        data = self.to_dict()
        lines = []
        lines.append("+- HISTORICAL VALIDATION STATISTICS -------------------------------------------+")

        if not data:
            lines.append("| Validation Report: NOT AVAILABLE                                             |")
            lines.append("+------------------------------------------------------------------------------+")
            return "\n".join(lines)

        sum_s = data["summary_stats"]
        lines.append(f"| Days Evaluated : {sum_s['total_days_evaluated']:<3} | Total Cand Evaluated : {sum_s['total_candidates_evaluated']:<4} | Avg Market Score: {sum_s['avg_market_score']:>5.1f} |")
        lines.append(f"| Buy Count      : {sum_s['overall_buy_count']:<3} | Decision Freq %      : {sum_s['decision_frequency_pct']:>5.1f}% | Avg Conf Score  : {data['confidence_stats']['avg_confidence']:>5.1f}% |")
        lines.append("| " + "-"*76 + " |")

        # Outcome validations (Accuracy)
        lines.append("| Outcome Validation & Accuracy by Window:                                     |")
        if data["outcome_validations"]:
            for ov in data["outcome_validations"]:
                lines.append(f"|   * {ov['evaluation_window']:<15}: Success: {ov['success_count']:<3} Fail: {ov['failure_count']:<3} Accuracy: {ov['accuracy_pct']:>5.1f}% P&L: INR {ov['total_profit_loss']:+,.1f} |")
        else:
            lines.append("|   No outcome validation details available.                                   |")

        lines.append("| " + "-"*76 + " |")

        # Strategy Performance
        lines.append("| Strategy Performances Table:                                                 |")
        lines.append("| STRATEGY           | CANDIDATES | BUYS | WATCHES | AVG CONFIDENCE            |")
        lines.append("| " + "-"*18 + "+" + "-"*10 + "+" + "-"*6 + "+" + "-"*9 + "+" + "-"*25 + " |")
        for sp in data["strategy_performances"][:4]:
            lines.append(
                f"| {sp['strategy_name']:<18} | {sp['total_candidates']:>10} | {sp['buy_count']:>4} | {sp['watch_count']:>7} | {sp['avg_confidence_score']:>12.1f}%            |"
            )

        lines.append("| " + "-"*76 + " |")

        # Daily highlights
        if data["daily_validations"]:
            lines.append("| Recent Days Validation Highlights:                                           |")
            for dv in data["daily_validations"][-3:]:  # last 3 days
                lines.append(f"|   * [{dv['date']}] Spot Score: {dv['market_score']:.1f} | Cands: {dv['candidates_count']} | Buys: {dv['buy_count']} | {dv['outcome_summary'][:20]:<20} |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
