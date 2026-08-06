// src/frontend/components/HistoricalValidation.tsx
import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { ValidationReport } from "../types";
import { AlertCircle, History, BadgePercent, BookOpen } from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";

export function HistoricalValidation() {
  const { validationReport: report, syncBroker } = useWorkstationState();
  const loading = false;
  const error = null;
  const fetchValidation = async () => { await syncBroker(true); };

  if (loading) {
    return (
      <div id="validation-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-44 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div id="validation-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold">Historical Validation Offline</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Could not retrieve historical logs."}</p>
        <button onClick={fetchValidation} className="px-3 py-1 bg-slate-900 text-xs text-slate-300 border border-slate-800 rounded">
          Sync Engine
        </button>
      </div>
    );
  }

  const { summary_stats } = report;
  const outcomeValidations = safeArray(report?.outcome_validations) as any[];
  const dailyValidations = safeArray(report?.daily_validations) as any[];

  return (
    <div id="historical-validation" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <History size={18} className="text-cyan-400" />
          <h3 className="font-bold text-white text-base">Historical Backtest Validation</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500 font-bold uppercase">
          REPORT ID: {safeString(report?.report_id)}
        </span>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
          <span className="text-[10px] font-mono text-slate-500 block uppercase mb-1">Passed Ratio</span>
          <span className="text-lg font-mono font-bold text-emerald-400">
            {formatNumber(summary_stats?.overall_accuracy_pct, 1)}%
          </span>
        </div>

        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
          <span className="text-[10px] font-mono text-slate-500 block uppercase mb-1">Sample Windows Checked</span>
          <span className="text-lg font-mono font-bold text-white">
            {safeNumber(summary_stats?.sample_size_days)} Days
          </span>
        </div>

        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
          <span className="text-[10px] font-mono text-slate-500 block uppercase mb-1">Evaluations Audited</span>
          <span className="text-lg font-mono font-bold text-cyan-400">
            {safeNumber(summary_stats?.total_candidates_evaluated)} Options
          </span>
        </div>

        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
          <span className="text-[10px] font-mono text-slate-500 block uppercase mb-1">Avg Market Score</span>
          <span className="text-lg font-mono font-bold text-cyan-400">
            {formatNumber(summary_stats?.avg_market_score, 1)} / 100
          </span>
        </div>
      </div>

      {/* Multi-Window Outcome Accuracy percentages */}
      <div className="space-y-3">
        <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <BadgePercent size={14} className="text-cyan-400" /> Multi-Window Outcome Accuracy Mapping
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {outcomeValidations.map((out, idx) => (
            <div key={idx} className="p-4 bg-slate-900/20 border border-slate-800 rounded space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400 uppercase">{safeString(out?.evaluation_window)} Window</span>
                <span className="text-emerald-400 font-bold">{formatNumber(out?.accuracy_pct, 1)}% Acc</span>
              </div>
              <div className="h-1.5 w-full bg-slate-950 rounded overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded"
                  style={{ width: `${safeNumber(out?.accuracy_pct)}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>W/L: {safeNumber(out?.success_count)}/{safeNumber(out?.failure_count)}</span>
                <span className="text-emerald-400">P&L: {formatCurrency(out?.total_profit_loss, 0)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Daily Validation audit trail */}
      <div className="space-y-3 pt-2">
        <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <BookOpen size={14} className="text-cyan-400" /> Daily Validation Audit Logs
        </h4>

        <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
          {dailyValidations.map((v, idx) => (
            <div key={idx} className="p-3 bg-slate-900/20 hover:bg-slate-900/40 rounded border border-slate-800 transition text-xs flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div className="space-y-1 text-left">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-white">{safeString(v?.date)}</span>
                  <span className="px-1.5 py-0.5 text-[9px] font-mono bg-slate-800 text-slate-300 rounded border border-slate-700">
                    Score: {formatNumber(v?.market_score, 1)}
                  </span>
                </div>
                <p className="text-slate-400 text-xs">{safeString(v?.outcome_summary)}</p>
              </div>

              <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-mono text-slate-500 sm:w-64">
                <div className="p-1 bg-slate-950 rounded border border-slate-800/60">
                  <span className="text-slate-400 block font-bold">{safeNumber(v?.total_signals)}</span>
                  <span className="text-[7.5px] text-slate-500 uppercase block leading-none mt-0.5">Signals</span>
                </div>
                <div className="p-1 bg-slate-950 rounded border border-slate-800/60">
                  <span className="text-emerald-400 block font-bold">{safeNumber(v?.win_count)}</span>
                  <span className="text-[7.5px] text-slate-500 uppercase block leading-none mt-0.5">Wins</span>
                </div>
                <div className="p-1 bg-slate-950 rounded border border-slate-800/60">
                  <span className="text-rose-400 block font-bold">{safeNumber(v?.loss_count)}</span>
                  <span className="text-[7.5px] text-slate-500 uppercase block leading-none mt-0.5">Losses</span>
                </div>
                <div className="p-1 bg-slate-950 rounded border border-slate-800/60">
                  <span className={`block font-bold ${safeNumber(v?.realized_pnl) >= 0 ? "text-emerald-400" : "text-rose-450"}`}>
                    {formatNumber(v?.realized_pnl, 0)}
                  </span>
                  <span className="text-[7.5px] text-slate-500 uppercase block leading-none mt-0.5">P&L</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}

export default HistoricalValidation;
