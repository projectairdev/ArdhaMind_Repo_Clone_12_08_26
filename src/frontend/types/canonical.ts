/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Canonical Frontend Data Models & TypeScript Contracts.
 * Exactly matches backend Canonical State, Analytics, Prediction, Decision, and Product exports.
 */

export type DataQualityStatus =
  | "VALID"
  | "DELAYED"
  | "STALE"
  | "RECOVERING"
  | "UNAVAILABLE"
  | "SESSION_MISMATCH"
  | "BACKFILLED"
  | "COMPLETED";

export type MarketPhase =
  | "PRE_MARKET"
  | "PRE_OPEN"
  | "OPENING_RANGE"
  | "MARKET_OPEN"
  | "NEAR_CLOSE"
  | "POST_MARKET"
  | "MARKET_CLOSED";

export type DecisionState =
  | "BLOCKED"
  | "NO_TRADE"
  | "WATCH"
  | "WAIT"
  | "READY_FOR_HUMAN_REVIEW"
  | "INVALIDATED";

export type OpportunitySetup =
  | "OPENING_RANGE_BREAKOUT"
  | "BREAKDOWN"
  | "RETEST"
  | "TREND_CONTINUATION"
  | "NO_SETUP";

export type StrategySuitability =
  | "LONG_CALL"
  | "LONG_PUT"
  | "BULL_CALL_SPREAD"
  | "BEAR_PUT_SPREAD"
  | "DEFINED_RISK_ONLY"
  | "NO_TRADE"
  | "UNAVAILABLE";

export type RiskLevel =
  | "LOW"
  | "NORMAL"
  | "ELEVATED"
  | "EXTREME"
  | "CIRCUIT_RISK";

export type ConfidenceBand = "LOW" | "MEDIUM" | "HIGH";

export type DirectionBias = "BULLISH" | "BEARISH" | "NEUTRAL" | "UNCERTAIN";

export type MarketRegimeType =
  | "TREND_UP"
  | "TREND_DOWN"
  | "RANGE_BOUND"
  | "COMPRESSION"
  | "HIGH_VOLATILITY"
  | "TRANSITIONAL"
  | "EXPANSION";

export type OptionsSentiment =
  | "BULLISH_CONFIRMATION"
  | "BEARISH_CONFIRMATION"
  | "NEUTRAL_EXPIRY"
  | "CALL_SQUEEZE"
  | "PUT_SQUEEZE"
  | "MIXED";

export interface CanonicalSessionContext {
  calendar_date: string;
  market_phase: MarketPhase;
  is_trading_day: boolean;
  active_trading_date: string | null;
  completed_session_date: string;
  previous_session_date: string;
  next_trading_date: string;
  phase_label?: string;
}

export interface CanonicalInstrumentState {
  canonical_instrument_id: string;
  symbol: string;
  session_date: string;
  last_price: number | null;
  exchange_timestamp: string | null;
  received_at: string | null;
  open: number | null;
  high: number | null;
  low: number | null;
  previous_close: number | null;
  change: number | null;
  change_pct: number | null;
  volume: number | null;
  oi: number | null;
  bid: number | null;
  ask: number | null;
  spread: number | null;
  provider: string;
  quality: DataQualityStatus;
}

export interface FeedHealthMetric {
  status: "HEALTHY" | "DELAYED" | "STALE" | "RECOVERING" | "DISCONNECTED";
  socket_connected: boolean;
  last_tick_at: string | null;
  tick_age_ms: number;
  provider_latency_ms: number | null;
  ticks_per_second: number;
  quality: DataQualityStatus;
}

export interface CanonicalFeedHealth {
  overall_status: "HEALTHY" | "DEGRADED" | "STALE" | "RECOVERING" | "NOT_RUNNING";
  socket_connected: boolean;
  nifty_feed?: FeedHealthMetric;
  vix_feed?: FeedHealthMetric;
  quality: DataQualityStatus;
}

export interface CanonicalCandle {
  start: string;
  end: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
  oi?: number | null;
  quality: string;
  is_forming?: boolean;
}

export interface CanonicalPriceStructure {
  last_price: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  previous_close: number | null;
  change: number | null;
  change_pct: number | null;
  range_points: number | null;
  range_pct: number | null;
  atr_14: number | null;
  is_compressed: boolean;
  opening_range_status: string;
  or_high: number | null;
  or_low: number | null;
  vwap: number | null;
  vwap_is_genuine: boolean;
  twap: number | null;
  trend_direction: DirectionBias;
  trend_strength: string;
  swing_high: number | null;
  swing_low: number | null;
  key_supports: number[];
  key_resistances: number[];
  gap_status: string;
  gap_points: number | null;
  gap_filled: boolean;
  day_character?: string;
  quality: DataQualityStatus;
}

export interface CanonicalBreadth {
  advances: number;
  declines: number;
  unchanged: number;
  total_constituents: number;
  ratio: number | null;
  advance_pct: number | null;
  leadership_bias: DirectionBias;
  heavyweight_bias: DirectionBias;
  sector_bias: Record<string, DirectionBias>;
  quality: DataQualityStatus;
}

export interface StrikeRow {
  strike: number;
  ce_ltp: number | null;
  ce_oi: number | null;
  ce_oi_change: number | null;
  ce_iv: number | null;
  ce_volume: number | null;
  ce_strength: string;
  ce_buildup: string;
  pe_ltp: number | null;
  pe_oi: number | null;
  pe_oi_change: number | null;
  pe_iv: number | null;
  pe_volume: number | null;
  pe_strength: string;
  pe_buildup: string;
  is_atm?: boolean;
  is_call_wall?: boolean;
  is_put_wall?: boolean;
}

export interface CanonicalOptionsIntelligence {
  spot_price: number | null;
  underlying_price?: number | null;
  expiry: string;
  atm_strike: number | null;
  pcr: number | null;
  max_pain: number | null;
  call_wall: number | null;
  put_wall: number | null;
  total_call_oi: number;
  total_put_oi: number;
  total_call_volume: number;
  total_put_volume: number;
  options_confirmation: OptionsSentiment;
  strike_universe: StrikeRow[];
  /** Option-chain provider snapshot time (falls back to market observation time). */
  observed_at?: string | null;
  quality: DataQualityStatus;
}

export interface FactorContribution {
  factor_name: string;
  vote: DirectionBias;
  nominal_weight: number;
  effective_weight: number;
  is_available: boolean;
  rationale: string;
}

export interface MagnitudeBucket {
  bucket_name: string;
  range_label: string;
  probability: number;
}

export interface CanonicalPredictionSnapshot {
  target_session_date: string;
  phase: MarketPhase;
  direction_bias: DirectionBias;
  direction_confidence: number;
  factor_contributions: FactorContribution[];
  magnitude_distribution: MagnitudeBucket[];
  expected_range_points: number | null;
  confidence_score: number;
  confidence_band: ConfidenceBand;
  calibration_maturity: string;
  quality: DataQualityStatus;

  /**
   * Live projection detail emitted by the backend prediction subsystem
   * (PredictionEngine.generate_prediction, serialized by LivePredictionService).
   * Optional so replay fixtures and older envelopes remain valid.
   */
  status?: "OK" | "UNAVAILABLE";
  unavailable_reason?: string;
  prediction_id?: string;
  model_version?: string;
  calibration_version?: string;
  generated_at?: string;
  generated_at_ist?: string;
  reference_price?: number | null;
  expected_move_points?: number | null;
  primary_target?: number | null;
  invalidation_level?: number | null;
  scenario_up_prob?: number | null;
  scenario_down_prob?: number | null;
  scenario_range_prob?: number | null;
  magnitude_lower_band_pts?: number | null;
  magnitude_upper_band_pts?: number | null;
  volatility_corridor?: {
    near_level?: number | null;
    far_level?: number | null;
    lower_band_pts?: number | null;
    upper_band_pts?: number | null;
  };
  similar_sessions?: SimilarSessionAnalog[];
  supporting_factors?: string[];
  caution_factors?: string[];
  market_regime?: string;
  is_live_projection?: boolean;
  basis?: "LIVE_SESSION" | "LAST_COMPLETED_SESSION" | "UNAVAILABLE";
}

export interface SimilarSessionAnalog {
  session_date: string;
  similarity_score: number;
  similarity_pct: number;
  regime: string;
  observed_move_pts: number;
  observed_range_pts: number;
  observed_direction: string;
}

export interface StrikeCandidate {
  canonical_id: string;
  option_type: "CE" | "PE";
  strike: number;
  ltp: number | null;
  distance_from_spot: number;
  liquidity: "LOW" | "NORMAL" | "HIGH";
  strength: "WEAK" | "MODERATE" | "STRONG";
  oi_context: string;
  iv: number | null;
  spread: number | null;
  rationale: string[];
  risks: string[];
}

export interface ChecklistItem {
  label: string;
  passed: boolean;
  details?: string;
}

export interface CanonicalDecisionSnapshot {
  decision_state: DecisionState;
  decision_headline: string;
  opportunity_setup: OpportunitySetup;
  trigger_condition: string;
  invalidation_boundary: string;
  confidence_band: ConfidenceBand;
  confidence_score: number;
  risk_level: RiskLevel;
  strategy_suitability: StrategySuitability;
  strike_candidates: StrikeCandidate[];
  checklist_items: ChecklistItem[];
  bullish_factors: string[];
  bearish_factors: string[];
  caution_factors: string[];
  quality: DataQualityStatus;
}

export interface CanonicalMorningPlan {
  session_date: string;
  reference_close: number;
  opening_bias: DirectionBias;
  direction_probability: number;
  magnitude_distribution: MagnitudeBucket[];
  expected_trading_range: { low: number; high: number };
  support_resistance_levels: { supports: number[]; resistances: number[] };
  gap_context: string;
  regime_expectation: MarketRegimeType;
  options_structure: {
    pcr: number | null;
    max_pain: number | null;
    call_wall: number | null;
    put_wall: number | null;
  };
  bullish_scenario: { trigger: string; target_area: string; invalidation: string };
  bearish_scenario: { trigger: string; target_area: string; invalidation: string };
  neutral_scenario: { condition: string; action: string };
  first_15m_checklist: string[];
  quality: DataQualityStatus;
}

export interface CanonicalLiveGuide {
  session_date: string;
  timestamp: string;
  nifty_bias: DirectionBias;
  confidence: number;
  active_setup: OpportunitySetup;
  invalidation_boundary: string;
  trigger_status: "ARMED" | "TRIGGERED" | "WAITING" | "INVALIDATED";
  primary_strike_candidate?: StrikeCandidate;
  key_factors_summary: string;
  caution_notes: string[];
  quality: DataQualityStatus;
}

export interface CanonicalTomorrowPlan {
  session_date?: string;
  completed_session_date: string;
  session_summary: {
    open: number | null;
    high: number | null;
    low: number | null;
    close: number | null;
    previous_close?: number | null;
    change: number | null;
    change_pct: number | null;
    range_points: number | null;
    vwap?: number | null;
    volume?: number | null;
  };
  day_type: "TREND_DAY" | "RANGE_DAY" | "EXPANSION_DAY" | "INSIDE_DAY" | "NEUTRAL_DAY" | "DISTRIBUTION_DAY";
  final_breadth: { advances: number; declines: number; unchanged?: number; ratio: number | null };
  leadership_summary?: string;
  options_closing_structure: {
    pcr: number | null;
    max_pain: number | null;
    call_wall: number | null;
    put_wall: number | null;
    notable_shifts?: string[];
  };
  prediction_outcome: {
    predicted_bias: DirectionBias;
    actual_bias: DirectionBias;
    direction_accurate: boolean;
    magnitude_bucket_hit: string;
    expected_range_points?: number;
    actual_range_points?: number;
    sample_size?: number;
  };
  signals_worked: string[];
  signals_failed: string[];
  key_levels_next_session: { supports: number[]; resistances: number[] };
  preliminary_next_bias: DirectionBias;
  known_missing_context?: string[];
  quality: DataQualityStatus;
}

export interface CanonicalNewsPayloadItem {
  id?: string;
  headline?: string;
  title?: string;
  source?: string;
  publisher?: string;
  region?: string;
  country?: string;
  impact_level?: "HIGH" | "MEDIUM" | "LOW" | string;
  sentiment?: "POSITIVE" | "NEGATIVE" | "NEUTRAL" | string;
  expected_direction?: string;
  relevance_score?: number;
  nifty_relevance?: number;
  published_at?: string;
  timestamp?: string;
  summary?: string;
  description?: string;
  transmission_summary?: string;
  why_it_matters?: string;
  entities?: string[];
  affected_companies?: string[];
  affected_sectors?: string[];
}

export interface CanonicalSectorItem {
  name: string;
  change_percent?: number | null;
  change_pct?: number | null;
  status?: "BULLISH" | "BEARISH" | "NEUTRAL";
  advance_count?: number;
  decline_count?: number;
}

export interface CanonicalSettledSessionSummary {
  session_date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  previous_close: number | null;
  change: number | null;
  change_pct: number | null;
  range_points: number | null;
  vwap: number | null;
  or_high: number | null;
  or_low: number | null;
  atr_14: number | null;
  structural_levels?: {
    pivot?: number;
    r1?: number;
    r2?: number;
    r3?: number;
    s1?: number;
    s2?: number;
    s3?: number;
    raw_atr_14?: number;
  };
  closing_vix?: number | null;
  vix_close?: number | null;
  closing_breadth?: {
    advances?: number;
    declines?: number;
    ratio?: number | null;
  };
  institutional_flows?: {
    net?: number;
    fii_net?: number;
    dii_net?: number;
    fii?: number;
    dii?: number;
    pro?: number;
    retail?: number;
  };
  quality: "COMPLETED" | "VALID" | "UNAVAILABLE";
}

export interface CanonicalFrontendEnvelope {
  runtime_id: string;
  state_revision: number;
  published_at: string;
  /** Authoritative observation time of the underlying market data (real tick/exchange
   *  timestamp) — distinct from `published_at`, which is envelope generation time. */
  market_observed_at?: string | null;
  session: CanonicalSessionContext;
  market: {
    nifty?: CanonicalInstrumentState;
    vix?: CanonicalInstrumentState;
    /** Observation time of the market snapshot (mirrors nifty.exchange_timestamp). */
    observed_at?: string | null;
    state_revision: number;
    quality: DataQualityStatus;
  };
  feed_health: CanonicalFeedHealth;
  candles: {
    "1m"?: CanonicalCandle[];
    "5m"?: CanonicalCandle[];
    "15m"?: CanonicalCandle[];
    "60m"?: CanonicalCandle[];
  };
  price_structure: CanonicalPriceStructure;
  breadth: CanonicalBreadth;
  options: CanonicalOptionsIntelligence;
  regime: {
    regime_type: MarketRegimeType;
    rationale: string;
    volatility_state: string;
  };
  prediction: CanonicalPredictionSnapshot;
  decision: CanonicalDecisionSnapshot;
  active_product?: {
    product_type: "MORNING_PLAN" | "LIVE_GUIDE" | "TOMORROW_PLAN";
    morning_plan?: CanonicalMorningPlan;
    live_guide?: CanonicalLiveGuide;
    tomorrow_plan?: CanonicalTomorrowPlan;
  };
  news_intelligence?: {
    items?: CanonicalNewsPayloadItem[];
    tone?: string;
    risk?: string;
  };
  macro_intelligence?: {
    economic_events?: any[];
    macro_factors?: any[];
  };
  newsItems?: CanonicalNewsPayloadItem[];
  sectorPerformance?: CanonicalSectorItem[];
  marketOverview?: {
    sectors?: CanonicalSectorItem[];
  };
  settled_session?: CanonicalSettledSessionSummary;
  data_quality: DataQualityStatus;
}
