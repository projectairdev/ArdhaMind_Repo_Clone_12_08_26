import React, { useState } from "react";
import { Sliders, Save, RotateCcw, AlertTriangle, CheckCircle2, ShieldCheck } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import {
  SettingsPresentationState,
  UserPreferencesState,
  saveStoredPreferences,
  DEFAULT_USER_PREFERENCES,
} from "../../utils/canonicalSettingsAdapter";
import { useWorkstationState } from "../../context/WorkstationStateContext";

export function SettingsPreferences({ pres }: { pres: SettingsPresentationState }) {
  const [prefs, setPrefs] = useState<UserPreferencesState>(pres.preferences);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [showConfirmReset, setShowConfirmReset] = useState(false);

  const { niftyModeOverride, setNiftyModeOverride, setIntelligenceSubTabOverride } = useWorkstationState() as any;

  const handleChange = (key: keyof UserPreferencesState, value: any) => {
    const updated = { ...prefs, [key]: value };
    setPrefs(updated);
    saveStoredPreferences(updated);
    setSaveMessage("Preferences saved to local storage.");
    setTimeout(() => setSaveMessage(null), 3000);
  };

  const handleResetPreferences = () => {
    setPrefs(DEFAULT_USER_PREFERENCES);
    saveStoredPreferences(DEFAULT_USER_PREFERENCES);
    setShowConfirmReset(false);
    setSaveMessage("Local UI preferences reset to defaults.");
    setTimeout(() => setSaveMessage(null), 3000);
  };

  const handleStagingSessionClick = (mode: "auto" | "pre_market" | "live" | "post_market") => {
    if (setNiftyModeOverride) {
      setNiftyModeOverride(mode);
      if (mode === "auto") {
        if (setIntelligenceSubTabOverride) setIntelligenceSubTabOverride(null);
      } else if (mode === "pre_market") {
        if (setIntelligenceSubTabOverride) setIntelligenceSubTabOverride("pre_market");
      } else if (mode === "live") {
        if (setIntelligenceSubTabOverride) setIntelligenceSubTabOverride("now");
      } else if (mode === "post_market") {
        if (setIntelligenceSubTabOverride) setIntelligenceSubTabOverride("next_day");
      }
    }
  };

  return (
    <div className="space-y-3 font-sans text-left text-[11px] min-w-0">
      {/* ── 1. USER INTERFACE & FORMATTING PREFERENCES ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="WORKSTATION DISPLAY &amp; FORMATTING PREFERENCES" eyebrow="1. User Preferences" accent="cyan" />
        <div className="p-3 bg-[#0B0D10] space-y-3 font-mono text-[10px]">
          {saveMessage && (
            <div className="p-2 bg-[#00C896]/10 border border-[#00C896]/30 text-[#00C896] rounded flex items-center justify-between text-[9px]">
              <span className="flex items-center gap-1">
                <CheckCircle2 size={12} />
                {saveMessage}
              </span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Time Format */}
            <div className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1">
              <label className="text-[#707987] font-bold block uppercase text-[9px]">Clock Format:</label>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleChange("timeFormat", "12h")}
                  className={`px-2 py-1 rounded text-[9px] font-bold transition ${
                    prefs.timeFormat === "12h" ? "bg-[#38BDF8] text-[#050607]" : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                  }`}
                >
                  12-Hour (11:33 PM IST)
                </button>
                <button
                  onClick={() => handleChange("timeFormat", "24h")}
                  className={`px-2 py-1 rounded text-[9px] font-bold transition ${
                    prefs.timeFormat === "24h" ? "bg-[#38BDF8] text-[#050607]" : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                  }`}
                >
                  24-Hour (23:33 IST)
                </button>
              </div>
            </div>

            {/* Number Format */}
            <div className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1">
              <label className="text-[#707987] font-bold block uppercase text-[9px]">Numeric Notation:</label>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleChange("numberFormat", "IN")}
                  className={`px-2 py-1 rounded text-[9px] font-bold transition ${
                    prefs.numberFormat === "IN" ? "bg-[#00C896] text-[#050607]" : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                  }`}
                >
                  Indian (Lakhs / Crores)
                </button>
                <button
                  onClick={() => handleChange("numberFormat", "INTL")}
                  className={`px-2 py-1 rounded text-[9px] font-bold transition ${
                    prefs.numberFormat === "INTL" ? "bg-[#00C896] text-[#050607]" : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                  }`}
                >
                  International (Millions / Billions)
                </button>
              </div>
            </div>

            {/* Default Landing Workspace */}
            <div className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1">
              <label className="text-[#707987] font-bold block uppercase text-[9px]">Default Landing Workspace:</label>
              <div className="flex items-center gap-1.5 flex-wrap">
                {(["market", "intelligence", "news", "portfolio"] as const).map((ws) => (
                  <button
                    key={ws}
                    onClick={() => handleChange("defaultWorkspace", ws)}
                    className={`px-2 py-1 rounded text-[9px] font-bold uppercase transition ${
                      prefs.defaultWorkspace === ws ? "bg-[#8B5CF6] text-white" : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    {ws === "news" ? "NEWS & UPDATES" : ws}
                  </button>
                ))}
              </div>
            </div>

            {/* Default Market Tab */}
            <div className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1">
              <label className="text-[#707987] font-bold block uppercase text-[9px]">Default Market Tab:</label>
              <div className="flex items-center gap-1.5">
                {(["nifty", "metrics", "options"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => handleChange("defaultMarketTab", tab)}
                    className={`px-2 py-1 rounded text-[9px] font-bold uppercase transition ${
                      prefs.defaultMarketTab === tab ? "bg-[#38BDF8] text-[#050607]" : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Surface>

      {/* ── 2. STAGING QA CONTROLS (ONLY IN STAGING ENVIRONMENT) ── */}
      {pres.environment === "STAGING" && (
        <Surface className="overflow-hidden">
          <SectionHeader title="STAGING QA PREVIEW CONTROLS" eyebrow="2. Staging Only" accent="amber" />
          <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[10px]">
            <div className="text-[9px] text-[#E59700]">
              QA Session Preview Mode (Transient Staging Controls — Not saved as permanent user preferences):
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {(["auto", "pre_market", "live", "post_market"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => handleStagingSessionClick(m)}
                  className={`px-2.5 py-1 rounded text-[9px] font-bold uppercase transition ${
                    niftyModeOverride === m
                      ? "bg-[#E59700] text-[#050607]"
                      : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                  }`}
                >
                  {m === "auto" ? "Auto" : m === "pre_market" ? "Pre-Market" : m === "live" ? "Live Session" : "Post-Market"}
                </button>
              ))}
            </div>
          </div>
        </Surface>
      )}

      {/* ── 3. SAFE LOCAL UI RESET ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="SAFE LOCAL UI RESET" eyebrow="3. User Storage Management" accent="violet" />
        <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[10px]">
          <p className="text-[9px] text-[#707987] leading-relaxed">
            Resets local browser UI preferences to workstation defaults. Does NOT disconnect broker session, alter market data, or delete backend state.
          </p>

          {!showConfirmReset ? (
            <button
              onClick={() => setShowConfirmReset(true)}
              className="px-3 py-1.5 bg-[#191D23] hover:bg-[#242830] border border-[#242830] text-[#E6E8EB] font-bold rounded text-[9px] transition flex items-center gap-1.5"
            >
              <RotateCcw size={11} />
              Reset Local UI Preferences
            </button>
          ) : (
            <div className="p-2.5 bg-[#E5484D]/10 border border-[#E5484D]/30 rounded space-y-2">
              <div className="text-[9px] font-bold text-[#E5484D] flex items-center gap-1">
                <AlertTriangle size={12} />
                Confirm Reset Local UI Preferences?
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleResetPreferences}
                  className="px-2.5 py-1 bg-[#E5484D] text-white font-bold rounded text-[9px]"
                >
                  Yes, Reset UI Preferences
                </button>
                <button
                  onClick={() => setShowConfirmReset(false)}
                  className="px-2.5 py-1 bg-[#191D23] text-[#A5ABB4] font-bold rounded text-[9px]"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </Surface>
    </div>
  );
}

export default SettingsPreferences;
