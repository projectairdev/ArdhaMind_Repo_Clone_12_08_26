from __future__ import annotations

import unittest
from typing import List
from src.models import (
    TradeJournalEntry,
    PortfolioSnapshot,
    PaperTrade,
    AnalyticsReport,
)
from src.analytics_engine import (
    PerformanceMetricsCalculator,
    StrategyAnalyser,
    RegimeAnalyser,
    ConfidenceAnalyser,
    RiskAnalyser,
    TimeAnalyser,
    PortfolioAnalyser,
    SummaryBuilder,
    PerformanceAnalyticsBuilder,
)
from src.dashboard.dashboard_builder import TradingWorkstationDashboard

class TestPerformanceAnalytics(unittest.TestCase):
    def setUp(self) -> None:
        # Construct sample TradeJournalEntry objects
        self.entries = [
            TradeJournalEntry(
                entry_id="JE_1",
                trade_id="T_1",
                candidate_id="C_1",
                tradingsymbol="NIFTY26NOV24200CE",
                decision_summary="Bullish trend continuation",
                explanation_summary="Market score high, bullish breakout confirmed.",
                market_score_val=85.0,
                market_score_grade="A",
                confidence_score=92.0,
                risk_grade="LOW",
                strategy_name="MOMENTUM",
                entry_time="2026-07-10T09:30:00",
                entry_premium=100.0,
                entry_capital=50000.0,
                entry_lots=10,
                exit_time="2026-07-10T10:15:00",
                exit_premium=120.0,
                exit_reason="TARGET",
                pnl=10000.0,
                pnl_pct=20.0,
                duration_seconds=2700.0,
                outcome="WIN",
                market_regime="BULLISH",
                confidence_band="HIGH",
                notes="classification: EXCELLENT, bias: BULLISH",
            ),
            TradeJournalEntry(
                entry_id="JE_2",
                trade_id="T_2",
                candidate_id="C_2",
                tradingsymbol="BANKNIFTY26NOV24400PE",
                decision_summary="Bearish mean reversion",
                explanation_summary="Overextended rally, option resistance heavy.",
                market_score_val=45.0,
                market_score_grade="D",
                confidence_score=55.0,
                risk_grade="HIGH",
                strategy_name="REVERSION",
                entry_time="2026-07-10T11:00:00",
                entry_premium=200.0,
                entry_capital=100000.0,
                entry_lots=10,
                exit_time="2026-07-10T11:30:00",
                exit_premium=150.0,
                exit_reason="STOP_LOSS",
                pnl=-25000.0,
                pnl_pct=-25.0,
                duration_seconds=1800.0,
                outcome="LOSS",
                market_regime="VOLATILE",
                confidence_band="MEDIUM",
                notes="classification: POOR, bias: BEARISH",
            ),
            TradeJournalEntry(
                entry_id="JE_3",
                trade_id="T_3",
                candidate_id="C_3",
                tradingsymbol="NIFTY26NOV24300CE",
                decision_summary="Scalping entry on support",
                explanation_summary="Orderbook imbalance positive.",
                market_score_val=75.0,
                market_score_grade="B",
                confidence_score=78.0,
                risk_grade="MEDIUM",
                strategy_name="SCALPING",
                entry_time="2026-07-11T14:00:00",
                entry_premium=150.0,
                entry_capital=75000.0,
                entry_lots=10,
                exit_time="2026-07-11T14:10:00",
                exit_premium=165.0,
                exit_reason="TARGET",
                pnl=7500.0,
                pnl_pct=10.0,
                duration_seconds=600.0,
                outcome="WIN",
                market_regime="TRENDING",
                confidence_band="MEDIUM",
                notes="classification: GOOD, bias: BULLISH",
            )
        ]

    def test_overall_metrics(self) -> None:
        metrics = PerformanceMetricsCalculator.calculate(self.entries)

        self.assertEqual(metrics.total_trades, 3)
        self.assertEqual(metrics.winning_trades, 2)
        self.assertEqual(metrics.losing_trades, 1)
        self.assertAlmostEqual(metrics.win_rate, 66.6666666, places=4)

        # Gross profit: 10000 + 7500 = 17500. Gross loss: 25000
        # Profit factor: 17500 / 25000 = 0.70
        self.assertAlmostEqual(metrics.profit_factor, 0.70, places=2)

        # Expectancy: (2/3 * 8750) + (1/3 * -25000) = 5833.333 - 8333.333 = -2500.00
        self.assertAlmostEqual(metrics.expectancy, -2500.0, places=2)

        # Average holding time: (2700 + 1800 + 600) / 3 = 1700
        self.assertEqual(metrics.average_holding_time, 1700.0)

        self.assertEqual(metrics.largest_winner, 10000.0)
        self.assertEqual(metrics.largest_loser, -25000.0)

    def test_drawdown_and_recovery(self) -> None:
        # Chronological order of exits:
        # JE_1 (exit at 10:15) -> pnl +10000, equity = 1,010,000, peak = 1,010,000, dd = 0
        # JE_2 (exit at 11:30) -> pnl -25000, equity = 985,000, peak = 1,010,000, dd = 25000
        # JE_3 (exit next day) -> pnl +7500, equity = 992,500, peak = 1,010,000, dd = 17500
        # Max drawdown should be 25000.0
        metrics = PerformanceMetricsCalculator.calculate(self.entries)
        self.assertEqual(metrics.maximum_drawdown, 25000.0)

        # Recovery factor: total_pnl / max_dd = (10000 - 25000 + 7500) / 25000 = -7500 / 25000 = -0.30
        self.assertAlmostEqual(metrics.recovery_factor, -0.30, places=2)

    def test_strategy_analysis(self) -> None:
        strat_perf = StrategyAnalyser.analyze(self.entries)
        self.assertEqual(len(strat_perf), 3)

        mom = next(s for s in strat_perf if s.strategy_name == "MOMENTUM")
        self.assertEqual(mom.total_trades, 1)
        self.assertEqual(mom.win_rate, 100.0)
        self.assertEqual(mom.average_return, 10000.0)
        self.assertEqual(mom.capital_utilization, 50000.0)

    def test_regime_analysis(self) -> None:
        market_perf = RegimeAnalyser.analyze(self.entries)

        regimes = market_perf.by_regime
        self.assertEqual(len(regimes), 3)

        self.assertEqual(RegimeAnalyser.extract_opportunity(self.entries[0]), "EXCELLENT")
        self.assertEqual(RegimeAnalyser.extract_opportunity(self.entries[1]), "POOR")
        self.assertEqual(RegimeAnalyser.extract_opportunity(self.entries[2]), "GOOD")

        self.assertEqual(RegimeAnalyser.extract_directional_bias(self.entries[0]), "BULLISH")
        self.assertEqual(RegimeAnalyser.extract_directional_bias(self.entries[1]), "BEARISH")

        opps = market_perf.by_opportunity
        self.assertEqual(len(opps), 3)

        biases = market_perf.by_bias
        self.assertEqual(len(biases), 2)

    def test_confidence_analysis(self) -> None:
        conf_perf = ConfidenceAnalyser.analyze(self.entries)
        self.assertEqual(len(conf_perf), 3)

        bands = [c.confidence_band for c in conf_perf]
        self.assertIn("90–100", bands)
        self.assertIn("50–60", bands)
        self.assertIn("70–80", bands)

    def test_risk_analysis(self) -> None:
        risk_perf = RiskAnalyser.analyze(self.entries, total_portfolio_capital=1000000.0)
        self.assertEqual(len(risk_perf), 3)

        low = next(r for r in risk_perf if r.risk_grade == "LOW")
        self.assertEqual(low.total_trades, 1)
        self.assertEqual(low.portfolio_utilization, 5.0)

    def test_time_analysis(self) -> None:
        time_perf = TimeAnalyser.analyze(self.entries)
        self.assertIn(9, time_perf.by_entry_hour)
        self.assertIn(11, time_perf.by_entry_hour)
        self.assertIn(14, time_perf.by_entry_hour)

        self.assertIn("Friday", time_perf.by_day_of_week)
        self.assertIn("Saturday", time_perf.by_day_of_week)

    def test_portfolio_analysis(self) -> None:
        port_perf = PortfolioAnalyser.analyze(self.entries, initial_capital=1000000.0)
        self.assertEqual(port_perf.initial_capital, 1000000.0)
        self.assertEqual(port_perf.final_capital, 992500.0)
        self.assertEqual(port_perf.total_pnl, -7500.0)
        self.assertEqual(port_perf.return_on_capital, -0.75)
        self.assertEqual(port_perf.maximum_drawdown, 25000.0)

    def test_summary_builder(self) -> None:
        overall = PerformanceMetricsCalculator.calculate(self.entries)
        strategies = StrategyAnalyser.analyze(self.entries)
        market = RegimeAnalyser.analyze(self.entries)
        confidence = ConfidenceAnalyser.analyze(self.entries)
        risk = RiskAnalyser.analyze(self.entries, 1000000.0)
        time_perf = TimeAnalyser.analyze(self.entries)
        portfolio = PortfolioAnalyser.analyze(self.entries, 1000000.0)

        summary = SummaryBuilder.build(
            overall=overall,
            strategies=strategies,
            market=market,
            confidence=confidence,
            risk=risk,
            time_perf=time_perf,
            portfolio=portfolio,
        )

        self.assertTrue(len(summary.strengths) > 0)
        self.assertTrue(len(summary.weaknesses) > 0)
        self.assertTrue(len(summary.recommendations) > 0)

    def test_master_builder_and_dashboard(self) -> None:
        report = PerformanceAnalyticsBuilder.build_report(self.entries, initial_capital=1000000.0)
        self.assertIsInstance(report, AnalyticsReport)

        db = TradingWorkstationDashboard(
            journal=self.entries,
            analytics_report=report,
        )
        data = db.to_dict()
        self.assertIn("performance_analytics", data)
        self.assertEqual(data["performance_analytics"]["report_id"], report.report_id)

        cli_output = db.render_cli()
        self.assertIn("PERFORMANCE ANALYTICS REPORT", cli_output)
        self.assertIn("SYSTEM DIAGNOSTIC SUMMARY", cli_output)
        self.assertIn("PORTFOLIO STATISTICS", cli_output)
