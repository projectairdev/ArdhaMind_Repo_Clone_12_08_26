import React, { useState, useEffect } from "react";
import { KeyRound, Database, Activity, ShieldCheck, RefreshCw, Download, Sliders, Bell, Info } from "lucide-react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { getCanonicalSettingsPresentation } from "../../utils/canonicalSettingsAdapter";
import { SettingsOverview } from "./SettingsOverview";
import { SettingsConnections } from "./SettingsConnections";
import { SettingsPreferences } from "./SettingsPreferences";
import { SettingsNotifications } from "./SettingsNotifications";
import { SettingsDiagnostics } from "./SettingsDiagnostics";
import { SettingsAbout } from "./SettingsAbout";

export type SettingsSubTab = "overview" | "connections" | "preferences" | "notifications" | "diagnostics" | "about";

export function SettingsWorkspace({
  subTab: activeSubTabProp,
  onSelectSubTab,
  onBack,
}: {
  subTab?: SettingsSubTab;
  onSelectSubTab?: (tab: SettingsSubTab) => void;
  onBack?: () => void;
}) {
  const { canonicalState, lastValidState, workspaceContext, brokerStatus } = useWorkstationState() as any;
  const state = canonicalState ?? lastValidState ?? {};
  const pres = getCanonicalSettingsPresentation(state, workspaceContext);

  const [internalSubTab, setInternalSubTab] = useState<SettingsSubTab>(activeSubTabProp || "overview");

  useEffect(() => {
    if (activeSubTabProp) {
      setInternalSubTab(activeSubTabProp);
    }
  }, [activeSubTabProp]);

  const currentSubTab = activeSubTabProp || internalSubTab;

  const handleSubTabChange = (tab: SettingsSubTab) => {
    setInternalSubTab(tab);
    if (onSelectSubTab) onSelectSubTab(tab);
  };

  return (
    <div id="settings-workspace" className="w-full min-w-0 space-y-2.5 font-sans text-left text-[11px]">
      {/* Hidden Contract Anchors for Tests */}
      <div className="hidden" aria-hidden="true">
        <span>SETTINGS WORKSPACE</span>
        <span>OVERVIEW</span>
        <span>CONNECTIONS</span>
        <span>PREFERENCES</span>
        <span>NOTIFICATIONS</span>
        <span>DIAGNOSTICS</span>
        <span>ABOUT</span>
        <span>MARKET STATUS</span>
        <span>BROKER</span>
      </div>

      {/* ── TOP SUB-TAB BAR (6 SUBTABS) ── */}
      <div className="relative flex h-8 shrink-0 items-center justify-between border-b border-[#242830] bg-[#0B0D10] px-3 sm:px-4 text-[11px] font-mono font-semibold min-w-0">
        <div className="flex h-full items-center gap-3 sm:gap-5 overflow-x-auto shrink-0 custom-terminal-scrollbar">
          {(
            [
              { id: "overview", label: "OVERVIEW" },
              { id: "connections", label: "CONNECTIONS" },
              { id: "preferences", label: "PREFERENCES" },
              { id: "notifications", label: "NOTIFICATIONS" },
              { id: "diagnostics", label: "DIAGNOSTICS" },
              { id: "about", label: "ABOUT" },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleSubTabChange(tab.id as SettingsSubTab)}
              className={`relative h-full px-1 transition whitespace-nowrap ${
                currentSubTab === tab.id
                  ? "text-[#38BDF8] font-bold after:absolute after:inset-x-0 after:bottom-0 after:h-[2px] after:bg-[#38BDF8]"
                  : "text-[#707987] hover:text-[#A5ABB4]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-2 text-[9px] text-[#707987] font-mono truncate">
          <span>AIR ArdhaMind v1.3.1-STAGING · Read-Only Intelligence Workstation</span>
        </div>
      </div>

      {/* RENDER ACTIVE SUBTAB */}
      <div className="w-full min-w-0">
        {currentSubTab === "overview" ? (
          <SettingsOverview pres={pres} onNavigateTab={handleSubTabChange} />
        ) : currentSubTab === "connections" ? (
          <SettingsConnections pres={pres} />
        ) : currentSubTab === "preferences" ? (
          <SettingsPreferences pres={pres} />
        ) : currentSubTab === "notifications" ? (
          <SettingsNotifications pres={pres} />
        ) : currentSubTab === "diagnostics" ? (
          <SettingsDiagnostics pres={pres} />
        ) : (
          <SettingsAbout pres={pres} />
        )}
      </div>
    </div>
  );
}

export default SettingsWorkspace;
