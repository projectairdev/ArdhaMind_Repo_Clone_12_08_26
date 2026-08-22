# PHASE 3 — IDEMPOTENCY & SUBMISSION GUARANTEES SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Idempotency Specification  
**Component:** `OrderIntentService` (`src/execution_engine/order_intent_service.py`)  
**Scope:** Client-Side Single-Intent Invariants, Broker Constraint Alignment, Replay Prevention  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. PRECISE GUARANTEE WORDING & LIMITS

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ARDHA IDEMPOTENCY SAFETY GUARANTEE                              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ARDHA GUARANTEES:                                                                      │
│ 1. At-Most-One Logical OrderIntent submitted from the Ardha backend per approval event │
│ 2. Single Authoritative Backend Submission Gateway (Zero frontend broker dispatch)     │
│ 3. Mandatory In-Flight Lock preventing parallel or double-click dispatches             │
│ 4. Mandatory Reconcile-Before-Resubmit Protocol for all network uncertainties          │
│                                                                                        │
│ BROKER REALITY LIMIT:                                                                  │
│ Standard broker REST endpoints lack distributed ACID two-phase commit primitives.     │
│ Therefore, "Zero Duplicate Orders" is achieved through Strict Client Idempotency       │
│ combined with Bounded Broker Reconciliation, NOT unvalidated assumptions.              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. KITE ORDER TAG CONSTRAINTS & FORMAT

- **Broker Field:** `tag` in `kite.place_order(..., tag=client_order_id)`
- **Kite Technical Limits:** Maximum **20 alphanumeric characters** (`[a-zA-Z0-9]`).
- **Ardha Deterministic Tag Format:**
  `ARD{YYMMDD}{SEQ:04d}{HASH:06s}` (Length: exactly 19 characters).
  Example: `ARD2608240001A8F9B2`

---

## 3. SINGLE SUBMISSION OWNER INVARIANT

- **Frontend:** Dispatches authenticated `/api/execution/approve` request only.
- **Node Bridge:** Routes request to Python backend without broker interaction.
- **Authoritative Owner:** `OrderIntentService.submit_intent()` in Python backend.
- **In-Flight Mutex:** Memory-locked + SQLite write-ahead row lock per `proposal_id`. Double-clicks return HTTP 409 Conflict.
