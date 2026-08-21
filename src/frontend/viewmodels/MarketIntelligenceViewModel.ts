// src/frontend/viewmodels/MarketIntelligenceViewModel.ts

export type Availability = "LIVE" | "DELAYED" | "STALE" | "DEGRADED" | "UNAVAILABLE";

export interface SourceMeta {
  availability: Availability;
  observedAt: string | null;
  source: string | null;
}

export interface MarketIntelligenceViewModel {
  runtimeId: string | null;
  sequenceNumber: number | null;
  generatedAt: string;
  marketStatus: "PRE_MARKET" | "OPEN" | "POST_MARKET" | "CLOSED" | "HOLIDAY" | "UNAVAILABLE";

  regime: {
    name: string | null;
    bias: "BULLISH" | "BEARISH" | "NEUTRAL" | null;
    strengthScore: number | null;
    confidencePct: number | null;
    description: string | null;
    source: SourceMeta;
  };

  corridor: {
    spotPrice: number | null;
    spotChange: number | null;
    spotChangePct: number | null;
    vwap: number | null;
    immediateSupport: number | null;
    immediateResistance: number | null;
    status:
      | "ABOVE_VWAP"
      | "BELOW_VWAP"
      | "INSIDE_CORRIDOR"
      | "TESTING_SUPPORT"
      | "TESTING_RESISTANCE"
      | "ABOVE_RESISTANCE"
      | "BELOW_SUPPORT"
      | "UNAVAILABLE";
    source: SourceMeta;
  };

  participation: {
    advances: number | null;
    declines: number | null;
    unchanged: number | null;
    breadthPct: number | null;
    breadthBias: "POSITIVE" | "NEGATIVE" | "BALANCED" | "UNAVAILABLE";
    hasDivergence: boolean | null;
    divergenceNote: string | null;
    source: SourceMeta;
  };

  derivatives: {
    pcr: number | null;
    callWall: number | null;
    putWall: number | null;
    maxPain: number | null;
    indiaVix: number | null;
    volatilityRegime: "EXPANSION" | "COMPRESSION" | "NORMAL" | "UNAVAILABLE";
    source: SourceMeta;
  };

  leadership: {
    topAdvancingSector: string | null;
    topDecliningSector: string | null;
    topAdvancingSectorPct: number | null;
    topDecliningSectorPct: number | null;
    heavyweightsAdvancingCount: number | null;
    heavyweightsDecliningCount: number | null;
    heavyweightsTotalCount: number | null;
    summary: string | null;
    source: SourceMeta;
  };

  institutional: {
    fiiNet: number | null;
    diiNet: number | null;
    combinedNet: number | null;
    interpretation: "SUPPORTIVE" | "OPPOSING" | "MIXED" | "NEUTRAL" | "UNAVAILABLE";
    source: SourceMeta;
  };

  sessionStory: {
    morningThesisSummary: string | null;
    currentEvolutionSummary: string | null;
    keyEvents: Array<{
      time: string;
      event: string;
      source: string | null;
    }>;
    source: SourceMeta;
  };

  riskContext: {
    newsImpact: "POSITIVE" | "NEGATIVE" | "MIXED" | "NEUTRAL" | "UNAVAILABLE";
    eventRisk: "LOW" | "MODERATE" | "HIGH" | "UNAVAILABLE";
    blockers: string[];
    confirmations: string[];
    source: SourceMeta;
  };

  opportunity: {
    hasQualifiedSetup: boolean;
    setupName: string | null;
    priorityScore: number | null;
    direction: "BULLISH" | "BEARISH" | "NEUTRAL" | null;
    status: "QUALIFIED" | "STANDBY" | "BLOCKED" | "UNAVAILABLE";
    statusSummary: string | null;
    proposalId: string | null;
    source: SourceMeta;
  };
}
