# AIR ArdhaMind — Persistence Blockers & Architectural Risks

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Audit Standard**: Data Persistence & Rollover Audit v1.0  
**Date**: August 2026  

---

## Classified Architectural Blockers & Risks

### P0 — CRITICAL DATA LOSS & CORRUPTION RISKS
1. **Un-Atomic Session History Writes**:
   - `data/cache/session_history_{date}.json` accumulates intraday logs and snapshots directly without guaranteed atomic temp-file replace during active trading.
   - *Impact*: Process crash or sudden kill during market close write leaves zero-byte or corrupted session history file.

2. **Transient Inversion of Initial Market State**:
   - `WorkstationStateService` initializes with empty fallback context before first WebSocket snapshot arrives.
   - *Impact*: UI briefly renders empty or default values on startup until initial WebSocket state packet is parsed.

---

### P1 — REQUIRED NEXT-SESSION INPUT NOT DURABLY STORED
1. **Intraday OI Delta Reference Loss**:
   - Option chain open interest changes (`change_in_oi`) depend on live intraday ticks or `.cache/kite_nifty_option_snapshot.json`.
   - If daemon restarts overnight, day-over-day OI baseline relies on provider refetch because prior-day final chain snapshot is not stored in a dedicated daily options database.
   - *Impact*: Next morning PRE option analysis depends on external provider refetch instead of frozen prior-day close OI table.

2. **Weekend FII/DII Evening Overwrite Risk**:
   - `.cache/nse_participant_derivatives.json` stores only the latest institutional flow report.
   - *Impact*: Multi-day historical institutional flow trend must be refetched from NSE website if local cache is reset.

---

### P2 — OVERWRITE & RESTART INCONSISTENCY RISKS
1. **Overnight Option Snapshot Overwrite**:
   - `.cache/kite_nifty_option_snapshot.json` stores `underlying_spot` and option chain.
   - *Impact*: Weekend pre-market state could overwrite Friday's market-close options snapshot if an off-hours poll runs with empty quotes.

2. **Deduplication State Memory Binding**:
   - News deduplication hash map resides in memory inside `FinancialNewsProvider`.
   - *Impact*: Process restart forces re-evaluation of news items from `.cache/news_cache.json`, potentially re-triggering news impact calculation.

---

### P3 — INEFFICIENT PERSISTENCE & REFETCH
1. **Monolithic Cache Files**:
   - `macro_cache.json` (4.0 MB) and `news_cache.json` (1.5 MB) are rewritten completely on every poll cycle.
   - *Impact*: Unnecessary disk I/O overhead on SSD storage.

---

### P4 — OBSERVABILITY & DOCUMENTATION GAPS
1. **Missing Data Retention Policy Execution**:
   - Historical `session_history_{date}.json` files accumulate indefinitely in `data/cache/` (e.g. `29 MB` for 2026-08-18).
   - *Impact*: Disk space growth over long-term operations without automated pruning.
