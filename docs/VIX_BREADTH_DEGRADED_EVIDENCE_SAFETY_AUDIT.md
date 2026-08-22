# INDIA VIX & MARKET BREADTH DEGRADED-EVIDENCE SAFETY AUDIT

**Document Version:** 1.0.0 — Authoritative Safety & Gating Verification  
**Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Scope:** Resolution of degraded VIX and Breadth fallbacks in runtime state, intelligence, and execution gating.

---

## 1. EXECUTIVE RESOLUTION & AUDIT FINDINGS

This audit investigated the two phrases flagged in the Kite Connectivity Audit:
1. *"volatility regime shifts to neutral / assumes conservative volatility range"*
2. *"Local Index Weighted Proxy"*

### Definitive Conclusion:
- **Phrase 1 (VIX Neutral/Conservative):** Descriptive terminology referring to the downstream risk engine's conservative posture when VIX is unavailable. In canonical state ([`unified_nifty.py:186`](file:///opt/ardhamind/staging/src/intelligence_engine/unified_nifty.py#L186)), when VIX is missing, the signal regime is explicitly stamped `"UNAVAILABLE"` with provenance `"validated VIX unavailable"`.
- **Phrase 2 (Breadth Proxy):** **Merely descriptive documentation.** In the active staging runtime, there is **NO** proxy module calculating or fabricating synthetic advance/decline numbers. Breadth is computed strictly from actual 50-constituent quote observations ([`kite_intelligence_service.py:152`](file:///opt/ardhamind/staging/src/broker/services/kite_intelligence_service.py#L152)). When coverage is $<40/50$, `advances` and `declines` are strictly returned as `None` (`UNAVAILABLE`).

---

## 2. INDIA VIX RUNTIME TRACE & FALLBACK AUDIT

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   INDIA VIX RUNTIME EVALUATION TRACE                             │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

1. Kite Ticker Token Ingestion
   └─► Instrument: Token 264969 (India VIX)
   └─► Ingestion: KiteTickerAdapter._on_kite_ticks() -> StreamHealthMonitor

2. Canonical State Normalization
   └─► Module: src/intelligence_engine/unified_nifty.py -> _signal()
   └─► Check: eligible = value is not None and isinstance(value, (int, float)) and value > 0
   └─► Missing State: Returns regime="UNAVAILABLE", reason="validated VIX unavailable"

3. Opportunity Engine Gating
   └─► Module: src/opportunity_engine/qualification.py -> qualify_opportunity()
   └─► Rule: If freshness_state == "STALE" or market_state == "DEGRADED" -> BLOCKED

4. Execution-Readiness & Trade Readiness Contract
   └─► Module: src/opportunity_engine/engine.py
   └─► Behavior: Strategy requiring volatility bounds cannot qualify as TRADE_READY when VIX is UNAVAILABLE
```

- **Fabricated VIX:** **NO.** Canonical state never injects synthetic numbers into market state.
- **Stale Provenance:** **PRESERVED.** When live VIX ticks freeze, timestamp and age are preserved with `freshness: "stale"`.

---

## 3. MARKET BREADTH RUNTIME TRACE & FALLBACK AUDIT

- **Source Implementation:** [`src/broker/services/kite_intelligence_service.py:140-175`](file:///opt/ardhamind/staging/src/broker/services/kite_intelligence_service.py#L140)
- **Minimum Coverage Threshold:** $40 / 50$ NIFTY constituents ($80\%$).
- **Insufficient Coverage Behavior:**
  ```python
  if valid < minimum:
      return {
          **base,
          "advances": None,
          "declines": None,
          "unchanged": None,
          "advance_decline_ratio": None,
          "status": "UNAVAILABLE" # or "PARTIAL"
      }
  ```
- **Fabricated Breadth:** **NO.** No synthetic advance/decline values are generated.
- **Opportunity Gating on Breadth Stale:** **PASS.** `QualificationEngine` returns `OpportunityStatus.BLOCKED`.

---

## 4. SCENARIO MATRIX & OPPORTUNITY GATING

| Ingestion Scenario | Canonical State | Opportunity Qualification | Trade Ready Eligibility | Safety Classification |
|:---|:---:|:---:|:---:|:---:|
| **A. NIFTY Fresh + VIX Stale** | `DEGRADED_VOLATILITY` | Directional spot momentum active; Volatility-dependent options blocked | `QUALIFIED` (Spot Only) | **SAFE_DEGRADED** |
| **B. NIFTY Fresh + Breadth Stale** | `DEGRADED_BREADTH` | Breadth alignment requirement fails; Gated to BLOCKED | `BLOCKED` | **SAFE_DEGRADED** |
| **C. NIFTY Fresh + Both Stale** | `DEGRADED` | All multi-factor strategies blocked | `BLOCKED` | **BLOCKED** |
| **D. Options Fresh + VIX Missing** | `OPTIONS_ONLY` | Contract purchase gating requires volatility bounds; Gated to BLOCKED | `BLOCKED` | **BLOCKED** |

---

## 5. AUDIT DEFECT CLASSIFICATION

- **P0 Defects:** **0 (ZERO).** No unsafe fallback values or fabricated data influence trade qualification or execution readiness.
- **P1 Items:** **0.** Display layers in UI explicitly reflect `UNAVAILABLE` or `STALE` status badges.
- **P2 Items:** **1** (Cleanup of legacy default string placeholders in secondary narrative text templates in `deterministic_fallback.py`).
