import React, { useState } from "react";
import { AlertTriangle, CheckCircle2, Clock, Database, KeyRound, ShieldCheck } from "lucide-react";
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
import { DecisionEngine } from "./DecisionEngine";

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

export function NiftyLiveWorkspace() {
  const [tab, setTab] = useState("Overview");
  const { marketContext, optionContext, loading } = useWorkstationState();
  const marketAvailable = Boolean(marketContext?.current_spot && marketContext?.last_tick_time);
  return <div className="space-y-5"><Heading eyebrow="Live intelligence" title="NIFTY Live" description="Validated market, trend and option-chain intelligence. Read only."/><Tabs values={["Overview", "Price & Trend", "Options"]} active={tab} onChange={setTab}/>
    {loading && !marketAvailable ? <ReadinessState kind="initializing" title="Initializing market intelligence" reason="Waiting for a validated Kite market observation."/> : !marketAvailable ? <ReadinessState kind="unavailable" title="Live market data unavailable" reason="Connect Kite or wait for a valid market snapshot. No fallback price is shown."/> : tab === "Overview" ? <><ExecutiveSummary/><MarketScoring/></> : tab === "Price & Trend" ? <MarketOverview/> : optionContext?.underlying_spot ? <MarketOverview/> : <ReadinessState kind="blocked" title="Options analysis blocked" reason="Waiting for a valid option chain and current expiry."/>}
  </div>;
}

export function PreMarketPlannerWorkspace() {
  const [tab, setTab] = useState("Evening Outlook");
  const { eveningReport } = useWorkstationState();
  const available = Boolean(eveningReport?.timestamp);
  return <div className="space-y-5"><Heading eyebrow="Next-session intelligence" title="Pre-Market Planner" description="Previous-session evidence and opening preparation without fabricated cues."/><Tabs values={["Evening Outlook", "8:50 AM Briefing", "Opening Checklist"]} active={tab} onChange={setTab}/>{available ? <TomorrowWorkspace/> : <ReadinessState kind="blocked" title={`${tab} unavailable`} reason="Waiting for historical data or a final validated session snapshot."/>}</div>;
}

export function TodaysAnalysisWorkspace() {
  const { marketContext } = useWorkstationState();
  return <div className="space-y-5"><Heading eyebrow="Meaning, not headlines" title="Today’s Analysis" description="Why NIFTY is behaving as it is and which scenarios are confirming or failing."/>{marketContext?.current_spot ? <MarketStory/> : <ReadinessState kind="blocked" title="Today’s Analysis is waiting" reason="A validated market context is required before interpreting the session."/>}</div>;
}

export function NewsUpdatesWorkspace() {
  const [tab, setTab] = useState("Live Feed");
  const { newsSentiment } = useWorkstationState();
  const available = Boolean(newsSentiment?.articles?.length && newsSentiment?.timestamp);
  return <div className="space-y-5"><Heading eyebrow="What happened" title="NEWS & UPDATES" description="Source- and time-aware market updates. Analysis remains in Today’s Analysis."/><Tabs values={["Live Feed", "Market Impact", "Events", "Corporate", "Watchlist"]} active={tab} onChange={setTab}/>{available ? <NewsIntelligence/> : <ReadinessState kind="unavailable" title="News provider unavailable" reason="No verified live news records are available. Hardcoded publisher records are not displayed."/>}</div>;
}

export function LiveAssistantWorkspace() {
  const { marketContext, decisionReport } = useWorkstationState();
  const ready = Boolean(marketContext?.current_spot && decisionReport?.timestamp);
  return <div className="space-y-5"><Heading eyebrow="Plan versus live market" title="Live Assistant" description="Current scenario, confirmations, invalidations, changes and what to watch next."/>{ready ? <><IntradayAssistant/><DecisionEngine/></> : <ReadinessState kind="blocked" title="Live Assistant is waiting" reason="Validated market context and current analytical outputs are required. No journal or simulated trade state is used."/>}</div>;
}

export function SettingsWorkspace() {
  const { themeClasses } = useTheme();
  const { workspaceContext, marketContext, connectionState, syncBroker, brokerAccount } = useWorkstationState();
  const [apiKey, setApiKey] = useState(""); const [accessToken, setAccessToken] = useState(""); const [message, setMessage] = useState("");
  const connect = async () => { try { setMessage("Connecting read-only Kite session…"); await connectBroker(apiKey, accessToken, false, false); await syncBroker(); setMessage("Kite session connected. Order execution remains disabled."); } catch (error) { setMessage(error instanceof Error ? error.message : "Kite connection failed."); } };
  const status = workspaceContext.brokerState;
  return <div className="space-y-5"><Heading eyebrow="Configuration and diagnostics" title="Settings" description="Kite, OpenAI readiness, data sources, notifications, diagnostics, appearance and product information."/>
    <div className="grid gap-4 lg:grid-cols-2">
      <section className={`${themeClasses.card} rounded-xl border p-5 text-left`}><div className="flex items-center gap-2 font-bold text-white"><KeyRound size={16}/>Kite · Read Only</div><p className="mt-2 text-xs text-neutral-400">Session: <strong>{status}</strong> · Client: {brokerAccount?.client_id || "Unavailable"}</p><div className="mt-4 space-y-2"><input aria-label="Kite API key" value={apiKey} onChange={e=>setApiKey(e.target.value)} placeholder="Kite API key" className="w-full rounded border border-neutral-800 bg-neutral-950 p-2 text-xs"/><input aria-label="Kite access token" type="password" value={accessToken} onChange={e=>setAccessToken(e.target.value)} placeholder="Access token" className="w-full rounded border border-neutral-800 bg-neutral-950 p-2 text-xs"/><button onClick={connect} className="rounded bg-cyan-900 px-3 py-2 text-xs font-bold text-cyan-100">Connect / Reconnect</button>{message && <p className="text-xs text-neutral-400">{message}</p>}</div><div className="mt-4 flex items-center gap-2 text-xs text-emerald-400"><ShieldCheck size={14}/>Order placement, modification, cancellation and exits are unavailable.</div></section>
      <section className={`${themeClasses.card} rounded-xl border p-5 text-left`}><div className="flex items-center gap-2 font-bold text-white"><Database size={16}/>Data Sources</div><p className="mt-3 text-xs text-neutral-400">REST: {status === "CONNECTED" ? "Connected" : "Unavailable"}</p><p className="mt-1 text-xs text-neutral-400">WebSocket: {connectionState}</p><p className="mt-1 text-xs text-neutral-400">Market feed: {marketContext?.feed_health || "Unavailable"}</p><p className="mt-1 text-xs text-neutral-400">Last observation: {marketContext?.last_tick_time || "Unavailable"}</p></section>
      <section className={`${themeClasses.card} rounded-xl border p-5 text-left`}><div className="flex items-center gap-2 font-bold text-white"><CheckCircle2 size={16}/>OpenAI</div><p className="mt-3 text-xs text-neutral-400">Provider status: Not configured</p><p className="mt-1 text-xs text-neutral-400">Model: Unavailable</p><p className="mt-1 text-xs text-emerald-400">Deterministic explanation fallback: Available</p></section>
      <section className={`${themeClasses.card} rounded-xl border p-5 text-left`}><div className="flex items-center gap-2 font-bold text-white"><Clock size={16}/>Diagnostics</div><p className="mt-3 text-xs text-neutral-400">Broker: {status}</p><p className="mt-1 text-xs text-neutral-400">Feed latency: {marketContext?.feed_latency_ms ? `${marketContext.feed_latency_ms} ms` : "Unavailable"}</p><p className="mt-1 text-xs text-neutral-400">Product: AIR ArdhaMind · Phase 1 read-only intelligence</p></section>
    </div>
  </div>;
}

