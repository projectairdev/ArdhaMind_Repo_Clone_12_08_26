// src/frontend/components/MarketOverview.tsx
import React from "react";
import { useWorkstationState, useMarketData, useOptionIntelligence } from "../context/WorkstationStateContext";
import { AlertTriangle, Compass, TrendingUp, HelpCircle, Table, Activity, Newspaper } from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";

export function MarketOverview() {
  const {
    eveningReport: planner,
    loading,
    error,
    syncBroker
  } = useWorkstationState();
  const { data: market } = useMarketData();
  const { data: option } = useOptionIntelligence();

  if (loading && !market) {
    return (
      <div id="market-overview-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4 text-left">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-48 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div id="market-overview-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3 text-left">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertTriangle size={18} />
          <h3 className="font-semibold">Market Overview Unavailable</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Connection timed out."}</p>
        <button onClick={() => syncBroker(true)} className="px-3 py-1 bg-slate-900 text-xs text-slate-300 rounded border border-slate-800 hover:bg-slate-800">
          Retry
        </button>
      </div>
    );
  }

  const currentSpot = safeNumber(market?.current_spot);
  const newsItems = safeArray(planner?.economic_calendar) as any[];
  const vixContext: any = market?.india_vix_context || {};
  const hasVerifiedVix = vixContext.value != null && Boolean(vixContext.observation_timestamp);

  return (
    <div id="market-overview" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6 text-left">
      {/* Title */}
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <Compass size={18} className="text-cyan-400" />
          <h3 className="font-bold text-white text-base">Market Intelligence Overview</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500 uppercase">NSE Futures & Options Feed</span>
      </div>

      {/* Main stats layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Spot Card */}
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800/60 space-y-1">
          <span className="text-[10px] font-mono font-medium text-slate-500 uppercase">Spot Pivot Index</span>
          <div className="text-lg font-mono font-bold text-white">
            {formatCurrency(currentSpot, 2)}
          </div>
          <p className="text-xs text-emerald-400 flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
            {safeString(market?.trend_direction) === "BULLISH" ? "Trending Bullish" : "Trending Bearish"}
          </p>
        </div>

        {/* India VIX Card */}
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800/60 space-y-1">
          <span className="text-[10px] font-mono font-medium text-slate-500 uppercase">India VIX (Vol State)</span>
          <div className="text-lg font-mono font-bold text-white">
            {hasVerifiedVix ? formatNumber(vixContext.value, 2) : "UNAVAILABLE"}
          </div>
          <p className="text-xs text-cyan-400 flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400"></span>
            {hasVerifiedVix ? safeString(vixContext.regime, "UNAVAILABLE") : "UNAVAILABLE"}
          </p>
        </div>

        {/* Put-Call Ratio Card */}
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800/60 space-y-1">
          <span className="text-[10px] font-mono font-medium text-slate-500 uppercase">Put-Call Ratio (PCR)</span>
          <div className="text-lg font-mono font-bold text-white">
            {formatNumber(option?.pcr, 2)}
          </div>
          <p className="text-xs text-slate-400">
            Bias: {safeNumber(option?.pcr) >= 1.0 ? "BULLISH_CONFLUENCE" : "BEARISH_DISTRIBUTION"}
          </p>
        </div>

        {/* ATR Card */}
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800/60 space-y-1">
          <span className="text-[10px] font-mono font-medium text-slate-500 uppercase">ATR Range (14 Period)</span>
          <div className="text-lg font-mono font-bold text-white">
            {formatNumber(market?.atr, 2)}
          </div>
          <p className="text-xs text-slate-400">Volatility cushion factor</p>
        </div>
      </div>

      {/* S/R Pivots Visualization Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Support Pivot Points */}
        <div className="space-y-2">
          <h4 className="text-xs font-mono font-semibold text-rose-400 tracking-wide uppercase">Support Bands (S1 - S3)</h4>
          <div className="overflow-hidden rounded border border-slate-800 bg-slate-900/20">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/40 text-[10px] font-mono text-slate-500">
                  <th className="px-3 py-1.5">Pivots</th>
                  <th className="px-3 py-1.5">Value</th>
                  <th className="px-3 py-1.5 text-right">Distance to Spot</th>
                </tr>
              </thead>
              <tbody className="text-[11px] font-mono text-slate-300">
                {safeArray(market?.support_levels).map((val, idx) => (
                  <tr key={idx} className="border-b border-slate-800 hover:bg-slate-900/20">
                    <td className="px-3 py-2 text-rose-400/80 font-semibold">S{idx + 1} Pivot</td>
                    <td className="px-3 py-2 text-white">{formatCurrency(val, 2)}</td>
                    <td className="px-3 py-2 text-right text-rose-400">
                      -{formatNumber(Math.abs(currentSpot - safeNumber(val)), 1)} pts
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Resistance Pivot Points */}
        <div className="space-y-2">
          <h4 className="text-xs font-mono font-semibold text-emerald-400 tracking-wide uppercase">Resistance Bands (R1 - R3)</h4>
          <div className="overflow-hidden rounded border border-slate-800 bg-slate-900/20">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/40 text-[10px] font-mono text-slate-500">
                  <th className="px-3 py-1.5">Pivots</th>
                  <th className="px-3 py-1.5">Value</th>
                  <th className="px-3 py-1.5 text-right">Distance to Spot</th>
                </tr>
              </thead>
              <tbody className="text-[11px] font-mono text-slate-300">
                {safeArray(market?.resistance_levels).map((val, idx) => (
                  <tr key={idx} className="border-b border-slate-800 hover:bg-slate-900/20">
                    <td className="px-3 py-2 text-emerald-400/80 font-semibold">R{idx + 1} Pivot</td>
                    <td className="px-3 py-2 text-white">{formatCurrency(val, 2)}</td>
                    <td className="px-3 py-2 text-right text-emerald-400">
                      +{formatNumber(Math.abs(safeNumber(val) - currentSpot), 1)} pts
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 📊 Active Option Chain Matrix */}
      <div className="space-y-3">
        <h4 className="text-xs font-mono font-semibold text-neutral-200 tracking-wide uppercase flex items-center gap-1.5">
          <Table size={14} className="text-cyan-400" /> Active Option Chain Matrix (Strikes Near ATM)
        </h4>
        <div className="overflow-x-auto rounded border border-slate-800 bg-slate-900/20">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/50 text-[10px] text-slate-500 uppercase">
                <th className="px-4 py-2">Strike</th>
                <th className="px-4 py-2">Type</th>
                <th className="px-4 py-2 text-right">Premium (LTP)</th>
                <th className="px-4 py-2 text-right">Open Interest (OI)</th>
                <th className="px-4 py-2 text-right">Volume</th>
                <th className="px-4 py-2 text-right">Implied Vol (IV)</th>
              </tr>
            </thead>
            <tbody className="text-slate-300">
              {(safeArray(option?.top_candidate_strikes) as any[]).map((s: any, idx) => (
                <tr key={idx} className="border-b border-slate-800 hover:bg-slate-900/30">
                  <td className="px-4 py-2.5 font-bold text-white">{safeString(s?.strike)}</td>
                  <td className={`px-4 py-2.5 font-extrabold ${safeString(s?.instrument_type || s?.type) === "CE" ? "text-emerald-400" : "text-rose-400"}`}>
                    {safeString(s?.instrument_type || s?.type)}
                  </td>
                  <td className="px-4 py-2.5 text-right text-white">{formatCurrency(s?.premium || s?.ltp, 2)}</td>
                  <td className="px-4 py-2.5 text-right text-slate-400">{formatNumber(s?.oi)}</td>
                  <td className="px-4 py-2.5 text-right text-slate-400">{formatNumber(s?.volume)}</td>
                  <td className="px-4 py-2.5 text-right text-cyan-400">{formatNumber(s?.iv, 1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 📰 Sentiment & Economic Calendar */}
      <div className="space-y-3">
        <h4 className="text-xs font-mono font-semibold text-neutral-200 tracking-wide uppercase flex items-center gap-1.5">
          <Newspaper size={14} className="text-cyan-400" /> Economic Calendar & Sentiment Drivers
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {newsItems.length === 0 ? <p className="text-xs text-slate-500">No verified economic-calendar observations are available.</p> : newsItems.map((item, idx) => (
            <div key={idx} className="p-3.5 bg-slate-900/40 border border-slate-800 rounded-lg space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-slate-500 font-bold">{safeString(item?.time)}</span>
                <span className={`px-1.5 py-0.5 rounded text-[8px] font-mono font-bold ${
                  safeString(item?.impact) === "HIGH" ? "bg-rose-950/60 text-rose-400 border border-rose-900/30" : "bg-cyan-950/60 text-cyan-400 border border-cyan-900/30"
                }`}>
                  {safeString(item?.impact)} IMPACT
                </span>
              </div>
              <p className="text-xs text-slate-200 font-medium font-sans mt-1">{safeString(item?.event)}</p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}

export default MarketOverview;
