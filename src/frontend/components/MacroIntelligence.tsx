// src/frontend/components/MacroIntelligence.tsx
import React, { useState } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  Globe,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Layers,
  Calendar,
  RefreshCw,
  Info,
  ShieldCheck,
  Building2
} from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatDate
} from "../utils/safeHelpers";

export function GlobalCuesWidget() {
  const { canonicalState, lastValidState } = useWorkstationState();
  const macro = (canonicalState ?? lastValidState)?.macro_intelligence || {};
  const quotes = macro.quotes || {};
  const quoteStatus = macro.quote_status || {};
  const freshness = macro.domain_freshness?.global_quotes || "unavailable";

  const expectedQuotes = [
    ["GIFT_NIFTY", "GIFT Nifty"], ["S&P 500", "S&P 500"], ["NASDAQ", "Nasdaq"],
    ["DOW_JONES", "Dow"], ["NIKKEI_225", "Nikkei"], ["HANG_SENG", "Hang Seng"],
    ["BRENT_CRUDE", "Brent"], ["GOLD", "Gold"], ["USD_INR", "USD/INR"], ["DXY", "DXY"], ["US_10Y", "US 10Y"],
  ];
  const quoteList = Object.values(quotes) as any[];

  if (quoteList.length === 0) {
    return (
      <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg text-left space-y-2">
        <div className="flex items-center gap-2 text-slate-300 font-semibold text-xs">
          <Globe size={14} className="text-cyan-400" />
          <span>Global Markets & Commodities</span>
        </div>
        <p className="text-xs text-slate-500 italic">No external market quotes connected.</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg text-left space-y-3">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2 text-white font-bold text-xs">
          <Globe size={14} className="text-cyan-400" />
          <span>Global Cues & Macro Telemetry</span>
        </div>
        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
          Freshness: {freshness}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
        {expectedQuotes.map(([key, label], idx) => {
          const q: any = quotes[key];
          if (!q) return <div key={key} data-macro-key={key} className="p-2 bg-slate-950 rounded border border-slate-850 text-[10px]"><span className="font-bold text-slate-300">{label}</span><span className="block mt-1 text-amber-400">UNAVAILABLE</span><span className="block mt-1 text-[9px] text-slate-500">{safeString(quoteStatus[key]?.reason || "no validated observation")}</span></div>;
          const isUp = safeNumber(q.change) >= 0;
          return (
            <div key={q.symbol || idx} data-macro-key={key} className="p-2 bg-slate-950 rounded border border-slate-850 space-y-0.5">
              <div className="flex justify-between text-[10px] font-mono text-slate-400">
                <span className="font-bold text-slate-200 uppercase truncate">{safeString(q.name || q.symbol)}</span>
                <span className="text-[9px] text-slate-500">{safeString(q.currency)}</span>
              </div>
              <div className="text-[9px] text-slate-500 mt-1">{safeString(q.source_name)} · {safeString(q.source_symbol)} · observed {formatDate(q.observation_timestamp)} · {safeString(q.freshness_status)}</div>
              <div className="flex justify-between items-baseline pt-0.5">
                <span className="text-xs font-bold font-mono text-white">{formatNumber(q.price, 2)}</span>
                <span className={`text-[10px] font-mono font-semibold flex items-center ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                  {isUp ? <TrendingUp size={10} className="mr-0.5" /> : <TrendingDown size={10} className="mr-0.5" />}
                  {isUp ? "+" : ""}{formatNumber(q.change_pct, 2)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function InstitutionalFlowWidget() {
  const { canonicalState, lastValidState } = useWorkstationState();
  const macro = (canonicalState ?? lastValidState)?.macro_intelligence || {};
  const flows = safeArray(macro.institutional_flows) as any[];
  const freshness = macro.domain_freshness?.institutional_flows || "unavailable";

  return (
    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg text-left space-y-3">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2 text-white font-bold text-xs">
          <Activity size={14} className="text-emerald-400" />
          <span>FII / DII Trading Activity</span>
        </div>
        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
          Freshness: {freshness}
        </span>
      </div>

      {flows.length === 0 ? (
        <p className="text-xs text-slate-500 italic">Institutional flow unavailable: {safeString(macro.provider_health?.institutional_flow_provider?.operational_error_reason || "no validated official prior-session records were returned")}. </p>
      ) : (
        <div className="space-y-2">
          {flows.map((flow, idx) => {
            const isBuy = safeNumber(flow.net_value) >= 0;
            return (
              <div key={idx} className="flex justify-between items-center p-2 bg-slate-950 rounded border border-slate-850 text-xs">
                <div className="space-y-0.5">
                  <span className="font-bold text-slate-200 font-mono text-[11px]">{safeString(flow.dataset_type)}</span>
                  <span className="block text-[10px] text-slate-500 font-mono">Date: {safeString(flow.date)}</span>
                </div>
                <div className="text-right space-y-0.5 font-mono">
                  <span className={`font-bold ${isBuy ? "text-emerald-400" : "text-rose-400"}`}>
                    {isBuy ? "NET BUY: +" : "NET SELL: "}{formatNumber(flow.net_value, 2)} Cr
                  </span>
                  <span className="block text-[9px] text-slate-500">{safeString(flow.source_name)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function NiftyConstituentsWidget() {
  const { canonicalState, lastValidState } = useWorkstationState();
  const macro = (canonicalState ?? lastValidState)?.macro_intelligence || {};
  const meta = macro.constituent_metadata || {};

  if (!meta.is_available) {
    return (
      <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg text-left space-y-2">
        <div className="flex items-center gap-2 text-slate-300 font-semibold text-xs">
          <Building2 size={14} className="text-amber-400" />
          <span>NIFTY 50 Official Membership</span>
        </div>
        <p className="text-xs text-amber-400/80">Official constituent membership metadata is currently unavailable.</p>
      </div>
    );
  }

  const constituents = safeArray(meta.constituents) as any[];

  return (
    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg text-left space-y-3">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2 text-white font-bold text-xs">
          <Building2 size={14} className="text-cyan-400" />
          <span>NIFTY 50 Official Membership ({constituents.length})</span>
        </div>
        <span className="text-[10px] font-mono text-slate-400">Resolved to Kite: {safeNumber(meta.resolution_count, 0)}/{constituents.length}</span>
      </div>

      <p className="text-[10px] font-mono text-slate-500">Snapshot {safeString(meta.effective_snapshot_date || "UNAVAILABLE")} · Version {safeString(meta.metadata_version)}</p>
      {meta.reconstitution?.status === "AVAILABLE" || meta.reconstitution?.status === "DEGRADED" ? <p className="text-[10px] text-cyan-300">Reconstitution: {safeString(meta.reconstitution.review_frequency)} · {safeString(meta.reconstitution.review_schedule)}</p> : <p className="text-[10px] text-amber-400">Reconstitution metadata: UNAVAILABLE</p>}
      {safeString(meta.weights_status).toUpperCase() !== "AVAILABLE" && <p className="text-[10px] text-amber-400">Weights: {safeString(meta.weights_status || "UNAVAILABLE").toUpperCase()} — {safeString(meta.weights_reason)}</p>}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono">
        {constituents.slice(0, 12).map((c, idx) => (
          <div key={c.symbol || idx} className="p-2 bg-slate-950 rounded border border-slate-850 flex justify-between items-center">
            <div>
              <span className="font-bold text-white block">{safeString(c.symbol)}</span>
              <span className="text-[9px] text-slate-500 block">{safeString(c.sector)}</span>
            </div>
            <span className="text-[9px] text-cyan-400">{safeString(c.isin)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
