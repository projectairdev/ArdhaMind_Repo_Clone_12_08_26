from __future__ import annotations
import logging
from typing import Optional

from src.workspace.workspace_mode import WorkspaceMode
from src.workspace.mode_validator import ModeValidator

logger = logging.getLogger("WorkspaceModeGuard")


class WorkspaceError(Exception):
    """Base class for all Workspace operating mode errors."""
    pass


class InvalidModeTransitionError(WorkspaceError):
    """Raised when an invalid or unsafe operating mode transition is attempted."""
    def __init__(self, from_mode: WorkspaceMode, to_mode: WorkspaceMode, reason: str) -> None:
        message = f"Forbidden transition from {from_mode.name} to {to_mode.name}: {reason}"
        super().__init__(message)
        self.from_mode = from_mode
        self.to_mode = to_mode
        self.reason = reason


class ModeGuard:
    """
    Enforces runtime safety boundaries. Throws InvalidModeTransitionError if
    conditions are not met before transitioning workspace modes.
    """

    @classmethod
    def guard_transition(
        cls,
        from_mode: WorkspaceMode,
        to_mode: WorkspaceMode,
        operator_confirmed: bool = False,
        bypass_market_open: bool = True
    ) -> None:
        """
        Enforces constraints when transitioning from one mode to another.
        Raises InvalidModeTransitionError if any security or health guard fails.
        """
        logger.info(f"Guarding transition: {from_mode.name} -> {to_mode.name}")

        if to_mode == WorkspaceMode.LIVE_PRACTICE:
            # Transition to LIVE_PRACTICE is always permitted (fail-safe)
            return

        elif to_mode == WorkspaceMode.LIVE_TRADING:
            res = ModeValidator.can_enter_live(
                operator_confirmed=operator_confirmed,
                bypass_market_open=bypass_market_open
            )
            if not res["status"]:
                reason = "; ".join(res["errors"])
                raise InvalidModeTransitionError(from_mode, to_mode, reason)
