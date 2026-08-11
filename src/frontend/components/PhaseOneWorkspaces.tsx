import React, { useState } from "react";
import { AlertTriangle, CheckCircle2, Clock, Database, KeyRound, ShieldCheck } from "lucide-react";
import { formatDate, formatDateTimeIST, formatNumber, safeArray, safeNumber, safeString } from "../utils/safeHelpers";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { connectBroker } from "../services/broker";
import { ExecutiveSummary } from "./ExecutiveSummary";
import { MarketOverview } from "./MarketOverview";
import { MarketScoring } from "./MarketScoring";
import { TomorrowWorkspace } from "./TomorrowWorkspace";
import { MarketStory } from "./MarketStory";
import { NewsIntelligence } from "./NewsIntelligence";
import { IntradayAssistant } from "./IntradayAssistant";
import { NiftyLiveWorkspace as NiftyLiveView } from "./NiftyLiveWorkspace";
import { SettingsDashboard } from "./SettingsDashboard";
import { ErrorBoundary } from "./ErrorBoundary";
import { TodaysAnalysisSynthesis } from "./UnifiedIntelligencePanel";

export type ReadinessKind = "initializing" | "unavailable" | "stale" | "blocked" | "closed" | "expired" | "partial" | "error";

export function ReadinessState({ kind, title, reason }: { kind: ReadinessKind; title: string; reason: string }) {
  const colors = kind === "expired" || kind === "error" ? "border-rose-900/60 bg-rose-950/20 text-rose-300" : kind === "stale" || kind === "partial" ? "border-amber-900/60 bg-amber-950/20 text-amber-300" : "border-slate-800 bg-slate-950/60 text-slate-300";
  return <div data-readiness={kind} className={`rounded-xl border p-6 text-left ${colors}`}>
    <div className="flex items-center gap-2 font-bold"><AlertTriangle size={16} />{title}</div>
    <p className="mt-2 text-xs text-slate-400">{reason}</p>
  </div>;
}

function Tabs({ values, active, onChange }: { values: string[]; active: string; onChange: (value: string) => void }) {
  return <div className="flex flex-wrap gap-2 border-b border-neutral-800 pb-3">{values.map(value => <button key={value} onClick={() => onChange(value)} className={`rounded-lg border px-3 py-1.5 text-xs font-bold ${active === value ? "border-cyan-700 bg-cyan-950/30 text-cyan-300" : "border-neutral-800 bg-neutral-900 text-neutral-400"}`}>{value}</button>)}</div>;
}

function Heading({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <div className="text-left"><div className="text-[10px] font-black uppercase tracking-[0.22em] text-cyan-400">{eyebrow}</div><h2 className="mt-1 text-xl font-bold text-white">{title}</h2><p className="mt-1 text-xs text-neutral-500">{description}</p></div>;
}

function ClosedSessionIntelligence({ mode }: { mode: "analysis" | "assistant" }) {
  const { canonicalState } = useWorkstationState();
  const market: any = canonicalState?.market_data || {};
  const macro: any = canonicalState?.macro_intelligence || {};
  const news: any[] = safeArray(canonicalState?.news_intelligence?.items) as any[];
  const clusters: any[] = safeArray(canonicalState?.news_intelligence?.event_clusters) as any[];
  const candles: any[] = safeArray(market.candles) as any[];
  const highs = candles.map(c => Number(c.h)).filter(Number.isFinite);
  const lows = candles.map(c => Number(c.l)).filter(Number.isFinite);
  const observed = canonicalState?.data_quality?.market_data?.observed_at;
  const temporal: any = canonicalState?.news_intelligence?.workspace_temporal || {};
  const sinceCloseIds = new Set(safeArray(temporal.since_close_item_ids).map(String));
  const previousSessionIds = new Set(safeArray(temporal.previous_session_context_item_ids).map(String));
  const sinceCloseClusterIds = new Set(safeArray(temporal.since_close_cluster_ids).map(String));
  const sinceClose = news.filter(item => sinceCloseIds.has(String(item.id)));
  const previousSession = news.filter(item => previousSessionIds.has(String(item.id)));
  const clustersSinceClose = clusters.filter(cluster => sinceCloseClusterIds.has(String(cluster.event_cluster_id))).slice(0, 6);
  const macroWorkspace: any = macro.workspace_context || {};
  const selectedQuoteKeys: string[] = mode === "assistant"
    ? safeArray(macroWorkspace.live_assistant_quote_keys).map(String)
    : safeArray(macroWorkspace.todays_analysis_quote_keys).map(String);
  const quotes = selectedQuoteKeys.map(key => macro.quotes?.[key]).filter(Boolean) as any[];
  const economicEvents = safeArray(macro.economic_events) as any[];
  const releasedEconomic = economicEvents.filter(event => safeString(event.status) === "RELEASED").sort((a, b) => new Date(b.scheduled_at).getTime() - new Date(a.scheduled_at).getTime());
  const nextEconomic = economicEvents.filter(event => ["SCHEDULED", "UPCOMING", "DUE"].includes(safeString(event.status)) && ["HIGH", "CRITICAL"].includes(safeString(event.impact_level).toUpperCase()) && new Date(event.scheduled_at).getTime() >= Date.now()).sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())[0];
  const summary = market.current_spot && highs.length && lows.length ? `NIFTY closed at ${formatNumber(market.current_spot, 2)}. Session high ${formatNumber(Math.max(...highs), 2)}, low ${formatNumber(Math.min(...lows), 2)}. Observed ${formatDate(observed)} via Kite Historical API.` : "No verified last-session price summary is available.";
  const fiiIndexFutures: any = macro.institutional_derivatives?.positioning?.FII_INDEX_FUTURES;
  const vix: any = macro.india_vix || {};
  const optionIv: any = canonicalState?.option_intelligence || {};
  const specializedContext = [
    fiiIndexFutures ? `FII index futures ${safeString(fiiIndexFutures.positioning)} (${Number(fiiIndexFutures.net_position) >= 0 ? "+" : ""}${formatNumber(fiiIndexFutures.net_position, 0)} contracts)` : "FII index futures unavailable",
    vix.value != null && vix.observation_timestamp ? `India VIX ${formatNumber(vix.value, 2)} (${safeString(vix.regime)}; ${safeString(vix.freshness)})` : "India VIX unavailable",
    safeString(optionIv.iv_status).toUpperCase() === "AVAILABLE" ? `ATM option IV ${formatNumber(optionIv.atm_iv, 2)}% from ${safeNumber(optionIv.iv_rows, 0)} converged rows` : "Option IV unavailable",
  ].join(" · ");
  const cards = mode === "analysis" ? [
    ["Last Session Summary", summary],
    ["Trend / Structure", market.market_regime && market.market_regime !== "UNKNOWN" ? `${safeString(market.market_regime)} · ${safeString(market.trend_direction)} · VWAP ${market.vwap > 0 ? formatNumber(market.vwap, 2) : "unavailable"} · ATR ${market.atr > 0 ? formatNumber(market.atr, 2) : "unavailable"}` : "Insufficient validated candles for structural classification."],
    ["Major Verified Developments", news.length ? news.slice(0, 3).map(n => safeString(n.headline)).join(" · ") : "No verified news developments available."],
    ["Macro Context", quotes.length ? `${quotes.length} freshness-eligible cross-market observations. ${quotes.slice(0, 4).map(q => `${safeString(q.name || q.symbol)} ${formatNumber(q.change_pct, 2)}% (${safeString(q.freshness_status)})`).join(" · ")}` : "No freshness-eligible macro context available."],
    ["Institutional & Volatility Context", `${specializedContext}. Context only; these observations do not establish causality.`],
    ["Morning Expectations", "No canonical morning-plan snapshot is available for confirmation/invalidation comparison."],
    ["End-of-Day State", `${safeString(market.trend_direction || "UNKNOWN")} · ${safeString(market.volatility_state || "UNKNOWN")} · MARKET_CLOSED`],
  ] : [
    ["Last Session Summary", summary],
    ["Developments Since Close", sinceClose.length ? `${sinceClose.length} verified developments since the last Kite observation.` : "No verified updates available."],
    ["News Since Close", sinceClose.length ? sinceClose.slice(0, 4).map(n => safeString(n.headline)).join(" · ") : "No verified updates available."],
    ["Cross-Market Context Since Close", quotes.length ? quotes.slice(0, 6).map(q => `${safeString(q.name || q.symbol)} ${Number(q.change_pct) >= 0 ? "+" : ""}${formatNumber(q.change_pct, 2)}% vs source previous close (${safeString(q.freshness_status)})`).join(" · ") : "No global-market observation newer than the last Indian market observation is available."],
    ["What Matters: Positioning & Volatility", `${specializedContext}. Watch whether volatility and price movement confirm one another; no execution action is generated.`],
    ["Next Session Watch Items", news.length || quotes.length ? "Review verified news, global cues, and the opening gap before enabling intraday confirmation logic." : "No verified updates available."],
  ];
  const clusterCards = mode === "analysis" ? [
    ["Last Session Summary", summary],
    ["Trend / Structure", market.market_regime && market.market_regime !== "UNKNOWN" ? `${safeString(market.market_regime)} · ${safeString(market.trend_direction)} · VWAP ${market.vwap > 0 ? formatNumber(market.vwap, 2) : "unavailable"} · ATR ${market.atr > 0 ? formatNumber(market.atr, 2) : "unavailable"}` : "Insufficient validated candles for structural classification."],
    ["Major Verified Developments", clustersSinceClose.length ? clustersSinceClose.slice(0, 3).map(cluster => safeString(cluster.canonical_headline)).join(" · ") : "No verified current or post-close news developments are available."],
    ["Macro Context", quotes.length ? `${quotes.length} freshness-eligible cross-market observations. ${quotes.slice(0, 4).map(q => `${safeString(q.name || q.symbol)} ${formatNumber(q.change_pct, 2)}% (${safeString(q.freshness_status)})`).join(" · ")}` : "No freshness-eligible macro context available."],
    ["Institutional & Volatility Context", `${specializedContext}. Context only; these observations do not establish causality.`],
    ["Previous-Session Context", previousSession.length ? previousSession.slice(0, 3).map(item => safeString(item.headline)).join(" · ") : "No freshness-eligible previous-session context is available."],
    ["End-of-Day State", `${safeString(market.trend_direction || "UNKNOWN")} · ${safeString(market.volatility_state || "UNKNOWN")} · MARKET_CLOSED`],
  ] : [
    ["Last Session Summary", summary],
    ["Developments Since Close", clustersSinceClose.length ? `${clustersSinceClose.length} distinct NIFTY-relevant event clusters since the last Kite observation.` : "No verified event clusters since close."],
    ["What Changed", clustersSinceClose.length ? clustersSinceClose.slice(0, 4).map(cluster => safeString(cluster.canonical_headline)).join(" · ") : "No verified event-cluster changes available."],
    ["Cross-Market Context Since Close", quotes.length ? quotes.slice(0, 6).map(q => `${safeString(q.name || q.symbol)} ${Number(q.change_pct) >= 0 ? "+" : ""}${formatNumber(q.change_pct, 2)}% vs source previous close (${safeString(q.freshness_status)})`).join(" · ") : "No global-market observation newer than the last Indian market observation is available."],
    ["What Matters: Positioning & Volatility", `${specializedContext}. Watch whether volatility and price movement confirm one another; no execution action is generated.`],
    ["What Matters / What To Watch", nextEconomic ? `${safeString(nextEconomic.event_name)} scheduled ${formatDateTimeIST(nextEconomic.scheduled_at_ist || nextEconomic.scheduled_at)}. ${safeString(nextEconomic.reasoning)}` : clustersSinceClose.length ? clustersSinceClose.slice(0, 3).map(cluster => `${safeString(cluster.reasoning)} Monitor ${safeArray(cluster.affected_channels).join(", ") || "the stated transmission channel"}.`).join(" · ") : "No verified cluster-based or scheduled-event watch item is available."],
  ];
  return <div className="grid gap-4 md:grid-cols-2">{clusterCards.map(([title, body]) => <section key={title} className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 text-left"><h3 className="text-xs font-bold uppercase text-cyan-300">{title}</h3><p className="mt-2 text-xs leading-relaxed text-slate-300">{body}</p></section>)}</div>;
}

export function NiftyLiveWorkspace() {
  const [tab, setTab] = useState("Overview");
  const { marketContext, optionContext, loading } = useWorkstationState();
  const marketAvailable = Boolean(marketContext?.current_spot && marketContext?.last_tick_time);
  return <ErrorBoundary fallbackTitle="NIFTY Live Workspace Error">
    <div className="space-y-5"><Heading eyebrow="Live market" title="NIFTY Live" description="Live NIFTY market intelligence. No fallback price is shown." /><Tabs values={["Overview", "Price & Trend", "Options"]} active={tab} onChange={setTab} />
      {loading && !marketAvailable ? <ReadinessState kind="initializing" title="Initializing market data" reason="Waiting for market observations." /> : !marketAvailable ? <ReadinessState kind="unavailable" title="Live market data unavailable" reason="Connect broker or wait for a valid market snapshot." /> : <NiftyLiveView view={tab === "Price & Trend" ? "price-trend" : tab === "Options" ? "options" : "overview"} />}
    </div>
  </ErrorBoundary>;
}



export function TodaysAnalysisWorkspace() {
  const { marketContext, canonicalState } = useWorkstationState();
  const closed = Boolean(canonicalState?.market_session?.is_closed || canonicalState?.market_session?.status === "CLOSED");
  return (
    <div className="space-y-5">
      <TodaysAnalysisSynthesis />
      {closed ? (
        <MarketStory />
      ) : (marketContext?.current_spot && marketContext.feed_health === "HEALTHY") ? (
        <MarketStory />
      ) : (
        <ReadinessState kind="blocked" title="Today’s Analysis is waiting" reason="A healthy current-session market feed is required." />
      )}
    </div>
  );
}

export function NewsUpdatesWorkspace() {
  return (
    <div className="space-y-5">
      <NewsIntelligence />
    </div>
  );
}

export function LiveAssistantWorkspace() {
  return (
    <div className="space-y-5">
      <IntradayAssistant />
    </div>
  );
}

export function SettingsWorkspace() {
  return (
    <div className="space-y-5">
      <SettingsDashboard />
    </div>
  );
}

export { MarketPulseWorkspace } from "./MarketPulseWorkspace";
export { PreMarketPlannerWorkspace } from "./PreMarketPlannerWorkspace";
