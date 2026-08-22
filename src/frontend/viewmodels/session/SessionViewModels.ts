// src/frontend/viewmodels/session/SessionViewModels.ts

export type Availability = "LIVE" | "DELAYED" | "STALE" | "DEGRADED" | "UNAVAILABLE" | "LAST_SESSION";

export interface SourceMeta {
  availability: Availability;
  observedAt: string | null;
  source: string | null;
}

export interface ScenarioEvidenceRow {
  label: string;
  value: string;
}

export interface StrategyItem {
  name: string;
  tag: string; // e.g. "Preferred", "Alternate", "Tactical"
  suitabilityStars?: number; // e.g. 1 to 5
  whenCondition: string;
  trigger: string;
  targetArea: string;
  invalidation: string;
  riskReward: string;
  confidence: string;
  evidence: string;
  historicalProofText: string;
  winRate?: string;
  expectancy?: string;
  tradesTested?: string;
}

export interface ValueSuggestionItem {
  zone: string;
  upper: string;
  lower: string;
  conviction: "High" | "Moderate" | "Low" | "UNAVAILABLE";
  rationale: string;
  dataBasis: string;
}

export interface StrikeSuggestionItem {
  type: "Best Call Strike Zone" | "Best Put Strike Zone";
  strikeZone: string;
  rationale: string;
  confidence: string;
  dataBasis: string;
  availability: "AVAILABLE" | "UNAVAILABLE";
}

export interface RiskContextState {
  globalCues: string;
  vixValue: string;
  vixChange?: string;
  eventRisk: "Low" | "Moderate" | "High" | "UNAVAILABLE";
  newsSentiment: string;
  marketMood: string;
  volatilityExpectation: string;
  gapImpact: string;
  liquidity: string;
  sectorTone: string;
  overallRisk: string;
  confidenceScore: string;
  confirmationsCount: number;
  blockersCount: number;
  proofBadges: string[];
  blockers: string[];
  confirmations: string[];
}

export interface FieldStatusViewModel<T = string | number | null> {
  value: T;
  status: "AVAILABLE" | "NOT_QUALIFIED" | "STALE" | "UNAVAILABLE" | "WAITING" | "DEGRADED" | "REQUIRES_LIVE_OPTIONS" | "WAITING_FOR_OPTIONS_CONFIRMATION" | "WAITING_FOR_TRIGGER";
}

export interface EntryConditionViewModel {
  primary_trigger: string;
  confirmation_conditions: string[];
  invalidation_condition: string;
  formatted_statement: string;
}

export interface MarketDecisionSummaryViewModel {
  decision_id: string;
  as_of: string;
  session_date: string;
  session_phase: string;
  bias: FieldStatusViewModel<string | null>;
  setup: FieldStatusViewModel<string | null>;
  strike: FieldStatusViewModel<string | null>;
  entry_condition: FieldStatusViewModel<EntryConditionViewModel | null>;
  confidence: FieldStatusViewModel<number | null>;
  liquidity: FieldStatusViewModel<string | null>;
  data_quality: FieldStatusViewModel<string | null>;
  risk: FieldStatusViewModel<string | null>;
  status: "WAITING" | "WATCH" | "QUALIFYING" | "READY_FOR_APPROVAL" | "BLOCKED" | "INVALIDATED" | "EXPIRED" | "UNAVAILABLE" | "MARKET_CLOSED";
  invalidation: string | null;
  supporting_evidence: string[];
  blocking_reasons: string[];
  provenance: {
    canonical_sequence?: number;
    runtime_id?: string;
    opportunity_id?: string;
    strategy_id?: string;
    liquidity_policy_version?: string;
    evidence_sources?: string[];
    freshness_summary?: Record<string, string>;
  };
}

export interface MorningPlanViewModel {
  decisionSummary?: MarketDecisionSummaryViewModel | null;
  generatedAt: string;
  snapshotTimestamp: string;
  isPreparing: boolean;
  bestPlan: {
    spotIndex: string;
    carryForwardLevel: string;
    openingRangeEst: string;
    preferredBias: "BULLISH" | "BEARISH" | "NEUTRAL" | "UNAVAILABLE";
    invalidation: string;
    rationale: string;
    why: string;
    trigger: string;
    confidenceScore: string;
  };
  primaryScenario: {
    name: string;
    confidencePct: string;
    plan: string;
    dataBasis: string;
    evidenceTable: ScenarioEvidenceRow[];
    invalidation: string;
    historicalProofText: string;
  };
  alternateScenario: {
    name: string;
    confidencePct: string;
    plan: string;
    dataBasis: string;
    evidenceTable: ScenarioEvidenceRow[];
    invalidation: string;
    historicalProofText: string;
  };
  whatToWatchFirst15Min: Array<{
    title: string;
    condition: string;
    status: string;
  }>;
  suitableStrategies: StrategyItem[];
  yesterdaysInfo: {
    sessionDate: string;
    close: string;
    high: string;
    low: string;
    prevClose: string;
    change: string;
    changePct: string;
    advDec: string;
    vwap: string;
    pcr: string;
    fiiCashCr: string;
    diiCashCr: string;
  };
  todaysOpen: {
    windowLabel: string;
    open: string;
    high: string;
    low: string;
    vwap: string;
    rangePts: string;
    breadth: string;
    priceVsVwap: string;
    pcr: string;
    fiiCashCr: string;
    diiCashCr: string;
    isImmutable: boolean;
  };
  keyLevelsDecisionZone: {
    resistance2: string;
    resistance1: string;
    pivotDecisionZone: string;
    support1: string;
    support2: string;
    bullishAbove: string;
    bearishBelow: string;
    invalidationLevel: string;
    mustHoldLevel: string;
    trendFilter: string;
  };
  morningRisk: RiskContextState;
  dataBackedValueSuggestions: ValueSuggestionItem[];
}

export interface LiveGuideViewModel {
  decisionSummary?: MarketDecisionSummaryViewModel | null;
  generatedAt: string;
  lastUpdatedTime: string;
  bestActionNow: {
    status: "WAIT" | "WATCH" | "CONFIRMATION REQUIRED" | "BIAS STRENGTHENING" | "BIAS WEAKENING" | "SETUP QUALIFIED" | "RISK INCREASED" | "MORNING THESIS INVALIDATED";
    statusColor: string;
    headline: string;
    rationale: string;
    nextTrigger: string;
    invalidation: string;
    confidenceScore: string;
  };
  currentMarketState: {
    bias: string;
    priceStructure: string;
    marketBreadth: string;
    vwapStatus: string;
    momentum: string;
    volatility: string;
    vixStr: string;
    thesisComparison: {
      morningBias: string;
      currentStatus: string;
      whatChanged: string;
    };
  };
  primaryScenario: {
    name: string;
    confidencePct: string;
    plan: string;
    conditions: string;
    whatToDo: string;
    keyLevels: string;
    invalidation: string;
    evidenceTags: string[];
  };
  alternateScenario: {
    name: string;
    confidencePct: string;
    plan: string;
    conditions: string;
    whatToDo: string;
    keyLevels: string;
    invalidation: string;
    evidenceTags: string[];
  };
  keyLevelsValueSuggestions: ValueSuggestionItem[];
  liveMetrics: {
    niftySpot: string;
    niftyChange: string;
    bankNiftySpot: string;
    bankNiftyChange: string;
    indiaVix: string;
    indiaVixChange: string;
    rsiMomentum: string;
    pcr: string;
    breadth: string;
    breadthAdvDec: string;
    freshnessLabel?: string;
    isLive?: boolean;
  };
  realTimeWatchlist: {
    leadingSectors: string[];
    laggingSectors: string[];
    topGainers: string[];
    topLosers: string[];
  };
  suitableStrategies: StrategyItem[];
  opportunityStatus: {
    stage: "IDEA" | "CONDITIONS" | "CONFIRMATION" | "SETUP QUALIFIED";
    setupName: string | null;
    direction: string | null;
    actionText: string;
    summary: string;
    hasTrade: boolean;
  };
  riskContext: RiskContextState;
}

export interface TomorrowPlanViewModel {
  decisionSummary?: MarketDecisionSummaryViewModel | null;
  generatedAt: string;
  sessionDate: string;
  nextSessionDate: string;
  bestPlan: {
    headline: string;
    rationale: string;
    spotIndex: string;
    carryForwardLevel: string;
    openingZone: string;
    bias: string;
    bullishTrigger: string;
    bearishTrigger: string;
    preferredEntryArea: string;
    invalidationLevels: string;
    evidencePoints: string[];
    confidenceScore: string;
    dataBasisProof: string;
  };
  bestStrikeSuggestions: StrikeSuggestionItem[];
  whatToPrepare: {
    checklist: string[];
    dataBasisProof: string;
  };
  suitableStrategies: StrategyItem[];
  tomorrowRisk: RiskContextState;
  todaysMarketOverview: {
    open: string;
    high: string;
    low: string;
    close: string;
    dayChange: string;
    dayType: string;
    breadth: string;
    vwapBehavior: string;
    leadership: string;
    vixChange: string;
  };
  criticalLevelsTomorrow: {
    support1: string;
    support2: string;
    carryForwardLevel: string;
    openingZone: string;
    resistance1: string;
    resistance2: string;
    bullishTrigger: string;
    bearishTrigger: string;
    invalidationLevel: string;
  };
  scenariosTomorrow: {
    primary: {
      name: string;
      confidencePct: string;
      conditions: string;
      whatToDo: string;
      keyLevels: string;
    };
    alternate: {
      name: string;
      confidencePct: string;
      conditions: string;
      whatToDo: string;
      keyLevels: string;
    };
  };
  confidenceAndStructure: {
    planConfidence: string;
    dataQuality: string;
    structureScore: string;
    volatilityRegime: string;
    liquidity: string;
  };
}
