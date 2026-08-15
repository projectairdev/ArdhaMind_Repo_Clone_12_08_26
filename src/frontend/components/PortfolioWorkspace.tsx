import React from "react";
import { Briefcase, Shield, Clock, LineChart, Lock } from "lucide-react";

export function PortfolioWorkspace() {
  return (
    <div className="space-y-5 font-sans text-left max-w-5xl mx-auto py-4">
      <div className="rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-surface)] p-6 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="rounded-xl bg-slate-900 p-3 text-cyan-400 border border-slate-800">
            <Briefcase size={28} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white tracking-tight">Portfolio & Position Risk Management</h2>
              <span className="rounded bg-cyan-950/80 px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider text-cyan-400 border border-cyan-800">
                PHASE 3 WORKSPACE
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Read-Only Portfolio Intelligence, Risk Exposure & Execution Monitoring
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-[var(--air-line)] bg-[var(--air-surface)] p-5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-white uppercase tracking-wider font-mono">Position Risk Exposure</div>
            <Shield size={16} className="text-slate-500" />
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Real-time portfolio delta, gamma, and concentration risk diagnostics calculated against live market prices.
          </p>
          <div className="pt-2 text-[10px] font-mono text-slate-500 flex items-center gap-1">
            <Lock size={12} /> Scheduled for Phase 3 Release
          </div>
        </div>

        <div className="rounded-xl border border-[var(--air-line)] bg-[var(--air-surface)] p-5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-white uppercase tracking-wider font-mono">Execution Monitoring</div>
            <Clock size={16} className="text-slate-500" />
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Read-only order lifecycle tracking, slippage analysis, and broker status verification.
          </p>
          <div className="pt-2 text-[10px] font-mono text-slate-500 flex items-center gap-1">
            <Lock size={12} /> Scheduled for Phase 3 Release
          </div>
        </div>

        <div className="rounded-xl border border-[var(--air-line)] bg-[var(--air-surface)] p-5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-white uppercase tracking-wider font-mono">Performance Analytics</div>
            <LineChart size={16} className="text-slate-500" />
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Equity curve attribution, trade expectation statistics, and risk-adjusted return metrics.
          </p>
          <div className="pt-2 text-[10px] font-mono text-slate-500 flex items-center gap-1">
            <Lock size={12} /> Scheduled for Phase 3 Release
          </div>
        </div>
      </div>
    </div>
  );
}
