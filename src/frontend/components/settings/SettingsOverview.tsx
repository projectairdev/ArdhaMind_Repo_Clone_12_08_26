import React from "react";
import { KeyRound, ShieldCheck, Activity, Database, CheckCircle2, Clock, Server, AlertCircle } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import { SettingsPresentationState } from "../../utils/canonicalSettingsAdapter";
import { useNavigation } from "../../context/NavigationContext";

export function SettingsOverview({
  pres,
  onNavigateTab,
}: {
  pres: SettingsPresentationState;
  onNavigateTab: (tab: any) => void;
}) {
  const { navigateTo } = useNavigation();

  return (
    <div className="space-y-3 font-sans text-left text-[11px] min-w-0">
      {/* ── TOP SUMMARY CARDS (6 SUMMARY CARDS) ── */}
      <Surface className="overflow-hidden">
        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-[#191D23] bg-[#0B0D10] p-2 sm:p-2.5 items-center font-mono">
          {pres.overviewCards.map((card, i) => {
            const getTarget = () => {
              if (i === 0) return { workspace: "settings" as const, tab: "connections", section: "settings-connections-broker" };
              if (i === 1) return { workspace: "settings" as const, tab: "diagnostics", section: "settings-diagnostics-market-feed" };
              if (i === 2) return { workspace: "settings" as const, tab: "diagnostics", section: "settings-diagnostics-options" };
              if (i === 3) return { workspace: "settings" as const, tab: "diagnostics", section: "settings-diagnostics-news" };
              if (i === 4) return { workspace: "settings" as const, tab: "preferences" };
              return { workspace: "settings" as const, tab: "diagnostics" };
            };
            return (
              <button
                key={i}
                onClick={() => navigateTo(getTarget())}
                className="px-2 py-1 space-y-0.5 min-w-0 text-left hover:bg-[#13161A] rounded transition cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#38BDF8]"
              >
                <div className="text-[8px] font-bold uppercase text-[#707987] tracking-wider truncate">{card.title}</div>
                <div className={`text-xs font-extrabold uppercase ${card.status === "CONNECTED" || card.status === "HEALTHY" ? "text-[#00C896]" : card.status === "READY" ? "text-[#38BDF8]" : "text-[#E5484D]"}`}>
                  {card.status}
                </div>
                <div className="text-[7px] text-[#707987] truncate">{card.detail}</div>
              </button>
            );
          })}
        </div>
      </Surface>

      {/* ── MAIN OVERVIEW GRID: 2 COLUMNS ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 items-start min-w-0">
        {/* API & BROKER CONNECTIONS SUMMARY */}
        <Surface className="overflow-hidden">
          <SectionHeader title="API &amp; BROKER CONNECTIONS SUMMARY" eyebrow="Configured Telemetry" accent="cyan" />
          <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[10px]">
            <div className="divide-y divide-[#191D23]">
              {pres.services.map((svc, idx) => (
                <div key={idx} className="flex items-center justify-between py-1.5 min-w-0">
                  <div className="min-w-0">
                    <div className="font-bold text-[#E6E8EB] flex items-center gap-1">
                      <span className="truncate">{svc.name}</span>
                      {svc.isOfficial && <ShieldCheck size={10} className="text-[#8B5CF6] shrink-0" />}
                    </div>
                    <div className="text-[8px] text-[#707987] truncate">{svc.detail}</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${
                      svc.status === "CONNECTED" || svc.status === "HEALTHY" ? "bg-[#00C896]/20 text-[#00C896]" : svc.status === "READY" ? "bg-[#38BDF8]/20 text-[#38BDF8]" : "bg-[#E5484D]/20 text-[#E5484D]"
                    }`}>
                      {svc.status}
                    </span>
                    <button
                      onClick={() => navigateTo(idx === 0 ? { workspace: "settings", tab: "connections", section: "settings-connections-broker" } : { workspace: "settings", tab: "diagnostics" })}
                      className="text-[#38BDF8] hover:underline text-[9px] font-bold cursor-pointer"
                    >
                      Manage →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Surface>

        {/* SYSTEM PREFERENCES & NOTIFICATION SUMMARY */}
        <div className="space-y-3 min-w-0 items-start">
          <Surface className="overflow-hidden">
            <SectionHeader title="SYSTEM PREFERENCES SUMMARY" eyebrow="Display &amp; Formatting" accent="violet" />
            <div className="p-3 bg-[#0B0D10] space-y-1.5 font-mono text-[9px]">
              <div className="flex justify-between py-1 border-b border-[#191D23]">
                <span className="text-[#707987]">Theme:</span>
                <span className="text-[#E6E8EB] font-bold uppercase">{pres.preferences.theme} (Institutional Dark)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#191D23]">
                <span className="text-[#707987]">Timezone:</span>
                <span className="text-[#38BDF8] font-bold">{pres.preferences.timezone}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#191D23]">
                <span className="text-[#707987]">Date / Time Format:</span>
                <span className="text-[#E6E8EB] font-bold">{pres.preferences.dateFormat} · {pres.preferences.timeFormat}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#191D23]">
                <span className="text-[#707987]">Default Landing Workspace:</span>
                <span className="text-[#00C896] font-bold uppercase">{pres.preferences.defaultWorkspace}</span>
              </div>
              <div className="pt-1 text-right">
                <button
                  onClick={() => onNavigateTab("preferences")}
                  className="text-[#38BDF8] font-bold hover:underline text-[9px]"
                >
                  Configure Preferences →
                </button>
              </div>
            </div>
          </Surface>

          <Surface className="overflow-hidden">
            <SectionHeader title="DIAGNOSTICS &amp; RUNTIME SUMMARY" eyebrow="State Telemetry" accent="cyan" />
            <div className="p-3 bg-[#0B0D10] space-y-1.5 font-mono text-[9px]">
              <div className="flex justify-between py-1 border-b border-[#191D23]">
                <span className="text-[#707987]">Runtime ID:</span>
                <span className="text-[#38BDF8] font-bold">{pres.diagnostics.runtimeId}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#191D23]">
                <span className="text-[#707987]">State Sequence:</span>
                <span className="text-[#E6E8EB] font-bold">#{pres.diagnostics.stateSequence}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#191D23]">
                <span className="text-[#707987]">Environment:</span>
                <span className="text-[#E59700] font-bold uppercase">{pres.environment}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[#707987]">Last Telemetry Sync:</span>
                <span className="text-[#00C896] font-bold">{pres.lastUpdatedIst}</span>
              </div>
              <div className="pt-1 text-right">
                <button
                  onClick={() => onNavigateTab("diagnostics")}
                  className="text-[#38BDF8] font-bold hover:underline text-[9px]"
                >
                  View Full Diagnostics →
                </button>
              </div>
            </div>
          </Surface>
        </div>
      </div>
    </div>
  );
}

export default SettingsOverview;
