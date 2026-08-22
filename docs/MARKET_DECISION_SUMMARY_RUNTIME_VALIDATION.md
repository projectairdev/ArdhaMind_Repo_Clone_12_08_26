# MARKET DECISION SUMMARY — RUNTIME VISUAL & BEHAVIORAL VALIDATION

**Document Version:** 1.0.0 — Authoritative Visual Validation  
**Target Workspace:** `Market Intelligence Workspace` (`staging.ardhamind.projectair.in`)  
**Status:** VALIDATED (All 3 Sub-Tabs Render Compact Decision Summary Strip)

---

## 1. RUNTIME VISUAL VALIDATION BY SUB-TAB

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. MORNING PLAN (PRE-MARKET)                                                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [BULLISH]  PRE-OPEN CONSTRUCTIVE STRUCTURE                     [ WATCH ]               │
│ Target Contract: REQUIRES LIVE OPTIONS                                                 │
│ Trigger: Sustain above 24,240 Carry-Forward Pivot on 09:15 open bar                    │
│ Confidence: 70%   |   Liquidity: UNAVAILABLE   |   Data Quality: HIGH   |   Risk: MOD  │
│ Invalidation: Below 24,180                                                             │
│ Evidence: Above VWAP • Positive Breadth Bias • FII Cash Supportive                     │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. LIVE GUIDE (MARKET HOURS)                                                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [BULLISH]  PULLBACK CONTINUATION                               [ READY FOR APPROVAL ]  │
│ Target Contract: 24,300 CE                                                             │
│ Trigger: Break above 24,310 with Breadth >30 and 5m bar close                          │
│ Confidence: 78%   |   Liquidity: EXCELLENT     |   Data Quality: HIGH   |   Risk: MOD  │
│ Invalidation: Close below 24,240                                                       │
│ Evidence: Above VWAP (24,250) • Breadth 32A / 17D • Put Wall 24,200 Support            │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. TOMORROW PLAN (POST-CLOSE / WEEKEND)                                                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [BULLISH]  CARRY-FORWARD STRUCTURE                             [ MARKET CLOSED ]       │
│ Target Contract: REQUIRES LIVE OPTIONS                                                 │
│ Trigger: Next-session opening sustain above 24,250 Pivot for continuation             │
│ Confidence: 62%   |   Liquidity: UNAVAILABLE   |   Data Quality: SETTLED | Risk: POST │
│ Invalidation: Next-session open below 24,180 S1                                        │
│ Evidence: Settled Close 24,252 • Breadth Positive • Volatility Stable                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. INVARIANTS & INTEGRITY PROOF
- **No Telemetry Replaced:** Detailed analytical tables, scenario matrix, strategy suitability lists, decision zones, and risk breakdown remain fully intact beneath the summary strip.
- **Zero Order Execution Coupling:** The summary layer is purely informational and contains no hooks to live order placement or execution routing.
- **Phase F Baseline Isolated:** No files in `src/storage/` or Kite streaming/connectivity were modified.
