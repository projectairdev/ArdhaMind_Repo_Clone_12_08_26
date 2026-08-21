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
import { SettingsWorkspace as SettingsWorkspaceNew } from "./settings/SettingsWorkspace";
import { ErrorBoundary } from "./ErrorBoundary";
import { TodaysAnalysisSynthesis } from "./UnifiedIntelligencePanel";
import { DataDetailsDrawer } from "./intelligence/CanonicalPresentation";

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
  const { marketContext, canonicalState, lastValidState, loading } = useWorkstationState() as any;
  const sessionStatus = canonicalState?.market_session?.status || "CLOSED";
  const isClosedSession = Boolean(
    canonicalState?.market_session?.is_closed ||
    sessionStatus === "CLOSED" ||
    sessionStatus === "HOLIDAY" ||
    sessionStatus === "WEEKEND" ||
    marketContext?.session_mode === "LAST_SESSION" ||
    marketContext?.session_mode === "LAST_VALID_SESSION"
  );

  const spot = marketContext?.current_spot || canonicalState?.market_data?.current_spot || lastValidState?.market_data?.current_spot;
  const lastTickTime = marketContext?.last_tick_time || canonicalState?.data_quality?.market_data?.observed_at;

  const marketAvailable = isClosedSession
    ? Boolean(spot)
    : Boolean(spot && lastTickTime);

  return <ErrorBoundary fallbackTitle="Market Command Workspace Error">
    <div className="space-y-5">
      <Heading eyebrow="Live market" title="Market Command" description="Live NIFTY market intelligence. No fallback price is shown." />
      {loading && !spot ? (
        <ReadinessState kind="initializing" title="Initializing market data" reason="Waiting for market observations." />
      ) : !marketAvailable ? (
        <ReadinessState kind="unavailable" title="Live market data unavailable" reason="Connect broker or wait for a valid market snapshot." />
      ) : (
        <NiftyLiveView />
      )}
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
        <ReadinessState kind="blocked" title="Session Intelligence is waiting" reason="A healthy current-session market feed is required." />
      )}
    </div>
  );
}

import { NewsWorkspace } from "./news/NewsWorkspace";

export function NewsUpdatesWorkspace() {
  return (
    <div className="space-y-5">
      <NewsWorkspace />
    </div>
  );
}

import { MarketIntelligenceWorkspace } from "./MarketIntelligenceWorkspace";

export function LiveAssistantWorkspace() {
  return (
    <div className="space-y-5">
      <MarketIntelligenceWorkspace />
    </div>
  );
}

export function SettingsWorkspace(props: any) {
  return <SettingsWorkspaceNew {...props} />;
}

export function ForwardOutlookWorkspace() {
  const { canonicalState, lastValidState } = useWorkstationState();
  const state = canonicalState ?? lastValidState;
  const outlook = state?.forward_outlook || state?.unified_intelligence?.forward_outlook || state?.outlook?.forward_outlook || {};
  const todayReport = state?.todays_analysis || state?.session_story?.todays_analysis || {};

  const primary = outlook.primary_scenario || {};
  const alternates = safeArray(outlook.alternate_scenarios);
  const whatChanged = outlook.what_changed || {};
  const dataQuality = outlook.data_quality || {};

  const confidence = safeString(outlook.overall_confidence || "MODERATE").toUpperCase();
  const confStyle = confidence === "HIGH"
    ? "bg-emerald-950/80 border-emerald-700 text-emerald-300"
    : confidence === "LOW"
    ? "bg-amber-950/80 border-amber-700 text-amber-300"
    : "bg-cyan-950/80 border-cyan-700 text-cyan-300";

  const sessionStatus = safeString(state?.market_session?.status || "CLOSED").toUpperCase();
  const isClosed = Boolean(state?.market_session?.is_closed || ["CLOSED", "HOLIDAY", "POST_CLOSE"].includes(sessionStatus));

  return (
    <ErrorBoundary fallbackTitle="Scenario Outlook Workspace Error">
      <div id="forward-outlook-workspace" className="space-y-6 text-left font-sans">

        {/* ── 1. HEADER BANNER ── */}
        <header className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-900 pb-3">
            <div>
              <div className="flex items-center gap-2 text-[10px] font-bold text-cyan-400 uppercase tracking-widest">
                <Clock size={16} />
                <span>SCENARIO OUTLOOK · HORIZON: NEXT 15–30 MINUTES</span>
                <span className={`px-2 py-0.5 rounded text-[9px] border font-bold ${
                  isClosed ? "bg-slate-900 border-slate-700 text-slate-400" : "bg-emerald-950/80 border-emerald-700 text-emerald-300"
                }`}>
                  {isClosed ? "SESSION COMPLETE" : "● LIVE OUTLOOK"}
                </span>
              </div>
              <h2 className="text-xl font-black text-white mt-1 uppercase tracking-tight">SCENARIO OUTLOOK — NEAR-TERM DETERMINISTIC SCENARIOS</h2>
            </div>
            <div className="text-right text-[10px] font-mono">
              <span className="text-slate-400 block uppercase">OUTLOOK CONFIDENCE</span>
              <span className={`px-2.5 py-1 rounded text-xs font-bold border inline-block mt-0.5 ${confStyle}`}>
                {confidence} CONFIDENCE
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-sans">
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-850">
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Current Session Trend (Today's Analysis)</span>
              <span className="font-bold text-white mt-0.5 block">{safeString(todayReport.trend_classification || "INSUFFICIENT_DATA")}</span>
            </div>
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-850">
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Scenario Separation / Spread</span>
              <span className="font-bold text-cyan-300 mt-0.5 block">
                {outlook.scenario_spread != null ? `${safeNumber(outlook.scenario_spread, 0.0).toFixed(1)} score pts` : "UNAVAILABLE"} ({confidence === "LOW" ? "Mixed / Low Separation" : "Clear Primary Lead"})
              </span>
            </div>
          </div>
        </header>

        {/* ── 2. PRIMARY SCENARIO HERO CARD ── */}
        <div className="p-6 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono relative overflow-hidden">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-slate-850 pb-3 gap-2">
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-1 bg-cyan-950 border border-cyan-800 text-cyan-300 rounded text-xs font-bold uppercase tracking-wider">
                PRIMARY SCENARIO
              </span>
              <span className="text-lg font-black text-white">{safeString(primary.headline || (outlook.analysis_status === "INSUFFICIENT_DATA" ? "INSUFFICIENT MARKET DATA — OUTLOOK UNAVAILABLE" : "RANGE CONTINUATION & CONSOLIDATION"))}</span>
            </div>
            <span className="text-xs text-slate-400">Score: <strong className="text-cyan-300">{primary.scenario_score != null ? safeNumber(primary.scenario_score, 0.0).toFixed(1) : "0.0"}</strong> / 100</span>
          </div>

          <p className="text-sm text-slate-300 font-sans leading-relaxed">
            {safeString(primary.description || "Authoritative spot price telemetry is currently unavailable.")}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-sans text-xs pt-2">

            {/* Supporting Evidence */}
            <div className="p-4 bg-slate-900/60 rounded-lg border border-slate-850 space-y-2">
              <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider block">SUPPORTING EVIDENCE</span>
              <ul className="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                {safeArray(primary.supporting_evidence).map((ev: string, i: number) => (
                  <li key={i}>{ev}</li>
                ))}
              </ul>
            </div>

            {/* Invalidation Conditions */}
            <div className="p-4 bg-rose-950/20 rounded-lg border border-rose-900/40 space-y-2">
              <span className="text-[10px] font-mono font-bold text-rose-400 uppercase tracking-wider block">WHAT WOULD PROVE THIS WRONG? (INVALIDATION)</span>
              <ul className="list-disc list-inside space-y-1 text-rose-200 text-[11px]">
                {safeArray(primary.invalidation_conditions).map((inv: string, i: number) => (
                  <li key={i}>{inv}</li>
                ))}
              </ul>
            </div>

          </div>

          {/* Relevant Levels Bar */}
          <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-850 flex flex-wrap justify-between items-center text-xs font-mono gap-3">
            <div>Support: <strong className="text-emerald-400">{primary.relevant_levels?.support != null ? formatNumber(primary.relevant_levels.support, 0) : "UNAVAILABLE"}</strong></div>
            <div>VWAP Anchor: <strong className="text-cyan-300">{primary.relevant_levels?.vwap != null ? formatNumber(primary.relevant_levels.vwap, 2) : "UNAVAILABLE"}</strong></div>
            <div>Resistance: <strong className="text-rose-400">{primary.relevant_levels?.resistance != null ? formatNumber(primary.relevant_levels.resistance, 0) : "UNAVAILABLE"}</strong></div>
          </div>
        </div>

        {/* ── 3. ALTERNATE SCENARIOS ── */}
        <div className="space-y-3 font-mono">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">ALTERNATE PLAUSIBLE SCENARIOS</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-sans">
            {alternates.map((alt: any, idx: number) => (
              <div key={alt.scenario_id || alt.scenario_type || idx} className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 hover:border-slate-700 transition font-mono">
                <div className="flex justify-between items-center border-b border-slate-850 pb-2">
                  <span className="font-bold text-slate-200 text-xs uppercase">{alt.scenario_type || "ALTERNATE SCENARIO"}</span>
                  <span className="text-[10px] text-slate-400 font-bold">Score: {safeNumber(alt.scenario_score, 45.0).toFixed(1)}</span>
                </div>
                <h4 className="text-xs font-bold text-cyan-200 font-sans">{alt.headline}</h4>
                <p className="text-[11px] text-slate-400 font-sans leading-relaxed">{alt.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── 4. WHAT CHANGED IN THE OUTLOOK? ── */}
        {whatChanged.status && (
          <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 font-mono text-xs">
            <span className="font-bold text-cyan-400 uppercase text-[10px] block">WHAT CHANGED IN THE OUTLOOK?</span>
            <p className="text-slate-300 font-sans leading-relaxed text-[11px]">
              {safeString(whatChanged.summary || "Outlook remains stable relative to prior evaluation.")}
            </p>
          </div>
        )}

        {/* ── 5. EVIDENCE & DETAILS DRAWER ── */}
        <DataDetailsDrawer
          title="Forward Outlook — Deterministic Scoring, Methodology Version & Outcome Validation Stub"
        >
          <pre className="p-3 bg-slate-900 border border-slate-800 rounded text-[10px] font-mono text-slate-300 overflow-x-auto">
            {JSON.stringify({
              methodology_version: outlook.methodology_version || "v1.2-d3.5f",
              outlook_id: outlook.outlook_id,
              scenario_spread: outlook.scenario_spread,
              outcome_validation_stub: outlook.outcome_validation_stub,
              data_quality: dataQuality
            }, null, 2)}
          </pre>
        </DataDetailsDrawer>

      </div>
    </ErrorBoundary>
  );
}

export { MarketPulseWorkspace } from "./MarketPulseWorkspace";
export { PreMarketPlannerWorkspace } from "./PreMarketPlannerWorkspace";
