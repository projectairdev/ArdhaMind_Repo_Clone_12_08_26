# PHASE 3 — FINAL IMPLEMENTATION CONTRACT & EXECUTION SAFETY SPECIFICATION

**Document Version:** 1.1.0 — Authoritative Final Frozen Contract  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** FROZEN FOR MONDAY PHASE F LIVE SHADOW OBSERVATION  
**Production Isolation:** Staging Only — Production Untouched.

---

## 1. THE 10 PILLARS OF PHASE 3 TRADER-CONTROLLED EXECUTION

1. **Explicit Human Approval Mandatory:** Zero orders are placed or modified without an authenticated trader click on UI.
2. **Versioned Policy Contracts:** All thresholds live in testable DTOs (`ExecutionPolicyRegistry`). All specific numerical values (e.g. 15 pts spot slippage, 50 bps option slippage, 115% margin buffer, ₹2,000 cash buffer) are explicit **current policy defaults** or **example configurations**, not immutable architecture truths.
3. **Six-Domain Health Separation:** Broker auth, Execution API, WebSocket, Subscriptions, Market Feeds, and Reconciliation operate orthogonally.
4. **Strict Pre-Trade Gating:** `PreTradeSafetyGate` re-evaluates all 22 checks synchronously at the millisecond of submission.
5. **Client Idempotency & Single Owner:** Exactly one backend submission gateway with memory/DB locks preventing duplicate orders.
6. **Bounded Reconciliation Protocol:** Network timeouts enter `UNKNOWN_RECONCILING`; zero blind retries; multi-pass resolution across orderbook, trades, and positions governed by `OrderReconciliationPolicy`.
7. **Broker-Truth Authority:** Exchange execution reports are 100% authoritative for order state, fills, and holdings. Zero local fill inference.
8. **Sequential Protective Stop Architecture:** Standardizes on sequential broker-native `SL` (Stop-Loss Limit) orders placed immediately upon confirmed entry fill. Positions without confirmed broker stops expose transient state `PROTECTION_STATUS = UNPROTECTED`.
9. **Write-Ahead Durable Rehydration:** `TraderApproval`, `PreTradeSafetyResult`, and `OrderIntent` must be durably committed before dispatching to Kite, ensuring recovery across browser reloads or backend restarts.
10. **Attribution-Separated Performance V2:** Separates Decision Quality, Proposal Calibration, Approval Latency, Execution Slippage, and Position Management.

---

## 2. RESTART DOUBLE-SUBMISSION RISK STATUS

- **RESTART DOUBLE-SUBMIT DESIGN MITIGATION:** **COMPLETE** (Write-ahead durability + single submission owner + bounded reconciliation + unique client order tags).
- **RUNTIME DOUBLE-SUBMIT RISK:** **TO_BE_VALIDATED_DURING_PHASE_3_4_AND_3_5** (Subject to live crash injection, broker acknowledgement race, and restart testing during controlled execution phases).

---

## 3. STAGED IMPLEMENTATION READINESS GATE

Phase 3 contract is **FROZEN**. Implementation is **STRICTLY BLOCKED** until:
1. Monday Phase F Real Live NSE Shadow Acceptance completes successfully (2026-08-24 08:45–15:40 IST).
2. Lightweight session storage baseline is validated in production shadow.
3. User explicitly authorizes Phase 3.1 Decision Ledger foundation work.
