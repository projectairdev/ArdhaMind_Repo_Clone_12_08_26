# AIR ArdhaMind — Kite Retirement & Decommissioning Plan

This document defines the safe, staged retirement plan for legacy Kite market data dependencies following full cutover to DhanHQ canonical architecture.

---

## 1. Decommissioning Prerequisites

Kite retirement must NOT begin until all of the following conditions are met:
1. Canonical DhanHQ pipeline has run continuously in production for a minimum of 5 full trading sessions without unhandled crashes, state freezes, or sequence locks.
2. Shadow comparison reports zero discrepancies across NIFTY 50 prices, candle timestamps, and market phases.
3. User explicitly approves decommissioning in writing.

---

## 2. Staged Decommissioning Matrix

| Stage | Action | Verification | Rollback Capability |
| :--- | :--- | :--- | :--- |
| **Stage 1: Inactive Standby** | Disable KiteTicker connection on boot; retain legacy classes as cold backup. | Backend boots directly into CanonicalRuntime without Kite socket. | Immediate config toggle to restart KiteTicker. |
| **Stage 2: Legacy Route Deprecation** | Deprecate legacy HTTP endpoints (`/api/kite/*`); redirect internal services to canonical endpoints. | Frontend and backend only access canonical state. | Re-enable legacy endpoints via environment flag. |
| **Stage 3: Package Archive & Cleanup** | Move legacy Kite provider code to `src/legacy/kite/` archive or delete cleanly; remove `kiteconnect` from requirements. | Full test suite (`pytest`) runs cleanly without Kite SDK. | Git branch / tag rollback. |

---

## 3. Invariants Maintained During Retirement

- **Zero Downtime**: Active intelligence generation continues uninterrupted.
- **Data Continuity**: Historical candle databases and session logs remain preserved.
- **Safety Invariant**: System remains 100% read-only throughout all stages.
