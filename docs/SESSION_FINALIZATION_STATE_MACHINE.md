# SESSION FINALIZATION & LIFECYCLE STATE MACHINE DESIGN

**Document Version:** 1.0.0 — Authoritative State Machine Design  
**Target Module:** `src/storage/session_lifecycle_manager.py`  
**Purpose:** Precise, deterministic finalization lifecycle for AIR Ardha trading sessions.

---

## 1. STATE MACHINE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    SESSION LIFECYCLE STATE TRANSITIONS                          │
└─────────────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │  NOT_STARTED │ (00:00 – 09:00 IST)
     └──────┬───────┘
            │ 09:00 IST (Pre-Open Session)
            ▼
     ┌──────────────┐
     │   PRE_OPEN   │ ──► [Freeze 09:00–09:08 Opening Snapshot]
     └──────┬───────┘
            │ 09:15 IST (Continuous Trading)
            ▼
     ┌──────────────┐
     │  MARKET_OPEN │ ──► [Append 5m Candles & Record 15m Telemetry Buckets]
     └──────┬───────┘
            │ 15:20 IST (Pre-Close Threshold)
            ▼
 ┌──────────────────────┐
 │  PRE_CLOSE_CAPTURE   │ ──► [Snapshot live Option Chain & Derivatives Depth]
 └──────────┬───────────┘
            │ 15:30 IST (Market Closes)
            ▼
 ┌──────────────────────┐
 │    CLOSE_PENDING     │ ──► [Wait for Exchange Settled Close (15:30–15:35)]
 └──────────┬───────────┘
            │ 15:35 IST (Reconciliation Trigger)
            ▼
 ┌──────────────────────┐
 │     RECONCILING      │ ──► [Fetch Kite Historical Day Candle + Match Settled OHLC]
 └──────────┬───────────┘
            │ Match Verified
            ▼
 ┌──────────────────────┐
 │   FINALIZED_BASE     │ ──► [Atomically write SessionCloseCore & OptionsCloseBaseline]
 └──────────┬───────────┘
            │ 18:00+ IST (FII/DII Cash Reports Released by NSDL/NSE)
            ▼
 ┌──────────────────────┐
 │    ENRICHED_EOD      │ ──► [Attach Institutional Net Flows (Without mutating OHLC)]
 └──────────┬───────────┘
            │ 23:59 IST (Midnight Rollover)
            ▼
 ┌──────────────────────┐
 │   FROZEN_ARCHIVE     │ ──► [Permanent Immutable Read-Only State for next session PRE]
 └──────────────────────┘
```

---

## 2. DETAILED STATE TRANSITION CONTRACTS

### 1. `PRE_CLOSE_CAPTURE` (15:20 – 15:30 IST)
- **Trigger:** System time reaches 15:20 IST on an active trading day.
- **Action:** Captures the full active option chain (`NFO:NIFTY*` quotes) to ensure closing Open Interest and LTPs are captured before exchange derivative quote streams shut down.
- **Guard:** If market disconnect occurs, preserves the newest available valid options packet as `last_valid_options_at`.

### 2. `CLOSE_PENDING` $\rightarrow$ `RECONCILING` (15:30 – 15:35 IST)
- **Trigger:** System time reaches 15:30 IST.
- **Action:** Halts streaming tick ingestion; requests authoritative daily summary candle from Zerodha Kite (`kite.historical_data(..., "day")`) and exchange settlements.
- **Reconciliation Invariant:** Compares live recorded high/low/close with official settled numbers. If drift is $\le 2.0$ points (typical closing auction adjustment), the official exchange close is adopted with provenance `"OFFICIAL_RECONCILED"`.

### 3. `FINALIZED_BASE` (15:35 IST)
- **Action:**
  1. Computes mathematical structural levels (Pivot, R1-R3, S1-S3, Local ATR bands).
  2. Generates closing market breadth and regime classification.
  3. Writes `data/session_store/close/YYYY-MM-DD.json` atomically.
  4. Writes `data/session_store/options_close/YYYY-MM-DD.json` atomically.
  5. Freezes `data/session_store/integrity/YYYY-MM-DD.json`.
- **Idempotency Rule:** The write includes an idempotency key (`CLOSE_{session_date}_GEN{generation}_{hash}`). Re-running finalization with identical generation is a strict no-op.

### 4. `ENRICHED_EOD` (18:00 – 21:00 IST)
- **Trigger:** NSE / NSDL publishes official FII / DII cash market settlement reports.
- **Action:** Appends `institutional_flows` to the session close core.
- **Strict Invariant:** Official market OHLC, pivots, and options baselines are **strictly immutable** and cannot be modified by evening enrichment.

---

## 3. MISSED CLOSE RECOVERY (CRASH / OFFLINE RESTART)

If the server was offline or crashed between 15:20 and 15:35 IST:
1. **Detection on Startup:** `LightweightSessionStore` inspects `data/session_store/close/{session_date}.json`. If absent and current time is post-close, triggers `recover_missed_close(session_date)`.
2. **Historical Recovery Flow:**
   - Calls `kite.historical_data(nifty_token, session_date, session_date, "day")` $\rightarrow$ retrieves official Open, High, Low, Close, Volume.
   - Loads last valid options baseline captured before server offline or marks options baseline `"RECOVERED_PARTIAL"`.
   - Computes mathematical structural levels (R1, S1, Pivot).
   - Generates `SessionCloseCore` with provenance `"RECOVERED_HISTORICAL_API"`.
   - Finalizes session cleanly, unblocking next-session PRE-market analysis.

---

## 4. HOLIDAY & WEEKEND SAFEGUARDS

1. **Strict Trading Day Invariant:**
   `SessionCloseCore` is **NEVER** created for Saturdays, Sundays, or declared NSE trading holidays unless a special trading session (e.g. Muhurat Trading) was officially scheduled and executed.
2. **Next-Session PRE Resolution:**
   When running on Monday morning at 08:45 AM, `LightweightSessionStore.load_latest_session_close()` automatically steps backward to find the last genuine finalized trading day (Friday `session_close_YYYY-MM-DD.json`), guaranteeing zero empty state or holiday crashes.
