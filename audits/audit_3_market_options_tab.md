# Options Tab — Full E2E Forensic Audit

### 1. Summary

A comprehensive, read-only forensic audit was conducted across the **Market → Options** tab ([OptionsIntelligenceWorkspace.tsx](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx)), covering the Derivatives State Strip, Positioning Map, Smart Option Chain ladder (Table, Heatmap, and Change views), Strike Inspector, Primary Advisory Candidate card, Derivatives Evidence panels, and underlying Python options engines (`iv.py`, `max_pain.py`, `oi_analysis.py`, `chain_builder.py`, `workstation_state_service.py`). While backend mathematical functions for Max Pain and non-inverted PCR calculation are theoretically sound and broker authentication tokens remain unexposed, the investigation identified **2 Critical**, **7 High**, **6 Medium**, and **5 Low** severity defects.

Most critically, when live option chain data from the broker is unpopulated or disconnected, the frontend executes an elaborate mathematical simulation: it manufactures 11 synthetic strike prices around ATM, computes fictitious option premiums using a hardcoded linear time-value decay formula, generates fake Open Interest distributions using a Gaussian bell-curve exponential algorithm, and invents OI changes and buildup states. Furthermore, the UI prominently promises Greeks inspection ("Click any strike row to inspect Call/Put Greeks"), yet Delta, Gamma, Theta, and Vega are completely absent from both the option chain table and the strike inspector. Additionally, the spot price separator in the chain table is hardcoded to strike 24,200 (vanishing whenever NIFTY trades outside 24,150–24,200), and changing the expiry dropdown does not switch or reload strikes.

| Severity | Finding Count | Primary Impact Area |
| :--- | :---: | :--- |
| **Critical** | **2** | Synthetic option chain generation with Gaussian bell-curve OI & artificial premium time-decay formula |
| **High** | **7** | Promised Greeks (Delta/Gamma/Theta/Vega) completely missing from UI, false "sub-second stream" claim, hardcoded derivatives metrics fallbacks, spot price tape divergence, full table re-render on every tick, missing observation timestamps, synthetic candidate trade generator |
| **Medium** | **6** | Spot line hardcoded to strike 24200, non-functional expiry dropdown, flat zero ΔOI colored green, missing sticky ATM pin, unreachable empty chain state, hardcoded Greek solver inputs in backend service |
| **Low** | **5** | Pre-open carryover ambiguity, static date residue, missing Indian digit grouping on high LTPs, hardcoded dark mode palette, static replay fixture residue |
| **Total** | **20** | |

---

### Complete Data Inventory & Source Mapping

Every field and metric displayed on the Options tab is enumerated below with its underlying source, computation method, and data pipeline:

| Field / Metric Displayed | UI Location | Underlying Source / Field | Computation / Sourcing Method | Live Ticking vs Static |
| :--- | :--- | :--- | :--- | :--- |
| **Expiry Date** | Header Strip & Dropdown | `envelope.options.expiry` | Kite Instrument Master / Hardcoded `"03 Sep 2026"` | Static / Weekly |
| **Underlying Spot Price** | Header Strip & Spot Bar | `options.spot_price` / `authState.spot` | Kite WebSocket (Token `256265`) | Real-Time Ticking |
| **Spot Change & Change %** | Header Strip & Spot Bar | Computed: `spotPrice - prevClose` | Computed from Kite Ticks | Real-Time Ticking |
| **ATM Strike** | Header Strip & Chain Pin | `options.atm_strike` / `round(spot/50)*50` | Computed Nearest 50-Multiple | Real-Time Ticking |
| **Put-Call Ratio (PCR)** | Header Strip & Summary | `options.pcr` OR Fallback `1.08` | `total_put_oi / total_call_oi` (Python) OR Synthetic | Periodic / Dynamic |
| **Max Pain Strike** | Header Strip & Concentr. | `options.max_pain` OR `atmStrike - 50` | Cumulative Loss Minimization OR Synthetic | Periodic / Dynamic |
| **ATM Implied Volatility (IV)**| Header Strip | `options.atm_iv` OR `vix.last_price` | Black-Scholes Solver (`iv.py`) OR VIX Proxy | Periodic / Dynamic |
| **Total Call & Put OI (Cr)** | Header Strip & Progress | `options.total_call_oi`, `total_put_oi` | Cumulative Contract Sum OR Synthetic (`1.43/1.54 Cr`)| Periodic / Dynamic |
| **OI Bias / Skew** | Header Strip & Summary | `options.options_confirmation` | Rule-based classification on PCR & Walls | Periodic / Dynamic |
| **Call Wall & Put Wall** | Positioning Map & Badges | `options.call_wall`, `put_wall` | Maximum Strike OI OR Synthetic (`atm ± 200`) | Periodic / Dynamic |
| **Strike Universe (Strikes)** | Center Option Ladder | `options.strike_universe` | Kite REST Quotes / **Synthetic Fallback (11 Strikes)**| Periodic / Snapshot |
| **Call & Put LTP** | Option Ladder & Inspector | `s.ce_ltp`, `s.pe_ltp` | Kite Quotes OR **Synthetic Formula `intrinsic + timeVal`**| Periodic / Snapshot |
| **Call & Put OI (Lakh)** | Option Ladder & Inspector | `s.ce_oi`, `s.pe_oi` | Kite Quotes OR **Synthetic Gaussian Bell Curve**| Periodic / Snapshot |
| **Call & Put Change in OI** | Option Ladder (Table/Chg) | `s.ce_oi_change`, `s.pe_oi_change` | Snapshot Delta OR **Synthetic `8% / 11%` of OI** | Periodic / Snapshot |
| **Call & Put IV (%)** | Option Ladder & Inspector | `s.ce_iv`, `s.pe_iv` | Python Bisection Solver OR `null` | Periodic / Snapshot |
| **Call & Put Buildup** | Option Ladder (Change) | `s.ce_buildup`, `s.pe_buildup` | Price/OI Matrix (`LONG_BUILDUP`, etc.) | Periodic / Snapshot |
| **Greeks (Δ, Γ, Θ, V)** | **MISSING FROM UI** | Calculated in Backend | **NOT DISPLAYED** despite UI label claiming Greeks | **ABSENT FROM UI** |
| **Bid / Ask Spread** | **MISSING FROM TABLE** | Available in Backend `leg.bid/ask`| **NOT DISPLAYED** in smart option table | **ABSENT FROM UI** |
| **Volume** | **MISSING FROM TABLE** | Available in Backend `leg.volume` | **NOT DISPLAYED** in smart option table | **ABSENT FROM UI** |
| **Candidate Strike Setup** | Right Column (Advisory) | `envelope.decision.strike_candidates`| Python Trader Decision Engine OR Synthetic | Dynamic / Snapshot |

---

### 2. Forensic Findings by Dimension (1–13)

```
================================================================================
DIMENSION 1: DATA INVENTORY & SOURCE FIDELITY
================================================================================
```

#### Finding 1.1: Synthetic Option Chain Generation with Gaussian Bell-Curve Open Interest
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:84-125](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L84-L125)
* **Actual Code:**
  ```tsx
  if (raw.length === 0 && (resolvedSpot != null || atmStrike != null)) {
    const baseAtm = atmStrike || (resolvedSpot ? Math.round(resolvedSpot / 50) * 50 : 23850);
    raw = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5].map((offset) => ({
      strike: baseAtm + offset * 50,
      is_atm: offset === 0,
    }));
  }
  ...
  const baseCallOi = Math.round(1800000 * Math.exp(-Math.pow((strikeVal - (atm + 100)) / 250, 2)));
  const basePutOi = Math.round(1950000 * Math.exp(-Math.pow((strikeVal - (atm - 100)) / 250, 2)));

  const ce_oi = s.ce_oi ?? s.callOi ?? s.call_oi ?? (s.call_oi === 0 ? 0 : baseCallOi);
  const pe_oi = s.pe_oi ?? s.putOi ?? s.put_oi ?? (s.put_oi === 0 ? 0 : basePutOi);
  const ce_oi_change = s.ce_oi_change ?? s.callChg ?? s.call_oi_change ?? Math.round((Number(ce_oi) || 100000) * 0.08);
  const pe_oi_change = s.pe_oi_change ?? s.putChg ?? s.put_oi_change ?? Math.round((Number(pe_oi) || 100000) * 0.11);
  ```
* **Why it is wrong:** When real option chain data is unavailable, the workspace fabricates 11 strikes and populates open interest using synthetic Gaussian exponential distributions centered at `atm ± 100` (`1,800,000 * exp(...)`). It then calculates change in OI as an arbitrary 8% and 11% of the fabricated OI. This violates the core safety invariant prohibiting fabricated market data.
* **Severity:** **Critical**

#### Finding 1.2: Synthetic Strike LTP, Time Value, and Buildup State Calculation
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:106-124](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L106-L124)
* **Actual Code:**
  ```tsx
  const diff = strikeVal - currentSpot;
  const intrinsicCe = Math.max(0, currentSpot - strikeVal);
  const intrinsicPe = Math.max(0, strikeVal - currentSpot);
  const timeVal = Math.max(15, 65 - Math.abs(diff) * 0.12);

  const ce_ltp = s.ce_ltp ?? s.callLtp ?? s.call_ltp ?? (intrinsicCe > 0 ? intrinsicCe + timeVal : Math.max(2.5, timeVal));
  const pe_ltp = s.pe_ltp ?? s.putLtp ?? s.put_ltp ?? (intrinsicPe > 0 ? intrinsicPe + timeVal : Math.max(2.5, timeVal));
  ...
  const ce_buildup = s.ce_buildup ?? s.callBuildup ?? (ce_oi_change > 0 ? "LONG_BUILDUP" : "SHORT_COVERING");
  const pe_buildup = s.pe_buildup ?? s.putBuildup ?? (pe_oi_change > 0 ? "SHORT_BUILDUP" : "LONG_UNWINDING");
  ```
* **Why it is wrong:** Missing option premiums are synthesized using an arbitrary linear model (`65 - |diff| * 0.12`), and missing institutional buildup states are manufactured from the synthetic OI change.
* **Severity:** **Critical**

#### Finding 1.3: Promised Greeks Feature Missing from Entire Workspace
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:536-574, 787, 820-870](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L787)
* **Actual Code:**
  Line 787 explicitly instructs the user:
  ```tsx
  <span>Click any strike row to inspect Call/Put Greeks and positioning delta</span>
  ```
  However, in the chain table headers (lines 536–574), the columns are only `OI`, `ΔOI`, `LTP`, and `IV`. When a user clicks a strike row, the Strike Inspector (lines 820–870) only displays `LTP`, `OI`, and `IV`.
* **Why it is wrong:** Delta ($\Delta$), Gamma ($\Gamma$), Theta ($\Theta$), and Vega ($V$) are completely absent from both the Smart Option Chain and the Strike Inspector. The UI explicitly advertises Greeks inspection but provides no Greeks columns or values.
* **Severity:** **High**

#### Finding 1.4: Hardcoded Derivatives Summary Metrics Fallbacks
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:72-78, 274, 303, 312](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L72-L312)
* **Actual Code:**
  ```tsx
  const maxPain = isDataAvailable ? (options.max_pain || (atmStrike != null ? atmStrike - 50 : null)) : null;
  const callWall = isDataAvailable ? (options.call_wall || (atmStrike != null ? atmStrike + 200 : null)) : null;
  const putWall = isDataAvailable ? (options.put_wall || (atmStrike != null ? atmStrike - 200 : null)) : null;
  ...
  {pcr != null ? pcr.toFixed(2) : "1.08"}
  ...
  {totalCallOiCr != null ? `${totalCallOiCr.toFixed(2)} Cr` : "1.43 Cr"}
  ...
  {totalPutOiCr != null ? `${totalPutOiCr.toFixed(2)} Cr` : "1.54 Cr"}
  ```
* **Why it is wrong:** Missing summary metrics are populated with arbitrary offsets (`atmStrike ± 200`, `atmStrike - 50`) and static strings (`"1.08"`, `"1.43 Cr"`, `"1.54 Cr"`).
* **Severity:** **High**

```
================================================================================
DIMENSION 2: REAL-TIME PIPELINE
================================================================================
```

#### Finding 2.1: False "Sub-Second Stream" Telemetry Claim
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:788](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L788)
* **Actual Code:**
  ```tsx
  <span>Data: NSE NIFTY 50 Options · Sub-second Stream</span>
  ```
* **Why it is wrong:** In `SubscriptionManager.py:9-26`, only index instruments (`NIFTY 50`, `INDIA VIX`, `BANKNIFTY`) are subscribed to upstream KiteTicker WebSocket streams. Option contracts are fetched via REST quotes or periodic snapshots (`chain_builder.py:96-100`). Claiming "Sub-second Stream" misleads the trader about data latency.
* **Severity:** **High**

#### Finding 2.2: Hardcoded Spot Line Separator at Strike 24,200
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:600-609](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L600-L609)
* **Actual Code:**
  ```tsx
  const showSpotLineBefore = strikePx === 24200 && spotPrice != null && spotPrice < 24200 && spotPrice >= 24150;
  ...
  {showSpotLineBefore && spotPrice != null && (
    <tr className="bg-emerald-500/10 border-y-2 border-emerald-500/80">
      <td colSpan={9} className="py-1 text-center font-bold text-[10px] text-emerald-300 tracking-wider">
        ─── SPOT: {spotPrice.toLocaleString("en-IN", { minimumFractionDigits: 2 })} ... ───
      </td>
    </tr>
  )}
  ```
* **Why it is wrong:** The horizontal divider representing the underlying spot price is hardcoded specifically to `strikePx === 24200`. If NIFTY trades at 23,800, 24,500, or any price outside 24,150–24,200, the spot line separator disappears entirely from the option chain ladder.
* **Severity:** **Medium**

#### Finding 2.3: Non-Functional Expiry Contract Dropdown
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:61, 84-142, 353-367](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L61-L367)
* **Actual Code:**
  ```tsx
  const [selectedExpiry, setSelectedExpiry] = useState<string>(activeExpiry);
  ...
  <select value={selectedExpiry} onChange={(e) => setSelectedExpiry(e.target.value)} ...>
  ```
* **Why it is wrong:** While `selectedExpiry` state updates when the user picks a different contract from the dropdown, `selectedExpiry` is omitted from the dependency array of `strikes` (line 142) and triggers no WebSocket resubscription or API query. Changing the expiry dropdown does not reload or update the option chain strikes.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 3: CALCULATED FIELDS & FORMULAS
================================================================================
```

#### Finding 3.1: Hardcoded Inputs to Backend Black-Scholes Greeks Engine
* **File & Lines:** [src/application/workstation_state_service.py:3605-3616](file:///p:/ArdhaMind-Local/ardhamind/staging/src/application/workstation_state_service.py#L3605-L3616)
* **Actual Code:**
  ```python
  greeks_res = calculate_black_scholes_greeks(
      spot=spot,
      strike=cand_strike,
      time_to_expiry_years=2.0 / 365.0,
      volatility=vol_val,
      option_type="CE",
  )
  ...
  "ltp": round(spot * 0.004, 2) if spot else None,
  ```
* **Why it is wrong:** In `workstation_state_service.py`, `time_to_expiry_years` is hardcoded to `2.0 / 365.0` (assuming exactly 2 days to expiry every single day), and candidate option LTP is hardcoded to `spot * 0.004`.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 4: MARKET STATE / SESSION HANDLING
================================================================================
```

#### Finding 4.1: Static Fallback Expiry Date Residue
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:245](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L245), [src/application/workstation_state_service.py:3569](file:///p:/ArdhaMind-Local/ardhamind/staging/src/application/workstation_state_service.py#L3569)
* **Actual Code:**
  ```tsx
  {options.expiry || (isReplayMode ? "28 Aug 2026" : "03 Sep 2026")}
  ```
  ```python
  opt_expiry = o_ctx.get("expiry") or o_ctx.get("current_expiry") or "2026-09-03"
  ```
* **Why it is wrong:** Hardcodes `"03 Sep 2026"` as the default active weekly expiry across both frontend and backend.
* **Severity:** **Low**

#### Finding 4.2: Ambiguous Pre-Open OI Presentation
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:235-326](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L235-L326)
* **Actual Code:**
  During 09:00–09:15 IST (when the cash market discovers opening prices but derivatives trading is closed), the Options tab presents the chain identically to live market hours without labeling OI as "Previous Session Carryover".
* **Severity:** **Low**

```
================================================================================
DIMENSION 5: TIMESTAMP & TIMEZONE
================================================================================
```

#### Finding 5.1: Complete Absence of Data Observation Timestamps
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:1-1056](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L1-L1056)
* **Actual Code:**
  There is no timestamp anywhere in `OptionsIntelligenceWorkspace.tsx`.
* **Why it is wrong:** Neither individual strikes, the option chain ladder, nor the top telemetry strip display `observed_at`, `exchange_timestamp`, or "last updated" in IST. A trader cannot verify if the options chain is current or stalled.
* **Severity:** **High**

```
================================================================================
DIMENSION 6: CROSS-TAB CONSISTENCY
================================================================================
```

#### Finding 6.1: Spot Price Priority Discrepancy with NIFTY Live Workspace
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:43-50](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L43-L50)
* **Actual Code:**
  ```tsx
  const resolvedSpot = Number(options?.spot_price)
    || Number((options as any)?.underlying_price)
    || Number((options as any)?.underlying_spot)
    || authState.spot
    || ...
  ```
* **Why it is wrong:** `OptionsIntelligenceWorkspace` prioritizes `options.spot_price` (which is stamped when the option chain snapshot was generated) over `authState.spot` (the live WebSocket tick). If the option chain snapshot is 30 seconds old, the Options tab displays an outdated spot price while the NIFTY tab displays the live price.
* **Severity:** **High**

```
================================================================================
DIMENSION 7: FORMATTING & SIGN/COLOR LOGIC
```

#### Finding 7.1: Zero Change in Open Interest (ΔOI = 0.00 L) Rendered as Positive Green
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:639, 696](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L639-L696)
* **Actual Code:**
  ```tsx
  <td className={`... ${cOiChgLakh >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
    {cOiChgLakh >= 0 ? "+" : ""}{cOiChgLakh.toFixed(2)}
  </td>
  ...
  <td className={`... ${pOiChgLakh >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
    {pOiChgLakh >= 0 ? "+" : ""}{pOiChgLakh.toFixed(2)}
  </td>
  ```
* **Why it is wrong:** When change in OI is `0.00`, `>= 0` evaluates to `true`, displaying `+0.00` in green text rather than neutral gray.
* **Severity:** **Medium**

#### Finding 7.2: Deep ITM Option LTPs Omit Indian Digit Grouping
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:645, 692](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L645-L692)
* **Actual Code:**
  ```tsx
  {s.ce_ltp != null ? s.ce_ltp.toFixed(2) : "—"}
  {s.pe_ltp != null ? s.pe_ltp.toFixed(2) : "—"}
  ```
* **Why it is wrong:** Uses `.toFixed(2)` without `toLocaleString("en-IN")`. Deep ITM options trading above ₹1,000 render as `1450.25` instead of `1,450.25`.
* **Severity:** **Low**

```
================================================================================
DIMENSION 8: ERROR HANDLING & FALLBACKS
```

#### Finding 8.1: Synthetic Advisory Candidate Trade Generator with Fabricated Pricing
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:174-211](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L174-L211)
* **Actual Code:**
  ```tsx
  } else if (!cand && atmStrike != null) {
    const isBearish = (authState.spot != null && authState.vwap != null && authState.spot < authState.vwap);
    const candType = isBearish ? "PE" as const : "CE" as const;
    const candStrike = atmStrike;
    const matchingRow = strikes.find((s) => s.strike === candStrike);
    const ltpVal = matchingRow ? (candType === "CE" ? matchingRow.ce_ltp : matchingRow.pe_ltp) : 120.00;
    cand = {
      canonical_id: `OPT:NSE:NIFTY:${authState.sessionDate || "2026-09-02"}:${candType}:${candStrike}`,
      option_type: candType,
      strike: candStrike,
      ltp: ltpVal ?? 120.00,
      ...
    };
  }
  ```
* **Why it is wrong:** When the decision engine produces no candidate trade, the component manufactures an advisory candidate on the fly, defaulting the option premium to `₹120.00` if unmapped.
* **Severity:** **High**

```
================================================================================
DIMENSION 9: LOADING STATES
```

#### Finding 9.1: Dedicated Empty Chain State Unreachable Due to Preemptive Fallbacks
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:89-94, 515-521](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L89-L521)
* **Actual Code:**
  The component contains an "Awaiting live derivatives stream" empty state at line 515:
  ```tsx
  {displayedStrikes.length === 0 ? (
    <div className="...">Awaiting live derivatives stream / Option chain data</div>
  ) : ...}
  ```
* **Why it is wrong:** Because lines 89–94 proactively synthesize 11 strikes whenever `resolvedSpot` or `atmStrike` is non-null, `displayedStrikes.length` is never 0 on an active workstation, preventing the loading/empty state from ever rendering.
* **Severity:** **Medium**

```
================================================================================
DIMENSION 10: UI/LAYOUT & RESPONSIVE INTEGRITY
```

#### Finding 10.1: ATM Strike Row Lacks Sticky Pinning During Vertical Scroll
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:514, 611-624](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L514-L624)
* **Actual Code:**
  The container has `max-h-[460px] overflow-x-auto`. The `<thead>` is sticky (`sticky top-0 z-10`), but the ATM strike row has no sticky CSS classes.
* **Why it is wrong:** When viewing "ALL STRIKES" (up to 31 rows), scrolling up or down pushes the ATM row out of view. In institutional option desks, the ATM row remains pinned or centered.
* **Severity:** **Medium**

#### Finding 10.2: Hardcoded Dark Mode Styling Without Theme Variable Support
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:235-1050](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L235-L1050)
* **Actual Code:**
  Uses hardcoded Tailwind classes (`bg-neutral-950`, `bg-neutral-900/60`, `border-neutral-800`).
* **Why it is wrong:** The workspace does not respond to light mode or theme provider settings.
* **Severity:** **Low**

```
================================================================================
DIMENSION 11: DEAD CODE & MOCK-DATA RESIDUE
```

#### Finding 11.1: Replay Fixture `CANONICAL_28_AUG_STRIKE_UNIVERSE` Residue
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:12, 96, 176](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L12-L176)
* **Actual Code:**
  ```tsx
  import { CANONICAL_28_AUG_STRIKE_UNIVERSE } from "../../data/canonicalFixtures";
  ...
  else if (raw.length === 0 && isReplayMode) {
    raw = CANONICAL_28_AUG_STRIKE_UNIVERSE;
  }
  ```
* **Why it is wrong:** Relies on a hardcoded 21-strike static fixture from 28 August 2026.
* **Severity:** **Low**

```
================================================================================
DIMENSION 12: PERFORMANCE & MEMORY
```

#### Finding 12.1: Full Option Ladder Re-Evaluation on Every Incoming NIFTY Spot Tick
* **File & Lines:** [src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx:84-142](file:///p:/ArdhaMind-Local/ardhamind/staging/src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx#L84-L142)
* **Actual Code:**
  ```tsx
  const strikes: StrikeRow[] = useMemo(() => {
    ...
  }, [options.strike_universe, isReplayMode, resolvedSpot, atmStrike, callWall, putWall]);
  ```
* **Why it is wrong:** `resolvedSpot` changes on every single tick received from KiteTicker WebSocket (multiple times per second). Because `resolvedSpot` is in `strikes`' dependency array, every tick recalculates the entire strike universe and causes React to re-render all rows in the option chain table rather than updating only the spot line.
* **Severity:** **High**

```
================================================================================
DIMENSION 13: CONSOLE & NETWORK HYGIENE
```

* **Audit Result:** Inspected for console spam, unhandled promise rejections, and credential leaks. No network hygiene or secret exposure defects identified.

---

### 3. Verified Clean

The following items were explicitly audited and verified to be clean of defects:

* **Read-Only Safety Invariant:** Verified clean. Zero order placement, trade routing, or broker mutation capabilities exist in the options workspace.
* **Backend Put-Call Ratio Math:** Verified clean. `OptionsIntelligenceEngine.analyze` computes `total_put_oi / total_call_oi` (not inverted).
* **Backend Max Pain Algorithm:** Verified clean. `OptionsIntelligenceEngine.calculate_max_pain` correctly minimizes cumulative option buyer loss across strikes.
* **Crore / Lakh Unit Scaling:** Verified clean. Division by $10^7$ for Crores in summary and $10^5$ for Lakhs in table rows is mathematically correct.
* **ITM / OTM Shading Accuracy:** Verified clean. Call ITM (`strike < spot`) and Put ITM (`strike > spot`) correctly apply `bg-neutral-900/60` background contrast.
* **Absence of Memory Leaks:** Verified clean. No uncleaned setInterval or window resize listeners exist in `OptionsIntelligenceWorkspace.tsx`.
* **Broker Credential Security:** Verified clean. No Kite API keys, access tokens, or secrets are exposed in client payloads or DOM attributes.
