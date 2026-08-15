import React, { useState } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { safeNumber, formatNumber, safeString } from "../utils/safeHelpers";
import { OptionChainLadder } from "./visualizations/OptionChainLadder";
import { OpenInterestHeatmap } from "./visualizations/OpenInterestHeatmap";
import { SemanticBadge } from "./intelligence/CanonicalPresentation";
import { PieChart } from "lucide-react";

export function OptionsWorkspace() {
  const { marketContext, canonicalState } = useWorkstationState() as any;
  const rawSpot = marketContext?.current_spot;
  const spot = rawSpot != null ? safeNumber(rawSpot, 0) : null;

  const mData = canonicalState?.market_data || {};
  const rawChange = marketContext?.spot_change ?? mData.change_points ?? mData.spot_change;
  const rawChangePct = marketContext?.spot_change_pct ?? mData.change_percent ?? mData.spot_change_pct;
  const change = safeNumber(rawChange, 0);
  const changePct = safeNumber(rawChangePct, 0);
  const isPositive = change >= 0;

  const optionsData = canonicalState?.options_intelligence || {};
  const pcr = safeNumber(optionsData.pcr ?? marketContext?.pcr, 0);
  const maxPain = safeNumber(optionsData.max_pain ?? marketContext?.max_pain, 0);

  const [activeTab, setActiveTab] = useState<"chain" | "heatmap" | "all">("all");

  return (
    <div className="space-y-4 font-sans text-left">
      <div className="rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-surface)] p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-indigo-950/60 p-2 text-indigo-400 border border-indigo-800">
              <PieChart size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white tracking-tight">NIFTY Options Command</h2>
                <SemanticBadge value={canonicalState?.market_session?.status || marketContext?.trading_session} />
              </div>
              <p className="text-[11px] text-slate-400">Canonical Option Chain & Open Interest Analytics</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
            <div className="rounded-lg bg-slate-950 px-3 py-1.5 border border-slate-800">
              <div className="text-[9px] text-slate-500 font-sans">Spot Price</div>
              <div className="text-sm font-bold text-white">{spot != null ? formatNumber(spot, 2) : "--"}</div>
              <div className={`text-[10px] font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                {isPositive ? "+" : ""}{formatNumber(change, 2)} ({isPositive ? "+" : ""}{formatNumber(changePct, 2)}%)
              </div>
            </div>

            {pcr > 0 && (
              <div className="rounded-lg bg-slate-950 px-3 py-1.5 border border-slate-800">
                <div className="text-[9px] text-slate-500 font-sans">PCR (OI)</div>
                <div className="text-sm font-bold text-cyan-300">{formatNumber(pcr, 2)}</div>
                <div className="text-[10px] text-slate-400 font-sans">{pcr > 1.2 ? "Bullish Sentiment" : pcr < 0.8 ? "Bearish Sentiment" : "Neutral"}</div>
              </div>
            )}

            {maxPain > 0 && (
              <div className="rounded-lg bg-slate-950 px-3 py-1.5 border border-slate-800">
                <div className="text-[9px] text-slate-500 font-sans">Max Pain</div>
                <div className="text-sm font-bold text-amber-300">{formatNumber(maxPain, 0)}</div>
                <div className="text-[10px] text-slate-400 font-sans font-mono">Key Expiry Anchor</div>
              </div>
            )}
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-1 rounded-lg bg-slate-950 p-1 border border-slate-800 text-[11px] font-semibold">
            <button
              onClick={() => setActiveTab("all")}
              className={`rounded-md px-3 py-1 transition ${
                activeTab === "all" ? "bg-cyan-950 text-cyan-300 border border-cyan-800" : "text-slate-400 hover:text-white"
              }`}
            >
              Unified Chain & Heatmap
            </button>
            <button
              onClick={() => setActiveTab("chain")}
              className={`rounded-md px-3 py-1 transition ${
                activeTab === "chain" ? "bg-cyan-950 text-cyan-300 border border-cyan-800" : "text-slate-400 hover:text-white"
              }`}
            >
              Option Chain Ladder
            </button>
            <button
              onClick={() => setActiveTab("heatmap")}
              className={`rounded-md px-3 py-1 transition ${
                activeTab === "heatmap" ? "bg-cyan-950 text-cyan-300 border border-cyan-800" : "text-slate-400 hover:text-white"
              }`}
            >
              OI Distribution Heatmap
            </button>
          </div>
          <div className="hidden sm:block text-[10px] font-mono text-slate-500">
            Source: Kite Live Option Stream & Canonical State
          </div>
        </div>
      </div>

      {(activeTab === "all" || activeTab === "chain") && (
        <div className="rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-surface)] p-4">
          <OptionChainLadder />
        </div>
      )}

      {(activeTab === "all" || activeTab === "heatmap") && (
        <div className="rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-surface)] p-4">
          <OpenInterestHeatmap />
        </div>
      )}
    </div>
  );
}
