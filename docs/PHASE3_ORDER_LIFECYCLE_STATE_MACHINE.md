# PHASE 3 — ORDER LIFECYCLE STATE MACHINE & IDEMPOTENCY SPECIFICATION

**Document Version:** 1.0.0 — Authoritative State Machine & Idempotency Specification  
**Component:** `OrderLifecycleManager` (`src/execution_engine/order_lifecycle_manager.py`)  
**Scope:** Order State Transitions, Zero-Duplicate Submission Idempotency, Broker Unknown Replay Resolution  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. IMMUTABLE ORDER INTENT & THREE-TIER ID MAPPING

To guarantee that network retries, browser double-clicks, or service restarts can **never produce duplicate broker orders**, Ardha establishes a strict three-tier identifier mapping:

```
[Trade Proposal] ──► [Trader Approval] ──► [OrderIntent] (client_order_id)
                                                    │
                                                    ▼
                                      [Broker Submission Gateway]
                                                    │
                                                    ▼
                                     [Zerodha Kite] (broker_order_id)
```

- **`proposal_id`:** Unique trade proposal identifier.
- **`approval_id`:** Unique trader approval event record.
- **`order_intent_id` / `client_order_id`:** Globally unique deterministic string (`INTENT-{session_date}-{approval_id_hash}`). Stamped as `tag` in Kite `place_order()`.
- **`broker_order_id`:** Authoritative exchange identifier assigned by Zerodha Kite upon acknowledgement.

---

## 2. ORDER STATE MACHINE TRANSITION MATRIX

```
┌─────────────────┐
│     CREATED     │
└────────┬────────┘
         │ (PreTradeSafetyGate passed)
         ▼
┌─────────────────┐
│ READY_TO_SUBMIT │
└────────┬────────┘
         │ (Submitting via Kite API)
         ▼
┌─────────────────┐       (Network Timeout / Unknown)      ┌─────────────────────┐
│   SUBMITTING    ├───────────────────────────────────────►│ UNKNOWN_RECONCILING │
└────────┬────────┘                                        └──────────┬──────────┘
         │                                                            │
         │ (HTTP 200 / Broker Order ID Received)                      │ (Reconciled via Orderbook)
         ▼                                                            ▼
┌─────────────────┐                                        ┌─────────────────────┐
│  ACKNOWLEDGED   │◄───────────────────────────────────────┤   FOUND IN BROKER   │
└────────┬────────┘                                        └─────────────────────┘
         │                                                            │ (Confirmed Not in Broker)
         ├──────────────────────────────┬─────────────────────────────┼────────────────────────┐
         │ (Exchange Accepts)           │ (Immediate Reject)          ▼                        │
         ▼                              ▼                   ┌──────────────────┐               │
┌─────────────────┐            ┌──────────────────┐         │ NOT_SUBMITTED_OK │               │
│      OPEN       │            │     REJECTED     │         └──────────────────┘               │
└────────┬────────┘            └──────────────────┘                                            │
         │                                                                                     │
         ├──────────────────────────────┬─────────────────────────────┬────────────────────────┤
         │ (Partial Fill)               │ (Full Fill)                 │ (Cancelled)            │ (Expired)
         ▼                              ▼                             ▼                        ▼
┌─────────────────┐            ┌──────────────────┐         ┌──────────────────┐      ┌─────────────────┐
│ PARTIALLY_FILLED│            │      FILLED      │         │    CANCELLED     │      │     EXPIRED     │
└────────┬────────┘            └──────────────────┘         └──────────────────┘      └─────────────────┘
         │                               ▲
         └───────────────────────────────┘ (Remaining quantity fills)
```

---

## 3. UNKNOWN BROKER STATE RECONCILIATION PROTOCOL

If Kite API times out or crashes during `place_order()`:
1. State transitions immediately to `UNKNOWN_RECONCILING`.
2. The orchestrator **NEVER submits a retry blindly**.
3. It queries the broker orderbook using `client_order_id` (`tag`) and timestamp range.
4. **Case A (Found in Broker):** Maps order to `ACKNOWLEDGED` with the found `broker_order_id`.
5. **Case B (Confirmed Absent):** Transitions to `NOT_SUBMITTED_FAILED` and alerts the trader. Re-submission requires fresh approval.

---

## 4. PARTIAL FILLS & POSITION TRUTH

- Position sizing and average entry prices are updated **strictly on confirmed execution reports** (`trade_id`, `fill_qty`, `fill_price`).
- If an order is partially filled and then cancelled, the position reflects exact executed quantity with zero synthetic rounding.
