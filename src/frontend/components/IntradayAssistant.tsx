// src/frontend/components/IntradayAssistant.tsx
import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { AlertCircle, Activity, ShieldCheck, Info } from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber
} from "../utils/safeHelpers";

export function IntradayAssistant() {
  const { intradayReport: report, syncBroker, market_session, marketContext, canonicalState, data } = useWorkstationState() as any;
  const isClosed = Boolean(market_session?.is_closed || market_session?.status === "closed" || market_session?.status === "holiday" || marketContext?.session_mode === "LAST_SESSION");
  const loading = false;
  const error = null;
  const fetchIntraday = async () => { await syncBroker(true); };

  if (loading) {
    return (
      <div id="intraday-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-44 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (isClosed) {
    const spot = safeNumber(marketContext?.current_spot, 0);
    const macroObj = canonicalState?.macro_intelligence || data?.macro_intelligence || {};
    const vixContext: any = macroObj.india_vix || marketContext?.india_vix_context || {};
    const vix = vixContext.value != null && vixContext.observation_timestamp ? safeNumber(vixContext.value, 0) : 0;
    const macroQuotes = macroObj.quotes || {};
    const newsObj = canonicalState?.news_intelligence || data?.news_intelligence || {};
    const newsItems = newsObj.items || newsObj.articles || [];

    return (
      <div id="intraday-assistant-closed" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6 text-left font-mono">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2">
            <Activity size={18} className="text-cyan-400" />
            <h3 className="font-bold text-white text-base">Live Assistant · Closed Session Mode</h3>
          </div>
          <span className="px-2.5 py-1 text-xs font-bold rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
            CLOSED_SESSION_READY
          </span>
        </div>

        {/* 1. LAST SESSION SUMMARY */}
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-white font-bold text-xs">
            <ShieldCheck size={14} className="text-emerald-400" />
            <span>LAST SESSION SUMMARY</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
              <span className="text-[10px] text-slate-400 block">NIFTY Last Close</span>
              <span className="font-bold text-white">{spot > 0 ? formatNumber(spot, 2) : "--"}</span>
            </div>
            <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
              <span className="text-[10px] text-slate-400 block">India VIX Close</span>
              <span className="font-bold text-cyan-400">{vix > 0 ? formatNumber(vix, 2) : "--"}</span>
            </div>
            <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
              <span className="text-[10px] text-slate-400 block">Market Session</span>
              <span className="font-bold text-amber-400">MARKET CLOSED</span>
            </div>
          </div>
        </div>

        {/* 2. DEVELOPMENTS & MACRO/GLOBAL CHANGES */}
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-white font-bold text-xs">
            <Activity size={14} className="text-purple-400" />
            <span>DEVELOPMENTS & MACRO CHANGES SINCE CLOSE</span>
          </div>
          {Object.keys(macroQuotes).length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              {Object.values(macroQuotes).slice(0, 4).map((q: any) => (
                <div key={q.symbol} className="p-2 bg-slate-950 rounded border border-slate-850">
                  <span className="text-[10px] text-slate-400 block font-bold">{q.name || q.symbol}</span>
                  <span className={`font-bold ${safeNumber(q.change_pct, 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {formatNumber(safeNumber(q.price, 0), 2)} ({safeNumber(q.change_pct, 0) >= 0 ? "+" : ""}{formatNumber(safeNumber(q.change_pct, 0), 2)}%)
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 font-sans">No global macro quote updates available since session close.</p>
          )}
        </div>

        {/* 3. NEWS SINCE CLOSE */}
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-white font-bold text-xs">
            <Info size={14} className="text-cyan-400" />
            <span>NEWS INTELLIGENCE SINCE CLOSE</span>
          </div>
          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            {newsItems.length > 0
              ? `${newsItems.length} verified news item(s) ingested since last session. Check News & Updates workspace for full headlines.`
              : "No new verified news items ingested since session close."}
          </p>
        </div>

        {/* 4. NEXT SESSION WATCH ITEMS */}
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-white font-bold text-xs">
            <Info size={14} className="text-amber-400" />
            <span>WHAT TO WATCH NEXT SESSION</span>
          </div>
          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            GIFT Nifty remains unavailable unless a genuine provider is configured. Treat freshness-eligible global observations as context only; intraday VWAP acceptance and live confirmation tracking activate from the Indian market feed.
          </p>
        </div>
      </div>
    );
  }

  const monitor = canonicalState?.unified_intelligence?.live_assistant_monitor || canonicalState?.live_assistant_monitor || {};
  const currentView = monitor.current_market_view || canonicalState?.unified_intelligence?.overall_view || "Mixed Setup";
  const conviction = monitor.conviction || canonicalState?.unified_intelligence?.conviction || "Moderate Conviction";
  const bestBehavior = monitor.best_supported_behavior || canonicalState?.unified_intelligence?.preferred_setup?.description || "Wait for opening range and breadth confirmation.";
  const confirms = monitor.what_confirms_it || safeArray(canonicalState?.unified_intelligence?.supports);
  const weakens = monitor.what_weakens_it || safeArray(canonicalState?.unified_intelligence?.invalidation_conditions);
  const decisionAreas = monitor.decision_areas || safeArray(canonicalState?.unified_intelligence?.decision_zones);
  const whatChangedList = monitor.what_changed || ["Waiting for the next validated intelligence update."];
  const nextWatchList = monitor.next_watch || ["Watch price action around key decision zones."];

  return (
    <div id="intraday-assistant" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6 text-left font-mono">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-cyan-400" />
          <h3 className="font-bold text-white text-base">Live Assistant · Real-Time Market Monitor</h3>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 font-extrabold">{currentView.toUpperCase()}</span>
          <span className="px-2.5 py-0.5 text-xs font-bold rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
            {conviction.toUpperCase()}
          </span>
        </div>
      </div>

      {/* 1. WHAT IS NIFTY DOING NOW */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 font-sans">
        <div className="flex items-center gap-2 text-cyan-300 font-bold text-xs font-mono">
          <Activity size={14} />
          <span>WHAT IS NIFTY DOING NOW?</span>
        </div>
        <p className="text-xs text-slate-200 leading-relaxed">
          {monitor.nifty_action_summary || `NIFTY spot is ${marketContext?.current_spot ? formatNumber(marketContext.current_spot, 2) : "--"}. Market context is ${currentView.toLowerCase()} with ${conviction.toLowerCase()}.`}
        </p>
      </div>
      {/* CANONICAL GLOBAL EVENTS */}
      <div data-assistant-event-clusters className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 font-sans">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-white font-bold text-xs font-mono">
          <Info size={14} className="text-purple-400" />
          <span>CANONICAL GLOBAL EVENTS</span>
        </div>
        {(safeArray(canonicalState?.news_intelligence?.event_clusters) as any[])
          .filter(cluster => ["BREAKING", "RECENT", "ACTIVE_EVENT"].includes(safeString(cluster.recency_state).toUpperCase()))
          .length ? (
            (safeArray(canonicalState?.news_intelligence?.event_clusters) as any[])
              .filter(cluster => ["BREAKING", "RECENT", "ACTIVE_EVENT"].includes(safeString(cluster.recency_state).toUpperCase()))
              .slice(0, 3)
              .map(cluster => (
                <div key={cluster.event_cluster_id} className="text-xs text-slate-300">
                  <span className="font-semibold text-white">WHAT CHANGED:</span> {safeString(cluster.canonical_headline)}{" "}
                  <span className="text-cyan-300">WHAT MATTERS:</span> {safeString(cluster.reasoning)}{" "}
                  <span className="text-amber-300">WHAT TO WATCH:</span> {safeArray(cluster.affected_channels).join(", ") || "stated transmission channels"}.
                </div>
              ))
          ) : (
            <p className="text-xs text-slate-400">No current canonical event cluster meets the active-session recency rule.</p>
          )}
      </div>

      {/* 2 & 3. BEST-SUPPORTED BEHAVIOR TO WATCH */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 font-sans">
        <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs font-mono">
          <ShieldCheck size={14} />
          <span>BEST-SUPPORTED BEHAVIOR TO WATCH</span>
        </div>
        <p className="text-xs text-slate-200 leading-relaxed font-semibold">
          {bestBehavior}
        </p>
      </div>

      {/* 4 & 5. WHAT CONFIRMS IT & WHAT WEAKENS IT */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs font-mono">
            <Info size={14} />
            <span>WHAT CONFIRMS IT</span>
          </div>
          <ul className="text-xs text-slate-300 space-y-1.5 font-sans">
            {confirms.length ? confirms.map((item: any, idx: number) => <li key={idx}>• {safeString(item)}</li>) : <li>• Waiting for quantitative evidence confirmation.</li>}
          </ul>
        </div>
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-xs font-mono">
            <AlertCircle size={14} />
            <span>WHAT WEAKENS / INVALIDATES IT</span>
          </div>
          <ul className="text-xs text-slate-300 space-y-1.5 font-sans">
            {weakens.length ? weakens.map((item: any, idx: number) => <li key={idx}>• {safeString(item)}</li>) : <li>• No explicit invalidation condition triggered.</li>}
          </ul>
        </div>
      </div>

      {/* 6. DECISION AREAS */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <div className="flex items-center gap-2 text-purple-400 font-bold text-xs font-mono">
          <Activity size={14} />
          <span>KEY DECISION ZONES NOW</span>
        </div>
        {decisionAreas.length ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            {decisionAreas.slice(0, 3).map((zone: any, i: number) => (
              <div key={i} className="p-2.5 bg-slate-950 rounded border border-slate-850">
                <span className="text-[10px] text-slate-400 block font-bold">{zone.role || "DECISION ZONE"}</span>
                <span className="font-bold text-cyan-300">{zone.lower ? `${formatNumber(zone.lower, 1)} – ${formatNumber(zone.upper, 1)}` : formatNumber(zone.center || zone.value, 1)}</span>
                <span className="text-[9px] text-slate-500 block mt-0.5">{zone.contributing_count || 2} contributing level(s)</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400 font-sans">Decision zones being calculated from live structure.</p>
        )}
      </div>

      {/* 7. WHAT CHANGED */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
        <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs font-mono">
          <Activity size={14} />
          <span>WHAT CHANGED IN THIS CYCLE</span>
        </div>
        <ul className="text-xs text-slate-300 space-y-1 font-sans">
          {whatChangedList.map((item: any, idx: number) => <li key={idx}>• {safeString(item)}</li>)}
        </ul>
      </div>

      {/* 8. NEXT WATCH */}
      <div className="p-4 bg-amber-950/15 border border-amber-900/50 rounded-xl space-y-2">
        <div className="flex items-center gap-2 text-amber-300 font-bold text-xs font-mono">
          <Info size={14} />
          <span>NEXT WATCH CONDITIONS</span>
        </div>
        <ul className="text-xs text-slate-300 space-y-1 font-sans">
          {nextWatchList.map((item: any, idx: number) => <li key={idx}>• {safeString(item)}</li>)}
        </ul>
      </div>
    </div>
  );
}
