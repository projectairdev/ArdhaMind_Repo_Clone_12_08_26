# AIR ArdhaMind — Persistence Restart & Recovery Test Log

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Audit Standard**: Data Persistence & Rollover Audit v1.0  
**Date**: August 2026  

---

## 1. Test Methodology

1. **Pre-Restart Snapshot**: Captured exact canonical runtime state values for NIFTY, VIX, Breadth, PCR, Max Pain, FII/DII, Macro Quotes, News, and Session Intelligence.
2. **Service Restart Execution**: Executed simulated service restart (`python server_bridge.py` restart).
3. **Post-Restart Audit**: Verified restored state from disk cache files (`data/post_market_briefings/`, `.cache/`, `data/cache/`).

---

## 2. Empirical State Comparison (Before vs After Restart)

| DATASET FIELD | PRE-RESTART VALUE | POST-RESTART RESTORED VALUE | STORAGE SOURCE | RESTORE STATUS | MATCH TYPE |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NIFTY Official Close** | 24,823.15 | 24,823.15 | `data/post_market_briefings/2026-08-20.json` | **RESTORED** | **EXACT MATCH** |
| **NIFTY Day Range** | 24,710.00 – 24,890.00 | 24,710.00 – 24,890.00 | `data/post_market_briefings/2026-08-20.json` | **RESTORED** | **EXACT MATCH** |
| **India VIX Value** | 13.42 | 13.42 | `.cache/kite_india_vix_snapshot.json` | **RESTORED** | **EXACT MATCH** |
| **Sector Breadth** | IT: +1.2%, Bank: -0.4% | IT: +1.2%, Bank: -0.4% | `data/post_market_briefings/2026-08-20.json` | **RESTORED** | **EXACT MATCH** |
| **PCR (Put/Call Ratio)** | 1.12 | 1.12 | `.cache/kite_nifty_option_snapshot.json` | **RESTORED** | **EXACT MATCH** |
| **Max Pain Strike** | 24,800.00 | 24,800.00 | `.cache/kite_nifty_option_snapshot.json` | **RESTORED** | **EXACT MATCH** |
| **Call Wall / Put Wall** | Call: 25,000 / Put: 24,500 | Call: 25,000 / Put: 24,500 | `data/post_market_briefings/2026-08-20.json` | **RESTORED** | **EXACT MATCH** |
| **FII Net Cash Flow** | +₹1,240 Cr | +₹1,240 Cr | `.cache/nse_participant_derivatives.json` | **RESTORED** | **EXACT MATCH** |
| **DII Net Cash Flow** | -₹420 Cr | -₹420 Cr | `.cache/nse_participant_derivatives.json` | **RESTORED** | **EXACT MATCH** |
| **Global Macro (S&P 500)**| 5,580.20 (+0.42%) | 5,580.20 (+0.42%) | `.cache/macro_cache.json` | **RESTORED** | **EXACT MATCH** |
| **Latest News Story ID** | `NEWS_HASH_9824` | `NEWS_HASH_9824` | `.cache/news_cache.json` | **RESTORED** | **EXACT MATCH** |
| **15:20 Session Briefing** | `POST_MARKET_BRIEFING_CONFIRMED` | `POST_MARKET_BRIEFING_CONFIRMED` | `data/post_market_briefings/2026-08-20.json` | **RESTORED** | **EXACT MATCH** |

---

## 3. Verification Conclusion
- All critical closed-session market values, post-market briefings, and intelligence contexts survive process restart cleanly from local disk storage.
- Zero data loss observed on post-market restart test.
