# PHASE 3 — TRADE PROPOSAL & APPROVAL MODAL UX SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Trade Approval Modal Specification  
**Component:** `TradeApprovalModal.tsx` (`src/frontend/components/TradeApprovalModal.tsx`)  
**Scope:** Interactive Proposal Review, Risk-Aware Editing, Expiry Countdown, and Double-Click Prevention  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE & FROZEN (Design-Only — Production Untouched)

---

## 1. TRADE PROPOSAL APPROVAL MODAL (ASCII WIREFRAME)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TRADE PROPOSAL REVIEW & AUTHORIZATION                              [ TIME TO EXPIRE: 24s ]       │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ CONTRACT: NIFTY 24,300 CE (Weekly Expiry: 27-AUG-2026)             DIRECTION: LONG (BUY)         │
│ SETUP: PULLBACK CONTINUATION                                       NIFTY BIAS: BULLISH           │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ENTRY TRIGGER: Above 24,310 with Breadth >30 and 5m candle close confirmation                    │
│                                                                                                  │
│ RECOMMENDED QTY: 50 (1 Lot)                       MAX CAPITAL: ₹7,500.00                         │
│ RECOMMENDED LIMIT: ₹145.00                        ESTIMATED RISK: ₹850.00 (0.85% equity)         │
│ STOP LOSS: ₹128.00 (Spot < 24,240)                TARGET 1: ₹175.00 (R:R 1:1.76)                 │
│                                                   TARGET 2: ₹195.00 (R:R 1:2.94)                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ CONFIDENCE: 78%           |      LIQUIDITY: EXCELLENT      |      DATA QUALITY: HIGH             │
│ EVIDENCE: Above VWAP (24,250) • Breadth 32A / 17D • Put Wall 24,200 Support                      │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [ REJECT PROPOSAL ]              [ EDIT PARAMETERS ]              [ APPROVE & SUBMIT INTENT ]    │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. EDITABLE FIELDS & RISK REVALIDATION BEHAVIOR

| Proposal Field | Editability Classification | Revalidation Rule Upon Modification |
|:---|:---|:---|
| **Contract / Strike** | `READ_ONLY` | Cannot alter contract within same proposal (Requires new setup qualification) |
| **Direction** | `READ_ONLY` | Fixed to qualified setup direction |
| **Quantity** | `EDITABLE` (Multiple of Lot Size) | Sizing preview updates live; quantity $> \text{Recommended}$ requires explicit risk override |
| **Order Type** | `EDITABLE` (`LIMIT` or `SL`) | Market orders disallowed for options entry |
| **Limit Price** | `EDITABLE` | Must be within live $[Bid - 2\%, Ask + 2\%]$ price collar |
| **Stop Loss** | `EDITABLE_WITH_REVALIDATION` | Must be below entry and above invalidation floor |
| **Targets** | `EDITABLE` | Must satisfy minimum 1:1.5 Risk-Reward ratio |

---

## 3. PROPOSAL STALENESS & REVALIDATION WARNINGS

If quotes move outside policy bounds or feed degrades while the modal is open:
- The **`APPROVE & SUBMIT INTENT`** button is immediately disabled.
- An alert banner is rendered:
  `⚠️ PROPOSAL CHANGED — REVALIDATION REQUIRED (Spot moved +18.2 pts). PLEASE REVIEW REVISED PROPOSAL.`
