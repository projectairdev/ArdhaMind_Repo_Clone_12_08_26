from __future__ import annotations

import os
import unittest
from typing import Dict, List
from src.models import (
    DecisionReport,
    CandidateDecision,
    DecisionSummary,
    DecisionStatistics,
    ConfidenceReport,
    CandidateConfidence,
    ConfidenceSummary,
    RiskReport,
    CandidateRisk,
    CapitalAllocation,
    MarketScore,
    MarketContext,
    PaperTrade,
    PaperPosition,
    TradeJournalEntry,
    PaperStrategyPerformance,
)
from src.paper_trading.entry_manager import PaperEntryManager
from src.paper_trading.position_manager import PaperPositionManager
from src.paper_trading.exit_manager import PaperExitManager
from src.paper_trading.journal_manager import PaperJournalManager
from src.paper_trading.performance_builder import PaperPerformanceBuilder
from src.paper_trading.portfolio_manager import PaperPortfolioManager
from src.pipeline.paper_trading_pipeline import PaperTradingPipeline
from src.dashboard.paper_trading_panel import PaperTradingPanel


class TestPaperTradingSubsystem(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_portfolio_file = "test_paper_portfolio.json"
        if os.path.exists(self.temp_portfolio_file):
            os.remove(self.temp_portfolio_file)

        # Mock Candidate details
        self.candidate_id = "SCALPING_NIFTY26NOV24200CE"
        self.tradingsymbol = "NIFTY26NOV24200CE"

        # Mock Decision Report
        self.decision_report = DecisionReport(
            report_id="DR_TEST_001",
            risk_report_id="RR_TEST_001",
            candidate_decisions=[
                CandidateDecision(
                    candidate_id=self.candidate_id,
                    tradingsymbol=self.tradingsymbol,
                    strategy_name="SCALPING",
                    decision="BUY",
                    priority_score=95.0,
                    execution_priority=1,
                    allocated_capital=50000.0,
                    allocated_lots=2,
                    explanation="Strong momentum buy signal",
                ),
                CandidateDecision(
                    candidate_id="SCALPING_NIFTY26NOV24200PE",
                    tradingsymbol="NIFTY26NOV24200PE",
                    strategy_name="SCALPING",
                    decision="WATCH",
                    priority_score=45.0,
                    execution_priority=-1,
                    allocated_capital=0.0,
                    allocated_lots=0,
                    explanation="Wait for breakout",
                ),
            ],
            summary=DecisionSummary("EXECUTE", self.candidate_id, "Portfolio parameters healthy"),
            stats=DecisionStatistics(2, 1, 0, 1, 0, 0, 50000.0),
            timestamp="2026-07-10T10:00:00",
        )

        # Mock Confidence Report
        self.confidence_report = ConfidenceReport(
            report_id="CR_TEST_001",
            trade_plan_id="TP_TEST_001",
            candidate_confidences=[
                CandidateConfidence(
                    candidate_id=self.candidate_id,
                    tradingsymbol=self.tradingsymbol,
                    strategy_name="SCALPING",
                    confidence_score=88.0,
                    raw_score=85.0,
                )
            ],
            summary=ConfidenceSummary(self.candidate_id, self.candidate_id, 88.0, 1, ["High confidence"]),
        )

        # Mock Risk Report
        self.risk_report = RiskReport(
            report_id="RR_TEST_001",
            confidence_report_id="CR_TEST_001",
            candidate_risks=[
                CandidateRisk(
                    candidate_id=self.candidate_id,
                    tradingsymbol=self.tradingsymbol,
                    strategy_name="SCALPING",
                    risk_grade="LOW_RISK",
                    capital_allocation=CapitalAllocation(
                        allocated_capital=50000.0,
                        allocated_lots=2,
                        risk_amount=1000.0,
                        utilization_pct=5.0,
                        confidence_score=88.0,
                        risk_multiplier=1.0,
                    ),
                    is_approved=True,
                )
            ],
        )

    def tearDown(self) -> None:
        if os.path.exists(self.temp_portfolio_file):
            os.remove(self.temp_portfolio_file)

    def test_entry_manager_evaluates_only_buy_or_sell(self) -> None:
        trades = PaperEntryManager.evaluate_entries(
            decision_report=self.decision_report,
            confidence_report=self.confidence_report,
            risk_report=self.risk_report,
            market_prices={self.tradingsymbol: 500.0},
        )
        self.assertEqual(len(trades), 1)
        trade = trades[0]
        self.assertEqual(trade.candidate_id, self.candidate_id)
        self.assertEqual(trade.action, "BUY")
        self.assertEqual(trade.premium, 500.0)
        self.assertEqual(trade.lots, 2)
        self.assertEqual(trade.capital, 50000.0)
        self.assertEqual(trade.confidence_score, 88.0)
        self.assertEqual(trade.risk_grade, "LOW_RISK")

    def test_position_tracking_updates_mtm_and_drawdown(self) -> None:
        # Create Trade
        trades = PaperEntryManager.evaluate_entries(
            self.decision_report, self.confidence_report, self.risk_report, {self.tradingsymbol: 500.0}
        )
        trade = trades[0]

        # Initialize Position
        pos = PaperPositionManager.create_position(trade)
        self.assertEqual(pos.status, "OPEN")
        self.assertEqual(pos.current_mtm, 0.0)

        # Update Position - Price Goes Up (Nifty lot size = 50, lots = 2, total multiplier = 100)
        pos_up = PaperPositionManager.update_position(pos, current_premium=550.0, elapsed_seconds=60.0)
        self.assertEqual(pos_up.current_premium, 550.0)
        self.assertEqual(pos_up.current_mtm, (550.0 - 500.0) * 2 * 50)  # +5000.0
        self.assertEqual(pos_up.peak_mtm, 5000.0)
        self.assertEqual(pos_up.drawdown, 0.0)
        self.assertEqual(pos_up.holding_time_seconds, 60.0)

        # Update Position - Price Goes Down from Peak
        pos_down = PaperPositionManager.update_position(pos_up, current_premium=520.0, elapsed_seconds=30.0)
        self.assertEqual(pos_down.current_mtm, (520.0 - 500.0) * 2 * 50)  # +2000.0
        self.assertEqual(pos_down.peak_mtm, 5000.0)
        self.assertEqual(pos_down.drawdown, 3000.0)  # Peak - Current MTM
        self.assertEqual(pos_down.holding_time_seconds, 90.0)

    def test_exit_manager_handles_all_reasons(self) -> None:
        trades = PaperEntryManager.evaluate_entries(
            self.decision_report, self.confidence_report, self.risk_report, {self.tradingsymbol: 500.0}
        )
        pos = PaperPositionManager.create_position(trades[0])

        # Target Hit
        reason_target = PaperExitManager.evaluate_exit(pos, current_premium=601.0, target_premium=600.0)
        self.assertEqual(reason_target, "Target Hit")

        # Stop Hit
        reason_stop = PaperExitManager.evaluate_exit(pos, current_premium=449.0, stop_premium=450.0)
        self.assertEqual(reason_stop, "Stop Hit")

        # Time Exit
        pos_timed = PaperPositionManager.update_position(pos, 500.0, 3600.0)
        reason_time = PaperExitManager.evaluate_exit(pos_timed, current_premium=500.0, max_holding_time=3500.0)
        self.assertEqual(reason_time, "Time Exit")

        # Manual Exit
        reason_manual = PaperExitManager.evaluate_exit(pos, 500.0, manual_close=True)
        self.assertEqual(reason_manual, "Manual Close")

        # Plan Invalidated
        reason_invalid = PaperExitManager.evaluate_exit(pos, 500.0, plan_invalidated=True)
        self.assertEqual(reason_invalid, "Plan Invalidated")

        # Expiry Exit
        reason_expired = PaperExitManager.evaluate_exit(pos, 500.0, is_expired=True)
        self.assertEqual(reason_expired, "Expiry Exit")

    def test_journal_entry_generation(self) -> None:
        trades = PaperEntryManager.evaluate_entries(
            self.decision_report, self.confidence_report, self.risk_report, {self.tradingsymbol: 500.0}
        )
        pos = PaperPositionManager.create_position(trades[0])
        pos_updated = PaperPositionManager.update_position(pos, 550.0, 120.0)

        entry = PaperJournalManager.create_journal_entry(
            position=pos_updated,
            exit_time="2026-07-10T10:02:00",
            exit_premium=550.0,
            exit_reason="Target Hit",
            decision_summary="Overall bullish execute",
            explanation_summary="Exited on hitting target",
            market_score_val=80.0,
            market_score_grade="A",
            market_regime="UPTREND",
        )

        self.assertEqual(entry.outcome, "WIN")
        self.assertEqual(entry.pnl, 5000.0)
        self.assertEqual(entry.pnl_pct, 10.0)
        self.assertEqual(entry.duration_seconds, 120.0)
        self.assertEqual(entry.market_regime, "UPTREND")
        self.assertEqual(entry.confidence_band, "HIGH")

    def test_portfolio_persistence_and_capital_realization(self) -> None:
        manager = PaperPortfolioManager(file_path=self.temp_portfolio_file, default_capital=100000.0)
        self.assertEqual(manager.total_capital, 100000.0)
        self.assertEqual(len(manager.open_positions), 0)

        # Evaluate and enter trade
        trades = PaperEntryManager.evaluate_entries(
            self.decision_report, self.confidence_report, self.risk_report, {self.tradingsymbol: 500.0}
        )
        success = manager.add_trade(trades[0])
        self.assertTrue(success)
        self.assertEqual(len(manager.open_positions), 1)
        self.assertEqual(manager.get_allocated_capital(), 50000.0)
        self.assertEqual(manager.get_available_capital(), 50000.0)

        # Simulate update prices
        manager.update_market_prices({self.tradingsymbol: 550.0}, 60.0)
        self.assertEqual(manager.open_positions[0].current_mtm, 5000.0)

        # Exit trade and check capital increase
        exits = manager.process_exits(
            market_prices={self.tradingsymbol: 550.0},
            target_premiums={self.tradingsymbol: 540.0},  # triggers target hit since 550 >= 540
            exit_time="2026-07-10T10:01:00",
        )
        self.assertEqual(len(exits), 1)
        self.assertEqual(exits[0].exit_reason, "Target Hit")
        self.assertEqual(len(manager.open_positions), 0)

        # Realized PNL is 5000, so total capital should be 105000
        self.assertEqual(manager.total_capital, 105000.0)
        self.assertEqual(manager.get_allocated_capital(), 0.0)

        # Check saved state loads correctly
        loaded_manager = PaperPortfolioManager(file_path=self.temp_portfolio_file)
        self.assertEqual(loaded_manager.total_capital, 105000.0)
        self.assertEqual(len(loaded_manager.closed_trades), 1)

    def test_performance_builder_calculates_correct_ratios(self) -> None:
        # Create mock journal entries
        j1 = TradeJournalEntry(
            entry_id="JE_1",
            trade_id="T_1",
            candidate_id="C1",
            tradingsymbol="S1",
            decision_summary="D1",
            explanation_summary="E1",
            market_score_val=75.0,
            market_score_grade="B",
            confidence_score=85.0,
            risk_grade="LOW",
            strategy_name="SCALPING",
            entry_time="T1",
            entry_premium=100.0,
            entry_capital=10000.0,
            entry_lots=2,
            exit_time="T2",
            exit_premium=120.0,
            exit_reason="Target Hit",
            pnl=2000.0,
            pnl_pct=20.0,
            duration_seconds=120.0,
            outcome="WIN",
            market_regime="VOLATILE",
            confidence_band="HIGH",
        )
        j2 = TradeJournalEntry(
            entry_id="JE_2",
            trade_id="T_2",
            candidate_id="C2",
            tradingsymbol="S2",
            decision_summary="D2",
            explanation_summary="E2",
            market_score_val=65.0,
            market_score_grade="C",
            confidence_score=55.0,
            risk_grade="MEDIUM",
            strategy_name="BREAKOUT",
            entry_time="T3",
            entry_premium=200.0,
            entry_capital=20000.0,
            entry_lots=2,
            exit_time="T4",
            exit_premium=180.0,
            exit_reason="Stop Hit",
            pnl=-2000.0,
            pnl_pct=-10.0,
            duration_seconds=180.0,
            outcome="LOSS",
            market_regime="VOLATILE",
            confidence_band="MEDIUM",
        )

        entries = [j1, j2]
        report = PaperPerformanceBuilder.build_report(entries)

        self.assertEqual(report.total_trades, 2)
        self.assertEqual(report.win_rate, 50.0)
        self.assertEqual(report.loss_rate, 50.0)
        self.assertEqual(report.average_profit, 2000.0)
        self.assertEqual(report.average_loss, -2000.0)
        self.assertEqual(report.profit_factor, 1.0)
        self.assertEqual(report.expectancy, 0.0)  # (0.5 * 2000) + (0.5 * -2000) = 0
        self.assertEqual(report.average_holding_time_seconds, 150.0)

        # Check grouping
        self.assertEqual(len(report.by_strategy), 2)
        self.assertEqual(len(report.by_regime), 1)
        self.assertEqual(len(report.by_confidence_band), 2)

    def test_pipeline_integrates_all_components(self) -> None:
        pipeline = PaperTradingPipeline(portfolio_file=self.temp_portfolio_file)
        pipeline.portfolio_manager.clear_portfolio()

        # Step 1: Execute step with BUY decision and prices
        res = pipeline.execute_step(
            decision_report=self.decision_report,
            confidence_report=self.confidence_report,
            risk_report=self.risk_report,
            market_prices={self.tradingsymbol: 500.0},
        )

        self.assertEqual(len(res["new_entered_trades"]), 1)
        self.assertEqual(len(res["open_positions"]), 1)
        self.assertEqual(len(res["new_exited_trades"]), 0)

        # Step 2: Execute step where price triggers exit target
        res_exit = pipeline.execute_step(
            market_prices={self.tradingsymbol: 610.0},  # Default target triggers (BUY target = 500 * 1.20 = 600.0)
            elapsed_seconds=100.0,
            current_time_str="2026-07-10T10:05:00",
        )

        self.assertEqual(len(res_exit["new_entered_trades"]), 0)
        self.assertEqual(len(res_exit["new_exited_trades"]), 1)
        self.assertEqual(res_exit["new_exited_trades"][0].exit_reason, "Target Hit")
        self.assertEqual(len(res_exit["open_positions"]), 0)
        self.assertEqual(res_exit["performance"].total_trades, 1)
        self.assertEqual(res_exit["performance"].win_rate, 100.0)

    def test_dashboard_panel_to_dict_and_cli_render(self) -> None:
        # Check empty or None handling
        panel = PaperTradingPanel()
        cli_out = panel.render_cli()
        self.assertIn("NOT ACTIVE", cli_out)
        self.assertIn("No active simulated positions", cli_out)

        # Check full data rendering
        pipeline = PaperTradingPipeline(portfolio_file=self.temp_portfolio_file)
        pipeline.portfolio_manager.clear_portfolio()
        
        # Enter a trade
        pipeline.execute_step(
            decision_report=self.decision_report,
            confidence_report=self.confidence_report,
            risk_report=self.risk_report,
            market_prices={self.tradingsymbol: 500.0},
        )
        
        snap = pipeline.portfolio_manager.get_snapshot()
        perf = PaperPerformanceBuilder.build_report(pipeline.portfolio_manager.closed_trades)
        
        panel_full = PaperTradingPanel(
            snapshot=snap,
            performance=perf,
            open_positions=pipeline.portfolio_manager.open_positions,
            journal=pipeline.portfolio_manager.closed_trades,
        )
        
        cli_out_full = panel_full.render_cli()
        self.assertIn("TOTAL CAPITAL", cli_out_full)
        self.assertIn("ACTIVE SIMULATED POSITIONS", cli_out_full)
        self.assertIn("NIFTY26NOV24200CE", cli_out_full)
