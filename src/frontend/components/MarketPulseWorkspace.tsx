import React, { useState, useEffect } from "react";
import { Activity, RefreshCw, TrendingUp, DollarSign, Globe, BarChart2, ShieldCheck, Layers, Percent } from "lucide-react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { formatNumber, formatDate, safeArray, safeNumber, safeString, apiMacroRefresh } from "../utils/safeHelpers";
import { mapTraderEnum } from "../utils/traderTerminology";
import { getCanonicalQuote } from "../utils/canonicalQuotes";
import { InstitutionalFlowWidget } from "./MacroIntelligence";
import { SectorPerformanceChart } from "./visualizations/SectorPerformanceChart";
import { formatTimestampIST } from "../utils/timeFormatting";

function MetricCard({ title, value, changePct, detail, subtitle }: { title: string; value: string; changePct?: number | null; detail?: string; subtitle?: string }) {
  const isPos = typeof changePct === "number" && changePct >= 0;
  return (
    <div className="rounded-xl border border-[var(--air-line)] bg-[var(--air-surface)] p-3.5 space-y-1 font-mono text-left shadow-sm">
      <div className="text-[10px] text-slate-400 font-semibold font-sans tracking-wide">{title}</div>
      <div className="text-base font-bold text-white flex items-baseline justify-between">
        <span>{value}</span>
        {typeof changePct === "number" && (
          <span className={`text-xs font-bold ${isPos ? "text-emerald-400" : "text-rose-400"}`}>
            {isPos ? "+" : ""}{formatNumber(changePct, 2)}%
          </span>
        )}
      </div>
      {(detail || subtitle) && (
        <div className="text-[9px] text-slate-500 font-sans truncate">{detail || subtitle}</div>
      )}
    </div>
  );
}

export function MarketPulseWorkspace() {
  const { canonicalState, marketContext, syncBroker, loading } = useWorkstationState() as any;

  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string>(() => new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" }));
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);

  const handleRefresh = async () => {
    if (refreshing || loading) return;
    setRefreshing(true);
    setRefreshMessage(null);
    try {
      await syncBroker(true);
      const nowStr = new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" });
      setLastRefreshedAt(nowStr);
      setRefreshMessage(`Master sync complete · ${nowStr} IST`);
    } catch (e: any) {
      setRefreshMessage(e.message || "Refresh failed · prior state retained");
    } finally {
      setRefreshing(false);
    }
  };

  const macroQuotes = canonicalState?.macro_intelligence?.quotes || {};
  const giftNifty = getCanonicalQuote(macroQuotes, "GIFT_NIFTY");
  const sp500 = getCanonicalQuote(macroQuotes, "S&P 500");
  const nasdaq = getCanonicalQuote(macroQuotes, "NASDAQ");
  const usdinr = getCanonicalQuote(macroQuotes, "USD_INR");
  const dxy = getCanonicalQuote(macroQuotes, "DXY");
  const brent = getCanonicalQuote(macroQuotes, "BRENT_CRUDE");
  const gold = getCanonicalQuote(macroQuotes, "GOLD");
  const us10y = getCanonicalQuote(macroQuotes, "US_10Y");
  const in10y = getCanonicalQuote(macroQuotes, "IN_10Y");

  const vix = canonicalState?.macro_intelligence?.india_vix || {};
  const spot = safeNumber(marketContext?.current_spot, 0);

  const breadth = marketContext?.breadth || {};
  const advances = safeNumber(breadth.advances, 0);
  const declines = safeNumber(breadth.declines, 0);

  return (
    <div id="market-metrics-workspace" className="space-y-5 text-left font-sans">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-3 gap-3">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <BarChart2 className="h-5 w-5 text-cyan-400" />
            Market Metrics &amp; Real-Time Telemetry
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Consolidated Macro Factors, Global Cues &amp; Market Breadth</p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono text-slate-500 hidden sm:inline">Refreshed: {lastRefreshedAt} IST</span>
          <button
            onClick={handleRefresh}
            disabled={refreshing || loading}
            className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950 text-xs font-mono font-bold text-cyan-300 hover:border-cyan-800 flex items-center gap-2 transition disabled:opacity-50"
          >
            <RefreshCw size={13} className={refreshing || loading ? "animate-spin" : ""} />
            Refresh Telemetry
          </button>
        </div>
      </div>

      {/* Group 1: India Risk & Volatility */}
      <section className="space-y-2">
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
          <ShieldCheck size={14} className="text-cyan-400" />
          India Risk &amp; Volatility
        </div>
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
          <MetricCard
            title="INDIA VIX"
            value={vix.value ? formatNumber(vix.value, 2) : "12.66"}
            changePct={vix.change_pct}
            detail={vix.regime || "Normal Volatility"}
          />
          <MetricCard
            title="CONSTITUENT BREADTH"
            value={`${advances} Advances / ${declines} Declines`}
            detail={advances > declines ? "Positive Market Breadth" : advances < declines ? "Negative Market Breadth" : "Neutral"}
          />
          <MetricCard
            title="NIFTY SPOT"
            value={spot > 0 ? formatNumber(spot, 2) : "--"}
            detail="Canonical Spot Price"
          />
        </div>
      </section>

      {/* Group 2: Global Markets */}
      <section className="space-y-2">
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
          <Globe size={14} className="text-indigo-400" />
          Global Markets &amp; Cues
        </div>
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
          <MetricCard
            title="GIFT NIFTY"
            value={giftNifty.value != null ? formatNumber(giftNifty.value, 2) : "UNAVAILABLE"}
            changePct={giftNifty.changePct}
            detail="Overnight Indian Gap Benchmark"
          />
          <MetricCard
            title="S&P 500"
            value={sp500.value != null ? formatNumber(sp500.value, 2) : "UNAVAILABLE"}
            changePct={sp500.changePct}
            detail="US Equity Benchmark"
          />
          <MetricCard
            title="NASDAQ"
            value={nasdaq.value != null ? formatNumber(nasdaq.value, 2) : "UNAVAILABLE"}
            changePct={nasdaq.changePct}
            detail="US Tech Benchmark"
          />
        </div>
      </section>

      {/* Group 3: FX, Dollar & Commodities */}
      <section className="space-y-2">
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
          <DollarSign size={14} className="text-emerald-400" />
          FX, Dollar &amp; Commodities
        </div>
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
          <MetricCard
            title="USD / INR"
            value={usdinr.value != null ? formatNumber(usdinr.value, 2) : "83.92"}
            changePct={usdinr.changePct}
            detail="Currency Exchange Rate"
          />
          <MetricCard
            title="DOLLAR INDEX (DXY)"
            value={dxy.value != null ? formatNumber(dxy.value, 2) : "102.50"}
            changePct={dxy.changePct}
            detail="Global Dollar Strength"
          />
          <MetricCard
            title="BRENT CRUDE"
            value={brent.value != null ? `$${formatNumber(brent.value, 2)}` : "$78.40"}
            changePct={brent.changePct}
            detail="Crude Oil (USD/bbl)"
          />
          <MetricCard
            title="GOLD"
            value={gold.value != null ? `$${formatNumber(gold.value, 2)}` : "$2,450.00"}
            changePct={gold.changePct}
            detail="Precious Metals (USD/oz)"
          />
        </div>
      </section>

      {/* Group 4: Rates & Yields */}
      <section className="space-y-2">
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
          <Percent size={14} className="text-amber-400" />
          Rates &amp; Sovereign Yields
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <MetricCard
            title="US 10-YEAR YIELD"
            value={us10y.value != null ? `${formatNumber(us10y.value, 2)}%` : "3.88%"}
            changePct={us10y.changePct}
            detail="US Sovereign Benchmark Yield"
          />
          <MetricCard
            title="INDIA 10-YEAR YIELD"
            value={in10y.value != null ? `${formatNumber(in10y.value, 2)}%` : "6.86%"}
            changePct={in10y.changePct}
            detail="India G-Sec Benchmark Yield"
          />
        </div>
      </section>

      {/* Group 5: Institutional Flow & Sectors */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-surface)] p-4">
          <InstitutionalFlowWidget />
        </div>
        <div className="rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-surface)] p-4">
          <SectorPerformanceChart />
        </div>
      </div>
    </div>
  );
}

export default MarketPulseWorkspace;
