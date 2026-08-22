# PHASE 3 — ORDER RECONCILIATION & UNKNOWN STATE PROTOCOL

**Document Version:** 1.0.0 — Authoritative Reconciliation Specification  
**Component:** `OrderReconciliationProtocol` (`src/execution_engine/order_reconciliation_protocol.py`)  
**Scope:** HTTP 504 / API Timeout Resolution, Bounded Multi-Pass Reconciliation, Resubmission Invariants  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. THE UNKNOWN STATE PROBLEM & RESOLUTION INVARIANT

If a timeout, network drop, or HTTP 504 occurs during `broker.place_order()`, Ardha enters `UNKNOWN_RECONCILING`.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              RECONCILIATION GOLDEN RULE                                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ "Not immediately visible in orderbook" NEVER EQUALS "Not Submitted".                   │
│ Ardha NEVER executes a blind retry.                                                    │
│ Ardha reconciles across 3 evidence sources over a bounded window before resolving.    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. BOUNDED MULTI-PASS RECONCILIATION WORKFLOW

```
[API Timeout / 504] ──► [State: UNKNOWN_RECONCILING]
                               │
                               ▼
               [Pass 1: Immediate Orderbook Scan (t + 1s)]
                               │ (Check tag / symbol / qty / side)
             ┌─────────────────┴─────────────────┐
             ▼                                   ▼
      [MATCH FOUND]                       [NOT FOUND]
             │                                   │
             ▼                                   ▼
 [State: ACKNOWLEDGED]           [Pass 2: Trade & Position Scan (t + 3s)]
                                                 │
                               ┌─────────────────┴─────────────────┐
                               ▼                                   ▼
                        [MATCH FOUND]                       [NOT FOUND]
                               │                                   │
                               ▼                                   ▼
                       [State: FILLED]             [Pass 3: Final Orderbook Verification (t + 7s)]
                                                                   │
                                                 ┌─────────────────┴─────────────────┐
                                                 ▼                                   ▼
                                          [MATCH FOUND]                     [CONFIRMED ABSENT]
                                                 │                                   │
                                                 ▼                                   ▼
                                       [State: ACKNOWLEDGED]              [State: NOT_SUBMITTED_CONFIRMED]
                                                                                     │
                                                                                     ▼
                                                                          [MANDATORY FRESH APPROVAL]
```

---

## 3. RESUBMISSION CONTRACT

1. If reconciliation resolves to `NOT_SUBMITTED_CONFIRMED`:
   - The original `OrderIntent` is marked `TERMINATED_ABORTED`.
   - The trader is notified immediately.
   - **Resubmission requires a completely fresh `TraderApproval` event**. Zero automatic re-dispatch.
2. If reconciliation remains `STILL_UNCERTAIN` after max observation window ($15.0$s):
   - State locks to `MANUAL_INTERVENTION_REQUIRED`.
   - All new orders blocked until broker state is verified by trader.
