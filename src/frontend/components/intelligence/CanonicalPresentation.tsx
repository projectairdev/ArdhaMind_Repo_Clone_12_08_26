import React from "react";
import { safeArray, safeString, formatNumber } from "../../utils/safeHelpers";

export type SemanticKind = "state" | "freshness" | "readiness" | "confidence" | "risk";

function tone(value: string, kind: SemanticKind) {
  const state = value.toUpperCase();
  if (kind === "risk") {
    if (state.includes("HIGH") || state.includes("IMMINENT")) return "border-rose-800 bg-rose-950/30 text-rose-300";
    if (state.includes("ELEVATED") || state.includes("MODERATE")) return "border-amber-800 bg-amber-950/30 text-amber-300";
    if (state.includes("LOW") || state.includes("NORMAL")) return "border-emerald-800 bg-emerald-950/40 text-emerald-300";
  }
  if (kind === "confidence" && state === "INSUFFICIENT") return "border-rose-800 bg-rose-950/30 text-rose-300";
  if (["READY", "FRESH", "VALID", "HIGH", "BULLISH", "POSITIVE", "RISK_ON"].includes(state)) return "border-emerald-800 bg-emerald-950/40 text-emerald-300";
  if (["PARTIAL", "PARTIAL_READY", "STALE", "LAST_VALID_SESSION", "MARKET_CLOSED", "MODERATE", "ELEVATED", "MIXED", "CONFLICTED"].includes(state)) return "border-amber-800 bg-amber-950/30 text-amber-300";
  if (["BLOCKED", "ERROR", "INVALID", "BEARISH", "NEGATIVE", "RISK_OFF", "IMMINENT"].includes(state)) return "border-rose-800 bg-rose-950/30 text-rose-300";
  return "border-slate-700 bg-slate-900 text-slate-300";
}

export function SemanticBadge({ value, kind = "state" }: { value: unknown; kind?: SemanticKind }) {
  const text = safeString(value || "UNAVAILABLE").toUpperCase();
  return <span data-semantic-kind={kind} data-semantic-state={text} className={`inline-flex rounded border px-2 py-1 text-[9px] font-bold tracking-wide ${tone(text, kind)}`}>{text.replaceAll("_", " ")}</span>;
}

export function ProvenanceLine({ source, observedAt, freshness }: { source?: unknown; observedAt?: unknown; freshness?: unknown }) {
  return <div className="flex flex-wrap gap-x-3 gap-y-1 text-[9px] text-slate-500">
    <span>Source: {safeString(source || "UNAVAILABLE")}</span>
    <span>Observed: {safeString(observedAt || "UNAVAILABLE")}</span>
    <SemanticBadge value={freshness} kind="freshness" />
  </div>;
}

export function EvidenceList({ title, items, toneClass = "text-slate-300" }: { title: string; items: unknown; toneClass?: string }) {
  const values = safeArray(items as any[]).map(item => safeString(item)).filter(Boolean);
  return <div><div className="text-[9px] font-bold uppercase tracking-wide text-slate-500">{title}</div>{values.length ? <ul className={`mt-1 space-y-1 text-[10px] ${toneClass}`}>{values.map((item, index) => <li key={`${item}-${index}`}>• {item.replaceAll("_", " ")}</li>)}</ul> : <p className="mt-1 text-[10px] text-slate-600">No eligible evidence reported.</p>}</div>;
}

export function KeyLevelsPanel({ levels }: { levels: unknown }) {
  const rows = safeArray(levels as any[]) as any[];
  return <section data-canonical-levels className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
    <div className="text-[9px] font-bold uppercase text-slate-500">Genuine key levels</div>
    {rows.length ? <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{rows.map((level, index) => <div key={`${level.origin}-${level.value}-${index}`} className="flex items-center justify-between rounded border border-slate-800 px-2 py-1.5 text-[10px]"><span className="font-bold text-white">{formatNumber(level.value, 2)}</span><span className="text-slate-500">{safeString(level.role)} · {safeString(level.origin)}</span></div>)}</div> : <p className="mt-2 text-[10px] text-slate-500">UNAVAILABLE — no genuine canonical level is eligible.</p>}
  </section>;
}

export function ScenarioCard({ scenario }: { key?: string; scenario: any }) {
  return <article data-canonical-scenario={safeString(scenario?.name)} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-[10px] text-slate-300">
    <div className="flex items-center justify-between gap-2"><strong className="text-cyan-300">{safeString(scenario?.name).replaceAll("_", " ")}</strong><SemanticBadge value={scenario?.priority} /></div>
    <div className="mt-2"><b>Confirm:</b> {safeArray(scenario?.confirmation_conditions).join(" · ") || "UNAVAILABLE"}</div>
    <div className="mt-1 text-rose-300"><b>Invalidate:</b> {safeArray(scenario?.invalidation_conditions).join(" · ") || "UNAVAILABLE"}</div>
    <div className="mt-2 text-[9px] text-slate-600">Conditional scenario only · Not a prediction · No execution instruction</div>
  </article>;
}

export function ExplicitState({ title, state, reason }: { title: string; state: unknown; reason: unknown }) {
  return <section className="rounded-lg border border-slate-800 bg-slate-950/60 p-3"><div className="flex items-center justify-between gap-3"><strong className="text-[10px] text-white">{title}</strong><SemanticBadge value={state} kind="readiness" /></div><p className="mt-2 text-[10px] text-slate-500">{safeString(reason || "No additional detail is available.")}</p></section>;
}
