# AIR ArdhaMind — Session Rollover & Carry-Forward Matrix

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Audit Standard**: Data Persistence & Rollover Audit v1.0  
**Date**: August 2026  

---

## 15:30 IST Session Finalization & Carry-Forward Mapping

| FIELD | ENDED SESSION VALUE | FINALIZATION SOURCE | PERSISTED? | IMMUTABLE? | OVERNIGHT ENRICHED? | NEXT SESSION INPUT? | OVERWRITE RISK | RESTART SAFE? | STATUS |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NIFTY Official Close** | 24,823.15 | NSE Official / 15:30 Ticker | **YES** (`data/post_market_briefings/{date}.json`) | **YES** | No | **YES** (Reference Close) | **LOW** | **YES** | **PASS** |
| **NIFTY Day Open/High/Low** | O: 24,750, H: 24,890, L: 24,710 | Kite Quote Intraday Summary | **YES** (`data/post_market_briefings/{date}.json`) | **YES** | No | **YES** (Prior Day Levels) | **LOW** | **YES** | **PASS** |
| **NIFTY VWAP & ATR** | 24,795.4 / 142.0 | `MarketContextBuilder` Calculation | **YES** (`data/post_market_briefings/{date}.json`) | **YES** | No | **YES** (Technical Baseline) | **LOW** | **YES** | **PASS** |
| **1-Min Candle Buffer** | 375 Intraday Candles | Kite Historical REST API | **YES** (`data/cache/nifty_candles_cache.json`) | **NO** (Overwritten next day) | No | **YES** (Intraday Context) | **MEDIUM** | **YES** | **WARNING** |
| **Final PCR & Max Pain** | PCR: 1.12, Max Pain: 24,800 | `MarketFeedService` Snapshot | **YES** (`data/post_market_briefings/{date}.json`) | **YES** | No | **YES** (Options Baseline) | **LOW** | **YES** | **PASS** |
| **Options Call/Put Walls** | Call: 25,000, Put: 24,500 | `MarketFeedService` Snapshot | **YES** (`data/post_market_briefings/{date}.json`) | **YES** | No | **YES** (Options Support/Resist) | **LOW** | **YES** | **PASS** |
| **Final Sector Breadth** | IT: +1.2%, Bank: -0.4% | `MarketContextBuilder` Sector Matrix | **YES** (`data/post_market_briefings/{date}.json`) | **YES** | No | **YES** (Sector Momentum) | **LOW** | **YES** | **PASS** |
| **India VIX Close** | 13.42 | Kite Quote / `KiteIntelligenceService` | **YES** (`.cache/kite_india_vix_snapshot.json`) | **NO** (Overwritten by next tick) | No | **YES** (Volatility Input) | **MEDIUM** | **YES** | **WARNING** |
| **FII / DII Net Flow** | FII: +₹1,240 Cr, DII: -₹420 Cr | NSE Evening Report | **YES** (`.cache/nse_participant_derivatives.json`) | **NO** (Mutated on arrival) | **YES** (Arrives ~18:30 IST) | **YES** (Institutional Bias) | **MEDIUM** | **YES** | **PASS** |
| **GIFT Nifty / Global Cues** | GIFT: 24,860, S&P: +0.4% | Yahoo Ingestion / Evening Fetch | **YES** (`.cache/gift_nifty_snapshot.json`) | **NO** (Continuously updated) | **YES** (Overnight Market) | **YES** (Opening Bias / Gap) | **LOW** | **YES** | **PASS** |
| **Overnight News Catalysts** | Eligible News Headlines | `FinancialNewsProvider` | **YES** (`.cache/news_cache.json`) | **NO** (Mutated array) | **YES** (Overnight Feed) | **YES** (News Context) | **LOW** | **YES** | **PASS** |
| **Session Intelligence Summary**| 15:20 IST Briefing Report | `PostMarketBriefingEngine` | **YES** (`data/post_market_briefings/{date}.json`) | **YES** | No | **YES** (Prior Day Narrative) | **NONE** | **YES** | **PASS** |
| **Portfolio Proposals State** | Validated / Expired Proposals | SQLite DB (`proposals_audit.db`) | **YES** (`data/proposals_audit.db`) | **YES** | No | **YES** (Portfolio State) | **LOW** | **YES** | **PASS** |
