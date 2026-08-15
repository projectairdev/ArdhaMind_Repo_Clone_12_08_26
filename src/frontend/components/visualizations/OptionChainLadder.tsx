import React, { useState, useMemo } from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { Layers, AlertTriangle } from "lucide-react";
import { safeNumber, safeString, formatNumber } from "../../utils/safeHelpers";
import { formatTimestampIST } from "../../utils/timeFormatting";

export function OptionChainLadder() {
  const { optionContext, marketContext, canonicalState } = useWorkstationState() as any;
  const rawSpot = marketContext?.current_spot || optionContext?.underlying_spot;
  const spot = rawSpot != null ? safeNumber(rawSpot, 0) : 0;
  const rawStrikes = optionContext?.strikes;
  const strikes = Array.isArray(rawStrikes) ? rawStrikes : [];
  const quality = canonicalState?.data_quality?.option_intelligence;
  const expiry = optionContext?.current_weekly_expiry || optionContext?.expiry;

  const [strikeSortDir, setStrikeSortDir] = useState<"asc" | "desc">("asc");

  const isAvailable = Boolean(rawSpot && quality?.source && quality?.observed_at && expiry && strikes.length > 0);

  const sortedStrikes = useMemo(() => {
    return [...strikes].sort((a: any, b: any) => {
      const diff = safeNumber(a.strike) - safeNumber(b.strike);
      return strikeSortDir === "asc" ? diff : -diff;
    });
  }, [strikes, strikeSortDir]);

  if (!isAvailable) {
    return (
      <div className="p-5 bg-[var(--air-surface)] border border-[var(--air-line-strong)] rounded-xl space-y-2 text-left font-mono text-xs">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <AlertTriangle size={15} />
          <span>Option Chain Telemetry Matrix Unavailable</span>
        </div>
        <p className="text-slate-400 text-[11px]">
          Option chain aggregate is not active or current expiry observation is missing. Connect Kite broker or await snapshot.
        </p>
      </div>
    );
  }

  const atmStrike = optionContext?.atm_strike != null ? safeNumber(optionContext.atm_strike, 0) : null;
  const pcr = optionContext?.pcr != null ? safeNumber(optionContext.pcr, 0) : null;
  const maxPain = optionContext?.max_pain != null ? safeNumber(optionContext.max_pain, 0) : null;
  const obsTime = quality?.observed_at ? formatTimestampIST(quality.observed_at) : "UNAVAILABLE";

  return (
    <div className="space-y-3 text-left font-sans">
      <div className="flex flex-col gap-2 border-b border-slate-800 pb-2.5 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-2">
          <Layers size={16} className="text-indigo-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">
            NIFTY Option Chain Matrix <span className="text-[9px] text-slate-400 font-normal">({expiry})</span>
          </h3>
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-mono text-slate-400">
          <span>Observed: {obsTime}</span>
          <span className="text-emerald-400 font-bold">PCR: {pcr != null ? formatNumber(pcr, 2) : "--"}</span>
          <span className="text-amber-400 font-bold">Max Pain: {maxPain != null ? maxPain : "--"}</span>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950" tabIndex={0} aria-label="Scrollable NIFTY option chain">
        <table className="w-full text-xs font-mono border-collapse">
          <thead>
            <tr className="bg-slate-900/90 text-slate-400 border-b border-slate-800 text-[10px] uppercase font-bold tracking-wider">
              <th colSpan={4} className="p-1.5 text-center text-rose-400 border-r border-slate-800 bg-rose-950/20">CALLS (CE)</th>
              <th
                className="p-1.5 text-center text-white bg-slate-900 border-r border-slate-800 cursor-pointer select-none"
                onClick={() => setStrikeSortDir(d => d === "asc" ? "desc" : "asc")}
              >
                STRIKE {strikeSortDir === "asc" ? "↑" : "↓"}
              </th>
              <th colSpan={4} className="p-1.5 text-center text-emerald-400 bg-emerald-950/20">PUTS (PE)</th>
            </tr>
            <tr className="bg-slate-950 text-slate-400 border-b border-slate-800 text-[9px] uppercase">
              <th className="p-1.5 text-right text-rose-400">CALL OI</th>
              <th className="p-1.5 text-right text-rose-400">CALL CHG</th>
              <th className="p-1.5 text-right text-rose-400">LTP / VOL</th>
              <th className="p-1.5 text-right text-rose-400 border-r border-slate-800">IV</th>
              <th className="p-1.5 text-center text-white bg-slate-900 border-r border-slate-800">PRICE</th>
              <th className="p-1.5 text-left text-emerald-400">LTP / VOL</th>
              <th className="p-1.5 text-left text-emerald-400">IV</th>
              <th className="p-1.5 text-left text-emerald-400">PUT CHG</th>
              <th className="p-1.5 text-left text-emerald-400">PUT OI</th>
            </tr>
          </thead>
          <tbody>
            {sortedStrikes.map((s) => {
              const isAtm = atmStrike != null && s.strike === atmStrike;
              const isMaxPain = maxPain != null && s.strike === maxPain;
              const isCallItm = spot > 0 && s.strike < spot;
              const isPutItm = spot > 0 && s.strike > spot;

              return (
                <tr
                  key={s.strike}
                  className={`border-b border-slate-900 transition-colors text-[11px] ${
                    isAtm
                      ? "bg-cyan-950/60 font-bold border-y border-cyan-500/50"
                      : isCallItm && isPutItm
                      ? "bg-slate-900/40"
                      : isCallItm
                      ? "bg-rose-950/15"
                      : isPutItm
                      ? "bg-emerald-950/15"
                      : "hover:bg-slate-900/60"
                  }`}
                >
                  {/* Call Columns */}
                  <td className="p-1.5 text-right text-slate-300">{formatNumber(s.callOi, 0)}</td>
                  <td className={`p-1.5 text-right font-bold ${s.callChg >= 0 ? "text-rose-400" : "text-emerald-400"}`}>
                    {s.callChg == null ? "--" : `${s.callChg >= 0 ? "+" : ""}${formatNumber(s.callChg, 0)}`}
                  </td>
                  <td className="p-1.5 text-right text-slate-400">
                    <span className="text-white font-semibold">{formatNumber(s.callLtp, 2)}</span>
                    <span className="text-[9px] text-slate-500 ml-1">({formatNumber(s.callVolume, 0)})</span>
                  </td>
                  <td className="p-1.5 text-right text-cyan-300 border-r border-slate-800">
                    {s.callIv == null ? "--" : `${formatNumber(s.callIv, 1)}%`}
                  </td>

                  {/* Center Strike Column */}
                  <td
                    className={`p-1.5 text-center font-bold border-r border-slate-800 ${
                      isAtm
                        ? "text-cyan-300 bg-cyan-900/80"
                        : isMaxPain
                        ? "text-amber-300 bg-amber-950/60"
                        : "text-white bg-slate-900"
                    }`}
                  >
                    {s.strike}
                    {isAtm && <span className="text-[8px] block text-cyan-300 font-extrabold uppercase">ATM</span>}
                    {isMaxPain && !isAtm && <span className="text-[8px] block text-amber-300 font-extrabold uppercase">MAX PAIN</span>}
                  </td>

                  {/* Put Columns */}
                  <td className="p-1.5 text-left text-slate-400">
                    <span className="text-white font-semibold">{formatNumber(s.putLtp, 2)}</span>
                    <span className="text-[9px] text-slate-500 ml-1">({formatNumber(s.putVolume, 0)})</span>
                  </td>
                  <td className="p-1.5 text-left text-cyan-300">
                    {s.putIv == null ? "--" : `${formatNumber(s.putIv, 1)}%`}
                  </td>
                  <td className={`p-1.5 text-left font-bold ${s.putChg >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {s.putChg == null ? "--" : `${s.putChg >= 0 ? "+" : ""}${formatNumber(s.putChg, 0)}`}
                  </td>
                  <td className="p-1.5 text-left text-slate-300">{formatNumber(s.putOi, 0)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default OptionChainLadder;
