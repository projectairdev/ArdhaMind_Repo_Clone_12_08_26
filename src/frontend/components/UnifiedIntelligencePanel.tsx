import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { safeArray, safeString } from "../utils/safeHelpers";

export function UnifiedIntelligencePanel({ workspace }: { workspace: "PRE_MARKET" | "TODAYS_ANALYSIS" | "LIVE_ASSISTANT" }) {
  const { canonicalState } = useWorkstationState();
  const intelligence: any = canonicalState?.unified_intelligence;
  if (!intelligence) return <section data-unified-intelligence={workspace} className="rounded-xl border border-amber-900/50 bg-amber-950/15 p-5 text-left text-xs text-amber-300">Unified canonical intelligence is not yet available.</section>;
  const signals = Object.entries(intelligence.signals || {}) as Array<[string, any]>;
  const scenarios = safeArray(intelligence.scenarios) as any[];
  const levels = safeArray(intelligence.key_levels) as any[];
  return <section data-unified-intelligence={workspace} data-intelligence-engine={intelligence.engine} className="rounded-xl border border-cyan-900/50 bg-slate-950/70 p-5 text-left space-y-4">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-400">{safeString(intelligence.mode).replaceAll("_", " ")}</div><h3 className="mt-1 text-sm font-bold text-white">{safeString(intelligence.alignment).replaceAll("_", " ")}</h3></div><div className="flex gap-2 text-[10px] font-bold"><span className="rounded border border-slate-700 px-2 py-1 text-slate-300">{safeString(intelligence.confidence)} CONFIDENCE</span><span className="rounded border border-amber-800 px-2 py-1 text-amber-300">{safeString(intelligence.risk?.state)} RISK</span></div></div>
    <p className="text-xs leading-relaxed text-slate-300">{safeString(intelligence.explanation)}</p>
    <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-5">{signals.map(([name, signal]) => <div key={name} className={`rounded border p-2 ${signal.eligible ? "border-slate-800 bg-slate-900/70" : "border-slate-900 bg-slate-950 text-slate-600"}`}><div className="text-[9px] font-bold uppercase text-slate-500">{name}</div><div className="mt-1 text-[10px] font-bold text-slate-200">{safeString(signal.state)}</div><div className="mt-1 text-[9px] text-slate-500">{signal.eligible ? safeString(signal.evidence?.[0]) : safeString(signal.ineligibility_reason)}</div></div>)}</div>
    {workspace === "PRE_MARKET" && scenarios.length > 0 && <div className="grid gap-3 md:grid-cols-2">{scenarios.map(s => <div key={s.name} className="rounded border border-slate-800 p-3 text-[10px] text-slate-300"><div className="font-bold text-cyan-300">{safeString(s.priority)} · {safeString(s.name).replaceAll("_", " ")}</div><div className="mt-2"><b>Confirm:</b> {safeArray(s.confirmation_conditions).join(" · ")}</div><div className="mt-1 text-rose-300"><b>Invalidate:</b> {safeArray(s.invalidation_conditions).join(" · ")}</div></div>)}</div>}
    {workspace !== "PRE_MARKET" && <div className="grid gap-3 md:grid-cols-2 text-[10px]"><div><span className="font-bold text-emerald-300">CONFIRMS:</span> {safeArray(intelligence.confirming_signals).join(", ") || "No dominant confirmation"}</div><div><span className="font-bold text-rose-300">CONTRADICTS:</span> {safeArray(intelligence.opposing_signals).join(", ") || "No eligible opposition"}</div></div>}
    <div className="text-[10px] text-slate-500">Genuine levels: {levels.length ? levels.slice(0, 8).map(l => `${l.value} ${l.origin}`).join(" · ") : "UNAVAILABLE"} · Human decision required · No execution</div>
  </section>;
}
