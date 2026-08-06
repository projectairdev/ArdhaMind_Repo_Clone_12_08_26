// src/frontend/components/IntradayAssistant.tsx
import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { IntradayReport } from "../types";
import { AlertCircle, Activity, ShieldCheck, Info, AlertTriangle } from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber
} from "../utils/safeHelpers";

export function IntradayAssistant() {
  const { intradayReport: report, syncBroker } = useWorkstationState();
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

  // Safe checks and derived data from the actual IntradayReport schema
  const planStatus = safeString(report.summary?.plan_status, "PLAN_ACTIVE");
  const isPlanValid = planStatus.toLowerCase().includes("valid") ?? true;
  
  const marketChanges = safeArray(report.market_changes) as any[];
  // Find PCR change details if present in market_changes
  const pcrChange = marketChanges.find((m) =>
    safeString(m?.metric_name).toLowerCase().includes("pcr")
  );
  
  const overallPcrShift = safeNumber(report.summary?.overall_pcr_shift);
  const overallVixShift = safeNumber(report.summary?.overall_vix_shift);
  const significantChangesCount = safeNumber(report.summary?.significant_market_changes_count);
  const candidateChanges = safeArray(report.candidate_changes) as any[];
  const validationReasons = safeArray(report.validation_reasons) as any[];

  return (
    <div id="intraday-assistant" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6 text-left">
      {/* Title */}
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

      {/* Intraday shifts gauges */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* PUT-CALL RATIO GAUGE */}
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono text-slate-500 block uppercase">Put-Call Ratio (PCR) Shift</span>
          <div className="text-lg font-mono font-bold text-white">
            {pcrChange ? safeString(pcrChange.current_value) : "1.15"}
          </div>
          <p className="text-xs text-slate-400">
            Intraday Shift: {overallPcrShift >= 0 ? "+" : ""}{formatNumber(overallPcrShift, 2)}
            {pcrChange?.change_pct !== undefined ? ` (${safeNumber(pcrChange.change_pct) >= 0 ? "+" : ""}${formatNumber(pcrChange.change_pct, 1)}%)` : ""}
          </p>
        </div>

        {/* INDIA VIX GAUGE */}
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono text-slate-500 block uppercase">India VIX shift</span>
          <div className="text-lg font-mono font-bold text-white">
            {formatNumber(overallVixShift * 100, 1)}%
          </div>
          <p className="text-xs text-slate-400">
            Bias: {overallVixShift <= 0 ? "Cooling Volatility" : "Rising Volatility"}
          </p>
        </div>

        {/* ACTIVE TRIGGERS STATUS */}
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono text-slate-500 block uppercase">Significant Market Changes</span>
          <div className="text-lg font-mono font-bold text-cyan-400">
            {significantChangesCount} Flagged
          </div>
          <p className="text-xs text-slate-400">
            Out of {safeNumber(report.summary?.total_candidates_monitored)} active candidates
          </p>
        </div>
      </div>

      {/* Live Option Candidates status trackers */}
      <div className="space-y-3">
        <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider">
          Live Option Candidates Intraday Tracker
        </h4>

        <div className="overflow-x-auto rounded border border-slate-800 bg-slate-900/10">
          <table className="w-full text-left border-collapse min-w-[600px]">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900 text-[10px] font-mono text-slate-500 uppercase">
                <th className="px-4 py-2">Candidate ID</th>
                <th className="px-4 py-2">Trading Symbol</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Previous Decision</th>
                <th className="px-4 py-2">Suggested Action</th>
                <th className="px-4 py-2">Reasoning & Alignment</th>
              </tr>
            </thead>
            <tbody className="text-xs font-mono text-slate-300">
              {candidateChanges.map((cand, idx) => {
                const suggestedDecision = safeString(cand?.suggested_decision);
                const isProceed = suggestedDecision === "BUY" || suggestedDecision === "PROCEED";
                const statusStr = safeString(cand?.status);
                return (
                  <tr key={idx} className="border-b border-slate-800 hover:bg-slate-900/20">
                    <td className="px-4 py-3 text-slate-500 text-xs">{safeString(cand?.candidate_id)}</td>
                    <td className="px-4 py-3 text-cyan-400 font-semibold">{safeString(cand?.tradingsymbol)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        statusStr === "UNCHANGED" 
                          ? "bg-slate-800 text-slate-300 border border-slate-700"
                          : "bg-amber-950/40 text-amber-400 border border-amber-900"
                      }`}>
                        {statusStr}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400">{safeString(cand?.previous_decision)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded border ${
                        isProceed
                          ? "bg-emerald-950/40 text-emerald-400 border-emerald-900"
                          : "bg-rose-950/40 text-rose-400 border-rose-900"
                      }`}>
                        {suggestedDecision}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-300 font-sans max-w-xs truncate" title={safeString(cand?.explanation)}>
                      {safeString(cand?.explanation)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Market changes detailed ledger */}
      {marketChanges.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider">
            Intraday Metric Feed Ledger
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {marketChanges.map((metric, idx) => (
              <div key={idx} className="p-4 bg-slate-900/20 border border-slate-800/80 rounded-lg flex items-start gap-3">
                <div className={`p-1.5 rounded mt-0.5 ${
                  metric?.is_significant ? "bg-amber-950/60 text-amber-400" : "bg-slate-800 text-slate-400"
                }`}>
                  {metric?.is_significant ? <AlertTriangle size={15} /> : <Info size={15} />}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-white">{safeString(metric?.metric_name)}</span>
                    {metric?.is_significant && (
                      <span className="text-[8px] font-mono font-bold text-amber-400 px-1 py-0.5 bg-amber-950 rounded">SIGNIFICANT</span>
                    )}
                  </div>
                  <div className="text-[11px] font-mono text-slate-400">
                    Prev: <span className="text-slate-300">{safeString(metric?.previous_value)}</span> • Curr: <span className="text-cyan-300 font-bold">{safeString(metric?.current_value)}</span>
                    {metric?.change_pct !== undefined && (
                      <span className={`ml-2 font-bold ${safeNumber(metric.change_pct) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        ({safeNumber(metric.change_pct) >= 0 ? "+" : ""}{formatNumber(metric.change_pct, 2)}%)
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-300 font-sans leading-relaxed pt-0.5">{safeString(metric?.message)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Reasons & Strategic Safeguards */}
      {validationReasons.length > 0 && (
        <div className="space-y-2.5 pt-2">
          <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-slate-400 uppercase">
            <ShieldCheck size={14} className="text-cyan-400" />
            <span>Plan Validation Reasons & Safeguards</span>
          </div>
          <div className="space-y-2">
            {validationReasons.map((reason, idx) => (
              <div key={idx} className="p-3 bg-slate-900/20 border border-slate-800 rounded text-xs text-slate-300 flex items-start gap-2.5 leading-relaxed">
                <span className="mt-1.5 h-1.5 w-1.5 bg-emerald-400 rounded-full flex-shrink-0 animate-pulse" />
                <p>{safeString(reason)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default IntradayAssistant;
