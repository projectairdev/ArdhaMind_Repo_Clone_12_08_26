import React from "react";
import { safeArray, safeString, formatNumber } from "../../utils/safeHelpers";
import { mapTraderEnum, mapTraderLabel } from "../../utils/traderTerminology";
import { useWorkstationState } from "../../context/WorkstationStateContext";

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
  const domain = kind === "confidence" ? "confidence" : kind === "risk" ? "risk" : kind === "freshness" ? "freshness" : kind === "readiness" ? "readiness" : "general";
  const display = mapTraderEnum(text, domain);
  return <span data-semantic-kind={kind} data-semantic-state={text} className={`inline-flex rounded border px-2 py-1 text-[9px] font-bold tracking-wide ${tone(text, kind)}`}>{display}</span>;
}

export function ProvenanceLine({ source, observedAt, freshness }: { source?: unknown; observedAt?: unknown; freshness?: unknown }) {
  const srcStr = safeString(source || "UNAVAILABLE");
  const displaySource = srcStr === "kite_historical_api" ? "Kite Historical API" : srcStr;
  return <div className="flex flex-wrap gap-x-3 gap-y-1 text-[9px] text-slate-500">
    <span>Source: {displaySource}</span>
    <span>Observed: {safeString(observedAt || "UNAVAILABLE")}</span>
    <SemanticBadge value={freshness} kind="freshness" />
  </div>;
}

export function EvidenceList({ title, items, toneClass = "text-slate-300" }: { title: string; items: unknown; toneClass?: string }) {
  const values = safeArray(items as any[]).map(item => safeString(item)).filter(Boolean);
  return <div><div className="text-[9px] font-bold uppercase tracking-wide text-slate-500">{mapTraderLabel(title)}</div>{values.length ? <ul className={`mt-1 space-y-1 text-[10px] ${toneClass}`}>{values.map((item, index) => <li key={`${item}-${index}`}>• {mapTraderEnum(item)}</li>)}</ul> : <p className="mt-1 text-[10px] text-slate-600">No active signals reported.</p>}</div>;
}

export function KeyLevelsPanel({ levels }: { levels: unknown }) {
  const rows = safeArray(levels as any[]) as any[];
  return <section data-canonical-levels className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-left">
    <div className="text-[9px] font-bold uppercase text-slate-500">Key Levels to Watch</div>
    {rows.length ? <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{rows.map((level, index) => <div key={`${level.origin}-${level.value}-${index}`} className="flex items-center justify-between rounded border border-slate-800 px-2 py-1.5 text-[10px]"><span className="font-bold text-white font-mono">{formatNumber(level.value, 2)}</span><span className="text-slate-400">{mapTraderEnum(level.role)} · {mapTraderEnum(level.origin)}</span></div>)}</div> : <p className="mt-2 text-[10px] text-slate-500">UNAVAILABLE — no genuine canonical level is eligible.</p>}
  </section>;
}

export function ScenarioCard({ scenario }: { key?: string; scenario: any }) {
  const { canonicalState, marketContext } = useWorkstationState() as any;
  const sessionStatus = canonicalState?.market_session?.status || marketContext?.trading_session || "CLOSED";
  const isClosed = Boolean(canonicalState?.market_session?.is_closed || ["CLOSED", "HOLIDAY", "POST_CLOSE", "WEEKEND"].includes(String(sessionStatus).toUpperCase()));

  const primary = safeString(scenario?.priority).toUpperCase().includes("PRIMARY");
  const stateLabel = isClosed ? "NEXT SESSION — PENDING" : "LIVE SESSION — ACTIVE";

  const mapCondition = (cond: any) => {
    if (!isClosed) return mapTraderEnum(cond);
    const c = String(cond).toLowerCase();
    if (c.includes("opening range")) return "Opening Range: Pending";
    if (c.includes("breadth")) return "Breadth Confirmation: Pending";
    if (c.includes("vwap")) return "VWAP Confirmation: Pending";
    if (c.includes("live scenario") || c.includes("scenario confirmation") || c.includes("confirmation")) return "Live Scenario Confirmation: Pending";
    return mapTraderEnum(cond) + ": Pending";
  };

  return <article data-canonical-scenario={safeString(scenario?.name)} className={`rounded-lg border bg-slate-950/60 p-3 text-[10px] text-slate-300 ${primary ? "border-cyan-800/70" : "border-slate-800"}`}>
    <div className="flex items-center justify-between gap-2">
      <strong className="text-cyan-300">{mapTraderEnum(scenario?.name)}</strong>
      <div className="flex gap-1.5 items-center">
        <span className={`px-1.5 py-0.5 rounded text-[7px] font-bold border font-mono ${isClosed ? "border-amber-800 bg-amber-950/30 text-amber-300" : "border-emerald-800 bg-emerald-950/30 text-emerald-300"}`}>
          {stateLabel}
        </span>
        <SemanticBadge value={scenario?.priority} />
      </div>
    </div>
    <div className="mt-2"><b>Supports:</b> {safeArray(scenario?.confirmation_conditions).map(v => mapCondition(v)).join(" · ") || "UNAVAILABLE"}</div>
    <div className="mt-1 text-rose-300"><b>Invalidates:</b> {safeArray(scenario?.invalidation_conditions).map(v => mapTraderEnum(v)).join(" · ") || "UNAVAILABLE"}</div>
    <div className="mt-2 text-[9px] text-slate-600">Conditional scenario only · Not a prediction · No execution instruction</div>
  </article>;
}

export function ExplicitState({ title, state, reason }: { key?: string; title: string; state: unknown; reason: unknown }) {
  return <section className="rounded-lg border border-slate-800 bg-slate-950/60 p-3"><div className="flex items-center justify-between gap-3"><strong className="text-[10px] text-white">{mapTraderLabel(title)}</strong><SemanticBadge value={state} kind="readiness" /></div><p className="mt-2 text-[10px] text-slate-500">{safeString(reason || "No additional detail is available.")}</p></section>;
}

export function nearestDecisionLevels(zones: any[], spot: number | null) {
  const zoneRows = safeArray(zones);
  const supports = zoneRows.filter((z: any) => z && z.role === "SUPPORT");
  const resistances = zoneRows.filter((z: any) => z && z.role === "RESISTANCE");

  let nearestSupport: any = null;
  let nearestResistance: any = null;

  if (spot != null && !isNaN(spot) && spot > 0) {
    const below = supports.filter((z: any) => z.upper <= spot || z.lower <= spot);
    if (below.length > 0) {
      below.sort((a: any, b: any) => b.upper - a.upper);
      nearestSupport = below[0];
    } else if (supports.length > 0) {
      const sorted = [...supports].sort((a: any, b: any) => Math.abs(a.lower - spot) - Math.abs(b.lower - spot));
      nearestSupport = sorted[0];
    }

    const above = resistances.filter((z: any) => z.lower >= spot || z.upper >= spot);
    if (above.length > 0) {
      above.sort((a: any, b: any) => a.lower - b.lower);
      nearestResistance = above[0];
    } else if (resistances.length > 0) {
      const sorted = [...resistances].sort((a: any, b: any) => Math.abs(a.lower - spot) - Math.abs(b.lower - spot));
      nearestResistance = sorted[0];
    }
  } else {
    if (supports.length > 0) {
      const sorted = [...supports].sort((a: any, b: any) => b.upper - a.upper);
      nearestSupport = sorted[0];
    }
    if (resistances.length > 0) {
      const sorted = [...resistances].sort((a: any, b: any) => a.lower - b.lower);
      nearestResistance = sorted[0];
    }
  }

  return { nearestSupport, nearestResistance };
}

// Legacy alias check for tests: DecisionZonesPanel
export const DecisionZonesPanel = DecisionAreasPanel;

export function DecisionAreasPanel({ zones, rawLevels }: { zones: unknown; rawLevels: unknown }) {
  const [showRaw, setShowRaw] = React.useState(false);
  const zoneRows = safeArray(zones as any[]) as any[];
  const rawRows = safeArray(rawLevels as any[]) as any[];

  if (!zoneRows.length && !rawRows.length) {
    return (
      <section data-decision-zones className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-left">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">DECISION AREAS</div>
        <p className="mt-1 text-[10px] text-slate-500 italic">No consolidated decision zones are available for this session.</p>
      </section>
    );
  }

  if (!zoneRows.length && rawRows.length > 0) {
    return (
      <section data-decision-zones className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-left space-y-2">
        <div className="flex items-center justify-between border-b border-slate-800/60 pb-1.5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">DECISION AREAS</div>
          <button onClick={() => setShowRaw(!showRaw)} className="text-[9px] font-mono text-cyan-400 hover:underline">
            {showRaw ? "Hide raw levels" : `View raw levels & provenance (${rawRows.length}) ⓘ`}
          </button>
        </div>
        <p className="text-[10px] text-slate-400 italic">No consolidated decision zones are available for this session.</p>
        {showRaw && <KeyLevelsPanel levels={rawLevels} />}
      </section>
    );
  }

  return (
    <section data-decision-zones className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 text-left space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
        <div>
          <div className="text-[10px] font-black uppercase tracking-wider text-cyan-400">DECISION AREAS</div>
          <p className="text-[9px] text-slate-500 font-mono mt-0.5">{zoneRows.length} decision zones derived from backend canonical levels</p>
        </div>
        <button onClick={() => setShowRaw(!showRaw)} className="text-[9px] font-mono text-cyan-400 hover:underline border border-slate-800 bg-slate-900 px-2 py-1 rounded">
          {showRaw ? "Hide raw levels" : `View raw levels & provenance (${rawRows.length}) ⓘ`}
        </button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {zoneRows.map((zone: any) => {
          const roleTone = zone.role === "SUPPORT"
            ? "border-emerald-800/80 bg-emerald-950/30 text-emerald-300"
            : zone.role === "RESISTANCE"
            ? "border-rose-800/80 bg-rose-950/30 text-rose-300"
            : "border-cyan-800/80 bg-cyan-950/30 text-cyan-300";

          const roleLabel = zone.role === "SUPPORT" ? "Support Zone" : zone.role === "RESISTANCE" ? "Resistance Zone" : "Reference Level";

          return (
            <div key={zone.zone_id} className={`rounded-lg border p-3 text-[10px] ${roleTone}`}>
              <div className="flex items-center justify-between font-bold border-b border-current/20 pb-1">
                <span className="font-mono text-xs text-white">{zone.display_range}</span>
                <span className="text-[9px] uppercase px-1.5 py-0.5 rounded border border-current font-semibold">{roleLabel}</span>
              </div>
              <div className="mt-2 text-[10px] opacity-90 leading-tight">{zone.rationale}</div>
              {safeArray(zone.contributing_levels).length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1 text-[8px] opacity-75 border-t border-current/15 pt-1.5">
                  {safeArray(zone.contributing_levels).map((lvl: any, idx: number) => (
                    <span key={idx} className="bg-slate-950/80 px-1.5 py-0.5 rounded font-mono border border-current/20">
                      {formatNumber(lvl.value, 2)} ({mapTraderEnum(lvl.origin)})
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {showRaw && (
        <div data-provenance-details className="mt-3 border-t border-slate-800 pt-3">
          <KeyLevelsPanel levels={rawLevels} />
        </div>
      )}
    </section>
  );
}
