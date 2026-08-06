# Phase 3 live runtime map

Before Phase 3, `server_bridge.run_daemon` refreshed `cached_market_context` and
`cached_option_context`, called `generate_dynamic_workspace_data`, then selected
core fields from both products into `legacy_data`. Phase 2 canonicalized that map
only at the final transport seam. This allowed duplicated calculations and mixed
refresh ages.

| Stage | Before | Input/output | Phase 3 authority | Missing/blocking dependency |
|---|---|---|---|---|
| Market | partially canonical `MarketContextBuilder` | Kite ticks -> dictionary | validated `RuntimeInput` -> `MarketContext` | valid positive spot, timestamp, market domain fields |
| Options | partially canonical live builder | instruments/quotes -> dictionary | validated input -> `OptionContext` | spot consistency, expiry, complete contract |
| Trade context | bridge/dynamic path | market/options + derived subcontexts | `TradeContextBuilder` | ready market and options |
| Score | canonical builder, formerly invoked by dynamic path | `TradeContext` -> `MarketScore` | `MarketScoringPipeline` | trade context |
| Opportunity | canonical builder | context/score -> opportunity | `OpportunityPipeline` | score |
| Strategy | canonical builder | context/score/opportunity | `StrategyPipeline` | opportunity |
| Planning | legacy executable-shaped plan | strategy/options/opportunity | `TradePlannerPipeline`, then read-only scenario adapter | valid options |
| Confidence | canonical | plan/strategy/opportunity/score | `ConfidencePipeline` | partial options degrade |
| Risk | canonical `risk_engine_v2` | confidence/plan/context/score | `RiskPipeline`; state sanitizer removes allocation fields | confidence |
| Decision | legacy `DecisionReport` | execution-oriented reports | canonical `DecisionSupportReport` | validated upstream stages |
| Explanation | legacy report | multiple reports | deterministic canonical explanation | reports only validated fields |
| News | no real provider | unavailable dictionary | real-or-unavailable input | never blocks market analytics |
| Operations | bridge legacy | service diagnostics | legacy compatibility, Phase 4 candidate | independent |
| Account | optional broker calls | read-only account maps | optional input boundary; excluded from analysis | never blocks analytics |

The browser consumer remains `WorkstationStateContext` over the Express WebSocket
relay. One `RuntimeSnapshot` now covers validation through analytical result,
canonical state, compatibility serialization and broadcast.
