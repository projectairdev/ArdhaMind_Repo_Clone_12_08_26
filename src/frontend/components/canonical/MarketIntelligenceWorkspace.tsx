/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Canonical MARKET INTELLIGENCE Workspace.
 * Streamlined dedicated strategic planning workspace:
 * - Automatically time-routed to the active session phase strategy cockpit:
 *     - PRE_MARKET / PRE_OPEN: MorningPlanView (Expected Open, Scenario Tree, 09:15 Checklist)
 *     - LIVE / MARKET_OPEN / OPENING_RANGE / NEAR_CLOSE: LiveGuideView (Intraday Execution Directives)
 *     - POST_MARKET / MARKET_CLOSED: TomorrowPlanView (Settlement Post-Mortem & Tomorrow Roadmap)
 * - Pure dynamic binding to authoritative sessionPhase with zero stale replay leakage
 */

import React, { useState } from "react";
import { useCanonicalState } from "../../context/CanonicalStateContext";
import { MorningPlanView } from "../intelligence/MorningPlanView";
import { LiveGuideView } from "../intelligence/LiveGuideView";
import { TomorrowPlanView } from "../intelligence/TomorrowPlanView";
import { isPreviewEnabled } from "../../utils/featureFlags";

export function MarketIntelligenceWorkspace() {
  const { envelope, sessionPhase, sessionIdentity } = useCanonicalState();
  const previewAllowed = isPreviewEnabled();
  const [phaseOverride, setPhaseOverride] = useState<string>("AUTO");

  const authoritativePhase = sessionPhase ?? sessionIdentity?.sessionPhase ?? envelope?.session?.market_phase ?? "PRE_MARKET";
  const effectiveMarketPhase = (previewAllowed && phaseOverride !== "AUTO")
    ? phaseOverride
    : authoritativePhase;

  const isMorning =
    effectiveMarketPhase === "PRE_MARKET" ||
    effectiveMarketPhase === "PRE_OPEN" ||
    effectiveMarketPhase === "MORNING_PLAN";

  const isLive =
    effectiveMarketPhase === "LIVE" ||
    effectiveMarketPhase === "MARKET_OPEN" ||
    effectiveMarketPhase === "OPENING_RANGE" ||
    effectiveMarketPhase === "NEAR_CLOSE" ||
    effectiveMarketPhase === "LIVE_GUIDE";

  const isPostMarket =
    effectiveMarketPhase === "POST_MARKET" ||
    effectiveMarketPhase === "MARKET_CLOSED" ||
    effectiveMarketPhase === "TOMORROW_PLAN" ||
    (!isMorning && !isLive);

  return (
    <div className="flex flex-col gap-2 w-full bg-neutral-950 text-neutral-200 font-mono text-left select-none">
      {/* Optional Phase Preview Toolbar (Rendered strictly when VITE_ENABLE_PHASE_PREVIEW=true) */}
      {previewAllowed && (
        <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-1 bg-[#0E1013] border border-[#1E232B] rounded-[3px] text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">Active Plan:</span>
            <span className="text-[11px] font-bold text-[#38BDF8]">
              {isMorning ? "MORNING PLAN (PRE-MARKET)" : isLive ? "LIVE GUIDE (INTRADAY)" : "TOMORROW PLAN (POST-MARKET)"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[10px] text-neutral-400 uppercase font-bold">Phase Preview:</label>
            <select
              value={phaseOverride}
              onChange={(e) => setPhaseOverride(e.target.value)}
              className="bg-[#12151A] border border-[#242830] hover:border-[#38BDF8]/50 text-[#E6E8EB] text-[11px] rounded-[2px] px-2 py-0.5 focus:outline-none focus:ring-1 focus:ring-[#38BDF8]"
            >
              <option value="AUTO">AUTO (CLOCK RESOLVED)</option>
              <option value="MORNING_PLAN">MORNING PLAN (08:00 – 09:15)</option>
              <option value="LIVE_GUIDE">LIVE GUIDE (09:15 – 15:30)</option>
              <option value="TOMORROW_PLAN">TOMORROW PLAN (15:30 – 08:00)</option>
            </select>
            {phaseOverride !== "AUTO" && (
              <span className="px-1.5 py-0.5 text-[9px] font-bold tracking-wider text-amber-300 bg-amber-500/15 border border-amber-500/30 rounded-[2px] uppercase animate-pulse">
                OVERRIDE ACTIVE
              </span>
            )}
          </div>
        </div>
      )}

      {isMorning && <MorningPlanView canonicalState={envelope} />}
      {isLive && <LiveGuideView canonicalState={envelope} />}
      {isPostMarket && !isMorning && !isLive && <TomorrowPlanView canonicalState={envelope} />}
    </div>
  );
}
