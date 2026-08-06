from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from src.workspace.workspace_mode import WorkspaceMode
from src.workspace.modes import (
    MarketDataSource,
    ExecutionMode,
    PortfolioSource,
    AnalyticsMode,
    NotificationMode,
)

@dataclass(frozen=True)
class WorkspaceContext:
    """
    Immutable, frozen dataclass representing the current Workspace state and behaviour configuration.
    """
    current_mode: WorkspaceMode
    broker_type: str                  # e.g., "MOCK" or "ZERODHA"
    market_data_source: MarketDataSource
    execution_mode: ExecutionMode
    portfolio_source: PortfolioSource
    analytics_mode: AnalyticsMode
    notification_mode: NotificationMode
    authentication_status: str        # e.g., "AUTHENTICATED", "UNAUTHENTICATED", "EXPIRED"
    market_status: str                # e.g., "OPEN", "CLOSED"
    session_status: str               # e.g., "ACTIVE", "INACTIVE", "EXPIRED"
    timestamp: str                    # Formatted datetime string or Unix timestamp
