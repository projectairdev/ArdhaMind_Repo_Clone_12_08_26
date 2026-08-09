// src/frontend/components/visualizations/GlobalMarketsDashboard.tsx
import React from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { Globe } from "lucide-react";
import { safeNumber, safeString, formatNumber } from "../../utils/safeHelpers";

export function GlobalMarketsDashboard({ compact = false }: { compact?: boolean }) {
  const { canonicalState, lastValidState } = useWorkstationState() as any;
  const macro = (canonicalState || lastValidState)?.macro_intelligence || {};
  const quotes = macro.quotes || {};
  const quoteStatus = macro.quote_status || {};
  const workspace = macro.workspace_context || {};
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

  const regions = [
    {
      name: "AMERICAS",
      items: [
        { name: "S&P 500", key: "S&P 500" },
        { name: "NASDAQ", key: "NASDAQ" },
        { name: "DOW JONES", key: "DOW_JONES" },
      ]
    },
    {
      name: "ASIA / PACIFIC",
      items: [
        { name: "GIFT NIFTY", key: "GIFT_NIFTY" },
        { name: "NIKKEI 225", key: "NIKKEI_225" },
        { name: "HANG SENG", key: "HANG_SENG" },
      ]
    },
    {
      name: "COMMODITIES & FX",
      items: [
        { name: "BRENT CRUDE", key: "BRENT_CRUDE" },
        { name: "GOLD", key: "GOLD" },
        { name: "USD/INR", key: "USD_INR" },
        { name: "DXY", key: "DXY" },
        { name: "US 10Y YIELD", key: "US_10Y" },
      ]
    }
  ];
  const compactKeys = new Set(workspace.nifty_live_quote_keys || ["S&P 500", "NASDAQ", "NIKKEI_225", "BRENT_CRUDE", "USD_INR", "US_10Y"]);
  const visibleRegions = compact
    ? [{ name: "COMPACT CROSS-MARKET CONTEXT", items: regions.flatMap(region => region.items).filter(item => compactKeys.has(item.key)) }]
    : regions;

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 text-left font-sans">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Globe size={16} className="text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">Global Markets & Macro Telemetry</h3>
        </div>
        <span className="text-[10px] font-mono text-cyan-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
          Yahoo Finance chart observations · {safeString(macro.domain_freshness?.global_quotes || "unavailable").toUpperCase()}
        </span>
      </div>

      <div className={`grid grid-cols-1 ${compact ? "" : "md:grid-cols-3"} gap-4 font-mono`}>
        {visibleRegions.map((reg) => (
          <div key={reg.name} className="p-3 bg-slate-950 rounded-lg border border-slate-850 space-y-2">
            <span className="text-[10px] text-slate-400 font-bold block uppercase border-b border-slate-900 pb-1">
              {reg.name}
            </span>
            <div className="space-y-2">
              {reg.items.map((it) => {
                const liveObj = quotes[it.key];
                const status = quoteStatus[it.key] || {};
                if (!liveObj) return compact ? null : <div key={it.key} className="flex justify-between gap-3 text-xs"><span className="font-bold text-slate-300">{it.name}</span><span className="text-right text-amber-400">UNAVAILABLE<span className="block text-[9px] text-slate-500">{safeString(status.reason || "no validated observation")}</span></span></div>;
                const price = safeNumber(liveObj.price, 0);
                const chg = safeNumber(liveObj.change_pct, 0);
                const isPos = chg >= 0;

                return (
                  <div key={it.key} data-macro-key={it.key} className="flex justify-between items-center gap-3 text-xs">
                    <span className="text-slate-300 font-bold">{it.name}<span className="block text-[9px] font-normal text-slate-500">{safeString(liveObj.source_symbol)} · {safeString(liveObj.freshness_status)}</span></span>
                    <div className="text-right">
                      <span className="font-bold text-white block">{formatNumber(price, 2)}</span>
                      <span className={`text-[10px] font-semibold ${isPos ? "text-emerald-400" : "text-rose-400"}`}>
                        {isPos ? "+" : ""}{formatNumber(chg, 2)}%
                      </span>
                      <span className="block text-[9px] text-slate-500">Observed {safeString(liveObj.observation_timestamp)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
