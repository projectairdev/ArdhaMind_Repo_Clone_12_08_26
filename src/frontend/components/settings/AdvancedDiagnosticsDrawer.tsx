// src/frontend/components/settings/AdvancedDiagnosticsDrawer.tsx
import React from "react";
import { X, Activity, Download, Database, ShieldCheck, Cpu } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import { SettingsPresentationState } from "../../utils/canonicalSettingsAdapter";
import { DetectorHealthPanel } from "./DetectorHealthPanel";
import { ArdhaPerformancePanel } from "./ArdhaPerformancePanel";

export function AdvancedDiagnosticsDrawer({
  pres,
  isOpen,
  onClose,
}: {
  pres: SettingsPresentationState;
  isOpen: boolean;
  onClose: () => void;
}) {
  if (!isOpen) return null;

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
    <div
      id="advanced-diagnostics-modal"
      className="fixed inset-0 z-50 flex items-center justify-end bg-black/80 backdrop-blur-sm transition-opacity p-0 sm:p-4"
    >
      <div
        className="flex h-full w-full max-w-2xl flex-col border border-[#242830] bg-[#07080A] shadow-2xl overflow-hidden rounded-[4px] animate-in slide-in-from-right duration-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Drawer Header */}
        <div className="flex h-11 items-center justify-between border-b border-[#191D23] bg-[#0E1013] px-4">
          <div className="flex items-center gap-2">
            <Activity size={14} className="text-[#38BDF8]" />
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#E6E8EB]">
              Institutional Diagnostics &amp; Telemetry
            </span>
            <span className="rounded bg-[#00C896]/20 px-1.5 py-0.5 font-mono text-[9px] font-bold text-[#00C896]">
              {diag.overallHealth}
            </span>
          </div>
          <button
            onClick={onClose}
            aria-label="Close diagnostics"
            className="flex h-7 w-7 items-center justify-center rounded text-[#707987] hover:bg-[#191D23] hover:text-[#E6E8EB] transition"
          >
            <X size={14} />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-terminal-scrollbar font-mono text-[10px]">
          {/* 1. System Runtime Summary */}
          <div className="grid grid-cols-3 gap-2 text-[9px] text-[#707987]">
            <div className="p-2 rounded bg-[#0B0D10] border border-[#191D23]">
              <div className="text-[8px] uppercase font-bold text-[#707987]">Runtime ID</div>
              <div className="font-bold text-[#38BDF8] mt-0.5 truncate">{diag.runtimeId}</div>
            </div>
            <div className="p-2 rounded bg-[#0B0D10] border border-[#191D23]">
              <div className="text-[8px] uppercase font-bold text-[#707987]">State Sequence</div>
              <div className="font-bold text-[#E6E8EB] mt-0.5">#{diag.stateSequence}</div>
            </div>
            <div className="p-2 rounded bg-[#0B0D10] border border-[#191D23]">
              <div className="text-[8px] uppercase font-bold text-[#707987]">Market Session</div>
              <div className="font-bold text-[#00C896] mt-0.5 uppercase">{diag.marketSession}</div>
            </div>
          </div>

          {/* 2. Component Readiness Matrix */}
          <Surface id="settings-diagnostics-market-feed" className="overflow-hidden">
            <SectionHeader title="COMPONENT READINESS MATRIX" eyebrow="1. Ingestion Pipeline Readiness" accent="cyan" />
            <div className="p-3 bg-[#0B0D10] space-y-2">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {Object.entries(diag.componentReadiness).map(([comp, status]) => (
                  <div
                    key={comp}
                    id={`settings-diagnostics-${comp.replace("_", "-")}`}
                    className="p-2 rounded bg-[#0E1013] border border-[#191D23]"
                  >
                    <div className="text-[8px] text-[#707987] font-bold uppercase truncate">
                      {comp.replace("_", " ")}
                    </div>
                    <div
                      className={`font-bold text-xs uppercase mt-0.5 ${
                        status === "ready" || status === "connected" || status === "live"
                          ? "text-[#00C896]"
                          : status === "market_closed"
                          ? "text-[#38BDF8]"
                          : "text-[#E59700]"
                      }`}
                    >
                      {status}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Surface>

          {/* Post-Auth Startup Telemetry */}
          {diag.postAuthMetrics && (
            <Surface id="settings-diagnostics-post-auth-latency" className="overflow-hidden">
              <SectionHeader title="POST-AUTH STARTUP LATENCY TELEMETRY" eyebrow="2. Startup Latency Trace" accent="emerald" />
              <div className="p-3 bg-[#0B0D10] space-y-2">
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 font-mono text-[9.5px]">
                  <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                    <div className="text-[8px] text-[#707987] font-bold uppercase">TOKEN EXCHANGE</div>
                    <div className="font-bold text-[#E6E8EB] mt-0.5">{diag.postAuthMetrics.tokenExchangeMs ?? "—"} ms</div>
                  </div>
                  <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                    <div className="text-[8px] text-[#707987] font-bold uppercase">SESSION SAVE</div>
                    <div className="font-bold text-[#E6E8EB] mt-0.5">{diag.postAuthMetrics.sessionSaveMs ?? "—"} ms</div>
                  </div>
                  <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                    <div className="text-[8px] text-[#707987] font-bold uppercase">BROKER CONNECT</div>
                    <div className="font-bold text-[#E6E8EB] mt-0.5">{diag.postAuthMetrics.brokerConnectMs ?? "—"} ms</div>
                  </div>
                  <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                    <div className="text-[8px] text-[#707987] font-bold uppercase">FEED SUBSCRIBE</div>
                    <div className="font-bold text-[#E6E8EB] mt-0.5">{diag.postAuthMetrics.feedConnectMs ?? "—"} ms</div>
                  </div>
                  <div className="p-2 rounded bg-[#0E1013] border border-[#38BDF8]/30 bg-[#38BDF8]/5">
                    <div className="text-[8px] text-[#38BDF8] font-bold uppercase">TOTAL POST-AUTH</div>
                    <div className="font-bold text-[#00C896] mt-0.5">{diag.postAuthMetrics.totalPostAuthMs ?? "—"} ms</div>
                  </div>
                </div>
              </div>
            </Surface>
          )}

          {/* 3. Dataset Integrity Checks & Export */}
          <Surface id="settings-diagnostics-options" className="overflow-hidden">
            <SectionHeader title="DATASET INTEGRITY &amp; TELEMETRY COUNTS" eyebrow="2. Pipeline Integrity" accent="violet" />
            <div className="p-3 bg-[#0B0D10] space-y-2">
              <div className="divide-y divide-[#191D23]">
                {diag.dataIntegrity.map((row, idx) => (
                  <div key={idx} className="flex items-center justify-between py-1.5">
                    <div>
                      <div className="font-bold text-[#E6E8EB]">{row.dataset}</div>
                      <div className="text-[8px] text-[#707987]">Provider: {row.provider}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[8.5px] text-[#707987]">Count: {row.count}</span>
                      <span className="text-[8px] font-bold text-[#00C896] bg-[#00C896]/20 px-1.5 py-0.5 rounded uppercase">
                        {row.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-2 border-t border-[#191D23] flex items-center justify-between">
                <span className="text-[8.5px] text-[#707987]">Sanitized JSON diagnostics telemetry for technical audit.</span>
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

          {/* 4. Phase 3.1 Opportunity Detector Diagnostics */}
          <Surface className="overflow-hidden">
            <SectionHeader title="OPPORTUNITY DETECTOR HEALTH &amp; METRICS" eyebrow="3. Detector Telemetry" accent="amber" />
            <div className="p-3 bg-[#0B0D10]">
              <DetectorHealthPanel />
            </div>
          </Surface>

          {/* 5. Ardha Performance Telemetry */}
          <Surface id="settings-diagnostics-ardha-performance" className="overflow-hidden">
            <SectionHeader
              title="ARDHA PERFORMANCE — PREDICTION VS REALITY"
              detail="50-Field Standard Evaluation Contract"
              eyebrow="4. Prediction Accuracy"
              accent="emerald"
            />
            <div className="p-3 bg-[#0B0D10]">
              <ArdhaPerformancePanel />
            </div>
          </Surface>
        </div>

        {/* Drawer Footer */}
        <div className="flex h-10 items-center justify-between border-t border-[#191D23] bg-[#0E1013] px-4 font-mono text-[9px] text-[#707987]">
          <span>AIR ArdhaMind v1.3.1-STAGING · Read-Only Workstation</span>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded bg-[#191D23] text-[#E6E8EB] hover:bg-[#242830] transition font-bold"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default AdvancedDiagnosticsDrawer;
