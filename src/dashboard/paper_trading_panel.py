from __future__ import annotations

from typing import Any, Dict, List, Optional
from src.models import (
    PortfolioSnapshot,
    PerformanceReport,
    PaperPosition,
    TradeJournalEntry,
)


class PaperTradingPanel:
    """
    Paper Trading Panel presenting Paper Portfolio Snapshot, Journal Summary, and Performance Metrics.
    Supports structured to_dict() for API integration and render_cli() for terminal rendering.
    """

    def __init__(
        self,
        snapshot: Optional[PortfolioSnapshot] = None,
        performance: Optional[PerformanceReport] = None,
        open_positions: Optional[List[PaperPosition]] = None,
        journal: Optional[List[TradeJournalEntry]] = None,
    ) -> None:
        self.snapshot = snapshot
        self.performance = performance
        self.open_positions = open_positions or []
        self.journal = journal or []

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured presentation-ready data.
        """
        snapshot_data = {}
        if self.snapshot:
            s = self.snapshot
            snapshot_data = {
                "timestamp": s.timestamp,
                "total_capital": s.total_capital,
                "allocated_capital": s.allocated_capital,
                "available_capital": s.available_capital,
                "open_positions_count": s.open_positions_count,
                "closed_trades_count": s.closed_trades_count,
                "total_pnl": s.total_pnl,
                "realized_pnl": s.realized_pnl,
                "unrealized_pnl": s.unrealized_pnl,
            }

        perf_data = {}
        if self.performance:
            p = self.performance
            perf_data = {
                "total_trades": p.total_trades,
                "win_rate": p.win_rate,
                "loss_rate": p.loss_rate,
                "average_profit": p.average_profit,
                "average_loss": p.average_loss,
                "profit_factor": p.profit_factor,
                "expectancy": p.expectancy,
                "average_holding_time_seconds": p.average_holding_time_seconds,
                "by_strategy": [
                    {
                        "strategy_name": s.strategy_name,
                        "total_trades": s.total_trades,
                        "win_rate": s.win_rate,
                        "total_pnl": s.total_pnl,
                    }
                    for s in p.by_strategy
                ],
                "by_regime": [
                    {
                        "market_regime": r.market_regime,
                        "total_trades": r.total_trades,
                        "win_rate": r.win_rate,
                        "total_pnl": r.total_pnl,
                    }
                    for r in p.by_regime
                ],
                "by_confidence_band": [
                    {
                        "confidence_band": c.confidence_band,
                        "total_trades": c.total_trades,
                        "win_rate": c.win_rate,
                        "total_pnl": c.total_pnl,
                    }
                    for c in p.by_confidence_band
                ],
            }

        open_pos_data = []
        for pos in self.open_positions:
            open_pos_data.append({
                "position_id": pos.position_id,
                "tradingsymbol": pos.trade.tradingsymbol,
                "action": pos.trade.action,
                "entry_price": pos.trade.premium,
                "current_price": pos.current_premium,
                "lots": pos.trade.lots,
                "current_mtm": pos.current_mtm,
                "drawdown": pos.drawdown,
                "holding_time_seconds": pos.holding_time_seconds,
            })

        journal_data = []
        for entry in self.journal:
            journal_data.append({
                "entry_id": entry.entry_id,
                "tradingsymbol": entry.tradingsymbol,
                "strategy": entry.strategy_name,
                "action": "BUY" if entry.entry_lots > 0 else "SELL", # Standard display fallback
                "entry_time": entry.entry_time,
                "entry_premium": entry.entry_premium,
                "exit_time": entry.exit_time,
                "exit_premium": entry.exit_premium,
                "exit_reason": entry.exit_reason,
                "pnl": entry.pnl,
                "pnl_pct": entry.pnl_pct,
                "duration_seconds": entry.duration_seconds,
                "outcome": entry.outcome,
            })

        return {
            "snapshot": snapshot_data or None,
            "performance": perf_data or None,
            "open_positions": open_pos_data,
            "journal": journal_data,
        }

    def render_cli(self) -> str:
        """
        Renders terminal ASCII dashboard for paper trading subsystem.
        """
        data = self.to_dict()
        lines = []

        # Header
        lines.append("+- PAPER PORTFOLIO SNAPSHOT ---------------------------------------------------+")

        # Snapshot Section
        if data["snapshot"]:
            snap = data["snapshot"]
            lines.append(
                f"| TOTAL CAPITAL: {snap['total_capital']:,.2f} INR  | AVAILABLE: {snap['available_capital']:,.2f} INR |"
            )
            lines.append(
                f"| ALLOCATED:     {snap['allocated_capital']:,.2f} INR  | OPEN POS:  {snap['open_positions_count']:<3} | CLOSED: {snap['closed_trades_count']:<3}  |"
            )
            lines.append(
                f"| REALIZED P&L:  {snap['realized_pnl']:+,.2f} INR  | UNREALIZED MTM: {snap['unrealized_pnl']:+,.2f} INR      |"
            )
            lines.append(
                f"| TOTAL PORTFOLIO P&L: {snap['total_pnl']:+,.2f} INR                                        |"
            )
        else:
            lines.append("| Paper Portfolio Snapshot: NOT ACTIVE (Run pipeline first)                   |")

        lines.append("| " + "="*76 + " |")

        # Open Positions Sub-section
        lines.append("| ACTIVE SIMULATED POSITIONS:                                                  |")
        if data["open_positions"]:
            for op in data["open_positions"][:4]:
                act_col = f"{op['action']} {op['lots']} Lots"
                lines.append(
                    f"|   * {op['tradingsymbol']:<22} | {act_col:<14} | MTM: {op['current_mtm']:+,.2f} INR ({op['holding_time_seconds']:.0f}s) |"
                )
        else:
            lines.append("|   No active simulated positions.                                             |")

        lines.append("| " + "="*76 + " |")

        # Performance Section
        lines.append("| HISTORICAL PERFORMANCE SUMMARY:                                              |")
        if data["performance"]:
            perf = data["performance"]
            lines.append(
                f"| Trades: {perf['total_trades']:<4} | Win Rate: {perf['win_rate']:.1f}% | Loss Rate: {perf['loss_rate']:.1f}% | PF: {perf['profit_factor']:.2f} |"
            )
            lines.append(
                f"| Avg Profit: {perf['average_profit']:+,.2f} | Avg Loss: {perf['average_loss']:+,.2f} | Expectancy: {perf['expectancy']:+,.2f} |"
            )
            lines.append("| " + "-"*76 + " |")
            lines.append("| Performance by Strategy:                                                     |")
            for s in perf["by_strategy"][:3]:
                lines.append(
                    f"|   * {s['strategy_name']:<12} | Trades: {s['total_trades']:<3} | WinRate: {s['win_rate']:>5.1f}% | PNL: {s['total_pnl']:+,.2f} INR |"
                )
        else:
            lines.append("|   No performance metrics compiled.                                           |")

        lines.append("| " + "="*76 + " |")

        # Journal Section
        lines.append("| RECENT TRADE JOURNAL ENTRIES:                                                |")
        if data["journal"]:
            for jr in data["journal"][:3]:
                outcome_sign = "+" if jr["pnl"] >= 0 else ""
                lines.append(
                    f"|   * {jr['tradingsymbol']:<22} | Exit: {jr['exit_reason']:<12} | PNL: {outcome_sign}{jr['pnl']:,.2f} ({jr['pnl_pct']:.1f}%) |"
                )
        else:
            lines.append("|   Journal empty. No trades completed.                                        |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
