// src/frontend/components/TomorrowWorkspace.tsx
import React from "react";
import {
  Calendar,
  Compass,
  AlertCircle,
  Target,
  Layers,
  AlertTriangle
} from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";

export function TomorrowWorkspace() {
  const { themeClasses, accentClasses, fontClasses } = useTheme();
  const { eveningReport: report, loading, error, syncBroker } = useWorkstationState();

  if (loading && !report) {
    return (
      <div id="tomorrow-loading" className="space-y-6 animate-pulse p-2 text-left">
        <div className="h-20 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-64 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
          <div className="h-64 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div id="tomorrow-error" className="p-8 bg-neutral-950 border border-rose-900 rounded-xl text-center space-y-4 max-w-xl mx-auto my-12">
        <AlertCircle size={40} className="text-rose-500 mx-auto" />
        <h3 className="text-base font-bold text-white">Evening Outlook Cache Offline</h3>
        <p className="text-xs text-neutral-400">{error || "Could not retrieve tomorrow's pre-market layout."}</p>
        <button onClick={() => syncBroker(true)} className="px-4 py-2 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 text-xs font-mono rounded text-white transition">
          Retry Preparation Sync
        </button>
      </div>
    );
  }

  // Derive tomorrow planning variables
  const directionalBias = safeString(report?.tomorrow_outlook?.directional_bias, "NEUTRAL");
  const isBullish = directionalBias === "BULLISH";
  const spotPrice = report?.market_summary?.spot_price ?? null;

  // Production Integrity: Expected range MUST come from backend (ATR or IV-based).
  // NEVER use hardcoded ±180. Display — if unavailable.
  const expectedRange = report?.tomorrow_outlook?.expected_trading_range ?? null;
  const expectedRangeMin: number | null = expectedRange?.min_limit ?? null;
  const expectedRangeMax: number | null = expectedRange?.max_limit ?? null;

  const supportLevels = safeArray(report?.tomorrow_outlook?.key_support_levels);
  const resistanceLevels = safeArray(report?.tomorrow_outlook?.key_resistance_levels);
  const optimizationNotes = safeArray(report?.optimization_notes);
  const warningsList = safeArray(report?.risk_watchlist?.warnings);

  return (
    <div id="tomorrow-preparation-terminal" className={`space-y-6 text-left ${fontClasses.base}`}>
      
      {/* ── WORKSPACE TITLE AREA ── */}
      <div className={`flex flex-col md:flex-row md:items-center justify-between border-b ${themeClasses.border} pb-4 gap-4`}>
        <div>
          <span className={`text-[10px] font-mono uppercase tracking-widest font-extrabold ${accentClasses.text}`}>
            Preparation Workspace
          </span>
          <h2 className="text-xl sm:text-2xl font-black tracking-tight mt-1 flex items-center gap-2">
            <Calendar className="h-5.5 w-5.5 text-cyan-400" />
            Tomorrow's Outlook & Evening Planner
          </h2>
          <p className={`text-xs ${themeClasses.textMuted} mt-0.5`}>
            Construct tactical bias, configure watchlist parameters, and establish tomorrow's risk limits.
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider font-extrabold">Directional Bias:</span>
          <span className={`px-2.5 py-1 text-xs font-mono font-extrabold rounded flex items-center gap-1.5 ${
            isBullish 
              ? "bg-emerald-950/50 text-emerald-400 border border-emerald-800/40" 
              : "bg-rose-950/50 text-rose-400 border border-rose-800/40"
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${isBullish ? "bg-emerald-400 animate-pulse" : "bg-rose-400 animate-pulse"}`}></span>
            {directionalBias}
          </span>
        </div>
      </div>

      {/* ── MAIN BENTO GRID ARCHITECTURE ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT COLUMN: Tomorrow Overview, Levels, and Watchlists */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* CARD 1: TOMORROW OVERVIEW */}
          <div className={`${themeClasses.card} border rounded-xl p-5 space-y-4 relative overflow-hidden`}>
            <div className="absolute top-0 right-0 h-32 w-32 bg-cyan-500/2 rounded-full blur-3xl"></div>
            <div className="flex items-center gap-2 border-b border-neutral-900 pb-2">
              <Compass className="h-4 w-4 text-cyan-400" />
              <h3 className="font-mono text-xs font-extrabold uppercase tracking-wider text-neutral-200">
                Tomorrow Overview
              </h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
              {/* Bias Stat */}
              <div className="bg-neutral-900/40 border border-neutral-850/60 p-3.5 rounded-lg">
                <span className="text-[9px] font-mono text-neutral-500 uppercase tracking-widest block font-bold">Directional Bias</span>
                <span className={`text-base font-black font-sans block mt-1 ${isBullish ? "text-emerald-400" : "text-rose-400"}`}>
                  {directionalBias}
                </span>
              </div>
              
              {/* Strategy Stat */}
              <div className="bg-neutral-900/40 border border-neutral-850/60 p-3.5 rounded-lg">
                <span className="text-[9px] font-mono text-neutral-500 uppercase tracking-widest block font-bold">Recommended Strategy</span>
                <span className="text-base font-black text-white block mt-1 uppercase truncate">
                  {safeString(report?.summary?.best_strategy, "N/A")}
                </span>
              </div>

              {/* Confidence Stat */}
              <div className="bg-neutral-900/40 border border-neutral-850/60 p-3.5 rounded-lg">
                <span className="text-[9px] font-mono text-neutral-500 uppercase tracking-widest block font-bold">Confidence Index</span>
                <span className="text-base font-black text-cyan-400 font-mono block mt-1">
                  {formatNumber(report?.tomorrow_outlook?.opportunity_strength, 1)}%
                </span>
              </div>

              {/* Volatility Stat */}
              <div className="bg-neutral-900/40 border border-neutral-850/60 p-3.5 rounded-lg">
                <span className="text-[9px] font-mono text-neutral-500 uppercase tracking-widest block font-bold">Expected Volatility</span>
                <span className="text-base font-black text-amber-400 font-mono block mt-1">
                  {formatNumber(report?.market_summary?.vix_price, 2)} <span className="text-[10px] text-neutral-500 font-normal">VIX</span>
                </span>
              </div>
            </div>
          </div>

          {/* CARD 2: KEY MARKET LEVELS */}
          <div className={`${themeClasses.card} border rounded-xl p-5 space-y-4`}>
            <div className="flex items-center gap-2 border-b border-neutral-900 pb-2">
              <Target className="h-4 w-4 text-emerald-400" />
              <h3 className="font-mono text-xs font-extrabold uppercase tracking-wider text-neutral-200">
                Key Market Levels
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Support Levels */}
              <div className="bg-neutral-900/30 border border-neutral-850 p-4 rounded-lg space-y-2.5">
                <div className="flex items-center gap-2 border-b border-neutral-850 pb-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span className="text-[10px] font-mono font-bold text-neutral-400 uppercase tracking-wider">
                    Key Support Levels (Buy Floor)
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1 font-mono">
                  {supportLevels.length === 0 ? (
                    <span className="text-xs text-neutral-500 italic">No support levels reported</span>
                  ) : (
                    supportLevels.map((lvl, idx) => (
                      <span key={idx} className="px-2.5 py-1 bg-neutral-950 border border-neutral-800 text-emerald-400 font-extrabold rounded text-xs">
                        {formatNumber(lvl)}
                      </span>
                    ))
                  )}
                </div>
                <p className="text-[10px] text-neutral-500 italic">
                  Index holding above these zones preserves overall structural bullish bias.
                </p>
              </div>

              {/* Resistance Levels */}
              <div className="bg-neutral-900/30 border border-neutral-850 p-4 rounded-lg space-y-2.5">
                <div className="flex items-center gap-2 border-b border-neutral-850 pb-1.5">
                  <span className="h-2 w-2 rounded-full bg-rose-400 animate-pulse"></span>
                  <span className="text-[10px] font-mono font-bold text-neutral-400 uppercase tracking-wider">
                    Key Resistance Levels (Sell Ceiling)
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1 font-mono">
                  {resistanceLevels.length === 0 ? (
                    <span className="text-xs text-neutral-500 italic">No resistance levels reported</span>
                  ) : (
                    resistanceLevels.map((lvl, idx) => (
                      <span key={idx} className="px-2.5 py-1 bg-neutral-950 border border-neutral-800 text-rose-400 font-extrabold rounded text-xs">
                        {formatNumber(lvl)}
                      </span>
                    ))
                  )}
                </div>
                <p className="text-[10px] text-neutral-500 italic">
                  Aggressive call writing clusters located at these levels. Expect selling pressure on first touch.
                </p>
              </div>

            </div>

            {/* Gap Expectations & Expected Range */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="bg-neutral-900/40 border border-neutral-850 p-3.5 rounded-lg flex items-center justify-between text-xs">
                <div className="text-left">
                  <span className="text-[9px] font-mono text-neutral-500 uppercase block font-bold">Gift Nifty Gap Expectations</span>
                  {/* Production Integrity: Gift Nifty requires an overnight pre-market feed.
                      This pipeline does not have that feed. Display — per Rule 1. */}
                  <span className="text-xs font-black text-neutral-500 mt-1 block font-mono">—</span>
                  <span className="text-[9px] text-neutral-600 font-mono">Pre-market feed required</span>
                </div>
              </div>
              <div className="bg-neutral-900/40 border border-neutral-850 p-3.5 rounded-lg flex items-center justify-between text-xs">
                <div className="text-left">
                  <span className="text-[9px] font-mono text-neutral-500 uppercase block font-bold">Expected Mathematical Range</span>
                  <span className="text-xs font-black text-cyan-400 font-mono mt-1 block">
                    {expectedRangeMin !== null && expectedRangeMax !== null
                      ? `${formatCurrency(expectedRangeMin, 0)} — ${formatCurrency(expectedRangeMax, 0)}`
                      : <span className="text-neutral-500">—</span>
                    }
                  </span>
                  {expectedRangeMin === null && (
                    <span className="text-[9px] text-neutral-600 font-mono">Derived from ATR/IV once feed is live</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Outlook details & Checklist */}
        <div className="lg:col-span-4 space-y-6">
          <div className={`${themeClasses.card} border rounded-xl p-5 space-y-5`}>
            <div className="flex items-center gap-2 border-b border-neutral-900 pb-2">
              <Layers className="h-4 w-4 text-cyan-400" />
              <h3 className="font-mono text-xs font-extrabold uppercase tracking-wider text-neutral-200">
                Planning Details
              </h3>
            </div>

            {/* Outlook */}
            <div className="space-y-1 text-left">
              <span className="text-[9px] font-mono font-extrabold text-cyan-400 uppercase tracking-widest block">
                Tomorrow Outlook Summary
              </span>
              <p className="text-xs text-neutral-300 leading-relaxed bg-cyan-950/5 border border-cyan-900/10 p-3 rounded-lg font-mono">
                {safeString(report?.tomorrow_outlook?.description, "No outlook description loaded.")}
              </p>
            </div>

            {/* Recommended Preparation */}
            <div className="space-y-1.5 text-left">
              <span className="text-[9px] font-mono font-extrabold text-neutral-400 uppercase tracking-widest block">
                Recommended Preparation Guidelines
              </span>
              <ul className="space-y-2 text-[11px] text-neutral-300 list-none pl-1 leading-normal">
                {optimizationNotes.length > 0 ? (
                  optimizationNotes.map((note, idx) => (
                    <li key={idx} className="flex gap-1.5 items-start">
                      <span className="text-cyan-400 font-black">•</span>
                      <span>{safeString(note)}</span>
                    </li>
                  ))
                ) : (
                  <li className="flex gap-1.5 items-start">
                    <span className="text-cyan-400 font-black">•</span>
                    <span>Configure strict pre-trade ATR parameters prior to open.</span>
                  </li>
                )}
              </ul>
            </div>

            {/* Important Risks */}
            <div className="space-y-2 border-t border-neutral-900 pt-3">
              <span className="text-[9px] font-mono font-extrabold text-amber-500 uppercase tracking-widest block">
                Important Execution Risks
              </span>
              
              {warningsList.length > 0 ? (
                warningsList.map((warn, idx) => (
                  <div key={idx} className="p-3 bg-amber-950/15 border border-amber-900/30 rounded text-xs text-amber-300 leading-normal text-left flex gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5 animate-pulse" />
                    <span className="font-mono">{safeString(warn)}</span>
                  </div>
                ))
              ) : (
                <div className="p-2 bg-neutral-900 border border-neutral-850 rounded text-center text-xs text-neutral-500 font-mono">
                  No critical risks flagged for tomorrow.
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}

export default TomorrowWorkspace;
