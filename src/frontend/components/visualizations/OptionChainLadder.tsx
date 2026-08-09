// src/frontend/components/visualizations/OptionChainLadder.tsx
import React from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { Layers, AlertTriangle } from "lucide-react";
import { safeNumber, safeString, formatNumber } from "../../utils/safeHelpers";

export function OptionChainLadder() {
  const { optionContext, marketContext, canonicalState } = useWorkstationState() as any;
  const rawSpot = marketContext?.current_spot || optionContext?.underlying_spot;
  const rawStrikes = optionContext?.strikes;
  const strikes = Array.isArray(rawStrikes) ? rawStrikes : [];
  const quality = canonicalState?.data_quality?.option_intelligence;
  const expiry = optionContext?.current_weekly_expiry || optionContext?.expiry;
  const isAvailable = Boolean(rawSpot && quality?.source && quality?.observed_at && expiry && strikes.length > 0);

  if (!isAvailable) {
    return (
      <div className="p-6 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-left font-mono text-xs">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <AlertTriangle size={16} />
          <span>Option Chain Telemetry Matrix Unavailable</span>
        </div>
        <p className="text-slate-400">
          Option chain aggregate is not active or current expiry observation is missing. No synthetic options values displayed.
        </p>
      </div>
    );
  }

  const atmStrike = optionContext?.atm_strike != null ? safeNumber(optionContext.atm_strike, 0) : null;
  const pcr = optionContext?.pcr != null ? safeNumber(optionContext.pcr, 0) : null;
  const maxPain = optionContext?.max_pain != null ? safeNumber(optionContext.max_pain, 0) : null;

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 text-left font-sans">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Layers size={16} className="text-emerald-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">Option Chain Matrix & OI Ladder</h3>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="text-slate-400">{quality?.freshness_status === "market_closed" ? "LAST_VALID_SNAPSHOT" : String(quality?.freshness_status).toUpperCase()} · {expiry}</span>
          <span className="text-emerald-400 font-bold">PCR: {pcr != null ? formatNumber(pcr, 2) : "--"}</span>
          <span className="text-cyan-400 font-bold">Max Pain: {maxPain != null ? maxPain : "--"}</span>
          <span className="text-amber-400 font-bold">IV: {safeString(optionContext?.iv_status).toUpperCase() === "AVAILABLE" ? `${formatNumber(optionContext?.atm_iv, 2)}% ATM` : "UNAVAILABLE"}</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono border-collapse">
          <thead>
            <tr className="bg-slate-950 text-slate-400 border-b border-slate-800 text-[10px] uppercase">
              <th className="p-2 text-right text-rose-400">CALL OI</th>
              <th className="p-2 text-right text-rose-400">CALL CHG</th>
              <th className="p-2 text-right text-rose-400">CALL LTP / VOL</th>
              <th className="p-2 text-right text-rose-400">CALL IV</th>
              <th className="p-2 text-center text-white bg-slate-900">STRIKE</th>
              <th className="p-2 text-left text-emerald-400">PUT LTP / VOL</th>
              <th className="p-2 text-left text-emerald-400">PUT IV</th>
              <th className="p-2 text-left text-emerald-400">PUT CHG</th>
              <th className="p-2 text-left text-emerald-400">PUT OI</th>
            </tr>
          </thead>
          <tbody>
            {strikes.map((s) => {
              const isAtm = atmStrike != null && s.strike === atmStrike;
              const isMaxPain = maxPain != null && s.strike === maxPain;
              return (
                <tr
                  key={s.strike}
                  className={`border-b border-slate-850 hover:bg-slate-850/50 transition-colors ${
                    isAtm ? "bg-cyan-950/40 font-bold" : ""
                  }`}
                >
                  <td className="p-2 text-right text-slate-300">{formatNumber(s.callOi, 0)}</td>
                  <td className="p-2 text-right text-rose-400">{s.callChg == null ? "--" : `${s.callChg >= 0 ? "+" : ""}${formatNumber(s.callChg, 0)}`}</td>
                  <td className="p-2 text-right text-slate-400">{formatNumber(s.callLtp, 2)} / {formatNumber(s.callVolume, 0)}</td>
                  <td className="p-2 text-right text-cyan-300">{s.callIv == null ? "--" : `${formatNumber(s.callIv, 2)}%`}</td>
                  <td className={`p-2 text-center font-bold ${isAtm ? "text-cyan-300 bg-cyan-900/60" : "text-white bg-slate-900"}`}>
                    {s.strike}
                    {isAtm && <span className="text-[9px] block text-cyan-400 font-normal">ATM</span>}
                    {isMaxPain && <span className="text-[9px] block text-amber-400 font-normal">MAX PAIN</span>}
                  </td>
                  <td className="p-2 text-left text-slate-400">{formatNumber(s.putLtp, 2)} / {formatNumber(s.putVolume, 0)}</td>
                  <td className="p-2 text-left text-cyan-300">{s.putIv == null ? "--" : `${formatNumber(s.putIv, 2)}%`}</td>
                  <td className={`p-2 text-left ${s.putChg >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {s.putChg == null ? "--" : `${s.putChg >= 0 ? "+" : ""}${formatNumber(s.putChg, 0)}`}
                  </td>
                  <td className="p-2 text-left text-slate-300">{formatNumber(s.putOi, 0)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
