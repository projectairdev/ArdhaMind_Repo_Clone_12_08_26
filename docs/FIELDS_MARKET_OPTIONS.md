# AIR Ardha Staging — Market: Options Data-Field Inventory

**Surface:** `Market Workspace` → `Options Workspace` (`OptionsWorkspace.tsx`, `OptionChainLadder.tsx`, `OpenInterestHeatmap.tsx`)  
**Environment:** Staging (`staging.ardhamind.projectair.in`)  
**Audit Date:** August 2026  
**Scope:** Complete visible data fields across Derivatives State Strip, Positioning Map, Smart Option Chain (Table, Heatmap, OI Change views), Options Inspector (Greeks & Strike Breakdown), and Strike Structure Summary.

---

## 1. DERIVATIVES STATE STRIP (TOP 11-CELL GRID)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Selected Expiry Date | EXPIRY | Date String | Option Chain Matrix | `option_intelligence.expiry_date` | On expiry select | Nearest weekly expiry |
| Expiry Countdown Label | DTE BADGE | String/Badge | Mathematical Model | Calculated days to expiry | Real-time | "Expires Today" / "3 Days" |
| NIFTY Spot Price Baseline | SPOT | Number/INR | Feed Stream | `ticks["NIFTY 50"].last_price` / `spot` | 1s stream | Last valid tick |
| Spot Delta Points | SPOT DELTA | Points & % | Feed Stream | `ticks["NIFTY 50"].change` | 1s stream | "+45.2 pts (+0.18%)" |
| At-The-Money (ATM) Strike | ATM STRIKE | Number/INR | Option Matrix | `option_intelligence.atm_strike` | Real-time | Nearest 50 strike |
| Put-Call Ratio (OI) | PCR (OI) | Float | Option Matrix | `option_intelligence.put_call_ratio` | 5s stream | "0.94" |
| PCR Sentiment Bias | PCR BIAS | Enum/Badge | Derivatives Model | `option_intelligence.pcr_sentiment` | 5s stream | "BULLISH_BIAS" / "NEUTRAL" |
| Put-Call Ratio (Volume) | PCR (VOL) | Float | Option Matrix | `option_intelligence.pcr_volume` | 5s stream | "1.08" / "UNAVAILABLE" |
| Max Pain Strike Pin | MAX PAIN | Number/INR | Option Matrix | `option_intelligence.max_pain` | 5s stream | "24,800" |
| ATM Implied Volatility | ATM IV | Percentage | Black-Scholes Engine | `option_intelligence.atm_iv` | 5s stream | "13.45%" |
| IV Regime Classification | IV REGIME | Enum/Badge | Volatility Model | `option_intelligence.iv_regime` | 5s stream | "LOW_VOLATILITY" / "EXPANDING" |
| Total Call Open Interest (Cr) | TOTAL CALL OI | Float & % | Option Matrix | `option_intelligence.total_ce_oi` | 5s stream | "4.82 Cr (52%)" |
| Total Put Open Interest (Cr) | TOTAL PUT OI | Float & % | Option Matrix | `option_intelligence.total_pe_oi` | 5s stream | "4.45 Cr (48%)" |
| OI Skew Stance | OI SKEW | String | Derivatives Model | `option_intelligence.oi_skew` | 5s stream | "CALL_HEAVY" / "BALANCED" |
| Derivatives Bias Verdict | DERIVATIVES BIAS | Enum/Badge | Derivatives Model | `option_intelligence.derivatives_bias` | 5s stream | "MILDLY_BEARISH" / "NEUTRAL" |

---

## 2. POSITIONING MAP (LEFT COLUMN)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Expiry Dropdown Selector | EXPIRY SELECTOR | Dropdown | Option Ingest | `option_intelligence.available_expiries[]` | Session load | Weekly expiries list |
| Call Total OI Value (Cr) | CALL OI (CR) | Float (Cr) | Option Matrix | `option_intelligence.total_ce_oi` | 5s stream | "4.82 Cr" |
| Put Total OI Value (Cr) | PUT OI (CR) | Float (Cr) | Option Matrix | `option_intelligence.total_pe_oi` | 5s stream | "4.45 Cr" |
| Combined Total OI (Cr) | COMBINED OI | Float (Cr) | Option Matrix | `total_ce_oi + total_pe_oi` | 5s stream | "9.27 Cr" |
| Call/Put Open Interest Bar | CE / PE Ratio Bar | Visual Slider | Mathematical Model | `total_ce_oi / (total_ce_oi + total_pe_oi)` | 5s stream | Segmented percentage bar |
| Major Call Resistance Wall | CALL WALL | Number/INR | Option Matrix | `option_intelligence.call_wall` | 5s stream | "25,000" |
| Major Put Support Wall | PUT WALL | Number/INR | Option Matrix | `option_intelligence.put_wall` | 5s stream | "24,500" |
| Max Pain Strike Level | MAX PAIN PIN | Number/INR | Option Matrix | `option_intelligence.max_pain` | 5s stream | "24,800" |
| Distance: Spot to Call Wall | SPOT → CALL WALL | Points & % | Mathematical Model | `call_wall - spot` | 1s stream | "+180 pts (+0.73%)" |
| Distance: Spot to Put Wall | SPOT → PUT WALL | Points & % | Mathematical Model | `spot - put_wall` | 1s stream | "-320 pts (-1.29%)" |
| Distance: Spot to Max Pain | SPOT → MAX PAIN | Points & % | Mathematical Model | `spot - max_pain` | 1s stream | "-20 pts (-0.08%)" |
| Defined Range Bracket | RANGE BRACKET | Points Bracket | Option Matrix | `${put_wall} - ${call_wall}` | 5s stream | "24,500 - 25,000 (500 pts)" |

---

## 3. SMART OPTION CHAIN LADDER (CENTER COLUMN)

### Controls & View Modifiers
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Chain View Mode Selector | TABLE / OI HEATMAP / OI CHANGE | Button Group | Frontend State | `viewMode` | User click | "TABLE" default |
| Strike Ordering Toggle | ASC / DESC (↑ / ↓) | Button Toggle | Frontend State | `strikeSortAsc` | User click | Ascending default |
| ATM Focus Center Button | RE-CENTER ATM | Button Trigger | Frontend State | `scrollToAtm()` | User click | Smooth scrolls ladder |

### Column-by-Column Ladder Grid (11 Columns)
| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Call Total OI (Lakhs) | CALL OI (L) | Float (Lakhs) | Option Matrix | `option_intelligence.chain[].ce_oi` | 5s stream | "124.5 L" |
| Call OI Bar / Heatmap Cell | CE OI Heatmap | Visual Bar / Color | Mathematical Model | `ce_oi / max_ce_oi` | 5s stream | Green intensity gradient |
| Call Net OI Change (Lakhs) | CE ΔOI (L) | Float (Lakhs) | Option Matrix | `option_intelligence.chain[].ce_oi_change` | 5s stream | "+14.2 L" / "-5.1 L" |
| Call Last Traded Price (LTP) | CE LTP | Number/INR | Feed Stream | `option_intelligence.chain[].ce_ltp` | 1s stream | "₹142.50" |
| Call Price Change % | CE CHG % | Percentage | Feed Stream | `option_intelligence.chain[].ce_change_pct` | 1s stream | "+12.4%" / "-8.2%" |
| Call Implied Volatility | CE IV | Percentage | Black-Scholes Engine | `option_intelligence.chain[].ce_iv` | 5s stream | "13.8%" |
| Call Build-up Label | CE BUILDUP | Enum/Pill | Derivatives Model | `option_intelligence.chain[].ce_buildup` | 5s stream | "LONG_BUILDUP" / "SHORT_COVERING" |
| Strike Price Hero | STRIKE | Number/INR | Option Matrix | `option_intelligence.chain[].strike` | Static Grid | "24,800" (Bold) |
| Strike Badges (ATM, Walls) | BADGES | Badges Array | Option Matrix | Badges: `ATM`, `CALL WALL`, `PUT WALL`, `MAX PAIN` | Real-time | Visual color badges |
| Put Build-up Label | PE BUILDUP | Enum/Pill | Derivatives Model | `option_intelligence.chain[].pe_buildup` | 5s stream | "SHORT_BUILDUP" / "LONG_UNWINDING" |
| Put Implied Volatility | PE IV | Percentage | Black-Scholes Engine | `option_intelligence.chain[].pe_iv` | 5s stream | "14.2%" |
| Put Price Change % | PE CHG % | Percentage | Feed Stream | `option_intelligence.chain[].pe_change_pct` | 1s stream | "-15.2%" / "+6.8%" |
| Put Last Traded Price (LTP) | PE LTP | Number/INR | Feed Stream | `option_intelligence.chain[].pe_ltp` | 1s stream | "₹98.20" |
| Put Net OI Change (Lakhs) | PE ΔOI (L) | Float (Lakhs) | Option Matrix | `option_intelligence.chain[].pe_oi_change` | 5s stream | "+28.4 L" / "-2.0 L" |
| Put Total OI (Lakhs) | PUT OI (L) | Float (Lakhs) | Option Matrix | `option_intelligence.chain[].pe_oi` | 5s stream | "158.0 L" |
| Put OI Bar / Heatmap Cell | PE OI Heatmap | Visual Bar / Color | Mathematical Model | `pe_oi / max_pe_oi` | 5s stream | Red/Orange intensity gradient |

---

## 4. OPTIONS INSPECTOR (RIGHT COLUMN)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Volatility Structure: ATM IV | ATM IV | Percentage | Black-Scholes Engine | `option_intelligence.atm_iv` | 5s stream | "13.45%" |
| Volatility Structure: IV Percentile | IV PERCENTILE | Percentage | Historical DB | `option_intelligence.iv_percentile` | Daily recomputation | "32%" / "UNAVAILABLE" |
| Volatility Structure: RBI Base Rate | RBI BASE RATE | Percentage | Macro Reference | `macro_intelligence.rbi_repo_rate` | Macro config | "6.50%" |
| Selected Strike Hero | SELECTED STRIKE | Number/INR | User Selection | `selectedStrike` (defaults to ATM) | User click | Strike price (e.g. 24,800) |
| Strike Focus Badge | STRIKE BADGE | Badge | Selection Resolver | Selected strike role | User click | "ATM ANCHOR" / "OUT OF THE MONEY" |
| Selected Strike Distance from Spot | DISTANCE FROM SPOT | Points & % | Mathematical Model | `selectedStrike - spot` | 1s stream | "+50 pts (+0.20%)" |
| Selected Call (CE) LTP | CE LTP | Number/INR | Feed Stream | `selectedChainRow.ce_ltp` | 1s stream | "₹142.50" |
| Selected Call (CE) Total OI | CE TOTAL OI | Float (Lakhs) | Option Matrix | `selectedChainRow.ce_oi` | 5s stream | "124.5 L" |
| Selected Call (CE) Net OI Change | CE ΔOI | Float (Lakhs) | Option Matrix | `selectedChainRow.ce_oi_change` | 5s stream | "+14.2 L" |
| Selected Call (CE) IV | CE IV | Percentage | Black-Scholes Engine | `selectedChainRow.ce_iv` | 5s stream | "13.8%" |
| Selected Put (PE) LTP | PE LTP | Number/INR | Feed Stream | `selectedChainRow.pe_ltp` | 1s stream | "₹98.20" |
| Selected Put (PE) Total OI | PE TOTAL OI | Float (Lakhs) | Option Matrix | `selectedChainRow.pe_oi` | 5s stream | "158.0 L" |
| Selected Put (PE) Net OI Change | PE ΔOI | Float (Lakhs) | Option Matrix | `selectedChainRow.pe_oi_change` | 5s stream | "+28.4 L" |
| Selected Put (PE) IV | PE IV | Percentage | Black-Scholes Engine | `selectedChainRow.pe_iv` | 5s stream | "14.2%" |
| Black-Scholes Greeks: Delta | DELTA (Δ) | Float | Black-Scholes Engine | `selectedChainRow.greeks.delta` | Recomputation | Explicit "UNAVAILABLE" if missing |
| Black-Scholes Greeks: Gamma | GAMMA (Γ) | Float | Black-Scholes Engine | `selectedChainRow.greeks.gamma` | Recomputation | Explicit "UNAVAILABLE" if missing |
| Black-Scholes Greeks: Theta | THETA (Θ) | Float | Black-Scholes Engine | `selectedChainRow.greeks.theta` | Recomputation | Explicit "UNAVAILABLE" if missing |
| Black-Scholes Greeks: Vega | VEGA (ν) | Float | Black-Scholes Engine | `selectedChainRow.greeks.vega` | Recomputation | Explicit "UNAVAILABLE" if missing |

---

## 5. BOTTOM GRID: WHAT CHANGED & STRIKE STRUCTURE SUMMARY

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Derivatives What Changed (Bulleted) | WHAT CHANGED (OI EVIDENCE) | Array<String> | Derivatives Model | `option_intelligence.evidence_bullet_points` | Continuous | "Baseline OI structure established" |
| Strike Structure: Put Support Strike | PUT SUPPORT ANCHOR | Strike & Pts | Option Matrix | `${put_wall} (${spot - put_wall} pts)` | 5s stream | "24,500 PE (-320 pts)" |
| Strike Structure: Spot / Max Pain Node | SPOT / MAX PAIN ANCHOR | Spot & Pain | Option Matrix | `Spot: ${spot} · Max Pain: ${max_pain}` | 1s stream | "Spot: 24,820 · Pain: 24,800" |
| Strike Structure: Call Resistance Strike | CALL RESISTANCE ANCHOR | Strike & Pts | Option Matrix | `${call_wall} (${call_wall - spot} pts)` | 5s stream | "25,000 CE (+180 pts)" |
| Summary Strip: PCR Value | PCR (OI) | Float | Option Matrix | `option_intelligence.put_call_ratio` | 5s stream | "0.94" |
| Summary Strip: OI Skew Stance | OI SKEW | String | Derivatives Model | `option_intelligence.oi_skew` | 5s stream | "CALL_HEAVY" |
| Summary Strip: Bias Verdict | BIAS | Enum/Badge | Derivatives Model | `option_intelligence.derivatives_bias` | 5s stream | "MILDLY_BEARISH" |
| Summary Strip: Range Range | ACTIVE RANGE | String | Mathematical Model | `${put_wall} - ${call_wall}` | 5s stream | "24,500 - 25,000" |
