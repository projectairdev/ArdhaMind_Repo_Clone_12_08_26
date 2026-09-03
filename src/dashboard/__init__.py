from __future__ import annotations

from src.dashboard.summary_panel import SummaryPanel
from src.dashboard.market_panel import MarketPanel
from src.dashboard.strategy_panel import StrategyPanel
from src.dashboard.trade_panel import TradePanel
from src.dashboard.risk_panel import RiskPanel
from src.dashboard.validation_panel import ValidationPanel
from src.dashboard.optimization_panel import OptimizationPanel
from src.dashboard.planner_panel import PlannerPanel
from src.dashboard.intraday_panel import IntradayPanel
from src.dashboard.explanation_panel import ExplanationPanel
from src.dashboard.news_panel import NewsIntelligencePanel
from src.dashboard.broker_panel import BrokerPanel
from src.dashboard.execution_panel import ExecutionPanel
from src.dashboard.operations_panel import OperationsPanel
from src.dashboard.configuration_panel import ConfigurationPanel
from src.dashboard.dashboard_builder import TradingWorkstationDashboard

__all__ = [
    "SummaryPanel",
    "MarketPanel",
    "StrategyPanel",
    "TradePanel",
    "RiskPanel",
    "ValidationPanel",
    "OptimizationPanel",
    "PlannerPanel",
    "IntradayPanel",
    "ExplanationPanel",
    "NewsIntelligencePanel",
    "BrokerPanel",
    "ExecutionPanel",
    "OperationsPanel",
    "ConfigurationPanel",
    "TradingWorkstationDashboard",
]
