import React, { useState, useMemo } from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { safeNumber, formatNumber } from "../../utils/safeHelpers";

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
}: OptionChainLadderProps = {}) {
  const { optionContext, marketContext, canonicalState } = useWorkstationState() as any;
  const options = canonicalState?.option_intelligence || canonicalState?.options_intelligence || optionContext || {};
  const rawSpot = marketContext?.current_spot || options?.underlying_spot;
  const spot = rawSpot != null && Number(rawSpot) > 0 ? Number(rawSpot) : null;
  const rawStrikes = options?.strikes || options?.contracts || options?.heatmap;
  const strikes = Array.isArray(rawStrikes) ? rawStrikes : [];

  const expiry = propSelectedExpiry || options?.current_weekly_expiry || options?.expiry || "18 Aug 2026";
  const [internalSortDir, setInternalSortDir] = useState<"asc" | "desc">("asc");
  const [internalViewMode, setInternalViewMode] = useState<OptionChainViewMode>("TABLE");
  const [internalSelectedStrike, setInternalSelectedStrike] = useState<number | null>(null);

  const activeViewMode = propViewMode ?? internalViewMode;
  const setViewMode = onSelectViewMode ?? setInternalViewMode;

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
    : (spot ? Math.round(spot / 50) * 50 : null));

  const maxPain = propMaxPain ?? (options?.max_pain != null && Number(options.max_pain) > 0
    ? Number(options.max_pain)
    : null);

  const callWall = propCallWall ?? (options?.highest_call_oi_strike != null ? Number(options.highest_call_oi_strike) : 24500);
  const putWall = propPutWall ?? (options?.highest_put_oi_strike != null ? Number(options.highest_put_oi_strike) : 24300);

  const sortedStrikes = useMemo(() => {
    return [...strikes].sort((a: any, b: any) => {
      const diff = safeNumber(a.strike || a.strike_price, 0) - safeNumber(b.strike || b.strike_price, 0);
      return internalSortDir === "asc" ? diff : -diff;
    });
  }, [strikes, internalSortDir]);

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
    <div className="flex flex-col h-full space-y-1.5 text-left font-sans">
      {/* Header with Mode Switcher */}
      <div className="flex items-center justify-between border-b border-[#191D23] bg-[#0E1013] px-3 py-1.5 text-[11px] font-mono font-bold text-[#E6E8EB]">
        <div className="flex items-center gap-2">
          <span>SMART OPTION CHAIN</span>
          <span className="text-[#38BDF8] text-[10px]">[{expiry}]</span>
        </div>

        {/* View Mode Buttons */}
        <div className="flex items-center bg-[#08090B] p-0.5 rounded border border-[#191D23] text-[9.5px]">
          {(["TABLE", "HEATMAP", "CHANGE"] as OptionChainViewMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-2 py-0.5 rounded font-mono font-semibold transition-colors ${
                activeViewMode === mode
                  ? "bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/30"
                  : "text-[#707987] hover:text-[#E6E8EB]"
              }`}
            >
              {mode === "TABLE" ? "Table" : mode === "HEATMAP" ? "OI Heatmap" : "OI Change"}
            </button>
          ))}
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto flex-1 bg-[#08090B] border border-[#191D23] rounded-[2px]" tabIndex={0} aria-label="NIFTY option chain matrix">
        <table className="w-full text-[10.5px] font-mono border-collapse text-left select-none">
          <thead className="sticky top-0 z-10 bg-[#0E1013]">
            <tr className="text-[#707987] border-b border-[#191D23] text-[9.5px] uppercase font-bold">
              <th colSpan={activeViewMode === "HEATMAP" ? 2 : activeViewMode === "CHANGE" ? 3 : 5} className="p-1.5 text-center text-[#E5484D] border-r border-[#191D23] bg-[#E5484D]/10">
                CALLS (CE)
              </th>
              <th
                className="p-1.5 text-center text-[#E6E8EB] bg-[#08090B] border-r border-[#191D23] cursor-pointer hover:bg-[#13161A]"
                onClick={() => setInternalSortDir((d) => (d === "asc" ? "desc" : "asc"))}
              >
                STRIKE {internalSortDir === "asc" ? "↑" : "↓"}
              </th>
              <th colSpan={activeViewMode === "HEATMAP" ? 2 : activeViewMode === "CHANGE" ? 3 : 5} className="p-1.5 text-center text-[#00C896] bg-[#00C896]/10">
                PUTS (PE)
              </th>
            </tr>
            <tr className="bg-[#0B0D10] text-[#707987] border-b border-[#191D23] text-[8.5px] uppercase font-bold">
              {activeViewMode === "TABLE" ? (
                <>
                  <th className="p-1 text-right text-[#E5484D]">OI (Lakh)</th>
                  <th className="p-1 text-right text-[#E5484D]">ΔOI (L)</th>
                  <th className="p-1 text-right text-[#E5484D]">LTP</th>
                  <th className="p-1 text-right text-[#E5484D]">CHG %</th>
                  <th className="p-1 text-right text-[#E5484D] border-r border-[#191D23]">IV</th>
                  <th className="p-1 text-center text-[#E6E8EB] bg-[#0E1013] border-r border-[#191D23]">STRIKE</th>
                  <th className="p-1 text-left text-[#00C896]">IV</th>
                  <th className="p-1 text-left text-[#00C896]">CHG %</th>
                  <th className="p-1 text-left text-[#00C896]">LTP</th>
                  <th className="p-1 text-left text-[#00C896]">ΔOI (L)</th>
                  <th className="p-1 text-left text-[#00C896]">OI (Lakh)</th>
                </>
              ) : activeViewMode === "HEATMAP" ? (
                <>
                  <th className="p-1 text-right text-[#E5484D]">OI (Lakh)</th>
                  <th className="p-1 text-right text-[#E5484D] border-r border-[#191D23]">CALL OI CONCENTRATION</th>
                  <th className="p-1 text-center text-[#E6E8EB] bg-[#0E1013] border-r border-[#191D23]">STRIKE</th>
                  <th className="p-1 text-left text-[#00C896]">PUT OI CONCENTRATION</th>
                  <th className="p-1 text-left text-[#00C896]">OI (Lakh)</th>
                </>
              ) : (
                <>
                  <th className="p-1 text-right text-[#E5484D]">CE ΔOI (L)</th>
                  <th className="p-1 text-right text-[#E5484D]">CE LTP CHG</th>
                  <th className="p-1 text-right text-[#E5484D] border-r border-[#191D23]">CE BUILD-UP</th>
                  <th className="p-1 text-center text-[#E6E8EB] bg-[#0E1013] border-r border-[#191D23]">STRIKE</th>
                  <th className="p-1 text-left text-[#00C896]">PE BUILD-UP</th>
                  <th className="p-1 text-left text-[#00C896]">PE LTP CHG</th>
                  <th className="p-1 text-left text-[#00C896]">PE ΔOI (L)</th>
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#191D23]">
            {sortedStrikes.length === 0 ? (
              <tr>
                <td colSpan={11} className="p-8 text-center text-[#707987] italic font-mono">
                  Option chain telemetry unavailable or awaiting broker session snapshot.
                </td>
              </tr>
            ) : (
              sortedStrikes.map((s: any, i: number) => {
                const strikePx = Number(s.strike || s.strike_price);
                const isAtm = s.isAtm || (atmStrike != null && strikePx === atmStrike);
                const isMaxPain = s.isMaxPain || (maxPain != null && strikePx === maxPain);
                const isCallWall = callWall != null && strikePx === callWall;
                const isPutWall = putWall != null && strikePx === putWall;
                const isSelected = activeSelectedStrike != null && strikePx === activeSelectedStrike;

                const cOi = s.callOi ?? s.ce_oi ?? s.call_oi;
                const cChg = s.callChg ?? s.ce_oi_change ?? s.call_oi_change;
                const cLtp = s.callLtp ?? s.ce_ltp ?? s.call_ltp;
                const cChgPct = s.callChgPct ?? s.ce_change_pct;
                const cIv = s.callIv ?? s.ce_iv;

                const pIv = s.putIv ?? s.pe_iv;
                const pChgPct = s.putChgPct ?? s.pe_change_pct;
                const pLtp = s.putLtp ?? s.pe_ltp ?? s.put_ltp;
                const pChg = s.putChg ?? s.pe_oi_change ?? s.put_oi_change;
                const pOi = s.putOi ?? s.pe_oi ?? s.put_oi;

                // Heatmap percentages
                const cOiNum = safeNumber(cOi, 0);
                const pOiNum = safeNumber(pOi, 0);
                const cHeatPct = Math.min(100, Math.round((cOiNum / maxOiInChain) * 100));
                const pHeatPct = Math.min(100, Math.round((pOiNum / maxOiInChain) * 100));

                // Deterministic build-up classification
                const cChgNum = safeNumber(cChg, 0);
                const pChgNum = safeNumber(pChg, 0);
                const cBuildLabel = cChgNum > 10000 ? "OI BUILD" : cChgNum < -10000 ? "OI REDUCTION" : "UNCHANGED";
                const pBuildLabel = pChgNum > 10000 ? "OI BUILD" : pChgNum < -10000 ? "OI REDUCTION" : "UNCHANGED";

                return (
                  <tr
                    key={strikePx || i}
                    onClick={() => handleStrikeClick(strikePx)}
                    className={`cursor-pointer transition-colors text-[10px] ${
                      isSelected
                        ? "bg-[#38BDF8]/20 ring-1 ring-[#38BDF8]"
                        : isAtm
                        ? "bg-[#38BDF8]/10"
                        : "hover:bg-[#13161A]"
                    }`}
                  >
                    {activeViewMode === "TABLE" ? (
                      <>
                        {/* Call Columns */}
                        <td className="p-1 text-right text-[#E6E8EB] air-data">{formatOiLakh(cOi)}</td>
                        <td className={`p-1 text-right font-bold air-data ${cChg != null && Number(cChg) >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                          {cChg != null ? formatOiChgLakh(cChg) : "—"}
                        </td>
                        <td className="p-1 text-right font-semibold text-[#E6E8EB] air-data">{cLtp != null ? formatNumber(Number(cLtp), 2) : "—"}</td>
                        <td className={`p-1 text-right font-bold air-data ${cChgPct != null && Number(cChgPct) >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                          {cChgPct != null ? `${Number(cChgPct) >= 0 ? "+" : ""}${formatNumber(Number(cChgPct), 1)}%` : "—"}
                        </td>
                        <td className="p-1 text-right text-[#38BDF8] border-r border-[#191D23] air-data">
                          {cIv != null ? `${formatNumber(Number(cIv), 1)}%` : "—"}
                        </td>

                        {/* Center Strike Column with Smart Badges */}
                        <td className="p-1 text-center font-bold border-r border-[#191D23] bg-[#0E1013]">
                          <div className="flex items-center justify-center gap-1">
                            <span className={isAtm ? "text-[#38BDF8] font-black" : "text-[#E6E8EB]"}>{strikePx}</span>
                            {isAtm && <span className="bg-[#38BDF8]/20 text-[#38BDF8] text-[7px] px-1 py-0.2 rounded font-mono font-bold">ATM</span>}
                            {isCallWall && <span className="bg-[#E5484D]/20 text-[#E5484D] text-[7px] px-1 py-0.2 rounded font-mono font-bold">CALL WALL</span>}
                            {isPutWall && <span className="bg-[#00C896]/20 text-[#00C896] text-[7px] px-1 py-0.2 rounded font-mono font-bold">PUT WALL</span>}
                            {isMaxPain && !isAtm && <span className="bg-[#E59700]/20 text-[#E59700] text-[7px] px-1 py-0.2 rounded font-mono font-bold">MAX PAIN</span>}
                          </div>
                        </td>

                        {/* Put Columns */}
                        <td className="p-1 text-left text-[#38BDF8] air-data">{pIv != null ? `${formatNumber(Number(pIv), 1)}%` : "—"}</td>
                        <td className={`p-1 text-left font-bold air-data ${pChgPct != null && Number(pChgPct) >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                          {pChgPct != null ? `${Number(pChgPct) >= 0 ? "+" : ""}${formatNumber(Number(pChgPct), 1)}%` : "—"}
                        </td>
                        <td className="p-1 text-left font-semibold text-[#E6E8EB] air-data">{pLtp != null ? formatNumber(Number(pLtp), 2) : "—"}</td>
                        <td className={`p-1 text-left font-bold air-data ${pChg != null && Number(pChg) >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                          {pChg != null ? formatOiChgLakh(pChg) : "—"}
                        </td>
                        <td className="p-1 text-left text-[#E6E8EB] air-data">{formatOiLakh(pOi)}</td>
                      </>
                    ) : activeViewMode === "HEATMAP" ? (
                      <>
                        <td className="p-1 text-right text-[#E6E8EB] air-data">{formatOiLakh(cOi)}</td>
                        <td className="p-1 text-right border-r border-[#191D23] pr-2">
                          <div className="w-full bg-[#191D23] h-2.5 rounded overflow-hidden flex justify-end">
                            <div style={{ width: `${cHeatPct}%` }} className="h-full bg-gradient-to-l from-[#E5484D] to-[#E5484D]/40 rounded" />
                          </div>
                        </td>
                        <td className="p-1 text-center font-bold border-r border-[#191D23] bg-[#0E1013]">
                          <div className="flex items-center justify-center gap-1">
                            <span className={isAtm ? "text-[#38BDF8] font-black" : "text-[#E6E8EB]"}>{strikePx}</span>
                            {isAtm && <span className="bg-[#38BDF8]/20 text-[#38BDF8] text-[7px] px-1 py-0.2 rounded font-mono font-bold">ATM</span>}
                            {isCallWall && <span className="bg-[#E5484D]/20 text-[#E5484D] text-[7px] px-1 py-0.2 rounded font-mono font-bold">CW</span>}
                            {isPutWall && <span className="bg-[#00C896]/20 text-[#00C896] text-[7px] px-1 py-0.2 rounded font-mono font-bold">PW</span>}
                          </div>
                        </td>
                        <td className="p-1 text-left pl-2">
                          <div className="w-full bg-[#191D23] h-2.5 rounded overflow-hidden flex justify-start">
                            <div style={{ width: `${pHeatPct}%` }} className="h-full bg-gradient-to-r from-[#00C896] to-[#00C896]/40 rounded" />
                          </div>
                        </td>
                        <td className="p-1 text-left text-[#E6E8EB] air-data">{formatOiLakh(pOi)}</td>
                      </>
                    ) : (
                      <>
                        <td className={`p-1 text-right font-bold air-data ${cChgNum >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                          {cChg != null ? formatOiChgLakh(cChg) : "—"}
                        </td>
                        <td className={`p-1 text-right font-bold air-data ${cChgPct != null && Number(cChgPct) >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                          {cChgPct != null ? `${Number(cChgPct) >= 0 ? "+" : ""}${formatNumber(Number(cChgPct), 1)}%` : "—"}
                        </td>
                        <td className="p-1 text-right border-r border-[#191D23]">
                          <span className={`text-[7.5px] font-bold px-1 py-0.5 rounded ${
                            cBuildLabel === "OI BUILD" ? "bg-[#00C896]/20 text-[#00C896]" : cBuildLabel === "OI REDUCTION" ? "bg-[#E5484D]/20 text-[#E5484D]" : "text-[#707987]"
                          }`}>
                            {cBuildLabel}
                          </span>
                        </td>
                        <td className="p-1 text-center font-bold border-r border-[#191D23] bg-[#0E1013]">
                          <div className="flex items-center justify-center gap-1">
                            <span className={isAtm ? "text-[#38BDF8] font-black" : "text-[#E6E8EB]"}>{strikePx}</span>
                            {isAtm && <span className="bg-[#38BDF8]/20 text-[#38BDF8] text-[7px] px-1 py-0.2 rounded font-mono font-bold">ATM</span>}
                          </div>
                        </td>
                        <td className="p-1 text-left">
                          <span className={`text-[7.5px] font-bold px-1 py-0.5 rounded ${
                            pBuildLabel === "OI BUILD" ? "bg-[#00C896]/20 text-[#00C896]" : pBuildLabel === "OI REDUCTION" ? "bg-[#E5484D]/20 text-[#E5484D]" : "text-[#707987]"
                          }`}>
                            {pBuildLabel}
                          </span>
                        </td>
                        <td className={`p-1 text-left font-bold air-data ${pChgPct != null && Number(pChgPct) >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                          {pChgPct != null ? `${Number(pChgPct) >= 0 ? "+" : ""}${formatNumber(Number(pChgPct), 1)}%` : "—"}
                        </td>
                        <td className={`p-1 text-left font-bold air-data ${pChgNum >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                          {pChg != null ? formatOiChgLakh(pChg) : "—"}
                        </td>
                      </>
                    )}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center text-[8.5px] font-mono text-[#707987] px-1">
        <span>Click any strike row to inspect Volatility, Greeks, and Positioning delta</span>
        <span>Data Source: NSE Options, Zerodha Kite</span>
      </div>
    </div>
  );
}

export default OptionChainLadder;

