from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import AnalyticsReport

class PerformanceAnalyticsPanel:
    """
    Performance Analytics Panel presenting comprehensive trading statistics.
    Supports structured to_dict() for API integration and render_cli() for terminal rendering.
    """

    def __init__(self, report: Optional[AnalyticsReport] = None) -> None:
        self.report = report

    def to_dict(self) -> Dict[str, Any]:
        if not self.report:
            return {}

        rep = self.report
        overall = rep.overall_metrics
        portfolio = rep.portfolio_metrics
        summary = rep.summary

        overall_dict = {
            "total_trades": overall.total_trades,
            "winning_trades": overall.winning_trades,
            "losing_trades": overall.losing_trades,
            "win_rate": overall.win_rate,
            "average_profit": overall.average_profit,
            "average_loss": overall.average_loss,
            "profit_factor": overall.profit_factor,
            "expectancy": overall.expectancy,
            "average_holding_time": overall.average_holding_time,
            "largest_winner": overall.largest_winner,
            "largest_loser": overall.largest_loser,
            "maximum_drawdown": overall.maximum_drawdown,
            "recovery_factor": overall.recovery_factor,
        }
        portfolio_dict = {
            "initial_capital": portfolio.initial_capital,
            "final_capital": portfolio.final_capital,
            "total_pnl": portfolio.total_pnl,
            "return_on_capital": portfolio.return_on_capital,
            "maximum_drawdown": portfolio.maximum_drawdown,
            "sharpe_ratio": portfolio.sharpe_ratio,
            "profit_factor": portfolio.profit_factor,
        }
        strategies_list = [
            {
                "strategy_name": s.strategy_name,
                "total_trades": s.total_trades,
                "win_rate": s.win_rate,
                "average_return": s.average_return,
                "profit_factor": s.profit_factor,
                "expectancy": s.expectancy,
                "capital_utilization": s.capital_utilization,
            }
            for s in rep.strategy_metrics
        ]
        confidence_list = [
            {
                "confidence_band": c.confidence_band,
                "total_trades": c.total_trades,
                "win_rate": c.win_rate,
                "average_return": c.average_return,
            }
            for c in rep.confidence_metrics
        ]
        risk_list = [
            {
                "risk_grade": r.risk_grade,
                "total_trades": r.total_trades,
                "win_rate": r.win_rate,
                "average_return": r.average_return,
                "capital_allocation_avg": r.capital_allocation_avg,
                "portfolio_utilization": r.portfolio_utilization,
            }
            for r in rep.risk_metrics
        ]
        time_dict = {
            "avg_holding_time": rep.time_metrics.avg_holding_time,
            "by_entry_hour": rep.time_metrics.by_entry_hour,
            "by_day_of_week": rep.time_metrics.by_day_of_week,
        }

        return {
            "report_id": rep.report_id,
            "timestamp": rep.timestamp,
            "overall": overall_dict,
            "overall_metrics": overall_dict,
            "portfolio": portfolio_dict,
            "portfolio_metrics": portfolio_dict,
            "strategies": strategies_list,
            "strategy_metrics": strategies_list,
            "confidence": confidence_list,
            "confidence_metrics": confidence_list,
            "risk": risk_list,
            "risk_metrics": risk_list,
            "time": time_dict,
            "time_metrics": time_dict,
            "summary": {
                "strengths": summary.strengths,
                "weaknesses": summary.weaknesses,
                "recommendations": summary.recommendations,
            }
        }

    def render_cli(self) -> str:
        if not self.report:
            return (
                "+- PERFORMANCE ANALYTICS -----------------------------------------------------+\n"
                "| No performance analytics report available.                                   |\n"
                "+------------------------------------------------------------------------------+"
            )

        data = self.to_dict()
        overall = data["overall"]
        portfolio = data["portfolio"]
        summary = data["summary"]

        lines = []
        lines.append("+- PERFORMANCE ANALYTICS REPORT -----------------------------------------------+")
        lines.append(f"| REPORT ID: {data['report_id']:<20} | GENERATED AT: {data['timestamp']:<26} |")
        lines.append("|" + "-" * 78 + "|")
        lines.append("| OVERALL STATISTICS:                                                          |")
        lines.append(
            f"|   Trades: {overall['total_trades']:<4} | Wins: {overall['winning_trades']:<4} | Losses: {overall['losing_trades']:<4} | Win Rate: {overall['win_rate']:.1f}% |"
        )
        lines.append(
            f"|   Avg Win: {overall['average_profit']:+,.2f} INR   | Avg Loss: {overall['average_loss']:+,.2f} INR | Expectancy: {overall['expectancy']:+,.2f} INR |"
        )
        lines.append(
            f"|   Profit Factor: {overall['profit_factor']:.2f} | Max DD: {overall['maximum_drawdown']:,.2f} INR | Recovery Factor: {overall['recovery_factor']:.2f} |"
        )
        lines.append(
            f"|   Largest Win: {overall['largest_winner']:+,.2f} INR | Largest Loss: {overall['largest_loser']:+,.2f} INR |"
        )

        lines.append("|" + "-" * 78 + "|")
        lines.append("| PORTFOLIO STATISTICS:                                                        |")
        lines.append(
            f"|   Initial Cap: {portfolio['initial_capital']:,.2f} INR | Final Cap: {portfolio['final_capital']:,.2f} INR |"
        )
        lines.append(
            f"|   Total P&L: {portfolio['total_pnl']:+,.2f} INR ({portfolio['return_on_capital']:.2f}%) | Sharpe Ratio: {portfolio['sharpe_ratio']:.2f} |"
        )

        lines.append("|" + "-" * 78 + "|")
        lines.append("| STRATEGY PERFORMANCE breakdown:                                              |")
        for s in data["strategies"][:5]:
            lines.append(
                f"|   * {s['strategy_name']:<12} | Trades: {s['total_trades']:<3} | WinRate: {s['win_rate']:>5.1f}% | AvgRet: {s['average_return']:+,.2f} INR |"
            )

        lines.append("|" + "-" * 78 + "|")
        lines.append("| CONFIDENCE CORRELATION breakdown:                                            |")
        for c in data["confidence"][:5]:
            lines.append(
                f"|   * Band {c['confidence_band']:<8} | Trades: {c['total_trades']:<3} | WinRate: {c['win_rate']:>5.1f}% | AvgRet: {c['average_return']:+,.2f} INR |"
            )

        lines.append("|" + "-" * 78 + "|")
        lines.append("| RISK GRADE breakdown:                                                        |")
        for r in data["risk"][:5]:
            lines.append(
                f"|   * Grade {r['risk_grade']:<7} | Trades: {r['total_trades']:<3} | WinRate: {r['win_rate']:>5.1f}% | Util: {r['portfolio_utilization']:>5.2f}% |"
            )

        lines.append("|" + "-" * 78 + "|")
        lines.append("| SYSTEM DIAGNOSTIC SUMMARY:                                                   |")
        lines.append("|   STRENGTHS:                                                                 |")
        for st in summary["strengths"][:3]:
            lines.append(f"|     + {st:<71} |")
        lines.append("|   WEAKNESSES:                                                                |")
        for wk in summary["weaknesses"][:3]:
            lines.append(f"|     - {wk:<71} |")
        lines.append("|   RECOMMENDATIONS:                                                           |")
        for rc in summary["recommendations"][:3]:
            lines.append(f"|     > {rc:<71} |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
