import React from 'react';
import { resolveMarketIntelligenceSession } from '../src/frontend/viewmodels/session/MarketIntelligenceSessionResolver';
import { buildSessionViewModels } from '../src/frontend/viewmodels/session/buildSessionViewModels';

console.log("=== 1. TEST AUTO SESSION RESOLUTION ===");
const times = [
  { time: "09:05 AM IST", date: new Date("2026-08-21T03:35:00Z"), expected: "MORNING_PLAN" },
  { time: "09:12 AM IST", date: new Date("2026-08-21T03:42:00Z"), expected: "MORNING_PLAN" },
  { time: "11:30 AM IST", date: new Date("2026-08-21T06:00:00Z"), expected: "LIVE_GUIDE" },
  { time: "03:26 PM IST", date: new Date("2026-08-21T09:56:00Z"), expected: "LIVE_GUIDE" },
  { time: "03:45 PM IST", date: new Date("2026-08-21T10:15:00Z"), expected: "TOMORROW_PLAN" }
];

times.forEach(t => {
  const res = resolveMarketIntelligenceSession({ customDate: t.date });
  if (res.effectiveSubTab !== t.expected) {
    throw new Error(`Timing mismatch for ${t.time}: expected ${t.expected}, got ${res.effectiveSubTab}`);
  }
  console.log(`[PASS] ${t.time} -> Resolved SubTab "${res.effectiveSubTab}" (Stage: ${res.lifecycleStage})`);
});

console.log("\n=== 2. TEST VIEW MODEL BUILDER FOR ALL 3 SUBVIEWS ===");
const canonicalFull = {
  market_data: {
    current_spot: 24268.40,
    spot_change: 68.20,
    spot_change_pct: 0.28,
    open: 24268.00,
    high: 24272.00,
    low: 24238.00,
    vwap: 24262.00,
    breadth: { advances: 27, declines: 21, unchanged: 2 }
  },
  option_intelligence: {
    pcr: 0.92,
    call_wall: 24500,
    put_wall: 24100,
    vix: 13.12
  },
  unified_intelligence: {
    market_regime: { bias: "BULLISH" },
    confidence: 65,
    key_levels: { immediate_support: 24210, immediate_resistance: 24380 }
  }
};

const vms = buildSessionViewModels(canonicalFull);
console.log("Morning Plan Best Plan:", vms.morningPlan.bestPlan);
console.log("Live Guide Best Action:", vms.liveGuide.bestActionNow);
console.log("Tomorrow Plan Best Plan:", vms.tomorrowPlan.bestPlan);
console.log("Tomorrow Strike Suggestions:", vms.tomorrowPlan.bestStrikeSuggestions);

console.log("\n=== ALL SESSION VIEW MODEL SMOKE TESTS PASSED CLEANLY ===");
