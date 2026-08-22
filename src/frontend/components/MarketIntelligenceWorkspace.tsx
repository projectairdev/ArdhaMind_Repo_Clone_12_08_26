// src/frontend/components/MarketIntelligenceWorkspace.tsx
import React, { useMemo, useState, useEffect } from "react";
import {
  Sun,
  Activity,
  Calendar,
  ChevronDown,
} from "lucide-react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  MarketIntelligencePreviewMode,
  MarketIntelligenceSubTab,
  resolveMarketIntelligenceSession,
} from "../viewmodels/session/MarketIntelligenceSessionResolver";
import { buildSessionViewModels } from "../viewmodels/session/buildSessionViewModels";
import { MorningPlanView } from "./intelligence/MorningPlanView";
import { LiveGuideView } from "./intelligence/LiveGuideView";
import { TomorrowPlanView } from "./intelligence/TomorrowPlanView";
import { TemporalContextStrip } from "./ui/TemporalContextStrip";

export function MarketIntelligenceWorkspace() {
  const { canonicalState, lastValidState, marketContext, optionContext } = useWorkstationState() as any;
  const [previewMode, setPreviewMode] = useState<MarketIntelligencePreviewMode>("AUTO");
  const [selectedSubTab, setSelectedSubTab] = useState<MarketIntelligenceSubTab | null>(null);
  const [tick, setTick] = useState(0);

  // Periodic 1-second refresh for clock and time boundary transitions
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  // Reactive state binding to canonical state and live tick overlays
  const rawState = useMemo(() => {
    const base = canonicalState ?? lastValidState ?? {};
    return {
      ...base,
      marketContext: marketContext ?? base.marketContext ?? base.market_data,
      optionContext: optionContext ?? base.optionContext ?? base.option_intelligence,
    };
  }, [canonicalState, lastValidState, marketContext, optionContext]);

  // Resolve session timing and default subtab
  const sessionTiming = useMemo(() => {
    return resolveMarketIntelligenceSession({
      marketSessionState: rawState.market_session,
      previewMode: previewMode,
    });
  }, [rawState.market_session, previewMode, tick]);

  // Active subtab respects user manual tab click during current session or defaults to resolved
  const activeSubTab: MarketIntelligenceSubTab =
    previewMode !== "AUTO"
      ? (previewMode as MarketIntelligenceSubTab)
      : selectedSubTab ?? sessionTiming.effectiveSubTab;

  // Build the 3 specialized session view models
  const { morningPlan, liveGuide, tomorrowPlan } = useMemo(() => {
    return buildSessionViewModels(rawState, {
      isClosedSession: sessionTiming.isClosedSession,
      previewMode,
      marketStatusText: sessionTiming.marketStatusText,
    });
  }, [rawState, sessionTiming.isClosedSession, previewMode, sessionTiming.marketStatusText]);

  return (
    <div
      data-testid="market-intelligence-workspace"
      className="space-y-2.5 font-sans text-left text-[#E6E8EB]"
    >
      {/* ── TEMPORAL CONTEXT STRIP ── */}
      <TemporalContextStrip canonicalState={rawState} customTitle="Institutional Market Intelligence & Scenarios" />

      {/* ─────────────────────────────────────────────────────────────
          COMPACT SUBTAB ROW & PREVIEW SELECTOR (MATCHING MARKET)
      ───────────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#191D23] bg-[#0B0D10] p-1.5 rounded-[3px] border border-[#242830]">
        {/* Subtabs */}
        <div className="flex items-center gap-1 bg-[#08090B] p-0.5 rounded-[2px] border border-[#191D23]">
          <button
            type="button"
            onClick={() => {
              setSelectedSubTab("MORNING_PLAN");
              if (previewMode !== "AUTO") setPreviewMode("MORNING_PLAN");
            }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-[2px] text-[11px] font-bold font-mono tracking-wider transition ${
              activeSubTab === "MORNING_PLAN"
                ? "bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8]"
                : "text-[#707987] hover:text-[#E6E8EB] border border-transparent"
            }`}
          >
            <Sun size={12} />
            <span>MORNING PLAN</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setSelectedSubTab("LIVE_GUIDE");
              if (previewMode !== "AUTO") setPreviewMode("LIVE_GUIDE");
            }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-[2px] text-[11px] font-bold font-mono tracking-wider transition ${
              activeSubTab === "LIVE_GUIDE"
                ? "bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8]"
                : "text-[#707987] hover:text-[#E6E8EB] border border-transparent"
            }`}
          >
            <Activity size={12} />
            <span>LIVE GUIDE</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setSelectedSubTab("TOMORROW_PLAN");
              if (previewMode !== "AUTO") setPreviewMode("TOMORROW_PLAN");
            }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-[2px] text-[11px] font-bold font-mono tracking-wider transition ${
              activeSubTab === "TOMORROW_PLAN"
                ? "bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8]"
                : "text-[#707987] hover:text-[#E6E8EB] border border-transparent"
            }`}
          >
            <Calendar size={12} />
            <span>TOMORROW PLAN</span>
          </button>
        </div>

        {/* Preview Selector */}
        <div className="flex items-center gap-1.5 text-[11px] font-mono">
          <span className="text-[#707987] text-[10px] font-semibold uppercase">Preview:</span>
          <div className="relative">
            <select
              value={previewMode}
              onChange={(e) => {
                const val = e.target.value as MarketIntelligencePreviewMode;
                setPreviewMode(val);
                if (val !== "AUTO") {
                  setSelectedSubTab(val as MarketIntelligenceSubTab);
                } else {
                  setSelectedSubTab(null);
                }
              }}
              className="appearance-none bg-[#08090B] text-[11px] font-mono font-bold text-[#E6E8EB] px-2.5 py-1 pr-6 rounded-[2px] border border-[#242830] hover:border-[#38BDF8]/40 focus:outline-none focus:border-[#38BDF8]"
            >
              <option value="AUTO">AUTO ({sessionTiming.autoResolvedSubTab.replace("_", " ")})</option>
              <option value="MORNING_PLAN">MORNING PLAN</option>
              <option value="LIVE_GUIDE">LIVE GUIDE</option>
              <option value="TOMORROW_PLAN">TOMORROW PLAN</option>
            </select>
            <ChevronDown size={11} className="text-[#707987] absolute right-1.5 top-2 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          ACTIVE SUBVIEW RENDERING
      ───────────────────────────────────────────────────────────── */}
      <div className="pt-0.5">
        {activeSubTab === "MORNING_PLAN" && <MorningPlanView vm={morningPlan} />}
        {activeSubTab === "LIVE_GUIDE" && <LiveGuideView vm={liveGuide} />}
        {activeSubTab === "TOMORROW_PLAN" && <TomorrowPlanView vm={tomorrowPlan} />}
      </div>
    </div>
  );
}

export default MarketIntelligenceWorkspace;
