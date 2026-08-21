import React from 'react';
import { normalizeModuleId, PrimaryModuleId } from '../src/frontend/context/NavigationContext';
import { PRIMARY_MODULES } from '../src/frontend/layout/DashboardLayout';
import { buildMarketIntelligenceViewModel } from '../src/frontend/viewmodels/buildMarketIntelligenceViewModel';

console.log("=== 1. SIDEBAR CONSOLIDATION SMOKE TEST ===");
console.log("Modules in PRIMARY_MODULES:", PRIMARY_MODULES.map(m => `${m.label} (id: ${m.id})`));
if (PRIMARY_MODULES.length !== 6) {
  throw new Error(`Expected 6 sidebar modules, found ${PRIMARY_MODULES.length}`);
}

console.log("\n=== 2. LEGACY SAVED-STATE MIGRATION TEST ===");
const testCases = [
  { input: "intelligence", expected: "market_intelligence" },
  { input: "market_insights", expected: "market_intelligence" },
  { input: "pre_market_briefing", expected: "market_intelligence" },
  { input: "market_intelligence_v2", expected: "market_intelligence" },
  { input: "market_intelligence", expected: "market_intelligence" },
  { input: "market", expected: "market" },
  { input: "news", expected: "news" },
  { input: "portfolio", expected: "portfolio" },
  { input: "trading_cheatsheet", expected: "trading_cheatsheet" },
  { input: "ardha_performance", expected: "ardha_performance" },
  { input: "invalid_key", expected: "market" }
];

testCases.forEach(({ input, expected }) => {
  const result = normalizeModuleId(input);
  if (result !== expected) {
    throw new Error(`Migration error for ${input}: got ${result}, expected ${expected}`);
  }
  console.log(`[PASS] Saved "${input}" -> Resolved "${result}"`);
});

console.log("\n=== 3. MARKET INTELLIGENCE VIEWMODEL PIPELINE SMOKE TEST ===");
const vm = buildMarketIntelligenceViewModel({
  market_session: { status: "OPEN" },
  market_data: { current_spot: 24238.55, spot_change: 56.40, vwap: 24235.10, breadth: { advances: 20, declines: 30 } }
});
console.log("Market Intelligence ViewModel generated cleanly:", {
  marketStatus: vm.marketStatus,
  corridorStatus: vm.corridor.status,
  spotPrice: vm.corridor.spotPrice,
  breadthBias: vm.participation.breadthBias,
  opportunityStatus: vm.opportunity.status
});

console.log("\n=== ALL SMOKE TESTS PASSED CLEANLY ===");
