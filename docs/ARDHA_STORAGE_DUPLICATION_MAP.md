# AIR ArdhaMind — Storage Duplication Map

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Audit Standard**: Complete Storage Inventory Standard v1.0  
**Date**: August 2026  

---

## 1. Storage Duplication Analysis

| LOGICAL DATASET | PRIMARY SOURCE | DERIVED COPIES | DUPLICATION CLASSIFICATION | RATIONALE / IMPACT |
| :--- | :--- | :--- | :--- | :--- |
| **NIFTY Official Close** | `data/post_market_briefings/{date}.json` | 1. `data/cache/session_history_{date}.json`<br>2. `.cache/kite_nifty_option_snapshot.json`<br>3. `data/performance_records/{date}.json` | **NECESSARY DERIVED COPY** | Session briefing is the canonical post-market record; option snapshot holds underlying spot for chain calculations; performance record holds evaluated actual value. |
| **Put / Call Ratio (PCR)** | `.cache/kite_nifty_option_snapshot.json` | 1. `data/post_market_briefings/{date}.json`<br>2. `data/cache/session_history_{date}.json`<br>3. `.cache/pre_market_briefings/PMB_{date}.json` | **NECESSARY DERIVED COPY** | Live chain is the active source; post-market briefing freezes end-of-day PCR; pre-market briefing carries PCR forward as baseline. |
| **Max Pain & Option Walls** | `.cache/kite_nifty_option_snapshot.json` | 1. `data/post_market_briefings/{date}.json`<br>2. `data/cache/session_history_{date}.json` | **NECESSARY DERIVED COPY** | Option snapshot is live runtime source; post-market briefing freezes levels for next-session context. |
| **FII / DII Net Cash Flows** | `.cache/nse_participant_derivatives.json` | 1. `data/post_market_briefings/{date}.json`<br>2. `.cache/pre_market_briefings/PMB_{date}.json` | **NECESSARY DERIVED COPY** | FII cache holds latest raw report from NSE; briefings freeze institutional sentiment for historical reference. |
| **India VIX Value** | `.cache/kite_india_vix_snapshot.json` | 1. `data/post_market_briefings/{date}.json`<br>2. `data/cache/session_history_{date}.json` | **NECESSARY DERIVED COPY** | VIX snapshot is live source; briefing freezes volatility regime for performance evaluation. |
| **Financial News Items** | `.cache/news_cache.json` | 1. `data/cache/session_history_{date}.json`<br>2. `.cache/news_cache.json.pre_truth_repair_backup` | **UNNECESSARY DUPLICATION** | Backup file `news_cache.json.pre_truth_repair_backup` (1.6 MB) is a legacy audit artifact that duplicates active news cache. |
| **Session History Files** | `data/cache/session_history_{date}.json` | 1. `.cache/test_session.json` | **UNNECESSARY DUPLICATION** | `.cache/test_session.json` is a leftover test isolation artifact. |
