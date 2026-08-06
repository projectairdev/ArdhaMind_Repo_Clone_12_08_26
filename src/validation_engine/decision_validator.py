from __future__ import annotations

from typing import Dict, List, Any
from src.models.validation_report import OutcomeValidation
from src.validation_engine.historical_runner import DailyPipelineResult
from src.utils import setup_logger

logger = setup_logger("DecisionValidator")


class DecisionValidator:
    """
    Validates trading decisions by comparing them against actual market outcomes
    across configurable windows (Same-day, Next-day, Expiry-day).
    """

    def validate_for_window(
        self,
        results: List[DailyPipelineResult],
        actual_outcomes: Dict[str, Dict[str, float]],
        window: str,
    ) -> OutcomeValidation:
        """
        Validates decisions for a single evaluation window.
        """
        success_count = 0
        failure_count = 0
        total_pnl = 0.0

        for result in results:
            date_str = result.date
            spot_price = result.market_context.current_spot

            # Get outcome price for this day and window
            day_outcomes = actual_outcomes.get(date_str, {})
            outcome_price = day_outcomes.get(window)

            if outcome_price is None:
                logger.warning(
                    f"No outcome price found for {date_str} and window {window}. Skipping."
                )
                continue

            # Process decisions
            for decision in result.decision_report.candidate_decisions:
                # We only validate executable decisions
                if decision.decision not in ("BUY", "SELL"):
                    continue

                symbol = decision.tradingsymbol
                is_ce = "CE" in symbol
                is_pe = "PE" in symbol

                lots = decision.allocated_lots if decision.allocated_lots > 0 else 1

                # Determine success/failure and P&L
                is_success = False
                pnl = 0.0

                if decision.decision == "BUY":
                    if is_ce:
                        is_success = outcome_price > spot_price
                        pnl = (outcome_price - spot_price) * 50 * lots
                    elif is_pe:
                        is_success = outcome_price < spot_price
                        pnl = (spot_price - outcome_price) * 50 * lots
                elif decision.decision == "SELL":
                    if is_ce:
                        is_success = outcome_price <= spot_price
                        pnl = (spot_price - outcome_price) * 50 * lots
                    elif is_pe:
                        is_success = outcome_price >= spot_price
                        pnl = (outcome_price - spot_price) * 50 * lots

                if is_success:
                    success_count += 1
                else:
                    failure_count += 1

                total_pnl += pnl

        total_decisions = success_count + failure_count
        accuracy = (success_count / total_decisions * 100.0) if total_decisions > 0 else 100.0

        return OutcomeValidation(
            evaluation_window=window,
            success_count=success_count,
            failure_count=failure_count,
            accuracy_pct=round(accuracy, 2),
            total_profit_loss=round(total_pnl, 2),
        )

    def validate_all(
        self,
        results: List[DailyPipelineResult],
        actual_outcomes: Dict[str, Dict[str, float]],
        windows: List[str] = None,
    ) -> List[OutcomeValidation]:
        """
        Validates decisions across multiple evaluation windows.
        """
        if windows is None:
            windows = ["Same-day", "Next-day", "Expiry-day"]

        validations = []
        for window in windows:
            val = self.validate_for_window(results, actual_outcomes, window)
            validations.append(val)
        return validations
