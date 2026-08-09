// src/frontend/components/visualizations/OpenInterestHeatmap.tsx
import React from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { Activity, ShieldCheck } from "lucide-react";
import { safeNumber, formatNumber } from "../../utils/safeHelpers";

export function OpenInterestHeatmap() {
  const { optionContext, canonicalState } = useWorkstationState() as any;
  const rawStrikes = optionContext?.heatmap || optionContext?.strikes;
  const strikes = Array.isArray(rawStrikes) ? rawStrikes : [];
  const quality = canonicalState?.data_quality?.option_intelligence;
  const expiry = optionContext?.current_weekly_expiry || optionContext?.expiry;
  const hasData = Boolean(strikes.length > 0 && quality?.source && quality?.observed_at && expiry);

  if (!hasData) {
    return (
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 text-left font-mono text-xs">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <Activity size={16} />
          <span>Open Interest Distribution Heatmap</span>
        </div>
        <p className="text-slate-400">
          Option Telemetry = UNAVAILABLE (No validated option-chain snapshot available). No manufactured strikes or heatmaps displayed.
        </p>
      </div>
    );
  }

  const atmStrike = safeNumber(optionContext?.atm_strike, 0);

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 text-left font-sans">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-purple-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">Open Interest Distribution Heatmap</h3>
        </div>
        <div className="flex items-center gap-3 text-[10px] font-mono">
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-rose-500 inline-block"></span> Call Resistance</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-emerald-500 inline-block"></span> Put Support</span>
        </div>
      </div>

      <div className="space-y-2 font-mono text-xs">
        {strikes.map((s: any) => {
          const isAtm = s.strike === atmStrike;
          return (
            <div key={s.strike} className="space-y-1">
              <div className="flex justify-between items-center text-[10px] text-slate-400">
                <span className="font-bold text-slate-200">
                  Strike {s.strike} {isAtm ? "(ATM)" : ""}
                </span>
                <span className="text-purple-400 font-semibold">{s.label || ""}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 h-4">
                {/* CALL OI Bar */}
                <div className="bg-slate-950 rounded overflow-hidden flex justify-end">
                  <div
                    className="bg-gradient-to-l from-rose-500 to-rose-900 h-full rounded"
                    style={{ width: `${safeNumber(s.callRatio, 0) * 100}%` }}
                  ></div>
                </div>
                {/* PUT OI Bar */}
                <div className="bg-slate-950 rounded overflow-hidden flex justify-start">
                  <div
                    className="bg-gradient-to-r from-emerald-500 to-emerald-900 h-full rounded"
                    style={{ width: `${safeNumber(s.putRatio, 0) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
