# PHASE 3 — EXECUTION FAILURE STATES & UI ERROR RESOLUTION MATRIX

**Document Version:** 1.0.0 — Authoritative Failure UI Matrix  
**Scope:** Visual States, User Messaging, Error Actions, and Trader Resolution Workflows  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE & FROZEN (Design-Only — Production Untouched)

---

## 1. FAILURE SCENARIO UI PRESENTATION MATRIX

| Failure State | Primary UI Banner | Visual Accent | Trader Action Button | Backend Invariant Enforced |
|:---|:---|:---:|:---|:---|
| **Broker Disconnected** | `BROKER SESSION EXPIRED — PLEASE RE-AUTHENTICATE` | Amber / Red | `[ LOG IN VIA KITE ]` | Proposals remain visible; submission blocked |
| **Market Feeds Stale** | `MARKET FEED STALE (>15.0s) — EXECUTION BLOCKED` | Amber | `[ AWAITING LIVE FEED ]` | Prevents submitting stale reference quotes |
| **Pre-Trade Gate Failed** | `SUBMISSION BLOCKED: MARGIN INSUFFICIENT (Req: ₹8,200, Avail: ₹5,100)` | Red | `[ ADJUST QUANTITY / RECHECK ]`| Re-evaluates live funds before unlock |
| **Timeout / Unknown Order**| `ORDER STATUS UNCERTAIN — RECONCILING WITH BROKER (DO NOT RESUBMIT)` | Red Flashing | `[ RECONCILING... (Please Wait) ]` | Bounded multi-pass orderbook scan; zero blind retry |
| **Position Unprotected** | `CRITICAL: POSITION OPEN WITHOUT BROKER STOP-LOSS` | Red Flashing | `[ RETRY BROKER SL ] / [ SQUARE-OFF ]`| High-priority warning card on Portfolio workspace |
| **Market Closed / Post-15:30**| `MARKET CLOSED — INTRADAY EXECUTION DISABLED` | Grey / Slate | `[ VIEW TOMORROW PLAN ]` | Disallows any new live order intent |
| **Proposal Expired** | `PROPOSAL EXPIRED (30s Window Exceeded)` | Slate | `[ REFRESH / RE-QUALIFY ]` | Invalidates stale approval token |
| **Revalidation Required** | `SLIPPAGE EXCEEDED POLICY COLLAR — REVIEW REVISED PROPOSAL` | Amber | `[ REVIEW REVISED PROPOSAL ]` | Halts dispatch; updates limit reference price |
