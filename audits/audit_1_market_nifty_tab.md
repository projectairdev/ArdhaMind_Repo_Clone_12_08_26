# NIFTY Tab — Full E2E Forensic Audit

### 1. Summary

A comprehensive, read-only forensic audit was conducted across the entire **Market → NIFTY** tab, covering all four active operational phase workspaces (**Morning**, **Opening**, **Live**, and **Post-Market**), the central telemetry header (`NiftyHeader.tsx`), the financial charting engine (`CanonicalTradingChart.tsx`), the authoritative state convergence engine (`CanonicalStateContext.tsx`), the backend streaming bridge, and all associated session schedulers. While the platform upholds its core read-only invariants and guarantees single-upstream KiteTicker isolation with zero client-side credential leakage, the audit identified **2 Critical**, **8 High**, **11 Medium**, and **5 Low** severity defects. Most critically, the live workspace contains multiple synthetic data fallbacks—including fabricated sector performance algorithms and hardcoded price level offsets—which directly violate the core safety rule prohibiting synthetic or fabricated market data. Additionally, session phase transitions currently depend on client-side browser clocks rather than authoritative exchange tick time, and real-time tick streaming in the charting layer triggers complete array replacements (`.setData`) instead of incremental bar updates.

| Severity | Finding Count | Primary Impact Area |
| :--- | :---: | :--- |
| **Critical** | **2** | Fabricated sector formulas & arbitrary structural price level offsets in live path |
| **High** | **8** | Fabricated options metrics, client clock session hijacking, inverted day location, chart series re-population on tick, missing tick timestamp |
| **Medium** | **11** | Mislabeled labels ("Settled VWAP" during live), missing Indian digit grouping, 5 dead component files, 1s global re-render cascade, checkbox state crosstalk |
| **Low** | **5** | Float rounding drift in % change, minimum 0.1 range floor, responsive `divide-x` artifacts, unbacked REST polling, unused top bar timestamp |
| **Total** | **26** | |

---

### 2. Forensic Findings by Dimension (1–13)

```
================================================================================
DIMENSION 1: DATA SOURCE & FIELD-LEVEL FIDELITY
================================================================================
```

#### Finding 1.1: Fabricated Sector Leadership Fallback Algorithm in Live Workspace
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx:149-158`
* **Actual Code:**
  ```tsx
  let rawSectors = (envelope as any)?.market?.sectors || (envelope as any)?.sectors || [];
  if (!Array.isArray(rawSectors) || rawSectors.length === 0) {
    rawSectors = [
      { name: "NIFTY BANK", change_pct: marketState.changePct != null ? Number((marketState.changePct * 1.1 + 0.12).toFixed(2)) : 0.45 },
      { name: "NIFTY AUTO", change_pct: marketState.changePct != null ? Number((marketState.changePct * 0.9 + 0.35).toFixed(2)) : 0.65 },
      { name: "NIFTY PHARMA", change_pct: marketState.changePct != null ? Number((marketState.changePct * 0.4 + 0.05).toFixed(2)) : 0.20 },
      { name: "NIFTY IT", change_pct: marketState.changePct != null ? Number((marketState.changePct * 0.8 - 0.25).toFixed(2)) : -0.15 },
      { name: "NIFTY FMCG", change_pct: marketState.changePct != null ? Number((marketState.changePct * 0.3 - 0.18).toFixed(2)) : -0.10 },
      { name: "NIFTY METAL", change_pct: marketState.changePct != null ? Number((marketState.changePct * 1.3 - 0.40).toFixed(2)) : -0.35 },
    ];
  }
  ```
* **Why it is wrong:** When real sector data is missing or empty, the live workspace synthesizes six fictitious sectors with mathematical multipliers pegged to NIFTY change (e.g. `marketState.changePct * 1.1 + 0.12`). This fabricates fake sector performance and directly violates the absolute production invariant: *"Never fabricate market data. Never replace missing data with synthetic values."*
* **Severity:** **Critical**

#### Finding 1.2: Hardcoded Synthetic Fallbacks for Structural Levels and ATR
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx:84, 94, 104, 107-108`
* **Actual Code:**
  ```tsx
  const atr14 = price_structure.atr_14 ?? (currentPrice != null ? currentPrice * 0.006 : null);
  ...
  return openPrice != null ? openPrice + 35 : null; // ORH fallback
  ...
  return openPrice != null ? openPrice - 35 : null; // ORL fallback
  ...
  const immediateResistance = price_structure?.key_resistances?.[0] ?? (openPrice != null && atr14 ? openPrice + atr14 * 0.5 : (currentPrice != null ? currentPrice + 45 : null));
  const immediateSupport = price_structure?.key_supports?.[0] ?? (openPrice != null && atr14 ? openPrice - atr14 * 0.5 : (currentPrice != null ? currentPrice - 45 : null));
  ```
* **Why it is wrong:** When the price structure or opening range is unpopulated, the component synthesizes levels using arbitrary point offsets (`openPrice ± 35`, `currentPrice ± 45`) and synthetic ATR (`currentPrice * 0.006`). This violates the core architectural rule: *"StructuralLevelEngine evidence-based levels only. No arbitrary price offsets."*
* **Severity:** **Critical**

#### Finding 1.3: Hardcoded Synthetic Options Metrics and Confirmation Texts
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx:111-114, 622-624`
* **Actual Code:**
  ```tsx
  const resolvedPutWall = options?.put_wall ?? (resolvedAtmStrike != null ? resolvedAtmStrike - 200 : null);
  const resolvedCallWall = options?.call_wall ?? (resolvedAtmStrike != null ? resolvedAtmStrike + 200 : null);
  const resolvedPcr = options?.pcr ?? (envelope as any)?.options?.pcr ?? 1.08;
  ...
  <span>Synthesis: <strong className="text-[#00C896]">Put Base Holding</strong></span>
  <span className="text-[#00C896] font-bold">CONFIRMED</span>
  ```
* **Why it is wrong:** If real options OI data is unavailable, strikes are synthetically generated at `±200` from ATM, PCR defaults to `1.08`, and the bottom card unconditionally hardcodes "Put Base Holding" and "CONFIRMED".
* **Severity:** **High**

#### Finding 1.4: Mislabeled "Settled VWAP" Telemetry Field During Live Market
* **File & Lines:** `src/frontend/components/canonical/nifty/NiftyHeader.tsx:90-92, 246-251`
* **Actual Code:**
  ```tsx
  const resolvedSettledVwap = isLiveTape
    ? (authState.vwap ?? price_structure?.vwap ?? null)
    : (settledVwap ?? authState.vwap ?? price_structure?.vwap ?? settled?.vwap ?? null);
  ...
  <span className="text-[9.5px] uppercase tracking-widest text-neutral-500 font-semibold">
    Settled VWAP
  </span>
  <span className="text-xs lg:text-sm font-bold text-amber-400 mt-0.5">
    {resolvedSettledVwap != null ? `₹${formatNumber(resolvedSettledVwap, 2)}` : "—"}
  </span>
  ```
* **Why it is wrong:** During continuous trading (`isLiveTape`), the value bound to this display is the *live intraday running VWAP*. However, the UI label is static and displays "Settled VWAP", misleading the user into believing they are viewing yesterday's closed VWAP.
* **Severity:** **Medium**

#### Finding 1.5: Pre-Open Indicative Auction Print Mislabeled as "Prev Close"
* **File & Lines:** `src/frontend/components/canonical/nifty/NiftyHeader.tsx:74-79, 213-219`
* **Actual Code:**
  ```tsx
  const resolvedSettledClose =
    settledClose ??
    (isPreMarket || isPreOpen
      ? (authState.spot ?? market?.nifty?.last_price ?? settled?.close)
      : (settled?.close ?? authState.prevClose ?? market?.nifty?.previous_close)) ??
    null;
  ```
* **Why it is wrong:** During `PRE_OPEN` (09:00–09:15 IST), `resolvedSettledClose` falls back to `authState.spot` (which is the matched indicative auction price), yet the UI label at line 214 is "Prev Close". An indicative discovery price is therefore displayed under the label "Prev Close".
* **Severity:** **High**

```
================================================================================
DIMENSION 2: REAL-TIME PIPELINE
================================================================================
```

#### Finding 2.1: Fragmented Header Implementation Across Workspace Phases
* **File & Lines:** `src/frontend/components/canonical/nifty/OpeningWorkspace.tsx:100-151`, `src/frontend/components/canonical/nifty/PostMarketWorkspace.tsx:116-187`
* **Actual Code:**
  `OpeningWorkspace.tsx` and `PostMarketWorkspace.tsx` do not import or render `<NiftyHeader />`. Instead, each implements its own custom markup with divergent fallback logic.
* **Why it is wrong:** While `MorningWorkspace` and `LiveWorkspace` use the unified `NiftyHeader`, `OpeningWorkspace` reads `nifty.last_price` directly with zero fallback cascades, rendering `"Unavailable"` if `nifty.last_price` is briefly unpopulated during connection transitions.
* **Severity:** **Medium**

#### Finding 2.2: Premature Opening Range Status Lock Evaluation
* **File & Lines:** `src/frontend/components/canonical/nifty/OpeningWorkspace.tsx:91-95`
* **Actual Code:**
  ```tsx
  const isOrComplete =
    price_structure.opening_range_status === "CONFIRMED_BREAKOUT_UP" ||
    price_structure.opening_range_status === "CONFIRMED_BREAKOUT_DOWN" ||
    price_structure.opening_range_status === "FAILED_BREAKOUT" ||
    session?.market_phase === "MARKET_OPEN";
  ```
* **Why it is wrong:** If backend market state registers `session.market_phase === "MARKET_OPEN"` at 09:15:05 IST, `isOrComplete` immediately evaluates to `true` and displays "OR Status: LOCKED", even though the 15-minute opening range is still actively forming until 09:30:00 IST.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 3: CALCULATED FIELDS & FORMULAS
================================================================================
```

#### Finding 3.1: Arbitrary 2.5x Scaling and 10% Floor in ATR Utilization Formula
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx:134-137`
* **Actual Code:**
  ```tsx
  const atrUtilization = useMemo(() => {
    if (dayRange == null || atr14 == null || atr14 <= 0) return null;
    return Math.round(Math.min(100, Math.max(10, (dayRange / (atr14 * 2.5)) * 100)));
  }, [dayRange, atr14]);
  ```
* **Why it is wrong:** The formula divides `dayRange` by `(atr14 * 2.5)` instead of `atr14`, suppressing true ATR utilization by 60%. Furthermore, `Math.max(10, ...)` forces the gauge to report at least 10% utilization even when the market has moved 0 points. This directly conflicts with `PostMarketWorkspace.tsx:80` and `resolveAuthoritativeMarketState.ts:278`.
* **Severity:** **High**

#### Finding 3.2: Inverted Day Location Metric Display in Live Workspace
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx:140-144, 285`
* **Actual Code:**
  ```tsx
  const raw = ((currentPrice - dayLow) / (dayHigh - dayLow)) * 100;
  return Math.max(0, Math.min(100, Math.round(raw)));
  ...
  <span className="font-bold text-[#38BDF8] text-[10.5px]">
    {dayLocationPct != null ? `Upper ${100 - dayLocationPct}%` : "—"}
  </span>
  ```
* **Why it is wrong:** The display unconditionally prefixes the value with `"Upper"`. If the price is trading at the day low (`dayLocationPct = 5%`), it displays `Upper 95%`. A trader reading this would believe the asset is near the upper edge of its day range when it is actually breaking down at the low.
* **Severity:** **High**

#### Finding 3.3: Mathematical Rounding Drift Between % Change Calculation Paths
* **File & Lines:** `src/frontend/utils/resolveAuthoritativeMarketState.ts:191-192` vs `src/frontend/context/CanonicalStateContext.tsx:604-605`
* **Actual Code:**
  `resolveAuthoritativeMarketState`:
  ```ts
  change = Number((spot - settledClose).toFixed(2));
  changePercent = Number(((change / settledClose) * 100).toFixed(2));
  ```
  `CanonicalStateContext`:
  ```ts
  const changePct = prevClose != null && prevClose > 0 ? Number((((price - prevClose) / prevClose) * 100).toFixed(2)) : ...;
  ```
* **Why it is wrong:** `resolveAuthoritativeMarketState` computes `changePercent` using the 2-decimal rounded `change`, whereas `CanonicalStateContext` computes `changePct` using the raw unrounded float difference. This results in a 1-basis-point discrepancy on rounding thresholds.
* **Severity:** **Low**

#### Finding 3.4: Artificial 0.1 Point Range Floor in Opening Workspace
* **File & Lines:** `src/frontend/components/canonical/nifty/OpeningWorkspace.tsx:81`
* **Actual Code:**
  ```tsx
  const orRange = (orHigh != null && orLow != null) ? Math.max(0.1, orHigh - orLow) : null;
  ```
* **Why it is wrong:** Fabricates a non-zero range of `0.1` points when `orHigh === orLow` (e.g. initial print at 09:15:00).
* **Severity:** **Low**

```
================================================================================
DIMENSION 4: MARKET STATE / SESSION HANDLING
================================================================================
```

#### Finding 4.1: Client OS Wall Clock Controls Session Phase State Machine
* **File & Lines:** `src/frontend/context/CanonicalStateContext.tsx:298-303, 370-379`, `src/frontend/session/sessionPhaseEngine.ts:86-106, 201-250`
* **Actual Code:**
  ```ts
  const [clockTick, setClockTick] = useState<Date>(new Date());
  useEffect(() => {
    const timer = setInterval(() => setClockTick(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  ...
  resolveCanonicalSessionIdentity({ customDate: clockTick, ... });
  ```
* **Why it is wrong:** The entire session phase state machine (`PRE_MARKET`, `PRE_OPEN`, `LIVE`, `NEAR_CLOSE`, `POST_MARKET`) evaluates based on `new Date()` from the client browser. If a user's local PC clock is skewed by 10 minutes, the client will enter `LIVE` mode while the exchange is still in pre-open, or enter `POST_MARKET` while the market is still actively trading.
* **Severity:** **High**

#### Finding 4.2: Hardcoded Fallback Session Dates in Trading Day Engines
* **File & Lines:** `src/frontend/session/sessionPhaseEngine.ts:173, 194`
* **Actual Code:**
  ```ts
  return { iso: "2026-08-28", formatted: "28 Aug 2026" };
  ...
  return { iso: "2026-09-01", formatted: "01 Sep 2026" };
  ```
* **Why it is wrong:** If the trading day lookback loop exceeds 30 iterations (or encounters an unexpected boundary), it returns hardcoded date strings from August/September 2026.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 5: TIMESTAMP & TIMEZONE
================================================================================
```

#### Finding 5.1: No Exchange Tick / Observation Timestamp Displayed on NIFTY Tab
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx:666-680`, `src/frontend/components/canonical/nifty/NiftyHeader.tsx:135-268`
* **Actual Code:**
  The trust footer displays `DATA STATE: LIVE FEED`, `PREVIOUS SESSION: AVAILABLE`, `CANONICAL DATA: VALID`, and `Source: NSE Real-Time Feed`. Neither `NiftyHeader` nor `LiveWorkspace` renders `exchange_timestamp` or `observed_at`.
* **Why it is wrong:** The trader has no indication of the precise exchange observation time of the live tick. Stale or frozen ticks cannot be visually audited for time freshness on the tab.
* **Severity:** **High**

#### Finding 5.2: `lastUpdated` Context State Driven by Browser Packet Receipt Time
* **File & Lines:** `src/frontend/context/CanonicalStateContext.tsx:508, 687`
* **Actual Code:**
  ```ts
  setLastUpdated(new Date());
  ```
* **Why it is wrong:** `lastUpdated` reflects the local browser time when the WebSocket frame was parsed, not the exchange tick timestamp.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 6: CROSS-TAB CONSISTENCY
================================================================================
```

#### Finding 6.1: Cross-Tab Inconsistency Between NIFTY Tab and METRICS Tab
* **File & Lines:** `src/frontend/components/MarketPulseWorkspace.tsx:328-341` vs `src/frontend/components/canonical/nifty/LiveWorkspace.tsx:84, 100-104`
* **Actual Code:**
  In `MarketPulseWorkspace.tsx`:
  ```ts
  const atr = rawAtr != null && Number(rawAtr) >= 20 ? Number(rawAtr) : 135.10;
  const vixVal = authState.vix ?? ... ?? 10.68;
  ```
* **Why it is wrong:** Switching from `Market → NIFTY` to `Market → METRICS` reveals mismatched ATR and VIX values whenever live data is thin, because `MarketPulseWorkspace` falls back to hardcoded literals (`135.10` and `10.68`) while the NIFTY tab uses authoritative context resolvers.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 7: FORMATTING & SIGN/COLOR LOGIC
================================================================================
```

#### Finding 7.1: Missing Indian Digit Grouping in PostMarketWorkspace
* **File & Lines:** `src/frontend/components/canonical/nifty/PostMarketWorkspace.tsx:121, 129, 148, 155, 162, 168`
* **Actual Code:**
  ```tsx
  {closePrice != null ? closePrice.toFixed(2) : "—"}
  ...
  {absChange.toFixed(2)}
  ...
  {prevClose != null ? prevClose.toFixed(2) : "—"}
  ```
* **Why it is wrong:** Uses raw JavaScript `.toFixed(2)` rather than `formatNumber` / `toLocaleString("en-IN")`. Large price figures render as `23882.85` instead of `23,882.85`, violating Indian financial digit grouping standards.
* **Severity:** **Medium**

#### Finding 7.2: Zero-Change (Flat) Edge Case Rendered as Green with `+` Sign
* **File & Lines:** `src/frontend/components/canonical/nifty/NiftyHeader.tsx:107, 197-198`, `src/frontend/components/canonical/nifty/PostMarketWorkspace.tsx:65, 120, 129`
* **Actual Code:**
  ```tsx
  const isPositive = (resolvedChange ?? 0) >= 0;
  ...
  <div className={`flex items-center text-xs font-mono font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
    <span>{isPositive ? "+" : ""}{formatNumber(resolvedChange, 2)}</span>
  </div>
  ```
* **Why it is wrong:** When change is exactly `0.00`, `>= 0` evaluates to `true`. The UI displays `+0.00` in green text instead of treating flat zero as neutral grey.
* **Severity:** **Medium**

#### Finding 7.3: Inconsistent Decimal Precision Across Adjacent Metric Cards
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx:80, 385`, `src/frontend/components/canonical/nifty/PostMarketWorkspace.tsx:242, 313`
* **Actual Code:**
  In `LiveWorkspace`, `dayRange` is rounded via `toFixed(1)` at line 80, but rendered as `formatNumber(dayRange, 2)` at line 385. In `PostMarketWorkspace`, `dayRange` is formatted with `toFixed(0)` at line 242 and `toFixed(1)` at line 313.
* **Why it is wrong:** The same numerical field displays with different decimal precisions within adjacent cards of the same view.
* **Severity:** **Low**

```
================================================================================
DIMENSION 8: ERROR HANDLING & FALLBACKS
================================================================================
```

#### Finding 8.1: Missing Data Masked with Synthetic Numbers Instead of Awaiting States
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx:84-114`
* **Actual Code:**
  Refer to Findings 1.1, 1.2, and 1.3.
* **Why it is wrong:** Partial stream failures (e.g. LTP streaming while options or breadth pipelines encounter transient delay) cause the UI to render fabricated values rather than an explicit "Awaiting Data" indicator.
* **Severity:** **High**

#### Finding 8.2: Transient Stale Alert Flash on Initial Component Mount
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx:69, 72, 209-217`
* **Actual Code:**
  ```tsx
  const hasLivePrice = currentPrice != null && currentPrice > 0;
  const isStale = (data_quality === "STALE" || data_quality === "UNAVAILABLE") && !hasLivePrice;
  ...
  {isStale && (
    <div className="... bg-[#EF4444]/20 border border-[#EF4444] text-[#EF4444] ...">
      STALE DATA — LIVE INTERPRETATION PAUSED
    </div>
  )}
  ```
* **Why it is wrong:** During initial hydration before the first packet arrives, `currentPrice` is `null` and `data_quality` is `"UNAVAILABLE"`. `isStale` evaluates to `true`, flashing a red error banner for a few milliseconds before the first envelope resolves.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 9: LOADING STATES
================================================================================
```

#### Finding 9.1: Absence of Skeleton Loaders on Cold Start
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx`, `src/frontend/components/canonical/chart/CanonicalTradingChart.tsx:211`
* **Actual Code:**
  ```ts
  if (targetSet.length === 0) return { min: 24400, max: 24650 };
  ```
* **Why it is wrong:** There are no dedicated skeleton loader cards for metric panels. On cold start with empty cache, metric cells render unpopulated dash strings while the chart initializes with an arbitrary hardcoded price axis (`24400` to `24650`).
* **Severity:** **Medium**

```
================================================================================
DIMENSION 10: UI/LAYOUT & RESPONSIVE INTEGRITY
================================================================================
```

#### Finding 10.1: Shared Checkbox State Crosstalk in Morning Workspace
* **File & Lines:** `src/frontend/components/canonical/nifty/MorningWorkspace.tsx:69, 258-268, 499-512`
* **Actual Code:**
  ```tsx
  const [checklist, setChecklist] = useState<Record<number, boolean>>({ ... });
  const toggleCheck = (i: number) => setChecklist((prev) => ({ ...prev, [i]: !prev[i] }));
  ```
* **Why it is wrong:** Card 4 ("PRE-MARKET ACTION CHECKLIST") in the right stack and Col 4 ("MORNING CHECKLIST") in the bottom row both bind to the exact same `checklist[idx]` state array and `toggleCheck` handler. Clicking item 0 in the bottom checklist toggles item 0 in the right-hand checklist, even though their prompt labels are completely different.
* **Severity:** **Medium**

#### Finding 10.2: Tailwind `divide-x` Responsive Row-Wrap Visual Glitch
* **File & Lines:** `src/frontend/components/canonical/nifty/PostMarketWorkspace.tsx:144`
* **Actual Code:**
  ```tsx
  <div className="flex flex-wrap items-center divide-x divide-[#1E232B] text-xs">
  ```
* **Why it is wrong:** When the viewport drops below 1280px and header items wrap onto a second line, `divide-x` places a vertical border on the leftmost item of the wrapped line.
* **Severity:** **Low**

#### Finding 10.3: Hardcoded Dark Mode Palette Without Theme Token Integration
* **File & Lines:** `src/frontend/components/canonical/nifty/LiveWorkspace.tsx`, `src/frontend/components/canonical/nifty/MorningWorkspace.tsx`
* **Actual Code:**
  Components use hardcoded hex values (`bg-[#08090B]`, `bg-[#0E1013]`, `border-[#1E232B]`).
* **Why it is wrong:** Switching the application theme via `ThemeContext` has no effect on the NIFTY workspace; the entire workspace remains locked in hardcoded dark styling.
* **Severity:** **Low**

```
================================================================================
DIMENSION 11: DEAD CODE & MOCK-DATA RESIDUE
================================================================================
```

#### Finding 11.1: Five Completely Orphaned Component Files in Component Tree
* **Files:**
  1. `src/frontend/components/canonical/nifty/PreMarketWorkspace.tsx` (600 lines)
  2. `src/frontend/components/canonical/nifty/SupportingPanels.tsx` (300 lines)
  3. `src/frontend/components/canonical/nifty/MarketStructurePanel.tsx` (190 lines)
  4. `src/frontend/components/canonical/nifty/PhaseSpecificPanels.tsx` (260 lines)
  5. `src/frontend/components/canonical/CanonicalNiftyChart.tsx` (400 lines)
* **Why it is wrong:** Over 1,750 lines of code across 5 files in the NIFTY component tree are unimported by any active route or workspace. They represent leftover scaffolding from prior iterations.
* **Severity:** **Medium**

#### Finding 11.2: Mock Data Residue in Live Fallback Paths
* **Files & Lines:**
  - `PostMarketWorkspace.tsx:235`: `{breadth?.advance_pct != null ? ... : "40% Adv"}`
  - `PostMarketWorkspace.tsx:424`: `{breadth?.leadership_bias || "BEARISH BIAS"}`
  - `PostMarketWorkspace.tsx:109`: `tomorrowPlan?.preliminary_next_bias || "BULLISH"`
  - `PostMarketWorkspace.tsx:54`: `completedDate = ... || "2026-09-01"`
  - `LiveWorkspace.tsx:204`: `liveGuide?.confidence ?? 74;`
  - `CanonicalTradingChart.tsx:211`: `{ min: 24400, max: 24650 }`
* **Why it is wrong:** Plausible numbers and biased strings (`"40% Adv"`, `"BEARISH BIAS"`, `"BULLISH"`, `74`) remain embedded in live ternary fallbacks.
* **Severity:** **High**

```
================================================================================
DIMENSION 12: PERFORMANCE & MEMORY
================================================================================
```

#### Finding 12.1: Full Chart Series Replacement (`.setData`) on Every WebSocket Tick
* **File & Lines:** `src/frontend/components/canonical/chart/CanonicalTradingChart.tsx:649-661`
* **Actual Code:**
  ```tsx
  useEffect(() => {
    if (!candleSeriesRef.current || !vwapSeriesRef.current || !activitySeriesRef.current) return;
    candleSeriesRef.current.setData(chartData as any);
    vwapSeriesRef.current.setData(showVwap ? (vwapCalculatedData as any) : []);
    upper1SeriesRef.current?.setData(showBands ? (upper1Data as any) : []);
    lower1SeriesRef.current?.setData(showBands ? (lower1Data as any) : []);
    upper2SeriesRef.current?.setData(showBands ? (upper2Data as any) : []);
    lower2SeriesRef.current?.setData(showBands ? (lower2Data as any) : []);
    ema9SeriesRef.current?.setData(showEmas ? (ema9Data as any) : []);
    ema21SeriesRef.current?.setData(showEmas ? (ema21Data as any) : []);
    activitySeriesRef.current.setData(showActivity ? (activityData as any) : []);
  }, [...]);
  ```
* **Why it is wrong:** Lightweight-charts supports incremental updates via `.update(bar)`. In this implementation, `.setData()` is called for all 9 series on *every incoming tick*, destroying and re-allocating memory for hundreds of bars multiple times per second during high-velocity trading.
* **Severity:** **High**

#### Finding 12.2: Global 1-Second Interval Triggering Unnecessary App-Wide Re-renders
* **File & Lines:** `src/frontend/context/CanonicalStateContext.tsx:300-303, 809-822`
* **Actual Code:**
  ```ts
  useEffect(() => {
    const timer = setInterval(() => setClockTick(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  ```
* **Why it is wrong:** `clockTick` triggers every 1,000ms, causing `sessionIdentity` to regenerate. Because `sessionIdentity` is in the dependency array of the root context provider's value (line 819), the context reference changes every second, forcing a full virtual DOM reconciliation of `DashboardLayout`, `NiftyHeader`, and the active workspace even when no market data has changed.
* **Severity:** **Medium**

#### Finding 12.3: Boundary Scheduler Timer Thrashing on Every Render
* **File & Lines:** `src/frontend/hooks/useSessionPhaseScheduler.ts:65-101`, `src/frontend/context/CanonicalStateContext.tsx:545-548`
* **Actual Code:**
  In `CanonicalStateContext.tsx`:
  ```ts
  useSessionPhaseScheduler(() => {
    setClockTick(new Date());
    fetchLiveEnvelope({ forceRefresh: true });
  });
  ```
* **Why it is wrong:** An inline anonymous function is passed to `useSessionPhaseScheduler`. On every 1-second tick, the callback reference changes, causing `triggerTransition` to change and forcing `useEffect` in `useSessionPhaseScheduler` to clear and re-arm its `setTimeout` and `setInterval` every second.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 13: CONSOLE & NETWORK HYGIENE
================================================================================
```

#### Finding 13.1: Indefinite REST Fallback Polling Without Exponential Backoff
* **File & Lines:** `src/frontend/context/CanonicalStateContext.tsx:751`
* **Actual Code:**
  ```ts
  const interval = setInterval(fetchCanonicalState, 3000);
  ```
* **Why it is wrong:** If the server is offline or restarting, the client hammers `/api/canonical/envelope` every 3 seconds indefinitely with no backoff or circuit breaking.
* **Severity:** **Low**

#### Finding 13.2: Declared but Unused Authoritative Timestamp in Top Bar
* **File & Lines:** `src/frontend/components/WorkstationTopBar.tsx:40-44`
* **Actual Code:**
  ```tsx
  const authoritativeTs =
    state?.generated_at ||
    state?.data_quality?.market_data?.observed_at ||
    state?.market_data?.observed_at;
  ```
* **Why it is wrong:** `authoritativeTs` is declared and computed, but never rendered anywhere in `WorkstationTopBar`.
* **Severity:** **Low**

---

### 3. Verified Clean

The following items were explicitly investigated and verified to be correct and clean of defects:

* **Broker Key & Token Isolation:** Verified clean. Neither `activeApiKey`, `activeAccessToken`, nor `OPENAI_API_KEY` are exported to client-side bundles, exposed in WebSocket broadcasts, or serialized in REST payloads.
* **Single-Upstream KiteTicker Invariant:** Verified clean. `StreamingOrchestrator` implements a strict singleton with `generation_id` isolation. Spawning, refreshing, or switching browser tabs does not create duplicate upstream KiteTicker connections.
* **Transient Disconnection Auth Preservation:** Verified clean. Transient WebSocket drops do not invalidate stored Kite authentication; session tokens remain valid and reconnect loops execute cleanly.
* **Kite Instrument Token Subscriptions:** Verified clean. `SubscriptionManager` correctly maps NIFTY 50 to token `256265`, INDIA VIX to `264969`, and secondary indices to their official NSE tokens with duplicate subscription filtering.
* **Read-Only Invariant Enforcement:** Verified clean. All REST mutation routes reject mutation requests via `rejectReadOnlyMutation`; zero order placement or mutation code exists in the workspace path.
* **Multi-TF Candle Deduplication:** Verified clean. `CanonicalTradingChart.tsx:307-341` correctly parses, sorts, and deduplicates historical candle timestamps into strictly ascending Unix seconds, preventing lightweight-charts panic crashes.
* **Chart Instance Cleanup:** Verified clean. `CanonicalTradingChart.tsx:628-646` cleanly disconnects `ResizeObserver`, removes window event listeners, detaches primitives, and invokes `chart.remove()`.
* **REST API Rate Limiting:** Verified clean. `server.ts:16-35` enforces a 120-request/min sliding window per IP on `/api/` endpoints to protect against client request thrashing.
