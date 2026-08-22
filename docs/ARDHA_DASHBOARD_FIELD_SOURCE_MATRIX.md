# AIR Ardha Staging — Dashboard Field Source & Ingestion Matrix

**Environment:** Staging (`staging.ardhamind.projectair.in`)  
**Audit Date:** August 2026  
**Scope:** Complete cross-layer data provenance mapping from upstream external APIs down to canonical workstation state and UI presentation.

---

## 1. UPSTREAM DATA PROVIDERS & INGESTION PROTOCOLS

| Provider ID | Provider Name | Upstream API Protocol | Ingestion Service in Ardha | Ingestion Cadence | Primary Canonical State Path |
|:---|:---|:---|:---|:---|:---|
| `PROV_ZERODHA_TICKER` | Zerodha Kite Connect WebSocket | Binary WebSocket (KiteTicker) | `src/market_feed.py` / `gateway.py` | Real-time binary ticks (1s batch) | `workstationState.ticks["NIFTY 50"]` |
| `PROV_ZERODHA_REST` | Zerodha Kite Connect REST v3 | HTTPS REST (OAuth Session) | `src/broker_gateway.py` | 5s polling / event-driven | `workstationState.broker_status`, `phase3` |
| `PROV_NSE_BREADTH` | NSE India Web Telemetry | HTTPS REST / Scraping | `src/ingestion/breadth_feed.py` | 15s polling | `workstationState.market_score.breadth` |
| `PROV_NSE_OPTIONS` | NSE Option Chain Stream | HTTPS JSON / Kite NFO Instruments | `src/option_feed.py` | 5s polling | `workstationState.option_intelligence` |
| `PROV_GLOBAL_MACRO` | Yahoo Finance / AlphaVantage / FX | HTTPS REST | `src/macro_feed.py` | 10s polling / 60s fallback | `workstationState.macro_intelligence` |
| `PROV_NEWS_PUBLIC` | Reuters / Bloomberg / Moneycontrol | HTTPS RSS & News Feeds | `src/news_feed.py` | 30s ingest cycle | `workstationState.news_intelligence` |
| `PROV_OFFICIAL_POLICY` | RBI / SEBI / PIB Official Portals | HTTPS Feed Scraper | `src/news_feed.py` / `macro_feed.py` | 60s ingest cycle | `macro_intelligence.official_india_events` |
| `PROV_INST_FLOWS` | NSE / NSDL Provisional Reports | HTTPS EOD Reports | `src/macro_feed.py` | Daily at 18:30 IST | `macro_intelligence.institutional_flows` |
| `PROV_AI_ASSISTANT` | OpenAI GPT-4o / Local Fast Engine | HTTPS REST (Stream/JSON) | `src/live_assistant/server.py` | On-demand user query | `live_assistant_temporal_state` |

---

## 2. CANONICAL STATE OBJECT MAP & UPDATE CADENCES

| State Key | Canonical Type | Production / Staging Source Module | Typical Update Cadence | Downstream Visual Workspaces |
|:---|:---|:---|:---|:---|
| `ticks["NIFTY 50"]` | `TickData` (Spot, Change, High, Low) | `src/server_bridge.py` | 1 second continuous stream | Market: Nifty, Metrics, Options, TopBar |
| `market_score` | `MarketScore` (Regime, Momentum, Breadth) | `src/scoring_engine.py` | 5-15 seconds | Market: Metrics, Nifty, Intelligence |
| `option_intelligence` | `OptionIntelligence` (Chain, PCR, Walls, Skew) | `src/option_analyzer.py` | 5 seconds | Market: Options, Nifty, Intelligence |
| `macro_intelligence` | `MacroIntelligence` (Cues, Flows, Calendar) | `src/macro_analyzer.py` | 10 seconds (Global) / EOD (Flows) | Market: Nifty, Metrics, News: Calendar |
| `news_intelligence` | `NewsIntelligence` (Stories, Drivers, Risks) | `src/news_analyzer.py` | 30 seconds continuous | News: Live News, Catalysts, TopBar |
| `pre_market_briefing` | `PreMarketBriefing` (Thesis, Scenarios, Watch) | `src/briefing_engine.py` | 08:30 & 09:08 IST Frozen | Market: Nifty (PRE), Intelligence (Morning) |
| `post_market_briefing` | `PostMarketBriefing` (Close, Review, Drivers) | `src/post_market_engine.py` | 15:35 IST Frozen | Market: Nifty (POST), Intelligence (Tomorrow) |
| `opportunity` | `OpportunityContext` (Active trade proposal) | `src/opportunity_detector.py` | Continuous / 8s poll | Portfolio, Intelligence (Live Guide) |
| `phase3` | `Phase3State` (Positions, Orders, Journal) | `src/phase3/` state machine | 5s polling / WS broadcast | Portfolio Workspace, TopBar |
| `workspace_readiness` | `WorkspaceReadiness` (Diagnostics) | `server.ts` health checker | 5 seconds | Settings: Connections, Diagnostics |

---

## 3. UI PRESENTATION ADAPTERS & NORMALIZERS

| Surface | Presentation Adapter File | Responsibility |
|:---|:---|:---|
| Global Shell & Session | `src/frontend/utils/sessionResolver.ts` | Resolves pre/live/post session phase, market open timers, and IST time formatting |
| NIFTY Live & Metrics | `src/frontend/utils/safeHelpers.ts` | Indian numerical formatting (`formatNumber`, `formatOiLakh`), safe delta calculations |
| Options Chain & Greeks | `src/frontend/components/OptionsWorkspace.tsx` | Fallback zero suppression, strike distance math, Greeks "UNAVAILABLE" badge handling |
| News & Catalysts | `src/frontend/utils/canonicalNewsAdapter.ts` | Direction scoring, publisher attribution, timeline merging, impact categorization |
| Settings & Diagnostics | `src/frontend/utils/canonicalSettingsAdapter.ts` | LocalStorage preferences persistence, component readiness normalization |
| Intelligence Views | `src/frontend/components/intelligence/` | View model adapters (`vm`) mapping canonical state snapshots to structured view cards |
| Live Assistant | `src/frontend/components/LiveAssistantPanel.tsx` | Markdown rendering, grounding badge synthesis, intent/evidence metadata extraction |

---

## 4. FAILURE MODES & FALLBACK BEHAVIORS

| Failure Scenario | Affected Data Fields | Graceful Degradation Behavior |
|:---|:---|:---|
| **Broker Disconnected / Token Expired** | Live ticks, Open positions, Active orders | Workstation displays amber `AUTH_REQUIRED` badge in TopBar and Portfolio; falls back to `lastValidState` snapshot; trade execution controls are hard-locked. |
| **Market Closed (Off-Hours / Weekend)** | Real-time spot stream, Intraday candles | Session resolver engages PRE or POST mode; spot displays last official closing price; banners clearly indicate `MARKET CLOSED`. |
| **NSE Breadth Ingestion Lag** | Advances, Declines, A/D ratio, 52W Highs/Lows | Displays last valid breadth count; if 52W high/low is unpopulated, renders explicit `"UNAVAILABLE"` rather than dummy zeroes. |
| **Option Greeks Calculation Missing** | Delta, Gamma, Theta, Vega in Options Inspector | Displays clean `"UNAVAILABLE"` badge with informative tooltip explaining missing canonical volatility input without fabricating zeroes. |
| **Macro Cross-Asset API Timeout** | Cross-asset prices, Sparklines | Retains previous cached price with neutral flat sparkline; status shows `"STALE_CACHED"`. |
| **Live Assistant Offline / Engine Exception** | Assistant conversational response | Catch handler dispatches grounded fallback response citing active canonical session context and directing trader to primary workspace panels. |
