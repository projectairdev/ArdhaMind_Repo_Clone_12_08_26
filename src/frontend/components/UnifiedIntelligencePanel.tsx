import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { formatNumber, safeArray, safeString } from "../utils/safeHelpers";
import { mapTraderEnum } from "../utils/traderTerminology";
import { DecisionAreasPanel, DecisionZonesPanel, EvidenceList, ExplicitState, KeyLevelsPanel, ScenarioCard, SemanticBadge, nearestDecisionLevels } from "./intelligence/CanonicalPresentation";

function useCanonicalIntelligence() {
  const { canonicalState } = useWorkstationState();
  return { canonicalState: canonicalState as any, intelligence: canonicalState?.unified_intelligence as any };
}

function UnavailableView({ name }: { name: string }) {
  return <section data-unified-intelligence={name} className="rounded-xl border border-amber-900/50 bg-amber-950/15 p-4 text-left text-xs text-amber-300">Unified canonical intelligence is not yet available.</section>;
}

function AnalysisScenarioSummary({ scenarios }: { scenarios: any[] }) {
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
  const zones = safeArray(intelligence.decision_zones) as any[];
  const gift = canonicalState?.macro_intelligence?.quotes?.GIFT_NIFTY;
  const breadth = canonicalState?.market_data?.breadth;
  const options = canonicalState?.option_intelligence;
  const volatility = canonicalState?.macro_intelligence?.india_vix;
  const news = canonicalState?.news_intelligence;
  const context = [
    ["Expected Opening", intelligence.signals?.opening?.state, signalEvidence(intelligence.signals?.opening)],
    ["GIFT Nifty", gift ? "AVAILABLE" : "UNAVAILABLE", gift ? `${formatNumber(gift.value, 2)} · ${safeString(gift.freshness_status || gift.freshness)}` : "No eligible GIFT observation."],
    ["Global Cues", intelligence.signals?.global?.state, signalEvidence(intelligence.signals?.global)],
    ["FII / DII Positioning", intelligence.signals?.institutional?.state, signalEvidence(intelligence.signals?.institutional)],
    ["Breadth", breadth?.status, breadth?.coverage ? `${safeString(breadth.coverage.valid)} / ${safeString(breadth.coverage.expected)} constituents` : "Breadth unavailable."],
    ["Options", options?.status, options?.snapshot_timestamp ? `Observed ${safeString(options.snapshot_timestamp)}` : "Options snapshot unavailable."],
    ["Volatility", volatility?.status || (volatility?.value != null ? "AVAILABLE" : "UNAVAILABLE"), volatility?.value != null ? `India VIX ${formatNumber(volatility.value, 2)}` : "Volatility context unavailable."],
    ["News & Event Risk", news?.status, `${safeArray(news?.items).length} verified news items`],
  ];
  return <section data-unified-intelligence="PRE_MARKET" data-intelligence-view="next-session-setup" data-intelligence-engine={intelligence.engine} className="space-y-4 rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-left">
    <div className="flex flex-wrap items-center justify-between gap-2"><div><div className="text-[9px] font-black uppercase tracking-[.18em] text-cyan-400">Tomorrow's Market Setup</div><h3 className="mt-1 text-sm font-bold text-white">Pre-Market Setup</h3></div><SemanticBadge value={intelligence.readiness} kind="readiness"/></div>
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{context.map(([title, state, reason]) => <ExplicitState key={String(title)} title={String(title)} state={state} reason={reason}/>)}</div>
    <AnalysisScenarioSummary scenarios={scenarios}/><div className="grid gap-3 md:grid-cols-2"><EvidenceList title="What Supports the Setup" items={intelligence.confirming_signals} toneClass="text-emerald-300"/><EvidenceList title="What Could Break the Setup" items={[...safeArray(intelligence.opposing_signals), ...safeArray(intelligence.risk?.reasons)]} toneClass="text-rose-300"/></div>
  </section>;
}

export function TodaysAnalysisSynthesis() {
  const { canonicalState, intelligence } = useCanonicalIntelligence();
  if (!intelligence) return <UnavailableView name="TODAYS_ANALYSIS"/>;
  const scenarios = safeArray(intelligence.scenarios) as any[];
  const change = intelligence.change_intelligence || {};
  const riskReason = safeArray(intelligence.risk?.reasons).join(" · ") || "No elevated risk factors reported.";
  const session = canonicalState?.market_session?.status || intelligence.session?.status || intelligence.mode;
  const zones = safeArray(intelligence.decision_zones) as any[];
  const evidenceItems = safeArray(intelligence.evidence_items) as any[];
  const confirmingEv = evidenceItems.filter(e => e.stance === "CONFIRMING");
  const opposingEv = evidenceItems.filter(e => e.stance === "OPPOSING");
  const neutralEv = evidenceItems.filter(e => e.stance === "NEUTRAL" || e.stance === "UNAVAILABLE");

  const spot = canonicalState?.market_data?.current_spot || null;
  const { nearestSupport, nearestResistance } = nearestDecisionLevels(zones, spot);
  const primaryScenario = scenarios.find((s: any) => safeString(s.priority).toUpperCase().includes("PRIMARY")) || scenarios[0];
  const primaryScenarioName = primaryScenario ? mapTraderEnum(primaryScenario.name) : "UNAVAILABLE";

  const rawChangeStatus = change.status || "UNAVAILABLE";
  const changeStatus = rawChangeStatus === "UNAVAILABLE" ? "PREVIOUS_COMPARISON_NOT_AVAILABLE_YET" : rawChangeStatus;
  const changeReason = rawChangeStatus === "UNAVAILABLE" ? "Previous comparison not available yet for this refresh snapshot." : (change.reason || "Change intelligence is unavailable.");

  return (
    <section data-unified-intelligence="TODAYS_ANALYSIS" data-intelligence-view="full-session-synthesis" data-intelligence-engine={intelligence.engine} className="space-y-4 rounded-xl border border-cyan-900/50 bg-slate-950/70 p-5 text-left">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div data-analysis-session-heading className="text-[10px] font-black uppercase tracking-[.2em] text-cyan-400">
            {analysisSessionHeading(session)}
          </div>
          <h3 className="mt-1 text-sm font-bold text-white">TODAY'S NIFTY VIEW — WHAT DROVE THE MARKET AND WHY</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <SemanticBadge value={intelligence.readiness} kind="readiness"/>
          <SemanticBadge value={intelligence.alignment}/>
          <SemanticBadge value={intelligence.market_regime}/>
          <SemanticBadge value={intelligence.confidence} kind="confidence"/>
          <SemanticBadge value={`${safeString(intelligence.risk?.state)}_RISK`} kind="risk"/>
        </div>
      </div>

      <p className="text-xs leading-relaxed text-slate-300">{safeString(intelligence.explanation)}</p>

      {/* WHY THIS VIEW — EXPLANATORY EVIDENCE */}
      <div className="grid gap-3 md:grid-cols-3">
        {/* SUPPORTIVE EVIDENCE */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 border-b border-slate-800/60 pb-1.5 mb-2">
            What Supports This View
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
          ) : (
            <EvidenceList title="What Supports This View" items={intelligence.confirming_signals} toneClass="text-emerald-300"/>
          )}
        </div>

        {/* CAUTION / OPPOSING EVIDENCE */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <div className="text-[10px] font-bold uppercase tracking-wider text-amber-400 border-b border-slate-800/60 pb-1.5 mb-2">
            What Goes Against It
          </div>
          {opposingEv.length || neutralEv.length ? (
            <ul className="space-y-2 text-[10px] text-amber-200">
              {[...opposingEv, ...neutralEv].map((item: any) => (
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
          ) : (
            <EvidenceList title="What Goes Against It" items={intelligence.opposing_signals} toneClass="text-rose-300"/>
          )}
        </div>

        {/* WHAT CHANGED */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <ExplicitState title="What Changed Since the Previous View?" state={changeStatus} reason={changeReason}/>
        </div>
      </div>

      {/* COMPACT KEY STRUCTURE & SCENARIO CONTEXT REFERENCES */}
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 font-mono">
          <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 border-b border-slate-800/60 pb-1.5 mb-2">
            Key Structure
          </div>
          <div className="space-y-1 text-xs">
            <div><span className="text-slate-400">Support:</span> <span className="font-semibold text-emerald-400">{nearestSupport ? nearestSupport.display_range : "UNAVAILABLE"}</span></div>
            <div><span className="text-slate-400">Resistance:</span> <span className="font-semibold text-rose-400">{nearestResistance ? nearestResistance.display_range : "UNAVAILABLE"}</span></div>
            <div className="mt-2 pt-2 border-t border-slate-800/60 text-[10px] text-slate-500 font-sans font-normal">
              View full Decision Areas in: <br />
              <span className="text-cyan-400 font-bold">NIFTY Live → Price & Trend</span>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 font-mono">
          <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 border-b border-slate-800/60 pb-1.5 mb-2">
            Scenario Context
          </div>
          <div className="space-y-1 text-xs">
            <div>
              <span className="text-slate-400">Primary scenario:</span>{" "}
              <span className="font-semibold text-white">{primaryScenarioName}</span>
              <span className="ml-2 px-1.5 py-0.5 rounded text-[8px] font-bold border border-slate-700 bg-slate-800/50 text-slate-400 font-sans font-mono">
                PREVIOUS SESSION — FINALIZED
              </span>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800/60 text-[10px] text-slate-500 font-sans font-normal">
              See active monitoring in: <br />
              <span className="text-cyan-400 font-bold">Live Assistant</span>
            </div>
          </div>
        </div>
      </div>
      <ExplicitState title="What Could Change This View" state={intelligence.risk?.state} reason={riskReason}/>
    </section>
  );
}

export function LiveAssistantExplanationView() {
  const { canonicalState, intelligence } = useCanonicalIntelligence();
  if (!intelligence) return <UnavailableView name="LIVE_ASSISTANT"/>;

  const isClosed = Boolean(canonicalState?.market_session?.is_closed || intelligence.session === "CLOSED" || intelligence.mode === "SESSION_REVIEW");
  const outlook = intelligence.outlook || {};
  const preferredSetup = outlook.preferred_setup || {
    title: "No Clear Preferred Setup",
    description: "Wait for opening range and market breadth confirmation.",
  };
  const atTheOpenRaw = safeArray(outlook.at_the_open);
  const atTheOpen = atTheOpenRaw.map((x: any) => typeof x === "string" ? x : safeString(x?.item));
  const zones = safeArray(intelligence.decision_zones) as any[];
  const scenarios = safeArray(intelligence.scenarios) as any[];
  const evidenceItems = safeArray(intelligence.evidence_items) as any[];
  const confirmingEv = evidenceItems.filter(e => e.stance === "CONFIRMING");
  const opposingEv = evidenceItems.filter(e => e.stance === "OPPOSING" || e.stance === "NEUTRAL" || e.stance === "UNAVAILABLE");
  const change = intelligence.change_intelligence || {};
  const missing = safeArray(intelligence.evidence_completeness?.critical_missing).join(" · ") || safeArray(intelligence.unavailable_or_ineligible_signals).join(" · ") || "No critical missing data reported for this session mode.";

  const spot = canonicalState?.market_data?.current_spot || null;
  const { nearestSupport, nearestResistance } = nearestDecisionLevels(zones, spot);

  return (
    <section data-unified-intelligence="LIVE_ASSISTANT" data-intelligence-view="explanation-console" data-intelligence-engine={intelligence.engine} className="space-y-4 rounded-xl border border-slate-800 bg-slate-950/70 p-5 text-left">
      <div>
        <div className="text-[9px] font-black uppercase tracking-[.18em] text-cyan-400">
          {isClosed ? "NEXT SESSION WATCH — WHAT TO WATCH NEXT" : "LIVE MARKET MONITOR — WHAT TO WATCH NOW"}
        </div>
        <h3 className="mt-1 text-sm font-bold text-white">Understand ArdhaMind's View</h3>
        <p className="mt-1 text-xs text-slate-400">
          {isClosed
            ? "Live confirmation is paused while the market is closed. These are the conditions ArdhaMind will monitor when the next session begins."
            : "Live market monitoring active. Watching opening range, breadth confirmation, and decision zones."}
        </p>
      </div>

      <div data-canonical-assistant-answers className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        <ExplicitState title="Current Market State" state={intelligence.alignment} reason={safeString(intelligence.market_regime).replaceAll("_", " ")}/>
        <ExplicitState title="Why?" state={intelligence.confidence} reason={safeString(intelligence.explanation)}/>
        <ExplicitState title="What is the Risk?" state={intelligence.risk?.state} reason={safeArray(intelligence.risk?.reasons).join(" · ") || "No elevated risk factors reported."}/>
        <ExplicitState title="What Changed?" state={change.status || "UNAVAILABLE"} reason={change.reason || "Previous comparison not available yet."}/>
        <ExplicitState title="What Data is Missing?" state={missing.startsWith("No critical") ? "READY" : "PARTIAL"} reason={missing}/>
      </div>

      {/* BEST SUPPORTED MARKET BEHAVIOR */}
      <div className="rounded-lg border border-cyan-800/70 bg-cyan-950/20 p-4">
        <div className="text-[10px] font-black uppercase tracking-wider text-cyan-400">BEST-SUPPORTED MARKET BEHAVIOR</div>
        <h4 className="mt-1 text-sm font-bold text-white">{preferredSetup.title}</h4>
        <p className="mt-1 text-xs leading-relaxed text-slate-300">{preferredSetup.description}</p>
      </div>

      {/* WHAT TO WATCH NEXT */}
      {atTheOpen.length > 0 && (
        <div data-watchlist-conditions className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
          <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 mb-2">WHAT TO WATCH NEXT</div>
          <ul className="space-y-1.5 text-xs text-slate-300 font-mono">
            {atTheOpen.map((item: string, idx: number) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-cyan-400 font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* EVIDENCE BREAKDOWN */}
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 mb-2">What Supports This View?</div>
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
          ) : (
            <EvidenceList title="What Supports This View?" items={intelligence.confirming_signals} toneClass="text-emerald-300"/>
          )}
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <div className="text-[10px] font-bold uppercase tracking-wider text-amber-400 mb-2">What Goes Against It?</div>
          {opposingEv.length ? (
            <ul className="space-y-2 text-[10px] text-amber-200">
              {opposingEv.map((item: any) => (
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
          ) : (
            <EvidenceList title="What Goes Against It?" items={intelligence.opposing_signals} toneClass="text-rose-300"/>
          )}
        </div>
      </div>

      {/* COMPACT NEAREST LEVELS */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 font-mono">
        <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 mb-2">Nearest Support / Resistance</div>
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-slate-400 block text-[9px] uppercase">Nearest Support</span>
            <span className="font-semibold text-emerald-400 text-sm mt-0.5 block">{nearestSupport ? nearestSupport.display_range : "UNAVAILABLE"}</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[9px] uppercase">Nearest Resistance</span>
            <span className="font-semibold text-rose-400 text-sm mt-0.5 block">{nearestResistance ? nearestResistance.display_range : "UNAVAILABLE"}</span>
          </div>
        </div>
        <div className="mt-3 pt-2 border-t border-slate-800/60 text-[9px] text-slate-500 font-sans font-normal">
          Source: <span className="text-cyan-400 font-semibold">NIFTY Live → Price & Trend</span>
        </div>
      </div>

      <AnalysisScenarioSummary scenarios={scenarios}/>

      <div className="text-[9px] text-slate-600 border-t border-slate-800/60 pt-2">
        Invalidation conditions remain inside each scenario · Human decision required · Read only decision support
      </div>
    </section>
  );
}
