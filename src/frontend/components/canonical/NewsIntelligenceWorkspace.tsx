/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * NewsIntelligenceWorkspace.tsx
 * Flagship Bloomberg-Style News & Macro Intelligence Workspace.
 * 
 * Houses:
 * - LIVE NEWS (LiveNewsFeedView)
 * - CATALYSTS (CatalystsMatrixView)
 * - CALENDAR (EconomicCalendarView)
 * 
 * Features:
 * - Secondary Sub-Tab Navigation Bar
 */

import React, { useState, useEffect } from "react";
import { Radio, Zap, Calendar as CalendarIcon } from "lucide-react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { getCanonicalNewsPresentation } from "../../utils/canonicalNewsAdapter";
import { LiveNewsFeedView } from "../news/LiveNewsFeedView";
import { CatalystsMatrixView } from "../news/CatalystsMatrixView";
import { EconomicCalendarView } from "../news/EconomicCalendarView";

export type NewsIntelligenceViewMode = "LIVE_NEWS" | "CATALYSTS" | "CALENDAR";

export interface NewsIntelligenceWorkspaceProps {
  initialView?: NewsIntelligenceViewMode;
  onViewChange?: (view: NewsIntelligenceViewMode) => void;
}

export const NewsIntelligenceWorkspace: React.FC<NewsIntelligenceWorkspaceProps> = ({
  initialView = "LIVE_NEWS",
  onViewChange,
}) => {
  const { canonicalState, lastValidState, marketContext } = useWorkstationState() as any;
  const state = canonicalState ?? lastValidState ?? {};
  const pres = getCanonicalNewsPresentation(state, marketContext);

  const [activeView, setActiveView] = useState<NewsIntelligenceViewMode>(initialView);

  useEffect(() => {
    if (initialView) {
      setActiveView(initialView);
    }
  }, [initialView]);

  const setView = (v: NewsIntelligenceViewMode) => {
    setActiveView(v);
    onViewChange?.(v);
  };

  return (
    <div className="w-full flex flex-col gap-2 font-mono text-left select-none text-xs bg-neutral-950 p-2.5">
      {/* ── TOP SECONDARY SUB-TAB BAR ── */}
      <div className="flex items-center justify-between border-b border-neutral-800 pb-2 px-1 text-[11px] font-bold">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView("LIVE_NEWS")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded transition-all ${
              activeView === "LIVE_NEWS"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                : "text-neutral-400 hover:text-neutral-200 border border-transparent"
            }`}
          >
            <Radio className="w-3.5 h-3.5 text-rose-500" />
            <span>LIVE NEWS</span>
          </button>

          <button
            onClick={() => setView("CATALYSTS")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded transition-all ${
              activeView === "CATALYSTS"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                : "text-neutral-400 hover:text-neutral-200 border border-transparent"
            }`}
          >
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>CATALYSTS</span>
          </button>

          <button
            onClick={() => setView("CALENDAR")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded transition-all ${
              activeView === "CALENDAR"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                : "text-neutral-400 hover:text-neutral-200 border border-transparent"
            }`}
          >
            <CalendarIcon className="w-3.5 h-3.5 text-blue-400" />
            <span>CALENDAR</span>
          </button>
        </div>
      </div>

      {/* ── ACTIVE VIEW CONTAINER ── */}
      <div className="w-full">
        {activeView === "LIVE_NEWS" && (
          <LiveNewsFeedView
            pres={pres}
            onSelectSubTab={(tab) => {
              if (tab === "live_news") setView("LIVE_NEWS");
              if (tab === "catalysts") setView("CATALYSTS");
              if (tab === "calendar") setView("CALENDAR");
            }}
          />
        )}
        {activeView === "CATALYSTS" && <CatalystsMatrixView pres={pres} />}
        {activeView === "CALENDAR" && <EconomicCalendarView pres={pres} />}
      </div>
    </div>
  );
};

export default NewsIntelligenceWorkspace;
