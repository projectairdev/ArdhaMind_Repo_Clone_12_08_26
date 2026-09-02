/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Canonical NIFTY Workspace (4-Mode Trader Taxonomy).
 * Automatically time-routed by dual-clock authority (sessionPhase / intelligenceMode).
 * Modes:
 * 1. MORNING (Pre-Market / Pre-Open)
 * 2. OPENING (Opening Range)
 * 3. LIVE (Regular Live / Near Close)
 * 4. POST-MARKET (Completed Session Review)
 */

import React, { useState } from "react";
import { useCanonicalState } from "../../context/CanonicalStateContext";
import { MorningWorkspace } from "./nifty/MorningWorkspace";
import { OpeningWorkspace } from "./nifty/OpeningWorkspace";
import { LiveWorkspace } from "./nifty/LiveWorkspace";
import { PostMarketWorkspace } from "./nifty/PostMarketWorkspace";
import { isPreviewEnabled } from "../../utils/featureFlags";

export type SessionPhaseOverride = "AUTO" | "PRE_MARKET" | "LIVE" | "POST_MARKET";

export function MarketWorkspace() {
  const { envelope, traderMode, sessionPhase, intelligenceMode } = useCanonicalState();
  const [phaseOverride, setPhaseOverride] = useState<SessionPhaseOverride>("AUTO");
  const previewAllowed = isPreviewEnabled();

  const effectivePhase = (previewAllowed && phaseOverride !== "AUTO")
    ? phaseOverride
    : (sessionPhase ?? "PRE_MARKET");

  const isOpening =
    (!previewAllowed || phaseOverride === "AUTO") &&
    (traderMode === "OPENING" ||
     (sessionPhase === "LIVE" && intelligenceMode === "OPEN_VALIDATION"));

  const isLive =
    effectivePhase === "LIVE" ||
    ((!previewAllowed || phaseOverride === "AUTO") &&
     (traderMode === "LIVE" ||
      (sessionPhase === "LIVE" && !isOpening) ||
      sessionPhase === "NEAR_CLOSE"));

  const isPostMarket =
    effectivePhase === "POST_MARKET" ||
    ((!previewAllowed || phaseOverride === "AUTO") &&
     !isOpening &&
     !isLive &&
     (traderMode === "POST_MARKET" || sessionPhase === "POST_MARKET" || sessionPhase === "MARKET_CLOSED"));

  const isMorning =
    effectivePhase === "PRE_MARKET" ||
    (!isOpening && !isLive && !isPostMarket);

  return (
    <div className="flex flex-col gap-1.5 p-1.5 sm:p-2 bg-[#08090B] text-[#E6E8EB] min-h-screen font-mono select-none">
      {/* Optional Phase Preview Toolbar Strip (Conditional via VITE_ENABLE_PHASE_PREVIEW) */}
      {previewAllowed && (
        <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-1.5 bg-[#0E1013] border border-[#1E232B] rounded-[3px] text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#707987]">
              Active Phase:
            </span>
            <span className="text-[11px] font-bold text-[#38BDF8]">
              {effectivePhase === "LIVE" ? "LIVE MARKET" : effectivePhase === "POST_MARKET" ? "POST-MARKET" : "PRE-MARKET"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-[10px] uppercase text-[#707987]">Phase Preview:</label>
            <select
              value={phaseOverride}
              onChange={(e) => setPhaseOverride(e.target.value as SessionPhaseOverride)}
              className="bg-[#12151A] border border-[#242830] hover:border-[#38BDF8]/50 text-[#E6E8EB] text-[11px] rounded-[2px] px-2 py-0.5 focus:outline-none focus:ring-1 focus:ring-[#38BDF8]"
            >
              <option value="AUTO">AUTO (CLOCK RESOLVED)</option>
              <option value="PRE_MARKET">PRE-MARKET (08:00 – 09:15)</option>
              <option value="LIVE">LIVE MARKET (09:15 – 15:30)</option>
              <option value="POST_MARKET">POST-MARKET (15:30 – 08:00)</option>
            </select>

            {phaseOverride !== "AUTO" && (
              <span className="px-1.5 py-0.5 text-[9px] font-bold tracking-wider text-amber-300 bg-amber-500/15 border border-amber-500/30 rounded-[2px] uppercase animate-pulse">
                OVERRIDE ACTIVE
              </span>
            )}
          </div>
        </div>
      )}

      {/* 4-MODE DISPATCH */}
      {isMorning ? (
        <MorningWorkspace envelope={envelope} />
      ) : isOpening ? (
        <OpeningWorkspace envelope={envelope} />
      ) : isLive ? (
        <LiveWorkspace envelope={envelope} />
      ) : (
        <PostMarketWorkspace envelope={envelope} />
      )}
    </div>
  );
}
