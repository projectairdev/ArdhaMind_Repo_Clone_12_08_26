import React, { useState } from "react";
import { Bell, ShieldCheck, AlertCircle, CheckCircle2 } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import {
  SettingsPresentationState,
  NotificationSettingsState,
  saveStoredNotifications,
} from "../../utils/canonicalSettingsAdapter";

export function SettingsNotifications({ pres }: { pres: SettingsPresentationState }) {
  const [notifs, setNotifs] = useState<NotificationSettingsState>(pres.notifications);
  const [msg, setMsg] = useState<string | null>(null);

  const handleToggle = (key: keyof Omit<NotificationSettingsState, "browserPermission">) => {
    const updated = { ...notifs, [key]: !notifs[key] };
    setNotifs(updated);
    saveStoredNotifications(updated);
    setMsg("Notification setting updated.");
    setTimeout(() => setMsg(null), 3000);
  };

  const handleRequestPermission = async () => {
    if (typeof window !== "undefined" && "Notification" in window) {
      try {
        const perm = await Notification.requestPermission();
        const updated = { ...notifs, browserPermission: perm as any };
        setNotifs(updated);
        saveStoredNotifications(updated);
      } catch (e: any) {
        setMsg("Permission request failed: " + e.message);
      }
    }
  };

  return (
    <div className="space-y-3 font-sans text-left text-[11px] min-w-0">
      {/* ── 1. BROWSER PERMISSION STATUS ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="BROWSER NOTIFICATION PERMISSION STATUS" eyebrow="1. Delivery Readiness" accent="cyan" />
        <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[10px]">
          <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
            <div className="flex items-center gap-2">
              <Bell size={14} className="text-[#38BDF8]" />
              <span className="font-bold text-[#E6E8EB]">Browser Notification Subsystem</span>
            </div>
            <span
              className={`px-1.5 py-0.5 rounded text-[8.5px] font-bold ${
                notifs.browserPermission === "granted"
                  ? "bg-[#00C896]/20 text-[#00C896]"
                  : notifs.browserPermission === "denied"
                  ? "bg-[#E5484D]/20 text-[#E5484D]"
                  : "bg-[#E59700]/20 text-[#E59700]"
              }`}
            >
              PERMISSION: {notifs.browserPermission.toUpperCase()}
            </span>
          </div>

          {notifs.browserPermission !== "granted" && (
            <div className="p-2 bg-[#E59700]/10 border border-[#E59700]/30 rounded text-[#E59700] text-[9px] flex items-center justify-between">
              <span className="flex items-center gap-1">
                <AlertCircle size={12} />
                Browser notification permission required for desktop alert popups.
              </span>
              {notifs.browserPermission !== "unsupported" && (
                <button
                  onClick={handleRequestPermission}
                  className="px-2 py-0.5 bg-[#E59700] text-[#050607] font-bold rounded text-[8.5px]"
                >
                  Request Permission
                </button>
              )}
            </div>
          )}

          {msg && (
            <div className="p-1.5 bg-[#00C896]/10 border border-[#00C896]/30 text-[#00C896] rounded text-[8.5px] font-bold">
              {msg}
            </div>
          )}
        </div>
      </Surface>

      {/* ── 2. ALERT SUBSCRIPTION TOGGLES ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="WORKSTATION ALERT SUBSCRIPTIONS" eyebrow="2. Notification Preferences" accent="violet" />
        <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[9.5px]">
          <div className="divide-y divide-[#191D23]">
            {/* High Impact News */}
            <div className="flex items-center justify-between py-2">
              <div>
                <div className="font-bold text-[#E6E8EB]">High Impact Market News Alerts</div>
                <div className="text-[8px] text-[#707987]">Alerts when HIGH impact market-moving stories occur</div>
              </div>
              <button
                onClick={() => handleToggle("highImpactNewsAlerts")}
                className={`px-2.5 py-1 rounded text-[8.5px] font-bold transition ${
                  notifs.highImpactNewsAlerts ? "bg-[#00C896] text-[#050607]" : "bg-[#191D23] text-[#707987]"
                }`}
              >
                {notifs.highImpactNewsAlerts ? "ENABLED" : "DISABLED"}
              </button>
            </div>

            {/* Market Open / Close */}
            <div className="flex items-center justify-between py-2">
              <div>
                <div className="font-bold text-[#E6E8EB]">Market Session Open / Close Alerts</div>
                <div className="text-[8px] text-[#707987]">Alerts when NSE market session status changes</div>
              </div>
              <button
                onClick={() => handleToggle("marketOpenCloseAlerts")}
                className={`px-2.5 py-1 rounded text-[8.5px] font-bold transition ${
                  notifs.marketOpenCloseAlerts ? "bg-[#00C896] text-[#050607]" : "bg-[#191D23] text-[#707987]"
                }`}
              >
                {notifs.marketOpenCloseAlerts ? "ENABLED" : "DISABLED"}
              </button>
            </div>

            {/* Broker Disconnect */}
            <div className="flex items-center justify-between py-2">
              <div>
                <div className="font-bold text-[#E6E8EB]">Broker Session Disconnect Alerts</div>
                <div className="text-[8px] text-[#707987]">Alerts when Zerodha Kite session expires or disconnects</div>
              </div>
              <button
                onClick={() => handleToggle("brokerDisconnectAlerts")}
                className={`px-2.5 py-1 rounded text-[8.5px] font-bold transition ${
                  notifs.brokerDisconnectAlerts ? "bg-[#00C896] text-[#050607]" : "bg-[#191D23] text-[#707987]"
                }`}
              >
                {notifs.brokerDisconnectAlerts ? "ENABLED" : "DISABLED"}
              </button>
            </div>

            {/* Economic Events */}
            <div className="flex items-center justify-between py-2">
              <div>
                <div className="font-bold text-[#E6E8EB]">Scheduled Macro Release Reminders</div>
                <div className="text-[8px] text-[#707987]">Alerts ahead of scheduled high-impact economic releases</div>
              </div>
              <button
                onClick={() => handleToggle("economicEventReminders")}
                className={`px-2.5 py-1 rounded text-[8.5px] font-bold transition ${
                  notifs.economicEventReminders ? "bg-[#00C896] text-[#050607]" : "bg-[#191D23] text-[#707987]"
                }`}
              >
                {notifs.economicEventReminders ? "ENABLED" : "DISABLED"}
              </button>
            </div>

            {/* System Health */}
            <div className="flex items-center justify-between py-2">
              <div>
                <div className="font-bold text-[#E6E8EB]">System Degradation &amp; Telemetry Warnings</div>
                <div className="text-[8px] text-[#707987]">Alerts when data quality or stream readiness drops</div>
              </div>
              <button
                onClick={() => handleToggle("systemHealthWarnings")}
                className={`px-2.5 py-1 rounded text-[8.5px] font-bold transition ${
                  notifs.systemHealthWarnings ? "bg-[#00C896] text-[#050607]" : "bg-[#191D23] text-[#707987]"
                }`}
              >
                {notifs.systemHealthWarnings ? "ENABLED" : "DISABLED"}
              </button>
            </div>
          </div>
        </div>
      </Surface>
    </div>
  );
}

export default SettingsNotifications;
