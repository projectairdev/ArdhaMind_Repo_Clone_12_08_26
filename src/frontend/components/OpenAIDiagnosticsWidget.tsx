// src/frontend/components/OpenAIDiagnosticsWidget.tsx
import React, { useEffect, useState } from "react";
import { Sparkles, ShieldCheck, Activity, Cpu } from "lucide-react";
import { formatNumber, formatDate } from "../utils/safeHelpers";

export function OpenAIDiagnosticsWidget() {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    fetch("/api/interpretation/status")
      .then((res) => res.json())
      .then((data) => setStatus(data))
      .catch(() => setStatus(null));
  }, []);

  if (!status) {
    return (
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-left font-mono text-xs text-slate-400">
        Loading OpenAI diagnostics...
      </div>
    );
  }

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 text-left font-sans">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Cpu size={16} className="text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">OpenAI Bounded Interpretation Diagnostics</h3>
        </div>
        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
          status.status === "available" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-slate-950 text-slate-400 border border-slate-800"
        }`}>
          {status.status}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
          <span className="text-[10px] text-slate-400 block">Model Target</span>
          <span className="font-bold text-white">{status.model}</span>
        </div>
        <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
          <span className="text-[10px] text-slate-400 block">Last Latency</span>
          <span className="font-bold text-cyan-400">{formatNumber(status.last_latency_ms, 1)} ms</span>
        </div>
        <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
          <span className="text-[10px] text-slate-400 block">Total Requests</span>
          <span className="font-bold text-emerald-400">{status.total_requests}</span>
        </div>
        <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
          <span className="text-[10px] text-slate-400 block">Failed Requests</span>
          <span className="font-bold text-rose-400">{status.failed_requests}</span>
        </div>
      </div>

      <div className="p-3 bg-slate-950 rounded border border-slate-850 space-y-1 text-xs font-mono">
        <span className="text-[10px] text-slate-400 block font-bold">Status Reason & Grounding Policy</span>
        <p className="text-slate-300 text-[11px]">{status.reason}</p>
        <span className="text-[9px] text-slate-500 block pt-1">
          Grounding Rule: Canonical Workstation State is 100% authoritative. No artificial signals generated.
        </span>
      </div>
    </div>
  );
}
