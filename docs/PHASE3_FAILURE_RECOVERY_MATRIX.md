# PHASE 3 — FAILURE RECOVERY & EDGE CASE RESOLUTION MATRIX

**Document Version:** 1.0.0 — Authoritative Fault Tolerance & Recovery Matrix  
**Scope:** Exhaustive Failure Modes, Invariant Violations, Network Timeouts, and Safe Recovery Protocols  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. EXHAUSTIVE FAILURE MATRIX & SYSTEM BEHAVIOR

| Incident Scenario | Root Cause / Trigger | Immediate State Transition | Automatic Recovery Protocol | Trader Action Required |
|:---|:---|:---|:---|:---|
| **Broker Disconnect Before Submit** | Auth token expired or socket drop | `SUBMISSION_BLOCKED` | Halts submission; preserves proposal state; initiates reconnect | Log into Kite if session invalid |
| **API Timeout During `place_order()`** | Network partition / HTTP 504 | `UNKNOWN_RECONCILING` | Queries broker orderbook with `client_order_id`; resolves Ack vs Not Submitted | Notifies trader with reconciled truth |
| **Partial Fill Then WebSocket Drop** | Packet loss or network crash | `PARTIAL_POSITION` | Reconstructs filled qty from REST trades sync; cancels or monitors remaining | Trader confirms whether to keep open |
| **Spot Staleness at Approval Instant** | Tick feed delay $>15.0$s | `REVALIDATION_REQUIRED` | Aborts submission; requires fresh spot tick before enabling approval | Re-approves when feeds refresh |
| **Slippage Breach Post-Approval** | Option ask jumps $>50$ bps | `SLIPPAGE_BREACH_BLOCKED`| Halts order intent dispatch; generates revised limit price recommendation | Reviews revised proposal |
| **Broker Margin Rejection** | Insufficient free cash | `ORDER_REJECTED` | Captures broker reject reason; updates available margin cache | Adjusts quantity or adds funds |
| **Server Crash With Open Orders** | Process restart / OS reboot | `STARTUP_RECONCILING` | Reconciles open intents against active broker orderbook on boot | Confirms active portfolio status |
| **Emergency Kill-Switch Triggered** | Trader manual stop or loss breach| `ALL_EXECUTION_DISABLED` | Disables new order submissions; preserves existing protective stops | Trader assesses portfolio |

---

## 2. SECURITY & AUTHORIZATION INVARIANTS
1. **Zero Credential Exposure:** Kite API secrets, request tokens, and access tokens reside **strictly in backend secure storage**. Zero credentials passed to frontend.
2. **Server-Side Authorization Check:** Every trade action is authenticated on the backend session bridge before dispatching to Kite.
3. **Audit Trail Completeness:** Every security or execution exception is written to `data/audit/security_events.jsonl`.
