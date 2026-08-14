# AIR ARDHAMIND — COLD START LATENCY AUDIT

## CURRENT TIMELINE:
- **T0 (0.0s): Browser Navigation** — User opens `https://ardhamind.projectair.in` in a fresh browser tab.
- **T+0.1s: HTML Response** — Express serves `dist/index.html` (422 bytes).
- **T+0.4s: JS/CSS Load** — Browser fetches monolithic JS bundle `dist/assets/index-WzggJx1H.js` (457 KB uncompressed) and CSS bundle `dist/assets/index-Cuxcomxx.css` (82 KB).
- **T+0.5s: React Mount** — `App.tsx` mounts `WorkstationStateProvider` and `DashboardLayout`. UI shell renders immediately with default fallback indicators (`--`, `UNAVAILABLE`).
- **T+0.6s: REST Sync Waterfall** — `WorkstationStateContext` invokes `syncBroker(true)`, triggering a blocking REST `fetch("/api/workspace")`.
- **T+1.2s: REST Sync Resolves** — `/api/workspace` returns initial Node in-memory state.
- **T+1.3s: Browser WebSocket Connect** — Frontend initiates WebSocket connection `wss://ardhamind.projectair.in/api/ws` only *after* `syncBroker(true)` completes (`syncBroker(true).finally(connect)`).
- **T+1.4s: WebSocket Handshake Complete** — WS upgrade completes at `/api/ws`. Node immediately sends current in-memory state (`{ type: "state", data: workstationState }`).
- **T+1.5s - T+55.0s: Python Daemon Cold-Start Blocking** — (On service startup/restart) `src/server_bridge.py` executes **triple synchronous pipeline hydration**:
  1. Global scope `perform_cold_start_hydration()` runs `MacroPipeline().run()` and `NewsPipeline().run()` synchronously.
  2. `run_daemon()` startup sequence re-runs `NewsPipeline().run()` and `MacroPipeline().run()` synchronously before starting the main event loop.
  3. `run_initial_refreshes()` thread runs them a third time.
  External HTTP requests to news RSS and macro providers stall Python daemon startup for 30–50 seconds before tick #1 of the `while True` loop executes.
- **T+55.0s: First Python State Push** — Python daemon completes initial loop tick and prints `{ type: "state", data: ... }` to stdout.
- **T+55.1s: Node WS Broadcast** — Node reads stdout line, updates `workstationState`, and broadcasts to connected WebSocket clients.
- **T+55.2s: First Canonical State Received** — React receives WS payload and updates `canonicalState`.
- **T+55.3s: NIFTY Spot Rendered** — NIFTY spot price populates in `NiftyLiveWorkspace`.
- **T+55.5s: Breadth & Options Rendered** — Constituent breadth, Options PCR, and Max Pain populate.
- **T+56.0s: Workspace Usable** — Primary NIFTY Live workstation is fully functional.
- **T+60.0s+: Secondary Providers Enriched** — Background news and macro refreshes continue.

## PRIMARY BOTTLENECK:
**Redundant Synchronous Pipeline Hydration on Python Daemon Boot (`src/server_bridge.py`):**
The Python daemon executes external HTTP requests for `NewsPipeline` and `MacroPipeline` **synchronously twice sequentially** (once at module import scope `perform_cold_start_hydration()` lines 74–137 and once at `run_daemon()` startup lines 532–554) before entering the main loop (`while True`). External API timeouts and network latency block the daemon from starting its tick loop, delaying the first canonical state broadcast by 30 to 50 seconds.

## SECONDARY BOTTLENECKS:
1. **Frontend WebSocket Connection Waterfall (`src/frontend/context/WorkstationStateContext.tsx` line 1196):**
   The frontend delays WebSocket initialization by chaining `syncBroker(true).finally(connect)`, forcing the browser to wait for a REST roundtrip to `/api/workspace` before attempting a WebSocket handshake.
2. **Synchronous News/Macro Refreshes in Main Loop (`src/server_bridge.py` lines 1140–1171):**
   Every 300 seconds, the 3-second daemon tick blocks synchronously inside `NewsPipeline().run()` and `MacroPipeline().run()`, causing 5–15 second freezes in state push heartbeats.
3. **Monolithic JS Bundle / Eager Workspace Loading (`src/frontend/layout/DashboardLayout.tsx` lines 5–14):**
   All workspace components (Nifty Live, Pre-Market Planner, Today's Analysis, Forward Outlook, Market Pulse, News, Settings) are eagerly imported, forcing a 457 KB JS bundle parse on initial page load.

## ROOT CAUSE:
The Python daemon architecture couples core real-time market data state generation (NIFTY spot, ticks, status) with heavy secondary provider enrichment (News RSS scraping, Macro economic events). Executing secondary network pipelines synchronously on the main daemon thread before starting the tick loop blocks the canonical state push. Concurrently, the React frontend unnecessarily waits for a REST workspace fetch before establishing its WebSocket feed.

## CLASSIFICATION:
**P1** (Cold-start latency prevents NIFTY Live usability within target 5s SLO).

## MINIMAL REPAIR:
1. **Python Daemon Non-Blocking Bootstrap (`src/server_bridge.py`):**
   Remove synchronous `NewsPipeline().run()` and `MacroPipeline().run()` calls from global import scope `perform_cold_start_hydration()` and `run_daemon()` startup. Rely on warm disk cache (`.cache/`) for initial snapshot and run fresh news/macro pipeline fetches exclusively in background threads (`run_initial_refreshes()`). Wrap the periodic 300s news/macro refreshes inside `while True` in detached threads so they never block the 3-second daemon loop tick.
2. **Frontend Direct Concurrent WebSocket Initialization (`src/frontend/context/WorkstationStateContext.tsx`):**
   Connect WebSocket immediately on mount in parallel with REST hydration instead of chaining `syncBroker(true).finally(connect)`. Upon WS open, Node immediately pushes the latest in-memory `workstationState` to the React client.
3. **Route / Component Code-Splitting (`src/frontend/layout/DashboardLayout.tsx`):**
   Convert non-critical workspace tab imports (`PreMarketPlannerWorkspace`, `TomorrowWorkspace`, `NewsUpdatesWorkspace`, etc.) to `React.lazy()` with `Suspense`, reducing initial JS bundle size from 457 KB to ~150 KB.

## EXPECTED LATENCY AFTER REPAIR:
- **Shell render:** <= 1.2s
- **WebSocket connect:** <= 1.8s
- **First canonical snapshot pushed:** <= 2.2s
- **NIFTY Live usable:** <= 3.0s (Target SLO <= 5s achieved)
- **Secondary enrichment:** Fully asynchronous background hydration

## FILES/FUNCTIONS:
- `src/server_bridge.py`:
  - `perform_cold_start_hydration()`
  - `run_daemon()`
- `src/frontend/context/WorkstationStateContext.tsx`:
  - `WorkstationStateProvider` / `useEffect` initialization (`line 1196`)
- `src/frontend/layout/DashboardLayout.tsx`:
  - Component imports (`lines 5–14`)

## TESTS REQUIRED:
- `.venv/bin/python -m pytest tests/test_null_semantics_audit_repairs.py`
- `.venv/bin/python -m pytest tests/test_e4b_read_only_boundary.py`
- `.venv/bin/python -m pytest` (full regression test suite)
- `npx tsc --noEmit`
- `npm run build`
