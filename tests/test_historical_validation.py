from __future__ import annotations

import datetime
import unittest
import pandas as pd

from src.models import (
    RiskEngineConfig,
    DecisionEngineConfig,
    ValidationReport,
)
from src.pipeline import ValidationPipeline
from src.validation_engine import (
    HistoricalRunner,
    DecisionValidator,
    StatisticsCalculator,
    PerformanceAnalyzer,
    ValidationReportBuilder,
    DailyPipelineResult,
)


class MockKiteClient:
    """
    Mock Kite Connect API client returning highly realistic, custom data for tests.
    """

    def __init__(self) -> None:
        self.spot = 24200.0
        self.vix = 13.5

    def quote(self, keys):
        res = {}
        for k in keys:
            if k == "NSE:NIFTY 50":
                res[k] = {
                    "last_price": self.spot,
                    "volume": 2500000,
                    "ohlc": {"open": self.spot - 50.0, "high": self.spot + 100.0, "low": self.spot - 100.0, "close": self.spot - 20.0},
                }
            elif k == "NSE:INDIA VIX":
                res[k] = {
                    "last_price": self.vix,
                }
            elif k.startswith("NFO:"):
                # Option quote
                is_ce = "CE" in k
                strike = 24200.0
                if "24150" in k:
                    strike = 24150.0
                elif "24250" in k:
                    strike = 24250.0

                # Simple premium simulation
                diff = self.spot - strike
                if is_ce:
                    ltp = max(5.0, 100.0 + diff)
                else:
                    ltp = max(5.0, 100.0 - diff)

                res[k] = {
                    "last_price": ltp,
                    "ohlc": {"close": ltp - 2.0},
                    "volume": 12000,
                    "oi": 80000,
                    "oi_change": 1500,
                    "depth": {
                        "buy": [{"price": ltp - 0.05, "quantity": 100}],
                        "sell": [{"price": ltp + 0.05, "quantity": 100}],
                    }
                }
        return res

    def ltp(self, keys):
        res = {}
        for k in keys:
            if k == "NSE:NIFTY 50":
                res[k] = {"last_price": self.spot}
            elif k == "NSE:INDIA VIX":
                res[k] = {"last_price": self.vix}
        return res

    def historical_data(
        self, instrument_token, from_date, to_date, interval, continuous=False, oi=False
    ):
        dates = pd.date_range(start=from_date, end=to_date, periods=100)
        closes = [self.spot - 50.0 + i * 1.0 for i in range(100)]
        highs = [c + 15.0 for c in closes]
        lows = [c - 15.0 for c in closes]
        return [
            {
                "date": d,
                "open": c - 5.0,
                "high": h,
                "low": l,
                "close": c,
                "volume": 20000,
            }
            for d, c, h, l in zip(dates, closes, highs, lows)
        ]


class TestHistoricalValidation(unittest.TestCase):
    def setUp(self):
        # 1. Setup Mock Kite Client
        self.kite = MockKiteClient()

        # 2. Setup mock instruments DataFrame
        self.expiry_date = datetime.date(2026, 11, 12)  # A Thursday in Nov 2026
        self.expiry_str = self.expiry_date.strftime("%Y-%m-%d")

        rows = [
            # NIFTY Index
            {
                "exchange": "NSE",
                "segment": "INDICES",
                "tradingsymbol": "NIFTY 50",
                "name": "NIFTY 50",
                "instrument_token": 256265,
                "expiry": pd.NaT,
                "strike": 0.0,
                "instrument_type": "EQ",
            },
            # NIFTY Option - 24150 CE
            {
                "exchange": "NFO",
                "segment": "NFO-OPT",
                "tradingsymbol": "NIFTY26NOV24150CE",
                "name": "NIFTY",
                "instrument_token": 11111,
                "expiry": self.expiry_date,
                "strike": 24150.0,
                "instrument_type": "CE",
            },
            # NIFTY Option - 24200 CE
            {
                "exchange": "NFO",
                "segment": "NFO-OPT",
                "tradingsymbol": "NIFTY26NOV24200CE",
                "name": "NIFTY",
                "instrument_token": 22222,
                "expiry": self.expiry_date,
                "strike": 24200.0,
                "instrument_type": "CE",
            },
            # NIFTY Option - 24250 CE
            {
                "exchange": "NFO",
                "segment": "NFO-OPT",
                "tradingsymbol": "NIFTY26NOV24250CE",
                "name": "NIFTY",
                "instrument_token": 33333,
                "expiry": self.expiry_date,
                "strike": 24250.0,
                "instrument_type": "CE",
            },
            # NIFTY Option - 24150 PE
            {
                "exchange": "NFO",
                "segment": "NFO-OPT",
                "tradingsymbol": "NIFTY26NOV24150PE",
                "name": "NIFTY",
                "instrument_token": 44444,
                "expiry": self.expiry_date,
                "strike": 24150.0,
                "instrument_type": "PE",
            },
            # NIFTY Option - 24200 PE
            {
                "exchange": "NFO",
                "segment": "NFO-OPT",
                "tradingsymbol": "NIFTY26NOV24200PE",
                "name": "NIFTY",
                "instrument_token": 55555,
                "expiry": self.expiry_date,
                "strike": 24200.0,
                "instrument_type": "PE",
            },
            # NIFTY Option - 24250 PE
            {
                "exchange": "NFO",
                "segment": "NFO-OPT",
                "tradingsymbol": "NIFTY26NOV24250PE",
                "name": "NIFTY",
                "instrument_token": 66666,
                "expiry": self.expiry_date,
                "strike": 24250.0,
                "instrument_type": "PE",
            },
        ]
        self.instruments_df = pd.DataFrame(rows)

        # 3. Setup Replay configs
        self.replay_days = [
            {
                "date": "2026-11-09",
                "kite": self.kite,
                "instruments_df": self.instruments_df,
                "spot_price": 24200.0,
                "expiry_date": self.expiry_date,
                "session_dt": datetime.datetime(2026, 11, 9, 10, 30, 0),
            },
            {
                "date": "2026-11-10",
                "kite": self.kite,
                "instruments_df": self.instruments_df,
                "spot_price": 24200.0,
                "expiry_date": self.expiry_date,
                "session_dt": datetime.datetime(2026, 11, 10, 10, 30, 0),
            },
        ]

        self.actual_outcomes = {
            "2026-11-09": {
                "Same-day": 24280.0,
                "Next-day": 24320.0,
                "Expiry-day": 24400.0,
            },
            "2026-11-10": {
                "Same-day": 24150.0,
                "Next-day": 24120.0,
                "Expiry-day": 24400.0,
            },
        }

    def test_historical_runner_replay(self) -> None:
        """
        Verify that HistoricalRunner correctly runs the end-to-end trading pipeline
        without modifying existing engines.
        """
        runner = HistoricalRunner()
        results = runner.run_replay(self.replay_days)

        self.assertEqual(len(results), 2)
        for res in results:
            self.assertIsInstance(res, DailyPipelineResult)
            self.assertIsNotNone(res.market_context)
            self.assertIsNotNone(res.option_context)
            self.assertIsNotNone(res.trade_context)
            self.assertIsNotNone(res.market_score)
            self.assertIsNotNone(res.opportunity_context)
            self.assertIsNotNone(res.strategy_evaluation)
            self.assertIsNotNone(res.trade_plan)
            self.assertIsNotNone(res.confidence_report)
            self.assertIsNotNone(res.risk_report)
            self.assertIsNotNone(res.decision_report)

            # Ensure data from contexts matches the replayed day
            self.assertEqual(res.market_context.current_spot, 24200.0)
            self.assertEqual(res.option_context.underlying_spot, 24200.0)

    def test_historical_replay_deterministic_identity(self) -> None:
        """
        Verify that replaying identical market states produces identical context values.
        """
        runner = HistoricalRunner()
        # Execute replay twice for the same configuration
        results_1 = runner.run_replay([self.replay_days[0]])
        results_2 = runner.run_replay([self.replay_days[0]])

        self.assertEqual(len(results_1), 1)
        self.assertEqual(len(results_2), 1)

        res_1 = results_1[0]
        res_2 = results_2[0]

        # Verify that scores, confidences, and decisions are identical
        self.assertEqual(res_1.market_score.overall_score, res_2.market_score.overall_score)
        self.assertEqual(
            len(res_1.decision_report.candidate_decisions),
            len(res_2.decision_report.candidate_decisions),
        )
        for dec_1, dec_2 in zip(
            res_1.decision_report.candidate_decisions,
            res_2.decision_report.candidate_decisions,
        ):
            self.assertEqual(dec_1.candidate_id, dec_2.candidate_id)
            self.assertEqual(dec_1.decision, dec_2.decision)
            self.assertEqual(dec_1.priority_score, dec_2.priority_score)

    def test_decision_validator_pnl_and_accuracy(self) -> None:
        """
        Verify that DecisionValidator computes correct outcomes and P&L.
        """
        runner = HistoricalRunner()
        results = runner.run_replay(self.replay_days)

        validator = DecisionValidator()
        outcomes = validator.validate_all(results, self.actual_outcomes)

        self.assertEqual(len(outcomes), 3)  # Same-day, Next-day, Expiry-day
        for outcome in outcomes:
            self.assertIn(outcome.evaluation_window, ["Same-day", "Next-day", "Expiry-day"])
            self.assertGreaterEqual(outcome.success_count, 0)
            self.assertGreaterEqual(outcome.failure_count, 0)
            self.assertTrue(0.0 <= outcome.accuracy_pct <= 100.0)

    def test_statistics_calculator(self) -> None:
        """
        Verify that StatisticsCalculator correctly aggregates daily statistics.
        """
        runner = HistoricalRunner()
        results = runner.run_replay(self.replay_days)

        conf_stats = StatisticsCalculator.calculate_confidence_stats(results)
        risk_stats = StatisticsCalculator.calculate_risk_stats(results)
        summary_stats = StatisticsCalculator.calculate_summary_stats(results)

        # Basic validations
        self.assertEqual(summary_stats.total_days_evaluated, 2)
        self.assertGreaterEqual(summary_stats.total_candidates_evaluated, 0)
        self.assertTrue(0.0 <= conf_stats.avg_confidence <= 100.0)
        self.assertTrue(0.0 <= conf_stats.max_confidence <= 100.0)
        self.assertTrue(0.0 <= conf_stats.min_confidence <= 100.0)
        self.assertTrue(0.0 <= conf_stats.std_confidence <= 100.0)
        self.assertGreaterEqual(risk_stats.total_allocated_capital, 0.0)

    def test_performance_analyzer(self) -> None:
        """
        Verify that PerformanceAnalyzer groups metrics by strategy and decision types correctly.
        """
        runner = HistoricalRunner()
        results = runner.run_replay(self.replay_days)

        strat_perfs = PerformanceAnalyzer.analyze_strategy_performance(results)
        dec_perfs = PerformanceAnalyzer.analyze_decision_performance(results)

        self.assertGreaterEqual(len(strat_perfs), 0)
        for strat in strat_perfs:
            self.assertIsNotNone(strat.strategy_name)
            self.assertGreaterEqual(strat.total_candidates, 0)

        self.assertEqual(len(dec_perfs), 5)  # BUY, SELL, WATCH, REJECT, NO TRADE
        for dec in dec_perfs:
            self.assertIn(dec.decision_type, ["BUY", "SELL", "WATCH", "REJECT", "NO TRADE"])
            self.assertTrue(0.0 <= dec.percentage <= 100.0)

    def test_validation_pipeline_end_to_end(self) -> None:
        """
        Verify that ValidationPipeline aggregates runner, validator, statistics,
        and performance modules into a high-quality, fully populated ValidationReport.
        """
        pipeline = ValidationPipeline()
        report = pipeline.run(self.replay_days, self.actual_outcomes)

        self.assertIsInstance(report, ValidationReport)
        self.assertTrue(report.report_id.startswith("VAL_"))
        self.assertEqual(len(report.daily_validations), 2)
        self.assertEqual(len(report.outcome_validations), 3)
        self.assertIsNotNone(report.summary_stats)
        self.assertIsNotNone(report.confidence_stats)
        self.assertIsNotNone(report.risk_stats)
        self.assertEqual(len(report.decision_performances), 5)
