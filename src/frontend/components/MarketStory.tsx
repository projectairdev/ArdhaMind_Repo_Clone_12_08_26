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

export function MarketStory() {
  const { themeClasses, accentClasses, fontClasses, densityClasses } = useTheme();
  const {
    syncing: loading
  } = useWorkstationState();
  const { data: mc } = useMarketData();
  const { data: oc } = useOptionIntelligence();
  const { data: news } = useNewsIntelligence();

  const spot = mc?.current_spot || 0;
  const vwap = mc?.vwap || 0;
  const atr = mc?.atr || 0;
  const vix = mc?.india_vix || 0;
  const trend = mc?.trend_direction || "NEUTRAL";
  const regime = mc?.market_regime || "UNKNOWN";
  const trendStrength = mc?.trend_strength || 0;
  const pcr = oc?.pcr || mc?.pcr || 0;
  const atmIv = oc?.atm_iv || 0;
  const expectedMove = oc?.expected_move || 0;
  const feedHealth = mc?.feed_health || "OFFLINE";

  // Timeline events sourced from news pipeline articles
  const articles = news?.articles || [];
  const overallSentiment = news?.overall_sentiment ?? 0;
  const sentimentBias = news?.sentiment_bias || "NEUTRAL";
  const isPanic = news?.is_news_panic_active ?? false;

  // Construct dynamic intelligence narrative based ONLY on observed parameters
  let dynamicNarrative = "";
  if (spot > 0 && feedHealth === "HEALTHY") {
    dynamicNarrative = `NIFTY Spot Index is trading at ${spot.toFixed(2)}. The price is trading ${
      spot >= vwap ? "above" : "below"
    } the calculated intraday VWAP of ${vwap.toFixed(2)}, indicating a short-term ${
      spot >= vwap ? "bullish" : "bearish"
    } posture. Volatility indicators show India VIX at ${vix.toFixed(2)} (${
      mc?.volatility_state || "NORMAL"
    } state) with an ATR of ${atr.toFixed(2)} points. Option chain structures reveal an ATM strike of ${
      oc?.atm_strike || Math.round(spot / 50.0) * 50.0
    } and an Option PCR of ${pcr.toFixed(2)}, pointing to a ${
      pcr >= 1.15 ? "bullish options bias" : pcr <= 0.85 ? "bearish options bias" : "neutral options balance"
    }. `;

    if (articles.length > 0) {
      dynamicNarrative += `News intelligence sentiment index is currently ${sentimentBias} (${
        overallSentiment >= 0 ? "+" : ""
      }${overallSentiment.toFixed(2)}) based on ${articles.length} active macro news streams. ${
        isPanic
          ? "CRITICAL: Market sentiment panic thresholds have been crossed. Elevated risk parameters active."
          : "Sentiment flows remain within baseline risk parameters."
      }`;
    } else {
      dynamicNarrative += "No matching macro news headlines detected in the current cycle. Technical parameters are directing active sentiment classification.";
    }
  } else {
    dynamicNarrative = "Insufficient live market context available. Please connect broker to establish live data streams.";
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
            feedHealth === "HEALTHY" ? "bg-emerald-950/40 text-emerald-400 border border-emerald-800/30" : "bg-rose-950/40 text-rose-400 border border-rose-900/30"
          }`}>
            Feed: {feedHealth}
          </span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
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

            {articles.length > 0 ? (
              <div className="relative pl-6 border-l border-neutral-800 space-y-8">
                {articles.map((art, idx) => {
                  const isPositive = art.sentiment_score > 0.15;
                  const isNegative = art.sentiment_score < -0.15;
                  return (
                    <div key={idx} className="relative">
                      {/* Timeline Dot icon overlay */}
                      <div className={`absolute -left-[31px] top-1 h-4 w-4 rounded-full border-2 flex items-center justify-center bg-[#0a0a0a] ${
                        isPositive ? "border-emerald-500 text-emerald-500" :
                        isNegative ? "border-rose-500 text-rose-500" : "border-neutral-600 text-neutral-400"
                      }`}>
                        <div className={`h-1.5 w-1.5 rounded-full ${
                          isPositive ? "bg-emerald-500" :
                          isNegative ? "bg-rose-500" : "bg-neutral-600"
                        }`} />
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-xs font-bold text-cyan-400">
                            {art.published_at ? art.published_at.slice(11, 16) : timeString()}
                          </span>
                          <span className="text-[9px] font-mono font-extrabold uppercase px-2 py-0.5 rounded bg-neutral-900 border border-neutral-800 text-neutral-400">
                            {art.source}
                          </span>
                          <span className={`text-[9px] font-bold ${
                            isPositive ? "text-emerald-400" : isNegative ? "text-rose-400" : "text-neutral-400"
                          }`}>
                            {art.severity} SEVERITY | SENTIMENT: {art.sentiment_score.toFixed(2)}
                          </span>
                        </div>
                        <h4 className="text-xs font-bold text-white mt-1">{art.headline}</h4>
                        <p className="text-xs text-neutral-400 leading-relaxed">{art.summary}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center space-y-3">
                <AlertTriangle className="h-8 w-8 text-neutral-600 animate-pulse" />
                <div className="space-y-1">
                  <p className="text-sm font-bold text-neutral-300">No live news streams active</p>
                  <p className="text-xs text-neutral-500 max-w-md">
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
                  <span className="font-extrabold text-white">₹{oc?.atm_strike || Math.round(spot / 50.0) * 50.0}</span>
                </div>
                <div className="flex justify-between items-center p-2.5 bg-neutral-900/40 rounded border border-neutral-800/50">
                  <span className="text-neutral-400">Implied Volatility</span>
                  <span className="font-extrabold text-white">{atmIv.toFixed(2)}%</span>
                </div>
                <div className="flex justify-between items-center p-2.5 bg-neutral-900/40 rounded border border-neutral-800/50">
                  <span className="text-neutral-400">Expected Weekly Move</span>
                  <span className="font-extrabold text-cyan-400">±{expectedMove.toFixed(2)} pts</span>
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
