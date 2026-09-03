# AIR ArdhaMind Production Handover

> **Archived, redacted copy.** Live process PIDs, the systemd service name, and the
> broker account identifier / holder name present in the original operational
> handover have been redacted. Engineering rationale is preserved verbatim.

## 1. Current Production State
- **Timestamp (IST):** 2026-08-14 05:36:00 IST
- **Deployment Path:** `/opt/ArdhaMind`
- **Service Status:** `[redacted-service-name]` ACTIVE (running)
- **Node Server PID:** `[redacted]` (`node /opt/ArdhaMind/dist/server.cjs`)
- **Python Bridge Daemon PID:** `[redacted]` (`python src/server_bridge.py`)
- **Public Domain:** `https://ardhamind.projectair.in`
- **Health Status:** `READY` (`/api/health` 200 OK)
- **Market Session:** `CLOSED` / Pre-Market (Awaiting 09:15 IST opening bell)
- **Broker Auth State:** `CONNECTED` (Session valid, Profile `[redacted]` validated)
- **Feed/Stream State:** `CONNECTED` / Idle Pre-Market (Awaiting first session tick)
- **KiteTicker Instance Count:** `<= 1` (Single-upstream StreamingOrchestrator invariant enforced)
- **Subscription State:** Configured for NIFTY 50 basket & constituent indices
- **Canonical Runtime State:** `READY` (Runtime ID `986c6970-3656-4ad0-adec-748dabf5b733`)
- **State Sequence:** Sequence `38+`

## 2. Current Accepted Architecture
- **CanonicalWorkstationState:** Single frontend source of truth.
- **Deterministic Analytical Pipeline:** Evidence-based intelligence engines with no artificial offsets or synthetic values.
- **Process Model:** Single Express Node process (`dist/server.cjs`), single Python daemon (`src/server_bridge.py`).
- **Streaming Orchestrator:** Single `StreamingOrchestrator` managing at most **one** upstream `KiteTicker` instance.
- **Browser Transport Isolation:** Browser WebSockets are independent of Kite broker authentication and do not trigger extra upstream connections on tab refresh.
- **Frontend Architecture:** Six read-only workspaces (NIFTY Live, Live Assistant, Today's Analysis, Forward Outlook, Pre-Market Planner, Market Pulse).
- **READ_ONLY Execution Guard:** Strict read-only workstation.

**Absolute Policy:**
- **NO** execution capabilities.
- **NO** paper trading capabilities.
- **NO** mock or sample market data.
- **NO** synthetic prices, structural levels, or fake telemetry.

## 3. Important Repairs Completed

### A. Kite Auth Oscillation Repair
- Sticky daemon broker auth state in `KiteGateway`.
- 120-second positive validation cache prevents API rate-limit hammering.
- Transient errors (HTTP 5xx, timeouts, idle streams) preserve authenticated state.
- Genuine auth rejections (HTTP 401, 403, `ExpiredAccessTokenError`) invalidate auth.

### B. Explicit Broker Disconnect Repair
- Implemented correct `SessionManager.delete_session` path.
- Explicit user logout invalidates session credentials permanently; does not auto-restore stale credentials on tab reload.

### C. Unauthenticated Daemon Hardening
- No `StreamingOrchestrator` or `KiteTicker` instance created when unauthenticated.
- Missing stream telemetry is represented as `null`, never fake sentinel values.

### D. Canonical Null-Semantics Repair
Missing data must remain missing (`None` / `UNAVAILABLE`).

Specifically eliminated synthetic/default behavior:
- Spot default `24500.0` removed.
- Options PCR default `1.00` removed.
- Breadth default `25 Advances / 25 Declines` removed.
- GIFT gap default `0.00` points removed.
- `FLAT_OPEN` character on missing GIFT removed (evaluates to `UNCERTAIN`).
- Synthetic Forward Outlook structural level fallbacks (`24400`, `24480`, `24580`) removed.
- Synthetic high-confidence scenario scores (95/100) on missing evidence removed.
- Hardcoded Today's Analysis breadth defaults removed.
- Zero Live Assistant deltas (`0.0` pts / `0.0%`) on single-checkpoint windows removed (returns `None` / `UNAVAILABLE`).
- Fake `0.0s (Live)` tick age on disconnected feed removed (renders `Awaiting First Tick` / `UNAVAILABLE`).

### E. GIFT Consistency Repair
- Market Pulse and Pre-Market Planner consume the same canonical `GIFT_NIFTY` quote from `macro_intelligence`.
- Eligible pre-09:15 IST frozen pre-market snapshot recomputes automatically when authoritative GIFT quote arrives.
- No workspace-specific synthetic GIFT values.

### F. Trading-Day Rollover Protection
- Historical session data is preserved per date.
- Previous-session observations do not masquerade as current-session evidence.

## 4. Latest Verification
- **Targeted Regression Suite:** `tests/test_null_semantics_audit_repairs.py` — **10 / 10 PASSED**
- **Read-Only Boundary Suite:** `tests/test_e4b_read_only_boundary.py` — **32 / 32 PASSED**
- **Full Regression Suite:** `.venv/bin/python -m pytest -q -p no:cacheprovider` — **1258 PASSED / 0 FAILED** (1 skipped fixture)
- **TypeScript Check:** `npx tsc --noEmit` — **PASSED (0 errors)**
- **Production Build:** `npm run build` — **PASSED** (`dist/index.html` & `dist/server.cjs` clean)
- **Production Smoke Test:** Local API `/api/health` `READY`, public URL `https://ardhamind.projectair.in/` `200 OK`, Broker auth `CONNECTED`.

## 5. Current Kite State
- **Broker:** `CONNECTED`
- **Session:** `VALID` (`session_valid: true`, authenticated at `2026-08-14T00:00:52Z`)
- **Profile:** `VALIDATED` (`[redacted]` — [redacted account holder])
- **Ticker Instances:** `1` (Single-upstream StreamingOrchestrator invariant enforced)
- **Feed:** `CONNECTED` (Pre-market idle, awaiting 09:15 IST ticks)
- **First Authoritative Market Tick:** Awaiting opening session (`tick_age_seconds: None`)
- **GIFT Nifty:** Truthfully `UNAVAILABLE` until authoritative feed updates
- **READ_ONLY:** Hard-disabled & enforced across all endpoints

## 6. Today's Live-Session Objective
- **Target Session:** 14-Aug-2026 NSE session.
- **Primary Objective:** **OBSERVE, DO NOT DEVELOP.**
- Until an actual blocking defect occurs:
  - Do NOT modify code.
  - Do NOT restart service.
  - Do NOT clear historical data.
  - Do NOT force provider refreshes.
  - Do NOT manufacture unavailable telemetry.

**Expected Progression:**
Authenticated → Pre-Market → First Authoritative Ticks → Current-Session Telemetry → Breadth/Options Population → Live Assistant Evidence Accumulation → Today's Analysis Evidence Accumulation → Forward Outlook Scenarios (when sufficient evidence exists).

## 7. Live Acceptance Checks
For the next engineering session, verify:
- Broker remains `CONNECTED` without oscillation.
- Exactly one Python daemon process.
- Exactly one `StreamingOrchestrator`.
- Maximum one `KiteTicker` instance.
- `reconnect_count` remains stable unless genuine reconnect occurs.
- `generation_id` does not unexpectedly change.
- First tick is authoritative.
- Tick age becomes real numeric value only after first tick arrives.
- Today's `trading_date` is `2026-08-14`.
- Previous-session telemetry is not treated as current session.
- NIFTY spot populates correctly from live tick.
- Breadth populates from today's observed constituent ticks.
- Options / PCR populate from authoritative current data.
- GIFT provenance is consistent across workspaces.
- $\text{UNKNOWN} \neq \text{ZERO}$
- $\text{UNAVAILABLE} \neq \text{NEUTRAL}$
- $\text{INSUFFICIENT\_DATA} \neq \text{BALANCED}$
- $\text{DISCONNECTED} \neq \text{LIVE}$
- No synthetic Forward Outlook levels.
- READ_ONLY remains intact.

## 8. Recommended Checkpoints
Do not poll aggressively in loops. Check at key session milestones:
- Pre-Market Setup (Before 09:15 IST)
- Market Open (Shortly after 09:15 IST)
- Opening Range Completion (09:30–09:45 IST)
- Midday Session (12:00–13:00 IST)
- Pre-Close (15:00–15:30 IST)
- Post-Close Final Analysis (After 15:30 IST)

## 9. Standstill Rules
A fresh Gemini session **MUST NOT** immediately change code.

First:
1. Read `GEMINI_HANDOVER.md`.
2. Inspect current runtime.
3. Compare runtime against this checkpoint.
4. Diagnose any anomaly using logs.
5. Modify code **ONLY** for a proven defect.

Never interpret normal pre-market/off-market data unavailability as a defect.

## 10. Resume Instruction

### FOR NEXT GEMINI SESSION

Read this entire file first.

Then inspect the current production runtime before making any changes.

AIR ArdhaMind is currently in live production soak/testing.

Do not redesign or refactor.

Preserve:
- production architecture
- canonical truth semantics
- historical data
- single-upstream streaming architecture
- strict READ_ONLY boundary

If the system is healthy, report its state and leave it untouched.

If a defect exists:
diagnose → prove root cause → propose minimal fix → test → wait for deployment authorization.
