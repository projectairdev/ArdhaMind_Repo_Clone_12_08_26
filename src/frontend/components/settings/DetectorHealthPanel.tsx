import React from "react";
import { Activity, CheckCircle2, AlertTriangle, ShieldX, Cpu } from "lucide-react";
import { useWorkstationState } from "../../context/WorkstationStateContext";

export function DetectorHealthPanel() {
  const { canonicalState, lastValidState } = useWorkstationState();
  const state = canonicalState ?? lastValidState;
  const oppIntel = state?.opportunity_intelligence;
  const healthMap = oppIntel?.detector_health || {};
  const metrics = oppIntel?.scan_metrics;

  const healthList = Object.values(healthMap);

  return (
    <div className="space-y-4 font-mono text-[11px] text-[#E6E8EB]">
      {/* Metrics Banner */}
      <div className="bg-[#050607] border border-[#242830] p-3.5 rounded flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-[#38BDF8]" />
          <div>
            <span className="text-xs font-bold text-white block">Opportunity Engine Scan Health</span>
            <span className="text-[10px] text-[#707987]">Last Scan: {metrics?.last_scan_at ? new Date(metrics.last_scan_at).toLocaleTimeString("en-IN") : "Active"}</span>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div>
            <span className="text-[9.5px] text-[#707987] block">SCAN DURATION</span>
            <span className="font-bold text-[#38BDF8]">{metrics?.scan_duration_ms ?? 0} ms</span>
          </div>
          <div>
            <span className="text-[9.5px] text-[#707987] block">DETECTORS DURATION</span>
            <span className="font-bold text-[#00C896]">{metrics?.detector_duration_ms ?? 0} ms</span>
          </div>
          <div>
            <span className="text-[9.5px] text-[#707987] block">EVALUATED TODAY</span>
            <span className="font-bold text-white">{metrics?.candidates_evaluated ?? 0}</span>
          </div>
        </div>
      </div>

      {/* Detector Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {healthList.map((health: any) => (
          <div key={health.detector_id} className="bg-[#0B0D10] border border-[#242830] rounded p-3.5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu size={15} className="text-[#8B5CF6]" />
                <span className="font-bold text-xs text-white uppercase">{health.detector_id} Detector</span>
                <span className="text-[10px] text-gray-500">v{health.version}</span>
              </div>
              <span className={`px-2 py-0.5 rounded text-[9.5px] font-bold ${
                health.status === "HEALTHY" ? "bg-[#00C896]/20 text-[#00C896] border border-[#00C896]/40" :
                health.status === "BLOCKED" ? "bg-amber-500/20 text-amber-400 border border-amber-500/40" :
                "bg-red-500/20 text-red-400 border border-red-500/40"
              }`}>
                {health.status}
              </span>
            </div>

            {/* Daily Detection Counts */}
            <div className="grid grid-cols-4 gap-2 text-center text-[10px] bg-[#050607] p-2 rounded border border-[#191D23]">
              <div>
                <span className="text-[#707987] block">DETECTED</span>
                <span className="font-bold text-[#38BDF8]">{health.detections_today}</span>
              </div>
              <div>
                <span className="text-[#707987] block">QUALIFIED</span>
                <span className="font-bold text-[#00C896]">{health.qualified_today}</span>
              </div>
              <div>
                <span className="text-[#707987] block">BLOCKED</span>
                <span className="font-bold text-amber-400">{health.blocked_today}</span>
              </div>
              <div>
                <span className="text-[#707987] block">REJECTED</span>
                <span className="font-bold text-gray-400">{health.rejected_today}</span>
              </div>
            </div>

            {/* Blockers or Errors */}
            {health.data_blockers && health.data_blockers.length > 0 && (
              <div className="bg-amber-500/10 border border-amber-500/30 p-2 rounded text-[10px] text-amber-300">
                <span className="font-bold">Input Blocker:</span> {health.data_blockers.join("; ")}
              </div>
            )}

            {health.errors && health.errors.length > 0 && (
              <div className="bg-red-500/10 border border-red-500/30 p-2 rounded text-[10px] text-red-300">
                <span className="font-bold">Errors:</span> {health.errors.join("; ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
