# AIR ArdhaMind — Storage Usage & Retention Report

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Audit Standard**: Complete Storage Inventory Standard v1.0  
**Date**: August 2026  

---

## 1. Storage Size & File Count Breakdown

| STORAGE PATH | FILE COUNT | DISK SIZE | OLDEST FILE | NEWEST FILE | RETENTION TYPE | UNBOUNDED GROWTH RISK? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `.cache/` (Root Files) | 16 | 9.7 MB | `news_cache.json.pre_truth_repair_backup` (Aug 22) | `kite_nifty_option_snapshot.json` (Aug 22) | Latest / Fixed Horizon | **NO** |
| `.cache/pre_market_briefings/` | 5 | 160.0 KB | `PMB_2026-08-17.json` (Aug 22) | `PMB_2026-08-24.json` (Aug 21) | Permanent Historical | **LOW** (~30 KB / session) |
| `data/cache/` | 13 | 110.0 MB | `session_history_2026-08-15.json` (Aug 16) | `session_history_2026-08-22.json` (Aug 22) | Intraday Logs Archive | **HIGH** (~30 MB / session) |
| `data/post_market_briefings/` | 1 | 12.0 KB | `2026-08-20.json` (Aug 22) | `2026-08-20.json` (Aug 22) | Permanent Historical | **LOW** (~12 KB / session) |
| `data/performance_records/` | 5 | 1.4 MB | `2026-08-19.json` (Aug 19) | `2026-08-22.json` (Aug 22) | Permanent Historical | **MEDIUM** (~200 KB / session) |
| `data/proposals_audit.db` | 1 (SQLite) | 128.0 KB | Database Creation | Active Updates | Permanent Audit DB | **LOW** |
| **TOTAL** | **41 Files** | **~121.5 MB** | Aug 16, 2026 | Aug 22, 2026 | Mixed Retention | **MANAGED** |

---

## 2. Retention Policy Inventory by Dataset Family

1. **Broker Credentials (`.cache/session.json`)**:
   - Retention: 24 Hours TTL. Automatically invalidated upon explicit logout or token expiration.
2. **Runtime Snapshots (`.cache/*.json`)**:
   - Retention: Latest-only overwrite. Overwritten every 5s to 60s during active market session.
3. **Pre & Post-Market Briefing Archives (`data/*_briefings/`)**:
   - Retention: Permanent dated JSON archives. Provides historical lineage for next-session context.
4. **Performance Evaluation Records (`data/performance_records/`)**:
   - Retention: Permanent dated JSON archives. Enforces immutability check on prediction fields.
5. **Intraday Session History (`data/cache/session_history_{date}.json`)**:
   - Retention: Unbounded daily accumulation (~30 MB/day).
   - *Recommendation for future sprint*: Implement 30-day retention prune for intraday session history logs while preserving permanent briefing and performance records.
