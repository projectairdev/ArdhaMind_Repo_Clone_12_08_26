# Dashboard-Wide E2E Audit — Connectivity, Live Feed & Cross-Tab Sync

### 1. Summary

A comprehensive, read-only dashboard-wide forensic audit was conducted across the application's global connectivity layer, real-time WebSocket transport, and cross-tab data synchronization architecture. 

The audit focused on the core system plumbing:
- React Context Providers: [src/App.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/App.tsx), [CanonicalStateContext.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/CanonicalStateContext.tsx), [WorkstationStateContext.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/WorkstationStateContext.tsx), and [NavigationContext.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/NavigationContext.tsx)
- Server WebSocket Hub & Express Upgrades: [server.ts](file:///p:/ArdhaMind-Local/ardhamind/staging/server.ts)
- Upstream Kite Streaming Layer: [streaming_orchestrator.py](file:///p:/ArdhaMind-Local/ardhamind/staging/src/broker/services/streaming_orchestrator.py), [subscription_manager.py](file:///p:/ArdhaMind-Local/ardhamind/staging/src/broker/services/subscription_manager.py), and [kite_ticker_adapter.py](file:///p:/ArdhaMind-Local/ardhamind/staging/src/broker/adapters/kite_ticker_adapter.py)
- Cross-tab consumption across NIFTY, Metrics, Options, Predictions, Market Intelligence, and News & Updates.

The audit revealed **3 Critical**, **3 High**, **3 Medium**, and **2 Low** severity defects. The most urgent discovery is that **the application runs two competing WebSocket connections and two separate state management stores simultaneously in every browser tab**:
- In `src/App.tsx`, `<CanonicalStateProvider>` and `<WorkstationStateProvider>` are both mounted at the root. Each independently instantiates `new WebSocket("/api/ws")` and opens two parallel, redundant WebSocket channels to the Node server for every open tab.
- The two contexts independently deserialize ticks and state envelopes into separate React state trees (`liveEnvelope` vs `canonicalState`), causing race conditions and UI drift between components that consume `useCanonicalState()` versus `useWorkstationState()`.
- While `WorkstationStateContext` listens for server-dispatched `auth_event` messages (e.g. broker disconnects or token expirations), `CanonicalStateContext` completely ignores `auth_event`. As a result, when Kite disconnects or the access token expires, components powered by `CanonicalStateContext` (NIFTY, Predictions, Market Intelligence) remain in a ghost "connected" state until a full page reload or forced poll occurs.
- When market data is unavailable, different tabs render completely contradictory hardcoded fallback values for the exact same metric: India VIX falls back to `10.68` on Metrics, `12.5` on Options, and `13.20` on Market Intelligence; PCR falls back to `0.94` on Metrics, `1.08` on Options, and `1.02` on Market Intelligence.

| Severity | Finding Count | Primary Impact Area |
| :--- | :---: | :--- |
| **Critical** | **3** | Dual competing WebSockets & dual state stores, unhandled `auth_event` in Canonical context (ghost sessions), divergent cross-tab fallbacks |
| **High** | **3** | Redundant dual REST boot fetches, strictly one-way WebSocket preventing on-demand option subscriptions, fragmented offline error handling |
| **Medium** | **3** | Unbounded 1-minute candle accumulation in memory, competing reconnect timers (2000ms vs 1500ms), drifted timestamp presentation |
| **Low** | **2** | Production console log noise in tick path, missing `window.navigator.onLine` event listeners |
| **Total** | **11** | |

---

### Cross-Tab Value Sync Matrix

The matrix below inventories every major data point that is rendered in more than one location across the dashboard, verifying source parity and synchronization behavior:

| Data Point | Locations Found | Underlying State Source | In Sync? | Synchronization Notes & Discrepancies |
| :--- | :--- | :--- | :---: | :--- |
| **NIFTY Spot / LTP** | Top Bar, NIFTY Live, Metrics, Options, Predictions, Market Intelligence | `envelope.market.nifty.last_price` | **PARTIAL** | In sync during active stream. On missing data / boot, Options falls back to synthetic `24200.00` while NIFTY displays `—`. |
| **India VIX** | Top Bar, Metrics (Tier 2), Options Strip, Live Guide (Pillar 5) | `envelope.market.vix.last_price` | **NO (ON FALLBACK)** | **Severe Discrepancy:** When missing, Metrics displays `10.68`, Options displays `12.5`, Live Guide displays `13.20`, Top Bar displays `—`. |
| **Put-Call Ratio (PCR)**| Metrics (Tier 1), Options Intelligence, Live Guide (Pillar 4) | `envelope.options.pcr` | **NO (ON FALLBACK)** | **Severe Discrepancy:** When missing, Metrics displays `0.94`, Options displays `1.08`, Live Guide displays `1.02`. |
| **Market Breadth (Adv/Dec)**| NIFTY Live, Morning Workspace, Metrics (Tier 1), Live Guide (Pillar 2) | `envelope.market.breadth` | **YES** | All views consistently resolve advances/declines and ratio from `market.breadth`. |
| **Market Sentiment / Tone** | Metrics (Tier 2), Morning Plan, Live Guide, News & Updates | Multiple Independent Derivations | **NO** | Metrics displays percentage score (`68% Bullish`), Morning Plan displays string (`BALANCED CUES`), News displays integer delta (`+4 (POS)`). |
| **Sector Leadership** | Metrics (Tier 5), Live News Feed Ribbon, Live Guide (Pillar 3) | `market.sectors` vs Static String | **NO** | Metrics and News read real sectors; Live Guide renders hardcoded sentence: *"Broad-based sector participation and active institutional flows observed."* |
| **FII / DII Net Flow** | Metrics (Tier 3), News & Updates Live Wire | `envelope.institutional_flow` vs Hardcoded | **NO** | Metrics reads real EOD cash figures; News & Updates displays hardcoded fake numbers in default stories (`+₹2,145 Cr`, `₹1,850 Cr`). |
| **Session High / Low** | NIFTY Hero, Options Positioning Map, Predictions Funnel, Tomorrow Plan | `price_structure.high/low` | **YES** | All modules resolve from `price_structure` via `resolveAuthoritativeMarketState()`. |
| **Anchor VWAP** | NIFTY Hero, Morning Plan, Live Guide, Tomorrow Plan | `price_structure.vwap` | **YES** | Consistently resolved from authoritative session mean. |

---

### 2. Forensic Findings by Dimension (1–10)

```
================================================================================
DIMENSION 1: GLOBAL CONNECTION ARCHITECTURE
================================================================================
```

#### Finding 1.1: Dual Competing WebSockets & Parallel State Stores Running Concurrently in Every Tab
* **File & Lines:** [src/App.tsx:16-22](file:///p:/ArdhaMind-Local/ardhamind/staging/src/App.tsx#L16-L22), [src/frontend/context/CanonicalStateContext.tsx:551-565](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/CanonicalStateContext.tsx#L551-L565), [src/frontend/context/WorkstationStateContext.tsx:1230-1238](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/WorkstationStateContext.tsx#L1230-L1238)
* **Actual Code:**
  In `App.tsx`:
  ```tsx
  <ThemeProvider>
    <CanonicalStateProvider>
      <WorkstationStateProvider>
        <NavigationProvider>
          <DashboardLayout />
        </NavigationProvider>
      </WorkstationStateProvider>
    </CanonicalStateProvider>
  </ThemeProvider>
  ```
  In `CanonicalStateContext.tsx:563`:
  ```tsx
  ws = new WebSocket(`${protocol}//${host}/api/ws`);
  ```
  In `WorkstationStateContext.tsx:1237`:
  ```tsx
  ws = new WebSocket(`${protocol}//${host}/api/ws`);
  ```
* **Why it is wrong:** The root `App.tsx` wraps the dashboard with both `CanonicalStateProvider` and `WorkstationStateProvider`. Each provider executes its own `useEffect` on mount and creates its own independent `new WebSocket("/api/ws")` connection. This means every single open browser tab opens **two parallel WebSocket connections** to the Express backend. Both connections receive the same messages, parse JSON independently, and update two distinct React state trees (`liveEnvelope` vs `canonicalState`), doubling client socket overhead and creating race conditions between tabs and subcomponents.
* **Severity:** **Critical**

```
================================================================================
DIMENSION 2: SUBSCRIPTION LIFECYCLE ACROSS TAB SWITCHES
================================================================================
```

#### Finding 2.1: Completely One-Way Client WebSocket Preventing On-Demand Option Subscriptions
* **File & Lines:** [src/frontend/context/CanonicalStateContext.tsx:563-715](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/CanonicalStateContext.tsx#L563-L715), [src/frontend/context/WorkstationStateContext.tsx:1237-1420](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/WorkstationStateContext.tsx#L1237-L1420)
* **Actual Code:**
  Neither `CanonicalStateContext` nor `WorkstationStateContext` contains a single `ws.send()` call. The WebSocket transport is strictly one-way downstream (`ws.onmessage`).
* **Why it is wrong:** When a user navigates between tabs (e.g. from NIFTY $\rightarrow$ Options Intelligence), the client cannot request subscriptions for option strikes or newly inspected instruments. The backend only subscribes to the 5 default index tokens (`DEFAULT_INDICES` in `subscription_manager.py:9-26`) and its own calculated ATM window. When a user opens an expiry or strike outside the backend's default window, the client is unable to subscribe to the live stream, leading to missing data and forcing the Options tab to generate synthetic strikes.
* **Severity:** **High**

```
================================================================================
DIMENSION 3: AUTH / SESSION & TOKEN REFRESH
================================================================================
```

#### Finding 3.1: Unhandled Auth & Disconnect Events in Canonical State Context Causing Ghost Sessions
* **File & Lines:** [src/frontend/context/CanonicalStateContext.tsx:570-594](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/CanonicalStateContext.tsx#L570-L594), [server.ts:976-992](file:///p:/ArdhaMind-Local/ardhamind/staging/server.ts#L976-L992)
* **Actual Code:**
  In `server.ts:976`:
  ```typescript
  wss.clients.forEach((client) => {
    client.send(JSON.stringify({
      type: "auth_event",
      brokerState: "DISCONNECTED",
      feedState: "DISCONNECTED",
      timestamp: new Date().toISOString()
    }));
  });
  ```
  In `CanonicalStateContext.tsx:570`:
  ```tsx
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "SESSION_PHASE_CHANGED") { ... }
    else if (msg.type === "canonical_envelope") { ... }
    else if (msg.type === "state") { ... }
    else if (msg.type === "live_event" || msg.type === "tick") { ... }
    // NOTE: "auth_event" is completely ignored!
  };
  ```
* **Why it is wrong:** When Kite disconnects or an access token expires (`ExpiredAccessTokenError`), the Node server broadcasts an `auth_event` message (`{ type: "auth_event", brokerState: "DISCONNECTED" }`). While `WorkstationStateContext` catches this event, `CanonicalStateContext` has no handler for `auth_event`. Consequently, any workspace powered by `CanonicalStateContext` (NIFTY, Predictions, Market Intelligence) fails to register the broker disconnection and continues rendering stale market data under the illusion that the session is still active.
* **Severity:** **Critical**

```
================================================================================
DIMENSION 4: RECONNECTION BEHAVIOR
================================================================================
```

#### Finding 4.1: Competing WebSocket Reconnect Backoff Timers (2000ms vs 1500ms)
* **File & Lines:** [src/frontend/context/CanonicalStateContext.tsx:703](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/CanonicalStateContext.tsx#L703), [src/frontend/context/WorkstationStateContext.tsx:1406](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/WorkstationStateContext.tsx#L1406)
* **Actual Code:**
  - In `CanonicalStateContext.tsx:703`: `reconnectTimeout = setTimeout(connectWebSocket, 2000);`
  - In `WorkstationStateContext.tsx:1406`: `reconnectTimeout = setTimeout(connect, 1500);`
* **Why it is wrong:** When the network connection drops, the two contexts reconnect at different intervals (1500ms vs 2000ms). When connection is restored, `WorkstationStateContext` re-establishes its socket 500ms earlier and triggers `acceptCanonicalState()`, while `CanonicalStateContext` reconnects later. This causes staggered renders where different parts of the same page update at different times, creating visual glitching.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 5: CROSS-TAB VALUE SYNC MATRIX
================================================================================
```

#### Finding 5.1: Cross-Tab Value Discrepancies & Divergent Hardcoded Fallbacks for Critical Market Telemetry
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:327, 397](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L327), [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:274](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L274), [src/frontend/components/intelligence/LiveGuideView.tsx:445, 452](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/LiveGuideView.tsx#L445)
* **Actual Code:**
  - **India VIX:**
    - Metrics Tab: `vixVal ?? 10.68`
    - Options Tab: `vixVal ?? 12.5`
    - Live Guide Tab: `vixVal ?? "13.20"`
  - **Put-Call Ratio (PCR):**
    - Metrics Tab: `pcr ?? 0.94`
    - Options Tab: `pcr ?? "1.08"`
    - Live Guide Tab: `pcr ?? "1.02"`
* **Why it is wrong:** When live data is not received, the tabs do not fall back to `null` or a shared constant. Instead, each component author has embedded their own arbitrary numbers directly into the component code. A trader navigating between Metrics, Options, and Market Intelligence observes three completely different values for India VIX and PCR at the exact same moment.
* **Severity:** **Critical**

```
================================================================================
DIMENSION 6: GLOBAL STATE MANAGEMENT
================================================================================
```

#### Finding 6.1: Redundant Initial REST Boot Requests Duplicating Identical State Envelopes
* **File & Lines:** [src/frontend/context/CanonicalStateContext.tsx:500-520](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/CanonicalStateContext.tsx#L500-L520), [src/frontend/context/WorkstationStateContext.tsx:1140-1160](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/WorkstationStateContext.tsx#L1140-L1160)
* **Actual Code:**
  On page mount:
  1. `CanonicalStateContext` issues `fetch("/api/canonical-envelope")`.
  2. `WorkstationStateContext` issues `fetch("/api/state")`.
* **Why it is wrong:** On application bootstrap, the browser issues two heavy HTTP GET requests in parallel to fetch substantially identical market state payloads, immediately before both WebSocket connections connect and send the same state again. This quadruples the network bandwidth consumed during cold start.
* **Severity:** **High**

```
================================================================================
DIMENSION 7: GLOBAL TIMESTAMP CONSISTENCY
================================================================================
```

#### Finding 7.1: Inconsistent "Last Updated" Clock Resolution and Timezone Presentation Across Modules
* **File & Lines:** [src/frontend/components/canonical/nifty/LiveWorkspace.tsx:60](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/nifty/LiveWorkspace.tsx#L60), [src/frontend/context/CanonicalStateContext.tsx:687](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/CanonicalStateContext.tsx#L687), [src/frontend/utils/canonicalNewsAdapter.ts:485](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalNewsAdapter.ts#L485)
* **Actual Code:**
  `LiveWorkspace.tsx` uses `formatTime(lastUpdated, "HH:mm:ss")` from client clock, while the Top Bar formats exchange timestamps from `tick.exchange_timestamp`, and `canonicalNewsAdapter.ts` programmatically calculates relative offsets from `Date.now()`.
* **Why it is wrong:** Clocks displayed across different tabs do not derive from a single synchronized server timestamp. If the user's system clock is skewed by 2 minutes, local time displays drift relative to exchange execution timestamps.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 8: APP-WIDE ERROR / OFFLINE HANDLING
================================================================================
```

#### Finding 8.1: Fragmented and Inconsistent App-Wide Offline / Feed Error Communication
* **File & Lines:** [src/frontend/layout/DashboardLayout.tsx:156-166](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/layout/DashboardLayout.tsx#L156-L166), [src/frontend/components/NiftyLiveWorkspace.tsx:1787](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/NiftyLiveWorkspace.tsx#L1787), [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:788](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L788)
* **Actual Code:**
  `DashboardLayout.tsx:156` only displays an alert if `workspaceContext.brokerState === "TOKEN_EXPIRED"`. If the WebSocket drops or the feed enters `DEGRADED`, no global banner is rendered. Individual tabs handle offline states inconsistently: `NiftyLiveWorkspace` shows a large error banner, while `OptionsIntelligenceWorkspace` falsely continues to show "Sub-Second Stream", and `NewsWorkspace` shows no indication of feed failure.
* **Why it is wrong:** The app lacks a unified, global offline/degraded mode banner. A user on the Options or Market Intelligence tab is not alerted that the global market feed is down.
* **Severity:** **High**

```
================================================================================
DIMENSION 9: LONG-SESSION MEMORY & PERFORMANCE
================================================================================
```

#### Finding 9.1: Unbounded 1-Minute Candle Accumulation in Memory During Extended Sessions
* **File & Lines:** [src/frontend/context/CanonicalStateContext.tsx:610-630](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/CanonicalStateContext.tsx#L610-L630)
* **Actual Code:**
  ```tsx
  const existing1m = base.candles?.["1m"] ? [...base.candles["1m"]] : [];
  if (existing1m.length > 0) {
    ...
  } else {
    existing1m.push({ ... });
  }
  ```
* **Why it is wrong:** In `CanonicalStateContext`, incoming ticks append forming 1-minute candles to `base.candles["1m"]` without any maximum length cap or rolling window eviction. During an entire 6.25-hour trading session (375 minutes), this array continuously expands. Because every tick copies the entire array (`[...base.candles["1m"]]`), the memory allocation and garbage collection overhead increases monotonically over the trading day.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 10: CONSOLE & NETWORK HYGIENE (APP-WIDE)
================================================================================
```

#### Finding 10.1: Persistent Console Log Noise in Production Ingestion Path
* **File & Lines:** [src/frontend/context/WorkstationStateContext.tsx:1236, 1241, 1252](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/WorkstationStateContext.tsx#L1236)
* **Actual Code:**
  ```tsx
  console.log(`Connecting to workstation WebSocket: ${wsUrl}`);
  console.log("Workstation WebSocket connected.");
  console.log("[BOOT-FE] first WS snapshot received");
  ```
* **Why it is wrong:** Unconditional `console.log` statements remain active in production code. During reconnect cycles, these logs spam the browser developer console.
* **Severity:** **Low**

#### Finding 10.2: Missing Global Network Online/Offline Event Handlers
* **File & Lines:** [src/frontend/context/CanonicalStateContext.tsx:551-715](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/context/CanonicalStateContext.tsx#L551-L715)
* **Actual Code:**
  Neither context listens to `window.addEventListener("online")` or `window.addEventListener("offline")`.
* **Why it is wrong:** When a device loses internet connectivity and regains it (e.g. laptop wake from sleep or Wi-Fi reconnect), the browser marks the connection offline immediately. Without `window.online` event listeners, the client waits for the 2000ms WebSocket timeout to fail before initiating reconnect procedures.
* **Severity:** **Low**

---

### 3. Verified Clean

The following items were explicitly audited and verified to be clean of defects:

* **Single Upstream KiteTicker Invariant:** Verified clean. In `StreamingOrchestrator` (`src/broker/services/streaming_orchestrator.py:25-30`), a strict singleton pattern ensures that exactly one upstream KiteTicker instance connects to Zerodha Kite at any time, with generation ID guards (`generation_id`) preventing connection leaks.
* **Zero Client-Side Broker Mutation:** Verified clean. Neither `CanonicalStateContext` nor `WorkstationStateContext` exposes any order placement, trade execution, or account mutation endpoints to browser components.
* **Token Isolation & Credential Security:** Verified clean. Neither Kite API keys, access tokens, nor user session secrets are broadcast over the browser `/api/ws` channel or stored in client `localStorage`.
* **WebSocket Heartbeat Supervision:** Verified clean. The server-side WebSocket implementation actively handles connection dropouts and client disconnects without hanging sockets.
* **Authoritative Anchor VWAP Calculation:** Verified clean. Session VWAP resolves consistently from `price_structure.vwap` across all tabs without client-side divergence.
