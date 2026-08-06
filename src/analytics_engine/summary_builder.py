from __future__ import annotations

from typing import List
from src.models import (
    AnalyticsSummary,
    PerformanceMetrics,
    StrategyPerformance,
    MarketPerformance,
    ConfidencePerformance,
    RiskPerformance,
    TimePerformance,
    PortfolioPerformance,
)

class SummaryBuilder:
    """
    Stateless builder that generates actionable trading strengths, weaknesses,
    and recommendations based on computed performance analytics.
    """

    @staticmethod
    def build(
        overall: PerformanceMetrics,
        strategies: List[StrategyPerformance],
        market: MarketPerformance,
        confidence: List[ConfidencePerformance],
        risk: List[RiskPerformance],
        time_perf: TimePerformance,
        portfolio: PortfolioPerformance,
    ) -> AnalyticsSummary:
        strengths: List[str] = []
        weaknesses: List[str] = []
        recommendations: List[str] = []

        # Overall Win Rate & Profit Factor Analysis
        if overall.win_rate >= 60.0:
            strengths.append(f"High system win rate of {overall.win_rate:.1f}%.")
        elif overall.win_rate < 40.0 and overall.total_trades > 0:
            weaknesses.append(f"Sub-optimal win rate of {overall.win_rate:.1f}%.")
            recommendations.append("Enhance candidate selection filters to improve trade entry win rates.")

        if overall.profit_factor >= 1.8:
            strengths.append(f"Outstanding profit factor of {overall.profit_factor:.2f}.")
        elif overall.profit_factor < 1.0 and overall.total_trades > 0:
            weaknesses.append(f"System is unprofitable with a profit factor of {overall.profit_factor:.2f}.")
            recommendations.append("Halt live trading and review core edge, as overall expectancy is negative.")

        # Drawdown and Recovery
        if portfolio.maximum_drawdown > 0:
            dd_pct = (portfolio.maximum_drawdown / portfolio.initial_capital) * 100.0
            if dd_pct > 15.0:
                weaknesses.append(f"Deep peak-to-valley drawdown of {portfolio.maximum_drawdown:,.2f} INR ({dd_pct:.1f}% of capital).")
                recommendations.append("Reduce position sizing (lot sizes) to mitigate excessive portfolio drawdown.")
            elif dd_pct < 5.0 and overall.total_trades > 0:
                strengths.append(f"Excellent drawdown containment ({dd_pct:.1f}% max capital drawdown).")

        # Strategy Performance
        if strategies:
            best_strat = strategies[0]
            worst_strat = strategies[-1]
            if best_strat.win_rate >= 60.0 and best_strat.total_trades >= 3:
                strengths.append(f"Strong performance in strategy '{best_strat.strategy_name}' (Win Rate: {best_strat.win_rate:.1f}%).")
                recommendations.append(f"Allocate higher capital weight to the top-performing '{best_strat.strategy_name}' strategy.")
            if worst_strat.average_return < 0 and worst_strat.total_trades >= 3:
                weaknesses.append(f"Underperformance in strategy '{worst_strat.strategy_name}' (Avg Return: {worst_strat.average_return:+,.2f} INR).")
                recommendations.append(f"Review entry constraints or temporarily pause trading the '{worst_strat.strategy_name}' strategy.")

        # Confidence Calibration
        if confidence:
            high_conf = [c for c in confidence if "90" in c.confidence_band or "80" in c.confidence_band]
            low_conf = [c for c in confidence if "Under 50" in c.confidence_band or "50–60" in c.confidence_band]

            if high_conf and low_conf:
                avg_high_wr = sum(c.win_rate for c in high_conf) / len(high_conf)
                avg_low_wr = sum(c.win_rate for c in low_conf) / len(low_conf)
                if avg_high_wr > avg_low_wr + 10.0:
                    strengths.append("Excellent confidence model alignment; high-confidence setups yield superior win rates.")
                elif avg_high_wr < avg_low_wr:
                    weaknesses.append("Confidence model inverse calibration: high-confidence setups underperform low-confidence ones.")
                    recommendations.append("Re-evaluate and retune confidence scoring factors to restore proper alignment.")

        # Temporal patterns
        if time_perf.by_entry_hour:
            worst_hour = min(time_perf.by_entry_hour, key=time_perf.by_entry_hour.get)
            worst_hour_pnl = time_perf.by_entry_hour[worst_hour]
            if worst_hour_pnl < -10000.0:
                weaknesses.append(f"Significant losses accumulated during hour {worst_hour:02d}:00 (PnL: {worst_hour_pnl:+,.2f} INR).")
                recommendations.append(f"Avoid initiating new positions during the {worst_hour:02d}:00 hour block.")

        # Defaults if empty or new system
        if not strengths:
            strengths.append("Establishing trading baseline.")
        if not weaknesses:
            weaknesses.append("No critical weaknesses identified in the current sample size.")
        if not recommendations:
            recommendations.append("Maintain disciplined execution according to risk parameters and accumulate more trade data.")

        return AnalyticsSummary(
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )
