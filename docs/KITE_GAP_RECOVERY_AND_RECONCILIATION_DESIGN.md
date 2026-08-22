# ZERODHA KITE FEED GAP RECOVERY & CONNECTIVITY RECONCILIATION DESIGN

**Document Version:** 1.0.0 — Authoritative Gap Recovery Design  
**Target Modules:** `src/broker/services/market_feed_service.py`, `src/storage/connectivity_ledger.py`

---

## 1. COMPREHENSIVE CONNECTION & FEED STATE MATRIX (CASES A–I)

| Operational Scenario | Ingestion State | What is Written to Disk | What is NOT Written | Last-Valid Behavior | Recovery Source | Finalization Rule | Quality Status |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **Case A: Market Open + Kite Disconnected** | `DISCONNECTED` | Connectivity Event (`WS_DISCONNECTED`) | No false ticks / No zero candles | Retains last observed live spot & depth in memory | Reconnection daemon | Prohibited until restored or EOD | `DEGRADED` |
| **Case B: Market Open + Connected + No Ticks (Silent Stall)** | `STALLED_SILENT` | Connectivity Event (`SILENT_STALL`) | No flatline duplicate ticks | Stalls last timestamp; warns telemetry | Heartbeat watchdog triggers reconnect | Prohibited until restored or EOD | `DEGRADED` |
| **Case C: Market Open + Partial Domain Failure** (e.g. Options depth down, Spot live) | `PARTIAL_FEED` | Real-time Spot & 5m Candles; records `OPTIONS_STALE` event | No fake 0.00 options depth | Spot continues; Options shows `UNAVAILABLE` | Option quote polling retry | Permitted with `PARTIAL_EVIDENCE` flag | `PARTIAL` |
| **Case D: Market Open + Reconnecting** | `RECONNECTING` | Reconnect attempt logged | No data writes during socket handshake | Holds last valid in-memory state | Reconnect exponential backoff | Hold pending | `DEGRADED` |
| **Case E: Market Open + Recovered** | `HEALTHY` | Connectivity Event (`MARKET_FEED_RECOVERED`); Gap candles | No gaps left in candle buffer | Backfills 1-min & 5-min candles via REST | `kite.historical_data` REST API | Normal 15:35 EOD finalization | `COMPLETE` |
| **Case F: Market Closed (15:30–09:00)** | `CLOSED` | Off-hours recovery snapshot (periodic 60s) | No live candle appends | Freezes 15:30 EOD closing truth | In-memory EOD baseline | Read-only | `FROZEN` |
| **Case G: Weekend / NSE Holiday** | `HOLIDAY` | Nothing (Zero session files created) | No weekend session records | Serves previous Friday's finalized close | Previous trading day close | Read-only | `HOLIDAY_STANDBY` |
| **Case H: Server Offline at 15:30** | `OFFLINE` | Nothing during crash | No corrupted partial files | Recovers on startup via missed-close routine | Kite historical Daily API | Automatic on next startup | `RECOVERED` |
| **Case I: Kite Down until after Close** | `OUTAGE_EXTENDED` | Connectivity outage ledger | No live ticks recorded | Uses last valid options snapshot; EOD OHLC via exchange | NSE / NSDL EOD reports | Reconciles using exchange EOD settlements | `RECOVERED_PARTIAL` |

---

## 2. SEPARATION OF CONCERNS: AUTH VS FEED VS SUBSCRIPTION

```
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
│   BROKER AUTH STATE    │      │  WEBSOCKET COMM STATE  │      │   FEED FRESHNESS STATE │
├────────────────────────┤      ├────────────────────────┤      ├────────────────────────┤
│ • AUTHENTICATED        │      │ • CONNECTED            │      │ • LIVE_STREAMING (<1s) │
│ • TOKEN_EXPIRED        │      │ • CONNECTING           │      │ • STALLED (>3s)        │
│ • UNCONFIGURED         │      │ • CLOSED / DISCONNECTED│      │ • DEGRADED (>10s)      │
└────────────────────────┘      └────────────────────────┘      └────────────────────────┘
```
**Strict Architectural Rule:** `broker_auth_state == "AUTHENTICATED"` and `websocket_state == "CONNECTED"` **NEVER** imply market data is live. Market data freshness is independently evaluated using monotonically advancing exchange timestamps (`observed_at_ist`).

---

## 3. DETERMINISTIC GAP RECOVERY WORKFLOW

```
  [Live Streaming] ──► [WS Drop Detected] ──► [Record Outage Timestamp T_drop]
                                                      │
                                                      ▼
  [Live Resumed]   ◄── [Recompute Indicators] ◄── [Backfill 5m Candles via REST]
                                                      │
                                                      ▼
                                       [Mark Provenance: RECOVERED_HISTORICAL]
```

1. **Detection:** When WebSocket tick delta exceeds 3,000ms during market hours, the feed monitor logs a `SILENT_STALL` or `WS_DISCONNECTED` event.
2. **Re-establishment:** WebSocket reconnects and resubscribes to NIFTY 50 and active option tokens.
3. **Gap Backfill:** System issues a single historical REST request:
   `kite.historical_data(nifty_token, from_date=T_drop - 5m, to_date=now, interval="minute")`
4. **Deduplication & Insertion:** Fetched candles are deduplicated against existing buffer timestamps and cleanly merged.
5. **Indicator Recalculation:** `EMA20`, `EMA50`, `EMA200`, `RSI14`, `VWAP` are recomputed in **<0.5ms**, restoring full analytical integrity without restarting the server.
6. **Provenance Tracking:** Ingested gap candles are tagged with `"source": "RECOVERED_HISTORICAL"` in memory and audit logs.
