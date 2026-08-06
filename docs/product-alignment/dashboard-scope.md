# Dashboard Information Architecture

## Target workspaces

| Target workspace | Existing sources/components | Disposition | Required real-data additions |
|---|---|---|---|
| Market Command Center | `HomeDashboard`, `ExecutiveSummary`, `MarketScoring`, selected `MarketStory` | Merge/retain | Source, age, feed health, blocked-stage reasons, deterministic/AI narrative label |
| NIFTY Price and Trend | `MarketOverview`, parts of `IntradayAssistant` | Retain | Candlestick/time-series data, timeframe timestamp, indicator provenance |
| Option-Chain Intelligence | `TradeCenter`, option sections in `MarketOverview` | Recompose | Full chain table/ladder, per-contract quote time, OI/volume/IV quality, expiry coverage |
| Trade Assistant | `TradeCenter`, `DecisionEngine`, `ExecutiveSummary` | Retain as scenarios | Confirmation/invalidation, scenario lifecycle, no quantity or execute action |
| Market Intelligence and News | `MarketStory`, `NewsIntelligence` | Merge | Real provider/source links, fetch time, dedup and news-unavailable state |
| Intraday Assistant | `IntradayAssistant` | Retain | Canonical scenario reference, observation age, changed-dependency explanation |
| Historical Intelligence | `PerformanceAnalytics`, `HistoricalValidation`, parts of `TomorrowWorkspace` | Major refactor | Persisted market/scenario snapshots; exclude virtual P&L |
| System Health and Provenance | `SystemReadinessReport`, `OperationsManager` | Merge/strengthen | Per-source latency, freshness, last good state, pipeline-stage status |
| Settings and Broker | `ConfigurationManager`, `BrokerIntegration` | Merge | Read-only scope, session/feed permissions, no mode/live-trading toggle |

## Existing page disposition

| Existing page/component | Current purpose/source | Final disposition |
|---|---|---|
| Dashboard / `HomeDashboard` | Aggregated WebSocket context | Keep as Market Command Center |
| Market / `MarketOverview` | Market and option context | Keep, split price and option intelligence clearly |
| `MarketScoring` | Score report | Keep in Command Center with dependency quality |
| Trade Center / `TradeCenter` | Candidates and Gemini-branded rationale | Keep as read-only Trade Assistant; remove execution/quantity language |
| Portfolio / `LivePortfolio` | Broker and virtual funds/positions | Remove as primary workspace; optionally expose minimal read-only account health under Broker |
| Execution / `ExecutionWorkspace` | Place and exit operations | Remove from AIR ArdhaMind; extract to future paper app |
| Tomorrow / `TomorrowWorkspace` | Evening planner | Keep as pre-market/next-session briefing in Historical Intelligence |
| Market Story / `MarketStory` | Narrative plus news | Merge into Market Intelligence and Command Center |
| Performance / `PerformanceAnalytics` | Virtual trade performance | Extract trade analytics; redesign for intelligence history |
| `HistoricalValidation` | Historical engine outcomes | Keep as advanced Historical Intelligence after provenance work |
| `OptimizationAdvisor` | Weight/threshold advice | Remove from Phase 1 UI; internal/future only |
| Trading Journal | Static mock journal | Extract/remove immediately from final user navigation |
| System Settings | Themes, operations and config | Keep; simplify to read-only configuration and health |
| Broker Account | Login/profile | Keep read-only connection workspace |
| `DecisionEngine` | Decision report | Merge into Trade Assistant as Decision Support |
| `NewsIntelligence` | WebSocket news | Keep within Market Intelligence after real-provider isolation |

## Duplicated and misleading UI

- Market summaries repeat across `HomeDashboard`, `ExecutiveSummary`, `MarketOverview`, `MarketStory` and `TradeCenter`.
- Broker connection state appears in header, home, portfolio, execution and account with different semantics.
- Trade scenarios, decisions and execution controls are visually adjacent, suggesting an executable recommendation.
- Portfolio, journal and performance pages belong to the simulation product.
- `TradingJournal` is confirmed mock-only through its direct `mockTradeJournal` import.
- “Gemini AI Rationale” must not be shown unless an actual audited AI response exists.

## Missing presentation capability

- Professional NIFTY candlestick/timeframe charts
- Option ladder/chain with synchronized CE/PE rows
- OI and change-in-OI visualization
- IV skew/term view
- Explicit source/freshness chips
- Stage dependency/blocking panel
- Historical intelligence timeline

This review defines information architecture only; it does not prescribe a visual redesign.

