import React, { useState } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { formatDate, formatDateTimeIST, formatNumber, safeArray, safeString } from "../utils/safeHelpers";
import { GlobalCuesWidget, InstitutionalFlowWidget } from "./MacroIntelligence";
import { ParticipantPositioningWidget, VolatilityContextWidget } from "./SpecializedIntelligence";
import { UnifiedIntelligencePanel } from "./UnifiedIntelligencePanel";

function TabButton({ value, active, onClick }: { key?: string; value: string; active: boolean; onClick: () => void }) {
  return <button onClick={onClick} className={`rounded-lg border px-3 py-1.5 text-xs font-bold ${active ? "border-cyan-700 bg-cyan-950/30 text-cyan-300" : "border-neutral-800 bg-neutral-900 text-neutral-400"}`}>{value}</button>;
}

function Card({ title, children, tone = "default" }: { key?: string; title: string; children: React.ReactNode; tone?: "default" | "warning" | "danger" }) {
  const color = tone === "danger" ? "border-rose-900/50 bg-rose-950/20" : tone === "warning" ? "border-amber-900/50 bg-amber-950/20" : "border-slate-800 bg-slate-950/60";
  return <section className={`rounded-xl border p-5 text-left ${color}`}><h3 className="text-xs font-bold uppercase text-cyan-300">{title}</h3><div className="mt-2 text-xs leading-relaxed text-slate-300">{children}</div></section>;
}

export function PreMarketPlannerWorkspace() {
  const [tab, setTab] = useState("Evening Outlook");
  const { canonicalState } = useWorkstationState() as any;
  const market = canonicalState?.market_data || {};
  const macro = canonicalState?.macro_intelligence || {};
  const news = safeArray(canonicalState?.news_intelligence?.items) as any[];
  const clusters = safeArray(canonicalState?.news_intelligence?.event_clusters) as any[];
  const quotes = macro.quotes || {};
  const macroWorkspace = macro.workspace_context || {};
  const sinceCloseQuoteKeys = new Set(safeArray(macroWorkspace.since_india_close_quote_keys).map(String));
  const sinceCloseQuotes = Object.entries(quotes).filter(([key]) => sinceCloseQuoteKeys.has(key)).map(([, quote]) => quote as any);
  const flows = safeArray(macro.institutional_flows) as any[];
  const events = safeArray(macro.economic_events) as any[];
  const istDay = (value: string | Date) => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(value));
  const todayEvents = events.filter(event => istDay(event.scheduled_at_ist || event.scheduled_at) === istDay(new Date()));
  const highImpactToday = todayEvents.filter(event => ["HIGH", "CRITICAL"].includes(safeString(event.impact_level).toUpperCase()));
  const nextHigh = events.filter(event => ["HIGH", "CRITICAL"].includes(safeString(event.impact_level).toUpperCase()) && new Date(event.scheduled_at).getTime() >= Date.now()).sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())[0];
  const corporate = (safeArray(macro.official_india_events) as any[]).filter(event => ["CORPORATE_ANNOUNCEMENT", "EARNINGS", "CORPORATE_ACTION", "BOARD_MEETING"].includes(safeString(event.event_category).toUpperCase()));
  const candles = safeArray(market.candles) as any[];
  const high = candles.length ? Math.max(...candles.map(c => Number(c.h))) : null;
  const low = candles.length ? Math.min(...candles.map(c => Number(c.l))) : null;
  const readiness = canonicalState?.workspace_readiness?.pre_market_850_readiness || {};
  const readinessMeta = new Set(["is_full_premarket_ready", "overall_state", "ready_inputs", "unavailable_inputs", "blocked_inputs"]);
  const missing = Object.entries(readiness).filter(([key, value]) => !readinessMeta.has(key) && value !== "READY").map(([key]) => key.replaceAll("_", " "));
  const openingGap = macro.opening_gap || {};
  const optionReady = safeString(canonicalState?.option_intelligence?.status).toLowerCase() === "ready";
  const marketReady = Boolean(market.current_spot && canonicalState?.data_quality?.market_data?.quality_status === "valid");
  const operationalState = marketReady && optionReady && news.length > 0 && Object.keys(quotes).length >= 10 && flows.length > 0 && events.length > 0 ? "Ready" : marketReady || news.length > 0 || Object.keys(quotes).length > 0 ? "Partial" : "Not Ready";
  const temporal = canonicalState?.news_intelligence?.workspace_temporal || {};
  const sinceCloseIds = new Set(safeArray(temporal.since_close_item_ids).map(String));
  const sinceCloseClusterIds = new Set(safeArray(temporal.since_close_cluster_ids).map(String));
  const sinceClose = news.filter(item => sinceCloseIds.has(String(item.id)));
  const overnightClusters = clusters.filter(cluster =>
    sinceCloseClusterIds.has(String(cluster.event_cluster_id)) &&
    (["HIGH", "CRITICAL"].includes(safeString(cluster.impact_level).toUpperCase()) || Number(cluster.nifty_relevance) >= 6)
  ).slice(0, 6);

  return <div className="space-y-5">
    <div className="text-left"><div className="text-[10px] font-black uppercase tracking-[0.22em] text-cyan-400">Next-session intelligence</div><h2 className="mt-1 text-xl font-bold text-white">Pre-Market Planner</h2><p className="mt-1 text-xs text-neutral-500">Three purpose-specific preparation views backed by canonical inputs.</p></div>
    <UnifiedIntelligencePanel workspace="PRE_MARKET" />
    <div className="flex flex-wrap gap-2 border-b border-neutral-800 pb-3">{["Evening Outlook", "8:50 AM Briefing", "Opening Checklist"].map(value => <TabButton key={value} value={value} active={tab === value} onClick={() => setTab(value)}/>)}</div>

    {tab === "Evening Outlook" && <div data-premarket-panel="evening" className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2"><Card title="Last Session Summary">NIFTY closed at {market.current_spot ? formatNumber(market.current_spot, 2) : "UNAVAILABLE"}. High {high != null ? formatNumber(high, 2) : "UNAVAILABLE"}, low {low != null ? formatNumber(low, 2) : "UNAVAILABLE"}; source Kite Historical API.</Card><Card title="Post-Close / Global Developments">{sinceClose.length ? `${sinceClose.length} verified developments since the last market observation.` : "No verified post-close developments are available."}</Card></div>
      <div className="grid gap-4 md:grid-cols-2"><Card title="Overseas Observations Since India Close">{sinceCloseQuotes.length ? sinceCloseQuotes.slice(0, 6).map(q => `${safeString(q.name)} ${Number(q.change_pct) >= 0 ? "+" : ""}${formatNumber(q.change_pct, 2)}% vs source previous close (${safeString(q.freshness_status)})`).join(" · ") : "No global-market observations newer than the last Indian market observation are available."}</Card><Card title="Latest News Since Close">{sinceClose.length ? sinceClose.slice(0, 5).map(item => safeString(item.headline)).join(" · ") : "No verified news since close."}</Card></div>
      <div className="grid gap-4 md:grid-cols-2"><Card title="Overnight Risk Watch">{sinceClose.filter(item => ["Geopolitics", "Crude", "Currency/Yields", "Global Markets"].includes(safeString(item.category))).slice(0, 4).map(item => safeString(item.headline)).join(" · ") || "No verified overnight risk story is available."}</Card><Card title="Next-Session Unknowns & Readiness Gaps" tone="warning">{missing.length ? missing.join(", ") : "No canonical readiness gaps reported."} · Opening gap remains unknown until a genuine pre-open observation exists.</Card></div>
      <Card title="Overnight Risk Intelligence">{overnightClusters.length ? <div className="space-y-3">{overnightClusters.map(cluster => <div key={cluster.event_cluster_id} data-overnight-cluster={cluster.event_cluster_id} className="border-b border-slate-800 pb-2 last:border-0"><div className="font-semibold text-white">{safeString(cluster.canonical_headline)}</div><div className="mt-1 font-mono text-[10px] text-slate-400">{formatDate(cluster.last_updated)} · {safeString(cluster.verification_strength)} · NIFTY {formatNumber(cluster.nifty_relevance, 1)}/10 · {safeString(cluster.impact_level)} · {safeString(cluster.expected_direction)}</div><div className="mt-1 text-cyan-200">Channels: {safeArray(cluster.affected_channels).join(", ") || "UNAVAILABLE"}</div></div>)}</div> : "No meaningful verified event cluster has updated since the previous Indian market close."}</Card>
    </div>}

    {tab === "8:50 AM Briefing" && <div data-premarket-panel="briefing-850" className="space-y-4">
      <GlobalCuesWidget/>
      <div className="grid gap-4 md:grid-cols-3">
        <div data-briefing-category="cash-flow"><InstitutionalFlowWidget/></div>
        <div data-briefing-category="derivative-positioning"><ParticipantPositioningWidget compact/></div>
        <div data-briefing-category="volatility"><VolatilityContextWidget/></div>
      </div>
      <Card title="Overnight News">{sinceClose.length ? sinceClose.slice(0, 5).map(item => safeString(item.headline)).join(" · ") : "No verified overnight news available."}</Card>
      <Card title="Today's High-Impact Events">{highImpactToday.length ? <div className="space-y-3">{highImpactToday.map(event => <div key={event.event_id} data-premarket-economic-event={event.event_id} className="border-b border-slate-800 pb-2 last:border-0"><div className="font-bold text-white">{formatDateTimeIST(event.scheduled_at_ist || event.scheduled_at)} · {safeString(event.country)} · {safeString(event.event_name)}</div><div className="mt-1 font-mono text-[10px]">{safeString(event.impact_level)} · Forecast: {event.forecast ?? "UNAVAILABLE"}{event.forecast != null ? safeString(event.unit) : ""} · Previous: {event.previous ?? "UNAVAILABLE"}{event.previous != null ? safeString(event.unit) : ""} · NIFTY {formatNumber(event.nifty_relevance, 1)}/10</div><div className="mt-1 text-cyan-200">Channels: {safeArray(event.affected_channels).join(", ") || "UNAVAILABLE"}</div></div>)}</div> : "No HIGH/CRITICAL canonical economic event is scheduled today."}</Card>
      <div className="grid gap-4 md:grid-cols-2"><Card title="Next High-Impact Event">{nextHigh ? `${safeString(nextHigh.country)} · ${safeString(nextHigh.event_name)} · ${formatDateTimeIST(nextHigh.scheduled_at_ist || nextHigh.scheduled_at)}` : "NONE"}</Card><Card title="Official Corporate Events">{corporate.length ? corporate.slice(0, 5).map(event => `${safeString(event.symbol)} · ${safeString(event.event_category)}`).join(" · ") : "UNAVAILABLE — no validated corporate events were returned."}</Card></div>
      <Card title="Opening Gap Context & Deterministic Indication" tone={openingGap.status === "READY" ? "default" : "warning"}>{openingGap.status === "READY" ? `${safeString(openingGap.classification)} · ${Number(openingGap.gap_points) >= 0 ? "+" : ""}${formatNumber(openingGap.gap_points, 2)} points (${Number(openingGap.gap_pct) >= 0 ? "+" : ""}${formatNumber(openingGap.gap_pct, 2)}%). ${safeString(openingGap.disclaimer)}` : "UNAVAILABLE until eligible genuine GIFT Nifty and validated NIFTY reference observations are present."}</Card>
    </div>}

    {tab === "Opening Checklist" && <div data-premarket-panel="opening-checklist" className="space-y-4">
      <Card title={`Operational State: ${operationalState}`} tone={operationalState === "Not Ready" ? "danger" : operationalState === "Partial" ? "warning" : "default"}>Pre-open status derived only from current canonical records.</Card>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">{[
        ["Broker Connected", safeString(canonicalState?.broker_status?.status || "unavailable").toUpperCase()], ["Market Feed", safeString(canonicalState?.market_feed_status?.status || "unavailable").toUpperCase()], ["Options Snapshot", optionReady ? "AVAILABLE" : "UNAVAILABLE"], ["News Freshness", safeString(canonicalState?.news_intelligence?.freshness || "unavailable").toUpperCase()], ["Macro Freshness", safeString(macro.domain_freshness?.global_quotes || "unavailable").toUpperCase()], ["Events Due Today", todayEvents.length ? String(todayEvents.length) : "NONE"]
      ].map(([label, value]) => <Card key={label} title={label}>{value}</Card>)}</div>
      <Card title="Event Risk Today">{todayEvents.length ? <div className="grid gap-2 md:grid-cols-2">{["BEFORE_OPEN", "DURING_SESSION", "AFTER_CLOSE", "OVERNIGHT"].map(bucket => { const grouped = todayEvents.filter(event => safeString(event.session_timing) === bucket && ["HIGH", "CRITICAL"].includes(safeString(event.impact_level).toUpperCase())); return <div key={bucket}><span className="font-bold text-cyan-300">{bucket.replace("_", " ")}:</span> {grouped.length ? grouped.map(event => `${safeString(event.event_name)} at ${formatDateTimeIST(event.scheduled_at_ist || event.scheduled_at)}`).join(" · ") : "No major events"}</div>; })}</div> : "No canonical economic event is scheduled today."}</Card>
      <div className="grid gap-4 md:grid-cols-2"><Card title="Invalidation Conditions & Risk Warnings" tone="danger">Do not enable intraday confirmation if the broker/feed disconnects, timestamps become stale, the opening gap invalidates last-session structure, or options remain unavailable.</Card><Card title="Missing Critical Data" tone="warning">{missing.length ? missing.join(", ") : "None reported."}</Card></div>
    </div>}
  </div>;
}
