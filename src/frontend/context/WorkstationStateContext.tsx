// src/frontend/context/WorkstationStateContext.tsx
import React, { createContext, useContext, useState, useEffect, useMemo } from "react";
import { resolveMarketSessionState, resolveCompletedSessionMetrics, getMarketSessionBadge } from "../utils/canonicalSemanticContract";
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
  CanonicalWorkstationState,
  LiveAssistantMaterialEvent,
  LiveAssistantSnapshot
} from "../types";
import { normalizeInstrumentKey, isCanonicalNifty, isCanonicalVix } from "../utils/symbolNormalizer";

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
  stateHistory: LiveAssistantSnapshot[];
  liveEventStream: LiveAssistantMaterialEvent[];
  liveLatencyMetrics: {
    p50: number;
    p95: number;
    lastTotalMs: number;
    sampleCount: number;
  };
  streamDiagnostics: {
    ticksReceived: number;
    ticksProcessed: number;
    duplicatesRejected: number;
    outOfOrderRejected: number;
    staleRejected: number;
  };
  /** Direct live NIFTY tick from WebSocket. null when no tick received yet. */
  liveNiftyTick: {
    price: number;
    open?: number;
    high?: number;
    low?: number;
    previous_close?: number;
    change_points?: number;
    change_pct?: number;
    observed_at?: string;
    sequence?: number;
  } | null;
  /** Direct live option LTPs from WebSocket, keyed by canonical symbol. */
  liveOptionLTPs: Record<string, {
    ltp: number;
    volume?: number;
    oi?: number;
    bid?: number;
    ask?: number;
    observed_at?: string;
  }>;
}

const defaultWorkspaceContext: WorkspaceContext = {
  currentMode: "READ_ONLY",
  brokerState: "DISCONNECTED",
  marketState: "CLOSED",
  brokerType: "ZERODHA",
  marketDataSource: "LIVE",
  executionMode: "READ_ONLY",
  portfolioSource: "READ_ONLY_BROKER",
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
    trading_mode: "READ_ONLY",
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
  const [liveNiftyTick, setLiveNiftyTick] = useState<{
    price: number;
    open?: number;
    high?: number;
    low?: number;
    previous_close?: number;
    change_points?: number;
    change_pct?: number;
    observed_at?: string;
    sequence?: number;
  } | null>(null);
  const [liveOptionLTPs, setLiveOptionLTPs] = useState<Record<string, {
    ltp: number;
    volume?: number;
    oi?: number;
    bid?: number;
    ask?: number;
    observed_at?: string;
  }>>({});
  const [liveVix, setLiveVix] = useState<{
    value: number;
    change?: number;
    change_pct?: number;
    observed_at?: string;
  } | null>(null);

  const [latencyRingBuffer, setLatencyRingBuffer] = useState<number[]>([]);
  const [lastLatencyTotal, setLastLatencyTotal] = useState<number>(0);
  const [diagCounters, setDiagCounters] = useState({
    ticksReceived: 0,
    ticksProcessed: 0,
    duplicatesRejected: 0,
    outOfOrderRejected: 0,
    staleRejected: 0
  });

  // Bounded snapshot history: max 300 lightweight snapshots (set by backend tick)
  // Backend keys: market_regime → "Regime shifted", alignment → "Market Alignment shifted",
  //               advances → "Breadth changed", pcr (threshold 0.02), india_vix (threshold 0.1)
  const [stateHistory, setStateHistory] = useState<LiveAssistantSnapshot[]>([]);
  // Bounded live event stream: max 50 backend-generated MaterialEvent records
  const [liveEventStream, setLiveEventStream] = useState<LiveAssistantMaterialEvent[]>([]);

  // Sync both from canonical state on each backend tick
  const syncHistoryAndEvents = React.useCallback((incoming: CanonicalWorkstationState) => {
    const market = incoming.market_data || {};
    const breadth = market.breadth || {};
    const snapshot: LiveAssistantSnapshot = {
      generated_at: incoming.generated_at,
      state_sequence: incoming.state_sequence,
      market_state: incoming.market_session?.status || "unknown",
      spot: Number.isFinite(Number(market.current_spot)) ? Number(market.current_spot) : null,
      regime: String(market.market_regime || "UNKNOWN"),
      alignment: String(incoming.unified_intelligence?.alignment || "UNKNOWN"),
      advances: Number.isFinite(Number(breadth.advances)) ? Number(breadth.advances) : null,
      declines: Number.isFinite(Number(breadth.declines)) ? Number(breadth.declines) : null,
      pcr: Number.isFinite(Number(incoming.option_intelligence?.pcr)) ? Number(incoming.option_intelligence.pcr) : null,
      india_vix: Number.isFinite(Number(incoming.macro_intelligence?.india_vix?.value)) ? Number(incoming.macro_intelligence.india_vix.value) : null,
    };
    setStateHistory(prev => [...prev, snapshot].slice(-300));
    const events = incoming?.live_assistant_temporal_state?.material_events || [];
    setLiveEventStream(events.slice(0, 50));
  }, []);

  const workspaceContext = useMemo<WorkspaceContext>(() => {
    const state = canonicalState ?? lastValidState;
    if (!state) return defaultWorkspaceContext;
    const rawBroker = state.broker_status;
    const normStatus = rawBroker?.normalized_status || (
      rawBroker?.status === "CONNECTED_VERIFIED" || rawBroker?.execution_verified === true ? "CONNECTED_VERIFIED" :
        rawBroker?.status === "session_expired" || rawBroker?.status === "token_expired" || rawBroker?.status === "CONNECTED_AUTH_REQUIRED" || rawBroker?.blocker_code === "AUTH_REQUIRED" || rawBroker?.authenticated === false ? "CONNECTED_AUTH_REQUIRED" :
          rawBroker?.status === "reconnecting" || rawBroker?.status === "RECONNECTING" ? "RECONNECTING" :
            rawBroker?.status === "unverified" || rawBroker?.status === "BROKER_STATE_UNVERIFIED" || rawBroker?.status === "connected" ? "BROKER_STATE_UNVERIFIED" :
              "DISCONNECTED"
    );
    const mStatus = state.market_session?.status;
    return {
      ...defaultWorkspaceContext,
      brokerState: normStatus,
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
    const lastTickTime = liveNiftyTick?.observed_at ?? state?.data_quality?.market_data?.observed_at ?? "";
    const currentSpot = liveNiftyTick?.price ?? liveTickPrice ?? raw.current_spot ?? 0;
    const spotChange = liveNiftyTick?.change_points ?? raw.spot_change ?? 0;
    const spotChangePct = liveNiftyTick?.change_pct ?? raw.spot_change_pct ?? 0;
    const sessionHigh = liveNiftyTick?.high != null && liveNiftyTick.high > 0 ? liveNiftyTick.high : raw.high;
    const sessionLow = liveNiftyTick?.low != null && liveNiftyTick.low > 0 ? liveNiftyTick.low : raw.low;

    return {
      ...defaultMarketContext,
      ...raw,
      current_spot: currentSpot,
      ltp: currentSpot,
      spot_change: spotChange,
      spot_change_pct: spotChangePct,
      high: sessionHigh,
      low: sessionLow,
      feed_health: feedHealth as any,
      feed_latency_ms: feedLatency,
      last_tick_time: lastTickTime
    };
  }, [canonicalState, lastValidState, liveTickPrice, liveNiftyTick]);

  const optionContext = useMemo<OptionContext>(() => {
    const state = canonicalState ?? lastValidState;
    const raw = state?.option_intelligence;
    if (!raw) return defaultOptionContext;
    const currentSpot = liveNiftyTick?.price ?? liveTickPrice ?? state?.market_data?.current_spot ?? 0;
    const contracts = raw.chain_contracts || raw.contracts || [];

    // Overlay live LTPs onto option chain contracts
    const updatedContracts = contracts.map((c: any) => {
      const sym = c.tradingsymbol || c.symbol;
      const live = sym ? liveOptionLTPs[sym] : null;
      if (!live) return c;
      return {
        ...c,
        ltp: live.ltp > 0 ? live.ltp : c.ltp,
        bid: live.bid != null && live.bid > 0 ? live.bid : c.bid,
        ask: live.ask != null && live.ask > 0 ? live.ask : c.ask,
        volume: live.volume != null && live.volume > 0 ? live.volume : c.volume,
        oi: live.oi != null && live.oi > 0 ? live.oi : c.oi,
        last_trade_time: live.observed_at || c.last_trade_time
      };
    });

    return {
      ...defaultOptionContext,
      ...raw,
      underlying_spot: currentSpot,
      atm_strike: raw.atm_strike ?? (currentSpot > 0 ? Math.round(currentSpot / 50) * 50 : 0),
      chain_contracts: updatedContracts,
      contracts: updatedContracts
    };
  }, [canonicalState, lastValidState, liveTickPrice, liveNiftyTick, liveOptionLTPs]);

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

  const acceptCanonicalState = React.useCallback((rawData: CanonicalWorkstationState | null | undefined) => {
    if (
      !rawData || typeof rawData !== "object" ||
      typeof rawData.schema_version !== "string" ||
      typeof rawData.state_sequence !== "number" ||
      typeof rawData.runtime_id !== "string" ||
      typeof rawData.generated_at !== "string" ||
      !rawData.market_session || !rawData.application_status ||
      !rawData.workspace_readiness || !rawData.data_quality
    ) {
      setDiagnosticsError("invalid_payload");
      setDiagnosticsDetails("Payload is missing mandatory canonical fields.");
      return false;
    }
    if (rawData.schema_version !== "2.0.0") {
      setDiagnosticsError("schema_incompatible");
      setDiagnosticsDetails(`Expected schema version 2.0.0, received ${rawData.schema_version}`);
      return false;
    }

    setCanonicalState(prev => {
      if (prev && prev.runtime_id === rawData.runtime_id && rawData.state_sequence <= prev.state_sequence) return prev;
      setLastValidState(rawData);
      syncHistoryAndEvents(rawData);
      setLastSyncTime(new Date().toLocaleTimeString());
      setApiLatency(Math.max(0, Date.now() - new Date(rawData.generated_at).getTime()));
      return rawData;
    });
    setDiagnosticsError(null);
    setDiagnosticsDetails("");
    setLiveTickPrice(null);
    setLoading(false);
    return true;
  }, [syncHistoryAndEvents]);

  /*
  // Previously it called workspaceService.fetchContext() which fetched GET /api/workspace.
  // That endpoint returns workstationState.workspaceContext from server RAM —
  // which was still DISCONNECTED immediately after login (daemon had just restarted).
  // This caused syncBroker to actively re-propagate the stale DISCONNECTED state to React.
  //
  // The WebSocket channel is the single source of truth.
  // The daemon broadcasts full state every 3 seconds automatically.
  // auth_event broadcasts handle instant auth-state changes.
  */
  const firstWsReceivedRef = React.useRef(false);

  // Bootstrap from the latest canonical server snapshot so the UI does not
  // depend on the first WebSocket frame to leave its loading state. Subsequent
  // state updates continue to arrive over the WebSocket channel.
  const syncBroker = async (_forceSync = false) => {
    setSyncing(true);
    try {
      const response = await fetch("/api/workspace");
      if (!response.ok) throw new Error(`Workspace bootstrap failed (${response.status})`);
      const rawData = await response.json();
      console.log("[BOOT-FE] first REST snapshot received");
      if (!acceptCanonicalState(rawData)) throw new Error("Workspace bootstrap returned an invalid canonical state");
      setErrorState(null);
    } catch (err: any) {
      setErrorState(err.message || "Workspace bootstrap failed.");
    } finally {
      setLoading(false);
      setSyncing(false);
    }
  };

  // Switch workspace operating mode
  const setWorkspaceMode = async (newMode: WorkspaceMode) => {
    setLoading(true);
    setErrorState(null);
    try {
      const result = await workspaceService.setMode(newMode, true);
      if (result.success) {
        setWorkspaceModeState(newMode);
        await syncBroker(true);
        return { success: true };
      }
      setErrorState(result.error || `Transition to ${newMode} blocked by safety guard.`);
      return { success: false, error: result.error };
    } finally {
      setLoading(false);
    }
  };

  // Logout current active Zerodha broker session
  const logoutBroker = async () => {
    setSyncing(true);
    try {
      await fetch("/api/broker/logout", { method: "POST" });
      setCanonicalState(null);
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
    const connected = params.get("connected") || params.get("broker");
    const loginStatus = params.get("login") || params.get("status");

    if (connected === "true" || connected === "connected" || loginStatus === "success") {
      window.history.replaceState({}, document.title, window.location.pathname);
      syncBroker(true);
    } else if (loginStatus === "failed") {
      const reason = params.get("reason");
      setErrorState(reason || "Zerodha KiteConnect login failed.");
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
      };

      ws.onmessage = (event) => {
        if (isUnmounted) return;
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "state") {
            if (!firstWsReceivedRef.current) {
              firstWsReceivedRef.current = true;
              console.log("[BOOT-FE] first WS snapshot received");
            }
            acceptCanonicalState(msg.data);
          } else if (msg.type === "auth_event" || msg.type === "phase3_broker_health_updated") {
            const raw = msg.data || {};
            const normStatus = raw.status || raw.normalized_status || msg.brokerState || "DISCONNECTED";
            const updateBroker = (prev: any) => {
              if (!prev) return null;
              return {
                ...prev,
                broker_status: {
                  ...prev.broker_status,
                  ...raw,
                  status: normStatus,
                  normalized_status: normStatus,
                  execution_verified: normStatus === "CONNECTED_VERIFIED",
                  authenticated: normStatus === "CONNECTED_VERIFIED" || normStatus === "BROKER_STATE_UNVERIFIED",
                  session_valid: normStatus === "CONNECTED_VERIFIED" || normStatus === "BROKER_STATE_UNVERIFIED",
                  reconciliation_complete: normStatus === "CONNECTED_VERIFIED",
                  reconnect_required: normStatus !== "CONNECTED_VERIFIED",
                  last_successful_update: msg.timestamp || prev.broker_status?.last_successful_update
                }
              };
            };
            setCanonicalState(prev => updateBroker(prev));
            setLastValidState(prev => updateBroker(prev));
            setLastSyncTime(new Date().toLocaleTimeString());
            console.log("[AUTH_EVENT] brokerState updated to:", normStatus);
          } else if (msg.type === "live_event") {
            const eventData = msg.data;
            const t_now = Date.now();
            if (eventData.transport_sent_at || eventData.backend_received_at) {
              try {
                const t_ref = new Date(eventData.transport_sent_at || eventData.backend_received_at).getTime();
                const latency = Math.max(0, t_now - t_ref);
                setApiLatency(latency);
                setLastLatencyTotal(latency);
                setLatencyRingBuffer(prev => [...prev.slice(-99), latency]);
              } catch (e) {
                console.warn("Latency calculation error:", e);
              }
            }

            const sym = normalizeInstrumentKey(eventData.symbol);
            if (isCanonicalNifty(sym)) {
              setLiveNiftyTick({
                price: eventData.price,
                open: eventData.open,
                high: eventData.high,
                low: eventData.low,
                previous_close: eventData.previous_close,
                change_points: eventData.change_points,
                change_pct: eventData.change_pct,
                observed_at: eventData.provider_observed_at,
                sequence: eventData.state_sequence
              });
              setLiveTickPrice(eventData.price);
            } else if (isCanonicalVix(sym)) {
              setLiveVix({
                value: eventData.price,
                change: eventData.change_points,
                change_pct: eventData.change_pct,
                observed_at: eventData.provider_observed_at
              });
            } else if (sym) {
              setLiveOptionLTPs(prev => ({
                ...prev,
                [sym]: {
                  ltp: eventData.price,
                  volume: eventData.volume,
                  oi: eventData.oi,
                  bid: eventData.bid,
                  ask: eventData.ask,
                  observed_at: eventData.provider_observed_at
                }
              }));
            }

            setDiagCounters(prev => ({
              ...prev,
              ticksReceived: prev.ticksReceived + 1,
              ticksProcessed: prev.ticksProcessed + 1
            }));
          } else if (msg.type === "tick") {
            const symbol = normalizeInstrumentKey(msg.symbol);
            const tick = msg.data;

            if (tick.backend_forward_timestamp) {
              try {
                const t_now = Date.now();
                const t_recv = new Date(tick.backend_forward_timestamp).getTime();
                const latency = t_now - t_recv;
                setApiLatency(Math.max(0, latency));
                setLastLatencyTotal(latency);
                setLatencyRingBuffer(prev => [...prev.slice(-99), latency]);
              } catch (e) {
                console.warn("Failed to calculate latency:", e);
              }
            }

            if (isCanonicalNifty(symbol)) {
              if (tick.last_price > 0) {
                setLiveTickPrice(tick.last_price);
                setLiveNiftyTick(prev => ({
                  price: tick.last_price,
                  open: tick.ohlc?.open ?? prev?.open,
                  high: tick.ohlc?.high ?? prev?.high,
                  low: tick.ohlc?.low ?? prev?.low,
                  previous_close: tick.ohlc?.close ?? prev?.previous_close,
                  change_points: prev?.previous_close ? tick.last_price - prev.previous_close : prev?.change_points,
                  change_pct: prev?.previous_close ? ((tick.last_price - prev.previous_close) / prev.previous_close) * 100 : prev?.change_pct,
                  observed_at: tick.exchange_timestamp,
                  sequence: tick.state_sequence
                }));
              }
            } else if (isCanonicalVix(symbol)) {
              if (tick.last_price > 0) {
                setLiveVix({
                  value: tick.last_price,
                  observed_at: tick.exchange_timestamp
                });
              }
            } else if (symbol) {
              if (tick.last_price > 0) {
                setLiveOptionLTPs(prev => ({
                  ...prev,
                  [symbol]: {
                    ltp: tick.last_price,
                    volume: tick.volume,
                    oi: tick.oi,
                    observed_at: tick.exchange_timestamp
                  }
                }));
              }
            }

            setDiagCounters(prev => ({
              ...prev,
              ticksReceived: prev.ticksReceived + 1,
              ticksProcessed: prev.ticksProcessed + 1
            }));
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
        if (!isUnmounted) {
          reconnectTimeout = setTimeout(connect, 3000);
        }
      };
    }

    console.log("[BOOT-FE] provider mounted");
    console.log("[BOOT-FE] websocket connect initiated");
    connect();
    syncBroker(true);

    return () => {
      isUnmounted = true;
      if (ws) {
        try {
          ws.close();
        } catch { }
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, [acceptCanonicalState]);

  const liveLatencyMetrics = useMemo(() => {
    if (latencyRingBuffer.length === 0) {
      return { p50: 0, p95: 0, lastTotalMs: lastLatencyTotal, sampleCount: 0 };
    }
    const sorted = [...latencyRingBuffer].sort((a, b) => a - b);
    const p50 = sorted[Math.floor(sorted.length * 0.5)] || 0;
    const p95 = sorted[Math.floor(sorted.length * 0.95)] || 0;
    return {
      p50: Math.round(p50),
      p95: Math.round(p95),
      lastTotalMs: Math.round(lastLatencyTotal),
      sampleCount: latencyRingBuffer.length
    };
  }, [latencyRingBuffer, lastLatencyTotal]);

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
        stateHistory,
        liveEventStream,
        liveLatencyMetrics,
        streamDiagnostics: diagCounters,
        liveNiftyTick,
        liveOptionLTPs,
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

/**
 * Returns raw canonical market_data WITHOUT live tick overlay.
 * Use this for ANALYTICAL fields only (regime, trend, breadth, support/resistance).
 *
 * @deprecated For instantaneous live price presentation (spot, change, high, low)
 * use `useLiveMarketPresentation()` or `useWorkstationState().marketContext` which
 * already has the live tick overlay applied.
 */
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
  const raw = context.canonicalState?.broker_status || context.lastValidState?.broker_status;
  return {
    data: raw || { status: "disconnected", reconnect_required: true, last_successful_update: null },
    isStale: context.marketConnection !== "CONNECTED" || !context.canonicalState,
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

/**
 * useLiveMarketPresentation — Authoritative live presentation contract.
 *
 * Single hook for ALL instantaneous market price display surfaces.
 * Applies session gating:
 *   OPEN        → live tick wins (liveNiftyTick > marketContext canonical)
 *   PRE_MARKET  → canonical only; no live tick override
 *   POST_MARKET → canonical final only; live tick must NOT override
 *   CLOSED      → canonical only
 *
 * Source labels:
 *   LIVE_TICK         — live WebSocket tick active, session OPEN
 *   CANONICAL_FALLBACK — canonical valid, no live tick or session not OPEN
 *   UNAVAILABLE       — no data
 *
 * DO NOT drive analytical fields (regime, breadth, confidence, PCR,
 * support/resistance, scenarios) from this hook — use canonical hooks.
 */
export function useLiveMarketPresentation() {
  const ctx = useWorkstationState();

  const state = ctx.canonicalState ?? ctx.lastValidState;
  const mc = ctx.marketContext;
  const raw = state?.market_data;

  const sessionState = resolveMarketSessionState(state);
  const sessionBadge = getMarketSessionBadge(sessionState);
  const isOpenSession = sessionBadge.isOpen;

  const completed = resolveCompletedSessionMetrics(
    state,
    ctx.marketContext
  );

  const currentSpot = isOpenSession
    ? (mc.current_spot > 0 ? mc.current_spot : null)
    : sessionBadge.isPostMarket
      ? (completed.close ?? null)
      : (
        raw?.current_spot != null &&
          Number(raw.current_spot) > 0
          ? Number(raw.current_spot)
          : null
      );

  const change = isOpenSession
    ? (mc.spot_change ?? null)
    : sessionBadge.isPostMarket
      ? (completed.change ?? null)
      : (raw?.spot_change ?? null);

  const changePct = isOpenSession
    ? (mc.spot_change_pct ?? null)
    : sessionBadge.isPostMarket
      ? (completed.changePercent ?? null)
      : (raw?.spot_change_pct ?? null);

  const high = isOpenSession
    ? (mc.high && mc.high > 0 ? mc.high : null)
    : sessionBadge.isPostMarket
      ? (completed.high ?? null)
      : (
        raw?.high != null && Number(raw.high) > 0
          ? Number(raw.high)
          : null
      );

  const low = isOpenSession
    ? (mc.low && mc.low > 0 ? mc.low : null)
    : sessionBadge.isPostMarket
      ? (completed.low ?? null)
      : (
        raw?.low != null && Number(raw.low) > 0
          ? Number(raw.low)
          : null
      );

  const lastTickTime = isOpenSession
    ? (mc.last_tick_time || null)
    : (raw?.last_tick_time || null);

  const hasLiveTick = ctx.liveNiftyTick != null;

  const source:
    | "LIVE_TICK"
    | "CANONICAL_FALLBACK"
    | "COMPLETED_SESSION"
    | "UNAVAILABLE" =
    isOpenSession && hasLiveTick
      ? "LIVE_TICK"
      : sessionBadge.isPostMarket && currentSpot != null
        ? "COMPLETED_SESSION"
        : currentSpot != null
          ? "CANONICAL_FALLBACK"
          : "UNAVAILABLE";

  const freshness:
    | "FRESH"
    | "LAST_VALID"
    | "FINAL"
    | "UNAVAILABLE" =
    source === "LIVE_TICK"
      ? "FRESH"
      : source === "COMPLETED_SESSION"
        ? "FINAL"
        : source === "CANONICAL_FALLBACK"
          ? "LAST_VALID"
          : "UNAVAILABLE";

  return {
    sessionMode: sessionBadge.isOpen
      ? "OPEN"
      : sessionBadge.isPreMarket
        ? "PRE_MARKET"
        : sessionBadge.isPostMarket
          ? "POST_MARKET"
          : "CLOSED",

    sessionBadge,
    isOpenSession,

    currentSpot,
    change,
    changePct,
    high,
    low,
    lastTickTime,

    source,
    freshness,

    optionLTPs: ctx.liveOptionLTPs,

    vix:
      state?.macro_intelligence?.india_vix?.value ??
      mc.india_vix ??
      null,
  };
}