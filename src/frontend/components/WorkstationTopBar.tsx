// src/frontend/components/WorkstationTopBar.tsx
import React, { useEffect, useState } from "react";
import { Menu, X, Settings as SettingsIcon, Clock, Sparkles } from "lucide-react";
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
  const [clockIst, setClockIst] = useState({ dateStr: "", timeStr: "" });

  useEffect(() => {
    if ((import.meta as any).env?.VITE_STAGING_MODE === "true") {
      document.title = "[STAGING] ARDHA Workstation";
    }
  }, []);

  // Live IST Clock (1-second tick)
  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const dateStr = new Intl.DateTimeFormat("en-GB", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "short",
        year: "numeric",
      }).format(now);

      const timeStr = new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      })
        .format(now)
        .toUpperCase();

      setClockIst({ dateStr, timeStr });
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

  const brokerTextClass = isVerified
    ? "text-[#00C896]"
    : isAuthRequired
    ? "text-[#E59700]"
    : isReconnecting
    ? "text-[#E59700]"
    : isUnverified
    ? "text-[#8B5CF6]"
    : "text-[#E5484D]";

  const marketTextClass = sessionBadge.isOpen
    ? "text-[#00C896]"
    : sessionBadge.isPreMarket
    ? "text-[#38BDF8]"
    : "text-[#E59700]";

  const staging = (import.meta as any).env?.VITE_STAGING_MODE === "true";

  return (
    <header
      data-testid="phase1-top-bar"
      className="sticky top-0 z-50 flex h-14 md:h-16 shrink-0 items-center justify-between border-b border-[#191D23] bg-[#050607] px-3.5 sm:px-5 font-mono text-[11px] w-full min-w-0"
    >
      {/* ── LEFT: ARDHA BRAND IDENTITY ── */}
      <div className="flex items-center gap-2 min-w-0 shrink-0">
        <button
          aria-label="Toggle navigation"
          title="Toggle navigation"
          className="rounded border border-[#242830] bg-[#0B0D10] p-1.5 text-[#A5ABB4] hover:bg-[#13161A] lg:hidden shrink-0"
          onClick={onToggleMobile}
        >
          {mobileOpen ? <X size={14} /> : <Menu size={14} />}
        </button>

        <div className="flex items-center gap-1.5 min-w-0">
          <ArdhaMindBrandMark size={20} />
          <span className="text-[13px] font-bold tracking-tight text-[#E6E8EB] whitespace-nowrap font-mono">ARDHA</span>
          {staging && (
            <span className="rounded border border-[#E59700]/40 bg-[#E59700]/10 px-1 py-0.2 text-[8px] font-bold text-[#E59700] uppercase shrink-0 tracking-wider">
              STAGING
            </span>
          )}
        </div>
      </div>

      {/* ── RIGHT: STATUS + ACTIONS + CLOCK CLUSTER ── */}
      <div className="flex items-center gap-3 sm:gap-3.5 shrink-0 text-[#A5ABB4]">
        {/* 1. Market Status (Text-only, no icon, no large box) */}
        <button
          onClick={() => navigateTo({ workspace: "market", tab: "nifty", section: "market-nifty-session-summary" })}
          title="View Market Command (NIFTY)"
          aria-label="Market Status"
          className="hidden sm:flex items-center gap-1.5 text-[10.5px] hover:opacity-80 transition cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#38BDF8] rounded px-1"
        >
          <span className="text-[#707987]">Market:</span>
          <span className={`font-bold uppercase tracking-tight ${marketTextClass}`}>
            {sessionBadge.label}
          </span>
        </button>

        {/* Separator */}
        <span className="hidden sm:inline text-[#242830] select-none text-[12px]">|</span>

        {/* 2. Broker Status (Text-only, no icon, no large box) */}
        <button
          onClick={() => navigateTo({ workspace: "settings", tab: "connections", section: "settings-connections-broker" })}
          title="View Broker Authentication & Integration"
          aria-label="Broker Status"
          className="hidden sm:flex items-center gap-1.5 text-[10.5px] hover:opacity-80 transition cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#38BDF8] rounded px-1"
        >
          <span className="text-[#707987]">Broker:</span>
          <span className={`font-bold uppercase tracking-tight ${brokerTextClass}`}>
            {brokerLabel}
          </span>
        </button>

        {/* Separator */}
        <span className="hidden sm:inline text-[#242830] select-none text-[12px]">|</span>

        {/* 3. Live Assistant (Icon-only with hover tooltip) */}
        <div className="relative group flex items-center">
          <button
            onClick={toggleAssistant}
            aria-label="Live Assistant"
            className={`flex h-8 w-8 items-center justify-center rounded-[3px] border transition cursor-pointer ${
              assistantOpen
                ? "border-[#8B5CF6] bg-[#8B5CF6]/20 text-[#C084FC] shadow-[0_0_8px_rgba(139,92,246,0.25)]"
                : "border-[#242830] bg-[#0B0D10] text-[#707987] hover:border-[#8B5CF6]/50 hover:text-[#C084FC] hover:bg-[#13161A]"
            }`}
          >
            <Sparkles size={15} />
          </button>
          {/* Tooltip */}
          <div className="absolute right-0 top-full mt-1.5 hidden group-hover:flex items-center z-50 pointer-events-none">
            <div className="rounded border border-[#242830] bg-[#0E1013] px-2 py-1 text-[9.5px] font-mono text-[#E6E8EB] shadow-xl whitespace-nowrap">
              Live Assistant
            </div>
          </div>
        </div>

        {/* 4. Settings (Icon-only with hover tooltip) */}
        <div className="relative group flex items-center">
          <button
            onClick={onOpenSettings}
            aria-label="Settings"
            className={`flex h-8 w-8 items-center justify-center rounded-[3px] border transition cursor-pointer ${
              settingsOpen
                ? "border-[#38BDF8] bg-[#38BDF8]/20 text-[#38BDF8] shadow-[0_0_8px_rgba(56,189,248,0.25)]"
                : "border-[#242830] bg-[#0B0D10] text-[#707987] hover:border-[#38BDF8]/50 hover:text-[#E6E8EB] hover:bg-[#13161A]"
            }`}
          >
            <SettingsIcon size={15} />
          </button>
          {/* Tooltip */}
          <div className="absolute right-0 top-full mt-1.5 hidden group-hover:flex items-center z-50 pointer-events-none">
            <div className="rounded border border-[#242830] bg-[#0E1013] px-2 py-1 text-[9.5px] font-mono text-[#E6E8EB] shadow-xl whitespace-nowrap">
              Settings
            </div>
          </div>
        </div>

        {/* Separator */}
        <span className="hidden md:inline text-[#242830] select-none text-[12px]">|</span>

        {/* 5. Clock / Date Region (Clock icon followed by date & time, NO calendar icon) */}
        <div className="hidden md:flex items-center gap-1.5 text-[10px] font-mono shrink-0">
          <Clock size={13} className="text-[#38BDF8]" />
          <span className="text-[#707987]">{clockIst.dateStr}</span>
          <span className="text-[#333942] select-none">·</span>
          <span className="text-[#38BDF8] font-bold">{clockIst.timeStr} IST</span>
        </div>
      </div>
    </header>
  );
}

export default WorkstationTopBar;
