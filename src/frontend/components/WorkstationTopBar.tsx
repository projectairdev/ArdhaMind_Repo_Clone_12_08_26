import React, { useEffect, useState } from "react";
import { Menu, X, Settings as SettingsIcon, Clock, ShieldCheck, Zap } from "lucide-react";
import { useBrokerStatus, useWorkstationState } from "../context/WorkstationStateContext";
import { useNavigation } from "../context/NavigationContext";
import {
  resolveMarketSessionState,
  getMarketSessionBadge,
} from "../utils/canonicalSemanticContract";
import { ArdhaMindBrandMark } from "./ui/VisualAssets";

interface WorkstationTopBarProps {
  mobileOpen: boolean;
  onToggleMobile: () => void;
  onOpenSettings: () => void;
  settingsOpen?: boolean;
}

export function WorkstationTopBar({
  mobileOpen,
  onToggleMobile,
  onOpenSettings,
  settingsOpen = false,
}: WorkstationTopBarProps) {
  const { canonicalState, lastValidState } = useWorkstationState();
  const { data: broker } = useBrokerStatus();
  const { navigateTo, assistantOpen, toggleAssistant } = useNavigation();
  const [clockIst, setClockIst] = useState({ fullDate: "", compactDate: "", timeIst: "" });

  useEffect(() => {
    if ((import.meta as any).env?.VITE_STAGING_MODE === "true") {
      document.title = "[STAGING] AIR ArdhaMind";
    }
  }, []);

  // Live IST Clock (1-second tick)
  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const fullDate = new Intl.DateTimeFormat("en-GB", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "short",
        year: "numeric",
      }).format(now);

      const compactDate = new Intl.DateTimeFormat("en-GB", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "short",
      }).format(now);

      const timeIst = new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      })
        .format(now)
        .toUpperCase();

      setClockIst({ fullDate, compactDate, timeIst });
    };

    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const state = canonicalState ?? lastValidState;
  const canonicalSession = resolveMarketSessionState(state);
  const sessionBadge = getMarketSessionBadge(canonicalSession);

  // Authoritative Normalized Broker Health Contract
  const rawBroker = state?.broker_status || broker;
  const rawStatus = String((rawBroker as any)?.status || (rawBroker as any)?.connection_status || "").toUpperCase();
  const normalizedStatus: string = (rawBroker as any)?.normalized_status || (
    rawStatus === "CONNECTED_VERIFIED" || (rawBroker as any)?.execution_verified === true ? "CONNECTED_VERIFIED" :
    rawStatus === "CONNECTED_AUTH_REQUIRED" || rawStatus === "SESSION_EXPIRED" || rawStatus === "TOKEN_EXPIRED" || rawStatus === "AUTH_REQUIRED" || (rawBroker as any)?.blocker_code === "AUTH_REQUIRED" || (rawBroker as any)?.authenticated === false ? "CONNECTED_AUTH_REQUIRED" :
    rawStatus === "RECONNECTING" ? "RECONNECTING" :
    rawStatus === "BROKER_STATE_UNVERIFIED" || rawStatus === "UNVERIFIED" || rawStatus === "CONNECTED" || (rawBroker as any)?.reconciliation_complete === false ? "BROKER_STATE_UNVERIFIED" :
    "DISCONNECTED"
  );

  const isVerified = normalizedStatus === "CONNECTED_VERIFIED";
  const isAuthRequired = normalizedStatus === "CONNECTED_AUTH_REQUIRED";
  const isReconnecting = normalizedStatus === "RECONNECTING";
  const isUnverified = normalizedStatus === "BROKER_STATE_UNVERIFIED";

  const brokerLabel = isVerified
    ? "CONNECTED"
    : isAuthRequired
    ? "AUTH REQUIRED"
    : isReconnecting
    ? "RECONNECTING"
    : isUnverified
    ? "VERIFYING"
    : "DISCONNECTED";

  const brokerDotClass = isVerified
    ? "bg-[#00C896]"
    : isAuthRequired
    ? "bg-[#E59700]"
    : isReconnecting
    ? "bg-[#E59700]"
    : isUnverified
    ? "bg-[#8B5CF6]"
    : "bg-[#E5484D]";

  const brokerTextClass = isVerified
    ? "text-[#00C896]"
    : isAuthRequired
    ? "text-[#E59700]"
    : isReconnecting
    ? "text-[#E59700]"
    : isUnverified
    ? "text-[#8B5CF6]"
    : "text-[#E5484D]";

  const staging = (import.meta as any).env?.VITE_STAGING_MODE === "true";

  return (
    <header
      data-testid="phase1-top-bar"
      className="sticky top-0 z-50 grid grid-cols-[auto_1fr_auto] h-[56px] shrink-0 items-center border-b border-[#242830] bg-[#050607] px-3.5 sm:px-4 font-mono text-[11px] w-full min-w-0"
    >
      {/* ── ZONE 1: LEFT BRAND CLUSTER ── */}
      <div className="justify-self-start flex items-center gap-2.5 min-w-0 shrink-0">
        <button
          aria-label="Toggle navigation"
          title="Toggle navigation"
          className="rounded border border-[#242830] bg-[#0B0D10] p-1.5 text-[#A5ABB4] hover:bg-[#13161A] lg:hidden shrink-0"
          onClick={onToggleMobile}
        >
          {mobileOpen ? <X size={15} /> : <Menu size={15} />}
        </button>

        <div className="flex items-center gap-2 min-w-0">
          <ArdhaMindBrandMark size={24} />
          <span className="text-[15px] font-bold tracking-tight text-[#E6E8EB] whitespace-nowrap">ArdhaMind</span>
          {staging && (
            <span className="rounded border border-[#E59700]/40 bg-[#E59700]/10 px-1.5 py-0.5 text-[9.5px] font-bold text-[#E59700] uppercase shrink-0">
              STAGING
            </span>
          )}
        </div>
      </div>

      {/* ── ZONE 2: CENTER GLOBAL STATUS CLUSTER ── */}
      <div className="justify-self-center hidden sm:flex items-center gap-3 text-[10px] bg-[#0B0D10] border border-[#191D23] px-3 py-1 rounded-[3px] shrink-0">
        {/* Market Status (Navigates to Market Nifty) */}
        <button
          onClick={() => navigateTo({ workspace: "market", tab: "nifty", section: "market-nifty-session-summary" })}
          title="View Market Command (NIFTY)"
          aria-label="Market Status — View Market Command"
          className="flex items-center gap-1.5 whitespace-nowrap hover:bg-[#13161A] px-1 py-0.5 rounded cursor-pointer transition focus:outline-none focus:ring-1 focus:ring-[#38BDF8]"
        >
          <span className={`h-2 w-2 rounded-full shrink-0 ${sessionBadge.dotClass}`} />
          <span className="text-[#707987]">Market:</span>
          <span className={`font-bold ${sessionBadge.isOpen ? "text-[#00C896]" : sessionBadge.isPreMarket ? "text-[#38BDF8]" : "text-[#E59700]"}`}>
            {sessionBadge.label}
          </span>
        </button>

        <span className="text-[#242830]">|</span>

        {/* Broker Status (Navigates to Settings Connections Broker Integration) */}
        <button
          onClick={() => navigateTo({ workspace: "settings", tab: "connections", section: "settings-connections-broker" })}
          title="View Broker Authentication & Integration"
          aria-label="Broker Status — View Broker Connections"
          className="flex items-center gap-1.5 whitespace-nowrap hover:bg-[#13161A] px-1 py-0.5 rounded cursor-pointer transition focus:outline-none focus:ring-1 focus:ring-[#38BDF8]"
        >
          <span
            className={`h-2 w-2 rounded-full shrink-0 ${brokerDotClass}`}
          />
          <span className="text-[#707987]">Broker:</span>
          <span
            className={`font-bold ${brokerTextClass}`}
          >
            {brokerLabel}
          </span>
        </button>
      </div>

      {/* ── ZONE 3: RIGHT GLOBAL ACTIONS & IST CLOCK ── */}
      <div className="justify-self-end flex items-center gap-2.5 shrink-0 text-[#A5ABB4]">
        {/* Live Assistant Button */}
        <button
          onClick={toggleAssistant}
          title="Live Assistant — Conversational Intelligence"
          aria-label="Live Assistant — Conversational Intelligence"
          className={`hidden md:flex items-center gap-1.5 text-[9.5px] font-bold border px-2.5 py-1 rounded-[3px] transition cursor-pointer shrink-0 ${
            assistantOpen
              ? "border-[#8B5CF6] bg-[#8B5CF6]/30 text-white shadow-[0_0_10px_rgba(139,92,246,0.3)]"
              : "border-[#8B5CF6]/40 bg-[#8B5CF6]/10 text-[#8B5CF6] hover:bg-[#8B5CF6]/20"
          }`}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-[#8B5CF6] shrink-0 animate-pulse" />
          <span>Live Assistant</span>
        </button>

        {/* Settings Button */}
        <button
          onClick={() => navigateTo({ workspace: "settings", tab: "overview" })}
          title="Settings &amp; System Diagnostics"
          className={`flex items-center gap-1.5 rounded border px-2.5 py-1 text-[10px] font-bold transition cursor-pointer shrink-0 ${
            settingsOpen
              ? "border-[#38BDF8] bg-[#38BDF8]/15 text-[#38BDF8]"
              : "border-[#242830] bg-[#0B0D10] text-[#E6E8EB] hover:bg-[#13161A]"
          }`}
        >
          <SettingsIcon size={13} className={settingsOpen ? "text-[#38BDF8]" : "text-[#A5ABB4]"} />
          <span>Settings</span>
        </button>

        <span className="hidden xl:inline text-[#242830]">|</span>

        {/* Centralized Live IST Clock */}
        <div className="hidden lg:flex items-center gap-1.5 text-[9.5px] font-mono shrink-0">
          <Clock size={11} className="text-[#38BDF8]" />
          <span className="text-[#707987] hidden xl:inline">{clockIst.fullDate}</span>
          <span className="text-[#707987] xl:hidden">{clockIst.compactDate}</span>
          <span className="text-[#707987]">·</span>
          <span className="text-[#38BDF8] font-bold">{clockIst.timeIst} IST</span>
        </div>
      </div>
    </header>
  );
}

export default WorkstationTopBar;
