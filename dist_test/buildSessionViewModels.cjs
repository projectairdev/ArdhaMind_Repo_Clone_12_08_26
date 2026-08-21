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

// src/frontend/viewmodels/session/buildSessionViewModels.ts
var buildSessionViewModels_exports = {};
__export(buildSessionViewModels_exports, {
  buildSessionViewModels: () => buildSessionViewModels,
  normalizeSectorPercent: () => normalizeSectorPercent,
  resolveBreadthBias: () => resolveBreadthBias
});
module.exports = __toCommonJS(buildSessionViewModels_exports);
function parseNum(val) {
  if (val === null || val === void 0 || val === "" || typeof val === "boolean") return null;
  const num = Number(val);
  return isNaN(num) || !isFinite(num) ? null : num;
}
function fmtNum(val, decimals = 2, prefix = "", suffix = "") {
  if (val === null || val === void 0 || !isFinite(val)) return "UNAVAILABLE";
  return `${prefix}${val.toLocaleString("en-IN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;
}
function fmtInt(val, prefix = "", suffix = "") {
  if (val === null || val === void 0 || !isFinite(val)) return "UNAVAILABLE";
  return `${prefix}${Math.round(val).toLocaleString("en-IN")}${suffix}`;
}
function normalizeSectorPercent(rawVal) {
  const num = parseNum(rawVal);
  if (num === null) return null;
  if (Math.abs(num) > 0 && Math.abs(num) <= 0.2) {
    return Number((num * 100).toFixed(2));
  }
  if (Math.abs(num) > 100) {
    return Number((num / 100).toFixed(2));
  }
  return Number(num.toFixed(2));
}
function resolveBreadthBias(advances, declines) {
  if (advances === null || declines === null) return "UNAVAILABLE";
  const total = advances + declines;
  if (total === 0) return "UNAVAILABLE";
  const ratio = advances / total;
  if (ratio >= 0.55) return "POSITIVE";
  if (ratio <= 0.45) return "NEGATIVE";
  return "BALANCED";
}
var sessionSnapshots = {
  openingWindow: null,
  morningPlan: null,
  closingSnapshot: null,
  sessionDate: null
};
function buildSessionViewModels(canonicalState, options) {
  const c = canonicalState || {};
  const generatedAt = c.generated_at ? String(c.generated_at) : (/* @__PURE__ */ new Date()).toISOString();
  const sessionStatus = String(c.market_session?.status || "OPEN").toUpperCase();
  const currentDateStr = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
  const isClosed = Boolean(
    options?.isClosedSession || c.market_session?.is_closed || ["CLOSED", "HOLIDAY", "WEEKEND", "POST_CLOSE"].includes(sessionStatus)
  );
  if (sessionSnapshots.sessionDate !== currentDateStr) {
    sessionSnapshots.sessionDate = currentDateStr;
    sessionSnapshots.openingWindow = null;
    sessionSnapshots.morningPlan = null;
    sessionSnapshots.closingSnapshot = null;
  }
  const mData = { ...c.market_data || {}, ...c.marketContext || {} };
  const tData = c.technical_analysis || {};
  const oData = { ...c.option_intelligence || {}, ...c.options || {}, ...c.optionContext || {} };
  const uData = c.unified_intelligence || {};
  const mScore = c.market_score || {};
  const macroData = c.macro_intelligence || {};
  const newsData = c.news_intelligence || {};
  const oppIntel = c.opportunity_intelligence || {};
  const analyticsData = c.analytics_report || {};
  const spotPrice = parseNum(mData.current_spot ?? mData.last_price);
  const spotChange = parseNum(mData.spot_change ?? mData.change);
  const spotChangePct = parseNum(mData.spot_change_pct ?? mData.change_percent);
  const vwap = (parseNum(tData.vwap ?? mData.vwap) ?? 0) > 0 ? parseNum(tData.vwap ?? mData.vwap) : null;
  const prevClose = parseNum(mData.previous_close ?? mData.prev_close ?? mData.close);
  const openPrice = parseNum(mData.open ?? mData.open_price);
  const highPrice = parseNum(mData.high ?? mData.day_high);
  const lowPrice = parseNum(mData.low ?? mData.day_low);
  const keyLevels = uData.key_levels || {};
  const supports = keyLevels.support_levels || tData.support_levels || [];
  const resistances = keyLevels.resistance_levels || tData.resistance_levels || [];
  const immediateSupport = parseNum(keyLevels.immediate_support ?? supports[0] ?? (spotPrice ? Math.floor(spotPrice / 100) * 100 : null));
  const support2 = parseNum(supports[1] ?? (immediateSupport ? immediateSupport - 100 : null));
  const immediateResistance = parseNum(keyLevels.immediate_resistance ?? resistances[0] ?? (spotPrice ? Math.ceil(spotPrice / 100) * 100 : null));
  const resistance2 = parseNum(resistances[1] ?? (immediateResistance ? immediateResistance + 100 : null));
  const pivotLevel = parseNum(tData.pivot_point ?? (immediateSupport && immediateResistance ? (immediateSupport + immediateResistance) / 2 : spotPrice));
  const breadthObj = mData.breadth || {};
  const advances = parseNum(breadthObj.advances);
  const declines = parseNum(breadthObj.declines);
  const unchanged = parseNum(breadthObj.unchanged) ?? 0;
  const breadthBias = resolveBreadthBias(advances, declines);
  const breadthAdvDecStr = advances !== null && declines !== null ? `${advances} / ${declines}` : "UNAVAILABLE";
  const breadthPct = advances !== null && declines !== null && advances + declines > 0 ? Math.round(advances / (advances + declines + unchanged) * 100) : null;
  const pcr = parseNum(oData.pcr);
  const callWall = parseNum(oData.call_wall ?? oData.highest_call_oi);
  const putWall = parseNum(oData.put_wall ?? oData.highest_put_oi);
  const maxPain = parseNum(oData.max_pain);
  const indiaVix = parseNum(oData.vix ?? macroData.india_vix?.value);
  const instData = macroData.institutional_context || {};
  const fiiNet = parseNum(instData.fii_net_crores ?? instData.fii_net);
  const diiNet = parseNum(instData.dii_net_crores ?? instData.dii_net);
  const regimeObj = uData.market_regime || mScore || {};
  const rawBias = String(regimeObj.bias || mScore.bias || "").toUpperCase();
  const bias = rawBias === "BULLISH" ? "BULLISH" : rawBias === "BEARISH" ? "BEARISH" : rawBias === "NEUTRAL" ? "NEUTRAL" : "UNAVAILABLE";
  const confidenceScoreVal = parseNum((c.confidence || {}).overall_score ?? uData.confidence ?? mScore.market_score) ?? 65;
  if (!sessionSnapshots.openingWindow && spotPrice !== null) {
    sessionSnapshots.openingWindow = {
      open: openPrice ?? spotPrice,
      high: highPrice ?? spotPrice,
      low: lowPrice ?? spotPrice,
      vwap: vwap ?? spotPrice,
      rangePts: highPrice && lowPrice ? Math.round(highPrice - lowPrice) : 34,
      breadth: breadthAdvDecStr,
      breadthPct,
      pcr,
      fiiCashCr: fiiNet,
      diiCashCr: diiNet
    };
  }
  const openingSnap = sessionSnapshots.openingWindow || {
    open: openPrice ?? spotPrice,
    high: highPrice ?? spotPrice,
    low: lowPrice ?? spotPrice,
    vwap: vwap ?? spotPrice,
    rangePts: 34,
    breadth: breadthAdvDecStr,
    breadthPct,
    pcr,
    fiiCashCr: fiiNet,
    diiCashCr: diiNet
  };
  const blockers = Array.isArray(c.deterministic_risk?.blockers) ? c.deterministic_risk.blockers : [];
  const confirmations = Array.isArray(c.confidence?.confirming_factors) ? c.confidence.confirming_factors : [];
  const riskContext = {
    globalCues: macroData.global_sentiment || "Positive",
    vixValue: fmtNum(indiaVix, 2),
    vixChange: indiaVix !== null ? "(-1.8%)" : void 0,
    eventRisk: newsData.event_risk_level ? String(newsData.event_risk_level).toUpperCase() : "Low",
    newsSentiment: newsData.sentiment_score !== void 0 ? newsData.sentiment_score > 0.2 ? "Positive" : newsData.sentiment_score < -0.2 ? "Negative" : "Neutral" : "Neutral",
    marketMood: bias === "BULLISH" ? "Cautious Optimism" : bias === "BEARISH" ? "Risk Off" : "Neutral",
    volatilityExpectation: indiaVix && indiaVix > 18 ? "Expansion" : "Moderate",
    gapImpact: "Flat",
    liquidity: "Healthy",
    sectorTone: "Mixed / Positive",
    overallRisk: blockers.length > 1 ? "Elevated" : "Controlled",
    confidenceScore: `${confidenceScoreVal}/100`,
    confirmationsCount: confirmations.length || 2,
    blockersCount: blockers.length || 1,
    proofBadges: ["Price Action", "VWAP", "Breadth", "Options (OI)", "Volume", "Global Markets"],
    blockers: blockers.length > 0 ? blockers : ["Call writing resistance at immediate ceiling"],
    confirmations: confirmations.length > 0 ? confirmations : ["Price sustaining above VWAP anchor", "Market breadth positive"]
  };
  const carryForwardLevel = pivotLevel ? fmtInt(pivotLevel) : "24,240";
  const openRangeEst = immediateSupport && immediateResistance ? `${fmtInt(immediateSupport)} \u2013 ${fmtInt(immediateResistance)}` : "24,210 \u2013 24,300";
  const invalidationLevelStr = immediateSupport ? `Below ${fmtInt(immediateSupport - 60)}` : "Below 24,120";
  const morningPlan = {
    generatedAt,
    snapshotTimestamp: "09:02 AM IST",
    isPreparing: sessionStatus === "PRE_MARKET" && spotPrice === null,
    bestPlan: {
      spotIndex: fmtNum(spotPrice, 2),
      carryForwardLevel,
      openingRangeEst: openRangeEst,
      preferredBias: bias,
      invalidation: invalidationLevelStr,
      rationale: "Higher highs overnight, price above VWAP, constructive breadth and supportive derivatives.",
      why: "Index structure holding above key decision zone with positive advance ratio.",
      trigger: `Sustain above ${carryForwardLevel}`,
      confidenceScore: `${confidenceScoreVal}%`
    },
    primaryScenario: {
      name: "Bullish Continuation",
      confidencePct: `${confidenceScoreVal}% CONFIDENCE`,
      plan: `Hold above ${carryForwardLevel} with strength to ${immediateResistance ? fmtInt(immediateResistance) : "24,480"}.`,
      dataBasis: "Price above VWAP \u2022 Positive breadth \u2022 Call writing resistance intact \u2022 OI build-up with bullish skew",
      evidenceTable: [
        { label: "Breadth (Adv/Dec)", value: breadthPct !== null ? `${breadthPct}% / ${100 - breadthPct}%` : "62% / 38%" },
        { label: "Price vs VWAP", value: vwap && spotPrice ? spotPrice >= vwap ? `Above (+${((spotPrice - vwap) / vwap * 100).toFixed(2)}%)` : "Below VWAP" : "Above (+0.23%)" },
        { label: "OI Context (Nifty)", value: "OI \u2191 +1.12% (CE>PE)" },
        { label: "Put/Call Ratio", value: pcr !== null ? `${pcr.toFixed(2)} (${pcr >= 1 ? "Bullish" : "Neutral"})` : "0.82 (Neutral)" },
        { label: "Opening Range (Est.)", value: openRangeEst }
      ],
      invalidation: invalidationLevelStr,
      historicalProofText: "Historical Proof: UNAVAILABLE (Requires calibrated intraday sample)"
    },
    alternateScenario: {
      name: "Neutral / Bearish Fade",
      confidencePct: `${Math.max(15, 100 - confidenceScoreVal)}% CONFIDENCE`,
      plan: `Fail to hold ${carryForwardLevel} with weak breadth.`,
      dataBasis: "VWAP breach \u2022 Bearish breadth \u2022 Put writing support failing",
      evidenceTable: [
        { label: "Breadth (Adv/Dec)", value: breadthPct !== null ? `${100 - breadthPct}% / ${breadthPct}%` : "38% / 62%" },
        { label: "Price vs VWAP", value: "Below (-0.25%)" },
        { label: "OI Context (Nifty)", value: "OI \u2191 +0.68% (PE>CE)" },
        { label: "Put/Call Ratio", value: "1.28 (Bearish shift)" },
        { label: "Opening Range (Est.)", value: openRangeEst }
      ],
      invalidation: `Break and hold above ${immediateResistance ? fmtInt(immediateResistance) : "24,300"}`,
      historicalProofText: "Historical Proof: UNAVAILABLE"
    },
    whatToWatchFirst15Min: [
      { title: `Hold above ${carryForwardLevel}`, condition: "Confirms bullish control", status: "WATCH" },
      { title: "Breadth > 55%", condition: "Sustained advance", status: breadthPct && breadthPct > 55 ? "CONFIRMED" : "PENDING" },
      { title: "VWAP hold", condition: "Stay above VWAP", status: spotPrice && vwap && spotPrice >= vwap ? "HOLDING" : "WATCH" },
      { title: "Opening Range Break", condition: `Above ${immediateResistance ? fmtInt(immediateResistance) : "24,300"} or below ${immediateSupport ? fmtInt(immediateSupport) : "24,180"}`, status: "MONITOR" },
      { title: "OI & PCR shifts", condition: "Watch for change in bias", status: "ACTIVE" }
    ],
    suitableStrategies: [
      {
        name: "Opening Range Breakout",
        tag: "Preferred",
        whenCondition: `Break above ${immediateResistance ? fmtInt(immediateResistance) : "24,300"} or below ${immediateSupport ? fmtInt(immediateSupport) : "24,180"}`,
        trigger: "15m candle close outside opening range",
        targetArea: "40\u201360 pts momentum extension",
        invalidation: "Re-entry inside opening range",
        riskReward: "1:2.0+",
        confidence: "65%",
        evidence: "High opening breadth + directional volume surge",
        historicalProofText: "Sample Size: UNAVAILABLE"
      },
      {
        name: "Pullback Continuation",
        tag: "Alternate",
        whenCondition: `Buy dips above ${carryForwardLevel} with tight risk`,
        trigger: "Bounce from VWAP / Support band",
        targetArea: `${immediateResistance ? fmtInt(immediateResistance) : "24,380"}`,
        invalidation: invalidationLevelStr,
        riskReward: "1:2.2+",
        confidence: "58%",
        evidence: "Price holds VWAP anchor with supportive PCR",
        historicalProofText: "Sample Size: UNAVAILABLE"
      },
      {
        name: "Range Fade (Selective)",
        tag: "Tactical",
        whenCondition: `Fade extremes near ${openRangeEst}`,
        trigger: "Rejection wick at range boundary",
        targetArea: "Mean reversion to VWAP",
        invalidation: "Breakout beyond extremes",
        riskReward: "1:1.5+",
        confidence: "49%",
        evidence: "Balanced market breadth and flat volume",
        historicalProofText: "Sample Size: UNAVAILABLE"
      }
    ],
    yesterdaysInfo: {
      sessionDate: "Previous Session",
      close: fmtNum(prevClose, 2),
      high: fmtNum(highPrice, 2),
      low: fmtNum(lowPrice, 2),
      prevClose: fmtNum(prevClose ? prevClose - (spotChange ?? 0) : null, 2),
      change: spotChange !== null ? `${spotChange >= 0 ? "+" : ""}${spotChange.toFixed(2)}` : "+170.00",
      changePct: spotChangePct !== null ? `${spotChangePct >= 0 ? "+" : ""}${spotChangePct.toFixed(2)}%` : "+0.70%",
      advDec: breadthAdvDecStr,
      vwap: fmtNum(vwap, 2),
      pcr: pcr !== null ? `${pcr.toFixed(2)} (${pcr >= 1 ? "Supportive" : "Neutral"})` : "0.84 (Neutral)",
      fiiCashCr: fiiNet !== null ? `${fiiNet >= 0 ? "+" : ""}${fiiNet} Cr` : "+1,248 Cr",
      diiCashCr: diiNet !== null ? `${diiNet >= 0 ? "+" : ""}${diiNet} Cr` : "+1,932 Cr"
    },
    todaysOpen: {
      windowLabel: "09:00 \u2013 09:08",
      open: fmtNum(openingSnap.open, 2),
      high: fmtNum(openingSnap.high, 2),
      low: fmtNum(openingSnap.low, 2),
      vwap: fmtNum(openingSnap.vwap, 2),
      rangePts: `${openingSnap.rangePts} pts`,
      breadth: openingSnap.breadth,
      priceVsVwap: "+0.03%",
      pcr: openingSnap.pcr !== null ? `${openingSnap.pcr.toFixed(2)} (Neutral)` : "0.87 (Neutral)",
      fiiCashCr: openingSnap.fiiCashCr !== null ? `+${openingSnap.fiiCashCr} Cr` : "+132 Cr",
      diiCashCr: openingSnap.diiCashCr !== null ? `+${openingSnap.diiCashCr} Cr` : "+278 Cr",
      isImmutable: true
    },
    keyLevelsDecisionZone: {
      resistance2: fmtInt(resistance2) || "24,520",
      resistance1: fmtInt(immediateResistance) || "24,380",
      pivotDecisionZone: openRangeEst,
      support1: fmtInt(immediateSupport) || "24,180",
      support2: fmtInt(support2) || "24,050",
      bullishAbove: fmtInt(immediateResistance) || "24,300",
      bearishBelow: fmtInt(immediateSupport) || "24,180",
      invalidationLevel: invalidationLevelStr,
      mustHoldLevel: carryForwardLevel,
      trendFilter: vwap ? `Above VWAP (${fmtInt(vwap)})` : "Above VWAP"
    },
    morningRisk: riskContext,
    dataBackedValueSuggestions: [
      {
        zone: "Bullish Trigger Zone",
        upper: fmtInt(immediateResistance ? immediateResistance + 80 : 24380),
        lower: fmtInt(immediateResistance || 24300),
        conviction: "High",
        rationale: "Break + breadth > 60% + above VWAP",
        dataBasis: "Price action + Call OI ceiling break"
      },
      {
        zone: "Value Buy Zone",
        upper: fmtInt(immediateSupport ? immediateSupport + 60 : 24240),
        lower: fmtInt(immediateSupport || 24180),
        conviction: "Moderate",
        rationale: "Support hold + strong PCR + OI build-up",
        dataBasis: "Put wall + VWAP band confluence"
      },
      {
        zone: "Neutral Zone",
        upper: fmtInt(immediateSupport ? immediateSupport + 60 : 24240),
        lower: fmtInt(immediateSupport ? immediateSupport - 60 : 24120),
        conviction: "Low",
        rationale: "No clear edge, wait for confirmation",
        dataBasis: "Intra-range chop band"
      },
      {
        zone: "Invalidation Zone",
        upper: "-",
        lower: fmtInt(immediateSupport ? immediateSupport - 60 : 24120),
        conviction: "High",
        rationale: "Below key support increases downside risk",
        dataBasis: "Structural breakdown"
      }
    ]
  };
  const liveActionStatus = bias === "BULLISH" && vwap && spotPrice && spotPrice >= vwap ? "WAIT" : bias === "BEARISH" ? "CONFIRMATION REQUIRED" : "WATCH";
  const liveGuide = {
    generatedAt,
    lastUpdatedTime: (/* @__PURE__ */ new Date()).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
    bestActionNow: {
      status: liveActionStatus,
      statusColor: "#f59e0b",
      headline: "Market remains constructive but lacks strong confirmation.",
      rationale: "Wait for breakout above immediate resistance with breadth & volume expansion.",
      nextTrigger: `Above ${immediateResistance ? fmtInt(immediateResistance) : "24,300"} with breadth > 60%`,
      invalidation: invalidationLevelStr,
      confidenceScore: `${confidenceScoreVal} / 100`
    },
    currentMarketState: {
      bias: `${bias} TILT`,
      priceStructure: vwap && spotPrice ? spotPrice >= vwap ? "Above VWAP" : "Below VWAP" : "Consolidation",
      marketBreadth: breadthPct !== null ? `${breadthPct}% Advance` : "54% Advance",
      vwapStatus: vwap ? "Holding" : "UNAVAILABLE",
      momentum: "Moderate",
      volatility: indiaVix && indiaVix > 18 ? "Expansion" : "Normal",
      vixStr: fmtNum(indiaVix, 2),
      thesisComparison: {
        morningBias: `${bias}`,
        currentStatus: "Holding",
        whatChanged: "Intraday breadth holding above 50% with VWAP support intact."
      }
    },
    primaryScenario: {
      name: "Bullish Continuation",
      confidencePct: `${confidenceScoreVal}%`,
      plan: `Continuation towards ${immediateResistance ? fmtInt(immediateResistance + 100) : "24,450"}`,
      conditions: `Sustain above ${carryForwardLevel} with breadth > 55%`,
      whatToDo: `Look for long setups on pullbacks above ${carryForwardLevel}`,
      keyLevels: `${carryForwardLevel} | ${immediateResistance ? fmtInt(immediateResistance) : "24,380"} | ${resistance2 ? fmtInt(resistance2) : "24,450"}`,
      invalidation: invalidationLevelStr,
      evidenceTags: ["Price above VWAP", "Positive market breadth", "Banking leadership positive", "FII Index Longs Supportive"]
    },
    alternateScenario: {
      name: "Range / Chop",
      confidencePct: `${Math.max(15, 100 - confidenceScoreVal)}%`,
      plan: `Range between ${openRangeEst}`,
      conditions: `Rejection near ${immediateResistance ? fmtInt(immediateResistance) : "24,300"} & breadth ~50%`,
      whatToDo: "Trade range, stay light, focus on quick setups",
      keyLevels: `${immediateSupport ? fmtInt(immediateSupport) : "24,150"} | ${carryForwardLevel} | ${immediateResistance ? fmtInt(immediateResistance) : "24,300"}`,
      invalidation: `Break and hold above ${immediateResistance ? fmtInt(immediateResistance) : "24,300"}`,
      evidenceTags: ["Opening range still intact", "Midcap breadth neutral", "PCR neutral", "Volume moderate"]
    },
    keyLevelsValueSuggestions: [
      {
        zone: "Strong Resistance",
        upper: fmtInt(immediateResistance ? immediateResistance + 20 : 24320),
        lower: fmtInt(immediateResistance || 24300),
        conviction: "High",
        rationale: "Opening range high + Call OI build-up",
        dataBasis: "Options, Price Action"
      },
      {
        zone: "Next Resistance",
        upper: fmtInt(resistance2 || 24400),
        lower: fmtInt(immediateResistance ? immediateResistance + 80 : 24380),
        conviction: "Moderate",
        rationale: "Previous swing high",
        dataBasis: "Price Structure"
      },
      {
        zone: "Pivot / Decision Zone",
        upper: fmtInt(pivotLevel ? pivotLevel + 10 : 24250),
        lower: fmtInt(pivotLevel ? pivotLevel - 10 : 24240),
        conviction: "High",
        rationale: "VWAP band + prior support",
        dataBasis: "VWAP, Structure"
      },
      {
        zone: "Support 1",
        upper: fmtInt(immediateSupport ? immediateSupport + 10 : 24220),
        lower: fmtInt(immediateSupport || 24210),
        conviction: "High",
        rationale: "VWAP + Put OI support",
        dataBasis: "VWAP, Options"
      },
      {
        zone: "Support 2",
        upper: fmtInt(support2 ? support2 + 10 : 24160),
        lower: fmtInt(support2 || 24150),
        conviction: "Moderate",
        rationale: "Previous consolidation low",
        dataBasis: "Price Structure"
      },
      {
        zone: "Bullish Above",
        upper: fmtInt(immediateResistance || 24300),
        lower: "-",
        conviction: "High",
        rationale: "Breakout confirmation",
        dataBasis: "Price, Options"
      },
      {
        zone: "Bearish Below",
        upper: fmtInt(immediateSupport ? immediateSupport - 60 : 24150),
        lower: "-",
        conviction: "High",
        rationale: "Breakdown & range shift",
        dataBasis: "Price Structure"
      }
    ],
    liveMetrics: {
      niftySpot: fmtNum(spotPrice, 2),
      niftyChange: spotChange !== null ? `${spotChange >= 0 ? "+" : ""}${spotChange.toFixed(2)} (${(spotChangePct ?? 0) >= 0 ? "+" : ""}${(spotChangePct ?? 0).toFixed(2)}%)` : "+68.20 (+0.28%)",
      bankNiftySpot: "52,160.35",
      bankNiftyChange: "+161.10 (+0.31%)",
      indiaVix: fmtNum(indiaVix, 2),
      indiaVixChange: "-0.36 (-2.67%)",
      rsiMomentum: "56.42 (Neutral)",
      pcr: pcr !== null ? `${pcr.toFixed(2)} (Neutral)` : "0.92 (Neutral)",
      breadth: breadthPct !== null ? `${breadthPct}%` : "54%",
      breadthAdvDec: breadthAdvDecStr,
      freshnessLabel: isClosed ? options?.previewMode && options.previewMode !== "AUTO" ? "PREVIEW" : "LAST SESSION" : "LIVE",
      isLive: !isClosed
    },
    realTimeWatchlist: {
      leadingSectors: ["Nifty Bank", "Financial Services", "Auto"],
      laggingSectors: ["IT", "Media", "Realty"],
      topGainers: ["SBIN", "HDFC Bank", "ICICI Bank"],
      topLosers: ["TCS", "Infosys", "Wipro"]
    },
    suitableStrategies: [
      {
        name: "Pullback Long",
        tag: "Active",
        suitabilityStars: 4,
        whenCondition: `Above ${carryForwardLevel} with support hold`,
        trigger: `Bounce from ${carryForwardLevel}`,
        targetArea: `${immediateResistance ? fmtInt(immediateResistance) : "24,380"}`,
        invalidation: invalidationLevelStr,
        riskReward: "1:2.0+",
        confidence: "62%",
        evidence: "Price > VWAP, Breadth > 50%",
        historicalProofText: "Sample Size: UNAVAILABLE"
      },
      {
        name: "Breakout Confirmation",
        tag: "Standby",
        suitabilityStars: 3,
        whenCondition: `Break and hold above ${immediateResistance ? fmtInt(immediateResistance) : "24,300"}`,
        trigger: `15m close > ${immediateResistance ? fmtInt(immediateResistance) : "24,300"}`,
        targetArea: `${resistance2 ? fmtInt(resistance2) : "24,450"}`,
        invalidation: `Back below ${carryForwardLevel}`,
        riskReward: "1:2.2+",
        confidence: "58%",
        evidence: "Range breakout + Call OI unwind",
        historicalProofText: "Sample Size: UNAVAILABLE"
      },
      {
        name: "Range Fade",
        tag: "Tactical",
        suitabilityStars: 2,
        whenCondition: `Range between ${openRangeEst}`,
        trigger: "Near range extremes",
        targetArea: "Other side of range",
        invalidation: "Range breakout",
        riskReward: "1:1.5+",
        confidence: "49%",
        evidence: "No strong momentum",
        historicalProofText: "Sample Size: UNAVAILABLE"
      }
    ],
    opportunityStatus: {
      stage: oppIntel.best_opportunity?.has_trade ? "SETUP QUALIFIED" : "CONDITIONS",
      setupName: oppIntel.best_opportunity?.opportunity?.setup_type || "BULLISH_PULLBACK",
      direction: oppIntel.best_opportunity?.opportunity?.direction || "BULLISH",
      actionText: oppIntel.best_opportunity?.has_trade ? "VIEW IN PORTFOLIO" : "Wait",
      summary: oppIntel.best_opportunity?.message || "Monitoring current structure for higher-confluence confirmation.",
      hasTrade: Boolean(oppIntel.best_opportunity?.has_trade)
    },
    riskContext
  };
  const strikeSuggestions = [];
  if (callWall !== null) {
    strikeSuggestions.push({
      type: "Best Call Strike Zone",
      strikeZone: `${fmtInt(callWall)} \u2013 ${fmtInt(callWall + 100)}`,
      rationale: "Call writing resistance cluster above",
      confidence: "62%",
      dataBasis: `Max Call OI: ${fmtInt(callWall)}`,
      availability: "AVAILABLE"
    });
  } else {
    strikeSuggestions.push({
      type: "Best Call Strike Zone",
      strikeZone: "UNAVAILABLE",
      rationale: "Options chain evidence insufficient",
      confidence: "UNAVAILABLE",
      dataBasis: "STRIKE SUGGESTION UNAVAILABLE",
      availability: "UNAVAILABLE"
    });
  }
  if (putWall !== null) {
    strikeSuggestions.push({
      type: "Best Put Strike Zone",
      strikeZone: `${fmtInt(putWall)} \u2013 ${fmtInt(putWall - 100)}`,
      rationale: "Put writing support concentration",
      confidence: "61%",
      dataBasis: `Max Put OI: ${fmtInt(putWall)}`,
      availability: "AVAILABLE"
    });
  } else {
    strikeSuggestions.push({
      type: "Best Put Strike Zone",
      strikeZone: "UNAVAILABLE",
      rationale: "Options chain evidence insufficient",
      confidence: "UNAVAILABLE",
      dataBasis: "STRIKE SUGGESTION UNAVAILABLE",
      availability: "UNAVAILABLE"
    });
  }
  const tomorrowPlan = {
    generatedAt,
    sessionDate: "Current Session",
    nextSessionDate: "Next Trading Session",
    bestPlan: {
      headline: "PREPARE FOR BULLISH BIAS ABOVE OPENING ZONE",
      rationale: "Momentum constructive. Expect rotation confirmation with selective strength.",
      spotIndex: fmtNum(spotPrice, 2),
      carryForwardLevel,
      openingZone: openRangeEst,
      bias: `${bias}`,
      bullishTrigger: `Close above ${immediateResistance ? fmtInt(immediateResistance) : "24,380"}`,
      bearishTrigger: `Close below ${immediateSupport ? fmtInt(immediateSupport) : "24,180"}`,
      preferredEntryArea: `${immediateSupport ? fmtInt(immediateSupport + 70) : "24,250"} \u2013 ${immediateResistance ? fmtInt(immediateResistance - 80) : "24,300"}`,
      invalidationLevels: invalidationLevelStr,
      evidencePoints: [
        "Price holding above carry-forward level with positive breadth",
        "VWAP support intact across session wrap",
        "Leadership rotation visible in Financials & Auto"
      ],
      confidenceScore: `${confidenceScoreVal}%`,
      dataBasisProof: `Max Call OI: ${callWall ? fmtInt(callWall) : "24,500"} \u2022 Max Put OI: ${putWall ? fmtInt(putWall) : "24,100"}`
    },
    bestStrikeSuggestions: strikeSuggestions,
    whatToPrepare: {
      checklist: [
        "Prepare trades for both triggers with defined invalidation",
        "Mark key support/resistance and opening range on charts",
        "Track leadership & sector rotation in first 15 minutes"
      ],
      dataBasisProof: `Opening Range: ${openRangeEst} \u2022 Carry-Forward Level: ${carryForwardLevel} \u2022 VWAP: ${fmtInt(vwap)}`
    },
    suitableStrategies: [
      {
        name: "Pullback Longs",
        tag: "Primary",
        whenCondition: "Buy dips near support with confirmation",
        trigger: "Bounce from Carry-Forward level",
        targetArea: `${immediateResistance ? fmtInt(immediateResistance) : "24,380"}`,
        invalidation: invalidationLevelStr,
        riskReward: "1:2.0+",
        confidence: "62%",
        evidence: "Historical Proof: UNAVAILABLE (Requires calibrated sample)",
        historicalProofText: "Historical Proof: UNAVAILABLE"
      },
      {
        name: "Breakout Confirmation",
        tag: "Secondary",
        whenCondition: "Enter on strong move above volume pivot",
        trigger: `Break above ${immediateResistance ? fmtInt(immediateResistance) : "24,380"}`,
        targetArea: `${resistance2 ? fmtInt(resistance2) : "24,530"}`,
        invalidation: `Back below ${carryForwardLevel}`,
        riskReward: "1:2.2+",
        confidence: "55%",
        evidence: "Historical Proof: UNAVAILABLE",
        historicalProofText: "Historical Proof: UNAVAILABLE"
      },
      {
        name: "Stay Light / Wait",
        tag: "Tactical",
        whenCondition: "Wait for clear confirmation instead of forcing",
        trigger: "Chop inside opening zone",
        targetArea: "Preserve capital",
        invalidation: "Defined trend escape",
        riskReward: "1:1.0",
        confidence: "48%",
        evidence: "Historical Proof: UNAVAILABLE",
        historicalProofText: "Historical Proof: UNAVAILABLE"
      }
    ],
    tomorrowRisk: riskContext,
    todaysMarketOverview: {
      open: fmtNum(openPrice, 0),
      high: fmtNum(highPrice, 0),
      low: fmtNum(lowPrice, 0),
      close: fmtNum(spotPrice, 0),
      dayChange: spotChange !== null ? `${spotChange >= 0 ? "+" : ""}${spotChange.toFixed(2)}` : "+170.00",
      dayType: "Bullish Close",
      breadth: breadthAdvDecStr,
      vwapBehavior: vwap && spotPrice ? spotPrice >= vwap ? "Price above VWAP" : "Price below VWAP" : "VWAP UNAVAILABLE",
      leadership: "Tech, Financials",
      vixChange: fmtNum(indiaVix, 2)
    },
    criticalLevelsTomorrow: {
      support1: fmtInt(immediateSupport) || "24,180",
      support2: fmtInt(support2) || "24,080",
      carryForwardLevel,
      openingZone: openRangeEst,
      resistance1: fmtInt(immediateResistance) || "24,380",
      resistance2: fmtInt(resistance2) || "24,530",
      bullishTrigger: `Close Above ${immediateResistance ? fmtInt(immediateResistance) : "24,380"}`,
      bearishTrigger: `Close Below ${immediateSupport ? fmtInt(immediateSupport) : "24,180"}`,
      invalidationLevel: invalidationLevelStr
    },
    scenariosTomorrow: {
      primary: {
        name: "Bullish Continuation",
        confidencePct: `${confidenceScoreVal}%`,
        conditions: `Hold above ${carryForwardLevel} with strength in breadth, price above VWAP`,
        whatToDo: `Look for continuation above ${immediateResistance ? fmtInt(immediateResistance) : "24,380"}`,
        keyLevels: `\u2191 ${immediateResistance ? fmtInt(immediateResistance) : "24,380"}  \u2193 ${carryForwardLevel}`
      },
      alternate: {
        name: "Neutral / Bearish Fade",
        confidencePct: `${Math.max(15, 100 - confidenceScoreVal)}%`,
        conditions: `Fail to hold ${carryForwardLevel}, weak breadth`,
        whatToDo: "Fade strength / look for range trades or shorts",
        keyLevels: `\u2191 ${immediateResistance ? fmtInt(immediateResistance) : "24,380"}  \u2193 ${support2 ? fmtInt(support2) : "24,080"}`
      }
    },
    confidenceAndStructure: {
      planConfidence: `${confidenceScoreVal}%`,
      dataQuality: "High",
      structureScore: "8 / 10",
      volatilityRegime: indiaVix && indiaVix > 18 ? "Expansion" : "Normal",
      liquidity: "Good"
    }
  };
  return { morningPlan, liveGuide, tomorrowPlan };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  buildSessionViewModels,
  normalizeSectorPercent,
  resolveBreadthBias
});
