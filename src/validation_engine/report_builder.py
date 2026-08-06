from __future__ import annotations

import uuid
from typing import Dict, List, Optional
from src.models.validation_report import DailyValidation, ValidationReport
from src.validation_engine.historical_runner import DailyPipelineResult
from src.validation_engine.statistics import StatisticsCalculator
from src.validation_engine.performance import PerformanceAnalyzer
from src.validation_engine.decision_validator import DecisionValidator
from src.utils import now_str


class ValidationReportBuilder:
    """
    Assembles historical replay outcomes and analytical metrics into a ValidationReport.
    """

    @staticmethod
    def build_report(
        results: List[DailyPipelineResult],
        actual_outcomes: Optional[Dict[str, Dict[str, float]]] = None,
        windows: Optional[List[str]] = None,
        report_id: Optional[str] = None,
    ) -> ValidationReport:
        """
        Constructs a complete ValidationReport from replay results and historical outcomes.
        """
        if report_id is None:
            report_id = f"VAL_{uuid.uuid4().hex[:8].upper()}"

        if actual_outcomes is None:
            actual_outcomes = {}

        if windows is None:
            windows = ["Same-day", "Next-day", "Expiry-day"]

        # 1. Build DailyValidations list
        daily_validations = []
        for res in results:
            # Generate a brief outcome summary description
            b_count = res.decision_report.stats.buy_count
            s_count = res.decision_report.stats.sell_count
            cap_allocated = res.risk_report.exposure_summary.total_capital_allocated

            summary_msg = (
                f"Market score {res.market_score.overall_score:.1f} ({res.market_score.letter_grade}). "
                f"{b_count} BUYs, {s_count} SELLs. Allocated Capital: {cap_allocated:.2f}."
            )

            # If outcome is available, append the details
            day_outcomes = actual_outcomes.get(res.date, {})
            same_day_outcome = day_outcomes.get("Same-day")
            if same_day_outcome is not None:
                summary_msg += f" Same-day NIFTY Close: {same_day_outcome:.2f} (Entry spot: {res.market_context.current_spot:.2f})."

            daily_validations.append(
                DailyValidation(
                    date=res.date,
                    market_score=res.market_score.overall_score,
                    candidates_count=res.decision_report.stats.total_candidates_evaluated,
                    buy_count=b_count,
                    sell_count=s_count,
                    watch_count=res.decision_report.stats.watch_count,
                    reject_count=res.decision_report.stats.reject_count,
                    no_trade_count=res.decision_report.stats.no_trade_count,
                    total_allocated_capital=cap_allocated,
                    decision_report_id=res.decision_report.report_id,
                    outcome_summary=summary_msg,
                )
            )

        # 2. Compute statistics
        confidence_stats = StatisticsCalculator.calculate_confidence_stats(results)
        risk_stats = StatisticsCalculator.calculate_risk_stats(results)
        summary_stats = StatisticsCalculator.calculate_summary_stats(results)

        # 3. Compute performances
        strategy_performances = PerformanceAnalyzer.analyze_strategy_performance(results)
        decision_performances = PerformanceAnalyzer.analyze_decision_performance(results)

        # 4. Compute outcome validations
        validator = DecisionValidator()
        outcome_validations = validator.validate_all(results, actual_outcomes, windows)

        return ValidationReport(
            report_id=report_id,
            daily_validations=daily_validations,
            strategy_performances=strategy_performances,
            decision_performances=decision_performances,
            confidence_stats=confidence_stats,
            risk_stats=risk_stats,
            outcome_validations=outcome_validations,
            summary_stats=summary_stats,
            timestamp=now_str(),
        )
