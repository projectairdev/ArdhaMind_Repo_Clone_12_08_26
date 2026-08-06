from __future__ import annotations

from typing import Optional
from src.models import PaperPosition, TradeJournalEntry


class PaperJournalManager:
    """
    Stateless manager responsible for creating trade journal entries when positions are completed.
    """

    @staticmethod
    def create_journal_entry(
        position: PaperPosition,
        exit_time: str,
        exit_premium: float,
        exit_reason: str,
        decision_summary: Optional[str] = None,
        explanation_summary: Optional[str] = None,
        market_score_val: float = 75.0,
        market_score_grade: str = "B",
        market_regime: str = "VOLATILE",
        notes: str = "",
    ) -> TradeJournalEntry:
        """
        Creates a completed TradeJournalEntry from a PaperPosition and exit metrics.
        """
        trade = position.trade
        entry_premium = trade.premium
        lots = trade.lots
        lot_size = 50 if "NIFTY" in trade.tradingsymbol else 1

        # Calculate P&L based on trade action (BUY or SELL)
        if trade.action == "BUY":
            pnl = (exit_premium - entry_premium) * lots * lot_size
            pnl_pct = ((exit_premium - entry_premium) / entry_premium) * 100.0
        else:  # "SELL"
            pnl = (entry_premium - exit_premium) * lots * lot_size
            pnl_pct = ((entry_premium - exit_premium) / entry_premium) * 100.0

        outcome = "WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "FLAT")

        # Derive confidence band
        if trade.confidence_score >= 80.0:
            confidence_band = "HIGH"
        elif trade.confidence_score >= 50.0:
            confidence_band = "MEDIUM"
        else:
            confidence_band = "LOW"

        # Safe summaries if None
        resolved_decision_summary = decision_summary or f"Simulated {trade.action} on {trade.tradingsymbol}"
        resolved_explanation_summary = explanation_summary or f"Stateless paper trading exit reason: {exit_reason}"

        return TradeJournalEntry(
            entry_id=f"JE_{trade.trade_id}",
            trade_id=trade.trade_id,
            candidate_id=trade.candidate_id,
            tradingsymbol=trade.tradingsymbol,
            decision_summary=resolved_decision_summary,
            explanation_summary=resolved_explanation_summary,
            market_score_val=market_score_val,
            market_score_grade=market_score_grade,
            confidence_score=trade.confidence_score,
            risk_grade=trade.risk_grade,
            strategy_name=trade.strategy_name,
            entry_time=trade.entry_time,
            entry_premium=entry_premium,
            entry_capital=trade.capital,
            entry_lots=lots,
            exit_time=exit_time,
            exit_premium=exit_premium,
            exit_reason=exit_reason,
            pnl=pnl,
            pnl_pct=pnl_pct,
            duration_seconds=position.holding_time_seconds,
            outcome=outcome,
            market_regime=market_regime,
            confidence_band=confidence_band,
            notes=notes,
        )
