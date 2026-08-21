import React from 'react';
import { buildMarketIntelligenceViewModel } from '../src/frontend/viewmodels/buildMarketIntelligenceViewModel';

const mockState = {
  market_session: { status: "OPEN", is_closed: false },
  market_data: {
    current_spot: 24238.55,
    spot_change: 56.40,
    vwap: 24235.10,
    breadth: { advances: 20, declines: 30, unchanged: 0 },
    sectors: [
      { name: "METALS", change_percent: 1.25 },
      { name: "IT", change_percent: -0.85 }
    ],
    heavyweights: [
      { name: "RELIANCE", change: 5.2 },
      { name: "HDFCBANK", change: -2.1 },
      { name: "ICICIBANK", change: 3.4 }
    ]
  },
  option_intelligence: {
    pcr: 1.15,
    call_wall: 24300,
    put_wall: 24100,
    max_pain: 24200,
    vix: 13.85
  },
  unified_intelligence: {
    market_regime: { regime_type: "RANGE DAY", bias: "BULLISH", trend_strength: 62 },
    confidence: { overall_score: 71 },
    overall_view: "Constructive intraday structure above VWAP anchor.",
    session_story: {
      pre_market_report: { summary: "Pre-market outlook biased positive." },
      todays_analysis: { summary: "Intraday evolution holding support." },
      key_events: [
        { time: "09:15", event: "Market open above VWAP.", source: "PRICE_ACTION" }
      ]
    }
  },
  opportunity_intelligence: {
    best_opportunity: {
      has_trade: true,
      opportunity: {
        setup_type: "BULLISH_BREAKOUT",
        direction: "BULLISH",
        priority_score: 8.5,
        proposal_id: "prop_123"
      },
      message: "Qualified BULLISH_BREAKOUT active near 24,240."
    }
  }
};

const vm = buildMarketIntelligenceViewModel(mockState);
console.log("=== VIEWMODEL BUILDER VERIFICATION ===");
console.log("Regime Name:", vm.regime.name);
console.log("Regime Bias:", vm.regime.bias);
console.log("Corridor Status:", vm.corridor.status);
console.log("Spot Price:", vm.corridor.spotPrice);
console.log("VWAP:", vm.corridor.vwap);
console.log("Breadth:", vm.participation.advances, "ADV /", vm.participation.declines, "DEC");
console.log("Breadth Bias:", vm.participation.breadthBias);
console.log("Has Divergence:", vm.participation.hasDivergence);
console.log("Divergence Note:", vm.participation.divergenceNote);
console.log("PCR:", vm.derivatives.pcr);
console.log("VIX:", vm.derivatives.indiaVix);
console.log("Volatility Regime:", vm.derivatives.volatilityRegime);
console.log("Top Adv Sector:", vm.leadership.topAdvancingSector, vm.leadership.topAdvancingSectorPct);
console.log("Top Dec Sector:", vm.leadership.topDecliningSector, vm.leadership.topDecliningSectorPct);
console.log("Heavyweights:", vm.leadership.summary);
console.log("Morning Thesis:", vm.sessionStory.morningThesisSummary);
console.log("Current Evolution:", vm.sessionStory.currentEvolutionSummary);
console.log("Timeline Events:", vm.sessionStory.keyEvents.length);
console.log("Opportunity Status:", vm.opportunity.status);
console.log("Opportunity Setup:", vm.opportunity.setupName);
console.log("Opportunity Deep Link Proposal:", vm.opportunity.proposalId);
