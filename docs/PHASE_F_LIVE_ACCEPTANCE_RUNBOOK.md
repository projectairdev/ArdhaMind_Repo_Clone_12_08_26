# PHASE F — LIVE NSE SHADOW ACCEPTANCE RUNBOOK

**Document Version:** 1.0.0 — Authoritative Live Execution Runbook  
**Target Trading Session:** Monday 2026-08-24 (08:45 IST → 15:40 IST)  
**Execution Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Objective:** Validate Lightweight Session Storage & Market Decision Summary against REAL LIVE NSE market conditions in parallel shadow mode with legacy session_history.  
**Critical Success Criterion:** **ZERO UNRECONCILED CRITICAL DATA GAPS**

---

## 1. PRE-MARKET READINESS PROTOCOL (08:45 IST)

```
08:45 IST CHECKLIST:
[ ] 1. Verify staging git status (clean tree, tag: STAGING_MARKET_DECISION_SUMMARY_ACCEPTED)
[ ] 2. Verify ardhamind.service and nginx.service are active (PID, ports 80/443/3000)
[ ] 3. Verify system clock timezone: Asia/Kolkata (IST)
[ ] 4. Verify disk space: >10GB free on /opt/ardhamind
[ ] 5. Verify Kite session login and token authentication status
[ ] 6. Confirm data/session_store/ directories are present
[ ] 7. Confirm legacy session_history writing is ENABLED
[ ] 8. Verify Market Decision Summary renders "INITIALIZING / WATCH" on UI
```

---

## 2. PRE-OPEN & FIRST TICK OBSERVATION (09:00 — 09:15 IST)

- **09:00–09:08 IST:** Observe pre-open session transitions. Verify zero false "LIVE" alerts or spurious disconnect storms.
- **09:15:00 IST:** Record exact millisecond timestamps for:
  - `auth_verified_at`
  - `ws_connected_at`
  - `subscriptions_restored_at`
  - `first_nifty_tick_at`
  - `first_breadth_at`
  - `first_vix_at`
  - `first_options_at`
  - `canonical_live_at`
  - `intelligence_ready_at`
- **Verify:** First NIFTY tick is genuine provider data, sequence increments monotonically, and no stale Friday values are displayed.

---

## 3. CONTINUOUS SESSION MONITORING (09:15 — 15:20 IST)

- Monitor 15-minute telemetry intervals (`data/session_store/telemetry/2026-08-24.json`).
- Verify rolling 5m candle generation (`data/session_store/cache/nifty_5m_candles.json`).
- Verify atomic updates to `data/session_store/cache/latest_canonical_state.json`.
- Execute periodic shadow diffs against legacy `session_history_2026-08-24.json`. Critical mismatches must be **0**.

---

## 4. PRE-CLOSE CAPTURE (15:20 IST)

- At **15:20 IST**, observe pre-close valid options capture.
- Verify `latest_valid_options` snapshot is locked and stored for `OptionsCloseBaseline`.
- Ensure post-market empty/off-hours packets **DO NOT OVERWRITE** the 15:20 candidate.

---

## 5. CLOSE STANDBY & RECONCILIATION (15:30 — 15:40 IST)

- **15:30 IST:** Confirm state transitions from `MARKET_OPEN` to `CLOSE_PENDING`. Ingestion remains active for final settlement.
- **15:35+ IST:** Execute `CloseReconciliationPolicy` comparing candidate close vs official NSE settled close.
- **15:40 IST:** Finalize:
  - `data/session_store/close/2026-08-24.json` (`SessionCloseCore`)
  - `data/session_store/options_close/2026-08-24.json` (`OptionsCloseBaseline`)
  - `data/session_store/integrity/2026-08-24.json` (`SessionIntegrityEnvelope`)
- Run retention manager pruning.
