# AIR ArdhaMind — Dashboard-Wide Temporal Provenance Matrix

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Standard**: Canonical Temporal Session & Provenance Model v2.0  
**Date**: August 2026  

---

## 1. Temporal Provenance Mapping Matrix

| Workspace | Section | Field / Label | Source Session Date | Source `observed_at` | Canonical `validated_at` | Display Label Standard | Freshness Status | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Market NIFTY** | Pre-Market Outlook | OPENING BIAS | `target_trading_date` (e.g. 24 Aug) | Ingestion pipeline | `last_updated_ist` | `OPENING BIAS (Next Session · 24 Aug 2026)` | `FRESH` | **PASS** |
| **Market NIFTY** | Pre-Market Outlook | EXPECTED OPEN | `target_trading_date` | Ingestion pipeline | `last_updated_ist` | `EXPECTED NEXT-SESSION OPEN` | `FRESH` | **PASS** |
| **Market NIFTY** | Key Levels | Reference Close | `reference_close_date` (e.g. 21 Aug) | Previous Close | `canonical_committed_at` | `Reference Close (21 Aug 2026)` | `FRESH` | **PASS** |
| **Market NIFTY** | Key Levels | GIFT Nifty Quote | Current / Off-Session | `quotes.GIFT_NIFTY.observed_at` | `quotes.GIFT_NIFTY.checked_at` | `LATEST GIFT NIFTY OBSERVATION` | `FRESH` | **PASS** |
| **Market NIFTY** | Institutional | FII / DII Flow | `institutional_context.trading_date` | Official Exchange Data | `checked_at` | `INSTITUTIONAL POSITIONING · Cash Market (21 Aug 2026)` | `FRESH` | **PASS** |
| **Market Metrics** | Market State | NIFTY Spot & Delta | Current Session | `market_data.observed_at` | `canonical_committed_at` | `NIFTY 50 SPOT` + `TemporalContextStrip` | `LIVE` / `FRESH` | **PASS** |
| **Market Metrics** | Global & Macro | World Exchanges | Exchange Local Timezone | Instrument `observed_at` | Instrument `checked_at` | Local Center Status (`Tokyo CLOSED`, `Frankfurt CLOSED`) | `FRESH` | **PASS** |
| **Market Options** | Derivatives Strip | Option Chain | Expiry Date (e.g. 27 Aug) | `options.snapshot_timestamp` | `options.last_updated_ist` | `NIFTY OPTIONS · 27 AUG 2026 EXPIRY (21 Aug Close)` | `LAST VALID` | **PASS** |
| **Market Intelligence**| Session Scenarios | Scenario Targets | Target Session Date | Model Ingestion | Model Validation | `SESSION BIAS — 24 AUG` / `FOR SESSION: 24 AUG 2026` | `FRESH` | **PASS** |
| **News & Updates** | Live News & Events | Publisher Timestamp | Verified Publication Time | Discovery Pipeline | Engine Validation | `Today · HH:MM IST`, `Yesterday`, or `Discovered HH:MM` | `FRESH` | **PASS** |
| **Portfolio** | Risk & Positions | Prior Proposals | Original Session Date | Proposal Timestamp | State Sync | `EXPIRED / PRIOR SESSION` | `EXPIRED` | **PASS** |

---

## 2. Temporal Display & Preview Rules
1. **Weekend Behavior**: On Saturday and Sunday, all market-derived screens display `MARKET: WEEKEND`, `Last Valid Session: 21 Aug 2026`, and `Next Session: 24 Aug 2026`.
2. **Preview Mode Rule**: When QA staging preview is active (`PRE`, `LIVE`, `POST`), a prominent banner displays `STAGING PREVIEW · NEXT SESSION PREVIEW` to ensure preview state is never mistaken for real-time live trading.
3. **No Generic "Today"**: Ambiguous generic labels like "Today", "Current", or "Last" are replaced by dynamic date-aware labels.
