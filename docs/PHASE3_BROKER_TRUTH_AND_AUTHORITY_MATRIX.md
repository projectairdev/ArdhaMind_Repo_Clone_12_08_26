# PHASE 3 — BROKER TRUTH & SYSTEM AUTHORITY MATRIX

**Document Version:** 1.0.0 — Authoritative Truth Domain Specification  
**Scope:** Strict Separation between Broker-Authoritative Facts and Ardha-Authoritative Intelligence  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. DOMAIN AUTHORITY SEPARATION MATRIX

```
┌────────────────────────────────────────┬───────────────────────────────────────────────┐
│ BROKER IS 100% AUTHORITATIVE FOR:      │ ARDHA IS 100% AUTHORITATIVE FOR:              │
├────────────────────────────────────────┼───────────────────────────────────────────────┤
│ • Order Acceptance / Exchange Ack      │ • Market Regime & Bias Evaluation             │
│ • Broker Order ID Assignment           │ • Opportunity Detection & Scoring             │
│ • Order Lifecycle Status (OPEN/FILLED) │ • Target Strike & Trigger Qualification       │
│ • Exact Fill Quantity & Price          │ • Trade Proposal Generation                   │
│ • Official Positions & Quantity        │ • Trader Approval & Pre-Trade Safety Gating   │
│ • Account Free Margin & Funds          │ • Invalidation Boundaries & Structural Stops  │
│ • Realized P&L from Broker Trades      │ • Exit Recommendations (HOLD / TRAIL / EXIT)  │
└────────────────────────────────────────┴───────────────────────────────────────────────┘
```

---

## 2. RACE CONDITIONS & RESOLUTION PROTOCOLS

### 1. Cancel / Fill Race:
- **Scenario:** Trader clicks `CANCEL ORDER`; simultaneously, market hits limit price and fills at exchange.
- **Resolution:** Broker execution truth **always wins**. The order status becomes `FILLED`. The position model updates to open holdings. Zero synthetic cancellations.

### 2. Modify / Fill Race:
- **Scenario:** Trader clicks `MODIFY LIMIT`; broker fills original price before modification executes.
- **Resolution:** Broker returns `MODIFY_REJECTED (ORDER ALREADY FILLED)`. Ardha updates position average price to original fill truth.

### 3. Zero Local Fill Inference:
- **Invariant:** Ardha **NEVER infers an order fill based on market price movements**. Fills are recorded strictly upon receiving broker execution reports or orderbook status updates.
