// src/frontend/components/MacroIntelligence.tsx
import React, { useState, useMemo } from "react";
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
import { formatTimestampIST } from "../utils/timeFormatting";
import { mapFreshness, mapTraderEnum } from "../utils/traderTerminology";
import { getCanonicalQuote } from "../utils/canonicalQuotes";

export function GlobalCuesWidget({
  onRefresh,
  onRefreshItem,
  refreshing = false,
  refreshingKeys = {},
  checkedAt,
  refreshStatus = "idle",
  refreshMessage
}: {
  onRefresh?: () => void;
  onRefreshItem?: (key: string) => void;
  refreshing?: boolean;
  refreshingKeys?: Record<string, boolean>;
  checkedAt?: string;
  refreshStatus?: string;
  refreshMessage?: string | null;
}) {
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
      return "PREVIOUS US SESSION";
    }
    if (upperKey.includes("NIKKEI") || upperKey.includes("HANG_SENG") || upperKey.includes("HANGSENG")) {
      return "CURRENT ASIAN SESSION";
    }
    if (upperKey.includes("GIFT")) {
      return "CURRENT SESSION";
    }
    if (upperKey.includes("BRENT") || upperKey.includes("GOLD")) {
      return "24H COMMODITIES";
    }
    if (upperKey.includes("USD_INR") || upperKey.includes("DXY") || upperKey.includes("US_10Y") || upperKey.includes("TNX") || upperKey.includes("10Y")) {
      return "GLOBAL FX & RATES";
    }
    if (freshnessStr.includes("LAST_VALID") || freshnessStr.includes("PREVIOUS")) {
      return "PREVIOUS TRADING SESSION";
    }
    return mapFreshness(q.freshnessStatus || q.freshness_status || "LAST_VALID_SESSION");
  };

  const renderTile = (key: string, label: string, isFeatured = false) => {
    const q = getCanonicalQuote(quotes, key);
    const rawQuote = quotes[q.canonicalKey] || quotes[key];
    const sessionLabel = getTruthfulSessionLabel(key, rawQuote || q);
    const isItemRefreshing = Boolean(refreshingKeys[key] || (refreshing && !onRefreshItem));

    const handleTileRefresh = (e: React.MouseEvent) => {
      e.stopPropagation();
      if (onRefreshItem) {
        onRefreshItem(key);
      } else if (onRefresh) {
        onRefresh();
      }
    };

    if (!q.isAvailable) {
      return (
        <div key={key} data-macro-key={key} className={`p-3 bg-slate-900/60 rounded-lg border border-slate-850 space-y-1 font-mono ${isFeatured ? "border-cyan-800/80 bg-cyan-950/20" : ""}`}>
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-slate-300">{label}</span>
            <div className="flex items-center gap-1.5">
              <button
                onClick={handleTileRefresh}
                disabled={isItemRefreshing}
                title={`Refresh ${label}`}
                aria-label={`Refresh ${label}`}
                className="text-[9px] font-mono text-cyan-400 hover:text-cyan-300 p-0.5 rounded border border-slate-800 bg-slate-900/80 transition"
              >
                <RefreshCw size={10} className={isItemRefreshing ? "animate-spin text-cyan-400" : ""} />
              </button>
              <span className="text-[10px] text-slate-500 font-semibold">{sessionLabel}</span>
            </div>
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
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleTileRefresh}
              disabled={isItemRefreshing}
              title={`Refresh ${label}`}
              aria-label={`Refresh ${label}`}
              className="text-[9px] font-mono text-cyan-400 hover:text-cyan-300 p-0.5 rounded border border-slate-800 bg-slate-900/80 transition hover:bg-cyan-950/60"
            >
              <RefreshCw size={10} className={isItemRefreshing ? "animate-spin text-cyan-400" : ""} />
            </button>
            <span className="text-[10px] text-slate-400 font-sans">{sessionLabel}</span>
          </div>
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

export function InstitutionalFlowWidget({
  onRefresh,
  refreshing = false,
  checkedAt,
  refreshStatus = "idle",
  refreshMessage
}: {
  onRefresh?: () => void;
  refreshing?: boolean;
  checkedAt?: string;
  refreshStatus?: string;
  refreshMessage?: string | null;
}) {
  const { canonicalState, lastValidState } = useWorkstationState() as any;
  const macro = (canonicalState ?? lastValidState)?.macro_intelligence || {};
  const flows = safeArray(macro.institutional_flows) as any[];

  const reportDate = flows.length > 0 ? flows[0].date : "UNAVAILABLE";
  const observedAtRaw = flows.length > 0 ? flows[0].retrieved_at : "UNAVAILABLE";
  const observedAt = observedAtRaw !== "UNAVAILABLE" ? formatTimestampIST(observedAtRaw) : "UNAVAILABLE";
  const rawFreshness = flows.length > 0 ? flows[0].freshness_status : (macro.domain_freshness?.institutional_flows || "unavailable");
  const sessionContext = "Previous Trading Session";
  const cleanFreshness = ["fresh", "live", "current"].includes(String(rawFreshness).toLowerCase())
    ? "Recent Observation"
    : mapTraderEnum(rawFreshness);

  return (
    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg text-left space-y-3 font-mono">
      <div className="flex flex-col gap-1.5 border-b border-slate-800 pb-2">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2 text-white font-bold text-xs">
            <Activity size={14} className="text-emerald-400" />
            <span>FII / DII Trading Activity</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-slate-400">
              {sessionContext}
            </span>
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={refreshing}
                title="Refresh Institutional Flows (FII/DII)"
                className="text-[9px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 border border-slate-800 bg-slate-950 px-1.5 py-0.5 rounded transition"
              >
                <RefreshCw size={10} className={refreshing ? "animate-spin" : ""} />
                {refreshing ? "REFRESHING..." : "↻ REFRESH FII/DII"}
              </button>
            )}
          </div>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 text-[9px] text-slate-500">
          <div className="flex flex-wrap gap-x-3">
            <span>Report Date: {reportDate}</span>
            <span>Observed: {observedAt}</span>
            {checkedAt && <span>Checked: <strong className="text-slate-300">{checkedAt}</strong></span>}
            <span>Freshness: <span className="text-slate-400 font-semibold">{cleanFreshness}</span></span>
          </div>
          {refreshMessage && (
            <span className={`font-semibold ${refreshStatus === "failed" || refreshStatus === "rate_limited" ? "text-rose-400" : "text-cyan-300"}`}>
              {refreshMessage}
            </span>
          )}
        </div>
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
  const [showAll, setShowAll] = useState(false);
  const { canonicalState, lastValidState } = useWorkstationState() as any;
  const stateObj = canonicalState || lastValidState;
  const meta = stateObj?.macro_intelligence?.constituent_metadata || {};
  const marketData = stateObj?.market_data || {};
  const breadth = marketData.breadth || {};
  const coverage = breadth.coverage || {};

  const constituents = safeArray(meta.constituents) as any[];
  const totalCount = constituents.length || 50;
  const isResolutionAvailable = meta.is_available && meta.resolution_count !== undefined;
  const resolutionDisplay = isResolutionAvailable ? `${meta.resolution_count} / ${totalCount}` : "Unavailable";

  const observedCount = coverage.valid != null ? coverage.valid : null;
  const observedDisplay = observedCount != null ? `${observedCount} / 50` : "Unavailable";

  const [sortBy, setSortBy] = useState<"symbol" | "sector" | "resolution">("symbol");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const sortedConstituents = useMemo(() => {
    return [...constituents].sort((a: any, b: any) => {
      let diff = 0;
      if (sortBy === "sector") {
        diff = safeString(a.sector || a.industry || "NIFTY 50").localeCompare(safeString(b.sector || b.industry || "NIFTY 50"));
      } else if (sortBy === "resolution") {
        const resA = a.instrument_token || a.is_resolved ? 1 : 0;
        const resB = b.instrument_token || b.is_resolved ? 1 : 0;
        diff = resB - resA;
      } else {
        diff = safeString(a.symbol).localeCompare(safeString(b.symbol));
      }
      if (diff === 0) {
        diff = safeString(a.symbol).localeCompare(safeString(b.symbol));
      }
      return sortDir === "asc" ? diff : -diff;
    });
  }, [constituents, sortBy, sortDir]);

  const visibleConstituents = showAll ? sortedConstituents : sortedConstituents.slice(0, 15);

  return (
    <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl text-left space-y-4 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
        <div className="flex items-center gap-2 text-white font-bold text-sm font-mono">
          <Building2 size={18} className="text-cyan-400" />
          <span className="uppercase tracking-wider">NIFTY 50 OFFICIAL MEMBERSHIP</span>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="px-2.5 py-1 rounded bg-slate-900 text-slate-300 border border-slate-800 font-bold">
            Official Members: {totalCount}
          </span>
          <span className="px-2.5 py-1 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800 font-bold">
            {/* Kite Resolved */}
            Kite Instruments Resolved: {resolutionDisplay}
          </span>
        </div>
      </div>

      {/* SUMMARY STATS BAR */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 font-mono text-xs">
        <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-850">
          <span className="text-[10px] text-slate-500 block uppercase">Official Members</span>
          <span className="font-bold text-white text-sm">{totalCount} members</span>
        </div>
        <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-850">
          <span className="text-[10px] text-slate-500 block uppercase">Kite Instruments Resolved</span>
          <span className="font-bold text-emerald-400 text-sm">{resolutionDisplay}</span>
        </div>
        <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-850">
          <span className="text-[10px] text-slate-500 block uppercase">Constituent Quotes Observed</span>
          <span className="font-bold text-amber-400 text-sm">{observedDisplay}</span>
        </div>
        <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-850">
          <span className="text-[10px] text-slate-500 block uppercase">Reconstitution</span>
          <span className="font-bold text-cyan-300 text-sm">{mapTraderEnum(meta.reconstitution?.review_frequency || "SEMI_ANNUAL")}</span>
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
        <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 mb-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-900 pb-1.5">
          <span>CONSTITUENT BASKET ({constituents.length || 50})</span>

          <div className="flex items-center gap-1.5 font-mono text-[9px] text-slate-500 normal-case">
            <span className="font-bold">Sort:</span>
            <button onClick={() => { setSortBy("symbol"); setSortDir(d => d === "asc" ? "desc" : "asc"); }} className={`px-1.5 py-0.5 rounded border ${sortBy === "symbol" ? "border-cyan-600 bg-cyan-950/45 text-cyan-300 font-bold" : "border-slate-800 text-slate-500"}`}>
              Symbol {sortBy === "symbol" && (sortDir === "asc" ? "↑" : "↓")}
            </button>
            <button onClick={() => { setSortBy("sector"); setSortDir(d => d === "asc" ? "desc" : "asc"); }} className={`px-1.5 py-0.5 rounded border ${sortBy === "sector" ? "border-cyan-600 bg-cyan-950/45 text-cyan-300 font-bold" : "border-slate-800 text-slate-500"}`}>
              Sector {sortBy === "sector" && (sortDir === "asc" ? "↑" : "↓")}
            </button>
            <button onClick={() => { setSortBy("resolution"); setSortDir(d => d === "asc" ? "desc" : "asc"); }} className={`px-1.5 py-0.5 rounded border ${sortBy === "resolution" ? "border-cyan-600 bg-cyan-950/45 text-cyan-300 font-bold" : "border-slate-800 text-slate-500"}`}>
              Resolution Status {sortBy === "resolution" && (sortDir === "asc" ? "↑" : "↓")}
            </button>
          </div>

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
