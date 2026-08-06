# Capability Disposition

Ratings: **A** core; **B** useful/small changes; **C** major refactor; **D** extract; **E** remove from product/runtime; **F** test-only; **G** future phase.

| Capability | Current role and dependencies | Runtime status | Rating | Definitive action / migration risk |
|---|---|---|---:|---|
| `models/` | Python report contracts used throughout | Active | A | Keep; separate broker service DTO imports and generate shared contracts. High compatibility sensitivity. |
| `data_engine/` | Kite instruments, quotes, history | Active/legacy consumers | C | Keep capability; adapt behind validated read-only data ports. Remove fake fallback later. |
| `indicator_engine/` | Technical calculations | Active | A | Keep and validate numerical contracts. |
| `options_engine/` | Chain, OI, PCR, max pain, IV, liquidity | Active | A | Keep; require complete/fresh quotes and expand metadata. |
| `trade_engine/` | Market+option trade context | Active in canonical flows | A | Keep as scenario-context seam. |
| `scoring_engine/` | Deterministic composite scoring | Active | A | Keep; version inputs/weights and propagate quality. |
| `opportunity_engine/` | Opportunity classification | Active | A | Keep; block on invalid dependencies. |
| `strategy_engine/` | Strategy suitability | Active | A | Keep as non-executing suitability analysis. |
| `confidence_engine/` | Bonuses, penalties, confidence | Active/partly canonical | B | Keep; calibrate and expose reasons/dependencies. |
| `risk_engine_v2/` | Scenario allocation/constraints/exposure | Canonical pipeline | B | Keep scenario risk, remove execution quantity semantics from user output. |
| `decision_engine/` | Rules and priorities | Active/partly bridge | B | Rename product output concept to decision support, not trading decision; preserve engine initially. |
| `explanation_engine/` | Deterministic narratives | Active | A | Keep as required fallback and audit baseline. |
| `intraday/` | Confirmation/invalidation monitoring | Active | A | Keep; remove position-management framing. |
| `planner_engine/` | Candidate generation/filter/ranking | Active/bridge overlap | B | Keep as scenario generator; never emit executable intent. |
| `planner/` | Tomorrow/evening summaries | Active | B | Keep as briefing/report composition. |
| `news_engine/` | RSS plus hardcoded providers | Active mixed | C | Retain processing; replace active static providers and add provenance. |
| `analytics_engine/` | Trade-performance analysis | Active from virtual ledger | D/C | Extract trade P&L analytics; retain reusable intelligence-quality analytics after redesign. |
| `validation_engine/` | Historical pipeline evaluation | Partial | C | Retain as internal validation/historical intelligence, not advertised backtester. |
| `optimization_engine/` | Recommendations from validation | Partial | G | Remove from main UI now; retain internal/future capability. |
| `broker/` | Modern Kite/mock adapters and streaming | Active | A/C | Canonical read-only broker/data layer; isolate mock and execution methods. |
| `broker_engine/` | Legacy reports/orders | Tests and mock adapter | Deprecate | Migrate unique DTO/report needs, then retire. Dependency verification required for mock adapter. |
| `execution_engine/` | Confirmation, lifecycle, placement | Endpoints/UI/tests | D/G | Extract lifecycle/simulation; retain only a disabled port/interface if useful. |
| `paper_trading/` | Paper portfolio domain | Pipeline/tests | D | Preserve for future separate app; remove production imports after extraction. |
| `workspace/` | Practice/trading mode guards | Active | C | Replace user modes with fixed read-only runtime profile; keep health/state concepts. |
| Python `dashboard/` | CLI/dictionary serializers | Bridge/tests | B/Deprecate | Retain serializers temporarily; React is canonical UI. Verify each bridge import before retirement. |
| React `frontend/` | User workstation | Active | C | Preserve components/styles; recompose pages around read-only information architecture. |
| `operations_engine/` | Readiness and service health | Active | B | Keep; add feed freshness/provenance checks. |
| `configuration_engine/` | Profiles/validation/export | Active | B | Canonical configuration management; simplify for one mode. |
| `config_engine/` | Global constants and YAML | Widely active | Deprecate | Replace with typed settings incrementally; cannot remove until broad import migration. |
| `strategies/` | Legacy plugin execution strategy | Scripts/legacy pipelines | Deprecate/G | Preserve unique `BreakoutTrendStrategy` behavior until verified, then adapt or archive. |
| `server_bridge.py` | Monolithic runtime/orchestration | Production-active | C | Incrementally reduce to compatibility entry point. Highest migration risk. |
| Express relay | REST, WS, state and credentials | Production-active | C | Make stateless transport; remove execution/mode endpoints and business state. |
| WebSocket state | Full snapshots and ticks | Production-active | B | Keep transport; add schema, sequence, heartbeat, provenance and staleness. |
| Local JSON persistence | Sessions, virtual portfolio | Active | C/D | Keep secure session adapter temporarily; extract virtual ledger. |
| SQLite caches | Instrument cache | Active | B | Keep with schema/version/freshness and atomic refresh. |
| Frontend local storage | Mode and UI preferences | Active | E/B | Remove business mode; keep visual preferences only. |
| Mock services | Defaults, journal, lifecycle | Production-visible | F/E | Fixtures/test-only; remove from production bundles and runtime paths. |
| Legacy CLI/scripts | Alternate entry paths | Not browser-active, imports legacy systems | Deprecate | Retain until dependency verification; archive or remove later. |

## Definitive grouping

### Keep as core

Models, indicators, options, trade context, scoring, opportunity, strategy suitability, deterministic explanations, intraday monitoring, canonical pipelines, read-only Kite connectivity and WebSocket delivery.

### Keep with small changes

Confidence, risk V2, decision-support rules, planner/report composition, operations, configuration engine, instrument cache and most React presentation components.

### Major refactor

Data ingestion/validation, news, historical intelligence, frontend state ownership, Express relay, workspace modes and `server_bridge.py`.

### Extract to future paper application

`paper_trading/`, virtual execution, mock broker transactional behavior, virtual portfolio, trading journal, browser order lifecycle, simulated-fill analytics and execution-oriented UI.

### Deprecate

`broker_engine/`, `risk_engine/`, `config_engine/`, `strategies/`, redundant old pipelines and legacy CLI/scripts after verified migration.

### Remove from user-facing product

Portfolio hub as a trading ledger, Execution workspace, Trading Journal, live-mode selector, quantity/order controls and optimization-as-trading UI.

### Remove from production runtime

Mock frontend data, hardcoded news/macro providers, root Kite mock fallback, mock broker selection, fake numeric defaults, execution endpoints and commands.

### Test-only

Synthetic market fixtures, mock broker, sample news, virtual fills and lifecycle fixtures.

### Future phase

OpenAI interpretation, external alerts, richer historical store, professional charts, option ladder, multi-broker support and any execution interface.

