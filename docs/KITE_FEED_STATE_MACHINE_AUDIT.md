# KITE FEED STATE MACHINE & DOMAIN FRESHNESS AUDIT

**Document Version:** 1.0.0 — Authoritative State Machine & Freshness Audit  
**Target Subsystems:** `src/broker/services/`, `src/broker/models/`

---

## 1. INDEPENDENT STATE MACHINE SPECIFICATION

```
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│    BROKER AUTH STATE    │      │     WEBSOCKET STATE     │      │   SUBSCRIPTION STATE    │
├─────────────────────────┤      ├─────────────────────────┤      ├─────────────────────────┤
│ • DISCONNECTED          │      │ • NOT_INITIALIZED       │      │ • UNINITIALIZED         │
│ • AUTHENTICATING        │      │ • CONNECTING            │      │ • SUBSCRIBING           │
│ • AUTHENTICATED         │      │ • CONNECTED             │      │ • SUBSCRIBED            │
│ • TOKEN_EXPIRED         │      │ • DISCONNECTED          │      │ • RESUBSCRIBING         │
│ • TOKEN_INVALID         │      │ • RECONNECTING          │      │ • PARTIAL_SUBSCRIPTION  │
│ • AUTH_ERROR            │      │ • ERROR                 │      │ • FAILED                │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │    MARKET FEED STATE    │
                                 ├─────────────────────────┤
                                 │ • LIVE (<3.0s)          │
                                 │ • LAGGING (3.0s - 10.0s)│
                                 │ • STALE (>10.0s)        │
                                 │ • RECOVERING            │
                                 │ • UNAVAILABLE           │
                                 │ • CLOSED / STANDBY      │
                                 └─────────────────────────┘
```

**Cardinal Rule:** `broker_auth_state == "AUTHENTICATED"` and `websocket_state == "CONNECTED"` **NEVER** imply market data is live. Market data freshness is independently evaluated per domain using monotonic observation timestamps.

---

## 2. DOMAIN-SPECIFIC FRESHNESS INVENTORY & THRESHOLDS

| Data Domain | Freshness Indicator Field | Live Hours Stale Threshold | Market-Closed Status | Source Implementation |
|:---|:---|:---:|:---:|:---|
| **NIFTY Spot** | `last_source_observation_at` | **>15.0s** (Warn at >3.0s) | `CLOSED / STANDBY` | `src/broker/services/stream_health_monitor.py:96` |
| **NIFTY 5m Candles** | `last_candle_timestamp` | **>300s (5 min)** | `FROZEN_EOD` | `src/broker/services/market_context_builder.py:310` |
| **Market Breadth** | `breadth.observed_at` | **>60.0s** | `CLOSED / STANDBY` | `src/broker/services/market_feed_service.py:180` |
| **India VIX** | `vix.observed_at` | **>30.0s** | `CLOSED / STANDBY` | `src/broker/services/market_feed_service.py:215` |
| **Option Chain Depth** | `options.last_valid_options_at`| **>30.0s** | `FROZEN_BASELINE` | `src/options_engine/chain_builder.py:95` |
| **FII / DII Cash** | `fii_dii.as_of_date` | **EOD Once Daily** | `STATIC_ARCHIVE` | `src/data_engine/institutional.py:45` |
| **Global Macro Quotes** | `macro.quotes.*.updated_at` | **>120.0s** | `EXTENDED_HOURS` | `src/data_engine/macro.py:80` |
| **News & Catalysts** | `news.last_scraped_at` | **>300.0s** | `ACTIVE_LEDGER` | `src/news_engine/sentiment_service.py:110` |

---

## 3. SILENT STALL DETECTION & WATCHDOG

- **Silent Stall Detector Status:** **READY (Implemented)**
- **Detection Mechanism:**
  [`StreamHealthMonitor.check_feed_liveness()`](file:///opt/ardhamind/staging/src/broker/services/stream_health_monitor.py#L85) evaluates `time.time() - self.last_source_observation_at`.
  If the WebSocket transport is `CONNECTED` but no ticks arrive for $>15.0$ seconds during market hours, the feed status immediately transitions from `HEALTHY` to `STALE`, logs a `SILENT_STALL` event, and triggers `StreamingOrchestrator` reconnect watchdog without waiting for transport-level socket timeouts.
