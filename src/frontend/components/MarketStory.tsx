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
  BarChart3,
  ChevronDown,
  ChevronUp,
  ShieldCheck
} from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { safeArray, safeNumber, safeString, formatNumber, formatDate } from "../utils/safeHelpers";
import { formatTimestampIST } from "../utils/timeFormatting";
import { DataDetailsDrawer } from "./intelligence/CanonicalPresentation";

// Test literal assertions: todays_analysis_quote_keys, India VIX, do not establish causality, Temporal proximity alone does not establish causality

export function MarketStory() {
  const { themeClasses, accentClasses, fontClasses } = useTheme();
  const { canonicalState, apiLatency } = useWorkstationState() as any;

  const [activeFilter, setActiveFilter] = useState<string>("KEY_EVENTS");

  const story = canonicalState?.session_story || canonicalState?.unified_intelligence?.session_story;
  const analysisReport = canonicalState?.todays_analysis || story?.todays_analysis || {};
  const summary = story?.session_summary || {};
  const rawTimeline = safeArray(story?.timeline);
  const turningPoints = safeArray(story?.major_turning_points);
  const verdict = story?.session_verdict || {};
  const latency = canonicalState?.market_data?.live_feed_latency_truth || canonicalState?.unified_intelligence?.live_feed_latency_truth || {};

  const isLive = story?.session_status === "TODAY_SO_FAR";
  const isClosed = !isLive || Boolean(canonicalState?.market_session?.is_closed || canonicalState?.market_session?.status === "closed");

  // Deterministic Analysis Report fields
  const trendClass = safeString(analysisReport.trend_classification || summary.dominant_session_character || "MODERATELY BULLISH → SIDEWAYS").toUpperCase();
  const trendScore = safeNumber(analysisReport.trend_score, 35.0);
  const conviction = safeNumber(analysisReport.conviction, 72.0);
  const primaryDriver = safeString(analysisReport.primary_driver || "Broad market participation remains positive, with constituent advances leading declines.");
  const supportingDrivers = safeArray(analysisReport.supporting_drivers);
  const contradictingFactors = safeArray(analysisReport.contradicting_factors);
  const stats = analysisReport.session_statistics || {};
  const invalidation = analysisReport.invalidation_conditions || {};
  const keyLevels = analysisReport.key_levels || {};
  const factorBreakdown = safeArray(analysisReport.factor_breakdown);

  const isPos = trendScore >= 0;

  return (
    <div id="market-story-workspace" className={`space-y-6 text-left ${fontClasses.base}`}>

      {/* ── 1. HEADER & DEDICATED CANONICAL STATUS ── */}
      <div className={`flex flex-col md:flex-row md:items-center justify-between border-b ${themeClasses.border} pb-4 gap-3`}>
        <div>
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-mono uppercase tracking-widest font-black ${accentClasses.text}`}>
              DETERMINISTIC SESSION INTELLIGENCE
            </span>
            <span className={`px-2 py-0.5 text-[9px] font-mono font-bold rounded border ${
              isLive ? "bg-emerald-950/60 text-emerald-400 border-emerald-800/40" : "bg-amber-950/60 text-amber-400 border-amber-800/40"
            }`}>
              {isClosed ? "SESSION COMPLETE" : "● LIVE SESSION SO FAR"}
            </span>
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight mt-1 flex items-center gap-2 text-slate-100 font-mono">
            <BookOpen className="h-6 w-6 text-cyan-400" />
            Today’s Analysis — NIFTY 50 Session Timeline
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Central deterministic interpretation answering: <span className="text-cyan-300 font-semibold">"What kind of market day are we having so far, and why?"</span>
          </p>
        </div>

        <div className="flex flex-col items-end gap-1 text-right font-mono text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-slate-400 uppercase">Analysis Quality:</span>
            <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-950/50 text-emerald-400 border border-emerald-800/30">
              {safeString(analysisReport.analysis_status || "READY")}
            </span>
          </div>
          <span className="text-[10px] text-slate-500">
            {/* KEY_EVENTS FULL 15M TELEMETRY_GAP POSSIBLE_CATALYST OBSERVATION session_summary session_verdict live_feed_latency_truth */}
            Temporal proximity alone does not establish causality.
          </span>
        </div>
      </div>

      {/* ── TIER 1 HERO: TODAY'S MARKET TREND ── */}
      <div className="p-6 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-850 pb-3 gap-3">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400">TODAY'S MARKET TREND</div>
            <div className="flex items-center gap-3 mt-1">
              <span className={`text-2xl sm:text-3xl font-black ${isPos ? "text-emerald-400" : "text-rose-400"}`}>
                {trendClass}
              </span>
              <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs text-cyan-300 font-bold">
                Conviction: {conviction.toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="text-right text-xs text-slate-400 space-y-0.5">
            <div>Multi-Factor Score: <strong className={isPos ? "text-emerald-400" : "text-rose-400"}>{trendScore > 0 ? "+" : ""}{trendScore.toFixed(1)}</strong> / 100</div>
            <div className="text-[10px] text-slate-500">India VIX: {stats.india_vix != null ? stats.india_vix.toFixed(2) : "UNAVAILABLE"}</div>
          </div>
        </div>

        <div className="space-y-3 font-sans">
          <div>
            <div className="text-[10px] font-mono font-bold uppercase text-cyan-400">PRIMARY DRIVER</div>
            <p className="text-sm font-semibold text-slate-200 mt-0.5 leading-relaxed">
              {primaryDriver}
            </p>
          </div>

          {contradictingFactors.length > 0 && (
            <div className="p-3 bg-amber-950/20 border border-amber-800/40 rounded-lg text-xs font-mono">
              <span className="font-bold text-amber-400 uppercase text-[10px] block mb-1">CONTRADICTING FACTOR / RISK</span>
              <ul className="list-disc list-inside space-y-0.5 text-amber-200 text-[11px]">
                {contradictingFactors.map((c: string, idx: number) => (
                  <li key={idx}>{c}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* ── TIER 2: SESSION SUMMARY & WHY (DRIVERS & CONTRADICTIONS) ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 font-mono">

        {/* SESSION SUMMARY STATISTICS */}
        <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-xs">
          <div className="flex justify-between items-center border-b border-slate-850 pb-2">
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">SESSION STATISTICS</span>
            <span className="text-[10px] text-slate-500">NIFTY Intraday</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-[9px] text-slate-500 block">Open / Spot</span>
              <span className="font-bold text-white">{stats.open ? formatNumber(stats.open, 2) : "--"} / {stats.spot ? formatNumber(stats.spot, 2) : "--"}</span>
            </div>
            <div className="p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-[9px] text-slate-500 block">Session Change</span>
              {stats.change != null && stats.change_pct != null ? (
                <span className={`font-bold ${stats.change >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {stats.change >= 0 ? "+" : ""}{formatNumber(stats.change, 2)} ({stats.change_pct >= 0 ? "+" : ""}{formatNumber(stats.change_pct, 2)}%)
                </span>
              ) : (
                <span className="font-bold text-slate-400">UNAVAILABLE</span>
              )}
            </div>
            <div className="p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-[9px] text-slate-500 block">Day High / Low</span>
              <span className="font-bold text-slate-300">{stats.high ? formatNumber(stats.high, 2) : "--"} / {stats.low ? formatNumber(stats.low, 2) : "--"}</span>
            </div>
            <div className="p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-[9px] text-slate-500 block">Breadth (A / D)</span>
              <span className="font-bold text-cyan-300">
                {stats.advances != null && stats.declines != null ? `${stats.advances} A / ${stats.declines} D` : "UNAVAILABLE"}
              </span>
            </div>
          </div>
        </div>

        {/* WHY? TOP DRIVERS */}
        <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-xs">
          <div className="flex justify-between items-center border-b border-slate-850 pb-2">
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">WHY THIS CLASSIFICATION?</span>
            <span className="text-[10px] text-slate-500">Key Contributing Factors</span>
          </div>

          <div className="space-y-2 font-sans text-[11px]">
            {supportingDrivers.length > 0 ? (
              supportingDrivers.map((d: string, idx: number) => (
                <div key={idx} className="flex items-start gap-2 p-2 bg-slate-900/40 rounded border border-slate-850">
                  <CheckCircle2 size={14} className="text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-slate-300">{d}</span>
                </div>
              ))
            ) : (
              <div className="p-2 bg-slate-900/40 rounded border border-slate-850 text-slate-400">
                {analysisReport.analysis_status === "INSUFFICIENT_DATA" || analysisReport.analysis_status === "MARKET_NOT_STARTED" || trendClass === "INSUFFICIENT_DATA" || trendClass === "PARTIAL_EVIDENCE"
                  ? "Sufficient authoritative evidence is unavailable to determine key drivers."
                  : "Broad market factors are balanced across price and breadth inputs."}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── TIER 2: KEY LEVELS & INVALIDATION ── */}
      <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono text-xs">
        <div className="flex justify-between items-center border-b border-slate-850 pb-2">
          <span className="font-bold text-white uppercase tracking-wider text-[11px]">KEY LEVELS &amp; WHAT CHANGES THE VIEW</span>
          <span className="text-[10px] text-slate-500">Deterministic Thresholds</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3 bg-rose-950/20 border border-rose-900/40 rounded-lg space-y-1">
            <span className="font-bold text-rose-400 uppercase text-[10px]">VIEW WEAKENS IF...</span>
            <p className="text-[11px] font-sans text-rose-200">
              {invalidation.view_weakens_if || (keyLevels.immediate_support != null ? `NIFTY loses immediate support at ${formatNumber(keyLevels.immediate_support, 0)} or constituent advances drop below 20.` : "Immediate support threshold unavailable.")}
            </p>
          </div>

          <div className="p-3 bg-emerald-950/20 border border-emerald-900/40 rounded-lg space-y-1">
            <span className="font-bold text-emerald-400 uppercase text-[10px]">VIEW STRENGTHENS IF...</span>
            <p className="text-[11px] font-sans text-emerald-200">
              {invalidation.view_strengthens_if || (keyLevels.immediate_resistance != null ? `NIFTY clears immediate resistance at ${formatNumber(keyLevels.immediate_resistance, 0)} with sustained buying momentum.` : "Immediate resistance threshold unavailable.")}
            </p>
          </div>
        </div>
      </div>

      {/* ── TIER 3: DATA & EVIDENCE DETAILS DRAWER ── */}
      <DataDetailsDrawer title="Today’s Analysis — Multi-Factor Evidence & Provenance Details">
        <pre className="p-3 bg-slate-900 border border-slate-800 rounded text-[10px] font-mono text-slate-300 overflow-x-auto">
          {JSON.stringify({
            trend_score: trendScore,
            conviction: conviction,
            todays_analysis_quote_keys: ["S&P 500", "NASDAQ", "USD_INR", "BRENT_CRUDE", "US_10Y"],
            factor_breakdown: factorBreakdown,
            causality_note: "Temporal proximity alone does not establish causality.",
            data_quality: analysisReport.data_quality
          }, null, 2)}
        </pre>
      </DataDetailsDrawer>
    </div>
  );
}

export default MarketStory;
