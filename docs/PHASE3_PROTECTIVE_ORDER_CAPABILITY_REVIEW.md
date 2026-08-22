# PHASE 3 — PROTECTIVE ORDER CAPABILITY REVIEW

**Document Version:** 1.0.0 — Authoritative Broker Protective Stop Capability Review  
**Provider:** Zerodha Kite Connect API (NSE Options Segment)  
**Scope:** Order Type Capabilities (SL, SL-M, GTT), Product Types (MIS vs NRML), Failure Policies  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** CAPABILITY AUDIT COMPLETED (Design-Only — Production Untouched)

---

## 1. ZERODHA KITE OPTIONS CAPABILITY AUDIT

| Mechanism | Order Type / API | NIFTY Options Support | Product Type | Capability Status | Notes / Limitations |
|:---|:---|:---:|:---:|:---:|:---|
| **Stop-Loss Limit** | `order_type="SL"` | **YES** | `MIS` / `NRML` | **SUPPORTED** | Requires `price` (limit) and `trigger_price`. Recommended protective stop mechanism. |
| **Stop-Loss Market** | `order_type="SL-M"` | **LIMITED** | `MIS` / `NRML` | **EXCHANGE_RESTRICTED** | NSE frequently blocks SL-M on stock/index options due to freak trade prevention circulars. |
| **Good-Till-Triggered**| `/gtt/triggers` | **YES** | `NRML` / `CNC` | **SUPPORTED** | Broker-side multi-day persistent trigger. Operates for carry-forward options. |
| **Cover Orders (CO)** | `order_type="CO"` | **NO** | `MIS` | **NOT_SUPPORTED** | Disabled by Zerodha on index options. |

---

## 2. PROTECTIVE STOP ARCHITECTURAL RECOMMENDATION

1. **Primary Intraday Protective Order:** Broker-native **`SL` (Stop-Loss Limit)** with a 5-point limit collar below trigger price to ensure execution while complying with exchange circulars.
2. **Stop Failure Policy:** If a broker-native SL cannot be placed (e.g. margin rejection or exchange API failure), `PreTradeSafetyGate` flags `PROTECTIVE_STOP_UNAVAILABLE` and **BLOCKS the entry order**.
3. **Synthetic Stop Fallback:** Disallowed as sole protection for new entries in Phase 3.
