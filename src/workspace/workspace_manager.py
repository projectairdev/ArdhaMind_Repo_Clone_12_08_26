from __future__ import annotations
import logging
import time
from typing import Optional, Dict, Any

from src.config_engine import Config
from src.workspace.workspace_mode import WorkspaceMode
from src.workspace.workspace_context import WorkspaceContext
from src.workspace.modes import (
    MarketDataSource,
    ExecutionMode,
    PortfolioSource,
    AnalyticsMode,
    NotificationMode,
)
from src.workspace.mode_validator import ModeValidator
from src.workspace.mode_guard import ModeGuard, InvalidModeTransitionError
from src.broker.services.broker_service import BrokerService
from src.broker.models.trading_mode import TradingMode

logger = logging.getLogger("WorkspaceManager")


class WorkspaceManager:
    """
    Singleton manager class to control, transition and expose operating workspace contexts.
    Keeps state completely isolated and stateless with respect to engines.
    """
    _instance: Optional[WorkspaceManager] = None

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        # Load mode from Configuration
        mode_str = getattr(Config, "WORKSPACE_MODE", "") or getattr(Config, "DEFAULT_WORKSPACE_MODE", "LIVE_PRACTICE")
        try:
            self._current_mode = WorkspaceMode(mode_str)
        except ValueError:
            logger.warning(f"Invalid operating mode '{mode_str}' in configuration, falling back to LIVE_PRACTICE.")
            self._current_mode = WorkspaceMode.LIVE_PRACTICE

        self._initialized = True

    @classmethod
    def get_instance(cls) -> WorkspaceManager:
        if cls._instance is None:
            cls._instance = WorkspaceManager()
        return cls._instance

    @property
    def current_mode(self) -> WorkspaceMode:
        """Returns the current active WorkspaceMode."""
        return self._current_mode

    def set_mode(
        self,
        new_mode: WorkspaceMode,
        operator_confirmed: bool = False,
        bypass_market_open: bool = True
    ) -> bool:
        """
        Attempts to change the workspace operating mode.
        If validation fails, raises InvalidModeTransitionError and triggers auto-fallback if configured.
        """
        if self._current_mode == new_mode:
            return True

        try:
            # Perform guard check
            ModeGuard.guard_transition(
                from_mode=self._current_mode,
                to_mode=new_mode,
                operator_confirmed=operator_confirmed,
                bypass_market_open=bypass_market_open
            )
            
            # Transition passed checks - update mode
            old_mode = self._current_mode
            self._current_mode = new_mode
            Config.WORKSPACE_MODE = new_mode.value
            
            # Propagate system-wide broker-level mode updates if necessary (both use Zerodha)
            try:
                broker_service = BrokerService.get_instance()
                broker_service.set_mode(TradingMode.LIVE_ZERODHA)
                try:
                    broker_service.load_session()
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Failed to synchronize BrokerService mode during transition: {e}")

            logger.info(f"Workspace operating mode changed from {old_mode.name} to {new_mode.name}")
            return True
            
        except Exception as e:
            logger.error(f"Transition check failed: {e}")
            raise e

    def get_context(self) -> WorkspaceContext:
        """
        Builds the immutable WorkspaceContext representing the current operating mode and metrics.
        """
        mode = self._current_mode
        
        # Centralized Behaviour Matrix resolution (Task 4)
        if mode == WorkspaceMode.LIVE_PRACTICE:
            market_data = MarketDataSource.LIVE
            broker_type = "ZERODHA"
            portfolio = PortfolioSource.BROKER
            exec_mode = ExecutionMode.PAPER_EXECUTION
            analytics = AnalyticsMode.ENABLED
            notification = NotificationMode.ENABLED
        elif mode == WorkspaceMode.LIVE_TRADING:
            market_data = MarketDataSource.LIVE
            broker_type = "ZERODHA"
            portfolio = PortfolioSource.BROKER
            exec_mode = ExecutionMode.LIVE_BROKER
            analytics = AnalyticsMode.ENABLED
            notification = NotificationMode.ENABLED
        else: # Fail-safe fallbacks
            market_data = MarketDataSource.LIVE
            broker_type = "ZERODHA"
            portfolio = PortfolioSource.BROKER
            exec_mode = ExecutionMode.PAPER_EXECUTION
            analytics = AnalyticsMode.ENABLED
            notification = NotificationMode.ENABLED

        # Fetch real-time status details from the Broker layer
        try:
            broker_service = BrokerService.get_instance()
            health = broker_service.health()
            auth_status = getattr(health, "authentication_status", "UNAUTHENTICATED")
            market_status = getattr(health, "market_status", "CLOSED")
            session_status = "ACTIVE" if getattr(health, "session_valid", False) else "INACTIVE"
        except Exception:
            auth_status = "UNAUTHENTICATED"
            market_status = "CLOSED"
            session_status = "INACTIVE"

        return WorkspaceContext(
            current_mode=mode,
            broker_type=broker_type,
            market_data_source=market_data,
            execution_mode=exec_mode,
            portfolio_source=portfolio,
            analytics_mode=analytics,
            notification_mode=notification,
            authentication_status=auth_status,
            market_status=market_status,
            session_status=session_status,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
