import React from "react";
import { useWorkstationState, useMarketData, useOptionIntelligence, useLiveMarketPresentation } from "../context/WorkstationStateContext";
import { MarketContext, OptionContext, DecisionReport } from "../types";
import { AlertCircle, ArrowUpRight, TrendingUp, TrendingDown, Cpu, Landmark, Clock, RefreshCw } from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";

export function ExecutiveSummary() {
  const {
    canonicalState,
    lastValidState,
    syncing: loading,
    error
  } = useWorkstationState();
  // useLiveMarketPresentation: session-gated live price source (OPEN → liveNiftyTick overlay,
  // POST_MARKET/CLOSED → canonical final). Never raw market_data price fields.
  const livePresentation = useLiveMarketPresentation();
  // useMarketData: raw canonical analytical fields (regime, trend, breadth) — NOT for price.
  const { data: market } = useMarketData();
  const { data: option } = useOptionIntelligence();

  const stateObj = canonicalState ?? lastValidState;

  if (loading) {
    return (
      <div id="exec-summary-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4">
        <div className="h-6 w-1/3 bg-slate-800 rounded"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-24 bg-slate-900 rounded"></div>
          <div className="h-24 bg-slate-900 rounded"></div>
          <div className="h-24 bg-slate-900 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !stateObj) {
    return (
      <div id="exec-summary-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3 text-left">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold">Executive Summary Offline</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Telemetry loading error."}</p>
        <button onClick={() => window.location.reload()} className="px-3 py-1 bg-slate-900 text-xs text-slate-300 border border-slate-800 rounded flex items-center gap-1.5 cursor-pointer">
          <RefreshCw size={12} /> Reconnect
        </button>
      </div>
    );
  }

  const decisionSupport = stateObj.decision_support;
  const scenarios = stateObj.trade_scenarios || [];
  const bestCandidate = null;

  const overallAction = (decisionSupport?.blockers?.length > 0 || decisionSupport?.missing_confirmations?.length > 0)
    ? "HOLD"
    : "MONITOR";
  const totalCandidates = scenarios.length;
  const statusMessage = decisionSupport?.market_interpretation || "No status loaded";
  const conclusions = decisionSupport?.warnings || [];

  return (
    <div id="executive-summary" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6 text-left">
      {/* Title */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <Cpu size={18} className="text-cyan-400" />
          <h3 className="font-bold text-white text-base">Terminal Executive Summary</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500 font-bold uppercase">
          REPORT ID: NONE
        </span>
      </div>

      {/* Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Market Spot & Regime */}
        <div className="p-4 bg-slate-900/60 rounded-lg border border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">NIFTY 50 Spot</span>
            {livePresentation.change != null && livePresentation.change >= 0
              ? <TrendingUp size={14} className="text-emerald-400" />
              : <TrendingDown size={14} className="text-rose-400" />}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-mono font-bold text-white">
              {livePresentation.currentSpot != null ? formatCurrency(livePresentation.currentSpot, 2) : "—"}
            </span>
            {livePresentation.changePct != null && (
              <span className={`text-xs font-mono font-medium ${livePresentation.changePct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {livePresentation.changePct >= 0 ? "+" : ""}{formatNumber(livePresentation.changePct, 2)}%
              </span>
            )}
            <span className={`text-[9px] font-mono uppercase ml-1 ${
              livePresentation.source === "LIVE_TICK" ? "text-emerald-500" :
              livePresentation.source === "CANONICAL_FALLBACK" ? "text-amber-500" :
              "text-slate-600"
            }`}>
              {livePresentation.source === "LIVE_TICK" ? "● LIVE" :
               livePresentation.source === "CANONICAL_FALLBACK" ? "⊙ LAST" : "—"}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <span className="px-1.5 py-0.5 text-[10px] font-mono bg-slate-800 text-slate-300 rounded uppercase">
              {safeString(market?.market_regime, "NORMAL")}
            </span>
            <span className="px-1.5 py-0.5 text-[10px] font-mono bg-emerald-950/40 text-emerald-400 rounded uppercase">
              {safeString(market?.trend_direction, "SIDEWAYS")}
            </span>
          </div>
          <div className="border-t border-slate-800/60 pt-2.5 flex items-center justify-between text-[10px] font-mono text-slate-500">
            <span>NSE: 09:15 - 15:30 IST</span>
            <span className={`flex items-center gap-1 ${
              livePresentation.sessionBadge.isOpen ? "text-emerald-400" :
              livePresentation.sessionBadge.isPreMarket ? "text-sky-400" :
              "text-amber-400"
            }`}>
              <span className="h-1.5 w-1.5 rounded-full bg-current"></span>
              {livePresentation.sessionBadge.label}
            </span>
          </div>
        </div>

        {/* Unified Decision Route */}
        <div className="p-4 bg-slate-900/60 rounded-lg border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">System Priority Action</span>
            <Cpu size={14} className="text-cyan-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-white">
              {overallAction}
            </span>
            <span className="text-xs text-cyan-400 font-mono">Run: {totalCandidates} Checked</span>
          </div>
          <p className="text-xs text-slate-400 truncate">{statusMessage}</p>
        </div>

        {/* Top Lot Recommended Candidate */}
        <div className="p-4 bg-slate-900/60 rounded-lg border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Top Selected Contract</span>
            <Landmark size={14} className="text-amber-400" />
          </div>
          {bestCandidate ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono font-semibold text-white">{(bestCandidate as any).tradingsymbol}</span>
                <span className="px-1.5 py-0.5 text-[10px] font-mono bg-emerald-950/40 text-emerald-400 rounded">
                  BUY
                </span>
              </div>
              <div className="flex justify-between text-[11px] font-mono text-slate-400">
                <span>Lots: {safeNumber((bestCandidate as any).allocated_lots)}</span>
                <span>Margin: {formatCurrency((bestCandidate as any).allocated_capital)}</span>
              </div>
            </>
          ) : (
            <span className="text-xs text-slate-500 italic block pt-1">No Active Allocation</span>
          )}
        </div>
      </div>

      {/* Actionable Operators Conclusions Banner */}
      <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg space-y-2">
        <h4 className="text-xs font-mono font-semibold text-slate-300 tracking-wider uppercase">Active Dispatch Protocols</h4>
        <ul className="space-y-1.5">
          {safeArray(conclusions).map((c, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
              <span className="mt-1 flex-shrink-0 h-1.5 w-1.5 rounded-full bg-cyan-400"></span>
              <span>{safeString(c)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default ExecutiveSummary;
