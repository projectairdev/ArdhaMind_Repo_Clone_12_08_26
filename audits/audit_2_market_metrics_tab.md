# Metrics Tab — Full E2E Forensic Audit

### 1. Summary

A comprehensive, read-only forensic audit was conducted across the **Market → Metrics** tab (`MarketPulseWorkspace.tsx`), covering all 5 architectural tiers, 10 institutional metric cards, and the underlying data ingestion pipelines (Kite real-time WebSocket ticks, Kite market context snapshots, Yahoo Finance cross-asset macro ingestion, and NSE EOD cash flow feeds). While the tab successfully maintains read-only execution invariants and isolates Kite broker credentials, the investigation revealed **3 Critical**, **6 High**, **6 Medium**, and **5 Low** severity defects. 

Most critically, the workspace engages in extensive mathematical fabrication when backend feeds are unpopulated: it synthesizes 8 heavyweight stock prices and index point contributions via hardcoded formulas, manufactures 8 sector performance indices with artificial beta multipliers, fabricates a "Constituents Above 20 DMA" metric by multiplying the day's advance count by `1.05`, and embeds static dummy values (`-5,039.80 Cr` FII flow, `135.10` ATR, `10.68` VIX, and hardcoded confluence percentages like `74/100` and `85% Bullish`). Additionally, the "Refresh" action on the Global Macro card misleadingly triggers a Kite broker account sync rather than updating global quotes, and an invisible DOM container exists containing dummy strings specifically injected to pass legacy test assertions.

| Severity | Finding Count | Primary Impact Area |
| :--- | :---: | :--- |
| **Critical** | **3** | Fabricated constituent heavyweight matrix, synthetic sector matrix, artificial "Above 20 DMA" formula |
| **High** | **6** | Pseudo-internals in breadth, synthetic EMA/RSI fallbacks, hardcoded confluence metrics, hardcoded FII/ATR/VIX fallbacks, deceptive broker sync on macro refresh, missing observation timestamps |
| **Medium** | **6** | Hidden DOM test-scaffolding residue, dead `liveTickPrice` state hook, zero skeleton loaders, cross-tab discrepancies with NIFTY tab, flat zero rendered as green positive, heuristic VWAP SD bands |
| **Low** | **5** | Decimal precision drift across cards, hardcoded session dates, inverted R:R ratio on breakout, hardcoded dark mode palette, 1-second unmemoized re-render cascade |
| **Total** | **20** | |

---

### Complete Metric Inventory & Data Source Mapping

Before detailing the findings, every metric and data point displayed across the 10 cards of the Metrics tab is enumerated below with its bound source and update frequency:

| # | Card / Section | Displayed Metric | Underlying Source / Field | Ingestion Pipeline | Update Frequency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Card 1: Global & Macro Context** | 11 Benchmark Assets (GIFT Nifty, S&P 500, NASDAQ, DOW, Nikkei, Hang Seng, Brent, Gold, USD/INR, DXY, US 10Y) | `macro_intelligence.quotes[symbol]` (`last_price`, `change_pct`, `candles`) | Yahoo Finance Scraper (`GlobalMarketProvider`) | Periodic (~300s / 5 min) |
| 2 | **Card 2: Market State** | NIFTY 50 Spot Price | `authState.spot` / `envelope.market.nifty.last_price` | Kite WebSocket (Token `256265`) | Real-Time Ticking |
| 3 | **Card 2: Market State** | Point Change & % Change | `authState.change`, `authState.changePct` | Kite WebSocket / Computed | Real-Time Ticking |
| 4 | **Card 2: Market State** | Session OHLC & Range | `price_structure.{open, high, low, range_points}` | Computed from Kite Ticks | Real-Time Ticking |
| 5 | **Card 2: Market State** | Intraday VWAP & Spot vs VWAP Delta | `price_structure.vwap`, computed difference | Computed from Kite Ticks | Real-Time Ticking |
| 6 | **Card 2: Market State** | Opening Gap Points & % | Computed from `openPrice - prevClose` | Computed Aggregate | Static after Open |
| 7 | **Card 2: Market State** | Intraday Range Location % | Computed: `(spot - low) / (high - low) * 100` | Computed Aggregate | Real-Time Ticking |
| 8 | **Card 2: Market State** | ATR Utilization % | Computed: `(intradayRange / atr14) * 100` | Computed Aggregate | Real-Time Ticking |
| 9 | **Card 2: Market State** | 52-Week High/Low & Deltas | `market.year_high`, `market.year_low` | Kite Quote API / Settled Session | Daily / Periodic |
| 10 | **Card 2: Market State** | Statistical VWAP Envelope (±1 SD) | Computed: `vwap ± (intradayRange * 0.34)` | Computed Heuristic | Real-Time Ticking |
| 11 | **Card 2: Market State** | India VIX & Volatility Regime | `authState.vix` / `macro.india_vix` | Kite WebSocket (Token `264969`) | Real-Time Ticking |
| 12 | **Card 3: Quantitative Matrix** | Primary Bias, Trend Strength, Confluence Score | Hardcoded strings and numbers ("BULLISH CONTINUATION", "72 / 100", "74 / 100") | Hardcoded Frontend Literals | Static (Fabricated) |
| 13 | **Card 3: Quantitative Matrix** | Volume Participation (Up/Down Vol Ratio) | Hardcoded strings ("64.2% / 35.8%") | Hardcoded Frontend Literals | Static (Fabricated) |
| 14 | **Card 3: Quantitative Matrix** | Factor Weights (Price Action, Breadth, Options, Flows) | Hardcoded percentages (85%, 70%, 65%, 55%) | Hardcoded Frontend Literals | Static (Fabricated) |
| 15 | **Card 3: Quantitative Matrix** | Execution Targets (R2, R1, Invalidation, R:R) | `price_structure.key_resistances`, `key_supports` | Python Structural Level Engine | Dynamic / Periodic |
| 16 | **Card 4: Heavyweight Impact** | Top 8 Heavyweights (HDFCBANK, RELIANCE, ICICIBANK, INFY, ITC, TCS, LT, BHARTIARTL) | `marketContext.heavyweights` OR **Synthetic Fallback** | Kite Constituent Quotes OR Synthetic | Periodic OR Fake Ticking |
| 17 | **Card 5: Sector Participation** | 8 Sectoral Indices (Bank, Auto, IT, Pharma, Metal, FMCG, Realty, Energy) | `marketContext.sectors` OR **Synthetic Fallback** | Kite Sector Indices OR Synthetic | Periodic OR Fake Ticking |
| 18 | **Card 6: Breadth Internals** | Advances, Declines, Unchanged Count & % | `authState.breadth.{advances, declines, unchanged}` | Computed from 50 Constituent Ticks | Dynamic (~1s - 5s) |
| 19 | **Card 6: Breadth Internals** | Advance / Decline Ratio | `authState.breadth.ratio` | Computed Aggregate | Dynamic (~1s - 5s) |
| 20 | **Card 6: Breadth Internals** | Up Vol vs Down Vol, Above VWAP, Above 20 DMA | Computed from `advPct` and `advCount * 1.05` | Re-used Advance Count / Fabricated | Dynamic (Fabricated) |
| 21 | **Card 7: Institutional Flows** | FII Cash Net, DII Cash Net, Combined Net | `macro.institutional_flows` (FII/DII) | NSE EOD Cash Report (`InstitutionalFlowProvider`) | End-of-Day (1x Daily) |
| 22 | **Card 7: Institutional Flows** | Net Positioning Balance Slider | Computed from `fiiNet + diiNet` | Computed Aggregate | End-of-Day (1x Daily) |
| 23 | **Card 8: Volatility Expansion** | India VIX, Daily ATR 14, Session Range | `authState.vix`, `price_structure.atr_14`, `range_points` | Kite WebSocket / Analytical Engine | Real-Time Ticking |
| 24 | **Card 9: Structural Price Ladder** | Sorted Price Stack (R2, R1, Spot, VWAP, S1, S2) + Deltas | `price_structure`, `settled_session` | Python Structural Level Engine | Dynamic / Real-Time |
| 25 | **Card 10: Technical References** | Daily EMA 20, EMA 50, EMA 200 | `technical.ema_{20, 50, 200}` OR **Synthetic `spot * beta`** | Technical Analysis Service OR Synthetic | Periodic OR Fake Ticking |
| 26 | **Card 10: Technical References** | 14-Period Daily RSI | `technical.rsi_14` OR **Hardcoded `56.4`** | Technical Analysis Service OR Fallback | Periodic OR Static |
| 27 | **Card 10: Technical References** | Session VWAP Deviation (pts & %) | Computed: `spot - vwap` | Computed Aggregate | Real-Time Ticking |

---

### 2. Forensic Findings by Dimension (1–13)

```
================================================================================
DIMENSION 1: METRIC INVENTORY & DATA SOURCE FIDELITY
================================================================================
```

#### Finding 1.1: Synthetic Top 8 Heavyweight Constituent Matrix Generation
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:430-462](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L430-L462)
* **Actual Code:**
  ```tsx
  const heavyweights: any[] = useMemo(() => {
    if (rawHeavyweights.length > 0) return rawHeavyweights;
    if (spot != null && isDataAvailable) {
      const constituentBaseline = [
        { symbol: "HDFCBANK", name: "HDFC Bank", weight: "11.8%", baseLtp: 1640.50, beta: 1.1 },
        { symbol: "RELIANCE", name: "Reliance Ind", weight: "9.2%", baseLtp: 2980.00, beta: 1.0 },
        { symbol: "ICICIBANK", name: "ICICI Bank", weight: "7.9%", baseLtp: 1195.20, beta: 1.2 },
        { symbol: "INFY", name: "Infosys", weight: "5.8%", baseLtp: 1880.00, beta: 0.8 },
        { symbol: "ITC", name: "ITC Ltd", weight: "4.4%", baseLtp: 502.40, beta: 0.6 },
        { symbol: "TCS", name: "TCS", weight: "4.2%", baseLtp: 4460.00, beta: 0.7 },
        { symbol: "LT", name: "Larsen & Toubro", weight: "3.9%", baseLtp: 3680.00, beta: 1.1 },
        { symbol: "BHARTIARTL", name: "Bharti Airtel", weight: "3.7%", baseLtp: 1540.00, beta: 1.3 },
      ];
      const netPct = changePct != null ? changePct : 0.45;
      return constituentBaseline.map((c, i) => {
        const cPct = Number((netPct * c.beta + (i % 2 === 0 ? 0.15 : -0.10)).toFixed(2));
        const cLtp = Number((c.baseLtp * (1 + cPct / 100)).toFixed(2));
        const ptsContrib = Number((cPct * parseFloat(c.weight) * 0.12).toFixed(1));
        const isPos = cPct >= 0;
        return {
          symbol: c.symbol,
          name: c.name,
          weight: c.weight,
          ltp: cLtp,
          changePct: cPct,
          pts: ptsContrib,
          vwapBias: isPos ? "Above VWAP" : "Below VWAP",
          biasClass: isPos ? "text-[#00C896]" : "text-[#EF4444]",
        };
      });
    }
    return [];
  }, [rawHeavyweights, spot, isDataAvailable, changePct]);
  ```
* **Why it is wrong:** When real constituent heavyweight data is unavailable from the backend, the UI synthesizes fake LTPs, fake percentage changes, fake NIFTY point contributions, and fake VWAP biases for HDFC Bank, Reliance, ICICI Bank, Infosys, ITC, TCS, L&T, and Bharti Airtel by applying mathematical multipliers to NIFTY's index percentage change. This generates completely fabricated market data in direct violation of the zero-fabrication invariant.
* **Severity:** **Critical**

#### Finding 1.2: Synthetic Sector Participation Matrix Generation
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:360-387](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L360-L387)
* **Actual Code:**
  ```tsx
  const sectorList = useMemo(() => {
    if (rawSectors.length > 0) return rawSectors;
    if (spot != null && isDataAvailable) {
      const baseSectors = [
        { name: "NIFTY BANK", sector: "BANK", beta: 1.15, adv: 8, dec: 4 },
        { name: "NIFTY AUTO", sector: "AUTO", beta: 1.05, adv: 10, dec: 5 },
        { name: "NIFTY IT", sector: "IT", beta: -0.45, adv: 3, dec: 7 },
        { name: "NIFTY PHARMA", sector: "PHARMA", beta: 0.40, adv: 11, dec: 9 },
        { name: "NIFTY METAL", sector: "METAL", beta: 0.85, adv: 9, dec: 6 },
        { name: "NIFTY FMCG", sector: "FMCG", beta: 0.55, adv: 8, dec: 7 },
        { name: "NIFTY REALTY", sector: "REALTY", beta: 1.35, adv: 7, dec: 3 },
        { name: "NIFTY ENERGY", sector: "ENERGY", beta: 0.70, adv: 6, dec: 4 },
      ];
      const netPct = changePct != null ? changePct : 0.45;
      return baseSectors.map((s) => {
        const chg = Number((netPct * s.beta).toFixed(2));
        return {
          name: s.name,
          sector: s.sector,
          change_pct: chg,
          adv: s.adv,
          dec: s.dec,
          trend: chg > 0.1 ? "Bullish" : chg < -0.1 ? "Bearish" : "Neutral",
        };
      });
    }
    return [];
  }, [rawSectors, spot, isDataAvailable, changePct]);
  ```
* **Why it is wrong:** If backend sector performance is empty, the workspace invents performance data for 8 major sectors, hardcoding static advance/decline ratios (e.g. Bank 8/4, IT 3/7, Auto 10/5) and calculating synthetic sector changes by multiplying index change by a hardcoded beta.
* **Severity:** **Critical**

#### Finding 1.3: Hardcoded Fallback Values for FII/DII Flows, ATR, and India VIX
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:328-330, 340, 396-397](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L328-L397)
* **Actual Code:**
  ```tsx
  // ATR fallback:
  const rawAtr = state.price_structure?.atr_14 ?? envelope.price_structure?.atr_14 ?? marketContext?.atr ?? settled?.atr_14 ?? (envelope.active_product?.tomorrow_plan?.session_summary?.atr) ?? 135.10;
  const atr = rawAtr != null && Number(rawAtr) >= 20 ? Number(rawAtr) : 135.10;
  ...
  // VIX fallback:
  const vixVal = authState.vix ?? (isDataAvailable ? (...) : (settled?.closing_vix ?? 10.68));
  ...
  // FII/DII Cash Flow fallbacks:
  const fiiNet = fiiFlow.net_value != null ? Number(fiiFlow.net_value) : (settled?.institutional_flows?.fii_net ?? -5039.80);
  const diiNet = diiFlow.net_value != null ? Number(diiFlow.net_value) : (settled?.institutional_flows?.dii_net ?? 5183.90);
  ```
* **Why it is wrong:** Missing numerical data must remain `null` so the UI can render an explicit awaiting-data state. Instead, this workspace substitutes specific, plausible-looking market numbers (`-5039.80 Cr`, `5183.90 Cr`, `135.10 pts`, `10.68 pts`).
* **Severity:** **High**

```
================================================================================
DIMENSION 2: REAL-TIME PIPELINE
================================================================================
```

#### Finding 2.1: Misleading "Refresh" Button on Global Macro Card Triggers Broker Sync
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:241-250, 511-523](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L241-L523)
* **Actual Code:**
  ```tsx
  const handleRefresh = async () => {
    setLoading(true);
    try {
      if (workspaceContext?.syncBroker) {
        await workspaceContext.syncBroker(true);
      }
    } finally {
      setLoading(false);
    }
  };
  ...
  <SectionHeader
    title="1. GLOBAL & MACRO CONTEXT"
    icon={Globe}
    action={
      <button onClick={handleRefresh} ...>
        <span>{refreshState === "refreshing" ? "Refreshing…" : refreshState === "updated" ? "Updated" : "Refresh"}</span>
      </button>
    }
  />
  ```
* **Why it is wrong:** The action button is placed in the header of Card 1 ("1. GLOBAL & MACRO CONTEXT"), which displays Yahoo Finance benchmark assets (S&P 500, Brent Crude, etc.). When a user clicks "Refresh", it invokes `workspaceContext.syncBroker(true)`, which triggers a Kite broker session sync. It does not fetch or update global quotes, yet flashes "Updated", misleading the trader.
* **Severity:** **High**

#### Finding 2.2: Daily EOD Flows Presented in Same Visual Context as Live Ticking Telemetry
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:753-757, 830](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L753-L830)
* **Actual Code:**
  ```tsx
  <div className="bg-neutral-950 p-1 rounded border border-[#00C896]/20">
    <span className="text-neutral-500 block text-[7px] uppercase font-bold">FLOWS</span>
    <span className="font-bold uppercase text-[#00C896]">
      {fiiNet != null && diiNet != null ? `${fiiNet + diiNet >= 0 ? "+" : ""}${formatNumber(fiiNet + diiNet, 1)} CR` : "AWAITING PUBLICATION"}
    </span>
  </div>
  ```
* **Why it is wrong:** In the top ribbon of Card 3, `FLOWS (+144.1 CR)` is displayed alongside live-ticking factors (`VOLATILITY: LIVE (13.45)` and `BREADTH: 32 ADV / 18 DEC`) with identical styling, implying that institutional cash flows are ticking live during market hours, when they are only published once daily by NSE after 17:30 IST.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 3: CALCULATED FIELDS & FORMULAS
================================================================================
```

#### Finding 3.1: Fabricated "Constituents Above 20 DMA" Formula
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:1163-1165](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L1163-L1165)
* **Actual Code:**
  ```tsx
  <div className="flex justify-between py-0.5">
    <span className="text-neutral-400">Constituents Above 20 DMA</span>
    <span className={`font-bold air-data ${advCount >= 25 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
      {Math.round(advCount * 1.05)} / 50 Stocks ({Math.min(100, Math.round(advPct * 1.05))}%)
    </span>
  </div>
  ```
* **Why it is wrong:** The workspace claims to display how many NIFTY 50 stocks are trading above their 20-day Moving Average. Instead of querying constituent historical candles and computing actual moving averages, it literally multiplies the day's intraday advance count by `1.05` (`Math.round(advCount * 1.05)`). This is pure mathematical fabrication.
* **Severity:** **Critical**

#### Finding 3.2: Advance Count Recycled as "Volume Ratio" and "Above Daily VWAP"
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:1155-1161](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L1155-L1161)
* **Actual Code:**
  ```tsx
  <div className="flex justify-between py-0.5">
    <span className="text-neutral-400">Up Vol vs Down Vol Ratio</span>
    <span className={`font-bold air-data ${advPct >= 50 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
      {advPct}% Up Vol / {decPct}% Down Vol
    </span>
  </div>
  <div className="flex justify-between py-0.5">
    <span className="text-neutral-400">Constituents Above Daily VWAP</span>
    <span className={`font-bold air-data ${advCount >= 25 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
      {advCount} / 50 Stocks ({advPct}%)
    </span>
  </div>
  ```
* **Why it is wrong:** The metric labeled "Up Vol vs Down Vol Ratio" directly binds to `advPct` (the percentage of advancing stocks), completely ignoring trade volumes. The metric labeled "Constituents Above Daily VWAP" directly binds to `advCount` (stocks trading above yesterday's close), completely ignoring constituent VWAP levels.
* **Severity:** **High**

#### Finding 3.3: Arbitrary Intraday Range Multiplier for "Statistical VWAP Envelope"
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:322-323](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L322-L323)
* **Actual Code:**
  ```tsx
  const vwapPlus1Sd = (vwap != null && intradayRange != null) ? Number((vwap + intradayRange * 0.34).toFixed(2)) : null;
  const vwapMinus1Sd = (vwap != null && intradayRange != null) ? Number((vwap - intradayRange * 0.34).toFixed(2)) : null;
  ```
* **Why it is wrong:** The label claims to display "VWAP +1 SD" and "VWAP -1 SD". Instead of calculating the volume-weighted standard deviation of price, it multiplies the day's high-low range by `0.34`.
* **Severity:** **Medium**

#### Finding 3.4: Negative Risk-Reward Ratio on Resistance Breakout
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:972-980](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L972-L980)
* **Actual Code:**
  ```tsx
  const r1 = envelope.price_structure?.key_resistances?.[0];
  const s1 = envelope.price_structure?.key_supports?.[0];
  if (spot != null && r1 != null && s1 != null && (spot - s1) > 0) {
    return `${((r1 - spot) / (spot - s1)).toFixed(2)} : 1`;
  }
  ```
* **Why it is wrong:** When the price trades above R1 (`spot > r1`), `(r1 - spot)` is negative, producing nonsensical outputs like `-0.35 : 1`.
* **Severity:** **Low**

```
================================================================================
DIMENSION 4: MARKET STATE / SESSION HANDLING
================================================================================
```

#### Finding 4.1: Hardcoded Settlement Dates in Live View
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:608, 1373](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L608-L1373)
* **Actual Code:**
  ```tsx
  Settled on {envelope.session?.completed_session_date || authState.sessionDate || settled?.session_date || "2026-09-01"}
  ...
  Source: {isReplayMode ? "28 Aug 2026 Tape Levels" : ...}
  ```
* **Why it is wrong:** If session metadata is unpopulated, the UI falls back to hardcoded date literals (`"2026-09-01"` and `"28 Aug 2026"`).
* **Severity:** **Low**

```
================================================================================
DIMENSION 5: TIMESTAMP & TIMEZONE
================================================================================
```

#### Finding 5.1: Complete Absence of Data Observation Timestamps Across Metric Cards
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:500-1430](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L500-L1430)
* **Actual Code:**
  None of the 10 metric cards display `observed_at`, `exchange_timestamp`, or an "as of <time> IST" indicator.
* **Why it is wrong:** Card 1 displays global quotes from Yahoo Finance without indicating whether they are 5 minutes old or from yesterday. Cards 4 and 5 display heavyweight and sector matrices without tick timestamps. Card 7 displays FII flows with a date but no publication timestamp. The user has no way of verifying data freshness.
* **Severity:** **High**

```
================================================================================
DIMENSION 6: CROSS-TAB CONSISTENCY
================================================================================
```

#### Finding 6.1: Discrepancies Between NIFTY Tab and METRICS Tab
* **File & Lines:** [MarketPulseWorkspace.tsx:328-340](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L328-L340) vs [LiveWorkspace.tsx:84, 151](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/nifty/LiveWorkspace.tsx#L84-L151)
* **Actual Code:**
  - In `MarketPulseWorkspace.tsx:329`: ATR fallback is `135.10`.
  - In `LiveWorkspace.tsx:84`: ATR fallback is `currentPrice * 0.006` (~`147.00`).
  - In `MarketPulseWorkspace.tsx:363`: Fallback sectors contain 8 sectors (with REALTY and ENERGY).
  - In `LiveWorkspace.tsx:151`: Fallback sectors contain 6 sectors (without REALTY and ENERGY).
* **Why it is wrong:** Navigating between the `NIFTY` tab and the `METRICS` tab during data feed interruptions produces contradictory ATR figures and differing sector lists.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 7: FORMATTING & SIGN/COLOR LOGIC
================================================================================
```

#### Finding 7.1: Zero-Change (Flat) Rendered as Positive Green Across All Cards
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:288, 533, 624, 641, 1018, 1076, 1192, 1210](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L288-L1210)
* **Actual Code:**
  ```tsx
  const positive = (change ?? 0) >= 0; // Card 2
  const pos = numPct >= 0;             // Card 1
  const isPos = hw.changePct >= 0;     // Card 4
  const pos = chg >= 0;                // Card 5
  fiiNet >= 0 ? "text-[#00C896]" : ... // Card 7
  ```
* **Why it is wrong:** Every single component card checks `>= 0`. When a price change, net flow, or delta is exactly `0.00`, it is evaluated as positive, rendering `+0.00` in bright green text (`#00C896`) rather than neutral gray.
* **Severity:** **Medium**

#### Finding 7.2: Inconsistent Decimal Precision Across Adjacent Cards
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:619, 755, 1193, 1280](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L619-L1280)
* **Actual Code:**
  - `intradayRange`: 2 decimals in Card 2 (`formatNumber(intradayRange, 2) pts`), but 1 decimal in Card 8 (`formatNumber(intradayRange, 1) pts`).
  - `fiiNet + diiNet`: 1 decimal in Card 3 ribbon (`formatNumber(fiiNet + diiNet, 1) CR`), but 2 decimals in Card 7 table (`formatNumber(netFlow, 2) Cr`).
* **Why it is wrong:** The exact same numerical fields are displayed with varying precisions across different sections of the same view.
* **Severity:** **Low**

```
================================================================================
DIMENSION 8: ERROR HANDLING & FALLBACKS
================================================================================
```

#### Finding 8.1: Synthetic Technical Indicators (EMAs & RSI) Fallbacks
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:421-424](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L421-L424)
* **Actual Code:**
  ```tsx
  const ema20 = isDataAvailable ? (technical.ema_20 ?? (spot ? Number((spot * 0.996).toFixed(2)) : null)) : null;
  const ema50 = isDataAvailable ? (technical.ema_50 ?? (spot ? Number((spot * 0.991).toFixed(2)) : null)) : null;
  const ema200 = isDataAvailable ? (technical.ema_200 ?? (spot ? Number((spot * 0.975).toFixed(2)) : null)) : null;
  const rsiVal = technical.rsi_14 ?? 56.4;
  ```
* **Why it is wrong:** When the technical analysis engine has not computed EMAs, the workspace synthesizes EMA 20 as `spot * 0.996`, EMA 50 as `spot * 0.991`, EMA 200 as `spot * 0.975`, and defaults RSI to `56.4`.
* **Severity:** **High**

```
================================================================================
DIMENSION 9: LOADING STATES
================================================================================
```

#### Finding 9.1: Total Absence of Skeleton Loaders on Initial Hydration
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:235-1430](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L235-L1430)
* **Actual Code:**
  No `<Skeleton>` component, placeholder layout, or card-level shimmer loaders exist in the file.
* **Why it is wrong:** During initial mount or before the WebSocket connects, the workspace renders empty cards with `"—"`, unpopulated tables, or flashes hardcoded fallback values.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 10: UI/LAYOUT & RESPONSIVE INTEGRITY
================================================================================
```

#### Finding 10.1: Hardcoded Dark Mode Palette Bypassing Application Theme Tokens
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:480-1430](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L480-L1430)
* **Actual Code:**
  Hardcoded Tailwind color classes (`bg-neutral-950`, `bg-neutral-900/50`, `border-neutral-800/80`, `text-neutral-200`) are used throughout.
* **Why it is wrong:** The workspace does not support dynamic theming or light mode; switching the theme leaves the Metrics tab locked in dark styling.
* **Severity:** **Low**

```
================================================================================
DIMENSION 11: DEAD CODE & MOCK-DATA RESIDUE
================================================================================
```

#### Finding 11.1: Hidden DOM Scaffold Injected to Satisfy Automated Tests
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:481-499](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L481-L499)
* **Actual Code:**
  ```tsx
  {/* Hidden Hooks for Test Invariants & Contract Anchors */}
  <div className="hidden" aria-hidden="true">
    <button onClick={handleRefresh}>
      {refreshState === "refreshing" ? "Refreshing…" : "Sync"}
    </button>
    <span>await syncBroker(true)</span>
    <span>refreshState === "refreshing"</span>
    <span>Market metrics & global telemetry</span>
    <span>INDIA_VIX</span>
    <span>Object.keys(quotes)</span>
    <span>xl:grid-cols-[minmax(280px</span>
    <span>selected.kind === "institutional</span>
    <span>getCanonicalQuote(macroQuote</span>
    <span>mapTraderEnum(sectors[0].ob</span>
    <span>Session review</span>
    <span>&lt;SectorPerformanceChart</span>
    <span>formatRelativeAge</span>
  </div>
  ```
* **Why it is wrong:** An invisible DOM block (`className="hidden" aria-hidden="true"`) exists solely to contain string literals that legacy integration tests search for via raw string matching (e.g. `tests/test_market_pulse_scoped_refresh.py` and `tests/test_sprint_c101_ui_polish.py`). This is dead scaffolding designed to bypass test assertion failures.
* **Severity:** **Medium**

#### Finding 11.2: Completely Hardcoded Confluence Factor Weights & Scores
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:779, 805, 809, 817, 889-928](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L779-L928)
* **Actual Code:**
  ```tsx
  <span className="font-bold text-neutral-100">{isDataAvailable ? "72 / 100" : "—"}</span>
  ...
  <span className="font-bold text-neutral-200">{isDataAvailable ? "64.2%" : "Awaiting Live Stream"}</span>
  ...
  <span className="font-bold text-neutral-400">{isDataAvailable ? "35.8%" : "—"}</span>
  ...
  <span className="font-bold text-neutral-200">{isDataAvailable ? "68% (34 / 50)" : "—"}</span>
  ...
  <span className="text-[7.5px] px-1 py-0.2 rounded bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30">74 / 100</span>
  ...
  <span className="text-[#00C896] font-bold">85% Bullish</span>
  ...
  <span className="text-[#00C896] font-bold">70% Bullish</span>
  ...
  <span className="text-[#38BDF8] font-bold">65% Neutral-Bull</span>
  ...
  <span className="text-[#38BDF8] font-bold">55% Mild Bullish</span>
  ```
* **Why it is wrong:** Card 3 ("3. QUANTITATIVE INSTITUTIONAL MATRIX") presents sub-cards claiming to show real-time quantitative multi-factor confluence. Every single score and percentage in Sub-Card 5 is completely hardcoded (`74/100`, `85% Bullish`, `70% Bullish`, `65% Neutral-Bull`, `55% Mild Bullish`), along with `72/100` Trend Strength, `64.2%` Up Vol, and `68% (34/50)` Above Daily VWAP.
* **Severity:** **High**

```
================================================================================
DIMENSION 12: PERFORMANCE & MEMORY
================================================================================
```

#### Finding 12.1: Dead `liveTickPrice` State Hook
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:238, 277](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L238-L277)
* **Actual Code:**
  ```tsx
  const [liveTickPrice, setLiveTickPrice] = useState<number | null>(null);
  ...
  const spot = authState.spot ?? (isDataAvailable ? (... : (liveTickPrice ?? ...)) : null);
  ```
* **Why it is wrong:** `liveTickPrice` is allocated via `useState`, but `setLiveTickPrice` is never invoked anywhere in the codebase. It represents dead state residue that is always `null`.
* **Severity:** **Medium**

#### Finding 12.2: 1-Second Context Invalidation Triggering Full Workspace Reconciliation
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:235-1430](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L235-L1430)
* **Actual Code:**
  `MarketPulseWorkspace` consumes `useCanonicalState()`, which updates every 1,000ms via `clockTick`.
* **Why it is wrong:** Because only 2 sub-elements (`sectorList` and `heavyweights`) are wrapped in `useMemo`, all 1,437 lines of JSX and calculations (including sorting the structural price ladder, mapping the 11 global instruments, and computing gap math) re-execute every single second regardless of whether any data changed.
* **Severity:** **Low**

```
================================================================================
DIMENSION 13: CONSOLE & NETWORK HYGIENE
================================================================================
```

#### Finding 13.1: Redundant Broker Sync Network Traffic on UI Refresh
* **File & Lines:** [src/frontend/components/MarketPulseWorkspace.tsx:241-248](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L241-L248)
* **Actual Code:**
  ```tsx
  if (workspaceContext?.syncBroker) {
    await workspaceContext.syncBroker(true);
  }
  ```
* **Why it is wrong:** Repeatedly clicking "Refresh" triggers unnecessary HTTP calls to Kite broker endpoints instead of refreshing client data caches.
* **Severity:** **Low**

---

### 3. Verified Clean

The following items were explicitly audited and verified to be clean of defects:

* **Read-Only Invariant Enforcement:** Verified clean. No order placement, trade modification, or mutation controls exist on this tab.
* **Broker Credential Security:** Verified clean. Neither Kite API keys, access tokens, nor Yahoo Finance headers leak into the client DOM or network responses.
* **Kite Upstream Ticker Fidelity:** Verified clean. The primary spot price and India VIX bind directly to authoritative Kite WebSocket tokens `256265` and `264969` via `resolveAuthoritativeMarketState`.
* **Division by Zero Guards:** Verified clean. Line 1138 (`totalB > 0 ? Math.round((unchCount / totalB) * 100) : 0`) and line 1093 (`adv / (adv + dec || 1)`) correctly guard against division by zero.
* **Cross-Asset Sparkline Geometry:** Verified clean. `MiniTrendSparkline` in lines 186–232 filters out zero/null values, enforces a minimum 2-point array requirement, and properly scales SVG polyline points without causing layout reflows or clipping.
* **Global Asset Icon Fidelity:** Verified clean. `CrossAssetIcon` cleanly renders custom SVG emblems for all 11 global benchmark instruments without external font or asset dependencies.
