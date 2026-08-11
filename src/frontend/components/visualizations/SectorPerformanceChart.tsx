// src/frontend/components/visualizations/SectorPerformanceChart.tsx
import React, { useState, useMemo } from "react";
import { Activity, TrendingUp, TrendingDown, PieChart } from "lucide-react";
import { mapTraderEnum } from "../../utils/traderTerminology";
import { safeNumber, safeString, formatNumber } from "../../utils/safeHelpers";

// We import useWorkstationState from context
import { useWorkstationState } from "../../context/WorkstationStateContext";

export function SectorPerformanceChart() {
  const { marketContext } = useWorkstationState() as any;
  const rawSectors = marketContext?.sectors;
  const sectors = Array.isArray(rawSectors) ? rawSectors : [];

  const [sortBy, setSortBy] = useState<"change" | "name">("change");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const hasData = sectors.length > 0;

  const sortedSectors = useMemo(() => {
    return [...sectors].sort((a: any, b: any) => {
      let diff = 0;
      if (sortBy === "name") {
        diff = safeString(a.name).localeCompare(safeString(b.name));
      } else { // change
        diff = safeNumber(a.change_pct, 0) - safeNumber(b.change_pct, 0);
      }
      if (diff === 0) {
        diff = safeString(a.name).localeCompare(safeString(b.name));
      }
      return sortDir === "desc" ? -diff : diff;
    });
  }, [sectors, sortBy, sortDir]);

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

  const handleSort = (key: typeof sortBy) => {
    if (sortBy === key) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSortBy(key);
      setSortDir(key === "name" ? "asc" : "desc");
    }
  };

  return (
    <div className="rounded-lg border border-[var(--air-line)] bg-[var(--air-surface)] p-4 text-left font-sans">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <PieChart size={16} className="text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">Sector Performance & Relative Strength</h3>
        </div>

        {/* Sorting controls */}
        <div className="flex items-center gap-1.5 font-mono text-[9px] text-slate-450">
          <span className="text-slate-500 font-bold">Sort:</span>
          <button onClick={() => handleSort("change")} className={`px-1.5 py-0.5 rounded border ${sortBy === "change" ? "border-cyan-600 bg-cyan-950/45 text-cyan-300 font-bold" : "border-slate-800 text-slate-500"}`}>
            % Change {sortBy === "change" && (sortDir === "asc" ? "↑" : "↓")}
          </button>
          <button onClick={() => handleSort("name")} className={`px-1.5 py-0.5 rounded border ${sortBy === "name" ? "border-cyan-600 bg-cyan-950/45 text-cyan-300 font-bold" : "border-slate-800 text-slate-500"}`}>
            Alphabetical {sortBy === "name" && (sortDir === "asc" ? "↑" : "↓")}
          </button>
        </div>

        <div className="flex items-center gap-2 font-mono text-[10px]">
          {allSameMode && (
            <span className="whitespace-nowrap rounded border border-slate-800 bg-slate-950 px-2 py-0.5 text-slate-400">
              {commonModeLabel}
            </span>
          )}
        </div>
      </div>

      <div className="font-mono text-xs mt-2">
        {sortedSectors.map((s: any, idx: number) => {
          const changePct = safeNumber(s.change_pct, 0);
          const isPositive = changePct >= 0;
          const barWidth = Math.min(100, Math.abs(changePct) * 40);
          const isExceptionalRow = !allSameMode && s.observation_mode && s.observation_mode !== firstMode;
          return (
            <div key={idx} className="grid grid-cols-[minmax(7rem,1fr)_5rem_5rem] items-center gap-3 border-b border-b-slate-900 py-1.5 last:border-0">
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
