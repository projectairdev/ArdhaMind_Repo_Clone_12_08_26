# ArdhaMind Architecture Reference

This document maps the verified analytical and data pipeline architecture of **AIR ArdhaMind**.

---

## 1. Verified Analytical Pipeline Chain

```text
Market Feed / Kite Provider
      │
      ▼
Normalization & Options Engine  (max_pain, call_wall, put_wall, pcr)
      │
      ▼
TradeContext & Market Context   (spot, vwap, orh, orl, vix, breadth)
      │
      ▼
Score & Opportunity Engine     (detectors, qualification, ranking, scoring)
      │
      ▼
Strategy & Pre-Market Engine    (briefings, high/low zones, decision corridor)
      │
      ▼
Planner & Scenarios            (Scenario A/B/C, activation rules)
      │
      ▼
Confidence & Risk Assessment    (confidence %, risk grade, regime)
      │
      ▼
Decision Support & Unified State (CanonicalWorkstationState)
      │
      ▼
Explanation & Server Bridge     (server_bridge.py daemon, WebSocket / API)
      │
      ▼
Frontend Client State          (WorkstationStateContext, React UI)
```

---

## 2. Server-Authoritative Ownership

- **Python Backend Daemon (`src/server_bridge.py`)**: Owns market data ingestion, options calculation, opportunity scoring, briefing generation, performance evaluation, and WebSocket state emission.
- **Node Gateway / Server (`server.ts` -> `dist/server.cjs`)**: Serves REST APIs (`/api/state`, `/api/performance/*`, `/api/briefing/*`) and static assets.
- **React Frontend (`src/frontend/`)**: Renders trader workstation dashboards. Accepts server-emitted state without recreating server-side mathematical models.
