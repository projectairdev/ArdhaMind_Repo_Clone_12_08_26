# Canonical Data Truth Matrix (STAGING ONLY)

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Specification**: Detailed field-by-field lineage matrix across all active Ardha Mind workspaces.

---

## 1. MARKET Workspace — NIFTY View

| UI Field | Display Value | Source Provider | Canonical Field Path | Frontend Component | Update Cadence | Fallback Behavior | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NIFTY Spot Price** | 24,450.75 | Zerodha KiteConnect | `market_data.current_spot` | `NiftyLiveWorkspace` | Live Stream (1s) | `"WAITING FOR LIVE DATA"` | **PASS** |
| **Spot Change / %** | +125.40 (+0.52%) | Zerodha KiteConnect | `market_data.spot_change` / `pct` | `NiftyLiveWorkspace` | Live Stream (1s) | `"--"` | **PASS** |
| **Session Open / High / Low** | 24,350 / 24,480 / 24,310 | Zerodha KiteConnect | `market_data.open / high / low` | `NiftyLiveWorkspace` | Live Stream (1s) | `"--"` | **PASS** |
| **Previous Close** | 24,325.35 | Zerodha KiteConnect | `market_data.previous_close` | `NiftyLiveWorkspace` | Daily Sync | `"--"` | **PASS** |
| **Intraday VWAP** | 24,412.50 | Derived (Kite Ticks) | `market_data.vwap` | `NiftyLiveWorkspace` | Tick Recalculation | `"UNAVAILABLE"` | **PASS** |
| **Market Session Status** | CLOSED / LIVE | System Clock / Kite | `market_session.status` | `NiftyLiveWorkspace` | Session Change | `"CLOSED"` | **PASS** |
| **Chart Candles (1m/5m)** | OHLC Series | Kite Historical API | `market_data.candles` | `NiftyCandlestickChart` | 1m Bar Close | Empty Series | **PASS** |
| **Advancing / Declining Sectors** | 14 Adv / 10 Dec | NSE Sector Feed | `market_data.sector_breadth` | `SectorParticipationDonut` | 15s | `0 / 0` (Fail-Closed) | **PASS** |
| **India VIX** | 13.45 (-2.1%) | NSE VIX Feed | `macro_intelligence.india_vix` | `VixGauge` | 15s | `"UNAVAILABLE"` | **PASS** |

---

## 2. MARKET Workspace — METRICS View

| UI Field | Display Value | Source Provider | Canonical Field Path | Frontend Component | Update Cadence | Fallback Behavior | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EMA 20 / 50 / 200** | 24,410 / 24,320 / 23,890 | Technical Engine | `market_data.ema_20 / 50 / 200` | `MarketPulseWorkspace` | 1m Bar | `"--"` | **PASS** |
| **RSI (14)** | 58.4 | Technical Engine | `market_data.rsi` | `MarketPulseWorkspace` | 1m Bar | `"--"` | **PASS** |
| **MACD / Signal** | +42.1 / +38.0 | Technical Engine | `market_data.macd` | `MarketPulseWorkspace` | 1m Bar | `"--"` | **PASS** |
| **Pivot / R1 / S1** | 24,380 / 24,520 / 24,250 | Technical Engine | `market_data.pivots` | `MarketPulseWorkspace` | Daily | `"--"` | **PASS** |
| **GIFT Nifty** | 24,485 (+0.4%) | NSE IX / Global Feed | `macro_intelligence.quotes.GIFT_NIFTY` | `GlobalMarketsTable` | 15s | `isAvailable: false` | **PASS** |
| **S&P 500 / Nasdaq** | 5,580 / 17,890 | Yahoo Finance / Global | `macro_intelligence.quotes.S&P 500` | `GlobalMarketsTable` | 30s | `isAvailable: false` | **PASS** |
| **Brent Crude Oil** | $82.40/bbl | Global Commodities | `macro_intelligence.quotes.BRENT_CRUDE` | `GlobalMarketsTable` | 30s | `isAvailable: false` | **PASS** |
| **USD / INR** | 83.92 | RBI / Forex Feed | `macro_intelligence.quotes.USD_INR` | `GlobalMarketsTable` | 30s | `isAvailable: false` | **PASS** |

---

## 3. MARKET Workspace — OPTIONS View

| UI Field | Display Value | Source Provider | Canonical Field Path | Frontend Component | Update Cadence | Fallback Behavior | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Selected Expiry** | 18 Aug 2026 | NSE Option Chain | `option_intelligence.expiry` | `OptionsWorkspace` | Expiry Select | Default Weekly | **PASS** |
| **ATM Strike** | 24,450 | Derived (Spot / 50) | `option_intelligence.atm_strike` | `OptionsWorkspace` | Tick | Spot Rounding | **PASS** |
| **PCR (OI)** | 1.12 | NSE Option Chain | `option_intelligence.pcr` | `OptionsWorkspace` | 5s | `"UNAVAILABLE"` | **PASS** |
| **Max Pain Pin** | 24,400 | Derived (Option OI) | `option_intelligence.max_pain` | `OptionsWorkspace` | 15s | `"UNAVAILABLE"` | **PASS** |
| **ATM IV** | 13.8% | Derived (Black-Scholes) | `option_intelligence.atm_iv` | `OptionsWorkspace` | 5s | `"UNAVAILABLE"` | **PASS** |
| **Call Wall (Resistance)** | 24,600 | NSE Option Chain | `option_intelligence.highest_call_oi_strike` | `OptionsWorkspace` | 15s | `"UNAVAILABLE"` (Repaired) | **PASS** |
| **Put Wall (Support)** | 24,300 | NSE Option Chain | `option_intelligence.highest_put_oi_strike` | `OptionsWorkspace` | 15s | `"UNAVAILABLE"` (Repaired) | **PASS** |

---

## 4. MARKET INTELLIGENCE Workspace

| UI Field | Display Value | Source Provider | Canonical Field Path | Frontend Component | Update Cadence | Fallback Behavior | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Scenario** | Bullish Continuation | Scenario Resolver | `forward_outlook.primary_scenario` | `MarketIntelligenceWorkspace` | 15s | Fail-Closed Stub | **PASS** |
| **Outlook Confidence** | HIGH / MODERATE | Scenario Engine | `forward_outlook.overall_confidence` | `MarketIntelligenceWorkspace` | 15s | `"MODERATE"` | **PASS** |
| **Supporting Evidence** | 3 Verified Clues | Evidence Engine | `forward_outlook.supporting_evidence` | `MarketIntelligenceWorkspace` | 15s | Empty Array | **PASS** |
| **Invalidation Rules** | Spot < 24,350 | Technical Engine | `forward_outlook.invalidation` | `MarketIntelligenceWorkspace` | 15s | Empty Array | **PASS** |

---

## 5. NEWS & UPDATES Workspace

| UI Field | Display Value | Source Provider | Canonical Field Path | Frontend Component | Update Cadence | Fallback Behavior | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Verified Headline** | RBI Policy Update | Verified RSS Feed | `news_intelligence.items.headline` | `NewsWorkspace` | 60s Poll | Empty Feed | **PASS** |
| **Relative Publication Age** | "14m ago" | Derived (Published IST) | `news_intelligence.items.published_at` | `NewsCard` | 10s Re-render | IST Date | **PASS** |
| **High Impact Count** | 4 Verified Events | Classifier Engine | `news_intelligence.high_impact_count` | `NewsWorkspace` | 60s Poll | `0` | **PASS** |

---

## 6. PORTFOLIO Workspace

| UI Field | Display Value | Source Provider | Canonical Field Path | Frontend Component | Update Cadence | Fallback Behavior | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Open Positions** | Live Position List | Phase3 Engine / Broker | `/api/phase3/state` | `PortfolioWorkspace` | WS / Poll (5s) | Empty List | **PASS** |
| **Execution Kill Switch** | INACTIVE / ACTIVE | Safety Manager | `/api/phase3/safety/status` | `PortfolioWorkspace` | WS / Poll (5s) | `"INACTIVE"` | **PASS** |

---

## 7. SETTINGS & GLOBAL SHELL Workspace

| UI Field | Display Value | Source Provider | Canonical Field Path | Frontend Component | Update Cadence | Fallback Behavior | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Broker Session Status** | CONNECTED | Zerodha OAuth | `/api/broker/health` | `WorkstationTopBar` | 10s Poll | `"DISCONNECTED"` | **PASS** |
| **System Runtime ID** | `a624d9b5-staging` | System Config | `canonical_presentation.runtime_id` | `SettingsWorkspace` | Static | `"—"` | **PASS** |
