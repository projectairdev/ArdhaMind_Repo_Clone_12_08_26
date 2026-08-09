// src/frontend/components/visualizations/SectorPerformanceChart.tsx
import React, { useState } from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { Activity, TrendingUp, TrendingDown, PieChart } from "lucide-react";
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

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 text-left font-sans">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <PieChart size={16} className="text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">Sector Performance & Relative Strength</h3>
        </div>
        <span className="text-[10px] font-mono text-cyan-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
          Ranked by Relative Strength
        </span>
      </div>

      <div className="space-y-2.5 font-mono text-xs">
        {sectors.map((s: any, idx: number) => {
          const changePct = safeNumber(s.change_pct, 0);
          const isPositive = changePct >= 0;
          const barWidth = Math.min(100, Math.abs(changePct) * 40);
          return (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between items-center text-[11px]">
                <span className="font-bold text-white">{s.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-850">
                    {safeString(s.observation_mode || "UNAVAILABLE")}
                  </span>
                  <span className={`font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                    {isPositive ? "+" : ""}{formatNumber(changePct, 2)}%
                  </span>
                </div>
              </div>
              <div className="h-2 w-full bg-slate-950 rounded overflow-hidden flex">
                <div
                  className={`h-full rounded ${isPositive ? "bg-emerald-500" : "bg-rose-500"}`}
                  style={{ width: `${barWidth}%` }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
