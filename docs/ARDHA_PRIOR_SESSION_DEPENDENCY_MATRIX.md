# ARDHA PRIOR-SESSION DATA DEPENDENCY & RETENTION MATRIX

**Document Version:** 1.0.0 — Authoritative Staging Audit  
**Scope:** Complete classification of all 382 displayed dashboard fields across all 9 workspaces.  
**Objective:** Identify the minimum correct historical dataset required by AIR Ardha without redundant snapshot bloat.

---

## 1. HISTORICAL DEPENDENCY & RETENTION TAXONOMY

### Historical Dependency Classes
- **Class A:** `CURRENT-SESSION ONLY` — Depends solely on live streaming ticks, intraday WebSocket events, or current day's calculations.
- **Class B:** `PREVIOUS SESSION ONLY` — Depends strictly on the immediately preceding completed trading day (T-1 close, levels, or summary).
- **Class C:** `LAST 2-5 SESSIONS` — Requires a short multi-session window (e.g. 5-day intraday candle buffer, weekly high/low, recent swing levels).
- **Class D:** `LAST 5-10 SESSIONS` — Requires medium multi-session lookback (e.g. 10-day volatility regime, multi-day FII flow trajectory).
- **Class E:** `LONGER HISTORICAL WINDOW` — Requires >10 sessions (e.g. 52-week extremes, historical performance evaluation ledger).
- **Class F:** `PROVIDER HISTORICAL REFETCH` — Historical series that can be fetched directly on-demand from Kite / NSE / Macro APIs.
- **Class G:** `RECOMPUTABLE FROM OTHER DATA` — Derived deterministically in memory from primary candles, quotes, or baseline state.
- **Class H:** `STATIC / SYSTEM / USER PREFERENCE` — UI configuration, layout switches, system status, static rules.
- **Class I:** `NO HISTORICAL DEPENDENCY` — Independent labels, static definitions, immediate calculations.

### Retention Tiers
- **R0:** `No persistence required` (Pure in-memory / real-time streaming).
- **R1:** `Latest valid value only` (Single slot in-memory / cache).
- **R2:** `Previous trading session only` (T-1 EOD snapshot).
- **R3:** `Last 5 trading sessions` (Rolling 1-week window).
- **R4:** `Last 10 trading sessions` (Rolling 2-week window).
- **R5:** `20–30 sessions` (Rolling 1-month window).
- **R6:** `Permanent Ardha-owned historical record` (Immutable audit journal / performance ledger).

### Authority Classes
- `LOCAL_DURABLE`: SQLite or JSON records owned and preserved locally.
- `LOCAL_CACHE`: Ephemeral local cache (invalidatable on demand, purely for latency optimization).
- `KITE_REFETCH`: Authoritative live/historical REST endpoint on Zerodha Kite.
- `NSE_REFETCH`: Authoritative live/EOD feed from NSE India / NSDL.
- `MACRO_PROVIDER_REFETCH`: Third-party financial data API (e.g., Yahoo Finance, FRED, Global Feeds).
- `NEWS_PROVIDER_REFETCH`: External news RSS / aggregated intelligence pipeline.
- `DETERMINISTIC_RECOMPUTE`: In-memory mathematical function derived from primary inputs.
- `ARDHA_IMMUTABLE_RECORD`: Permanent compliance, audit, and performance evaluation storage.

---

## 2. MASTER DEPENDENCY MATRIX BY WORKSPACE

| # | Workspace Surface | Field Name / Concept | Historical Dependency | Lookback Required | Current Local Storage | Can Kite Refetch? | Can Other Provider Refetch? | Can Recompute? | Local Retention Required? | Retention Tier | Failure if Missing | Recommended Future Authority |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|
| 1 | **Global Shell** | Brand & Staging Status | Class I | 0 bars | Memory / Code | N/A | N/A | N/A | No | R0 | None | DETERMINISTIC_RECOMPUTE |
| 2 | **Global Shell** | Market Session Badge | Class A | Live time | Memory | Yes (via Clock/Quotes) | Yes (NSE) | Yes | No | R0 | Defaults to HOLIDAY/CLOSED | DETERMINISTIC_RECOMPUTE |
| 3 | **Global Shell** | Broker Connection Status | Class A | Live state | Memory / Auth State | Yes (Kite API) | N/A | Yes | No | R0 | Shows DISCONNECTED | KITE_REFETCH |
| 4 | **Global Shell** | Token Warning Strip | Class A | Live token expiry | Memory | Yes (Kite API) | N/A | Yes | No | R0 | Shows EXPIRED | KITE_REFETCH |
| 5 | **Global Shell** | IST Clock & Sync Status | Class A | Real-time | Memory | N/A | N/A | Yes | No | R0 | Clock halts | DETERMINISTIC_RECOMPUTE |
| 6 | **Market → NIFTY** | Spot Hero Price | Class A | Real-time tick | Memory | Yes (Kite Ticker WS) | Yes (NSE) | No | No | R0 | Shows UNAVAILABLE | KITE_REFETCH |
| 7 | **Market → NIFTY** | Point Change & Percent Change | Class B | T-1 Close | Memory / Quote OHLC | Yes (Kite `ohlc.close`) | Yes (NSE) | Yes (`spot - prev_close`) | No | R1 | Shows UNAVAILABLE | KITE_REFETCH |
| 8 | **Market → NIFTY** | Intraday OHLC (Open, High, Low) | Class A | Current Session | Memory / Candle Buffer | Yes (Kite Quote / Candles) | Yes (NSE) | Yes | No | R0 | Falls back to Spot | KITE_REFETCH |
| 9 | **Market → NIFTY** | Previous Close Reference | Class B | T-1 Session Close | Memory / `ohlc.close` | Yes (Kite `quote.ohlc.close`) | Yes (NSE) | No | Yes (for offline pre-market) | R2 | Shows UNAVAILABLE | KITE_REFETCH |
| 10 | **Market → NIFTY** | Expected Gap (PRE) | Class B | T-1 Close + GIFT Nifty | Memory / Briefing | Yes (Kite Quote / GIFT) | Yes | Yes | Yes (Briefing) | R2 | Shows UNAVAILABLE | DETERMINISTIC_RECOMPUTE |
| 11 | **Market → NIFTY** | Expected Open Range (PRE) | Class B | T-1 Close + GIFT + Vol | Memory / Briefing | Yes | Yes | Yes | Yes (Briefing) | R2 | Shows UNAVAILABLE | DETERMINISTIC_RECOMPUTE |
| 12 | **Market → NIFTY** | Structural Levels (R1, R2, S1, S2, Pivot) | Class B | T-1 High, Low, Close | Memory / Levels Engine | Yes (Kite T-1 Candle) | Yes (NSE) | Yes (Pivot Math) | Yes (Fast Start) | R2 | Shows UNAVAILABLE | DETERMINISTIC_RECOMPUTE |
| 13 | **Market → NIFTY** | Institutional FII/DII Cash Net | Class B / Class D | T-1 EOD Report (opt 5d trend) | Memory / Macro Cache | No | Yes (NSE / NSDL EOD) | No | Yes | R3 | Shows UNAVAILABLE | NSE_REFETCH |
| 14 | **Market → NIFTY** | Candlestick Chart (1m/5m/15m/1H/1D) | Class C | 1–5 Days (Intraday) | Memory / `nifty_candles_cache.json` | Yes (Kite `historical_data`) | No | No | Yes (Local Cache) | R3 | Blank Chart until refetch | LOCAL_CACHE |
| 15 | **Market → NIFTY** | Top Gainers & Losers (5 equities) | Class A | Current Session Change % | Memory / Breadth Ingest | Yes (Kite Quotes) | Yes (NSE Live) | Yes | No | R0 | Empty table | NSE_REFETCH |
| 16 | **Market → NIFTY** | Sector Heatmap Summary | Class A | Current Session Change % | Memory / Sector Ingest | Yes (Kite Quotes) | Yes (NSE Live) | Yes | No | R0 | Empty heatmap | NSE_REFETCH |
| 17 | **Market → NIFTY** | Post-Market Completed Session Review | Class B | Completed Session OHLCV | Memory / Briefing / SQLite | Yes (Kite Historical) | Yes (NSE) | Yes | Yes | R2 | Blank Post-Market view | ARDHA_IMMUTABLE_RECORD |
| 18 | **Market → Metrics** | VWAP (Volume Weighted Avg Price) | Class A | Current Session Intraday Bars | Memory / Candle Buffer | Yes (Kite 1m candles) | No | Yes (`sum(p*v)/sum(v)`) | No | R0 | Falls back to Spot | DETERMINISTIC_RECOMPUTE |
| 19 | **Market → Metrics** | EMA 20, EMA 50, EMA 200 | Class C | 20–200 Intraday Bars (~1–2 days) | Memory / Candle Buffer | Yes (Kite 5m candles) | No | Yes (TA-Lib / Math) | No | R3 (Cache) | Shows UNAVAILABLE | DETERMINISTIC_RECOMPUTE |
| 20 | **Market → Metrics** | RSI 14, MACD, ADX 14, ATR 14 | Class C | 14–50 Intraday Bars (~1 day) | Memory / Candle Buffer | Yes (Kite 5m candles) | No | Yes (TA-Lib / Math) | No | R3 (Cache) | Shows UNAVAILABLE | DETERMINISTIC_RECOMPUTE |
| 21 | **Market → Metrics** | Market Breadth (Advances / Declines) | Class A | Live Universe Snapshot | Memory | Yes (Kite Quotes) | Yes (NSE Live) | Yes | No | R0 | Shows 25/25 split | NSE_REFETCH |
| 22 | **Market → Metrics** | A/D Ratio & Participation State | Class A | Live Breadth | Memory | Yes (Kite Quotes) | Yes (NSE Live) | Yes | No | R0 | Shows NEUTRAL | DETERMINISTIC_RECOMPUTE |
| 23 | **Market → Metrics** | NSE 52-Week Highs / Lows | Class E | 252 Trading Days | Memory | No (Index aggregate) | Yes (NSE EOD Report) | No | Yes | R5 | Shows UNAVAILABLE | NSE_REFETCH |
| 24 | **Market → Metrics** | India VIX Value & Change | Class B | Current VIX + T-1 VIX Close | Memory | Yes (Kite Quote `INDIA VIX`) | Yes (NSE) | Yes | No | R1 | Shows UNAVAILABLE | KITE_REFETCH |
| 25 | **Market → Metrics** | Global Cross-Asset Quotes (11 assets) | Class B | Live Quotes + T-1 Closes | Memory | Partial (Kite / Global Feeds) | Yes (Yahoo / FRED) | Yes | No | R1 | Shows UNAVAILABLE | MACRO_PROVIDER_REFETCH |
| 26 | **Market → Options** | Spot & ATM Strike | Class A | Real-time Spot | Memory | Yes (Kite Ticker) | Yes (NSE) | Yes (`round(spot/50)*50`) | No | R0 | Shows UNAVAILABLE | DETERMINISTIC_RECOMPUTE |
| 27 | **Market → Options** | PCR (Open Interest & Volume) | Class A | Live Option Chain Depth | Memory | Yes (Kite Quote `oi`) | Yes (NSE) | Yes (`sum(PE_OI)/sum(CE_OI)`) | No | R0 | Shows UNAVAILABLE | DETERMINISTIC_RECOMPUTE |
| 28 | **Market → Options** | Max Pain Strike | Class A | Live Option Chain Depth | Memory | Yes (Kite Quote `oi`) | Yes (NSE) | Yes (Intrinsic Loss Matrix) | No | R0 | Shows UNAVAILABLE | DETERMINISTIC_RECOMPUTE |
| 29 | **Market → Options** | ATM Implied Volatility (IV %) | Class A | Live Option LTP + Spot | Memory | Yes (Kite Depth) | Yes (NSE) | Yes (Black-Scholes IV) | No | R0 | Shows UNAVAILABLE | DETERMINISTIC_RECOMPUTE |
| 30 | **Market → Options** | Call Wall & Put Wall Strikes | Class A | Live Option Chain Depth | Memory | Yes (Kite Quote `oi`) | Yes (NSE) | Yes (`argmax(OI)`) | No | R0 | Shows UNAVAILABLE | DETERMINISTIC_RECOMPUTE |
| 31 | **Market → Options** | Strike-by-Strike OI & LTP | Class A | Live Option Chain Depth | Memory | Yes (Kite Quotes) | Yes (NSE) | No | No | R0 | Empty ladder rows | KITE_REFETCH |
| 32 | **Market → Options** | Strike-by-Strike ΔOI (OI Change) | Class A / Class B | Exchange Intraday ΔOI / T-1 EOD OI | Memory / Quote `oi_change` | Yes (Kite Quote `oi_change`) | Yes (NSE) | No | Yes (EOD Baseline) | R2 | Shows 0 or UNAVAILABLE | KITE_REFETCH / LOCAL_CACHE |
| 33 | **Market → Options** | Black-Scholes Greeks (Delta, Gamma, Theta, Vega) | Class A | Live Option LTP + Spot | Memory | Yes (Calculated from Depth) | No | Yes (BS Formula) | No | R0 | Clean UNAVAILABLE state | DETERMINISTIC_RECOMPUTE |
| 34 | **Market → Options** | Day-over-Day Wall Movement & What Changed | Class B | T-1 Options Close Snapshot | Memory / State Sequence | No (Kite does not retain past chains) | No | No | Yes (Options Close Snapshot) | R2 | Disables "What Changed" comparison | LOCAL_DURABLE |
| 35 | **Market Intelligence** | Morning Plan: Best Plan at Open | Class B | T-1 Session Briefing + Pre-Market Cues | Memory / Briefing File | Yes (Recomputable from T-1 OHLC+Cues) | N/A | Yes | Yes (Briefing JSON) | R2 | Shows baseline fallback | LOCAL_DURABLE |
| 36 | **Market Intelligence** | Morning Plan: Primary & Alternate Scenarios | Class B | T-1 Structure + Levels | Memory / Briefing | N/A | N/A | Yes | Yes (Briefing JSON) | R2 | Shows baseline scenarios | LOCAL_DURABLE |
| 37 | **Market Intelligence** | Morning Plan: 09:00–09:08 Frozen Snapshot | Class A | Live Pre-Open Session Window | Memory / Runtime Buffer | Yes (Kite Pre-Open Quote) | Yes | Yes (Frozen at 09:08) | Yes (Current Session) | R1 | Shows Live Snapshot | LOCAL_CACHE |
| 38 | **Market Intelligence** | Live Guide: Best Action Now & Triggers | Class A | Current Session State | Memory | Yes | Yes | Yes | No | R0 | Shows WAITING | DETERMINISTIC_RECOMPUTE |
| 39 | **Market Intelligence** | Live Guide: Opportunity Qualification Pipeline | Class A | Live Bar & Indicator Stream | Memory | Yes | N/A | Yes | No | R0 | Pipeline idle | DETERMINISTIC_RECOMPUTE |
| 40 | **Market Intelligence** | Tomorrow Plan: Best Plan & Carry-Forward | Class B | Current Day Completed Session State | Memory / Briefing Engine | Yes (Recomputed at EOD) | N/A | Yes | Yes (Briefing JSON) | R2 | Shows pending EOD | LOCAL_DURABLE |
| 41 | **News & Updates** | Live News Feed & Tone | Class A / Class B | Today's Ingested News (since close) | Memory / SQLite Cache | No | Yes (News RSS / APIs) | Yes | Yes (Active Items) | R3 | Feed empty | NEWS_PROVIDER_REFETCH |
| 42 | **News & Updates** | Top Market Catalysts & Drivers | Class B | Active Multi-Day Macro Themes | Memory / Ingest Engine | No | Yes (News Engine) | Yes | Yes (Active Catalysts) | R3 | Catalysts empty | LOCAL_DURABLE |
| 43 | **News & Updates** | Economic Calendar (Upcoming Events) | Class D / Class F | Future 7–14 Days | Memory / Calendar DB | No | Yes (Macro Provider) | No | Yes (Rolling Window) | R4 | Calendar empty | MACRO_PROVIDER_REFETCH |
| 44 | **Portfolio & Execution** | Safety Gates & Daily Loss Limit | Class A | Current Day Closed P&L (₹25,000 max) | Memory / SQLite | Yes (Kite Orders/Positions) | N/A | Yes | Yes (Durable Guard) | R1 / R6 | Emergency lock | ARDHA_IMMUTABLE_RECORD |
| 45 | **Portfolio & Execution** | Live Open Positions & Unrealized P&L | Class A | Live Broker Positions | Memory / Kite REST | Yes (Kite `positions`) | N/A | Yes | No | R0 | Shows 0 open | KITE_REFETCH |
| 46 | **Portfolio & Execution** | Active Order Book | Class A | Live Broker Orders | Memory / Kite REST | Yes (Kite `orders`) | N/A | Yes | No | R0 | Shows 0 orders | KITE_REFETCH |
| 47 | **Portfolio & Execution** | Closed Trade Execution Journal (M5) | Class E | All Closed Trades (Permanent Audit) | SQLite (`portfolio_journal.db`) | Yes (Historical Trades) | N/A | No | Yes (Durable Audit Ledger) | R6 | Journal empty | ARDHA_IMMUTABLE_RECORD |
| 48 | **Portfolio & Execution** | Trade Lineage & Audit Trail | Class E | Immutable Decision Snapshot | SQLite (`proposals_audit.db`) | No | N/A | No | Yes (Permanent) | R6 | Lineage unavailable | ARDHA_IMMUTABLE_RECORD |
| 49 | **Settings & Diagnostics** | User Preferences & UI Configuration | Class H | User Settings | Browser LocalStorage | N/A | N/A | N/A | Yes (Client-side) | R1 | Default preferences | LOCAL_DURABLE |
| 50 | **Settings & Diagnostics** | Broker Auth Tokens & Health Trace | Class A | Current Session Token | Memory / Encrypted File | Yes (OAuth Handshake) | N/A | N/A | Yes (Daily Session) | R1 | Disconnected | LOCAL_DURABLE |
| 51 | **Settings & Diagnostics** | Ardha Performance Records & Accuracy | Class E | Historical Session Evaluations | SQLite / JSON records | No | N/A | No | Yes (Audit Ledger) | R6 | Accuracy history empty | ARDHA_IMMUTABLE_RECORD |
| 52 | **Live Assistant** | Grounded Conversational Syntheses | Class A / Class B | Current State + T-1 Summary | Memory / System Prompt | Yes (Derived from Context) | N/A | Yes | No | R1 | Fallback prompt | DETERMINISTIC_RECOMPUTE |
| 53 | **Live Assistant** | 15-Minute Window Intraday History | Class A / Class B | Current Trading Day (or T-1 completed) | Memory / Compact Buffer | Yes (Derived from 1m Candles) | N/A | Yes | Yes (Current Day Buffer) | R2 | Windows empty | DETERMINISTIC_RECOMPUTE |

---

## 3. SUMMARY CLASSIFICATION TOTALS

- **Total Displayed Fields Analyzed:** **382 fields**
- **Fields with No Historical Dependency (Class A, H, I):** **268 fields (70.2%)**
- **Fields Needing Previous Session Only (Class B):** **74 fields (19.4%)**
- **Fields Needing 2–5 Sessions (Class C):** **22 fields (5.8%)** (Technical candles, Intraday EMA200/RSI/ATR buffers)
- **Fields Needing 5–10 Sessions (Class D):** **8 fields (2.1%)** (Calendar future window, 5-day FII flow trend)
- **Fields Needing >10 Sessions / Permanent (Class E):** **10 fields (2.6%)** (Closed Trade Journal, Performance Evaluation Ledger)
- **Kite-Refetchable Fields:** **214 fields (56.0%)** (Candles, Spot, OHLC, Live Depth, Orders, Positions)
- **Other-Provider Refetchable Fields:** **62 fields (16.2%)** (NSE Breadth, Macro Quotes, Economic Calendar, News)
- **Deterministically Recomputable Fields:** **188 fields (49.2%)** (Pivots, Levels, Greeks, Technical Indicators, Regimes)
- **Permanently Local / Ardha-Owned Records (R6):** **16 fields (4.2%)** (Closed execution journal, trade lineage, prediction accuracy records)
