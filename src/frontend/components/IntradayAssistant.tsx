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

  if (error || !report) {
    return (
      <div id="intraday-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold">Intraday Assistant Offline</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Could not retrieve real-time alerts."}</p>
        <button onClick={fetchIntraday} className="px-3 py-1 bg-slate-900 text-xs text-slate-300 border border-slate-800 rounded">
          Sync Assistant
        </button>
      </div>
    );
  }

  const planStatus = safeString(report?.summary?.plan_status, "UNAVAILABLE");
  const isPlanValid = planStatus.toLowerCase().includes("valid") ?? true;
  const overallPcrShift = safeNumber(report?.summary?.overall_pcr_shift);
  const overallVixShift = safeNumber(report?.summary?.overall_vix_shift);
  const significantChangesCount = safeNumber(report?.summary?.significant_market_changes_count);
  const activeEventClusters = (safeArray(canonicalState?.news_intelligence?.event_clusters) as any[])
    .filter(cluster => ["BREAKING", "RECENT", "ACTIVE_EVENT"].includes(safeString(cluster.recency_state).toUpperCase()))
    .slice(0, 3);
  const upcomingEconomicEvent = (safeArray(canonicalState?.macro_intelligence?.economic_events) as any[])
    .filter(event => ["UPCOMING", "DUE", "SCHEDULED"].includes(safeString(event.status)) && new Date(event.scheduled_at).getTime() >= Date.now() && ["HIGH", "CRITICAL"].includes(safeString(event.impact_level).toUpperCase()))
    .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())[0];

  return (
    <div id="intraday-assistant" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6 text-left">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-cyan-400" />
          <h3 className="font-bold text-white text-base">Intraday Assistant Live Alerts</h3>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-500">Plan Validity State:</span>
          <span className={`px-2 py-0.5 text-xs font-mono font-bold rounded border ${
            isPlanValid
              ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/50"
              : "bg-rose-950/40 text-rose-400 border-rose-800/50"
          }`}>
            {planStatus.toUpperCase()}
          </span>
        </div>
      </div>

      <div data-assistant-event-clusters className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-white font-bold text-xs font-mono"><Info size={14} className="text-purple-400"/><span>CANONICAL GLOBAL EVENTS</span></div>
        {activeEventClusters.length ? activeEventClusters.map(cluster => <div key={cluster.event_cluster_id} className="text-xs text-slate-300"><span className="font-semibold text-white">WHAT CHANGED:</span> {safeString(cluster.canonical_headline)} <span className="text-cyan-300">WHAT MATTERS:</span> {safeString(cluster.reasoning)} <span className="text-amber-300">WHAT TO WATCH:</span> {safeArray(cluster.affected_channels).join(", ") || "stated transmission channels"}.</div>) : <p className="text-xs text-slate-400">No current canonical event cluster meets the active-session recency rule.</p>}
      </div>

      <div data-assistant-economic-risk className="p-4 bg-amber-950/15 border border-amber-900/50 rounded-xl text-xs text-slate-300">
        <span className="font-bold text-amber-300">WHAT TO WATCH NEXT: </span>
        {upcomingEconomicEvent ? `${safeString(upcomingEconomicEvent.event_name)} scheduled ${new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "short" }).format(new Date(upcomingEconomicEvent.scheduled_at))} IST — ${safeString(upcomingEconomicEvent.session_timing).replace("_", " ").toLowerCase()}. Channels: ${safeArray(upcomingEconomicEvent.affected_channels).join(", ") || "UNAVAILABLE"}.` : "No upcoming HIGH/CRITICAL canonical economic event is currently in scope."}
      </div>

      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-white font-bold text-xs font-mono">
          <Activity size={14} className="text-cyan-400" />
          <span>WHAT CHANGED IN THIS CYCLE</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
          <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
            <span className="text-[10px] text-slate-400 block">PCR Shift</span>
            <span className="font-bold text-emerald-400">{overallPcrShift >= 0 ? "+" : ""}{formatNumber(overallPcrShift, 2)}</span>
          </div>
          <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
            <span className="text-[10px] text-slate-400 block">VIX Shift</span>
            <span className="font-bold text-cyan-400">{formatNumber(overallVixShift * 100, 1)}%</span>
          </div>
          <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
            <span className="text-[10px] text-slate-400 block">Significant Changes</span>
            <span className="font-bold text-amber-400">{significantChangesCount} Observed</span>
          </div>
        </div>
      </div>
    </div>
  );
}
