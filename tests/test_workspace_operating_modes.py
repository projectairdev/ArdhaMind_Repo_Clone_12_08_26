from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch

from src.configuration_engine.runtime import Config
from src.workspace import (
    WorkspaceMode,
    WorkspaceContext,
    WorkspaceManager,
    MarketDataSource,
    ExecutionMode,
    PortfolioSource,
    AnalyticsMode,
    NotificationMode,
    ModeValidator,
    ModeGuard,
    InvalidModeTransitionError,
)
from src.broker.models.trading_mode import TradingMode


def test_workspace_modes_exist():
    """Task 1: Verify all required workspace modes exist as immutable enums."""
    assert WorkspaceMode.LIVE_PRACTICE == "LIVE_PRACTICE"
    assert WorkspaceMode.LIVE_TRADING == "LIVE_TRADING"


def test_workspace_context_immutability():
    """Task 2: Verify WorkspaceContext is an immutable frozen dataclass."""
    ctx = WorkspaceContext(
        current_mode=WorkspaceMode.LIVE_PRACTICE,
        broker_type="ZERODHA",
        market_data_source=MarketDataSource.LIVE,
        execution_mode=ExecutionMode.PAPER_EXECUTION,
        portfolio_source=PortfolioSource.BROKER,
        analytics_mode=AnalyticsMode.ENABLED,
        notification_mode=NotificationMode.ENABLED,
        authentication_status="UNAUTHENTICATED",
        market_status="CLOSED",
        session_status="INACTIVE",
        timestamp="2026-07-11 12:00:00"
    )
    
    assert ctx.current_mode == WorkspaceMode.LIVE_PRACTICE
    assert ctx.broker_type == "ZERODHA"
    
    # Attempting to modify attributes should raise frozen error
    with pytest.raises(Exception):
        ctx.current_mode = WorkspaceMode.LIVE_TRADING


@patch("src.broker.services.broker_service.BrokerService.get_instance")
def test_workspace_manager_behavior_matrix(mock_broker_get):
    """Task 3 & 4: Verify WorkspaceManager loads correctly and builds Context as per Behaviour Matrix."""
    # Mock broker service to return healthy stats
    mock_broker = MagicMock()
    mock_health = MagicMock()
    mock_health.authentication_status = "AUTHENTICATED"
    mock_health.session_valid = True
    mock_health.connection_status = "CONNECTED"
    mock_health.api_status = "ONLINE"
    mock_health.market_status = "OPEN"
    mock_broker.health.return_value = mock_health
    mock_broker_get.return_value = mock_broker

    # Initialize manager
    manager = WorkspaceManager.get_instance()
    
    # Test LIVE_PRACTICE matrix
    manager._current_mode = WorkspaceMode.LIVE_PRACTICE
    ctx_practice = manager.get_context()
    assert ctx_practice.current_mode == WorkspaceMode.LIVE_PRACTICE
    assert ctx_practice.market_data_source == MarketDataSource.LIVE
    assert ctx_practice.broker_type == "ZERODHA"
    assert ctx_practice.portfolio_source == PortfolioSource.BROKER
    assert ctx_practice.execution_mode == ExecutionMode.PAPER_EXECUTION
    assert ctx_practice.analytics_mode == AnalyticsMode.ENABLED
    assert ctx_practice.notification_mode == NotificationMode.ENABLED

    # Test LIVE_TRADING matrix
    manager._current_mode = WorkspaceMode.LIVE_TRADING
    ctx_live = manager.get_context()
    assert ctx_live.current_mode == WorkspaceMode.LIVE_TRADING
    assert ctx_live.market_data_source == MarketDataSource.LIVE
    assert ctx_live.broker_type == "ZERODHA"
    assert ctx_live.portfolio_source == PortfolioSource.BROKER
    assert ctx_live.execution_mode == ExecutionMode.LIVE_BROKER


@patch("src.broker.services.broker_service.BrokerService.get_instance")
def test_workspace_mode_guards_and_transitions(mock_broker_get):
    """Task 5 & 9: Verify validation guards preventing dangerous transitions."""
    mock_broker = MagicMock()
    mock_health = MagicMock()
    mock_broker.health.return_value = mock_health
    mock_broker_get.return_value = mock_broker

    manager = WorkspaceManager.get_instance()
    manager._current_mode = WorkspaceMode.LIVE_PRACTICE

    # Transitioning to LIVE_TRADING without ALLOW_LIVE_TRADING configuration must fail
    Config.ALLOW_LIVE_TRADING = False
    with pytest.raises(InvalidModeTransitionError) as excinfo:
        manager.set_mode(WorkspaceMode.LIVE_TRADING, operator_confirmed=True)
    assert "fixed read-only product mode" in str(excinfo.value)

    # Transitioning to LIVE_TRADING without credentials/confirmation must fail
    Config.ALLOW_LIVE_TRADING = True
    Config.REQUIRE_CONFIRMATION = True
    with pytest.raises(InvalidModeTransitionError) as excinfo:
        manager.set_mode(WorkspaceMode.LIVE_TRADING, operator_confirmed=False)
    assert "fixed read-only product mode" in str(excinfo.value)

    # Transition with operator confirmation but unhealthy risk engine must still fail
    Config.RISK_ENGINE_HEALTHY = False
    with pytest.raises(InvalidModeTransitionError) as excinfo:
        manager.set_mode(WorkspaceMode.LIVE_TRADING, operator_confirmed=True)
    assert "fixed read-only product mode" in str(excinfo.value)
    Config.RISK_ENGINE_HEALTHY = True


@patch("src.broker.services.broker_service.BrokerService.get_instance")
def test_workspace_live_trading_remains_blocked_when_dependencies_are_healthy(mock_broker_get):
    """Healthy dependencies must never activate an execution-capable mode."""
    mock_broker = MagicMock()
    mock_health = MagicMock()
    mock_health.authentication_status = "AUTHENTICATED"
    mock_health.session_valid = True
    mock_health.connection_status = "CONNECTED"
    mock_health.api_status = "ONLINE"
    mock_health.market_status = "OPEN"
    mock_broker.health.return_value = mock_health
    mock_broker_get.return_value = mock_broker

    manager = WorkspaceManager.get_instance()
    manager._current_mode = WorkspaceMode.LIVE_PRACTICE
    
    Config.ALLOW_LIVE_TRADING = True
    Config.REQUIRE_CONFIRMATION = True
    Config.RISK_ENGINE_HEALTHY = True
    Config.EMERGENCY_STOP_TRIGGERED = False

    with pytest.raises(InvalidModeTransitionError, match="fixed read-only product mode"):
        manager.set_mode(WorkspaceMode.LIVE_TRADING, operator_confirmed=True, bypass_market_open=True)
    assert manager.current_mode != WorkspaceMode.LIVE_TRADING


def test_configuration_engine_integration():
    """Task 6: Verify Configuration Engine extensions are integrated."""
    assert hasattr(Config, "WORKSPACE_MODE")
    assert hasattr(Config, "DEFAULT_WORKSPACE_MODE")
    assert hasattr(Config, "ALLOW_LIVE_TRADING")
    assert hasattr(Config, "REQUIRE_CONFIRMATION")
    assert hasattr(Config, "SHOW_MODE_WARNING")
    assert hasattr(Config, "AUTO_FALLBACK_TO_DEVELOPMENT")
