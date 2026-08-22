# PHASE 3 — EXIT & STOP MODIFICATION APPROVAL UX SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Exit Approval Specification  
**Component:** `ExitApprovalModal.tsx` (`src/frontend/components/ExitApprovalModal.tsx`)  
**Scope:** Discretionary Exits, Partial Profit Booking, Stop-Loss Trailing Authorization  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE & FROZEN (Design-Only — Production Untouched)

---

## 1. EXIT RECOMMENDATION & AUTHORIZATION MODAL

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ POSITION EXIT AUTHORIZATION                                      [ CURRENT P&L: +₹1,275.00 ]     │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ POSITION: NIFTY 24,300 CE (50 Qty)                               CURRENT LTP: ₹168.00            │
│ ENTRY AVG: ₹142.50                                               TARGET 1 (₹175.00): 72% ACHIEVED│
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ARDHA RECOMMENDATION: [ PARTIAL PROFIT BOOKING (50% LOT ALLOCATION) ]                            │
│ RATIONALE: NIFTY approaching 24,350 call resistance cluster; lock ₹637.50 profit on 25 qty.       │
│                                                                                                  │
│ PROPOSED ACTION: SELL 25 Qty at LIMIT ₹167.50 (Leave 25 Qty with Stop trailed to ₹145.00)       │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [ CANCEL / CONTINUE HOLDING ]           [ EDIT QUANTITY ]           [ AUTHORIZE PARTIAL EXIT ]   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. STOP-LOSS TRAILING AUTHORIZATION MODAL

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ AUTHORIZE PROTECTIVE STOP-LOSS UPDATE                                                            │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ POSITION: NIFTY 24,300 CE (50 Qty)                               CURRENT LTP: ₹168.00            │
│ CURRENT ACTIVE STOP: ₹128.00 (Risk: -₹725.00)                                                    │
│ RECOMMENDED NEW STOP: ₹148.00 (Guaranteed Minimum Profit: +₹275.00)                              │
│                                                                                                  │
│ WHY: Spot index established a higher swing low at 24,312. Raising stop protects capital.         │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [ DISMISS / KEEP CURRENT STOP ]                                    [ AUTHORIZE BROKER SL UPDATE ]│
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```
