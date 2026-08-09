// src/frontend/components/visualizations/NiftyCandlestickChart.tsx
import React, { useState } from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { Layers, AlertTriangle } from "lucide-react";
import { safeNumber, safeString, formatNumber, formatDate } from "../../utils/safeHelpers";

export function NiftyCandlestickChart() {
  const { marketContext, canonicalState } = useWorkstationState() as any;
  const rawSpot = marketContext?.current_spot;
  const isAvailable = Boolean(rawSpot && marketContext?.last_tick_time);

  const spot = safeNumber(rawSpot, 0);
  const vwap = safeNumber(marketContext?.vwap, 0);
  const dq = canonicalState?.data_quality?.market_data || {};

  const [showVwap, setShowVwap] = useState(true);

  if (!isAvailable) {
    return (
      <div className="p-6 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-left font-mono text-xs">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <AlertTriangle size={16} />
          <span>NIFTY Intraday Candlestick Chart Unavailable</span>
        </div>
        <p className="text-slate-400">
          No live NIFTY observation detected. Connect Kite broker or await validated market snapshot.
        </p>
      </div>
    );
  }

  const candles = Array.isArray(marketContext?.candles) ? marketContext.candles : [];
  if (candles.length === 0) return <div className="p-6 bg-slate-950 border border-slate-800 rounded-xl text-left font-mono text-xs text-amber-400">Historical chart unavailable — Kite returned no validated candles.</div>;
  const sessionHigh = Math.max(...candles.map((c: any) => safeNumber(c.h, Number.NEGATIVE_INFINITY)));
  const sessionLow = Math.min(...candles.map((c: any) => safeNumber(c.l, Number.POSITIVE_INFINITY)));

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 text-left font-sans">
      <div className="flex flex-wrap justify-between items-center border-b border-slate-800 pb-3 gap-2">
        <div className="flex items-center gap-2">
          <Layers size={16} className="text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">NIFTY 50 Intraday OHLC & Overlays</h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          {vwap > 0 && <button
            onClick={() => setShowVwap(!showVwap)}
            className={`px-2 py-1 rounded border text-[10px] font-bold ${
              showVwap ? "bg-amber-950/60 text-amber-400 border-amber-800" : "bg-slate-950 text-slate-500 border-slate-850"
            }`}
          >
            VWAP ({formatNumber(vwap, 0)})
          </button>}
          <span className="px-2 py-1 rounded bg-slate-950 text-amber-400 border border-slate-800 text-[10px] uppercase font-bold">
            {safeString(dq.freshness_status || "UNAVAILABLE")} · Kite Historical API · {dq.observed_at ? formatDate(dq.observed_at) : "UNAVAILABLE"}
          </span>
        </div>
      </div>

      <div className="h-48 w-full bg-slate-950 rounded-lg border border-slate-850 p-2 relative flex flex-col justify-between font-mono">
        <div className="flex justify-between text-[10px] text-slate-500 border-b border-slate-900 pb-1">
          <span>High: {formatNumber(sessionHigh, 1)}</span>
          <span>Close: {formatNumber(spot, 1)}</span>
          <span>Low: {formatNumber(sessionLow, 1)}</span>
        </div>

        <div className="flex-1 flex items-end justify-between px-4 pt-2 pb-1 gap-2">
          {candles.map((c, idx) => {
            const isBull = c.c >= c.o;
            const range = Math.max(0.01, sessionHigh - sessionLow);
            const height = Math.max(5, Math.min(100, (Math.abs(c.c - c.o) / range) * 100));
            const volHeight = 0;
            return (
              <div key={idx} className="flex-1 flex flex-col items-center justify-end h-full group relative">
                <div className="w-0.5 bg-slate-600 mb-0.5" style={{ height: "70%" }}></div>
                <div
                  className={`w-full rounded-xs transition-all ${
                    isBull ? "bg-emerald-500 border border-emerald-400" : "bg-rose-500 border border-rose-400"
                  }`}
                  style={{ height: `${height}%` }}
                ></div>
                <div
                  className={`w-full mt-1 opacity-40 ${isBull ? "bg-emerald-400" : "bg-rose-400"}`}
                  style={{ height: `${volHeight}px` }}
                ></div>
                <span className="text-[9px] text-slate-500 mt-1">{c.time}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
