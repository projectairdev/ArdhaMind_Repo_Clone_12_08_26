# LIGHTWEIGHT SESSION STORAGE ARCHITECTURE SPECIFICATION

**Document Version:** 1.1.0 — Authoritative Corrected Staging Architecture Design  
**Target Component:** `LightweightSessionStore` (`src/storage/lightweight_session_store.py`)  
**Design Status:** Approved for Implementation (Design Corrections Applied)  
**Production Isolation:** Staging Only (`/opt/ardhamind/staging`) — Production Untouched.

---

## 1. EXECUTIVE ARCHITECTURAL OVERVIEW

AIR Ardha's legacy storage architecture writes full canonical workstation state snapshots (~40KB each) to disk every 15–30 seconds during market hours (`data/cache/session_history_{date}.json`), generating **35 MB to 45 MB per session** (>1.2 GB/month). Over 99% of this data is identical static metadata repeatedly serialized.

The **Lightweight Session Storage Architecture** replaces this monolithic snapshot dump with a modular, domain-partitioned, event-driven storage subsystem. It achieves **100% functional fidelity** across all 382 dashboard data fields, decision scenarios, and AI assistant reasoning while reducing operational daily disk footprint to **~47 KB/day (a 99.89% reduction)**, establishing permanent EOD history at **~7.7 KB/session (~1.9 MB/year)**, and reducing startup cold-start I/O from **~500ms to <5ms**.

---

## 2. HIGH-LEVEL SYSTEM ARCHITECTURE & DATA FLOW

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                INGESTION & FEED LAYER                                  │
│  Zerodha Kite Ticker (WS) │ Zerodha Kite Connect (REST) │ NSE / NSDL │ Global Macro / News │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CANONICAL WORKSTATION STATE SERVICE                             │
│       Monotonic Sequence (#18420+) │ In-Memory State Tree │ Zero Fabricated Zeroes     │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       LIGHTWEIGHT SESSION STORAGE SUBSYSTEM                            │
│                         (src/storage/lightweight_session_store.py)                     │
├─────────────────────────┬──────────────────────────┬───────────────────────────────────┤
│ A. Current State        │ B. Intraday Series       │ C. Multi-Session Caches           │
│    Recovery Snapshot    │    15-Min Telemetry Ring │    Rolling 5-Day 5m Candle Cache  │
│    (latest_state.json)  │    (telemetry/YYYY-MM-DD)│    (cache/nifty_5m_candles.json)  │
├─────────────────────────┼──────────────────────────┼───────────────────────────────────┤
│ D. EOD Session Close    │ E. EOD Options Close     │ F. Carry-Forward & Governance     │
│    Session Close Core   │    Options Close Baseline│    Active Catalysts & Macro Themes│
│    (close/YYYY-MM-DD)   │    (options/YYYY-MM-DD)  │    Session Integrity Envelope     │
│    [PERMANENT ~3.8KB]   │    [PERMANENT ~2.1KB]    │    [PERMANENT ~1.8KB]             │
└─────────────────────────┴──────────────────────────┴───────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CONSUMING WORKSPACES & ENGINES                                  │
│  NIFTY (PRE/LIVE/POST) │ Options Ladder │ Market Metrics │ Market Intelligence (Plans) │
│  Live Assistant Engine │ Performance Engine (OHLC) │ Safety Policy │ Advanced Diagnostics│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. CORE STORAGE COMPONENTS & RESPONSIBILITIES

The storage layer is partitioned into **7 distinct domain stores**, each with independent serialization, validation, and lifecycle semantics:

### 1. `LatestCanonicalRecoverySnapshot` (`data/session_store/cache/latest_canonical_state.json` ~40KB)
- **Role:** Instant daemon restart hydration and state sequence continuity.
- **Write Cadence:** Periodic atomic write (every 60s or on significant state mutation). Single file overwritten atomically.
- **Content:** Complete in-memory canonical state snapshot for seamless cold-start resumption.

### 2. `RollingCandleCache` (`data/session_store/cache/nifty_5m_candles.json` ~32KB)
- **Role:** Primary data source for all technical indicators (EMA20, EMA50, EMA200, RSI14, MACD, ADX14, ATR14, VWAP) and multi-timeframe candlestick charts.
- **Write Cadence:** Appended every 5 minutes during live hours; synchronized via historical REST refetch on startup.
- **Retention:** Exactly **5 trading sessions** (375 5-minute bars). Older sessions pruned automatically.

### 3. `IntradayTelemetrySeries` (`data/session_store/telemetry/YYYY-MM-DD.json` ~4.2KB)
- **Role:** Provides 15-minute window historical evidence for Live Assistant narratives and intraday market evolution tracking.
- **Write Cadence:** Appended at the boundary of each 15-minute trading window (09:30, 09:45, ... 15:30; 25 buckets total).
- **Retention:** Rolling 5 trading sessions.

### 4. `SessionCloseCore` (`data/session_store/close/YYYY-MM-DD.json` ~3.8KB)
- **Role:** Authoritative, finalized record of the completed session's market truth. Powers next-session PRE-market analysis, pivot boundaries, opening scenarios, and carry-forward levels.
- **Write Cadence:** Written at **15:30+ EOD** upon official close reconciliation. Immutable once finalized.
- **Retention:** **PERMANENT** (~3.8KB; 250 trading days = ~950KB/year).

### 5. `OptionsCloseBaseline` (`data/session_store/options_close/YYYY-MM-DD.json` ~2.1KB)
- **Role:** Authoritative closing derivatives baseline. Powers Day-over-Day ΔOI, Wall shift detection, and Max Pain migration on the next morning's Options Ladder and longitudinal derivatives research.
- **Write Cadence:** Captured during pre-close window (15:20) and finalized post-close. Guarded: off-hours empty option packets can never overwrite a valid closing baseline.
- **Retention:** **PERMANENT** (~2.1KB; 250 trading days = ~525KB/year).

### 6. `ActiveCatalystCarryForward` (`data/session_store/cache/active_catalysts.json` ~4.6KB)
- **Role:** Tracks unresolved macroeconomic events, policy catalysts, and carry-forward market risks across session boundaries.
- **Write Cadence:** Updated upon new high-impact news ingestion or catalyst resolution.
- **Retention:** Active items persisted until resolved or expired; historical resolved items pruned after 5 sessions.

### 7. `SessionIntegrityEnvelope` (`data/session_store/integrity/YYYY-MM-DD.json` ~1.8KB)
- **Role:** Comprehensive audit envelope recording feed continuity, broker disconnects, data quality scores, gap durations, and reconciliation status for the session.
- **Write Cadence:** Continuously updated in memory; finalized and frozen at EOD.
- **Retention:** **PERMANENT** audit ledger (~1.8KB; 250 trading days = ~450KB/year).

---

## 4. INGESTION CONTINUITY & MARKET CLOSE RECONCILIATION

### Ingestion Continuity Rule
$$\text{MARKET SESSION CLOSED} \neq \text{MARKET FEED PROCESS STOPPED}$$
- Reaching wall-clock 15:30:00 IST triggers transition to `CLOSE_PENDING`, **not** process termination or socket disconnection.
- WebSocket streaming and feed listeners remain active in `STANDBY` to capture closing auction settlements and late-arriving trade reports.

### Configurable `CloseReconciliationPolicy`
Reconciliation replaces arbitrary hardcoded thresholds with a versioned, configurable policy:
```json
{
  "policy_version": "v1.0-standard",
  "comparison_source": "KITE_HISTORICAL_DAY_CANDLE",
  "max_absolute_drift_points": 5.0,
  "max_relative_drift_bps": 2.5,
  "source_priority": ["LIVE_CANONICAL_OBSERVED", "OFFICIAL_DAY_CANDLE", "NSE_SETTLEMENT", "LAST_VALID_FALLBACK"],
  "allow_provider_correction": true
}
```

---

## 5. PRODUCTION LIVE ACCEPTANCE CRITERION

Production deployment requires zero unreconciled critical data gaps:
$$\mathbf{ZERO\ UNRECONCILED\ CRITICAL\ DATA\ GAPS}$$
- Transient network or WebSocket drops are permitted provided they are automatically detected, safely degraded in UI indicators, and backfilled via REST historical sync with provenance tracking.
