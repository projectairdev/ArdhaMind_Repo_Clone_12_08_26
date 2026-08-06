// src/frontend/components/LivePortfolio.tsx
import React, { useState } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  Wallet,
  Briefcase,
  Layers,
  Activity,
  RefreshCw,
  Clock,
  AlertCircle,
  TrendingUp
} from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";

export function LivePortfolio() {
  const {
    portfolioReport: report,
    loading,
    syncing: refreshing,
    error,
    syncBroker
  } = useWorkstationState();

  const [activeSubTab, setActiveSubTab] = useState<"summary" | "positions" | "holdings" | "orders" | "trades">("summary");

  const loadReport = async (isManual = false) => {
    await syncBroker(true);
  };

  if (loading && !report) {
    return (
      <div id="live-portfolio-loading" className="p-6 bg-slate-900 border border-slate-850 rounded-xl space-y-4 animate-pulse">
        <div className="flex justify-between items-center">
          <div className="h-6 w-1/3 bg-slate-800 rounded"></div>
          <div className="h-8 w-24 bg-slate-800 rounded"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="h-24 bg-slate-850 rounded-lg"></div>
          <div className="h-24 bg-slate-850 rounded-lg"></div>
          <div className="h-24 bg-slate-850 rounded-lg"></div>
          <div className="h-24 bg-slate-850 rounded-lg"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div id="live-portfolio-error" className="p-8 bg-neutral-950 border border-rose-900 rounded-xl text-center space-y-4 max-w-xl mx-auto my-12 text-left">
        <AlertCircle size={40} className="text-rose-500 mx-auto" />
        <h3 className="text-base font-bold text-white">Portfolio Ledger Offline</h3>
        <p className="text-xs text-neutral-400">{error || "Could not retrieve real-time capital allocation records."}</p>
        <button onClick={() => loadReport(true)} className="px-4 py-2 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 text-xs font-mono rounded text-white transition cursor-pointer">
          Retry Sync
        </button>
      </div>
    );
  }

  const isConnected = safeString(report?.sync_status) === "SUCCESS" || safeString(report?.broker_health?.connection_status) === "CONNECTED";
  const holdings = safeArray(report?.holdings) as any[];
  const positions = report?.positions || { net: [], day: [] };
  const statistics = report?.statistics || {
    available_cash: 0,
    total_margin_utilized: 0,
    total_holdings_value: 0,
    today_mtm: 0,
    total_realized_pnl: 0,
    total_unrealized_pnl: 0,
    total_portfolio_value: 0
  };
  const broker_health = report?.broker_health || { connection_status: "DISCONNECTED", trading_mode: "PAPER_TRADING" };

  const getPnLStyle = (val: number) => {
    if (val > 0) return "text-emerald-400";
    if (val < 0) return "text-rose-400";
    return "text-slate-400";
  };

  const formatTimestamp = (ts?: string) => {
    if (!ts) return "N/A";
    if (ts.includes("T")) {
      return ts.split("T")[1]?.slice(0, 8) || ts;
    }
    if (ts.includes(" ")) {
      return ts.split(" ")[1]?.slice(0, 8) || ts;
    }
    return ts;
  };

  return (
    <div id="live-portfolio-panel" className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl text-left">
      {/* Top Banner with sync details */}
      <div className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Briefcase className="text-cyan-400 h-5 w-5" />
            <h3 className="font-bold text-white text-base">Live Portfolio & Account Sync</h3>
            {!isConnected && (
              <span className="px-2 py-0.5 text-[9px] font-mono font-bold bg-rose-950/40 text-rose-400 border border-rose-900/50 rounded">
                DISCONNECTED
              </span>
            )}
            {isConnected && safeString(broker_health.trading_mode) === "PAPER_TRADING" && (
              <span className="px-2 py-0.5 text-[9px] font-mono font-bold bg-amber-950/40 text-amber-400 border border-amber-900/50 rounded">
                PRACTICE_MODE
              </span>
            )}
            {isConnected && safeString(broker_health.trading_mode) === "LIVE_ZERODHA" && (
              <span className="px-2 py-0.5 text-[9px] font-mono font-bold bg-emerald-950/40 text-emerald-400 border border-emerald-900/50 rounded">
                LIVE_MODE
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">
            Real-time synchronization of positions, CNC holdings, margins, and orders via secure gateway abstraction.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto font-mono text-xs">
          <div className="text-right hidden sm:block">
            <span className="text-[10px] text-slate-500 block">LAST GATEWAY SYNC</span>
            <span className="text-[11px] text-slate-300 font-bold flex items-center gap-1">
              <Clock className="h-3 w-3 text-cyan-400" />
              {formatTimestamp(safeString(report?.timestamp))} UTC
            </span>
          </div>

          <button
            onClick={() => loadReport(true)}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-750 text-white hover:text-cyan-400 border border-slate-700 hover:border-cyan-800/40 rounded-lg text-xs font-semibold transition disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span>{refreshing ? "Syncing..." : "Sync Broker"}</span>
          </button>
        </div>
      </div>

      {/* Disconnected Notice fallback */}
      {!isConnected ? (
        <div className="p-12 text-center space-y-4">
          <div className="inline-flex p-4 bg-rose-950/20 text-rose-400 rounded-full border border-rose-900/30">
            <AlertCircle className="h-8 w-8" />
          </div>
          <h4 className="text-base font-bold text-white">Zerodha KiteConnect Session Missing</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed font-sans">
            Your live portfolio is currently disconnected because there is no active Kite session. 
            Please navigate to the <span className="text-cyan-400 font-semibold font-mono">Broker Connection</span> tab to complete OAuth authentication.
          </p>
        </div>
      ) : (
        <>
          {/* Real-time Tickers Summary Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 border-b border-slate-800">
            <div className="p-5 border-r border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[10px] font-mono uppercase tracking-wider">Available Cash</span>
                <Wallet className="h-4 w-4 text-slate-500" />
              </div>
              <div className="text-lg font-mono font-bold text-white leading-none">
                {formatCurrency(statistics.available_cash, 2)}
              </div>
              <p className="text-[10px] text-slate-500 font-mono">
                Equity cash buffer segment
              </p>
            </div>

            <div className="p-5 border-r border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[10px] font-mono uppercase tracking-wider">Margin Utilized</span>
                <Layers className="h-4 w-4 text-slate-500" />
              </div>
              <div className="text-lg font-mono font-bold text-amber-400 leading-none">
                {formatCurrency(statistics.total_margin_utilized, 2)}
              </div>
              <p className="text-[10px] text-slate-500 font-mono">
                Collateral + premium locks
              </p>
            </div>

            <div className="p-5 border-r border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[10px] font-mono uppercase tracking-wider">Holdings Value</span>
                <TrendingUp className="h-4 w-4 text-slate-500" />
              </div>
              <div className="text-lg font-mono font-bold text-cyan-400 leading-none">
                {formatCurrency(statistics.total_holdings_value, 2)}
              </div>
              <p className="text-[10px] text-slate-500 font-mono">
                Long-term CNC equity value
              </p>
            </div>

            <div className="p-5 space-y-1.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[10px] font-mono uppercase tracking-wider">Today's MTM</span>
                <Activity className="h-4 w-4 text-slate-500" />
              </div>
              <div className={`text-lg font-mono font-bold leading-none ${getPnLStyle(safeNumber(statistics.today_mtm))}`}>
                {safeNumber(statistics.today_mtm) >= 0 ? "+" : ""}{formatCurrency(statistics.today_mtm, 2)}
              </div>
              <p className="text-[10px] text-slate-500 font-mono">
                Net Day + NRML positions MTM
              </p>
            </div>
          </div>

          {/* Sub-Tabs Selector */}
          <div className="flex bg-slate-900/60 p-2 border-b border-slate-850 gap-2">
            <button
              onClick={() => setActiveSubTab("summary")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition cursor-pointer ${
                activeSubTab === "summary"
                  ? "bg-slate-800 text-cyan-400 border border-slate-750 font-bold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Account summary
            </button>
            <button
              onClick={() => setActiveSubTab("positions")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer ${
                activeSubTab === "positions"
                  ? "bg-slate-800 text-cyan-400 border border-slate-750 font-bold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Open Positions
              <span className="bg-slate-950 text-slate-400 text-[10px] px-1.5 py-0.5 rounded-full font-mono border border-slate-800">
                {safeArray(positions.net).length}
              </span>
            </button>
            <button
              onClick={() => setActiveSubTab("holdings")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer ${
                activeSubTab === "holdings"
                  ? "bg-slate-800 text-cyan-400 border border-slate-750 font-bold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Holdings (CNC)
              <span className="bg-slate-950 text-slate-400 text-[10px] px-1.5 py-0.5 rounded-full font-mono border border-slate-800">
                {holdings.length}
              </span>
            </button>
          </div>

          {/* Sub-Tab Panel Body */}
          <div className="p-6">
            {activeSubTab === "summary" && (
              <div className="space-y-4 max-w-2xl font-mono text-xs">
                <h4 className="text-sm font-bold text-white border-b border-slate-850 pb-2">Double-Entry Account Metrics</h4>
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500 uppercase text-[9px]">Opening Capital Balance:</span>
                  <span className="text-white font-bold">{formatCurrency(safeNumber(statistics.available_cash) + safeNumber(statistics.total_margin_utilized), 2)}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500 uppercase text-[9px]">Utilized Capital Limit:</span>
                  <span className="text-amber-400 font-bold">{formatCurrency(statistics.total_margin_utilized, 2)}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500 uppercase text-[9px]">Free Liquid Cash Balance:</span>
                  <span className="text-emerald-400 font-bold">{formatCurrency(statistics.available_cash, 2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 uppercase text-[9px]">Realized Day Profits:</span>
                  <span className={`font-bold ${getPnLStyle(safeNumber(statistics.total_realized_pnl))}`}>{formatCurrency(statistics.total_realized_pnl, 2)}</span>
                </div>
              </div>
            )}

            {activeSubTab === "positions" && (
              <div className="space-y-4">
                {safeArray(positions.net).length === 0 ? (
                  <p className="text-xs text-slate-500 font-mono italic">No active contracts open.</p>
                ) : (
                  <div className="overflow-x-auto rounded border border-slate-800 bg-slate-950/20 text-xs font-mono">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-900/50 text-[10px] text-slate-500 uppercase">
                          <th className="px-4 py-2.5">Symbol</th>
                          <th className="px-4 py-2.5">Product</th>
                          <th className="px-4 py-2.5 text-right">Quantity</th>
                          <th className="px-4 py-2.5 text-right">Avg Entry Price</th>
                          <th className="px-4 py-2.5 text-right">Last Traded Price</th>
                          <th className="px-4 py-2.5 text-right">Day MTM</th>
                        </tr>
                      </thead>
                      <tbody className="text-slate-300">
                        {(safeArray(positions.net) as any[]).map((pos: any, idx) => (
                          <tr key={idx} className="border-b border-slate-800 hover:bg-slate-900/20">
                            <td className="px-4 py-3 text-cyan-400 font-bold">{safeString(pos?.symbol)}</td>
                            <td className="px-4 py-3 text-slate-500">{safeString(pos?.product)}</td>
                            <td className={`px-4 py-3 text-right font-bold ${safeNumber(pos?.quantity) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                              {safeNumber(pos?.quantity)}
                            </td>
                            <td className="px-4 py-3 text-right text-white">{formatCurrency(pos?.average_price, 2)}</td>
                            <td className="px-4 py-3 text-right text-white">{formatCurrency(pos?.last_price, 2)}</td>
                            <td className={`px-4 py-3 text-right font-bold ${getPnLStyle(safeNumber(pos?.mtm))}`}>
                              {safeNumber(pos?.mtm) >= 0 ? "+" : ""}{formatCurrency(pos?.mtm, 2)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {activeSubTab === "holdings" && (
              <div className="space-y-4">
                {holdings.length === 0 ? (
                  <p className="text-xs text-slate-500 font-mono italic">No long-term CNC holdings records found.</p>
                ) : (
                  <div className="overflow-x-auto rounded border border-slate-800 bg-slate-950/20 text-xs font-mono">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-900/50 text-[10px] text-slate-500 uppercase">
                          <th className="px-4 py-2.5">Holding Symbol</th>
                          <th className="px-4 py-2.5 text-right">Shares Count</th>
                          <th className="px-4 py-2.5 text-right">Average Price</th>
                          <th className="px-4 py-2.5 text-right">Current LTP</th>
                          <th className="px-4 py-2.5 text-right">Current Value</th>
                          <th className="px-4 py-2.5 text-right">Total P&L</th>
                        </tr>
                      </thead>
                      <tbody className="text-slate-300">
                        {holdings.map((h, idx) => (
                          <tr key={idx} className="border-b border-slate-800 hover:bg-slate-900/20">
                            <td className="px-4 py-3 text-white font-bold">{safeString(h?.symbol)}</td>
                            <td className="px-4 py-3 text-right text-white">{safeNumber(h?.quantity)}</td>
                            <td className="px-4 py-3 text-right text-slate-400">{formatCurrency(h?.average_price, 2)}</td>
                            <td className="px-4 py-3 text-right text-slate-400">{formatCurrency(h?.current_price || h?.last_price, 2)}</td>
                            <td className="px-4 py-3 text-right text-white">{formatCurrency(h?.current_value || (safeNumber(h?.quantity) * safeNumber(h?.last_price)), 2)}</td>
                            <td className={`px-4 py-3 text-right font-bold ${getPnLStyle(safeNumber(h?.unrealized_pnl || h?.pnl))}`}>
                              {safeNumber(h?.unrealized_pnl || h?.pnl) >= 0 ? "+" : ""}{formatCurrency(h?.unrealized_pnl || h?.pnl, 2)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default LivePortfolio;
