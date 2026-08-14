# AIR ArdhaMind — Intraday Intelligence Zero-Evidence Root-Cause Audit Report

**Date:** 15-Aug-2026  
**Repository:** `/opt/ArdhaMind`  
**Target Session Inspected:** `2026-08-15` (Saturday / Non-Trading Weekend)  
**Status:** **DIAGNOSTIC AUDIT COMPLETE — ROOT CAUSE IDENTIFIED**  

---

## Executive Summary

The Intraday Intelligence workspace currently renders completed-session 15-minute windows as `INSUFFICIENT WINDOW EVIDENCE` with 0 telemetry checkpoints (`obs_count: 0`, `span: 0s`). 

Our empirical root-cause audit proves that **the UI is 100% correctly and truthfully representing the underlying data state**:
1. Today (15-Aug-2026) is Saturday—a non-trading weekend session. Zero continuous trading market snapshots were generated or recorded between 09:15 IST and 15:30 IST on 15-Aug-2026.
2. `LiveAssistantEngine` evaluated 15-minute windows for the active runtime `session_date` (`2026-08-15`). Because 15-Aug has 0 trading snapshots, `LiveAssistantEngine` correctly returned `INSUFFICIENT_WINDOW_EVIDENCE` for all 25 windows.
3. Prior to our recent test-isolation safety fixes, an un-isolated test execution on 14-Aug overwrote `data/cache/session_history_2026-08-14.json` on disk with an empty snapshot array (`"snapshots": []`).
4. `session_history_2026-08-13.json` on disk remains fully intact with 562 snapshots (including 27 active trading-phase snapshots).

---

## Production Data Path & Payload Verification

| Layer | Output / Observation |
|---|---|
| **Disk Cache (`session_history_2026-08-15.json`)** | 249 snapshots recorded (all during closed weekend state 00:52–01:08 IST). 0 trading-phase snapshots. |
| **Disk Cache (`session_history_2026-08-14.json`)** | 0 snapshots (empty file created during pre-hardening un-isolated test execution). |
| **Disk Cache (`session_history_2026-08-13.json`)** | 562 total snapshots (27 trading-phase snapshots, 535 post-close snapshots). |
| **Backend Engine (`LiveAssistantEngine`)** | Evaluates 25 15-minute buckets for target date `2026-08-15`. Receives 0 snapshots in 09:15–15:30 IST window -> returns `INSUFFICIENT_WINDOW_EVIDENCE` (`obs_count: 0`). |
| **Canonical API (`GET /api/workspace`)** | `unified_intelligence.live_assistant_intelligence.windows` contains 25 items, all with `headline: "XX:XX–YY:YY IST \| INSUFFICIENT WINDOW EVIDENCE"` and `observation_count: 0`. |
| **Frontend UI (`IntradayAssistant.tsx`)** | Faithfully renders backend canonical payload without filtering valid data. |

---

## Diagnostic Classification

**Primary Failure Category:**  
`J. EXPECTED / NO HISTORICAL DATA`  
- For session `2026-08-15` (Saturday), no trading session occurred. `INSUFFICIENT_WINDOW_EVIDENCE` is the **100% truthful and un-fabricated representation** of missing market telemetry for a non-trading date.

**Secondary Failure Category:**  
`C & D. HISTORICAL ARCHIVE SELECTOR UNCOUPLED FROM COMPLETED SESSION ARCHIVE`  
- `LiveAssistantEngine` evaluates windows strictly for the active runtime `session_date` (`2026-08-15`). During non-trading weekend/holiday states, the engine evaluates the current date instead of falling back to the most recent valid completed trading session archive (`2026-08-13`).
- In addition, `_filter_retained_snapshots` in `workstation_state_service.py` bucketed 3-minute anchor snapshots using UTC hours (`ts_str[11:16]`) rather than converting to IST hours (`+05:30`).

---

## Hardening Regression Audit

- **Did recent weekend hardening cause data loss?** **NO.**
- The recent hardening fixes (specifically `tmp_path` test isolation and `_persist_session_history` guards) are what **prevent** production history files from being overwritten or lost in future sessions.
- The 0-evidence cards on the weekend UI are the truthful reflection that Saturday Aug 15 was not a trading session.

---

## Minimal Repair Plan (For Future Implementation)

1. **Strict Zero-Fabrication Guarantee**: Maintain the invariant that no synthetic backfill or fake checkpoints are ever created.
2. **Completed Session Archive Selection**: When `session_status` is `HOLIDAY` or `CLOSED` on a non-trading date (e.g. weekend), update `LiveAssistantEngine` / `WorkstationStateService` to select the most recent persisted session history file containing valid trading snapshots (e.g. `2026-08-13` or `2026-08-14`) for historical window rendering, while keeping current live state strictly isolated.
3. **IST 3-Minute Bucket Alignment**: Update `_filter_retained_snapshots` in `workstation_state_service.py` to parse UTC ISO timestamps into IST time (`+05:30`) before computing 3-minute interval anchor keys (`(mm // 3) * 3`).
