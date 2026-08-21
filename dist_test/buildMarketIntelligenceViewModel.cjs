var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/frontend/viewmodels/buildMarketIntelligenceViewModel.ts
var buildMarketIntelligenceViewModel_exports = {};
__export(buildMarketIntelligenceViewModel_exports, {
  buildMarketIntelligenceViewModel: () => buildMarketIntelligenceViewModel
});
module.exports = __toCommonJS(buildMarketIntelligenceViewModel_exports);
function resolveSourceMeta(primaryTimestamp, hasValidData, isDegraded = false) {
  if (!hasValidData) {
    return { availability: "UNAVAILABLE", observedAt: null, source: null };
  }
  if (isDegraded) {
    return { availability: "DEGRADED", observedAt: primaryTimestamp || null, source: "CANONICAL_STATE" };
  }
  return { availability: "LIVE", observedAt: primaryTimestamp || null, source: "CANONICAL_STATE" };
}
function parseNumber(val) {
  if (val === null || val === void 0 || val === "" || typeof val === "boolean") return null;
  const num = Number(val);
  return isNaN(num) || !isFinite(num) ? null : num;
}
function buildMarketIntelligenceViewModel(canonicalState, optionalSessionEvidence) {
  const c = canonicalState || {};
  const runtimeId = c.runtime_id ? String(c.runtime_id) : null;
  const sequenceNumber = parseNumber(c.state_sequence);
  const generatedAt = c.generated_at ? String(c.generated_at) : (/* @__PURE__ */ new Date()).toISOString();
  const sessionStatus = String(c.market_session?.status || c.market_feed_status?.status || "OPEN").toUpperCase();
  let marketStatus = "OPEN";
  if (sessionStatus === "CLOSED" || c.market_session?.is_closed) {
    marketStatus = "CLOSED";
  } else if (sessionStatus === "PRE_MARKET") {
    marketStatus = "PRE_MARKET";
  } else if (sessionStatus === "POST_MARKET" || sessionStatus === "POST_CLOSE") {
    marketStatus = "POST_MARKET";
  } else if (sessionStatus === "HOLIDAY") {
    marketStatus = "HOLIDAY";
  }
  const mData = { ...c.marketContext || {}, ...c.market_data || {} };
  const tData = c.technical_analysis || {};
  const oData = { ...c.optionContext || {}, ...c.option_intelligence || {}, ...c.options || {} };
  const uData = c.unified_intelligence || {};
  const mScore = c.market_score || {};
  const macroData = c.macro_intelligence || {};
  const newsData = c.news_intelligence || {};
  const oppIntel = c.opportunity_intelligence || {};
  const obsTime = c.generated_at || mData.observed_at || mData.timestamp || null;
  const regimeObj = uData.market_regime || mScore || {};
  const regimeName = regimeObj.regime_type || regimeObj.regime || null;
  const rawBias = String(regimeObj.bias || mScore.bias || "").toUpperCase();
  const bias = rawBias === "BULLISH" ? "BULLISH" : rawBias === "BEARISH" ? "BEARISH" : rawBias === "NEUTRAL" ? "NEUTRAL" : null;
  const strengthScore = parseNumber(regimeObj.trend_strength ?? mScore.market_score);
  const confidencePct = parseNumber((c.confidence || {}).overall_score ?? uData.confidence);
  const regimeDesc = uData.overall_view || regimeObj.description || null;
  const regimeSource = resolveSourceMeta(obsTime, regimeName !== null || strengthScore !== null);
  const spotPrice = parseNumber(mData.current_spot ?? mData.last_price);
  const spotChange = parseNumber(mData.spot_change ?? mData.change ?? mData.change_points);
  const spotChangePct = parseNumber(mData.spot_change_pct ?? mData.change_percent);
  const vwap = parseNumber(tData.vwap ?? mData.vwap);
  const keyLevels = uData.key_levels || {};
  const supports = keyLevels.support_levels || tData.support_levels || [];
  const resistances = keyLevels.resistance_levels || tData.resistance_levels || [];
  const immediateSupport = parseNumber(keyLevels.immediate_support ?? supports[0]);
  const immediateResistance = parseNumber(keyLevels.immediate_resistance ?? resistances[0]);
  let corridorStatus = "UNAVAILABLE";
  if (spotPrice !== null && vwap !== null) {
    if (immediateResistance !== null && spotPrice > immediateResistance) {
      corridorStatus = "ABOVE_RESISTANCE";
    } else if (immediateSupport !== null && spotPrice < immediateSupport) {
      corridorStatus = "BELOW_SUPPORT";
    } else if (spotPrice >= vwap) {
      corridorStatus = "ABOVE_VWAP";
    } else {
      corridorStatus = "BELOW_VWAP";
    }
  }
  const corridorSource = resolveSourceMeta(obsTime, spotPrice !== null);
  const breadthObj = mData.breadth || {};
  const advances = parseNumber(breadthObj.advances);
  const declines = parseNumber(breadthObj.declines);
  const unchanged = parseNumber(breadthObj.unchanged);
  let breadthPct = null;
  let breadthBias = "UNAVAILABLE";
  let hasDivergence = null;
  let divergenceNote = null;
  if (advances !== null && declines !== null) {
    const total = advances + declines + (unchanged || 0);
    breadthPct = total > 0 ? Math.round(advances / total * 100) : null;
    if (advances > declines) {
      breadthBias = "POSITIVE";
    } else if (declines > advances) {
      breadthBias = "NEGATIVE";
    } else {
      breadthBias = "BALANCED";
    }
    if (spotChange !== null) {
      if (spotChange > 0 && breadthBias === "NEGATIVE") {
        hasDivergence = true;
        divergenceNote = `Spot change is positive (+${spotChange.toFixed(2)}) but market breadth is negative (${advances} ADV / ${declines} DEC).`;
      } else if (spotChange < 0 && breadthBias === "POSITIVE") {
        hasDivergence = true;
        divergenceNote = `Spot change is negative (${spotChange.toFixed(2)}) but market breadth is positive (${advances} ADV / ${declines} DEC).`;
      } else {
        hasDivergence = false;
      }
    }
  }
  const participationSource = resolveSourceMeta(obsTime, advances !== null && declines !== null);
  const pcr = parseNumber(oData.pcr);
  const callWall = parseNumber(oData.call_wall);
  const putWall = parseNumber(oData.put_wall);
  const maxPain = parseNumber(oData.max_pain);
  const indiaVix = parseNumber(oData.vix ?? macroData.india_vix?.value);
  let volatilityRegime = "UNAVAILABLE";
  if (indiaVix !== null) {
    if (indiaVix > 18) {
      volatilityRegime = "EXPANSION";
    } else if (indiaVix < 12) {
      volatilityRegime = "COMPRESSION";
    } else {
      volatilityRegime = "NORMAL";
    }
  }
  const derivativesSource = resolveSourceMeta(obsTime, pcr !== null || indiaVix !== null || callWall !== null);
  const sectors = Array.isArray(mData.sectors) ? mData.sectors : [];
  const heavyweights = Array.isArray(mData.heavyweights) ? mData.heavyweights : [];
  let topAdvancingSector = null;
  let topDecliningSector = null;
  let topAdvancingSectorPct = null;
  let topDecliningSectorPct = null;
  if (sectors.length > 0) {
    const sortedSectors = [...sectors].sort(
      (a, b) => (parseNumber(b.change_percent ?? b.change) || 0) - (parseNumber(a.change_percent ?? a.change) || 0)
    );
    const top = sortedSectors[0];
    const bottom = sortedSectors[sortedSectors.length - 1];
    if (top) {
      topAdvancingSector = top.sector || top.name || null;
      topAdvancingSectorPct = parseNumber(top.change_percent ?? top.change);
    }
    if (bottom) {
      topDecliningSector = bottom.sector || bottom.name || null;
      topDecliningSectorPct = parseNumber(bottom.change_percent ?? bottom.change);
    }
  }
  let hwAdvCount = null;
  let hwDecCount = null;
  let hwTotalCount = null;
  let hwSummary = null;
  if (heavyweights.length > 0) {
    hwTotalCount = heavyweights.length;
    hwAdvCount = heavyweights.filter((h) => (parseNumber(h.change ?? h.change_pct) || 0) > 0).length;
    hwDecCount = heavyweights.filter((h) => (parseNumber(h.change ?? h.change_pct) || 0) < 0).length;
    hwSummary = `${hwAdvCount}/${hwTotalCount} heavyweights advancing`;
  }
  const leadershipSource = resolveSourceMeta(obsTime, sectors.length > 0 || heavyweights.length > 0);
  const instData = macroData.institutional_context || {};
  const fiiNet = parseNumber(instData.fii_net_crores ?? instData.fii_net);
  const diiNet = parseNumber(instData.dii_net_crores ?? instData.dii_net);
  let combinedNet = null;
  let instInterpretation = "UNAVAILABLE";
  if (fiiNet !== null || diiNet !== null) {
    combinedNet = (fiiNet || 0) + (diiNet || 0);
    if (combinedNet > 500) {
      instInterpretation = "SUPPORTIVE";
    } else if (combinedNet < -500) {
      instInterpretation = "OPPOSING";
    } else if (fiiNet !== null && diiNet !== null && fiiNet * diiNet < 0) {
      instInterpretation = "MIXED";
    } else {
      instInterpretation = "NEUTRAL";
    }
  }
  const institutionalSource = resolveSourceMeta(obsTime, fiiNet !== null || diiNet !== null);
  const sessionStoryRaw = uData.session_story || c.session_story || {};
  const morningThesisSummary = sessionStoryRaw.pre_market_report?.summary || uData.pre_market_report?.summary || null;
  const currentEvolutionSummary = sessionStoryRaw.todays_analysis?.summary || uData.todays_analysis?.summary || null;
  const rawEvents = Array.isArray(sessionStoryRaw.key_events) ? sessionStoryRaw.key_events : Array.isArray(optionalSessionEvidence?.key_events) ? optionalSessionEvidence.key_events : [];
  const keyEvents = rawEvents.map((ev) => ({
    time: String(ev.time || ev.occurred_at || ""),
    event: String(ev.event || ev.title || ev.description || ""),
    source: ev.source ? String(ev.source) : "SESSION_ENGINE"
  }));
  const sessionStorySource = resolveSourceMeta(obsTime, morningThesisSummary !== null || currentEvolutionSummary !== null || keyEvents.length > 0);
  const rawNewsImpact = String(newsData.sentiment_score > 0.2 ? "POSITIVE" : newsData.sentiment_score < -0.2 ? "NEGATIVE" : "NEUTRAL").toUpperCase();
  const newsImpact = newsData.sentiment_score !== void 0 ? rawNewsImpact : "UNAVAILABLE";
  const eventRisk = newsData.event_risk_level ? String(newsData.event_risk_level).toUpperCase() : "LOW";
  const blockers = Array.isArray(c.deterministic_risk?.blockers) ? c.deterministic_risk.blockers : [];
  const confirmations = Array.isArray(c.confidence?.confirming_factors) ? c.confidence.confirming_factors : [];
  const riskSource = resolveSourceMeta(obsTime, true);
  const bestOpp = oppIntel.best_opportunity || {};
  const oppDetail = bestOpp.opportunity || {};
  const hasQualifiedSetup = Boolean(bestOpp.has_trade && oppDetail && oppDetail.setup_type);
  const setupName = oppDetail.setup_type || null;
  const priorityScore = parseNumber(oppDetail.priority_score ?? oppDetail.confluence_score);
  const rawOppDir = String(oppDetail.direction || "").toUpperCase();
  const direction = rawOppDir === "BULLISH" ? "BULLISH" : rawOppDir === "BEARISH" ? "BEARISH" : rawOppDir === "NEUTRAL" ? "NEUTRAL" : null;
  let oppStatus = "UNAVAILABLE";
  if (hasQualifiedSetup) {
    oppStatus = "QUALIFIED";
  } else if (bestOpp.reason === "THRESHOLD_NOT_MET" || bestOpp.reason === "NO_QUALIFIED_SETUP") {
    oppStatus = "STANDBY";
  } else if (bestOpp.reason === "BLOCKED") {
    oppStatus = "BLOCKED";
  }
  const statusSummary = bestOpp.message || (hasQualifiedSetup ? `Qualified ${setupName} active` : "No qualified setup currently meets entry criteria.");
  const proposalId = oppDetail.proposal_id || oppDetail.id || null;
  const oppSource = resolveSourceMeta(obsTime, bestOpp !== void 0);
  return {
    runtimeId,
    sequenceNumber,
    generatedAt,
    marketStatus,
    regime: {
      name: regimeName,
      bias,
      strengthScore,
      confidencePct,
      description: regimeDesc,
      source: regimeSource
    },
    corridor: {
      spotPrice,
      spotChange,
      spotChangePct,
      vwap,
      immediateSupport,
      immediateResistance,
      status: corridorStatus,
      source: corridorSource
    },
    participation: {
      advances,
      declines,
      unchanged,
      breadthPct,
      breadthBias,
      hasDivergence,
      divergenceNote,
      source: participationSource
    },
    derivatives: {
      pcr,
      callWall,
      putWall,
      maxPain,
      indiaVix,
      volatilityRegime,
      source: derivativesSource
    },
    leadership: {
      topAdvancingSector,
      topDecliningSector,
      topAdvancingSectorPct,
      topDecliningSectorPct,
      heavyweightsAdvancingCount: hwAdvCount,
      heavyweightsDecliningCount: hwDecCount,
      heavyweightsTotalCount: hwTotalCount,
      summary: hwSummary,
      source: leadershipSource
    },
    institutional: {
      fiiNet,
      diiNet,
      combinedNet,
      interpretation: instInterpretation,
      source: institutionalSource
    },
    sessionStory: {
      morningThesisSummary,
      currentEvolutionSummary,
      keyEvents,
      source: sessionStorySource
    },
    riskContext: {
      newsImpact,
      eventRisk,
      blockers,
      confirmations,
      source: riskSource
    },
    opportunity: {
      hasQualifiedSetup,
      setupName,
      priorityScore,
      direction,
      status: oppStatus,
      statusSummary,
      proposalId,
      source: oppSource
    }
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  buildMarketIntelligenceViewModel
});
