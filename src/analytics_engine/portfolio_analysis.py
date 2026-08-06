from __future__ import annotations

import math
from typing import List
from src.models import PortfolioPerformance, TradeJournalEntry

class PortfolioAnalyser:
    """
    Stateless evaluator for portfolio-level performance metrics.
    """

    @staticmethod
    def calculate_sharpe_ratio(entries: List[TradeJournalEntry]) -> float:
        if len(entries) < 2:
            return 0.0

        pnl_pcts = [e.pnl_pct for e in entries]
        mean_pct = sum(pnl_pcts) / len(pnl_pcts)
        
        variance = sum((x - mean_pct) ** 2 for x in pnl_pcts) / (len(pnl_pcts) - 1)
        std_dev = math.sqrt(variance)
        if std_dev == 0.0:
            return 0.0

        # Raw trade-level Sharpe ratio (mean / std_dev)
        return mean_pct / std_dev

    @classmethod
    def analyze(cls, entries: List[TradeJournalEntry], initial_capital: float = 1000000.0) -> PortfolioPerformance:
        total_pnl = sum(e.pnl for e in entries)
        final_capital = initial_capital + total_pnl
        return_on_capital = (total_pnl / initial_capital) * 100.0 if initial_capital > 0 else 0.0

        # Calculate max drawdown
        sorted_entries = sorted(entries, key=lambda e: e.exit_time or e.entry_time)
        equity = initial_capital
        peak = initial_capital
        max_dd = 0.0

        for e in sorted_entries:
            equity += e.pnl
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        # Calculate profit factor
        wins = [e for e in entries if e.pnl > 0]
        losses = [e for e in entries if e.pnl < 0]
        gross_profits = sum(w.pnl for w in wins)
        gross_losses = abs(sum(l.pnl for l in losses))
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else (gross_profits if gross_profits > 0 else 1.0)

        sharpe_ratio = cls.calculate_sharpe_ratio(entries)

        return PortfolioPerformance(
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_pnl=total_pnl,
            return_on_capital=return_on_capital,
            maximum_drawdown=max_dd,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
        )
