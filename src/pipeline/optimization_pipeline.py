from __future__ import annotations

from typing import Optional
from src.models import (
    ValidationReport,
    OptimizationReport,
)
from src.optimization_engine import RecommendationBuilder


class OptimizationPipeline:
    """
    End-to-end Optimization & Tuning Advisor Pipeline.
    Consumes a ValidationReport and runs the stateless optimization engine
    to produce a detailed, immutable OptimizationReport containing evidence-based tuning recommendations.
    """

    def __init__(self) -> None:
        self.builder = RecommendationBuilder()

    def run(
        self, report: ValidationReport, report_id: Optional[str] = None
    ) -> OptimizationReport:
        """
        Executes optimization analysis over the historical validation report.
        """
        return self.builder.build_report(report=report, report_id=report_id)
