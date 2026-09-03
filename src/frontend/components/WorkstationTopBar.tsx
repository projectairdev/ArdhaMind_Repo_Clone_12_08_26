// src/frontend/components/WorkstationTopBar.tsx
import React, { useEffect, useState, useMemo } from "react";
import { Menu, X, Settings as SettingsIcon, Clock, Sparkles } from "lucide-react";
import { useBrokerStatus, useWorkstationState } from "../context/WorkstationStateContext";
import { useCanonicalState } from "../context/CanonicalStateContext";
import { useNavigation } from "../context/NavigationContext";
import { ArdhaMindBrandMark } from "./ui/VisualAssets";

interface WorkstationTopBarProps {
  mobileOpen: boolean;
  onToggleMobile: () => void;
  onOpenSettings: () => void;
  settingsOpen?: boolean;
}

export function WorkstationTopBar({
  onToggleMobile,
  onOpenSettings,
  mobileOpen = false,
  settingsOpen = false,
}: WorkstationTopBarProps) {
  const { canonicalState, lastValidState, marketConnection } = useWorkstationState() as any;
  const {
    isFixtureData,
    isReplayMode,
    sessionIdentity,
    sessionPhase,
    isConnected,
  } = useCanonicalState();
  const { data: broker } = useBrokerStatus();
  const { navigateTo, assistantOpen, toggleAssistant } = useNavigation();

  useEffect(() => {
    if ((import.meta as any).env?.VITE_STAGING_MODE === "true") {
      document.title = "[STAGING] ARDHA Workstation";
    }
  }, []);

  const state = canonicalState ?? lastValidState;
  const authoritativeTs =
    state?.generated_at ||
    state?.data_quality?.market_data?.observed_at ||
    state?.market_data?.observed_at;

  const isDisconnected = marketConnection === "DISCONNECTED" || !isConnected;

  // Single authoritative continuous ticking IST clock sourced from unified sessionIdentity
  const { displayDate, displayTime } = useMemo(() => {
    return {
      displayDate: sessionIdentity.calendar_date_formatted,
      displayTime: sessionIdentity.wall_clock_ist,
    };
  }, [sessionIdentity]);

  // Authoritative Normalized Broker Health Contract.
  // NOTE: broker connection status is derived ONLY from real broker auth/session
  // fields. The browser<->local-server WebSocket state (`isConnected`) is
  // deliberately NOT part of this — a live tab socket does not mean Zerodha is
  // authenticated, and OR-ing it in previously showed a false green "CONNECTED"
  // through expired tokens / 401s / explicit logout.
  const rawBroker = state?.broker_status || broker;
  const rawStatus = String((rawBroker as any)?.status || (rawBroker as any)?.connection_status || (rawBroker as any)?.normalized_status || "").toUpperCase();
  const isBrokerConnected =
    rawStatus === "CONNECTED_VERIFIED" ||
    rawStatus === "CONNECTED" ||
    rawStatus === "HEALTHY" ||
    rawStatus === "READY" ||
    (rawBroker as any)?.execution_verified === true ||
    (rawBroker as any)?.socket_connected === true;

  const isAuthRequired =
    rawStatus === "CONNECTED_AUTH_REQUIRED" ||
    rawStatus === "SESSION_EXPIRED" ||
    rawStatus === "TOKEN_EXPIRED" ||
    rawStatus === "AUTH_REQUIRED" ||
    (rawBroker as any)?.blocker_code === "AUTH_REQUIRED" ||
    (rawBroker as any)?.authenticated === false;

  const isReconnecting = rawStatus === "RECONNECTING" || rawStatus === "CONNECTING";
  const isUnverified = (rawStatus === "BROKER_STATE_UNVERIFIED" || rawStatus === "UNVERIFIED") && !isBrokerConnected;

  // Auth-required / session-expired is evaluated BEFORE "connected" so a
  // legitimate AUTH_REQUIRED / SESSION_EXPIRED / TOKEN_EXPIRED state can never be
  // silently overridden by a stale or partial "connected" read (e.g. a broker
  // socket still open while the access token has expired).
  const brokerLabel = isAuthRequired
    ? "AUTH REQUIRED"
    : isBrokerConnected
      ? "CONNECTED"
      : isReconnecting
        ? "RECONNECTING"
        : isUnverified
          ? "VERIFYING"
          : "DISCONNECTED";

  const brokerTextClass = isAuthRequired
    ? "text-[#E59700]"
    : isBrokerConnected
      ? "text-[#00C896]"
      : isReconnecting
        ? "text-[#E59700]"
        : isUnverified
          ? "text-[#8B5CF6]"
          : "text-[#E5484D]";

  const isFixture = isFixtureData || isReplayMode;

  const isLiveActual = sessionPhase === "LIVE" && !isFixture;
  const isLiveReplay = sessionPhase === "LIVE" && isFixture;
  const isNearCloseActual = sessionPhase === "NEAR_CLOSE" && !isFixture;
  const isNearCloseReplay = sessionPhase === "NEAR_CLOSE" && isFixture;

  const marketTextClass =
    isLiveActual
      ? "text-[#00C896]"
      : isLiveReplay
        ? "text-[#E59700]"
        : sessionPhase === "PRE_MARKET" || sessionPhase === "PRE_OPEN"
          ? "text-[#38BDF8]"
          : isNearCloseActual
            ? "text-[#F59E0B]"
            : "text-[#E59700]";

  const marketStatusLabel =
    isLiveActual
      ? "LIVE"
      : isLiveReplay
        ? "LIVE (REPLAY DATA)"
        : sessionPhase === "PRE_MARKET"
          ? "PRE-MARKET"
          : sessionPhase === "PRE_OPEN"
            ? "PRE-OPEN"
            : isNearCloseActual
              ? "CLOSING"
              : isNearCloseReplay
                ? "CLOSING (REPLAY DATA)"
                : "CLOSED (POST)";

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
        {/* 1. Market Status */}
        <button
          onClick={() => navigateTo({ workspace: "market", tab: "nifty", section: "market-nifty-session-summary" })}
          title={`Market Phase: ${sessionIdentity.phase_label}`}
          aria-label="Market Status"
          className="hidden sm:flex items-center gap-1.5 text-[10.5px] hover:opacity-80 transition cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#38BDF8] rounded px-1"
        >
          <span className="text-[#707987]">Market:</span>
          <span className={`font-bold uppercase tracking-tight ${marketTextClass}`}>
            {marketStatusLabel}
          </span>
        </button>

        {/* Replay Mode Badge (When in explicit replay mode only) */}
        {isReplayMode && (
          <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/40">
            REPLAY MODE
          </span>
        )}

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
            className={`flex h-8 w-8 items-center justify-center rounded-[3px] border transition cursor-pointer ${assistantOpen
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
            className={`flex h-8 w-8 items-center justify-center rounded-[3px] border transition cursor-pointer ${settingsOpen
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
          <Clock size={13} className={isDisconnected ? "text-[#E5484D]" : "text-[#38BDF8]"} />
          {isDisconnected && (
            <span className="rounded border border-[#E5484D]/40 bg-[#E5484D]/10 px-1 py-0.2 text-[8.5px] font-bold text-[#E5484D] uppercase tracking-wider">
              CLIENT TIME (DISCONNECTED)
            </span>
          )}
          <span className="text-[#707987]">{displayDate}</span>
          <span className="text-[#333942] select-none">·</span>
          <span className={`font-bold ${isDisconnected ? "text-[#E5484D]" : "text-[#38BDF8]"}`}>{displayTime}</span>
        </div>
      </div>
    </header>
  );
}

export default WorkstationTopBar;
