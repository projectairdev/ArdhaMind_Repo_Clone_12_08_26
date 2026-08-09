import React from "react";
import { AlertTriangle, CheckCircle2, ChevronRight, XCircle } from "lucide-react";
import { safeArray, safeString } from "../../utils/safeHelpers";
import { mapTraderEnum } from "../../utils/traderTerminology";
import { DecisionZonesPanel, ScenarioCard, SemanticBadge } from "./CanonicalPresentation";

interface OutlookCardProps {
  intelligence: any;
  macro?: any;
}

export function TomorrowsOutlookCard({ intelligence, macro }: OutlookCardProps) {
  if (!intelligence) return null;

  const outlook = intelligence.outlook || {};
  const relation = safeString(outlook.target_session_relation || "TOMORROW");
  const dateStr = outlook.target_session_date;

  let targetTitle = "Tomorrow's NIFTY Outlook";
  if (relation === "TODAY") {
    targetTitle = "Today's NIFTY Outlook";
  } else if (relation === "NEXT_TRADING_SESSION") {
    targetTitle = dateStr ? `${dateStr} NIFTY Outlook` : "Next Session NIFTY Outlook";
  } else if (dateStr) {
    targetTitle = `${dateStr} NIFTY Outlook`;
  }

  const overallView = safeString(outlook.overall_view || "No Clear Setup");
  const expectedOpening = safeString(outlook.expected_opening || "Opening Indication Unavailable");
  const conviction = safeString(outlook.conviction || mapTraderEnum(intelligence.confidence, "confidence"));
  const riskLabel = safeString(outlook.risk_label || mapTraderEnum(intelligence.risk?.state, "risk"));
  const preferredSetup = outlook.preferred_setup || {
    scenario_id: null,
    title: "No Clear Preferred Setup",
    description: "Wait for opening range and market breadth confirmation.",
  };
  const keyConcerns = safeArray(outlook.key_concerns?.length ? outlook.key_concerns : intelligence.risk?.reasons);
  const mainConcern = safeString(keyConcerns[0] || "No major concern reported.");

  const evidenceItems = safeArray(intelligence.evidence_items) as any[];
  const hasEvidenceItems = evidenceItems.length > 0;
  const confirmingEv = evidenceItems.filter(e => e.stance === "CONFIRMING");
  const opposingEv = evidenceItems.filter(e => e.stance === "OPPOSING");
  const neutralEv = evidenceItems.filter(e => e.stance === "NEUTRAL" || e.stance === "MIXED");

  const supportsFallback = hasEvidenceItems ? [] : safeArray(outlook.supports?.length ? outlook.supports : intelligence.confirming_signals);
  const cautionFallback = hasEvidenceItems ? [] : safeArray(outlook.caution?.length ? outlook.caution : keyConcerns);
  const opposesFallback = hasEvidenceItems ? [] : safeArray(outlook.opposes?.length ? outlook.opposes : intelligence.opposing_signals);

  const atTheOpenRaw = safeArray(outlook.at_the_open);
  const atTheOpen = atTheOpenRaw.map((x: any) => typeof x === "string" ? x : safeString(x?.item));
  const scenarios = safeArray(intelligence.scenarios) as any[];
  const decisionZones = safeArray(intelligence.decision_zones) as any[];
  const rawLevels = safeArray(intelligence.key_levels) as any[];

  // Tone color helper for overall view
  const overallTone = overallView.includes("Positive")
    ? "border-emerald-800 bg-emerald-950/50 text-emerald-300"
    : overallView.includes("Negative")
    ? "border-rose-800 bg-rose-950/50 text-rose-300"
    : overallView.includes("Mixed")
    ? "border-amber-800 bg-amber-950/50 text-amber-300"
    : "border-slate-800 bg-slate-900 text-slate-300";

  return (
    <section data-tomorrows-outlook className="space-y-4 rounded-xl border border-cyan-900/60 bg-slate-950/80 p-5 text-left">
      {/* LEVEL 1 — ANSWER */}
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
          <div>
            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-400">
              {targetTitle.toUpperCase()}
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <span className={`inline-flex rounded border px-2.5 py-1 text-xs font-bold ${overallTone}`}>
                {overallView}
              </span>
              <SemanticBadge value={conviction} kind="confidence" />
              <SemanticBadge value={riskLabel} kind="risk" />
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-right">
            <span className="block text-[9px] font-bold uppercase tracking-wider text-slate-500">Expected Opening</span>
            <span className="mt-0.5 block text-xs font-bold text-cyan-300">{expectedOpening}</span>
          </div>
        </div>

        {/* Preferred Setup to Watch */}
        <div data-preferred-setup className="mt-4 rounded-lg border border-cyan-800/70 bg-cyan-950/20 p-4">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-wider text-cyan-400">
            <ChevronRight size={14} className="text-cyan-400" />
            <span>PREFERRED SETUP TO WATCH</span>
          </div>
          <h4 className="mt-1 text-sm font-bold text-white">{preferredSetup.title}</h4>
          <p className="mt-1 text-xs leading-relaxed text-slate-300">{preferredSetup.description}</p>
          {mainConcern && (
            <div className="mt-2 text-[11px] text-amber-300 flex items-center gap-1.5 font-medium">
              <AlertTriangle size={13} className="text-amber-400 shrink-0" />
              <span><strong className="text-amber-200">Main Concern:</strong> {mainConcern}</span>
            </div>
          )}
        </div>
      </div>

      {/* LEVEL 2 — WHY (EXPLANATORY EVIDENCE BREAKDOWN WITH TEMPORAL CONTEXT) */}
      <div className="grid gap-3 md:grid-cols-3">
        {/* SUPPORTS */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-emerald-400 border-b border-slate-800/60 pb-1.5 mb-2">
            <CheckCircle2 size={13} />
            <span>SUPPORTS THE VIEW</span>
          </div>
          {confirmingEv.length ? (
            <ul className="space-y-2 text-[10px] text-emerald-200">
              {confirmingEv.map((item: any) => (
                <li key={item.evidence_id} className="flex flex-col gap-0.5 border-b border-emerald-950/40 pb-1.5 last:border-none">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-emerald-300">{item.category_label}</span>
                    <span className="text-[8px] px-1 py-0.2 rounded border border-emerald-800/60 bg-emerald-950/40 text-emerald-400">
                      {mapTraderEnum(item.temporal_relation)}
                    </span>
                  </div>
                  <span className="text-slate-300">{item.summary}</span>
                </li>
              ))}
            </ul>
          ) : supportsFallback.length ? (
            <ul className="space-y-1.5 text-[10px] text-emerald-200">
              {supportsFallback.map((item: any, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-emerald-400 font-bold">•</span>
                  <span>{mapTraderEnum(item)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-[10px] text-slate-500 italic">No strong confirming evidence.</p>
          )}
        </div>

        {/* CAUTION / MIXED */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-amber-400 border-b border-slate-800/60 pb-1.5 mb-2">
            <AlertTriangle size={13} />
            <span>CAUTION / MIXED</span>
          </div>
          {neutralEv.length ? (
            <ul className="space-y-2 text-[10px] text-amber-200">
              {neutralEv.map((item: any) => (
                <li key={item.evidence_id} className="flex flex-col gap-0.5 border-b border-amber-950/40 pb-1.5 last:border-none">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-300">{item.category_label}</span>
                    <span className="text-[8px] px-1 py-0.2 rounded border border-amber-800/60 bg-amber-950/40 text-amber-400">
                      {mapTraderEnum(item.temporal_relation)}
                    </span>
                  </div>
                  <span className="text-slate-300">{item.summary}</span>
                </li>
              ))}
            </ul>
          ) : cautionFallback.length ? (
            <ul className="space-y-1.5 text-[10px] text-amber-200">
              {cautionFallback.map((item: any, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-amber-400 font-bold">•</span>
                  <span>{mapTraderEnum(item)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-[10px] text-slate-500 italic">No specific caution factors.</p>
          )}
        </div>

        {/* OPPOSES */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-rose-400 border-b border-slate-800/60 pb-1.5 mb-2">
            <XCircle size={13} />
            <span>GOES AGAINST THE VIEW</span>
          </div>
          {opposingEv.length ? (
            <ul className="space-y-2 text-[10px] text-rose-200">
              {opposingEv.map((item: any) => (
                <li key={item.evidence_id} className="flex flex-col gap-0.5 border-b border-rose-950/40 pb-1.5 last:border-none">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-rose-300">{item.category_label}</span>
                    <span className="text-[8px] px-1 py-0.2 rounded border border-rose-800/60 bg-rose-950/40 text-rose-400">
                      {mapTraderEnum(item.temporal_relation)}
                    </span>
                  </div>
                  <span className="text-slate-300">{item.summary}</span>
                </li>
              ))}
            </ul>
          ) : opposesFallback.length ? (
            <ul className="space-y-1.5 text-[10px] text-rose-200">
              {opposesFallback.map((item: any, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-rose-400 font-bold">•</span>
                  <span>{mapTraderEnum(item)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-[10px] text-slate-500 italic">No opposing evidence reported.</p>
          )}
        </div>
      </div>

      {/* LEVEL 3 — PLAN (SCENARIOS, WATCHLIST, DECISION ZONES & LEVELS) */}
      <div className="space-y-3 border-t border-slate-800/80 pt-3">
        {/* Scenarios */}
        {scenarios.length > 0 && (
          <div>
            <div className="mb-2 text-[10px] font-bold uppercase text-slate-400">Market Scenarios</div>
            <div className="grid gap-3 md:grid-cols-2">
              {scenarios.map((sc: any) => (
                <ScenarioCard key={sc.name} scenario={sc} />
              ))}
            </div>
          </div>
        )}

        {/* At the Open Watchlist */}
        {atTheOpen.length > 0 && (
          <div data-at-the-open-watchlist className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 text-xs">
            <div className="text-[10px] font-bold uppercase text-cyan-400 mb-2">At the Open — Watch These</div>
            <ol className="list-decimal list-inside space-y-1 text-slate-300 font-mono text-[11px]">
              {atTheOpen.map((item: string, idx: number) => (
                <li key={idx} className="leading-snug">{item}</li>
              ))}
            </ol>
          </div>
        )}

        {/* Key Decision Zones & Levels */}
        <DecisionZonesPanel zones={decisionZones} rawLevels={rawLevels} />
      </div>
    </section>
  );
}
