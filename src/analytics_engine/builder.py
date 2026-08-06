from __future__ import annotations

import uuid
from datetime import datetime
from typing import List
from src.models import AnalyticsReport, TradeJournalEntry
from src.analytics_engine.performance_metrics import PerformanceMetricsCalculator
from src.analytics_engine.strategy_analysis import StrategyAnalyser
from src.analytics_engine.regime_analysis import RegimeAnalyser
from src.analytics_engine.confidence_analysis import ConfidenceAnalyser
from src.analytics_engine.risk_analysis import RiskAnalyser
from src.analytics_engine.time_analysis import TimeAnalyser
from src.analytics_engine.portfolio_analysis import PortfolioAnalyser
from src.analytics_engine.summary_builder import SummaryBuilder

class PerformanceAnalyticsBuilder:
    """
    Stateless builder that orchestrates the entire Performance Analytics Engine
    and compiles the final consolidated AnalyticsReport.
    """

    @staticmethod
    def build_report(
        entries: List[TradeJournalEntry],
        initial_capital: float = 1000000.0,
        report_id: str | None = None,
    ) -> AnalyticsReport:
        if report_id is None:
            report_id = f"AN_REP_{uuid.uuid4().hex[:8].upper()}"

        overall = PerformanceMetricsCalculator.calculate(entries)
        strategies = StrategyAnalyser.analyze(entries)
        market = RegimeAnalyser.analyze(entries)
        confidence = ConfidenceAnalyser.analyze(entries)
        risk = RiskAnalyser.analyze(entries, initial_capital)
        time_perf = TimeAnalyser.analyze(entries)
        portfolio = PortfolioAnalyser.analyze(entries, initial_capital)

        summary = SummaryBuilder.build(
            overall=overall,
            strategies=strategies,
            market=market,
            confidence=confidence,
            risk=risk,
            time_perf=time_perf,
            portfolio=portfolio,
        )

        try:
            from src.utils import now_str
            timestamp = now_str()
        except ImportError:
            timestamp = datetime.utcnow().isoformat()

        return AnalyticsReport(
            report_id=report_id,
            overall_metrics=overall,
            strategy_metrics=strategies,
            market_metrics=market,
            confidence_metrics=confidence,
            risk_metrics=risk,
            time_metrics=time_perf,
            portfolio_metrics=portfolio,
            summary=summary,
            timestamp=timestamp,
        )
