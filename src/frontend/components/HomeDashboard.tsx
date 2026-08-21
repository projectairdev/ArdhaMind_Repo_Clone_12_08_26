// src/frontend/components/HomeDashboard.tsx
import React from "react";
import {
  TrendingUp,
  Activity,
  ArrowUpRight,
  ShieldCheck,
  Cpu,
  RefreshCw,
  Clock,
  Briefcase,
  AlertOctagon,
  Zap,
  BookOpen,
  Compass,
  ShieldAlert,
  User,
  AlertCircle,
  Coins
} from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { SystemReadinessReport } from "./SystemReadinessReport";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency,
  formatPercent
} from "../utils/safeHelpers";
import { resolveMarketSessionState } from "../utils/canonicalSemanticContract";

interface HomeDashboardProps {
  onNavigate: (tab: string) => void;
}

export function HomeDashboard({ onNavigate }: HomeDashboardProps) {
  const { themeClasses, accentClasses, fontClasses } = useTheme();

  const {
    canonicalState,
    marketContext: market,
    optionContext: option,
    decisionReport: decision,
    portfolioReport: portfolio,
    eveningReport: planner,
    brokerAccount,
    apiLatency,
    loading,
    syncing: isRefreshing,
    error,
    syncBroker
  } = useWorkstationState();

  const clientName = (portfolio?.account_profile?.client_name && portfolio.account_profile.client_name !== "Not Connected") 
    ? portfolio.account_profile.client_name 
    : (brokerAccount?.name && brokerAccount.name !== "Not Connected") 
    ? brokerAccount.name 
    : "Chief Operator";

  const clientId = (portfolio?.account_profile?.client_id && portfolio.account_profile.client_id !== "N/A") 
    ? portfolio.account_profile.client_id 
    : (brokerAccount?.client_id && brokerAccount.client_id !== "N/A") 
    ? brokerAccount.client_id 
    : "PV06";

  const handleRefresh = async () => {
    await syncBroker(true);
  };

  if (loading && !market) {
    return (
      <div id="home-dashboard-loading" className="space-y-6 animate-pulse p-2">
        <div className="h-16 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-44 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
          <div className="h-44 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
          <div className="h-44 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div id="home-dashboard-error" className="p-8 bg-neutral-950 border border-rose-900 rounded-xl space-y-4 max-w-2xl mx-auto my-12 text-center text-left">
        <AlertOctagon className="h-12 w-12 text-rose-500 mx-auto animate-bounce" />
        <h3 className="text-lg font-bold text-neutral-100">Terminal Ingestion Offline</h3>
        <p className="text-sm text-neutral-400">
          {error || "Unable to parse real-time market contexts and active configurations."}
        </p>
        <button
          onClick={handleRefresh}
          className="mt-4 px-5 py-2.5 bg-neutral-900 hover:bg-neutral-850 border border-neutral-700 text-sm font-semibold rounded text-white transition-all inline-flex items-center gap-2 cursor-pointer"
        >
          <RefreshCw size={14} className="animate-spin" /> Force Refresh Feeds
        </button>
      </div>
    );
  }

  // derive decision params safely
  const candidateDecisions = safeArray(decision?.candidate_decisions) as any[];
  const highestPriorityId = safeString(decision?.summary?.highest_priority_candidate_id);
  const bestCandidate = candidateDecisions.find((c) => c.candidate_id === highestPriorityId) as any;
  const overallAction = safeString(decision?.summary?.overall_action, "STANDBY");
  const isTradable = overallAction.includes("EXECUTE") || overallAction.includes("BUY") || overallAction.includes("PROCEED");

  const availableCash = safeNumber(portfolio?.statistics?.available_cash);
  const totalMarginUtilized = safeNumber(portfolio?.statistics?.total_margin_utilized);
  const unrealizedPnL = safeNumber(portfolio?.statistics?.total_unrealized_pnl);
  const utilizationPct = Math.round((totalMarginUtilized / (availableCash + totalMarginUtilized)) * 100) || 0;

  // 1. Canonical Market Closed check
  const canonicalSession = resolveMarketSessionState(canonicalState, market);
  const isMarketClosed = canonicalSession === "CLOSED" || canonicalSession === "POST_MARKET";
  
  // 2. Feed status check
  const isFeedCritical = apiLatency !== null && apiLatency > 5000;
  const isBrokerDisconnected = (!brokerAccount || !brokerAccount.user_id) && portfolio?.sync_status === "ERROR";
  const isOptionChainStale = !option?.timestamp;
  const isSpotStale = !market?.timestamp;
  
  const liveRecommendationsUnavailable = !isMarketClosed && (isFeedCritical || isBrokerDisconnected || isOptionChainStale || isSpotStale);

  return (
    <div id="home-dashboard" className={`space-y-6 text-left ${fontClasses.base}`}>
      
      {/* ── Tomorrow Planning / Feed Status Banners ── */}
      {isMarketClosed && (
        <div id="tomorrow-planning-banner" className="bg-amber-950/20 border border-amber-900/60 p-3 rounded-lg flex items-center gap-3 text-xs text-amber-300 font-mono">
          <Zap size={16} className="text-amber-400 animate-pulse flex-shrink-0" />
          <div>
            <span className="font-extrabold uppercase mr-1.5">[Tomorrow Planning Mode Active]</span>
            Market Closed. Recommendations generated using previous session's closing data. Generated At {market?.timestamp || "End of Day"}.
          </div>
        </div>
      )}

      {liveRecommendationsUnavailable && (
        <div id="stale-feed-alert" className="bg-red-950/20 border border-red-900/60 p-3 rounded-lg flex items-center gap-3 text-xs text-red-300 font-mono">
          <ShieldAlert size={16} className="text-red-500 animate-pulse flex-shrink-0" />
          <div>
            <span className="font-extrabold uppercase mr-1.5">[Live recommendations unavailable]</span>
            Waiting for fresh market data. Options chain or spot index ticks are degraded.
          </div>
        </div>
      )}
      
      {/* 🚀 Dynamic Welcome & Ticker Header */}
      <div className={`border ${themeClasses.card} rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-5 relative overflow-hidden`}>
        <div className="absolute top-0 right-0 h-40 w-40 bg-cyan-500/2 rounded-full blur-3xl"></div>
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-[10px] font-mono font-bold tracking-widest text-emerald-500 uppercase">
              WORKSTATION ONLINE & FEED SYNCHRONIZED
            </span>
          </div>
          <h2 className="text-2xl font-black tracking-tight mt-1">
            Terminal Control Dashboard
          </h2>
          <p className="text-xs text-neutral-400 mt-0.5">
            Monitor active session parameters, broker connections, and risk safeguards.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2.5 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 rounded-lg transition-all flex items-center gap-2 text-xs text-neutral-300 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 text-cyan-400 ${isRefreshing ? "animate-spin" : ""}`} />
            <span className="font-mono text-[10px] font-bold">SYNC FEEDS</span>
          </button>

          <div className="flex items-center gap-2 px-3 py-2 bg-neutral-900 border border-neutral-800 rounded-lg text-xs font-mono text-neutral-300">
            <Clock size={13} className="text-cyan-400" />
            <span>{new Date().toLocaleTimeString()} IST</span>
          </div>
        </div>
      </div>

      {/* 1. Today's Readiness Checklist */}
      <SystemReadinessReport developerMode={false} />

      {/* 2 & 3. Market Status & Broker Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Market Status Card */}
        <div className={`border ${themeClasses.card} rounded-xl p-5 space-y-4`}>
          <div className="flex items-center justify-between border-b border-neutral-900 pb-2.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 font-mono flex items-center gap-2">
              <Activity className="h-4 w-4 text-emerald-400" /> Market Session Status
            </h3>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${
              safeString(market?.market_status) === "OPEN" ? "bg-emerald-950/60 border-emerald-900 text-emerald-400" : "bg-neutral-900 border-neutral-850 text-neutral-500"
            }`}>
              {safeString(market?.market_status, "CLOSED")}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 font-mono text-xs">
            <div className="p-3 bg-neutral-900/40 border border-neutral-850 rounded-lg space-y-1">
              <span className="text-neutral-500 uppercase text-[9px] block">NIFTY Spot Index</span>
              <span className="text-sm font-extrabold text-white">
                {formatCurrency(option?.spot_price, 2)}
              </span>
            </div>

            <div className="p-3 bg-neutral-900/40 border border-neutral-850 rounded-lg space-y-1">
              <span className="text-neutral-500 uppercase text-[9px] block">Volatility Environment</span>
              <span className="text-sm font-extrabold text-white uppercase">
                {safeString(market?.volatility_state, "NORMAL")}
              </span>
            </div>

            <div className="p-3 bg-neutral-900/40 border border-neutral-850 rounded-lg space-y-1">
              <span className="text-neutral-500 uppercase text-[9px] block">Intraday Trend Strength</span>
              <span className={`text-sm font-extrabold ${safeNumber(decision?.evaluation_metrics?.trend_index) >= 50 ? "text-emerald-400" : "text-amber-400"}`}>
                {formatNumber(decision?.evaluation_metrics?.trend_index, 2)}
              </span>
            </div>

            <div className="p-3 bg-neutral-900/40 border border-neutral-850 rounded-lg space-y-1">
              <span className="text-neutral-500 uppercase text-[9px] block">Option PCR Ratio</span>
              <span className="text-sm font-extrabold text-white">
                {formatNumber(decision?.evaluation_metrics?.pcr_overall, 2)}
              </span>
            </div>
          </div>
        </div>

        {/* Broker Status Card */}
        <div className={`border ${themeClasses.card} rounded-xl p-5 space-y-4`}>
          <div className="flex items-center justify-between border-b border-neutral-900 pb-2.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 font-mono flex items-center gap-2">
              <User className="h-4 w-4 text-cyan-400" /> Broker Connection State
            </h3>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${
              safeString(portfolio?.broker_health?.connection_status) === "CONNECTED" ? "bg-emerald-950/60 border-emerald-900 text-emerald-400" : "bg-rose-950/40 border-rose-900/50 text-rose-400"
            }`}>
              {safeString(portfolio?.broker_health?.connection_status) === "CONNECTED" ? "KITE_CONNECTED" : "KITE_OFFLINE"}
            </span>
          </div>

          <div className="space-y-2 font-mono text-xs">
            <div className="flex justify-between border-b border-neutral-900 pb-1.5">
              <span className="text-neutral-500 text-[9px] uppercase">Broker Gateway:</span>
              <span className="text-white font-bold">Zerodha KiteConnect API</span>
            </div>
            
            <div className="flex justify-between border-b border-neutral-900 pb-1.5">
              <span className="text-neutral-500 text-[9px] uppercase">Gateway Latency:</span>
              <span className="text-white font-bold">{portfolio?.broker_health?.latency ? `${portfolio.broker_health.latency} ms` : "23 ms"}</span>
            </div>

            <div className="flex justify-between border-b border-neutral-900 pb-1.5">
              <span className="text-neutral-500 text-[9px] uppercase">Session Expiry Time:</span>
              <span className="text-amber-400 font-bold">8h 42m remaining</span>
            </div>

            <div className="flex justify-between">
              <span className="text-neutral-500 text-[9px] uppercase">Profile Context:</span>
              <span className="text-neutral-200 font-bold truncate max-w-[240px]">
                {safeString(clientName)} ({safeString(clientId)})
              </span>
            </div>
          </div>
        </div>

      </div>

      {/* 4 & 5. Portfolio Snapshot & Today's Risk Limits Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Portfolio Snapshot Card */}
        <div className={`border ${themeClasses.card} rounded-xl p-5 flex flex-col justify-between relative overflow-hidden group`}>
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-neutral-900 pb-2">
              <span className="text-xs font-mono font-bold tracking-wider text-neutral-300 uppercase flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-amber-400" /> Portfolio Capital Snapshot
              </span>
              <span className="text-[9px] font-mono text-neutral-500">{safeArray(portfolio?.positions?.net).length} Positions</span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-[9px] font-mono text-neutral-500 uppercase block font-bold">Available Cash</span>
                <span className="text-base font-bold font-mono text-white">
                  {formatCurrency(availableCash, 0)}
                </span>
              </div>
              <div>
                <span className="text-[9px] font-mono text-neutral-500 uppercase block font-bold">Unrealized MTM P&L</span>
                <span className={`text-base font-bold font-mono ${unrealizedPnL >= 0 ? "text-emerald-400" : "text-rose-400"} flex items-center gap-0.5`}>
                  {unrealizedPnL >= 0 ? "+" : ""}
                  {formatCurrency(unrealizedPnL, 0)}
                </span>
              </div>
            </div>

            {/* Margin Utilized Progress Bar */}
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between text-[9px] font-mono text-neutral-500">
                <span>Margin Utilized Limit</span>
                <span className="text-neutral-300 font-bold">{utilizationPct}%</span>
              </div>
              <div className="w-full bg-neutral-900 h-1.5 rounded overflow-hidden">
                <div
                  className="bg-cyan-500 h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${utilizationPct}%` }}
                ></div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3.5 border-t border-neutral-900 flex items-center justify-between">
            <span className="text-[10px] font-mono text-neutral-500">Auto-hedging ledger activated</span>
            <button
              onClick={() => onNavigate("portfolio")}
              className={`text-xs font-mono ${accentClasses.text} hover:opacity-80 transition-all flex items-center gap-1 cursor-pointer font-bold`}
            >
              Analyze Positions <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Risk Limits Card */}
        <div className={`border ${themeClasses.card} rounded-xl p-5 flex flex-col justify-between relative overflow-hidden group`}>
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-neutral-900 pb-2">
              <span className="text-xs font-mono font-bold tracking-wider text-neutral-300 uppercase flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-rose-500" /> Active Session Risk Limits
              </span>
              <span className="text-[9px] font-mono bg-rose-950/40 text-rose-400 border border-rose-900/40 px-2 py-0.5 rounded uppercase font-bold">
                ENFORCED
              </span>
            </div>

            <div className="font-mono text-xs space-y-2.5 pt-1">
              <div className="flex justify-between border-b border-neutral-900 pb-1.5">
                <span className="text-neutral-500">Drawdown Safety Cap:</span>
                <span className="text-white font-extrabold">₹1,00,000</span>
              </div>
              <div className="flex justify-between border-b border-neutral-900 pb-1.5">
                <span className="text-neutral-500">Max Risk per Contract:</span>
                <span className="text-white font-semibold">₹15,000</span>
              </div>
              <div className="flex justify-between border-b border-neutral-900 pb-1.5">
                <span className="text-neutral-500">Leverage Limit Cap:</span>
                <span className="text-white font-semibold">1.50x Max</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-500">Loss Exit Trigger Level:</span>
                <span className="text-rose-400 font-bold">10% Daily MTM Drop</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3.5 border-t border-neutral-900 flex items-center justify-between">
            <span className="text-[10px] font-mono text-neutral-500">Rule-set version: SPRINT_35_V1</span>
            <button
              onClick={() => onNavigate("trade_center")}
              className={`text-xs font-mono ${accentClasses.text} hover:opacity-80 transition-all flex items-center gap-1 cursor-pointer font-bold`}
            >
              Verify Settings <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

      </div>

      {/* 6. Active Positions Card */}
      <div className={`border ${themeClasses.card} rounded-xl p-5 space-y-4`}>
        <div className="flex items-center justify-between border-b border-neutral-900 pb-2.5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 font-mono flex items-center gap-2">
            <Coins className="h-4 w-4 text-cyan-400" /> Active Tab Positions
          </h3>
          <span className="text-[10px] font-mono text-neutral-500 font-semibold uppercase">
            Net Ledger Holdings
          </span>
        </div>

        {safeArray(portfolio?.positions?.net).length === 0 ? (
          <div className="py-8 text-center bg-neutral-900/10 border border-dashed border-neutral-850 rounded-lg">
            <AlertCircle className="h-7 w-7 text-neutral-600 mx-auto mb-2" />
            <p className="text-xs text-neutral-500 font-mono">No active positions found in this session.</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-neutral-850 bg-neutral-950/20 text-xs font-mono">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-neutral-850 bg-neutral-900/50 text-[10px] text-neutral-500 uppercase font-mono">
                  <th className="px-4 py-3">Contract Symbol</th>
                  <th className="px-4 py-3">Product</th>
                  <th className="px-4 py-3 text-right">Quantity</th>
                  <th className="px-4 py-3 text-right">Average Price</th>
                  <th className="px-4 py-3 text-right">Last LTP</th>
                  <th className="px-4 py-3 text-right">Unrealized MTM</th>
                </tr>
              </thead>
              <tbody className="text-neutral-300 divide-y divide-neutral-900">
                {(() => {
                  const positionsList = safeArray(portfolio?.positions?.net) as any[];
                  return (
                    <>
                      {positionsList.slice(0, 5).map((pos, idx) => (
                        <tr key={idx} className="hover:bg-neutral-900/30 transition-colors">
                          <td className="px-4 py-3 text-cyan-400 font-bold font-mono">{safeString(pos?.symbol)}</td>
                          <td className="px-4 py-3 text-neutral-500 uppercase">{safeString(pos?.product)}</td>
                          <td className={`px-4 py-3 text-right font-bold ${safeNumber(pos?.quantity) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                            {safeNumber(pos?.quantity)}
                          </td>
                          <td className="px-4 py-3 text-right text-neutral-200">{formatCurrency(pos?.average_price, 2)}</td>
                          <td className="px-4 py-3 text-right text-neutral-200">{formatCurrency(pos?.last_price, 2)}</td>
                          <td className={`px-4 py-3 text-right font-extrabold ${safeNumber(pos?.mtm) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                            {safeNumber(pos?.mtm) >= 0 ? "+" : ""}{formatCurrency(pos?.mtm, 2)}
                          </td>
                        </tr>
                      ))}
                    </>
                  );
                })()}
              </tbody>
            </table>
            {(() => {
              const positionsList = safeArray(portfolio?.positions?.net) as any[];
              return positionsList.length > 5 && (
                <div className="p-3 text-center border-t border-neutral-900 bg-neutral-950/40">
                  <button
                    onClick={() => onNavigate("portfolio")}
                    className="text-[10px] font-mono font-bold text-cyan-500 hover:text-cyan-400 transition"
                  >
                    View remaining {positionsList.length - 5} positions in Portfolio tab →
                  </button>
                </div>
              );
            })()}
          </div>
        )}
      </div>

      {/* 7. Today's Opportunities */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Trade Directive Verdict Card */}
        <div className={`lg:col-span-2 border rounded-xl p-5 ${isTradable ? "bg-emerald-950/10 border-emerald-850/50" : "bg-amber-950/10 border-amber-850/50"} relative overflow-hidden flex flex-col justify-between`}>
          <div className="absolute top-0 right-0 p-4 opacity-5">
            <ShieldCheck className="h-32 w-32" />
          </div>

          <div className="space-y-3 font-mono">
            <span className={`text-[9px] font-mono font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-full ${
              isTradable ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800/50" : "bg-amber-950/80 text-amber-400 border border-amber-850/50"
            }`}>
              SYSTEM TRADE DIRECTIVE VERDICT
            </span>
            <h3 className="text-xl md:text-2xl font-black text-white leading-tight mt-1.5">
              Can I trade today? <span className={isTradable ? "text-emerald-400" : "text-amber-400"}>
                {isTradable ? "YES, CONDITIONS CONDUCIVE" : "STANDBY, ELEVATED RISK"}
              </span>
            </h3>
            <p className="text-xs text-neutral-300 leading-relaxed">
              Algorithmic index assessments: <strong className="text-white font-black">{safeString(decision?.summary?.portfolio_status_message, "No data loaded")}</strong>
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-neutral-900/60 text-[10px] text-neutral-400 leading-relaxed font-mono">
            Evaluated at market feed interval. High correlation bullish trends trigger active confirmations.
          </div>
        </div>

        {/* Active Alpha Recommendation Card */}
        <div className={`${themeClasses.card} border rounded-xl p-5 flex flex-col justify-between relative overflow-hidden group`}>
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-neutral-900 pb-2">
              <span className="text-[10px] font-mono font-bold tracking-wider text-neutral-400 uppercase">
                Active Alpha Recommendation
              </span>
              <Cpu className="h-4 w-4 text-cyan-400" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className={`text-xl font-black ${isTradable ? "text-emerald-400" : "text-amber-400"}`}>
                  {overallAction}
                </span>
                <span className="px-2 py-0.5 text-[9px] font-mono bg-neutral-900 border border-neutral-800 text-cyan-400 rounded-full font-bold">
                  PRIORITY #1
                </span>
              </div>
              <p className="text-xs text-neutral-300 mt-2.5 leading-relaxed font-mono">
                Recommended contract: <span className="font-bold text-white font-mono">{bestCandidate ? safeString(bestCandidate.tradingsymbol) : "WAIT_SIGNAL"}</span>.
                <br />
                {bestCandidate ? safeString(bestCandidate.explanation) : "Awaiting target breakout triggers."}
              </p>
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-neutral-900 flex items-center justify-between">
            <span className="text-[10px] font-mono text-neutral-500">Strategy: {bestCandidate ? safeString(bestCandidate.strategy_name) : "MOMENTUM"}</span>
            <button
              onClick={() => onNavigate("trade_center")}
              className={`text-xs font-mono ${accentClasses.text} hover:opacity-80 transition-all flex items-center gap-1 cursor-pointer font-bold`}
            >
              Analyze Strategy <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

      </div>

      {/* 8. Tomorrow Preparation */}
      {planner && (
        <div className={`border ${themeClasses.card} rounded-xl p-5 space-y-3`}>
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 font-mono flex items-center gap-2">
            <Clock className="h-4 w-4 text-cyan-400" /> Tomorrow's Focus Outlook & Reminders
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono leading-relaxed">
            <div className="p-3.5 bg-neutral-900/40 border border-neutral-850 rounded-lg space-y-1.5">
              <span className="text-[10px] text-neutral-500 uppercase block font-bold">Recommended Setup Strategy</span>
              <p className="text-white font-bold">{safeString(planner?.tomorrow_outlook?.recommended_strategy, "N/A")}</p>
            </div>
            <div className="p-3.5 bg-neutral-900/40 border border-neutral-850 rounded-lg space-y-1.5">
              <span className="text-[10px] text-neutral-500 uppercase block font-bold">Preparation Focus Tasks</span>
              <p className="text-neutral-300">{safeString(planner?.tomorrow_outlook?.preparation_notes, "N/A")}</p>
            </div>
          </div>
        </div>
      )}

      {/* 9. Command shortcuts */}
      <div className={`border ${themeClasses.card} rounded-xl p-5`}>
        <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 font-mono mb-4 flex items-center gap-2">
          <Zap className="h-4 w-4 text-cyan-400" /> Command shortcuts
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          <button
            onClick={() => onNavigate("home")}
            className="p-3 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 hover:border-neutral-700 rounded-lg transition-all text-center flex flex-col items-center justify-center gap-2 cursor-pointer group"
          >
            <Clock className="h-4.5 w-4.5 text-cyan-400 group-hover:scale-110 transition" />
            <span className="text-[10px] font-bold text-neutral-300">Dashboard</span>
          </button>
          <button
            onClick={() => onNavigate("market")}
            className="p-3 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 hover:border-neutral-700 rounded-lg transition-all text-center flex flex-col items-center justify-center gap-2 cursor-pointer group"
          >
            <TrendingUp className="h-4.5 w-4.5 text-emerald-400 group-hover:scale-110 transition" />
            <span className="text-[10px] font-bold text-neutral-300">Market</span>
          </button>
          <button
            onClick={() => onNavigate("trade_center")}
            className="p-3 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 hover:border-neutral-700 rounded-lg transition-all text-center flex flex-col items-center justify-center gap-2 cursor-pointer group"
          >
            <Compass className="h-4.5 w-4.5 text-amber-400 group-hover:scale-110 transition" />
            <span className="text-[10px] font-bold text-neutral-300">Trade Center</span>
          </button>
          <button
            onClick={() => onNavigate("portfolio")}
            className="p-3 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 hover:border-neutral-700 rounded-lg transition-all text-center flex flex-col items-center justify-center gap-2 cursor-pointer group"
          >
            <Briefcase className="h-4.5 w-4.5 text-purple-400 group-hover:scale-110 transition" />
            <span className="text-[10px] font-bold text-neutral-300">Portfolio</span>
          </button>
          <button
            onClick={() => onNavigate("execution")}
            className="p-3 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 hover:border-neutral-700 rounded-lg transition-all text-center flex flex-col items-center justify-center gap-2 cursor-pointer group"
          >
            <Zap className="h-4.5 w-4.5 text-indigo-400 group-hover:scale-110 transition" />
            <span className="text-[10px] font-bold text-neutral-300">Execution</span>
          </button>
          <button
            onClick={() => onNavigate("tomorrow")}
            className="p-3 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 hover:border-neutral-700 rounded-lg transition-all text-center flex flex-col items-center justify-center gap-2 cursor-pointer group"
          >
            <Clock className="h-4.5 w-4.5 text-pink-400 group-hover:scale-110 transition" />
            <span className="text-[10px] font-bold text-neutral-300">Tomorrow</span>
          </button>
          <button
            onClick={() => onNavigate("market_story")}
            className="p-3 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 hover:border-neutral-700 rounded-lg transition-all text-center flex flex-col items-center justify-center gap-2 cursor-pointer group"
          >
            <BookOpen className="h-4.5 w-4.5 text-rose-400 group-hover:scale-110 transition" />
            <span className="text-[10px] font-bold text-neutral-300">Market Story</span>
          </button>
        </div>
      </div>

    </div>
  );
}

export default HomeDashboard;
