// src/frontend/viewmodels/buildMarketIntelligenceViewModel.test.ts
import { buildMarketIntelligenceViewModel } from "./buildMarketIntelligenceViewModel";

function assert(condition: boolean, msg: string) {
  if (!condition) {
    throw new Error(`ASSERTION FAILED: ${msg}`);
  }
}

export function runViewModelTests() {
  console.log("=== RUNNING MARKET INTELLIGENCE VIEW MODEL BUILDER TESTS ===");

  // Test 1: Full Healthy Canonical State
  const healthyState = {
    runtime_id: "rt-test-1",
    state_sequence: 101,
    generated_at: "2026-08-21T10:00:00Z",
    market_session: { status: "OPEN", is_closed: false },
    market_data: {
      current_spot: 24238.55,
      spot_change: 56.40,
      spot_change_pct: 0.23,
      breadth: { advances: 20, declines: 30, unchanged: 0 },
      sectors: [{ sector: "NIFTY IT", change_percent: 1.2 }, { sector: "NIFTY AUTO", change_percent: -0.8 }],
      heavyweights: [{ symbol: "RELIANCE", change: 0.8 }, { symbol: "HDFCBANK", change: -0.2 }]
    },
    technical_analysis: {
      vwap: 24235.10,
      support_levels: [24218, 24180],
      resistance_levels: [24280, 24320]
    },
    options: {
      vix: 13.85,
      pcr: 1.15,
      call_wall: 24300,
      put_wall: 24100,
      max_pain: 24200
    },
    unified_intelligence: {
      market_regime: { regime_type: "TREND_PULLBACK", bias: "BULLISH", trend_strength: 72 },
      key_levels: { immediate_support: 24218, immediate_resistance: 24280 }
    },
    opportunity_intelligence: {
      best_opportunity: {
        has_trade: false,
        reason: "THRESHOLD_NOT_MET",
        message: "No qualified setup currently meets qualification thresholds."
      }
    }
  };

  const vm1 = buildMarketIntelligenceViewModel(healthyState);
  assert(vm1.runtimeId === "rt-test-1", "runtimeId mapped correctly");
  assert(vm1.sequenceNumber === 101, "sequenceNumber mapped correctly");
  assert(vm1.corridor.spotPrice === 24238.55, "spotPrice mapped");
  assert(vm1.corridor.vwap === 24235.10, "vwap mapped");
  assert(vm1.corridor.status === "ABOVE_VWAP", "corridor status ABOVE_VWAP");
  assert(vm1.participation.advances === 20, "advances mapped");
  assert(vm1.participation.declines === 30, "declines mapped");
  assert(vm1.participation.breadthBias === "NEGATIVE", "20 ADV / 30 DEC classified as NEGATIVE");
  assert(vm1.participation.hasDivergence === true, "Spot UP (+56.40) vs NEGATIVE breadth triggers divergence alert");
  assert(vm1.derivatives.pcr === 1.15, "PCR mapped");
  assert(vm1.derivatives.callWall === 24300, "callWall mapped");
  assert(vm1.derivatives.putWall === 24100, "putWall mapped");
  assert(vm1.derivatives.indiaVix === 13.85, "indiaVix mapped");
  assert(vm1.derivatives.volatilityRegime === "NORMAL", "VIX 13.85 classified as NORMAL volatility regime");
  assert(vm1.leadership.topAdvancingSector === "NIFTY IT", "topAdvancingSector mapped");
  assert(vm1.leadership.topDecliningSector === "NIFTY AUTO", "topDecliningSector mapped");
  assert(vm1.opportunity.hasQualifiedSetup === false, "hasQualifiedSetup is false when threshold not met");
  assert(vm1.opportunity.status === "STANDBY", "opportunity status is STANDBY");
  console.log("  [PASS] Test 1: Full Healthy Canonical State");

  // Test 2: Missing Breadth & Missing Options Null Semantics
  const partialState = {
    runtime_id: "rt-test-2",
    state_sequence: 102,
    generated_at: "2026-08-21T10:05:00Z",
    market_data: { current_spot: 24238.55 },
    technical_analysis: {},
    options: {}
  };

  const vm2 = buildMarketIntelligenceViewModel(partialState);
  assert(vm2.participation.advances === null, "missing advances is null");
  assert(vm2.participation.declines === null, "missing declines is null");
  assert(vm2.participation.breadthBias === "UNAVAILABLE", "missing breadth is UNAVAILABLE (not 0/0)");
  assert(vm2.derivatives.pcr === null, "missing PCR is null");
  assert(vm2.derivatives.callWall === null, "missing callWall is null");
  assert(vm2.derivatives.indiaVix === null, "missing VIX is null");
  assert(vm2.derivatives.source.availability === "UNAVAILABLE", "derivatives source is UNAVAILABLE");
  assert(vm2.corridor.vwap === null, "missing VWAP is null");
  assert(vm2.corridor.status === "UNAVAILABLE", "missing VWAP makes corridor status UNAVAILABLE (not false ABOVE/BELOW)");
  console.log("  [PASS] Test 2: Missing Data Null Semantics");

  // Test 3: Qualified Active Setup Mapping
  const activeTradeState = {
    runtime_id: "rt-test-3",
    opportunity_intelligence: {
      best_opportunity: {
        has_trade: true,
        opportunity: {
          setup_type: "TREND_PULLBACK_VWAP",
          priority_score: 78,
          direction: "BULLISH",
          proposal_id: "PROP-20260821-01"
        }
      }
    }
  };

  const vm3 = buildMarketIntelligenceViewModel(activeTradeState);
  assert(vm3.opportunity.hasQualifiedSetup === true, "hasQualifiedSetup is true when active trade present");
  assert(vm3.opportunity.setupName === "TREND_PULLBACK_VWAP", "setupName mapped");
  assert(vm3.opportunity.priorityScore === 78, "priorityScore mapped");
  assert(vm3.opportunity.direction === "BULLISH", "direction mapped");
  assert(vm3.opportunity.status === "QUALIFIED", "status is QUALIFIED");
  assert(vm3.opportunity.proposalId === "PROP-20260821-01", "proposalId mapped for deep linking");
  console.log("  [PASS] Test 3: Qualified Active Setup Mapping");

  console.log("=== ALL VIEW MODEL BUILDER TESTS PASSED SUCCESSFULLY ===");
}

if (require.main === module) {
  runViewModelTests();
}
