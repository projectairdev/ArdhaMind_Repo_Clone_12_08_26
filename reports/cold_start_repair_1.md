# AIR ARDHAMIND — COLD-START REPAIR 1 REPORT

## CHANGES:
1. Removed synchronous `MacroPipeline().run()` and `NewsPipeline().run()` calls from `perform_cold_start_hydration()` in `src/server_bridge.py`.
2. Removed redundant synchronous `NewsPipeline().run()` and `MacroPipeline().run()` calls from `run_daemon()` startup sequence.
3. Created non-blocking background refresh helper functions (`_bg_refresh_news` and `_bg_refresh_macro`) guarded by non-blocking lock acquisition (`news_refresh_lock.acquire(blocking=False)` and `macro_refresh_lock.acquire(blocking=False)`).
4. Refactored `run_initial_refreshes()` to spawn `_bg_refresh_news` and `_bg_refresh_macro` in detached daemon background threads once upon daemon start.
5. Replaced synchronous 300-second news and macro compilation inside `run_daemon()` main `while True` loop with background thread invocations, preventing network latency from stalling the 3-second canonical tick heartbeat.
6. Added minimal production-safe boot timing diagnostics (`[BOOT]` and `[BACKGROUND]` logs).
7. Added targeted regression test suite `tests/test_cold_start_repair_1.py`.

## OLD BOOTSTRAP:
- Python process start → `perform_cold_start_hydration()` runs `MacroPipeline` and `NewsPipeline` synchronously.
- `run_daemon()` starts → runs `NewsPipeline` and `MacroPipeline` synchronously AGAIN.
- `run_initial_refreshes()` thread runs `NewsPipeline` and `MacroPipeline` a 3rd time.
- Main loop starts tick #1 after ~30–50 seconds of blocking HTTP requests.
- Main loop periodic 300s refreshes block the main loop thread for 5–15 seconds every 5 minutes.

## NEW BOOTSTRAP:
- Python process start → `perform_cold_start_hydration()` loads local disk cache snapshots only (<50ms).
- `run_daemon()` initializes → enters canonical `while True` main loop immediately (<1s).
- First canonical state generated and emitted to Node via stdout stdout pipe within <=2s.
- `run_initial_refreshes()` triggers `_bg_refresh_news` and `_bg_refresh_macro` asynchronously in background threads.
- Periodic 300s news/macro refreshes execute in background threads without blocking main loop ticks.

## DUPLICATE STARTUP REFRESHES:
**REMOVED**
Previously executed 3 times synchronously/asynchronously. Now executed exactly once through the single background initial refresh path (`run_initial_refreshes()` triggering `_bg_refresh_news` and `_bg_refresh_macro` with non-blocking lock guards).

## PERIODIC REFRESH:
**NON-BLOCKING**
Periodic refreshes inside `run_daemon()` now spawn daemon threads (`_bg_refresh_news` and `_bg_refresh_macro`), freeing the main daemon loop thread immediately (0ms delay).

## CONCURRENCY GUARD:
`news_refresh_lock.acquire(blocking=False)` and `macro_refresh_lock.acquire(blocking=False)` guarantee at most one active background refresh thread per domain. If a refresh is already in progress, additional triggers exit cleanly without duplicate execution or race conditions.

## CACHE/FRESHNESS INTEGRITY:
- Unpopulated/initial states retain truthful `unavailable` / `UNAVAILABLE` status and original timestamps.
- Disk cache snapshots retain original dates and provenance.
- Failed background refreshes preserve existing cached state without artificial timestamp renewal.

## TARGETED TESTS:
`tests/test_cold_start_repair_1.py` & `tests/test_d39_offmarket_hydration_and_session_truth.py`: **28 / 28 PASSED**

## FULL PYTEST:
`pytest -q -p no:cacheprovider`: **1303 PASSED / 1 SKIPPED / 0 FAILED**

## READ_ONLY:
`tests/test_e4b_read_only_boundary.py`: **32 / 32 PASSED** (and 22 CLI/Daemon integration tests PASSED)

## GIT DIFF CHECK:
`git diff --check`: **CLEAN** (0 errors)

## FILES CHANGED:
- `src/server_bridge.py`
- `tests/test_cold_start_repair_1.py` (new test suite)
- `reports/cold_start_repair_1.md` (this report)

## EXPECTED FIRST-CANONICAL LATENCY:
- Daemon boot to main loop entry: <= 1.0s
- First canonical state emitted from Python daemon: <= 2.0s
- External News/Macro HTTP latency impact on time-to-first-canonical: **0.0s**

## PRODUCTION RESTART:
**NOT PERFORMED** (Implementation and tests only, per rules)

## STATUS:
**PASS**
