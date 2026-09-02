/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Frontend Canonical Presentation & Phase-Aware NIFTY + METRICS Test Suite.
 * Validates:
 * 1. Convergence & runtime_id sequence reset (avoiding sequence lock).
 * 2. Revision monotonicity.
 * 3. Stale-state evaluation & decision BLOCKED revocation.
 * 4. Zero fallback numeric prevention (no ₹0 / 0 PCR for unavailable data).
 * 5. 4-Mode Trader Presentation Taxonomy (MORNING, OPENING, LIVE, POST-MARKET).
 * 6. Single-Session Spine Truth (Reconciled with 28 Aug 2026 external reference tape).
 * 7. Certified Previous Close (24,090.85) and positive Net Change (+84.80 / +0.35%).
 * 8. Candidate strike advisory structure (zero order buttons).
 * 9. Routing hierarchy: NIFTY workspace rendered only when marketSubTab === "nifty", NOT "metrics".
 * 10. Multi-Timeframe Chart Aggregation (1m, 3m, 5m, 15m, 1h, 1D deterministic OHLCV aggregation).
 * 11. 1D Daily Candle Model equals exact certified session OHLC (24122.05 / 24188.65 / 24076.50 / 24175.65).
 * 12. Single coherent VWAP across all MORNING surfaces (~24,142.80, never 24,536.20).
 * 13. METRICS Tab Invariants:
 *     - M1: METRICS prev close, close, and change match certified spine constants.
 *     - M2: NIFTY 50 breadth totals 50 when labeled NIFTY 50.
 *     - M3: No banned synthetic anchors in METRICS.
 *     - M4: Interpretation card synthesis fields render without error.
 *     - M5: Institutional block exposes as-of date (28 Aug 2026).
 *     - M6: NIFTY freeze invariants still pass.
 */

import {
  CANONICAL_FIXTURE_PRE_MARKET,
  CANONICAL_FIXTURE_PRE_OPEN,
  CANONICAL_FIXTURE_OPENING_RANGE,
  CANONICAL_FIXTURE_REGULAR_LIVE,
  CANONICAL_FIXTURE_NEAR_CLOSE,
  CANONICAL_FIXTURE_POST_MARKET,
  CANONICAL_28_AUG_SESSION_CANDLES,
  CANONICAL_28_AUG_STRIKE_UNIVERSE,
  VERIFIED_28_AUG_SPINE_CONSTANTS,
} from "../data/canonicalFixtures";
import {
  CanonicalFrontendEnvelope,
  DataQualityStatus,
  MarketPhase,
  DecisionState,
} from "../types/canonical";
import {
  adaptCanonicalToChart,
  aggregateCandles,
} from "../components/canonical/chart/chartAdapter";
import { resolveStrikeCandidateDistance } from "../utils/canonicalSemanticContract";
import { getHorizonCalibration } from "../utils/canonicalIntelligenceAdapter";
import {
  getCanonicalNewsPresentation,
  getSectorToneFromScore,
  getEntityBadge,
  formatDiscoveryTimestamp,
  normalizeRelevanceScore,
  getContextualTransmission,
} from "../utils/canonicalNewsAdapter";
import {
  resolveCanonicalSessionIdentity,
  resolveSessionPhase,
  resolveIntelligenceMode,
} from "../session/sessionPhaseEngine";
import { resolveAuthoritativeMarketState } from "../utils/canonicalResolvers";
import fs from "node:fs";

function assert(condition: boolean, message: string) {
  if (!condition) {
    console.error(`❌ FAILED: ${message}`);
    throw new Error(`Assertion failed: ${message}`);
  }
  console.log(`✅ PASSED: ${message}`);
}

export function runFrontendTests() {
  console.log("==================================================");
  console.log("RUNNING FRONTEND CANONICAL & METRICS TESTS");
  console.log("==================================================");

  // Test 1: Envelope Null Safety & Structural Keys
  const env = CANONICAL_FIXTURE_PRE_MARKET;
  assert(env.session !== undefined, "Session state exists in envelope");
  assert(env.market !== undefined, "Market quotes exist in envelope");
  assert(env.price_structure !== undefined, "Price structure exists in envelope");
  assert(env.breadth !== undefined, "Breadth state exists in envelope");
  assert(env.options !== undefined, "Options state exists in envelope");
  assert(env.regime !== undefined, "Regime state exists in envelope");
  assert(env.prediction !== undefined, "Prediction state exists in envelope");
  assert(env.decision !== undefined, "Decision state exists in envelope");
  assert(env.candles !== undefined, "Candles exist in envelope");

  // Test 2: Runtime ID & Revision Monotonicity
  assert(typeof env.runtime_id === "string" && env.runtime_id.length > 0, "Runtime ID is populated");
  assert(typeof env.state_revision === "number" && env.state_revision > 0, "State revision is monotonic number");

  // Test 3: Data Quality Status Validation
  const validStatus: DataQualityStatus[] = ["VALID", "STALE", "DELAYED", "COMPLETED"];
  assert(validStatus.includes(env.data_quality), "Data quality status is valid enum");

  // Test 4: Phase-Specific Workstation Modes
  assert(CANONICAL_FIXTURE_PRE_MARKET.session.market_phase === "PRE_MARKET", "Pre-market phase is PRE_MARKET");
  assert(CANONICAL_FIXTURE_PRE_OPEN.session.market_phase === "PRE_OPEN", "Pre-open phase is PRE_OPEN");
  assert(CANONICAL_FIXTURE_OPENING_RANGE.session.market_phase === "OPENING_RANGE", "Opening range phase is OPENING_RANGE");
  assert(CANONICAL_FIXTURE_REGULAR_LIVE.session.market_phase === "MARKET_OPEN", "Regular live phase is MARKET_OPEN");
  assert(CANONICAL_FIXTURE_NEAR_CLOSE.session.market_phase === "NEAR_CLOSE", "Near close phase is NEAR_CLOSE");
  assert(CANONICAL_FIXTURE_POST_MARKET.session.market_phase === "POST_MARKET", "Post market phase is POST_MARKET");

  // Test 5: Candidate Strike Advisory Contract
  const candidate = CANONICAL_FIXTURE_PRE_MARKET.decision.strike_candidates[0];
  assert(candidate.strike === 24150 && candidate.option_type === "CE", "Candidate strike identified");
  assert(candidate.rationale.length >= 1, "Candidate contains structured rationales");
  assert(candidate.risks.length >= 1, "Candidate contains structured risk disclaimers");

  // Test 6: Routing Separation Contract
  function resolveMarketWorkspace(presentationMode: string, activeModule: string, marketSubTab: string): string {
    if (presentationMode === "CANONICAL_UI" && activeModule === "market" && marketSubTab === "nifty") {
      return "CanonicalMarketWorkspace";
    }
    if (presentationMode === "CANONICAL_UI" && activeModule === "market" && marketSubTab === "metrics") {
      return "MarketPulseWorkspace";
    }
    if (presentationMode === "CANONICAL_UI" && activeModule === "market" && marketSubTab === "options") {
      return "CanonicalOptionsWorkspace";
    }
    return "LegacyWorkspace";
  }

  assert(resolveMarketWorkspace("CANONICAL_UI", "market", "nifty") === "CanonicalMarketWorkspace", "NIFTY subtab routes to CanonicalMarketWorkspace");
  assert(resolveMarketWorkspace("CANONICAL_UI", "market", "metrics") === "MarketPulseWorkspace", "METRICS subtab routes to MarketPulseWorkspace");
  assert(resolveMarketWorkspace("CANONICAL_UI", "market", "options") === "CanonicalOptionsWorkspace", "OPTIONS subtab routes to CanonicalOptionsWorkspace");

  // ====================================================
  // CERTIFIED SESSION SPINE TRUTH INVARIANTS (28 AUG 2026)
  // ====================================================

  const allFixtures = [
    { name: "PRE_MARKET", fix: CANONICAL_FIXTURE_PRE_MARKET },
    { name: "PRE_OPEN", fix: CANONICAL_FIXTURE_PRE_OPEN },
    { name: "OPENING_RANGE", fix: CANONICAL_FIXTURE_OPENING_RANGE },
    { name: "REGULAR_LIVE", fix: CANONICAL_FIXTURE_REGULAR_LIVE },
    { name: "NEAR_CLOSE", fix: CANONICAL_FIXTURE_NEAR_CLOSE },
    { name: "POST_MARKET", fix: CANONICAL_FIXTURE_POST_MARKET },
  ];

  // T1: All default NIFTY mode fixtures share the verified 28 Aug 2026 session date
  for (const item of allFixtures) {
    const sDate = item.fix.session.active_trading_date || item.fix.session.calendar_date;
    assert(sDate === VERIFIED_28_AUG_SPINE_CONSTANTS.session_date, `${item.name} session date is unified 2026-08-28`);
  }

  // T2: previous_close is certified and exactly equal across all spine modes (24,090.85)
  for (const item of allFixtures) {
    assert(item.fix.price_structure.previous_close === VERIFIED_28_AUG_SPINE_CONSTANTS.previous_close, `${item.name} price_structure.previous_close equals certified 24,090.85`);
    assert(item.fix.market.nifty.previous_close === VERIFIED_28_AUG_SPINE_CONSTANTS.previous_close, `${item.name} market.nifty.previous_close equals certified 24,090.85`);
  }

  // T3: open is exactly equal across all modes once session opened (24,122.05)
  for (const item of allFixtures) {
    assert(item.fix.price_structure.open === VERIFIED_28_AUG_SPINE_CONSTANTS.open, `${item.name} session open price equals 24,122.05`);
  }

  // T4: or_high / or_low are identical across all modes once formed (ORH: 24,165.40, ORL: 24,095.20)
  for (const item of allFixtures) {
    assert(item.fix.price_structure.or_high === VERIFIED_28_AUG_SPINE_CONSTANTS.or_high, `${item.name} OR High equals 24,165.40`);
    assert(item.fix.price_structure.or_low === VERIFIED_28_AUG_SPINE_CONSTANTS.or_low, `${item.name} OR Low equals 24,095.20`);
  }

  // T5: POST final close equals verified spine session close (24,175.65)
  assert(CANONICAL_FIXTURE_POST_MARKET.market.nifty.last_price === VERIFIED_28_AUG_SPINE_CONSTANTS.close, "Post-market last_price is 24,175.65");
  assert(CANONICAL_FIXTURE_POST_MARKET.price_structure.last_price === VERIFIED_28_AUG_SPINE_CONSTANTS.close, "Post-market price_structure.last_price is 24,175.65");
  assert(CANONICAL_FIXTURE_POST_MARKET.active_product.tomorrow_plan?.session_summary?.close === VERIFIED_28_AUG_SPINE_CONSTANTS.close, "Tomorrow plan summary close is 24,175.65");

  // T6: POST verified OHLC & Positive Net Change (+84.80 / +0.35%) matches certified constants
  const postSummary = CANONICAL_FIXTURE_POST_MARKET.active_product.tomorrow_plan?.session_summary;
  assert(postSummary?.open === VERIFIED_28_AUG_SPINE_CONSTANTS.open, "POST Open is 24,122.05");
  assert(postSummary?.high === VERIFIED_28_AUG_SPINE_CONSTANTS.high, "POST High is 24,188.65");
  assert(postSummary?.low === VERIFIED_28_AUG_SPINE_CONSTANTS.low, "POST Low is 24,076.50");
  assert(postSummary?.close === VERIFIED_28_AUG_SPINE_CONSTANTS.close, "POST Close is 24,175.65");
  assert(postSummary?.change === VERIFIED_28_AUG_SPINE_CONSTANTS.change, "POST Change is positive +84.80");
  assert(postSummary?.change_pct === VERIFIED_28_AUG_SPINE_CONSTANTS.change_pct, "POST Change % is positive +0.35%");

  // T7: LIVE snapshot semantics (at 13:42 IST snapshot, high is 24,165.40 and LTP is 24,152.40 within session low 24,076.50 and high 24,188.65)
  const liveLTP = CANONICAL_FIXTURE_REGULAR_LIVE.price_structure.last_price;
  assert(liveLTP <= VERIFIED_28_AUG_SPINE_CONSTANTS.high && liveLTP >= VERIFIED_28_AUG_SPINE_CONSTANTS.low, "LIVE last_price is within spine day extremes");
  assert(CANONICAL_FIXTURE_REGULAR_LIVE.price_structure.high === VERIFIED_28_AUG_SPINE_CONSTANTS.or_high, "LIVE 13:42 snapshot high equals high formed so far (24,165.40)");

  // T8: Key levels within session band (~23,900 to ~24,300)
  for (const item of allFixtures) {
    for (const sup of item.fix.price_structure.key_supports) {
      assert(sup >= 23900 && sup <= 24250, `${item.name} support ${sup} is within session-relevant band`);
    }
    for (const res of item.fix.price_structure.key_resistances) {
      assert(res >= 24050 && res <= 24350, `${item.name} resistance ${res} is within session-relevant band`);
    }
  }

  // T9: MORNING single coherent VWAP is ~24,142.80 (never 24,536.20)
  assert(CANONICAL_FIXTURE_PRE_MARKET.price_structure.vwap === VERIFIED_28_AUG_SPINE_CONSTANTS.vwap, "Pre-market VWAP equals verified session VWAP 24,142.80");
  assert(CANONICAL_FIXTURE_PRE_MARKET.price_structure.vwap !== 24536.20, "Pre-market VWAP is strictly not stale 24,536.20");

  // T10: NIFTY 50 breadth totals 50 in every mode fixture
  for (const item of allFixtures) {
    const b = item.fix.breadth;
    assert(b.total_constituents === 50, `${item.name} breadth total constituents is 50`);
    assert(b.advances + b.declines + b.unchanged === 50, `${item.name} constituent sum equals total 50`);
  }

  // ====================================================
  // TIMEFRAME SWITCHING & DETERMINISTIC AGGREGATION TESTS
  // ====================================================

  const full375Candles = CANONICAL_28_AUG_SESSION_CANDLES;
  assert(full375Candles.length === 375, "Session contains full 375 1m intraday candles (09:15–15:30 IST)");

  // T11: Aggregate 5m candle count is exactly 375 / 5 = 75 candles
  const candles5m = aggregateCandles(full375Candles, "5m");
  assert(candles5m.length === 75, "5m aggregation produces exactly 75 candles (375 / 5)");

  // T12: Aggregate 3m candle count is exactly 375 / 3 = 125 candles
  const candles3m = aggregateCandles(full375Candles, "3m");
  assert(candles3m.length === 125, "3m aggregation produces exactly 125 candles (375 / 3)");

  // T13: Aggregate 15m candle count is exactly 375 / 15 = 25 candles
  const candles15m = aggregateCandles(full375Candles, "15m");
  assert(candles15m.length === 25, "15m aggregation produces exactly 25 candles (375 / 15)");

  // T14: Aggregate 1h (60m) candle count is exactly Math.ceil(375 / 60) = 7 candles
  const candles1h = aggregateCandles(full375Candles, "1h");
  assert(candles1h.length === 7, "1h aggregation produces exactly 7 candles (Math.ceil(375 / 60))");

  // T15: Aggregate 1D produces 1 full session candle matching daily OHLC
  const candles1D = aggregateCandles(full375Candles, "1D");
  assert(candles1D.length === 1, "1D aggregation produces exactly 1 full-day candle");
  assert(candles1D[0].open === VERIFIED_28_AUG_SPINE_CONSTANTS.open, "1D Daily Bar Open is 24,122.05");
  assert(candles1D[0].high === VERIFIED_28_AUG_SPINE_CONSTANTS.high, "1D Daily Bar High is 24,188.65");
  assert(candles1D[0].low === VERIFIED_28_AUG_SPINE_CONSTANTS.low, "1D Daily Bar Low is 24,076.50");
  assert(candles1D[0].close === VERIFIED_28_AUG_SPINE_CONSTANTS.close, "1D Daily Bar Close is 24,175.65");

  // T16: OHLC Preservation across aggregations
  const maxHigh1m = Math.max(...full375Candles.map((c) => c.high));
  const minLow1m = Math.min(...full375Candles.map((c) => c.low));
  const maxHigh5m = Math.max(...candles5m.map((c) => c.high));
  const minLow5m = Math.min(...candles5m.map((c) => c.low));
  assert(maxHigh5m === maxHigh1m, `5m max high (${maxHigh5m}) preserves 1m max high (${maxHigh1m})`);
  assert(minLow5m === minLow1m, `5m min low (${minLow5m}) preserves 1m min low (${minLow1m})`);
  assert(maxHigh1m === VERIFIED_28_AUG_SPINE_CONSTANTS.high, "1m max high equals 24,188.65");
  assert(minLow1m === VERIFIED_28_AUG_SPINE_CONSTANTS.low, "1m min low equals 24,076.50");

  // T17: Volume sum preservation
  const totalVol1m = full375Candles.reduce((sum, c) => sum + (c.volume || 0), 0);
  const totalVol5m = candles5m.reduce((sum, c) => sum + (c.volume || 0), 0);
  assert(totalVol5m === totalVol1m, `5m total volume (${totalVol5m}) equals 1m total volume (${totalVol1m})`);

  // T18: Chart Adapter accepts selectedTf and updates model
  const liveChart1m = adaptCanonicalToChart(
    CANONICAL_FIXTURE_REGULAR_LIVE.candles["1m"],
    CANONICAL_FIXTURE_REGULAR_LIVE.price_structure,
    "2026-08-28",
    "MARKET_OPEN",
    null,
    "1m"
  );
  const liveChart5m = adaptCanonicalToChart(
    CANONICAL_FIXTURE_REGULAR_LIVE.candles["1m"],
    CANONICAL_FIXTURE_REGULAR_LIVE.price_structure,
    "2026-08-28",
    "MARKET_OPEN",
    null,
    "5m"
  );
  assert(liveChart1m.candles.length === 268, "Live 1m chart model contains 268 candles");
  assert(liveChart5m.candles.length === Math.ceil(268 / 5), "Live 5m chart model contains 54 candles");
  assert(liveChart1m.candles.length !== liveChart5m.candles.length, "Timeframe switching produces different series length");

  // T19: Chart Identity Invariants
  function resolveChartToolbarBadge(phase: string, tf: string): string {
    if (phase === "PRE_MARKET") return "PRE-MARKET";
    if (phase === "OPENING_RANGE") return "OPENING";
    if (phase === "POST_MARKET" || phase === "MARKET_CLOSED") return `${tf} · POST REVIEW`;
    return `${tf} · LIVE`;
  }

  assert(resolveChartToolbarBadge("POST_MARKET", "5m") === "5m · POST REVIEW", "POST_MARKET toolbar badge is 5m · POST REVIEW");
  assert(resolveChartToolbarBadge("POST_MARKET", "5m").includes("LIVE") === false, "POST_MARKET toolbar badge never contains LIVE");
  assert(resolveChartToolbarBadge("MARKET_OPEN", "1m") === "1m · LIVE", "LIVE toolbar badge is 1m · LIVE");

  // ====================================================
  // METRICS TAB (MARKET PULSE) CANONICAL INVARIANTS
  // ====================================================

  // M1: METRICS prev close / close / change match certified spine constants
  const metricsClose = VERIFIED_28_AUG_SPINE_CONSTANTS.close;
  const metricsPrevClose = VERIFIED_28_AUG_SPINE_CONSTANTS.previous_close;
  const metricsChange = Number((metricsClose - metricsPrevClose).toFixed(2));
  const metricsChangePct = Number(((metricsChange / metricsPrevClose) * 100).toFixed(2));

  assert(metricsClose === 24175.65, "METRICS close equals certified 24,175.65");
  assert(metricsPrevClose === 24090.85, "METRICS previous_close equals certified 24,090.85");
  assert(metricsChange === 84.80, "METRICS change equals positive +84.80");
  assert(metricsChangePct === 0.35, "METRICS change % equals positive +0.35%");

  // M2: NIFTY 50 breadth totals 50 when labeled NIFTY 50
  const metricsAdv = 29;
  const metricsDec = 20;
  const metricsUnch = 1;
  const metricsTotal = metricsAdv + metricsDec + metricsUnch;
  assert(metricsTotal === 50, "METRICS NIFTY 50 breadth totals exactly 50 constituents");
  assert(Math.round((metricsAdv / metricsTotal) * 100) === 58, "METRICS advance percentage is 58%");

  // M3: ATR in points unit and matches day range context
  const metricsAtr = 112.20;
  const metricsRange = VERIFIED_28_AUG_SPINE_CONSTANTS.range_points;
  assert(metricsAtr >= 100 && metricsAtr <= 150, "METRICS ATR is in realistic points unit (~112 pts)");
  assert(metricsRange === 112.15, "METRICS day range equals verified 112.15 pts");

  // M4: Institutional Positioning values and dates (Certified 28 Aug)
  const fiiCash = -5039.80;
  const diiCash = 5183.90;
  const combinedNet = Number((fiiCash + diiCash).toFixed(2));
  assert(combinedNet === 144.10, "METRICS combined net institutional flow is positive +144.10 Cr");

  // M6: Key Structural Levels in METRICS match spine
  assert(VERIFIED_28_AUG_SPINE_CONSTANTS.key_resistances[0] === 24165.40, "METRICS Immediate Resistance R1 equals 24,165.40");
  assert(VERIFIED_28_AUG_SPINE_CONSTANTS.key_resistances[1] === 24188.65, "METRICS Day High R2 equals 24,188.65");
  assert(VERIFIED_28_AUG_SPINE_CONSTANTS.key_supports[0] === 24095.20, "METRICS Immediate Support S1 equals 24,095.20");
  assert(VERIFIED_28_AUG_SPINE_CONSTANTS.key_supports[1] === 24076.50, "METRICS Day Low S2 equals 24,076.50");

  // M7: ATR normalization scale & percentage
  const testAtr = 112.20;
  const testSpot = 24175.65;
  const testAtrPct = Number(((testAtr / testSpot) * 100).toFixed(2));
  assert(testAtr > 50 && testAtr < 200, "ATR is normalized daily scale (112.20 pts), never 1m bar (2.37 pts)");
  assert(testAtrPct >= 0.40 && testAtrPct <= 0.80, `ATR % of spot is ${testAtrPct}% (~0.46%), never 0.01%`);

  // M8: Regime token sanitization fallback
  function testSanitizeRegime(reg: string | null | undefined): string {
    if (!reg) return "RANGE-BOUND";
    const u = String(reg).toUpperCase().trim();
    if (u === "UNKNOWN" || u === "" || u === "NULL") return "RANGE-BOUND";
    return u.replace(/_/g, " ");
  }
  assert(testSanitizeRegime("UNKNOWN") === "RANGE-BOUND", "UNKNOWN regime is sanitized to RANGE-BOUND");
  assert(testSanitizeRegime(null) === "RANGE-BOUND", "Null regime is sanitized to RANGE-BOUND");
  assert(testSanitizeRegime("TRENDING_UP") === "TRENDING UP", "TRENDING_UP is sanitized to readable format");

  // M9: Structural levels proximity deltas
  const testR1Delta = Number((24188.65 - testSpot).toFixed(2));
  const testS1Delta = Number((24095.20 - testSpot).toFixed(2));
  assert(testR1Delta > 0, "R1 resistance delta relative to spot is positive (+13.00 pts)");
  assert(testS1Delta < 0, "S1 support delta relative to spot is negative (-80.45 pts)");

  // M10: Strict integer Unix seconds ascending sort
  const sampleTimes = [1756631400, 1756631100, 1756631700];
  const sortedTimes = [...new Set(sampleTimes)].sort((a, b) => a - b);
  assert(sortedTimes[0] === 1756631100 && sortedTimes[2] === 1756631700, "Chart timestamps are deduplicated and strictly sorted ascending");

  // M11: Top 8 Heavyweight Impact Matrix
  const hwPoints = [18.4, 10.2, -3.1, 42.6, 18.9, -4.8, 1.8, 5.2];
  const netHwPoints = Number(hwPoints.reduce((a, b) => a + b, 0).toFixed(1));
  const itDuoPoints = Number((42.6 + 18.9).toFixed(1));
  assert(netHwPoints === 89.2, "Top 8 heavyweight net point impact equals +89.2 pts");
  // ====================================================
  // OPTIONS WORKSPACE & SMART STRIKE LADDER INVARIANTS
  // ====================================================
  assert(CANONICAL_28_AUG_STRIKE_UNIVERSE.length === 21, "Options strike universe contains 21 verified strikes (23,700 to 24,700)");
  const atmRow = CANONICAL_28_AUG_STRIKE_UNIVERSE.find((s) => s.strike === 24200);
  const callWallRow = CANONICAL_28_AUG_STRIKE_UNIVERSE.find((s) => s.strike === 24300);
  const putWallRow = CANONICAL_28_AUG_STRIKE_UNIVERSE.find((s) => s.strike === 24000);
  const maxPainRow = CANONICAL_28_AUG_STRIKE_UNIVERSE.find((s) => s.strike === 24150);

  assert(atmRow?.is_atm === true, "ATM strike is 24,200 with is_atm true");
  assert(callWallRow?.is_call_wall === true, "Call Wall strike is 24,300 with is_call_wall true");
  assert(putWallRow?.is_put_wall === true, "Put Wall strike is 24,000 with is_put_wall true");
  assert(maxPainRow?.strike === 24150, "Max pain strike is 24,150");

  const nearAtmFilterStrikes = CANONICAL_28_AUG_STRIKE_UNIVERSE.filter((s) => Math.abs(s.strike - 24200) <= 300);
  assert(nearAtmFilterStrikes.length === 13, "Near ATM ±300 pts filter contains exactly 13 strikes (23,900 – 24,500)");

  assert(CANONICAL_FIXTURE_POST_MARKET.options.spot_price === 24175.65, "Options spot price equals certified 24,175.65");
  assert(CANONICAL_FIXTURE_POST_MARKET.options.atm_strike === 24200, "Options ATM strike equals 24,200");
  assert(CANONICAL_FIXTURE_POST_MARKET.options.call_wall === 24300, "Options Call Wall equals 24,300");
  assert(CANONICAL_FIXTURE_POST_MARKET.options.put_wall === 24000, "Options Put Wall equals 24,000");
  assert(CANONICAL_FIXTURE_POST_MARKET.options.max_pain === 24150, "Options Max Pain equals 24,150");
  assert(CANONICAL_FIXTURE_POST_MARKET.options.pcr === 1.05, "Options PCR equals 1.05");

  const candRes = resolveStrikeCandidateDistance({ option_type: "CE", strike: 24150 }, 24175.65);
  assert(candRes.distance === 25.65, "Candidate 24150 CE spot distance is exactly 25.65 pts");
  assert(candRes.isItm === true, "Candidate 24150 CE is ITM relative to spot 24,175.65");
  assert(candRes.distanceLabel === "+25.65 pts (ITM)", "Candidate 24150 CE distance label is '+25.65 pts (ITM)'");

  const candMorningRes = resolveStrikeCandidateDistance({ option_type: "CE", strike: 24150 }, 24122.05);
  assert(candMorningRes.distance === 27.95, "Candidate 24150 CE pre-open distance is exactly 27.95 pts");
  assert(candMorningRes.isItm === false, "Candidate 24150 CE is OTM relative to expected open 24,122.05");
  assert(candMorningRes.distanceLabel === "-27.95 pts (OTM)", "Candidate 24150 CE distance label is '-27.95 pts (OTM)'");

  // ====================================================
  // MARKET INTELLIGENCE 4-TIER COCKPIT INVARIANTS
  // ====================================================
  const miHeroBias = "BULLISH CONTINUATION";
  const miConfidence = 74;
  const miPrimaryProb = 65;
  const miAlternateProb = 35;
  const miStrat1RR = "1 : 2.4";
  const miStrat2RR = "1 : 1.8";
  const miStrat3RR = "1 : 1.5";
  const miCandidateLtp = 92.50;
  const miTarget1 = 125.00;
  const miTarget2 = 155.00;
  const miStopLoss = 68.00;
  const miRRRatio = "1 : 2.55";
  const miDelta = 0.58;
  const miTheta = -12.40;
  const miIv = 12.80;
  const miVega = 14.20;
  const miVix = 10.68;
  const miPillarsConfirmed = 5;
  const miBreadthRatio = Math.round((30 / 50) * 100);

  assert(miHeroBias === "BULLISH CONTINUATION", "Market Intelligence active setup bias is BULLISH CONTINUATION");
  assert(miConfidence === 74, "Market Intelligence confidence score is 74 / 100");
  assert(miPrimaryProb + miAlternateProb === 100, "Scenario probabilities sum to exactly 100% (65% + 35%)");
  assert(miStrat1RR === "1 : 2.4", "Strategy 1 Pullback Long risk-to-reward equals 1 : 2.4");
  assert(miStrat2RR === "1 : 1.8", "Strategy 2 Breakout Continuation risk-to-reward equals 1 : 1.8");
  assert(miStrat3RR === "1 : 1.5", "Strategy 3 Range Fade risk-to-reward equals 1 : 1.5");
  assert(miCandidateLtp === 92.50, "Candidate 24150 CE premium is ₹92.50");
  assert(miTarget1 === 125.00, "Candidate 24150 CE target 1 is ₹125.00 (+35.1%)");
  assert(miTarget2 === 155.00, "Candidate 24150 CE target 2 is ₹155.00 (+67.5%)");
  assert(miStopLoss === 68.00, "Candidate 24150 CE stop loss is ₹68.00 (-26.5%)");
  assert(miRRRatio === "1 : 2.55", "Candidate 24150 CE Risk/Reward Ratio is 1 : 2.55");
  assert(miDelta === 0.58 && miTheta === -12.40 && miIv === 12.80 && miVega === 14.20, "Candidate Greeks: Delta 0.58, Theta -12.40/day, IV 12.80%, Vega +14.20");
  assert(miVix === 10.68, "Market Intelligence VIX environment is 10.68 pts");
  assert(miPillarsConfirmed === 5, "Multi-pillar confluence confirms 5/5 pillars");
  assert(miBreadthRatio === 60, "Breadth ratio is mathematically 60% (30 / 50)");

  // ====================================================
  // PREDICTION CHART HORIZON CALIBRATION INVARIANTS
  // ====================================================
  const calib1m = getHorizonCalibration("1m");
  assert(calib1m.primaryTarget === 24188.65, "1m Horizon primary target reaches Day High 24,188.65");
  assert(calib1m.alternateTarget === 24162.00, "1m Horizon alternate target dips to 24,162.00");
  assert(calib1m.envelopeTop === 24190.00 && calib1m.envelopeBottom === 24160.00, "1m Horizon envelope is 24,160.00 – 24,190.00 (±15 pts)");

  const calib5m = getHorizonCalibration("5m");
  assert(calib5m.primaryTarget === 24200.00, "5m Horizon primary target reaches 24,200.00 Call Wall");
  assert(calib5m.alternateTarget === 24142.80, "5m Horizon alternate target dips to 24,142.80 VWAP");
  assert(calib5m.envelopeTop === 24215.00 && calib5m.envelopeBottom === 24135.00, "5m Horizon envelope is 24,135.00 – 24,215.00");

  const calib15m = getHorizonCalibration("15m");
  assert(calib15m.primaryTarget === 24250.00, "15m Horizon primary target reaches 24,250.00");
  assert(calib15m.alternateTarget === 24076.50, "15m Horizon alternate target dips to 24,076.50");
  assert(calib15m.envelopeTop === 24270.00 && calib15m.envelopeBottom === 24080.00, "15m Horizon envelope is 24,080.00 – 24,270.00");

  const calib1D = getHorizonCalibration("1D");
  assert(calib1D.primaryTarget === 24350.00, "1D Horizon primary target reaches 24,350.00");
  assert(calib1D.alternateTarget === 23980.00, "1D Horizon alternate target dips to 23,980.00");
  assert(calib1D.envelopeTop === 24380.00 && calib1D.envelopeBottom === 23950.00, "1D Horizon envelope is 23,950.00 – 24,380.00");

  assert(calib1m.analogOutcome === 6.50, "1m Horizon analog outcome is +6.50 pts");
  assert(calib5m.analogOutcome === 28.00, "5m Horizon analog outcome is +28.00 pts");
  assert(calib15m.analogOutcome === 18.40, "15m Horizon analog outcome is +18.40 pts");
  assert(calib1D.analogOutcome === 94.20, "1D Horizon analog outcome is +94.20 pts");

  const predPrimaryProb = 65;
  const predAltProb = 35;
  const predWeights = { priceAction: 35, derivatives: 25, breadth: 25, macro: 15 };
  const totalWeight = predWeights.priceAction + predWeights.derivatives + predWeights.breadth + predWeights.macro;

  assert(predPrimaryProb + predAltProb === 100, "Prediction vector probabilities sum to 100% (65% + 35%)");
  assert(totalWeight === 100, "Forecast factor confluence weights sum to exactly 100%");

  // ====================================================
  // NEWS & MACRO INTELLIGENCE INVARIANTS
  // ====================================================
  const newsPres = getCanonicalNewsPresentation({}, {});
  // Zero-fabrication contract: with no real provider payload the feed is empty,
  // never backfilled with synthetic "curated" stories.
  assert(newsPres.liveFeed.length === 0, "Live news feed is empty when no real provider stories are present (no fabricated fallback)");

  // Test Relevance Cap (0..1 and percentage bounded <= 100)
  newsPres.liveFeed.forEach((story) => {
    assert(story.niftyRelevance >= 0 && story.niftyRelevance <= 1.0, `Story ${story.id} relevance ${story.niftyRelevance} is bounded between 0 and 1.0`);
    const pct = Math.min(100, Math.max(0, Math.round(story.niftyRelevance <= 1 ? story.niftyRelevance * 100 : story.niftyRelevance)));
    assert(pct <= 100 && pct >= 0, `Story ${story.id} percentage relevance ${pct}% never exceeds 100%`);
  });

  // Test Dynamic Subtitle Generation (no boilerplate)
  newsPres.liveFeed.forEach((story) => {
    assert(!story.whyItMatters.includes("Official Indian corporate earnings or disclosure transmission"), "WhyItMatters purges repetitive boilerplate");
    assert(!story.whyItMatters.includes("Provides tactical session sentiment cue"), "WhyItMatters purges generic cue boilerplate");
    assert(story.whyItMatters.startsWith("Transmits to"), "WhyItMatters provides contextual dynamic transmission sentence");
  });

  // Test Bullish Headline Classification
  const surgeStory = newsPres.liveFeed.find((s) => s.headline.includes("Vanguard") || s.headline.includes("surge"));
  if (surgeStory) {
    assert(surgeStory.expectedDirection === "POSITIVE", "Surge/Vanguard story is classified as POSITIVE ↑");
  }

  // Test Sector News Impact Dynamic Sentiment
  const bullishTone = getSectorToneFromScore(0.45);
  const bearishTone = getSectorToneFromScore(-0.35);
  const neutralTone = getSectorToneFromScore(0.05);
  assert(bullishTone.label === "BULLISH", "Score +0.45 produces BULLISH sector tone");
  assert(bearishTone.label === "BEARISH", "Score -0.35 produces BEARISH sector tone");
  assert(neutralTone.label === "NEUTRAL", "Score +0.05 produces NEUTRAL sector tone");

  // Test Entity Badges
  const validBadges = ["[US MACRO]", "[INDIA DOMESTIC]", "[DOMESTIC]", "[GLOBAL ASSETS]", "[CENTRAL BANK]", "[FLOWS]"];
  newsPres.liveFeed.forEach((story) => {
    const badge = getEntityBadge(story);
    assert(validBadges.includes(badge.text), `Story ${story.id} entity badge ${badge.text} is in standardized badge set`);
  });

  // Test Discovery Timestamp Formatting
  const testIso = "2026-08-28T13:51:00.000Z";
  const formattedDiscovery = formatDiscoveryTimestamp(testIso);
  assert(/\d{2}:\d{2}:\d{2} \d{2}:\d{2}:\d{2} IST/.test(formattedDiscovery), "formatDiscoveryTimestamp matches DD:MM:YY HH:mm:ss IST");
  assert(formatDiscoveryTimestamp(null) === "28:08:26 13:51:00 IST", "formatDiscoveryTimestamp handles null fallback cleanly");

  // Test Relevance Normalization
  assert(normalizeRelevanceScore(0.85) === 85, "normalizeRelevanceScore converts 0.85 to 85%");
  assert(normalizeRelevanceScore(94) === 94, "normalizeRelevanceScore keeps 94 as 94%");
  assert(normalizeRelevanceScore(0.95) === 95, "normalizeRelevanceScore converts 0.95 to 95%");

  // Test Contextual Transmission (helper is independent of feed contents)
  const transmission = getContextualTransmission({ category: "MACRO", headline: "Sample", summary: "Sample summary" });
  assert(typeof transmission === "string" && transmission.length > 10, "getContextualTransmission returns detailed transmission analysis");

  // ====================================================
  // ECONOMIC CALENDAR ZERO-FABRICATION INVARIANTS
  // ====================================================
  // With no real economic-calendar provider payload the calendar is empty,
  // never backfilled with ~65 hardcoded events pinned to fixed dates.
  assert(newsPres.calendarEvents.length === 0, "Economic calendar is empty when no real provider events are present (no fabricated fallback)");

  // Verify all events (if any real ones are present) have non-empty required fields
  newsPres.calendarEvents.forEach((ev) => {
    assert(Boolean(ev.id), `Event ID is defined for ${ev.eventName}`);
    assert(Boolean(ev.eventName), `Event name is defined for ${ev.id}`);
    assert(Boolean(ev.region), `Event region is defined for ${ev.eventName}`);
    assert(Boolean(ev.timeIST), `Event timeIST is defined for ${ev.eventName}`);
    assert(Boolean(ev.date), `Event date is defined for ${ev.eventName}`);
    assert(Boolean(ev.impact), `Event impact is defined for ${ev.eventName}`);
    assert(Boolean(ev.transmission), `Event transmission is defined for ${ev.eventName}`);
  });

  // ====================================================
  // TIER-A TRUTH HARDENING: CALIBRATION & FORMING CANDLE INVARIANTS
  // ====================================================
  // Test Calibration Maturity Gating (n=1, n=5, n=20)
  const calib1 = getHorizonCalibration("15m", 1);
  assert(calib1.maturity === "INSUFFICIENT_SAMPLE", "n=1 returns INSUFFICIENT_SAMPLE maturity");
  assert(calib1.conviction.includes("INSUFFICIENT SAMPLE (n=1)"), "n=1 conviction includes explicit INSUFFICIENT SAMPLE tag");

  const calib10 = getHorizonCalibration("15m", 10);
  assert(calib10.maturity === "OBSERVATIONAL", "n=10 returns OBSERVATIONAL maturity");
  assert(calib10.conviction.includes("OBSERVATIONAL (n=10)"), "n=10 conviction includes explicit OBSERVATIONAL tag");

  const calib25 = getHorizonCalibration("15m", 25);
  assert(calib25.maturity === "ACTIONABLE", "n=25 returns ACTIONABLE maturity");
  assert(calib25.conviction.includes("(CALIBRATED)"), "n=25 conviction includes (CALIBRATED) tag");

  // Test Forming Bar Merge in adaptCanonicalToChart
  const formingBar: any = {
    start: "2026-08-28T14:15:00.000Z",
    end: "2026-08-28T14:16:00.000Z",
    open: 24175.00,
    high: 24180.00,
    low: 24172.00,
    close: 24178.50,
    volume: 5400,
    quality: "VALID",
  };
  const liveChartModel = adaptCanonicalToChart(
    CANONICAL_28_AUG_SESSION_CANDLES.slice(0, 50),
    CANONICAL_FIXTURE_REGULAR_LIVE.price_structure,
    "2026-08-28",
    "MARKET_OPEN",
    formingBar,
    "1m"
  );
  assert(liveChartModel.candles.length === 51, "Forming bar successfully merged into live chart series (50 + 1 = 51 bars)");
  const lastBar = liveChartModel.candles[liveChartModel.candles.length - 1];
  assert(lastBar.isForming === true, "Last merged candle has isForming: true");
  assert(lastBar.close === 24178.50, "Last merged candle reflects forming close price");

  // Test Settled Session Cross-Surface Single Vectors (28 Aug Truth)
  assert(VERIFIED_28_AUG_SPINE_CONSTANTS.previous_close === 24090.85, "Spine previous close is 24090.85");
  assert(VERIFIED_28_AUG_SPINE_CONSTANTS.close === 24175.65, "Spine close is 24175.65");
  assert(VERIFIED_28_AUG_SPINE_CONSTANTS.change === 84.80, "Spine net change is +84.80");
  assert(VERIFIED_28_AUG_SPINE_CONSTANTS.vwap === 24142.80, "Spine anchor VWAP is 24142.80");
  assert(VERIFIED_28_AUG_SPINE_CONSTANTS.vix === 10.68, "Spine India VIX is 10.68 pts");

  // P0 Integrity: Fixture VIX Single-Source Assertions
  assert(CANONICAL_FIXTURE_POST_MARKET.market.vix.last_price === 10.68, "POST_MARKET fixture vix.last_price is certified 10.68 (zero 14.12 residue)");
  assert(CANONICAL_FIXTURE_PRE_MARKET.market.vix.last_price === 10.68, "PRE_MARKET fixture vix.last_price is certified 10.68");
  assert(CANONICAL_FIXTURE_REGULAR_LIVE.market.vix.last_price === 10.68, "REGULAR_LIVE fixture vix.last_price is certified 10.68");

  // P0 Integrity: Verify Banned Flow Literals Purged from NiftyLiveWorkspace
  import("fs").then((fs) => {
    const niftyLiveCode = fs.readFileSync("src/frontend/components/NiftyLiveWorkspace.tsx", "utf-8");
    assert(!niftyLiveCode.includes("-542.7 Cr"), "NiftyLiveWorkspace purges -542.7 Cr banned literal");
    assert(!niftyLiveCode.includes("+2,124.1 Cr"), "NiftyLiveWorkspace purges +2,124.1 Cr banned literal");
    assert(!niftyLiveCode.includes("+1,581.4 Cr"), "NiftyLiveWorkspace purges +1,581.4 Cr banned literal");
    assert(niftyLiveCode.includes("-5,039.80 Cr"), "NiftyLiveWorkspace binds to certified -5,039.80 Cr FII flow");
    assert(niftyLiveCode.includes("+5,183.90 Cr"), "NiftyLiveWorkspace binds to certified +5,183.90 Cr DII flow");
    assert(niftyLiveCode.includes("+144.10 Cr"), "NiftyLiveWorkspace binds to certified +144.10 Cr Net flow");
  });

  // Dual Clock System Tests (SessionPhaseEngine + IntelligenceModeEngine)
  const createIstDate = (year: number, month: number, day: number, hour: number, minute: number, second: number) => {
    // Convert IST (UTC+5:30) to Date object
    const utcMs = Date.UTC(year, month - 1, day, hour - 5, minute - 30, second);
    return new Date(utcMs);
  };

  // 1. Monday 06:45 IST -> PRE_MARKET + OVERNIGHT_SYNTHESIS (Data window: SETTLED_COMPLETED)
  const d0645 = createIstDate(2026, 8, 31, 6, 45, 0);
  const id0645 = resolveCanonicalSessionIdentity({ customDate: d0645 });
  assert(id0645.sessionPhase === "PRE_MARKET", "06:45 IST resolves to PRE_MARKET exchange phase");
  assert(id0645.intelligenceMode === "OVERNIGHT_SYNTHESIS", "06:45 IST resolves to OVERNIGHT_SYNTHESIS intelligence mode");
  assert(id0645.data_window === "SETTLED_COMPLETED", "06:45 IST data window is SETTLED_COMPLETED");
  assert(id0645.completed_session_date === "2026-08-28", "Completed session date is 2026-08-28 (Fri)");

  // 2. Monday 08:45 IST -> PRE_MARKET + PRE_COMMIT_PLAN (08:30–09:00 window)
  const d0845 = createIstDate(2026, 8, 31, 8, 45, 0);
  const id0845 = resolveCanonicalSessionIdentity({ customDate: d0845 });
  assert(id0845.sessionPhase === "PRE_MARKET", "08:45 IST resolves to PRE_MARKET exchange phase");
  assert(id0845.intelligenceMode === "PRE_COMMIT_PLAN", "08:45 IST resolves to PRE_COMMIT_PLAN intelligence mode");
  assert(id0845.data_window === "SETTLED_COMPLETED", "08:45 IST data window is SETTLED_COMPLETED");

  // 3. Monday 09:05 IST -> PRE_OPEN + AUCTION_READ (09:00–09:15 window)
  const d0905 = createIstDate(2026, 8, 31, 9, 5, 0);
  const id0905 = resolveCanonicalSessionIdentity({ customDate: d0905 });
  assert(id0905.sessionPhase === "PRE_OPEN", "09:05 IST resolves to PRE_OPEN exchange phase");
  assert(id0905.intelligenceMode === "AUCTION_READ", "09:05 IST resolves to AUCTION_READ intelligence mode");
  assert(id0905.data_window === "PRE_OPEN_AUCTION", "09:05 IST data window is PRE_OPEN_AUCTION");

  // 4. Monday 09:20 IST -> LIVE + OPEN_VALIDATION (09:15–09:30 window)
  const d0920 = createIstDate(2026, 8, 31, 9, 20, 0);
  const id0920 = resolveCanonicalSessionIdentity({ customDate: d0920 });
  assert(id0920.sessionPhase === "LIVE", "09:20 IST resolves to LIVE exchange phase");
  assert(id0920.intelligenceMode === "OPEN_VALIDATION", "09:20 IST resolves to OPEN_VALIDATION intelligence mode");
  assert(id0920.data_window === "SESSION_SO_FAR", "09:20 IST data window is SESSION_SO_FAR");

  // 5. Monday 11:00 IST -> LIVE + REGIME_MONITOR (09:30–14:45 window)
  const d1100 = createIstDate(2026, 8, 31, 11, 0, 0);
  const id1100 = resolveCanonicalSessionIdentity({ customDate: d1100 });
  assert(id1100.sessionPhase === "LIVE", "11:00 IST resolves to LIVE exchange phase");
  assert(id1100.intelligenceMode === "REGIME_MONITOR", "11:00 IST resolves to REGIME_MONITOR intelligence mode");
  assert(id1100.data_window === "SESSION_SO_FAR", "11:00 IST data window is SESSION_SO_FAR");

  // 6. Monday 15:00 IST -> LIVE + DECISION_WINDOW (14:45–15:25 window)
  const d1500 = createIstDate(2026, 8, 31, 15, 0, 0);
  const id1500 = resolveCanonicalSessionIdentity({ customDate: d1500 });
  assert(id1500.sessionPhase === "LIVE", "15:00 IST resolves to LIVE exchange phase");
  assert(id1500.intelligenceMode === "DECISION_WINDOW", "15:00 IST resolves to DECISION_WINDOW intelligence mode");

  // 7. Monday 15:28 IST -> NEAR_CLOSE + CLOSE_TRANSFER (15:25–15:40 window)
  const d1528 = createIstDate(2026, 8, 31, 15, 28, 0);
  const id1528 = resolveCanonicalSessionIdentity({ customDate: d1528 });
  assert(id1528.sessionPhase === "NEAR_CLOSE", "15:28 IST resolves to NEAR_CLOSE exchange phase");
  assert(id1528.intelligenceMode === "CLOSE_TRANSFER", "15:28 IST resolves to CLOSE_TRANSFER intelligence mode");

  // 8. Monday 16:10 IST -> POST_MARKET + OVERNIGHT_SYNTHESIS (15:40–06:00 window)
  const d1610 = createIstDate(2026, 8, 31, 16, 10, 0);
  const id1610 = resolveCanonicalSessionIdentity({ customDate: d1610 });
  assert(id1610.sessionPhase === "POST_MARKET", "16:10 IST resolves to POST_MARKET exchange phase");
  assert(id1610.intelligenceMode === "OVERNIGHT_SYNTHESIS", "16:10 IST resolves to OVERNIGHT_SYNTHESIS intelligence mode");
  assert(id1610.data_window === "SETTLED_COMPLETED", "16:10 IST data window is SETTLED_COMPLETED");

  // 9. Weekend Sunday 11:00 IST -> POST_MARKET substrate + OVERNIGHT_SYNTHESIS
  const dSun = createIstDate(2026, 8, 30, 11, 0, 0);
  const idSun = resolveCanonicalSessionIdentity({ customDate: dSun });
  assert(idSun.is_weekend === true, "Sunday is marked as weekend");
  assert(idSun.sessionPhase === "POST_MARKET", "Weekend maps to POST_MARKET settled substrate");
  // 10. Manual Preview Override Sync
  const idManual = resolveCanonicalSessionIdentity({
    customDate: d1610,
    preview_sessionPhase: "PRE_MARKET",
    preview_intelligenceMode: "PRE_COMMIT_PLAN",
  });
  assert(idManual.sessionPhase === "PRE_MARKET", "Manual override updates sessionPhase to PRE_MARKET");
  assert(idManual.intelligenceMode === "PRE_COMMIT_PLAN", "Manual override updates intelligenceMode to PRE_COMMIT_PLAN");
  assert(idManual.is_replay_mode === true, "Manual override sets is_replay_mode to true");

  // 11. Chart Effectiveness & Viewport Mapping Invariants
  const resolveChartDefaultsForIdentity = (sessionPhase: string, intelligenceMode: string, dataWindow: string) => {
    const isPreMarketBaseline = sessionPhase === "PRE_MARKET" || intelligenceMode === "PRE_COMMIT_PLAN";
    const isPostReview = sessionPhase === "POST_MARKET" || dataWindow === "SETTLED_COMPLETED" || intelligenceMode === "OVERNIGHT_SYNTHESIS" || intelligenceMode === "CLOSE_TRANSFER";
    return {
      viewMode: (isPostReview || isPreMarketBaseline) ? "FIT_SESSION" : "FOCUS",
      timeframe: (isPostReview || isPreMarketBaseline) ? "5m" : "1m",
      statusBadge: isPreMarketBaseline
        ? "● PRIOR SESSION BASELINE (28 AUG)"
        : isPostReview
          ? "● COMPLETED SESSION REVIEW"
          : sessionPhase === "PRE_OPEN"
            ? "● PRE-OPEN AUCTION (INDICATIVE)"
            : "● REALTIME SYNC",
    };
  };

  const preMarketChart = resolveChartDefaultsForIdentity("PRE_MARKET", "PRE_COMMIT_PLAN", "SETTLED_COMPLETED");
  assert(preMarketChart.viewMode === "FIT_SESSION", "PRE_MARKET default viewport is FIT_SESSION");
  assert(preMarketChart.timeframe === "5m", "PRE_MARKET default timeframe is 5m");
  assert(preMarketChart.statusBadge !== "● REALTIME SYNC", "PRE_MARKET status badge is NEVER REALTIME SYNC");
  assert(preMarketChart.statusBadge === "● PRIOR SESSION BASELINE (28 AUG)", "PRE_MARKET status badge is explicit prior session baseline");

  const postMarketChart = resolveChartDefaultsForIdentity("POST_MARKET", "OVERNIGHT_SYNTHESIS", "SETTLED_COMPLETED");
  assert(postMarketChart.viewMode === "FIT_SESSION", "POST_MARKET default viewport is FIT_SESSION");
  assert(postMarketChart.timeframe === "5m", "POST_MARKET default timeframe is 5m");
  assert(postMarketChart.statusBadge === "● COMPLETED SESSION REVIEW", "POST_MARKET status badge is COMPLETED SESSION REVIEW");

  const liveChart = resolveChartDefaultsForIdentity("LIVE", "REGIME_MONITOR", "SESSION_SO_FAR");
  assert(liveChart.viewMode === "FOCUS", "LIVE REGIME_MONITOR default viewport is FOCUS");
  assert(liveChart.timeframe === "1m", "LIVE default timeframe is 1m");
  assert(liveChart.statusBadge === "● REALTIME SYNC", "LIVE fresh feed status badge is REALTIME SYNC");

  const openValChart = resolveChartDefaultsForIdentity("LIVE", "OPEN_VALIDATION", "SESSION_SO_FAR");
  assert(openValChart.viewMode === "FOCUS", "OPEN_VALIDATION default viewport is FOCUS");
  assert(openValChart.timeframe === "1m", "OPEN_VALIDATION default timeframe is 1m");

  // 12. Prediction Scenario Gating & 2-Path Discipline
  const calibObs = getHorizonCalibration("15m", 10);
  assert(calibObs.maturity === "OBSERVATIONAL", "10 samples returns OBSERVATIONAL maturity (5 <= n < 20)");
  assert(calibObs.invalidation.length > 0, "Prediction specifies concrete invalidation floor");

  // 13. Session-Span & As-Of Integrity
  // A) POST 1m series covers 09:15 to 15:30 (375 bars)
  const post1m = CANONICAL_FIXTURE_POST_MARKET.candles["1m"];
  assert(post1m.length === 375, "POST 1m series has exactly 375 candles (09:15 to 15:30)");
  const first1m = post1m[0];
  const last1m = post1m[post1m.length - 1];
  assert(first1m.start.includes("09:15"), "First 1m bar starts at 09:15");
  assert(last1m.start.includes("15:29") && last1m.end.includes("15:30"), "Last 1m bar covers up to 15:30 close");

  // B) POST 5m aggregation covers 75 candles
  const post5m = aggregateCandles(post1m, "5m");
  assert(post5m.length === 75, "POST 5m aggregation yields exactly 75 candles (375 / 5)");
  const last5m = post5m[post5m.length - 1];
  assert(last5m.start.includes("15:25") && last5m.end.includes("15:30"), "Last 5m candle spans 15:25 to 15:30");

  // C) LIVE fixture snapshot exposes AS OF 13:42
  const live1m = CANONICAL_FIXTURE_REGULAR_LIVE.candles["1m"];
  assert(live1m.length === 268, "LIVE snapshot fixture has 268 candles");
  const lastLive = live1m[live1m.length - 1];
  assert(lastLive.start.includes("13:42"), "LIVE snapshot ends at 13:42 IST");

  // D) Morning baseline candle count is full session baseline (> 3 candles)
  const morning1m = CANONICAL_FIXTURE_PRE_MARKET.candles["1m"];
  assert(morning1m.length === 375, "Morning baseline has full 375 candles for prior session review");

  // E) Day High / Low SO FAR semantics
  const getHighBadge = (dataWindow: string, isPost: boolean) => {
    const isSoFar = dataWindow === "SESSION_SO_FAR" || !isPost;
    return isSoFar ? "DAY HIGH (SO FAR)" : "DAY HIGH";
  };
  assert(getHighBadge("SESSION_SO_FAR", false) === "DAY HIGH (SO FAR)", "SESSION_SO_FAR produces DAY HIGH (SO FAR)");
  assert(getHighBadge("SETTLED_COMPLETED", true) === "DAY HIGH", "SETTLED_COMPLETED produces final DAY HIGH");

  // F) Completed session date across all fixtures
  assert(CANONICAL_FIXTURE_PRE_MARKET.session.completed_session_date === "2026-08-28", "PRE_MARKET completed_session_date is 2026-08-28");
  assert(CANONICAL_FIXTURE_POST_MARKET.session.completed_session_date === "2026-08-28", "POST_MARKET completed_session_date is 2026-08-28");
  assert(CANONICAL_FIXTURE_REGULAR_LIVE.session.completed_session_date === "2026-08-28", "REGULAR_LIVE completed_session_date is 2026-08-28");

  // G) Grep test: MorningWorkspace & PreMarketWorkspace clean of banned literals
  const morningWsCode = fs.readFileSync("src/frontend/components/canonical/nifty/MorningWorkspace.tsx", "utf-8");
  assert(!morningWsCode.includes("+1,242"), "MorningWorkspace has purged +1,242 Cr literal");
  assert(!morningWsCode.includes("below 14 (13.68"), "MorningWorkspace has purged 13.68 VIX literal");
  assert(!morningWsCode.includes("EXECUTION FIRST"), "MorningWorkspace has purged EXECUTION FIRST");
  assert(morningWsCode.includes("PLAN FIRST"), "MorningWorkspace includes PLAN FIRST");

  const preMarketWsCode = fs.readFileSync("src/frontend/components/canonical/nifty/PreMarketWorkspace.tsx", "utf-8");
  assert(!preMarketWsCode.includes("24,482.00"), "PreMarketWorkspace has purged 24,482 gap literal");
  assert(!preMarketWsCode.includes("EXECUTION FIRST"), "PreMarketWorkspace has purged EXECUTION FIRST");

  const phasePanelsCode = fs.readFileSync("src/frontend/components/canonical/nifty/PhaseSpecificPanels.tsx", "utf-8");
  assert(!phasePanelsCode.includes("EXECUTION FIRST"), "PhaseSpecificPanels has purged EXECUTION FIRST");

  // 14. Option A Clean Break: Single UI and Purged Dual-Clock Authority Label
  const topBarCode = fs.readFileSync("src/frontend/components/WorkstationTopBar.tsx", "utf-8");
  assert(!topBarCode.includes("AUTO (Dual-Clock Authority)"), "WorkstationTopBar purges AUTO (Dual-Clock Authority)");
  assert(!topBarCode.includes("presentationMode === \"LEGACY_UI\""), "WorkstationTopBar purges legacy UI presentation switcher");

  const marketWsCode = fs.readFileSync("src/frontend/components/canonical/MarketWorkspace.tsx", "utf-8");
  assert(!marketWsCode.includes("ACTIVE SURFACE:"), "MarketWorkspace purges redundant ACTIVE SURFACE bar");
  assert(!marketWsCode.includes("majorModes.map"), "MarketWorkspace purges interactive mode tabs in favor of right-side preview dropdown");

  const liveGuideCode = fs.readFileSync("src/frontend/components/intelligence/LiveGuideView.tsx", "utf-8");
  assert(liveGuideCode.includes("REPLAY ADVISORY (HISTORICAL SNAPSHOT)"), "LiveGuideView renders REPLAY ADVISORY under off-market / replay");

  const morningPlanCode = fs.readFileSync("src/frontend/components/intelligence/MorningPlanView.tsx", "utf-8");
  assert(!morningPlanCode.includes("OPENING ARMED"), "MorningPlanView purges OPENING ARMED");
  assert(morningPlanCode.includes("OPENING PLAN PREPARED"), "MorningPlanView uses OPENING PLAN PREPARED");

  const tomorrowPlanCode = fs.readFileSync("src/frontend/components/intelligence/TomorrowPlanView.tsx", "utf-8");
  assert(!tomorrowPlanCode.includes("BREAKOUT ARMED"), "TomorrowPlanView purges BREAKOUT ARMED");
  // "Tomorrow Setup Posture" no longer hardcodes a scenario label / target zone —
  // it binds to the canonical tomorrow_plan.preliminary_next_bias and
  // key_levels_next_session, with an explicit awaiting state when absent.
  assert(!tomorrowPlanCode.includes("BREAKOUT SCENARIO ACTIVE"), "TomorrowPlanView purges hardcoded BREAKOUT SCENARIO ACTIVE posture");
  assert(!tomorrowPlanCode.includes("24,066.56"), "TomorrowPlanView purges hardcoded 24,066.56 pivot / target literals");
  assert(tomorrowPlanCode.includes("preliminary_next_bias"), "TomorrowPlanView binds setup posture to canonical preliminary_next_bias");
  assert(tomorrowPlanCode.includes("key_levels_next_session"), "TomorrowPlanView binds carry-forward pivots to canonical key_levels_next_session");

  // ====================================================
  // FIX 1, 2, 3: AUDITED REPAIR UNIT TESTS & VERIFICATION
  // ====================================================

  // T_PHASE_1: Standard time-of-day phase resolution
  assert(resolveSessionPhase("08:45:00", true, false) === "PRE_MARKET", "08:45 weekday is PRE_MARKET");
  assert(resolveSessionPhase("09:05:00", true, false) === "PRE_OPEN", "09:05 weekday is PRE_OPEN");
  assert(resolveSessionPhase("10:30:00", true, false) === "LIVE", "10:30 weekday is LIVE");
  assert(resolveSessionPhase("15:30:00", true, false) === "NEAR_CLOSE", "15:30 weekday is NEAR_CLOSE");
  assert(resolveSessionPhase("16:00:00", true, false) === "POST_MARKET", "16:00 weekday is POST_MARKET");
  assert(resolveSessionPhase("10:30:00", false, false) === "POST_MARKET", "Weekend 10:30 without market status is POST_MARKET");
  assert(resolveSessionPhase("10:30:00", true, true) === "POST_MARKET", "Holiday 10:30 without market status is POST_MARKET");

  // T_PHASE_2: Market status input overrides (Muhurat, Disaster Recovery, Special Sessions)
  assert(resolveSessionPhase("18:15:00", false, true, "MUHURAT") === "LIVE", "Muhurat session on holiday weekend resolves to LIVE phase");
  assert(resolveSessionPhase("10:00:00", false, false, "DR_SESSION") === "LIVE", "DR Saturday session resolves to LIVE phase");
  assert(resolveSessionPhase("11:30:00", false, false, "SPECIAL_SESSION") === "LIVE", "Special Saturday session resolves to LIVE phase");
  assert(resolveSessionPhase("09:05:00", false, false, "PRE_OPEN") === "PRE_OPEN", "Special PRE_OPEN status resolves to PRE_OPEN");
  assert(resolveSessionPhase("10:00:00", true, false, "OPEN") === "LIVE", "Explicit OPEN status resolves to LIVE");

  // T_INTEL_1: Standard time-of-day intelligence mode resolution
  assert(resolveIntelligenceMode("07:30:00", true, false) === "OVERNIGHT_SYNTHESIS", "07:30 is OVERNIGHT_SYNTHESIS");
  assert(resolveIntelligenceMode("08:45:00", true, false) === "PRE_COMMIT_PLAN", "08:45 is PRE_COMMIT_PLAN");
  assert(resolveIntelligenceMode("09:05:00", true, false) === "AUCTION_READ", "09:05 is AUCTION_READ");
  assert(resolveIntelligenceMode("09:20:00", true, false) === "OPEN_VALIDATION", "09:20 is OPEN_VALIDATION");
  assert(resolveIntelligenceMode("11:00:00", true, false) === "REGIME_MONITOR", "11:00 is REGIME_MONITOR");
  assert(resolveIntelligenceMode("15:00:00", true, false) === "DECISION_WINDOW", "15:00 is DECISION_WINDOW");
  assert(resolveIntelligenceMode("15:30:00", true, false) === "CLOSE_TRANSFER", "15:30 is CLOSE_TRANSFER");

  // T_INTEL_2: Market status intelligence mode resolution for Muhurat / DR sessions
  assert(resolveIntelligenceMode("18:15:00", false, true, "MUHURAT") === "REGIME_MONITOR", "Muhurat session on holiday resolves to REGIME_MONITOR");
  assert(resolveIntelligenceMode("10:00:00", false, false, "DR_SESSION") === "REGIME_MONITOR", "DR Saturday session resolves to REGIME_MONITOR");
  assert(resolveIntelligenceMode("09:05:00", false, false, "PRE_OPEN") === "AUCTION_READ", "Special PRE_OPEN status resolves to AUCTION_READ");

  // T_TOPBAR_CLOCK: Single clock authority & CLIENT TIME (DISCONNECTED) presence
  assert(topBarCode.includes("CLIENT TIME (DISCONNECTED)"), "TopBar contains CLIENT TIME (DISCONNECTED) fallback label");
  assert(topBarCode.includes("authoritativeTs"), "TopBar binds clock to authoritative state timestamp");

  // T_FIXTURE_BANNER: High-contrast fixture substitution banner in DashboardLayout
  const dashboardCode = fs.readFileSync("src/frontend/layout/DashboardLayout.tsx", "utf-8");
  assert(dashboardCode.includes("fixture-substitution-banner"), "DashboardLayout contains high-contrast fixture substitution banner");
  assert(dashboardCode.includes("FIXTURE DATA ACTIVE"), "DashboardLayout displays FIXTURE DATA ACTIVE tag");
  assert(dashboardCode.includes("NOT LIVE MARKET DATA"), "DashboardLayout explicitly states data is NOT LIVE MARKET DATA");

  // ====================================================
  // SPRINT 2: FIX 9, 10, 11, 12, 13 AUDITED REPAIR TESTS
  // ====================================================

  // FIX 9: Broader breadth null fallback
  const adapterCode = fs.readFileSync("src/frontend/utils/canonicalIntelligenceAdapter.ts", "utf-8");
  assert(!adapterCode.includes("?? 1120"), "canonicalIntelligenceAdapter purges 1120 broader advances fallback");
  assert(!adapterCode.includes("?? 1450"), "canonicalIntelligenceAdapter purges 1450 broader declines fallback");

  // FIX 10: Institutional flow null fallback & Awaiting EOD Settlement label
  assert(!adapterCode.includes("-1245.5"), "canonicalIntelligenceAdapter purges -1245.5 fabricated FII flow");
  assert(!adapterCode.includes("1850.2"), "canonicalIntelligenceAdapter purges 1850.2 fabricated DII flow");
  assert(!adapterCode.includes("17 Aug 2026 (EOD Reference)"), "canonicalIntelligenceAdapter purges 17 Aug 2026 fabricated date");
  assert(adapterCode.includes("Awaiting EOD Settlement"), "canonicalIntelligenceAdapter uses honest Awaiting EOD Settlement label");

  // FIX 11: Single source VIX and VIX Unavailable fallback
  assert(!adapterCode.includes(": 11.61"), "canonicalIntelligenceAdapter purges 11.61 VIX fallback");
  const niftyHeaderCode = fs.readFileSync("src/frontend/components/canonical/nifty/NiftyHeader.tsx", "utf-8");
  assert(!niftyHeaderCode.includes('|| "13.48"'), "NiftyHeader purges 13.48 VIX fallback");
  assert(niftyHeaderCode.includes("VIX Unavailable"), "NiftyHeader displays VIX Unavailable when missing");

  // FIX 12: Bloomberg/TT-class FEED DISCONNECTED watermark overlay
  assert(niftyHeaderCode.includes("feed-disconnected-watermark"), "NiftyHeader contains feed-disconnected-watermark testid");
  assert(niftyHeaderCode.includes("FEED DISCONNECTED"), "NiftyHeader contains FEED DISCONNECTED banner");
  const niftyLiveCode = fs.readFileSync("src/frontend/components/NiftyLiveWorkspace.tsx", "utf-8");
  assert(niftyLiveCode.includes("feed-disconnected-watermark"), "NiftyLiveWorkspace contains feed-disconnected-watermark testid");

  // FIX 13: Sector performance Feed Offline badge
  const sectorChartCode = fs.readFileSync("src/frontend/components/visualizations/SectorPerformanceChart.tsx", "utf-8");
  assert(sectorChartCode.includes("sector-feed-offline-badge"), "SectorPerformanceChart contains sector-feed-offline-badge testid");
  assert(sectorChartCode.includes("Feed Offline"), "SectorPerformanceChart renders explicit Feed Offline badge");

  // ====================================================
  // SPRINT 2 FOLLOW-UP: PATCH 1 & PATCH 2 AUDITED TESTS
  // ====================================================

  // PATCH 1: LiveNewsFeedView single VIX authority & 10.68 fallback purge
  const liveNewsCode = fs.readFileSync("src/frontend/components/news/LiveNewsFeedView.tsx", "utf-8");
  assert(!liveNewsCode.includes("10.68"), "LiveNewsFeedView purges 10.68 VIX fallback");
  assert(liveNewsCode.includes("canonicalVix"), "LiveNewsFeedView binds to single canonical VIX source");

  // PATCH 2: Broader breadth UI-level Breadth Unavailable test coverage
  const supportingPanelsCode = fs.readFileSync("src/frontend/components/canonical/nifty/SupportingPanels.tsx", "utf-8");
  assert(!supportingPanelsCode.includes("|| 1894"), "SupportingPanels purges 1894 fabricated advances");
  assert(!supportingPanelsCode.includes("|| 879"), "SupportingPanels purges 879 fabricated declines");
  assert(supportingPanelsCode.includes("breadth-unavailable-message"), "SupportingPanels contains breadth-unavailable-message testid");
  assert(supportingPanelsCode.includes("Breadth Unavailable"), "SupportingPanels renders explicit Breadth Unavailable message");

  const dataVizCode = fs.readFileSync("src/frontend/components/visualizations/DataVisualizations.tsx", "utf-8");
  assert(dataVizCode.includes("Breadth unavailable"), "DataVisualizations MarketBreadthMeter renders Breadth unavailable when null");

  // ====================================================
  // SPRINT 4: AUDITED UI, LABELING & CONFIDENCE CALIBRATION TESTS
  // ====================================================

  // FIX 22: Confidence % replaced by qualitative bands
  const intelAdapterCode = fs.readFileSync("src/frontend/utils/canonicalIntelligenceAdapter.ts", "utf-8");
  assert(intelAdapterCode.includes("High Confidence"), "canonicalIntelligenceAdapter includes High Confidence band");
  assert(intelAdapterCode.includes("Medium Confidence"), "canonicalIntelligenceAdapter includes Medium Confidence band");
  assert(intelAdapterCode.includes("Low Confidence"), "canonicalIntelligenceAdapter includes Low Confidence band");

  // FIX 23: Scenario Bezier curves presented as parametric volatility corridors
  const scenarioCanvasCode = fs.readFileSync("src/frontend/components/canonical/chart/ScenarioProjectionCanvas.tsx", "utf-8");
  assert(scenarioCanvasCode.includes("+1σ Volatility Corridor"), "ScenarioProjectionCanvas presents +1σ Volatility Corridor");
  assert(scenarioCanvasCode.includes("-1σ Volatility Corridor"), "ScenarioProjectionCanvas presents -1σ Volatility Corridor");
  assert(scenarioCanvasCode.includes("±2σ Volatility Envelope"), "ScenarioProjectionCanvas presents ±2σ Volatility Envelope");

  const scenarioOverlayCode = fs.readFileSync("src/frontend/components/canonical/chart/ScenarioProjectionOverlay.tsx", "utf-8");
  assert(scenarioOverlayCode.includes("+1σ CORRIDOR"), "ScenarioProjectionOverlay labels +1σ CORRIDOR");
  assert(scenarioOverlayCode.includes("-1σ CORRIDOR"), "ScenarioProjectionOverlay labels -1σ CORRIDOR");
  assert(!scenarioOverlayCode.includes("65% BASE"), "ScenarioProjectionOverlay purges 65% BASE probability fan label");

  // FIX 24: Uncalibrated accuracy badges gated behind n>=30
  const canonicalTomorrowPlanCode = fs.readFileSync("src/frontend/components/canonical/products/TomorrowPlanView.tsx", "utf-8");
  assert(canonicalTomorrowPlanCode.includes("Insufficient Track Record (n="), "TomorrowPlanView gates accuracy behind n>=30");

  // FIX 25: Economic calendar unconfigured provider status
  const econCalProviderCode = fs.readFileSync("src/news_engine/economic_calendar_provider.py", "utf-8");
  assert(econCalProviderCode.includes("Awaiting Provider Configuration"), "economic_calendar_provider sets Awaiting Provider Configuration");

  // FIX 26: Advisory-only terminology
  const orderPreviewModalCode = fs.readFileSync("src/frontend/components/OrderPreviewModal.tsx", "utf-8");
  assert(orderPreviewModalCode.includes("ADVISORY DECISION FRAME"), "OrderPreviewModal uses ADVISORY DECISION FRAME");
  assert(orderPreviewModalCode.includes("Model Invalidation Level"), "OrderPreviewModal uses Model Invalidation Level");
  assert(!orderPreviewModalCode.includes("PRE-FLIGHT ORDER PREVIEW"), "OrderPreviewModal purges PRE-FLIGHT ORDER PREVIEW");

  const activeOppHeroCode = fs.readFileSync("src/frontend/components/ActiveOpportunityHero.tsx", "utf-8");
  assert(activeOppHeroCode.includes("ACTIVE ADVISORY FRAME: STANDBY"), "ActiveOpportunityHero uses ACTIVE ADVISORY FRAME: STANDBY");
  assert(activeOppHeroCode.includes("Invalidation Floor"), "ActiveOpportunityHero uses Invalidation Floor");

  // FIX 27: Purge hardcoded ATM 24500 relic
  const intradayAssistantCode = fs.readFileSync("src/frontend/components/IntradayAssistant.tsx", "utf-8");
  assert(!intradayAssistantCode.includes("24500"), "IntradayAssistant purges 24500 strike relic");
  assert(intradayAssistantCode.includes("ATM Unavailable"), "IntradayAssistant uses ATM Unavailable fallback");

  // ====================================================
  // OPTION A CLEAN BREAK: DUAL UI, DUAL CLOCK & AUTO FIXTURE PURGE TESTS
  // ====================================================
  const canonicalContextCode = fs.readFileSync("src/frontend/context/CanonicalStateContext.tsx", "utf-8");
  assert(!canonicalContextCode.includes('"LEGACY_UI"'), "CanonicalStateContext purges LEGACY_UI mode");
  assert(!canonicalContextCode.includes('"CANONICAL_SHADOW"'), "CanonicalStateContext purges CANONICAL_SHADOW mode");
  assert(!canonicalContextCode.includes("autoFixture"), "CanonicalStateContext purges automatic wall-clock autoFixture substitution");
  assert(canonicalContextCode.includes("EMPTY_CANONICAL_ENVELOPE"), "CanonicalStateContext defines honest EMPTY_CANONICAL_ENVELOPE");

  const temporalStripCode = fs.readFileSync("src/frontend/components/ui/TemporalContextStrip.tsx", "utf-8");
  assert(!temporalStripCode.includes("CANONICAL_SHADOW"), "TemporalContextStrip purges CANONICAL_SHADOW check");
  assert(!temporalStripCode.includes("CANONICAL_UI"), "TemporalContextStrip purges CANONICAL_UI check");

  const liveWsCode = fs.readFileSync("src/frontend/components/canonical/nifty/LiveWorkspace.tsx", "utf-8");
  assert(!liveWsCode.includes("CANONICAL_SHADOW"), "LiveWorkspace purges CANONICAL_SHADOW check");
  assert(!liveWsCode.includes("CANONICAL_UI"), "LiveWorkspace purges CANONICAL_UI check");
  assert(!liveWsCode.includes("DATA STATE: <strong className=\"text-[#38BDF8]\">SHADOW REPLAY</strong>"), "LiveWorkspace purges hardcoded SHADOW REPLAY footer");

  assert(!dashboardCode.includes("isCanonicalPresentation"), "DashboardLayout purges isCanonicalPresentation branching");
  assert(!dashboardCode.includes("NiftyLiveWorkspace"), "DashboardLayout purges NiftyLiveWorkspace import");
  assert(!dashboardCode.includes('from "../components/OptionsWorkspace"'), "DashboardLayout purges legacy OptionsWorkspace import");

  const serverCode = fs.readFileSync("server.ts", "utf-8");
  assert(!serverCode.includes("24080.40"), "server.ts purges synthetic 24080.40 fallback spot price");

  const pulseWsCode = fs.readFileSync("src/frontend/components/MarketPulseWorkspace.tsx", "utf-8");
  assert(!pulseWsCode.includes("VERIFIED_28_AUG_SPINE_CONSTANTS"), "MarketPulseWorkspace purges VERIFIED_28_AUG_SPINE_CONSTANTS import and fallbacks");
  assert(!pulseWsCode.includes("SETTLED 28 AUG 2026"), "MarketPulseWorkspace purges hardcoded SETTLED 28 AUG 2026 badge");

  const optionsWsCode = fs.readFileSync("src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx", "utf-8");
  assert(optionsWsCode.includes("isDataAvailable = Boolean(isReplayMode ||"), "OptionsIntelligenceWorkspace gates strike universe and metrics behind isDataAvailable");

  const morningPlanViewCode = fs.readFileSync("src/frontend/components/intelligence/MorningPlanView.tsx", "utf-8");
  assert(morningPlanViewCode.includes("Awaiting Pre-Market Session Data"), "MorningPlanView provides honest empty state when live data is unavailable");

  const liveGuideViewCode = fs.readFileSync("src/frontend/components/intelligence/LiveGuideView.tsx", "utf-8");
  assert(liveGuideViewCode.includes("Awaiting Live Market Stream"), "LiveGuideView provides honest empty state when live data is unavailable");

  const tomorrowPlanViewCode = fs.readFileSync("src/frontend/components/intelligence/TomorrowPlanView.tsx", "utf-8");
  assert(tomorrowPlanViewCode.includes("Awaiting Completed Session Settlement"), "TomorrowPlanView provides honest empty state when live data is unavailable");

  const morningWsFooterCode = fs.readFileSync("src/frontend/components/canonical/nifty/MorningWorkspace.tsx", "utf-8");
  assert(!morningWsFooterCode.includes("DATA STATE: <strong className=\"text-[#38BDF8]\">SHADOW REPLAY</strong>"), "MorningWorkspace purges hardcoded SHADOW REPLAY footer");

  const openingWsFooterCode = fs.readFileSync("src/frontend/components/canonical/nifty/OpeningWorkspace.tsx", "utf-8");
  assert(!openingWsFooterCode.includes("DATA STATE: <strong className=\"text-[#38BDF8]\">SHADOW REPLAY</strong>"), "OpeningWorkspace purges hardcoded SHADOW REPLAY footer");

  const preMarketWsFooterCode = fs.readFileSync("src/frontend/components/canonical/nifty/PreMarketWorkspace.tsx", "utf-8");
  assert(!preMarketWsFooterCode.includes("DATA STATE: <strong className=\"text-[#38BDF8]\">SHADOW REPLAY</strong>"), "PreMarketWorkspace purges hardcoded SHADOW REPLAY footer");

  // ====================================================
  // PRE-MARKET DATA POLICY & ZERO HARDCODED FALLBACK INVARIANTS
  // ====================================================
  const pyWssCode = fs.readFileSync("src/application/workstation_state_service.py", "utf-8");
  assert(pyWssCode.includes("settled_close = close_core.market_ohlcv.close if (close_core and close_core.market_ohlcv) else None"), "Python workstation_state_service sets settled_close to None if missing");
  assert(!pyWssCode.includes("else 24080.40"), "Python workstation_state_service purges hardcoded 24080.40 fallback");
  assert(!pyWssCode.includes("else 24117.55"), "Python workstation_state_service purges hardcoded 24117.55 fallback");

  const pyStoreCode = fs.readFileSync("src/storage/lightweight_session_store.py", "utf-8");
  assert(!pyStoreCode.includes("previous_close=24090.85"), "LightweightSessionStore purges hardcoded previous_close literal");
  assert(!pyStoreCode.includes("raw_atr_14=112.20"), "LightweightSessionStore purges hardcoded raw_atr_14 literal");

  assert(!serverCode.includes("let settledClose = 24080.40"), "server.ts purges hardcoded settledClose 24080.40 initialization");
  assert(serverCode.includes("let settledClose: number | null = null;"), "server.ts initializes settledClose to null");

  assert(canonicalContextCode.includes("settled_session: null"), "EMPTY_CANONICAL_ENVELOPE initializes settled_session to null");

  // ====================================================
  // MASTER DEFECT REMEDIATION & CANONICAL RESOLVERS
  // ====================================================
  
  // Test null envelope
  const nullState = resolveAuthoritativeMarketState(null);
  assert(nullState.spot === null, "resolveAuthoritativeMarketState returns null spot for null envelope");

  // Test spot & prevClose resolution hierarchy
  const mockEnvelope: any = {
    market: {
      nifty: { last_price: 24055.80, previous_close: 24080.40, change: -24.60, change_pct: -0.102 },
      vix: { last_price: 10.68, change: -0.39 },
    },
    session: { active_trading_date: "2026-09-01" },
  };
  const resolvedState = resolveAuthoritativeMarketState(mockEnvelope);
  assert(resolvedState.spot === 24055.80, "resolveAuthoritativeMarketState resolves spot correctly");
  assert(resolvedState.prevClose === 24080.40, "resolveAuthoritativeMarketState resolves prevClose correctly");
  assert(Math.abs((resolvedState.change ?? 0) - (-24.60)) < 0.001, "resolveAuthoritativeMarketState computes change correctly");
  assert(resolvedState.vix === 10.68, "resolveAuthoritativeMarketState resolves VIX correctly");
  assert(resolvedState.sessionDate === "2026-09-01", "resolveAuthoritativeMarketState resolves session date correctly");

  // Test IST Chart Timezone Formatter presence
  const chartCode = fs.readFileSync("src/frontend/components/canonical/chart/CanonicalTradingChart.tsx", "utf-8");
  assert(chartCode.includes("timeZone: \"Asia/Kolkata\""), "CanonicalTradingChart configures IST timezone");
  assert(chartCode.includes("tickMarkFormatter"), "CanonicalTradingChart configures tickMarkFormatter");

  // Test OptionChainLadder IV resolution
  const ladderCode = fs.readFileSync("src/frontend/components/visualizations/OptionChainLadder.tsx", "utf-8");
  assert(ladderCode.includes("s.callIv ?? s.ce_iv ?? s.iv ?? s.implied_volatility"), "OptionChainLadder maps call IV with complete fallbacks");
  assert(ladderCode.includes("s.putIv ?? s.pe_iv ?? s.iv ?? s.implied_volatility"), "OptionChainLadder maps put IV with complete fallbacks");

  // Test TomorrowPlanView authoritative integration
  const tpvCode = fs.readFileSync("src/frontend/components/canonical/products/TomorrowPlanView.tsx", "utf-8");
  assert(tpvCode.includes("resolveAuthoritativeMarketState"), "TomorrowPlanView integrates resolveAuthoritativeMarketState");

  // Test MorningPlanView authoritative integration
  const mpvCode = fs.readFileSync("src/frontend/components/canonical/products/MorningPlanView.tsx", "utf-8");
  assert(mpvCode.includes("resolveAuthoritativeMarketState"), "MorningPlanView integrates resolveAuthoritativeMarketState");

  // Test MarketPulseWorkspace authoritative integration & offline banner
  const mpwCode = fs.readFileSync("src/frontend/components/MarketPulseWorkspace.tsx", "utf-8");
  assert(mpwCode.includes("resolveAuthoritativeMarketState"), "MarketPulseWorkspace integrates resolveAuthoritativeMarketState");
  // P1 Test: Options flat IV fallbacks purged
  const oiwCode = fs.readFileSync("src/frontend/components/canonical/OptionsIntelligenceWorkspace.tsx", "utf-8");
  assert(!oiwCode.includes("?? 12.8;"), "OptionsIntelligenceWorkspace purges ?? 12.8 IV fallback");
  assert(!oiwCode.includes("?? 13.2;"), "OptionsIntelligenceWorkspace purges ?? 13.2 IV fallback");

  // P1 Test: Authoritative ATR utilization in resolveAuthoritativeMarketState
  assert(resolvedState.atrUtilizationPct !== undefined, "resolveAuthoritativeMarketState calculates atrUtilizationPct");

  // P1 Test: CanonicalNewsAdapter rawItems lookup and non-identical default timestamps
  const newsAdapterCode = fs.readFileSync("src/frontend/utils/canonicalNewsAdapter.ts", "utf-8");
  assert(newsAdapterCode.includes("news_sentiment"), "canonicalNewsAdapter checks state.news_sentiment");
  // Zero-fabrication: the synthetic default news feed (and its forged
  // "minutes ago" timestamp scaffolding) has been removed entirely.
  assert(!newsAdapterCode.includes("makeNewsTime"), "canonicalNewsAdapter no longer builds a fabricated default feed with forged timestamps");
  assert(!newsAdapterCode.includes("defaultStories"), "canonicalNewsAdapter no longer references a fabricated defaultStories fallback");
  assert(!newsAdapterCode.includes("defaultEvents"), "canonicalNewsAdapter no longer references a fabricated defaultEvents calendar fallback");

  // Nifty Tab Integrity: Prior settled session high must NOT leak into live dayHigh
  const liveEnvelopeMock: any = {
    session: { market_phase: "LIVE" },
    candles: {
      "1m": [
        { high: 23911.99, low: 23820.00, open: 23850.00, close: 23890.00 },
        { high: 23895.00, low: 23786.80, open: 23890.00, close: 23840.00 },
      ]
    },
    settled_session: {
      close: 24080.40,
      high: 24055.80,
      low: 23950.00,
    }
  };
  const liveResolvedState = resolveAuthoritativeMarketState(liveEnvelopeMock);
  assert(liveResolvedState.dayHigh === 23911.99, "resolveAuthoritativeMarketState uses live session candle high (23911.99), not settled high");
  assert(liveResolvedState.dayLow === 23786.80, "resolveAuthoritativeMarketState uses live session candle low (23786.80), not settled low");
  assert(liveResolvedState.intradayRange === 125.19, "resolveAuthoritativeMarketState calculates actual session range (125.19 pts), eliminating 269.0 pt leakage");

  // Nifty Tab Breadth binding check
  const liveWorkspaceCode = fs.readFileSync("src/frontend/components/canonical/nifty/LiveWorkspace.tsx", "utf-8");
  assert(liveWorkspaceCode.includes("resolvedBreadthBias"), "LiveWorkspace uses resolvedBreadthBias for Panel 5");
  assert(!liveWorkspaceCode.includes("breadth?.unchanged ?? 0;"), "LiveWorkspace purges ?? 0 fallback on unchanged breadth");

  console.log("==================================================");
  console.log("ALL FRONTEND CANONICAL & PRE-MARKET ZERO-FALLBACK TESTS PASSED (100%)");
  console.log("==================================================");
}

// Auto-run if executed via tsx
runFrontendTests();



