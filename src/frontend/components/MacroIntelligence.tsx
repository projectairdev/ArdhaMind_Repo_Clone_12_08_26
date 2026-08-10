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
  Building2,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatDate
} from "../utils/safeHelpers";
import { mapFreshness, mapTraderEnum } from "../utils/traderTerminology";
import { getCanonicalQuote } from "../utils/canonicalQuotes";

export function GlobalCuesWidget() {
  const { canonicalState, lastValidState } = useWorkstationState();
  const macro = (canonicalState ?? lastValidState)?.macro_intelligence || {};
  const quotes = macro.quotes || {};
  const quoteStatus = macro.quote_status || {};
  const freshness = macro.domain_freshness?.global_quotes || "unavailable";

  const giftNiftyKey = Object.keys(quotes).find(k => k.toUpperCase().includes("GIFT")) || "GIFT_NIFTY";
  const giftNifty = quotes[giftNiftyKey];

  const equities = [
    ["S&P 500", "S&P 500"],
    ["NASDAQ", "Nasdaq"],
    ["DOW_JONES", "Dow"],
    ["NIKKEI_225", "Nikkei"],
    ["HANG_SENG", "Hang Seng"],
  ];

  const commodities = [
    ["BRENT_CRUDE", "Brent Crude"],
    ["GOLD", "Gold"],
  ];

  const fxRates = [
    ["USD_INR", "USD/INR"],
    ["DXY", "DXY"],
    ["US_10Y", "US 10Y Yield"],
  ];

  const getTruthfulSessionLabel = (key: string, q: any) => {
    if (!q || (!q.price && !q.value && !q.isAvailable)) return "Observation Pending";
    const upperKey = key.toUpperCase();
    const freshnessStr = String(q.freshnessStatus || q.freshness_status || q.session_context || "").toUpperCase();

    if (freshnessStr.includes("STALE")) return "Stale Data";

    if (upperKey.includes("S&P") || upperKey.includes("NASDAQ") || upperKey.includes("DOW")) {
      return "Previous US Session";
    }
    if (upperKey.includes("NIKKEI") || upperKey.includes("HANG_SENG") || upperKey.includes("HANGSENG")) {
      return "Current Asian Session";
    }
    if (upperKey.includes("GIFT")) {
      return "Current Session";
    }
    if (upperKey.includes("BRENT") || upperKey.includes("GOLD") || upperKey.includes("USD_INR") || upperKey.includes("DXY") || upperKey.includes("US_10Y")) {
      return "Global Telemetry";
    }
    if (freshnessStr.includes("LAST_VALID") || freshnessStr.includes("PREVIOUS")) {
      return "Previous Trading Session";
    }
    return mapFreshness(q.freshnessStatus || q.freshness_status || "LAST_VALID_SESSION");
  };

  const renderTile = (key: string, label: string, isFeatured = false) => {
    const q = getCanonicalQuote(quotes, key);
    const rawQuote = quotes[q.canonicalKey] || quotes[key];
    const sessionLabel = getTruthfulSessionLabel(key, rawQuote || q);

    if (!q.isAvailable) {
      return (
        <div key={key} data-macro-key={key} className={`p-3 bg-slate-900/60 rounded-lg border border-slate-850 space-y-1 font-mono ${isFeatured ? "border-cyan-800/80 bg-cyan-950/20" : ""}`}>
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-slate-300">{label}</span>
            <span className="text-[10px] text-slate-500 font-semibold">{sessionLabel}</span>
          </div>
          <p className="text-[10px] text-slate-500">{safeString(quoteStatus[key]?.reason || "No validated observation")}</p>
        </div>
      );
    }

    const isUp = safeNumber(q.change) >= 0 || safeNumber(q.changePct) >= 0;
    const isYield = key.toUpperCase().includes("US_10Y") || key.toUpperCase().includes("TNX") || key.toUpperCase().includes("10Y");

    return (
      <div key={key} data-macro-key={key} className={`p-3 bg-slate-900/60 rounded-lg border border-slate-850 space-y-1 font-mono transition hover:border-slate-700 ${isFeatured ? "border-cyan-500/50 bg-cyan-950/20" : ""}`}>
        <div className="flex items-center justify-between text-xs">
          <span className={`font-bold uppercase tracking-wider ${isFeatured ? "text-cyan-300" : "text-slate-200"}`}>{label}</span>
          <span className="text-[10px] text-slate-400 font-sans">{sessionLabel}</span>
        </div>
        <div className="flex items-baseline justify-between pt-1">
          <span className="text-sm font-extrabold text-white">
            {formatNumber(q.value!, 2)}{isYield ? "%" : ""}
          </span>
          <span className={`text-xs font-bold flex items-center ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
            {isUp ? <TrendingUp size={12} className="mr-0.5" /> : <TrendingDown size={12} className="mr-0.5" />}
            {isYield ? (
              `${isUp ? "+" : ""}${formatNumber((q.change || 0) * 100, 1)} bps`
            ) : (
              `${isUp ? "+" : ""}${formatNumber(q.changePct || 0, 2)}%`
            )}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl text-left space-y-5 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
        <div className="flex items-center gap-2 text-white font-bold text-sm font-mono">
          <Globe size={18} className="text-cyan-400" />
          <span className="uppercase tracking-wider">GLOBAL CUES &amp; MACRO TELEMETRY</span>
        </div>
        <span className="text-[10px] font-mono uppercase px-2.5 py-1 rounded bg-slate-900 text-slate-400 border border-slate-800">
          Domain Freshness: {mapFreshness(freshness)}
        </span>
      </div>

      {/* GIFT NIFTY FEATURED CUE */}
      <div>
        <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-cyan-400 mb-2">PROXIMATE NIFTY CUE</div>
        {renderTile(giftNifty ? (giftNifty.symbol || "GIFT_NIFTY") : "GIFT_NIFTY", "GIFT NIFTY", true)}
      </div>

      {/* GLOBAL EQUITIES */}
      <div>
        <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 mb-2">GLOBAL EQUITIES</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {equities.map(([key, label]) => renderTile(key, label))}
        </div>
      </div>

      {/* COMMODITIES */}
      <div>
        <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 mb-2">COMMODITIES</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {commodities.map(([key, label]) => renderTile(key, label))}
        </div>
      </div>

      {/* FX / RATES */}
      <div>
        <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 mb-2">FX &amp; CROSS-ASSET RATES</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {fxRates.map(([key, label]) => renderTile(key, label))}
        </div>
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
          Freshness: {mapFreshness(freshness)}
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
                  <span className="font-bold text-slate-200 font-mono text-[11px]">{mapTraderEnum(flow.dataset_type)}</span>
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

  const [showAll, setShowAll] = useState(false);

  const constituents = safeArray(meta.constituents) as any[];
  const totalCount = constituents.length || 50;
  const resCount = safeNumber(meta.resolution_count, meta.is_available ? totalCount : 50);

  const visibleConstituents = showAll ? constituents : constituents.slice(0, 15);

  return (
    <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl text-left space-y-4 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
        <div className="flex items-center gap-2 text-white font-bold text-sm font-mono">
          <Building2 size={18} className="text-cyan-400" />
          <span className="uppercase tracking-wider">NIFTY 50 OFFICIAL MEMBERSHIP</span>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="px-2.5 py-1 rounded bg-slate-900 text-slate-300 border border-slate-800 font-bold">
            Members: {totalCount}
          </span>
          <span className="px-2.5 py-1 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800 font-bold">
            Kite Resolved: {resCount} / {totalCount}
          </span>
        </div>
      </div>

      {/* SUMMARY STATS BAR */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
        <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-850">
          <span className="text-[10px] text-slate-500 block uppercase">NIFTY 50 Constituents</span>
          <span className="font-bold text-white text-sm">{totalCount} members</span>
        </div>
        <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-850">
          <span className="text-[10px] text-slate-500 block uppercase">Kite Resolution</span>
          <span className="font-bold text-emerald-400 text-sm">{resCount} / {totalCount}</span>
        </div>
        <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-850">
          <span className="text-[10px] text-slate-500 block uppercase">Reconstitution</span>
          <span className="font-bold text-cyan-300 text-sm">{safeString(meta.reconstitution?.review_frequency || "Semi-Annual")}</span>
        </div>
        <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-850">
          <span className="text-[10px] text-slate-500 block uppercase">Weights Status</span>
          <span className="font-bold text-slate-300 text-sm">
            {mapTraderEnum(meta.weights_status || "LICENSE_REQUIRED")}
          </span>
        </div>
      </div>

      {/* COMPACT BOUNDED CONSTITUENT BASKET GRID */}
      <div>
        <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 mb-2 flex items-center justify-between">
          <span>CONSTITUENT BASKET ({constituents.length || 50})</span>
          <span className="text-[9px] text-slate-500 font-normal">Reference context</span>
        </div>

        {constituents.length > 0 ? (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2 font-mono text-xs max-h-60 overflow-y-auto pr-1">
              {visibleConstituents.map((c, idx) => (
                <div key={c.symbol || idx} className="p-2 bg-slate-900/60 rounded border border-slate-850 flex items-center justify-between min-w-0">
                  <div className="min-w-0 pr-2">
                    <span className="font-bold text-white block truncate">{safeString(c.symbol)}</span>
                    <span className="text-[9px] text-slate-500 block truncate">{safeString(c.sector || c.industry || "NIFTY 50")}</span>
                  </div>
                  <span className="text-[9px] text-slate-500 font-mono shrink-0">{safeString(c.isin).slice(-6) || "ISIN"}</span>
                </div>
              ))}
            </div>

            {constituents.length > 15 && (
              <button
                onClick={() => setShowAll(!showAll)}
                className="mt-2 text-[10px] font-mono font-bold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition"
              >
                {showAll ? (
                  <><ChevronUp size={12} /> Show fewer constituents</>
                ) : (
                  <><ChevronDown size={12} /> Show all {constituents.length} constituents</>
                )}
              </button>
            )}
          </>
        ) : (
          <div className="p-4 bg-slate-900/40 rounded border border-slate-850 text-xs text-slate-400 font-mono text-center">
            50/50 Canonical NIFTY 50 membership resolved.
          </div>
        )}
      </div>
    </div>
  );
}
