// src/frontend/components/visualizations/GlobalMarketsDashboard.tsx
import React, { useState, useMemo } from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { Globe, ArrowUpDown } from "lucide-react";
import { safeNumber, safeString, formatNumber } from "../../utils/safeHelpers";
import { getCanonicalQuote } from "../../utils/canonicalQuotes";
import { mapTraderEnum } from "../../utils/traderTerminology";
import { formatTimestampIST } from "../../utils/timeFormatting";

export function GlobalMarketsDashboard({ compact = false }: { compact?: boolean }) {
  const { canonicalState, lastValidState } = useWorkstationState() as any;
  const macro = (canonicalState || lastValidState)?.macro_intelligence || {};
  const quotes = macro.quotes || {};
  const quoteStatus = macro.quote_status || {};
  const workspace = macro.workspace_context || {};

  const [sortBy, setSortBy] = useState<"default" | "asset" | "change" | "freshness" | "region">("default");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const regions = [
    {
      name: "AMERICAS",
      items: [
        { name: "S&P 500", key: "S&P 500", assetClass: "Equity Index", region: "Americas" },
        { name: "NASDAQ", key: "NASDAQ", assetClass: "Equity Index", region: "Americas" },
        { name: "DOW JONES", key: "DOW_JONES", assetClass: "Equity Index", region: "Americas" },
      ]
    },
    {
      name: "ASIA / PACIFIC",
      items: [
        { name: "GIFT NIFTY", key: "GIFT_NIFTY", assetClass: "Equity Index", region: "Asia" },
        { name: "NIKKEI 225", key: "NIKKEI_225", assetClass: "Equity Index", region: "Asia" },
        { name: "HANG SENG", key: "HANG_SENG", assetClass: "Equity Index", region: "Asia" },
      ]
    },
    {
      name: "COMMODITIES & FX",
      items: [
        { name: "BRENT CRUDE", key: "BRENT_CRUDE", assetClass: "Commodity", region: "Global" },
        { name: "GOLD", key: "GOLD", assetClass: "Commodity", region: "Global" },
        { name: "USD/INR", key: "USD_INR", assetClass: "Currency", region: "Global" },
        { name: "DXY", key: "DXY", assetClass: "Currency", region: "Global" },
        { name: "US 10Y YIELD", key: "US_10Y", assetClass: "Rate", region: "Global" },
      ]
    }
  ];

  const compactKeys = useMemo(() => new Set(workspace.nifty_live_quote_keys || ["S&P 500", "NASDAQ", "NIKKEI_225", "BRENT_CRUDE", "USD_INR", "US_10Y"]), [workspace.nifty_live_quote_keys]);

  const allItems = useMemo(() => {
    return regions.flatMap(region => region.items).map(it => {
      const q = getCanonicalQuote(quotes, it.key);
      const status = quoteStatus[it.key] || {};
      return {
        ...it,
        quote: q,
        status,
        price: safeNumber(q.value, 0),
        changePct: safeNumber(q.changePct, 0),
        freshness: safeString(q.freshnessStatus).toUpperCase()
      };
    });
  }, [quotes, quoteStatus]);

  const visibleItems = useMemo(() => {
    if (compact) {
      return allItems.filter(item => compactKeys.has(item.key));
    }
    return allItems;
  }, [compact, allItems, compactKeys]);

  const sortedItems = useMemo(() => {
    if (sortBy === "default") return visibleItems;

    return [...visibleItems].sort((a, b) => {
      let diff = 0;
      if (sortBy === "asset") {
        diff = a.assetClass.localeCompare(b.assetClass);
      } else if (sortBy === "change") {
        diff = a.changePct - b.changePct;
      } else if (sortBy === "freshness") {
        diff = a.freshness.localeCompare(b.freshness);
      } else if (sortBy === "region") {
        diff = a.region.localeCompare(b.region);
      }

      if (diff === 0) {
        diff = a.name.localeCompare(b.name);
      }

      return sortDir === "asc" ? diff : -diff;
    });
  }, [sortBy, sortDir, visibleItems]);

  const hasQuotes = Object.keys(quotes).length > 0;

  if (!hasQuotes) {
    return (
      <div className="p-6 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-left font-mono text-xs">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <Globe size={16} />
          <span>Global Markets & Macro Telemetry Unavailable</span>
        </div>
        <p className="text-slate-400">
          No validated global-market observations are available from canonical providers.
        </p>
      </div>
    );
  }

  const handleSortClick = (key: typeof sortBy) => {
    if (sortBy === key) {
      setSortDir(prev => prev === "asc" ? "desc" : "asc");
    } else {
      setSortBy(key);
      setSortDir("desc");
    }
  };

  const isSorted = sortBy !== "default";

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 text-left font-sans">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Globe size={16} className="text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">Global Markets & Macro Telemetry</h3>
        </div>

        {/* Sorting Controls */}
        {!compact && (
          <div className="flex flex-wrap items-center gap-2 font-mono text-[10px]">
            <span className="text-slate-500 font-bold uppercase">Sort by:</span>
            <button
              onClick={() => setSortBy("default")}
              className={`px-2 py-0.5 rounded border ${
                sortBy === "default" ? "border-cyan-600 bg-cyan-950/45 text-cyan-300" : "border-slate-850 text-slate-500"
              }`}
            >
              Default
            </button>
            <button
              onClick={() => handleSortClick("asset")}
              className={`px-2 py-0.5 rounded border flex items-center gap-1 ${
                sortBy === "asset" ? "border-cyan-600 bg-cyan-950/45 text-cyan-300" : "border-slate-850 text-slate-500"
              }`}
            >
              Asset Class {sortBy === "asset" && (sortDir === "asc" ? "↑" : "↓")}
            </button>
            <button
              onClick={() => handleSortClick("change")}
              className={`px-2 py-0.5 rounded border flex items-center gap-1 ${
                sortBy === "change" ? "border-cyan-600 bg-cyan-950/45 text-cyan-300" : "border-slate-850 text-slate-500"
              }`}
            >
              % Change {sortBy === "change" && (sortDir === "asc" ? "↑" : "↓")}
            </button>
            <button
              onClick={() => handleSortClick("freshness")}
              className={`px-2 py-0.5 rounded border flex items-center gap-1 ${
                sortBy === "freshness" ? "border-cyan-600 bg-cyan-950/45 text-cyan-300" : "border-slate-850 text-slate-500"
              }`}
            >
              Freshness {sortBy === "freshness" && (sortDir === "asc" ? "↑" : "↓")}
            </button>
            <button
              onClick={() => handleSortClick("region")}
              className={`px-2 py-0.5 rounded border flex items-center gap-1 ${
                sortBy === "region" ? "border-cyan-600 bg-cyan-950/45 text-cyan-300" : "border-slate-850 text-slate-500"
              }`}
            >
              Region {sortBy === "region" && (sortDir === "asc" ? "↑" : "↓")}
            </button>
          </div>
        )}
      </div>

      {isSorted && !compact ? (
        // Flat Table Layout for sorted list
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-slate-950 text-slate-400 border-b border-slate-850 text-[10px] uppercase text-left">
                <th className="p-2">Asset Name</th>
                <th className="p-2">Asset Class</th>
                <th className="p-2">Region</th>
                <th className="p-2 text-right">Price</th>
                <th className="p-2 text-right">% Change</th>
                <th className="p-2 text-right">Freshness</th>
                <th className="p-2 text-right">Observation Time</th>
              </tr>
            </thead>
            <tbody>
              {sortedItems.map((it) => {
                const isPos = it.changePct >= 0;
                const obsTime = it.quote.observedAt ? formatTimestampIST(it.quote.observedAt) : "Unavailable";
                return (
                  <tr key={it.key} data-macro-key={it.key} className="border-b border-slate-900 hover:bg-slate-900/30 transition text-left">
                    <td className="p-2 font-bold text-white">{it.name}</td>
                    <td className="p-2 text-slate-400">{it.assetClass}</td>
                    <td className="p-2 text-slate-400">{it.region}</td>
                    <td className="p-2 text-right text-slate-200 font-bold">{formatNumber(it.price, 2)}</td>
                    <td className={`p-2 text-right font-bold ${isPos ? "text-emerald-400" : "text-rose-400"}`}>
                      {isPos ? "+" : ""}{formatNumber(it.changePct, 2)}%
                    </td>
                    <td className="p-2 text-right text-slate-400">{mapTraderEnum(it.freshness)}</td>
                    <td className="p-2 text-right text-slate-500">{obsTime}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        // Default Region-Grouped Card Grid Layout
        <div className={`grid grid-cols-1 ${compact ? "" : "md:grid-cols-3"} gap-4 font-mono`}>
          {(compact ? [{ name: "COMPACT CROSS-MARKET CONTEXT", items: visibleItems }] : regions).map((reg) => (
            <div key={reg.name} className="p-3 bg-slate-950 rounded-lg border border-slate-850 space-y-2">
              <span className="text-[10px] text-slate-400 font-bold block uppercase border-b border-slate-900 pb-1">
                {reg.name}
              </span>
              <div className="space-y-2">
                {reg.items.map((it) => {
                  const itemData = visibleItems.find(x => x.key === it.key);
                  if (!itemData) return null;
                  const q = itemData.quote;
                  const status = itemData.status;
                  if (!q.isAvailable) return compact ? null : <div key={it.key} className="flex justify-between gap-3 text-xs"><span className="font-bold text-slate-300">{q.displayName}</span><span className="text-right text-amber-400">UNAVAILABLE<span className="block text-[9px] text-slate-500">{safeString(status.reason || "no validated observation")}</span></span></div>;
                  const price = itemData.price;
                  const chg = itemData.changePct;
                  const isPos = chg >= 0;
                  const obsTime = q.observedAt ? formatTimestampIST(q.observedAt) : "Unavailable";

                  return (
                    <div key={it.key} data-macro-key={it.key} className="flex justify-between items-center gap-3 text-xs">
                      <span className="text-slate-300 font-bold">{q.displayName}<span className="block text-[9px] font-normal text-slate-500">{q.sessionContext} · {mapTraderEnum(q.freshnessStatus)}</span></span>
                      <div className="text-right">
                        <span className="font-bold text-white block">{formatNumber(price, 2)}</span>
                        <span className={`text-[10px] font-semibold ${isPos ? "text-emerald-400" : "text-rose-400"}`}>
                          {isPos ? "+" : ""}{formatNumber(chg, 2)}%
                        </span>
                        <span className="block text-[9px] text-slate-500">Observed {obsTime}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
