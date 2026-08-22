# LIGHTWEIGHT SESSION STORAGE — PHASE F SHADOW ACCEPTANCE & LIVE OBSERVATION PROTOCOL

**Document Version:** 1.1.0 — Authoritative Shadow Validation & Real-Time Live Protocol  
**Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Current Date:** Saturday 2026-08-22  
**Engineering Status:** PHASE F HISTORICAL / REPLAY SHADOW VALIDATION: **PASS**  
**Real Live Market Status:** PHASE F REAL LIVE NSE ACCEPTANCE: **PENDING (Scheduled: Monday 2026-08-24 08:45–15:40 IST)**  
**Production Isolation:** Staging Only — Production Untouched.

---

## 1. DUAL STATUS CLASSIFICATION

1. **Engineering Historical / Replay Shadow Validation:** **PASS**
   - Verified that the complete Lightweight Session Storage Subsystem (`src/storage/`) is fully wired, loaded, and operating in parallel dual-write shadow mode alongside legacy `session_history`.
   - Successfully validated all 11 runtime hooks against the completed Friday 2026-08-21 trading session data with 0 shadow mismatches across 21 critical market fields.
2. **Real Live NSE Market Session Acceptance:** **PENDING**
   - Because today is Saturday 2026-08-22 (a non-trading weekend), genuine real-time live market acceptance cannot occur until the next active trading session on **Monday 2026-08-24 (08:45 IST $\rightarrow$ 15:40 IST)**.
   - Timestamps and connectivity transitions will be captured in real time as events occur.

---

## 2. PRE-LIVE RUNTIME WIRING AUDIT & ACTIVE HOOKS

The live staging runtime has active call paths verified across all 11 lifecycle hooks:

| Subsystem Hook / Lifecycle Event | Source File & Function / Hook Path | Wiring Verification Status |
|:---|:---|:---:|
| **`LightweightSessionStore` Singleton Init** | [`src/storage/lightweight_session_store.py:38`](file:///opt/ardhamind/staging/src/storage/lightweight_session_store.py#L38) `get_instance()` | **VERIFIED** |
| **`LatestCanonicalRecoverySnapshot` Write** | [`src/application/workstation_state_service.py:228`](file:///opt/ardhamind/staging/src/application/workstation_state_service.py#L228) in `_persist_session_history` | **VERIFIED** |
| **Rolling Candle Cache Sync** | [`src/application/workstation_state_service.py:1403`](file:///opt/ardhamind/staging/src/application/workstation_state_service.py#L1403) `store.sync_candles()` | **VERIFIED** |
| **15-Min Telemetry Bucket Recording** | [`src/application/workstation_state_service.py:242`](file:///opt/ardhamind/staging/src/application/workstation_state_service.py#L242) `store.record_telemetry_bucket()` | **VERIFIED** |
| **Connectivity Event Logging (JSONL)** | [`src/storage/lightweight_session_store.py:244`](file:///opt/ardhamind/staging/src/storage/lightweight_session_store.py#L244) `store.record_connectivity_event()` | **VERIFIED** |
| **Pre-Close Options Candidate Capture** | [`src/application/workstation_state_service.py:1394`](file:///opt/ardhamind/staging/src/application/workstation_state_service.py#L1394) `store.record_pre_close_options()` | **VERIFIED** |
| **`SessionCloseCore` EOD Finalization** | [`src/application/workstation_state_service.py:1447`](file:///opt/ardhamind/staging/src/application/workstation_state_service.py#L1447) `store.finalize_session_close()` | **VERIFIED** |
| **`OptionsCloseBaseline` EOD Finalization** | [`src/application/workstation_state_service.py:1451`](file:///opt/ardhamind/staging/src/application/workstation_state_service.py#L1451) `store.finalize_options_baseline()` | **VERIFIED** |
| **`SessionIntegrityEnvelope` Finalization** | [`src/application/workstation_state_service.py:1457`](file:///opt/ardhamind/staging/src/application/workstation_state_service.py#L1457) `store.finalize_integrity_envelope()` | **VERIFIED** |
| **`RetentionManager` Execution** | [`src/application/workstation_state_service.py:1463`](file:///opt/ardhamind/staging/src/application/workstation_state_service.py#L1463) `store.prune_expired_sessions()` | **VERIFIED** |
| **Reader Migration (New Store $\rightarrow$ Fallback)** | [`src/intelligence_engine/performance_tracker_engine.py:772`](file:///opt/ardhamind/staging/src/intelligence_engine/performance_tracker_engine.py#L772) & [`live_assistant_engine.py:143`](file:///opt/ardhamind/staging/src/intelligence_engine/live_assistant_engine.py#L143) | **VERIFIED** |

---

## 3. REAL-TIME OBSERVATION PROTOCOL (MONDAY 2026-08-24)

The genuine live NSE acceptance will execute continuously from **08:45:00 IST to 15:40:00 IST**, recording timestamps as events occur:

1. **08:45:00 IST — Pre-Market Startup:**
   - Process startup and runtime state initialization
   - Local lightweight storage hydration ($<5.0$ ms target)
   - T-1 `SessionCloseCore` and `OptionsCloseBaseline` load from 2026-08-21
   - 5-day rolling candle cache and active catalysts load
   - Broker authentication timestamp
2. **09:00:00 – 09:08:00 IST — NSE Pre-Open:**
   - WebSocket connection timestamp
   - Subscription restoration timestamp
   - Pre-market order book discovery and opening price capture
3. **09:15:00 IST — Market Open:**
   - First real NIFTY spot tick timestamp
   - First breadth, India VIX, and options chain observations
   - Canonical `LIVE` state transition timestamp
   - Full PRE $\rightarrow$ LIVE intelligence readiness timestamp
4. **09:15 – 15:30 IST — Continuous Trading & Shadow Writes:**
   - Dual-write verification: legacy `session_history` + lightweight store
   - Real-time 15-minute telemetry bucket emission (25 buckets)
   - Real-time 5-minute candle buffer updates
   - Natural connectivity monitoring (logging any disconnect or recording `NATURAL CONNECTIVITY INCIDENTS: 0`)
   - Opportunity evaluation safety during any degraded feed state
5. **15:20:00 IST — Pre-Close Derivative Capture:**
   - Active options chain candidate capture and protection
6. **15:30:00 IST — Continuous Trading Close:**
   - Ingestion listeners remain connected in `STANDBY`; session enters `CLOSE_PENDING`
7. **15:35:00+ IST — Official Close Reconciliation:**
   - `CloseReconciliationPolicy` execution against official Kite settlement candle
   - Atomic creation of permanent `SessionCloseCore`, `OptionsCloseBaseline`, and `SessionIntegrityEnvelope`
   - Shadow mismatch count verification
   - Calculation of unreconciled critical data gaps (must equal 0)

---

## 4. PHASE G DECOMMISSIONING BLOCKED

- **Legacy `session_history_{date}.json` Writes:** **STILL ENABLED**
- **Legacy History Files:** **UNTOUCHED & UNPRUNED**
- **Phase G:** **BLOCKED PENDING MONDAY LIVE OBSERVATION & EXPLICIT USER APPROVAL**
