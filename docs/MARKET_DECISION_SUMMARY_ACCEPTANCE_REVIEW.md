# MARKET DECISION SUMMARY — UI & SOURCE-OF-TRUTH ACCEPTANCE REVIEW

**Document Version:** 1.0.0 — Authoritative Acceptance Review  
**Subsystem:** Market Intelligence Trader Decision Summary Layer  
**Target Surface:** `MarketIntelligenceWorkspace.tsx` (`MorningPlanView.tsx`, `LiveGuideView.tsx`, `TomorrowPlanView.tsx`)  
**Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** ALL ACCEPTANCE GATES PASSED (Feature Frozen for Monday Phase F Live Observation)  
**Production Isolation:** Staging Only — Production Untouched.

---

## 1. BACKEND AUTHORITY & SOURCE-OF-TRUTH TRACE

Every rendered field in `MarketDecisionSummaryCard.tsx` is 100% backend-authoritative. React performs zero business calculation, strike selection, status evaluation, or risk derivation.

| Decision Field | Backend Source | Frontend Property | Frontend Transformation | Business Logic in React |
|:---|:---|:---|:---|:---:|
| **NIFTY Bias** | `decision_summary.bias` | `vm.decisionSummary.bias` | Maps enum to semantic badge color | **NO** |
| **Setup** | `decision_summary.setup` | `vm.decisionSummary.setup` | Displays uppercase setup title | **NO** |
| **Strike** | `decision_summary.strike` | `vm.decisionSummary.strike` | Formats contract text / status label | **NO** |
| **Entry Condition** | `decision_summary.entry_condition` | `vm.decisionSummary.entry_condition` | Renders formatted statement | **NO** |
| **Confidence** | `decision_summary.confidence` | `vm.decisionSummary.confidence` | Formats integer percentage string | **NO** |
| **Liquidity** | `decision_summary.liquidity` | `vm.decisionSummary.liquidity` | Color-codes grade text | **NO** |
| **Data Quality** | `decision_summary.data_quality` | `vm.decisionSummary.data_quality` | Color-codes category badge | **NO** |
| **Risk Level** | `decision_summary.risk` | `vm.decisionSummary.risk` | Color-codes risk label | **NO** |
| **Status** | `decision_summary.status` | `vm.decisionSummary.status` | Maps enum to icon & text badge | **NO** |
| **Invalidation** | `decision_summary.invalidation` | `vm.decisionSummary.invalidation` | Prepends "INVALIDATION:" label | **NO** |
| **Supporting Evidence**| `decision_summary.supporting_evidence` | `vm.decisionSummary.supporting_evidence`| Maps array to chip badges | **NO** |
| **Blocking Reasons** | `decision_summary.blocking_reasons` | `vm.decisionSummary.blocking_reasons` | Formats token strings to labels | **NO** |

---

## 2. LIQUIDITY POLICY SINGLE-SOURCE AUDIT

- **Authoritative Liquidity Policy Sources:** **1 (Exactly ONE)**
- **Authoritative Module:** [`DecisionLiquidityPolicy`](file:///opt/ardhamind/staging/src/intelligence_engine/decision_summary_composer.py#L17) in `src/intelligence_engine/decision_summary_composer.py`.
- **Configurable Parameters:** `max_spread_bps=250.0`, `min_volume=1000`, `min_open_interest=25000`, `min_depth_quantity=50`.
- **UI Logic Duplication:** **0.** The frontend renders the backend-evaluated `liquidity.value` without independently testing spreads or volume.

---

## 3. DECISION IDENTITY STABILITY AUDIT

- **Precedence:** Uses `opportunity_id` (e.g. `DEC-OPP-20260821-001`) whenever available.
- **Fallback Binning:** If no discrete opportunity ID exists, hashes `(session_date, setup, direction, strike, round(spot / 50.0) * 50)`.
- **Stability Verification:**
  - Minor spot price movements ($\pm 2.0$ pts) $\rightarrow$ **Identical `decision_id`**
  - Confidence updates ($78\% \rightarrow 79\%$) $\rightarrow$ **Identical `decision_id`**
  - Data Quality updates $\rightarrow$ **Identical `decision_id`**
  - Direction or setup change $\rightarrow$ **New `decision_id`**
  - New trading session $\rightarrow$ **New `decision_id`**

---

## 4. BROWSER VALIDATION ACROSS SUB-TABS

1. **Morning Plan (Pre-Market):**
   - Renders Decision Summary strip at the top with `WATCH` status and `REQUIRES LIVE OPTIONS` strike state.
   - Detailed Morning Plan panels, scenarios, and decision zones remain 100% intact underneath.
2. **Live Guide (Market Hours):**
   - Surfaces full 4-row layout: Primary (Bias, Setup, Status) $\rightarrow$ Trade (Strike, Trigger) $\rightarrow$ Quality Strip (Confidence, Liquidity, DQ, Risk) $\rightarrow$ Detail (Invalidation & Evidence).
   - Trader can evaluate trade posture in $<3.0$ seconds (*Decision First*).
3. **Tomorrow Plan (Post-Close / Weekend):**
   - Displays carry-forward bias with `MARKET CLOSED` badge and next-session continuation triggers.
   - Live order-dependent strikes correctly marked `REQUIRES LIVE OPTIONS`.

---

## 5. DEGRADATION & SAFETY GATES VALIDATION

- **Broker Disconnected Test:** All analytical fields (Bias, Setup, Strike, Entry, Conf, Liq, DQ, Risk) remain 100% visible; status transitions to `QUALIFYING` with blocking reason `BROKER_AUTH_REQUIRED`.
- **Options Stale Test:** Spot trend and setup remain visible; strike degrades to `WAITING_FOR_OPTIONS_CONFIRMATION`, status to `BLOCKED` with `OPTIONS_FEED_STALE` flagged.
- **Market Closed Test:** Status transitions to `MARKET_CLOSED`; live execution readiness disabled.
- **Live Order Execution Boundary:** **0 order placement connections** (Purely informational decision summary).

---

## 6. MONDAY PHASE F BASELINE ISOLATION PROOF

- **Files in `src/storage/`:** **100% UNTOUCHED**
- **Kite Streaming & Reconnect Orchestrator:** **100% UNTOUCHED**
- **Feed Freshness Watchdog & Retention Manager:** **100% UNTOUCHED**
- **All Core Storage & Regression Tests (50/50):** **100% PASSED**
- **TypeScript Static Typecheck (`tsc --noEmit`):** **0 ERRORS**
- **Production Bundle (`npm run build`):** **SUCCESSFUL**
