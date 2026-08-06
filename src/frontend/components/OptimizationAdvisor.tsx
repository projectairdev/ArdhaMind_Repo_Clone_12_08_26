// src/frontend/components/OptimizationAdvisor.tsx
import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { OptimizationReport } from "../types";
import { AlertCircle, Sliders, ThumbsUp, ArrowRight } from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";

export function OptimizationAdvisor() {
  const { optimizationReport: report, syncBroker } = useWorkstationState();
  const loading = false;
  const error = null;
  const fetchOptimization = async () => { await syncBroker(true); };

  if (loading) {
    return (
      <div id="optimization-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-44 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div id="optimization-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold">Optimization Advisor Offline</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Could not retrieve optimization suggestions."}</p>
        <button onClick={fetchOptimization} className="px-3 py-1 bg-slate-900 text-xs text-slate-300 border border-slate-800 rounded">
          Sync Engine
        </button>
      </div>
    );
  }

  const recommendations = safeArray(report?.recommendations) as any[];
  const strategyOptimizations = safeArray(report?.strategy_optimizations) as any[];
  const thresholdRecommendations = safeArray(report?.threshold_recommendations) as any[];

  return (
    <div id="optimization-advisor" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <Sliders size={18} className="text-cyan-400" />
          <h3 className="font-bold text-white text-base">Performance Optimization Advisor</h3>
        </div>
        <div className="text-right">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Active Optimizations</span>
          <span className="text-lg font-mono font-bold text-cyan-400">
            {safeNumber(report?.summary?.total_recommendations)} Recommendations
          </span>
        </div>
      </div>

      {/* Snapshot summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-900/10 p-4 rounded-lg border border-slate-800">
        <div>
          <span className="text-[10px] font-mono text-slate-500 block uppercase">Critical Adjustments</span>
          <span className="text-base font-mono font-bold text-rose-400">{safeNumber(report?.summary?.critical_adjustments)} Pending</span>
        </div>
        <div>
          <span className="text-[10px] font-mono text-slate-500 block uppercase">Expected Profit Factor Boost</span>
          <span className="text-base font-mono font-bold text-emerald-400">+{formatCurrency(report?.summary?.potential_pnl_improvement, 0)}</span>
        </div>
        <div>
          <span className="text-[10px] font-mono text-slate-500 block uppercase">Average Recommendation Confidence</span>
          <span className="text-base font-mono font-bold text-cyan-400">{safeNumber(report?.summary?.recommendation_confidence_avg)}%</span>
        </div>
      </div>

      {/* Recommendations details card lists */}
      <div className="space-y-4">
        <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Sliders size={14} className="text-cyan-400" /> Active System recommendations
        </h4>

        <div className="space-y-4">
          {recommendations.map((rec, idx) => (
            <div key={idx} className="p-4 bg-slate-900/20 border border-slate-800 rounded-lg space-y-3 text-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-850 px-1.5 py-0.5 rounded font-bold">
                    {safeString(rec?.category)}
                  </span>
                  <h5 className="font-semibold text-white text-xs">{safeString(rec?.title)}</h5>
                </div>
                <div className="flex items-center gap-1.5 text-xs font-mono text-slate-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  <span>Current: {safeString(rec?.current_value)}</span>
                  <ArrowRight size={12} className="text-cyan-400" />
                  <span className="text-emerald-400 font-bold">Rec: {safeString(rec?.recommended_value)}</span>
                </div>
              </div>

              <p className="text-slate-400 leading-relaxed text-xs">{safeString(rec?.description)}</p>

              {/* Evidence sub card details */}
              <div className="p-3 bg-slate-950/40 rounded border border-slate-800/80 text-[11px] font-mono text-slate-400 space-y-1.5">
                <div className="font-bold text-slate-300 uppercase text-[9px] flex items-center gap-1">
                  <ThumbsUp size={11} className="text-cyan-400" /> Empirical Backtest Evidence
                </div>
                <p>Rationale: {safeString(rec?.rationale)}</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 pt-1 border-t border-slate-900 text-slate-500">
                  <span>Sample size: {safeNumber(rec?.evidence?.historical_sample_size)} days</span>
                  <span>Affected: {safeArray(rec?.evidence?.affected_strategies).map((s) => safeString(s)).join(", ")}</span>
                  <span>Confidence: {safeNumber(rec?.evidence?.confidence_score)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Threshold and weight tables grids */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
        {/* Strategy weight recommendations */}
        <div className="space-y-2">
          <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase">Strategy Adjustments</h4>
          <div className="overflow-hidden rounded border border-slate-800 bg-slate-900/10">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900 text-[10px] font-mono text-slate-500 uppercase">
                  <th className="px-3 py-1.5">Strategy</th>
                  <th className="px-3 py-1.5">Accuracy</th>
                  <th className="px-3 py-1.5">Rec Action</th>
                </tr>
              </thead>
              <tbody className="text-[11px] font-mono text-slate-300">
                {strategyOptimizations.map((so, i) => (
                  <tr key={i} className="border-b border-slate-800 hover:bg-slate-900/20">
                    <td className="px-3 py-2 text-white font-semibold">{safeString(so?.strategy_name)}</td>
                    <td className="px-3 py-2 text-slate-400">{safeNumber(so?.current_accuracy)}%</td>
                    <td className="px-3 py-2">
                      <span className="px-1.5 py-0.5 bg-rose-950/40 text-rose-400 border border-rose-900/50 rounded">
                        {safeString(so?.recommended_action)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Threshold limits recommendations */}
        <div className="space-y-2">
          <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase">Threshold Parameters</h4>
          <div className="overflow-hidden rounded border border-slate-800 bg-slate-900/10">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900 text-[10px] font-mono text-slate-500 uppercase">
                  <th className="px-3 py-1.5">Parameter</th>
                  <th className="px-3 py-1.5">Current</th>
                  <th className="px-3 py-1.5">Rec</th>
                  <th className="px-3 py-1.5">Direction</th>
                </tr>
              </thead>
              <tbody className="text-[11px] font-mono text-slate-300">
                {thresholdRecommendations.map((tr, i) => (
                  <tr key={i} className="border-b border-slate-800 hover:bg-slate-900/20">
                    <td className="px-3 py-2 text-white font-semibold">{safeString(tr?.parameter_name)}</td>
                    <td className="px-3 py-2 text-slate-400">{safeString(tr?.current_value)}</td>
                    <td className="px-3 py-2 text-emerald-400 font-bold">{safeString(tr?.suggested_value)}</td>
                    <td className="px-3 py-2 text-cyan-400 font-bold">{safeString(tr?.direction)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OptimizationAdvisor;
