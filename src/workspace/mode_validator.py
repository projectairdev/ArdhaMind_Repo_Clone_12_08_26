from __future__ import annotations
import logging
from typing import Optional, Dict, Any

from src.config_engine import Config
from src.workspace.workspace_mode import WorkspaceMode
from src.broker.services.broker_service import BrokerService

logger = logging.getLogger("WorkspaceModeValidator")


class ModeValidator:
    """
    Validates workspace configurations, active state indicators, and checks transition requirements.
    Does not raise exceptions; returns structured results or booleans.
    """

    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """
        Validates the workspace-related environment variables and configurations.
        Returns a dict of validation status and potential error/warning messages.
        """
        errors = []
        warnings = []
        
        # Validate DEFAULT_WORKSPACE_MODE
        default_mode_str = getattr(Config, "DEFAULT_WORKSPACE_MODE", "LIVE_PRACTICE")
        try:
            default_mode = WorkspaceMode(default_mode_str)
        except ValueError:
            errors.append(f"Invalid DEFAULT_WORKSPACE_MODE configured: '{default_mode_str}'")
            default_mode = WorkspaceMode.LIVE_PRACTICE

        # Validate WORKSPACE_MODE if set
        current_mode_str = getattr(Config, "WORKSPACE_MODE", "")
        if current_mode_str:
            try:
                WorkspaceMode(current_mode_str)
            except ValueError:
                errors.append(f"Invalid WORKSPACE_MODE configured: '{current_mode_str}'")

        # Warning checks
        if default_mode == WorkspaceMode.LIVE_TRADING and not getattr(Config, "ALLOW_LIVE_TRADING", False):
            errors.append("DEFAULT_WORKSPACE_MODE is set to LIVE_TRADING, but ALLOW_LIVE_TRADING is False.")

        if getattr(Config, "SHOW_MODE_WARNING", True) and getattr(Config, "ALLOW_LIVE_TRADING", False):
            warnings.append("ALLOW_LIVE_TRADING is enabled. Ensure safety checks are rigorous.")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "default_mode": default_mode
        }

    @classmethod
    def can_enter_live_practice(cls) -> Dict[str, Any]:
        """Live Practice mode has no pre-requisites."""
        return {"status": True, "errors": []}

    @classmethod
    def can_enter_live(
        cls, operator_confirmed: bool = False, bypass_market_open: bool = True
    ) -> Dict[str, Any]:
        """
        Enforces strict safety checks to enter LIVE:
        ✓ ALLOW_LIVE_TRADING is True
        ✓ Operator Confirmation
        ✓ Risk Engine Config Healthy
        """
        errors = []
        
        if not getattr(Config, "ALLOW_LIVE_TRADING", False):
            errors.append("LIVE trading is disabled in system configurations.")

        # Check operator confirmation
        if getattr(Config, "REQUIRE_CONFIRMATION", True) and not operator_confirmed:
            errors.append("Operator confirmation is required to enter LIVE trading.")

        # Risk Engine config check
        if not getattr(Config, "RISK_ENGINE_HEALTHY", True):
            errors.append("Risk Engine is configured as unhealthy.")
            
        if getattr(Config, "EMERGENCY_STOP_TRIGGERED", False):
            errors.append("Emergency Stop has been triggered.")

        return {
            "status": len(errors) == 0,
            "errors": errors
        }
