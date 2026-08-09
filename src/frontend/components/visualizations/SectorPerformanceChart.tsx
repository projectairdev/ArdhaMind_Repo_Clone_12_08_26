// src/frontend/components/visualizations/SectorPerformanceChart.tsx
import React, { useState } from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { Activity, TrendingUp, TrendingDown, PieChart } from "lucide-react";
import { mapTraderEnum } from "../../utils/traderTerminology";
import { safeNumber, safeString, formatNumber } from "../../utils/safeHelpers";

export function SectorPerformanceChart() {
  const { marketContext } = useWorkstationState() as any;
  const rawSectors = marketContext?.sectors;
  const sectors = Array.isArray(rawSectors) ? rawSectors : [];
  const hasData = sectors.length > 0;

  if (!hasData) {
    return (
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 text-left font-mono text-xs">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <PieChart size={16} />
          <span>Sector Performance & Relative Strength</span>
        </div>
        <p className="text-slate-400">
          Sector performance unavailable — verified sector provider metadata unavailable.
        </p>
      </div>
    );
  }

  const firstMode = sectors[0]?.observation_mode || "LAST_SESSION";
  const allSameMode = sectors.every((s: any) => (s.observation_mode || firstMode) === firstMode);
  const commonModeLabel = mapTraderEnum(firstMode);

  return (
    <div className="rounded-lg border border-[var(--air-line)] bg-[var(--air-surface)] p-4 text-left font-sans">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <PieChart size={16} className="text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">Sector Performance & Relative Strength</h3>
        </div>
        <div className="flex items-center gap-2 font-mono text-[10px]">
          {allSameMode && (
            <span className="whitespace-nowrap rounded border border-slate-800 bg-slate-950 px-2 py-0.5 text-slate-400">
              {commonModeLabel}
            </span>
          )}
          <span className="whitespace-nowrap rounded border border-slate-800 bg-slate-950 px-2 py-0.5 text-cyan-400">
            Ranked by Relative Strength
          </span>
        </div>
      </div>

      <div className="font-mono text-xs mt-2">
        {sectors.map((s: any, idx: number) => {
          const changePct = safeNumber(s.change_pct, 0);
          const isPositive = changePct >= 0;
          const barWidth = Math.min(100, Math.abs(changePct) * 40);
          const isExceptionalRow = !allSameMode && s.observation_mode && s.observation_mode !== firstMode;
          return (
            <div key={idx} className="grid grid-cols-[minmax(7rem,1fr)_5rem_5rem] items-center gap-3 border-b border-[var(--air-line)] py-1.5 last:border-0">
              <div className="flex min-w-0 items-center justify-between text-[10px]">
                <span className="font-bold text-white truncate">{s.name}</span>
              </div>
              <div className="h-1.5 overflow-hidden bg-slate-950 rounded-full">
                <div className={`h-full ${isPositive ? "bg-emerald-500/80" : "bg-rose-500/80"}`} style={{ width: `${barWidth}%` }}/>
              </div>
              <div className="flex items-center justify-end gap-2">
                {isExceptionalRow && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800 whitespace-nowrap">
                    {mapTraderEnum(s.observation_mode)}
                  </span>
                )}
                <span className={`font-mono font-bold text-[11px] whitespace-nowrap ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                  {isPositive ? "+" : ""}{formatNumber(changePct, 2)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
