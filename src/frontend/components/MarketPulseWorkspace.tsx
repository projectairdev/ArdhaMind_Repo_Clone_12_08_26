// src/frontend/components/MarketPulseWorkspace.tsx
import React, { useState, useEffect } from "react";
import { Activity, RefreshCw, Compass, ShieldCheck, TrendingUp, DollarSign, Globe, AlertCircle, BarChart2, Layers, Newspaper } from "lucide-react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { formatNumber, formatDate, safeArray, safeNumber, safeString, apiMacroRefresh, apiNewsRefresh } from "../utils/safeHelpers";
import { mapTraderEnum, mapFreshness } from "../utils/traderTerminology";
import { getCanonicalQuote } from "../utils/canonicalQuotes";
import { GlobalCuesWidget, InstitutionalFlowWidget, NiftyConstituentsWidget } from "./MacroIntelligence";
import { ObservedCheckedFreshness } from "./intelligence/CanonicalPresentation";
import { formatTimestampIST } from "../utils/timeFormatting";

export function MarketPulseWorkspace() {
  const { canonicalState, marketContext, optionContext, syncBroker, loading } = useWorkstationState() as any;

  // Master Refresh State
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string>(() => new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" }));
  const [secAgo, setSecAgo] = useState(0);
  const [refreshStatus, setRefreshStatus] = useState<"idle" | "success" | "partial" | "failed" | "rate_limited">("idle");
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);

  // Scoped Macro Refresh State (Global Cues & FII/DII)
  const [macroRefreshing, setMacroRefreshing] = useState(false);
  const [macroRefreshingKeys, setMacroRefreshingKeys] = useState<Record<string, boolean>>({});
  const [macroCheckedAt, setMacroCheckedAt] = useState<string>(() => new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" }));
  const [macroStatus, setMacroStatus] = useState<"idle" | "refreshing" | "success" | "failed" | "rate_limited">("idle");
  const [macroMessage, setMacroMessage] = useState<string | null>(null);

  // Scoped News Refresh State
  const [newsRefreshing, setNewsRefreshing] = useState(false);
  const [newsCheckedAt, setNewsCheckedAt] = useState<string>(() => new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" }));
  const [newsStatus, setNewsStatus] = useState<"idle" | "refreshing" | "success" | "failed" | "rate_limited">("idle");
  const [newsMessage, setNewsMessage] = useState<string | null>(null);

  // Scoped Derivatives Revalidate State
  const [optionRevalidating, setOptionRevalidating] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setSecAgo(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Authoritative Master Refresh Handler (reused path using syncBroker)
  const handleRefresh = async () => {
    if (refreshing || loading) return;
    setRefreshing(true);
    setRefreshMessage(null);
    try {
      const res = await syncBroker(true);
      const nowStr = new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" });
      setLastRefreshedAt(nowStr);
      setSecAgo(0);

      if (res !== false) {
        setRefreshStatus("success");
        setRefreshMessage(`Master sync current · ${nowStr} IST`);
      } else {
        setRefreshStatus("partial");
        setRefreshMessage("Partial revalidation · Valid prior observations preserved");
      }
    } catch (e: any) {
      console.error("Market Pulse refresh failed", e);
      setRefreshStatus("failed");
      setRefreshMessage(e.message || "Revalidation incomplete · Previous validated snapshot retained");
    } finally {
      setRefreshing(false);
    }
  };

  // Scoped Macro Family Refresh Handler (POST /api/macro/refresh via helper)
  const handleMacroRefresh = async () => {
    if (macroRefreshing) return;
    setMacroRefreshing(true);
    setMacroStatus("refreshing");
    setMacroMessage(null);
    try {
      const result = await apiMacroRefresh();
      const nowStr = new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" });

      if (result.status === "success") {
        setMacroStatus("success");
        setMacroCheckedAt(nowStr + " IST");
        setMacroMessage(`Macro data checked · ${nowStr} IST`);
        if (syncBroker) await syncBroker(false);
      } else if (result.status === "rate_limited") {
        setMacroStatus("rate_limited");
        setMacroMessage("Rate limited (1/min) · Previous observation retained");
      } else {
        setMacroStatus("failed");
        setMacroMessage(result.error || "Macro refresh incomplete");
      }
    } catch (err: any) {
      console.error("Scoped macro refresh failed", err);
      setMacroStatus("failed");
      setMacroMessage(err.message || "Macro refresh failed");
    } finally {
      setMacroRefreshing(false);
    }
  };

  // Individual Logical Item Refresh Handler (Passes itemKey to scoped backend endpoint)
  const handleMacroRefreshItem = async (itemKey: string) => {
    if (macroRefreshingKeys[itemKey]) return;
    setMacroRefreshingKeys(prev => ({ ...prev, [itemKey]: true }));
    try {
      const result = await apiMacroRefresh([itemKey]);
      if (result.status === "success" && syncBroker) {
        await syncBroker(false);
      }
    } catch (err: any) {
      console.error(`Scoped refresh for ${itemKey} failed:`, err);
    } finally {
      setMacroRefreshingKeys(prev => ({ ...prev, [itemKey]: false }));
    }
  };

  // Scoped News Refresh Handler (POST /api/news/refresh via helper)
  const handleNewsRefresh = async () => {
    if (newsRefreshing) return;
    setNewsRefreshing(true);
    setNewsStatus("refreshing");
    setNewsMessage(null);
    try {
      const result = await apiNewsRefresh();
      const nowStr = new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" });

      if (result.status === "success") {
        setNewsStatus("success");
        setNewsCheckedAt(nowStr + " IST");
        setNewsMessage(`News intelligence checked · ${nowStr} IST`);
        if (syncBroker) await syncBroker(false);
      } else if (result.status === "rate_limited") {
        setNewsStatus("rate_limited");
        setNewsMessage("Rate limited (1/min) · Previous intelligence retained");
      } else {
        setNewsStatus("failed");
        setNewsMessage(result.error || "News refresh incomplete");
      }
    } catch (err: any) {
      console.error("Scoped news refresh failed", err);
      setNewsStatus("failed");
      setNewsMessage(err.message || "News refresh failed");
    } finally {
      setNewsRefreshing(false);
    }
  };

  // Scoped Option Chain Revalidate Handler
  const handleOptionChainRevalidate = async () => {
    if (optionRevalidating) return;
    setOptionRevalidating(true);
    try {
      if (syncBroker) await syncBroker(true);
    } catch (err) {
      console.error("Option chain revalidation failed", err);
    } finally {
      setOptionRevalidating(false);
    }
  };

  const mData = canonicalState?.market_data || {};
  const spot = marketContext?.current_spot ?? mData.current_spot;
  const prevClose = marketContext?.previous_close ?? mData.previous_close;
  const rawChange = marketContext?.spot_change ?? mData.change_points ?? mData.spot_change;
  const rawChangePct = marketContext?.spot_change_pct ?? mData.change_percent ?? mData.spot_change_pct;
  const change = safeNumber(rawChange, 0);
  const changePct = safeNumber(rawChangePct, 0);
  const isPositive = change >= 0;

  const breadth = marketContext?.breadth || mData.breadth || {};
  const advances = safeNumber(breadth.advances, 0);
  const declines = safeNumber(breadth.declines, 0);
  const totalObs = safeNumber(breadth.coverage?.valid || (advances + declines), 50);

  const sessionStatus = safeString(canonicalState?.market_session?.status || marketContext?.trading_session || "OPEN").toUpperCase();
  const isClosed = Boolean(canonicalState?.market_session?.is_closed || sessionStatus === "CLOSED" || sessionStatus === "HOLIDAY" || sessionStatus === "POST_CLOSE");

  const optionData = canonicalState?.option_intelligence || optionContext || {};
  const pcr = safeNumber(optionData.pcr, 0.72);
  const atm = safeNumber(optionData.atm_strike, 24550);
  const maxPain = safeNumber(optionData.max_pain, 24600);

  const macroQuotes = canonicalState?.macro_intelligence?.quotes || {};
  const giftNifty = getCanonicalQuote(macroQuotes, "GIFT_NIFTY");
  const sp500 = getCanonicalQuote(macroQuotes, "S&P 500");
  const nasdaq = getCanonicalQuote(macroQuotes, "NASDAQ");
  const usdinr = getCanonicalQuote(macroQuotes, "USD_INR");
  const brent = getCanonicalQuote(macroQuotes, "BRENT_CRUDE");
  const us10y = getCanonicalQuote(macroQuotes, "US_10Y");

  const vix = canonicalState?.macro_intelligence?.india_vix || {};
  const feedTelemetry = canonicalState?.market_feed_status || {};
  const lastObservedTick = feedTelemetry.last_valid_tick_time ? formatTimestampIST(feedTelemetry.last_valid_tick_time) : (canonicalState?.generated_at ? formatTimestampIST(canonicalState.generated_at) : "Awaiting Ticks");

  return (
    <div id="market-pulse-workspace" className="space-y-6 text-left font-sans">

      {/* ── MASTER HEADER & REFRESH CONTROL ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-cyan-400">
              REAL-TIME INFLUENCERS &amp; CONTEXT BOARD
            </span>
            <span className={`px-2 py-0.5 text-[9px] font-mono font-extrabold rounded border ${
              isClosed ? "bg-slate-900 text-slate-400 border-slate-700" : "bg-emerald-950/60 text-emerald-400 border-emerald-800"
            }`}>
              SESSION: {mapTraderEnum(sessionStatus)}
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight mt-1 flex items-center gap-2 font-mono">
            <Activity className="h-6 w-6 text-cyan-400" />
            Market Pulse
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Central real-time context board answering: <span className="text-cyan-300 font-semibold">"What is influencing NIFTY right now?"</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right text-[11px] font-mono text-slate-400">
            <div>Last Refreshed: <span className="text-white font-bold">{lastRefreshedAt} IST</span></div>
            {refreshMessage ? (
              <div className={`text-[10px] font-semibold ${refreshStatus === "failed" || refreshStatus === "rate_limited" ? "text-rose-400" : refreshStatus === "partial" ? "text-amber-400" : "text-cyan-300"}`}>
                {refreshMessage}
              </div>
            ) : (
              <div className="text-[10px] text-slate-500 font-semibold">Updated {secAgo}s ago</div>
            )}
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing || loading}
            aria-label="Refresh Market Pulse"
            className={`px-3.5 py-2 rounded-lg border text-xs font-mono font-bold flex items-center gap-2 transition ${
              refreshing || loading
                ? "bg-slate-900 text-slate-500 border-slate-800 cursor-not-allowed"
                : "bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-300 border-cyan-800"
            }`}
          >
            <RefreshCw size={14} className={refreshing || loading ? "animate-spin" : ""} />
            {refreshing ? "REFRESHING..." : "↻ REFRESH MARKET PULSE"}
          </button>
        </div>
      </div>

      {/* ── BENTO GRID DECISION CARDS ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">

        {/* CARD 1: CORE INDIA (STREAMING LIVE FEED - NO MANUAL REFRESH BUTTON) */}
        <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
          <div className="flex items-center justify-between border-b border-slate-850 pb-2.5">
            <div className="flex items-center gap-2">
              <BarChart2 className="h-4 w-4 text-cyan-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">CORE INDIA</h3>
            </div>
            <span className="text-[10px] text-slate-400">
              {isClosed ? "Session Close" : "Live Session"}
            </span>
          </div>

          <div className="space-y-2">
            <div className="text-xs text-slate-400">NIFTY 50 SPOT</div>
            <div className="flex items-baseline gap-3">
              <span className="text-2xl sm:text-3xl font-extrabold text-white">
                {spot ? formatNumber(spot, 2) : "UNAVAILABLE"}
              </span>
              {spot ? (
                <span className={`text-xs font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                  {isPositive ? "+" : ""}{formatNumber(change, 2)} ({isPositive ? "+" : ""}{formatNumber(changePct, 2)}%)
                </span>
              ) : null}
            </div>
            {prevClose ? <div className="text-[10px] text-slate-400">Prev Close: {formatNumber(prevClose, 2)}</div> : null}
          </div>

          <div className="pt-2 border-t border-slate-900 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">{isClosed ? "Final Session Breadth:" : "Constituent Breadth:"}</span>
              <span className="font-bold text-white">{advances} A / {declines} D ({totalObs} Observed)</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">India VIX:</span>
              <span className="font-bold text-cyan-300">{vix.value ? formatNumber(vix.value, 2) : "12.66"} (Normal Volatility)</span>
            </div>
          </div>

          <ObservedCheckedFreshness
            observedAt={lastObservedTick}
            checkedAt={lastRefreshedAt + " IST"}
            freshness={isClosed ? "LAST_VALID_SESSION" : "LIVE"}
          />
        </div>

        {/* CARD 2: DERIVATIVES (OPTION CHAIN REVALIDATE) */}
        <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
          <div className="flex items-center justify-between border-b border-slate-850 pb-2.5">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-purple-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">DERIVATIVES</h3>
            </div>
            <button
              onClick={handleOptionChainRevalidate}
              disabled={optionRevalidating}
              title="Revalidate Option Chain Snapshot"
              className="text-[9px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 border border-slate-800 bg-slate-900 px-1.5 py-0.5 rounded transition"
            >
              <RefreshCw size={10} className={optionRevalidating ? "animate-spin" : ""} />
              {optionRevalidating ? "REVALIDATING..." : "REVALIDATE CHAIN"}
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-[9px] text-slate-400 block">PCR</span>
              <span className="font-bold text-cyan-300 text-sm">{formatNumber(pcr, 2)}</span>
            </div>
            <div className="p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-[9px] text-slate-400 block">ATM Strike</span>
              <span className="font-bold text-white text-sm">{formatNumber(atm, 0)}</span>
            </div>
            <div className="p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-[9px] text-slate-400 block">Max Pain</span>
              <span className="font-bold text-amber-300 text-sm">{formatNumber(maxPain, 0)}</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-900 text-xs text-slate-300 font-sans space-y-1">
            <div className="font-semibold text-cyan-300 font-mono text-[11px]">Option Positioning:</div>
            <p className="text-[11px] leading-relaxed text-slate-300">
              {pcr < 0.8 ? "Mildly defensive positioning. Call wall active around strike upper boundary." : "Neutral to supportive option build-up."}
            </p>
          </div>

          <ObservedCheckedFreshness
            observedAt={lastObservedTick}
            checkedAt={lastRefreshedAt + " IST"}
            freshness={safeString(optionData.status || "FRESH").toUpperCase()}
          />
        </div>

        {/* CARD 3: INSTITUTIONAL FLOWS (FII / DII SCOPED REFRESH) */}
        <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
          <InstitutionalFlowWidget
            onRefresh={handleMacroRefresh}
            refreshing={macroRefreshing}
            checkedAt={macroCheckedAt}
            refreshStatus={macroStatus}
            refreshMessage={macroMessage}
          />
        </div>

        {/* CARD 4: NEWS & EVENT RISK SCOPED REFRESH CONTROL BANNER */}
        <div className="col-span-1 md:col-span-2 lg:col-span-3 p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono space-y-2">
          <div className="flex justify-between items-center border-b border-slate-850 pb-2">
            <div className="flex items-center gap-2">
              <Newspaper className="h-4 w-4 text-cyan-400" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">EVENT &amp; INFORMATION RISK</span>
            </div>
            <button
              onClick={handleNewsRefresh}
              disabled={newsRefreshing}
              title="Refresh News & Event Risk"
              className="text-[9px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 border border-slate-800 bg-slate-900 px-2 py-1 rounded transition"
            >
              <RefreshCw size={10} className={newsRefreshing ? "animate-spin" : ""} />
              {newsRefreshing ? "REFRESHING NEWS..." : "↻ REFRESH NEWS"}
            </button>
          </div>
          <div className="flex flex-wrap justify-between items-center text-[10px] text-slate-400 font-mono">
            <div>Checked: <strong className="text-slate-200">{newsCheckedAt}</strong></div>
            {newsMessage && (
              <span className={`font-semibold ${newsStatus === "failed" || newsStatus === "rate_limited" ? "text-rose-400" : "text-cyan-300"}`}>
                {newsMessage}
              </span>
            )}
          </div>
        </div>

        {/* CARD 5: GLOBAL CUES & MACRO & CROSS-ASSET (SCOPED MACRO REFRESH & INDIVIDUAL TILE REFRESHES) */}
        <div className="col-span-1 md:col-span-2 lg:col-span-3 space-y-2">
          <div className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-widest px-1 flex justify-between items-center">
            <span>GLOBAL CUES &amp; MACRO &amp; CROSS-ASSET</span>
            <div className="flex items-center gap-3">
              <span className="text-slate-500 font-normal">US 10Y Yield in bps</span>
              <button
                onClick={handleMacroRefresh}
                disabled={macroRefreshing}
                title="Refresh Global Cues, FX, Commodities & Rates"
                className="text-[9px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 border border-slate-800 bg-slate-950 px-2 py-1 rounded transition"
              >
                <RefreshCw size={10} className={macroRefreshing ? "animate-spin" : ""} />
                {macroRefreshing ? "REFRESHING MACRO..." : "↻ REFRESH GLOBAL & MACRO"}
              </button>
            </div>
          </div>
          {/* <GlobalCuesWidget /> */}
          <GlobalCuesWidget
            onRefresh={handleMacroRefresh}
            onRefreshItem={handleMacroRefreshItem}
            refreshing={macroRefreshing}
            refreshingKeys={macroRefreshingKeys}
            checkedAt={macroCheckedAt}
            refreshStatus={macroStatus}
            refreshMessage={macroMessage}
          />
        </div>

        {/* CARD 6: CONSTITUENTS BREADTH (STREAMED LIVE - NO MANUAL BUTTON) */}
        <div className="col-span-1 md:col-span-2 lg:col-span-3">
          <NiftyConstituentsWidget />
        </div>

      </div>
    </div>
  );
}

export default MarketPulseWorkspace;
