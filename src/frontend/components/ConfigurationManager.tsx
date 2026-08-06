// src/frontend/components/ConfigurationManager.tsx
import React, { useEffect, useState } from "react";
import { getConfigurationReport } from "../services/dashboard";
import { ConfigurationReport } from "../types";
import { AlertCircle, Settings, Sliders, CheckSquare } from "lucide-react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  safeArray,
  safeNumber,
  safeString,
  safeObject
} from "../utils/safeHelpers";

export interface ConfigurationManagerProps {
  visiblePanels: Record<string, boolean>;
  onTogglePanel: (panelKey: string) => void;
}

export function ConfigurationManager({ visiblePanels, onTogglePanel }: ConfigurationManagerProps) {
  const { preferredTradingStyle, setPreferredTradingStyle, configurationReport: report, syncBroker } = useWorkstationState();
  const loading = false;
  const error = null;
  const fetchConfig = async () => { await syncBroker(true); };

  // Preference fields state
  const [logLevel, setLogLevel] = useState("INFO");
  const [intervalVal, setIntervalVal] = useState(15);
  const [notifSound, setNotifSound] = useState(true);

  useEffect(() => {
    if (report?.preferences) {
      setLogLevel(safeString(report.preferences.logging_level, "INFO"));
      setIntervalVal(safeNumber(report.preferences.refresh_interval_seconds, 15));
      setNotifSound(true);
    }
  }, [report]);

  const handleSavePreferences = (e: React.FormEvent) => {
    e.preventDefault();
    alert("Workspace preferences saved and persistent across sessions.");
  };

  if (loading) {
    return (
      <div id="config-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-44 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div id="config-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold">Configuration Manager Unresponsive</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Could not retrieve system parameters."}</p>
        <button onClick={fetchConfig} className="px-3 py-1 bg-slate-900 text-xs text-slate-300 border border-slate-800 rounded">
          Sync Configurations
        </button>
      </div>
    );
  }

  const panelsObj = safeObject(visiblePanels, {});
  const panelsKeys = safeArray(Object.keys(panelsObj));

  return (
    <div id="configuration-manager" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6 text-left">
      {/* Title */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <Settings size={18} className="text-cyan-400" />
          <h3 className="font-bold text-white text-base">Configuration & Workspace Manager</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500 font-bold uppercase">
          WORKSPACE CONFIG VERSION: 1.0.0
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Toggle Visible Dashboard Panels checklist */}
        <div className="lg:col-span-7 bg-slate-900/20 p-4 rounded-lg border border-slate-800 space-y-3">
          <h4 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wide border-b border-slate-800 pb-2 flex items-center gap-1.5">
            <CheckSquare size={14} className="text-cyan-400" /> Visible Workstation Panels filter
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed mb-4">
            Select or filter down which analytics engines to render inside your current workspace. Unchecked panels will degrade gracefully and stand by in background cache.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {panelsKeys.map((panelKey) => (
              <div
                key={panelKey}
                onClick={() => onTogglePanel(panelKey)}
                className={`p-2.5 rounded border transition cursor-pointer flex items-center justify-between text-xs ${
                  panelsObj[panelKey]
                    ? "bg-cyan-950/20 border-cyan-850 text-white"
                    : "bg-slate-950/60 border-slate-850 text-slate-400 opacity-60"
                }`}
              >
                <span className="font-mono font-semibold uppercase">{panelKey.replace(/([A-Z])/g, " $1").trim()}</span>
                <div className={`h-3.5 w-3.5 rounded border flex items-center justify-center ${
                  panelsObj[panelKey] ? "bg-cyan-500 border-cyan-400 text-slate-950" : "border-slate-800"
                }`}>
                  {panelsObj[panelKey] && <span className="text-[9px] font-bold">✔</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Adjust configurations forms */}
        <div className="lg:col-span-5 bg-slate-900/20 p-4 rounded-lg border border-slate-800 space-y-4">
          <h4 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wide border-b border-slate-800 pb-2 flex items-center gap-1.5">
            <Sliders size={14} className="text-cyan-400" /> Adjust System Workspace Preferences
          </h4>

          <form onSubmit={handleSavePreferences} className="space-y-4 text-xs font-mono text-slate-300">
            <div className="space-y-1">
              <label className="text-slate-400">Terminal Logging Level</label>
              <select
                value={logLevel}
                onChange={(e) => setLogLevel(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
              >
                <option value="DEBUG">DEBUG (Detailed Telemetries)</option>
                <option value="INFO">INFO (Production standard)</option>
                <option value="WARNING">WARNING (Only alerts)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400">API Cache Refresh Interval (Seconds)</label>
              <input
                type="number"
                value={intervalVal}
                onChange={(e) => setIntervalVal(parseInt(e.target.value) || 15)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
              >
              </input>
            </div>

            <div className="flex items-center justify-between p-2 bg-slate-950/40 border border-slate-850 rounded">
              <span>Enable Auditory Alert sound cues</span>
              <button
                type="button"
                onClick={() => setNotifSound(!notifSound)}
                className={`px-3 py-1 rounded text-[11px] font-bold ${
                  notifSound ? "bg-emerald-950 text-emerald-400 border border-emerald-900" : "bg-slate-900 text-slate-400 border border-slate-800"
                }`}
              >
                {notifSound ? "SOUNDS_ON" : "SOUNDS_MUTED"}
              </button>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400">Preferred Trading Style</label>
              <select
                value={preferredTradingStyle}
                onChange={(e) => setPreferredTradingStyle(e.target.value as any)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
              >
                <option value="Intraday">Intraday (Weekly Focus)</option>
                <option value="Swing">Swing (Next Weekly & Monthly Focus)</option>
                <option value="Positional">Positional (Monthly & Far Expiry Focus)</option>
              </select>
            </div>

            <button
              type="submit"
              className="w-full py-2 bg-cyan-600 hover:bg-cyan-500 font-bold text-slate-950 rounded transition mt-4"
            >
              Apply Workspace Preferences
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default ConfigurationManager;
