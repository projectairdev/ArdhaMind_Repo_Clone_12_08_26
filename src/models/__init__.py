from __future__ import annotations

from src.models.market import (
    StructureMetrics,
    PriceLevelMetrics,
    RelativeStrengthMetrics,
    TimeframeMetrics,
    MultiTimeframeSummary,
    RegimeMetrics,
    MarketRegime,
    TrendSnapshot,
)
from src.models.market_context import MarketContext
from src.models.trade import (
    OptionSignal,
    StockSignal,
    TradeSignal,
    TradeRecommendation,
)
from src.models.risk import (
    RiskParameters,
    RejectionRecord,
    RiskCalculationResult,
)
from src.models.news import (
    NewsHeadline,
    NewsContext,
)
from src.models.options import (
    OptionContract,
    OptionChainMetrics,
)
from src.models.option_context import OptionContext
from src.models.trade_context import (
    TradeContext,
    SessionContext,
    ExpiryContext,
    MarketReadiness,
    ConfluenceContext,
)
from src.models.market_score import (
    TrendScore,
    OptionScore,
    VolatilityScore,
    LiquidityScore,
    SessionScore,
    ExpiryScore,
    ConfluenceScore,
    MarketScore,
)
from src.models.confidence_report import (
    ConfidenceReason,
    ConfidenceBonus,
    ConfidencePenalty,
    CandidateConfidence,
    ConfidenceSummary,
    ConfidenceReport,
)
from src.models.opportunity_context import (
    OpportunityClassification,
    DirectionalBias,
    OpportunityStrength,
    OpportunityWarning,
    InvalidationFactor,
    OpportunityProfile,
    MarketBreadthContext,
    GlobalContext,
    OpportunityContext,
)
from src.models.strategy_evaluation import (
    StrategyReason,
    StrategyWarning,
    StrategyConstraint,
    StrategyScore,
    EvaluationSummary,
    StrategyEvaluation,
)
from src.models.trade_plan import (
    CandidateReason,
    CandidateWarning,
    CandidateRejection,
    TradeCandidate,
    PlannerStatistics,
    PlannerSummary,
    TradePlan,
)
from src.models.risk_report import (
    RiskWarning,
    PortfolioConstraint,
    CapitalAllocation,
    CandidateRisk,
    SectorExposureDetail,
    DirectionalExposureDetail,
    ExpiryExposureDetail,
    ExposureSummary,
    RiskSummary,
    RiskEngineConfig,
    RiskReport,
)
from src.models.decision_report import (
    DecisionReason,
    DecisionWarning,
    CandidateDecision,
    DecisionSummary,
    DecisionStatistics,
    DecisionEngineConfig,
    DecisionReport,
)
from src.models.validation_report import (
    StrategyPerformance,
    DecisionPerformance,
    ConfidenceStatistics,
    RiskStatistics,
    OutcomeValidation,
    DailyValidation,
    SummaryStatistics,
    ValidationReport,
)
from src.models.optimization_report import (
    RecommendationEvidence,
    OptimizationRecommendation,
    StrategyOptimization,
    ThresholdRecommendation,
    WeightRecommendation,
    OptimizationSummary,
    OptimizationReport,
)
from src.models.evening_report import (
    MarketSummary,
    TomorrowOutlook,
    RecommendedStrategy,
    RecommendedCandidate,
    RejectedCandidate,
    RiskWatchlist,
    EventWatchlist,
    PlannerChecklist,
    ReportSummary,
    EveningReport,
)
from src.models.intraday_report import (
    PlanStatus,
    CandidateStatus,
    ActionRecommendation,
    MarketChange,
    ConfidenceChange,
    RiskChange,
    CandidateStatusReport,
    IntradaySummary,
    IntradayReport,
)
from src.models.explanation_report import (
    CandidateExplanation,
    DecisionExplanation,
    RiskExplanation,
    ConfidenceExplanation,
    StrategyExplanation,
    IntradayExplanation,
    PlannerExplanation,
    ExplanationSummary,
    ExplanationReport,
)
from src.models.paper_trade import (
    TradeLifecycle,
    TradeOutcome,
    PaperTrade,
    PaperPosition,
    TradeJournalEntry,
    PortfolioSnapshot,
    PaperStrategyPerformance,
    RegimePerformance,
    ConfidenceBandPerformance,
    PerformanceReport,
)
from src.models.analytics_report import (
    AnalyticsReport,
    PerformanceMetrics,
    AnalyticsStrategyPerformance,
    AnalyticsRegimePerformance,
    OpportunityPerformance,
    GradePerformance,
    BiasPerformance,
    MarketPerformance,
    ConfidencePerformance,
    RiskPerformance,
    TimePerformance,
    PortfolioPerformance,
    AnalyticsSummary,
)
from src.models.news_context_v2 import (
    NewsContext as NewsContextV2,
    NewsArticle,
    NewsEvent,
    AffectedMarket,
    AffectedSector,
    AffectedIndex,
    EventSeverity,
    MarketImpact,
    NewsSummary,
    NewsStatistics,
)
from src.models.execution_report import (
    ExecutionOrder,
    ExecutionRequest,
    ExecutionResponse,
    ExecutionStatus,
    ExecutionReport,
    BrokerAccount,
    BrokerFunds,
    BrokerPosition,
    BrokerHolding,
    BrokerOrder,
    ExecutionSummary,
    ExecutionResult,
    ExecutionValidation,
    ExecutionConfirmation,
    ExecutionReceipt,
    ExecutionFailure,
    ExecutionAuditEntry,
)
from src.models.execution_state import (
    OrderState,
    LivePosition,
    PositionContext,
    PortfolioContext,
    ExecutionTimeline,
    ExecutionAudit,
    ExecutionStatistics,
    ExecutionStateReport,
)
from src.models.order_lifecycle import (
    OrderLifecycleReport,
    OrderLifecycleEvent,
    ExecutionFill,
    ExecutionProgress,
    ExecutionStatusSummary,
    OrderModificationHistory,
    OrderCancellationRecord,
    BrokerExecutionSnapshot,
)
from src.models.operations_report import (
    ServiceStatus,
    StartupDiagnostics,
    DependencyStatus,
    ResourceUsage,
    SystemMetrics,
    HealthWarning,
    ReadinessStatus,
    OperationsSummary,
    OperationsReport,
)
from src.models.configuration_report import (
    ConfigurationItem,
    WorkspacePreferences,
    ConfigurationWarning,
    ConfigurationMigration,
    ConfigurationProfile,
    ConfigurationStatistics,
    ConfigurationSummary,
    ConfigurationReport,
)
from src.models.live_portfolio_report import (
    LivePortfolioReport,
    LivePortfolioReportBuilder,
    PortfolioStatistics,
)
from src.broker.services.account_service import AccountProfile
from src.broker.services.funds_service import AccountFunds, FundSegment
from src.broker.services.holdings_service import HoldingItem
from src.broker.services.positions_service import AccountPositions, PositionItem
from src.broker.services.orders_service import AccountOrders, OrderItem
from src.broker.services.trades_service import TradeItem

# Phase 2 canonical read-only contracts.
from src.models.data_quality import FreshnessStatus, QualityStatus, SectionStatus, ValueClassification, ValueMetadata
from src.models.canonical_workstation_state import CanonicalWorkstationState
from src.models.decision_support import DecisionSupportReport










