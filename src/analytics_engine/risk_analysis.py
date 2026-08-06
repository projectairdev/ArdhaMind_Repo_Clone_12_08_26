from __future__ import annotations

from typing import List, Dict
from src.models import RiskPerformance, TradeJournalEntry

class RiskAnalyser:
    """
    Stateless evaluator for risk grades and capital utilization.
    """

    @staticmethod
    def analyze(entries: List[TradeJournalEntry], total_portfolio_capital: float = 1000000.0) -> List[RiskPerformance]:
        if not entries:
            return []

        by_risk: Dict[str, List[TradeJournalEntry]] = {}
        for e in entries:
            grade = e.risk_grade or "MEDIUM"
            by_risk.setdefault(grade, []).append(e)

        results: List[RiskPerformance] = []
        for grade, grade_entries in by_risk.items():
            total = len(grade_entries)
            wins = [x for x in grade_entries if x.pnl > 0]
            win_rate = (len(wins) / total) * 100.0 if total > 0 else 0.0
            average_return = sum(x.pnl for x in grade_entries) / total if total > 0 else 0.0

            capital_allocation_avg = sum(x.entry_capital for x in grade_entries) / total if total > 0 else 0.0
            portfolio_utilization = (capital_allocation_avg / total_portfolio_capital) * 100.0 if total_portfolio_capital > 0 else 0.0

            results.append(
                RiskPerformance(
                    risk_grade=grade,
                    total_trades=total,
                    win_rate=win_rate,
                    average_return=average_return,
                    capital_allocation_avg=capital_allocation_avg,
                    portfolio_utilization=portfolio_utilization,
                )
            )

        return sorted(results, key=lambda x: x.total_trades, reverse=True)
