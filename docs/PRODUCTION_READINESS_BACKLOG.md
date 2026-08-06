# Production Readiness Backlog

* **Project Name:** Nifty Option Trading Workstation
* **Date:** July 15, 2026
* **Version:** 1.0.0-Beta
* **Review Sources:** Developer Architecture Review, Paper Trading & First-Time User Review, Professional Live Trading Review
* **Overall Production Readiness Score:** **47 / 100**

## Executive Summary
This document serves as the master backlog and single source of truth for all outstanding tasks required to elevate the Nifty Option Trading Workstation to a production-ready, retail-grade options trading terminal. 

While the system's real-time state synchronization (via persistent WebSocket broadcast and stdio daemon IPC channels) is highly optimized and layouts are safe from browser-level exceptions, **Version 1.0 is not production-ready.** Live order execution is unimplemented and raises `NotImplementedError`, option chain pricing parameters are static placeholders, ex-dates are hardcoded, and the core analytics inference pipelines are bypassed in the live daemon. Addressing these architectural and functional blockers is the primary requirement for production deployment.

---

## SECTION 1: PROJECT STATUS

* **Overall Completion:** **58%**
* **Current Strengths:**
  - **WebSocket State Broadcast:** Unified and lightweight real-time state syncing with 0ms component fetch overhead.
  - **Simulated Paper Trading:** Robust local simulated ledger (`virtual_execution.py`) with MTM ticks resolved dynamically.
  - **Layout Crash Safety:** Defensive guarding layers (`safeHelpers.ts`) preventing React UI thread exceptions.
* **Current Weaknesses:**
  - **No Live Order Execution:** Order endpoints inside the `KiteBrokerGateway` raise `NotImplementedError`.
  - **Mock Option Chain Data:** Option Greeks, Volume, and Open Interest are statically calculated from hardcoded mock dictionaries.
  - **Bypassed Model Inference:** Live market data is not passed to the Python analytical pipelines.
* **Biggest Production Risks:**
  - **Execution Failures:** Placing real trades in Live mode will raise exceptions, preventing position entries or emergency stops.
  - **Stale Contracts Recommendation:** The terminal continues to suggest expired contracts after ex-dates due to hardcoded weekly/monthly date structures.
* **Readiness Matrix:**
  - **Development Mode:** 100% (Fully ready for local offline simulation).
  - **Paper Trading Mode:** 90% (Operational, but requires visual badges to separate mock objects from real portfolio assets).
  - **Live Trading Mode:** 20% (Blocked; unimplemented order gateways).

---

## SECTION 2: WHAT IS COMPLETE

### Frontend
* **useWorkstationState Context:** Centralized React state controller linked to the persistent WebSocket client.

### Backend
* **Standard I/O IPC Bridge:** Fast stdin/stdout interface inside `server_bridge.py` running in `--action daemon` mode to interact with Express.

### Broker
* **Profile & Margin Sync:** Successful retrieval of authenticated Zerodha balances, user names, and API cache status.

### Paper Trading
* **Virtual Execution Ledger:** Complete position and cash ledger that persists simulated transactions to `virtual_portfolio.json`.

### Infrastructure
* **Vite Production Bundler:** Fully configured package pipeline generating minified, type-safe chunks.

### UI
* **Real-Time Clock:** Live IST timezone header clock rendering dynamic market phases.

### Performance
* **Zero-Spinner Tab Transitions:** Cached client-side route changes with zero redundant API calls.

---


### Architecture
* **Bypassed Pipeline Modules:** Core model inference components are skipped. Live parameters are built using mock shapes.
  - *Affected Modules:* `server_bridge.py`, `historical_runner.py`
  - *Priority:* High

### State Management & Synchronization
* **Unused State Variables:** The `connectionState` and `marketConnection` variables are resolved but never consumed by layout pages.
  - *Affected Modules:* `WorkstationStateContext.tsx`
  - *Priority:* Medium

### Broker Integration & Live Trading
* **Unimplemented Live Execution:** Places, modifies, and cancels order functions raise `NotImplementedError` in `KiteBrokerGateway`.
  - *Affected Modules:* `kite_broker.py`, `broker_service.py`
  - *Priority:* Critical

### Market Feed & Analysis
* **Static Options Greeks & Volumes:** Open Interest, Volumes, and Implied Volatility parameters are hardcoded numbers.
  - *Affected Modules:* `server_bridge.py`
  - *Priority:* Critical

### Paper Trading & UX
* **Merged Positions Lists:** Simulated net positions are merged with live positions in execution tables without visual badges.
  - *Affected Modules:* `positions_service.py`, `ExecutionWorkspace.tsx`, `LivePortfolio.tsx`
  - *Priority:* Critical

---

## SECTION 4: PRODUCTION BLOCKERS

* **Blocker 1: Live Order routing unimplemented**
  - *Problem:* Real transactions fail because KiteConnect API order routes raise `NotImplementedError`.
  - *Evidence:* `kite_broker.py` lines 500-508.
  - *Impact:* The terminal cannot place trades on the exchange.
  - *Dependencies:* None.

* **Blocker 2: Hardcoded Option Expiry Dates**
  - *Problem:* Contract dates are hardcoded strings. Suggests expired instruments after the weekly ex-date passes.
  - *Evidence:* `server_bridge.py` lines 158-162.
  - *Impact:* The terminal suggests expired contracts, resulting in broker order rejections.
  - *Dependencies:* None.

* **Blocker 3: Statically Simulated Options Greeks & Volume**
  - *Problem:* Implied Volatility and Open Interest metrics are hardcoded integers.
  - *Evidence:* `server_bridge.py` lines 1247-1290.
  - *Impact:* The trader cannot evaluate contract liquidity or bid-ask spreads.
  - *Dependencies:* None.

---

## SECTION 5: HIGH PRIORITY IMPROVEMENTS

* **1. Visual Badges for Virtual Transactions:** Distinguish virtual paper orders from real holdings with a `"VIRTUAL"` layout badge.
* **2. Operating Mode Rename:** Simplify `DEVELOPMENT` vs. `SANDBOX` vs. `PRACTICE` vs. `LIVE` into: `Offline Practice`, `Live Practice`, and `Live Trading` to prevent onboarding confusion.
* **3. Emergency Panic Button:** Add a prominent "Close All Positions" panic button to immediately exit volatile option trades.

---

## SECTION 6: MEDIUM PRIORITY IMPROVEMENTS

* **1. Active Tab Memory:** Cache the user's active tab in `localStorage` so that refreshing the browser maintains their current screen context.
* **2. Workspace Mode State Persistence:** Save workspace mode changes to a persistent config file on disk so they survive Express server restarts.

---

## SECTION 7: LOW PRIORITY / FUTURE ENHANCEMENTS

* **1. Console Log Suppression:** Clean up development debug statements in browser console logs during live WebSocket connections.
* **2. Tab Consolidation:** Merge **Performance** and **Trading Journal** into a single analytics panel.

---

## SECTION 8: TECHNICAL DEBT

* **Bypassed inference engine:** Model pipelines are backtest-only; live daemon generates static dictionary mockups.
* **Unused State hooks:** Destructured variables in `DashboardLayout.tsx` are unreferenced.
* **Hardcoded IST Holiday calendars:** Ex-dates are hardcoded in python instead of resolved dynamically.

---

## SECTION 9: REMAINING MOCK / PLACEHOLDER IMPLEMENTATIONS

| Location | Current Placeholder | Production Replacement | Priority |
| :--- | :--- | :--- | :--- |
| `kite_broker.py` (L500) | `raise NotImplementedError` | Implement KiteConnect API order routes. | **Critical** |
| `server_bridge.py` (L158) | Hardcoded expiry dates | Dynamic date calculator using active instrument cache. | **Critical** |
| `server_bridge.py` (L1247) | Static Option Chain Greeks | Live options ticker websocket connection. | **Critical** |
| `server_bridge.py` (L214) | Statically calculated reports | Run live inferences on python pipelines. | **High** |

---

## SECTION 10: PROJECT COMPLETION MATRIX

| Module | Completion | Status |
| :--- | :--- | :--- |
| Frontend | 90% | Stable |
| Backend | 75% | Functional |
| Broker Integration | 65% | Partial |
| Market Feed | 70% | Partial (Live Spot works; Option Greeks are mock) |
| Paper Trading | 95% | Stable |
| Live Trading | 30% | Blocked |
| Analytics Engine | 20% | Bypassed (Backtest-only) |
| Risk Engine | 20% | Bypassed (Backtest-only) |
| Testing | 50% | Needs Work |
| Performance | 80% | Stable |
| **Overall Workstation** | **58%** | **Needs Integration Work** |

---

## SECTION 11: IMPLEMENTATION ROADMAP

### Phase 1: Critical Production Blockers
1. **Task 1.1:** Implement `place_order`, `modify_order`, and `cancel_order` in `KiteBrokerGateway`.
2. **Task 1.2:** Write a dynamic option ex-date resolver that parses exchange lists.
3. **Task 1.3:** Subscribe the WebSocket ticker to live options feeds to update premium LTPs, IV, and Volume.
4. **Task 1.4:** Add visual `VIRTUAL` / `LIVE` badges to Positions/Orders listings.

### Phase 2: High Priority
1. **Task 2.1:** Integrate real-time pipelines (`ConfidencePipeline`, `DecisionPipeline`, etc.) in the background daemon.
2. **Task 2.2:** Add the Emergency Close All panic button to Execution panels.

### Phase 3: Production Polish
1. **Task 3.1:** Implement active tab caching in `localStorage`.
2. **Task 3.2:** Persist Workspace Mode choices on backend disk.

---

## SECTION 12: FINAL VERDICT

* **Workstation Readiness:** **NOT READY FOR PRODUCTION**
* **Recommendation:** **DO NOT RELEASE VERSION 1.0 TODAY**
* **Required Actions:** Live order placing routing, dynamic ex-date calendars, and live option chain ticker subscriptions must be integrated before launching this terminal to trade live options.
