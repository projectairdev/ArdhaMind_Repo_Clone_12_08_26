# PHASE 3 — PORTFOLIO WORKSPACE UI & UX SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Portfolio Workspace Specification  
**Surface:** `PortfolioWorkspace.tsx` (`src/frontend/components/PortfolioWorkspace.tsx`)  
**Scope:** Trader-Centric Active Position Card, Action Prompt, Interactive Approval Modal, Institutional Layout  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. PRODUCT PRINCIPLE & UX HIERARCHY

The **PORTFOLIO** workspace is designed around trader cognitive priorities:
1. **What am I holding?** (Contract & Net Quantity)
2. **How is it performing?** (Current LTP & Unrealized P&L)
3. **What is the thesis health?** (Original setup & structural status)
4. **What does Ardha recommend?** (Action callout: HOLD / TRAIL / EXIT)
5. **Do I need to act now?** (One-click explicit action authorization)

---

## 2. ACTIVE POSITION PRIMARY CARD (ASCII WIREFRAME)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ NIFTY 24,300 CE (27-AUG-2026)                                              [ OPEN ]    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Qty: 50 (1 Lot)       Avg Entry: ₹142.50      LTP: ₹168.00      P&L: +₹1,275 (+17.8%)  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ THESIS: PULLBACK CONTINUATION                               [ THESIS INTACT: STRONG ]  │
│ Stop Loss: ₹128.00 (Spot < 24,240)    |   Target 1: ₹175.00 (72% complete)             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ARDHA RECOMMENDATION: [ TRAIL STOP TO ₹145.00 ]                                       │
│ Rationale: Spot sustained above 24,310 resistance pivot; lock ₹2.50/sh minimum gain.   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [ AUTHORIZE TRAIL STOP ]         [ AUTHORIZE PARTIAL EXIT ]         [ CLOSE POSITION ] │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. INTERACTIVE TRADE APPROVAL MODAL (ASCII WIREFRAME)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             TRADE PROPOSAL APPROVAL REVIEW                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PROPOSAL: NIFTY 24,300 CE (Weekly Expiry)                                              │
│ SETUP: Pullback Continuation (NIFTY Bias: BULLISH)                                     │
│                                                                                        │
│ ENTRY TRIGGER: Above 24,310 with Breadth >30                                           │
│ RECOMMENDED QTY: 50 (1 Lot)                     MAX CAPITAL: ₹7,500                    │
│ RECOMMENDED LIMIT: ₹145.00                      ESTIMATED RISK: ₹850 (0.85%)           │
│ STOP LOSS: ₹128.00                              TARGETS: ₹175.00 / ₹195.00             │
│                                                                                        │
│ CONFIDENCE: 78%    |    LIQUIDITY: EXCELLENT    |    DATA QUALITY: HIGH                │
│ EVIDENCE: Above VWAP (24,250) • Breadth 32A / 17D • Put Wall 24,200 Support            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [ REJECT PROPOSAL ]              [ EDIT PARAMETERS ]              [ APPROVE & SUBMIT ] │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
