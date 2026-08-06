// src/frontend/types.ts

// --- MARKET INTELLIGENCE TYPES ---
export interface MarketContext {
  // Spot & Tick
  current_spot: number;
  ltp: number;
  last_tick_time: string;
  // Bid / Ask
  bid: number;
  ask: number;
  spread: number;
  // Volume & OI
  volume: number;
  oi: number;
  oi_change: number;
  // Computed from live ticks
  vwap: number;
  atr: number;
  // Volatility
  india_vix: number;
  volatility_state: string;
  // Options
  pcr: number;
  atm_strike: number;
  current_weekly_expiry: string;
  current_monthly_expiry: string;
  // Regime / Trend (computed from live data)
  market_regime: string;
  trend_direction: string;
  trend_strength: number;
  support_levels: number[];
  resistance_levels: number[];
  // Breadth
  market_breadth: number;
  // Feed health
  feed_latency_ms: number;
  feed_health: "HEALTHY" | "DEGRADED" | "OFFLINE" | "WAITING";
  // Session
  trading_session: string;
  current_expiry: string;
  timestamp: string;
}

// --- OPTION INTELLIGENCE TYPES ---
export interface OptionContext {
  underlying_spot: number;
  atm_strike: number;
  strike_step: number;
  current_weekly_expiry: string;
  current_monthly_expiry: string;
  next_weekly_expiry?: string;
  next_monthly_expiry?: string;
  far_expiry?: string;
  all_expiries?: string[];
  time_to_expiry: number; // in days
  atm_iv: number;
  expected_move: number;
  pcr: number;
  max_pain: number;
  highest_call_oi: number;
  highest_put_oi: number;
  highest_call_oi_change: number;
  highest_put_oi_change: number;
  support_strikes: number[];
  resistance_strikes: number[];
  liquidity_metrics: Record<string, any>;
  option_chain_summary: Record<string, any>;
  top_candidate_strikes: Array<Record<string, any>>;
  market_option_bias: string;
  timestamp: string;
  schema_version: string;
  pipeline_version: string;
}

// --- NEWS INTELLIGENCE TYPES ---
export interface NewsArticle {
  headline: string;
  summary: string;
  source: string;
  published_at: string;
  url: string;
  sentiment_score: number; // -1.0 to 1.0
  severity: "LOW" | "MEDIUM" | "HIGH";
  decayed_sentiment: number;
}

export interface NewsSentimentContext {
  articles: NewsArticle[];
  overall_sentiment: number; // -1.0 to 1.0
  sentiment_bias: "BULLISH" | "BEARISH" | "NEUTRAL";
  is_news_panic_active: boolean;
  timestamp: string;
}

// --- MARKET SCORING TYPES ---
export interface TrendScore {
  trend_strength_score: number;
  ema_alignment_score: number;
  adx_score: number;
  slope_score: number;
  momentum_score: number;
  overall_trend_score: number;
}

export interface OptionScore {
  pcr_score: number;
  max_pain_score: number;
  oi_structure_score: number;
  oi_buildup_score: number;
  liquidity_score: number;
  iv_score: number;
  expected_move_score: number;
  overall_option_score: number;
}

export interface VolatilityScore {
  atr_score: number;
  compression_score: number;
  expansion_score: number;
  iv_env_score: number;
  expected_move_score: number;
  overall_volatility_score: number;
}

export interface LiquidityScore {
  spread_score: number;
  volume_score: number;
  oi_score: number;
  tradability_score: number;
  overall_liquidity_score: number;
}

export interface SessionScore {
  session_type_score: number;
  is_tradable_score: number;
  overall_session_score: number;
}

export interface ExpiryScore {
  days_remaining_score: number;
  expiry_type_score: number;
  classification_score: number;
  overall_expiry_score: number;
}

export interface ConfluenceScore {
  trend_confluence_score: number;
  support_resistance_score: number;
  option_bias_score: number;
  volatility_score: number;
  liquidity_score: number;
  overall_confluence_score: number;
}

export interface MarketScore {
  trend: TrendScore;
  options: OptionScore;
  volatility: VolatilityScore;
  liquidity: LiquidityScore;
  session: SessionScore;
  expiry: ExpiryScore;
  confluence: ConfluenceScore;
  overall_score: number;
  letter_grade: string;
  classification: string;
  timestamp: string;
  schema_version: string;
  pipeline_version: string;
}

// --- OPPORTUNITY ANALYSIS TYPES ---
export interface OpportunityClassification {
  value: "EXCELLENT" | "GOOD" | "WATCHLIST" | "WAIT" | "POOR" | "AVOID";
  description: string;
}

export interface DirectionalBias {
  value: "BULLISH" | "BEARISH" | "SIDEWAYS" | "NEUTRAL";
  description: string;
}

export interface OpportunityStrength {
  imbalance_magnitude: number;
  trend_force: number;
  option_force: number;
  liquidity_force: number;
  overall_strength: number; // 0 to 100
}

export interface OpportunityWarning {
  warning_type: string;
  message: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
}

export interface InvalidationFactor {
  factor_type: string;
  is_invalidated: boolean;
  reason: string;
}

export interface OpportunityProfile {
  opportunity_type: string;
  momentum_suitability: "SUITABLE" | "UNSUITABLE" | "NEUTRAL";
  breakout_suitability: "SUITABLE" | "UNSUITABLE" | "NEUTRAL";
  reversal_suitability: "SUITABLE" | "UNSUITABLE" | "NEUTRAL";
  range_suitability: "SUITABLE" | "UNSUITABLE" | "NEUTRAL";
  scalping_suitability: "SUITABLE" | "UNSUITABLE" | "NEUTRAL";
  trend_following_suitability: "SUITABLE" | "UNSUITABLE" | "NEUTRAL";
  expiry_suitability: "SUITABLE" | "UNSUITABLE" | "NEUTRAL";
  suitability_reasons: string[];
}

export interface MarketBreadthContext {
  advance_decline_ratio?: number;
  sector_strength?: Record<string, number>;
  bank_nifty_confirmation?: boolean;
  fin_nifty_confirmation?: boolean;
  large_cap_participation?: number;
  mid_cap_participation?: number;
  is_available: boolean;
}

export interface GlobalContext {
  gift_nifty_status?: "POSITIVE" | "NEGATIVE" | "FLAT";
  us_markets_status?: "BULLISH" | "BEARISH" | "NEUTRAL";
  european_markets_status?: string;
  asian_markets_status?: string;
  vix_trend?: "RISING" | "FALLING" | "STABLE";
  usdinr_trend?: string;
  crude_oil_trend?: string;
  is_available: boolean;
}

export interface OpportunityContext {
  classification: OpportunityClassification;
  profile: OpportunityProfile;
  strength: OpportunityStrength;
  directional_bias: DirectionalBias;
  warnings: OpportunityWarning[];
  invalidation_factors: InvalidationFactor[];
  has_opportunity: boolean;
  timestamp: string;
  breadth: MarketBreadthContext;
  global_ctx: GlobalContext;
  schema_version: string;
  pipeline_version: string;
}

// --- STRATEGY EVALUATION TYPES ---
export interface StrategyReason {
  reason_type: string;
  message: string;
}

export interface StrategyWarning {
  warning_type: string;
  message: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
}

export interface StrategyConstraint {
  constraint_type: string;
  message: string;
  is_violated: boolean;
}

export interface StrategyScore {
  strategy_name: "MOMENTUM" | "BREAKOUT" | "TREND_FOLLOWING" | "MEAN_REVERSION" | "RANGE" | "EXPIRY" | "SCALPING";
  suitability_score: number;
  suitability_level: "HIGH" | "MEDIUM" | "LOW" | "NONE";
  reasons: StrategyReason[];
  warnings: StrategyWarning[];
  constraints: StrategyConstraint[];
  required_conditions_met: string[];
  rejected_conditions_met: string[];
}

export interface EvaluationSummary {
  top_strategies: string[];
  suitable_strategies_count: number;
  unsuitable_strategies_count: number;
  conclusions: string[];
}

export interface StrategyEvaluation {
  overall_best_strategy: string;
  evaluations: StrategyScore[];
  momentum_evaluation: StrategyScore;
  breakout_evaluation: StrategyScore;
  trend_following_evaluation: StrategyScore;
  mean_reversion_evaluation: StrategyScore;
  range_evaluation: StrategyScore;
  expiry_evaluation: StrategyScore;
  scalping_evaluation: StrategyScore;
  summary: EvaluationSummary;
  timestamp: string;
  schema_version: string;
  pipeline_version: string;
}

// --- TRADE PLANNER TYPES ---
export interface CandidateReason {
  reason_type: string;
  message: string;
}

export interface CandidateWarning {
  warning_type: string;
  message: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
}

export interface CandidateRejection {
  strategy_name: string;
  tradingsymbol: string;
  reason_type: string;
  message: string;
}

export interface TradeCandidate {
  candidate_id: string;
  strategy_name: string;
  tradingsymbol: string;
  strike: number;
  instrument_type: "CE" | "PE";
  expiry: string;
  distance_from_atm: number;
  atm_distance_class: "ATM" | "ATM_PLUS_1" | "ATM_MINUS_1" | "ATM_PLUS_2" | "ATM_MINUS_2" | "OTHER";
  oi: number;
  volume: number;
  spread_pct: number;
  iv: number;
  tradability_score: number;
  suitability_score: number;
  ranking_score: number;
  rank: number;
  reasons: CandidateReason[];
  warnings: CandidateWarning[];
  expiry_reason?: string;
}

export interface PlannerStatistics {
  total_candidates_generated: number;
  total_candidates_accepted: number;
  total_candidates_rejected: number;
  momentum_accepted_count: number;
  breakout_accepted_count: number;
  trend_following_accepted_count: number;
  mean_reversion_accepted_count: number;
  range_accepted_count: number;
  expiry_accepted_count: number;
  scalping_accepted_count: number;
  average_ranking_score: number;
}

export interface PlannerSummary {
  best_candidate_id: string;
  conclusions: string[];
}

export interface TradePlan {
  trade_plan_id: string;
  accepted_candidates: TradeCandidate[];
  rejected_candidates: CandidateRejection[];
  statistics: PlannerStatistics;
  summary: PlannerSummary;
  timestamp: string;
  schema_version: string;
  pipeline_version: string;
}

// --- CONFIDENCE TYPES ---
export interface ConfidenceReport {
  report_id: string;
  trade_plan_id: string;
  confidence_scores: Record<string, number>; // candidate_id -> confidence_score (0-100)
  scoring_factors: Record<string, Array<{ factor: string; score: number; weight: number }>>;
  summary_message: string;
  timestamp: string;
}

// --- RISK TYPES ---
export interface ApprovedCandidate {
  candidate_id: string;
  tradingsymbol: string;
  allocated_capital: number;
  allocated_lots: number;
  risk_pnl_limit: number;
  stop_loss_price: number;
  target_price: number;
  leverage_ratio: number;
}

export interface RiskReport {
  report_id: string;
  confidence_report_id: string;
  approved_candidates: ApprovedCandidate[];
  total_capital_allocated: number;
  portfolio_utilization_pct: number;
  risk_grade: "CONSERVATIVE" | "MODERATE" | "AGGRESSIVE";
  active_rules_triggered: string[];
  block_reasons: string[];
  warnings: string[];
  timestamp: string;
}

// --- DECISION TYPES ---
export interface DecisionReason {
  reason_type: string;
  message: string;
  metric_name: string;
  metric_value: number;
}

export interface DecisionWarning {
  warning_type: string;
  message: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
}

export interface CandidateDecision {
  candidate_id: string;
  tradingsymbol: string;
  strategy_name: string;
  decision: "BUY" | "SELL" | "WATCH" | "REJECT" | "NO TRADE";
  priority_score: number;
  execution_priority: number;
  explanation: string;
  supporting_evidence: DecisionReason[];
  blocking_factors: DecisionReason[];
  warnings: DecisionWarning[];
  allocated_capital: number;
  allocated_lots: number;
  expiry_reason?: string;
}

export interface DecisionSummary {
  overall_action: "EXECUTE" | "MONITOR" | "HOLD";
  highest_priority_candidate_id: string;
  portfolio_status_message: string;
  conclusions: string[];
}

export interface DecisionStatistics {
  total_candidates_evaluated: number;
  buy_count: number;
  sell_count: number;
  watch_count: number;
  reject_count: number;
  no_trade_count: number;
  total_allocated_capital: number;
}

export interface DecisionReport {
  report_id: string;
  risk_report_id: string;
  candidate_decisions: CandidateDecision[];
  priority_ranking: string[];
  summary: DecisionSummary;
  stats: DecisionStatistics;
  timestamp: string;
  schema_version: string;
  engine_version: string;
}

// --- EXECUTION / BROKER TYPES ---
export interface ExecutionOrder {
  candidate_id: string;
  tradingsymbol: string;
  exchange: string;
  transaction_type: "BUY" | "SELL";
  quantity: number;
  product: "MIS" | "NRML" | "CNC";
  order_type: "MARKET" | "LIMIT" | "SL" | "SL-M";
  price: number;
  trigger_price: number;
}

export interface ExecutionReport {
  report_id: string;
  request_id: string;
  submitted_orders: ExecutionOrder[];
  accepted_orders: ExecutionOrder[];
  rejected_orders: ExecutionOrder[];
  exchange_order_id: string;
  broker_order_id: string;
  timestamp: string;
  failure_reason: string;
  status: "PENDING" | "COMPLETED" | "FAILED" | "PARTIAL";
}

export interface BrokerAccount {
  client_id: string;
  name: string;
  email: string;
  broker: string;
}

export interface BrokerFunds {
  available_cash: number;
  margins: number;
  utilized_margin: number;
  available_margin: number;
}

export interface BrokerPosition {
  tradingsymbol: string;
  exchange: string;
  product: string;
  quantity: number;
  average_price: number;
  last_price: number;
  pnl: number;
  today_mtm: number;
}

export interface BrokerHolding {
  tradingsymbol: string;
  exchange: string;
  product: string;
  quantity: number;
  average_price: number;
  last_price: number;
  pnl: number;
}

export interface BrokerOrder {
  order_id: string;
  exchange_order_id: string;
  tradingsymbol: string;
  exchange: string;
  transaction_type: "BUY" | "SELL";
  quantity: number;
  product: string;
  order_type: string;
  status: "COMPLETE" | "REJECTED" | "OPEN" | "CANCELLED";
  price: number;
  filled_quantity: number;
  order_timestamp: string;
  status_message: string;
}

// --- PAPER TRADING TYPES ---
export interface PaperTrade {
  trade_id: string;
  decision_id: string;
  candidate_id: string;
  tradingsymbol: string;
  entry_time: string;
  premium: number;
  lots: number;
  capital: number;
  strategy_name: string;
  confidence_score: number;
  risk_grade: string;
  action: "BUY" | "SELL";
}

export interface PaperPosition {
  position_id: string;
  trade: PaperTrade;
  current_mtm: number;
  peak_mtm: number;
  drawdown: number;
  holding_time_seconds: number;
  status: "OPEN" | "CLOSED";
  current_premium: number;
}

export interface TradeJournalEntry {
  entry_id: string;
  trade_id: string;
  candidate_id: string;
  tradingsymbol: string;
  decision_summary: string;
  explanation_summary: string;
  market_score_val: number;
  market_score_grade: string;
  confidence_score: number;
  risk_grade: string;
  strategy_name: string;
  entry_time: string;
  entry_premium: number;
  entry_capital: number;
  entry_lots: number;
  exit_time: string;
  exit_premium: number;
  exit_reason: string;
  pnl: number;
  pnl_pct: number;
  duration_seconds: number;
  outcome: "WIN" | "LOSS" | "FLAT";
  market_regime: string;
  confidence_band: string;
  notes: string;
}

export interface PortfolioSnapshot {
  timestamp: string;
  total_capital: number;
  allocated_capital: number;
  available_capital: number;
  open_positions_count: number;
  closed_trades_count: number;
  total_pnl: number;
  realized_pnl: number;
  unrealized_pnl: number;
}

// --- PERFORMANCE ANALYTICS TYPES ---
export interface PerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  average_profit: number;
  average_loss: number;
  profit_factor: number;
  expectancy: number;
  average_holding_time: number;
  largest_winner: number;
  largest_loser: number;
  maximum_drawdown: number;
  recovery_factor: number;
}

export interface AnalyticsStrategyPerformance {
  strategy_name: string;
  total_trades: number;
  win_rate: number;
  average_return: number;
  profit_factor: number;
  expectancy: number;
  capital_utilization: number;
}

export interface AnalyticsRegimePerformance {
  market_regime: string;
  total_trades: number;
  win_rate: number;
  average_return: number;
  profit_factor: number;
  expectancy: number;
}

export interface OpportunityPerformance {
  opportunity_classification: string;
  total_trades: number;
  win_rate: number;
  average_return: number;
  profit_factor: number;
  expectancy: number;
}

export interface GradePerformance {
  market_score_grade: string;
  total_trades: number;
  win_rate: number;
  average_return: number;
  profit_factor: number;
  expectancy: number;
}

export interface BiasPerformance {
  directional_bias: string;
  total_trades: number;
  win_rate: number;
  average_return: number;
  profit_factor: number;
  expectancy: number;
}

export interface MarketPerformance {
  by_regime: AnalyticsRegimePerformance[];
  by_opportunity: OpportunityPerformance[];
  by_grade: GradePerformance[];
  by_bias: BiasPerformance[];
}

export interface ConfidencePerformance {
  confidence_band: string;
  total_trades: number;
  win_rate: number;
  average_return: number;
}

export interface RiskPerformance {
  risk_grade: string;
  total_trades: number;
  win_rate: number;
  average_return: number;
  capital_allocation_avg: number;
  portfolio_utilization: number;
}

export interface TimePerformance {
  by_entry_hour: Record<number, number>;
  by_day_of_week: Record<string, number>;
  avg_holding_time: number;
}

export interface PortfolioPerformance {
  initial_capital: number;
  final_capital: number;
  total_pnl: number;
  return_on_capital: number;
  maximum_drawdown: number;
  sharpe_ratio: number;
  profit_factor: number;
}

export interface AnalyticsSummary {
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

export interface AnalyticsReport {
  report_id: string;
  overall_metrics: PerformanceMetrics;
  strategy_metrics: AnalyticsStrategyPerformance[];
  market_metrics: MarketPerformance;
  confidence_metrics: ConfidencePerformance[];
  risk_metrics: RiskPerformance[];
  time_metrics: TimePerformance;
  portfolio_metrics: PortfolioPerformance;
  summary: AnalyticsSummary;
  timestamp: string;
}

// --- HISTORICAL VALIDATION TYPES ---
export interface DailyValidation {
  date: string;
  market_score: number;
  candidates_count: number;
  buy_count: number;
  sell_count: number;
  watch_count: number;
  reject_count: number;
  no_trade_count: number;
  total_allocated_capital: number;
  decision_report_id: string;
  outcome_summary: string;
}

export interface StrategyPerformance {
  strategy_name: string;
  total_candidates: number;
  buy_count: number;
  sell_count: number;
  watch_count: number;
  reject_count: number;
  no_trade_count: number;
  avg_confidence_score: number;
}

export interface DecisionPerformance {
  decision_type: string;
  count: number;
  percentage: number;
  avg_confidence: number;
  avg_allocated_capital: number;
}

export interface ConfidenceStatistics {
  avg_confidence: number;
  max_confidence: number;
  min_confidence: number;
  std_confidence: number;
}

export interface RiskStatistics {
  avg_allocated_capital: number;
  total_allocated_capital: number;
  max_allocated_capital: number;
  approved_count: number;
  rejected_count: number;
}

export interface OutcomeValidation {
  evaluation_window: string; // "Same-day", "Next-day", "Expiry-day"
  success_count: number;
  failure_count: number;
  accuracy_pct: number;
  total_profit_loss: number;
}

export interface SummaryStatistics {
  total_days_evaluated: number;
  total_candidates_evaluated: number;
  overall_buy_count: number;
  overall_sell_count: number;
  overall_watch_count: number;
  overall_reject_count: number;
  overall_no_trade_count: number;
  decision_frequency_pct: number;
  avg_market_score: number;
}

export interface ValidationReport {
  report_id: string;
  daily_validations: DailyValidation[];
  strategy_performances: StrategyPerformance[];
  decision_performances: DecisionPerformance[];
  confidence_stats: ConfidenceStatistics;
  risk_stats: RiskStatistics;
  outcome_validations: OutcomeValidation[];
  summary_stats: SummaryStatistics;
  timestamp: string;
  schema_version: string;
  engine_version: string;
}

// --- OPTIMIZATION TYPES ---
export interface RecommendationEvidence {
  historical_sample_size: number;
  observed_improvement_potential: number;
  affected_strategies: string[];
  expected_trade_off: string;
  confidence_score: number;
}

export interface OptimizationRecommendation {
  recommendation_id: string;
  category: string;
  title: string;
  description: string;
  current_value: string;
  recommended_value: string;
  evidence: RecommendationEvidence;
  rationale: string;
}

export interface StrategyOptimization {
  strategy_name: string;
  current_accuracy: number;
  recommended_action: string;
  rationale: string;
}

export interface ThresholdRecommendation {
  parameter_name: string;
  current_value: number;
  suggested_value: number;
  direction: string;
  impact: string;
}

export interface WeightRecommendation {
  strategy_or_factor: string;
  current_weight: number;
  suggested_weight: number;
  rationale: string;
}

export interface OptimizationSummary {
  total_recommendations: number;
  critical_adjustments: number;
  potential_pnl_improvement: number;
  recommendation_confidence_avg: number;
}

export interface OptimizationReport {
  report_id: string;
  validation_report_id: string;
  summary: OptimizationSummary;
  recommendations: OptimizationRecommendation[];
  strategy_optimizations: StrategyOptimization[];
  threshold_recommendations: ThresholdRecommendation[];
  weight_recommendations: WeightRecommendation[];
  timestamp: string;
  engine_version: string;
}

// --- EVENING PLANNER TYPES ---
export interface MarketSummary {
  spot_price: number;
  vix_price: number;
  regime: string;
  trend_direction: string;
  market_score: number;
  market_grade: string;
  session_type: string;
}

export interface TomorrowOutlook {
  directional_bias: string;
  outlook_classification: string;
  opportunity_strength: number;
  key_support_levels: number[];
  key_resistance_levels: number[];
  description: string;
}

export interface RecommendedStrategy {
  strategy_name: string;
  suitability_score: number;
  suitability_level: string;
  rationale: string[];
}

export interface RecommendedCandidate {
  candidate_id: string;
  tradingsymbol: string;
  strategy_name: string;
  decision: string;
  confidence_score: number;
  priority_score: number;
  allocated_capital: number;
  allocated_lots: number;
  strike: number;
  instrument_type: string;
  expiry: string;
}

export interface RejectedCandidate {
  tradingsymbol: string;
  strategy_name: string;
  reason_type: string;
  message: string;
}

export interface RiskWatchlist {
  warnings: string[];
  portfolio_warnings: string[];
  max_capital_limit: number;
  allocated_capital: number;
  portfolio_utilization_pct: number;
  risk_grade: string;
}

export interface EventWatchlist {
  events: string[];
  expiry_days_remaining: number;
  expiry_type: string;
}

export interface PlannerChecklist {
  checklist_items: string[];
}

export interface EveningReportSummary {
  best_candidate_id: string;
  best_strategy: string;
  total_accepted_candidates: number;
  total_rejected_candidates: number;
  action_type: string;
}

export interface EveningReport {
  report_id: string;
  market_summary: MarketSummary;
  tomorrow_outlook: TomorrowOutlook;
  recommended_strategies: RecommendedStrategy[];
  top_candidates: RecommendedCandidate[];
  rejected_candidates: RejectedCandidate[];
  risk_watchlist: RiskWatchlist;
  event_watchlist: EventWatchlist;
  checklist: PlannerChecklist;
  summary: EveningReportSummary;
  timestamp: string;
  engine_version: string;
  optimization_notes: string[];
}

// --- INTRADAY ASSISTANT TYPES ---
export interface MarketChange {
  metric_name: string;
  previous_value: number | string;
  current_value: number | string;
  change_pct?: number;
  is_significant: boolean;
  message: string;
}

export interface ConfidenceChange {
  candidate_id: string;
  previous_confidence: number;
  current_confidence: number;
  change_amt: number;
  status: string;
  explanation: string;
}

export interface RiskChange {
  candidate_id: string;
  previous_risk_grade: string;
  current_risk_grade: string;
  is_risk_increased: boolean;
  triggered_new_warnings: string[];
}

export interface CandidateStatusReport {
  candidate_id: string;
  tradingsymbol: string;
  status: string;
  explanation: string;
  previous_decision: string;
  suggested_decision: string;
}

export interface IntradaySummary {
  plan_status: string; // e.g., "Plan Still Valid", "Plan Needs Review", "Plan Invalidated"
  action_recommendation: string; // "PROCEED", "WAIT", "REVIEW", "CANCEL"
  total_candidates_monitored: number;
  invalidated_candidates_count: number;
  significant_market_changes_count: number;
  overall_pcr_shift: number;
  overall_vix_shift: number;
}

export interface IntradayReport {
  report_id: string;
  evening_report_id: string;
  summary: IntradaySummary;
  market_changes: MarketChange[];
  candidate_changes: CandidateStatusReport[];
  confidence_changes: ConfidenceChange[];
  risk_changes: RiskChange[];
  validation_reasons: string[];
  timestamp: string;
  engine_version: string;
}

// --- OPERATIONS MONITOR TYPES ---
export interface ServiceStatus {
  service_name: string;
  status: string;
  latency_ms: number;
  message: string;
  last_checked: string;
}

export interface StartupDiagnostics {
  config_valid: boolean;
  env_vars_valid: boolean;
  working_dirs_valid: boolean;
  required_folders_exist: boolean;
  cache_folders_exist: boolean;
  instrument_db_valid: boolean;
  checks: Record<string, boolean>;
}

export interface DependencyStatus {
  python_packages_valid: boolean;
  node_modules_valid: boolean;
  config_files_valid: boolean;
  details: Record<string, any>;
}

export interface ResourceUsage {
  cpu_percent: number;
  memory_used_mb: number;
  memory_percent: number;
  disk_free_gb: number;
  disk_percent: number;
}

export interface SystemMetrics {
  uptime_seconds: number;
  log_size_bytes: number;
  cache_size_bytes: number;
  python_version: string;
  platform_info: string;
  resources: ResourceUsage;
}

export interface HealthWarning {
  warning_id: string;
  source: string;
  severity: string;
  message: string;
  timestamp: string;
}

export interface ReadinessStatus {
  status: string;
  readiness_score: number;
  critical_blockers_count: number;
  warnings_count: number;
}

export interface OperationsSummary {
  timestamp: string;
  overall_status: string;
  readiness_score: number;
  uptime_str: string;
}

export interface OperationsReport {
  report_id: string;
  timestamp: string;
  summary: OperationsSummary;
  readiness: ReadinessStatus;
  services: ServiceStatus[];
  startup: StartupDiagnostics;
  dependencies: DependencyStatus;
  metrics: SystemMetrics;
  warnings: HealthWarning[];
}

// --- CONFIGURATION REPORT TYPES ---
export interface ConfigurationItem {
  key: string;
  value: any;
  category: string;
  description: string;
  is_valid: boolean;
}

export interface WorkspacePreferences {
  refresh_interval_seconds: number;
  cli_theme: string;
  react_theme: string;
  visible_panels: string[];
  default_screen: string;
  logging_level: string;
  report_export_format: string;
}

export interface ConfigurationWarning {
  warning_id: string;
  category: string;
  severity: string;
  message: string;
  invalid_value?: any;
}

export interface ConfigurationMigration {
  source_version: string;
  target_version: string;
  requires_migration: boolean;
  recommendations: string[];
}

export interface ConfigurationProfile {
  profile_id: string;
  name: string;
  description: string;
  settings: Record<string, any>;
}

export interface ConfigurationStatistics {
  total_keys: number;
  valid_keys: number;
  invalid_keys: number;
  warnings_count: number;
}

export interface ConfigurationSummary {
  timestamp: string;
  active_profile_name: string;
  schema_version: string;
  status: string;
}

export interface ConfigurationReport {
  report_id: string;
  timestamp: string;
  summary: ConfigurationSummary;
  preferences: WorkspacePreferences;
  active_profile: ConfigurationProfile;
  items: ConfigurationItem[];
  warnings: ConfigurationWarning[];
  migration?: ConfigurationMigration;
  statistics?: ConfigurationStatistics;
}

// --- AI EXPLANATION TYPES ---
export interface CandidateExplanation {
  candidate_id: string;
  tradingsymbol: string;
  strategy_name: string;
  decision: string;
  decision_reasoning: string;
  lots_reasoning: string;
  confidence_reasoning: string;
  risk_reasoning: string;
}

export interface DecisionExplanation {
  overall_action: string;
  highest_priority_candidate_id: string;
  portfolio_status_message: string;
  overall_decision_reasoning: string;
  candidate_explanations: CandidateExplanation[];
}

export interface RiskExplanation {
  portfolio_risk_grade: string;
  total_capital_allocated: number;
  portfolio_utilization_pct: number;
  portfolio_risk_reasoning: string;
  warnings_explanations: string[];
}

export interface ConfidenceExplanation {
  highest_confidence_candidate_id: string;
  confidence_reasoning: string;
}

export interface StrategyExplanation {
  overall_best_strategy: string;
  strategy_reasoning: string;
  all_strategy_scores: string[];
}

export interface IntradayExplanation {
  plan_status: string;
  action_recommendation: string;
  explanation: string;
  market_change_reasons: string[];
  candidate_change_reasons: string[];
}

export interface PlannerExplanation {
  directional_bias: string;
  outlook_classification: string;
  explanation: string;
}

export interface ExplanationSummary {
  title: string;
  brief_overview: string;
  key_findings: string[];
}

export interface ExplanationReport {
  report_id: string;
  timestamp: string;
  summary: ExplanationSummary;
  decision: DecisionExplanation;
  risk: RiskExplanation;
  confidence: ConfidenceExplanation;
  strategy: StrategyExplanation;
  intraday?: IntradayExplanation;
  planner?: PlannerExplanation;
  schema_version: string;
  engine_version: string;
}

// --- ORDER LIFECYCLE MONITORING TYPES ---
export interface OrderLifecycleEvent {
  event_id: string;
  timestamp: string;
  previous_state: string;
  new_state: string;
  trigger_source: string;
  operator: string;
  broker_response?: string;
  reason?: string;
}

export interface ExecutionProgress {
  requested_quantity: number;
  filled_quantity: number;
  remaining_quantity: number;
  average_fill_price: number;
  weighted_average: number;
  completion_percentage: number;
}

export interface ExecutionTimeline {
  order_id: string;
  tradingsymbol: string;
  events: OrderLifecycleEvent[];
}

export interface OrderModificationHistory {
  modification_id: string;
  timestamp: string;
  previous_quantity: number;
  previous_price: number;
  new_quantity: number;
  new_price: number;
  status: string;
}

export interface OrderCancellationRecord {
  cancellation_id: string;
  timestamp: string;
  requested_by: string;
  reason: string;
  status: string;
}

export interface OrderLifecycleReport {
  order_id: string;
  tradingsymbol: string;
  exchange: string;
  transaction_type: "BUY" | "SELL";
  quantity: number;
  product: string;
  order_type: string;
  current_state: string;
  progress: ExecutionProgress;
  timeline: ExecutionTimeline;
  modification_history: OrderModificationHistory[];
  cancellation_record?: OrderCancellationRecord;
  broker_remarks?: string;
  timestamp: string;
}

export interface OrderLifecycleStatistics {
  average_fill_time: number;
  broker_latency: number;
  exchange_latency: number;
  fill_efficiency: number;
  slippage: number;
  partial_fill_percentage: number;
  modification_count: number;
  cancellation_rate: number;
  execution_success_rate: number;
}


// --- CANONICAL WORKSTATION STATE 2.0.0 TYPES ---

export type FreshnessStatus = "fresh" | "stale" | "blocked" | "unavailable" | "market_closed";
export type QualityStatus = "valid" | "invalid" | "unverified";
export type ValueClassification = "live" | "calculated" | "historical" | "unavailable";
export type SectionStatus = "ready" | "degraded" | "blocked" | "unavailable" | "market_closed";

export interface ValueMetadata {
  source: string;
  instrument: string | null;
  observed_at: string | null;
  received_at: string | null;
  generated_at: string | null;
  age_seconds: number | null;
  freshness_status: FreshnessStatus;
  quality_status: QualityStatus;
  value_classification: ValueClassification;
  dependencies: string[];
  warnings: string[];
  error: string | null;
}

export interface WorkspaceReadiness {
  workspace: string;
  status: string;
  accessible: boolean;
  dependency_reasons: string[];
}

export interface TradeScenario {
  scenario_name: string;
  direction: string;
  activation_condition: string;
  confirmation_conditions: string[];
  missing_confirmations: string[];
  invalidation_condition: string | null;
  target_zones: number[];
  risk_classification: string;
  scenario_confidence: number;
  status: string;
}

export interface DecisionSupport {
  market_interpretation: string;
  current_scenario_status: string;
  required_confirmations: string[];
  missing_confirmations: string[];
  invalidation_conditions: string[];
  blockers: string[];
  warnings: string[];
  human_decision_required: boolean;
  status?: string;
}

export interface ReadOnlyAccountSummary {
  client_id: string;
  name: string;
  email: string;
  broker: string;
  [key: string]: any;
}

export interface CanonicalWorkstationState {
  schema_version: string;
  state_sequence: number;
  generated_at: string;
  runtime_id: string;
  market_session: { status: string; is_closed: boolean };
  application_status: { status: string; read_only: boolean };
  broker_status: { status: string; reconnect_required: boolean; last_successful_update: string | null };
  market_feed_status: { status: string; source: string };
  market_data: any;
  technical_analysis: any;
  option_intelligence: any;
  market_score: any;
  opportunity: any;
  strategy_suitability: any;
  trade_scenarios: TradeScenario[];
  confidence: any;
  deterministic_risk: any;
  decision_support: DecisionSupport;
  explanation: any;
  news_intelligence: any;
  read_only_account_summary: ReadOnlyAccountSummary | null;
  operations_health: any;
  workspace_readiness: Record<string, WorkspaceReadiness>;
  data_quality: {
    market_data: any;
    option_intelligence: any;
  };
  evening_report: any;
  intraday_report: any;
  validation_report: any;
  optimization_report: any;
  analytics_report: any;
  warnings: string[];
  errors: string[];
}


