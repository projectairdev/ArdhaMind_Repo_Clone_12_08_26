# Existing Product Versus Target

## Confirmed current runtime

The production entry path is React -> Express/WebSocket -> Python daemon. `server.ts:startPythonDaemon` starts `src/server_bridge.py --action daemon` with `PYTHONPATH=.`. `WorkstationStateContext.tsx` consumes `state` and `tick` messages. `server_bridge.py:generate_dynamic_workspace_data` directly assembles much of the workstation report.

| Original requirement | Intended behaviour | Current implementation | Status | Main issue / product impact | Disposition |
|---|---|---|---|---|---|
| Sample mode | Fake demonstration environment | No clean isolated sample product; mock values exist in frontend defaults/providers | Drifted | Fake values can resemble real state | Remove from user product; fixtures test-only |
| Mock mode | Live data plus simulated execution | `LIVE_PRACTICE`, mock gateway, virtual execution, paper ledger and UI mocks | Implemented but fragmented | Data and portfolio provenance are unclear | Extract paper capability |
| Real mode | Live data and live broker execution | `LIVE_TRADING` mode and endpoints exist; Kite order methods raise `NotImplementedError` | Partial/unsafe concept | UI promises capability the adapter cannot safely provide | Remove user mode; retain disabled interface only |
| Live market analysis | Real-time operator assistance | Kite REST/WebSocket and market builders exist | Partial | Bridge bypass and freshness gaps undermine trust | Keep and strengthen |
| NIFTY spot analysis | Technical analysis of real NIFTY | Market context, indicators, VIX and support/resistance | Implemented/partial runtime | Default context values and incomplete provenance | Core |
| NIFTY options analysis | Real chain intelligence | OI/PCR/max pain/IV/liquidity/ranking engines | Implemented/partial data | Missing full quote guarantees and Greeks | Core |
| Market scoring | Deterministic composite score | `MarketScoreBuilder` and scoring pipeline | Implemented | Live bridge may assemble surrounding context manually | Core |
| Opportunity detection | Identify viable conditions | `OpportunityContextBuilder` | Implemented | Threshold calibration and freshness dependency | Core |
| Strategy suitability | Compare strategy families | `strategy_engine/` plus legacy `strategies/` | Duplicate | Two meanings: suitability versus executable strategy plugin | Keep canonical suitability; deprecate legacy after mapping |
| Confidence | Quantify confluence | `confidence_engine/` | Implemented | Empirical calibration and runtime canonical use incomplete | Core with changes |
| Risk | Deterministic safety analysis | `risk_engine_v2/` plus legacy risk | Duplicate | Portfolio/execution assumptions remain | Keep scenario risk; migrate legacy |
| Trade planning | Entry/target/stop scenarios | Planner engine and bridge-generated candidates | Partial | Can look executable and may use synthesized inputs | Convert to read-only scenarios |
| Explanations | AI explains signals | Deterministic templates; Gemini label/dependency without active inference | Pseudo-AI | Product overstates AI | Keep fallback; future bounded OpenAI |
| News intelligence | Current event context | Google News RSS plus hardcoded provider records | Mixed | Static articles can appear current | Refactor; static providers test-only |
| Broker connectivity | Real Kite connectivity | Modern broker gateway reads account/data | Partial | Root shim can replace official package with mocks | Core read-only after isolation |
| Paper trading | Simulated execution | Two Python paper systems plus browser mocks | Implemented/fragmented | Dominates product state despite revised scope | Extract |
| Portfolio | Track real/paper positions | Broker portfolio and virtual positions coexist | Partial | Conflates decision support with account management | Keep minimal read-only broker context; extract ledger |
| Journal | Record trades | `TradingJournal.tsx` imports `mockTradeJournal` | Mock-only | Static content appears functional | Extract/remove from product |
| Live execution | Manual-confirmed broker orders | Express endpoints and execution UI exist; adapter is unimplemented | Incomplete | Dangerous surface and false expectation | Remove runtime/UI; disabled interface future-only |
| Dashboard | Unified workstation | Broad React dashboard with 11 tabs | Implemented | Organized around old execution/paper vision | Recompose information architecture |
| Alerts | Notify operator | Inline warning banners and state indicators | Partial | No authoritative alert event model or delivery | Keep in-app; strengthen |
| Scheduler | Continuous refresh | Daemon loops and five-minute news cache | Basic | Scheduling coupled to bridge and not observable | Major refactor |
| AI integration | AI-powered assistant | No active OpenAI/Gemini call found | Placeholder | UI “Gemini” label misrepresents capability | Future bounded service |
| Pre-market analysis | Prepare session | Tomorrow/evening planner | Partial | Inputs/provenance and naming are unclear | Keep as briefing |
| Intraday monitoring | Monitor scenario changes | Intraday engine and dashboard | Implemented/partial | Depends on trustworthy current state | Core |
| Historical analysis | Validate and learn | Validation and analytics engines | Partial | Limited persistent historical intelligence | Major refactor |
| End-of-day review | Summarize session | Evening/analytics reports | Partial | Often tied to paper trades | Retain market intelligence; extract trade P&L |

## Product drift

The application stopped near Phase 1 but accumulated Phase 2/3 concepts—quantity, confirmation, execution, portfolio and order lifecycle—before the underlying live data and canonical state were trustworthy. Consequently, UI completeness outpaced source provenance. “Live practice” simultaneously means live market data, paper execution and sometimes mock broker state; “live trading” exists as a user choice even though its central order methods are deliberately absent.

## Confirmed active versus dormant

- **Production-active:** Express/Python daemon, WebSocket context, modern `broker/`, market/option builders, selected scoring/opportunity/strategy builders, Google News pipeline, React dashboard.
- **Production-active mock:** Trading journal; browser-local order lifecycle if invoked; frontend default contexts until live packets arrive; hardcoded provider news through `NewsPipeline`.
- **Partially active:** canonical pipelines, analytics derived from virtual ledger, workspace mode manager.
- **Legacy:** `broker_engine/`, `risk_engine/`, `config_engine/`, `strategies/`, older pipeline/scripts—still imported and therefore not dead.
- **Disabled/incomplete:** real Kite order methods.
- **Test-only intent but not isolation:** root `kiteconnect.py` and mock broker adapter can be selected outside tests.

## Confusion map

| User sees | Actual source | Why confusing | Required correction |
|---|---|---|---|
| LIVE PRACTICE | Browser local storage, Express memory and Python workspace mode | “Live” refers to data while execution is paper; three owners can disagree | Single fixed `LIVE_INTELLIGENCE_READ_ONLY` product state |
| Live option signal | Cached Kite chain mixed with bridge candidate synthesis/default React contexts | Same visual treatment lacks per-field source/age | Canonical pipeline plus provenance; unavailable when incomplete |
| Broker connected | REST/session state and streamed portfolio health can diverge | Session validity does not guarantee fresh market feed | Separate session, feed and analysis health |
| Market score | Canonical builder over a bridge-assembled context | Score looks authoritative even if dependencies were synthesized | Dependency-quality propagation and hard blocks |
| News intelligence | Hardcoded `GoogleNewsProvider`/macro records through `NewsPipeline` | Publisher names and dates resemble live collection | Real provider only; fixtures test-only |
| Gemini AI rationale | Deterministic templates; no active model invocation | Branding implies an LLM-generated assessment | Label deterministic explanation; show AI unavailable |
| Portfolio | Broker and virtual execution sources | Operator cannot reliably infer real versus simulated holdings | Product keeps read-only broker context only; extract virtual ledger |
| Trading journal | Static `mockTradeJournal` | Fully rendered page implies recorded history | Remove/extract page until real intelligence history exists |
| Execution workspace | Active buttons call Express endpoints | UI implies supported execution despite adapter rejection | Remove controls and reject endpoints |
| Historical performance | Analytics may be built from virtual trades with synthetic classifications | Metrics appear to describe live decisions | Separate intelligence history from paper P&L analytics |

