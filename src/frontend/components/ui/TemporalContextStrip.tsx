// src/frontend/components/ui/TemporalContextStrip.tsx
import React from "react";
import { Calendar, ShieldCheck, AlertCircle, Sparkles } from "lucide-react";
import { useCanonicalState } from "../../context/CanonicalStateContext";
import { resolveCanonicalSessionIdentity } from "../../session/sessionPhaseEngine";

export function TemporalContextStrip({
  canonicalState,
  previewMode,
  customTitle,
}: {
  canonicalState?: any;
  previewMode?: "PRE" | "LIVE" | "POST";
  customTitle?: string;
}) {
  let canonicalContext: any = null;
  try {
    canonicalContext = useCanonicalState();
  } catch {
    // Context unavailable, fall back to standalone resolver
  }

  const identity = canonicalContext?.sessionIdentity || resolveCanonicalSessionIdentity({
    canonicalState,
  });

  const isFixture =
    canonicalContext?.isFixtureData ??
    (canonicalContext?.isReplayMode || identity.is_replay_mode);

  const isLiveActual = identity.sessionPhase === "LIVE" && !isFixture;
  const isLiveReplay = identity.sessionPhase === "LIVE" && isFixture;
  const isPre = identity.sessionPhase === "PRE_MARKET" || identity.sessionPhase === "PRE_OPEN";
  const isPost = identity.sessionPhase === "POST_MARKET";

  const statusColor = isLiveActual
    ? "text-[#00C896]"
    : isLiveReplay
    ? "text-[#E59700]"
    : isPre
    ? "text-[#38BDF8]"
    : "text-[#8B5CF6]";

  const dotClass = isLiveActual
    ? "bg-[#00C896] animate-pulse"
    : isLiveReplay
    ? "bg-[#E59700]"
    : isPre
    ? "bg-[#38BDF8]"
    : "bg-[#8B5CF6]";

  const marketPhaseDisplay = isLiveActual
    ? "LIVE"
    : isLiveReplay
    ? "LIVE (REPLAY DATA)"
    : identity.sessionPhase.replace(/_/g, "-");

  const dataWindowNotice =
    identity.data_window === "SETTLED_COMPLETED"
      ? `BASELINE: ${identity.completed_session_date_formatted} SETTLED`
      : identity.data_window === "PRE_OPEN_AUCTION"
      ? `PRE-OPEN AUCTION INDICATIVE`
      : `LIVE SESSION SO FAR (${identity.active_trading_date_formatted})`;

  return (
    <div
      id="temporal-context-strip"
      className="bg-[#0B0D10] border border-[#191D23] rounded-[2px] px-2 py-1 font-mono text-[9.5px] flex flex-wrap items-center justify-between gap-1.5"
    >
      {/* Left: Compact Context Badges */}
      <div className="flex flex-wrap items-center gap-1.5">
        {customTitle && (
          <span className="text-[#A5ABB4] font-bold text-[9.5px] mr-1 hidden sm:inline">
            {customTitle}
          </span>
        )}

        <div className="flex items-center gap-1 bg-[#0E1013] border border-[#191D23] px-1.5 py-0.2 rounded-[2px]">
          <span className={`h-1.5 w-1.5 rounded-full ${dotClass}`} />
          <span className={`font-bold uppercase tracking-wider ${statusColor} text-[9px]`}>
            {marketPhaseDisplay}
          </span>
        </div>

        <span className="bg-purple-500/10 border border-purple-500/25 text-purple-300 px-1.5 py-0.2 rounded-[2px] font-bold uppercase text-[8.5px] flex items-center gap-1">
          <Sparkles size={9} className="text-purple-400" />
          {identity.intelligenceMode.replace(/_/g, " ")}
        </span>

        <span className="bg-[#E59700]/10 border border-[#E59700]/25 text-[#E59700] px-1.5 py-0.2 rounded-[2px] font-bold uppercase text-[8.5px] flex items-center gap-1">
          <AlertCircle size={9} />
          {dataWindowNotice}
        </span>
      </div>

      {/* Right: Settled Baseline Reference (No duplicate clock) */}
      <div className="flex items-center gap-2 text-[9px] text-[#707987]">
        <div className="flex items-center gap-1">
          <Calendar size={10} className="text-[#38BDF8]" />
          <span>Settled:</span>
          <span className="font-bold text-[#E6E8EB]">{identity.completed_session_date_formatted}</span>
        </div>

        <div className="flex items-center gap-1">
          <span>Target:</span>
          <span className="font-bold text-[#00C896]">{identity.next_trading_date_formatted}</span>
        </div>
      </div>
    </div>
  );
}

export default TemporalContextStrip;
