// src/frontend/components/PerformanceAnalytics.tsx
import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { AnalyticsReport } from "../types";
import { AlertCircle, LineChart, Award, ThumbsUp } from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";

export function PerformanceAnalytics() {
  const { analyticsReport: report, syncing: loading, error } = useWorkstationState();

  if (loading) {
    return (
      <div id="analytics-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-44 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div id="analytics-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold">Performance Analytics Down</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Analytics metrics are currently offline."}</p>
        <button onClick={() => window.location.reload()} className="px-3 py-1 bg-slate-900 text-xs text-slate-300 border border-slate-800 rounded">
          Reconnect
        </button>
      </div>
    );
  }

  const overall_metrics = report?.overall_metrics;
  const totalTrades = safeNumber(overall_metrics?.total_trades);

  if (totalTrades === 0) {
    return (
      <div id="performance-analytics-empty" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-4">
          <LineChart size={18} className="text-slate-500" />
          <h3 className="font-bold text-white text-base">Performance Analytics Engine</h3>
        </div>
        <div className="flex flex-col items-center justify-center py-12 text-center space-y-3">
          <AlertCircle className="h-8 w-8 text-slate-650" />
          <div className="space-y-1">
            <p className="text-sm font-bold text-slate-300">No trade executions recorded</p>
            <p className="text-xs text-slate-500 max-w-md">
              Performance metrics, win/loss rates, profit factors, and strategy expectancy will populate once you begin executing trades or import a trading journal.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const strategyMetrics = safeArray(report?.strategy_metrics) as any[];
  const strengths = safeArray(report?.summary?.strengths) as string[];
  const weaknesses = safeArray(report?.summary?.weaknesses) as string[];

  return (
    <div id="performance-analytics" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <LineChart size={18} className="text-cyan-400" />
          <h3 className="font-bold text-white text-base">Performance Analytics Engine</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500 font-bold uppercase">
          REPORT ID: {safeString(report?.report_id)}
        </span>
      </div>

      {/* Primary Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Total Trades Audited</span>
          <span className="text-xl font-mono font-bold text-white">{safeNumber(overall_metrics?.total_trades)}</span>
        </div>

        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Win / Loss Rate</span>
          <span className="text-xl font-mono font-bold text-emerald-400">
            {formatNumber(overall_metrics?.win_rate, 1)}% <span className="text-xs text-slate-500 font-medium">({safeNumber(overall_metrics?.winning_trades)}W)</span>
          </span>
        </div>

        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Profit Factor ratio</span>
          <span className="text-xl font-mono font-bold text-cyan-400">
            {formatNumber(overall_metrics?.profit_factor, 2)}
          </span>
        </div>

        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Mathematical Expectancy</span>
          <span className="text-xl font-mono font-bold text-emerald-400">
            +{formatCurrency(overall_metrics?.expectancy, 0)}
          </span>
        </div>
      </div>

      {/* Advanced metrics details */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono text-slate-400">
        <div className="p-3 bg-slate-900/10 border border-slate-800 rounded">
          <span className="text-slate-500 block text-[9px] uppercase">Avg Winning Trade</span>
          <span className="text-emerald-400 font-bold">{formatCurrency(overall_metrics?.average_profit, 0)}</span>
        </div>
        <div className="p-3 bg-slate-900/10 border border-slate-800 rounded">
          <span className="text-slate-500 block text-[9px] uppercase">Avg Losing Trade</span>
          <span className="text-rose-400 font-bold">{formatCurrency(overall_metrics?.average_loss, 0)}</span>
        </div>
        <div className="p-3 bg-slate-900/10 border border-slate-800 rounded">
          <span className="text-slate-500 block text-[9px] uppercase">Largest Winner</span>
          <span className="text-emerald-400 font-bold">{formatCurrency(overall_metrics?.largest_winner, 0)}</span>
        </div>
        <div className="p-3 bg-slate-900/10 border border-slate-800 rounded">
          <span className="text-slate-500 block text-[9px] uppercase">Max Drawdown tag</span>
          <span className="text-rose-400 font-bold">{formatCurrency(overall_metrics?.maximum_drawdown, 0)}</span>
        </div>
      </div>

      {/* Strategy performance breakout list */}
      <div className="space-y-3">
        <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider">
          Strategy specific performance index
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {strategyMetrics.map((s, idx) => (
            <div key={idx} className="p-3.5 bg-slate-900/20 rounded border border-slate-800/80 space-y-2">
              <div className="flex justify-between items-center pb-1 border-b border-slate-800/60">
                <span className="text-xs font-mono font-bold text-white">{safeString(s?.strategy_name)}</span>
                <span className="text-xs font-mono font-bold text-emerald-400">{formatNumber(s?.win_rate, 1)}% Win</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[11px] font-mono text-slate-400">
                <div>
                  <span className="text-slate-500 block text-[9px] uppercase">Trades</span>
                  <span className="text-white">{safeNumber(s?.total_trades)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[9px] uppercase">PF Ratio</span>
                  <span className="text-white">{formatNumber(s?.profit_factor, 2)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[9px] uppercase">Expectancy</span>
                  <span className="text-white">{formatCurrency(s?.expectancy, 0)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Summary insights */}
      <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg space-y-3">
        <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-slate-300 uppercase">
          <ThumbsUp size={14} className="text-cyan-400" />
          <span>Analytics Strengths & Guidance</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-400">
          <div className="space-y-1">
            <span className="font-semibold text-emerald-400 text-[10px] uppercase font-mono">Verified Strengths</span>
            {strengths.map((str, i) => (
              <p key={i} className="leading-relaxed flex items-start gap-1">
                <span>•</span>
                <span>{safeString(str)}</span>
              </p>
            ))}
          </div>
          <div className="space-y-1">
            <span className="font-semibold text-rose-400 text-[10px] uppercase font-mono">Identified Weaknesses</span>
            {weaknesses.map((w, i) => (
              <p key={i} className="leading-relaxed flex items-start gap-1">
                <span>•</span>
                <span>{safeString(w)}</span>
              </p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
export default PerformanceAnalytics;
