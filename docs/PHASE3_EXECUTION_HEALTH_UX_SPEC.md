# PHASE 3 — EXECUTION HEALTH & KILL SWITCH UX SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Execution Health UI Specification  
**Component:** `ExecutionHealthStrip.tsx` & `GlobalKillSwitchControl.tsx`  
**Scope:** Multi-Domain Health Bar, Kill Switch States, and Prominent Banner Architecture  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE & FROZEN (Design-Only — Production Untouched)

---

## 1. COMPACT EXECUTION HEALTH STRIP (HEADER MOUNTED)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [BROKER: AUTHENTICATED]  [EXEC API: HEALTHY]  [FEED: FRESH (0.8s)]  [RECONCILIATION: CLEAR]  [KILL SWITCH: ACTIVE]      │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- Each badge is independently evaluated. Zero conflation between broker auth and market data health.
- If any critical domain degrades, its badge flashes in semantic amber/red.

---

## 2. GLOBAL KILL SWITCH UX ARCHITECTURE

Positioned in the primary header of the Portfolio and Execution workspaces:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ GLOBAL EXECUTION CONTROL                                             [ STATUS: EXECUTION ENABLED ]│
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Allowed Control Actions:                                                                         │
│ 1. [ PAUSE NEW ENTRIES ] — Disallows new trade proposals; permits active stop & exit execution.  │
│ 2. [ EMERGENCY SQUARE-OFF ALL ] — Immediately dispatches market exit intents for all open trades. │
│ 3. [ COMPLETE EXECUTION LOCKDOWN ] — Freezes all broker dispatch capabilities.                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```
