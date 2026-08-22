# AIR ArdhaMind — Data Persistence Matrix

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Audit Standard**: Data Persistence & Rollover Audit v1.0  
**Date**: August 2026  

---

## Complete Storage Inventory & Mapping

| DATASET | PRODUCER | CURRENT STORAGE | PATH / TABLE | PERSISTENCE TYPE | WRITE TRIGGER | SESSION KEY | SURVIVES RESTART | RETENTION | NEXT-SESSION CONSUMER | REFETCHABLE | RISK | STATUS |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Broker Session** | `SessionManager` | Local JSON | `.cache/session.json` | Persistent Cache | OAuth Callback / Login | `access_token` / 24h TTL | **YES** | 24 Hours | Startup Re-auth | **NO** (Requires re-login) | Session Expiry | **PASS** |
| **NIFTY Spot & Quote** | `MarketFeedService` | In-Memory / Snapshot | `.cache/kite_nifty_option_snapshot.json` | Latest Snapshot | Option Chain Poll | `underlying_spot` | **PARTIAL** | Latest Only | Reference Close / Expected Open | **YES** | Overwritten by new day tick before freeze | **WARNING** |
| **1-Min Intraday Candles** | `MarketContextBuilder` | Local JSON Cache | `data/cache/nifty_candles_cache.json` | Rolling Buffer | 5-Min Poll | Timestamp ISO | **YES** (Last 375) | 1 Session (375 candles) | Historical Volatility / Levels | **YES** (Kite REST API) | Intraday gaps if disconnected | **PASS** |
| **Option Chain & OI** | `MarketFeedService` | Local JSON Snapshot | `.cache/kite_nifty_option_snapshot.json` | Latest Snapshot | 5-Sec Chain Poll | Expiry + Strike | **YES** (Latest) | Overwritten on tick | PCR / Max Pain / Call Wall / Put Wall | **PARTIAL** (Intraday OI delta lost) | Day-over-day OI change requires prior close OI | **WARNING** |
| **India VIX Quote** | `KiteIntelligenceService` | Local JSON Snapshot | `.cache/kite_india_vix_snapshot.json` | Latest Snapshot | 60-Sec Quote Poll | Observation TS | **YES** | Latest Only | Volatility Regime / Expected Range | **YES** | Refetchable during market open | **PASS** |
| **GIFT Nifty Quote** | `SpecializedDataProvider` | Local JSON Snapshot | `.cache/gift_nifty_snapshot.json` | Latest Snapshot | 60-Sec Fetch | Timestamp | **YES** | Latest Only | Expected Gap / Opening Bias | **YES** (Yahoo Ingestion) | Nightly rollover overwrite | **PASS** |
| **FII / DII Cash Flows** | `InstitutionalFlowProvider` | Local JSON Cache | `.cache/nse_participant_derivatives.json` | Mutated Cache | Evening Report Poll | Trade Date | **YES** | Latest Report | Institutional Bias / PRE Outlook | **YES** (NSE Report) | Evening update missing if network down | **WARNING** |
| **Financial News Stories** | `FinancialNewsProvider` | Local JSON Cache | `.cache/news_cache.json` | Mutated Array | 60-Sec News Poll | Story Hash / URL | **YES** | 100 Latest Stories | News Impact / Catalysts | **NO** (Provider stream is transient) | Dedupe state lost if cache deleted | **PASS** |
| **Economic Calendar** | `EconomicCalendarProvider` | Local JSON Cache | `.cache/economic_calendar_cache.json` | Mutated Cache | Daily Poll | Event Date + Time | **YES** | Weekly Window | Economic Reminders / Risk Summary | **YES** | Low risk | **PASS** |
| **Global Market Quotes** | `GlobalMarketProvider` | Local JSON Cache | `.cache/macro_cache.json` | Mutated Cache | 60-Sec Poll | Symbol Key | **YES** | Latest Only | Global Cues / Gap Direction | **YES** | High dependency on Yahoo API | **PASS** |
| **Pre-Market Briefing** | `PreMarketBriefingEngine` | Dated JSON File | `data/pre_market_briefings/PMB_{date}.json` | Immutable File | 08:45 IST Trigger | Trading Date (`YYYY-MM-DD`) | **YES** | Immutable History | Morning Plan / Evaluation | **NO** (Deterministic calculation) | None | **PASS** |
| **Post-Market Briefing** | `PostMarketBriefingEngine` | Dated JSON File | `data/post_market_briefings/{date}.json` | Immutable File | 15:20 IST & 15:30 Reconciliation | Trading Date (`YYYY-MM-DD`) | **YES** | Immutable History | Next PRE Outlook / Day Close | **NO** (Frozen session snapshot) | None | **PASS** |
| **Session History Log** | `PerformanceTrackerEngine` | Dated JSON File | `data/cache/session_history_{date}.json` | Immutable File | Intraday Cadence / Close | Trading Date (`YYYY-MM-DD`) | **YES** | Daily Archives | Intraday Playbook / Historical Analysis | **NO** | High reliance on clean 15:30 write | **PASS** |
| **Performance Evaluator** | `PerformanceTrackerEngine` | Dated JSON File | `data/performance_records/{date}.json` | Immutable File | Post-Close Eval | Trading Date (`YYYY-MM-DD`) | **YES** | Permanent | Prediction vs Reality Score | **NO** | None | **PASS** |
| **Portfolio Proposals** | `PortfolioManager` | SQLite DB | `data/proposals_audit.db` | Relational Table | Proposal Creation / Expiry | Proposal UUID | **YES** | Permanent | Proposal Status / Audit Trail | **NO** | Invalidation state in memory | **WARNING** |
