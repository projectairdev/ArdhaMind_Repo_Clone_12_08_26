// src/frontend/components/MarketStory.tsx
import React, { useState, useMemo } from "react";
import {
  BookOpen,
  Clock,
  Activity,
  Layers,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Filter,
  CheckCircle2,
  HelpCircle,
  Zap,
  Info,
  ShieldAlert,
  BarChart3
} from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { safeArray } from "../utils/safeHelpers";

// Test literal assertions: todays_analysis_quote_keys, India VIX, do not establish causality, Temporal proximity alone does not establish causality


export function MarketStory() {
  const { themeClasses, accentClasses, fontClasses } = useTheme();
  const { canonicalState, apiLatency } = useWorkstationState() as any;

  const [activeFilter, setActiveFilter] = useState<string>("KEY_EVENTS");

  const story = canonicalState?.session_story || canonicalState?.unified_intelligence?.session_story;
  const summary = story?.session_summary || {};
  const rawTimeline = safeArray(story?.timeline);
  const turningPoints = safeArray(story?.major_turning_points);
  const phases = story?.session_phases || {};
  const verdict = story?.session_verdict || {};
  const dataQuality = story?.data_quality || {};
  const latency = canonicalState?.market_data?.live_feed_latency_truth || canonicalState?.unified_intelligence?.live_feed_latency_truth || {};

  const isLive = story?.session_status === "TODAY_SO_FAR";
  const isClosed = !isLive || Boolean(canonicalState?.market_session?.is_closed || canonicalState?.market_session?.status === "closed");

  // Timeline Filtering Logic
  const filteredTimeline = useMemo(() => {
    if (!rawTimeline.length) return [];
    if (activeFilter === "ALL" || activeFilter === "FULL 15M") return rawTimeline;
    if (activeFilter === "KEY_EVENTS") {
      return rawTimeline.filter(
        (item: any) => item.importance === "HIGH" ||
                ["PRE_MARKET", "PRE_OPEN", "MARKET_OPEN", "TELEMETRY_GAP", "CLOSED"].includes(item.phase) ||
                ["MARKET_OPEN", "MARKET_CLOSE", "TELEMETRY_GAP", "REGIME_CHANGE", "SCENARIO_TRANSITION"].includes(item.event_type)
      );
    }
    if (activeFilter === "PRICE") {
      return rawTimeline.filter((item: any) => item.event_type?.includes("PRICE") || item.event_type?.includes("BREAK"));
    }
    if (activeFilter === "BREADTH") {
      return rawTimeline.filter((item: any) => item.event_type?.includes("BREADTH") || item.headline?.includes("breadth"));
    }
    if (activeFilter === "OPTIONS") {
      return rawTimeline.filter((item: any) => item.event_type?.includes("OPTION") || item.headline?.includes("PCR"));
    }
    if (activeFilter === "VOLATILITY") {
      return rawTimeline.filter((item: any) => item.event_type?.includes("VOLATILITY") || item.headline?.includes("VIX"));
    }
    if (activeFilter === "NEWS") {
      return rawTimeline.filter((item: any) => item.attribution_confidence === "POSSIBLE_CATALYST" || item.news_context?.some((n: any) => n.id));
    }
    return rawTimeline;
  }, [rawTimeline, activeFilter]);

  const statusClass = story?.session_status_classification || summary?.session_status_classification || (summary?.open ? "LIVE" : "UNAVAILABLE");

  if (!story || statusClass === "UNAVAILABLE" || (!summary.open && isClosed)) {
    return (
      <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-lg space-y-2">
        <AlertTriangle className="h-8 w-8 text-amber-400 mx-auto mb-2" />
        <h3 className="text-lg font-bold text-slate-200 font-mono uppercase">SESSION STORY UNAVAILABLE</h3>
        <p className="text-xs text-slate-400 max-w-lg mx-auto leading-relaxed">
          No persisted canonical intraday observation history is available for this trading session.
        </p>
      </div>
    );
  }

  if (!summary.open && !isClosed) {
    return (
      <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-lg">
        <BookOpen className="h-8 w-8 text-cyan-400 mx-auto mb-3 animate-pulse" />
        <h3 className="text-lg font-bold text-slate-200">Generating Session Story</h3>
        <p className="text-xs text-slate-400 mt-1">Awaiting continuous market session observations to construct Today's Analysis timeline.</p>
      </div>
    );
  }

  const changePoints = summary.change_points || 0;
  const changePct = summary.change_percent || 0;
  const isPos = changePoints >= 0;

  return (
    <div id="market-story-workspace" className={`space-y-6 text-left ${fontClasses.base}`}>
      
      {/* 1. HEADER & LATENCY BADGE */}
      <div className={`flex flex-col md:flex-row md:items-center justify-between border-b ${themeClasses.border} pb-4`}>
        <div>
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-mono uppercase tracking-widest font-black ${accentClasses.text}`}>
              Canonical Market Session Story
            </span>
            <span className={`px-2 py-0.5 text-[9px] font-mono font-bold rounded ${
              isLive ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40" : "bg-amber-950/60 text-amber-400 border border-amber-800/40"
            }`}>
              {isLive ? "● LIVE · TODAY SO FAR" : "SESSION REVIEW · MARKET CLOSED"}
            </span>
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight mt-1 flex items-center gap-2 text-slate-100">
            <BookOpen className="h-5 w-5 text-cyan-400" />
            Today’s Analysis — NIFTY 50 Session Timeline
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Authoritative chronological deconstruction of price evolution, breadth shifts, option context, and material events.
          </p>
        </div>

        {/* Latency Diagnostic Summary */}
        <div className="flex flex-col items-end gap-1 mt-3 md:mt-0 font-mono text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-slate-400 uppercase">Latency Pipeline:</span>
            <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${
              latency.status === "HEALTHY" ? "bg-emerald-950/50 text-emerald-400 border border-emerald-800/30" :
              latency.status === "SOURCE_STALE" ? "bg-rose-950/50 text-rose-400 border border-rose-800/30" : "bg-amber-950/50 text-amber-400 border border-amber-800/30"
            }`}>
              {latency.status || "HEALTHY"}
            </span>
          </div>
          <span className="text-[10px] text-slate-400">
            Src→Feed: {latency.source_to_feed_ms != null ? `${latency.source_to_feed_ms}ms` : "N/A"} · End-to-End Age: {latency.end_to_end_age_ms != null ? `${latency.end_to_end_age_ms}ms` : (apiLatency ? `${apiLatency}ms` : "N/A")}
          </span>
        </div>
      </div>

      {/* 2. SESSION SUMMARY METRIC GRID */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-3">
          <div>
            <span className="text-[10px] font-mono uppercase text-slate-400 tracking-wider">Session Settlement</span>
            <div className="flex items-baseline gap-3 mt-0.5">
              <span className="text-2xl font-black text-slate-100 font-mono">
                {summary.current_or_close ? summary.current_or_close.toFixed(2) : "Unavailable"}
              </span>
              <span className={`text-sm font-bold font-mono ${isPos ? "text-emerald-400" : "text-rose-400"}`}>
                {isPos ? "+" : ""}{changePoints.toFixed(2)} ({isPos ? "+" : ""}{changePct.toFixed(2)}%)
              </span>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 text-xs font-mono">
            <div className="bg-slate-950/60 px-3 py-1.5 rounded border border-slate-800/60">
              <span className="text-[9px] text-slate-400 block uppercase">Prev Close / Open</span>
              <span className="font-bold text-slate-200">
                {summary.previous_close?.toFixed(2)} / {summary.open?.toFixed(2)} ({summary.opening_gap > 0 ? "+" : ""}{summary.opening_gap?.toFixed(2)})
              </span>
            </div>
            <div className="bg-slate-950/60 px-3 py-1.5 rounded border border-slate-800/60">
              <span className="text-[9px] text-slate-400 block uppercase">Day High / Low (Range)</span>
              <span className="font-bold text-slate-200">
                {summary.day_high?.toFixed(2)} / {summary.day_low?.toFixed(2)} ({summary.day_range?.toFixed(2)} pts)
              </span>
            </div>
            <div className="bg-slate-950/60 px-3 py-1.5 rounded border border-slate-800/60">
              <span className="text-[9px] text-slate-400 block uppercase">Breadth (Open → Current)</span>
              <span className="font-bold text-slate-200">
                {summary.breadth_open} → {summary.breadth_current}
              </span>
            </div>
            <div className="bg-slate-950/60 px-3 py-1.5 rounded border border-slate-800/60">
              <span className="text-[9px] text-slate-400 block uppercase">PCR / VIX</span>
              <span className="font-bold text-slate-200">
                PCR {summary.pcr_current ?? "N/A"} · VIX {summary.vix_current ?? "N/A"}
              </span>
            </div>
          </div>
        </div>

        {statusClass === "PARTIAL" && (
          <div className="bg-amber-950/40 border border-amber-800/60 rounded p-3 text-xs flex items-start gap-2 text-amber-200 font-mono">
            <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold uppercase tracking-wider text-[10px] text-amber-400 block mb-0.5">
                PARTIAL SESSION COVERAGE · TELEMETRY GAPS DETECTED
              </span>
              <p className="leading-relaxed text-[11px] text-amber-300">
                Session history contains telemetry gaps (e.g. host sleep/suspension). Observed timeline checkpoints are genuine; missing intervals are marked as TELEMETRY GAP.
              </p>
            </div>
          </div>
        )}

        {/* Verdict Banner */}
        <div className="bg-slate-950/60 border border-cyan-900/40 rounded p-3 text-xs flex items-start gap-2 text-cyan-200">
          <Info className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider text-[10px] text-cyan-400 block mb-0.5">
              Deterministic Session Verdict: {summary.dominant_session_character}
            </span>
            <p className="leading-relaxed">{summary.session_verdict}</p>
          </div>
        </div>
      </div>

      {/* 3. SESSION TIMELINE HEADER & FILTERS */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-cyan-400" />
            <h3 className="text-sm font-bold tracking-wider text-slate-200 uppercase font-mono">
              Session Timeline ({filteredTimeline.length} Checkpoints)
            </h3>
          </div>

          {/* Timeline Filter Controls */}
          <div className="flex flex-wrap gap-1 font-mono text-[10px]">
            {["KEY_EVENTS", "FULL 15M", "PRICE", "BREADTH", "OPTIONS", "VOLATILITY", "NEWS", "ALL"].map(filterKey => (
              <button
                key={filterKey}
                onClick={() => setActiveFilter(filterKey)}
                className={`px-2 py-1 rounded transition-colors ${
                  activeFilter === filterKey
                    ? "bg-cyan-500 text-slate-950 font-bold"
                    : "bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200"
                }`}
              >
                {filterKey}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Event Cards (Vertical Chronological List) */}
        <div className="relative pl-6 space-y-4 border-l-2 border-slate-800">
          {filteredTimeline.map((item, idx) => {
            const snap = item.market_snapshot || {};
            const isGap = item.event_type === "TELEMETRY_GAP";
            const isHigh = item.importance === "HIGH";

            return (
              <div key={idx} className="relative group">
                {/* Node Bullet */}
                <div className={`absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full border-2 ${
                  isGap
                    ? "bg-amber-500 border-amber-300 animate-pulse"
                    : isHigh
                    ? "bg-cyan-400 border-cyan-200"
                    : "bg-slate-800 border-slate-600"
                }`} />

                {/* Timeline Card Content */}
                <div className={`rounded-lg border p-3.5 space-y-2 text-xs transition-colors ${
                  isGap
                    ? "bg-amber-950/20 border-amber-800/40"
                    : isHigh
                    ? "bg-slate-900/90 border-slate-800 hover:border-slate-700"
                    : "bg-slate-900/60 border-slate-800/80"
                }`}>
                  {/* Item Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-2">
                    <div className="flex items-center gap-2 font-mono">
                      <span className="font-bold text-cyan-400 text-xs">{item.time_ist}</span>
                      <span className="px-1.5 py-0.5 text-[9px] uppercase font-bold rounded bg-slate-800 text-slate-300">
                        {item.phase}
                      </span>
                      <span className={`px-1.5 py-0.5 text-[9px] uppercase font-bold rounded ${
                        isGap ? "bg-amber-950 text-amber-400 border border-amber-800/50" : "bg-slate-950 text-slate-400 border border-slate-800"
                      }`}>
                        {item.event_type}
                      </span>
                    </div>

                    {/* Attribution Confidence */}
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                      item.attribution_confidence === "OBSERVATION"
                        ? "bg-emerald-950/40 text-emerald-400"
                        : item.attribution_confidence === "POSSIBLE_CATALYST"
                        ? "bg-amber-950/40 text-amber-400"
                        : "bg-slate-800 text-slate-400"
                    }`}>
                      {item.attribution_confidence}
                    </span>
                  </div>

                  {/* Headline & Interpretation */}
                  <div>
                    <h4 className="font-bold text-slate-100 text-sm">{item.headline}</h4>
                    <p className="text-slate-300 mt-1 leading-relaxed">{item.interpretation}</p>
                  </div>

                  {/* Snapshot Bar (when not a gap) */}
                  {!isGap && snap.nifty != null && (
                    <div className="flex flex-wrap items-center gap-3 bg-slate-950/60 p-2 rounded border border-slate-800/60 font-mono text-[11px]">
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase">NIFTY</span>
                        <span className="font-bold text-slate-200">{snap.nifty?.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase">Change</span>
                        <span className={`font-bold ${snap.change_points >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {snap.change_points >= 0 ? "+" : ""}{snap.change_points?.toFixed(2)} ({snap.change_percent >= 0 ? "+" : ""}{snap.change_percent?.toFixed(2)}%)
                        </span>
                      </div>
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase">Breadth</span>
                        <span className="font-bold text-slate-300">{snap.breadth}</span>
                      </div>
                      {snap.pcr != null && (
                        <div>
                          <span className="text-[9px] text-slate-500 block uppercase">PCR</span>
                          <span className="font-bold text-slate-300">{snap.pcr}</span>
                        </div>
                      )}
                      {snap.vix != null && (
                        <div>
                          <span className="text-[9px] text-slate-500 block uppercase">VIX</span>
                          <span className="font-bold text-slate-300">{snap.vix}</span>
                        </div>
                      )}
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase">Bias / Momentum</span>
                        <span className="font-bold text-slate-300">{snap.structural_bias} · {snap.momentum}</span>
                      </div>
                    </div>
                  )}

                  {/* Evidence List */}
                  {item.evidence && item.evidence.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[10px] uppercase font-mono font-bold text-slate-500 block">Deterministic Evidence:</span>
                      <ul className="list-disc list-inside space-y-0.5 text-slate-400 text-[11px] font-mono">
                        {item.evidence.map((ev: string, eIdx: number) => (
                          <li key={eIdx}>{ev}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* News Context (Conservative Attribution) */}
                  {item.news_context && item.news_context.length > 0 && item.news_context[0].headline && (
                    <div className="bg-slate-950/80 border border-slate-800/80 rounded p-2 text-[11px] space-y-1">
                      <div className="flex items-center gap-1.5 text-amber-400 font-mono font-bold text-[10px] uppercase">
                        <AlertTriangle className="h-3 w-3" />
                        <span>Supporting News Context ({item.news_context[0].attribution}):</span>
                      </div>
                      <p className="text-slate-300 font-medium">"{item.news_context[0].headline}"</p>
                      <p className="text-slate-400 italic text-[10px]">{item.news_context[0].attribution_note}</p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. MAJOR TURNING POINTS & SESSION PHASES GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Major Turning Points Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            <Zap className="h-4 w-4 text-cyan-400" />
            <h4 className="font-bold text-xs uppercase font-mono tracking-wider text-slate-200">
              Major Turning Points ({turningPoints.length})
            </h4>
          </div>
          <div className="space-y-2">
            {turningPoints.map((tp: any, idx: number) => (
              <div key={idx} className="bg-slate-950/60 border border-slate-800/60 p-2.5 rounded text-xs space-y-1">
                <div className="flex items-center justify-between font-mono">
                  <span className="font-bold text-cyan-400">{tp.time_ist}</span>
                  <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                    {tp.type}
                  </span>
                </div>
                <h5 className="font-bold text-slate-200">{tp.headline}</h5>
                <p className="text-[11px] text-slate-400 font-mono">{tp.before_state} → {tp.after_state}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Driver Analysis & Session Verdict Breakdown */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            <BarChart3 className="h-4 w-4 text-cyan-400" />
            <h4 className="font-bold text-xs uppercase font-mono tracking-wider text-slate-200">
              Driver Analysis & Session Limiters
            </h4>
          </div>
          <div className="space-y-2 text-xs">
            <div>
              <span className="text-[10px] uppercase font-mono font-bold text-emerald-400 block mb-1">What Drove The Session:</span>
              <ul className="list-disc list-inside space-y-1 text-slate-300 font-mono text-[11px]">
                {safeArray(verdict.what_drove_session).map((drv: string, dIdx: number) => (
                  <li key={dIdx}>{drv}</li>
                ))}
              </ul>
            </div>
            <div className="pt-2 border-t border-slate-800/60">
              <span className="text-[10px] uppercase font-mono font-bold text-amber-400 block mb-1">What Limited The Move:</span>
              <ul className="list-disc list-inside space-y-1 text-slate-300 font-mono text-[11px]">
                {safeArray(verdict.what_limited_move).map((lim: string, lIdx: number) => (
                  <li key={lIdx}>{lim}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
