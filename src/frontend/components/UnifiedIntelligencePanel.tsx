import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { safeArray, safeString } from "../utils/safeHelpers";
import { EvidenceList, ExplicitState, KeyLevelsPanel, ProvenanceLine, ScenarioCard, SemanticBadge } from "./intelligence/CanonicalPresentation";

export type IntelligenceWorkspace = "NIFTY_LIVE" | "PRE_MARKET" | "TODAYS_ANALYSIS" | "LIVE_ASSISTANT";

export function UnifiedIntelligencePanel({ workspace }: { workspace: IntelligenceWorkspace }) {
  const { canonicalState } = useWorkstationState();
  const intelligence: any = canonicalState?.unified_intelligence;
  if (!intelligence) return <section data-unified-intelligence={workspace} className="rounded-xl border border-amber-900/50 bg-amber-950/15 p-5 text-left text-xs text-amber-300">Unified canonical intelligence is not yet available.</section>;
  const signals = Object.entries(intelligence.signals || {}) as Array<[string, any]>;
  const scenarios = safeArray(intelligence.scenarios) as any[];
  const levels = safeArray(intelligence.key_levels) as any[];
  const change = intelligence.change_intelligence || {};
  return <section data-unified-intelligence={workspace} data-intelligence-engine={intelligence.engine} className="rounded-xl border border-cyan-900/50 bg-slate-950/70 p-5 text-left space-y-4">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-400">{safeString(intelligence.mode).replaceAll("_", " ")}</div><h3 className="mt-1 text-sm font-bold text-white">Canonical NIFTY Decision Context</h3></div><div className="flex flex-wrap gap-2"><SemanticBadge value={intelligence.readiness} kind="readiness"/><SemanticBadge value={intelligence.alignment}/><SemanticBadge value={intelligence.market_regime}/><SemanticBadge value={intelligence.confidence} kind="confidence"/><SemanticBadge value={`${safeString(intelligence.risk?.state)}_RISK`} kind="risk"/></div></div>
    <p className="text-xs leading-relaxed text-slate-300">{safeString(intelligence.explanation)}</p>
    <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-5">{signals.map(([name, signal]) => <div key={name} data-signal-family={name} className={`rounded border p-2 ${["price","opening"].includes(name) ? "border-cyan-900/60 bg-cyan-950/10" : signal.eligible ? "border-slate-800 bg-slate-900/70" : "border-slate-900 bg-slate-950"}`}><div className="flex items-center justify-between gap-1"><div className="text-[9px] font-bold text-slate-500">{name.toUpperCase()}</div><SemanticBadge value={signal.state}/></div><div className="mt-2 text-[9px] text-slate-500">{signal.eligible ? safeString(signal.evidence?.[0]) : safeString(signal.ineligibility_reason)}</div><details className="mt-2"><summary className="cursor-pointer text-[8px] text-slate-600 hover:text-slate-400">Source details</summary><div className="mt-1"><ProvenanceLine source={signal.source} observedAt={signal.observed_at} freshness={signal.freshness}/></div></details></div>)}</div>
    <div className="grid gap-4 md:grid-cols-3"><EvidenceList title="Confirming" items={intelligence.confirming_signals} toneClass="text-emerald-300"/><EvidenceList title="Contradicting" items={intelligence.opposing_signals} toneClass="text-rose-300"/><EvidenceList title="Unavailable / Ineligible" items={intelligence.unavailable_or_ineligible_signals} toneClass="text-amber-300"/></div>
    {workspace === "LIVE_ASSISTANT" && <div data-canonical-assistant-answers className="grid gap-3 md:grid-cols-3"><ExplicitState title="What is the market state?" state={intelligence.alignment} reason={`${safeString(intelligence.mode).replaceAll("_", " ")} · ${safeString(intelligence.market_regime).replaceAll("_", " ")}`}/><ExplicitState title="What is the current risk?" state={intelligence.risk?.state} reason={safeArray(intelligence.risk?.reasons).join(" · ") || "No elevated canonical risk reason reported."}/><ExplicitState title="How complete is the evidence?" state={intelligence.confidence} reason={safeArray(intelligence.evidence_completeness?.critical_missing).join(" · ") || "No critical missing evidence reported for this session mode."}/></div>}
    <KeyLevelsPanel levels={levels}/>
    {scenarios.length > 0 && <div><div className="mb-2 text-[9px] font-bold uppercase text-slate-500">Conditional scenarios</div><div className="grid gap-3 md:grid-cols-2">{scenarios.map(s => <ScenarioCard key={s.name} scenario={s}/>)}</div></div>}
    {(workspace === "TODAYS_ANALYSIS" || workspace === "LIVE_ASSISTANT") && <ExplicitState title="What changed?" state={change.status || "UNAVAILABLE"} reason={change.reason}/>}
    <div className="text-[9px] text-slate-600">Engine: {safeString(intelligence.engine)} · Human decision required · Read only · No execution</div>
  </section>;
}
