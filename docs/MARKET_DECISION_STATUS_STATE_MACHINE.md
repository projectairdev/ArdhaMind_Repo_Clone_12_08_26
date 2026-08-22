# MARKET DECISION SUMMARY — STATUS STATE MACHINE & SAFETY CONTRACT

**Document Version:** 1.0.0 — Authoritative State Machine Specification  
**Scope:** Decision Card Lifecycle & Informational Approval Contract  
**Design Target:** `MarketDecisionStatus`

---

## 1. STATE MACHINE TRANSITIONS

```
                     ┌──────────────────┐
                     │   UNAVAILABLE    │
                     └────────┬─────────┘
                              │ Session Open / Provider Ready
                              ▼
                     ┌──────────────────┐
                     │     WAITING      │◄─────────────────────────────┐
                     └────────┬─────────┘                              │
                              │ Setup Identified in Trigger Zone       │
                              ▼                                        │
                     ┌──────────────────┐                              │
            ┌───────►│      WATCH       │                              │
            │        └────────┬─────────┘                              │
            │                 │ Price in Trigger Tolerance             │
            │                 ▼                                        │
            │        ┌──────────────────┐                              │
            │        │    QUALIFYING    │                              │
            │        └────────┬─────────┘                              │
            │                 │ All 8 Safety Gates Passed              │
            │                 ▼                                        │
            │        ┌──────────────────┐                              │
            │        │READY_FOR_APPROVAL│                              │
            │        └────────┬─────────┘                              │
            │                 │                                        │
            │       ┌─────────┴─────────┐                              │
            │       │                   │                              │
    Stale / │       ▼ Setup Violated    ▼ Time Expired                 │
  Degraded  │┌──────────────┐   ┌──────────────┐                       │
            ││ INVALIDATED  │   │   EXPIRED    │───────────────────────┘
            │└──────────────┘   └──────────────┘
            │
            ▼
     ┌──────────────┐
     │   BLOCKED    │
     └──────────────┘
```

---

## 2. THE 8-POINT `READY_FOR_APPROVAL` MANDATORY SAFETY CONTRACT

A decision summary can transition into `READY_FOR_APPROVAL` **only** when all 8 conditions evaluate to `True`:

1. **Market Session Active:** `market_session_phase in ("MARKET_OPEN", "OPEN", "CONTINUOUS_TRADING")`
2. **Broker Authentication Valid:** `broker_auth_state == "AUTHENTICATED"` (if execution context enabled)
3. **Spot Price Fresh:** `time.time() - spot_observed_at < 15.0s`
4. **Target Option Contract Fresh:** `time.time() - contract_quote_observed_at < 15.0s`
5. **Option Chain Liquidity Valid:** `bid_ask_spread_bps <= 250` and `depth_liquidity != "POOR"`
6. **Breadth / Volatility Validated:** Breadth and VIX states are not `UNAVAILABLE` or `STALE`
7. **Reconciliation Clear:** `reconciliation_status != "PENDING"`
8. **Invalidation Level Explicit:** Structural invalidation stop level is strictly defined and $>0$.

---

## 3. CANONICAL BLOCKING REASONS INVENTORY

When any gate fails, the decision card explicitly surfaces the exact blocking reasons:
- `MARKET_CLOSED`: Live trade scanning paused outside market hours.
- `MARKET_FEED_STALE`: Real-time spot price tick age $>15.0$s.
- `OPTIONS_FEED_STALE`: Option strike quote age $>30.0$s.
- `BREADTH_INSUFFICIENT_COVERAGE`: Less than 40/50 constituent quotes active.
- `STRIKE_NOT_QUALIFIED`: Underlying volatility or strike liquidity failed qualification.
- `RECONCILIATION_PENDING`: Ingesting historical backfill post-reconnect.
- `RISK_LIMIT_BREACHED`: Trade structure exceeds maximum allocation bounds.
