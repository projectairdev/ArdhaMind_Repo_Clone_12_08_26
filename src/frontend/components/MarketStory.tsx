// src/frontend/components/MarketStory.tsx
import React from "react";
import {
  BookOpen,
  TrendingUp,
  TrendingDown,
  Clock,
  Globe,
  Layers,
  Sparkles,
  AlertTriangle,
  HelpCircle
} from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState, useMarketData, useOptionIntelligence, useNewsIntelligence } from "../context/WorkstationStateContext";
import { safeArray, safeString, safeNumber, stripHtml, formatDate, formatNumber } from "../utils/safeHelpers";
import { getTraderMarketStatus } from "../utils/traderTerminology";

export function MarketStory() {
  const { themeClasses, accentClasses, fontClasses, densityClasses } = useTheme();
  const {
    syncing: loading,
    market_session,
    canonicalState
  } = useWorkstationState() as any;
  const { data: mc } = useMarketData();
  const { data: oc } = useOptionIntelligence();
  const { data: news } = useNewsIntelligence();

  const spot = mc?.current_spot || 0;
  const vwap = mc?.vwap || 0;
  const atr = mc?.atr || 0;
  const vixContext: any = canonicalState?.macro_intelligence?.india_vix || mc?.india_vix_context || {};
  const hasVerifiedVix = vixContext.value != null && Boolean(vixContext.observation_timestamp);
  const vix = hasVerifiedVix ? safeNumber(vixContext.value) : null;
  const trend = mc?.trend_direction || "NEUTRAL";
  const regime = mc?.market_regime || "UNKNOWN";
  const trendStrength = mc?.trend_strength || 0;
  const pcr = oc?.pcr || mc?.pcr || 0;
  const atmIv = oc?.atm_iv || 0;
  const expectedMove = oc?.expected_move || 0;
  const feedHealth = mc?.feed_health || "OFFLINE";
  const isClosed = Boolean(market_session?.is_closed || market_session?.status === "closed" || market_session?.status === "holiday" || mc?.session_mode === "LAST_SESSION");
  const sessionStatus = market_session?.status || (isClosed ? "closed" : "open");
  const sessionLabel = getTraderMarketStatus(sessionStatus, market_session?.observed_at);
  const macro = canonicalState?.macro_intelligence || {};
  const macroKeys: string[] = safeArray(macro.workspace_context?.todays_analysis_quote_keys).map(String);
  const macroQuotes: any[] = macroKeys.map(key => macro.quotes?.[key]).filter(Boolean);

  // Active-session narrative consumes canonical event clusters, never repeated headlines.
  const eventClusters = news?.event_clusters || [];
  const overallSentiment = news?.overall_sentiment ?? 0;
  const sentimentBias = news?.sentiment_bias || "NEUTRAL";
  const isPanic = news?.is_news_panic_active ?? false;

  // Construct dynamic intelligence narrative based ONLY on observed parameters
  let dynamicNarrative = "";
  if (isClosed && spot > 0) {
    dynamicNarrative = `NIFTY Last Session Close was ${spot.toFixed(2)}. Market session is currently ${sessionLabel.toUpperCase()}.${vix != null ? ` India VIX was ${vix.toFixed(2)} at the verified observation timestamp.` : " India VIX is unavailable."} Real-time intraday tracking and scenario confirmations will resume on the next trading session.`;
  } else if (spot > 0 && feedHealth === "HEALTHY") {
    dynamicNarrative = `NIFTY Spot Index is trading at ${spot.toFixed(2)}. The price is trading ${
      spot >= vwap ? "above" : "below"
    } the calculated intraday VWAP of ${vwap.toFixed(2)}, indicating a short-term ${
      spot >= vwap ? "bullish" : "bearish"
    } posture.${vix != null ? ` Verified India VIX is ${vix.toFixed(2)}.` : " India VIX is unavailable."} ATR is ${atr.toFixed(2)} points.`;
    if (eventClusters.length > 0) {
      dynamicNarrative += ` ${eventClusters.length} canonical global event cluster(s) remain active; the highest-ranked transmission channels are shown below.`;
    }
    if (macroQuotes.length > 0) {
      dynamicNarrative += ` Cross-market context: ${macroQuotes.slice(0, 5).map(quote => `${safeString(quote.name || quote.symbol)} ${safeNumber(quote.change_pct) >= 0 ? "+" : ""}${formatNumber(quote.change_pct, 2)}% (${safeString(quote.freshness_status)})`).join("; ")}. These observations are contextual and do not establish causality.`;
    }
  } else {
    dynamicNarrative = `TODAY'S ANALYSIS UNAVAILABLE — ${sessionLabel.toUpperCase()}. Market feed is currently offline or session is closed.`;
  }

  return (
    <div id="market-story-workspace" className={`space-y-6 text-left ${fontClasses.base}`}>
      
      {/* Workspace Header */}
      <div className={`flex flex-col md:flex-row md:items-center justify-between border-b ${themeClasses.border} pb-4`}>
        <div>
          <span className={`text-[10px] font-mono uppercase tracking-widest font-black ${accentClasses.text}`}>
            Market Intelligence Narrative
          </span>
          <h2 className="text-2xl font-extrabold tracking-tight mt-1 flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-cyan-400" />
            Today’s Analysis
          </h2>
          <p className={`text-xs ${themeClasses.textMuted} mt-1`}>
            Deconstruct session mechanics, capital rotation flow, and technical sentiment anchors.
          </p>
        </div>
        <div className="flex items-center gap-2 mt-4 md:mt-0">
          <span className={`px-2.5 py-1 text-xs font-mono font-bold rounded ${
            isClosed ? "bg-amber-950/40 text-amber-400 border border-amber-800/30" : (feedHealth === "HEALTHY" ? "bg-emerald-950/40 text-emerald-400 border border-emerald-800/30" : "bg-rose-950/40 text-rose-400 border border-rose-900/30")
          }`}>
            {isClosed ? `Session: ${sessionLabel}` : `Feed: ${feedHealth}`}
          </span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Morning vs Live Market Behavior Comparison */}
        {isClosed ? (
          <div className="lg:col-span-12 p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 font-mono text-xs">
            <div className="flex items-center gap-2 text-amber-400 font-bold">
              <AlertTriangle size={16} />
              <span>TODAY'S ANALYSIS — {sessionLabel.toUpperCase()}</span>
            </div>
            <p className="text-slate-400">
              Intraday scenario confirmations and live VWAP acceptance tracking are disabled while market is {sessionLabel.toLowerCase()}.
            </p>
          </div>
        ) : null}

        {/* Left column - Live Narrative & News Timeline (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* AI Narrative Synthesis */}
          <div className={`${themeClasses.card} border rounded-xl ${densityClasses.padding} space-y-4 relative overflow-hidden`}>
            <div className="absolute top-0 right-0 p-3 opacity-10">
              <Sparkles className="h-16 w-16 text-cyan-400" />
            </div>
            
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan-400" />
              <h3 className="font-mono text-xs font-extrabold uppercase tracking-wider text-white">
                Session Intelligence Synthesis (Observed Data)
              </h3>
            </div>

            <div className="space-y-3">
              <p className="text-sm leading-relaxed text-neutral-300">
                "{dynamicNarrative}"
              </p>
            </div>

            {spot > 0 && feedHealth === "HEALTHY" && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-3 border-t border-neutral-800/60 text-xs font-mono">
                <div className="p-2.5 bg-neutral-900/40 rounded border border-neutral-800/40">
                  <span className="text-neutral-500 block uppercase text-[9px]">Market Regime</span>
                  <span className="font-bold text-white">{regime}</span>
                </div>
                <div className="p-2.5 bg-neutral-900/40 rounded border border-neutral-800/40">
                  <span className="text-neutral-500 block uppercase text-[9px]">Trend Direction</span>
                  <span className={`font-bold ${trend === "BULLISH" ? "text-emerald-400" : trend === "BEARISH" ? "text-rose-400" : "text-neutral-400"}`}>
                    {trend} ({trendStrength.toFixed(1)}%)
                  </span>
                </div>
                <div className="p-2.5 bg-neutral-900/40 rounded border border-neutral-800/40 col-span-2 md:col-span-1">
                  <span className="text-neutral-500 block uppercase text-[9px]">News Sentiment</span>
                  <span className={`font-bold ${sentimentBias === "BULLISH" ? "text-emerald-400" : sentimentBias === "BEARISH" ? "text-rose-400" : "text-neutral-400"}`}>
                    {sentimentBias} ({overallSentiment >= 0 ? "+" : ""}{overallSentiment.toFixed(2)})
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Chronological Visual Timeline */}
          <div className={`${themeClasses.card} border rounded-xl ${densityClasses.padding} space-y-6`}>
            <div className="flex items-center justify-between border-b border-neutral-800/60 pb-3">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-cyan-400" />
                <h3 className="font-bold text-sm text-white">Live Intelligence Timeline</h3>
              </div>
              <span className="text-[10px] font-mono text-neutral-500">Real-Time News Stream</span>
            </div>

            {eventClusters.length > 0 ? (
              <div className="space-y-4">
                {eventClusters.map((art: any, idx: number) => {
                  const headline = stripHtml(art.canonical_headline);
                  const source = safeArray(art.publishers).join(", ") || "UNAVAILABLE";
                  const summary = stripHtml(art.reasoning);
                  const category = stripHtml(art.category || "Regulatory / Macro");
                  const dir = safeString(art.expected_direction || art.direction || "NEUTRAL").toUpperCase();
                  const score = safeNumber(art.nifty_relevance, 0);
                  const importance = safeString(art.impact_level || "LOW").toUpperCase();

                  return (
                    <div key={art.event_cluster_id || idx} data-active-event-cluster={art.event_cluster_id} className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl space-y-3 font-sans">
                      <div className="flex justify-between items-start gap-3">
                        <div>
                          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400 block mb-1">
                            {source} · {category}
                          </span>
                          <h4 className="text-sm font-bold text-white leading-snug">{headline}</h4>
                        </div>
                        <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-extrabold uppercase shrink-0 border ${
                          dir === "BULLISH"
                            ? "bg-emerald-950/60 text-emerald-400 border-emerald-800"
                            : dir === "BEARISH"
                              ? "bg-rose-950/60 text-rose-400 border-rose-800"
                              : "bg-slate-950 text-slate-400 border-slate-800"
                        }`}>
                          Impact: {dir}
                        </span>
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed font-sans">{summary}</p>

                      <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-850 text-[10px] font-mono text-slate-400">
                        <span>Updated: {formatDate(art.last_updated)}</span>
                        <span>•</span>
                        <span className="uppercase">Importance: <strong className="text-white">{importance}</strong></span>
                        <span>•</span>
                        <span className="bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                          Relevance: {formatNumber(score, 1)}/10
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center space-y-3 font-mono">
                <AlertTriangle className="h-8 w-8 text-slate-600 animate-pulse" />
                <div className="space-y-1">
                  <p className="text-xs font-bold text-slate-300">No active canonical event clusters</p>
                  <p className="text-[11px] text-slate-500 max-w-md">
                    Waiting for matching verified economic headlines or market events.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right column - Unconfigured/Disabled integrations (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Economic Calendar events */}
          <div className={`${themeClasses.card} border rounded-xl ${densityClasses.padding} space-y-4`}>
            <div className="flex items-center justify-between border-b border-neutral-850 pb-2">
              <h3 className="text-xs font-bold font-mono text-neutral-300 uppercase flex items-center gap-1.5">
                <Globe className="h-4 w-4 text-purple-400" /> Premium Data Integrations
              </h3>
              <span className="text-[9px] font-mono text-neutral-500">Add-ons</span>
            </div>

            <div className="space-y-3">
              <div className="p-3 bg-neutral-900/40 rounded border border-neutral-800/40 text-xs space-y-2">
                <div className="flex items-center gap-1.5 text-amber-400 font-bold font-mono text-[10px]">
                  <HelpCircle className="h-3.5 w-3.5" /> EXTERNAL FEED REQUIRED
                </div>
                <p className="text-neutral-300 leading-relaxed text-[11px]">
                  <strong>Sector Rotation</strong>, <strong>Institutional Flows (FII/DII)</strong>, 
                  <strong>Global Markets Benchmark</strong>, and <strong>Economic Calendars</strong> are currently inactive.
                </p>
                <p className="text-neutral-500 text-[10px] leading-relaxed">
                  To view real-time data for these widgets, connect an external institutional market feed API (e.g., Bloomberg Enterprise, Reuters, or Moneycontrol Premium) in your workstation settings.
                </p>
              </div>
            </div>
          </div>

          {/* Option intelligence highlights */}
          {spot > 0 && feedHealth === "HEALTHY" && (
            <div className={`${themeClasses.card} border rounded-xl ${densityClasses.padding} space-y-4`}>
              <div className="flex items-center justify-between border-b border-neutral-850 pb-2">
                <h3 className="text-xs font-bold font-mono text-neutral-300 uppercase flex items-center gap-1.5">
                  <Layers className="h-4 w-4 text-cyan-400" /> Option Volatility Bounds
                </h3>
                <span className="text-[9px] font-mono text-neutral-500">Live Limits</span>
              </div>

              <div className="space-y-2 font-mono text-xs">
                <div className="flex justify-between items-center p-2.5 bg-neutral-900/40 rounded border border-neutral-800/50">
                  <span className="text-neutral-400">ATM Strike</span>
                  <span className="font-extrabold text-white">{oc?.atm_strike ? `₹${oc.atm_strike}` : "UNAVAILABLE"}</span>
                </div>
                <div className="flex justify-between items-center p-2.5 bg-neutral-900/40 rounded border border-neutral-800/50">
                  <span className="text-neutral-400">Implied Volatility</span>
                  <span className="font-extrabold text-white">{atmIv > 0 ? `${atmIv.toFixed(2)}%` : "UNAVAILABLE"}</span>
                </div>
                <div className="flex justify-between items-center p-2.5 bg-neutral-900/40 rounded border border-neutral-800/50">
                  <span className="text-neutral-400">Expected Weekly Move</span>
                  <span className="font-extrabold text-cyan-400">{expectedMove > 0 ? `±${expectedMove.toFixed(2)} pts` : "UNAVAILABLE"}</span>
                </div>
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}

function timeString(): string {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

export default MarketStory;
