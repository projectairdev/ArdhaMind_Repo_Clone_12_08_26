# Market Intelligence Tab — Full E2E Forensic Audit

### 1. Summary

A comprehensive, read-only forensic audit was conducted across the **Market Intelligence** workspace ([MarketIntelligenceWorkspace.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/MarketIntelligenceWorkspace.tsx)) and all 3 of its session-phase strategy cockpits:
1. **Morning Plan View** ([MorningPlanView.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/MorningPlanView.tsx) — Pre-Market 08:00–09:15 IST)
2. **Live Guide View** ([LiveGuideView.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/LiveGuideView.tsx) — Intraday 09:15–15:30 IST)
3. **Tomorrow Plan View** ([TomorrowPlanView.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/TomorrowPlanView.tsx) — Post-Market 15:30+ IST)

Additionally, the supporting quote resolver ([canonicalQuotes.ts](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/utils/canonicalQuotes.ts)) and orphaned intelligence modules were thoroughly investigated.

The audit revealed **3 Critical**, **4 High**, **4 Medium**, and **4 Low** severity defects. While the workspace correctly executes read-only presentation and features an intuitive multi-phase preview architecture, the diagnostic analysis and forward-planning recommendations are dominated by hardcoded values, canned boilerplate commentary presented as algorithmic post-mortems, and artificial arithmetic trade generation. Most critically:
- In `TomorrowPlanView.tsx`, the "Prediction Accuracy Audit" and "Diagnostic Breakdown" panels present hardcoded canned commentary strings and a fixed "9.4 / 10 Model Calibration Score" as if it were an authoritative algorithmic evaluation of the day's predictions.
- In `MorningPlanView.tsx`, the entire "Opening Range If-Then Decision Tree" hardcodes 12 exact strike/price levels (e.g. `24,077.55`, `24,066.56`, `24,143.15`, `23,952.55`) directly into JSX markup, regardless of what the real expected open or previous close actually is.
- In `LiveGuideView.tsx`, when broker candidate option trades are unmapped, the component synthesizes a complete derivative ticket with an arbitrary price formula (`spot * 0.0075`), hardcoded stop-loss/target multipliers (`0.65x`, `1.5x`, `2.2x`), and hardcoded Greek constants (Delta `0.52`, Theta `-14.2`, IV `12.5%`, Vega `8.4`).
- Global cues (GIFT Nifty, Nasdaq, Brent Crude, USD/INR) omit observation timestamps, market session open/closed states, and foreign timezone mappings.

| Severity | Finding Count | Primary Impact Area |
| :--- | :---: | :--- |
| **Critical** | **3** | Canned post-mortem commentary & fake calibration score, hardcoded price levels in morning decision tree, synthetic option trade ticket generator |
| **High** | **4** | Hardcoded reliability badges (76/100, "4/5 Supportive", "5/5 Confirmed"), static carry-forward pivots & swing playbook confidences, missing timestamps/timezone on global cues, cross-tab fallback discrepancies |
| **Medium** | **4** | Arbitrary ATR-based price offsets for R1/R2/S1/S2, orphaned dead code in intelligence directory, missing off-market awareness in morning view, static sector leadership boilerplate |
| **Low** | **4** | Invariant ATR fallback (135.10 pts), disconnected model confidence field, static 1-SD day range (110–135 pts), hardcoded "0 False Triggers" post-mortem text |
| **Total** | **15** | |

---

### Complete Data Inventory & Source Mapping

Every intelligence widget, metric, and commentary field across all 3 strategy views is enumerated below:

| Field / Metric Displayed | View / Location | Underlying Source / Field | Computation / Sourcing Method | Reality: Live vs Hardcoded |
| :--- | :--- | :--- | :--- | :--- |
| **Expected Open Auction** | Morning / Hero | `price_structure.open` | Kite Pre-Open Match Tick | Dynamic Pre-Open Data |
| **Expected Bias Badge** | Morning / Hero | Hardcoded in JSX | `● EXPECTED BIAS: BULLISH GAP-UP` | **COMPLETELY HARDCODED** |
| **Pre-Market Confidence** | Morning / Hero | Hardcoded in JSX | `CONFIDENCE: 76/100 · OBSERVATIONAL (n=1)`| **COMPLETELY HARDCODED** |
| **Expected 1-SD Day Range** | Morning / Hero | Hardcoded in JSX | `Expected 1-SD Day Range: 110 – 135 pts` | **COMPLETELY HARDCODED** |
| **Path A Primary (65% Prob)**| Morning / Tree | Hardcoded in JSX | `Trigger: Hold above 24,077.55 Open...` | **HARDCODED PRICES IN JSX** |
| **Path B Alternate (35% Prob)**| Morning / Tree | Hardcoded in JSX | `Trigger: Rejection at 24,066.56 Pivot...` | **HARDCODED PRICES IN JSX** |
| **Global Macro Alignment** | Morning / Alignment | Hardcoded in JSX | `4/5 SUPPORTIVE` | **COMPLETELY HARDCODED** |
| **GIFT NIFTY Quote** | Morning / Alignment | Yahoo Scraper / `macro_quotes` | `getCanonicalQuote(rawQuotes, "GIFT_NIFTY")`| Periodic Scrape (300s) |
| **US Tech (Nasdaq) Quote** | Morning / Alignment | Yahoo Scraper / `macro_quotes` | `getCanonicalQuote(rawQuotes, "NASDAQ")` | Periodic Scrape (300s) |
| **Brent Crude Oil Quote** | Morning / Alignment | Yahoo Scraper / `macro_quotes` | `getCanonicalQuote(rawQuotes, "BRENT_CRUDE")`| Periodic Scrape (300s) |
| **USD / INR Quote** | Morning / Alignment | Yahoo Scraper / `macro_quotes` | `getCanonicalQuote(rawQuotes, "USD_INR")` | Periodic Scrape (300s) |
| **Overnight Risk Sentiment** | Morning / Alignment | `macro_intelligence.sentiment` | Macro Provider Classifier OR Fallback | Dynamic / Fallback |
| **Discipline Checklist** | Morning / Checklist | Local React State | 4 Interactive Checklist Checkboxes | User-Toggled Interactive |
| **Intraday Directive & Trigger**| Live / Hero | Dynamic from `vwapRegime` | Real-time Spot vs VWAP Hysteresis | Dynamic Rule-Based Text |
| **Derivative Candidate Strike**| Live / Advisory | `envelope.decision.strike_candidates`| Decision Engine OR `round(spot/50)*50` | Dynamic / Fallback |
| **Candidate LTP** | Live / Advisory | `candObj.ltp` OR **`spot * 0.0075`** | Broker Quote OR **Synthetic 0.75% Formula**| **SYNTHETIC FORMULA FALLBACK**|
| **Candidate Invalidation / SL**| Live / Advisory | `candObj.stop_loss` OR **`LTP * 0.65`**| Decision Engine OR **Synthetic 0.65x Multiplier**| **SYNTHETIC FORMULA FALLBACK**|
| **Candidate Target 1 & 2** | Live / Advisory | `candObj.target1/2` OR **`LTP * 1.5/2.2`**| Decision Engine OR **Synthetic Multipliers** | **SYNTHETIC FORMULA FALLBACK**|
| **Candidate Greeks (Δ, θ, IV, ν)**| Live / Advisory | `candObj.delta/theta` OR **Defaults** | Greeks Solver OR **Hardcoded (0.52, -14.2, 12.5, 8.4)**| **HARDCODED GREEKS FALLBACK** |
| **Vertical Price Funnel** | Live / Funnel | `r2Level`, `r1Level`, `spot`, `vwap`, `s1`| Key Structural Levels OR **`spot ± atr * 0.75`**| Dynamic / Heuristic ATR |
| **5-Pillar Confluence Proof**| Live / Proof | Breadth, Spot vs VWAP, VIX | Real State + **Hardcoded Boilerplate** | Mixed Real / Boilerplate |
| **Ranked Strategy Playbook** | Live / Playbook | Dynamic from `vwapRegime` | 3 Regimes (Below, Above, Testing Mean) | Dynamic Strategy Rules |
| **Settlement Tape Metrics** | Tomorrow / Hero | `settled_session.close`, `high`, `low`| NSE EOD Cash Settlement Envelope | Dynamic Real Settlement |
| **Daily ATR Utilization** | Tomorrow / Hero | Computed: `(range / expectedAtr)*100` | Math Ratio of Session Range to ATR | Computed Real Data |
| **Directional Accuracy Audit**| Tomorrow / Audit | Hardcoded in JSX | `BEARISH DRIFT / DISTRIBUTION ── HIT` | **COMPLETELY HARDCODED** |
| **Model Calibration Score** | Tomorrow / Audit | Hardcoded in JSX | `9.4 / 10 · OBSERVATIONAL (n=1)` | **COMPLETELY HARDCODED** |
| **What Worked vs Failed Text**| Tomorrow / Diagnostic | Hardcoded in JSX | Canned Explanatory Commentary Templates | **CANNED BOILERPLATE TEXT** |
| **Carry-Forward Pivots** | Tomorrow / Roadmap | Hardcoded in JSX | `Immediate Breakout Pivot: 24,066.56` | **HARDCODED PRICES IN JSX** |
| **Swing Strategy Suitability**| Tomorrow / Roadmap | Hardcoded in JSX | 3 Strategies (75% Conf, 62% Conf, 40% Conf)| **COMPLETELY HARDCODED** |

---

### 2. Forensic Findings by Dimension (1–13)

```
================================================================================
DIMENSION 1: WIDGET INVENTORY & DATA SOURCE FIDELITY
================================================================================
```

#### Finding 1.1: Canned Boilerplate Commentary & Hardcoded Model Performance Metrics Masquerading as AI Post-Mortem Analysis
* **File & Lines:** [src/frontend/components/intelligence/TomorrowPlanView.tsx:161-213](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/TomorrowPlanView.tsx#L161-L213)
* **Actual Code:**
  ```tsx
  {/* Left Pane: PREDICTION OUTCOME & AUDIT SCORECARD */}
  <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
    <span className="text-neutral-400">Directional Forecast</span>
    <strong className="text-emerald-400">BEARISH DRIFT / DISTRIBUTION ── HIT (ACCURATE)</strong>
  </div>
  <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
    <span className="text-neutral-400">Range Magnitude Accuracy</span>
    <strong className="text-emerald-400">{formatNumber(sessionRange, 2)} pts vs {formatNumber(expectedAtr, 2)} pts (100.0% Consumed)</strong>
  </div>
  <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
    <span className="text-neutral-400">Invalidation Discipline</span>
    <strong className="text-emerald-400">{formatNumber(sessionLow, 2)} Low Held Firmly (0 False Triggers)</strong>
  </div>
  <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
    <span className="text-neutral-400">Model Calibration Score</span>
    <strong className="text-neutral-100 text-[10px]">9.4 / 10 · OBSERVATIONAL (n=1 session fit)</strong>
  </div>

  {/* Right Pane: WHAT WORKED VS WHAT FAILED (DIAGNOSTIC) */}
  <div className="text-neutral-300 leading-tight">
    • <strong className="text-neutral-200">Anchor VWAP Rebound: </strong>Bounce off {formatNumber(priorVwap, 2)} provided stable intraday pricing reference.
  </div>
  <div className="text-neutral-300 leading-tight">
    • <strong className="text-neutral-200">Put Wall Floor Defense: </strong>Maintenance above {formatNumber(sessionLow, 2)} session low held firmly.
  </div>
  <div className="text-neutral-300 leading-tight">
    • <strong className="text-neutral-200">Range Expansion: </strong>Full 100% ATR consumption achieved ({formatNumber(sessionRange, 2)} pts expansion).
  </div>
  <div className="text-neutral-300 leading-tight">
    • <strong className="text-neutral-200">Session High Resistance: </strong>Concentrated supply capped momentum at {formatNumber(sessionHigh, 2)}.
  </div>
  ```
* **Why it is wrong:** The post-market audit scorecard claims that the directional forecast was "BEARISH DRIFT / DISTRIBUTION ── HIT (ACCURATE)" and awards an authoritative "9.4 / 10 Model Calibration Score" via hardcoded static strings. The diagnostic post-mortem bullet points are static canned sentences interpolating numbers into pre-written explanations. None of this text or scoring is generated by Gemini, OpenAI, or the Python analytics engine. It presents a static template as a genuine post-market machine evaluation.
* **Severity:** **Critical**

#### Finding 1.2: Hardcoded Price Levels and Execution Directives Pinned in Morning Decision Tree
* **File & Lines:** [src/frontend/components/intelligence/MorningPlanView.tsx:164-198](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/MorningPlanView.tsx#L164-L198)
* **Actual Code:**
  ```tsx
  {/* Path A (Primary - 65% Prob): GAP-AND-GO EXTENSION */}
  <div className="text-[10.5px] text-neutral-300 space-y-0.5">
    <div><strong className="text-neutral-400">Trigger: </strong>Hold above 24,077.55 Open + sustain above 24,066.56 Pivot</div>
    <div><strong className="text-neutral-400">Target: </strong><span className="text-emerald-300 font-bold">24,100.00 – 24,143.15 (Day High Expansion)</span></div>
    <div><strong className="text-neutral-400">Action: </strong>Long entry on 1m pullback into 24,055 – 24,065 value zone (Stop: 24,043)</div>
  </div>

  {/* Path B (Alternate - 35% Prob): GAP FADE & VWAP MEAN REVERSION */}
  <div className="text-[10.5px] text-neutral-300 space-y-0.5">
    <div><strong className="text-neutral-400">Trigger: </strong>Rejection at 24,066.56 Pivot + breakdown below 24,043.78 VWAP</div>
    <div><strong className="text-neutral-400">Target: </strong><span className="text-rose-300 font-bold">23,952.55 (Session Day Low Floor) ──► 23,900.00 (Major Put Defense)</span></div>
    <div><strong className="text-neutral-400">Action: </strong>Fade intraday bounce near 24,060 with protective stop above 24,075</div>
  </div>
  ```
* **Why it is wrong:** The entire opening range execution matrix hardcodes 12 historical prices (`24,077.55`, `24,066.56`, `24,100.00`, `24,143.15`, `24,055`, `24,065`, `24,043`, `24,043.78`, `23,952.55`, `23,900.00`, `24,060`, `24,075`) into static JSX markup. Regardless of whether NIFTY opens at 23,500 or 25,200, the morning decision tree instructs the trader to watch `24,077.55` and `24,066.56`.
* **Severity:** **Critical**

#### Finding 1.3: Synthetic Intraday Derivative Trade Generation with Artificial Pricing & Multipliers
* **File & Lines:** [src/frontend/components/intelligence/LiveGuideView.tsx:86-94](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/LiveGuideView.tsx#L86-L94)
* **Actual Code:**
  ```tsx
  const candidateLtp = candObj?.ltp ?? (spot != null ? Number((spot * 0.0075).toFixed(2)) : null);
  const candidateTarget1 = candObj?.target1 ?? (candidateLtp != null ? Number((candidateLtp * 1.5).toFixed(2)) : null);
  const candidateTarget2 = candObj?.target2 ?? (candidateLtp != null ? Number((candidateLtp * 2.2).toFixed(2)) : null);
  const candidateStopLoss = candObj?.stop_loss ?? (candidateLtp != null ? Number((candidateLtp * 0.65).toFixed(2)) : null);
  const candidateDelta = candObj?.delta ?? greeks?.delta ?? (candidateOptionType === "CE" ? 0.52 : -0.48);
  const candidateTheta = candObj?.theta ?? greeks?.theta ?? -14.2;
  const candidateIv = candObj?.iv ?? envelope?.options?.atm_iv ?? vixVal ?? 12.5;
  const candidateVega = candObj?.vega ?? greeks?.vega ?? 8.4;
  ```
* **Why it is wrong:** If the decision engine produces no candidate strike, the live guide manufactures an option ticket with fake premium (`spot * 0.0075`), fake stop-loss (`LTP * 0.65`), fake targets (`1.5x` and `2.2x`), and static Greek values (`0.52`, `-14.2`, `12.5%`, `8.4`). This violates the core safety invariant prohibiting fabricated market data.
* **Severity:** **Critical**

```
================================================================================
DIMENSION 2: REAL-TIME / REFRESH PIPELINE
================================================================================
```

#### Finding 2.1: Total Absence of Timestamps, Timezones, and Market State Indicators on Global Cues
* **File & Lines:** [src/frontend/components/intelligence/MorningPlanView.tsx:215-272](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/MorningPlanView.tsx#L215-L272)
* **Actual Code:**
  ```tsx
  <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center text-[10.5px]">
    <span className="text-neutral-400">US Tech (Nasdaq)</span>
    <div className="flex items-center gap-1.5">
      <strong className="text-neutral-100">{nasdaqPrice}</strong>
      <span className={`font-bold ...`}>{nasdaqPct} ...</span>
    </div>
  </div>
  ```
* **Why it is wrong:** Although `getCanonicalQuote` provides `observedAt`, `freshnessStatus`, and `sessionContext`, `MorningPlanView` discards them. It displays Nasdaq, Brent, and GIFT NIFTY without timestamps, without converting foreign trading session hours to IST, and without indicating whether the US or commodity markets are currently open, in pre-market, or closed.
* **Severity:** **High**

```
================================================================================
DIMENSION 3: CALCULATED FIELDS & FORMULAS
================================================================================
```

#### Finding 3.1: Completely Static Sector Leadership Commentary Lacking Real Constituent Rotation Telemetry
* **File & Lines:** [src/frontend/components/intelligence/LiveGuideView.tsx:436](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/LiveGuideView.tsx#L436)
* **Actual Code:**
  ```tsx
  <div>
    <strong className="text-neutral-200">Sector Leadership: </strong>
    <span className="text-neutral-400">Broad-based sector participation and active institutional flows observed.</span>
  </div>
  ```
* **Why it is wrong:** Pillar 3 of the 5-Pillar Confluence Proof displays a static, invariant sentence ("Broad-based sector participation and active institutional flows observed") without computing or querying sector performance, sector rotation, or heavyweight contribution.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 4: MARKET STATE / SESSION HANDLING
================================================================================
```

#### Finding 4.1: Missing Off-Market Session Awareness in Morning Plan View
* **File & Lines:** [src/frontend/components/intelligence/MorningPlanView.tsx:83-145](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/MorningPlanView.tsx#L83-L145)
* **Actual Code:**
  Unlike `LiveGuideView` (which contains an `isOffMarket` replay banner at line 186), `MorningPlanView` has no off-market guard. If opened on a weekend or during an off-market holiday, it unconditionally asserts:
  ```tsx
  <span className="...">PHASE: PRE-MARKET AUCTION</span>
  <span className="...">● EXPECTED BIAS: BULLISH GAP-UP</span>
  <span className="...">OPENING PLAN PREPARED</span>
  ```
* **Why it is wrong:** The UI displays pre-market auction states and gap predictions when no pre-market session is occurring.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 5: TIMESTAMP & TIMEZONE
```

* **Audit Result:** Covered under **Finding 2.1**. Neither domestic observation times nor foreign timezone conversions are rendered anywhere on the global macro cards.

```
================================================================================
DIMENSION 6: CROSS-TAB CONSISTENCY
================================================================================
```

#### Finding 6.1: Inconsistent Derivative and Volatility Fallbacks Across Workspace Tabs
* **File & Lines:** [src/frontend/components/intelligence/LiveGuideView.tsx:445, 452](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/LiveGuideView.tsx#L445), [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:274](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L274), [src/frontend/components/MarketPulseWorkspace.tsx:397](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx#L397)
* **Actual Code:**
  - In `LiveGuideView.tsx:445`: `envelope.options?.pcr ?? "1.02"`
  - In `OptionsIntelligenceWorkspace.tsx:274`: `pcr != null ? pcr.toFixed(2) : "1.08"`
  - In `LiveGuideView.tsx:452`: `India VIX at {vixVal ?? "13.20"}`
  - In `MarketPulseWorkspace.tsx:397`: `vixVal ?? 10.68`
* **Why it is wrong:** Fallback constants are inconsistent across tabs: PCR falls back to `1.02` in Live Guide but `1.08` in Options; India VIX falls back to `13.20` in Live Guide but `10.68` in Market Pulse.
* **Severity:** **High**

```
================================================================================
DIMENSION 7: FORMATTING & SIGN/COLOR LOGIC
```

* **Audit Result:** Verified clean. Decimal precision is consistently bounded (`toFixed(2)`), sign prefixes (`+`/`-`) match numeric sign, and color encodings (emerald for bullish targets, rose for breakdown invalidations, cyan for breakouts) follow strict conventions.

```
================================================================================
DIMENSION 8: ERROR HANDLING & FALLBACKS
================================================================================
```

#### Finding 8.1: Arbitrary ATR Price Offsets for Structural Support/Resistance Levels
* **File & Lines:** [src/frontend/components/intelligence/LiveGuideView.tsx:97-100](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/LiveGuideView.tsx#L97-L100)
* **Actual Code:**
  ```tsx
  const r2Level = envelope?.price_structure?.key_resistances?.[1] ?? (spot != null && atr14 ? Number((spot + atr14 * 1.5).toFixed(2)) : (dayHigh != null ? dayHigh + 50 : null));
  const r1Level = envelope?.price_structure?.key_resistances?.[0] ?? (spot != null && atr14 ? Number((spot + atr14 * 0.75).toFixed(2)) : (dayHigh != null ? dayHigh + 25 : null));
  const s1Level = envelope?.price_structure?.key_supports?.[0] ?? (spot != null && atr14 ? Number((spot - atr14 * 0.75).toFixed(2)) : (dayLow != null ? dayLow - 25 : null));
  const s2Level = envelope?.price_structure?.key_supports?.[1] ?? (spot != null && atr14 ? Number((spot - atr14 * 1.5).toFixed(2)) : (dayLow != null ? dayLow - 50 : null));
  ```
* **Why it is wrong:** When the backend provides no key support or resistance levels, the component manufactures structural pivot levels by adding or subtracting fixed multiples of ATR (`spot ± atr14 * 0.75` and `spot ± atr14 * 1.5`) or fixed integer points (`dayHigh + 25`, `dayLow - 25`). This violates the absolute safety invariant requiring evidence-based structural levels only.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 9: LOADING STATES
```

* **Audit Result:** Verified clean. All three views implement clean empty/awaiting states (`Awaiting Pre-Market Session Data`, `Awaiting Live Market Stream`, `Awaiting Completed Session Settlement`) that render when prerequisite envelope data is missing, avoiding stuck spinners.

```
================================================================================
DIMENSION 10: UI/LAYOUT & RESPONSIVE INTEGRITY
```

* **Audit Result:** Verified clean. Responsive grids collapse cleanly from 12 columns to single columns on small viewports without text overlap or horizontal scroll overflows. The phase preview selector operates cleanly without layout shifting.

```
================================================================================
DIMENSION 11: DEAD CODE & MOCK-DATA RESIDUE
```

#### Finding 11.1: Unverified Static Reliability Scores and Confluence Badges
* **File & Lines:** [src/frontend/components/intelligence/MorningPlanView.tsx:103, 210](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/MorningPlanView.tsx#L103), [src/frontend/components/intelligence/LiveGuideView.tsx:404](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/LiveGuideView.tsx#L404)
* **Actual Code:**
  - `MorningPlanView.tsx:103`: `CONFIDENCE: 76/100 · OBSERVATIONAL (n=1)`
  - `MorningPlanView.tsx:210`: `4/5 SUPPORTIVE`
  - `LiveGuideView.tsx:404`: `5/5 CONFIRMED`
* **Why it is wrong:** Badges asserting "CONFIDENCE: 76/100", "4/5 SUPPORTIVE", and "5/5 CONFIRMED" are hardcoded strings in the JSX markup. They are static badges designed to appear quantitative.
* **Severity:** **High**

#### Finding 11.2: Hardcoded Carry-Forward Reference Pivots & Swing Strategy Confidences in Post-Market View
* **File & Lines:** [src/frontend/components/intelligence/TomorrowPlanView.tsx:236-332](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/TomorrowPlanView.tsx#L236-L332)
* **Actual Code:**
  ```tsx
  {/* Carry-Forward Reference Pivots */}
  <strong className="text-neutral-100">24,066.56</strong>
  ...
  <strong className="text-neutral-100">23,900.00</strong>

  {/* Multi-Session Strategy Suitability */}
  <span className="...">PREFERRED · 75% CONF</span>
  ...
  <span className="...">SECONDARY · 62% CONF</span>
  ...
  <span className="...">TACTICAL · 40% CONF</span>
  ```
* **Why it is wrong:** The pivots `24,066.56` and `23,900.00` as well as the strategy confidence numbers (`75%`, `62%`, `40%`) are hardcoded directly into the template.
* **Severity:** **High**

#### Finding 11.3: Orphaned Dead Code in Intelligence Directory
* **File & Lines:** [src/frontend/components/intelligence/MarketDecisionSummaryCard.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/MarketDecisionSummaryCard.tsx), [src/frontend/components/intelligence/TradeApprovalModal.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/TradeApprovalModal.tsx), [src/frontend/components/intelligence/ExecutionConfirmationModal.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/ExecutionConfirmationModal.tsx)
* **Actual Code:**
  `MarketDecisionSummaryCard.tsx` (17.9 KB) imports `TradeApprovalModal.tsx` (13.9 KB), which in turn imports `ExecutionConfirmationModal.tsx` (6.3 KB). None of these components are imported anywhere in active workspace layouts or routing tables. They represent 38 KB of unreferenced dead code.
* **Severity:** **Medium**

#### Finding 11.4: Disconnected Model Directional Confidence Metric Rendering Empty
* **File & Lines:** [src/frontend/components/intelligence/MorningPlanView.tsx:306](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/MorningPlanView.tsx#L306)
* **Actual Code:**
  ```tsx
  {envelope.prediction?.confidence_score != null ? `${formatNumber(...)` : "—"}
  ```
* **Why it is wrong:** Because `envelope.prediction` is never populated by `workstation_state_service.py` (as identified in Audit 4), this row permanently renders `—`.
* **Severity:** **Low**

#### Finding 11.5: Fixed Default 14-Day ATR Fallback (135.10 pts)
* **File & Lines:** [src/frontend/components/intelligence/TomorrowPlanView.tsx:68-69](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/TomorrowPlanView.tsx#L68-L69)
* **Actual Code:**
  ```typescript
  const rawExpectedAtr = envelope?.price_structure?.atr_14 ?? envelope?.settled_session?.atr_14 ?? (envelope.active_product?.tomorrow_plan?.session_summary?.atr) ?? 135.10;
  const expectedAtr = rawExpectedAtr != null && Number(rawExpectedAtr) >= 20 ? Number(rawExpectedAtr) : 135.10;
  ```
* **Why it is wrong:** Hardcodes `135.10` as the fallback ATR.
* **Severity:** **Low**

#### Finding 11.6: Hardcoded Expected 1-SD Day Range (110–135 pts)
* **File & Lines:** [src/frontend/components/intelligence/MorningPlanView.tsx:142](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/MorningPlanView.tsx#L142)
* **Actual Code:**
  ```tsx
  <span className="text-[8.5px] text-emerald-400 font-bold block">Expected 1-SD Day Range: 110 – 135 pts</span>
  ```
* **Why it is wrong:** Hardcodes `"110 – 135 pts"` in JSX instead of deriving it dynamically from India VIX or ATR.
* **Severity:** **Low**

#### Finding 11.7: Overly Optimistic Hardcoded Invalidation Metric in Post-Mortem Card
* **File & Lines:** [src/frontend/components/intelligence/TomorrowPlanView.tsx:171](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/intelligence/TomorrowPlanView.tsx#L171)
* **Actual Code:**
  ```tsx
  <strong className="text-emerald-400">{formatNumber(sessionLow, 2)} Low Held Firmly (0 False Triggers)</strong>
  ```
* **Why it is wrong:** Hardcodes `(0 False Triggers)` regardless of how many times intraday price action broke invalidation levels during the session.
* **Severity:** **Low**

```
================================================================================
DIMENSION 12: PERFORMANCE & MEMORY
```

* **Audit Result:** Verified clean. Zero orphaned interval timers or document listeners exist in `MorningPlanView.tsx`, `LiveGuideView.tsx`, or `TomorrowPlanView.tsx`. Memoization is used cleanly on price funnels and hysteresis bounds.

```
================================================================================
DIMENSION 13: CONSOLE & NETWORK HYGIENE
```

* **Audit Result:** Verified clean. No network requests are initiated directly from the view components; no console spam occurs; and no broker credentials, OpenAI/Gemini API keys, or secrets are exposed in payloads or DOM attributes.

---

### 3. Verified Clean

The following items were explicitly audited and verified to be clean of defects:

* **Read-Only Safety Invariant:** Verified clean. Zero live trade execution, order modification, or broker mutations occur in the Market Intelligence workspace.
* **Dynamic Phase Routing Architecture:** Verified clean. `MarketIntelligenceWorkspace.tsx` accurately maps `effectiveMarketPhase` to the corresponding phase cockpit with full support for safe manual preview overrides.
* **Interactive 09:15 Discipline Checklist:** Verified clean. The pre-market checklist provides responsive, non-destructive interactive verification gates for morning execution discipline.
* **Real-Time Funnel Spot Beacon Synchronization:** Verified clean. In `LiveGuideView.tsx`, the vertical price funnel dynamically repositions the active spot row, applies range percentage calculation, and pulses an active beacon aligned with Kite ticks.
* **Clean Fallback Views on Missing Data:** Verified clean. All three views implement graceful, non-crashing empty states (`Awaiting Pre-Market Session Data`, `Awaiting Live Market Stream`, `Awaiting Completed Session Settlement`) when data is unavailable.
* **Absence of Memory Leaks:** Verified clean. No window listeners or timer handles are left open upon workspace transitions.
* **Broker Credential Security:** Verified clean. Zero Kite API tokens or secret keys are exposed in client payloads or DOM attributes.
