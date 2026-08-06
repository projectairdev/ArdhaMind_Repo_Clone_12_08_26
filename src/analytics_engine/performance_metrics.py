from __future__ import annotations

from typing import List
from src.models import PerformanceMetrics, TradeJournalEntry

class PerformanceMetricsCalculator:
    """
    Stateless calculator for overall paper trading performance metrics.
    """

    @staticmethod
    def calculate(entries: List[TradeJournalEntry]) -> PerformanceMetrics:
        total_trades = len(entries)
        if total_trades == 0:
            return PerformanceMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                average_profit=0.0,
                average_loss=0.0,
                profit_factor=1.0,
                expectancy=0.0,
                average_holding_time=0.0,
                largest_winner=0.0,
                largest_loser=0.0,
                maximum_drawdown=0.0,
                recovery_factor=0.0,
            )

        wins = [e for e in entries if e.pnl > 0]
        losses = [e for e in entries if e.pnl < 0]

        winning_trades = len(wins)
        losing_trades = len(losses)

        win_rate = (winning_trades / total_trades) * 100.0

        average_profit = sum(w.pnl for w in wins) / winning_trades if winning_trades > 0 else 0.0
        average_loss = sum(l.pnl for l in losses) / losing_trades if losing_trades > 0 else 0.0

        gross_profits = sum(w.pnl for w in wins)
        gross_losses = abs(sum(l.pnl for l in losses))
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else (gross_profits if gross_profits > 0 else 1.0)

        # Expectancy formula: (Win% * Avg Profit) + (Loss% * Avg Loss)
        # Note: average_loss is already negative.
        loss_rate = (losing_trades / total_trades)
        expectancy = ((win_rate / 100.0) * average_profit) + (loss_rate * average_loss)

        average_holding_time = sum(e.duration_seconds for e in entries) / total_trades

        largest_winner = max((w.pnl for w in wins), default=0.0)
        largest_loser = min((l.pnl for l in losses), default=0.0)

        # Drawdown calculation
        sorted_entries = sorted(entries, key=lambda e: e.exit_time or e.entry_time)
        capital = 1000000.0
        equity = capital
        peak = capital
        max_dd = 0.0

        for e in sorted_entries:
            equity += e.pnl
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        total_pnl = sum(e.pnl for e in entries)
        recovery_factor = total_pnl / max_dd if max_dd > 0 else total_pnl

        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            average_profit=average_profit,
            average_loss=average_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            average_holding_time=average_holding_time,
            largest_winner=largest_winner,
            largest_loser=largest_loser,
            maximum_drawdown=max_dd,
            recovery_factor=recovery_factor,
        )
