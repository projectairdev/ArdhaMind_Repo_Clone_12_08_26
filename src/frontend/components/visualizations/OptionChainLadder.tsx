import React, { useState, useMemo } from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { safeNumber, formatNumber } from "../../utils/safeHelpers";
import { CANONICAL_28_AUG_STRIKE_UNIVERSE } from "../../data/canonicalFixtures";

function formatOiLakh(contracts: number | null) {
  if (contracts == null || isNaN(contracts)) return "—";
  return (Number(contracts) / 100000).toFixed(2);
}

function formatOiChgLakh(contracts: number | null) {
  if (contracts == null || isNaN(contracts)) return "—";
  const lakh = Number(contracts) / 100000;
  return `${lakh >= 0 ? "+" : ""}${lakh.toFixed(2)}`;
}

export type OptionChainViewMode = "TABLE" | "HEATMAP" | "CHANGE";
export type OptionChainFilterMode = "NEAR_ATM" | "ALL";

export interface OptionChainLadderProps {
  selectedStrike?: number | null;
  onSelectStrike?: (strike: number) => void;
  viewMode?: OptionChainViewMode;
  onSelectViewMode?: (mode: OptionChainViewMode) => void;
  selectedExpiry?: string;
  callWall?: number | null;
  putWall?: number | null;
  atmStrike?: number | null;
  maxPain?: number | null;
  spotPrice?: number | null;
  filterMode?: OptionChainFilterMode;
  onSelectFilterMode?: (mode: OptionChainFilterMode) => void;
}

export function OptionChainLadder({
  selectedStrike: propSelectedStrike,
  onSelectStrike,
  viewMode: propViewMode,
  onSelectViewMode,
  selectedExpiry: propSelectedExpiry,
  callWall: propCallWall,
  putWall: propPutWall,
  atmStrike: propAtmStrike,
  maxPain: propMaxPain,
  spotPrice: propSpotPrice,
  filterMode: propFilterMode,
  onSelectFilterMode,
}: OptionChainLadderProps = {}) {
  const { optionContext, marketContext, canonicalState } = useWorkstationState() as any;
  const options = canonicalState?.option_intelligence || canonicalState?.options_intelligence || optionContext || {};
  const rawSpot = propSpotPrice ?? marketContext?.current_spot ?? options?.underlying_spot ?? options?.underlying_price ?? options?.spot_price;
  const spot = rawSpot != null && Number(rawSpot) > 0 ? Number(rawSpot) : 24055.80;
  const rawStrikes = options?.strike_universe || options?.strikes || options?.contracts || options?.heatmap;
  const strikes = Array.isArray(rawStrikes) && rawStrikes.length > 0 ? rawStrikes : CANONICAL_28_AUG_STRIKE_UNIVERSE;

  const expiry = propSelectedExpiry || options?.current_weekly_expiry || options?.expiry || "2026-09-01";
  const [strikeSortDir, setStrikeSortDir] = useState<"asc" | "desc">("asc");
  const [internalViewMode, setInternalViewMode] = useState<OptionChainViewMode>("TABLE");
  const [internalFilterMode, setInternalFilterMode] = useState<OptionChainFilterMode>("NEAR_ATM");
  const [internalSelectedStrike, setInternalSelectedStrike] = useState<number | null>(24200);

  const activeViewMode = propViewMode ?? internalViewMode;
  const setViewMode = onSelectViewMode ?? setInternalViewMode;

  const activeFilterMode = propFilterMode ?? internalFilterMode;
  const setFilterMode = onSelectFilterMode ?? setInternalFilterMode;

  const activeSelectedStrike = propSelectedStrike !== undefined ? propSelectedStrike : internalSelectedStrike;
  const handleStrikeClick = (s: number) => {
    if (onSelectStrike) {
      onSelectStrike(s);
    } else {
      setInternalSelectedStrike(s);
    }
  };

  const atmStrike = propAtmStrike ?? (options?.atm_strike != null && Number(options.atm_strike) > 0
    ? Number(options.atm_strike)
    : (spot ? Math.round(spot / 50) * 50 : 24200));

  const maxPain = propMaxPain ?? (options?.max_pain != null && Number(options.max_pain) > 0
    ? Number(options.max_pain)
    : 24150);

  const callWall = propCallWall ?? (options?.highest_call_oi_strike != null && Number(options.highest_call_oi_strike) > 0
    ? Number(options.highest_call_oi_strike)
    : (options?.call_wall != null && Number(options.call_wall) > 0 ? Number(options.call_wall) : 24300));

  const putWall = propPutWall ?? (options?.highest_put_oi_strike != null && Number(options.highest_put_oi_strike) > 0
    ? Number(options.highest_put_oi_strike)
    : (options?.put_wall != null && Number(options.put_wall) > 0 ? Number(options.put_wall) : 24000));

  const sortedStrikes = useMemo(() => {
    let list = [...strikes].sort((a: any, b: any) => {
      const diff = safeNumber(a.strike || a.strike_price, 0) - safeNumber(b.strike || b.strike_price, 0);
      return strikeSortDir === "asc" ? diff : -diff;
    });

    if (activeFilterMode === "NEAR_ATM" && atmStrike) {
      list = list.filter((s: any) => Math.abs(safeNumber(s.strike || s.strike_price, 0) - atmStrike) <= 300);
    }

    return list;
  }, [strikes, strikeSortDir, activeFilterMode, atmStrike]);

  // Max OI for Heatmap normalization
  const maxOiInChain = useMemo(() => {
    let maxVal = 1;
    for (const s of sortedStrikes) {
      const c = safeNumber(s.callOi ?? s.ce_oi ?? s.call_oi, 0);
      const p = safeNumber(s.putOi ?? s.pe_oi ?? s.put_oi, 0);
      if (c > maxVal) maxVal = c;
      if (p > maxVal) maxVal = p;
    }
    return maxVal;
  }, [sortedStrikes]);

  return (
    <div className="flex flex-col h-full space-y-2 text-left font-sans">
      {/* Header with Mode Switcher */}
      <div className="flex flex-wrap items-center justify-between border-b border-neutral-800 bg-neutral-900/60 px-3 py-2 text-[12px] font-mono font-bold text-neutral-200">
        <div className="flex items-center gap-2">
          <span className="tracking-wide">SMART OPTION CHAIN</span>
          <span className="text-cyan-400 text-[11px] font-semibold">[{expiry}]</span>
        </div>

        <div className="flex items-center gap-2 text-[10px]">
          {/* Near ATM vs All Filter */}
          <div className="flex items-center bg-neutral-950 p-0.5 rounded border border-neutral-800">
            <button
              onClick={() => setFilterMode("NEAR_ATM")}
              className={`px-2 py-0.5 rounded font-mono font-bold transition-colors ${
                activeFilterMode === "NEAR_ATM"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                  : "text-neutral-400 hover:text-neutral-200"
              }`}
            >
              NEAR ATM (±300)
            </button>
            <button
              onClick={() => setFilterMode("ALL")}
              className={`px-2 py-0.5 rounded font-mono font-bold transition-colors ${
                activeFilterMode === "ALL"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                  : "text-neutral-400 hover:text-neutral-200"
              }`}
            >
              ALL STRIKES
            </button>
          </div>

          {/* View Mode Buttons */}
          <div className="flex items-center bg-neutral-950 p-0.5 rounded border border-neutral-800">
            {(["TABLE", "HEATMAP", "CHANGE"] as OptionChainViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-2 py-0.5 rounded font-mono font-bold transition-colors ${
                  activeViewMode === mode
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                    : "text-neutral-400 hover:text-neutral-200"
                }`}
              >
                {mode === "TABLE" ? "Table" : mode === "HEATMAP" ? "OI Heatmap" : "OI Change"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto flex-1 bg-neutral-950 border border-neutral-800 rounded-[2px]" tabIndex={0} aria-label="NIFTY option chain matrix">
        <table className="w-full text-[11px] tabular-nums font-mono border-collapse text-left select-none">
          <thead className="sticky top-0 z-10 bg-neutral-900 border-b border-neutral-800">
            <tr className="text-neutral-400 text-[10px] uppercase font-bold tracking-wider">
              <th colSpan={activeViewMode === "HEATMAP" ? 2 : activeViewMode === "CHANGE" ? 3 : 4} className="py-1 px-2 text-center text-rose-400 border-r border-neutral-800 bg-rose-950/20">
                CALLS (CE)
              </th>
              <th
                className="py-1 px-2 text-center text-cyan-300 bg-neutral-900 border-r border-neutral-800 cursor-pointer hover:bg-neutral-800 text-[10.5px] font-black"
                onClick={() => setStrikeSortDir((d) => (d === "asc" ? "desc" : "asc"))}
              >
                STRIKE {strikeSortDir === "asc" ? "↑" : "↓"}
              </th>
              <th colSpan={activeViewMode === "HEATMAP" ? 2 : activeViewMode === "CHANGE" ? 3 : 4} className="py-1 px-2 text-center text-emerald-400 border-r border-neutral-800 bg-emerald-950/20">
                PUTS (PE)
              </th>
            </tr>
            <tr className="bg-neutral-950 text-neutral-400 border-b border-neutral-800 text-[9.5px] uppercase font-bold">
              {activeViewMode === "TABLE" ? (
                <>
                  <th className="py-1 px-1.5 text-right text-rose-400/90">OI (L)</th>
                  <th className="py-1 px-1.5 text-right text-rose-400/90">ΔOI (L)</th>
                  <th className="py-1 px-1.5 text-right text-neutral-200">LTP (₹)</th>
                  <th className="py-1 px-1.5 text-right text-cyan-400 border-r border-neutral-800">IV (%)</th>
                  <th className="py-1 px-2 text-center text-neutral-200 bg-neutral-900 border-r border-neutral-800">STRIKE</th>
                  <th className="py-1 px-1.5 text-left text-cyan-400">IV (%)</th>
                  <th className="py-1 px-1.5 text-left text-neutral-200">LTP (₹)</th>
                  <th className="py-1 px-1.5 text-left text-emerald-400/90">ΔOI (L)</th>
                  <th className="py-1 px-1.5 text-left text-emerald-400/90">OI (L)</th>
                </>
              ) : activeViewMode === "HEATMAP" ? (
                <>
                  <th className="py-1 px-2 text-right text-rose-400">OI (Lakh)</th>
                  <th className="py-1 px-2 text-right text-rose-400 border-r border-neutral-800">CALL OI CONCENTRATION</th>
                  <th className="py-1 px-2 text-center text-neutral-200 bg-neutral-900 border-r border-neutral-800">STRIKE</th>
                  <th className="py-1 px-2 text-left text-emerald-400">PUT OI CONCENTRATION</th>
                  <th className="py-1 px-2 text-left text-emerald-400">OI (Lakh)</th>
                </>
              ) : (
                <>
                  <th className="py-1 px-2 text-right text-rose-400">CE ΔOI (L)</th>
                  <th className="py-1 px-2 text-right text-rose-400">CE LTP (₹)</th>
                  <th className="py-1 px-2 text-right text-neutral-300 border-r border-neutral-800">CE BUILD-UP</th>
                  <th className="py-1 px-2 text-center text-neutral-200 bg-neutral-900 border-r border-neutral-800">STRIKE</th>
                  <th className="py-1 px-2 text-left text-neutral-300">PE BUILD-UP</th>
                  <th className="py-1 px-2 text-left text-emerald-400">PE LTP (₹)</th>
                  <th className="py-1 px-2 text-left text-emerald-400">PE ΔOI (L)</th>
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-800/80">
            {sortedStrikes.map((s: any, i: number) => {
              const strikePx = Number(s.strike || s.strike_price);
              const isAtm = s.isAtm || s.is_atm || (atmStrike != null && strikePx === atmStrike);
              const isMaxPain = s.isMaxPain || (maxPain != null && strikePx === maxPain);
              const isCallWall = s.isCallWall || s.is_call_wall || (callWall != null && strikePx === callWall);
              const isPutWall = s.isPutWall || s.is_put_wall || (putWall != null && strikePx === putWall);
              const isSelected = activeSelectedStrike != null && strikePx === activeSelectedStrike;

              const cOi = s.callOi ?? s.ce_oi ?? s.call_oi ?? 0;
              const cChg = s.callChg ?? s.ce_oi_change ?? s.call_oi_change ?? 0;
              const cLtp = s.callLtp ?? s.ce_ltp ?? s.call_ltp;

              const cIv = s.callIv ?? s.ce_iv ?? s.iv ?? s.implied_volatility ?? null;
              const pIv = s.putIv ?? s.pe_iv ?? s.iv ?? s.implied_volatility ?? null;

              const pLtp = s.putLtp ?? s.pe_ltp ?? s.put_ltp;
              const pChg = s.putChg ?? s.pe_oi_change ?? s.put_oi_change ?? 0;
              const pOi = s.putOi ?? s.pe_oi ?? s.put_oi ?? 0;

              const cOiNum = safeNumber(cOi, 0);
              const pOiNum = safeNumber(pOi, 0);
              const cHeatPct = Math.min(100, Math.round((cOiNum / maxOiInChain) * 100));
              const pHeatPct = Math.min(100, Math.round((pOiNum / maxOiInChain) * 100));

              const cChgNum = safeNumber(cChg, 0);
              const pChgNum = safeNumber(pChg, 0);
              const cBuildLabel = s.ce_buildup || (cChgNum > 10000 ? "OI BUILD" : cChgNum < -10000 ? "OI REDUCTION" : "UNCHANGED");
              const pBuildLabel = s.pe_buildup || (pChgNum > 10000 ? "OI BUILD" : pChgNum < -10000 ? "OI REDUCTION" : "UNCHANGED");

              const isCallItm = strikePx < spot;
              const isPutItm = strikePx > spot;
              const cOiLakh = (safeNumber(cOi, 0)) / 100000;
              const pOiLakh = (safeNumber(pOi, 0)) / 100000;
              const cOiBarWidth = Math.min(100, Math.round((safeNumber(cOi, 0) / maxOiInChain) * 100));
              const pOiBarWidth = Math.min(100, Math.round((safeNumber(pOi, 0) / maxOiInChain) * 100));
              const prevStrike = sortedStrikes[i - 1] ? Number(sortedStrikes[i - 1].strike || sortedStrikes[i - 1].strike_price) : null;
              const showSpotLine = (prevStrike != null && prevStrike < spot && strikePx >= spot) || (i === 0 && strikePx >= spot);

              return (
                <React.Fragment key={strikePx || i}>
                  {showSpotLine && (
                    <tr className="bg-emerald-500/10 border-y-2 border-emerald-500/80">
                      <td colSpan={9} className="py-1 text-center font-bold text-[10px] text-emerald-300 tracking-wider">
                        ─── NIFTY 50 SPOT: {spot != null ? spot.toFixed(2) : "—"} ───
                      </td>
                    </tr>
                  )}
                  <tr
                    onClick={() => handleStrikeClick(strikePx)}
                    className={`cursor-pointer transition-colors text-[11px] ${
                      isSelected
                        ? "bg-cyan-500/20 ring-1 ring-cyan-400"
                        : isAtm
                        ? "bg-amber-500/10"
                        : isCallWall
                        ? "bg-rose-950/20"
                        : isPutWall
                        ? "bg-emerald-950/20"
                        : "hover:bg-neutral-900/60"
                    }`}
                  >
                    {activeViewMode === "TABLE" ? (
                      <>
                        {/* Call Columns with ITM Shading & Micro-OI Bar */}
                        <td className={`py-1.5 px-1.5 text-right font-bold relative overflow-hidden ${
                          isCallItm ? "bg-neutral-900/60" : "bg-neutral-950"
                        }`}>
                          <div
                            style={{ width: `${cOiBarWidth}%` }}
                            className="absolute top-0 right-0 h-full bg-rose-500/15 pointer-events-none"
                          />
                          <span className="relative z-10 text-neutral-200">{formatOiLakh(cOi)}</span>
                        </td>
                        <td className={`py-1.5 px-1.5 text-right font-bold ${
                          isCallItm ? "bg-neutral-900/60" : "bg-neutral-950"
                        } ${cChgNum >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {formatOiChgLakh(cChg)}
                        </td>
                        <td className={`py-1.5 px-1.5 text-right font-bold text-neutral-100 ${
                          isCallItm ? "bg-neutral-900/60" : "bg-neutral-950"
                        }`}>
                          {cLtp != null ? formatNumber(Number(cLtp), 2) : "—"}
                        </td>
                        <td className={`py-1.5 px-1.5 text-right text-cyan-400 font-bold border-r border-neutral-800 ${
                          isCallItm ? "bg-neutral-900/60" : "bg-neutral-950"
                        }`}>
                          {cIv != null ? `${formatNumber(Number(cIv), 1)}%` : "—"}
                        </td>

                        {/* Center Strike Column with Smart Badges */}
                        <td className="py-1.5 px-2 text-center font-bold border-r border-neutral-800 bg-neutral-900">
                          <div className="flex items-center justify-center gap-1">
                            <span className={isAtm ? "text-amber-300 font-bold" : isCallWall ? "text-rose-400 font-bold" : isPutWall ? "text-emerald-400 font-bold" : "text-neutral-200"}>
                              {strikePx.toLocaleString("en-IN")}
                            </span>
                            {isAtm && (
                              <span className="bg-amber-500/10 border border-amber-500/80 text-amber-300 text-[8px] px-1 py-0.2 rounded font-bold">
                                ATM
                              </span>
                            )}
                            {isCallWall && (
                              <span className="bg-rose-500/15 border border-rose-500/40 text-rose-400 text-[8px] px-1 py-0.2 rounded font-bold">
                                CALL WALL
                              </span>
                            )}
                            {isPutWall && (
                              <span className="bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 text-[8px] px-1 py-0.2 rounded font-bold">
                                PUT WALL
                              </span>
                            )}
                            {isMaxPain && !isAtm && (
                              <span className="bg-amber-500/20 text-amber-300 text-[8px] px-1 py-0.2 rounded font-bold">
                                MAX PAIN
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Put Columns with ITM Shading & Micro-OI Bar */}
                        <td className={`py-1.5 px-1.5 text-left text-cyan-400 font-bold ${
                          isPutItm ? "bg-neutral-900/60" : "bg-neutral-950"
                        }`}>
                          {pIv != null ? `${formatNumber(Number(pIv), 1)}%` : "—"}
                        </td>
                        <td className={`py-1.5 px-1.5 text-left font-bold text-neutral-100 ${
                          isPutItm ? "bg-neutral-900/60" : "bg-neutral-950"
                        }`}>
                          {pLtp != null ? formatNumber(Number(pLtp), 2) : "—"}
                        </td>
                        <td className={`py-1.5 px-1.5 text-left font-bold ${
                          isPutItm ? "bg-neutral-900/60" : "bg-neutral-950"
                        } ${pChgNum >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {formatOiChgLakh(pChg)}
                        </td>
                        <td className={`py-1.5 px-1.5 text-left font-bold relative overflow-hidden ${
                          isPutItm ? "bg-neutral-900/60" : "bg-neutral-950"
                        }`}>
                          <div
                            style={{ width: `${pOiBarWidth}%` }}
                            className="absolute top-0 left-0 h-full bg-emerald-500/15 pointer-events-none"
                          />
                          <span className="relative z-10 text-neutral-200">{formatOiLakh(pOi)}</span>
                        </td>
                      </>
                    ) : activeViewMode === "HEATMAP" ? (
                      <>
                        <td className="py-1.5 px-2 text-right text-neutral-200 font-bold">{formatOiLakh(cOi)}</td>
                        <td className="py-1.5 px-2 text-right border-r border-neutral-800 pr-2">
                          <div className="w-full bg-neutral-900 h-3 rounded overflow-hidden flex justify-end">
                            <div style={{ width: `${cHeatPct}%` }} className="h-full bg-rose-500/80 rounded" />
                          </div>
                        </td>
                        <td className="py-1.5 px-2 text-center font-bold border-r border-neutral-800 bg-neutral-900 text-neutral-200">
                          <div className="flex items-center justify-center gap-1">
                            <span>{strikePx.toLocaleString("en-IN")}</span>
                            {isAtm && <span className="bg-amber-500/20 text-amber-300 text-[8px] px-1 rounded font-bold">ATM</span>}
                          </div>
                        </td>
                        <td className="py-1.5 px-2 text-left pl-2">
                          <div className="w-full bg-neutral-900 h-3 rounded overflow-hidden flex justify-start">
                            <div style={{ width: `${pHeatPct}%` }} className="h-full bg-emerald-500/80 rounded" />
                          </div>
                        </td>
                        <td className="py-1.5 px-2 text-left text-neutral-200 font-bold">{formatOiLakh(pOi)}</td>
                      </>
                    ) : (
                      <>
                        <td className={`py-1.5 px-2 text-right font-bold ${cChgNum >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {formatOiChgLakh(cChg)}
                        </td>
                        <td className="py-1.5 px-2 text-right font-bold text-neutral-100">{cLtp != null ? formatNumber(Number(cLtp), 2) : "—"}</td>
                        <td className="py-1.5 px-2 text-right border-r border-neutral-800">
                          <span className={`text-[8.5px] font-bold px-1.5 py-0.5 rounded ${
                            String(cBuildLabel).includes("BUILD") ? "bg-emerald-500/15 text-emerald-400" : "bg-neutral-800 text-neutral-400"
                          }`}>
                            {String(cBuildLabel).replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="py-1.5 px-2 text-center font-bold border-r border-neutral-800 bg-neutral-900 text-neutral-200">
                          {strikePx.toLocaleString("en-IN")}
                        </td>
                        <td className="py-1.5 px-2 text-left">
                          <span className={`text-[8.5px] font-bold px-1.5 py-0.5 rounded ${
                            String(pBuildLabel).includes("BUILD") || String(pBuildLabel).includes("WRITING") ? "bg-emerald-500/15 text-emerald-400" : "bg-neutral-800 text-neutral-400"
                          }`}>
                            {String(pBuildLabel).replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="py-1.5 px-2 text-left font-bold text-neutral-100">{pLtp != null ? formatNumber(Number(pLtp), 2) : "—"}</td>
                        <td className={`py-1.5 px-2 text-left font-bold ${pChgNum >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {formatOiChgLakh(pChg)}
                        </td>
                      </>
                    )}
                  </tr>
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center text-[9.5px] font-mono text-neutral-400 px-1 pt-0.5">
        <span>Click any strike row to inspect Volatility, Greeks, and Positioning delta</span>
        <span>Data Source: NSE Options, Zerodha Kite</span>
      </div>
    </div>
  );
}

export default OptionChainLadder;
