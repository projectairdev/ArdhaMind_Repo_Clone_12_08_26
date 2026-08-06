# TypeScript Canonical Contracts (Phase 5.1)

The following TypeScript contracts are defined in [types.ts](file:///e:/AIR/ArdhaMind01/src/frontend/types.ts) to match the `CanonicalWorkstationState` (version `2.0.0`) shape and its sub-segments:

```typescript
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
  warnings: string[];
  errors: string[];
}
```
These contracts reflect the backend state directly with snake_case property structures and explicit optionality markers.
