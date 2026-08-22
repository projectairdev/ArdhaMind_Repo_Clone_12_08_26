# DATA FRESHNESS, OPPORTUNITY SAFETY & EXECUTION-READINESS MATRIX

**Document Version:** 1.0.0 — Authoritative Execution Readiness & Gating Audit  
**Target Subsystems:** `src/opportunity_engine/`, `src/execution_engine/`, `src/broker/`

---

## 1. OPPORTUNITY DETECTION FRESHNESS GATING

| Opportunity Detector / Strategy | Required Ingestion Domains | Freshness Gate Rule | Stale Data Behavior | Safety Status |
|:---|:---|:---|:---|:---:|
| **NIFTY Directional Trend / Momentum** | NIFTY Spot + 5m Candles + Breadth | `spot` age $<15$s and `breadth` age $<60$s | Returns `OpportunityStatus.BLOCKED` | **PASS (100% Gated)** |
| **Opening Range Breakout (ORB)** | NIFTY Spot + Intraday High/Low | `spot` age $<15$s and `market_state == "LIVE"` | Returns `OpportunityStatus.BLOCKED` | **PASS (100% Gated)** |
| **Options Strike / Premium Buy** | Spot + Option Depth + PCR + ATM IV | `options.last_valid_options_at` age $<30$s | Returns `OpportunityStatus.BLOCKED` | **PASS (100% Gated)** |
| **Mean Reversion / CPR Bounce** | Spot + Pivot Levels + Local ATR | `spot` age $<15$s and valid `pivot` | Returns `OpportunityStatus.BLOCKED` | **PASS (100% Gated)** |

---

## 2. EXECUTION-READINESS SAFETY GATES (PRE-ORDER CONTRACT)

Before any live or paper trade proposal can be marked `TRADE_READY` for execution, all 8 mandatory safety gates must be evaluated:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        8-POINT EXECUTION-READINESS SAFETY GATES                        │
├────────────────────────────────┬──────────────────────────────────────┬────────────────┤
│ 1. Broker Authentication Gate  │ broker_auth_state == "AUTHENTICATED" │ **ENFORCED**   │
│ 2. WebSocket Transport Gate    │ websocket_state == "CONNECTED"       │ **ENFORCED**   │
│ 3. Market Feed Freshness Gate  │ market_feed_state == "LIVE" (<15s)   │ **ENFORCED**   │
│ 4. Instrument Subscription Gate│ subscription_confirmed == True       │ **ENFORCED**   │
│ 5. Specific Quote Freshness    │ target_contract_age < 5.0s           │ **ENFORCED**   │
│ 6. Reconciliation Guard Gate   │ reconciliation_status != "PENDING"   │ **ENFORCED**   │
│ 7. Risk Engine Margin Gate     │ capital_allocation <= max_risk_limit │ **ENFORCED**   │
│ 8. Invalidation / Circuit Gate │ spot within dynamic stop boundaries  │ **ENFORCED**   │
└────────────────────────────────┴──────────────────────────────────────┴────────────────┘
```

---

## 3. PROFESSIONAL TERMINAL READINESS SCORECARD

| Professional Terminal Capability | Architecture Expectation | Ardha Current Staging Implementation | Readiness Score |
|:---|:---|:---|:---:|
| **Decoupled Auth vs Feed** | Broker session does not imply live ticks | `StreamHealthMonitor` separates broker auth from tick arrival | **READY** |
| **Domain-Specific Freshness** | Independent freshness tracking per asset | Separate age timers for Spot, Breadth, VIX, Options, Macro | **READY** |
| **Silent Stall Watchdog** | Detects open socket with no ticks | Age watchdog triggers reconnect at $>15$s inactivity | **READY** |
| **Rate-Limit Safe Gap Sync** | Single REST backfill request | `kite.historical_data` on reconnect (1 req/recovery) | **READY** |
| **Execution Gating on Stale** | Blocks trades when data degraded | `QualificationEngine` returns `BLOCKED` on stale feeds | **READY** |
| **Idempotent Order Lineage** | Lineage keys prevent duplicate orders | `proposals_audit.db` stores deterministic proposal IDs | **READY** |
| **Immutable EOD Provenance** | Settled truth frozen without overwrites | `SessionCloseCore` and `OptionsCloseBaseline` permanent | **READY** |
