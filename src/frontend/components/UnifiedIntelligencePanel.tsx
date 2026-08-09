import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { formatNumber, safeArray, safeString } from "../utils/safeHelpers";
import { EvidenceList, ExplicitState, KeyLevelsPanel, ScenarioCard, SemanticBadge } from "./intelligence/CanonicalPresentation";

function useCanonicalIntelligence() {
  const { canonicalState } = useWorkstationState();
  return { canonicalState: canonicalState as any, intelligence: canonicalState?.unified_intelligence as any };
}

function UnavailableView({ name }: { name: string }) {
  return <section data-unified-intelligence={name} className="rounded-xl border border-amber-900/50 bg-amber-950/15 p-4 text-left text-xs text-amber-300">Unified canonical intelligence is not yet available.</section>;
}

function ScenarioGrid({ scenarios }: { scenarios: any[] }) {
  return scenarios.length ? <div><div className="mb-2 text-[9px] font-bold uppercase text-slate-500">Primary and alternate scenarios</div><div className="grid gap-3 md:grid-cols-2">{scenarios.map(scenario => <ScenarioCard key={scenario.name} scenario={scenario}/>)}</div></div> : <ExplicitState title="Active scenarios" state="UNAVAILABLE" reason="No canonical scenario is eligible."/>;
}

function signalEvidence(signal: any) {
  return signal?.eligible ? safeString(signal.evidence?.[0]) : safeString(signal?.ineligibility_reason || "Canonical evidence unavailable.");
}

function analysisSessionHeading(value: unknown) {
  const state = safeString(value).toUpperCase();
  if (["PRE_OPEN", "PRE-OPEN"].includes(state)) return "PRE-MARKET CONTEXT";
  if (["OPEN", "MARKET_OPEN"].includes(state)) return "LIVE SESSION ANALYSIS";
  if (["WEEKEND", "HOLIDAY"].includes(state)) return "LAST SESSION / NEXT SESSION CONTEXT";
  const istWeekday = new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Kolkata", weekday: "short" }).format(new Date());
  if (state === "CLOSED" && ["Sat", "Sun"].includes(istWeekday)) return "LAST SESSION / NEXT SESSION CONTEXT";
  return "SESSION REVIEW";
}

export function NiftyIntelligenceStrip() {
  const { intelligence } = useCanonicalIntelligence();
  if (!intelligence) return <UnavailableView name="NIFTY_LIVE"/>;
  return <section data-unified-intelligence="NIFTY_LIVE" data-intelligence-view="compact-command-center" data-intelligence-engine={intelligence.engine} className="rounded-lg border border-slate-800 bg-slate-950/70 px-3 py-2.5 text-left">
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2"><div className="mr-auto text-[9px] font-bold uppercase tracking-[.16em] text-slate-500">Market intelligence</div><SemanticBadge value={intelligence.alignment}/><SemanticBadge value={intelligence.market_regime}/><SemanticBadge value={intelligence.confidence} kind="confidence"/><SemanticBadge value={`${safeString(intelligence.risk?.state)}_RISK`} kind="risk"/></div>
    <div className="mt-2 grid gap-2 text-[10px] sm:grid-cols-2"><div><span className="font-semibold text-emerald-300">Confirming:</span> {safeArray(intelligence.confirming_signals).map(value => safeString(value).replaceAll("_", " ")).join(" · ") || "None eligible"}</div><div><span className="font-semibold text-rose-300">Opposing:</span> {safeArray(intelligence.opposing_signals).map(value => safeString(value).replaceAll("_", " ")).join(" · ") || "None eligible"}</div></div>
  </section>;
}

export function PreMarketIntelligenceView() {
  const { canonicalState, intelligence } = useCanonicalIntelligence();
  if (!intelligence) return <UnavailableView name="PRE_MARKET"/>;
  const scenarios = safeArray(intelligence.scenarios) as any[];
  const levels = safeArray(intelligence.key_levels) as any[];
  const gift = canonicalState?.macro_intelligence?.quotes?.GIFT_NIFTY;
  const breadth = canonicalState?.market_data?.breadth;
  const options = canonicalState?.option_intelligence;
  const volatility = canonicalState?.macro_intelligence?.india_vix;
  const news = canonicalState?.news_intelligence;
  const context = [
    ["Opening Context", intelligence.signals?.opening?.state, signalEvidence(intelligence.signals?.opening)],
    ["GIFT Nifty", gift ? "AVAILABLE" : "UNAVAILABLE", gift ? `${formatNumber(gift.value, 2)} · ${safeString(gift.freshness_status || gift.freshness)}` : "No eligible canonical GIFT observation."],
    ["Global Context", intelligence.signals?.global?.state, signalEvidence(intelligence.signals?.global)],
    ["Institutional Context", intelligence.signals?.institutional?.state, signalEvidence(intelligence.signals?.institutional)],
    ["Breadth", breadth?.status, breadth?.coverage ? `${safeString(breadth.coverage.valid)} / ${safeString(breadth.coverage.expected)} constituents · ${safeString(breadth.freshness)}` : "Canonical breadth unavailable."],
    ["Options", options?.status, options?.snapshot_timestamp ? `Observed ${safeString(options.snapshot_timestamp)}` : "Canonical options snapshot unavailable."],
    ["Volatility", volatility?.status || (volatility?.value != null ? "AVAILABLE" : "UNAVAILABLE"), volatility?.value != null ? `India VIX ${formatNumber(volatility.value, 2)} · ${safeString(volatility.freshness)}` : "Canonical volatility context unavailable."],
    ["News / Event Risk", news?.status, `${safeArray(news?.items).length} canonical items · ${safeString(news?.freshness || news?.coverage_status)}`],
  ];
  return <section data-unified-intelligence="PRE_MARKET" data-intelligence-view="next-session-setup" data-intelligence-engine={intelligence.engine} className="space-y-4 rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-left">
    <div className="flex flex-wrap items-center justify-between gap-2"><div><div className="text-[9px] font-black uppercase tracking-[.18em] text-cyan-400">Pre-market readiness</div><h3 className="mt-1 text-sm font-bold text-white">Next-session setup</h3></div><SemanticBadge value={intelligence.readiness} kind="readiness"/></div>
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{context.map(([title, state, reason]) => <ExplicitState key={String(title)} title={String(title)} state={state} reason={reason}/>)}</div>
    <ScenarioGrid scenarios={scenarios}/><div className="grid gap-3 md:grid-cols-2"><EvidenceList title="Confirmation" items={intelligence.confirming_signals} toneClass="text-emerald-300"/><EvidenceList title="Invalidation / risk" items={[...safeArray(intelligence.opposing_signals), ...safeArray(intelligence.risk?.reasons)]} toneClass="text-rose-300"/></div><KeyLevelsPanel levels={levels}/>
  </section>;
}

export function TodaysAnalysisSynthesis() {
  const { canonicalState, intelligence } = useCanonicalIntelligence();
  if (!intelligence) return <UnavailableView name="TODAYS_ANALYSIS"/>;
  const scenarios = safeArray(intelligence.scenarios) as any[];
  const change = intelligence.change_intelligence || {};
  const riskReason = safeArray(intelligence.risk?.reasons).join(" · ") || "No elevated canonical risk reason reported.";
  const session = canonicalState?.market_session?.status || intelligence.session?.status || intelligence.mode;
  return <section data-unified-intelligence="TODAYS_ANALYSIS" data-intelligence-view="full-session-synthesis" data-intelligence-engine={intelligence.engine} className="space-y-4 rounded-xl border border-cyan-900/50 bg-slate-950/70 p-5 text-left">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><div data-analysis-session-heading className="text-[10px] font-black uppercase tracking-[.2em] text-cyan-400">{analysisSessionHeading(session)}</div><h3 className="mt-1 text-sm font-bold text-white">NIFTY Decision Context</h3></div><div className="flex flex-wrap gap-2"><SemanticBadge value={intelligence.readiness} kind="readiness"/><SemanticBadge value={intelligence.alignment}/><SemanticBadge value={intelligence.market_regime}/><SemanticBadge value={intelligence.confidence} kind="confidence"/><SemanticBadge value={`${safeString(intelligence.risk?.state)}_RISK`} kind="risk"/></div></div>
    <p className="text-xs leading-relaxed text-slate-300">{safeString(intelligence.explanation)}</p>
    <div className="grid gap-3 md:grid-cols-3"><EvidenceList title="What confirms the view" items={intelligence.confirming_signals} toneClass="text-emerald-300"/><EvidenceList title="What contradicts it" items={intelligence.opposing_signals} toneClass="text-rose-300"/><ExplicitState title="What changed?" state={change.status || "UNAVAILABLE"} reason={change.reason || "Change intelligence is unavailable."}/></div>
    <KeyLevelsPanel levels={intelligence.key_levels}/><ScenarioGrid scenarios={scenarios}/><ExplicitState title="Session risk and invalidation" state={intelligence.risk?.state} reason={riskReason}/>
  </section>;
}

export function LiveAssistantExplanationView() {
  const { intelligence } = useCanonicalIntelligence();
  if (!intelligence) return <UnavailableView name="LIVE_ASSISTANT"/>;
  const change = intelligence.change_intelligence || {};
  const riskReason = safeArray(intelligence.risk?.reasons).join(" · ") || "No elevated canonical risk reason reported.";
  const missing = safeArray(intelligence.evidence_completeness?.critical_missing).join(" · ") || safeArray(intelligence.unavailable_or_ineligible_signals).join(" · ") || "No critical missing evidence reported for this session mode.";
  return <section data-unified-intelligence="LIVE_ASSISTANT" data-intelligence-view="explanation-console" data-intelligence-engine={intelligence.engine} className="space-y-4 rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-left">
    <div><div className="text-[9px] font-black uppercase tracking-[.18em] text-cyan-400">Explanation console</div><h3 className="mt-1 text-sm font-bold text-white">Why ArdhaMind is saying this</h3></div>
    <div data-canonical-assistant-answers className="grid gap-3 md:grid-cols-2 lg:grid-cols-3"><ExplicitState title="What is the market state?" state={intelligence.alignment} reason={safeString(intelligence.market_regime).replaceAll("_", " ")}/><ExplicitState title="Why?" state={intelligence.confidence} reason={safeString(intelligence.explanation)}/><div className="p-2"><EvidenceList title="What confirms it?" items={intelligence.confirming_signals} toneClass="text-emerald-300"/></div><div className="p-2"><EvidenceList title="What contradicts it?" items={intelligence.opposing_signals} toneClass="text-rose-300"/></div><ExplicitState title="What is the current risk?" state={intelligence.risk?.state} reason={riskReason}/><ExplicitState title="What changed?" state={change.status || "UNAVAILABLE"} reason={change.reason || "Change intelligence is unavailable."}/><ExplicitState title="How complete is the evidence? What data is missing?" state={missing.startsWith("No critical") ? "READY" : "PARTIAL"} reason={missing}/></div>
    <KeyLevelsPanel levels={intelligence.key_levels}/><ScenarioGrid scenarios={safeArray(intelligence.scenarios) as any[]}/><div className="text-[9px] text-slate-600">Invalidation conditions remain inside each canonical scenario · Human decision required · Read only</div>
  </section>;
}
