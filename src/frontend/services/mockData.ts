// src/frontend/services/mockData.ts
import {
  MarketContext,
  OptionContext,
  NewsSentimentContext,
  MarketScore,
  OpportunityContext,
  StrategyEvaluation,
  StrategyScore,
  TradePlan,
  ConfidenceReport,
  RiskReport,
  DecisionReport,
  BrokerAccount,
  BrokerFunds,
  BrokerPosition,
  BrokerHolding,
  BrokerOrder,
  ExecutionReport,
  PaperPosition,
  PortfolioSnapshot,
  TradeJournalEntry,
  AnalyticsReport,
  ValidationReport,
  OptimizationReport,
  EveningReport,
  IntradayReport,
  OperationsReport,
  ConfigurationReport,
  ExplanationReport,
} from "../types";

const nowISO = () => new Date().toISOString();

// 1. Market Context
export const mockMarketContext: MarketContext = {
  current_spot: 24200.50,
  ltp: 24200.50,
  last_tick_time: nowISO(),
  bid: 24200.00,
  ask: 24201.00,
  spread: 1.00,
  volume: 1200000,
  oi: 2500000,
  oi_change: 15000,
  vwap: 24185.20,
  atr: 125.40,
  india_vix: 13.85,
  volatility_state: "NORMAL",
  pcr: 1.15,
  atm_strike: 24200.0,
  current_weekly_expiry: "2026-07-16",
  current_monthly_expiry: "2026-07-30",
  market_regime: "TRENDING",
  trend_direction: "BULLISH",
  trend_strength: 78.4,
  support_levels: [24100.0, 24000.0, 23850.0],
  resistance_levels: [24300.0, 24400.0, 24550.0],
  market_breadth: 0.65,
  feed_latency_ms: 5,
  feed_health: "HEALTHY",
  trading_session: "INTRADAY",
  current_expiry: "2026-07-16",
  timestamp: nowISO(),
};

// 2. Option Context
export const mockOptionContext: OptionContext = {
  underlying_spot: 24200.50,
  atm_strike: 24200.0,
  strike_step: 50.0,
  current_weekly_expiry: "2026-07-16",
  current_monthly_expiry: "2026-07-30",
  time_to_expiry: 5.4,
  atm_iv: 14.20,
  expected_move: 185.0,
  pcr: 1.15,
  max_pain: 24200.0,
  highest_call_oi: 4500000,
  highest_put_oi: 5200000,
  highest_call_oi_change: 250000,
  highest_put_oi_change: 480000,
  support_strikes: [24100.0, 24000.0],
  resistance_strikes: [24300.0, 24400.0],
  liquidity_metrics: {
    bid_ask_spread_avg: 0.05,
    slippage_estimate_ce: 0.02,
    slippage_estimate_pe: 0.03,
    active_contracts_count: 42,
  },
  option_chain_summary: {
    total_call_volume: 12500000,
    total_put_volume: 14300000,
    oi_pcr: 1.15,
    volume_pcr: 1.14,
  },
  top_candidate_strikes: [
    { strike: 24200.0, type: "CE", premium: 155.40, oi: 3200000, volume: 8500000, iv: 14.1 },
    { strike: 24150.0, type: "CE", premium: 190.20, oi: 1500000, volume: 4200000, iv: 14.3 },
    { strike: 24250.0, type: "CE", premium: 124.80, oi: 2100000, volume: 6100000, iv: 14.0 },
    { strike: 24200.0, type: "PE", premium: 145.20, oi: 2800000, volume: 7500000, iv: 14.5 },
  ],
  market_option_bias: "BULLISH_CONFLUENCE",
  timestamp: nowISO(),
  schema_version: "1.0",
  pipeline_version: "1.0",
};

// 3. News Context
export const mockNewsSentimentContext: NewsSentimentContext = {
  articles: [
    {
      headline: "RBI Keeps Rates Unchanged, Expresses Optimism on Economic Growth Outlook",
      summary: "The Reserve Bank of India decided to hold its key repo rate steady at 6.5%, matching market expectations, while noting robust structural momentum.",
      source: "Moneycontrol",
      published_at: nowISO(),
      url: "https://moneycontrol.com/rbi-rates",
      sentiment_score: 0.65,
      severity: "HIGH",
      decayed_sentiment: 0.62,
    },
    {
      headline: "Global Chip Shortage Eases, Fueling Rally in Major Automobile and Tech Stocks",
      summary: "Supply chains are normalizing rapidly, paving the way for record production and volume targets among Indian exporters.",
      source: "Bloomberg Quint",
      published_at: nowISO(),
      url: "https://bloomberg.com/chip-supply",
      sentiment_score: 0.45,
      severity: "MEDIUM",
      decayed_sentiment: 0.40,
    },
    {
      headline: "Crude Oil Prices Ease Below $78 a Barrel, Easing Domestic Inflationary Pressures",
      summary: "WTI Crude contracts slid 1.2% in Asian hours, providing positive macros for oil-importing developing nations like India.",
      source: "Reuters",
      published_at: nowISO(),
      url: "https://reuters.com/crude-oil-prices",
      sentiment_score: 0.55,
      severity: "MEDIUM",
      decayed_sentiment: 0.48,
    }
  ],
  overall_sentiment: 0.52,
  sentiment_bias: "BULLISH",
  is_news_panic_active: false,
  timestamp: nowISO(),
};

// 4. Market Score
export const mockMarketScore: MarketScore = {
  trend: {
    trend_strength_score: 82.5,
    ema_alignment_score: 90.0,
    adx_score: 75.0,
    slope_score: 80.0,
    momentum_score: 85.0,
    overall_trend_score: 82.5,
  },
  options: {
    pcr_score: 85.0,
    max_pain_score: 90.0,
    oi_structure_score: 80.0,
    oi_buildup_score: 85.0,
    liquidity_score: 95.0,
    iv_score: 75.0,
    expected_move_score: 80.0,
    overall_option_score: 84.3,
  },
  volatility: {
    atr_score: 80.0,
    compression_score: 70.0,
    expansion_score: 85.0,
    iv_env_score: 80.0,
    expected_move_score: 85.0,
    overall_volatility_score: 80.0,
  },
  liquidity: {
    spread_score: 95.0,
    volume_score: 90.0,
    oi_score: 85.0,
    tradability_score: 90.0,
    overall_liquidity_score: 90.0,
  },
  session: {
    session_type_score: 100.0,
    is_tradable_score: 100.0,
    overall_session_score: 100.0,
  },
  expiry: {
    days_remaining_score: 85.0,
    expiry_type_score: 80.0,
    classification_score: 85.0,
    overall_expiry_score: 83.3,
  },
  confluence: {
    trend_confluence_score: 88.0,
    support_resistance_score: 85.0,
    option_bias_score: 90.0,
    volatility_score: 80.0,
    liquidity_score: 90.0,
    overall_confluence_score: 86.6,
  },
  overall_score: 84.2,
  letter_grade: "B+",
  classification: "HIGH_CONFLUENCE_BULLISH",
  timestamp: nowISO(),
  schema_version: "1.0",
  pipeline_version: "1.0",
};

// 5. Opportunity Context
export const mockOpportunityContext: OpportunityContext = {
  classification: {
    value: "EXCELLENT",
    description: "All engines aligned for safe, highly liquid option execution.",
  },
  profile: {
    opportunity_type: "TREND_CONTINUATION",
    momentum_suitability: "SUITABLE",
    breakout_suitability: "NEUTRAL",
    reversal_suitability: "UNSUITABLE",
    range_suitability: "UNSUITABLE",
    scalping_suitability: "SUITABLE",
    trend_following_suitability: "SUITABLE",
    expiry_suitability: "NEUTRAL",
    suitability_reasons: [
      "Technical scores show robust upward trend slope on the 15-minute timeframe.",
      "Options PCR shows strong bullish support and aggressive put writing confluences.",
      "VIX environment is calm and stable, minimizing tail risk exposures."
    ],
  },
  strength: {
    imbalance_magnitude: 85.2,
    trend_force: 82.5,
    option_force: 86.8,
    liquidity_force: 92.0,
    overall_strength: 86.6,
  },
  directional_bias: {
    value: "BULLISH",
    description: "Dynamic models suggest upward breakout over spot 24,200.",
  },
  warnings: [
    {
      warning_type: "RESISTANCE_PROXIMITY",
      message: "Spot price is approaching major technical resistance line at 24,300.",
      severity: "LOW",
    }
  ],
  invalidation_factors: [
    {
      factor_type: "SUPPORT_BREAK",
      is_invalidated: false,
      reason: "Triggers if spot falls below major pivot support at 24,100.",
    },
    {
      factor_type: "LOSS_OF_TREND_ALIGNMENT",
      is_invalidated: false,
      reason: "Triggers if 15-minute slope flattens below threshold 0.15.",
    }
  ],
  has_opportunity: true,
  timestamp: nowISO(),
  breadth: {
    advance_decline_ratio: 2.15,
    sector_strength: { "Nifty Bank": 0.85, "Nifty IT": 1.10, "Nifty Auto": 0.60, "Nifty FMCG": -0.15 },
    bank_nifty_confirmation: true,
    fin_nifty_confirmation: true,
    large_cap_participation: 76.5,
    mid_cap_participation: 62.0,
    is_available: true,
  },
  global_ctx: {
    gift_nifty_status: "POSITIVE",
    us_markets_status: "BULLISH",
    european_markets_status: "BULLISH",
    asian_markets_status: "POSITIVE",
    vix_trend: "FALLING",
    usdinr_trend: "STABLE",
    crude_oil_trend: "FALLING",
    is_available: true,
  },
  schema_version: "1.0",
  pipeline_version: "1.0",
};

// 6. Strategy Evaluation
const createMockStrategyScore = (
  name: "MOMENTUM" | "BREAKOUT" | "TREND_FOLLOWING" | "MEAN_REVERSION" | "RANGE" | "EXPIRY" | "SCALPING",
  score: number,
  level: "HIGH" | "MEDIUM" | "LOW" | "NONE",
  reasons: string[]
): StrategyScore => ({
  strategy_name: name,
  suitability_score: score,
  suitability_level: level,
  reasons: reasons.map((r, i) => ({ reason_type: `ALIGNMENT_${i}`, message: r })),
  warnings: [],
  constraints: [],
  required_conditions_met: ["SPOT_ABOVE_EMA", "VOL_VALID"],
  rejected_conditions_met: [],
});

export const mockStrategyEvaluation: StrategyEvaluation = {
  overall_best_strategy: "MOMENTUM",
  evaluations: [
    createMockStrategyScore("MOMENTUM", 88.5, "HIGH", [
      "RSI is trending in 55-65 zone with high positive velocity.",
      "EMA alignment is positive across both 9 and 21 periods."
    ]),
    createMockStrategyScore("BREAKOUT", 76.0, "MEDIUM", [
      "Spot is near the daily upper resistance boundary, expecting expansion.",
    ]),
    createMockStrategyScore("TREND_FOLLOWING", 85.0, "HIGH", [
      "15-minute slope indicators are highly positive.",
    ]),
    createMockStrategyScore("MEAN_REVERSION", 24.5, "NONE", [
      "Market regime is strongly trending, avoiding reversion risk."
    ]),
    createMockStrategyScore("RANGE", 30.0, "LOW", [
      "Volatility expansion is starting, indicating range expansion."
    ]),
    createMockStrategyScore("EXPIRY", 45.0, "LOW", [
      "Expiry is 5 days away, option decay is low."
    ]),
    createMockStrategyScore("SCALPING", 82.0, "HIGH", [
      "Highly liquid option spreads permit ultra-low-friction quick scalping."
    ]),
  ],
  momentum_evaluation: createMockStrategyScore("MOMENTUM", 88.5, "HIGH", []),
  breakout_evaluation: createMockStrategyScore("BREAKOUT", 76.0, "MEDIUM", []),
  trend_following_evaluation: createMockStrategyScore("TREND_FOLLOWING", 85.0, "HIGH", []),
  mean_reversion_evaluation: createMockStrategyScore("MEAN_REVERSION", 24.5, "NONE", []),
  range_evaluation: createMockStrategyScore("RANGE", 30.0, "LOW", []),
  expiry_evaluation: createMockStrategyScore("EXPIRY", 45.0, "LOW", []),
  scalping_evaluation: createMockStrategyScore("SCALPING", 82.0, "HIGH", []),
  summary: {
    top_strategies: ["MOMENTUM", "TREND_FOLLOWING", "SCALPING"],
    suitable_strategies_count: 3,
    unsuitable_strategies_count: 4,
    conclusions: [
      "Select Momentum and Trend Following as core approaches.",
      "Utilize CE option buying with ATR-bracketed stop triggers."
    ],
  },
  timestamp: nowISO(),
  schema_version: "1.0",
  pipeline_version: "1.0",
};

// 7. Trade Planner (Candidates list)
export const mockTradePlan: TradePlan = {
  trade_plan_id: "PLAN_20260710_002",
  accepted_candidates: [
    {
      candidate_id: "MOMENTUM_NIFTY2671624200CE",
      strategy_name: "MOMENTUM",
      tradingsymbol: "NIFTY2671624200CE",
      strike: 24200.0,
      instrument_type: "CE",
      expiry: "2026-07-16",
      distance_from_atm: 0.5,
      atm_distance_class: "ATM",
      oi: 3200000,
      volume: 8500000,
      spread_pct: 0.04,
      iv: 14.1,
      tradability_score: 92.5,
      suitability_score: 88.5,
      ranking_score: 90.5,
      rank: 1,
      reasons: [{ reason_type: "ATM_STRIKE", message: "Highly liquid option chain anchor." }],
      warnings: [],
      expiry_reason: "Current weekly expiry selected because:\n• Momentum Strategy\n• Expected holding period: Intraday\n• Preferred Style: Intraday\n• Validated for liquidity & narrow spread"
    },
    {
      candidate_id: "SCALPING_NIFTY2671624150CE",
      strategy_name: "SCALPING",
      tradingsymbol: "NIFTY2671624150CE",
      strike: 24150.0,
      instrument_type: "CE",
      expiry: "2026-07-16",
      distance_from_atm: -50.0,
      atm_distance_class: "ATM_MINUS_1",
      oi: 1500000,
      volume: 4200000,
      spread_pct: 0.05,
      iv: 14.3,
      tradability_score: 88.0,
      suitability_score: 82.0,
      ranking_score: 85.0,
      rank: 2,
      reasons: [{ reason_type: "ITM_SAFETY", message: "In-the-money intrinsic value cushion." }],
      warnings: [],
      expiry_reason: "Current weekly expiry selected because:\n• Scalping Strategy\n• Expected holding period: Intraday\n• Preferred Style: Intraday\n• Validated for liquidity & narrow spread"
    },
    {
      candidate_id: "TREND_FOLLOWING_NIFTY2672324250CE",
      strategy_name: "TREND_FOLLOWING",
      tradingsymbol: "NIFTY2672324250CE",
      strike: 24250.0,
      instrument_type: "CE",
      expiry: "2026-07-23",
      distance_from_atm: 50.0,
      atm_distance_class: "ATM_PLUS_1",
      oi: 2100000,
      volume: 6100000,
      spread_pct: 0.06,
      iv: 14.0,
      tradability_score: 86.5,
      suitability_score: 85.0,
      ranking_score: 85.7,
      rank: 3,
      reasons: [{ reason_type: "OTM_LEVERAGE", message: "Slightly out-of-the-money high delta potential." }],
      warnings: [],
      expiry_reason: "Next weekly expiry selected because:\n• Trend Following Strategy\n• Expected holding period: 3-7 Days\n• Preferred Style: Swing\n• Validated for liquidity & narrow spread"
    },
    {
      candidate_id: "POSITIONAL_NIFTY2673024200CE",
      strategy_name: "POSITIONAL",
      tradingsymbol: "NIFTY2673024200CE",
      strike: 24200.0,
      instrument_type: "CE",
      expiry: "2026-07-30",
      distance_from_atm: 0.0,
      atm_distance_class: "ATM",
      oi: 2500000,
      volume: 1800000,
      spread_pct: 0.08,
      iv: 15.2,
      tradability_score: 82.0,
      suitability_score: 80.0,
      ranking_score: 81.2,
      rank: 4,
      reasons: [{ reason_type: "MONTHLY_CUSHION", message: "Monthly contract has lower theta decay." }],
      warnings: [],
      expiry_reason: "Current monthly expiry selected because:\n• Positional Strategy\n• Expected holding period: 2-6 Weeks\n• Preferred Style: Positional\n• Validated for liquidity & narrow spread"
    },
    {
      candidate_id: "LONG_TERM_NIFTY26NOV24200CE",
      strategy_name: "LONG_TERM",
      tradingsymbol: "NIFTY26NOV24200CE",
      strike: 24200.0,
      instrument_type: "CE",
      expiry: "2026-11-26",
      distance_from_atm: 0.0,
      atm_distance_class: "ATM",
      oi: 800000,
      volume: 300000,
      spread_pct: 0.22,
      iv: 16.5,
      tradability_score: 70.0,
      suitability_score: 75.0,
      ranking_score: 72.5,
      rank: 5,
      reasons: [{ reason_type: "FAR_EXPIRY_HEDGE", message: "November far-expiry contract for long-term hedging." }],
      warnings: [],
      expiry_reason: "Far monthly expiry selected because:\n• Long Term Strategy\n• Expected holding period: Several Months\n• Preferred Style: Positional\n• Validated for liquidity & narrow spread"
    }
  ],
  rejected_candidates: [
    {
      strategy_name: "MEAN_REVERSION",
      tradingsymbol: "NIFTY2671624200PE",
      reason_type: "STRATEGY_ALIGNMENT",
      message: "Mean reversion is completely unsuitable in current trending market environment.",
    }
  ],
  statistics: {
    total_candidates_generated: 12,
    total_candidates_accepted: 3,
    total_candidates_rejected: 9,
    momentum_accepted_count: 1,
    breakout_accepted_count: 0,
    trend_following_accepted_count: 1,
    mean_reversion_accepted_count: 0,
    range_accepted_count: 0,
    expiry_accepted_count: 0,
    scalping_accepted_count: 1,
    average_ranking_score: 87.06,
  },
  summary: {
    best_candidate_id: "MOMENTUM_NIFTY2671624200CE",
    conclusions: [
      "Focus capital allocation entirely on MOMENTUM_NIFTY2671624200CE.",
      "Scale down on slightly OTM contract TREND_FOLLOWING_NIFTY2672324250CE."
    ],
  },
  timestamp: nowISO(),
  schema_version: "1.0",
  pipeline_version: "1.0",
};

// 8. Confidence Report
export const mockConfidenceReport: ConfidenceReport = {
  report_id: "CONF_20260710_003",
  trade_plan_id: "PLAN_20260710_002",
  confidence_scores: {
    "MOMENTUM_NIFTY2671624200CE": 88.5,
    "SCALPING_NIFTY2671624150CE": 82.0,
    "TREND_FOLLOWING_NIFTY2672324250CE": 85.0,
  },
  scoring_factors: {
    "MOMENTUM_NIFTY2671624200CE": [
      { factor: "Market Trend Concordance", score: 92.0, weight: 0.4 },
      { factor: "Option OI Buildup Cushion", score: 86.0, weight: 0.3 },
      { factor: "Bid-Ask Spread Liquid Stability", score: 95.0, weight: 0.2 },
      { factor: "VIX Compression Align", score: 75.0, weight: 0.1 },
    ]
  },
  summary_message: "Calculated high confidence scores across all 3 accepted candidates due to strict trend and liquidity alignment.",
  timestamp: nowISO(),
};

// 9. Risk Report
export const mockRiskReport: RiskReport = {
  report_id: "RISK_20260710_004",
  confidence_report_id: "CONF_20260710_003",
  approved_candidates: [
    {
      candidate_id: "MOMENTUM_NIFTY2671624200CE",
      tradingsymbol: "NIFTY2671624200CE",
      allocated_lots: 10, // 500 options qty
      allocated_capital: 77700.0, // Qty * Premium (155.40)
      risk_pnl_limit: 15540.0, // Max 20% loss limit
      stop_loss_price: 124.30, // ATR based
      target_price: 217.60, // 1:2 ratio
      leverage_ratio: 1.0,
    },
    {
      candidate_id: "SCALPING_NIFTY2671624150CE",
      tradingsymbol: "NIFTY2671624150CE",
      allocated_lots: 8, // 400 options qty
      allocated_capital: 76080.0, // Qty * Premium (190.20)
      risk_pnl_limit: 11412.0, // Scalper risk is lower
      stop_loss_price: 161.70,
      target_price: 232.05,
      leverage_ratio: 1.0,
    }
  ],
  total_capital_allocated: 153780.0,
  portfolio_utilization_pct: 15.38, // Out of 10L cash limit
  risk_grade: "MODERATE",
  active_rules_triggered: [
    "MAX_SINGLE_TRADE_CAPITAL_10PCT",
    "MAX_PORTFOLIO_UTILIZATION_30PCT"
  ],
  block_reasons: [],
  warnings: [
    "Combined capital allocation exceeds INR 1,50,000. Risk level is Moderate."
  ],
  timestamp: nowISO(),
};

// 10. Decision Report
export const mockDecisionReport: DecisionReport = {
  report_id: "DEC_20260710_005",
  risk_report_id: "RISK_20260710_004",
  candidate_decisions: [
    {
      candidate_id: "MOMENTUM_NIFTY2671624200CE",
      tradingsymbol: "NIFTY2671624200CE",
      strategy_name: "MOMENTUM",
      decision: "BUY",
      priority_score: 92.5,
      execution_priority: 1,
      explanation: "Approved for full BUY execution. Extremely strong technical momentum coupled with put-option support cushions.",
      supporting_evidence: [
        { reason_type: "TREND", message: "ADX > 25 indicates robust trend structure.", metric_name: "ADX", metric_value: 28.5 },
        { reason_type: "OPTIONS", message: "PCR > 1.15 confirms option writer support.", metric_name: "PCR", metric_value: 1.15 }
      ],
      blocking_factors: [],
      warnings: [],
      allocated_capital: 77700.0,
      allocated_lots: 10,
      expiry_reason: "Current weekly expiry selected because:\n• Momentum Strategy\n• Expected holding period: Intraday\n• Preferred Style: Intraday\n• Validated for liquidity & narrow spread"
    },
    {
      candidate_id: "SCALPING_NIFTY2671624150CE",
      tradingsymbol: "NIFTY2671624150CE",
      strategy_name: "SCALPING",
      decision: "BUY",
      priority_score: 87.0,
      execution_priority: 2,
      explanation: "Approved for scalping buy. Spreads are highly liquid enabling quick entry/exit cycles with low slippage.",
      supporting_evidence: [
        { reason_type: "LIQUIDITY", message: "Average bid-ask spread is less than 0.05 paise.", metric_name: "Spread %", metric_value: 0.04 }
      ],
      blocking_factors: [],
      warnings: [],
      allocated_capital: 76080.0,
      allocated_lots: 8,
      expiry_reason: "Current weekly expiry selected because:\n• Scalping Strategy\n• Expected holding period: Intraday\n• Preferred Style: Intraday\n• Validated for liquidity & narrow spread"
    },
    {
      candidate_id: "TREND_FOLLOWING_NIFTY2672324250CE",
      tradingsymbol: "NIFTY2672324250CE",
      strategy_name: "TREND_FOLLOWING",
      decision: "WATCH",
      priority_score: 75.0,
      execution_priority: 3,
      explanation: "Placed on WATCH. While trend is strong, capital limits prevent third concurrent entry to shield overall exposure.",
      supporting_evidence: [],
      blocking_factors: [
        { reason_type: "RISK_EXPOSURE", message: "Exceeds multi-contract exposure margin guidelines.", metric_name: "Max Slots", metric_value: 2.0 }
      ],
      warnings: [
        { warning_type: "CAPITAL_OVERFLOW", message: "Exceeded single run slot counts.", severity: "LOW" }
      ],
      allocated_capital: 0.0,
      allocated_lots: 0,
      expiry_reason: "Next weekly expiry selected because:\n• Trend Following Strategy\n• Expected holding period: 3-7 Days\n• Preferred Style: Swing\n• Validated for liquidity & narrow spread"
    },
    {
      candidate_id: "POSITIONAL_NIFTY2673024200CE",
      tradingsymbol: "NIFTY2673024200CE",
      strategy_name: "POSITIONAL",
      decision: "BUY",
      priority_score: 81.2,
      execution_priority: 4,
      explanation: "Approved for positional buy. Lower theta decay risk on monthly contract allows Swing to mature with safety margin.",
      supporting_evidence: [],
      blocking_factors: [],
      warnings: [],
      allocated_capital: 80000.0,
      allocated_lots: 10,
      expiry_reason: "Current monthly expiry selected because:\n• Positional Strategy\n• Expected holding period: 2-6 Weeks\n• Preferred Style: Positional\n• Validated for liquidity & narrow spread"
    },
    {
      candidate_id: "LONG_TERM_NIFTY26NOV24200CE",
      tradingsymbol: "NIFTY26NOV24200CE",
      strategy_name: "LONG_TERM",
      decision: "WATCH",
      priority_score: 72.5,
      execution_priority: 5,
      explanation: "Placed on WATCH. November far-expiry contract suitable for positional hedge, waiting for volatility trigger.",
      supporting_evidence: [],
      blocking_factors: [],
      warnings: [],
      allocated_capital: 0.0,
      allocated_lots: 0,
      expiry_reason: "Far monthly expiry selected because:\n• Long Term Strategy\n• Expected holding period: Several Months\n• Preferred Style: Positional\n• Validated for liquidity & narrow spread"
    }
  ],
  priority_ranking: [
    "MOMENTUM_NIFTY2671624200CE",
    "SCALPING_NIFTY2671624150CE",
    "TREND_FOLLOWING_NIFTY2672324250CE",
    "POSITIONAL_NIFTY2673024200CE"
  ],
  summary: {
    overall_action: "EXECUTE",
    highest_priority_candidate_id: "MOMENTUM_NIFTY2671624200CE",
    portfolio_status_message: "Margin reserved, awaiting operator manual confirmation.",
    conclusions: [
      "Manually route 10 lots of NIFTY2671624200CE at current market price ~155.40.",
      "Manually route 8 lots of NIFTY2671624150CE at current market price ~190.20."
    ],
  },
  stats: {
    total_candidates_evaluated: 3,
    buy_count: 2,
    sell_count: 0,
    watch_count: 1,
    reject_count: 0,
    no_trade_count: 0,
    total_allocated_capital: 153780.0,
  },
  timestamp: nowISO(),
  schema_version: "1.0",
  engine_version: "1.0",
};

// 11. Broker Account & Funds
export const mockBrokerAccount: BrokerAccount = {
  client_id: "ZT1234",
  name: "Operator Chief",
  email: "operator@niftyworkstation.in",
  broker: "Zerodha Kite Connect",
};

export const mockBrokerFunds: BrokerFunds = {
  available_cash: 846220.0, // after reserving 153780
  margins: 1000000.0, // 10L capital
  utilized_margin: 153780.0,
  available_margin: 846220.0,
};

// Active positions in manual / live tracking ledger
export const mockBrokerPositions: BrokerPosition[] = [
  {
    tradingsymbol: "NIFTY2671624200CE",
    exchange: "NFO",
    product: "NRML",
    quantity: 500, // 10 lots
    average_price: 155.40,
    last_price: 162.10, // 24200.5 spot price movement
    pnl: 3350.00, // (162.1 - 155.4) * 500
    today_mtm: 3350.00,
  },
  {
    tradingsymbol: "NIFTY2671624150CE",
    exchange: "NFO",
    product: "NRML",
    quantity: 400, // 8 lots
    average_price: 190.20,
    last_price: 194.85,
    pnl: 1860.00,
    today_mtm: 1860.00,
  }
];

export const mockBrokerHoldings: BrokerHolding[] = [
  {
    tradingsymbol: "LIQUIDBEES",
    exchange: "NSE",
    product: "CNC",
    quantity: 50,
    average_price: 1000.0,
    last_price: 1000.0,
    pnl: 0.0,
  }
];

export const mockBrokerOrders: BrokerOrder[] = [
  {
    order_id: "260710000213",
    exchange_order_id: "130000000412",
    tradingsymbol: "NIFTY2671624200CE",
    exchange: "NFO",
    transaction_type: "BUY",
    quantity: 500,
    product: "NRML",
    order_type: "MARKET",
    status: "COMPLETE",
    price: 155.40,
    filled_quantity: 500,
    order_timestamp: nowISO(),
    status_message: "ORDER EXECUTED SUCCESS",
  },
  {
    order_id: "260710000214",
    exchange_order_id: "130000000413",
    tradingsymbol: "NIFTY2671624150CE",
    exchange: "NFO",
    transaction_type: "BUY",
    quantity: 400,
    product: "NRML",
    order_type: "MARKET",
    status: "COMPLETE",
    price: 190.20,
    filled_quantity: 400,
    order_timestamp: nowISO(),
    status_message: "ORDER EXECUTED SUCCESS",
  }
];

// 12. Execution Report
export const mockExecutionReport: ExecutionReport = {
  report_id: "EXE_20260710_006",
  request_id: "REQ_20260710_001",
  submitted_orders: [
    {
      candidate_id: "MOMENTUM_NIFTY2671624200CE",
      tradingsymbol: "NIFTY2671624200CE",
      exchange: "NFO",
      transaction_type: "BUY",
      quantity: 500,
      product: "NRML",
      order_type: "MARKET",
      price: 155.40,
      trigger_price: 0.0,
    }
  ],
  accepted_orders: [
    {
      candidate_id: "MOMENTUM_NIFTY2671624200CE",
      tradingsymbol: "NIFTY2671624200CE",
      exchange: "NFO",
      transaction_type: "BUY",
      quantity: 500,
      product: "NRML",
      order_type: "MARKET",
      price: 155.40,
      trigger_price: 0.0,
    }
  ],
  rejected_orders: [],
  exchange_order_id: "130000000412",
  broker_order_id: "260710000213",
  timestamp: nowISO(),
  failure_reason: "",
  status: "COMPLETED",
};

// 13. Paper Trading Positions & Portfolio Snapshot
export const mockPaperPositions: PaperPosition[] = [
  {
    position_id: "P_POS_001",
    trade: {
      trade_id: "T_001",
      decision_id: "DEC_20260710_005",
      candidate_id: "MOMENTUM_NIFTY2671624200CE",
      tradingsymbol: "NIFTY2671624200CE",
      entry_time: nowISO(),
      premium: 155.40,
      lots: 10,
      capital: 77700.0,
      strategy_name: "MOMENTUM",
      confidence_score: 88.5,
      risk_grade: "MODERATE",
      action: "BUY",
    },
    current_mtm: 3350.00,
    peak_mtm: 4500.00,
    drawdown: 0.0,
    holding_time_seconds: 1420.0,
    status: "OPEN",
    current_premium: 162.10,
  }
];

export const mockPortfolioSnapshot: PortfolioSnapshot = {
  timestamp: nowISO(),
  total_capital: 1000000.0,
  allocated_capital: 77700.0,
  available_capital: 922300.0,
  open_positions_count: 1,
  closed_trades_count: 148,
  total_pnl: 184500.0, // Overall historic paper trading profit
  realized_pnl: 181150.0,
  unrealized_pnl: 3350.0,
};

// Double-entry simulated ledger histories
export const mockTradeJournal: TradeJournalEntry[] = [
  {
    entry_id: "J_ENTRY_001",
    trade_id: "T_HIST_147",
    candidate_id: "SCALPING_NIFTY2671624100CE",
    tradingsymbol: "NIFTY2671624100CE",
    decision_summary: "Approved scalping buy under low volatility compress.",
    explanation_summary: "Executed due to strict 15m support confirmation.",
    market_score_val: 81.2,
    market_score_grade: "B",
    confidence_score: 84.0,
    risk_grade: "CONSERVATIVE",
    strategy_name: "SCALPING",
    entry_time: "2026-07-09T10:15:00Z",
    entry_premium: 135.20,
    entry_capital: 67600.0,
    entry_lots: 10,
    exit_time: "2026-07-09T10:42:00Z",
    exit_premium: 152.40,
    exit_reason: "TARGET_REACHED",
    pnl: 8600.0,
    pnl_pct: 12.72,
    duration_seconds: 1620,
    outcome: "WIN",
    market_regime: "SIDEWAYS",
    confidence_band: "HIGH",
    notes: "Perfect clean target tag on VWAP boundary bounce.",
  },
  {
    entry_id: "J_ENTRY_002",
    trade_id: "T_HIST_146",
    candidate_id: "MOMENTUM_NIFTY2672324250CE",
    tradingsymbol: "NIFTY2672324250CE",
    decision_summary: "Approved buy on momentum flag breakout.",
    explanation_summary: "Quick stop out under sudden price dip.",
    market_score_val: 78.5,
    market_score_grade: "B-",
    confidence_score: 79.5,
    risk_grade: "MODERATE",
    strategy_name: "MOMENTUM",
    entry_time: "2026-07-08T14:00:00Z",
    entry_premium: 112.50,
    entry_capital: 56250.0,
    entry_lots: 10,
    exit_time: "2026-07-08T14:15:00Z",
    exit_premium: 95.00,
    exit_reason: "STOP_LOSS_TRIGGER",
    pnl: -8750.0,
    pnl_pct: -15.55,
    duration_seconds: 900,
    outcome: "LOSS",
    market_regime: "VOLATILE",
    confidence_band: "MEDIUM",
    notes: "Sudden index reversal after European session close panic.",
  }
];

// 14. Performance Analytics Report
export const mockAnalyticsReport: AnalyticsReport = {
  report_id: "ANL_20260710_007",
  overall_metrics: {
    total_trades: 148,
    winning_trades: 96,
    losing_trades: 52,
    win_rate: 64.86,
    average_profit: 4250.0,
    average_loss: -2580.0,
    profit_factor: 3.04,
    expectancy: 1850.50,
    average_holding_time: 1420.0,
    largest_winner: 24500.0,
    largest_loser: -12600.0,
    maximum_drawdown: 35000.0,
    recovery_factor: 5.27,
  },
  strategy_metrics: [
    { strategy_name: "MOMENTUM", total_trades: 45, win_rate: 68.2, average_return: 2250.0, profit_factor: 2.85, expectancy: 1450.0, capital_utilization: 65000.0 },
    { strategy_name: "SCALPING", total_trades: 62, win_rate: 72.5, average_return: 1850.0, profit_factor: 3.42, expectancy: 1100.0, capital_utilization: 50000.0 },
    { strategy_name: "TREND_FOLLOWING", total_trades: 31, win_rate: 58.0, average_return: 3500.0, profit_factor: 2.15, expectancy: 1950.0, capital_utilization: 75000.0 },
    { strategy_name: "MEAN_REVERSION", total_trades: 10, win_rate: 40.0, average_return: -800.0, profit_factor: 0.85, expectancy: -320.0, capital_utilization: 45000.0 }
  ],
  market_metrics: {
    by_regime: [
      { market_regime: "TRENDING", total_trades: 85, win_rate: 74.1, average_return: 2850.0, profit_factor: 3.10, expectancy: 1850.0 },
      { market_regime: "SIDEWAYS", total_trades: 38, win_rate: 55.2, average_return: 850.0, profit_factor: 1.65, expectancy: 450.0 },
      { market_regime: "VOLATILE", total_trades: 25, win_rate: 48.0, average_return: -250.0, profit_factor: 0.92, expectancy: -110.0 }
    ],
    by_opportunity: [
      { opportunity_classification: "EXCELLENT", total_trades: 60, win_rate: 80.0, average_return: 3400.0, profit_factor: 4.20, expectancy: 2500.0 },
      { opportunity_classification: "GOOD", total_trades: 55, win_rate: 61.8, average_return: 1550.0, profit_factor: 2.10, expectancy: 950.0 },
      { opportunity_classification: "WATCHLIST", total_trades: 33, win_rate: 42.4, average_return: -180.0, profit_factor: 0.88, expectancy: -100.0 }
    ],
    by_grade: [
      { market_score_grade: "A", total_trades: 42, win_rate: 83.3, average_return: 4100.0, profit_factor: 4.80, expectancy: 3200.0 },
      { market_score_grade: "B", total_trades: 68, win_rate: 64.7, average_return: 1850.0, profit_factor: 2.30, expectancy: 1100.0 },
      { market_score_grade: "C", total_trades: 38, win_rate: 47.3, average_return: -450.0, profit_factor: 0.90, expectancy: -180.0 }
    ],
    by_bias: [
      { directional_bias: "BULLISH", total_trades: 85, win_rate: 69.4, average_return: 2150.0, profit_factor: 2.90, expectancy: 1350.0 },
      { directional_bias: "BEARISH", total_trades: 45, win_rate: 62.2, average_return: 1650.0, profit_factor: 2.40, expectancy: 980.0 },
      { directional_bias: "SIDEWAYS", total_trades: 18, win_rate: 44.4, average_return: -520.0, profit_factor: 0.78, expectancy: -250.0 }
    ]
  },
  confidence_metrics: [
    { confidence_band: "HIGH (>=80)", total_trades: 52, win_rate: 84.6, average_return: 3850.0 },
    { confidence_band: "MEDIUM (50-79)", total_trades: 74, win_rate: 59.4, average_return: 1250.0 },
    { confidence_band: "LOW (<50)", total_trades: 22, win_rate: 36.3, average_return: -920.0 }
  ],
  risk_metrics: [
    { risk_grade: "CONSERVATIVE", total_trades: 60, win_rate: 70.0, average_return: 1450.0, capital_allocation_avg: 45000.0, portfolio_utilization: 9.0 },
    { risk_grade: "MODERATE", total_trades: 72, win_rate: 63.8, average_return: 2450.0, capital_allocation_avg: 82000.0, portfolio_utilization: 16.4 },
    { risk_grade: "AGGRESSIVE", total_trades: 16, win_rate: 50.0, average_return: 1800.0, capital_allocation_avg: 165000.0, portfolio_utilization: 33.0 }
  ],
  time_metrics: {
    by_entry_hour: { 9: 12450.0, 10: 45200.0, 11: 32150.0, 12: -8500.0, 13: 15400.0, 14: 68400.0, 15: 18900.0 },
    by_day_of_week: { "Monday": 38400.0, "Tuesday": 45100.0, "Wednesday": 12600.0, "Thursday": 72400.0, "Friday": 16000.0 },
    avg_holding_time: 1420.0,
  },
  portfolio_metrics: {
    initial_capital: 1000000.0,
    final_capital: 1184500.0,
    total_pnl: 184500.0,
    return_on_capital: 18.45,
    maximum_drawdown: 3.5, // 3.5%
    sharpe_ratio: 2.45,
    profit_factor: 3.04,
  },
  summary: {
    strengths: [
      "Excellent win rate (72.5%) in Scalping under SIDEWAYS index conditions.",
      "Very high profit factor (4.20) on EXCELLENT opportunity categories."
    ],
    weaknesses: [
      "Negative expectancy in VOLATILE regimes due to rapid bid-ask slippages.",
      "Intraday lunch hours (12:00 to 13:00) showed recurring negative returns."
    ],
    recommendations: [
      "Automatically pause trade entries during intraday period 12:00 - 13:00.",
      "Favor ATM contracts over OTM to secure high delta sensitivity during breakouts."
    ]
  },
  timestamp: nowISO(),
};

// 15. Historical Validation Report
export const mockValidationReport: ValidationReport = {
  report_id: "VAL_20260710_008",
  daily_validations: [
    {
      date: "2026-07-09",
      market_score: 81.2,
      candidates_count: 14,
      buy_count: 3,
      sell_count: 0,
      watch_count: 2,
      reject_count: 1,
      no_trade_count: 8,
      total_allocated_capital: 215000.0,
      decision_report_id: "DEC_20260709_001",
      outcome_summary: "SUCCESS. Spot moved 0.75% higher matching our trend continuation plan."
    },
    {
      date: "2026-07-08",
      market_score: 68.4,
      candidates_count: 12,
      buy_count: 2,
      sell_count: 0,
      watch_count: 4,
      reject_count: 0,
      no_trade_count: 6,
      total_allocated_capital: 110000.0,
      decision_report_id: "DEC_20260708_001",
      outcome_summary: "PARTIAL FAIL. One scalp completed target, one momentum caught stop loss reversal."
    },
    {
      date: "2026-07-07",
      market_score: 84.8,
      candidates_count: 15,
      buy_count: 4,
      sell_count: 0,
      watch_count: 1,
      reject_count: 2,
      no_trade_count: 8,
      total_allocated_capital: 295000.0,
      decision_report_id: "DEC_20260707_001",
      outcome_summary: "EXCELLENT. Index rallied 1.2% tagging all CE targets under zero drawdown."
    }
  ],
  strategy_performances: [
    { strategy_name: "MOMENTUM", total_candidates: 45, buy_count: 18, sell_count: 0, watch_count: 12, reject_count: 5, no_trade_count: 10, avg_confidence_score: 74.2 },
    { strategy_name: "SCALPING", total_candidates: 62, buy_count: 35, sell_count: 0, watch_count: 15, reject_count: 2, no_trade_count: 10, avg_confidence_score: 82.5 }
  ],
  decision_performances: [
    { decision_type: "BUY", count: 53, percentage: 35.8, avg_confidence: 81.4, avg_allocated_capital: 82500.0 },
    { decision_type: "WATCH", count: 35, percentage: 23.6, avg_confidence: 62.5, avg_allocated_capital: 0.0 }
  ],
  confidence_stats: {
    avg_confidence: 72.8,
    max_confidence: 94.5,
    min_confidence: 41.2,
    std_confidence: 12.4
  },
  risk_stats: {
    avg_allocated_capital: 82500.0,
    total_allocated_capital: 4372500.0,
    max_allocated_capital: 185000.0,
    approved_count: 53,
    rejected_count: 8
  },
  outcome_validations: [
    { evaluation_window: "Same-day", success_count: 68, failure_count: 28, accuracy_pct: 70.83, total_profit_loss: 145000.0 },
    { evaluation_window: "Next-day", success_count: 12, failure_count: 18, accuracy_pct: 40.00, total_profit_loss: -12500.0 },
    { evaluation_window: "Expiry-day", success_count: 16, failure_count: 6, accuracy_pct: 72.72, total_profit_loss: 52000.0 }
  ],
  summary_stats: {
    total_days_evaluated: 30,
    total_candidates_evaluated: 395,
    overall_buy_count: 53,
    overall_sell_count: 0,
    overall_watch_count: 75,
    overall_reject_count: 42,
    overall_no_trade_count: 225,
    decision_frequency_pct: 13.4,
    avg_market_score: 75.4
  },
  timestamp: nowISO(),
  schema_version: "1.0",
  engine_version: "1.0",
};

// 16. Optimization Report
export const mockOptimizationReport: OptimizationReport = {
  report_id: "OPT_20260710_009",
  validation_report_id: "VAL_20260710_008",
  summary: {
    total_recommendations: 4,
    critical_adjustments: 2,
    potential_pnl_improvement: 22400.0,
    recommendation_confidence_avg: 88.5,
  },
  recommendations: [
    {
      recommendation_id: "OPT_REC_01",
      category: "CONFIDENCE_THRESHOLD",
      title: "Raise Momentum Execution Barrier",
      description: "Raising the buy execution barrier for momentum trades from 70.0 to 75.0 filters out noisy false breakout candidates.",
      current_value: "70.0",
      recommended_value: "75.0",
      evidence: {
        historical_sample_size: 45,
        observed_improvement_potential: 14200.0,
        affected_strategies: ["MOMENTUM"],
        expected_trade_off: "Will skip approximately 12.5% of trade entries but raises strategy win-rate by 7.4%.",
        confidence_score: 92.0
      },
      rationale: "Backtests indicate that momentum signals generated in the 70.0-74.9 confidence band suffer high regression due to volume exhaustion near visual resistance zones."
    }
  ],
  strategy_optimizations: [
    { strategy_name: "MEAN_REVERSION", current_accuracy: 40.0, recommended_action: "SUSPEND", rationale: "Current macro indices remain strictly trending, generating persistent losses on counter-trend revert models." }
  ],
  threshold_recommendations: [
    { parameter_name: "buy_confidence_threshold", current_value: 70.0, suggested_value: 75.0, direction: "INCREASE", impact: "High" }
  ],
  weight_recommendations: [
    { strategy_or_factor: "Trend Force weight", current_weight: 0.40, suggested_weight: 0.45, rationale: "Trend slope is a stronger physical buffer than session type scoring under index expansions." }
  ],
  timestamp: nowISO(),
  engine_version: "1.0",
};

// 17. Evening Planner Report
export const mockEveningReport: EveningReport = {
  report_id: "EVE_20260710_010",
  market_summary: {
    spot_price: 24200.50,
    vix_price: 13.85,
    regime: "TRENDING",
    trend_direction: "BULLISH",
    market_score: 84.2,
    market_grade: "B+",
    session_type: "NORMAL_HOURS",
  },
  tomorrow_outlook: {
    directional_bias: "BULLISH",
    outlook_classification: "EXCELLENT",
    opportunity_strength: 86.6,
    key_support_levels: [24100.0, 24000.0],
    key_resistance_levels: [24300.0, 24400.0],
    description: "Highly aligned indicators suggest positive follow-through during tomorrow morning session. Put writing is heavily stacked at 24200 strike."
  },
  recommended_strategies: [
    { strategy_name: "MOMENTUM", suitability_score: 88.5, suitability_level: "HIGH", rationale: ["Spot price closing above 50-period EMA.", "ADX showing steady trend compression release."] }
  ],
  top_candidates: [
    {
      candidate_id: "MOMENTUM_NIFTY2671624200CE",
      tradingsymbol: "NIFTY2671624200CE",
      strategy_name: "MOMENTUM",
      decision: "BUY",
      confidence_score: 88.5,
      priority_score: 92.5,
      allocated_capital: 77700.0,
      allocated_lots: 10,
      strike: 24200.0,
      instrument_type: "CE",
      expiry: "2026-07-16",
    }
  ],
  rejected_candidates: [
    { tradingsymbol: "NIFTY2671624200PE", strategy_name: "MEAN_REVERSION", reason_type: "TREND_ALIGNMENT", message: "Strong bullish slope blocks counter-trend put buying." }
  ],
  risk_watchlist: {
    warnings: ["Index approaching multi-week visual resistance pivot line at 24,300."],
    portfolio_warnings: [],
    max_capital_limit: 1000000.0,
    allocated_capital: 77700.0,
    portfolio_utilization_pct: 7.77,
    risk_grade: "CONSERVATIVE",
  },
  event_watchlist: {
    events: ["RBI minutes publication scheduled tomorrow at 14:00."],
    expiry_days_remaining: 5.0,
    expiry_type: "NORMAL",
  },
  checklist: {
    checklist_items: [
      "Verify Gift Nifty pre-market opening direction tomorrow at 08:30.",
      "Check option chain PCR update at 09:30 following initial weekly lot stack.",
      "Ensure broker Kite Connect session authentication is renewed by 09:00."
    ]
  },
  summary: {
    best_candidate_id: "MOMENTUM_NIFTY2671624200CE",
    best_strategy: "MOMENTUM",
    total_accepted_candidates: 1,
    total_rejected_candidates: 1,
    action_type: "EXECUTE",
  },
  timestamp: nowISO(),
  engine_version: "1.0",
  optimization_notes: ["ATR is stable at 125, visual stop losses should remain tightly configured."],
};

// 18. Intraday Assistant Report
export const mockIntradayReport: IntradayReport = {
  report_id: "INT_20260710_011",
  evening_report_id: "EVE_20260710_010",
  summary: {
    plan_status: "Plan Still Valid",
    action_recommendation: "PROCEED",
    total_candidates_monitored: 3,
    invalidated_candidates_count: 0,
    significant_market_changes_count: 1,
    overall_pcr_shift: 0.05,
    overall_vix_shift: -0.12,
  },
  market_changes: [
    { metric_name: "Spot Index Price", previous_value: 24180.0, current_value: 24200.5, change_pct: 0.08, is_significant: false, message: "Spot moved up slightly, consolidates above plan entry." },
    { metric_name: "Option PCR (24200)", previous_value: 1.10, current_value: 1.15, change_pct: 4.54, is_significant: true, message: "Put writing OI grew significantly, strengthening visual support." }
  ],
  candidate_changes: [
    { candidate_id: "MOMENTUM_NIFTY2671624200CE", tradingsymbol: "NIFTY2671624200CE", status: "UNCHANGED", explanation: "Confidence remains extremely high matching morning checklist bounds.", previous_decision: "BUY", suggested_decision: "BUY" }
  ],
  confidence_changes: [
    { candidate_id: "MOMENTUM_NIFTY2671624200CE", previous_confidence: 88.0, current_confidence: 88.5, change_amt: 0.5, status: "UNCHANGED", explanation: "Slight PCR increase bolsters contract strength." }
  ],
  risk_changes: [
    { candidate_id: "MOMENTUM_NIFTY2671624200CE", previous_risk_grade: "MODERATE", current_risk_grade: "MODERATE", is_risk_increased: false, triggered_new_warnings: [] }
  ],
  validation_reasons: [
    "Spot price remained safely within our daily planned bounds (24100 - 24300).",
    "No black-swan global index news occurred overnight."
  ],
  timestamp: nowISO(),
  engine_version: "1.0",
};

// 19. Operations Report
export const mockOperationsReport: OperationsReport = {
  report_id: "OP_20260710_012",
  timestamp: nowISO(),
  summary: {
    timestamp: nowISO(),
    overall_status: "READY",
    readiness_score: 98.4,
    uptime_str: "03 Hours 26 Minutes",
  },
  readiness: {
    status: "READY",
    readiness_score: 98.4,
    critical_blockers_count: 0,
    warnings_count: 1,
  },
  services: [
    { service_name: "Market Tick Feed Engine", status: "ONLINE", latency_ms: 12.4, message: "Feeds active, updating in sub-50ms cycles.", last_checked: nowISO() },
    { service_name: "Option Chain Parser Service", status: "ONLINE", latency_ms: 24.8, message: "Parsing 42 active weekly contracts successfully.", last_checked: nowISO() },
    { service_name: "Google Gemini Explanation API", status: "ONLINE", latency_ms: 320.0, message: "API connected, explanations generating correctly.", last_checked: nowISO() },
    { service_name: "Zerodha Kite Session Stream", status: "ONLINE", latency_ms: 45.1, message: "Session token valid, streaming quotes active.", last_checked: nowISO() }
  ],
  startup: {
    config_valid: true,
    env_vars_valid: true,
    working_dirs_valid: true,
    required_folders_exist: true,
    cache_folders_exist: true,
    instrument_db_valid: true,
    checks: { "ENV_API_KEY": true, "CACHE_DIR": true, "SQLITE_INST": true },
  },
  dependencies: {
    python_packages_valid: true,
    node_modules_valid: true,
    config_files_valid: true,
    details: { "python_version": "3.11.2", "vite_version": "6.2.3" },
  },
  metrics: {
    uptime_seconds: 12372.0,
    log_size_bytes: 142500,
    cache_size_bytes: 2420000,
    python_version: "Python 3.11.2",
    platform_info: "Linux Cloud Run container",
    resources: {
      cpu_percent: 4.2,
      memory_used_mb: 142.5,
      memory_percent: 18.5,
      disk_free_gb: 42.1,
      disk_percent: 12.5,
    }
  },
  warnings: [
    { warning_id: "W_LOG_GROWTH", source: "SystemMonitor", severity: "LOW", message: "Operations log has exceeded 100KB. Automatic rotation scheduled at midnight.", timestamp: nowISO() }
  ],
};

// 20. Configuration Report
export const mockConfigurationReport: ConfigurationReport = {
  report_id: "CFG_20260710_013",
  timestamp: nowISO(),
  summary: {
    timestamp: nowISO(),
    active_profile_name: "PAPER_TRADING",
    schema_version: "1.0",
    status: "VALID",
  },
  preferences: {
    refresh_interval_seconds: 10,
    cli_theme: "DARK",
    react_theme: "DARK",
    visible_panels: ["SUMMARY", "MARKET", "NEWS", "SCORE", "OPPORTUNITY", "STRATEGY", "PLANNER", "CONFIDENCE", "RISK", "DECISION", "EXECUTION", "OPERATIONS", "CONFIGURATION"],
    default_screen: "SUMMARY",
    logging_level: "INFO",
    report_export_format: "JSON",
  },
  active_profile: {
    profile_id: "P_PAPER_TRADING",
    name: "PAPER_TRADING",
    description: "Configured for zero-risk paper trade simulation with complete slip limits and fee accounting.",
    settings: {
      "initial_sim_capital": 1000000.00,
      "max_drawdown_limit_pct": 10.0,
      "lot_size_multiplier": 50,
      "default_lots_per_trade": 10,
      "broker_slippage_coef": 0.0005,
    }
  },
  items: [
    { key: "initial_sim_capital", value: 1000000.00, category: "PAPER_TRADING", description: "Virtual ledger balance assigned to paper engine.", is_valid: true },
    { key: "max_drawdown_limit_pct", value: 10.0, category: "RISK", description: "Portfolio stop loss that pauses all operations.", is_valid: true },
    { key: "buy_confidence_threshold", value: 70.0, category: "SCORING", description: "Minimum rating required to trigger BUY actions.", is_valid: true }
  ],
  warnings: [],
  migration: {
    source_version: "0.9-beta",
    target_version: "1.0.0",
    requires_migration: false,
    recommendations: ["Ensure legacy key margin_buffer_ratio is completely removed from templates."]
  },
  statistics: {
    total_keys: 48,
    valid_keys: 48,
    invalid_keys: 0,
    warnings_count: 0,
  }
};

// 21. AI Explanation Report
export const mockExplanationReport: ExplanationReport = {
  report_id: "EXP_20260710_014",
  timestamp: nowISO(),
  summary: {
    title: "NIFTY Workstation Market Intelligence Analysis",
    brief_overview: "NIFTY Index Spot has consolidated cleanly above support level 24,100 with active weekly put-option volume accumulation indicating solid momentum support.",
    key_findings: [
      "Technical slope regression is bullish on the 15-minute timeframe.",
      "The Put-Call-Ratio (1.15) confirms option writers are cushion defending spot 24,200.",
      "News macros are highly positive, following RBI rate hold updates."
    ],
  },
  decision: {
    overall_action: "EXECUTE",
    highest_priority_candidate_id: "MOMENTUM_NIFTY2671624200CE",
    portfolio_status_message: "Capital is preserved, ready to manually route recommended CE trades.",
    overall_decision_reasoning: "We recommend buying ATM call contracts. Market score grade B+ confirms visual technical breakouts, while risk filters approve lot sizes matching strict capital drawdown parameters.",
    candidate_explanations: [
      {
        candidate_id: "MOMENTUM_NIFTY2671624200CE",
        tradingsymbol: "NIFTY2671624200CE",
        strategy_name: "MOMENTUM",
        decision: "BUY",
        decision_reasoning: "Index spot is trading above short-term EMAs while options PCR has broken above 1.10. Both engines reflect mutual bullish confluences.",
        lots_reasoning: "Assigned 10 lots (500 qty) limiting capital exposure strictly within 10% of total simulation balance.",
        confidence_reasoning: "High confidence rating (88.5%) driven by extreme liquidity spreads and trend convergence.",
        risk_reasoning: "Configured visual stop-loss trigger at 124.30 (ATR-based margin of 31 points), protecting trade capital from noise whipsaws."
      }
    ]
  },
  risk: {
    portfolio_risk_grade: "MODERATE",
    total_capital_allocated: 153780.0,
    portfolio_utilization_pct: 15.38,
    portfolio_risk_reasoning: "Your risk exposure is Moderate. Total utilized capital stands at INR 1,53,780. Drawdowns are physically limited by absolute trailing stop-loss coordinates on open contracts.",
    warnings_explanations: [
      "Avoid entering third contracts concurrently to protect capital from sudden news shocks."
    ]
  },
  confidence: {
    highest_confidence_candidate_id: "MOMENTUM_NIFTY2671624200CE",
    confidence_reasoning: "MOMENTUM_NIFTY2671624200CE ranks highest due to its ATM delta position. Bid-ask spreads are ultra-low, confirming seamless exit execution potential."
  },
  strategy: {
    overall_best_strategy: "MOMENTUM",
    strategy_reasoning: "Trend intensity classifications highlight high momentum strength. Sideways mean-reversion strategies are bypassed completely.",
    all_strategy_scores: ["MOMENTUM: 88.5", "SCALPING: 82.0", "TREND_FOLLOWING: 85.0", "MEAN_REVERSION: 24.5"]
  },
  intraday: {
    plan_status: "Plan Still Valid",
    action_recommendation: "PROCEED",
    explanation: "Live spot movements correlate 100% with pre-market planning guides. RBI announcements didn't cause high-vix anomalies, keeping trades safe.",
    market_change_reasons: ["Option PCR increased from 1.10 to 1.15 reflecting put stack support."],
    candidate_change_reasons: ["No negative deviations reported in candidate open interest curves."]
  },
  planner: {
    directional_bias: "BULLISH",
    outlook_classification: "EXCELLENT",
    explanation: "Spot support is firmly anchored around 24,100 while tomorrow's target ranges reside at 24,300 visual resistance."
  },
  schema_version: "1.0",
  engine_version: "1.0",
};
