from __future__ import annotations

import json
import os
from typing import List, Dict, Optional, Any
from src.models import (
    PaperTrade,
    PaperPosition,
    TradeJournalEntry,
    PortfolioSnapshot,
)
from src.paper_trading.position_manager import PaperPositionManager
from src.paper_trading.exit_manager import PaperExitManager
from src.paper_trading.journal_manager import PaperJournalManager


class PaperPortfolioManager:
    """
    Stateful persistence layer tracking simulated paper trades, active positions, and capital.
    Persists data to paper_portfolio.json.
    """

    def __init__(self, file_path: str = "paper_portfolio.json", default_capital: float = 1000000.0) -> None:
        self.file_path = file_path
        self.default_capital = default_capital
        
        self.total_capital: float = default_capital
        self.open_positions: List[PaperPosition] = []
        self.closed_trades: List[TradeJournalEntry] = []
        
        self.load_portfolio()

    def load_portfolio(self) -> None:
        """
        Loads the paper portfolio state from file_path, or initializes default state if not found.
        """
        if not os.path.exists(self.file_path):
            self.total_capital = self.default_capital
            self.open_positions = []
            self.closed_trades = []
            return

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
            
            self.total_capital = float(data.get("total_capital", self.default_capital))
            
            # Load Open Positions
            self.open_positions = []
            for pos_dict in data.get("open_positions", []):
                trade_dict = pos_dict["trade"]
                trade = PaperTrade(
                    trade_id=trade_dict["trade_id"],
                    decision_id=trade_dict["decision_id"],
                    candidate_id=trade_dict["candidate_id"],
                    tradingsymbol=trade_dict["tradingsymbol"],
                    entry_time=trade_dict["entry_time"],
                    premium=float(trade_dict["premium"]),
                    lots=int(trade_dict["lots"]),
                    capital=float(trade_dict["capital"]),
                    strategy_name=trade_dict["strategy_name"],
                    confidence_score=float(trade_dict["confidence_score"]),
                    risk_grade=trade_dict["risk_grade"],
                    action=trade_dict["action"],
                )
                position = PaperPosition(
                    position_id=pos_dict["position_id"],
                    trade=trade,
                    current_mtm=float(pos_dict["current_mtm"]),
                    peak_mtm=float(pos_dict["peak_mtm"]),
                    drawdown=float(pos_dict["drawdown"]),
                    holding_time_seconds=float(pos_dict["holding_time_seconds"]),
                    status=pos_dict["status"],
                    current_premium=float(pos_dict["current_premium"]),
                )
                self.open_positions.append(position)
                
            # Load Closed Trades
            self.closed_trades = []
            for j_dict in data.get("closed_trades", []):
                entry = TradeJournalEntry(
                    entry_id=j_dict["entry_id"],
                    trade_id=j_dict["trade_id"],
                    candidate_id=j_dict["candidate_id"],
                    tradingsymbol=j_dict["tradingsymbol"],
                    decision_summary=j_dict["decision_summary"],
                    explanation_summary=j_dict["explanation_summary"],
                    market_score_val=float(j_dict["market_score_val"]),
                    market_score_grade=j_dict["market_score_grade"],
                    confidence_score=float(j_dict["confidence_score"]),
                    risk_grade=j_dict["risk_grade"],
                    strategy_name=j_dict["strategy_name"],
                    entry_time=j_dict["entry_time"],
                    entry_premium=float(j_dict["entry_premium"]),
                    entry_capital=float(j_dict["entry_capital"]),
                    entry_lots=int(j_dict["entry_lots"]),
                    exit_time=j_dict["exit_time"],
                    exit_premium=float(j_dict["exit_premium"]),
                    exit_reason=j_dict["exit_reason"],
                    pnl=float(j_dict["pnl"]),
                    pnl_pct=float(j_dict["pnl_pct"]),
                    duration_seconds=float(j_dict["duration_seconds"]),
                    outcome=j_dict["outcome"],
                    market_regime=j_dict.get("market_regime", "VOLATILE"),
                    confidence_band=j_dict.get("confidence_band", "MEDIUM"),
                    notes=j_dict.get("notes", ""),
                )
                self.closed_trades.append(entry)
                
        except Exception as e:
            # Fallback on parse failure
            self.total_capital = self.default_capital
            self.open_positions = []
            self.closed_trades = []

    def save_portfolio(self) -> None:
        """
        Saves the paper portfolio state to file_path.
        """
        try:
            # Serialize Open Positions
            ser_positions = []
            for pos in self.open_positions:
                t = pos.trade
                ser_positions.append({
                    "position_id": pos.position_id,
                    "current_mtm": pos.current_mtm,
                    "peak_mtm": pos.peak_mtm,
                    "drawdown": pos.drawdown,
                    "holding_time_seconds": pos.holding_time_seconds,
                    "status": pos.status,
                    "current_premium": pos.current_premium,
                    "trade": {
                        "trade_id": t.trade_id,
                        "decision_id": t.decision_id,
                        "candidate_id": t.candidate_id,
                        "tradingsymbol": t.tradingsymbol,
                        "entry_time": t.entry_time,
                        "premium": t.premium,
                        "lots": t.lots,
                        "capital": t.capital,
                        "strategy_name": t.strategy_name,
                        "confidence_score": t.confidence_score,
                        "risk_grade": t.risk_grade,
                        "action": t.action,
                    }
                })
                
            # Serialize Closed Trades
            ser_closed = []
            for j in self.closed_trades:
                ser_closed.append({
                    "entry_id": j.entry_id,
                    "trade_id": j.trade_id,
                    "candidate_id": j.candidate_id,
                    "tradingsymbol": j.tradingsymbol,
                    "decision_summary": j.decision_summary,
                    "explanation_summary": j.explanation_summary,
                    "market_score_val": j.market_score_val,
                    "market_score_grade": j.market_score_grade,
                    "confidence_score": j.confidence_score,
                    "risk_grade": j.risk_grade,
                    "strategy_name": j.strategy_name,
                    "entry_time": j.entry_time,
                    "entry_premium": j.entry_premium,
                    "entry_capital": j.entry_capital,
                    "entry_lots": j.entry_lots,
                    "exit_time": j.exit_time,
                    "exit_premium": j.exit_premium,
                    "exit_reason": j.exit_reason,
                    "pnl": j.pnl,
                    "pnl_pct": j.pnl_pct,
                    "duration_seconds": j.duration_seconds,
                    "outcome": j.outcome,
                    "market_regime": j.market_regime,
                    "confidence_band": j.confidence_band,
                    "notes": j.notes,
                })

            data = {
                "total_capital": self.total_capital,
                "open_positions": ser_positions,
                "closed_trades": ser_closed,
            }
            
            with open(self.file_path, "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception:
            pass

    def clear_portfolio(self) -> None:
        """
        Resets the portfolio state.
        """
        self.total_capital = self.default_capital
        self.open_positions = []
        self.closed_trades = []
        self.save_portfolio()

    def get_allocated_capital(self) -> float:
        """
        Calculates total capital currently allocated in open positions.
        """
        return sum(pos.trade.capital for pos in self.open_positions)

    def get_available_capital(self) -> float:
        """
        Calculates remaining unallocated capital.
        """
        return max(0.0, self.total_capital - self.get_allocated_capital())

    def add_trade(self, trade: PaperTrade) -> bool:
        """
        Attempts to enter a paper position for the trade.
        Returns True if successful, False if insufficient capital or position already open.
        """
        # Avoid duplicate trades for the same candidate in open positions
        for pos in self.open_positions:
            if pos.trade.candidate_id == trade.candidate_id:
                return False

        available = self.get_available_capital()
        if available < trade.capital:
            # Insufficient capital
            return False

        position = PaperPositionManager.create_position(trade)
        self.open_positions.append(position)
        self.save_portfolio()
        return True

    def update_market_prices(self, market_prices: Dict[str, float], elapsed_seconds: float) -> None:
        """
        Updates current premiums and calculates MTM for all active positions.
        """
        new_positions = []
        for pos in self.open_positions:
            # Use market price if available, otherwise stay with last current premium
            symbol = pos.trade.tradingsymbol
            price = market_prices.get(symbol) or market_prices.get(pos.trade.candidate_id) or pos.current_premium
            updated_pos = PaperPositionManager.update_position(pos, price, elapsed_seconds)
            new_positions.append(updated_pos)
            
        self.open_positions = new_positions
        self.save_portfolio()

    def process_exits(
        self,
        market_prices: Dict[str, float],
        decision_summary: Optional[str] = None,
        explanation_summary: Optional[str] = None,
        market_score_val: float = 75.0,
        market_score_grade: str = "B",
        market_regime: str = "VOLATILE",
        target_premiums: Optional[Dict[str, float]] = None,
        stop_premiums: Optional[Dict[str, float]] = None,
        max_holding_time: Optional[float] = None,
        plan_invalidated_candidates: Optional[List[str]] = None,
        is_expired_candidates: Optional[List[str]] = None,
        manual_close_candidates: Optional[List[str]] = None,
        exit_time: str = "2026-07-10T16:00:00",
    ) -> List[TradeJournalEntry]:
        """
        Statelessly evaluates active open positions against exit triggers.
        If a trigger is hit, completes the position, materializes capital adjustments, and writes to journal.
        Returns newly completed entries.
        """
        if target_premiums is None:
            target_premiums = {}
        if stop_premiums is None:
            stop_premiums = {}
        if plan_invalidated_candidates is None:
            plan_invalidated_candidates = []
        if is_expired_candidates is None:
            is_expired_candidates = []
        if manual_close_candidates is None:
            manual_close_candidates = []

        active_positions = []
        new_journal_entries = []

        for pos in self.open_positions:
            symbol = pos.trade.tradingsymbol
            candidate_id = pos.trade.candidate_id

            # Determine price
            price = market_prices.get(symbol) or market_prices.get(candidate_id) or pos.current_premium

            # Evaluate triggers
            exit_reason = PaperExitManager.evaluate_exit(
                position=pos,
                current_premium=price,
                target_premium=target_premiums.get(symbol) or target_premiums.get(candidate_id),
                stop_premium=stop_premiums.get(symbol) or stop_premiums.get(candidate_id),
                max_holding_time=max_holding_time,
                manual_close=(symbol in manual_close_candidates or candidate_id in manual_close_candidates),
                plan_invalidated=(symbol in plan_invalidated_candidates or candidate_id in plan_invalidated_candidates),
                is_expired=(symbol in is_expired_candidates or candidate_id in is_expired_candidates),
            )

            if exit_reason:
                # Create Journal Entry
                journal_entry = PaperJournalManager.create_journal_entry(
                    position=pos,
                    exit_time=exit_time,
                    exit_premium=price,
                    exit_reason=exit_reason,
                    decision_summary=decision_summary,
                    explanation_summary=explanation_summary,
                    market_score_val=market_score_val,
                    market_score_grade=market_score_grade,
                    market_regime=market_regime,
                )
                new_journal_entries.append(journal_entry)
                self.closed_trades.append(journal_entry)
                
                # Materialize Capital Realization
                self.total_capital += journal_entry.pnl
            else:
                # Stays open
                active_positions.append(pos)

        self.open_positions = active_positions
        self.save_portfolio()
        return new_journal_entries

    def get_snapshot(self) -> PortfolioSnapshot:
        """
        Generates a summary snapshot of the current paper portfolio state.
        """
        allocated = self.get_allocated_capital()
        available = self.get_available_capital()
        
        # MTM sums
        unrealized_pnl = sum(pos.current_mtm for pos in self.open_positions)
        realized_pnl = sum(entry.pnl for entry in self.closed_trades)
        total_pnl = unrealized_pnl + realized_pnl
        
        # Current system local time style
        import datetime
        now_str = datetime.datetime.now().isoformat()

        return PortfolioSnapshot(
            timestamp=now_str,
            total_capital=self.total_capital,
            allocated_capital=allocated,
            available_capital=available,
            open_positions_count=len(self.open_positions),
            closed_trades_count=len(self.closed_trades),
            total_pnl=total_pnl,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
        )
