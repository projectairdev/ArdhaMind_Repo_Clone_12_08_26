from __future__ import annotations

from typing import Dict, List, Optional, Any
from src.models import (
    DecisionReport,
    ConfidenceReport,
    RiskReport,
    MarketScore,
    MarketContext,
    PortfolioSnapshot,
    PerformanceReport,
    PaperTrade,
    PaperPosition,
    TradeJournalEntry,
)
from src.paper_trading.portfolio_manager import PaperPortfolioManager
from src.paper_trading.entry_manager import PaperEntryManager
from src.paper_trading.performance_builder import PaperPerformanceBuilder


class PaperTradingPipeline:
    """
    Paper Trading Pipeline coordinates entries, exits, position tracking, and performance reporting.
    """

    def __init__(self, portfolio_file: str = "paper_portfolio.json") -> None:
        self.portfolio_manager = PaperPortfolioManager(file_path=portfolio_file)

    def execute_step(
        self,
        decision_report: Optional[DecisionReport] = None,
        confidence_report: Optional[ConfidenceReport] = None,
        risk_report: Optional[RiskReport] = None,
        market_score: Optional[MarketScore] = None,
        market_context: Optional[MarketContext] = None,
        market_prices: Optional[Dict[str, float]] = None,
        elapsed_seconds: float = 60.0,
        manual_close_candidates: Optional[List[str]] = None,
        plan_invalidated_candidates: Optional[List[str]] = None,
        is_expired_candidates: Optional[List[str]] = None,
        target_premiums: Optional[Dict[str, float]] = None,
        stop_premiums: Optional[Dict[str, float]] = None,
        max_holding_time: Optional[float] = None,
        current_time_str: str = "2026-07-10T16:00:00",
    ) -> Dict[str, Any]:
        """
        Processes one step of the paper trading lifecycle:
        1. Updates open positions' current premiums and holding times.
        2. Evaluates exit triggers (target hit, stop hit, time exit, manual exit, plan invalidation).
        3. Generates paper entry trades from new BUY/SELL decisions.
        4. Compiles the updated portfolio snapshot and performance report.
        """
        if market_prices is None:
            market_prices = {}

        # Step 1: Update MTM/Premium of existing open positions
        self.portfolio_manager.update_market_prices(market_prices, elapsed_seconds)

        # Step 2: Evaluate exits
        decision_summary = None
        explanation_summary = None
        if decision_report:
            decision_summary = decision_report.summary.portfolio_status_message
            if decision_report.candidate_decisions:
                explanation_summary = " | ".join(
                    [d.explanation for d in decision_report.candidate_decisions[:2] if d.explanation]
                )

        market_score_val = market_score.overall_score if market_score else 75.0
        market_score_grade = market_score.letter_grade if market_score else "B"
        market_regime = market_context.market_regime if market_context else "VOLATILE"

        exited_journal_entries = self.portfolio_manager.process_exits(
            market_prices=market_prices,
            decision_summary=decision_summary,
            explanation_summary=explanation_summary,
            market_score_val=market_score_val,
            market_score_grade=market_score_grade,
            market_regime=market_regime,
            target_premiums=target_premiums,
            stop_premiums=stop_premiums,
            max_holding_time=max_holding_time,
            plan_invalidated_candidates=plan_invalidated_candidates,
            is_expired_candidates=is_expired_candidates,
            manual_close_candidates=manual_close_candidates,
            exit_time=current_time_str,
        )

        # Step 3: Evaluate and execute entries
        new_entered_trades: List[PaperTrade] = []
        if decision_report:
            entry_trades = PaperEntryManager.evaluate_entries(
                decision_report=decision_report,
                confidence_report=confidence_report,
                risk_report=risk_report,
                market_prices=market_prices,
            )
            for trade in entry_trades:
                success = self.portfolio_manager.add_trade(trade)
                if success:
                    new_entered_trades.append(trade)

        # Step 4: Build Snapshot & Performance Report
        snapshot = self.portfolio_manager.get_snapshot()
        performance = PaperPerformanceBuilder.build_report(self.portfolio_manager.closed_trades)

        return {
            "snapshot": snapshot,
            "performance": performance,
            "new_entered_trades": new_entered_trades,
            "new_exited_trades": exited_journal_entries,
            "open_positions": self.portfolio_manager.open_positions,
            "journal": self.portfolio_manager.closed_trades,
        }
