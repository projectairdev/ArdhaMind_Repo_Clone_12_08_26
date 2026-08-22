# LIGHTWEIGHT SESSION STORAGE DESIGN CORRECTIONS RECORD

**Document Version:** 1.0.0 — Authoritative Correction Record  
**Target Subsystem:** Lightweight Session Storage Architecture (`src/storage/`)  
**Sprint:** Implementation Preparation & Design Correction Pass

---

## 1. SUMMARY OF APPLIED ARCHITECTURAL CORRECTIONS

This document formalizes the four mandatory architectural corrections applied to the approved Lightweight Session Storage Architecture prior to implementation.

---

### CORRECTION 1: Removal of Artificial 15:30:00 Stream Ingestion Cutoff
- **Previous Assumption:** "15:30 IST: Streaming tick ingestion halts."
- **Problem:** Wall-clock 15:30:00 does not guarantee exchange trading close. Ticks and post-market closing auction trades settling between 15:30:00 and 15:30:45 IST would be artificially dropped if feed ingestion was forcefully severed at 15:30:00.
- **Corrected Invariant:**
  $$\text{MARKET SESSION CLOSED} \neq \text{MARKET FEED PROCESS STOPPED}$$
  - At 15:30:00 IST, the session enters `CLOSE_PENDING`.
  - Ingestion listeners and WebSocket subscriptions remain connected and active in `STANDBY`.
  - Live market observations continue contributing to the session until the canonical session resolver confirms `CLOSED` and official close reconciliation captures the final valid trade.

---

### CORRECTION 2: Replacement of Hard-Coded 2.0-Point Drift with Configurable `CloseReconciliationPolicy`
- **Previous Assumption:** Hard-coded "Verifies drift $\le$ 2.0 pts".
- **Problem:** A static 2.0-point rule hardcodes index volatility assumptions directly into the architecture without accounting for market regime, percentage scaling, or exchange policy revisions.
- **Corrected Architecture:** Introduced the versioned, configurable `CloseReconciliationPolicy`:
  - `policy_version`: e.g. `"v1.0-standard"`
  - `comparison_source`: `"KITE_HISTORICAL_DAY_CANDLE"` / `"NSE_EOD_SETTLEMENT"`
  - `max_absolute_drift_points`: Configurable float (default: `5.0 pts` during normal volatility)
  - `max_relative_drift_bps`: Configurable basis points (e.g. `2.5 bps` $\approx 6.0$ pts on Nifty @ 24,000)
  - `source_priority`: `["LIVE_CANONICAL_OBSERVED", "OFFICIAL_DAY_CANDLE", "NSE_SETTLEMENT", "LAST_VALID_FALLBACK"]`
  - `allow_provider_correction`: Boolean (true)
  - `reconciliation_result_states`: `MATCHED`, `WITHIN_TOLERANCE`, `CORRECTED_FROM_PROVIDER`, `PARTIAL`, `UNRESOLVED`
  - Reconciliation records the exact policy version and drift metrics used in `SessionIntegrityEnvelope`.

---

### CORRECTION 3: Revision of Production Live Acceptance Criterion
- **Previous Criterion:** "Zero tick drops during live hours".
- **Problem:** "Zero tick drops" is an unrealistic standard that conflates normal internet/broker transient network packet drops with critical data loss.
- **Corrected Criterion:**
  $$\mathbf{ZERO\ UNRECONCILED\ CRITICAL\ DATA\ GAPS}$$
  - **Allowed:** Transient packet loss / disconnects that are detected, safely degraded in the UI, and automatically backfilled/reconciled via REST historical sync.
  - **Prohibited:** Unreconciled critical gaps in OHLC, unrecorded disconnect events, or stale data presented as fresh live truth.

---

### CORRECTION 4: Permanent Retention for `OptionsCloseBaseline`
- **Previous Retention:** Rolling 5 trading sessions.
- **Problem:** Options close baselines represent unique, irrecoverable Ardha-observed derivative market depth (Call/Put Walls, Max Pain, ATM IV, strike distributions). Once an expiry passes, Kite historical APIs do not provide full options chain depth.
- **Corrected Retention:**
  - `OptionsCloseBaseline` is now **PERMANENT** (~2.1 KB per session).
  - Annual growth: $2.1\text{ KB} \times 250\text{ sessions} \approx \mathbf{525\text{ KB / Year}}$.
  - Enables longitudinal Call/Put Wall migration research, IV evolution studies, and historical decision quality analysis at negligible storage cost.

---

## 2. REVISED PERMANENT RETENTION & STORAGE FOOTPRINT

| Artifact | Retention Window | Storage Footprint | Annual Storage (250 sessions) |
|:---|:---:|:---:|:---:|
| **SessionCloseCore** | **PERMANENT** | ~3.8 KB / session | ~950 KB / year |
| **OptionsCloseBaseline** | **PERMANENT** | ~2.1 KB / session | ~525 KB / year |
| **SessionIntegrityEnvelope** | **PERMANENT** | ~1.8 KB / session | ~450 KB / year |
| **Σ Permanent Market History Growth** | — | **~7.7 KB / session** | **~1.92 MB / year** |
| **Rolling Candle Cache** | Rolling 5 Trading Sessions | ~32.4 KB fixed | ~32.4 KB ceiling |
| **Intraday Telemetry Series** | Rolling 5 Trading Sessions | ~4.2 KB / session | ~21.0 KB ceiling |
| **Connectivity Event Log** | Rolling 30 Trading Sessions | ~1.5 KB / session | ~45.0 KB ceiling |
| **Active Catalysts** | Active + 5-day resolved | ~4.6 KB fixed | ~4.6 KB ceiling |
| **Latest Recovery Snapshot** | Latest 1 valid state | ~40.0 KB fixed | ~40.0 KB ceiling |
| **Closed Trade Journal (M5)** | **PERMANENT AUDIT** | ~2.0 KB / trade | Permanent SQLite |
| **Proposal Lineage** | **PERMANENT AUDIT** | ~1.5 KB / proposal | Permanent SQLite |
| **Prediction Accuracy Records** | **PERMANENT AUDIT** | ~1.2 KB / record | Permanent SQLite/JSON |
