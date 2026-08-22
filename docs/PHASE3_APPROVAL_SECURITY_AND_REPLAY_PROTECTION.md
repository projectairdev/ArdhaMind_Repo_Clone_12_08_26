# PHASE 3 — APPROVAL SECURITY & REPLAY PROTECTION SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Approval Security Specification  
**Component:** `TraderApprovalService` (`src/execution_engine/trader_approval_service.py`)  
**Scope:** Cryptographic Anti-Replay Tokens, Session Bound Authorization, Multi-Click Guards  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. APPROVAL REQUEST SECURITY TOKEN CONTRACT

Every approval request submitted from the frontend must include:

```json
{
  "proposal_id": "PROP-20260824-001-A9F2",
  "decision_id": "DEC-20260824-BULL-24300CE",
  "approved_quantity": 50,
  "approved_order_type": "LIMIT",
  "approved_limit_price": 145.0,
  "approved_stop_loss": 128.0,
  "approved_targets": [175.0, 195.0],
  "request_timestamp_utc": "2026-08-24T09:30:15.120Z",
  "canonical_sequence": 14205,
  "anti_replay_nonce": "9f8a7c6e5d4b3a21"
}
```

---

## 2. BACKEND AUTHENTICATION & REPLAY VALIDATION

Upon receiving an approval request, the backend executes 5 mandatory validations:
1. **Single-Use Nonce Check:** Verifies `anti_replay_nonce` has never been evaluated before.
2. **Proposal Currency:** Verifies `proposal_id` exists in `READY_FOR_REVIEW` state and is not expired.
3. **Canonical Sequence Alignment:** Verifies `canonical_sequence` is within $\le 5$ updates of active state.
4. **Session Authentication:** Verifies caller has valid local admin session credentials.
5. **Atomic State Transition:** Transitions proposal status atomically to `APPROVED`, locking against parallel submissions.

---

## 3. BROWSER RELOAD & DOUBLE-CLICK SAFETY
- **Double-Click:** Secondary clicks receive cached HTTP 200/409 with the active in-flight intent status.
- **Browser Reload:** Reloading the UI triggers `/api/execution/active_state`, rehydrating existing intent/order state from backend memory without re-triggering execution.
