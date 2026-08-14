from __future__ import annotations

from src.validation_engine.state_consistency_invariant import verify_state_consistency_invariants
from src.validation_engine.decision_validator import DecisionValidator
from src.validation_engine.statistics import StatisticsCalculator
from src.validation_engine.performance import PerformanceAnalyzer
from src.validation_engine.report_builder import ValidationReportBuilder

def __getattr__(name: str):
    if name in ("HistoricalRunner", "DailyPipelineResult"):
        from src.validation_engine.historical_runner import HistoricalRunner, DailyPipelineResult
        if name == "HistoricalRunner":
            return HistoricalRunner
        return DailyPipelineResult
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "verify_state_consistency_invariants",
    "HistoricalRunner",
    "DailyPipelineResult",
    "DecisionValidator",
    "StatisticsCalculator",
    "PerformanceAnalyzer",
    "ValidationReportBuilder",
]
