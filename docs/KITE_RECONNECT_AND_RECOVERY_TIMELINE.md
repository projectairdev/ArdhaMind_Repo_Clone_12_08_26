# KITE RECONNECT & GAP RECOVERY TIMELINE AUDIT

**Document Version:** 1.0.0 — Authoritative Reconnect & Recovery Audit  
**Target Modules:** `src/broker/services/streaming_orchestrator.py`, `src/storage/lightweight_session_store.py`

---

## 1. RECONNECT TIMELINE & STABILIZATION SEQUENCE

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DETERMINISTIC RECONNECT & RECOVERY SEQUENCE                     │
└────────────────────────────────────────────────────────────────────────────────────────┘

  T0 [10:31:58.120]  Transport Drop / Silent Stall Detected (>3.0s tick delta)
  T1 [10:31:58.200]  Mark Canonical Feed State: "DEGRADED" -> Opportunity Gating BLOCKED
  T2 [10:31:58.250]  Log ConnectivityEvent: "WS_DISCONNECTED" (data/session_store/connectivity/)
  T3 [10:32:00.100]  StreamingOrchestrator initiates reconnect with exponential backoff
  T4 [10:32:03.450]  KiteTicker WebSocket connected successfully
  T5 [10:32:03.800]  SubscriptionManager restores NIFTY, VIX, 50 Constituents, Option strikes
  T6 [10:32:04.150]  First fresh tick arrives -> last_source_observation_at updated
  T7 [10:32:04.500]  Historical Gap Backfill: kite.historical_data(from_date=T0 - 5m) via REST
  T8 [10:32:05.100]  Deduplicate candles into RollingCandleCache; Recompute TA-Lib indicators
  T9 [10:32:05.350]  Mark Provenance: "RECOVERED_HISTORICAL"
 T10 [10:32:05.500]  Stabilization Gate Passed -> Canonical Feed State restored to "HEALTHY"
 T11 [10:32:05.600]  Opportunity Engine unblocks qualification
```

---

## 2. DISCONNECT DETECTION LATENCY

- **Explicit WebSocket Disconnect (Socket Close/Error):** **<100 ms** (Immediate callback `_on_kite_close`).
- **Silent Tick Stall (Socket Open, Ticks Frozen):** **3.0 s (Warning) / 15.0 s (Hard Stale Timeout)**.
- **Option Stream Stall (Spot Live, Options Frozen):** **30.0 s**.

---

## 3. FALSE-BREAKOUT & PRICE JUMP PROTECTION

- **Problem:** When re-establishing connection after a 2-minute outage, the first live spot tick may jump $+35$ points relative to the last stale pre-outage tick.
- **Protection Implementation:**
  [`src/opportunity_engine/detectors/`](file:///opt/ardhamind/staging/src/opportunity_engine/detectors/) requires historical candle sequence continuity before firing momentum or breakout triggers. If `reconciliation_status == "PENDING"`, raw tick jumps are quarantined during stabilization (T6 to T10), preventing false breakout triggers caused by data gap recovery.
