from __future__ import annotations

from typing import Any, Dict, List, Optional
from src.models import (
    MarketScore,
    OpportunityContext,
    StrategyEvaluation,
    TradePlan,
    ConfidenceReport,
    RiskReport,
    DecisionReport,
    EveningReport,
    IntradayReport,
    ValidationReport,
    OptimizationReport,
    ExplanationReport,
    PortfolioSnapshot,
    PerformanceReport,
    PaperPosition,
    TradeJournalEntry,
    AnalyticsReport,
    NewsContextV2,
    BrokerFunds,
    BrokerPosition,
    BrokerOrder,
    BrokerAccount,
    ExecutionStatus,
    ExecutionStateReport,
    OperationsReport,
    ConfigurationReport,
)
from src.dashboard.summary_panel import SummaryPanel
from src.dashboard.market_panel import MarketPanel
from src.dashboard.news_panel import NewsIntelligencePanel
from src.dashboard.strategy_panel import StrategyPanel
from src.dashboard.trade_panel import TradePanel
from src.dashboard.risk_panel import RiskPanel
from src.dashboard.validation_panel import ValidationPanel
from src.dashboard.optimization_panel import OptimizationPanel
from src.dashboard.planner_panel import PlannerPanel
from src.dashboard.intraday_panel import IntradayPanel
from src.dashboard.explanation_panel import ExplanationPanel
from src.dashboard.broker_panel import BrokerPanel
from src.dashboard.operations_panel import OperationsPanel
from src.dashboard.configuration_panel import ConfigurationPanel


class TradingWorkstationDashboard:
    """
    Unified operator workstation dashboard.
    Stateless presentation layer aggregating all modular panels.
    Designed for future Web/Desktop/Mobile client integration (to_dict()) and CLI rendering (render_cli()).
    """

    def __init__(
        self,
        market_score: Optional[MarketScore] = None,
        opportunity: Optional[OpportunityContext] = None,
        strategy_evaluation: Optional[StrategyEvaluation] = None,
        trade_plan: Optional[TradePlan] = None,
        confidence_report: Optional[ConfidenceReport] = None,
        risk_report: Optional[RiskReport] = None,
        decision_report: Optional[DecisionReport] = None,
        evening_report: Optional[EveningReport] = None,
        intraday_report: Optional[IntradayReport] = None,
        validation_report: Optional[ValidationReport] = None,
        optimization_report: Optional[OptimizationReport] = None,
        explanation_report: Optional[ExplanationReport] = None,
        portfolio_snapshot: Optional[PortfolioSnapshot] = None,
        performance_report: Optional[PerformanceReport] = None,
        open_positions: Optional[List[PaperPosition]] = None,
        journal: Optional[List[TradeJournalEntry]] = None,
        analytics_report: Optional[AnalyticsReport] = None,
        news_context: Optional[NewsContextV2] = None,
        broker_connection_status: Optional[Dict[str, Any]] = None,
        broker_funds: Optional[BrokerFunds] = None,
        broker_positions: Optional[List[BrokerPosition]] = None,
        broker_pending_orders: Optional[List[BrokerOrder]] = None,
        broker_execution_status: Optional[ExecutionStatus] = None,
        broker_account: Optional[BrokerAccount] = None,
        execution_state: Optional[ExecutionStateReport] = None,
        operations_report: Optional[OperationsReport] = None,
        configuration_report: Optional[ConfigurationReport] = None,
    ) -> None:
        self.summary_panel = SummaryPanel(
            market_score=market_score,
            opportunity=opportunity,
            trade_plan=trade_plan,
            confidence=confidence_report,
            risk=risk_report,
            decision=decision_report,
            evening_report=evening_report,
            intraday=intraday_report,
            validation=validation_report,
            optimization=optimization_report,
        )
        self.market_panel = MarketPanel(
            market_score=market_score,
            opportunity=opportunity,
        )
        self.news_panel = NewsIntelligencePanel(
            news_context=news_context,
        )
        self.strategy_panel = StrategyPanel(
            strategy_evaluation=strategy_evaluation,
        )
        self.trade_panel = TradePanel(
            trade_plan=trade_plan,
            confidence_report=confidence_report,
            decision_report=decision_report,
        )
        self.risk_panel = RiskPanel(
            risk_report=risk_report,
        )
        self.broker_panel = BrokerPanel(
            connection_status=broker_connection_status,
            funds=broker_funds,
            positions=broker_positions,
            pending_orders=broker_pending_orders,
            execution_status=broker_execution_status,
            account=broker_account,
        )
        from src.dashboard.execution_panel import ExecutionPanel
        self.execution_panel = ExecutionPanel(execution_state)
        self.operations_panel = OperationsPanel(operations_report)
        self.configuration_panel = ConfigurationPanel(configuration_report)
        self.validation_panel = ValidationPanel(
            validation_report=validation_report,
        )
        self.optimization_panel = OptimizationPanel(
            optimization_report=optimization_report,
        )
        self.planner_panel = PlannerPanel(
            evening_report=evening_report,
        )
        self.intraday_panel = IntradayPanel(
            intraday_report=intraday_report,
        )
        
        from src.dashboard.paper_trading_panel import PaperTradingPanel
        self.paper_trading_panel = PaperTradingPanel(
            snapshot=portfolio_snapshot,
            performance=performance_report,
            open_positions=open_positions,
            journal=journal,
        )
        
        if analytics_report is None and journal:
            from src.analytics_engine.builder import PerformanceAnalyticsBuilder
            initial_cap = portfolio_snapshot.total_capital if portfolio_snapshot else 1000000.0
            analytics_report = PerformanceAnalyticsBuilder.build_report(journal, initial_capital=initial_cap)

        from src.dashboard.performance_analytics_panel import PerformanceAnalyticsPanel
        self.performance_analytics_panel = PerformanceAnalyticsPanel(report=analytics_report)
        
        # Auto-build ExplanationReport if not provided and source data exists
        if explanation_report is None:
            if (decision_report or risk_report or confidence_report or trade_plan or
                    strategy_evaluation or opportunity or market_score or
                    evening_report or intraday_report):
                from src.explanation_engine.builder import ExplanationBuilder
                explanation_report = ExplanationBuilder.build(
                    decision_report=decision_report,
                    risk_report=risk_report,
                    confidence_report=confidence_report,
                    trade_plan=trade_plan,
                    strategy_evaluation=strategy_evaluation,
                    opportunity=opportunity,
                    market_score=market_score,
                    evening_report=evening_report,
                    intraday_report=intraday_report,
                )
        self.explanation_panel = ExplanationPanel(explanation_report)

    def to_dict(self) -> Dict[str, Any]:
        """
        Gathers presentation-ready structured data from all panels.
        No trading logic or calculations are performed here.
        """
        return {
            "summary": self.summary_panel.to_dict()["workstation_status"],
            "market_context": self.market_panel.to_dict(),
            "strategy": self.strategy_panel.to_dict(),
            "trade_pipeline": self.trade_panel.to_dict(),
            "risk": self.risk_panel.to_dict(),
            "broker": self.broker_panel.to_dict(),
            "validation": self.validation_panel.to_dict(),
            "optimization": self.optimization_panel.to_dict(),
            "planner": self.planner_panel.to_dict(),
            "intraday": self.intraday_panel.to_dict(),
            "explanations": self.explanation_panel.to_dict(),
            "paper_trading": self.paper_trading_panel.to_dict(),
            "performance_analytics": self.performance_analytics_panel.to_dict(),
            "news_intelligence": self.news_panel.to_dict(),
            "execution": self.execution_panel.to_dict(),
            "operations": self.operations_panel.to_dict(),
            "configuration": self.configuration_panel.to_dict(),
        }

    def render_cli(self) -> str:
        """
        Assembles a professional terminal dashboard, joining panels with clear dividing negative space.
        """
        blocks = []
        
        # Main Header
        header_lines = [
            "################################################################################",
            "##                     UNIFIED TRADING WORKSTATION DASHBOARD                  ##",
            "################################################################################",
            ""
        ]
        blocks.append("\n".join(header_lines))
        
        # 1. High-level Summary Panel
        blocks.append(self.summary_panel.render_cli())
        blocks.append("")
        
        # 2. Market Panel
        blocks.append(self.market_panel.render_cli())
        blocks.append("")
        
        # 2b. News Intelligence Context
        blocks.append(self.news_panel.render_cli())
        blocks.append("")
        
        # 3. Strategy Panel
        blocks.append(self.strategy_panel.render_cli())
        blocks.append("")
        
        # 4. Trade Candidates, Confidence & Decision Pipeline
        blocks.append(self.trade_panel.render_cli())
        blocks.append("")
        
        # 5. Risk Panel
        blocks.append(self.risk_panel.render_cli())
        blocks.append("")

        # 5b. Broker Panel
        blocks.append(self.broker_panel.render_cli())
        blocks.append("")

        # 5c. Execution Panel
        blocks.append(self.execution_panel.render_cli())
        blocks.append("")

        # 5d. Operations Health Panel
        blocks.append(self.operations_panel.render_cli())
        blocks.append("")

        # 5e. Workspace Configuration Panel
        blocks.append(self.configuration_panel.render_cli())
        blocks.append("")
        
        # 6. Intraday Monitor Status
        blocks.append(self.intraday_panel.render_cli())
        blocks.append("")
        
        # 7. Evening Planner Tomorrow Outlook
        blocks.append(self.planner_panel.render_cli())
        blocks.append("")
        
        # 8. Historical Validation Statistics
        blocks.append(self.validation_panel.render_cli())
        blocks.append("")
        
        # 9. System Optimization Advisory
        blocks.append(self.optimization_panel.render_cli())
        blocks.append("")

        # 10. Paper Trading Panel
        blocks.append(self.paper_trading_panel.render_cli())
        blocks.append("")

        # 10b. Performance Analytics Panel
        blocks.append(self.performance_analytics_panel.render_cli())
        blocks.append("")

        # 11. AI Explanation Layer
        blocks.append(self.explanation_panel.render_cli())
        blocks.append("")
        
        # Footer
        footer_lines = [
            "################################################################################",
            "##                         OPERATOR SESSION LIVE VIEW                         ##",
            "################################################################################"
        ]
        blocks.append("\n".join(footer_lines))
        
        return "\n".join(blocks)
