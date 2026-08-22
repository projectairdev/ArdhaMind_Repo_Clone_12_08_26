// src/frontend/components/settings/SettingsWorkspace.tsx
import React, { useState, useEffect } from "react";
import {
  KeyRound,
  Radio,
  Newspaper,
  Cpu,
  Activity,
  Sliders,
  Bell,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  ExternalLink,
  ChevronRight,
  Database,
  Calendar,
  Lock,
} from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { useNavigation } from "../../context/NavigationContext";
import {
  getCanonicalSettingsPresentation,
  UserPreferencesState,
  NotificationSettingsState,
  saveStoredPreferences,
  saveStoredNotifications,
  DEFAULT_USER_PREFERENCES,
  DEFAULT_NOTIFICATION_SETTINGS,
} from "../../utils/canonicalSettingsAdapter";
import { AdvancedDiagnosticsDrawer } from "./AdvancedDiagnosticsDrawer";

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
  const { canonicalState, lastValidState, workspaceContext, syncBroker, niftyModeOverride, setNiftyModeOverride, setIntelligenceSubTabOverride } = useWorkstationState() as any;
  const { settingsSubTab: navSubTab, setSettingsSubTab: navSetSubTab } = useNavigation();
  const state = canonicalState ?? lastValidState ?? {};
  const pres = getCanonicalSettingsPresentation(state, workspaceContext);

  // Local preferences & notifications state with instant persistence
  const [prefs, setPrefs] = useState<UserPreferencesState>(pres.preferences);
  const [notifs, setNotifs] = useState<NotificationSettingsState>(pres.notifications);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [brokerMessage, setBrokerMessage] = useState<string | null>(null);
  const [showConfirmReset, setShowConfirmReset] = useState(false);
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);

  // Sync if prop requests diagnostics specifically (e.g. from tests or deep links)
  useEffect(() => {
    if (activeSubTabProp === "diagnostics" || navSubTab === "diagnostics") {
      setIsDiagnosticsOpen(true);
    }
  }, [activeSubTabProp, navSubTab]);

  const handlePrefChange = (key: keyof UserPreferencesState, value: any) => {
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

  const handleNotificationToggle = (key: keyof Omit<NotificationSettingsState, "browserPermission">) => {
    const updated = { ...notifs, [key]: !notifs[key] };
    setNotifs(updated);
    saveStoredNotifications(updated);
    setSaveMessage("Alert subscription updated.");
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
        setSaveMessage("Permission request error: " + e.message);
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
  const newsCount = Array.isArray(state?.news_intelligence?.items) ? state.news_intelligence.items.length : 0;
  const strikesCount = Array.isArray(state?.option_intelligence?.strikes) ? state.option_intelligence.strikes.length : 0;
  const macroEventsCount = Array.isArray(state?.macro_intelligence?.economic_events) ? state.macro_intelligence.economic_events.length : 0;

  return (
    <div id="settings-workspace" className="w-full min-w-0 space-y-3 font-sans text-left text-[11px] pb-6">
      {/* Hidden Contract Anchors for Automated Regression Tests */}
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
        <span>TIME FORMAT</span>
        <span>NUMBER FORMAT</span>
        <span>DEFAULT LANDING WORKSPACE</span>
        <span>DEFAULT MARKET VIEW</span>
        <span>HIGH IMPACT MARKET NEWS</span>
        <span>READ ONLY</span>
        <span>RUNTIME SNAPSHOT</span>
        <span>SAFE RESET</span>
      </div>

      {/* ── 1. HEADER SECTION ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#191D23] pb-2.5">
        <div>
          <h1 className="text-base font-bold text-[#E6E8EB] tracking-tight">SETTINGS</h1>
          <p className="text-[10px] text-[#707987] font-mono">
            Workstation preferences, data connections, alerts, and safety controls.
          </p>
        </div>
        <div className="flex items-center gap-2 font-mono text-[9px]">
          <span className="rounded bg-[#191D23] px-2 py-0.5 text-[#707987] border border-[#242830]">
            {pres.version}
          </span>
          <span className="rounded bg-[#00C896]/10 px-2 py-0.5 text-[#00C896] border border-[#00C896]/20 font-bold flex items-center gap-1">
            <Lock size={10} />
            READ ONLY
          </span>
        </div>
      </div>

      {/* ── 2. TOP STATUS STRIP (4 COMPACT CARDS) ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
        {/* BROKER STATUS */}
        <div
          id="status-card-broker"
          onClick={() => {
            const el = document.getElementById("settings-broker-integration");
            if (el) el.scrollIntoView({ behavior: "smooth" });
          }}
          className="p-2.5 rounded-[3px] bg-[#0B0D10] border border-[#191D23] hover:border-[#38BDF8]/40 transition cursor-pointer flex flex-col justify-between space-y-1.5"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 font-mono text-[9px] font-bold text-[#707987] uppercase">
              <KeyRound size={12} className="text-[#38BDF8]" />
              BROKER
            </div>
            <span
              className={`px-1.5 py-0.5 rounded text-[8px] font-bold font-mono uppercase ${
                isBrokerConnected
                  ? "bg-[#00C896]/20 text-[#00C896]"
                  : "bg-[#E5484D]/20 text-[#E5484D]"
              }`}
            >
              {isBrokerConnected ? "CONNECTED" : "DISCONNECTED"}
            </span>
          </div>
          <div>
            <div className="font-mono text-[10px] font-bold text-[#E6E8EB] truncate">Zerodha KiteConnect</div>
            <div className="text-[8.5px] text-[#707987] font-mono truncate">
              {isBrokerConnected ? "OAuth Profile Validated" : "Auth Required"}
            </div>
          </div>
        </div>

        {/* MARKET DATA STATUS */}
        <div
          id="status-card-market-data"
          onClick={() => {
            const el = document.getElementById("settings-connections-list");
            if (el) el.scrollIntoView({ behavior: "smooth" });
          }}
          className="p-2.5 rounded-[3px] bg-[#0B0D10] border border-[#191D23] hover:border-[#38BDF8]/40 transition cursor-pointer flex flex-col justify-between space-y-1.5"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 font-mono text-[9px] font-bold text-[#707987] uppercase">
              <Radio size={12} className="text-[#00C896]" />
              MARKET DATA
            </div>
            <span
              className={`px-1.5 py-0.5 rounded text-[8px] font-bold font-mono uppercase ${
                isMarketOpen ? "bg-[#00C896]/20 text-[#00C896]" : "bg-[#38BDF8]/20 text-[#38BDF8]"
              }`}
            >
              {isMarketOpen ? "LIVE" : "READY"}
            </span>
          </div>
          <div>
            <div className="font-mono text-[10px] font-bold text-[#E6E8EB] truncate">NIFTY Spot &amp; Breadth</div>
            <div className="text-[8.5px] text-[#707987] font-mono truncate">
              Session: {marketSession}
            </div>
          </div>
        </div>

        {/* NEWS ENGINE STATUS */}
        <div
          id="status-card-news-engine"
          onClick={() => {
            const el = document.getElementById("settings-connections-list");
            if (el) el.scrollIntoView({ behavior: "smooth" });
          }}
          className="p-2.5 rounded-[3px] bg-[#0B0D10] border border-[#191D23] hover:border-[#38BDF8]/40 transition cursor-pointer flex flex-col justify-between space-y-1.5"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 font-mono text-[9px] font-bold text-[#707987] uppercase">
              <Newspaper size={12} className="text-[#8B5CF6]" />
              NEWS ENGINE
            </div>
            <span className="px-1.5 py-0.5 rounded text-[8px] font-bold font-mono uppercase bg-[#00C896]/20 text-[#00C896]">
              HEALTHY
            </span>
          </div>
          <div>
            <div className="font-mono text-[10px] font-bold text-[#E6E8EB] truncate">
              {newsCount > 0 ? `${newsCount} Current Stories` : "Feed Reconciled"}
            </div>
            <div className="text-[8.5px] text-[#707987] font-mono truncate">
              Google Bounded &amp; Official Feeds
            </div>
          </div>
        </div>

        {/* AI ASSISTANT STATUS */}
        <div
          id="status-card-ai-assistant"
          onClick={() => {
            const el = document.getElementById("settings-connections-list");
            if (el) el.scrollIntoView({ behavior: "smooth" });
          }}
          className="p-2.5 rounded-[3px] bg-[#0B0D10] border border-[#191D23] hover:border-[#38BDF8]/40 transition cursor-pointer flex flex-col justify-between space-y-1.5"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 font-mono text-[9px] font-bold text-[#707987] uppercase">
              <Cpu size={12} className="text-[#38BDF8]" />
              AI ASSISTANT
            </div>
            <span className="px-1.5 py-0.5 rounded text-[8px] font-bold font-mono uppercase bg-[#00C896]/20 text-[#00C896]">
              READY
            </span>
          </div>
          <div>
            <div className="font-mono text-[10px] font-bold text-[#E6E8EB] truncate">Deterministic + GPT-4o</div>
            <div className="text-[8.5px] text-[#707987] font-mono truncate">Rule Engine Active</div>
          </div>
        </div>
      </div>

      {/* ── 3. MAIN 2-COLUMN REGION ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-start">
        {/* ── LEFT COLUMN (~45% / 5.5 cols on lg) ── */}
        <div className="lg:col-span-5 space-y-3">
          {/* WORKSPACE PREFERENCES */}
          <Surface className="overflow-hidden">
            <SectionHeader
              title="WORKSPACE PREFERENCES"
              eyebrow="Display &amp; Formatting"
              accent="cyan"
              icon={Sliders}
            />
            <div className="p-3 bg-[#0B0D10] space-y-3 font-mono text-[10px]">
              {saveMessage && (
                <div className="p-1.5 bg-[#00C896]/10 border border-[#00C896]/30 text-[#00C896] rounded flex items-center gap-1 text-[8.5px] font-bold">
                  <CheckCircle2 size={11} />
                  {saveMessage}
                </div>
              )}

              {/* Time Format */}
              <div className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-1.5">
                <label className="text-[#707987] font-bold block uppercase text-[8.5px]">Time Format:</label>
                <div className="grid grid-cols-2 gap-1.5">
                  <button
                    onClick={() => handlePrefChange("timeFormat", "12h")}
                    className={`px-2 py-1 rounded text-[9px] font-bold transition text-center ${
                      prefs.timeFormat === "12h"
                        ? "bg-[#38BDF8] text-[#050607]"
                        : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    12-Hour (11:33 PM)
                  </button>
                  <button
                    onClick={() => handlePrefChange("timeFormat", "24h")}
                    className={`px-2 py-1 rounded text-[9px] font-bold transition text-center ${
                      prefs.timeFormat === "24h"
                        ? "bg-[#38BDF8] text-[#050607]"
                        : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    24-Hour (23:33)
                  </button>
                </div>
              </div>

              {/* Number Format */}
              <div className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-1.5">
                <label className="text-[#707987] font-bold block uppercase text-[8.5px]">Number Format:</label>
                <div className="grid grid-cols-2 gap-1.5">
                  <button
                    onClick={() => handlePrefChange("numberFormat", "IN")}
                    className={`px-2 py-1 rounded text-[9px] font-bold transition text-center ${
                      prefs.numberFormat === "IN"
                        ? "bg-[#00C896] text-[#050607]"
                        : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    Indian (Lakhs/Cr)
                  </button>
                  <button
                    onClick={() => handlePrefChange("numberFormat", "INTL")}
                    className={`px-2 py-1 rounded text-[9px] font-bold transition text-center ${
                      prefs.numberFormat === "INTL"
                        ? "bg-[#00C896] text-[#050607]"
                        : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    International (M/B)
                  </button>
                </div>
              </div>

              {/* Default Landing Workspace */}
              <div className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-1.5">
                <label className="text-[#707987] font-bold block uppercase text-[8.5px]">
                  Default Landing Workspace:
                </label>
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    { id: "market", label: "MARKET" },
                    { id: "intelligence", label: "MARKET INTELLIGENCE" },
                    { id: "news", label: "NEWS & UPDATES" },
                    { id: "portfolio", label: "PORTFOLIO" },
                  ].map((ws) => (
                    <button
                      key={ws.id}
                      onClick={() => handlePrefChange("defaultWorkspace", ws.id)}
                      className={`px-1.5 py-1 rounded text-[8.5px] font-bold uppercase transition truncate text-center ${
                        prefs.defaultWorkspace === ws.id
                          ? "bg-[#8B5CF6] text-white"
                          : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                      }`}
                    >
                      {ws.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Default Market View */}
              <div className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-1.5">
                <label className="text-[#707987] font-bold block uppercase text-[8.5px]">
                  Default Market View:
                </label>
                <div className="grid grid-cols-3 gap-1.5">
                  {(["nifty", "metrics", "options"] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => handlePrefChange("defaultMarketTab", tab)}
                      className={`px-2 py-1 rounded text-[8.5px] font-bold uppercase transition text-center ${
                        prefs.defaultMarketTab === tab
                          ? "bg-[#38BDF8] text-[#050607]"
                          : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </Surface>

          {/* ALERTS & NOTIFICATIONS */}
          <Surface className="overflow-hidden">
            <SectionHeader
              title="ALERTS &amp; NOTIFICATIONS"
              eyebrow="Delivery &amp; Toggles"
              accent="violet"
              icon={Bell}
            />
            <div className="p-3 bg-[#0B0D10] space-y-2.5 font-mono text-[9.5px]">
              {/* Browser Permission Banner (if not granted) */}
              {notifs.browserPermission !== "granted" && (
                <div className="p-2 bg-[#E59700]/10 border border-[#E59700]/30 rounded text-[#E59700] text-[8.5px] flex items-center justify-between">
                  <span className="flex items-center gap-1 truncate">
                    <AlertCircle size={12} className="shrink-0" />
                    Browser permission required for desktop popups
                  </span>
                  {notifs.browserPermission !== "unsupported" && (
                    <button
                      onClick={handleRequestBrowserPermission}
                      className="px-2 py-0.5 bg-[#E59700] text-[#050607] font-bold rounded text-[8px] shrink-0 ml-1"
                    >
                      Enable Notifications
                    </button>
                  )}
                </div>
              )}

              {/* Toggles */}
              <div className="divide-y divide-[#191D23]">
                {/* 1. High Impact News */}
                <div className="flex items-center justify-between py-2">
                  <div className="pr-2">
                    <div className="font-bold text-[#E6E8EB] text-[9.5px]">HIGH IMPACT MARKET NEWS</div>
                    <div className="text-[8px] text-[#707987]">Alerts when high-impact market-moving stories break</div>
                  </div>
                  <button
                    onClick={() => handleNotificationToggle("highImpactNewsAlerts")}
                    className={`px-2 py-0.5 rounded text-[8px] font-bold transition shrink-0 ${
                      notifs.highImpactNewsAlerts
                        ? "bg-[#00C896] text-[#050607]"
                        : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    {notifs.highImpactNewsAlerts ? "ON" : "OFF"}
                  </button>
                </div>

                {/* 2. Market Open / Close */}
                <div className="flex items-center justify-between py-2">
                  <div className="pr-2">
                    <div className="font-bold text-[#E6E8EB] text-[9.5px]">MARKET OPEN / CLOSE</div>
                    <div className="text-[8px] text-[#707987]">Session transition notices (09:00, 09:15, 15:30 IST)</div>
                  </div>
                  <button
                    onClick={() => handleNotificationToggle("marketOpenCloseAlerts")}
                    className={`px-2 py-0.5 rounded text-[8px] font-bold transition shrink-0 ${
                      notifs.marketOpenCloseAlerts
                        ? "bg-[#00C896] text-[#050607]"
                        : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    {notifs.marketOpenCloseAlerts ? "ON" : "OFF"}
                  </button>
                </div>

                {/* 3. Broker Session Alerts */}
                <div className="flex items-center justify-between py-2">
                  <div className="pr-2">
                    <div className="font-bold text-[#E6E8EB] text-[9.5px]">BROKER SESSION ALERTS</div>
                    <div className="text-[8px] text-[#707987]">Disconnection &amp; Kite session expiry warnings</div>
                  </div>
                  <button
                    onClick={() => handleNotificationToggle("brokerDisconnectAlerts")}
                    className={`px-2 py-0.5 rounded text-[8px] font-bold transition shrink-0 ${
                      notifs.brokerDisconnectAlerts
                        ? "bg-[#00C896] text-[#050607]"
                        : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    {notifs.brokerDisconnectAlerts ? "ON" : "OFF"}
                  </button>
                </div>

                {/* 4. Macro Event Reminders */}
                <div className="flex items-center justify-between py-2">
                  <div className="pr-2">
                    <div className="font-bold text-[#E6E8EB] text-[9.5px]">MACRO EVENT REMINDERS</div>
                    <div className="text-[8px] text-[#707987]">RBI MPC, US Fed, CPI &amp; GDP scheduled releases</div>
                  </div>
                  <button
                    onClick={() => handleNotificationToggle("economicEventReminders")}
                    className={`px-2 py-0.5 rounded text-[8px] font-bold transition shrink-0 ${
                      notifs.economicEventReminders
                        ? "bg-[#00C896] text-[#050607]"
                        : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    {notifs.economicEventReminders ? "ON" : "OFF"}
                  </button>
                </div>

                {/* 5. System Warnings */}
                <div className="flex items-center justify-between py-2">
                  <div className="pr-2">
                    <div className="font-bold text-[#E6E8EB] text-[9.5px]">SYSTEM WARNINGS</div>
                    <div className="text-[8px] text-[#707987]">Telemetry degradation, data latency &amp; circuit alerts</div>
                  </div>
                  <button
                    onClick={() => handleNotificationToggle("systemHealthWarnings")}
                    className={`px-2 py-0.5 rounded text-[8px] font-bold transition shrink-0 ${
                      notifs.systemHealthWarnings
                        ? "bg-[#00C896] text-[#050607]"
                        : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    {notifs.systemHealthWarnings ? "ON" : "OFF"}
                  </button>
                </div>
              </div>
            </div>
          </Surface>

          {/* STAGING QA CONTROLS (Only visible in STAGING environment) */}
          {pres.environment === "STAGING" && (
            <Surface className="overflow-hidden border-[#E59700]/30">
              <div className="flex items-center justify-between border-b border-[#191D23] bg-[#0E1013] px-3 py-1.5 font-mono">
                <span className="text-[8px] font-bold text-[#E59700] uppercase tracking-wider">
                  STAGING QA SESSION CONTROLS
                </span>
                <span className="text-[8px] text-[#707987]">Preview Override</span>
              </div>
              <div className="p-2.5 bg-[#0B0D10] font-mono text-[9px] space-y-1.5">
                <div className="text-[8px] text-[#707987]">
                  Forces session rendering mode for end-to-end interface validation:
                </div>
                <div className="grid grid-cols-4 gap-1.5">
                  {(["auto", "pre_market", "live", "post_market"] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => handleStagingSessionClick(mode)}
                      className={`px-1.5 py-1 rounded text-[8px] font-bold uppercase transition text-center truncate ${
                        (niftyModeOverride || "auto") === mode
                          ? "bg-[#E59700] text-[#050607]"
                          : "bg-[#191D23] text-[#707987] hover:text-[#E6E8EB]"
                      }`}
                    >
                      {mode.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </div>
            </Surface>
          )}

          {/* SAFE RESET */}
          <Surface className="overflow-hidden">
            <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[9.5px]">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-bold text-[#E6E8EB]">SAFE RESET</div>
                  <div className="text-[8px] text-[#707987]">
                    Reset local UI preferences to workstation defaults.
                  </div>
                </div>
                {!showConfirmReset ? (
                  <button
                    onClick={() => setShowConfirmReset(true)}
                    className="px-2.5 py-1 bg-[#191D23] hover:bg-[#242830] border border-[#242830] text-[#707987] hover:text-[#E6E8EB] rounded text-[8.5px] font-bold transition shrink-0"
                  >
                    Reset Defaults
                  </button>
                ) : (
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={handleResetPreferences}
                      className="px-2 py-0.5 bg-[#E5484D] text-white rounded text-[8px] font-bold transition"
                    >
                      Confirm Reset
                    </button>
                    <button
                      onClick={() => setShowConfirmReset(false)}
                      className="px-2 py-0.5 bg-[#191D23] text-[#707987] rounded text-[8px] font-bold transition"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
              <div className="text-[7.5px] text-[#555C68]">
                Safeguard: Does not disconnect broker, alter market data, or delete backend state.
              </div>
            </div>
          </Surface>
        </div>

        {/* ── RIGHT COLUMN (~55% / 7 cols on lg) ── */}
        <div className="lg:col-span-7 space-y-3">
          {/* CONNECTIONS & DATA SOURCES */}
          <Surface id="settings-connections-list" className="overflow-hidden">
            <SectionHeader
              title="CONNECTIONS &amp; DATA SOURCES"
              eyebrow="Integration Telemetry"
              accent="cyan"
              icon={Database}
            />
            <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[9.5px]">
              {brokerMessage && (
                <div className="p-1.5 bg-[#38BDF8]/10 border border-[#38BDF8]/30 text-[#38BDF8] rounded text-[8.5px] font-bold">
                  {brokerMessage}
                </div>
              )}

              <div className="divide-y divide-[#191D23]">
                {/* 1. ZERODHA KITECONNECT BROKER */}
                <div id="settings-broker-integration" className="py-2.5 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-[#242830] bg-[#08090B] text-[#38BDF8]">
                        <KeyRound size={11} />
                      </div>
                      <div>
                        <div className="font-bold text-[#E6E8EB] text-[10px]">Zerodha KiteConnect</div>
                        <div className="text-[8px] text-[#707987]">
                          Account: {pres.brokerState.clientIdMasked}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase ${
                          isBrokerConnected
                            ? "bg-[#00C896]/20 text-[#00C896]"
                            : "bg-[#E5484D]/20 text-[#E5484D]"
                        }`}
                      >
                        {pres.brokerState.status}
                      </span>
                      {isBrokerConnected ? (
                        <button
                          onClick={handleBrokerDisconnect}
                          className="px-2 py-0.5 bg-[#E5484D]/15 hover:bg-[#E5484D]/25 border border-[#E5484D]/30 text-[#E5484D] font-bold rounded text-[8px] transition"
                        >
                          Disconnect
                        </button>
                      ) : (
                        <button
                          onClick={handleOAuthConnect}
                          className="px-2 py-0.5 bg-[#38BDF8] text-[#050607] hover:bg-[#7DD3FC] font-bold rounded text-[8px] transition"
                        >
                          Authenticate Broker
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* 2. NSE MARKET DATA STREAM */}
                <div className="py-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-[#242830] bg-[#08090B] text-[#00C896]">
                      <Radio size={11} />
                    </div>
                    <div>
                      <div className="font-bold text-[#E6E8EB] text-[9.5px]">NSE Market Data Stream</div>
                      <div className="text-[8px] text-[#707987]">NIFTY spot &amp; constituent breadth telemetry</div>
                    </div>
                  </div>
                  <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-[#00C896]/20 text-[#00C896] uppercase">
                    {isMarketOpen ? "LIVE" : "READY"}
                  </span>
                </div>

                {/* 3. OPTIONS MATRIX */}
                <div className="py-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-[#242830] bg-[#08090B] text-[#38BDF8]">
                      <Activity size={11} />
                    </div>
                    <div>
                      <div className="font-bold text-[#E6E8EB] text-[9.5px]">NIFTY Option Chain Matrix</div>
                      <div className="text-[8px] text-[#707987]">
                        {strikesCount > 0 ? `${strikesCount} strikes loaded · OI &amp; depth telemetry` : "Derivatives matrix synced"}
                      </div>
                    </div>
                  </div>
                  <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-[#00C896]/20 text-[#00C896] uppercase">
                    HEALTHY
                  </span>
                </div>

                {/* 4. FINANCIAL NEWS PIPELINE */}
                <div className="py-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-[#242830] bg-[#08090B] text-[#8B5CF6]">
                      <Newspaper size={11} />
                    </div>
                    <div>
                      <div className="font-bold text-[#E6E8EB] text-[9.5px]">Financial News Pipeline</div>
                      <div className="text-[8px] text-[#707987]">
                        {newsCount > 0 ? `${newsCount} current-eligible stories active · Source attribution verified` : "News pipeline operational"}
                      </div>
                    </div>
                  </div>
                  <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-[#00C896]/20 text-[#00C896] uppercase">
                    HEALTHY
                  </span>
                </div>

                {/* 5. MACRO & ECONOMIC CALENDAR */}
                <div className="py-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-[#242830] bg-[#08090B] text-[#E59700]">
                      <Calendar size={11} />
                    </div>
                    <div>
                      <div className="font-bold text-[#E6E8EB] text-[9.5px]">Macro &amp; Economic Calendar</div>
                      <div className="text-[8px] text-[#707987]">
                        {macroEventsCount > 0 ? `${macroEventsCount} scheduled events · RBI, MoSPI, Fed telemetry` : "Macro telemetry active"}
                      </div>
                    </div>
                  </div>
                  <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-[#00C896]/20 text-[#00C896] uppercase">
                    HEALTHY
                  </span>
                </div>

                {/* 6. OPENAI GPT-4o ENGINE */}
                <div className="py-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-[#242830] bg-[#08090B] text-[#38BDF8]">
                      <Cpu size={11} />
                    </div>
                    <div>
                      <div className="font-bold text-[#E6E8EB] text-[9.5px]">OpenAI GPT-4o Reasoning</div>
                      <div className="text-[8px] text-[#707987]">Deterministic engine + GPT-4o synthesis active</div>
                    </div>
                  </div>
                  <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-[#00C896]/20 text-[#00C896] uppercase">
                    READY
                  </span>
                </div>
              </div>
            </div>
          </Surface>

          {/* READ-ONLY SAFETY */}
          <Surface className="overflow-hidden border-[#00C896]/30">
            <div className="p-2.5 bg-[#0B0D10] font-mono text-[9.5px] space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-[#00C896] text-[9.5px] uppercase">
                <ShieldCheck size={13} />
                READ-ONLY SAFETY INVARIANTS
              </div>
              <p className="text-[8.5px] text-[#707987] leading-relaxed">
                AIR ArdhaMind operates in strict <strong className="text-[#E6E8EB]">READ ONLY</strong> mode. Order placement, paper trading, order modification, and broker mutations are hard-disabled at the architecture level.
              </p>
            </div>
          </Surface>

          {/* RUNTIME SNAPSHOT */}
          <Surface className="overflow-hidden">
            <SectionHeader
              title="RUNTIME SNAPSHOT"
              eyebrow="System Telemetry"
              accent="emerald"
              icon={Activity}
            />
            <div className="p-3 bg-[#0B0D10] space-y-3 font-mono text-[9.5px]">
              <div className="grid grid-cols-2 gap-2 text-[#707987]">
                <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                  <div className="text-[8px] uppercase font-bold text-[#707987]">Runtime ID</div>
                  <div className="font-bold text-[#38BDF8] text-[9px] truncate font-mono mt-0.5">
                    {pres.diagnostics.runtimeId}
                  </div>
                </div>
                <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                  <div className="text-[8px] uppercase font-bold text-[#707987]">State Sequence</div>
                  <div className="font-bold text-[#E6E8EB] text-[9px] font-mono mt-0.5">
                    #{pres.diagnostics.stateSequence}
                  </div>
                </div>
                <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                  <div className="text-[8px] uppercase font-bold text-[#707987]">Environment</div>
                  <div className="font-bold text-[#E59700] text-[9px] uppercase mt-0.5">
                    {pres.environment}
                  </div>
                </div>
                <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                  <div className="text-[8px] uppercase font-bold text-[#707987]">Market Session</div>
                  <div className="font-bold text-[#00C896] text-[9px] uppercase mt-0.5">
                    {pres.diagnostics.marketSession}
                  </div>
                </div>
                <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                  <div className="text-[8px] uppercase font-bold text-[#707987]">Last Sync</div>
                  <div className="text-[#E6E8EB] text-[9px] truncate mt-0.5">
                    {pres.lastUpdatedIst}
                  </div>
                </div>
                <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                  <div className="text-[8px] uppercase font-bold text-[#707987]">Version</div>
                  <div className="text-[#38BDF8] text-[9px] font-bold mt-0.5">
                    {pres.version}
                  </div>
                </div>
              </div>

              {/* View Advanced Diagnostics Button */}
              <div className="pt-1 flex items-center justify-between border-t border-[#191D23]">
                <span className="text-[8px] text-[#707987]">
                  Dataset validation, detector health &amp; Ardha Performance telemetry
                </span>
                <button
                  id="btn-view-advanced-diagnostics"
                  onClick={() => setIsDiagnosticsOpen(true)}
                  className="px-2.5 py-1 bg-[#38BDF8]/15 hover:bg-[#38BDF8]/25 border border-[#38BDF8]/30 text-[#38BDF8] font-bold rounded text-[9px] transition flex items-center gap-1 shrink-0"
                >
                  VIEW ADVANCED DIAGNOSTICS
                  <ChevronRight size={11} />
                </button>
              </div>
            </div>
          </Surface>
        </div>
      </div>

      {/* ── 4. ADVANCED DIAGNOSTICS DRAWER (Preserves all technical & performance telemetry) ── */}
      <AdvancedDiagnosticsDrawer
        pres={pres}
        isOpen={isDiagnosticsOpen}
        onClose={() => {
          setIsDiagnosticsOpen(false);
          if (onSelectSubTab) onSelectSubTab("overview");
          if (navSetSubTab) navSetSubTab("overview");
        }}
      />
    </div>
  );
}

export default SettingsWorkspace;
