# Predictions Tab — Full E2E Forensic Audit

### 1. Summary

A comprehensive, read-only forensic audit was conducted across the **Market → Predictions** tab ([PredictionChartView.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/PredictionChartView.tsx)), covering the Scenario Projection Canvas ([ScenarioProjectionCanvas.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/chart/ScenarioProjectionCanvas.tsx)), Projection Overlay ([ScenarioProjectionOverlay.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/chart/ScenarioProjectionOverlay.tsx)), Horizon Calibration Adapter ([canonicalIntelligenceAdapter.ts](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalIntelligenceAdapter.ts)), and the underlying backend prediction subsystem ([prediction_engine.py](file:///p:/ArdhaMind-Local/ardhamind/staging/src/prediction/prediction_engine.py), `direction/`, `magnitude/`, `confidence/`, `history/`). The investigation revealed **3 Critical**, **5 High**, **4 Medium**, and **4 Low** severity defects.

Most critically, the Predictions tab is **entirely disconnected** from the sophisticated Python prediction pipeline (`PredictionEngine`, `DirectionPredictionEngine`, `MagnitudePredictionEngine`, `SimilarSessionFinder`). Not a single forecast or metric displayed on this tab originates from backend machine learning or statistical model inference. Instead, the frontend renders hardcoded telemetry: fixed scenario probabilities (65% / 35%), invariant model conviction scores (68, 72, 74, 78 / 100), hardcoded factor confluence weights (35%, 25%, 25%, 15%), static magnitude distributions (12%, 68%, 20%), and fabricated historical analogs from July and August 2026. Furthermore, across multiple time horizons, the forward projection targets are hardcoded to the exact price level of `24,066.56` regardless of current spot price, the chart x-axis permanently displays `"14:00 (LIVE)"` 24 hours a day, and the system continues to project active "live" trading cones when markets are closed.

| Severity | Finding Count | Primary Impact Area |
| :--- | :---: | :--- |
| **Critical** | **3** | Complete disconnection from backend model inference, hardcoded scenario probabilities & offsets, fabricated historical analog track records |
| **High** | **5** | Invariant conviction scores masquerading as dynamic inference, fixed target price (24,066.56) across spot moves, hardcoded "14:00 (LIVE)" axis tick, off-market session continuation without guards, complete absence of generation timestamps |
| **Medium** | **4** | Semantic inversion (target below spot labeled "Bullish Continuation"), hardcoded factor confluence & magnitude mock residue, unplumbed backend prediction engine, duplicate calibration evaluation |
| **Low** | **4** | Dead variable `isLiveTape`, bearish invalidation colored positive green, arbitrary fallback candle volume (800,000), fallback candle timestamp ("14:00") |
| **Total** | **16** | |

---

### Complete Data Inventory & Source Mapping

Every prediction, probability, target, and metric displayed on the Predictions tab is enumerated below with its underlying source, computation method, and data pipeline:

| Field / Metric Displayed | UI Location | Underlying Source / Field | Computation / Sourcing Method | Reality: Model vs Hardcoded |
| :--- | :--- | :--- | :--- | :--- |
| **Active Spot Reference** | Chart Canvas & Header | `authState.spot` | Kite WebSocket (Token `256265`) | **Real Live Ticking Price** |
| **Anchor VWAP & Levels** | Chart Canvas & Guides | `authState.vwap`, `dayHigh`, `dayLow` | Kite Tick Aggregate / Price Structure | **Real Session Metrics** |
| **5m Candlestick History** | Chart Canvas Base | `envelope.candles["5m"]` | Server Candle Stream (slice of 16) | **Real Market Data** |
| **Horizon Calibration Badge**| Card 1 & Canvas Toolbar | `calib.badge` | Static switch-case lookup per timeframe | **Hardcoded String** |
| **Path 1 Probability (65%)** | Card 1 (Base Scenario) | Hardcoded in JSX | `Path 1: VWAP Pullback Hold (65%)` | **COMPLETELY FABRICATED** |
| **Path 1 Target Zone** | Card 1 (Base Scenario) | `calib.targetRange` OR `spot + 25` | Hardcoded arithmetic offset (`+25 to +60`) | **Synthetic Arithmetic** |
| **Path 1 Hard Invalidation** | Card 1 (Base Scenario) | `calib.invalidation` OR `vwap` | Dynamic VWAP fallback OR `spot - 35` | **Mixed / Synthetic Offset** |
| **Path 2 Probability (35%)** | Card 1 (Alt Scenario) | Hardcoded in JSX | `Path 2: Mean Breakdown (35%)` | **COMPLETELY FABRICATED** |
| **Path 2 Target Zone** | Card 1 (Alt Scenario) | `authState.dayLow` OR `spot - 55` | Session Low OR Hardcoded offset (`spot - 55`)| **Mixed / Synthetic Offset** |
| **Path 2 Hard Invalidation** | Card 1 (Alt Scenario) | `authState.dayHigh` OR `spot + 35`| Day High OR Hardcoded offset (`spot + 35`) | **Mixed / Synthetic Offset** |
| **Model Conviction Score** | Header / Calibration | `calib.conviction` | Static lookup: `68`, `72`, `74`, `78 / 100` | **COMPLETELY HARDCODED** |
| **Primary Target Vector** | Canvas Corridor & Tag | `calib.primaryTarget` | Hardcoded `24066.56` for 5m, 15m, 1D | **STATIC HARDCODED PRICE** |
| **Alternate Target Vector** | Canvas Corridor & Tag | `calib.alternateTarget` | Dynamic `vwap` or `low` | **Arithmetic Level Fallback**|
| **Volatility Envelope (±2σ)**| Canvas Polygons & Tags | `calib.envelopeTop/Bottom` | `high + 25` / `low - 15` | **Heuristic Arithmetic Offset**|
| **Factor Confluence Weights**| Card 2 (Confluence Stack)| Hardcoded in JSX | `Price: 35%`, `Deriv: 25%`, `Br: 25%`, `Mac: 15%`| **COMPLETELY HARDCODED** |
| **Magnitude Distribution** | Card 3 (1-SD Magnitude) | Hardcoded in JSX | `Comp: 12%`, `Norm: 68%`, `Exp: 20%` | **COMPLETELY HARDCODED** |
| **Historical Analog 1** | Card 4 (Analog Matches) | Hardcoded in JSX | `14 Jul 2026: 91% Fit, +18.4 pts drift` | **COMPLETELY FABRICATED** |
| **Historical Analog 2** | Card 4 (Analog Matches) | Hardcoded in JSX | `02 Aug 2026: 86% Fit, +24.1 pts drift` | **COMPLETELY FABRICATED** |
| **Chart X-Axis "LIVE" Tick** | Canvas X-Axis Footer | `calib.ticks[11]` | Static string `{ text: "14:00 (LIVE)" }` | **STATIC HARDCODED LABEL** |
| **Backend Prediction Snapshot**| **UNCONNECTED** | `PredictionEngine.generate_prediction`| Python ML & Statistical Inference Subsystem| **NEVER SENT TO CLIENT** |

---

### 2. Forensic Findings by Dimension (1–13)

```
================================================================================
DIMENSION 1: PREDICTION SOURCE & DATA FIDELITY
================================================================================
```

#### Finding 1.1: Complete Disconnection from Backend Prediction Engine & Full Fabrication of Predictive Telemetry
* **File & Lines:** [src/frontend/components/intelligence/PredictionChartView.tsx:30-49](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/PredictionChartView.tsx#L30-L49), [src/application/workstation_state_service.py:1-3822](file:///p:/ArdhaMind-Local/ardhamind/staging/src/application/workstation_state_service.py)
* **Actual Code:**
  In `PredictionChartView.tsx`:
  ```tsx
  export const PredictionChartView: React.FC<PredictionChartViewProps> = ({ vm, canonicalState }) => {
    ...
    const { sessionIdentity, sessionPhase, intelligenceMode, envelope } = canonicalContext || {};
    const authState = resolveAuthoritativeMarketState(envelope);
    const activeSpot = authState.spot ?? (envelope?.price_structure?.last_price != null ? Number(envelope.price_structure.last_price) : null);

    // Dynamic Horizon Calibration Metrics
    const calib = useMemo(() => {
      return getHorizonCalibration(activeTimeframe, 1, activeSpot ?? undefined, authState.vwap ?? undefined, authState.dayHigh ?? undefined, authState.dayLow ?? undefined, authState.prevClose ?? undefined, authState.atr14 ?? undefined);
    }, [activeTimeframe, activeSpot, authState]);
  ```
* **Why it is wrong:** The codebase possesses a fully developed, deterministic prediction engine in `src/prediction/` (`PredictionEngine.generate_prediction`, `DirectionPredictionEngine`, `MagnitudePredictionEngine`, `PredictionConfidenceEngine`, and `SimilarSessionFinder`). However, `workstation_state_service.py` **never calls `PredictionEngine`** and **never packs any prediction snapshot into the canonical state envelope**. As a result, the frontend does not receive or consume any backend model output; it synthesizes the entire prediction interface through client-side hardcoded templates.
* **Severity:** **Critical**

#### Finding 1.2: Hardcoded Scenario Probabilities and Arbitrary Arithmetic Offsets
* **File & Lines:** [src/frontend/components/intelligence/PredictionChartView.tsx:93-128](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/PredictionChartView.tsx#L93-L128)
* **Actual Code:**
  ```tsx
  {/* Path 1: Base Trajectory (65%) */}
  <div className="p-1.5 rounded bg-emerald-950/25 border border-emerald-500/30 space-y-0.5 text-[9.5px]">
    <div className="flex justify-between items-center">
      <strong className="text-emerald-400">Path 1: VWAP Pullback Hold (65%)</strong>
      <span className="text-[8px] px-1 py-0.2 rounded bg-emerald-500/20 text-emerald-300">BASE</span>
    </div>
    <div className="flex justify-between text-neutral-300">
      <span>Target Zone:</span>
      <strong className="text-emerald-300">{calib.targetRange || (activeSpot != null ? `${formatNumber(activeSpot + 25, 2)} – ${formatNumber(activeSpot + 60, 2)}` : "—")}</strong>
    </div>
    <div className="flex justify-between text-neutral-400 text-[8.5px]">
      <span>Hard Invalidation:</span>
      <strong className="text-rose-400">{calib.invalidation || (authState.vwap != null ? formatNumber(authState.vwap, 2) : (activeSpot != null ? formatNumber(activeSpot - 35, 2) : "—"))}</strong>
    </div>
  </div>

  {/* Path 2: Alternate Trajectory (35%) */}
  <div className="p-1.5 rounded bg-rose-950/20 border border-rose-500/30 space-y-0.5 text-[9.5px]">
    <div className="flex justify-between items-center">
      <strong className="text-rose-300">Path 2: Mean Breakdown (35%)</strong>
      <span className="text-[8px] px-1 py-0.2 rounded bg-rose-500/20 text-rose-300">ALT</span>
    </div>
    <div className="flex justify-between text-neutral-300">
      <span>Target Zone:</span>
      <strong className="text-rose-300">{authState.dayLow != null ? `${formatNumber(authState.dayLow, 2)} (Session Low)` : (activeSpot != null ? `${formatNumber(activeSpot - 55, 2)} (Floor)` : "—")}</strong>
    </div>
    <div className="flex justify-between text-neutral-400 text-[8.5px]">
      <span>Hard Invalidation:</span>
      <strong className="text-emerald-400">{authState.dayHigh != null ? `> ${formatNumber(authState.dayHigh, 2)} (Day High)` : (activeSpot != null ? `> ${formatNumber(activeSpot + 35, 2)}` : "—")}</strong>
    </div>
  </div>
  ```
* **Why it is wrong:** The scenario probabilities "65%" and "35%" are hardcoded static strings in the JSX. They do not change whether the market is trending strongly, compressing, breaking down, or closed. The target and invalidation price ranges fall back to ungrounded arithmetic offsets (`spot + 25 to +60`, `spot - 35`, `spot - 55`, `spot + 35`), directly violating the production safety invariant against arbitrary price offsets.
* **Severity:** **Critical**

#### Finding 1.3: Invariant Model Conviction Scores Masquerading as Dynamic Inference
* **File & Lines:** [src/frontend/utils/canonicalIntelligenceAdapter.ts:1478, 1520, 1563, 1608, 1667, 1709, 1752, 1796](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalIntelligenceAdapter.ts#L1478-L1796)
* **Actual Code:**
  ```typescript
  case "1m":
    return { ... conviction: `68 / 100 ${convSuffix}` };
  case "5m":
    return { ... conviction: `72 / 100 ${convSuffix}` };
  case "1D":
    return { ... conviction: `78 / 100 ${convSuffix}` };
  case "15m":
  default:
    return { ... conviction: `74 / 100 ${convSuffix}` };
  ```
* **Why it is wrong:** The conviction scores (`68/100`, `72/100`, `74/100`, `78/100`) are static integers hardcoded into a switch-case statement. Regardless of market volatility, trend strength, or data completeness, the conviction score for any given timeframe never changes by even a single point.
* **Severity:** **High**

```
================================================================================
DIMENSION 2: REAL-TIME / REFRESH PIPELINE
================================================================================
```

#### Finding 2.1: Static Target Level 24,066.56 Pinned Across Spot Fluctuations
* **File & Lines:** [src/frontend/utils/canonicalIntelligenceAdapter.ts:1716, 1773, 1803, 1817](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalIntelligenceAdapter.ts#L1716-L1817)
* **Actual Code:**
  ```typescript
  // 5m Horizon (dynamic branch):
  primaryTarget: 24066.56,
  ...
  // 1D Horizon (dynamic branch):
  { price: 24066.56, label: "24,066.56 (Breakout Pivot)", ... },
  ...
  // 15m Horizon (dynamic branch):
  targetRange: `${formatNumber(24066.56, 2)} – ${formatNumber(high, 2)}`,
  primaryTarget: 24066.56,
  { price: 24066.56, label: "24,066.56 (Breakout Pivot / Target 1)", ... },
  ```
* **Why it is wrong:** Even in the dynamic code branch where live `spotVal` is passed, `primaryTarget` is hardcoded to the constant `24066.56`. If NIFTY trades at 23,800 or 25,000, the primary target line on the chart remains pinned to `24,066.56`, anchoring the forward projection corridor to an irrelevant historical price.
* **Severity:** **High**

#### Finding 2.2: Permanent "14:00 (LIVE)" Time-Axis Label Hardcoded on Candlestick Engine
* **File & Lines:** [src/frontend/utils/canonicalIntelligenceAdapter.ts:1506, 1549, 1642, 1695, 1738, 1827](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalIntelligenceAdapter.ts#L1506-L1827)
* **Actual Code:**
  ```typescript
  ticks: [
    { text: "09:15", slot: 0, anchor: "start" },
    { text: "10:30", slot: 3.5, anchor: "middle" },
    { text: "12:00", slot: 7, anchor: "middle" },
    { text: "13:30", slot: 9.5, anchor: "middle" },
    { text: "14:00 (LIVE)", slot: 11, anchor: "middle", isLive: true },
    { text: "15:00", slot: 16, anchor: "middle" },
    { text: "15:30 (EOD)", slot: 20, anchor: "end" },
  ],
  ```
* **Why it is wrong:** The horizontal time axis on the chart contains the literal string `"14:00 (LIVE)"`. Whether a trader views the workstation at 09:30 AM, 11:45 AM, 15:15 PM, or at midnight, the chart timeline asserts that the current live time is 14:00.
* **Severity:** **High**

```
================================================================================
DIMENSION 3: CALCULATED / DERIVED STATS
================================================================================
```

#### Finding 3.1: Fictitious Historical Analogs Presented as Quantitative Research Matches
* **File & Lines:** [src/frontend/components/intelligence/PredictionChartView.tsx:213-244](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/PredictionChartView.tsx#L213-L244)
* **Actual Code:**
  ```tsx
  {/* CARD 4: HISTORICAL ANALOG MATCHES */}
  <div className="bg-neutral-900/60 border border-neutral-800 rounded p-2.5 text-xs font-mono space-y-1.5 flex-1">
    <div className="flex items-center justify-between border-b border-neutral-800 pb-1">
      <span className="text-[10px] font-bold text-neutral-100 uppercase flex items-center gap-1">
        <Sparkles className="w-3 h-3 text-amber-400" />
        4. HISTORICAL ANALOGS
      </span>
      <span className="text-[7.5px] font-bold px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
        OBSERVATIONAL (n=2)
      </span>
    </div>

    <div className="space-y-1.5 text-[9.5px]">
      <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 space-y-0.5">
        <div className="flex justify-between items-center">
          <span className="font-bold text-neutral-200">14 Jul 2026</span>
          <span className="text-emerald-400 font-bold">91% Session Fit</span>
        </div>
        <span className="text-neutral-400 block text-[8.5px]">Regime: Bullish Gap + IT Expansion</span>
        <span className="text-cyan-300 block text-[8px]">14:00 ──► 15:30 Drift: +18.4 pts</span>
      </div>

      <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 space-y-0.5">
        <div className="flex justify-between items-center">
          <span className="font-bold text-neutral-200">02 Aug 2026</span>
          <span className="text-cyan-300 font-bold">86% Session Fit</span>
        </div>
        <span className="text-neutral-400 block text-[8.5px]">Regime: VWAP Pullback</span>
        <span className="text-cyan-300 block text-[8px]">14:00 ──► 15:30 Drift: +24.1 pts</span>
      </div>
    </div>
  </div>
  ```
* **Why it is wrong:** The historical analogs ("14 Jul 2026", "91% Session Fit", "+18.4 pts drift" and "02 Aug 2026", "86% Session Fit", "+24.1 pts drift") are hardcoded static JSX elements. They do not query historical market data, compute similarity metrics, or verify historical session returns. They present fabricated statistical track records to the trader.
* **Severity:** **Critical**

```
================================================================================
DIMENSION 4: MARKET STATE / SESSION HANDLING
================================================================================
```

#### Finding 4.1: Inactive Market State Violation: Live Projections Rendered Off-Hours Without Guards
* **File & Lines:** [src/frontend/components/intelligence/PredictionChartView.tsx:41](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/PredictionChartView.tsx#L41), [src/frontend/components/canonical/chart/ScenarioProjectionCanvas.tsx:87](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/chart/ScenarioProjectionCanvas.tsx#L87)
* **Actual Code:**
  ```tsx
  // PredictionChartView.tsx:
  const { sessionIdentity, sessionPhase, intelligenceMode, envelope } = canonicalContext || {};
  // sessionPhase is extracted but NEVER used to gate or label the predictions

  // ScenarioProjectionCanvas.tsx:
  const isLiveTape = sessionPhase === "LIVE" && !isReplayMode;
  // isLiveTape is computed but NEVER referenced anywhere in the component
  ```
* **Why it is wrong:** Outside market hours (evenings, weekends, holidays), the Predictions tab continues to render active forward projection corridors fanning out to hypothetical targets, showing "65% Base Probability" and "Normal Trend [ACTIVE REGIME]". There is no indicator stating that the market is closed or that intraday projections are inactive.
* **Severity:** **High**

```
================================================================================
DIMENSION 5: TIMESTAMP & TIMEZONE
================================================================================
```

#### Finding 5.1: Complete Absence of Prediction Generation Timestamps and Model Provenance Metadata
* **File & Lines:** [src/frontend/components/intelligence/PredictionChartView.tsx:1-253](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/PredictionChartView.tsx#L1-L253)
* **Actual Code:**
  The component contains no `observed_at`, `created_at`, or inference timestamp anywhere in its DOM tree.
* **Why it is wrong:** A trader viewing the page cannot determine when the prediction was generated, what snapshot revision it was based on, or what model version produced it. While the backend `PredictionRecord` model defines `created_at`, `reference_timestamp`, `model_version`, and `input_state_revision`, none of these fields exist in the frontend view.
* **Severity:** **High**

```
================================================================================
DIMENSION 6: CROSS-TAB CONSISTENCY
================================================================================
```

#### Finding 6.1: Semantic Inversion: Target Level Below Spot Labeled as "Bullish Continuation"
* **File & Lines:** [src/frontend/utils/canonicalIntelligenceAdapter.ts:1793-1803](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalIntelligenceAdapter.ts#L1793-L1803)
* **Actual Code:**
  ```typescript
  case "15m":
  default:
    return {
      horizon: "15m",
      ...
      bias: "BULLISH CONTINUATION",
      targetRange: `${formatNumber(24066.56, 2)} – ${formatNumber(high, 2)}`,
      primaryTarget: 24066.56,
      ...
    };
  ```
* **Why it is wrong:** When NIFTY spot on the NIFTY Live tab trades at `24,175.65`, the Predictions tab sets `primaryTarget` to `24,066.56` (109 points below the current spot price) while categorizing the bias as `"BULLISH CONTINUATION"`. A target below the spot price contradicts a bullish thesis.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 7: FORMATTING & SIGN/COLOR LOGIC
================================================================================
```

#### Finding 7.1: Bearish Breakdown Invalidation Level Colored in Positive Emerald Green
* **File & Lines:** [src/frontend/components/intelligence/PredictionChartView.tsx:119-121](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/PredictionChartView.tsx#L119-L121)
* **Actual Code:**
  ```tsx
  <div className="flex justify-between text-neutral-400 text-[8.5px]">
    <span>Hard Invalidation:</span>
    <strong className="text-emerald-400">{authState.dayHigh != null ? `> ${formatNumber(authState.dayHigh, 2)} (Day High)` : ...}</strong>
  </div>
  ```
* **Why it is wrong:** In Path 2 ("Path 2: Mean Breakdown (35%)"), the invalidation level (`> Day High`) represents failure of the short/bearish thesis. However, the invalidation price is styled with `text-emerald-400` (positive green), visually confusing failure of a short thesis with a favorable target.
* **Severity:** **Low**

```
================================================================================
DIMENSION 8: ERROR HANDLING & FALLBACKS
================================================================================
```

#### Finding 8.1: Arbitrary Fallback Candle Volume of 800,000
* **File & Lines:** [src/frontend/components/canonical/chart/ScenarioProjectionCanvas.tsx:178](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/chart/ScenarioProjectionCanvas.tsx#L178)
* **Actual Code:**
  ```typescript
  volume: c.volume || 800000,
  ```
* **Why it is wrong:** If volume data is missing for a 5-minute candlestick, the chart substitutes `800,000` rather than `null` or `0`, fabricating volume histogram bars.
* **Severity:** **Low**

```
================================================================================
DIMENSION 9: LOADING STATES
```

* **Audit Result:** Inspected for stuck loading spinners and unhandled async transitions. Because the component makes zero asynchronous requests and generates everything synchronously from client memory, there are no stuck loading spinners. When `activeSpot` is null, the empty state ("Awaiting session projection stream") renders cleanly. Verified Clean.

```
================================================================================
DIMENSION 10: UI/LAYOUT & RESPONSIVE INTEGRITY
```

* **Audit Result:** Inspected layout responsiveness and fullscreen maximize mode. When maximized (`isMaximized = true`), the right column unmounts (`{!isMaximized && ...}`) and the canvas expands to `w-screen h-screen` with a functional Escape key listener (`ScenarioProjectionCanvas.tsx:110-118`). On viewports `< lg`, the layout stacks into a single column cleanly without horizontal clipping. Verified Clean.

```
================================================================================
DIMENSION 11: DEAD CODE & MOCK-DATA RESIDUE
```

#### Finding 11.1: Hardcoded Factor Confluence and Magnitude Distributions Left as Static Mock Residue
* **File & Lines:** [src/frontend/components/intelligence/PredictionChartView.tsx:130-211](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/PredictionChartView.tsx#L130-L211)
* **Actual Code:**
  ```tsx
  {/* Card 2: Factor Confluence */}
  <span className="text-neutral-400">Price Action &amp; Structure</span>
  <strong className="text-emerald-400">35%</strong>
  ...
  <span className="text-neutral-400">Derivatives &amp; Options Flow</span>
  <strong className="text-emerald-400">25%</strong>
  ...
  <span className="text-neutral-400">Market Breadth &amp; Internals</span>
  <strong className="text-teal-300">25%</strong>
  ...
  <span className="text-neutral-400">Global Macro Backdrop</span>
  <strong className="text-cyan-300">15%</strong>

  {/* Card 3: Magnitude Distribution */}
  <span className="text-neutral-400">Compression (&lt;80 pts)</span>
  <strong className="text-neutral-300">12%</strong>
  ...
  <span className="text-emerald-300 font-bold">Normal Trend (80–120 pts)</span>
  <strong className="text-emerald-400 font-bold">68% [ACTIVE REGIME]</strong>
  ...
  <span className="text-neutral-400">Expansion (&gt;120 pts)</span>
  <strong className="text-neutral-300">20%</strong>
  ```
* **Why it is wrong:** The weights for factor confluence (35%, 25%, 25%, 15%) and the magnitude probabilities (12%, 68%, 20%) are hardcoded HTML markup with hardcoded CSS progress bar widths (`style={{ width: "35%" }}`). They do not reflect current market regime or volatility conditions.
* **Severity:** **Medium**

#### Finding 11.2: Dead Variable `isLiveTape` in Scenario Projection Canvas
* **File & Lines:** [src/frontend/components/canonical/chart/ScenarioProjectionCanvas.tsx:87](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/chart/ScenarioProjectionCanvas.tsx#L87)
* **Actual Code:**
  ```typescript
  const isLiveTape = sessionPhase === "LIVE" && !isReplayMode;
  ```
* **Why it is wrong:** `isLiveTape` is declared but never read or referenced in the file.
* **Severity:** **Low**

#### Finding 11.3: Unconnected Backend Prediction Engine Pipeline Left as Dead Code
* **File & Lines:** [src/prediction/prediction_engine.py:1-110](file:///p:/ArdhaMind-Local/ardhamind/staging/src/prediction/prediction_engine.py#L1-L110)
* **Actual Code:**
  An entire predictive intelligence engine consisting of 11 Python modules exists in `src/prediction/`, yet no production service or endpoint invokes it to populate the live workstation state.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 12: PERFORMANCE & MEMORY
```

#### Finding 12.1: Duplicate Calculation of `getHorizonCalibration` in View and Canvas Components
* **File & Lines:** [src/frontend/components/intelligence/PredictionChartView.tsx:47](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/PredictionChartView.tsx#L47), [src/frontend/components/canonical/chart/ScenarioProjectionCanvas.tsx:143](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/chart/ScenarioProjectionCanvas.tsx#L143)
* **Actual Code:**
  Both `PredictionChartView` and its child `ScenarioProjectionCanvas` independently invoke `getHorizonCalibration(activeTimeframe, ...)` on every tick, performing duplicate calculations.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 13: CONSOLE & NETWORK HYGIENE
```

* **Audit Result:** Inspected for network spam, unhandled promise rejections, and credential leakage. No network hygiene defects, console errors, or secret exposures identified. Verified Clean.

---

### 3. Verified Clean

The following items were explicitly audited and verified to be clean of defects:

* **Read-Only Safety Invariant:** Verified clean. The Predictions tab contains zero order placement, paper trading, or broker execution controls.
* **Live Spot Reference Synchronization:** Verified clean. `activeSpot` correctly binds to `authState.spot` and updates synchronously with incoming NIFTY ticks.
* **Escape Key Fullscreen Listener Cleanup:** Verified clean. `ScenarioProjectionCanvas.tsx:110-118` attaches the `keydown` listener when maximized and cleanly removes it on unmount.
* **DOM Ghosting Protection on Maximize:** Verified clean. The right column telemetry cards are unmounted (`{!isMaximized && ...}`) when maximized, avoiding DOM overlap.
* **Zero Credential Exposure:** Verified clean. No Kite API keys, access tokens, or backend secrets are leaked into client payloads or DOM attributes.
* **Zero Console Spam:** Verified clean. The component executes without unhandled exceptions or noisy console logging.
