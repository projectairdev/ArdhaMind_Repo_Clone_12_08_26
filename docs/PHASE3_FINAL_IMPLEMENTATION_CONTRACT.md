# PHASE 3 — FINAL IMPLEMENTATION CONTRACT & EXECUTION SAFETY SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Implementation Contract  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** FULLY VALIDATED & FROZEN FOR STAGING REVIEW  
**Production Isolation:** Staging Only — Production Untouched.

---

## 1. THE 10 PILLARS OF PHASE 3 TRADER-CONTROLLED EXECUTION

1. **Explicit Human Approval Mandatory:** Zero orders are placed or modified without an authenticated trader click on UI.
2. **Versioned Policy Contracts:** Zero architectural magic numbers; all thresholds live in testable DTOs (`ExecutionPolicyRegistry`).
3. **Six-Domain Health Separation:** Broker auth, Execution API, WebSocket, Subscriptions, Market Feeds, and Reconciliation operate orthogonally.
4. **Strict Pre-Trade Gating:** `PreTradeSafetyGate` re-evaluates all 22 checks synchronously at the millisecond of submission.
5. **Client Idempotency & Single Owner:** Exactly one backend submission gateway with memory/DB locks preventing duplicate orders.
6. **Bounded Reconciliation Protocol:** Network timeouts enter `UNKNOWN_RECONCILING`; zero blind retries; multi-pass resolution across orderbook, trades, and positions.
7. **Broker-Truth Authority:** Exchange execution reports are 100% authoritative for order state, fills, and holdings. Zero local fill inference.
8. **Broker-Native Protective Orders:** Standardizes on broker-native `SL` (Stop-Loss Limit) orders to protect capital against local disconnects.
9. **Immutable Decision Ledger:** Event-sourced, append-only history capturing complete lineage (*What Ardha knew, said, when, and why*).
10. **Attribution-Separated Performance V2:** Separates Decision Quality, Proposal Calibration, Approval Latency, Execution Slippage, and Position Management.

---

## 2. STAGED IMPLEMENTATION READINESS GATE

Phase 3 is fully designed and hardened. Implementation remains **STRICTLY BLOCKED** until:
1. Monday Phase F Real Live NSE Shadow Acceptance completes successfully (2026-08-24 08:45–15:40 IST).
2. Lightweight session storage baseline is validated in production shadow.
3. User explicitly authorizes Phase 3.1 Decision Ledger foundation work.
