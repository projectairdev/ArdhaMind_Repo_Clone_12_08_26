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

export function OptionChainLadder() {
  const { optionContext, marketContext, canonicalState } = useWorkstationState() as any;
  const rawSpot = marketContext?.current_spot || optionContext?.underlying_spot;
  const spot = rawSpot != null && Number(rawSpot) > 0 ? Number(rawSpot) : null;
  const rawStrikes = optionContext?.strikes || optionContext?.contracts;
  const strikes = Array.isArray(rawStrikes) ? rawStrikes : [];

  const expiry = optionContext?.current_weekly_expiry || optionContext?.expiry || "18 Aug 2026";
  const [strikeSortDir, setStrikeSortDir] = useState<"asc" | "desc">("asc");

  const sortedStrikes = useMemo(() => {
    return [...strikes].sort((a: any, b: any) => {
      const diff = safeNumber(a.strike || a.strike_price, 0) - safeNumber(b.strike || b.strike_price, 0);
      return strikeSortDir === "asc" ? diff : -diff;
    });
  }, [strikes, strikeSortDir]);

  const atmStrike = optionContext?.atm_strike != null && Number(optionContext.atm_strike) > 0
    ? Number(optionContext.atm_strike)
    : (spot ? Math.round(spot / 50) * 50 : null);
  const maxPain = optionContext?.max_pain != null && Number(optionContext.max_pain) > 0
    ? Number(optionContext.max_pain)
    : null;

  return (
    <div className="space-y-2 text-left font-sans">
      <div className="flex items-center justify-between border-b border-[#191D23] bg-[#0E1013] px-3.5 py-1.5 text-[11px] font-mono font-bold text-[#E6E8EB]">
        <span>NIFTY OPTION CHAIN — {expiry}</span>
        <div className="flex items-center gap-3 text-[10px] text-[#707987]">
          <span>View: <strong className="text-[#38BDF8]">Table</strong></span>
        </div>
      </div>

      <div className="overflow-x-auto bg-[#08090B] border border-[#191D23] rounded-[2px]" tabIndex={0} aria-label="NIFTY option chain matrix">
        <table className="w-full text-[11px] font-mono border-collapse text-left">
          <thead>
            <tr className="bg-[#0E1013] text-[#707987] border-b border-[#191D23] text-[10px] uppercase font-bold">
              <th colSpan={5} className="p-1.5 text-center text-[#E5484D] border-r border-[#191D23] bg-[#E5484D]/10">CALLS (CE)</th>
              <th
                className="p-1.5 text-center text-[#E6E8EB] bg-[#08090B] border-r border-[#191D23] cursor-pointer select-none hover:bg-[#13161A]"
                onClick={() => setStrikeSortDir((d) => (d === "asc" ? "desc" : "asc"))}
              >
                STRIKE {strikeSortDir === "asc" ? "↑" : "↓"}
              </th>
              <th colSpan={5} className="p-1.5 text-center text-[#00C896] bg-[#00C896]/10">PUTS (PE)</th>
            </tr>
            <tr className="bg-[#0B0D10] text-[#707987] border-b border-[#191D23] text-[9px] uppercase font-bold">
              <th className="p-1.5 text-right text-[#E5484D]">OI (Lakh)</th>
              <th className="p-1.5 text-right text-[#E5484D]">OI CHG (L)</th>
              <th className="p-1.5 text-right text-[#E5484D]">LTP</th>
              <th className="p-1.5 text-right text-[#E5484D]">CHG %</th>
              <th className="p-1.5 text-right text-[#E5484D] border-r border-[#191D23]">IV</th>
              <th className="p-1.5 text-center text-[#E6E8EB] bg-[#0E1013] border-r border-[#191D23]">ATM</th>
              <th className="p-1.5 text-left text-[#00C896]">IV</th>
              <th className="p-1.5 text-left text-[#00C896]">CHG %</th>
              <th className="p-1.5 text-left text-[#00C896]">LTP</th>
              <th className="p-1.5 text-left text-[#00C896]">OI CHG (L)</th>
              <th className="p-1.5 text-left text-[#00C896]">OI (Lakh)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#191D23]">
            {sortedStrikes.length === 0 ? (
              <tr>
                <td colSpan={11} className="p-6 text-center text-[#707987] italic font-mono">
                  Option chain telemetry unavailable or awaiting broker session snapshot.
                </td>
              </tr>
            ) : (
              sortedStrikes.map((s: any, i: number) => {
                const strikePx = Number(s.strike || s.strike_price);
                const isAtm = s.isAtm || (atmStrike != null && strikePx === atmStrike);
                const isMaxPain = s.isMaxPain || (maxPain != null && strikePx === maxPain);
                const isCallItm = spot != null && spot > 0 && strikePx < spot;
                const isPutItm = spot != null && spot > 0 && strikePx > spot;

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

                return (
                  <tr
                    key={strikePx || i}
                    className={`transition-colors text-[11px] hover:bg-[#13161A] ${
                      isAtm
                        ? "bg-[#38BDF8]/15 font-bold"
                        : isMaxPain
                        ? "bg-[#E59700]/15 font-bold"
                        : isCallItm && isPutItm
                        ? "bg-[#0B0D10]"
                        : isCallItm
                        ? "bg-[#E5484D]/5"
                        : isPutItm
                        ? "bg-[#00C896]/5"
                        : ""
                    }`}
                  >
                    {/* Call Columns */}
                    <td className="p-1.5 text-right text-[#E6E8EB] air-data">{formatOiLakh(cOi)}</td>
                    <td className={`p-1.5 text-right font-bold air-data ${cChg != null && Number(cChg) >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                      {cChg != null ? formatOiChgLakh(cChg) : "—"}
                    </td>
                    <td className="p-1.5 text-right font-semibold text-[#E6E8EB] air-data">{cLtp != null ? formatNumber(Number(cLtp), 2) : "—"}</td>
                    <td className={`p-1.5 text-right font-bold air-data ${cChgPct != null && Number(cChgPct) >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                      {cChgPct != null ? `${Number(cChgPct) >= 0 ? "+" : ""}${formatNumber(Number(cChgPct), 1)}%` : "—"}
                    </td>
                    <td className="p-1.5 text-right text-[#38BDF8] border-r border-[#191D23] air-data">
                      {cIv != null ? `${formatNumber(Number(cIv), 1)}%` : "—"}
                    </td>

                    {/* Center Strike Column */}
                    <td
                      className={`p-1.5 text-center font-bold border-r border-[#191D23] air-data ${
                        isAtm
                          ? "text-[#38BDF8] bg-[#38BDF8]/20"
                          : isMaxPain
                          ? "text-[#E59700] bg-[#E59700]/20"
                          : "text-[#E6E8EB] bg-[#0E1013]"
                      }`}
                    >
                      {strikePx}
                    </td>

                    {/* Put Columns */}
                    <td className="p-1.5 text-left text-[#38BDF8] air-data">{pIv != null ? `${formatNumber(Number(pIv), 1)}%` : "—"}</td>
                    <td className={`p-1.5 text-left font-bold air-data ${pChgPct != null && Number(pChgPct) >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                      {pChgPct != null ? `${Number(pChgPct) >= 0 ? "+" : ""}${formatNumber(Number(pChgPct), 1)}%` : "—"}
                    </td>
                    <td className="p-1.5 text-left font-semibold text-[#E6E8EB] air-data">{pLtp != null ? formatNumber(Number(pLtp), 2) : "—"}</td>
                    <td className={`p-1.5 text-left font-bold air-data ${pChg != null && Number(pChg) >= 0 ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                      {pChg != null ? formatOiChgLakh(pChg) : "—"}
                    </td>
                    <td className="p-1.5 text-left text-[#E6E8EB] air-data">{formatOiLakh(pOi)}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center text-[9px] font-mono text-[#707987] px-1 pt-1">
        <span>All values real-time or last valid · LTP in ₹ · OI in Lakh contracts · CHG vs Session Baseline</span>
        <span>Data Source: NSE Options, Zerodha Kite</span>
      </div>
    </div>
  );
}

export default OptionChainLadder;
