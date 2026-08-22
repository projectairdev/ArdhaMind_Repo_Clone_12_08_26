# PHASE 3 — PORTFOLIO WORKSPACE FINAL UX & UI SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Portfolio UX Specification  
**Surface:** `PortfolioWorkspace.tsx` (`src/frontend/components/PortfolioWorkspace.tsx`)  
**Scope:** Institutional Trader-Centric Portfolio Layout, Position Hierarchy, Empty States, and Protection Visibility  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE & FROZEN (Design-Only — Production Untouched)

---

## 1. PRODUCT PRINCIPLE & 3-SECOND TRADER SCAN

The **PORTFOLIO** workspace is structured around immediate trader comprehension:
1. **What am I holding?** (Contract symbol & Net Lot Quantity)
2. **How is it performing?** (Current LTP & Real-time Unrealized P&L in INR and %)
3. **What is the thesis health?** (Original Setup & Structural State: `THESIS_STRONG`, `THESIS_INTACT`, `THESIS_WEAKENING`, `THESIS_INVALIDATED`)
4. **What is the protective stop status?** (`PROTECTED` [SL Order ID], `PROTECTION_PENDING`, `UNPROTECTED`)
5. **What does Ardha recommend?** (`HOLD`, `TRAIL_STOP`, `PARTIAL_EXIT`, `EXIT`, `THESIS_INVALIDATED`)
6. **Do I need to act now?** (Direct action buttons for Trader Authorization)

---

## 2. ACTIVE POSITION PRIMARY CARD (ASCII WIREFRAME)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ NIFTY 24,300 CE (27-AUG-2026)                                              [ POSITION: OPEN ]   [ PROTECTED: SL ₹128.00 ]│
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ QTY: 50 (1 Lot)        AVG ENTRY: ₹142.50         CURRENT LTP: ₹168.00         UNREALIZED P&L: +₹1,275.00 (+17.89%)    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ THESIS: PULLBACK CONTINUATION                                                      [ THESIS HEALTH: INTACT & STRONG ]  │
│ Stop Boundary: Spot < 24,240 (Option SL ₹128.00)     |     Target 1: ₹175.00 (72% complete) | Target 2: ₹195.00         │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ARDHA RECOMMENDATION: [ TRAIL STOP TO ₹148.00 ]                                                      (URGENCY: NORMAL) │
│ Rationale: Spot index sustained above 24,310 resistance pivot. Lock minimum +₹5.50/sh profit buffer.                   │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [ AUTHORIZE TRAIL STOP (₹148.00) ]            [ AUTHORIZE PARTIAL EXIT (25 Qty) ]            [ AUTHORIZE FULL EXIT ]   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. UNPROTECTED POSITION HIGH-PRIORITY WARNING CARD

If an entry fills but the broker-native protective stop is not yet confirmed, the UI prominently displays:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ⚠️ HIGH PRIORITY: POSITION UNPROTECTED                                              [ PROTECTION_STATUS: UNPROTECTED ] │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ NIFTY 24,300 CE (50 Qty) is OPEN but NO BROKER-NATIVE STOP-LOSS ORDER IS ACTIVE.                                      │
│ Reason: Broker SL order placement pending confirmation or rejected by exchange collar.                                 │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [ RETRY PROTECTIVE SL (₹128.00) ]                        [ AUTHORIZE IMMEDIATE MARKET SQUARE-OFF ]                     │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. PORTFOLIO EMPTY STATE

When zero open positions exist, the workspace displays a clean, compact summary:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ NO OPEN POSITIONS                                                                          [ EXECUTION STATUS: READY ] │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Capital Allocated: ₹0.00 / Free Cash: ₹94,520.00     |     Daily Realized P&L: +₹1,850.00 (1 Trade Closed)             │
│ Active Opportunity: NIFTY 24,300 CE (Pullback Continuation) is QUALIFYING in Market Intelligence.                      │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [ VIEW ACTIVE PROPOSALS ]                                                 [ GO TO MARKET INTELLIGENCE WORKSPACE ]      │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
