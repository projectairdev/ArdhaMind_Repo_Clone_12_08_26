# Runtime Field Provenance

Verified against the Phase 1 live path: React `WorkstationStateContext` -> WebSocket `state`/`tick` -> Express `workstationState` in `server.ts` -> Python `run_daemon` / `generate_dynamic_workspace_data` in `src/server_bridge.py` -> broker services, builders and selected pipelines.

Legend: **L** live observation, **H** historical, **C** calculated, **S** synthesized in bridge, **U** unavailable. “Current timestamps” describes the pre-Phase-2 behavior, not the target contract.

## Market

| Canonical fields | Frontend/payload | Producer and actual source | Class/timestamps/fallback | Validation and migration/blockers |
|---|---|---|---|---|
| NIFTY price | `MarketOverview`, `MarketStory`; `marketContext.current_spot`, tick `last_price` | `MarketContextBuilder.build`; Kite ticker/REST via `StreamingOrchestrator` | L; tick/market timestamp; React starts unavailable | Validate positive finite NIFTY observation; spot blocks all dependent stages |
| change, % change, OHLC, previous close | primarily tick/quote shapes; not consistently present in `MarketContext` | Kite quote/tick OHLC where subscribed | L/U; source tick timestamps inconsistent | Add canonical market-data fields; unavailable until quote supplies OHLC |
| VWAP, ATR | `marketContext.vwap/atr` | `MarketContextBuilder` candle/tick buffer | C from L/H; report timestamp only | Require sufficient valid observations; dependencies spot/candles |
| trend, regime, volatility | `marketContext.trend_direction`, `market_regime`, `volatility_state` | market builder and indicator engines | C; generated timestamp; bridge also maps these into `TradeContext` | Canonical pipeline output; block when required lookback missing |
| support/resistance | `support_levels`, `resistance_levels` | market builder/indicator support-resistance | C; report timestamp | Preserve method metadata and inputs; partial allowed |
| breakout/breakdown | scenario/report fields, not one authoritative market field | planner/bridge synthesis | S/U | Canonical scenario stage only; requires validated levels |
| India VIX | `marketContext.india_vix` | broker market context / Kite instrument quote | L; quote time incompletely propagated | Independent 30/90-second quality threshold |
| breadth/heavyweights | opportunity dictionaries, some bridge-generated values | `OpportunityContextBuilder` plus bridge placeholders | C/S/U | Mark unavailable until authoritative constituent feed exists |

## Options

| Canonical fields | Frontend/payload | Producer/source | Class/timestamps/fallback | Migration/blockers |
|---|---|---|---|---|
| expiry, ATM, strikes | `optionContext` | `InstrumentService`/`InstrumentManager`, Kite instrument master | L metadata + C ATM; option-context timestamp | Current-day validated master mandatory |
| call/put OI and changes | `highest_call_oi`, `highest_put_oi`, change fields and chain summary | `MarketFeedService` or `OptionIntelligencePipeline` -> `analyze_oi`; Kite quotes | L/C; aggregate timestamp | Block options after 45 seconds; contract quotes after 30 seconds |
| PCR | `optionContext.pcr` | OI analyzer/market feed | C | Requires complete-enough call/put OI |
| max pain | `max_pain` | `options_engine.max_pain.calculate_max_pain` | C | Requires validated chain |
| IV, expected move | `atm_iv`, candidate IV, `expected_move` | `options_engine.iv`; quote premium + expiry + spot | C | No spot fallback; missing premium/expiry blocks |
| liquidity, bid/ask spread | `liquidity_metrics`, candidate `spread_pct` | chain builder/liquidity analyzer; Kite bid/ask/volume/OI | L/C | Per-quote 10/30-second limit |
| call/put wall | resistance/support strikes/highest OI | OI analyzer | C | Label calculation method rather than raw observation |

## Intelligence

| Canonical section | Current producer/payload | Current class | Migration/blockers |
|---|---|---|---|
| market score | `MarketScoreBuilder` called by bridge; `marketScore` | C over bridge-built trade context | Route through `MarketScoringPipeline`; blocked by invalid market context |
| opportunity | `OpportunityContextBuilder`; `opportunityContext` | C | Canonical `OpportunityPipeline`; depends on score/context |
| strategy suitability | `StrategyEvaluationBuilder`; `strategyEvaluation` | C | Canonical `StrategyPipeline`; no executable strategy intent |
| confidence | bridge dictionaries and confidence models | S/C | Canonical `ConfidencePipeline`; degrade/block by option dependencies |
| deterministic risk | bridge dictionaries / Risk V2 models | S/C | Canonical `RiskPipeline`; remove allocation/quantity from canonical transport |
| trade scenario/invalidation | bridge candidate synthesis and planner models | S/C | Canonical `TradePlannerPipeline`; no order-ready fields |
| decision support | legacy `decisionReport` | S/C | New `DecisionSupportReport` with compatibility adapter |
| explanation | deterministic `ExplanationReport` built in bridge | C/S | Deterministic fallback remains; source stage statuses included |

## External and operational

| Field | Consumer/path | Producer/source/class | Current fallback | Decision |
|---|---|---|---|---|
| news/corporate/events | News workspace; `newsSentiment` | daemon `NewsPipeline`; Phase 1 passes no hardcoded providers | U | Remain unavailable until real provider adapter; never blocks market math |
| Kite connection | top bar/Settings; `workspaceContext.brokerState` | `BrokerService`/Kite gateway/session | disconnected/expired | Canonical broker status with last success/reconnect required |
| browser WebSocket | top bar; `connectionState` | React WebSocket lifecycle | local client status | Transport status distinct from market-feed health |
| REST state | Settings | inferred from broker/session and calls | no canonical field | Add broker status subfield |
| instrument master | Settings/option analysis | `InstrumentService`, SQLite cache, Kite instruments | stale cache may be used | Current/previous-day classification and hard block rules |
| market feed health/age | top bar/Settings | `StreamingOrchestrator`, `StreamHealthMonitor`, market context | HTTP polling fallback | Canonical status and observation ages |
| funds/positions | legacy portfolio/Settings account summary | Kite REST or mock gateway | synthetic in mock mode | Optional read-only summary only; core must not depend on it |
| operations health | Settings; `operationsReport` | `OperationsReportBuilder`/bridge | some stable/default diagnostics | Canonical structured service health; no execution readiness |

## Timestamp gaps

Tick models contain exchange/backend timestamps and reports usually have one generated timestamp, but most displayed values do not carry `observed_at`, `received_at` and `generated_at` together. Express adds forwarding time to ticks; React also records local receipt time. Phase 2 canonical metadata resolves these as separate concepts.

## Confirmed false-data corrections

The Phase 1 option pipeline now blocks instead of using NIFTY 24000; React option/planner defaults are empty; hardcoded news providers are disconnected. Remaining bridge-synthesized fields are classified legacy until Phase 3 pipeline integration.

