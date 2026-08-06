# Frontend Field Migration Map: React Canonical-State Migration (Phase 5.1)

This document maps all legacy camelCase payload fields used in the React frontend to their canonical snake_case `CanonicalWorkstationState` (version `2.0.0`) counterparts, outlining their availability, shape differences, consumers, and migration actions.

---

## 1. Active-Consumer Migration Matrix

The following matrix documents every active frontend field consumption:

### 1. Market Context Telemetry

* **Legacy Field:** `marketContext`
* **Canonical Field:** `market_data`
* **Canonical Availability:** Authoritative stage `market` (status is `ready` or `market_closed`).
* **Shape Differences:** 
  * Nested properties remain identical (e.g., `current_spot`, `india_vix`, `atr`, `vwap`, `support_levels`, `resistance_levels`, `trend_direction`, `trend_strength`, `market_regime`).
  * `last_tick_time` is replaced by the canonical time metadata `observed_at` in `data_quality.market_data` or standard ISO string.
* **Consumer Components:**
  * `DashboardLayout.tsx` (reads `marketContext.last_tick_time` for KITE status bar)
  * `WorkstationTopBar.tsx` (reads `marketContext.feed_health` and `marketContext.feed_latency_ms`)
  * `PhaseOneWorkspaces.tsx` (reads `marketContext.current_spot` to gate workspaces)
  * `ExecutiveSummary.tsx` (reads `current_spot`, `market_regime`, `trend_direction`)
  * `MarketOverview.tsx` (reads `current_spot`, `trend_direction`, `india_vix`, `volatility_state`, `atr`, `support_levels`, `resistance_levels`)
  * `MarketStory.tsx` (reads `current_spot`, `vwap`, `atr`, `india_vix`, `trend_direction`, `market_regime`, `trend_strength`, `volatility_state`)
* **Migration Status:** Pending context update.

### 2. Option Chain Telemetry

* **Legacy Field:** `optionContext`
* **Canonical Field:** `option_intelligence`
* **Canonical Availability:** Authoritative stage `options` (status is `ready`, `degraded`, or `unavailable`).
* **Shape Differences:**
  * Nested properties remain identical (e.g., `pcr`, `atm_iv`, `expected_move`, `atm_strike`, `top_candidate_strikes`).
* **Consumer Components:**
  * `PhaseOneWorkspaces.tsx` (reads `optionContext.underlying_spot` to gate Options tab)
  * `ExecutiveSummary.tsx` (null-checks `optionContext`)
  * `MarketOverview.tsx` (reads `optionContext.pcr`, `optionContext.top_candidate_strikes`)
  * `MarketStory.tsx` (reads `optionContext.pcr`, `optionContext.atm_iv`, `optionContext.expected_move`, `optionContext.atm_strike`)
* **Migration Status:** Pending context update.

### 3. Market Score Telemetry

* **Legacy Field:** `marketScore`
* **Canonical Field:** `market_score`
* **Canonical Availability:** Authoritative stage `score` (status is `ready` or `blocked`).
* **Shape Differences:** Nested properties remain identical.
* **Consumer Components:**
  * `MarketScoring.tsx` (reads `score.trend`, `score.options`, `score.volatility`, `score.liquidity`, `score.expiry`, `score.overall_score`, `score.letter_grade`, `score.classification`)
* **Migration Status:** Pending context update.

### 4. Opportunity Context

* **Legacy Field:** `opportunityContext`
* **Canonical Field:** `opportunity`
* **Canonical Availability:** Authoritative stage `opportunity`.
* **Shape Differences:** None.
* **Consumer Components:** None (retained in context state for type safety).
* **Migration Status:** Pending context update.

### 5. Strategy Suitability

* **Legacy Field:** `strategyEvaluation`
* **Canonical Field:** `strategy_suitability`
* **Canonical Availability:** Authoritative stage `strategy`.
* **Shape Differences:** None.
* **Consumer Components:** None (retained in context settings for future use).
* **Migration Status:** Pending context update.

### 6. Trade Plan / Scenarios

* **Legacy Field:** `tradePlan` (formerly returned empty in live daemon payload)
* **Canonical Field:** `trade_scenarios`
* **Canonical Availability:** Authoritative stage `scenarios` (populated from accepted planner candidates).
* **Shape Differences:**
  * Array of scenarios containing: `scenario_name`, `direction`, `activation_condition`, `confirmation_conditions`, `invalidation_condition`, `target_zones`, `scenario_confidence`, `status`.
* **Consumer Components:**
  * `DecisionEngine.tsx` will be migrated to render `trade_scenarios` directly, utilizing the existing card layout:
    * `cand.execution_priority` → `idx + 1` (index in scenario list)
    * `cand.tradingsymbol` → `scenario.scenario_name`
    * `cand.decision` → `scenario.direction`
    * `cand.explanation` → `scenario.activation_condition`
    * `cand.supporting_evidence` → `scenario.confirmation_conditions`
    * `cand.blocking_factors` → `scenario.invalidation_condition`
* **Migration Status:** Pending context update.

### 7. Decision Engine / Support

* **Legacy Field:** `decisionReport`
* **Canonical Field:** `decision_support`
* **Canonical Availability:** Authoritative stage `decision_support` (status is `ready` or `degraded`).
* **Shape Differences:**
  * Mapped directly from `DecisionSupportReport` (properties: `market_interpretation`, `current_scenario_status`, `required_confirmations`, `missing_confirmations`, `invalidation_conditions`, `blockers`, `warnings`, `human_decision_required`).
  * In the frontend, the overall decision action (formerly `overall_action`) is calculated as:
    `const overallAction = (report.blockers.length > 0 || report.missing_confirmations.length > 0) ? "HOLD" : "MONITOR"`
* **Consumer Components:**
  * `ExecutiveSummary.tsx` (reads overall action, status message, warnings/conclusions)
  * `DecisionEngine.tsx` (reads overall action)
* **Migration Status:** Pending context update.

### 8. News Sentiment

* **Legacy Field:** `newsSentiment`
* **Canonical Field:** `news_intelligence`
* **Canonical Availability:** Authoritative stage `news` (status is `ready` or `unavailable`).
* **Shape Differences:** Nested properties remain identical.
* **Consumer Components:**
  * `NewsIntelligence.tsx` (reads `news.overall_sentiment`, `news.sentiment_bias`, `news.articles`, `news.is_news_panic_active`)
  * `MarketStory.tsx` (reads `news.articles`, `news.overall_sentiment`, `news.sentiment_bias`, `news.is_news_panic_active`)
* **Migration Status:** Pending context update.

### 9. Workspace Readiness

* **Legacy Field:** `workspaceReadiness` (root-level field in legacy JSON payload)
* **Canonical Field:** `workspace_readiness`
* **Canonical Availability:** Root property of `CanonicalWorkstationState`.
* **Shape Differences:** None.
* **Consumer Components:**
  * `DashboardLayout.tsx` and `PhaseOneWorkspaces.tsx` (inspect workspace status and dependency blockers).
* **Migration Status:** Pending context update.

### 10. Data Quality / Metadata

* **Legacy Field:** `canonicalMetadata` (root-level metadata)
* **Canonical Field:** `data_quality` & state root metadata
* **Canonical Availability:** Root property of `CanonicalWorkstationState`.
* **Shape Differences:** Matches the `CanonicalWorkstationState` metadata format.
* **Consumer Components:**
  * `WorkstationStateContext.tsx` (reads `schema_version`, `state_sequence`, `runtime_id`, `generated_at`).
* **Migration Status:** Pending context update.

---

## 3. Disconnected / Legacy Fields (Removed from State Feed)

The following compatibility fields are not present in `CanonicalWorkstationState` v2.0.0 and are mapped to empty/default states inside the provider to prevent active page crashes:
* `eveningReport` (defaults to static empty structure in `PreMarketPlannerWorkspace` if cache not populated)
* `intradayReport` (retained in context with safe defaults; all active consumers default gracefully)
* `validationReport` (retained with defaults)
* `optimizationReport` (retained with defaults)
* `analyticsReport` (retained with defaults)
* `operationsReport` (retained with defaults)
