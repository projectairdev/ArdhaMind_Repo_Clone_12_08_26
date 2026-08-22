# PHASE 3 — TRADER-CONTROLLED EXECUTION MASTER ARCHITECTURE

**Document Version:** 1.0.0 — Authoritative Master Architecture  
**Scope:** End-to-End Trader-Controlled Execution Pipeline, Boundaries, and Component Contracts  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** ARCHITECTURE DESIGN APPROVED FOR REVIEW (Design-Only — Zero Execution Code Added)  
**Production Isolation:** Staging Only — Production Untouched.

---

## 1. PRODUCT PRINCIPLE & CORE CHARTER

Phase 3 establishes a **Trader-Controlled Execution Paradigm**. AIR Ardha is an institutional intelligence and execution assistant, **NOT an autonomous black-box trading bot**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE PHASE 3 TRADER CHARTER                                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Ardha performs multi-factor market analysis & regime identification                 │
│ 2. Ardha qualifies structural setups, strikes, entry triggers, and invalidation stops   │
│ 3. Ardha synthesizes context into an immutable, structured TradeProposal               │
│ 4. Trader reviews the proposal with full provenance and rationale                     │
│ 5. Trader explicitly approves (or edits/rejects) the proposal                           │
│ 6. PreTradeSafetyGate executes hard multi-point revalidation at submission instant     │
│ 7. Ardha submits the single idempotent OrderIntent to Zerodha Kite                     │
│ 8. Ardha tracks order state transitions and reconstructs position from broker truth   │
│ 9. Ardha provides real-time exit intelligence (Hold / Trail / Reduce / Exit)          │
│ 10. Trader reviews and authorizes any exit or modification action                      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. STRICT PHASE BOUNDARY & PHASE 4 PROHIBITION

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 3 vs PHASE 4 EXECUTION BOUNDARY                           │
├────────────────────────────────────────┬───────────────────────────────────────────────┤
│ Permitted in Phase 3 (Trader-Controlled│ Prohibited in Phase 3 (Strictly Phase 4)      │
├────────────────────────────────────────┼───────────────────────────────────────────────┤
│ • Automated setup detection & scoring  │ • Automatic order placement on trigger hit    │
│ • Deterministic proposal generation    │ • Unattended order submission without human UI│
│ • Interactive Approval / Rejection UI  │ • Auto-routing orders from AI confidence      │
│ • Pre-trade deterministic safety gates │ • Automatic position scale-in without approval│
│ • Single-intent idempotent submission  │ • Synthetic order routing without broker auth │
│ • Broker-truth position reconstruction │ • Autonomous stop-loss movement               │
│ • Deterministic Exit Recommendations   │ • Paper / Mock trading modes disguised as live│
└────────────────────────────────────────┴───────────────────────────────────────────────┘
```

---

## 3. MASTER END-TO-END EXECUTION FLOW

```
[MarketDecisionSummary] (Status: READY_FOR_APPROVAL)
           │
           ▼
[TradeProposalBuilder] ──► Generates immutable TradeProposal (Status: READY_FOR_REVIEW)
           │
           ▼
[TraderReview Modal] ──► Trader reviews setup, strike, quantity, stop, targets, rationale
           │
           ├──────────────────────────────┬──────────────────────────────┐
           ▼                              ▼                              ▼
    [APPROVE AS IS]               [EDIT & APPROVE]                   [REJECT]
           │                              │                              │
           └──────────────┬───────────────┘                              ▼
                          │                                      [PROPOSAL REJECTED]
                          ▼
             [TraderApproval Record] (Captures approved params, expiry, timestamp)
                          │
                          ▼
             [PreTradeSafetyGate] (22-Point deterministic real-time gate)
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
       [GATE PASS]                 [GATE FAIL] ──► [BLOCKED / REVALIDATION_REQUIRED]
            │
            ▼
      [OrderIntent] (Immutable client_order_id & order parameters)
            │
            ▼
 [BrokerExecutionService] ──► Submits to Zerodha Kite API (with timeout & idempotency lock)
            │
            ▼
[OrderLifecycleManager] ──► SUBMITTED ──► ACKNOWLEDGED ──► OPEN ──► FILLED / REJECTED
            │
            ▼
[PositionLifecycleManager] ──► Reconstructs PositionState strictly from broker fills
            │
            ▼
[ExitIntelligenceEngine] ──► Evaluates real-time structural health (HOLD / TRAIL / EXIT)
            │
            ▼
 [TraderExitApproval] ──► Trader authorizes exit / target / stop modification
            │
            ▼
[DecisionLedger & PerformanceV2] ──► Immutable audit trail & multi-horizon evaluation
```

---

## 4. SUBSYSTEM ARCHITECTURE & OWNERSHIP MATRIX

| Subsystem Module | Responsibility | Authority Level | Existing Repository Status |
|:---|:---|:---|:---|
| `TradeProposalService` | Composes proposals from `MarketDecisionSummary` | Canonical Engine | **NEW DOMAIN MODULE** (Refactoring legacy `proposal_engine`) |
| `TraderApprovalService` | Captures, cryptographically signs, & validates trader approval | Human Interface | **NEW DOMAIN MODULE** |
| `PreTradeSafetyGate` | Enforces 22-point deterministic pre-submission safety checks | Safety Barrier | **NEW DOMAIN MODULE** (Replaces legacy `execution_validator`) |
| `OrderIntentService` | Generates immutable, idempotent order intent payloads | Submission Owner | **NEW DOMAIN MODULE** |
| `BrokerExecutionService`| Dispatches orders to Kite API & handles network timeouts | Broker Bridge | **REUSABLE / REFACTOR** (`src/broker/services/orders_service.py`) |
| `OrderLifecycleManager` | State machine tracking order status transitions | Broker State Sync | **REUSABLE / REFACTOR** (`src/execution_engine/order_lifecycle_manager.py`) |
| `PositionLifecycleManager`| Maintains live position views based on confirmed broker trades | Position Truth | **REUSABLE / REFACTOR** (`src/broker/services/positions_service.py`) |
| `ExitRecommendationService`| Computes structural hold/exit recommendations | Decision Assistant | **NEW DOMAIN MODULE** |
| `DecisionLedger` | Event-sourced immutable storage of all decision & execution events | System of Record | **NEW STORAGE PACKAGE** (`src/storage/decision_ledger/`) |
| `PerformanceEvaluatorV2`| Evaluates analytical, proposal, and execution performance | Attribution Engine| **NEW DOMAIN MODULE** (Refactoring legacy `performance_tracker_engine`) |
