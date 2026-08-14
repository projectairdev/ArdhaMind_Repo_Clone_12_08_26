from __future__ import annotations

import datetime
from typing import Dict, List, Optional, Set, Any
import pandas as pd

from src.models import (
    ValidationReport,
    RiskEngineConfig,
    DecisionEngineConfig,
)
from src.validation_engine.historical_runner import HistoricalRunner
from src.validation_engine.report_builder import ValidationReportBuilder


class ValidationPipeline:
    """
    End-to-end Historical Validation Pipeline.
    Orchestrates execution of the historical runner and delegates construction of the final ValidationReport.
    """

    def __init__(self) -> None:
        self.runner = HistoricalRunner()
        self.builder = ValidationReportBuilder()

    def run(
        self,
        replay_days: List[Dict[str, Any]],
        actual_outcomes: Optional[Dict[str, Dict[str, float]]] = None,
        windows: Optional[List[str]] = None,
        holidays: Optional[Set[datetime.date]] = None,
        half_days: Optional[Set[datetime.date]] = None,
        weights: Optional[Dict[str, float]] = None,
        risk_config: Optional[RiskEngineConfig] = None,
        decision_config: Optional[DecisionEngineConfig] = None,
        report_id: Optional[str] = None,
    ) -> ValidationReport:
        """
        Executes historical replay across the provided days, performs outcome validation,
        and returns a unified, immutable ValidationReport.
        """
        # Run historical replay across all provided days
        results = self.runner.run_replay(
            replay_days=replay_days,
            holidays=holidays,
            half_days=half_days,
            weights=weights,
            risk_config=risk_config,
            decision_config=decision_config,
        )

        # Build and compile the final validation report
        return self.builder.build_report(
            results=results,
            actual_outcomes=actual_outcomes,
            windows=windows,
            report_id=report_id,
        )
