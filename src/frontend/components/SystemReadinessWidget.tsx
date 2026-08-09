// src/frontend/components/SystemReadinessWidget.tsx
import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { ShieldCheck, Activity, Database, KeyRound, Sparkles, Cpu, Layers } from "lucide-react";
import { safeString } from "../utils/safeHelpers";

export function SystemReadinessWidget() {
  const { workspaceContext, marketContext, optionContext, newsSentiment, data, workspaceReadiness } = useWorkstationState() as any;

  const brokerStatus = safeString(workspaceContext?.brokerState, "DISCONNECTED");
  const feedStatus = safeString(marketContext?.feed_health, "OFFLINE");
  const optionStatus = optionContext?.underlying_spot ? "READY" : "UNAVAILABLE";
  const hasNewsProviders = Object.keys(newsSentiment?.provider_health || {}).length > 0;
  const newsStatus = (newsSentiment?.status === "ready" || newsSentiment?.section_status === "ready") && hasNewsProviders ? "READY" : "UNAVAILABLE";

  const macroData = data?.macro_intelligence || {};
  const hasMacroProviders = Object.keys(macroData?.provider_health || {}).length > 0;
  const macroStatus = (macroData.status === "ready" || macroData.section_status === "ready") && hasMacroProviders ? "READY" : "UNAVAILABLE";

  const liveAssistantReadiness =
    feedStatus === "HEALTHY" && optionStatus === "READY" ? "READY" : "DEGRADED";

  const items = [
    { label: "Zerodha Session", status: brokerStatus, icon: KeyRound },
    { label: "Market Feed", status: feedStatus, icon: Activity },
    { label: "Options Telemetry", status: optionStatus, icon: Layers },
    { label: "News Intelligence", status: newsStatus, icon: Database },
    { label: "Macro Telemetry", status: macroStatus, icon: Database },
    { label: "Live Assistant", status: liveAssistantReadiness, icon: Cpu },
  ];

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 text-left font-sans">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck size={16} className="text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">Consolidated Connection & Telemetry Readiness</h3>
        </div>
        <span className="text-[10px] font-mono text-cyan-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
          Canonical State Derived
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 font-mono text-xs">
        {items.map((it) => {
          const IconComponent = it.icon;
          const isOk = it.status === "CONNECTED" || it.status === "HEALTHY" || it.status === "READY";
          const isDegraded = it.status === "DEGRADED" || it.status === "EXPIRED" || it.status === "STALE";

          return (
            <div key={it.label} className="p-2.5 bg-slate-950 rounded border border-slate-850 space-y-1">
              <div className="flex items-center gap-1.5 text-slate-400 text-[10px]">
                <IconComponent size={12} className="text-cyan-400" />
                <span>{it.label}</span>
              </div>
              <span
                className={`font-bold block uppercase text-xs ${
                  isOk ? "text-emerald-400" : isDegraded ? "text-amber-400" : "text-slate-500"
                }`}
              >
                {it.status}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
