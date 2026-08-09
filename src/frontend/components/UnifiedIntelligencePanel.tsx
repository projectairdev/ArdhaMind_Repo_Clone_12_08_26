import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { safeArray, safeString } from "../utils/safeHelpers";
import { EvidenceList, ExplicitState, KeyLevelsPanel, ScenarioCard, SemanticBadge } from "./intelligence/CanonicalPresentation";

export type IntelligenceWorkspace = "NIFTY_LIVE" | "PRE_MARKET" | "TODAYS_ANALYSIS" | "LIVE_ASSISTANT";

function ContextHeader({ intelligence, compact = false }: { intelligence: any; compact?: boolean }) {
  return <div className="flex flex-wrap items-start justify-between gap-3"><div><div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-400">{safeString(intelligence.mode).replaceAll("_", " ")}</div><h3 className="mt-1 text-sm font-bold text-white">NIFTY Decision Context</h3></div><div className="flex flex-wrap gap-2"><SemanticBadge value={intelligence.readiness} kind="readiness"/><SemanticBadge value={intelligence.alignment}/><SemanticBadge value={intelligence.market_regime}/><SemanticBadge value={intelligence.confidence} kind="confidence"/>{!compact && <SemanticBadge value={`${safeString(intelligence.risk?.state)}_RISK`} kind="risk"/>}</div></div>;
}

function ScenarioGrid({ scenarios }: { scenarios: any[] }) {
  return scenarios.length ? <div><div className="mb-2 text-[9px] font-bold uppercase text-slate-500">Primary and alternate scenarios</div><div className="grid gap-3 md:grid-cols-2">{scenarios.map(scenario => <ScenarioCard key={scenario.name} scenario={scenario}/>)}</div></div> : <ExplicitState title="Active scenarios" state="UNAVAILABLE" reason="No canonical scenario is eligible."/>;
}

export function UnifiedIntelligencePanel({ workspace }: { workspace: IntelligenceWorkspace }) {
  const { canonicalState } = useWorkstationState();
  const intelligence: any = canonicalState?.unified_intelligence;
  if (!intelligence) return <section data-unified-intelligence={workspace} className="rounded-xl border border-amber-900/50 bg-amber-950/15 p-5 text-left text-xs text-amber-300">Unified canonical intelligence is not yet available.</section>;
  const scenarios = safeArray(intelligence.scenarios) as any[];
  const levels = safeArray(intelligence.key_levels) as any[];
  const change = intelligence.change_intelligence || {};
  const riskReason = safeArray(intelligence.risk?.reasons).join(" · ") || "No elevated canonical risk reason reported.";
  const missing = safeArray(intelligence.evidence_completeness?.critical_missing).join(" · ") || safeArray(intelligence.unavailable_or_ineligible_signals).join(" · ") || "No critical missing evidence reported for this session mode.";
  const shell = "rounded-xl border border-cyan-900/50 bg-slate-950/70 p-4 text-left space-y-4";

  if (workspace === "NIFTY_LIVE") return <section data-unified-intelligence={workspace} data-intelligence-view="compact-command-center" data-intelligence-engine={intelligence.engine} className={shell}>
    <ContextHeader intelligence={intelligence} compact/>
    <p className="text-xs leading-relaxed text-slate-300">{safeString(intelligence.explanation)}</p>
    <div className="grid gap-3 md:grid-cols-3"><EvidenceList title="Confirming signals" items={intelligence.confirming_signals} toneClass="text-emerald-300"/><EvidenceList title="Contradicting signals" items={intelligence.opposing_signals} toneClass="text-rose-300"/><ExplicitState title="Analytical risk" state={intelligence.risk?.state} reason={riskReason}/></div>
    <div className="text-[9px] text-slate-600">Compact current/session summary · Engine: {safeString(intelligence.engine)}</div>
  </section>;

  if (workspace === "PRE_MARKET") return <section data-unified-intelligence={workspace} data-intelligence-view="opening-preparation" data-intelligence-engine={intelligence.engine} className={shell}>
    <ContextHeader intelligence={intelligence}/>
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><ExplicitState title="Opening readiness" state={intelligence.readiness} reason={safeString(intelligence.explanation)}/>{[{ name: "opening", title: "Opening context" }, { name: "global", title: "Global context" }, { name: "institutional", title: "Institutional context" }].map(({ name, title }) => { const signal: any = intelligence.signals?.[name]; return <ExplicitState key={name} title={title} state={signal?.state || "UNAVAILABLE"} reason={signal?.eligible ? safeString(signal.evidence?.[0]) : safeString(signal?.ineligibility_reason || "Canonical evidence unavailable.")}/>; })}</div>
    <ScenarioGrid scenarios={scenarios}/>
    <KeyLevelsPanel levels={levels}/>
    <div className="grid gap-3 md:grid-cols-2"><EvidenceList title="Opening confirmation" items={intelligence.confirming_signals} toneClass="text-emerald-300"/><EvidenceList title="Risk / invalidation evidence" items={[...safeArray(intelligence.opposing_signals), ...safeArray(intelligence.risk?.reasons)]} toneClass="text-rose-300"/></div>
  </section>;

  if (workspace === "TODAYS_ANALYSIS") return <section data-unified-intelligence={workspace} data-intelligence-view="session-interpretation" data-intelligence-engine={intelligence.engine} className={shell}>
    <ContextHeader intelligence={intelligence}/>
    <p className="text-xs leading-relaxed text-slate-300">{safeString(intelligence.explanation)}</p>
    <div className="grid gap-3 md:grid-cols-3"><EvidenceList title="What confirms the view" items={intelligence.confirming_signals} toneClass="text-emerald-300"/><EvidenceList title="What contradicts it" items={intelligence.opposing_signals} toneClass="text-rose-300"/><ExplicitState title="What changed?" state={change.status || "UNAVAILABLE"} reason={change.reason || "Change intelligence is unavailable."}/></div>
    <KeyLevelsPanel levels={levels}/><ScenarioGrid scenarios={scenarios}/>
    <ExplicitState title="Session risk and invalidation" state={intelligence.risk?.state} reason={riskReason}/>
  </section>;

  return <section data-unified-intelligence={workspace} data-intelligence-view="explanation-console" data-intelligence-engine={intelligence.engine} className={shell}>
    <ContextHeader intelligence={intelligence}/>
    <div data-canonical-assistant-answers className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
      <ExplicitState title="What is the market state?" state={intelligence.alignment} reason={`${safeString(intelligence.mode).replaceAll("_", " ")} · ${safeString(intelligence.market_regime).replaceAll("_", " ")}`}/>
      <ExplicitState title="Why?" state={intelligence.confidence} reason={safeString(intelligence.explanation)}/>
      <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3"><EvidenceList title="What confirms it?" items={intelligence.confirming_signals} toneClass="text-emerald-300"/></div>
      <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3"><EvidenceList title="What contradicts it?" items={intelligence.opposing_signals} toneClass="text-rose-300"/></div>
      <ExplicitState title="What is the current risk?" state={intelligence.risk?.state} reason={riskReason}/>
      <ExplicitState title="What changed?" state={change.status || "UNAVAILABLE"} reason={change.reason || "Change intelligence is unavailable."}/>
      <ExplicitState title="How complete is the evidence? / What data is missing?" state={missing === "No critical missing evidence reported for this session mode." ? "READY" : "PARTIAL"} reason={missing}/>
    </div>
    <KeyLevelsPanel levels={levels}/><ScenarioGrid scenarios={scenarios}/>
    <div className="text-[9px] text-slate-600">What invalidates the view is stated inside each canonical scenario · Human decision required · Read only · No execution</div>
  </section>;
}
