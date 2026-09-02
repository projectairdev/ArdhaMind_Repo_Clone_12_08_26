// src/frontend/components/visualizations/HeavyweightTreemap.tsx
import React from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { Layers, TrendingUp, TrendingDown } from "lucide-react";
import { formatNumber } from "../../utils/safeHelpers";

export function HeavyweightTreemap() {
  const { marketContext } = useWorkstationState() as any;
  const rawHeavyweights = marketContext?.heavyweights || marketContext?.constituents;
  const heavyweights = Array.isArray(rawHeavyweights) ? rawHeavyweights : [];
  const hasData = heavyweights.length > 0;

  if (!hasData) {
    return (
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 text-left font-mono text-xs">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <Layers size={16} />
          <span>NIFTY Heavyweight Index Impact Treemap</span>
        </div>
        <p className="text-slate-400">
          NIFTY constituent contribution unavailable — verified weight metadata unavailable.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 text-left font-sans">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Layers size={16} className="text-emerald-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">NIFTY 50 Heavyweight Index Impact Treemap</h3>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono">
        {heavyweights.map((item: any) => {
          const changePct = Number(item.change_pct ?? item.change ?? 0);
          const weight = Number(item.weight ?? 5.0);
          const niftyPrevClose = Number(marketContext?.previous_close || 0);
          const computedPts = item.pts != null ? Number(item.pts) : (niftyPrevClose > 0 ? (changePct / 100) * (weight / 100) * niftyPrevClose : null);
          const isUp = changePct >= 0;
          return (
            <div
              key={item.symbol || item.name}
              className={`p-3 rounded-lg border text-left flex flex-col justify-between ${
                isUp
                  ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-300"
                  : "bg-rose-950/40 border-rose-800/60 text-rose-300"
              }`}
            >
              <div>
                <div className="flex justify-between items-center">
                  <span className="font-extrabold text-white text-xs">{item.symbol || item.name}</span>
                  <span className="text-[9px] opacity-75 font-normal">{weight.toFixed(1)}%</span>
                </div>
                <span className="text-[10px] block opacity-80 mt-0.5 font-bold">
                  {isUp ? "+" : ""}{formatNumber(changePct, 2)}%
                </span>
              </div>
              <div className="mt-2 pt-1 border-t border-slate-800/50 flex justify-between items-baseline text-[10px]">
                <span className="opacity-70">Impact:</span>
                <span className="font-bold">
                  {isUp ? "+" : ""}{formatNumber(computedPts, 1)} pts
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
