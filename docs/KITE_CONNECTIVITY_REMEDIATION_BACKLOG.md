# KITE CONNECTIVITY & RESILIENCE REMEDIATION BACKLOG

**Document Version:** 1.0.0 — Authoritative Defect & Enhancement Backlog  
**Status:** AUDIT COMPLETE — P0: 0 | P1: 2 | P2: 2  
**Implementation Policy:** Audit Only (No broad implementation without user request)

---

## 1. DEFECT CLASSIFICATION SUMMARY

```
┌────────────────────────────────────────────────────────────────────────┐
│               CONNECTIVITY & EXECUTION-READINESS DEFECT AUDIT          │
├────────────┬───────┬───────────────────────────────────────────────────┤
│ Severity   │ Count │ Description                                       │
├────────────┼───────┼───────────────────────────────────────────────────┤
│ **P0**     │ **0** │ False Live Status / Stale Trade Qualification     │
│ **P1**     │ **2** │ Secondary Reference Sanity & Reconnect Telemetry  │
│ **P2**     │ **2** │ Telemetry Histograms & Granular Greeks Latency    │
└────────────┴───────┴───────────────────────────────────────────────────┘
```

---

## 2. DETAILED BACKLOG ITEMS

### P0 Findings: NONE (0 Defects)
- **Validation:** Both `StreamHealthMonitor` and `QualificationEngine` explicitly check `freshness_state == "STALE"` and `spot <= 0`, blocking trade qualification whenever market data is degraded.
- **Last-Valid Guards:** Pre-close candidate preservation in `LightweightSessionStore` prevents off-hours empty packets from wiping derivative baselines.

### P1 Enhancements (Recommended for Next Sprint)
1. **P1-CONN-01: Secondary NSE India Reference Sanity Poller**
   - *Description:* Implement a low-frequency (30s) REST poller to `nseindia.com` as an out-of-band cross-check to detect broker-side pricing anomalies.
   - *Effort:* Low.
2. **P1-CONN-02: Reconnect Generation ID Propagation in Canonical Telemetry**
   - *Description:* Include `generation_id` and `reconnect_count` directly in the top-level `streamTelemetry` payload emitted to the React frontend.
   - *Effort:* Low.

### P2 Enhancements (Diagnostics & Tuning)
1. **P2-DIAG-01: REST API Latency Histogram**
   - *Description:* Log p50, p90, and p99 response times for `historical_data()` calls during EOD reconciliation.
2. **P2-DIAG-02: Strike-by-Strike Tick Rate Diagnostics**
   - *Description:* Track individual option strike tick frequency to identify illiquid strikes with low market activity.
