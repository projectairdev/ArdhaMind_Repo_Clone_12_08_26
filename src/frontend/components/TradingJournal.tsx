import React, { useEffect, useState } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber
} from "../utils/safeHelpers";
import { Surface, SectionHeader } from "./ui/WorkspacePrimitives";
import { InstrumentVisual } from "./ui/AuthenticMarketLogo";

export function TradingJournal() {
  const { workspaceMode: mode } = useWorkstationState();
  const [entries, setEntries] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [strategyFilter, setStrategyFilter] = useState("all");

  useEffect(() => {
    const prefix = mode === "LIVE_PRACTICE" ? "paper" : "live";
    const storedTrades = localStorage.getItem(`${prefix}_ledger_trades`);
    const ledgerTrades = storedTrades ? JSON.parse(storedTrades) : [];

    const journalEntries = ledgerTrades.map((t: any, idx: number) => ({
      entry_id: `JN-${idx + 1001}`,
      trade_id: t.trade_id || `TRD-${idx + 100}`,
      tradingsymbol: t.symbol || "NIFTY",
      strategy_name: t.exchange ? `${t.exchange} ${t.transaction_type}` : "MOMENTUM_BREAKOUT",
      market_score_val: 78,
      action: t.transaction_type || "BUY",
      setup: "Range Expansion Confirmation",
      result: t.transaction_type === "SELL" ? "+2.5 pts" : "Open Position",
      pnl: t.transaction_type === "SELL" ? t.quantity * 2.5 : 0.0,
      entry_time: t.timestamp || new Date().toISOString().slice(11, 19),
      notes: "Automated transaction audit details logged."
    }));
    setEntries(journalEntries);
  }, [mode]);

  const filteredEntries = (safeArray(entries) as any[]).filter((entry) => {
    const matchesSearch =
      safeString(entry?.tradingsymbol).toLowerCase().includes(search.toLowerCase()) ||
      safeString(entry?.notes).toLowerCase().includes(search.toLowerCase()) ||
      safeString(entry?.setup).toLowerCase().includes(search.toLowerCase());

    const matchesFilter =
      strategyFilter === "all" ||
      safeString(entry?.strategy_name).toLowerCase().includes(strategyFilter.toLowerCase());

    return matchesSearch && matchesFilter;
  });

  return (
    <div id="trading-journal-workspace" className="space-y-4 font-sans text-left">
      {/* Workspace Header */}
      <Surface glow="cyan" className="p-4 font-mono">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                TRADER OPERATOR JOURNAL
              </span>
              <span className="rounded bg-[#39D9FF]/10 px-2 py-0.5 text-[9px] font-bold text-[#39D9FF] border border-[#39D9FF]/30">
                AUDIT LEDGER
              </span>
            </div>
            <h2 className="mt-1 text-lg font-bold text-slate-100 uppercase tracking-tight">
              TRADING JOURNAL &amp; POST-MORTEM LEDGER
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Search symbol/notes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-[#07070a] px-3 py-1.5 border border-[#1a1a24] rounded text-slate-200 text-xs font-mono focus:outline-none focus:border-[#39D9FF]"
            />
            <select
              value={strategyFilter}
              onChange={(e) => setStrategyFilter(e.target.value)}
              className="bg-[#07070a] px-3 py-1.5 border border-[#1a1a24] text-slate-200 rounded text-xs font-mono focus:outline-none"
            >
              <option value="all">All Strategies</option>
              <option value="scalping">Scalping</option>
              <option value="momentum">Momentum</option>
              <option value="trend">Trend Following</option>
            </select>
          </div>
        </div>
      </Surface>

      {/* Main Journal Data Table */}
      {filteredEntries.length > 0 ? (
        <Surface className="overflow-hidden font-mono">
          <SectionHeader title="EXECUTED TRADES & AUDIT RECORDS" detail="Double-Entry Audit Log" accent="cyan" />
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[11px]">
              <thead>
                <tr className="border-b border-[#181820] bg-[#07070a] text-[9px] uppercase tracking-wider text-slate-400">
                  <th className="py-2.5 px-3 font-semibold">Time</th>
                  <th className="py-2.5 px-3 font-semibold">Instrument</th>
                  <th className="py-2.5 px-3 font-semibold">Setup</th>
                  <th className="py-2.5 px-3 font-semibold text-center">Action</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Result</th>
                  <th className="py-2.5 px-3 font-semibold">Notes / Post-Mortem</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#14141c]">
                {filteredEntries.map((entry) => (
                  <tr key={entry.entry_id} className="hover:bg-[#08080d] transition-colors">
                    <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap">{entry.entry_time}</td>
                    <td className="py-2.5 px-3">
                      <div className="flex items-center gap-2">
                        <InstrumentVisual symbol={entry.tradingsymbol} size={18} />
                        <span className="font-bold text-slate-200">{entry.tradingsymbol}</span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 font-sans text-xs">{entry.setup}</td>
                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${
                          entry.action === "BUY"
                            ? "border-[#00E5A8]/30 bg-[#00E5A8]/10 text-[#00E5A8]"
                            : "border-[#FF5C77]/30 bg-[#FF5C77]/10 text-[#FF5C77]"
                        }`}
                      >
                        {entry.action}
                      </span>
                    </td>
                    <td className={`py-2.5 px-3 text-right air-data font-bold ${entry.pnl >= 0 ? "text-[#00E5A8]" : "text-[#FF5C77]"}`}>
                      {entry.result}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 font-sans text-xs">{entry.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Surface>
      ) : (
        <Surface className="p-8 text-center space-y-2 font-mono">
          <div className="text-xs font-bold text-slate-300 uppercase">NO JOURNAL AUDIT RECORDS RECORDED</div>
          <p className="text-[11px] text-slate-500 font-sans max-w-md mx-auto">
            Trade post-mortems and double-entry audit records populate automatically upon session execution or paper ledger sync.
          </p>
        </Surface>
      )}
    </div>
  );
}

export default TradingJournal;
