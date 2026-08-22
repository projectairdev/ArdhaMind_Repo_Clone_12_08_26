# MARKET DECISION SUMMARY — UI & VISUAL SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Visual & Layout Spec  
**Target Surface:** `src/components/MarketIntelligence/DecisionSummaryCard.tsx`  
**Aesthetic Style:** Institutional Trading Terminal (Compact, Charcoal, Monospace Metrics, Accessible Text Badges)

---

## 1. COMPONENT PLACEMENT & VISUAL HIERARCHY

The Decision Summary Card is mounted immediately beneath the sub-tab header (`Morning Plan` / `Live Guide` / `Tomorrow Plan`) and directly above the detailed analytical panels.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              DECISION SUMMARY CARD (LIVE GUIDE)                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [BULLISH]  PULLBACK CONTINUATION                               [ READY FOR APPROVAL ]  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Target Strike: 24,300 CE                                                               │
│ Trigger: Above 24,310 with Breadth >30 and 5m candle close confirmation                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Confidence: 78%   |   Liquidity: GOOD   |   Data Quality: HIGH   |   Risk: MODERATE    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Invalidation: Close below 24,265 (Structure break)                                     │
│ Why / Evidence: Above VWAP (24,285) • Put Wall 24,200 Support • India VIX Stable (12.4)│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. REPRESENTATIVE MOCK LAYOUT SCENARIOS

### Scenario A: READY Bullish Setup (Live Hours)
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [BULLISH]  PULLBACK CONTINUATION                               [ READY FOR APPROVAL ]  │
│ 24,300 CE  |  Trigger: Above 24,310 on 5m bar close with Breadth >30                   │
│ Confidence: 78%   |   Liquidity: GOOD   |   Data Quality: HIGH   |   Risk: MODERATE    │
│ Invalidation: Below 24,265  |  Evidence: Above VWAP • Put Wall Support • VIX Stable    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Scenario B: READY Bearish Breakdown Setup (Live Hours)
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [BEARISH]  BREAKDOWN CONTINUATION                              [ READY FOR APPROVAL ]  │
│ 24,200 PE  |  Trigger: Below 24,240 on 5m bar close with Declines >35                  │
│ Confidence: 82%   |   Liquidity: EXCELLENT | Data Quality: HIGH   |   Risk: MODERATE   │
│ Invalidation: Above 24,285  |  Evidence: Below VWAP • Call Wall 24,500 • Breadth Heavy │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Scenario C: WAITING Setup (Observing Zone)
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [BULLISH]  SUPPORT BOUNCE                                            [ WAITING ]       │
│ Strike: NOT QUALIFIED (Awaiting Zone Entry)                                            │
│ Trigger: Pullback into 24,220–24,240 Support Zone with bullish candle rejection        │
│ Confidence: 65%   |   Liquidity: WAITING | Data Quality: HIGH   |   Risk: MODERATE     │
│ Waiting For: Spot approach into S1 zone (Current Spot: 24,275)                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Scenario D: BLOCKED Setup (Options Feed Stale)
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [BULLISH]  PULLBACK CONTINUATION                                     [ BLOCKED ]       │
│ Strike: NOT QUALIFIED (Options Stale)                                                  │
│ Trigger: Gated due to market data staleness                                            │
│ Confidence: DEGRADED | Liquidity: UNAVAILABLE | Data Quality: DEGRADED | Risk: BLOCKED │
│ Blocking Reasons: [OPTIONS_FEED_STALE: Option quotes >30s age]                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Scenario E: MARKET CLOSED / Tomorrow Plan (Post-Close / Weekend)
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [BULLISH BIAS]  CARRY-FORWARD STRUCTURE                          [ MARKET CLOSED ]     │
│ Strike: REQUIRES LIVE OPTIONS                                                          │
│ Key Trigger: Opening sustain above 24,250 Pivot for Next-Session Continuation          │
│ Confidence: 70%   |   Liquidity: N/A     | Data Quality: SETTLED | Risk: POST-SESSION  │
│ Invalidation: Next-session open below 24,180 S1                                        │
│ Context: Settled EOD Close at 24,252 (+20.15 pts) • FII Net Cash Positive              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. RESPONSIVE BREAKPOINTS

- **1920×1080 / 1600×900 (Desktop Full):** Single unified card, horizontal 4-column metrics strip (`Confidence`, `Liquidity`, `Data Quality`, `Risk`).
- **1366×768 (Standard Laptop):** 2×2 grid metrics strip; full text visibility with compact font scaling (`text-xs`).
- **Narrow Drawer / Mobile ($<768\text{px}$):** Stacked vertical cards with collapsible `Why / Evidence` drawer.
