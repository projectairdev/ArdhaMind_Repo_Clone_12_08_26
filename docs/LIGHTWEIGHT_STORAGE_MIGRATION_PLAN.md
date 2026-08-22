# LIGHTWEIGHT STORAGE MIGRATION PLAN & IMPLEMENTATION ROADMAP

**Document Version:** 1.0.0 — Authoritative Staging Migration Plan  
**Target Subsystems:** `src/storage/`, `src/intelligence_engine/`, `src/application/`  
**Execution Constraint:** Staging Only. Dual-write validation required prior to legacy deprecation.

---

## 1. READER-BY-READER MIGRATION MATRIX

| Consumer Module | Current Read Path | New Lightweight Read Path | Compatibility Fallback | Decommission Threshold |
|:---|:---|:---|:---|:---|
| **`PerformanceTrackerEngine`** ([`src/intelligence_engine/performance_tracker_engine.py`](file:///opt/ardhamind/staging/src/intelligence_engine/performance_tracker_engine.py#L770)) | `CACHE_DIR / f"session_history_{date}.json"` $\rightarrow$ `s_hist["actual_session"]` | `LightweightSessionStore.load_session_close(date)` $\rightarrow$ `close_core.market_ohlcv` | Falls back to legacy `session_history_{date}.json` if Close Core missing | Phase 6 (after 1 successful live trading session) |
| **`LiveAssistantEngine`** ([`src/intelligence_engine/live_assistant_engine.py`](file:///opt/ardhamind/staging/src/intelligence_engine/live_assistant_engine.py#L143)) | Scans `session_history_*.json` for full historical dumps $\rightarrow$ parses 800+ raw snapshots | `LightweightSessionStore.load_telemetry_series(date)` $\rightarrow$ reads 25 pre-bucketed 15m summaries | Falls back to scanning legacy `session_history_*.json` if telemetry missing | Phase 6 (after 1 successful live trading session) |
| **`WorkstationStateService`** ([`src/application/workstation_state_service.py`](file:///opt/ardhamind/staging/src/application/workstation_state_service.py#L57)) | Reads `session_history_{date}.json` $\rightarrow$ `snapshots[-1]` to restore sequence | `LightweightSessionStore.load_recovery_state()` $\rightarrow$ reads `cache/latest_canonical_state.json` | Falls back to `session_history_*.json` if recovery snapshot missing | Phase 6 (after 1 successful live trading session) |

---

## 2. STAGED IMPLEMENTATION PHASES

```
┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
│ PHASE A │ ──►  │ PHASE B │ ──►  │ PHASE C │ ──►  │ PHASE D │ ──►  │ PHASE E │ ──►  │ PHASE F │
└─────────┘      └─────────┘      └─────────┘      └─────────┘      └─────────┘      └─────────┘
  Atomic           Candle /         EOD Close        Reader           Dual-Write       Live Session
  Storage          Telemetry        & Options        Migration        Validation       Verification
  Primitives       Writers          Finalizer        (3 Readers)      (Zero Regress)   & Cutover
```

### Phase A: Core Schemas & Storage Primitives
- Create `src/storage/lightweight_session_store.py` with atomic write helpers and schema dataclasses.
- Setup directory tree: `data/session_store/{close,options_close,telemetry,integrity,connectivity,cache}/`.
- Unit test atomic file replacement, corruption handling, and directory creation.

### Phase B: Real-Time Writers & Ring Buffers
- Implement `RollingCandleCache` (5-day 5-minute candle buffer in `data/session_store/cache/nifty_5m_candles.json`).
- Implement 15-minute `IntradayTelemetrySeries` writer hooked into WorkstationStateService timer.
- Implement line-delimited `ConnectivityEvent` logger.

### Phase C: Session Close & Options Finalizer
- Implement `SessionLifecycleManager` with 15:20 pre-close capture, 15:35 reconciliation, and EOD enrichment.
- Implement `recover_missed_close()` for daemon cold-start post-15:30.
- Implement duplicate finalization protection with idempotency keys.

### Phase D: Reader Migration
- Update `PerformanceTrackerEngine`, `LiveAssistantEngine`, and `WorkstationStateService` to read from `LightweightSessionStore` with automatic fallback to legacy files.

### Phase E: Dual-Write & Shadow Validation
- Run storage engine in dual-write mode: writes both lightweight structures and legacy `session_history_{date}.json`.
- Execute validation test suite to confirm zero data discrepancies or missing fields.

### Phase F: Live Trading Session Verification
- Monitor one full live NSE session (08:45 – 15:40 IST).
- Verify real-time streaming, disconnect recovery, EOD finalization, and next-morning PRE load.

### Phase G: Decommission Legacy Writes
- Disable legacy `_persist_session_history` disk writes.
- Archive or prune legacy `session_history_*.json` files only upon explicit user sign-off.
