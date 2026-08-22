// src/frontend/components/settings/SettingsWorkspace.tsx
import React, { useState } from "react";
import {
  KeyRound,
  Radio,
  Newspaper,
  Cpu,
  Activity,
  Calendar,
  ChevronDown,
  CheckCircle2,
  AlertCircle,
  Download,
} from "lucide-react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import {
  getCanonicalSettingsPresentation,
  UserPreferencesState,
  NotificationSettingsState,
  saveStoredPreferences,
  saveStoredNotifications,
  DEFAULT_USER_PREFERENCES,
} from "../../utils/canonicalSettingsAdapter";
import { AdvancedDiagnosticsDrawer } from "./AdvancedDiagnosticsDrawer";
import { ArdhaPerformancePanel } from "./ArdhaPerformancePanel";

export type SettingsSubTab =
  | "overview"
  | "workspace"
  | "connections"
  | "ai_engines"
  | "notifications"
  | "safety"
  | "system"
  | "advanced"
  | "preferences"
  | "diagnostics"
  | "about";

export function SettingsWorkspace({
  onBack,
}: {
  subTab?: SettingsSubTab;
  onSelectSubTab?: (tab: SettingsSubTab) => void;
  onBack?: () => void;
}) {
  const {
    canonicalState,
    lastValidState,
    workspaceContext,
    syncBroker,
    niftyModeOverride,
    setNiftyModeOverride,
    setIntelligenceSubTabOverride,
  } = useWorkstationState() as any;

  const state = canonicalState ?? lastValidState ?? {};
  const pres = getCanonicalSettingsPresentation(state, workspaceContext);

  // Local preferences & notifications state with instant persistence
  const [prefs, setPrefs] = useState<UserPreferencesState>(pres.preferences);
  const [notifs, setNotifs] = useState<NotificationSettingsState>(pres.notifications);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [brokerMessage, setBrokerMessage] = useState<string | null>(null);
  const [showConfirmReset, setShowConfirmReset] = useState(false);
  const [advancedExpanded, setAdvancedExpanded] = useState(false);
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);
  const [showPerformancePanel, setShowPerformancePanel] = useState(false);

  const handlePrefChange = (key: keyof UserPreferencesState, value: any) => {
    const updated = { ...prefs, [key]: value };
    setPrefs(updated);
    saveStoredPreferences(updated);
    setSaveMessage("Preferences saved.");
    setTimeout(() => setSaveMessage(null), 3000);
  };

  const handleResetPreferences = () => {
    setPrefs(DEFAULT_USER_PREFERENCES);
    saveStoredPreferences(DEFAULT_USER_PREFERENCES);
    setShowConfirmReset(false);
    setSaveMessage("Local UI preferences reset to defaults.");
    setTimeout(() => setSaveMessage(null), 3000);
  };

  const handleNotificationToggle = (key: keyof Omit<NotificationSettingsState, "browserPermission">) => {
    const updated = { ...notifs, [key]: !notifs[key] };
    setNotifs(updated);
    saveStoredNotifications(updated);
    setSaveMessage("Alert settings updated.");
    setTimeout(() => setSaveMessage(null), 3000);
  };

  const handleRequestBrowserPermission = async () => {
    if (typeof window !== "undefined" && "Notification" in window) {
      try {
        const perm = await Notification.requestPermission();
        const updated = { ...notifs, browserPermission: perm as any };
        setNotifs(updated);
        saveStoredNotifications(updated);
      } catch (e: any) {
        setSaveMessage("Permission error: " + e.message);
      }
    }
  };

  const handleOAuthConnect = async () => {
    try {
      setBrokerMessage("Redirecting to official Zerodha OAuth login...");
      const res = await fetch("/api/broker/login-url");
      const body = await res.json();
      if (body && body.login_url) {
        window.location.href = body.login_url;
      } else {
        setBrokerMessage(body.error || "Failed to generate Zerodha login URL.");
      }
    } catch (err: any) {
      setBrokerMessage(err.message || "OAuth initiation failed.");
    }
  };

  const handleBrokerDisconnect = async () => {
    try {
      setBrokerMessage("Disconnecting broker session...");
      await fetch("/api/broker/logout", { method: "POST" });
      if (syncBroker) await syncBroker(true);
      setBrokerMessage("Broker session disconnected.");
      setTimeout(() => setBrokerMessage(null), 4000);
    } catch (err: any) {
      setBrokerMessage(err.message || "Disconnect failed.");
    }
  };

  const handleExportDiagnostics = () => {
    const diag = pres.diagnostics;
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

  const isBrokerConnected = pres.brokerState.status === "CONNECTED";
  const marketSession = pres.diagnostics.marketSession;
  const isMarketOpen = marketSession === "OPEN";

  return (
    <div id="settings-workspace" className="w-full max-w-[960px] mx-auto space-y-6 font-sans text-left pb-12 text-[11px]">
      {/* ── 1. PAGE HEADER (Clean title + subtitle only) ── */}
      <div className="border-b border-[#191D23] pb-3">
        <h1 className="text-[20px] font-bold text-[#E6E8EB] tracking-tight">SETTINGS</h1>
        <p className="text-[11px] text-[#707987] font-mono mt-0.5">
          Workspace preferences, connections and alerts.
        </p>
      </div>

      {/* Save Notification Toast / Banner */}
      {saveMessage && (
        <div className="p-2.5 bg-[#00C896]/10 border border-[#00C896]/30 text-[#00C896] rounded font-mono text-[9.5px] font-bold flex items-center gap-1.5">
          <CheckCircle2 size={13} />
          {saveMessage}
        </div>
      )}

      {/* Broker Action Message */}
      {brokerMessage && (
        <div className="p-2.5 bg-[#38BDF8]/10 border border-[#38BDF8]/30 text-[#38BDF8] rounded font-mono text-[9.5px] font-bold">
          {brokerMessage}
        </div>
      )}

      {/* ======================================================== */}
      {/* SECTION 1: GENERAL                                       */}
      {/* ======================================================== */}
      <section className="space-y-2">
        <h2 className="text-[13px] font-bold text-[#E6E8EB] uppercase tracking-wide font-mono">GENERAL</h2>
        <div className="bg-[#0B0D10] border border-[#191D23] rounded-[3px] p-4 divide-y divide-[#191D23] font-mono text-[11px]">
          {/* TIME FORMAT */}
          <div className="flex items-center justify-between py-3">
            <div>
              <div className="font-medium text-[#E6E8EB]">Time Format</div>
              <div className="text-[10px] text-[#707987]">Display format for all timestamped events and market feeds</div>
            </div>
            <div className="flex items-center gap-1 bg-[#0E1013] p-1 rounded border border-[#191D23]">
              <button
                onClick={() => handlePrefChange("timeFormat", "12h")}
                className={`px-3 py-1 rounded text-[10px] font-bold transition ${
                  prefs.timeFormat === "12h"
                    ? "bg-[#38BDF8] text-[#050607]"
                    : "text-[#707987] hover:text-[#E6E8EB]"
                }`}
              >
                12-Hour
              </button>
              <button
                onClick={() => handlePrefChange("timeFormat", "24h")}
                className={`px-3 py-1 rounded text-[10px] font-bold transition ${
                  prefs.timeFormat === "24h"
                    ? "bg-[#38BDF8] text-[#050607]"
                    : "text-[#707987] hover:text-[#E6E8EB]"
                }`}
              >
                24-Hour
              </button>
            </div>
          </div>

          {/* NUMBER FORMAT */}
          <div className="flex items-center justify-between py-3">
            <div>
              <div className="font-medium text-[#E6E8EB]">Number Format</div>
              <div className="text-[10px] text-[#707987]">Currency, volume, and open interest numerical scaling</div>
            </div>
            <div className="flex items-center gap-1 bg-[#0E1013] p-1 rounded border border-[#191D23]">
              <button
                onClick={() => handlePrefChange("numberFormat", "IN")}
                className={`px-3 py-1 rounded text-[10px] font-bold transition ${
                  prefs.numberFormat === "IN"
                    ? "bg-[#00C896] text-[#050607]"
                    : "text-[#707987] hover:text-[#E6E8EB]"
                }`}
              >
                Indian (Lakhs/Cr)
              </button>
              <button
                onClick={() => handlePrefChange("numberFormat", "INTL")}
                className={`px-3 py-1 rounded text-[10px] font-bold transition ${
                  prefs.numberFormat === "INTL"
                    ? "bg-[#00C896] text-[#050607]"
                    : "text-[#707987] hover:text-[#E6E8EB]"
                }`}
              >
                International (M/B)
              </button>
            </div>
          </div>

          {/* DEFAULT LANDING WORKSPACE */}
          <div className="flex items-center justify-between py-3">
            <div>
              <div className="font-medium text-[#E6E8EB]">Default Landing Workspace</div>
              <div className="text-[10px] text-[#707987]">Initial workspace presented upon opening AIR Ardha</div>
            </div>
            <div className="flex items-center gap-1 bg-[#0E1013] p-1 rounded border border-[#191D23]">
              {[
                { id: "market", label: "Market" },
                { id: "intelligence", label: "Market Intelligence" },
                { id: "news", label: "News & Updates" },
                { id: "portfolio", label: "Portfolio" },
              ].map((ws) => (
                <button
                  key={ws.id}
                  onClick={() => handlePrefChange("defaultWorkspace", ws.id)}
                  className={`px-2.5 py-1 rounded text-[10px] font-bold transition ${
                    prefs.defaultWorkspace === ws.id
                      ? "bg-[#8B5CF6] text-white"
                      : "text-[#707987] hover:text-[#E6E8EB]"
                  }`}
                >
                  {ws.label}
                </button>
              ))}
            </div>
          </div>

          {/* DEFAULT MARKET VIEW */}
          <div className="flex items-center justify-between py-3">
            <div>
              <div className="font-medium text-[#E6E8EB]">Default Market View</div>
              <div className="text-[10px] text-[#707987]">Primary sub-tab when navigating to Market workspace</div>
            </div>
            <div className="flex items-center gap-1 bg-[#0E1013] p-1 rounded border border-[#191D23]">
              {(["nifty", "metrics", "options"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => handlePrefChange("defaultMarketTab", tab)}
                  className={`px-3 py-1 rounded text-[10px] font-bold capitalize transition ${
                    prefs.defaultMarketTab === tab
                      ? "bg-[#38BDF8] text-[#050607]"
                      : "text-[#707987] hover:text-[#E6E8EB]"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* SECTION 2: CONNECTIONS                                   */}
      {/* ======================================================== */}
      <section className="space-y-2">
        <h2 className="text-[13px] font-bold text-[#E6E8EB] uppercase tracking-wide font-mono">CONNECTIONS</h2>
        <div className="bg-[#0B0D10] border border-[#191D23] rounded-[3px] p-4 divide-y divide-[#191D23] font-mono text-[11px]">
          {/* 1. Zerodha KiteConnect */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <KeyRound size={16} className="text-[#38BDF8] shrink-0" />
              <div>
                <div className="font-medium text-[#E6E8EB]">Zerodha KiteConnect</div>
                <div className="text-[10px] text-[#707987]">Broker connection &amp; session authorization</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                  isBrokerConnected
                    ? "bg-[#00C896]/20 text-[#00C896]"
                    : "bg-[#E5484D]/20 text-[#E5484D]"
                }`}
              >
                {isBrokerConnected ? "CONNECTED" : "DISCONNECTED"}
              </span>
              {isBrokerConnected ? (
                <button
                  onClick={handleBrokerDisconnect}
                  className="px-3 py-1 bg-[#191D23] hover:bg-[#E5484D]/20 hover:text-[#E5484D] border border-[#242830] text-[#707987] font-bold rounded text-[10px] transition"
                >
                  Manage
                </button>
              ) : (
                <button
                  onClick={handleOAuthConnect}
                  className="px-3 py-1 bg-[#38BDF8] text-[#050607] hover:bg-[#7DD3FC] font-bold rounded text-[10px] transition"
                >
                  Authenticate Broker
                </button>
              )}
            </div>
          </div>

          {/* 2. Market Data */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <Radio size={16} className="text-[#00C896] shrink-0" />
              <div>
                <div className="font-medium text-[#E6E8EB]">Market Data</div>
                <div className="text-[10px] text-[#707987]">NIFTY Spot &amp; constituent breadth telemetry</div>
              </div>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                isMarketOpen ? "bg-[#00C896]/20 text-[#00C896]" : "bg-[#38BDF8]/20 text-[#38BDF8]"
              }`}
            >
              {isMarketOpen ? "LIVE" : "READY"}
            </span>
          </div>

          {/* 3. Options Data */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <Activity size={16} className="text-[#38BDF8] shrink-0" />
              <div>
                <div className="font-medium text-[#E6E8EB]">Options Data</div>
                <div className="text-[10px] text-[#707987]">NIFTY Option Chain Matrix &amp; OI depth stream</div>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-[#00C896]/20 text-[#00C896]">
              HEALTHY
            </span>
          </div>

          {/* 4. News Engine */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <Newspaper size={16} className="text-[#8B5CF6] shrink-0" />
              <div>
                <div className="font-medium text-[#E6E8EB]">News Engine</div>
                <div className="text-[10px] text-[#707987]">Financial news pipeline &amp; official source feeds</div>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-[#00C896]/20 text-[#00C896]">
              HEALTHY
            </span>
          </div>

          {/* 5. Macro Calendar */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <Calendar size={16} className="text-[#E59700] shrink-0" />
              <div>
                <div className="font-medium text-[#E6E8EB]">Macro Calendar</div>
                <div className="text-[10px] text-[#707987]">Economic events &amp; institutional flow telemetry</div>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-[#00C896]/20 text-[#00C896]">
              HEALTHY
            </span>
          </div>

          {/* 6. AI Assistant */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <Cpu size={16} className="text-[#38BDF8] shrink-0" />
              <div>
                <div className="font-medium text-[#E6E8EB]">AI Assistant</div>
                <div className="text-[10px] text-[#707987]">Deterministic engine &amp; GPT-4o reasoning synthesis</div>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-[#38BDF8]/20 text-[#38BDF8]">
              READY
            </span>
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* SECTION 3: NOTIFICATIONS                                 */}
      {/* ======================================================== */}
      <section className="space-y-2">
        <h2 className="text-[13px] font-bold text-[#E6E8EB] uppercase tracking-wide font-mono">NOTIFICATIONS</h2>

        {/* Compact Inline Amber Banner for Browser Permission */}
        {notifs.browserPermission !== "granted" && notifs.browserPermission !== "unsupported" && (
          <div className="p-2.5 bg-[#E59700]/10 border border-[#E59700]/30 rounded-[3px] text-[#E59700] font-mono text-[10px] flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <AlertCircle size={14} className="shrink-0" />
              Desktop notification permission required.
            </span>
            <button
              onClick={handleRequestBrowserPermission}
              className="px-3 py-1 bg-[#E59700] text-[#050607] font-bold rounded text-[10px] transition shrink-0 ml-2"
            >
              Enable
            </button>
          </div>
        )}

        <div className="bg-[#0B0D10] border border-[#191D23] rounded-[3px] p-4 divide-y divide-[#191D23] font-mono text-[11px]">
          {/* 1. HIGH IMPACT MARKET NEWS */}
          <div className="flex items-center justify-between py-3">
            <div className="pr-3">
              <div className="font-medium text-[#E6E8EB]">HIGH IMPACT MARKET NEWS</div>
              <div className="text-[10px] text-[#707987]">Alert when significant market-moving stories occur.</div>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={notifs.highImpactNewsAlerts}
              onClick={() => handleNotificationToggle("highImpactNewsAlerts")}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                notifs.highImpactNewsAlerts ? "bg-[#00C896]" : "bg-[#191D23]"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-[#E6E8EB] shadow ring-0 transition duration-200 ease-in-out ${
                  notifs.highImpactNewsAlerts ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </button>
          </div>

          {/* 2. MARKET OPEN / CLOSE */}
          <div className="flex items-center justify-between py-3">
            <div className="pr-3">
              <div className="font-medium text-[#E6E8EB]">MARKET OPEN / CLOSE</div>
              <div className="text-[10px] text-[#707987]">Notify on important session transitions.</div>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={notifs.marketOpenCloseAlerts}
              onClick={() => handleNotificationToggle("marketOpenCloseAlerts")}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                notifs.marketOpenCloseAlerts ? "bg-[#00C896]" : "bg-[#191D23]"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-[#E6E8EB] shadow ring-0 transition duration-200 ease-in-out ${
                  notifs.marketOpenCloseAlerts ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </button>
          </div>

          {/* 3. BROKER SESSION ALERTS */}
          <div className="flex items-center justify-between py-3">
            <div className="pr-3">
              <div className="font-medium text-[#E6E8EB]">BROKER SESSION ALERTS</div>
              <div className="text-[10px] text-[#707987]">Session expiry/disconnection warnings.</div>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={notifs.brokerDisconnectAlerts}
              onClick={() => handleNotificationToggle("brokerDisconnectAlerts")}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                notifs.brokerDisconnectAlerts ? "bg-[#00C896]" : "bg-[#191D23]"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-[#E6E8EB] shadow ring-0 transition duration-200 ease-in-out ${
                  notifs.brokerDisconnectAlerts ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </button>
          </div>

          {/* 4. MACRO EVENT REMINDERS */}
          <div className="flex items-center justify-between py-3">
            <div className="pr-3">
              <div className="font-medium text-[#E6E8EB]">MACRO EVENT REMINDERS</div>
              <div className="text-[10px] text-[#707987]">Upcoming high-impact economic events.</div>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={notifs.economicEventReminders}
              onClick={() => handleNotificationToggle("economicEventReminders")}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                notifs.economicEventReminders ? "bg-[#00C896]" : "bg-[#191D23]"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-[#E6E8EB] shadow ring-0 transition duration-200 ease-in-out ${
                  notifs.economicEventReminders ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </button>
          </div>

          {/* 5. SYSTEM WARNINGS */}
          <div className="flex items-center justify-between py-3">
            <div className="pr-3">
              <div className="font-medium text-[#E6E8EB]">SYSTEM WARNINGS</div>
              <div className="text-[10px] text-[#707987]">Feed degradation and telemetry warnings.</div>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={notifs.systemHealthWarnings}
              onClick={() => handleNotificationToggle("systemHealthWarnings")}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                notifs.systemHealthWarnings ? "bg-[#00C896]" : "bg-[#191D23]"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-[#E6E8EB] shadow ring-0 transition duration-200 ease-in-out ${
                  notifs.systemHealthWarnings ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* SECTION 4: ADVANCED (Collapsed by default disclosure)    */}
      {/* ======================================================== */}
      <section className="bg-[#0B0D10] border border-[#191D23] rounded-[3px] overflow-hidden">
        <button
          onClick={() => setAdvancedExpanded(!advancedExpanded)}
          className="w-full flex items-center justify-between p-4 text-left font-mono hover:bg-[#12151A] transition cursor-pointer"
        >
          <div>
            <div className="text-[13px] font-bold text-[#E6E8EB] uppercase tracking-wide">ADVANCED</div>
            <div className="text-[10px] text-[#707987]">Diagnostics, QA controls and reset options</div>
          </div>
          <ChevronDown
            className={`transform transition-transform ${advancedExpanded ? "rotate-180 text-[#38BDF8]" : "text-[#707987]"}`}
            size={16}
          />
        </button>

        {advancedExpanded && (
          <div className="p-4 border-t border-[#191D23] space-y-4 font-mono text-[11px]">
            {/* Technical System Snapshot */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[9px] text-[#707987] bg-[#0E1013] p-3 rounded border border-[#191D23]">
              <div>Runtime ID: <span className="text-[#38BDF8] font-bold">{pres.diagnostics.runtimeId}</span></div>
              <div>State Sequence: <span className="text-[#E6E8EB] font-bold">#{pres.diagnostics.stateSequence}</span></div>
              <div>Environment: <span className="text-[#E59700] font-bold uppercase">{pres.environment}</span></div>
              <div>Session: <span className="text-[#00C896] font-bold uppercase">{pres.diagnostics.marketSession}</span></div>
              <div>Last Sync: <span className="text-[#E6E8EB]">{pres.lastUpdatedIst}</span></div>
              <div>Version: <span className="text-[#38BDF8] font-bold">{pres.version}</span></div>
            </div>

            {/* Action Buttons Group */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 border-t border-[#191D23]">
              <button
                onClick={() => setIsDiagnosticsOpen(true)}
                className="px-3 py-2 bg-[#38BDF8]/15 hover:bg-[#38BDF8]/25 border border-[#38BDF8]/30 text-[#38BDF8] font-bold rounded text-[10px] transition flex items-center justify-center gap-1.5"
              >
                <Activity size={13} />
                Open Diagnostics
              </button>
              <button
                onClick={() => setShowPerformancePanel(!showPerformancePanel)}
                className="px-3 py-2 bg-[#8B5CF6]/15 hover:bg-[#8B5CF6]/25 border border-[#8B5CF6]/30 text-[#8B5CF6] font-bold rounded text-[10px] transition flex items-center justify-center gap-1.5"
              >
                <Activity size={13} />
                View Performance
              </button>
              <button
                onClick={handleExportDiagnostics}
                className="px-3 py-2 bg-[#191D23] hover:bg-[#242830] border border-[#242830] text-[#E6E8EB] font-bold rounded text-[10px] transition flex items-center justify-center gap-1.5"
              >
                <Download size={13} />
                Export JSON
              </button>
            </div>

            {/* STAGING QA CONTROLS (STAGING ONLY) */}
            {pres.environment === "STAGING" && (
              <div className="p-3 bg-[#0E1013] border border-[#E59700]/30 rounded space-y-2">
                <div className="flex items-center justify-between text-[9px]">
                  <span className="font-bold text-[#E59700] uppercase">STAGING QA SESSION CONTROLS</span>
                  <span className="text-[#E59700] bg-[#E59700]/10 border border-[#E59700]/30 px-1.5 py-0.5 rounded font-bold">STAGING ONLY</span>
                </div>
                <div className="grid grid-cols-4 gap-1.5">
                  {(["auto", "pre_market", "live", "post_market"] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => handleStagingSessionClick(mode)}
                      className={`px-2 py-1 rounded text-[9px] font-bold uppercase transition text-center ${
                        (niftyModeOverride || "auto") === mode ? "bg-[#E59700] text-[#050607]" : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                      }`}
                    >
                      {mode.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* RESET UI PREFERENCES */}
            <div className="p-3 bg-[#0E1013] border border-[#191D23] rounded flex items-center justify-between">
              <div>
                <div className="font-bold text-[#E6E8EB] text-[11px]">RESET UI PREFERENCES</div>
                <div className="text-[9px] text-[#707987]">Restores UI settings to defaults without altering broker/session/backend data.</div>
              </div>
              {!showConfirmReset ? (
                <button
                  onClick={() => setShowConfirmReset(true)}
                  className="px-3 py-1.5 bg-[#191D23] hover:bg-[#242830] border border-[#242830] text-[#707987] hover:text-[#E6E8EB] rounded text-[9.5px] font-bold transition shrink-0"
                >
                  Reset Defaults
                </button>
              ) : (
                <div className="flex items-center gap-1.5 shrink-0">
                  <button onClick={handleResetPreferences} className="px-2.5 py-1 bg-[#E5484D] text-white rounded text-[9px] font-bold transition">
                    Confirm Reset
                  </button>
                  <button onClick={() => setShowConfirmReset(false)} className="px-2 py-1 bg-[#191D23] text-[#707987] rounded text-[9px] font-bold transition">
                    Cancel
                  </button>
                </div>
              )}
            </div>

            {/* Embedded Ardha Performance Panel if toggled */}
            {showPerformancePanel && (
              <div className="p-3 bg-[#0E1013] border border-[#191D23] rounded">
                <ArdhaPerformancePanel />
              </div>
            )}

            {/* Read-Only Safeguards Note */}
            <div className="text-[8.5px] text-[#707987] pt-1 border-t border-[#191D23]">
              Read-only safeguards active. Order placement, paper trading, and broker mutations are hard-disabled at the architecture level.
            </div>
          </div>
        )}
      </section>

      {/* ── ADVANCED DIAGNOSTICS DRAWER OVERLAY ── */}
      <AdvancedDiagnosticsDrawer
        pres={pres}
        isOpen={isDiagnosticsOpen}
        onClose={() => setIsDiagnosticsOpen(false)}
      />
    </div>
  );
}

export default SettingsWorkspace;
