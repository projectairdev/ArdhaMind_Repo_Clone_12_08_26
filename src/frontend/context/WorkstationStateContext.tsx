// src/frontend/context/WorkstationStateContext.tsx
import React, { createContext, useContext, useState, useEffect, useMemo } from "react";
import { workspaceService, WorkspaceMode, WorkspaceContext } from "../services/workspace";
import {
  getBrokerAccount,
  getBrokerFunds,
  getLivePortfolioReport,
  setRuntimeLiveTradingAllowed,
  LivePortfolioReport
} from "../services/broker";
import { getMarketContext, getOptionContext } from "../services/market";
import { getEveningReport, getTradePlan } from "../services/planner";
import {
  getMarketScore,
  getOpportunityContext,
  getStrategyEvaluation,
  getConfidenceReport,
  getRiskReport,
  getDecisionReport
} from "../services/dashboard";
import {
  BrokerAccount,
  BrokerFunds,
  MarketContext,
  OptionContext,
  EveningReport,
  MarketScore,
  OpportunityContext,
  StrategyEvaluation,
  StrategyScore,
  ConfidenceReport,
  RiskReport,
  DecisionReport,
  TradePlan,
  OperationsReport,
  ConfigurationReport,
  ExplanationReport,
  IntradayReport,
  ValidationReport,
  OptimizationReport,
  AnalyticsReport,
  NewsSentimentContext,
  CanonicalWorkstationState
} from "../types";

export type ConnectionState =
  | "DISCONNECTED"
  | "CONNECTING"
  | "AUTHENTICATED"
  | "PROFILE_LOADED"
  | "BROKER_READY"
  | "PRACTICE_READY"
  | "LIVE_READY";

export interface WorkstationStateContextProps {
  workspaceMode: WorkspaceMode;
  workspaceContext: WorkspaceContext;
  brokerAccount: BrokerAccount;
  brokerFunds: BrokerFunds;
  portfolioReport: LivePortfolioReport;
  marketContext: MarketContext;
  optionContext: OptionContext;
  eveningReport: EveningReport;
  marketScore: MarketScore;
  opportunityContext: OpportunityContext;
  strategyEvaluation: StrategyEvaluation;
  confidenceReport: ConfidenceReport;
  riskReport: RiskReport;
  decisionReport: DecisionReport;
  tradePlan: TradePlan;
  operationsReport: OperationsReport;
  configurationReport: ConfigurationReport;
  explanationReport: ExplanationReport;
  intradayReport: IntradayReport;
  validationReport: ValidationReport;
  optimizationReport: OptimizationReport;
  analyticsReport: AnalyticsReport;
  newsSentiment: NewsSentimentContext;
  connectionState: ConnectionState;
  marketConnection: "DISCONNECTED" | "CONNECTING" | "CONNECTED" | "ERROR";
  loading: boolean;
  syncing: boolean;
  error: string | null;
  lastSyncTime: string;
  apiLatency: number | null;
  allowLiveTrading: boolean;
  preferredTradingStyle: "Intraday" | "Swing" | "Positional";
  setWorkspaceMode: (mode: WorkspaceMode) => Promise<{ success: boolean; error?: string }>;
  syncBroker: (forceSync?: boolean) => Promise<void>;
  logoutBroker: () => Promise<void>;
  setAllowLiveTrading: (enabled: boolean) => Promise<void>;
  setPreferredTradingStyle: (style: "Intraday" | "Swing" | "Positional") => Promise<void>;
  canonicalState: CanonicalWorkstationState | null;
  lastValidState: CanonicalWorkstationState | null;
  diagnosticsError: string | null;
  diagnosticsDetails: string;
  setError: (err: string | null) => void;
}

const defaultWorkspaceContext: WorkspaceContext = {
  currentMode: "LIVE_PRACTICE",
  brokerState: "DISCONNECTED",
  marketState: "CLOSED",
  brokerType: "ZERODHA",
  marketDataSource: "LIVE",
  executionMode: "PAPER_EXECUTION",
  portfolioSource: "BROKER",
  analyticsMode: "ENABLED",
  notificationMode: "ENABLED",
  timestamp: new Date().toISOString()
};

const defaultBrokerAccount: BrokerAccount = {
  client_id: "N/A",
  name: "Not Connected",
  email: "N/A",
  broker: "N/A"
};

const defaultBrokerFunds: BrokerFunds = {
  available_cash: 0,
  margins: 0,
  utilized_margin: 0,
  available_margin: 0
};

const defaultPortfolioReport: LivePortfolioReport = {
  account_profile: {
    client_id: "N/A",
    client_name: "Not Connected",
    email: "N/A",
    pan: "N/A",
    broker_name: "N/A",
    user_type: "N/A",
    login_time: "N/A"
  },
  funds: {
    equity: {
      available_cash: 0,
      utilized_margin: 0,
      available_margin: 0,
      opening_balance: 0,
      collateral: 0,
      payin_amount: 0,
      payout_amount: 0
    },
    commodity: {
      available_cash: 0,
      utilized_margin: 0,
      available_margin: 0,
      opening_balance: 0,
      collateral: 0,
      payin_amount: 0,
      payout_amount: 0
    }
  },
  holdings: [],
  positions: {
    net: [],
    day: []
  },
  orders: {
    all_orders: [],
    completed: [],
    open_orders: []
  },
  trades: [],
  statistics: {
    total_holdings_value: 0,
    total_unrealized_pnl: 0,
    total_realized_pnl: 0,
    today_mtm: 0,
    total_margin_utilized: 0,
    available_cash: 0
  },
  timestamp: "",
  broker_health: {
    broker_name: "N/A",
    connection_status: "DISCONNECTED",
    trading_mode: "MOCK",
    latency: 0,
    authentication_status: "UNAUTHENTICATED",
    last_heartbeat: "N/A",
    instrument_cache_status: "UNINITIALIZED",
    market_status: "CLOSED",
    health_score: 100,
    last_error: null,
    session_valid: false,
    broker_version: "1.0",
    api_status: "OFFLINE"
  },
  sync_status: "SUCCESS"
};

const defaultMarketContext: MarketContext = {
  // [V1.3 Production Integrity] All values start at zero/empty.
  // Fabricated defaults (24200, 14.5, etc.) are removed.
  // The daemon will populate these within the first 3-second broadcast cycle.
  current_spot: 0,
  ltp: 0,
  last_tick_time: "",
  bid: 0,
  ask: 0,
  spread: 0,
  volume: 0,
  oi: 0,
  oi_change: 0,
  vwap: 0,
  atr: 0,
  india_vix: 0,
  volatility_state: "UNKNOWN",
  pcr: 0,
  atm_strike: 0,
  current_weekly_expiry: "",
  current_monthly_expiry: "",
  market_regime: "UNKNOWN",
  trend_direction: "NEUTRAL",
  trend_strength: 0,
  support_levels: [],
  resistance_levels: [],
  market_breadth: 0,
  feed_latency_ms: 0,
  feed_health: "OFFLINE",
  trading_session: "CLOSED",
  current_expiry: "",
  timestamp: new Date().toISOString()
};

const defaultOptionContext: OptionContext = {
  underlying_spot: 0,
  atm_strike: 0,
  strike_step: 0,
  current_weekly_expiry: "",
  current_monthly_expiry: "",
  time_to_expiry: 0,
  atm_iv: 0,
  expected_move: 0,
  pcr: 0,
  max_pain: 0,
  highest_call_oi: 0,
  highest_put_oi: 0,
  highest_call_oi_change: 0,
  highest_put_oi_change: 0,
  support_strikes: [],
  resistance_strikes: [],
  liquidity_metrics: {},
  option_chain_summary: {},
  top_candidate_strikes: [],
  market_option_bias: "NEUTRAL",
  timestamp: "",
  schema_version: "1.0",
  pipeline_version: "1.0"
};

const defaultEveningReport: EveningReport = {
  report_id: "N/A",
  market_summary: {
      spot_price: 0,
      vix_price: 0,
      regime: "UNKNOWN",
      trend_direction: "UNKNOWN",
      market_score: 0,
      market_grade: "N/A",
      session_type: "UNKNOWN"
  },
  tomorrow_outlook: {
    directional_bias: "NEUTRAL",
    outlook_classification: "WAIT",
      opportunity_strength: 0,
      key_support_levels: [],
      key_resistance_levels: [],
      description: "Unavailable"
  },
  recommended_strategies: [],
  top_candidates: [],
  rejected_candidates: [],
  risk_watchlist: {
    warnings: [],
    portfolio_warnings: [],
    max_capital_limit: 150000.0,
    allocated_capital: 0,
    portfolio_utilization_pct: 0,
    risk_grade: "CONSERVATIVE"
  },
  event_watchlist: {
    events: [],
    expiry_days_remaining: 0,
    expiry_type: "WEEKLY"
  },
  checklist: {
    checklist_items: []
  },
  summary: {
    best_candidate_id: "N/A",
    best_strategy: "N/A",
    total_accepted_candidates: 0,
    total_rejected_candidates: 0,
    action_type: "STANDBY"
  },
  timestamp: "",
  engine_version: "1.0",
  optimization_notes: []
};

const defaultAnalyticsReport: AnalyticsReport = {
  report_id: "N/A",
  overall_metrics: {
    total_trades: 0,
    winning_trades: 0,
    losing_trades: 0,
    win_rate: 0,
    average_profit: 0,
    average_loss: 0,
    profit_factor: 1,
    expectancy: 0,
    average_holding_time: 0,
    largest_winner: 0,
    largest_loser: 0,
    maximum_drawdown: 0,
    recovery_factor: 0
  },
  portfolio_metrics: {
    initial_capital: 1000000.0,
    final_capital: 1000000.0,
    total_pnl: 0,
    return_on_capital: 0,
    maximum_drawdown: 0,
    sharpe_ratio: 0,
    profit_factor: 1
  },
  strategy_metrics: [],
  market_metrics: {
    by_regime: [],
    by_opportunity: [],
    by_grade: [],
    by_bias: []
  },
  confidence_metrics: [],
  risk_metrics: [],
  time_metrics: {
    avg_holding_time: 0,
    by_entry_hour: {},
    by_day_of_week: {}
  },
  summary: {
    strengths: [],
    weaknesses: [],
    recommendations: []
  },
  timestamp: new Date().toISOString()
};

const defaultNewsSentimentContext: NewsSentimentContext = {
  articles: [],
  overall_sentiment: 0.0,
  sentiment_bias: "NEUTRAL",
  is_news_panic_active: false,
  timestamp: new Date().toISOString()
};

const defaultMarketScore: MarketScore = {
  trend: {
    trend_strength_score: 0,
    ema_alignment_score: 0,
    adx_score: 0,
    slope_score: 0,
    momentum_score: 0,
    overall_trend_score: 0
  },
  options: {
    pcr_score: 0,
    max_pain_score: 0,
    oi_structure_score: 0,
    oi_buildup_score: 0,
    liquidity_score: 0,
    iv_score: 0,
    expected_move_score: 0,
    overall_option_score: 0
  },
  volatility: {
    atr_score: 0,
    compression_score: 0,
    expansion_score: 0,
    iv_env_score: 0,
    expected_move_score: 0,
    overall_volatility_score: 0
  },
  liquidity: {
    spread_score: 0,
    volume_score: 0,
    oi_score: 0,
    tradability_score: 0,
    overall_liquidity_score: 0
  },
  session: {
    session_type_score: 0,
    is_tradable_score: 0,
    overall_session_score: 0
  },
  expiry: {
    days_remaining_score: 0,
    expiry_type_score: 0,
    classification_score: 0,
    overall_expiry_score: 0
  },
  confluence: {
    trend_confluence_score: 0,
    support_resistance_score: 0,
    option_bias_score: 0,
    volatility_score: 0,
    liquidity_score: 0,
    overall_confluence_score: 0
  },
  overall_score: 0,
  letter_grade: "C",
  classification: "NEUTRAL",
  timestamp: "",
  schema_version: "1.0",
  pipeline_version: "1.0"
};

const defaultOpportunityContext: OpportunityContext = {
  classification: { value: "WAIT", description: "STANDBY" },
  profile: {
    opportunity_type: "NONE",
    momentum_suitability: "NEUTRAL",
    breakout_suitability: "NEUTRAL",
    reversal_suitability: "NEUTRAL",
    range_suitability: "NEUTRAL",
    scalping_suitability: "NEUTRAL",
    trend_following_suitability: "NEUTRAL",
    expiry_suitability: "NEUTRAL",
    suitability_reasons: []
  },
  strength: {
    imbalance_magnitude: 0,
    trend_force: 0,
    option_force: 0,
    liquidity_force: 0,
    overall_strength: 0
  },
  directional_bias: { value: "NEUTRAL", description: "STANDBY" },
  warnings: [],
  invalidation_factors: [],
  has_opportunity: false,
  timestamp: "",
  breadth: { is_available: false },
  global_ctx: { is_available: false },
  schema_version: "1.0",
  pipeline_version: "1.0"
};

const createEmptyScore = (name: any): StrategyScore => ({
  strategy_name: name,
  suitability_score: 0,
  suitability_level: "NONE",
  reasons: [],
  warnings: [],
  constraints: [],
  required_conditions_met: [],
  rejected_conditions_met: []
});

const defaultStrategyEvaluation: StrategyEvaluation = {
  overall_best_strategy: "NONE",
  evaluations: [],
  momentum_evaluation: createEmptyScore("MOMENTUM"),
  breakout_evaluation: createEmptyScore("BREAKOUT"),
  trend_following_evaluation: createEmptyScore("TREND_FOLLOWING"),
  mean_reversion_evaluation: createEmptyScore("MEAN_REVERSION"),
  range_evaluation: createEmptyScore("RANGE"),
  expiry_evaluation: createEmptyScore("EXPIRY"),
  scalping_evaluation: createEmptyScore("SCALPING"),
  summary: {
    top_strategies: [],
    suitable_strategies_count: 0,
    unsuitable_strategies_count: 0,
    conclusions: []
  },
  timestamp: "",
  schema_version: "1.0",
  pipeline_version: "1.0"
};

const defaultConfidenceReport: ConfidenceReport = {
  report_id: "N/A",
  trade_plan_id: "N/A",
  confidence_scores: {},
  scoring_factors: {},
  summary_message: "No data loaded",
  timestamp: ""
};

const defaultRiskReport: RiskReport = {
  report_id: "N/A",
  confidence_report_id: "N/A",
  approved_candidates: [],
  total_capital_allocated: 0,
  portfolio_utilization_pct: 0,
  risk_grade: "CONSERVATIVE",
  active_rules_triggered: [],
  block_reasons: [],
  warnings: [],
  timestamp: ""
};

const defaultDecisionReport: DecisionReport = {
  report_id: "N/A",
  risk_report_id: "N/A",
  candidate_decisions: [],
  priority_ranking: [],
  summary: {
    overall_action: "HOLD",
    highest_priority_candidate_id: "N/A",
    portfolio_status_message: "No data loaded",
    conclusions: []
  },
  stats: {
    total_candidates_evaluated: 0,
    buy_count: 0,
    sell_count: 0,
    watch_count: 0,
    reject_count: 0,
    no_trade_count: 0,
    total_allocated_capital: 0
  },
  timestamp: "",
  schema_version: "1.0",
  engine_version: "1.0"
};

const defaultTradePlan: TradePlan = {
  trade_plan_id: "N/A",
  accepted_candidates: [],
  rejected_candidates: [],
  statistics: {
    total_candidates_generated: 0,
    total_candidates_accepted: 0,
    total_candidates_rejected: 0,
    momentum_accepted_count: 0,
    breakout_accepted_count: 0,
    trend_following_accepted_count: 0,
    mean_reversion_accepted_count: 0,
    range_accepted_count: 0,
    expiry_accepted_count: 0,
    scalping_accepted_count: 0,
    average_ranking_score: 0
  },
  summary: {
    best_candidate_id: "N/A",
    conclusions: []
  },
  timestamp: "",
  schema_version: "1.0",
  pipeline_version: "1.0"
};

const defaultOperationsReport: OperationsReport = {
  report_id: "N/A",
  timestamp: "",
  summary: {
    timestamp: "",
    overall_status: "OFFLINE",
    readiness_score: 0,
    uptime_str: "0s"
  },
  readiness: {
    status: "OFFLINE",
    readiness_score: 0,
    critical_blockers_count: 0,
    warnings_count: 0
  },
  services: [],
  startup: {
    config_valid: false,
    env_vars_valid: false,
    working_dirs_valid: false,
    required_folders_exist: false,
    cache_folders_exist: false,
    instrument_db_valid: false,
    checks: {}
  },
  dependencies: {
    python_packages_valid: false,
    node_modules_valid: false,
    config_files_valid: false,
    details: {}
  },
  metrics: {
    uptime_seconds: 0,
    log_size_bytes: 0,
    cache_size_bytes: 0,
    python_version: "",
    platform_info: "",
    resources: {
      cpu_percent: 0,
      memory_used_mb: 0,
      memory_percent: 0,
      disk_free_gb: 0,
      disk_percent: 0
    }
  },
  warnings: []
};

const defaultConfigurationReport: ConfigurationReport = {
  report_id: "N/A",
  timestamp: "",
  summary: {
    timestamp: "",
    active_profile_name: "DEVELOPMENT",
    schema_version: "1.0",
    status: "OK"
  },
  preferences: {
    refresh_interval_seconds: 10,
    cli_theme: "dark",
    react_theme: "dark",
    visible_panels: [],
    default_screen: "DASHBOARD",
    logging_level: "INFO",
    report_export_format: "JSON"
  },
  active_profile: {
    profile_id: "dev",
    name: "DEVELOPMENT",
    description: "Default Development Settings",
    settings: {}
  },
  items: [],
  warnings: []
};

const defaultExplanationReport: ExplanationReport = {
  report_id: "N/A",
  timestamp: "",
  summary: {
    title: "Explanation Layer Offline",
    brief_overview: "Connecting to server...",
    key_findings: []
  },
  decision: {
    overall_action: "HOLD",
    highest_priority_candidate_id: "N/A",
    portfolio_status_message: "Offline",
    overall_decision_reasoning: "",
    candidate_explanations: []
  },
  risk: {
    portfolio_risk_grade: "CONSERVATIVE",
    total_capital_allocated: 0,
    portfolio_utilization_pct: 0,
    portfolio_risk_reasoning: "",
    warnings_explanations: []
  },
  confidence: {
    highest_confidence_candidate_id: "N/A",
    confidence_reasoning: ""
  },
  strategy: {
    overall_best_strategy: "N/A",
    strategy_reasoning: "",
    all_strategy_scores: []
  },
  schema_version: "1.0",
  engine_version: "1.0"
};

const defaultIntradayReport: IntradayReport = {
  report_id: "N/A",
  evening_report_id: "N/A",
  summary: {
    plan_status: "INVALID",
    action_recommendation: "WAIT",
    total_candidates_monitored: 0,
    invalidated_candidates_count: 0,
    significant_market_changes_count: 0,
    overall_pcr_shift: 0,
    overall_vix_shift: 0
  },
  market_changes: [],
  candidate_changes: [],
  confidence_changes: [],
  risk_changes: [],
  validation_reasons: [],
  timestamp: "",
  engine_version: "1.0"
};

const defaultValidationReport: ValidationReport = {
  report_id: "N/A",
  daily_validations: [],
  strategy_performances: [],
  decision_performances: [],
  confidence_stats: {
    avg_confidence: 0,
    max_confidence: 0,
    min_confidence: 0,
    std_confidence: 0
  },
  risk_stats: {
    avg_allocated_capital: 0,
    total_allocated_capital: 0,
    max_allocated_capital: 0,
    approved_count: 0,
    rejected_count: 0
  },
  outcome_validations: [],
  summary_stats: {
    total_days_evaluated: 0,
    total_candidates_evaluated: 0,
    overall_buy_count: 0,
    overall_sell_count: 0,
    overall_watch_count: 0,
    overall_reject_count: 0,
    overall_no_trade_count: 0,
    decision_frequency_pct: 0,
    avg_market_score: 0
  },
  timestamp: "",
  schema_version: "1.0",
  engine_version: "1.0"
};

const defaultOptimizationReport: OptimizationReport = {
  report_id: "N/A",
  validation_report_id: "N/A",
  summary: {
    total_recommendations: 0,
    critical_adjustments: 0,
    potential_pnl_improvement: 0,
    recommendation_confidence_avg: 0
  },
  recommendations: [],
  strategy_optimizations: [],
  threshold_recommendations: [],
  weight_recommendations: [],
  timestamp: "",
  engine_version: "1.0"
};

const WorkstationStateContext = createContext<WorkstationStateContextProps | undefined>(undefined);

export function WorkstationStateProvider({ children }: { children: React.ReactNode }) {
  const [workspaceMode, setWorkspaceModeState] = useState<WorkspaceMode>(workspaceService.getMode());
  const [canonicalState, setCanonicalState] = useState<CanonicalWorkstationState | null>(null);
  const [lastValidState, setLastValidState] = useState<CanonicalWorkstationState | null>(null);
  const [diagnosticsError, setDiagnosticsError] = useState<string | null>(null);
  const [diagnosticsDetails, setDiagnosticsDetails] = useState<string>("");
  const [liveTickPrice, setLiveTickPrice] = useState<number | null>(null);

  const workspaceContext = useMemo<WorkspaceContext>(() => {
    const state = canonicalState ?? lastValidState;
    if (!state) return defaultWorkspaceContext;
    const bStatus = state.broker_status?.status;
    const mStatus = state.market_session?.status;
    return {
      ...defaultWorkspaceContext,
      brokerState: bStatus === "connected" ? "CONNECTED" : bStatus === "session_expired" ? "TOKEN_EXPIRED" : "DISCONNECTED",
      marketState: mStatus === "open" ? "OPEN" : mStatus === "holiday" ? "HOLIDAY" : "CLOSED",
      timestamp: state.generated_at
    };
  }, [canonicalState, lastValidState]);

  const brokerAccount = useMemo<BrokerAccount>(() => {
    const state = canonicalState ?? lastValidState;
    if (!state || !state.read_only_account_summary) return defaultBrokerAccount;
    return {
      client_id: state.read_only_account_summary.client_id,
      name: state.read_only_account_summary.name,
      email: state.read_only_account_summary.email,
      broker: state.read_only_account_summary.broker
    };
  }, [canonicalState, lastValidState]);

  const brokerFunds = useMemo<BrokerFunds>(() => defaultBrokerFunds, []);
  const portfolioReport = useMemo<LivePortfolioReport>(() => defaultPortfolioReport, []);

  const marketContext = useMemo<MarketContext>(() => {
    const state = canonicalState ?? lastValidState;
    const raw = state?.market_data;
    if (!raw) return defaultMarketContext;
    const feedHealth = state?.market_feed_status?.status?.toUpperCase() ?? "OFFLINE";
    const feedLatency = state?.data_quality?.market_data?.age_seconds ? state.data_quality.market_data.age_seconds * 1000 : 0;
    const lastTickTime = state?.data_quality?.market_data?.observed_at ?? "";
    const currentSpot = liveTickPrice ?? raw.current_spot ?? 0;
    return {
      ...defaultMarketContext,
      ...raw,
      current_spot: currentSpot,
      ltp: currentSpot,
      feed_health: feedHealth as any,
      feed_latency_ms: feedLatency,
      last_tick_time: lastTickTime
    };
  }, [canonicalState, lastValidState, liveTickPrice]);

  const optionContext = useMemo<OptionContext>(() => {
    const state = canonicalState ?? lastValidState;
    const raw = state?.option_intelligence;
    if (!raw) return defaultOptionContext;
    const currentSpot = liveTickPrice ?? state?.market_data?.current_spot ?? 0;
    return {
      ...defaultOptionContext,
      ...raw,
      underlying_spot: currentSpot,
      atm_strike: Math.round(currentSpot / 50.0) * 50.0
    };
  }, [canonicalState, lastValidState, liveTickPrice]);

  const eveningReport = useMemo<EveningReport>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.evening_report ?? defaultEveningReport;
  }, [canonicalState, lastValidState]);

  const marketScore = useMemo<MarketScore>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.market_score ?? defaultMarketScore;
  }, [canonicalState, lastValidState]);

  const opportunityContext = useMemo<OpportunityContext>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.opportunity ?? defaultOpportunityContext;
  }, [canonicalState, lastValidState]);

  const strategyEvaluation = useMemo<StrategyEvaluation>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.strategy_suitability ?? defaultStrategyEvaluation;
  }, [canonicalState, lastValidState]);

  const confidenceReport = useMemo<ConfidenceReport>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.confidence ?? defaultConfidenceReport;
  }, [canonicalState, lastValidState]);

  const riskReport = useMemo<RiskReport>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.deterministic_risk ?? defaultRiskReport;
  }, [canonicalState, lastValidState]);

  const decisionReport = useMemo<DecisionReport>(() => {
    const state = canonicalState ?? lastValidState;
    const raw = state?.decision_support;
    if (!raw) return defaultDecisionReport;
    const overallAction = (raw.blockers?.length > 0 || raw.missing_confirmations?.length > 0) ? "HOLD" : "MONITOR";
    return {
      report_id: "N/A",
      risk_report_id: "N/A",
      candidate_decisions: [],
      priority_ranking: [],
      summary: {
        overall_action: overallAction as any,
        highest_priority_candidate_id: "NONE",
        portfolio_status_message: raw.market_interpretation || "",
        conclusions: raw.warnings || []
      },
      stats: {
        total_candidates_evaluated: state?.trade_scenarios?.length ?? 0,
        buy_count: 0,
        sell_count: 0,
        watch_count: 0,
        reject_count: 0,
        no_trade_count: 0,
        total_allocated_capital: 0
      },
      timestamp: state?.generated_at || "",
      schema_version: "2.0.0",
      engine_version: "2.0.0"
    };
  }, [canonicalState, lastValidState]);

  const tradePlan = useMemo<TradePlan>(() => defaultTradePlan, []);
  
  const operationsReport = useMemo<OperationsReport>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.operations_health ?? defaultOperationsReport;
  }, [canonicalState, lastValidState]);

  const configurationReport = useMemo<ConfigurationReport>(() => defaultConfigurationReport, []);
  const explanationReport = useMemo<ExplanationReport>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.explanation ?? defaultExplanationReport;
  }, [canonicalState, lastValidState]);

  const intradayReport = useMemo<IntradayReport>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.intraday_report ?? defaultIntradayReport;
  }, [canonicalState, lastValidState]);

  const validationReport = useMemo<ValidationReport>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.validation_report ?? defaultValidationReport;
  }, [canonicalState, lastValidState]);

  const optimizationReport = useMemo<OptimizationReport>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.optimization_report ?? defaultOptimizationReport;
  }, [canonicalState, lastValidState]);

  const analyticsReport = useMemo<AnalyticsReport>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.analytics_report ?? defaultAnalyticsReport;
  }, [canonicalState, lastValidState]);

  const newsSentiment = useMemo<NewsSentimentContext>(() => {
    const state = canonicalState ?? lastValidState;
    return state?.news_intelligence ?? defaultNewsSentimentContext;
  }, [canonicalState, lastValidState]);
  const [marketConnection, setMarketConnection] = useState<"DISCONNECTED" | "CONNECTING" | "CONNECTED" | "ERROR">("DISCONNECTED");
  const [loading, setLoading] = useState<boolean>(true);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [error, setErrorState] = useState<string | null>(null);
  const [lastSyncTime, setLastSyncTime] = useState<string>("");
  const [apiLatency, setApiLatency] = useState<number | null>(null);
  const [allowLiveTrading, setAllowLiveTradingState] = useState<boolean>(
    workspaceService.getConfig().allowLiveTrading
  );
  const [preferredTradingStyle, setPreferredTradingStyleState] = useState<"Intraday" | "Swing" | "Positional">((() => {
    try {
      const saved = localStorage.getItem("PREFERRED_TRADING_STYLE");
      return (saved as any) || "Intraday";
    } catch {
      return "Intraday";
    }
  })());

  const setPreferredTradingStyle = async (style: "Intraday" | "Swing" | "Positional") => {
    try {
      setPreferredTradingStyleState(style);
      localStorage.setItem("PREFERRED_TRADING_STYLE", style);
      await fetch("/api/workspace/trading-preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preferredTradingStyle: style })
      });
      await syncBroker(true);
    } catch (err) {
      console.error("Failed to update trading style preference:", err);
    }
  };

  const setError = (err: string | null) => {
    setErrorState(err);
  };

  // [V1.3.1 FIX] syncBroker is now a documented no-op.
  // Previously it called workspaceService.fetchContext() which fetched GET /api/workspace.
  // That endpoint returns workstationState.workspaceContext from server RAM —
  // which was still DISCONNECTED immediately after login (daemon had just restarted).
  // This caused syncBroker to actively re-propagate the stale DISCONNECTED state to React.
  //
  // The WebSocket channel is the single source of truth.
  // The daemon broadcasts full state every 3 seconds automatically.
  // auth_event broadcasts handle instant auth-state changes.
  // No polling or manual REST fetch is correct here.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const syncBroker = async (_forceSync = false) => {
    // Intentionally empty. State arrives via WebSocket: type="state" (3s cycle)
    // and type="auth_event" (immediate on login/logout).
  };

  // Switch workspace operating mode
  const setWorkspaceMode = async (newMode: WorkspaceMode) => {
    setLoading(true);
    setErrorState(null);

    const result = await workspaceService.setMode(newMode, true);
    if (result.success) {
      setWorkspaceModeState(newMode);
      await syncBroker(true);
      return { success: true };
    } else {
      setLoading(false);
      setErrorState(result.error || `Transition to ${newMode} blocked by safety guard.`);
      return { success: false, error: result.error };
    }
  };

  // Logout current active Zerodha broker session
  const logoutBroker = async () => {
    setSyncing(true);
    try {
      await fetch("/api/broker/logout", { method: "POST" });
      setCanonicalState(null);
      setLastValidState(null);
      setLiveTickPrice(null);
      await syncBroker(true);
    } catch (err: any) {
      setErrorState(err.message || "Logout failed.");
    } finally {
      setSyncing(false);
    }
  };

  // Set runtime live trading authorized flag
  const setAllowLiveTrading = async (enabled: boolean) => {
    try {
      const persisted = await setRuntimeLiveTradingAllowed(enabled);
      workspaceService.updateConfig({ allowLiveTrading: persisted });
      setAllowLiveTradingState(persisted);
    } catch (err: any) {
      console.error("Failed to update live trading allowed flag:", err);
      setErrorState(err.message || "Failed to update runtime live trading flag.");
    }
  };

  // Connection State Machine Resolver
  const connectionState = useMemo<ConnectionState>(() => {
    const brokerState = workspaceContext.brokerState;
    if (brokerState !== "CONNECTED") {
      return "DISCONNECTED";
    }
    if (workspaceMode === "LIVE_TRADING") {
      return "LIVE_READY";
    }
    return "PRACTICE_READY";
  }, [workspaceMode, workspaceContext.brokerState]);

  useEffect(() => {
    let ws: globalThis.WebSocket | null = null;
    let reconnectTimeout: any = null;
    let isUnmounted = false;

    // Check parameters for redirected callbacks
    const params = new URLSearchParams(window.location.search);
    const loginStatus = params.get("login");
    const reason = params.get("reason");
    if (loginStatus === "success") {
      window.history.replaceState({}, document.title, window.location.pathname);
      syncBroker(true);
    } else if (loginStatus === "failed") {
      setErrorState(reason || "Zerodha KiteConnect login failed. Verify keys or request token.");
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    function connect() {
      if (isUnmounted) return;
      setMarketConnection("CONNECTING");
      
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/ws`;
      
      console.log(`Connecting to workstation WebSocket: ${wsUrl}`);
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (isUnmounted) return;
        console.log("Workstation WebSocket connected.");
        setMarketConnection("CONNECTED");
        setLoading(false);
      };

      ws.onmessage = (event) => {
        if (isUnmounted) return;
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "state") {
            const rawData = msg.data;

            // 1. Structural runtime checks for mandatory properties
            if (
              !rawData ||
              typeof rawData !== "object" ||
              typeof rawData.schema_version !== "string" ||
              typeof rawData.state_sequence !== "number" ||
              typeof rawData.runtime_id !== "string" ||
              typeof rawData.generated_at !== "string" ||
              !rawData.market_session ||
              !rawData.application_status ||
              !rawData.workspace_readiness ||
              !rawData.data_quality
            ) {
              setDiagnosticsError("invalid_payload");
              setDiagnosticsDetails("Payload is missing mandatory canonical fields.");
              console.error("Malformed state payload rejected.");
              return;
            }

            // 2. Schema version validation
            if (rawData.schema_version !== "2.0.0") {
              setDiagnosticsError("schema_incompatible");
              setDiagnosticsDetails(`Expected schema version 2.0.0, received ${rawData.schema_version}`);
              console.error(`Incompatible schema version: ${rawData.schema_version}`);
              return;
            }

            // 3. Session-aware sequence checking
            setCanonicalState(prev => {
              if (prev && prev.runtime_id === rawData.runtime_id) {
                if (rawData.state_sequence <= prev.state_sequence) {
                  console.warn(`Out-of-order sequence rejected: ${rawData.state_sequence} <= ${prev.state_sequence}`);
                  return prev;
                }
              } else if (prev) {
                console.log(`Runtime identity changed from ${prev.runtime_id} to ${rawData.runtime_id}. Resetting sequence tracking.`);
              }

              // Accept new state
              setLastValidState(rawData);
              setDiagnosticsError(null);
              setDiagnosticsDetails("");
              setLiveTickPrice(null); // Clear fast-path ticks on fresh state frame
              setLastSyncTime(new Date().toLocaleTimeString());
              return rawData;
            });
          } else if (msg.type === "auth_event") {
            const bState = msg.brokerState;
            const bStatus = bState === "CONNECTED" ? "connected" : bState === "TOKEN_EXPIRED" ? "session_expired" : "disconnected";
            const updateBroker = (prev: any) => {
              if (!prev) return null;
              return {
                ...prev,
                broker_status: {
                  ...prev.broker_status,
                  status: bStatus,
                  reconnect_required: bStatus === "session_expired",
                  last_successful_update: msg.timestamp || prev.broker_status.last_successful_update
                }
              };
            };
            setCanonicalState(prev => updateBroker(prev));
            setLastValidState(prev => updateBroker(prev));
            setLastSyncTime(new Date().toLocaleTimeString());
            console.log("[AUTH_EVENT] brokerState updated to:", msg.brokerState);
          } else if (msg.type === "tick") {
            const symbol = msg.symbol;
            const tick = msg.data;

            if (tick.backend_forward_timestamp) {
              try {
                const t_now = Date.now();
                const t_recv = new Date(tick.backend_forward_timestamp).getTime();
                const latency = t_now - t_recv;
                setApiLatency(Math.max(0, latency));
              } catch (e) {
                console.warn("Failed to calculate latency:", e);
              }
            }

            if (symbol === "NSE:NIFTY 50") {
              setLiveTickPrice(tick.last_price);
            }
          }
        } catch (err) {
          console.warn("WebSocket message parsing error:", err);
        }
      };

      ws.onerror = (err) => {
        console.error("Workstation WebSocket error:", err);
        setMarketConnection("ERROR");
      };

      ws.onclose = () => {
        console.log("Workstation WebSocket closed. Reconnecting...");
        setMarketConnection("DISCONNECTED");
        setCanonicalState(null); // Keep lastValidState as stale snapshot
        if (!isUnmounted) {
          reconnectTimeout = setTimeout(connect, 3000);
        }
      };
    }

    connect();

    return () => {
      isUnmounted = true;
      if (ws) {
        try {
          ws.close();
        } catch {}
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, []);

  return (
    <WorkstationStateContext.Provider
      value={{
        workspaceMode,
        workspaceContext,
        brokerAccount,
        brokerFunds,
        portfolioReport,
        marketContext,
        optionContext,
        eveningReport,
        analyticsReport,
        newsSentiment,
        marketScore,
        opportunityContext,
        strategyEvaluation,
        confidenceReport,
        riskReport,
        decisionReport,
        tradePlan,
        operationsReport,
        configurationReport,
        explanationReport,
        intradayReport,
        validationReport,
        optimizationReport,
        connectionState,
        marketConnection,
        loading,
        syncing,
        error,
        lastSyncTime,
        apiLatency,
        allowLiveTrading,
        preferredTradingStyle,
        setWorkspaceMode,
        syncBroker,
        logoutBroker,
        setAllowLiveTrading,
        setPreferredTradingStyle,
        canonicalState,
        lastValidState,
        diagnosticsError,
        diagnosticsDetails,
        setError,
      }}
    >
      {children}
    </WorkstationStateContext.Provider>
  );
}

export function useWorkstationState() {
  const context = useContext(WorkstationStateContext);
  if (!context) {
    throw new Error("useWorkstationState must be used within a WorkstationStateProvider");
  }
  return context;
}

export function useMarketData() {
  const context = useWorkstationState();
  const isLive = context.marketConnection === "CONNECTED" && !context.error;
  const raw = isLive ? context.canonicalState?.market_data : context.lastValidState?.market_data;
  return {
    data: raw || null,
    isStale: !isLive || !context.canonicalState,
    observedAt: context.canonicalState?.data_quality?.market_data?.observed_at ?? context.lastValidState?.data_quality?.market_data?.observed_at ?? null,
  };
}

export function useOptionIntelligence() {
  const context = useWorkstationState();
  const isLive = context.marketConnection === "CONNECTED" && !context.error;
  const raw = isLive ? context.canonicalState?.option_intelligence : context.lastValidState?.option_intelligence;
  return {
    data: raw || null,
    isStale: !isLive || !context.canonicalState,
  };
}

export function useBrokerStatus() {
  const context = useWorkstationState();
  const isLive = context.marketConnection === "CONNECTED" && !context.error;
  const raw = isLive ? context.canonicalState?.broker_status : context.lastValidState?.broker_status;
  return {
    data: raw || { status: "disconnected", reconnect_required: true, last_successful_update: null },
    isStale: !isLive || !context.canonicalState,
  };
}

export function useWorkspaceReadiness() {
  const context = useWorkstationState();
  const isLive = context.marketConnection === "CONNECTED" && !context.error;
  const raw = isLive ? context.canonicalState?.workspace_readiness : context.lastValidState?.workspace_readiness;
  return {
    data: raw || {},
    isStale: !isLive || !context.canonicalState,
  };
}

export function useDataQuality() {
  const context = useWorkstationState();
  const isLive = context.marketConnection === "CONNECTED" && !context.error;
  const raw = isLive ? context.canonicalState?.data_quality : context.lastValidState?.data_quality;
  return {
    data: raw || null,
    isStale: !isLive || !context.canonicalState,
  };
}

export function useMarketScore() {
  const context = useWorkstationState();
  const isLive = context.marketConnection === "CONNECTED" && !context.error;
  const raw = isLive ? context.canonicalState?.market_score : context.lastValidState?.market_score;
  return {
    data: raw || null,
    isStale: !isLive || !context.canonicalState,
  };
}

export function useNewsIntelligence() {
  const context = useWorkstationState();
  const isLive = context.marketConnection === "CONNECTED" && !context.error;
  const raw = isLive ? context.canonicalState?.news_intelligence : context.lastValidState?.news_intelligence;
  return {
    data: raw || null,
    isStale: !isLive || !context.canonicalState,
  };
}



