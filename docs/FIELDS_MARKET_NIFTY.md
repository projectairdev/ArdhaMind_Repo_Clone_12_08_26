# AIR Ardha Staging — Market: NIFTY Data-Field Inventory

**Surface:** `Market Workspace` → `NIFTY Workspace` (`NiftyLiveWorkspace.tsx`)  
**Environment:** Staging (`staging.ardhamind.projectair.in`)  
**Audit Date:** August 2026  
**Scope:** Complete visible data fields across Pre-Market (PRE), Live Session (LIVE), Post-Market (POST), and Side Drawer panels.

---

## 1. PRE-MARKET VIEW (`PreMarketDashboard`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Opening Bias | OPENING BIAS | Enum/Badge | Deterministic Resolver | `pre_market_briefing.opening_bias` / `niftyContext.bias` | On session load / snapshot | "NEUTRAL" |
| Expected Gap Points | EXPECTED GAP | String/Points | Pre-Market Engine | `pre_market_briefing.expected_gap_str` | Snapshot calculation | "Flat (0 pts)" |
| Expected Open Price | EXPECTED OPEN | Number/INR | Pre-Market Engine | `pre_market_briefing.expected_open_str` | Snapshot calculation | "₹24,850.00" / last close |
| Reference Close | REF CLOSE | Number/INR | Historical Market Feed | `pre_market_briefing.reference_close` | Session baseline | Previous session close |
| Overall Confidence Score | CONFIDENCE | Percentage | Scoring Engine | `pre_market_briefing.confidence_score` | Pre-market calculation | "78%" / "UNAVAILABLE" |
| Risk Summary | RISK LEVEL | Enum/Badge | Risk Model | `pre_market_briefing.risk_summary` | Pre-market calculation | "MODERATE" |
| Cross-Asset Price (10 assets) | Asset Price (GIFT, SPX, etc.) | Number | Macro Provider | `macro_intelligence.cross_assets[].price` | 10s polling | Last valid price |
| Cross-Asset Change % | Change % | Percentage | Macro Provider | `macro_intelligence.cross_assets[].change_pct` | 10s polling | 0.00% |
| Cross-Asset Sparkline | Trend | Array<Number> | Macro Provider | `macro_intelligence.cross_assets[].sparkline` | Static mini-array | Flat horizontal line |
| Market Availability Status | Market Status | Enum | Session Clock | `macro_intelligence.market_hours[city]` | 60s check | "OPEN" / "CLOSED" |
| Support Level 1 | S1 | Number | Pivot Engine | `niftyContext.levels.s1` | Static calculation | "24,750" |
| Support Level 2 | S2 | Number | Pivot Engine | `niftyContext.levels.s2` | Static calculation | "24,680" |
| Pivot Decision Level | PIVOT | Number | Pivot Engine | `niftyContext.levels.pivot` | Static calculation | "24,820" |
| Resistance Level 1 | R1 | Number | Pivot Engine | `niftyContext.levels.r1` | Static calculation | "24,900" |
| Resistance Level 2 | R2 | Number | Pivot Engine | `niftyContext.levels.r2` | Static calculation | "24,980" |
| FII Cash Net Flow | FII NET FLOW | Currency (Cr) | Institutional Pipeline | `macro_intelligence.institutional_flows.fii_net` | Daily EOD update | "₹-850.0 Cr" / "--" |
| DII Cash Net Flow | DII NET FLOW | Currency (Cr) | Institutional Pipeline | `macro_intelligence.institutional_flows.dii_net` | Daily EOD update | "₹+1,240.0 Cr" / "--" |
| Combined Net Flow | COMBINED NET | Currency (Cr) | Institutional Pipeline | `macro_intelligence.institutional_flows.combined_net` | Daily EOD update | "₹+390.0 Cr" / "--" |
| Institutional Stance | STANCE | String/Enum | Institutional Pipeline | `macro_intelligence.institutional_flows.stance` | Daily EOD update | "NET BUYERS" / "NEUTRAL" |
| Ranked Catalysts (Top 5) | Catalyst Headline | String | News Engine | `news_intelligence.top_catalysts[].headline` | Real-time news ingest | "No active catalysts" |
| Catalyst Impact Badge | Impact | Enum | News Engine | `news_intelligence.top_catalysts[].impact` | Real-time news ingest | "HIGH" / "MEDIUM" |
| Catalyst Sentiment | Direction | Enum | News Engine | `news_intelligence.top_catalysts[].sentiment` | Real-time news ingest | "POSITIVE" / "NEGATIVE" |
| Scheduled Macro Events | Event Time & Name | String | Macro Calendar | `macro_intelligence.calendar_events[]` | Daily schedule | "No scheduled events" |
| Primary Scenario Thesis | PRIMARY SCENARIO | String/Markdown | Briefing Generator | `pre_market_briefing.scenarios.primary` | Pre-market generation | Text narrative |
| Invalidation Condition | INVALIDATION | String | Briefing Generator | `pre_market_briefing.invalidation` | Pre-market generation | Explicit level condition |

---

## 2. LIVE VIEW (`LiveDashboard`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| NIFTY 50 Spot Price Hero | SPOT | Number/INR | Kite Ticker / Feed Bridge | `ticks["NIFTY 50"].last_price` / `niftyContext.spot` | 1s real-time stream | Last valid tick |
| Absolute Change Points | CHANGE | Number/Points | Market Feed Bridge | `ticks["NIFTY 50"].change` | 1s real-time stream | 0.00 pts |
| Percentage Change | CHANGE PCT | Percentage | Market Feed Bridge | `ticks["NIFTY 50"].change_pct` | 1s real-time stream | 0.00% |
| Market Trend Classification | TREND | Enum/Badge | Deterministic Model | `niftyContext.trend` | Continuous recomputation | "BULLISH" / "SIDEWAYS" |
| Session Open Price | OPEN | Number/INR | Kite Feed / Daily Bar | `niftyContext.ohlc.open` | Session start | First valid tick |
| Session High Price | HIGH | Number/INR | Kite Feed / Daily Bar | `niftyContext.ohlc.high` | Real-time high-water mark | Spot price |
| Session Low Price | LOW | Number/INR | Kite Feed / Daily Bar | `niftyContext.ohlc.low` | Real-time low-water mark | Spot price |
| Previous Session Close | PREV CLOSE | Number/INR | Historical Database | `niftyContext.ohlc.prev_close` | Session start | Last verified EOD close |
| Market Breadth Advances | ADVANCES | Integer | NSE Breadth Ingest | `market_score.breadth.advances` | 15s polling / tick update | 25 |
| Market Breadth Declines | DECLINES | Integer | NSE Breadth Ingest | `market_score.breadth.declines` | 15s polling / tick update | 25 |
| Advance/Decline Ratio | A/D RATIO | Float | Deterministic Model | `market_score.breadth.ad_ratio` | 15s polling / tick update | "1.00" |
| India VIX Value | INDIA VIX | Number | Kite Feed / Volatility Ingest | `macro_intelligence.cross_assets["INDIA_VIX"].price` | 1s stream | 14.20 |
| India VIX Change % | VIX CHANGE % | Percentage | Market Feed Bridge | `macro_intelligence.cross_assets["INDIA_VIX"].change_pct` | 1s stream | 0.00% |
| Candlestick Timeframe Selector | 1m / 5m / 15m / 1H / 1D | Interactive Toggle | Frontend State | `selectedTimeframe` | Instant | "5m" default |
| Interactive Candlestick Chart | Candles (O, H, L, C, V) | OHLCV Array | Historical DB & Feed | `niftyContext.intraday_candles` | 1s stream bar update | Last 75 candles |
| Top Gainers List (Top 5) | Symbol, LTP, Chg % | Array<Object> | Breadth Pipeline | `niftyContext.movers.gainers` | 15s update | Top 5 NSE equities |
| Top Losers List (Top 5) | Symbol, LTP, Chg % | Array<Object> | Breadth Pipeline | `niftyContext.movers.losers` | 15s update | Top 5 NSE equities |
| Sector Heatmap Summary | Sector Name, Chg % | Array<Object> | Sector Ingest Pipeline | `niftyContext.sectors` | 15s update | 5 key sectors |
| Intraday Day Range Bar | Range Slider | UI Graphic | Mathematical Model | `(spot - low) / (high - low)` | Real-time | Percentage fill |
| Key Resistance 2 | R2 | Number | Pivot Engine | `niftyContext.levels.r2` | Static | Calculated level |
| Key Resistance 1 | R1 | Number | Pivot Engine | `niftyContext.levels.r1` | Static | Calculated level |
| Central Pivot Point | PIVOT | Number | Pivot Engine | `niftyContext.levels.pivot` | Static | Calculated level |
| Key Support 1 | S1 | Number | Pivot Engine | `niftyContext.levels.s1` | Static | Calculated level |
| Key Support 2 | S2 | Number | Pivot Engine | `niftyContext.levels.s2` | Static | Calculated level |
| Key Support 3 | S3 | Number | Pivot Engine | `niftyContext.levels.s3` | Static | Calculated level |
| Options PCR Snapshot | PCR (OI) | Float | Option Chain Ingest | `option_intelligence.put_call_ratio` | 5s stream | 0.95 |
| Options Max Pain Strike | MAX PAIN | Number | Option Chain Matrix | `option_intelligence.max_pain` | 5s stream | Strike price |
| Options ATM Strike | ATM STRIKE | Number | Option Chain Matrix | `option_intelligence.atm_strike` | Real-time rounding | Nearest 50 strike |
| Options ATM IV | ATM IV | Percentage | Black-Scholes Engine | `option_intelligence.atm_iv` | 5s recalculation | 13.8% |
| Volatility Gauge Regime | VOLATILITY REGIME | Enum/Badge | Volatility Model | `market_score.volatility_regime` | Continuous | "NORMAL" / "LOW" |
| Sector Adv/Dec Donut | Advancing / Neutral / Declining | Donut Segments | Breadth Engine | `market_score.breadth` | 15s update | Multi-segment arc |

---

## 3. POST-MARKET VIEW (`PostMarketDashboard`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Completed Session Date | SESSION COMPLETED | Date String | Session Clock | `post_market_briefing.session_date` | Session close | Today's date |
| Final Official Close | FINAL CLOSE | Number/INR | NSE EOD Feed | `post_market_briefing.final_close` | 15:35 IST | Last traded spot |
| Session Total Change | TOTAL CHANGE | Points & % | EOD Feed | `post_market_briefing.change_points_pct` | 15:35 IST | Calculated from open |
| Session High | HIGH | Number/INR | EOD Feed | `post_market_briefing.day_high` | 15:35 IST | Session high |
| Session Low | LOW | Number/INR | EOD Feed | `post_market_briefing.day_low` | 15:35 IST | Session low |
| Total Traded Range | RANGE | Points | EOD Feed | `post_market_briefing.day_range` | 15:35 IST | High - Low pts |
| EOD Market Trend | TREND | Enum/Badge | Deterministic Model | `post_market_briefing.trend` | 15:35 IST | "TRENDING_BULLISH" |
| EOD Advance Count | ADVANCES | Integer | NSE EOD Breadth | `post_market_briefing.breadth.advances` | 15:35 IST | NIFTY 50 count |
| EOD Decline Count | DECLINES | Integer | NSE EOD Breadth | `post_market_briefing.breadth.declines` | 15:35 IST | NIFTY 50 count |
| EOD Unchanged Count | UNCHANGED | Integer | NSE EOD Breadth | `post_market_briefing.breadth.unchanged` | 15:35 IST | NIFTY 50 count |
| Day Character Badge | DAY CHARACTER | Enum | Daily Profiler | `post_market_briefing.day_character` | EOD generation | "TREND_DAY" / "RANGE" |
| Breadth State Badge | BREADTH STATE | Enum | Daily Profiler | `post_market_briefing.breadth_state` | EOD generation | "EXPANDING" |
| Close Location Badge | CLOSE LOCATION | Enum | Daily Profiler | `post_market_briefing.close_location` | EOD generation | "TOP_QUARTILE" |
| Institutional Stance Badge | INST. STANCE | Enum | Daily Profiler | `post_market_briefing.institutional_stance` | EOD generation | "NET_ACCUMULATION" |
| Completed 15m Chart | Full Session Candles | Array<OHLC> | DB Historical Store | `post_market_briefing.candles_15m` | Static on completion | 25 session bars |
| NSE 52-Week Highs | 52W HIGHS | Integer | NSE Breadth Ingest | `market_score.breadth.highs_52w` | Daily EOD | Integer count / "UNAVAILABLE" |
| NSE 52-Week Lows | 52W LOWS | Integer | NSE Breadth Ingest | `market_score.breadth.lows_52w` | Daily EOD | Integer count / "UNAVAILABLE" |
| EOD PCR | PCR (OI) | Float | Option Chain Matrix | `post_market_briefing.options.pcr` | 15:30 IST | Final session PCR |
| EOD Max Pain | MAX PAIN | Number | Option Chain Matrix | `post_market_briefing.options.max_pain` | 15:30 IST | Final session Max Pain |
| EOD ATM IV | ATM IV | Percentage | Option Chain Matrix | `post_market_briefing.options.atm_iv` | 15:30 IST | Final session IV |
| EOD FII Net Flow | FII NET | Currency (Cr) | Institutional Pipeline | `macro_intelligence.institutional_flows.fii_net` | 18:30 IST | Final FII Net |
| EOD DII Net Flow | DII NET | Currency (Cr) | Institutional Pipeline | `macro_intelligence.institutional_flows.dii_net` | 18:30 IST | Final DII Net |
| EOD Combined Net Flow | COMBINED NET | Currency (Cr) | Institutional Pipeline | `macro_intelligence.institutional_flows.combined_net` | 18:30 IST | Final Combined Net |
| Sector Leadership Ranking (Top 5) | Rank, Sector, Chg % | Array<Object> | Sector Pipeline | `post_market_briefing.sector_rankings` | 15:35 IST | 5 sector ranks |
| Session Drivers (Positives) | POSITIVE DRIVERS | Array<String> | Synthesis Engine | `post_market_briefing.positives` | EOD generation | Bullet points |
| Session Drivers (Negatives) | NEGATIVE DRIVERS | Array<String> | Synthesis Engine | `post_market_briefing.negatives` | EOD generation | Bullet points |
| Session Key Takeaway | KEY TAKEAWAY | String/Markdown | Synthesis Engine | `post_market_briefing.key_takeaway` | EOD generation | Synthesis summary |
| Session News Timeline | Time, Headline, Impact | Array<Object> | News Engine | `post_market_briefing.timeline_news` | EOD generation | Session news log |

---

## 4. MOVERS & SECTORS SLIDE-OVER DRAWER (`MoversSectorsDrawer`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Drawer Mode Active Tab | GAINERS / LOSERS / SECTORS | Tab Selector | Frontend State | `activeDrawerTab` | User interaction | "GAINERS" default |
| Full 50 NIFTY Movers List | Rank, Symbol, Last, Chg, Chg % | Array<Object> | Breadth Pipeline | `niftyContext.movers.all_ranked` | 15s stream | Complete sorted list |
| All 10 NSE Sectors Table | Sector Name, LTP, Chg %, Adv/Dec | Array<Object> | Sector Pipeline | `niftyContext.sectors.all` | 15s stream | 10 NSE sectors |
