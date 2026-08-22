# AIR Ardha Staging — Market: Metrics Data-Field Inventory

**Surface:** `Market Workspace` → `Metrics Workspace` (`MarketPulseWorkspace.tsx`)  
**Environment:** Staging (`staging.ardhamind.projectair.in`)  
**Audit Date:** August 2026  
**Scope:** Complete visible data fields across Row 1 (State & Macro Context), Row 2 (5-Column Quantitative Telemetry Grid), Row 3 (3-Column Participation & Interpretation Grid), and Footer Metadata.

---

## 1. ROW 1: MARKET STATE & CROSS-ASSET MACRO CONTEXT

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| NIFTY 50 Spot Hero | SPOT | Number/INR | Kite Feed / Market Bridge | `ticks["NIFTY 50"].last_price` / `spot` | 1s stream | Last valid tick |
| NIFTY Absolute Change | CHANGE | Number/Points | Market Bridge | `ticks["NIFTY 50"].change` | 1s stream | 0.00 |
| NIFTY Change Pct | CHANGE % | Percentage | Market Bridge | `ticks["NIFTY 50"].change_pct` | 1s stream | 0.00% |
| Trend Classification | TREND | Enum/Badge | Deterministic Model | `metrics.trend` | Continuous | "BULLISH" / "NEUTRAL" |
| Market Regime | REGIME | Enum/Badge | Regime Engine | `market_score.regime` | Continuous | "NORMAL_VOLATILITY" |
| Momentum Classification | MOMENTUM | Enum/Badge | Technical Engine | `metrics.momentum` | Continuous | "POSITIVE" / "MODERATE" |
| Volatility Regime | VOLATILITY REGIME | Enum/Badge | Volatility Engine | `market_score.volatility_regime` | Continuous | "LOW" / "NORMAL" |
| Breadth Bias | BREADTH BIAS | Enum/Badge | Breadth Engine | `market_score.breadth.bias` | 15s update | "POSITIVE" / "NEGATIVE" |
| GIFT Nifty Price & Chg % | GIFT NIFTY | Number & % | Macro Ingest Provider | `macro_intelligence.cross_assets["GIFT_NIFTY"]` | 10s polling | Value & sparkline / "--" |
| S&P 500 Price & Chg % | S&P 500 | Number & % | Macro Ingest Provider | `macro_intelligence.cross_assets["SPX"]` | 10s polling | Value & sparkline / "--" |
| Nasdaq Price & Chg % | NASDAQ | Number & % | Macro Ingest Provider | `macro_intelligence.cross_assets["NASDAQ"]` | 10s polling | Value & sparkline / "--" |
| Dow Jones Price & Chg % | DOW JONES | Number & % | Macro Ingest Provider | `macro_intelligence.cross_assets["DOW"]` | 10s polling | Value & sparkline / "--" |
| Nikkei 225 Price & Chg % | NIKKEI 225 | Number & % | Macro Ingest Provider | `macro_intelligence.cross_assets["NIKKEI"]` | 10s polling | Value & sparkline / "--" |
| Hang Seng Price & Chg % | HANG SENG | Number & % | Macro Ingest Provider | `macro_intelligence.cross_assets["HANG_SENG"]` | 10s polling | Value & sparkline / "--" |
| Brent Crude Price & Chg % | BRENT CRUDE | Number & % | Commodity Ingest | `macro_intelligence.cross_assets["BRENT_CRUDE"]` | 10s polling | Value & sparkline / "--" |
| Gold Comex Price & Chg % | GOLD COMEX | Number & % | Commodity Ingest | `macro_intelligence.cross_assets["GOLD"]` | 10s polling | Value & sparkline / "--" |
| USD/INR Exchange Rate & Chg % | USD / INR | Number & % | Currency Ingest | `macro_intelligence.cross_assets["USD_INR"]` | 10s polling | Value & sparkline / "--" |
| US Dollar Index (DXY) & Chg % | DXY INDEX | Number & % | Currency Ingest | `macro_intelligence.cross_assets["DXY"]` | 10s polling | Value & sparkline / "--" |
| US 10Y Treasury Yield & Chg | US 10Y YIELD | Number & pts | Fixed Income Ingest | `macro_intelligence.cross_assets["US10Y"]` | 10s polling | Value & sparkline / "--" |

---

## 2. ROW 2: 5-COLUMN QUANTITATIVE TELEMETRY GRID

### Column A: Price & Trend Metrics
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Intraday VWAP | VWAP | Number/INR | Mathematical Model | `metrics.vwap` | 1s recalculation | Session average / Spot |
| VWAP Deviation % | DEV % | Percentage | Mathematical Model | `metrics.vwap_deviation_pct` | 1s recalculation | 0.00% |
| Exponential MA 20 | EMA 20 | Number/INR | Indicator Engine | `metrics.ema20` | Real-time candle close | Calculated EMA |
| EMA 20 Delta % | EMA20 DELTA | Percentage | Indicator Engine | `(spot - ema20) / ema20 * 100` | 1s stream | 0.00% |
| Exponential MA 50 | EMA 50 | Number/INR | Indicator Engine | `metrics.ema50` | Real-time candle close | Calculated EMA |
| EMA 50 Delta % | EMA50 DELTA | Percentage | Indicator Engine | `(spot - ema50) / ema50 * 100` | 1s stream | 0.00% |
| Exponential MA 200 | EMA 200 | Number/INR | Indicator Engine | `metrics.ema200` | Real-time candle close | Calculated EMA |
| EMA 200 Delta % | EMA200 DELTA | Percentage | Indicator Engine | `(spot - ema200) / ema200 * 100` | 1s stream | 0.00% |
| Relative Strength Index (14) | RSI (14) | Float (0-100) | Indicator Engine | `metrics.rsi14` | 1s recalculation | 50.00 |
| RSI Momentum Zone | RSI ZONE | Enum/Badge | Indicator Engine | `metrics.rsi_zone` | 1s recalculation | "NEUTRAL" / "OVERBOUGHT" |
| MACD Line / Signal Line | MACD (12,26,9) | Tuple (Float) | Indicator Engine | `metrics.macd_line`, `metrics.macd_signal` | 1s recalculation | "14.2 / 10.1" |
| Average Directional Index (14) | ADX (14) | Float | Indicator Engine | `metrics.adx14` | 1s recalculation | 22.4 |
| Market Structure Label | STRUCTURE | Enum | Pattern Engine | `metrics.market_structure` | Continuous | "HIGHER_HIGHS" / "CONSOLIDATION" |

### Column B: Structural Support & Resistance Levels
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Resistance Level 2 | FLOOR R2 | Number & Delta % | Pivot Engine | `levels.r2` | Static | "25,050 (+0.8%)" |
| Resistance Level 1 | FLOOR R1 | Number & Delta % | Pivot Engine | `levels.r1` | Static | "24,950 (+0.4%)" |
| Daily Central Pivot | DAILY PIVOT | Number & Delta % | Pivot Engine | `levels.pivot` | Static | "24,850 (0.0%)" |
| Support Level 1 | FLOOR S1 | Number & Delta % | Pivot Engine | `levels.s1` | Static | "24,750 (-0.4%)" |
| Support Level 2 | FLOOR S2 | Number & Delta % | Pivot Engine | `levels.s2` | Static | "24,650 (-0.8%)" |
| Local ATR Upper Band (+1σ) | LOCAL R1 (+1σ) | Number/INR | Volatility Engine | `levels.local_r1` | Continuous | Calculated band |
| Local ATR Lower Band (-1σ) | LOCAL S1 (-1σ) | Number/INR | Volatility Engine | `levels.local_s1` | Continuous | Calculated band |
| Session High Level | SESSION HIGH | Number/INR | Daily Bar | `ohlc.high` | Real-time | Session high |
| Session Low Level | SESSION LOW | Number/INR | Daily Bar | `ohlc.low` | Real-time | Session low |
| Previous Session Close Level | PREV CLOSE | Number/INR | Daily Bar | `ohlc.prev_close` | Session start | Previous close |
| Intraday Traded Range | RANGE | Points | Mathematical Model | `ohlc.high - ohlc.low` | Real-time | Points |

### Column C: Market Breadth Telemetry
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Advancing Equities Count | ADVANCES | Integer | NSE Breadth Ingest | `market_score.breadth.advances` | 15s stream | 25 |
| Declining Equities Count | DECLINES | Integer | NSE Breadth Ingest | `market_score.breadth.declines` | 15s stream | 25 |
| Unchanged Equities Count | UNCHANGED | Integer | NSE Breadth Ingest | `market_score.breadth.unchanged` | 15s stream | 0 |
| Breadth Coverage Ratio | COVERAGE | String | Breadth Engine | `market_score.breadth.coverage` | Static | "50/50 NIFTY Constituents" |
| Advance/Decline Ratio | A/D RATIO | Float | Breadth Engine | `market_score.breadth.ad_ratio` | 15s stream | 1.00 |
| Advancing Percent | ADVANCING % | Percentage | Mathematical Model | `advances / 50 * 100` | 15s stream | 50.0% |
| Declining Percent | DECLINING % | Percentage | Mathematical Model | `declines / 50 * 100` | 15s stream | 50.0% |
| Breadth Trend Velocity | BREADTH TREND | Enum/Badge | Breadth Engine | `market_score.breadth.trend` | 15s stream | "EXPANDING_BULLISH" |
| NSE 52-Week Highs Count | 52W HIGHS | Integer | NSE Feed Ingest | `market_score.breadth.highs_52w` | Daily EOD | Integer / "UNAVAILABLE" |
| NSE 52-Week Lows Count | 52W LOWS | Integer | NSE Feed Ingest | `market_score.breadth.lows_52w` | Daily EOD | Integer / "UNAVAILABLE" |
| Participation State | PARTICIPATION | Enum | Breadth Engine | `market_score.breadth.participation` | 15s stream | "BROAD_BASED" / "NARROW" |

### Column D: Volatility & Range Consumption
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| India VIX Value | INDIA VIX | Float | Volatility Stream | `macro_intelligence.cross_assets["INDIA_VIX"].price` | 1s stream | 14.20 |
| India VIX Change % | VIX CHANGE % | Percentage | Volatility Stream | `macro_intelligence.cross_assets["INDIA_VIX"].change_pct` | 1s stream | 0.00% |
| Volatility Regime Label | VOLATILITY REGIME | Enum | Volatility Engine | `market_score.volatility_regime` | Continuous | "NORMAL" / "LOW" |
| Average True Range 14 | ATR (14) | Points | Indicator Engine | `metrics.atr14` | Real-time candle close | 142.5 pts |
| Intraday High-Low Range | INTRADAY RANGE | Points | Mathematical Model | `ohlc.high - ohlc.low` | Real-time | Points |
| Day Range Consumed % | RANGE CONSUMED | Percentage / Bar | Mathematical Model | `(high - low) / atr14 * 100` | Real-time | 68% fill |
| ATR as % of Spot Price | ATR % OF SPOT | Percentage | Mathematical Model | `atr14 / spot * 100` | Continuous | 0.58% |

### Column E: Key Telemetry Summary
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Spot Price Baseline | SPOT | Number/INR | Feed Stream | `spot` | 1s | Spot price |
| VIX Value | VIX | Float | Feed Stream | `vix` | 1s | VIX value |
| Breadth Advances / Declines | BREADTH | String | Breadth Engine | `${advances} / ${declines}` | 15s | "25 / 25" |
| Intraday VWAP Value | VWAP | Number/INR | Indicator Engine | `metrics.vwap` | 1s | VWAP value |
| Daily ATR Value | ATR | Points | Indicator Engine | `metrics.atr14` | 1s | ATR points |
| Spot vs EMA 50 | SPOT VS EMA50 | Percentage | Indicator Engine | `(spot - ema50) / ema50 * 100` | 1s | "+0.45%" |
| Spot vs EMA 200 | SPOT VS EMA200 | Percentage | Indicator Engine | `(spot - ema200) / ema200 * 100` | 1s | "+1.80%" |
| FII Cash Net | FII CASH | Currency (Cr) | Institutional Ingest | `macro_intelligence.institutional_flows.fii_net` | Daily EOD | "₹-850.0 Cr" |
| DII Cash Net | DII CASH | Currency (Cr) | Institutional Ingest | `macro_intelligence.institutional_flows.dii_net` | Daily EOD | "₹+1,240.0 Cr" |
| Institutional Net Combined | COMBINED NET | Currency (Cr) | Institutional Ingest | `macro_intelligence.institutional_flows.combined_net` | Daily EOD | "₹+390.0 Cr" |

---

## 3. ROW 3: SECTOR PARTICIPATION, INSTITUTIONAL POSITIONING & INTERPRETATION

### Column A: Sector Participation Matrix (10 Sectors Table)
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Sector Name (10 Sectors) | SECTOR | String | Sector Pipeline | `niftyContext.sectors[].name` | 15s stream | 10 NSE Sectors |
| Sector Change % | CHG % | Percentage | Sector Pipeline | `niftyContext.sectors[].change_pct` | 15s stream | 0.00% |
| Sector Advances / Declines | ADV / DEC | Tuple (Int) | Sector Pipeline | `niftyContext.sectors[].advances`, `declines` | 15s stream | Int counts |
| Sector Mini Breadth Bar | Breadth Bar | Graphic | Mathematical Model | `advances / total` | 15s stream | Visual bar |
| Sector Trend Direction | TREND | Enum/Arrow | Sector Pipeline | `niftyContext.sectors[].trend` | 15s stream | "BULLISH" / "BEARISH" |
| Positive Sectors Count | POSITIVE SECTORS | Integer | Sector Pipeline | `sectors.filter(s => s.change_pct > 0).length` | 15s stream | Count (e.g. 7) |
| Negative Sectors Count | NEGATIVE SECTORS | Integer | Sector Pipeline | `sectors.filter(s => s.change_pct < 0).length` | 15s stream | Count (e.g. 3) |
| Flat Sectors Count | FLAT SECTORS | Integer | Sector Pipeline | `sectors.filter(s => s.change_pct === 0).length` | 15s stream | Count (e.g. 0) |
| Strongest Outperforming Sector | STRONGEST SECTOR | String & % | Sector Pipeline | `sectors.maxBy(change_pct)` | 15s stream | "NIFTY METAL (+2.4%)" |
| Weakest Underperforming Sector | WEAKEST SECTOR | String & % | Sector Pipeline | `sectors.minBy(change_pct)` | 15s stream | "NIFTY IT (-1.1%)" |

### Column B: Institutional Positioning & Cash Flows
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| FII Cash Net Flow | FII CASH NET | Currency (Cr) | Institutional Ingest | `macro_intelligence.institutional_flows.fii_net` | Daily EOD | "₹-850.0 Cr" |
| FII Institutional Stance | FII STANCE | Enum/Badge | Institutional Model | `macro_intelligence.institutional_flows.fii_stance` | Daily EOD | "NET_SELLERS" |
| DII Cash Net Flow | DII CASH NET | Currency (Cr) | Institutional Ingest | `macro_intelligence.institutional_flows.dii_net` | Daily EOD | "₹+1,240.0 Cr" |
| DII Institutional Stance | DII STANCE | Enum/Badge | Institutional Model | `macro_intelligence.institutional_flows.dii_stance` | Daily EOD | "NET_BUYERS" |
| Combined Institutional Flow | COMBINED NET | Currency (Cr) | Institutional Ingest | `macro_intelligence.institutional_flows.combined_net` | Daily EOD | "₹+390.0 Cr" |
| Combined Market Stance | COMBINED STANCE | Enum/Badge | Institutional Model | `macro_intelligence.institutional_flows.combined_stance` | Daily EOD | "ACCUMULATION" |
| Net Balance Spectrum Slider | Flow Balance Slider | Graphic | Mathematical Model | `dii_net / (abs(fii_net) + dii_net)` | Daily EOD | Visual slider |
| Institutional Raw State Row | 6 State Pills | Enum Array | Institutional Model | `macro_intelligence.institutional_flows.states` | Daily EOD | 6 status pills |
| Flow Source & Reference Date | Source & Date Stamp | String | Institutional Pipeline | `macro_intelligence.institutional_flows.trade_date` | Daily EOD | "NSE Provisional · DD-MM-YYYY" |

### Column C: Metric Interpretation & Synthesis
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Raw State Grid: Trend | TREND | Enum/Pill | Synthesis Engine | `interpretation.trend_state` | Continuous | "BULLISH" |
| Raw State Grid: Momentum | MOMENTUM | Enum/Pill | Synthesis Engine | `interpretation.momentum_state` | Continuous | "STRONG_POSITIVE" |
| Raw State Grid: Breadth | BREADTH | Enum/Pill | Synthesis Engine | `interpretation.breadth_state` | Continuous | "EXPANDING" |
| Raw State Grid: Volatility | VOLATILITY | Enum/Pill | Synthesis Engine | `interpretation.volatility_state` | Continuous | "CONTAINED" |
| Raw State Grid: Institutional | INSTITUTIONAL | Enum/Pill | Synthesis Engine | `interpretation.institutional_state` | Continuous | "NET_BUYING" |
| Raw State Grid: Overall | OVERALL | Enum/Pill | Synthesis Engine | `interpretation.overall_state` | Continuous | "FAVORABLE_LONGS" |
| Structured Summary: Market State | MARKET STATE | String | Synthesis Engine | `interpretation.sections.market_state` | Continuous | Deterministic prose |
| Structured Summary: Participation | PARTICIPATION | String | Synthesis Engine | `interpretation.sections.participation` | Continuous | Deterministic prose |
| Structured Summary: Positioning | POSITIONING | String | Synthesis Engine | `interpretation.sections.positioning` | Continuous | Deterministic prose |
| Structured Summary: Risk & Bounds | RISK & BOUNDS | String | Synthesis Engine | `interpretation.sections.risk_bounds` | Continuous | Deterministic prose |
| Key Alignment: Breadth Alignment | Breadth Alignment | Enum/Badge | Alignment Engine | `interpretation.alignment.breadth` | Continuous | "ALIGNED_POSITIVE" |
| Key Alignment: Flow Alignment | Flow Alignment | Enum/Badge | Alignment Engine | `interpretation.alignment.flows` | Continuous | "ALIGNED_ACCUMULATION" |
| Key Alignment: Momentum Alignment | Momentum Alignment | Enum/Badge | Alignment Engine | `interpretation.alignment.momentum` | Continuous | "CONFIRMED" |

---

## 4. FOOTER METADATA STRIP

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Market Session Status | SESSION STATUS | Enum | Session Clock | `market_session.status` | Real-time | "OPEN" / "CLOSED" |
| Market Telemetry Date | DATE | Date String | Session Clock | `market_session.date` | Real-time | "DD MMM YYYY" |
| Institutional Flow Trade Date | INST. DATA DATE | Date String | Institutional Pipeline | `macro_intelligence.institutional_flows.trade_date` | Daily EOD | "DD MMM YYYY" |
| Data Provider Attribution | SOURCES | String | System Config | Static attribution | Static | "NSE Live Feed · Zerodha · Macro DB" |
