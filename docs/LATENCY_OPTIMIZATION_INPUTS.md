# Latency Optimization Inputs (STAGING ONLY)

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Specification**: Identified latency bottlenecks, polling intervals, and architectural input requirements for the upcoming ultra-low-latency event-driven market data delivery sprint.

---

## 1. Latency Bottleneck Inventory

### Bottleneck 1: Frontend HTTP Polling Fallback (5,000 ms Interval)
- **Path**: `WorkstationStateContext.tsx` &rarr; `fetchCanonicalState()`
- **Issue**: When WebSocket is not connected or during initial page load, the frontend polls `/api/state/canonical` every 5,000 ms. This causes up to a 5-second delay for live NIFTY tick updates.
- **Latency Contribution**: ~1,000–5,000 ms
- **Action for Next Sprint**: Transition NIFTY spot tick and Option Chain updates from 5s HTTP polling to direct real-time WebSocket push broadcasting.

### Bottleneck 2: Server Canonical State Rebuild Frequency (1,000 ms Loop)
- **Path**: `src/state_engine/canonical_builder.py` &rarr; `rebuild_canonical_state()`
- **Issue**: Canonical state is rebuilt on a fixed 1-second timer loop rather than immediately on incoming tick event triggers.
- **Latency Contribution**: ~100–1,000 ms
- **Action for Next Sprint**: Convert canonical state updates to event-driven state delta dispatchers triggered on tick receipt.

### Bottleneck 3: Large Monolithic Canonical State Payload (~45 KB JSON)
- **Path**: `/api/state/canonical`
- **Issue**: The entire canonical state (including market, options, news, macro, and intelligence trees) is serialized into a single monolithic JSON payload (~45 KB).
- **Latency Contribution**: ~80–180 ms network transfer and JSON parse time on client.
- **Action for Next Sprint**: Implement scoped state subscription channels (e.g. `channel:market_ticks`, `channel:options_top_strikes`, `channel:news_alerts`) for targeted lightweight JSON deltas (~1–3 KB).

### Bottleneck 4: Market Intelligence Derivation Sweep (15,000 ms Interval)
- **Path**: `src/intelligence_engine/scenario_resolver.py`
- **Issue**: Forward outlook scenario scoring runs every 15 seconds.
- **Latency Contribution**: Up to 15 seconds for scenario score re-evaluations after a major price break.
- **Action for Next Sprint**: Trigger instant scenario re-scoring when spot price crosses key technical levels (VWAP, Day High/Low, Pivot R1/S1).

---

## 2. Target Latency Metrics for Next Sprint

| Data Pipeline | Current Latency | Target Post-Optimization Latency |
| :--- | :--- | :--- |
| **NIFTY Tick Delivery to UI** | ~1,000–5,000 ms | `< 100 ms` |
| **Option Chain OI & LTP Sync** | ~5,000 ms | `< 250 ms` |
| **Market Status Change Sync** | ~5,000 ms | `< 100 ms` |
| **Live Assistant Evidence Refresh** | ~5,000 ms | `< 500 ms` |
