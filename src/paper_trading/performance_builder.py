from __future__ import annotations

from typing import List, Dict
from src.models import (
    PerformanceReport,
    PaperStrategyPerformance,
    RegimePerformance,
    ConfidenceBandPerformance,
    TradeJournalEntry,
)


class PaperPerformanceBuilder:
    """
    Stateless builder responsible for compiling historical paper trading performance reports.
    """

    @staticmethod
    def build_report(entries: List[TradeJournalEntry]) -> PerformanceReport:
        """
        Calculates win rates, average P&L, profit factors, and expectancy.
        Groups metrics by strategy, market regime, and confidence bands.
        """
        total_trades = len(entries)
        if total_trades == 0:
            return PerformanceReport(
                total_trades=0,
                win_rate=0.0,
                loss_rate=0.0,
                average_profit=0.0,
                average_loss=0.0,
                profit_factor=1.0,
                expectancy=0.0,
                average_holding_time_seconds=0.0,
                by_strategy=[],
                by_regime=[],
                by_confidence_band=[],
            )

        wins = [e for e in entries if e.pnl > 0]
        losses = [e for e in entries if e.pnl < 0]

        win_rate = (len(wins) / total_trades) * 100.0
        loss_rate = (len(losses) / total_trades) * 100.0

        average_profit = sum(w.pnl for w in wins) / len(wins) if wins else 0.0
        average_loss = sum(l.pnl for l in losses) / len(losses) if losses else 0.0

        gross_profits = sum(w.pnl for w in wins)
        gross_losses = abs(sum(l.pnl for l in losses))
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else (gross_profits if gross_profits > 0 else 1.0)

        # Expectancy formula: (Win% * Avg Profit) + (Loss% * Avg Loss)
        # Note: average_loss is negative, so we do addition directly.
        expectancy = ((win_rate / 100.0) * average_profit) + ((loss_rate / 100.0) * average_loss)

        avg_holding_time = sum(e.duration_seconds for e in entries) / total_trades

        # Group by Strategy
        strategy_groups: Dict[str, List[TradeJournalEntry]] = {}
        for e in entries:
            strategy_groups.setdefault(e.strategy_name, []).append(e)

        by_strategy: List[PaperStrategyPerformance] = []
        for strat, strat_entries in strategy_groups.items():
            strat_wins = [x for x in strat_entries if x.pnl > 0]
            by_strategy.append(
                PaperStrategyPerformance(
                    strategy_name=strat,
                    total_trades=len(strat_entries),
                    win_rate=(len(strat_wins) / len(strat_entries)) * 100.0,
                    total_pnl=sum(x.pnl for x in strat_entries),
                )
            )

        # Group by Market Regime
        regime_groups: Dict[str, List[TradeJournalEntry]] = {}
        for e in entries:
            regime_groups.setdefault(e.market_regime, []).append(e)

        by_regime: List[RegimePerformance] = []
        for regime, regime_entries in regime_groups.items():
            regime_wins = [x for x in regime_entries if x.pnl > 0]
            by_regime.append(
                RegimePerformance(
                    market_regime=regime,
                    total_trades=len(regime_entries),
                    win_rate=(len(regime_wins) / len(regime_entries)) * 100.0,
                    total_pnl=sum(x.pnl for x in regime_entries),
                )
            )

        # Group by Confidence Band
        band_groups: Dict[str, List[TradeJournalEntry]] = {}
        for e in entries:
            band_groups.setdefault(e.confidence_band, []).append(e)

        by_confidence_band: List[ConfidenceBandPerformance] = []
        for band, band_entries in band_groups.items():
            band_wins = [x for x in band_entries if x.pnl > 0]
            by_confidence_band.append(
                ConfidenceBandPerformance(
                    confidence_band=band,
                    total_trades=len(band_entries),
                    win_rate=(len(band_wins) / len(band_entries)) * 100.0,
                    total_pnl=sum(x.pnl for x in band_entries),
                )
            )

        return PerformanceReport(
            total_trades=total_trades,
            win_rate=win_rate,
            loss_rate=loss_rate,
            average_profit=average_profit,
            average_loss=average_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            average_holding_time_seconds=avg_holding_time,
            by_strategy=by_strategy,
            by_regime=by_regime,
            by_confidence_band=by_confidence_band,
        )
