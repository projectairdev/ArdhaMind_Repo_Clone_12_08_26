// src/frontend/components/ExecutionWorkspace.tsx
import React, { useState } from "react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { executeOrder, exitPosition } from "../services/broker";
import {
  Zap,
  AlertCircle,
  Play,
  Activity,
  RefreshCw,
  Layers,
  ShieldCheck,
  AlertTriangle,
  CheckCircle,
  XCircle,
  FileText,
  Clock
} from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";

export function ExecutionWorkspace() {
  const { themeClasses, fontClasses, accentClasses } = useTheme();
  const {
    workspaceMode,
    portfolioReport,
    syncing,
    error,
    syncBroker
  } = useWorkstationState();

  // Manual execution ticket state
  const [symbol, setSymbol] = useState("NIFTY26JUL2424200CE");
  const [qty, setQty] = useState(50); // 1 lot default
  const [price, setPrice] = useState(150.0);
  const [transType, setTransType] = useState<"BUY" | "SELL">("BUY");
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT" | "SL">("MARKET");
  const [productType, setProductType] = useState<"NRML" | "MIS" | "CNC">("NRML");

  const [executing, setExecuting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [execError, setExecError] = useState<string | null>(null);

  const isConnected = portfolioReport?.broker_health?.connection_status === "CONNECTED" || workspaceMode !== "LIVE_TRADING";
  const openPositions = (safeArray(portfolioReport?.positions?.net) as any[]).filter(p => safeNumber(p?.quantity) !== 0);
  const pendingOrders = safeArray(portfolioReport?.orders?.open_orders || (portfolioReport?.orders as any)?.open || []) as any[];
  const completedOrders = safeArray(portfolioReport?.orders?.completed || (portfolioReport?.orders as any)?.history || []) as any[];

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol.trim()) {
      setExecError("Trading symbol is required.");
      return;
    }

    setExecuting(true);
    setExecError(null);
    setMessage(null);

    try {
      const res = await executeOrder({
        candidate_id: "MANUAL_" + Date.now(),
        tradingsymbol: symbol.trim(),
        transaction_type: transType,
        quantity: qty,
        price: orderType === "MARKET" ? 0 : price,
        order_type: orderType,
        product: productType,
        exchange: "NFO",
        trigger_price: 0
      });

      setMessage(`Order successfully placed! ID: ${res.broker_order_id}`);
      await syncBroker(true);
    } catch (err: any) {
      setExecError(err.message || "Order placement failed.");
    } finally {
      setExecuting(false);
    }
  };

  const handleExitPosition = async (posSymbol: string, product: string) => {
    setExecuting(true);
    setExecError(null);
    setMessage(null);
    try {
      const res = await exitPosition(posSymbol, product);
      if (res.error) {
        setExecError(res.error);
      } else {
        setMessage(`Square off request submitted for ${posSymbol} (${product}).`);
        await syncBroker(true);
      }
    } catch (err: any) {
      setExecError(err.message || "Square off request failed.");
    } finally {
      setExecuting(false);
    }
  };

  const handleEmergencyExit = async () => {
    if (openPositions.length === 0) {
      setMessage("No active open positions to exit.");
      return;
    }

    if (!window.confirm("WARNING: You are about to SQUARE OFF ALL open positions. Proceed?")) {
      return;
    }

    setExecuting(true);
    setExecError(null);
    setMessage("Initiating system-wide emergency square-off...");

    try {
      const exitPromises = openPositions.map(pos =>
        exitPosition(safeString(pos.symbol), safeString(pos.product)).catch(err => ({ error: err.message || "Exit failed" }))
      );
      await Promise.all(exitPromises);
      setMessage("Emergency system-wide square-off completed.");
      await syncBroker(true);
    } catch (err: any) {
      setExecError(err.message || "One or more emergency exit orders failed.");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div id="execution-workspace" className={`space-y-6 text-left ${fontClasses.base}`}>
      
      {/* Workspace Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-neutral-850 pb-4 gap-4">
        <div>
          <span className={`text-[10px] font-mono uppercase tracking-widest font-extrabold ${accentClasses.text}`}>
            Secure Order Routing Gateway
          </span>
          <h2 className="text-xl sm:text-2xl font-black tracking-tight mt-1 flex items-center gap-2">
            <Zap className="h-5.5 w-5.5 text-indigo-400" />
            Execution Terminal
          </h2>
          <p className="text-xs text-neutral-400 mt-0.5">
            Place manual option contracts, exit active positions, and monitor live broker order routing.
          </p>
        </div>

        <button
          onClick={handleEmergencyExit}
          disabled={executing || openPositions.length === 0}
          className="px-4 py-2 bg-rose-650 hover:bg-rose-505 border border-rose-900 text-slate-100 font-bold text-xs font-mono rounded-lg transition-all shadow-[0_0_15px_rgba(220,38,38,0.15)] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          EMERGENCY PANIC EXIT (SQUARE OFF ALL)
        </button>
      </div>

      {/* Errors & Status notifications */}
      {(error || execError || message) && (
        <div className="space-y-2">
          {(error || execError) && (
            <div className="p-4 bg-rose-950/15 border border-rose-900/40 rounded-xl flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold text-white uppercase font-mono">Execution Gateway Exception</h4>
                <p className="text-[11px] text-rose-300 font-mono mt-0.5">{error || execError}</p>
              </div>
            </div>
          )}
          {message && (
            <div className="p-4 bg-emerald-950/15 border border-emerald-900/40 rounded-xl flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold text-white uppercase font-mono">Routing Event Alert</h4>
                <p className="text-[11px] text-emerald-300 font-mono mt-0.5">{message}</p>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT COLUMN: Manual Order Placement Ticket */}
        <div className="lg:col-span-5">
          <form
            onSubmit={handlePlaceOrder}
            className={`${themeClasses.card} border rounded-xl p-5 space-y-4 text-left`}
          >
            <div className="border-b border-neutral-900 pb-2 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Play size={13} className="text-cyan-400" />
                <span className="text-xs font-mono font-bold text-neutral-200 uppercase">
                  Manual Order Ticket
                </span>
              </div>
              <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded ${
                workspaceMode === "LIVE_TRADING"
                  ? "bg-rose-950/60 text-rose-400 border border-rose-900/40"
                  : "bg-amber-950/60 text-amber-400 border border-amber-900/40"
              }`}>
                {workspaceMode === "LIVE_TRADING" ? "REAL CAPITAL" : "PRACTICE PAPER"}
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              {/* Buy / Sell Toggle */}
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setTransType("BUY")}
                  className={`py-2 rounded-lg font-bold border transition ${
                    transType === "BUY"
                      ? "bg-emerald-950/50 border-emerald-900 text-emerald-400"
                      : "bg-[#0a0a0a]/40 border-neutral-900 text-neutral-500 hover:text-white"
                  }`}
                >
                  BUY / LONG
                </button>
                <button
                  type="button"
                  onClick={() => setTransType("SELL")}
                  className={`py-2 rounded-lg font-bold border transition ${
                    transType === "SELL"
                      ? "bg-rose-950/50 border-rose-900 text-rose-400"
                      : "bg-[#0a0a0a]/40 border-neutral-900 text-neutral-500 hover:text-white"
                  }`}
                >
                  SELL / SHORT
                </button>
              </div>

              {/* Symbol Input */}
              <div className="space-y-1">
                <label className="text-[10px] text-neutral-500 uppercase block">Trading Symbol</label>
                <input
                  type="text"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                  placeholder="e.g. NIFTY26JUL24200CE"
                  className="w-full bg-[#0a0a0a]/90 px-3 py-2 border border-neutral-800 rounded-lg text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              {/* Qty & Price */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] text-neutral-500 uppercase block">Quantity (Lots)</label>
                  <input
                    type="number"
                    value={qty}
                    onChange={(e) => setQty(Math.max(1, parseInt(e.target.value) || 0))}
                    className="w-full bg-[#0a0a0a]/90 px-3 py-2 border border-neutral-800 rounded-lg text-white font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-neutral-500 uppercase block">Limit Price (₹)</label>
                  <input
                    type="number"
                    step="0.05"
                    value={price}
                    disabled={orderType === "MARKET"}
                    onChange={(e) => setPrice(parseFloat(e.target.value) || 0.0)}
                    className="w-full bg-[#0a0a0a]/90 px-3 py-2 border border-neutral-800 rounded-lg text-white font-mono focus:outline-none focus:border-cyan-500 disabled:opacity-40"
                  />
                </div>
              </div>

              {/* Order Type & Product */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] text-neutral-500 uppercase block">Order Type</label>
                  <select
                    value={orderType}
                    onChange={(e) => setOrderType(e.target.value as any)}
                    className="w-full bg-[#0a0a0a]/90 px-3 py-2 border border-neutral-800 rounded-lg text-white font-mono focus:outline-none focus:border-cyan-500"
                  >
                    <option value="MARKET">MARKET</option>
                    <option value="LIMIT">LIMIT</option>
                    <option value="SL">STOPLOSS (SL)</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-neutral-500 uppercase block">Product</label>
                  <select
                    value={productType}
                    onChange={(e) => setProductType(e.target.value as any)}
                    className="w-full bg-[#0a0a0a]/90 px-3 py-2 border border-neutral-800 rounded-lg text-white font-mono focus:outline-none focus:border-cyan-500"
                  >
                    <option value="NRML">NRML (Expiry)</option>
                    <option value="MIS">MIS (Intraday)</option>
                    <option value="CNC">CNC (Delivery)</option>
                  </select>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={executing || !isConnected}
              className={`w-full py-2.5 rounded-lg text-xs font-bold font-mono transition text-center cursor-pointer ${
                transType === "BUY"
                  ? "bg-emerald-650 hover:bg-emerald-555 text-slate-100"
                  : "bg-rose-650 hover:bg-rose-555 text-slate-100"
              } disabled:opacity-45`}
            >
              {executing ? "Routing..." : `SUBMIT ${transType} ORDER`}
            </button>
          </form>
        </div>

        {/* RIGHT COLUMN: Open Positions & Order History Lists */}
        <div className="lg:col-span-7 space-y-6">
          {/* Active Positions */}
          <div className={`${themeClasses.card} border rounded-xl p-5 space-y-3`}>
            <div className="flex items-center justify-between border-b border-neutral-900 pb-2">
              <div className="flex items-center gap-1.5">
                <Activity size={13} className="text-cyan-400" />
                <span className="text-xs font-mono font-bold text-neutral-200 uppercase">
                  Active Positions ({openPositions.length})
                </span>
              </div>
            </div>

            {openPositions.length === 0 ? (
              <div className="py-8 text-center text-xs text-neutral-500 font-mono">No active open positions.</div>
            ) : (
              <div className="overflow-x-auto rounded border border-neutral-900 bg-neutral-950/20 text-xs font-mono">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-neutral-900 bg-neutral-900/50 text-[10px] text-neutral-500 uppercase">
                      <th className="px-3 py-2">Symbol</th>
                      <th className="px-3 py-2">Product</th>
                      <th className="px-3 py-2 text-right">Qty</th>
                      <th className="px-3 py-2 text-right">Avg</th>
                      <th className="px-3 py-2 text-right">LTP</th>
                      <th className="px-3 py-2 text-right">MTM P&L</th>
                      <th className="px-3 py-2 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="text-neutral-300">
                    {openPositions.map((pos, idx) => (
                      <tr key={idx} className="border-b border-neutral-900 hover:bg-neutral-900/20">
                        <td className="px-3 py-2 text-cyan-400 font-bold">{safeString(pos?.symbol)}</td>
                        <td className="px-3 py-2 text-neutral-400">{safeString(pos?.product)}</td>
                        <td className={`px-3 py-2 text-right font-bold ${safeNumber(pos?.quantity) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {safeNumber(pos?.quantity)}
                        </td>
                        <td className="px-3 py-2 text-right text-white">{formatCurrency(pos?.average_price, 1)}</td>
                        <td className="px-3 py-2 text-right text-white">{formatCurrency(pos?.last_price, 1)}</td>
                        <td className={`px-3 py-2 text-right font-bold ${safeNumber(pos?.mtm) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {formatCurrency(pos?.mtm, 0)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <button
                            onClick={() => handleExitPosition(safeString(pos?.symbol), safeString(pos?.product))}
                            disabled={executing}
                            className="px-2 py-1 bg-rose-950/20 hover:bg-rose-950/40 border border-rose-900/40 text-rose-400 rounded text-[10px] font-bold cursor-pointer"
                          >
                            EXIT
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pending & Open Orders */}
          <div className={`${themeClasses.card} border rounded-xl p-5 space-y-3`}>
            <div className="flex items-center justify-between border-b border-neutral-900 pb-2">
              <div className="flex items-center gap-1.5">
                <Clock size={13} className="text-cyan-400" />
                <span className="text-xs font-mono font-bold text-neutral-200 uppercase">
                  Pending Orders ({pendingOrders.length})
                </span>
              </div>
            </div>

            {pendingOrders.length === 0 ? (
              <div className="py-8 text-center text-xs text-neutral-500 font-mono">No pending orders.</div>
            ) : (
              <div className="overflow-x-auto rounded border border-neutral-900 bg-neutral-950/20 text-xs font-mono">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-neutral-900 bg-neutral-900/50 text-[10px] text-neutral-500 uppercase">
                      <th className="px-3 py-2">Symbol</th>
                      <th className="px-3 py-2">Type</th>
                      <th className="px-3 py-2 text-right">Qty</th>
                      <th className="px-3 py-2 text-right">Price</th>
                      <th className="px-3 py-2 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="text-neutral-300">
                    {pendingOrders.map((ord, idx) => (
                      <tr key={idx} className="border-b border-neutral-900 hover:bg-neutral-900/20">
                        <td className="px-3 py-2 text-cyan-400 font-bold">{safeString(ord?.tradingsymbol)}</td>
                        <td className={`px-3 py-2 font-bold ${safeString(ord?.transaction_type) === "BUY" ? "text-emerald-400" : "text-rose-400"}`}>
                          {safeString(ord?.transaction_type)}
                        </td>
                        <td className="px-3 py-2 text-right text-white">{safeNumber(ord?.quantity)}</td>
                        <td className="px-3 py-2 text-right text-white">{formatCurrency(ord?.price, 1)}</td>
                        <td className="px-3 py-2 text-center">
                          <span className="px-2 py-0.5 bg-amber-955/40 text-amber-400 border border-amber-900/50 rounded text-[9px]">
                            {safeString(ord?.status)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Today's Order History */}
          <div className={`${themeClasses.card} border rounded-xl p-5 space-y-3`}>
            <div className="flex items-center gap-1.5 border-b border-neutral-900 pb-2">
              <FileText size={13} className="text-cyan-400" />
              <span className="text-xs font-mono font-bold text-neutral-200 uppercase">
                Today's Completed Orders ({completedOrders.length})
              </span>
            </div>

            {completedOrders.length === 0 ? (
              <div className="py-8 text-center text-xs text-neutral-500 font-mono">No order history recorded today.</div>
            ) : (
              <div className="overflow-x-auto rounded border border-neutral-900 bg-neutral-950/20 text-xs font-mono">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-neutral-900 bg-neutral-900/50 text-[10px] text-neutral-500 uppercase">
                      <th className="px-3 py-2">Symbol</th>
                      <th className="px-3 py-2">Type</th>
                      <th className="px-3 py-2 text-right">Qty</th>
                      <th className="px-3 py-2 text-right">Price</th>
                      <th className="px-3 py-2 text-center">Outcome</th>
                    </tr>
                  </thead>
                  <tbody className="text-neutral-300">
                    {completedOrders.slice(0, 10).map((ord, idx) => (
                      <tr key={idx} className="border-b border-neutral-900 hover:bg-neutral-900/20">
                        <td className="px-3 py-2 text-white font-bold">{safeString(ord?.tradingsymbol)}</td>
                        <td className={`px-3 py-2 font-bold ${safeString(ord?.transaction_type) === "BUY" ? "text-emerald-400" : "text-rose-400"}`}>
                          {safeString(ord?.transaction_type)}
                        </td>
                        <td className="px-3 py-2 text-right text-neutral-400">{safeNumber(ord?.quantity)}</td>
                        <td className="px-3 py-2 text-right text-neutral-400">{formatCurrency(ord?.price || ord?.average_price, 1)}</td>
                        <td className="px-3 py-2 text-center">
                          <span className={`px-2 py-0.5 rounded text-[9px] ${
                            safeString(ord?.status) === "COMPLETE"
                              ? "bg-emerald-950/40 text-emerald-400 border border-emerald-900/50"
                              : "bg-rose-950/40 text-rose-400 border border-rose-900/50"
                          }`}>
                            {safeString(ord?.status)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

export default ExecutionWorkspace;
