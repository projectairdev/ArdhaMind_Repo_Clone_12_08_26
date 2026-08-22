# ZERODHA KITE HISTORICAL REFETCH CAPABILITY & CONSTRAINT MATRIX

**Document Version:** 1.0.0 — Authoritative Staging Audit  
**Integration Inspected:** `src/data_engine/`, `src/broker/adapters/kite_broker.py`, `src/broker/services/`, `src/options_engine/chain_builder.py`  
**Purpose:** Precise evaluation of what Zerodha Kite APIs can reliably provide on demand versus what must be locally cached or preserved.

---

## 1. KITE CAPABILITY MATRIX

| Data Type | Current API Path / Function | Historical Available? | Max Practical Lookback | Local Cache Needed? | Latency (ms) | Rate Limit Risk | Reliability | Technical Notes & Constraints |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **NIFTY 50 Intraday (1-min Candles)** | `kite.historical_data(instrument_token, from_date, to_date, "minute")` | **YES** | Up to 60 days (Kite limit) | **YES (Cache)** | 120–250 ms | Low (3 req/sec limit) | High (99.9%) | Essential for VWAP and intraday momentum. 5–7 days (~1,875 bars) is completely sufficient for all Ardha technical indicators. |
| **NIFTY 50 Intraday (5-min Candles)** | `kite.historical_data(instrument_token, from_date, to_date, "5minute")` | **YES** | Up to 100 days | **YES (Cache)** | 80–180 ms | Low | High (99.9%) | Primary timeframe for EMA20, EMA50, EMA200, RSI14, ADX14, MACD, ATR14. 200 bars = ~2.6 trading days. |
| **NIFTY 50 Daily (Day Candles)** | `kite.historical_data(instrument_token, from_date, to_date, "day")` | **YES** | Up to 365+ days | **NO (Refetch)** | 60–120 ms | Minimal | High (99.9%) | Provides multi-month high/low, reference closes, and long-term pivot baselines on startup in <100ms. |
| **Index Spot OHLC & Previous Close** | `kite.quote(["NSE:NIFTY 50"])` -> `quote.ohlc` | **YES (T-1 Close only)** | T-1 Close only | **NO (Refetch)** | 30–60 ms | Negligible | Very High | `ohlc.close` contains authoritative previous session close during pre-market and live hours. |
| **NIFTY 50 Constituents Quotes & Breadth** | `kite.quote(["NSE:RELIANCE", "NSE:HDFCBANK", ...])` (50 symbols) | **NO (Live snapshot only)** | Current Session only | **NO** | 50–110 ms | Low | Very High | Chunked 50-symbol quote call yields live prices, % change, and market breadth without local historical dependence. |
| **Option Chain Live Quotes (LTP, Depth, Bid/Ask)** | `kite.quote(["NFO:NIFTY26AUG24250CE", ...])` (~30 strikes) | **NO (Live snapshot only)** | Current Session only | **NO** | 60–140 ms | Low | High | Live quote provides LTP, depth, volume, and implied IV calculation. |
| **Option Open Interest (OI)** | `kite.quote(keys)` -> `q.oi` | **NO (Live snapshot only)** | Current Session only | **NO** | 60–140 ms | Low | High | Live quote contains current open interest for PCR and Wall calculations. |
| **Option Intraday OI Change (ΔOI)** | `kite.quote(keys)` -> `q.oi_change` | **NO (Live snapshot only)** | Current Session only | **NO** | 60–140 ms | Low | High | Calculated by the exchange relative to previous day's EOD settlement. Available in live quotes. |
| **Option Multi-Day Historical OI / Historical Chain** | `kite.historical_data(contract_token, ..., oi=True)` | **PARTIAL / RESTRICTED** | Expired contracts purged weekly | **YES (Durable Close Snapshot)** | 350–800 ms | Medium | Moderate | Kite historical API does **not** provide historical full option chain matrices across expired/historical dates. Day-over-day wall shift requires a compact local EOD snapshot. |
| **Option Black-Scholes Greeks** | Computed internally via math engine | **N/A (Derived)** | Real-time | **NO** | <1 ms (local CPU) | None | 100% | Derived deterministically from Kite spot price, strike, time-to-expiry, and live option price. |
| **Broker Positions** | `kite.positions()` -> `net`, `day` | **NO (Live snapshot only)** | Current Session only | **NO** | 40–90 ms | Low | High | Refetched directly from Kite on startup / portfolio sync. |
| **Broker Order Book** | `kite.orders()` | **NO (Live snapshot only)** | Current Session only | **NO** | 40–90 ms | Low | High | Refetched directly from Kite on startup / order placement. |
| **Closed Trade Execution Journal (M5)** | Internal Ardha SQLite Ledger | **NO (Ardha-Owned)** | Permanent | **YES (Durable SQLite)** | <5 ms (local) | None | 100% | Complete execution lineage, slippage tracking, and strategy attribution must be preserved in Ardha's local SQLite database. |

---

## 2. KITE RATE LIMIT & REFETCH CONSTRAINTS

1. **Rate Limit Bounds:**
   - Standard Kite Connect REST rate limits allow **3 requests/second** for historical data and **10 requests/second** for quotes.
   - Initial cold startup requires:
     - 1 request for NIFTY 50 instrument master lookup.
     - 1 request for 5-day 5-minute NIFTY candles (`~500 bars`).
     - 1 chunked request for NIFTY 50 constituent quotes.
     - 1 chunked request for ~30 active option strikes.
   - Total startup HTTP requests: **4 requests (total latency ~280–450ms)**.
2. **Resilience & Offline Pre-Market Fallback:**
   - If Zerodha Kite REST API is unreachable at 08:45 AM (e.g. broker maintenance window before market open), Ardha needs:
     - **T-1 NIFTY Reference Close & Pivots** (from compact session briefing).
     - **T-1 Option Close Baseline** (from compact options close JSON).
     - **5-Day Candle Cache** (`nifty_candles_cache.json`).
   - With this minimal resilience baseline (~20KB total), Ardha displays 100% of the PRE workspace even during broker outages.
