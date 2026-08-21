import React from "react";
import { Activity, Download, Server, ShieldCheck, Database, Clock } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import { SettingsPresentationState } from "../../utils/canonicalSettingsAdapter";
import { DetectorHealthPanel } from "./DetectorHealthPanel";
import { ArdhaPerformancePanel } from "./ArdhaPerformancePanel";

export function SettingsDiagnostics({ pres }: { pres: SettingsPresentationState }) {
  const diag = pres.diagnostics;

  const handleExportDiagnostics = () => {
    const data = {
      schema_version: "1.3.1-STAGING",
      generated_at: diag.generatedAt,
      generated_at_ist: diag.generatedAtIst,
      overall_health: diag.overallHealth,
      runtime_id: diag.runtimeId,
      state_sequence: diag.stateSequence,
      market_session: diag.marketSession,
      component_readiness: diag.componentReadiness,
      data_integrity: diag.dataIntegrity,
      environment: pres.environment,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ardhamind-diagnostics-${diag.runtimeId.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-3 font-sans text-left text-[11px] min-w-0">
      {/* ── 1. SYSTEM OVERALL HEALTH & RUNTIME METRICS ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="CANONICAL RUNTIME DIAGNOSTICS & SEQUENCE" eyebrow="1. System Health" accent="cyan" />
        <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[10px]">
          <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
            <div className="flex items-center gap-2">
              <Activity size={14} className="text-[#00C896]" />
              <span className="font-bold text-[#E6E8EB]">Overall System Operational Readiness</span>
            </div>
            <span
              className={`px-1.5 py-0.5 rounded text-[8.5px] font-bold ${
                diag.overallHealth === "HEALTHY" ? "bg-[#00C896]/20 text-[#00C896]" : "bg-[#E59700]/20 text-[#E59700]"
              }`}
            >
              200 OK ({diag.overallHealth})
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-[9px] text-[#707987]">
            <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
              <div className="uppercase font-bold text-[#707987]">Runtime ID</div>
              <div className="font-bold text-[#38BDF8] mt-0.5 font-mono">{diag.runtimeId}</div>
            </div>
            <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
              <div className="uppercase font-bold text-[#707987]">State Sequence</div>
              <div className="font-bold text-[#E6E8EB] mt-0.5 font-mono">#{diag.stateSequence}</div>
            </div>
            <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
              <div className="uppercase font-bold text-[#707987]">Market Session</div>
              <div className="font-bold text-[#00C896] mt-0.5 font-mono">{diag.marketSession}</div>
            </div>
          </div>
        </div>
      </Surface>

      {/* ── 2. COMPONENT READINESS MATRIX ── */}
      <Surface id="settings-diagnostics-market-feed" className="overflow-hidden">
        <SectionHeader title="COMPONENT READINESS MATRIX" eyebrow="2. Ingestion Pipeline Readiness" accent="violet" />
        <div className="p-3 bg-[#0B0D10] space-y-1.5 font-mono text-[9.5px]">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {Object.entries(diag.componentReadiness).map(([comp, status]) => (
              <div key={comp} id={`settings-diagnostics-${comp.replace("_", "-")}`} className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                <div className="text-[8px] text-[#707987] font-bold uppercase">{comp.replace("_", " ")}</div>
                <div className={`font-bold text-xs uppercase mt-0.5 ${
                  status === "ready" || status === "connected" || status === "live" ? "text-[#00C896]" : status === "market_closed" ? "text-[#38BDF8]" : "text-[#E59700]"
                }`}>
                  {status}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Surface>

      {/* ── 3. DATA INTEGRITY CHECKS & EXPORT ── */}
      <Surface id="settings-diagnostics-options" className="overflow-hidden">
        <SectionHeader title="DATASET INTEGRITY & PIPELINE VALIDATION" eyebrow="3. Quality Verification" accent="amber" />
        <div className="p-3 bg-[#0B0D10] space-y-2.5 font-mono text-[9.5px]">
          <div className="divide-y divide-[#191D23]">
            {diag.dataIntegrity.map((row, idx) => (
              <div key={idx} className="flex items-center justify-between py-1.5">
                <div>
                  <div className="font-bold text-[#E6E8EB]">{row.dataset}</div>
                  <div className="text-[8px] text-[#707987]">Provider: {row.provider}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[8px] text-[#707987]">Count: {row.count}</span>
                  <span className="text-[8px] font-bold text-[#00C896] bg-[#00C896]/20 px-1.5 py-0.5 rounded uppercase">
                    {row.status}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-[#191D23] flex items-center justify-between">
            <span className="text-[8.5px] text-[#707987]">Export sanitized JSON diagnostics telemetry report for support audit.</span>
            <button
              onClick={handleExportDiagnostics}
              className="px-3 py-1.5 bg-[#38BDF8]/15 hover:bg-[#38BDF8]/25 border border-[#38BDF8]/30 text-[#38BDF8] font-bold rounded text-[9.5px] transition flex items-center gap-1"
            >
              <Download size={11} />
              Export Diagnostics JSON
            </button>
          </div>
        </div>
      </Surface>

      {/* ── 4. PHASE 3.1 DETECTOR HEALTH DIAGNOSTICS ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="PHASE 3.1 OPPORTUNITY DETECTOR HEALTH & METRICS" eyebrow="4. Detector Diagnostics" accent="cyan" />
        <div className="p-3 bg-[#0B0D10]">
          <DetectorHealthPanel />
        </div>
      </Surface>

      {/* ── 5. ARDHA PERFORMANCE — PREDICTION VS REALITY ── */}
      <Surface id="settings-diagnostics-ardha-performance" className="overflow-hidden">
        <SectionHeader
          title="ARDHA PERFORMANCE — PREDICTION VS REALITY"
          detail="50-Field Standard Evaluation Contract"
          eyebrow="5. Accuracy & Performance Telemetry"
          accent="emerald"
        />
        <div className="p-3 bg-[#0B0D10]">
          <ArdhaPerformancePanel />
        </div>
      </Surface>
    </div>
  );
}

export default SettingsDiagnostics;
