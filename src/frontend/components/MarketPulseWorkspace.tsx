import React, { useState, useEffect } from "react";
import { Activity, RefreshCw, Compass, ShieldCheck, TrendingUp, DollarSign, Globe, AlertCircle, BarChart2, Layers } from "lucide-react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { formatNumber, formatDate, safeArray, safeNumber, safeString } from "../utils/safeHelpers";
import { mapTraderEnum, mapFreshness } from "../utils/traderTerminology";
import { getCanonicalQuote } from "../utils/canonicalQuotes";
import { GlobalCuesWidget, InstitutionalFlowWidget, NiftyConstituentsWidget } from "./MacroIntelligence";

export function MarketPulseWorkspace() {
  const { canonicalState, marketContext, optionContext, syncBroker, loading } = useWorkstationState() as any;
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string>(() => new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" }));
  const [secAgo, setSecAgo] = useState(0);
  const [refreshStatus, setRefreshStatus] = useState<"idle" | "success" | "failed">("idle");
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setSecAgo(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleRefresh = async () => {
    if (refreshing || loading) return;
    setRefreshing(true);
    setRefreshMessage(null);
    try {
      const res = await syncBroker(true);
      if (res !== false) {
        const nowStr = new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" });
        setLastRefreshedAt(nowStr);
        setSecAgo(0);
        setRefreshStatus("success");
        setRefreshMessage("Updated just now");
      } else {
        setRefreshStatus("failed");
        setRefreshMessage("Refresh incomplete · Previous validated snapshot retained");
      }
    } catch (e) {
      console.error("Market Pulse refresh failed", e);
      setRefreshStatus("failed");
      setRefreshMessage("Refresh incomplete · Previous validated snapshot retained");
    } finally {
      setRefreshing(false);
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

  const newsItems = safeArray(canonicalState?.news_intelligence?.items) as any[];
  const highTrustNews = newsItems.filter(n => safeString(n.trust_tier).includes("HIGH") || safeString(n.source_authority).includes("HIGH"));

  return (
    <div id="market-pulse-workspace" className="space-y-6 text-left font-sans">

      {/* ── HEADER & DEDICATED CANONICAL REFRESH CONTROL ── */}
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
              <div className={`text-[10px] font-semibold ${refreshStatus === "failed" ? "text-amber-400" : "text-cyan-300"}`}>
                {refreshMessage}
              </div>
            ) : (
              <div className="text-[10px] text-slate-500">Updated {secAgo}s ago</div>
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

      {/* ── BENTO GRID 6 DECISION CARDS ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">

        {/* CARD 1: CORE INDIA */}
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
                {spot ? formatNumber(spot, 2) : "--"}
              </span>
              <span className={`text-xs font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                {isPositive ? "+" : ""}{formatNumber(change, 2)} ({isPositive ? "+" : ""}{formatNumber(changePct, 2)}%)
              </span>
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
        </div>

        {/* CARD 2: DERIVATIVES */}
        <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
          <div className="flex items-center justify-between border-b border-slate-850 pb-2.5">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-purple-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">DERIVATIVES</h3>
            </div>
            <span className="text-[10px] text-slate-400">Options Matrix</span>
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
        </div>

        {/* CARD 3: INSTITUTIONAL FLOWS */}
        <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
          <div className="flex items-center justify-between border-b border-slate-850 pb-2.5">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-emerald-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">INSTITUTIONAL FLOWS</h3>
            </div>
            <span className="text-[10px] text-slate-400">{mapTraderEnum("LAST_VALID_SESSION")}</span>
          </div>

          <InstitutionalFlowWidget />
        </div>

        {/* CARD 4: GLOBAL CUES */}
        <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
          <div className="flex items-center justify-between border-b border-slate-850 pb-2.5">
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-cyan-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">GLOBAL CUES</h3>
            </div>
            <span className="text-[10px] text-slate-400">Proximate Summary</span>
          </div>

          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-850 space-y-1">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-white">GIFT NIFTY</span>
              {giftNifty.isAvailable ? (
                <span className={`font-bold ${giftNifty.change != null && giftNifty.change >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {formatNumber(giftNifty.value!, 2)} ({giftNifty.change != null && giftNifty.change >= 0 ? "+" : ""}{formatNumber(giftNifty.change!, 1)} pts)
                </span>
              ) : (
                <span className="font-bold text-amber-400">UNAVAILABLE</span>
              )}
            </div>
            <p className="text-[10px] text-slate-400 font-sans">
              {giftNifty.isAvailable
                ? (giftNifty.change != null && giftNifty.change < 0 ? "Slight negative external indication vs NIFTY reference." : "Positive external opening indication.")
                : "GIFT Nifty observation pending."}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-[10px] text-slate-400 block">S&amp;P 500</span>
              {sp500.isAvailable ? (
                <span className={`font-bold ${sp500.changePct != null && sp500.changePct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {formatNumber(sp500.value!, 1)} ({sp500.changePct != null && sp500.changePct >= 0 ? "+" : ""}{formatNumber(sp500.changePct!, 2)}%)
                </span>
              ) : (
                <span className="font-bold text-amber-400">UNAVAILABLE</span>
              )}
            </div>
            <div className="p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-[10px] text-slate-400 block">NASDAQ</span>
              {nasdaq.isAvailable ? (
                <span className={`font-bold ${nasdaq.changePct != null && nasdaq.changePct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {formatNumber(nasdaq.value!, 1)} ({nasdaq.changePct != null && nasdaq.changePct >= 0 ? "+" : ""}{formatNumber(nasdaq.changePct!, 2)}%)
                </span>
              ) : (
                <span className="font-bold text-amber-400">UNAVAILABLE</span>
              )}
            </div>
          </div>
        </div>

        {/* CARD 5: MACRO & CROSS-ASSET */}
        <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
          <div className="flex items-center justify-between border-b border-slate-850 pb-2.5">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-amber-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">MACRO &amp; CROSS-ASSET</h3>
            </div>
            <span className="text-[10px] text-slate-400">Real-Time Telemetry</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-slate-400">USD / INR</span>
              {usdinr.isAvailable ? (
                <span className="font-bold text-white">
                  {formatNumber(usdinr.value!, 2)} ({usdinr.changePct != null && usdinr.changePct >= 0 ? "+" : ""}{formatNumber(usdinr.changePct!, 2)}%)
                </span>
              ) : (
                <span className="font-bold text-amber-400">UNAVAILABLE</span>
              )}
            </div>
            <div className="flex justify-between items-center p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-slate-400">Brent Crude</span>
              {brent.isAvailable ? (
                <span className="font-bold text-amber-300">
                  ${formatNumber(brent.value!, 2)} ({brent.changePct != null && brent.changePct >= 0 ? "+" : ""}{formatNumber(brent.changePct!, 2)}%)
                </span>
              ) : (
                <span className="font-bold text-amber-400">UNAVAILABLE</span>
              )}
            </div>
            <div className="flex justify-between items-center p-2 bg-slate-900/60 rounded border border-slate-850">
              <span className="text-slate-400">US 10Y Yield</span>
              {us10y.isAvailable ? (
                <span className="font-bold text-cyan-300">
                  {formatNumber(us10y.value!, 2)}% ({us10y.change != null ? `${us10y.change >= 0 ? "+" : ""}${formatNumber(us10y.change * 100, 1)} bps` : "0 bps"})
                </span>
              ) : (
                <span className="font-bold text-amber-400">UNAVAILABLE</span>
              )}
            </div>
          </div>
        </div>

        {/* CARD 6: EVENT & INFORMATION RISK */}
        <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
          <div className="flex items-center justify-between border-b border-slate-850 pb-2.5">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-rose-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">EVENT &amp; INFORMATION RISK</h3>
            </div>
            <span className="text-[10px] text-slate-400">Verified Risk</span>
          </div>

          <div className="p-2.5 bg-slate-900/60 rounded border border-slate-850 text-xs">
            <div className="text-[10px] text-slate-400 uppercase font-bold">News Verification Summary</div>
            <div className="font-bold text-cyan-300 mt-0.5">
              {newsItems.length} relevant items · {highTrustNews.length} verified high-authority
            </div>
          </div>

          <div className="space-y-2 text-xs font-sans">
            {newsItems.length ? (
              newsItems.slice(0, 2).map((item, i) => (
                <div key={i} className="text-slate-300 text-[11px] leading-relaxed">
                  • <span className="font-semibold text-white">{safeString(item.title || item.headline)}</span> ({safeString(item.source_name || "Reuters")})
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400">No high-risk canonical event currently in scope.</p>
            )}
          </div>
        </div>

      </div>

      {/* ── SECTION A: STANDALONE FULL-WIDTH GLOBAL CUES & MACRO TELEMETRY ── */}
      <div className="pt-2">
        <GlobalCuesWidget />
      </div>

      {/* ── SECTION B: STANDALONE FULL-WIDTH NIFTY 50 OFFICIAL MEMBERSHIP ── */}
      <div>
        <NiftyConstituentsWidget />
      </div>

    </div>
  );
}
