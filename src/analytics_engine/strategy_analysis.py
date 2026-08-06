from __future__ import annotations

from typing import List, Dict
from src.models import AnalyticsStrategyPerformance, TradeJournalEntry

class StrategyAnalyser:
    """
    Stateless evaluator for strategy-specific trading performance.
    """

    @staticmethod
    def analyze(entries: List[TradeJournalEntry]) -> List[AnalyticsStrategyPerformance]:
        if not entries:
            return []

        by_strategy: Dict[str, List[TradeJournalEntry]] = {}
        for e in entries:
            strat_name = e.strategy_name or "UNKNOWN"
            by_strategy.setdefault(strat_name, []).append(e)

        results: List[AnalyticsStrategyPerformance] = []
        for strat, strat_entries in by_strategy.items():
            total = len(strat_entries)
            wins = [x for x in strat_entries if x.pnl > 0]
            losses = [x for x in strat_entries if x.pnl < 0]

            win_rate = (len(wins) / total) * 100.0 if total > 0 else 0.0
            average_return = sum(x.pnl for x in strat_entries) / total if total > 0 else 0.0

            gross_profit = sum(x.pnl for x in wins)
            gross_loss = abs(sum(x.pnl for x in losses))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)

            avg_win = sum(x.pnl for x in wins) / len(wins) if wins else 0.0
            avg_loss = sum(x.pnl for x in losses) / len(losses) if losses else 0.0
            expectancy = ((win_rate / 100.0) * avg_win) + (((total - len(wins)) / total) * avg_loss)

            capital_utilization = sum(x.entry_capital for x in strat_entries) / total if total > 0 else 0.0

            results.append(
                AnalyticsStrategyPerformance(
                    strategy_name=strat,
                    total_trades=total,
                    win_rate=win_rate,
                    average_return=average_return,
                    profit_factor=profit_factor,
                    expectancy=expectancy,
                    capital_utilization=capital_utilization,
                )
            )

        return sorted(results, key=lambda x: x.total_trades, reverse=True)
