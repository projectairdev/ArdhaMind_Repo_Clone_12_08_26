// src/frontend/components/IntradayAssistant.tsx
import React, { useState, useMemo } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  Activity,
  ShieldCheck,
  Info,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Clock,
  Layers,
  Building2
} from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber
} from "../utils/safeHelpers";
import { mapTraderEnum } from "../utils/traderTerminology";
import {
  formatTimestampIST,
  formatRelativeAge,
  formatTimeIST
} from "../utils/timeFormatting";
import { ScenarioCard, nearestDecisionLevels } from "./intelligence/CanonicalPresentation";

function ScenarioGrid({ scenarios }: { scenarios: any[] }) {
  return <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    {scenarios.map((scenario, index) => <ScenarioCard key={scenario.name || index} scenario={scenario} />)}
  </div>;
}

export function IntradayAssistant() {
  const {
    canonicalState,
    lastValidState,
    liveEventStream,
    marketContext,
    optionContext
  } = useWorkstationState();

  const [compareWindow, setCompareWindow] = useState<"1m" | "5m" | "15m" | "open">("5m");
  const [eventSort, setEventSort] = useState<"newest" | "materiality">("newest");

  const state = canonicalState ?? lastValidState;
  const mData = state?.market_data || {};
  const spot = marketContext?.current_spot ?? mData.current_spot;
  const prevClose = marketContext?.previous_close ?? mData.previous_close;
  const change = spot && prevClose ? spot - prevClose : 0;
  const changePct = prevClose ? (change / prevClose) * 100 : 0;
  const isPositive = change >= 0;

  const sessionStatus = safeString(state?.market_session?.status || marketContext?.trading_session || "CLOSED").toUpperCase();
  const isClosed = Boolean(state?.market_session?.is_closed || ["CLOSED", "HOLIDAY", "POST_CLOSE", "WEEKEND"].includes(sessionStatus));

  // Breadth
  const breadth = marketContext?.breadth || mData.breadth || {};
  const advances = safeNumber(breadth.advances, 0);
  const declines = safeNumber(breadth.declines, 0);

  // PCR
  const optionData = state?.option_intelligence || optionContext || {};
  const pcr = safeNumber(optionData.pcr, 0);

  // VIX
  const vix = safeNumber(state?.macro_intelligence?.india_vix?.value || marketContext?.india_vix || 12.6, 0);

  // Heavyweights Up/Down Count
  const heavyweights = Array.isArray(marketContext?.heavyweights) ? marketContext.heavyweights : [];
  const upHeavyweights = heavyweights.filter((h: any) => h.change >= 0).length;
  const totalHeavyweights = heavyweights.length;

  // GIFT Nifty
  const macroQuotes = state?.macro_intelligence?.quotes || {};
  const giftNifty = macroQuotes["GIFT_NIFTY"] || {};
  const giftPrice = safeNumber(giftNifty.price || giftNifty.value, 0);

  // News
  const newsItems = safeArray(state?.news_intelligence?.items) as any[];
  const highImpactNewsCount = newsItems.filter(n => String(n.impact_strength || n.impact_level).toUpperCase().includes("HIGH")).length;

  // 1. CONFIRMATION MATRIX STATE BIASES & STATUSES
  const confirmationMatrix = useMemo(() => {
    const tempState = state?.live_assistant_temporal_state;
    const families = tempState?.confirmation_families || [];
    const matrix: Record<string, { bias: string; status: string }> = {};
    families.forEach((f: any) => {
      matrix[f.family] = { bias: f.bias, status: f.status };
    });
    for (const fam of ["PRICE", "BREADTH", "OPTIONS", "VOLATILITY", "HEAVYWEIGHTS", "GLOBAL / MACRO", "NEWS / EVENT RISK"]) {
      if (!matrix[fam]) {
        matrix[fam] = { bias: "UNAVAILABLE", status: "UNAVAILABLE" };
      }
    }
    return matrix;
  }, [state]);

  // 2. TEMPORAL COMPARISON FINDER
  // Backend provides: comparisons[].requested_window ("SINCE OPEN" = openSnap baseline),
  // actual_duration, diff_spot (diffMs from backend tick delta), and targetTime-equivalent window labels.
  const comparisonData = useMemo(() => {
    const tempState = state?.live_assistant_temporal_state;
    if (!tempState || !tempState.comparisons) {
      return {
        available: false,
        label: "SINCE OPEN",
        diffDesc: "Waiting for historical state cycles...",
        diffSpot: 0,
        diffPCR: 0,
        diffVix: 0,
        diffAdv: 0,
        spotStatus: "Stable",
        breadthStatus: "Stable",
        pcrStatus: "Stable",
        vixStatus: "Stable",
        hwStatus: "Stable",
        interpretation: "Waiting for update..."
      };
    }
    const mapKey = {
      "1m": "1 MIN",
      "5m": "5 MIN",
      "15m": "15 MIN",
      "open": "SINCE OPEN"
    }[compareWindow] || "5 MIN";

    const matched = tempState.comparisons.find((c: any) => c.requested_window === mapKey);
    if (!matched || !matched.available) {
      return {
        available: false,
        label: mapKey === "SINCE OPEN" ? "SINCE OPEN" : `LAST ${mapKey}`,
        diffDesc: "Unavailable",
        diffSpot: 0,
        diffPCR: 0,
        diffVix: 0,
        diffAdv: 0,
        spotStatus: "Stable",
        breadthStatus: "Stable",
        pcrStatus: "Stable",
        vixStatus: "Stable",
        hwStatus: "Stable",
        interpretation: "Observation starting. Awaiting subsequent canonical updates."
      };
    }

    const labelText = mapKey === "SINCE OPEN" ? `SINCE OPEN (${matched.actual_duration})` : `LAST ${matched.actual_duration}`;
    return {
      available: true,
      label: labelText,
      diffSpot: matched.diff_spot,
      diffPCR: matched.diff_pcr,
      diffVix: matched.diff_vix,
      diffAdv: matched.diff_adv,
      spotStatus: matched.spot_status || "Stable",
      breadthStatus: matched.breadth_status || "Stable",
      pcrStatus: matched.pcr_status || "Stable",
      vixStatus: matched.vix_status || "Stable",
      hwStatus: matched.hw_status || "Stable",
      interpretation: matched.interpretation || "Market metrics are trading within stable range boundaries."
    };
  }, [compareWindow, state]);

  // Confirmation Matrix change arrows
  const arrowDirections = useMemo(() => {
    if (!comparisonData.available) {
      return { PRICE: "→", BREADTH: "→", OPTIONS: "→", VOLATILITY: "→", HEAVYWEIGHTS: "→", "GLOBAL / MACRO": "→", "NEWS / EVENT RISK": "→" };
    }
    const priceArrow = comparisonData.spotStatus === "Improving" ? "↑" : comparisonData.spotStatus === "Weakening" ? "↓" : "→";
    const breadthArrow = comparisonData.breadthStatus === "Improving" ? "↑" : comparisonData.breadthStatus === "Weakening" ? "↓" : "→";
    const optionsArrow = comparisonData.pcrStatus === "Improving" ? "↑" : comparisonData.pcrStatus === "Weakening" ? "↓" : "→";
    const volArrow = comparisonData.vixStatus === "Supportive" ? "↑" : comparisonData.vixStatus === "Elevated" ? "↓" : "→";
    const hwArrow = comparisonData.hwStatus === "Improving" ? "↑" : comparisonData.hwStatus === "Weakening" ? "↓" : "→";

    return {
      PRICE: priceArrow,
      BREADTH: breadthArrow,
      OPTIONS: optionsArrow,
      VOLATILITY: volArrow,
      HEAVYWEIGHTS: hwArrow,
      "GLOBAL / MACRO": "→",
      "NEWS / EVENT RISK": "→"
    };
  }, [comparisonData]);

  // Supporting, Neutral, Opposing, Unavailable Counts
  const matrixCounts = useMemo(() => {
    let supporting = 0;
    let neutral = 0;
    let opposing = 0;
    let unavailable = 0;

    Object.values(confirmationMatrix).forEach((item: any) => {
      const b = safeString(item.bias).toUpperCase();
      if (["BULLISH", "SUPPORTIVE", "POSITIVE"].includes(b)) {
        supporting++;
      } else if (["BEARISH", "RISK", "NEGATIVE"].includes(b)) {
        opposing++;
      } else if (b.includes("UNAVAILABLE")) {
        unavailable++;
      } else {
        neutral++;
      }
    });

    return { supporting, neutral, opposing, unavailable };
  }, [confirmationMatrix]);

  // Overall Market State
  const marketStateLabel = useMemo(() => {
    if (matrixCounts.supporting >= 5) return "Positive";
    if (matrixCounts.opposing >= 4) return "Negative";
    return "Mixed";
  }, [matrixCounts]);

  const marketStateChange = useMemo(() => {
    const mins = comparisonData.available ? comparisonData.label : "";
    if (comparisonData.spotStatus === "Improving") return `Improving (${mins})`;
    if (comparisonData.spotStatus === "Weakening") return `Weakening (${mins})`;
    return "Stable";
  }, [comparisonData]);

  // Nearest decision zones selector
  const zones = safeArray(state?.unified_intelligence?.decision_zones || state?.decision_zones);
  const { nearestSupport, nearestResistance } = nearestDecisionLevels(zones, spot);

  // Scenarios
  const scenarios = safeArray(state?.unified_intelligence?.scenarios || state?.scenarios);

  // Event stream sorting
  const sortedEvents = useMemo(() => {
    const stream = liveEventStream || [];
    const newestFirst = (a: typeof stream[number], b: typeof stream[number]) =>
      b.source_state_sequence - a.source_state_sequence;
    if (eventSort === "materiality") {
      return [...stream].sort((a, b) => {
        if (a.materiality === b.materiality) {
          return newestFirst(a, b);
        }
        return a.materiality === "high" ? -1 : 1;
      });
    }
    // Newest first
    return [...stream].sort(newestFirst);
  }, [liveEventStream, eventSort]);

  const lastUpdateStr = state?.generated_at ? formatTimeIST(state.generated_at) : "UNAVAILABLE";
  const relativeAgeStr = state?.generated_at ? formatRelativeAge(state.generated_at) : "N/A";

  return (
    <div id="live-assistant-workspace" className="space-y-6 text-left font-sans">
      {/* ── 1. CURRENT MARKET STATE COMPACT HEADER ── */}
      <header className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-900 pb-3">
          <div>
            <div className="flex items-center gap-2 text-[10px] font-bold text-cyan-400 uppercase tracking-widest">
              <span>{isClosed ? "LIVE ASSISTANT · MARKET CLOSED / NEXT SESSION WATCH" : "LIVE ASSISTANT · REAL-TIME CANONICAL MONITOR"}</span>
              <span className={`px-2 py-0.5 rounded text-[8px] border font-bold ${
                isClosed ? "bg-slate-950 border-slate-800 text-slate-500" : "bg-emerald-950/60 border-emerald-800 text-emerald-400"
              }`}>
                {isClosed ? "MARKET CLOSED" : "LIVE FEED"}
              </span>
            </div>
            <h2 className="text-lg font-black text-white mt-1 uppercase tracking-tight">CURRENT MARKET STATE</h2>
          </div>
          <div className="text-right text-[10px] text-slate-500">
            <div>CANONICAL UPDATE: <span className="text-white font-semibold">{lastUpdateStr}</span></div>
            <div>Latency: {relativeAgeStr}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 items-center">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">NIFTY SPOT</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-white">{spot ? formatNumber(spot, 2) : "--"}</span>
              <span className={`text-[11px] font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                {isPositive ? "+" : ""}{formatNumber(change, 2)} ({isPositive ? "+" : ""}{formatNumber(changePct, 2)}%)
              </span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">MARKET STATE</span>
            <span className="text-sm font-bold text-white block">
              {marketStateLabel} <span className="text-slate-400 font-normal">· {marketStateChange}</span>
            </span>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">BEST-SUPPORTED BEHAVIOR</span>
            <span className="text-xs font-bold text-cyan-300 block truncate" title={safeString(state?.unified_intelligence?.preferred_setup?.title || "Mixed Setup")}>
              {safeString(state?.unified_intelligence?.preferred_setup?.title || "Mixed Setup")}
            </span>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">CONFIRMATION MATRIX</span>
            <span className="text-xs font-bold text-slate-300 block">
              <span className="text-emerald-400">{matrixCounts.supporting} Supporting</span> · {matrixCounts.neutral} Neutral · <span className="text-rose-400">{matrixCounts.opposing} Opposing</span>{matrixCounts.unavailable > 0 ? ` · ${matrixCounts.unavailable} Unavailable` : ""}
            </span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* LEFT COLUMN: WHAT CHANGED & MATRIX */}
        <div className="lg:col-span-7 space-y-5">
          {/* ── 2. WHAT CHANGED TEMPORAL COMPARISON ── */}
          <section className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 font-mono">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 border-b border-slate-850 pb-2.5">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-cyan-400" />
                <h3 className="font-bold text-white text-xs uppercase tracking-wider">WHAT CHANGED — {comparisonData.label}</h3>
              </div>
              <div className="flex gap-1">
                {(["1m", "5m", "15m", "open"] as const).map(win => (
                  <button
                    key={win}
                    onClick={() => setCompareWindow(win)}
                    className={`px-2 py-0.5 rounded text-[9px] font-bold border transition ${
                      compareWindow === win
                        ? "border-cyan-600 bg-cyan-950/40 text-cyan-300"
                        : "border-slate-800 text-slate-500 hover:text-white"
                    }`}
                  >
                    {win.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {isClosed ? (
              <div className="p-3 bg-slate-950/80 rounded border border-slate-850 text-xs font-mono text-slate-400 space-y-1">
                <div className="font-bold text-amber-400 flex items-center gap-1.5">
                  <Clock size={14} />
                  <span>Closed-session snapshot unchanged</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Live NSE market-session intraday comparison is paused after market close. Global cues and news context continue updating independently.
                </p>
              </div>
            ) : comparisonData.available ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                  <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
                    <span className="text-[10px] text-slate-500 block font-bold">NIFTY</span>
                    <span className="font-semibold text-white block">
                      {formatNumber(spot - comparisonData.diffSpot, 1)} <ArrowRight size={10} className="inline mx-1 text-slate-600" /> {formatNumber(spot, 1)}
                    </span>
                    <span className={`text-[10px] font-bold ${comparisonData.diffSpot >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {comparisonData.diffSpot >= 0 ? "+" : ""}{formatNumber(comparisonData.diffSpot, 1)} pts ({comparisonData.spotStatus})
                    </span>
                  </div>

                  <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
                    <span className="text-[10px] text-slate-500 block font-bold">BREADTH</span>
                    <span className="font-semibold text-white block">
                      {advances - comparisonData.diffAdv}A <ArrowRight size={10} className="inline mx-1 text-slate-600" /> {advances}A
                    </span>
                    <span className={`text-[10px] font-bold ${comparisonData.breadthStatus === "Improving" ? "text-emerald-400" : "text-slate-400"}`}>
                      {comparisonData.breadthStatus} ({comparisonData.diffAdv >= 0 ? "+" : ""}{comparisonData.diffAdv} advances)
                    </span>
                  </div>

                  <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
                    <span className="text-[10px] text-slate-500 block font-bold">PCR</span>
                    <span className="font-semibold text-white block">
                      {formatNumber(pcr - comparisonData.diffPCR, 2)} <ArrowRight size={10} className="inline mx-1 text-slate-600" /> {formatNumber(pcr, 2)}
                    </span>
                    <span className={`text-[10px] font-bold ${comparisonData.pcrStatus === "Improving" ? "text-emerald-400" : "text-slate-400"}`}>
                      {comparisonData.pcrStatus}
                    </span>
                  </div>

                  <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
                    <span className="text-[10px] text-slate-500 block uppercase">VIX</span>
                    <span className="font-semibold text-white block">
                      {formatNumber(vix - comparisonData.diffVix, 2)} <ArrowRight size={10} className="inline mx-1 text-slate-600" /> {formatNumber(vix, 2)}
                    </span>
                    <span className={`text-[10px] font-bold ${comparisonData.vixStatus === "Supportive" ? "text-emerald-400" : "text-slate-400"}`}>
                      {comparisonData.vixStatus}
                    </span>
                  </div>

                  <div className="p-2.5 bg-slate-950 rounded border border-slate-850 col-span-2">
                    <span className="text-[10px] text-slate-500 block uppercase font-bold">INTERPRETATION</span>
                    <span className="text-[11px] leading-relaxed text-cyan-300 font-sans block mt-0.5">
                      {comparisonData.interpretation}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">Unavailable — No current-session comparison history</p>
            )}
          </section>

          {/* ── 3. CONFIRMATION MATRIX ── */}
          <section className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 font-mono">
            <div className="flex justify-between items-center border-b border-slate-850 pb-2.5">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-purple-400" />
                <h3 className="font-bold text-white text-xs uppercase tracking-wider">CONFIRMATION MATRIX</h3>
              </div>
              <span className="text-[9px] text-slate-500">Cross-market verification</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              {Object.entries(confirmationMatrix).map(([family, item]: [string, any]) => {
                const isBull = ["Bullish", "Supportive", "Positive"].includes(item.bias);
                const isBear = ["Bearish", "Risk", "Negative"].includes(item.bias);
                const arrow = arrowDirections[family as keyof typeof arrowDirections] || "→";

                return (
                  <div key={family} className="p-2.5 bg-slate-950 rounded border border-slate-850 flex justify-between items-center">
                    <div className="min-w-0">
                      <span className="text-[9px] text-slate-500 block font-bold uppercase">{family}</span>
                      <span className={`font-semibold block ${isBull ? "text-emerald-400" : isBear ? "text-rose-400" : "text-slate-300"}`}>
                        {item.bias}
                      </span>
                    </div>
                    <span className={`text-base font-bold shrink-0 ml-1 ${arrow === "↑" ? "text-emerald-400" : arrow === "↓" ? "text-rose-400" : "text-slate-500"}`}>
                      {arrow}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>
        </div>

        {/* RIGHT COLUMN: SCENARIOS & WHAT MATTERS NEXT */}
        <div className="lg:col-span-5 space-y-5">
          {/* ── 4. ACTIVE MARKET BEHAVIOR ── */}
          <section className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 font-mono">
            <div className="flex items-center gap-2 border-b border-slate-850 pb-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">ACTIVE MARKET BEHAVIOR</h3>
            </div>
            <div className="text-xs">
              <div className="font-bold text-cyan-300 text-sm">
                {safeString(state?.unified_intelligence?.preferred_setup?.title || "Mixed Setup")}
              </div>
              <p className="text-slate-400 text-[11px] leading-relaxed mt-1 font-sans">
                {safeString(state?.unified_intelligence?.preferred_setup?.description || "Market structure is currently mixed. Awaiting clearer directional alignment across price action, options build-up, and institutional flows.")}
              </p>
            </div>
          </section>

          {/* ── 5. WHAT MATTERS NEXT ── */}
          <section className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 font-mono">
            <div className="flex items-center gap-2 border-b border-slate-850 pb-2">
              <Info className="h-4 w-4 text-cyan-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">WHAT MATTERS NEXT</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 bg-slate-950 rounded border border-emerald-950/60">
                <span className="text-[9px] text-slate-500 block uppercase font-bold">NEAREST SUPPORT</span>
                <span className="font-bold text-emerald-400 text-sm block mt-0.5">
                  {nearestSupport ? formatNumber(nearestSupport.level, 0) : "--"}
                </span>
                <span className="text-[9px] text-slate-500 block truncate mt-0.5">{nearestSupport?.name || "No support defined"}</span>
              </div>
              <div className="p-2.5 bg-slate-950 rounded border border-rose-950/60">
                <span className="text-[9px] text-slate-500 block uppercase font-bold">NEAREST RESISTANCE</span>
                <span className="font-bold text-rose-400 text-sm block mt-0.5">
                  {nearestResistance ? formatNumber(nearestResistance.level, 0) : "--"}
                </span>
                <span className="text-[9px] text-slate-500 block truncate mt-0.5">{nearestResistance?.name || "No resistance defined"}</span>
              </div>
            </div>
          </section>
        </div>
      </div>

      {/* ── 6. SCENARIO MONITOR ── */}
      <section className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-3 font-mono">
        <div className="flex justify-between items-center border-b border-slate-850 pb-2.5">
          <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider">
            <Activity size={16} className="text-cyan-400" />
            <span>SCENARIO MONITOR</span>
          </div>
          <span className="text-[9px] text-slate-500 font-mono">Full scenario conditions matrix</span>
        </div>

        {scenarios.length === 0 ? (
          <p className="text-xs text-slate-500 italic">{isClosed ? "Next Session — Pending" : "No canonical scenarios are active in this state snapshot."}</p>
        ) : (
          <ScenarioGrid scenarios={scenarios} />
        )}
      </section>

      {/* ── 7. LIVE STATE EVENT STREAM / CANONICAL GLOBAL EVENTS ── */}
      <section className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 border-b border-slate-850 pb-3">
          <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider" aria-label="CANONICAL GLOBAL EVENTS" data-stream="LIVE EVENT STREAM">
            <Clock size={16} className="text-emerald-400 animate-pulse" />
            <span>LIVE STATE EVENT STREAM</span>
          </div>
          <div className="flex items-center gap-2 text-[10px]">
            <span className="text-slate-500 font-bold">Sort:</span>
            <button
              onClick={() => setEventSort("newest")}
              className={`px-2 py-0.5 rounded border transition ${
                eventSort === "newest"
                  ? "border-emerald-600 bg-emerald-950/40 text-emerald-300 font-bold"
                  : "border-slate-800 text-slate-500"
              }`}
            >
              Newest First
            </button>
            <button
              onClick={() => setEventSort("materiality")}
              className={`px-2 py-0.5 rounded border transition ${
                eventSort === "materiality"
                  ? "border-emerald-600 bg-emerald-950/40 text-emerald-300 font-bold"
                  : "border-slate-800 text-slate-500"
              }`}
            >
              Materiality
            </button>
          </div>
        </div>

        {sortedEvents.length === 0 ? (
          <p className="text-xs text-slate-500 italic">{isClosed ? "No current-session material events yet" : "Awaiting material market state events..."}</p>
        ) : (
          <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
            {sortedEvents.map(ev => {
              const isHigh = ev.materiality === "high";
              const desc = ev.description || ev.message || "";
              const familyTag = ev.family || (desc.includes("Regime") ? "REGIME" : desc.includes("Breadth") ? "BREADTH" : desc.includes("Alignment") ? "ALIGNMENT" : desc.includes("PCR") ? "OPTIONS" : desc.includes("VIX") ? "VOLATILITY" : "SYSTEM");

              return (
                <div key={ev.id} className="flex justify-between items-start gap-4 p-2 bg-slate-900/40 border border-slate-850 rounded text-xs">
                  <div className="flex items-start gap-2">
                    <span className="text-slate-500 font-mono text-[10px] shrink-0">{ev.occurred_at || ev.timestamp}</span>
                    <span className="px-1.5 py-0.5 rounded text-[8px] font-bold border bg-cyan-950/40 text-cyan-400 border-cyan-800/60 font-mono shrink-0">{familyTag}</span>
                    <span className={`font-semibold ${isHigh ? "text-amber-400" : "text-slate-200"}`}>
                      {desc}
                    </span>
                  </div>
                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${isHigh ? "bg-amber-950/50 text-amber-400 border border-amber-800/60" : "bg-slate-950 text-slate-500 border border-slate-800"}`}>
                    {ev.materiality.toUpperCase()}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
