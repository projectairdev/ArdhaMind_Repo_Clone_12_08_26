from __future__ import annotations

from typing import Optional
from src.models import PaperPosition


class PaperExitManager:
    """
    Stateless manager responsible for evaluating paper position exits.
    Supports: Target Hit, Stop Hit, Time Exit, Expiry Exit, Manual Close, Plan Invalidated.
    """

    @staticmethod
    def evaluate_exit(
        position: PaperPosition,
        current_premium: float,
        target_premium: Optional[float] = None,
        stop_premium: Optional[float] = None,
        max_holding_time: Optional[float] = None,
        manual_close: bool = False,
        plan_invalidated: bool = False,
        is_expired: bool = False,
    ) -> Optional[str]:
        """
        Evaluates the current state of a position and returns the exit reason if an exit is triggered.
        Otherwise returns None.
        """
        if position.status == "CLOSED":
            return None

        if manual_close:
            return "Manual Close"

        if plan_invalidated:
            return "Plan Invalidated"

        if is_expired:
            return "Expiry Exit"

        # Evaluate premium-based triggers
        entry_premium = position.trade.premium
        action = position.trade.action

        # Handle defaults for targets and stops if not explicitly provided
        # (e.g. Target at 20% gain, Stop at 10% loss as sensible trading defaults)
        if target_premium is None:
            if action == "BUY":
                target_premium = entry_premium * 1.20
            else:
                target_premium = entry_premium * 0.80

        if stop_premium is None:
            if action == "BUY":
                stop_premium = entry_premium * 0.90
            else:
                stop_premium = entry_premium * 1.10

        if action == "BUY":
            if current_premium >= target_premium:
                return "Target Hit"
            if current_premium <= stop_premium:
                return "Stop Hit"
        else:  # "SELL"
            if current_premium <= target_premium:
                return "Target Hit"
            if current_premium >= stop_premium:
                return "Stop Hit"

        # Time-based exit
        if max_holding_time is not None and position.holding_time_seconds >= max_holding_time:
            return "Time Exit"

        return None
