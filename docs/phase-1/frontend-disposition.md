# Phase 1 Frontend Disposition

| Existing surface | Current dependency | Disposition |
|---|---|---|
| `DashboardLayout` | All eleven legacy pages, workspace modes, portfolio metrics | Replace shell; retain responsive sidebar/theme language |
| `HomeDashboard` | Central workstation context | Merge useful overview into NIFTY Live |
| `ExecutiveSummary` | Market, opportunity and decision context | Reuse in NIFTY Live overview |
| `MarketOverview` | Market and option context | Reuse under Price & Trend / Options |
| `MarketScoring` | Market score context | Reuse in NIFTY Live overview |
| `TomorrowWorkspace` | Evening report context | Rename/repurpose as Pre-Market Planner |
| `MarketStory` | Market/news context | Repurpose as Today’s Analysis |
| `NewsIntelligence` | WebSocket news context | Reuse in NEWS & UPDATES |
| `IntradayAssistant` | Intraday report | Reuse in Live Assistant |
| `DecisionEngine` | Decision report | Reuse in Live Assistant as decision support |
| `BrokerIntegration` | Broker REST/context | Move into Settings / Kite |
| `SystemReadinessReport` | Central health context | Move into Settings / Diagnostics |
| `OperationsManager` | Operations/context | Move into Settings / Diagnostics |
| `ConfigurationManager` | Config and panel toggles | Retain later; legacy panel controls do not fit final shell |
| `TradeCenter` | Scenario plus execution-oriented presentation | Disconnect; reusable analysis already exposed elsewhere |
| `LivePortfolio` | Broker and virtual positions | Disconnect; paper/portfolio product only |
| `ExecutionWorkspace` | Order and exit REST actions | Disconnect and remove from build |
| `PerformanceAnalytics` | Trade/paper analytics | Disconnect; future intelligence-history redesign |
| `HistoricalValidation` | Validation report | Retain for later Historical Intelligence integration |
| `OptimizationAdvisor` | Optimization report | Disconnect from Phase 1 UI |
| `TradingJournal` | Direct `mockTradeJournal` import | Disconnect; shell repurposed as a new Live Assistant, not this component |
| `workspace.ts` | Practice/trading mode and localStorage | Remove from user shell; backend compatibility remains temporarily |
| `mockData.ts` | Static fixtures/default reports | Must not enter active production import graph; retain temporarily for test/reference |
| `order_lifecycle.ts` | Browser-local simulated order state | Disconnect; future paper application |

The frontend uses stateful tab rendering rather than a router. Obsolete tab IDs will be normalized to `nifty-live`; `/broker` and login callback paths will open Settings. No legacy execution tab remains reachable from the product shell.

