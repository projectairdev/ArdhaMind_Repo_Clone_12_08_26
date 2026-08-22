# LIGHTWEIGHT SESSION STORE EXACT SCHEMA SPECIFICATIONS

**Document Version:** 1.1.0 — Authoritative Corrected Schema Contract  
**Language:** Python Dataclasses / JSON Schemas  
**Target Subsystem:** `LightweightSessionStore`

---

## 1. SCHEMA 1: `SessionCloseCore` (`close/YYYY-MM-DD.json` ~3.8 KB — PERMANENT)

```json
{
  "$schema": "https://ardhamind.projectair.in/schemas/session_close_core_v1.json",
  "schema_name": "SESSION_CLOSE_CORE",
  "schema_version": "1.1.0",
  "session_date": "2026-08-21",
  "session_type": "REGULAR_TRADING",
  "finalized_at": "2026-08-21T15:35:12.450Z",
  "finalization_generation": 1,
  "idempotency_key": "CLOSE_2026-08-21_GEN1_b8f2a1c9",
  "market_ohlcv": {
    "open": 24225.45,
    "high": 24265.15,
    "low": 24206.80,
    "close": 24252.00,
    "volume": 284501230,
    "previous_close": 24231.85,
    "change_points": 20.15,
    "change_percent": 0.0832,
    "session_range_points": 58.35
  },
  "structural_levels": {
    "pivot": 24241.32,
    "r1": 24275.83,
    "r2": 24299.67,
    "r3": 24334.18,
    "s1": 24217.48,
    "s2": 24182.97,
    "s3": 24159.13,
    "local_atr_upper": 24282.40,
    "local_atr_lower": 24221.60
  },
  "market_regime": {
    "regime": "RANGE_DAY",
    "day_character": "CONSOLIDATION_SESSION",
    "momentum": "NEUTRAL",
    "volatility_regime": "LOW"
  },
  "closing_vix": {
    "vix_close": 12.45,
    "vix_change_points": -0.22,
    "vix_change_pct": -1.74,
    "volatility_state": "LOW"
  },
  "closing_breadth": {
    "advances": 25,
    "declines": 24,
    "unchanged": 1,
    "ad_ratio": 1.04,
    "breadth_bias": "NEUTRAL_BALANCED"
  },
  "institutional_flows": {
    "fii_net_crores": -542.7,
    "dii_net_crores": 2124.1,
    "combined_net_crores": 1581.4,
    "stance": "SUPPORTIVE",
    "as_of_date": "2026-08-21",
    "source": "NSE_EOD_SETTLEMENT"
  },
  "session_story": {
    "headline": "Nifty consolidated above 24,200 support floor with strong DII support.",
    "primary_driver": "Financials resilience (+0.72%) neutralized IT sector profit-taking (-0.26%).",
    "carry_forward_thesis": "Constructive base intact; upside expansion triggers above 24,288 structural resistance.",
    "key_takeaways": [
      "24,200 put base defended for third consecutive session.",
      "DII net buying exceeded +2,100 Cr, absorbing foreign institutional supply."
    ]
  },
  "provenance": {
    "provider": "ZERODHA_KITE_RECONCILED",
    "reconciliation_policy": "v1.0-standard",
    "reconciliation_status": "OFFICIAL_RECONCILED",
    "runtime_id": "07a1f4d7-fb86-4237-9d19-6a4fd1beaaf7"
  }
}
```

---

## 2. SCHEMA 2: `OptionsCloseBaseline` (`options_close/YYYY-MM-DD.json` ~2.1 KB — PERMANENT)

```json
{
  "$schema": "https://ardhamind.projectair.in/schemas/options_close_baseline_v1.json",
  "schema_name": "OPTIONS_CLOSE_BASELINE",
  "schema_version": "1.1.0",
  "session_date": "2026-08-21",
  "expiry_date": "2026-08-28",
  "captured_at": "2026-08-21T15:31:05.120Z",
  "underlying_spot": 24252.00,
  "atm_strike": 24250,
  "derivatives_summary": {
    "pcr_oi": 1.09,
    "pcr_volume": 0.98,
    "max_pain_strike": 24250,
    "call_wall_strike": 24500,
    "put_wall_strike": 24000,
    "atm_iv_pct": 12.8,
    "total_call_oi_crores": 14.82,
    "total_put_oi_crores": 16.15,
    "oi_skew_bias": "BALANCED_SUPPORTIVE"
  },
  "strike_baseline": [
    {"strike": 24000, "ce_oi": 95000, "pe_oi": 1850000, "ce_ltp": 272.0, "pe_ltp": 18.5, "ce_iv": 14.2, "pe_iv": 13.8},
    {"strike": 24050, "ce_oi": 42000, "pe_oi": 520000, "ce_ltp": 228.5, "pe_ltp": 24.0, "ce_iv": 13.9, "pe_iv": 13.5},
    {"strike": 24100, "ce_oi": 142000, "pe_oi": 890000, "ce_ltp": 182.4, "pe_ltp": 34.2, "ce_iv": 13.4, "pe_iv": 13.1},
    {"strike": 24150, "ce_oi": 210000, "pe_oi": 740000, "ce_ltp": 145.0, "pe_ltp": 46.5, "ce_iv": 13.0, "pe_iv": 12.9},
    {"strike": 24200, "ce_oi": 380000, "pe_oi": 1120000, "ce_ltp": 112.5, "pe_ltp": 62.0, "ce_iv": 12.8, "pe_iv": 12.7},
    {"strike": 24250, "ce_oi": 750000, "pe_oi": 820000, "ce_ltp": 84.0, "pe_ltp": 82.5, "ce_iv": 12.8, "pe_iv": 12.8},
    {"strike": 24300, "ce_oi": 1240000, "pe_oi": 410000, "ce_ltp": 59.0, "pe_ltp": 108.0, "ce_iv": 12.9, "pe_iv": 13.0},
    {"strike": 24350, "ce_oi": 910000, "pe_oi": 230000, "ce_ltp": 39.5, "pe_ltp": 139.0, "ce_iv": 13.1, "pe_iv": 13.3},
    {"strike": 24400, "ce_oi": 1580000, "pe_oi": 180000, "ce_ltp": 25.0, "pe_ltp": 174.5, "ce_iv": 13.4, "pe_iv": 13.7},
    {"strike": 24450, "ce_oi": 840000, "pe_oi": 95000, "ce_ltp": 15.2, "pe_ltp": 214.0, "ce_iv": 13.8, "pe_iv": 14.1},
    {"strike": 24500, "ce_oi": 2150000, "pe_oi": 120000, "ce_ltp": 9.8, "pe_ltp": 258.0, "ce_iv": 14.3, "pe_iv": 14.6}
  ],
  "provenance": {
    "provider": "ZERODHA_KITE_NFO",
    "last_valid_options_at": "2026-08-21T15:29:58.800Z",
    "finalization_quality": "COMPLETE_FINALIZED",
    "retention_tier": "PERMANENT"
  }
}
```

---

## 3. SCHEMA 3: `CloseReconciliationPolicy` (Configuration Object)

```json
{
  "policy_version": "v1.0-standard",
  "comparison_source": "KITE_HISTORICAL_DAY_CANDLE",
  "max_absolute_drift_points": 5.0,
  "max_relative_drift_bps": 2.5,
  "source_priority": [
    "LIVE_CANONICAL_OBSERVED",
    "OFFICIAL_DAY_CANDLE",
    "NSE_SETTLEMENT",
    "LAST_VALID_FALLBACK"
  ],
  "allow_provider_correction": true,
  "market_state_required": "CLOSED",
  "validation_window_seconds": 300
}
```

---

## 4. SCHEMA 4: `SessionIntegrityEnvelope` (`integrity/YYYY-MM-DD.json` ~1.8 KB — PERMANENT)

```json
{
  "$schema": "https://ardhamind.projectair.in/schemas/session_integrity_envelope_v1.json",
  "schema_name": "SESSION_INTEGRITY_ENVELOPE",
  "schema_version": "1.1.0",
  "session_date": "2026-08-21",
  "session_type": "REGULAR_TRADING",
  "finalization_status": "COMPLETE",
  "completeness_status": "FULL_SESSION",
  "broker_auth_state_at_close": "AUTHENTICATED",
  "websocket_state_at_close": "CONNECTED",
  "market_feed_state_at_close": "HEALTHY",
  "last_valid_nifty_tick_at": "2026-08-21T15:30:00.102Z",
  "last_valid_options_at": "2026-08-21T15:29:58.800Z",
  "last_valid_breadth_at": "2026-08-21T15:30:00.050Z",
  "last_valid_vix_at": "2026-08-21T15:30:00.100Z",
  "feed_gap_count": 1,
  "total_feed_gap_seconds": 4.2,
  "longest_feed_gap_seconds": 4.2,
  "degraded_intervals": [
    {"from": "2026-08-21T10:42:15.120Z", "to": "2026-08-21T10:42:19.320Z", "duration_seconds": 4.2, "cause": "WS_RECONNECT_SYNC"}
  ],
  "unrecoverable_intervals": [],
  "reconciliation": {
    "reconciliation_status": "MATCHED",
    "reconciliation_policy_version": "v1.0-standard",
    "reconciliation_completed_at": "2026-08-21T15:35:10.000Z",
    "sources_used": ["KITE_TICKER_STREAM", "KITE_REST_HISTORICAL", "NSE_SETTLEMENT"],
    "observed_close": 24252.00,
    "provider_settled_close": 24252.00,
    "drift_points": 0.00
  },
  "warnings": []
}
```
