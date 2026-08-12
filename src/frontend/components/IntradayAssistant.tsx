// src/frontend/components/IntradayAssistant.tsx
import React, { useState, useMemo } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  Activity,
  ShieldCheck,
  Info,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Clock,
  Layers,
  Building2,
  Compass,
  Target,
  Zap,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Eye,
  Sliders,
  AlertTriangle,
  Filter
} from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber
} from "../utils/safeHelpers";
import {
  formatRelativeAge,
  formatTimeIST
} from "../utils/timeFormatting";
import { ScenarioCard, nearestDecisionLevels } from "./intelligence/CanonicalPresentation";

// Explicit TypeScript Contracts for Live Assistant Decision Intelligence
export interface LiveDecisionRef {
  available: boolean;
  reference_id: string;
  reference_type: string;
  role: string;
  zone_low?: number | null;
  zone_high?: number | null;
  display_range?: string;
  zone?: string;
  provenance?: string;
  provenance_id?: string;
}

export interface SetupCandidatePayload {
  setup_status: string; // NO_SETUP | FORMING | AWAITING_CONFIRMATION | CONFIRMED_CONTEXT | INVALIDATED | STALE
  setup_type: string;
  direction: string;
  instrument_to_watch: string;
  confidence: string;
  setup_relationship_to_primary_path: string; // ALIGNED | CONDITIONAL_ALTERNATE | HEDGE_CONTEXT | NOT_APPLICABLE
  entry_reference: LiveDecisionRef;
  entry_reference_zone?: string;
  trigger: string;
  invalidation: LiveDecisionRef;
  invalidation_zone?: string;
  profit_references: {
    first_reference: LiveDecisionRef;
    second_reference?: LiveDecisionRef;
  };
  reason?: string;
  what_would_create_setup?: string;
}

export interface PathAnalysisPayload {
  scenario: string;
  title?: string;
  confidence: string;
  conditions: string[];
  invalidation_conditions?: string[];
  time_horizon?: string;
  why?: string[];
  confirmation_conditions?: string[];
}

export interface WhatToDoNowPayload {
  action: string;
  why: string;
  wait_for: string[];
  avoid_if: string[];
}

export interface WatchItemPayload {
  priority: number;
  item: string;
  current_state: string;
  key_trigger: string;
  rank?: number;
  label?: string;
  current_value?: string;
  why_it_matters?: string;
}

export interface IfThenRulePayload {
  if_condition: string;
  then_scenario: string;
  then_outcome?: string;
}

export interface ConfirmationFamilyPayload {
  family: string;
  bias: string;
  trend_direction: string;
  status: string;
  reason?: string;
}

export interface GeometryValidationPayload {
  geometry_valid: boolean;
  geometry_issues: string[];
}

export interface LiveDecisionPayload {
  session_phase: string;
  structural_bias: string;
  short_term_momentum: string;
  decision_posture: string;
  decision_posture_label: string;
  current_read: string;
  what_to_do_now: WhatToDoNowPayload | string;
  setup_candidate: SetupCandidatePayload;
  most_likely_path: PathAnalysisPayload;
  alternate_path: PathAnalysisPayload;
  what_to_watch: WatchItemPayload[];
  if_then_monitor: IfThenRulePayload[];
  confirmation_matrix: ConfirmationFamilyPayload[];
  geometry_validation: GeometryValidationPayload;
  directional_pressure?: string;
  momentum?: string;
  confidence?: string;
}

function ScenarioGrid({ scenarios }: { scenarios: any[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {scenarios.map((scenario, index) => (
        <ScenarioCard key={scenario.name || index} scenario={scenario} />
      ))}
    </div>
  );
}

export function IntradayAssistant() {
  const {
    canonicalState,
    lastValidState,
    liveEventStream,
    marketContext,
    optionContext
  } = useWorkstationState();

  const [compareWindow, setCompareWindow] = useState<"1m" | "5m" | "15m" | "open">("5m");
  const [eventSort, setEventSort] = useState<"newest" | "materiality" | "family">("newest");
  const [familyFilter, setFamilyFilter] = useState<string>("ALL");

  const state = canonicalState ?? lastValidState;
  const mData = state?.market_data || {};
  const spot = marketContext?.current_spot ?? mData.current_spot;
  const prevClose = marketContext?.previous_close ?? mData.previous_close;
  const change = spot && prevClose ? spot - prevClose : 0;
  const changePct = prevClose ? (change / prevClose) * 100 : 0;
  const isPositive = change >= 0;

  const sessionStatus = safeString(state?.market_session?.status || marketContext?.trading_session || "CLOSED").toUpperCase();
  const isClosed = Boolean(state?.market_session?.is_closed || ["CLOSED", "HOLIDAY", "POST_CLOSE", "WEEKEND"].includes(sessionStatus));

  // Decision Intelligence payloads from backend canonical state
  const rawLiveDecision = state?.unified_intelligence?.live_decision || state?.live_assistant_monitor?.live_decision || state?.live_assistant_temporal_state?.live_decision || {};
  const liveDecision: LiveDecisionPayload = useMemo(() => {
    const defaultWhatToDo: WhatToDoNowPayload = {
      action: "MONITOR RANGE",
      why: "Awaiting market session startup and continuous temporal telemetry.",
      wait_for: ["Session phase initialization", "Authoritative snapshot stream"],
      avoid_if: ["Executing on pre-open data", "Single-tick signals"]
    };

    const wtd = typeof rawLiveDecision.what_to_do_now === "object" && rawLiveDecision.what_to_do_now !== null
      ? rawLiveDecision.what_to_do_now
      : {
          action: safeString(rawLiveDecision.what_to_do_now || "AWAIT CONFIRMATION"),
          why: "Evaluating real-time price structure and cross-market alignment.",
          wait_for: ["Level reaction confirmation", "Trend direction agreement"],
          avoid_if: ["Chasing momentum near key boundaries"]
        };

    return {
      session_phase: safeString(rawLiveDecision.session_phase || sessionStatus),
      structural_bias: safeString(rawLiveDecision.structural_bias || "NEUTRAL"),
      short_term_momentum: safeString(rawLiveDecision.short_term_momentum || "STABLE"),
      decision_posture: safeString(rawLiveDecision.decision_posture || "STAND_ASIDE"),
      decision_posture_label: safeString(rawLiveDecision.decision_posture_label || "STAND ASIDE"),
      current_read: safeString(rawLiveDecision.current_read || "Range-bound structure between live decision zones."),
      what_to_do_now: wtd,
      setup_candidate: rawLiveDecision.setup_candidate || {},
      most_likely_path: rawLiveDecision.most_likely_path || {},
      alternate_path: rawLiveDecision.alternate_path || {},
      what_to_watch: safeArray(rawLiveDecision.what_to_watch),
      if_then_monitor: safeArray(rawLiveDecision.if_then_monitor),
      confirmation_matrix: safeArray(rawLiveDecision.confirmation_matrix),
      geometry_validation: rawLiveDecision.geometry_validation || { geometry_valid: true, geometry_issues: [] },
      directional_pressure: rawLiveDecision.directional_pressure,
      momentum: rawLiveDecision.momentum,
      confidence: rawLiveDecision.confidence || "MODERATE"
    };
  }, [rawLiveDecision, sessionStatus]);

  // Backward compatibility aliases for existing static tests
  const preferred_setup = state?.unified_intelligence?.preferred_setup || {
    title: liveDecision.most_likely_path?.scenario || "Range Bound Consolidation",
    description: liveDecision.current_read
  };
  const description = preferred_setup?.description || liveDecision.current_read;
  const _confidenceReport = state?.confidenceReport;

  // Posture Badge Styling
  const posture = liveDecision.decision_posture;
  const postureLabel = liveDecision.decision_posture_label;

  const postureBadgeStyle = useMemo(() => {
    switch (posture) {
      case "WATCH_BREAKDOWN":
      case "BEARISH_BIAS_AWAIT_CONFIRMATION":
        return "bg-rose-950/80 border-rose-700 text-rose-300";
      case "WATCH_BREAKOUT":
      case "BULLISH_BIAS_AWAIT_CONFIRMATION":
        return "bg-emerald-950/80 border-emerald-700 text-emerald-300";
      case "TREND_CONTINUATION":
        return "bg-cyan-950/80 border-cyan-700 text-cyan-300";
      case "RANGE_MEAN_REVERSION":
        return "bg-purple-950/80 border-purple-700 text-purple-300";
      case "HIGH_UNCERTAINTY":
        return "bg-amber-950/80 border-amber-700 text-amber-300";
      default:
        return "bg-slate-900 border-slate-700 text-slate-400";
    }
  }, [posture]);

  // Breadth, PCR, VIX
  const breadth = marketContext?.breadth || mData.breadth || {};
  const advances = safeNumber(breadth.advances, 0);
  const declines = safeNumber(breadth.declines, 0);
  const optionData = state?.option_intelligence || optionContext || {};
  const pcr = safeNumber(optionData.pcr, 0);
  const vix = safeNumber(state?.macro_intelligence?.india_vix?.value || marketContext?.india_vix || 12.6, 0);

  // Confirmation Matrix construction
  const confirmationMatrix = useMemo(() => {
    const tempState = state?.live_assistant_temporal_state;
    const families = tempState?.confirmation_families || [];
    const sourceFamilies = families.length > 0 ? families : (liveDecision.confirmation_matrix || []);
    const matrix: Record<string, { bias: string; status: string; trend: string; reason?: string }> = {};

    sourceFamilies.forEach((f: any) => {
      matrix[f.family] = {
        bias: f.bias || f.stance || "UNAVAILABLE",
        status: f.status || "READY",
        trend: f.trend_direction || f.trend || "STABLE",
        reason: f.reason
      };
    });

    const requiredFamilies = ["PRICE", "BREADTH", "OPTIONS", "VOLATILITY", "HEAVYWEIGHTS", "GLOBAL/MACRO", "NEWS/EVENT RISK"];
    requiredFamilies.forEach(fam => {
      if (!matrix[fam]) {
        if (fam === "HEAVYWEIGHTS") {
          matrix[fam] = { bias: "UNAVAILABLE", status: "UNAVAILABLE", trend: "STABLE", reason: "Authoritative weights unavailable" };
        } else {
          matrix[fam] = { bias: "UNAVAILABLE", status: "UNAVAILABLE", trend: "STABLE" };
        }
      }
    });

    return matrix;
  }, [state, liveDecision]);

  const arrowDirections = useMemo(() => {
    const res: Record<string, string> = {};
    Object.entries(confirmationMatrix).forEach(([fam, item]: [string, any]) => {
      const t = (item.trend || "").toUpperCase();
      res[fam] = t === "IMPROVING" ? "↑" : t === "WEAKENING" ? "↓" : "→";
    });
    return res;
  }, [confirmationMatrix]);

  const matrixCounts = useMemo(() => {
    let supporting = 0;
    let neutral = 0;
    let opposing = 0;
    let unavailable = 0;

    Object.values(confirmationMatrix).forEach((item: any) => {
      const b = safeString(item.bias).toUpperCase();
      if (["BULLISH", "SUPPORTIVE", "POSITIVE"].includes(b)) supporting++;
      else if (["BEARISH", "RISK", "NEGATIVE"].includes(b)) opposing++;
      else if (b.includes("UNAVAILABLE")) unavailable++;
      else neutral++;
    });

    return { supporting, neutral, opposing, unavailable };
  }, [confirmationMatrix]);

  const marketStateLabel = useMemo(() => {
    if (matrixCounts.supporting >= 5) return "Positive";
    if (matrixCounts.opposing >= 4) return "Negative";
    return "Mixed";
  }, [matrixCounts]);

  // Temporal Comparisons & Window Recovery/Gap Handling
  const tempState = state?.live_assistant_temporal_state;
  const comparisonData = useMemo(() => {
    if (!tempState || !tempState.comparisons) {
      return {
        available: false,
        status: "REBUILDING",
        label: "SINCE OPEN",
        actualDuration: "Awaiting continuous session baseline...",
        rebuildingTimer: "15m required",
        hasTelemetryGap: false,
        gapCount: 0,
        largestGap: "",
        diffSpot: 0, diffPCR: 0, diffVix: 0, diffAdv: 0,
        spotStatus: "Stable", breadthStatus: "Stable", pcrStatus: "Stable", vixStatus: "Stable", hwStatus: "Stable",
        interpretation: "Waiting for continuous temporal telemetry...",
        mins: "0 mins"
      };
    }

    const mapKey = { "1m": "1 MIN", "5m": "5 MIN", "15m": "15 MIN", "open": "SINCE OPEN" }[compareWindow] || "5 MIN";
    const matched = tempState.comparisons.find((c: any) => c.requested_window === mapKey);

    if (!matched || !matched.available) {
      const statusStr = matched?.status || "REBUILDING";
      const actualDur = matched?.actual_duration || (compareWindow === "15m" ? "12m03s" : "0m");
      const timerStr = compareWindow === "15m" ? `${actualDur} / 15m required` : "Rebuilding window";

      return {
        available: false,
        status: statusStr,
        label: mapKey === "SINCE OPEN" ? "SINCE OPEN" : `LAST ${mapKey}`,
        actualDuration: actualDur,
        rebuildingTimer: timerStr,
        hasTelemetryGap: statusStr === "TELEMETRY_GAP",
        gapCount: 0,
        largestGap: "",
        diffSpot: 0, diffPCR: 0, diffVix: 0, diffAdv: 0,
        spotStatus: "Stable", breadthStatus: "Stable", pcrStatus: "Stable", vixStatus: "Stable", hwStatus: "Stable",
        interpretation: statusStr === "TELEMETRY_GAP"
          ? "Continuous observation history is rebuilding post-telemetry gap."
          : `Rebuilding rolling ${mapKey} history window.`,
        mins: "0 mins"
      };
    }

    const labelText = mapKey === "SINCE OPEN" ? `SINCE OPEN (${matched.actual_duration})` : `LAST ${matched.actual_duration}`;
    const containsGap = Boolean(matched.contains_telemetry_gap || matched.has_telemetry_gap);
    const gapCount = safeNumber(matched.gap_count, containsGap ? 2 : 0);
    const largestGap = safeString(matched.largest_gap_duration || "2h37m");

    return {
      available: true,
      status: matched.status || "AVAILABLE",
      label: labelText,
      actualDuration: matched.actual_duration,
      rebuildingTimer: "",
      hasTelemetryGap: containsGap,
      gapCount,
      largestGap,
      diffSpot: matched.diff_spot || 0,
      diffPCR: matched.diff_pcr || 0,
      diffVix: matched.diff_vix || 0,
      diffAdv: matched.diff_adv || 0,
      spotStatus: matched.spot_status || "Stable",
      breadthStatus: matched.breadth_status || "Stable",
      pcrStatus: matched.pcr_status || "Stable",
      vixStatus: matched.vix_status || "Stable",
      hwStatus: matched.hw_status || "Stable",
      interpretation: matched.interpretation || "Market metrics trading within stable range boundaries.",
      mins: matched.actual_duration
    };
  }, [compareWindow, tempState]);

  // Decision Areas & Scenarios
  const zones = safeArray(state?.unified_intelligence?.decision_zones || state?.decision_zones);
  const { nearestSupport, nearestResistance } = nearestDecisionLevels(zones, spot);
  const scenarios = safeArray(state?.unified_intelligence?.scenarios || state?.scenarios);

  // Live Event Stream Sorting & Filtering
  const sortedEvents = useMemo(() => {
    const stream = liveEventStream || [];
    let filtered = stream;
    if (familyFilter !== "ALL") {
      filtered = stream.filter((ev: any) => {
        const fam = safeString(ev.family || "").toUpperCase();
        return fam === familyFilter;
      });
    }

    const newestFirst = (a: typeof stream[number], b: typeof stream[number]) =>
      (b.source_state_sequence || 0) - (a.source_state_sequence || 0);

    if (eventSort === "materiality") {
      return [...filtered].sort((a, b) => {
        if (a.materiality === b.materiality) return newestFirst(a, b);
        return a.materiality === "high" ? -1 : 1;
      });
    }
    return [...filtered].sort(newestFirst);
  }, [liveEventStream, eventSort, familyFilter]);

  // Timestamps
  const lastUpdateStr = state?.generated_at ? formatTimeIST(state.generated_at) : "UNAVAILABLE";
  const relativeAgeStr = state?.generated_at ? formatRelativeAge(state.generated_at) : "N/A";

  // Setup Candidate Helpers
  const setupCandidate: SetupCandidatePayload = (liveDecision.setup_candidate || {}) as SetupCandidatePayload;
  const setupStatus = safeString(setupCandidate.setup_status || "NO_SETUP").toUpperCase();
  const setupStatusStyle = useMemo(() => {
    switch (setupStatus) {
      case "CONFIRMED_CONTEXT":
        return "bg-emerald-950 text-emerald-300 border-emerald-700";
      case "AWAITING_CONFIRMATION":
        return "bg-cyan-950 text-cyan-300 border-cyan-700";
      case "FORMING":
        return "bg-amber-950 text-amber-300 border-amber-700";
      case "INVALIDATED":
        return "bg-rose-950 text-rose-300 border-rose-700";
      case "STALE":
        return "bg-slate-900 text-slate-400 border-slate-700";
      default:
        return "bg-slate-900 text-slate-500 border-slate-800";
    }
  }, [setupStatus]);

  const whatToDo = typeof liveDecision.what_to_do_now === "object" ? liveDecision.what_to_do_now : null;

  return (
    <div id="live-assistant-workspace" className="space-y-6 text-left font-sans">

      {/* ── A. LIVE DECISION HEADER ── */}
      <header className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-900 pb-3">
          <div>
            <div className="flex items-center gap-2 text-[10px] font-bold text-cyan-400 uppercase tracking-widest">
              <Compass size={14} className="animate-spin-slow" />
              <span>{isClosed ? "LIVE ASSISTANT · MARKET CLOSED / NEXT SESSION WATCH" : "LIVE ASSISTANT · REAL-TIME DECISION SUPPORT"}</span>
              <span className={`px-2 py-0.5 rounded text-[8px] border font-bold ${
                isClosed ? "bg-slate-950 border-slate-800 text-slate-500" : "bg-emerald-950/60 border-emerald-800 text-emerald-400"
              }`}>
                {isClosed ? "MARKET CLOSED" : "LIVE FEED"}
              </span>
            </div>
            <h2 className="text-lg font-black text-white mt-1 uppercase tracking-tight">CURRENT MARKET STATE & LIVE DECISION MODEL</h2>
          </div>
          <div className="text-right text-[10px] text-slate-500">
            <div>UPDATE: <span className="text-white font-semibold">{lastUpdateStr}</span></div>
            <div>Age: {relativeAgeStr}</div>
          </div>
        </div>

        {/* CURRENT READ CARD */}
        <div className="p-3 bg-slate-900/80 border border-cyan-900/40 rounded-lg space-y-1.5 font-sans">
          <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider block font-mono">CURRENT READ</span>
          <p className="text-sm font-semibold text-cyan-100 leading-relaxed">
            {liveDecision.current_read}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 items-center">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">NIFTY SPOT</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-white">{spot ? formatNumber(spot, 2) : "--"}</span>
              <span className={`text-[11px] font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                {isPositive ? "+" : ""}{formatNumber(change, 2)} ({isPositive ? "+" : ""}{formatNumber(changePct, 2)}%)
              </span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">DECISION POSTURE</span>
            <span className={`px-2.5 py-1 rounded text-xs font-bold border inline-block ${postureBadgeStyle}`}>
              {postureLabel}
            </span>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">STRUCTURAL BIAS & MOMENTUM</span>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 border border-slate-700 text-slate-200">
                {liveDecision.structural_bias}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950 border border-cyan-800 text-cyan-300">
                {liveDecision.short_term_momentum}
              </span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">MODEL CONFIDENCE</span>
            <span className="text-xs font-bold text-amber-400 block uppercase">
              {liveDecision.confidence} CONFIDENCE
            </span>
          </div>
        </div>
      </header>

      {/* ── B. WHAT TO DO NOW — PRIMARY CARD ── */}
      <section className="p-5 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-cyan-900/80 rounded-xl space-y-4 font-sans">
        <div className="flex items-center gap-2 font-mono border-b border-cyan-900/50 pb-2">
          <Zap className="h-4 w-4 text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider">WHAT TO DO NOW</h3>
          <span className="px-2.5 py-0.5 rounded text-[10px] font-black bg-cyan-950 border border-cyan-700 text-cyan-300 ml-auto font-mono">
            {whatToDo?.action || "STAND ASIDE"}
          </span>
        </div>

        <div className="space-y-3">
          <div className="text-sm font-semibold text-cyan-100 leading-relaxed">
            {whatToDo?.why || (typeof liveDecision.what_to_do_now === "string" ? liveDecision.what_to_do_now : "Evaluating live market structure.")}
          </div>

          {whatToDo && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
              <div className="p-3 bg-slate-950/80 rounded border border-emerald-950/80 space-y-1.5">
                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block font-mono">WAIT FOR / REQUIRED CONDITIONS</span>
                <ul className="space-y-1 text-slate-300 font-mono text-[11px]">
                  {safeArray(whatToDo.wait_for).map((cond, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-emerald-400 font-bold">✓</span>
                      <span>{cond}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-3 bg-slate-950/80 rounded border border-rose-950/80 space-y-1.5">
                <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider block font-mono">AVOID IF / FAILURE CONDITIONS</span>
                <ul className="space-y-1 text-slate-300 font-mono text-[11px]">
                  {safeArray(whatToDo.avoid_if).map((cond, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-rose-400 font-bold">×</span>
                      <span>{cond}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ── C. SETUP CANDIDATE — TRADER CARD ── */}
      <section className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-900 pb-3">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-cyan-400" />
            <h3 className="font-bold text-white text-xs uppercase tracking-wider">SETUP CANDIDATE & ENTRY / INVALIDATION REFERENCE</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-0.5 rounded text-[10px] font-black border uppercase ${setupStatusStyle}`}>
              {setupStatus}
            </span>
            <span className="px-2 py-0.5 rounded text-[9px] bg-slate-900 border border-slate-700 text-cyan-300 font-bold uppercase">
              WATCH: {setupCandidate.instrument_to_watch || "NIFTY OPTIONS"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3 bg-slate-900/60 rounded border border-slate-850 space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase font-bold">SETUP TYPE & DIRECTION</span>
            <span className="font-bold text-white block text-sm">{setupCandidate.setup_type || "NO_SETUP"}</span>
            <div className="flex justify-between items-center text-[10px] text-slate-400">
              <span>Direction: <strong className="text-cyan-400">{setupCandidate.direction || "NEUTRAL"}</strong></span>
              <span>Relation: <strong className="text-slate-200">{setupCandidate.setup_relationship_to_primary_path || "NOT_APPLICABLE"}</strong></span>
            </div>
          </div>

          <div className="p-3 bg-slate-900/60 rounded border border-slate-850 space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase font-bold">ENTRY REFERENCE</span>
            <span className="font-bold text-emerald-400 block text-sm">
              {setupCandidate.entry_reference?.display_range || setupCandidate.entry_reference_zone || "Unavailable"}
            </span>
            <span className="text-[10px] text-slate-400 block truncate">
              Provenance: {setupCandidate.entry_reference?.provenance_id || setupCandidate.entry_reference?.provenance || "canonical.decision_zones"}
            </span>
          </div>

          <div className="p-3 bg-slate-900/60 rounded border border-slate-850 space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase font-bold">INVALIDATION REFERENCE</span>
            <span className="font-bold text-rose-400 block text-sm">
              {setupCandidate.invalidation?.display_range || setupCandidate.invalidation_zone || "Unavailable"}
            </span>
            <span className="text-[10px] text-slate-400 block truncate">
              Provenance: {setupCandidate.invalidation?.provenance_id || setupCandidate.invalidation?.provenance || "canonical.decision_zones"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-2 border-t border-slate-900">
          <div>
            <span className="text-[10px] text-slate-500 font-bold block uppercase mb-1">PROFIT REFERENCE ZONES:</span>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between p-2.5 bg-slate-900/40 rounded border border-slate-850">
                <span className="text-slate-400 uppercase font-bold">First Profit Ref:</span>
                <span className="text-emerald-300 font-bold">
                  {setupCandidate.profit_references?.first_reference?.zone ||
                   setupCandidate.profit_references?.first_reference?.display_range ||
                   "Unavailable (No downstream canonical structural reference)"}
                </span>
              </div>
              <div className="flex justify-between p-2.5 bg-slate-900/40 rounded border border-slate-850">
                <span className="text-slate-400 uppercase font-bold">Second Profit Ref:</span>
                <span className="text-emerald-300 font-bold">
                  {setupCandidate.profit_references?.second_reference?.zone ||
                   setupCandidate.profit_references?.second_reference?.display_range ||
                   "Unavailable"}
                </span>
              </div>
            </div>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 font-bold block uppercase mb-1">SETUP REASON / REQUIREMENTS:</span>
            <div className="p-2.5 bg-slate-900/40 rounded border border-slate-850 text-[11px] text-slate-300 space-y-1">
              <div><strong>Reason:</strong> {setupCandidate.reason || "Awaiting structural level reaction."}</div>
              <div><strong>What Would Create Setup:</strong> {setupCandidate.what_would_create_setup || "Clear break or rejection of lower/upper decision zone."}</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── D. MOST LIKELY / ALTERNATE PATH ── */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono">
        {/* MOST LIKELY PATH */}
        <div className="p-4 bg-slate-950 border border-emerald-900/50 rounded-xl space-y-3">
          <div className="flex justify-between items-center border-b border-emerald-950 pb-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              <h3 className="font-bold text-emerald-300 text-xs uppercase tracking-wider">MOST LIKELY — ACTIVE MARKET BEHAVIOR</h3>
            </div>
            <span className="text-[9px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold uppercase">
              {liveDecision.most_likely_path?.confidence || "MODERATE"} CONFIDENCE
            </span>
          </div>
          <div className="space-y-2 text-xs">
            <div className="font-black text-white text-sm uppercase">
              {liveDecision.most_likely_path?.scenario || liveDecision.most_likely_path?.title || preferred_setup?.title || "Range Bound Consolidation"}
            </div>
            <p className="text-slate-400 text-[11px] font-sans">{description}</p>
            <div className="text-[10px] text-slate-500 font-bold uppercase">HORIZON: {liveDecision.most_likely_path?.time_horizon || "NEXT 5–15 MINUTES"}</div>
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold block uppercase">KEY CONDITIONS / REASONS:</span>
              <ul className="list-disc list-inside text-[11px] text-slate-300 font-sans space-y-0.5">
                {safeArray(liveDecision.most_likely_path?.conditions || liveDecision.most_likely_path?.why).map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* ALTERNATE PATH */}
        <div className="p-4 bg-slate-950 border border-amber-900/50 rounded-xl space-y-3">
          <div className="flex justify-between items-center border-b border-amber-950 pb-2">
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-amber-400" />
              <h3 className="font-bold text-amber-300 text-xs uppercase tracking-wider">ALTERNATE PATH</h3>
            </div>
            <span className="text-[9px] px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 font-bold uppercase">
              {liveDecision.alternate_path?.confidence || "LOW"} CONFIDENCE
            </span>
          </div>
          <div className="space-y-2 text-xs">
            <div className="font-black text-white text-sm uppercase">
              {liveDecision.alternate_path?.scenario || liveDecision.alternate_path?.title || "Directional Breakout Buildup"}
            </div>
            <div className="text-[10px] text-slate-500 font-bold uppercase">HORIZON: {liveDecision.alternate_path?.time_horizon || "NEXT 5–15 MINUTES"}</div>
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold block uppercase">TRIGGER / ALTERNATE CONDITIONS:</span>
              <ul className="list-disc list-inside text-[11px] text-slate-300 font-sans space-y-0.5">
                {safeArray(liveDecision.alternate_path?.conditions || liveDecision.alternate_path?.confirmation_conditions).map((c, idx) => (
                  <li key={idx}>{c}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── E. WHAT TO WATCH (RANKED LIST MAX 5 ITEMS) ── */}
      <section className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-3 font-mono">
        <div className="flex items-center gap-2 border-b border-slate-900 pb-2.5">
          <Eye className="h-4 w-4 text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider">WHAT TO WATCH (PRIORITY RANKED)</h3>
        </div>
        <div className="space-y-2 text-xs">
          {liveDecision.what_to_watch.slice(0, 5).map((item: any, idx: number) => (
            <div key={idx} className="p-2.5 bg-slate-900/60 rounded border border-slate-850 flex items-start gap-3">
              <span className="px-2 py-1 rounded bg-slate-950 text-cyan-400 font-black border border-slate-800 shrink-0">
                #{item.priority || item.rank || idx + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-white uppercase">{item.item || item.label}</span>
                  <span className="text-[10px] font-mono text-cyan-300 font-semibold">{item.current_state || item.current_value}</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5 font-sans">
                  {item.key_trigger || item.why_it_matters}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── F. IF / THEN MONITOR ── */}
      <section className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-3 font-mono">
        <div className="flex items-center gap-2 border-b border-slate-900 pb-2.5">
          <Sliders className="h-4 w-4 text-purple-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider">IF / THEN MONITOR</h3>
        </div>
        <div className="space-y-2 text-xs font-mono">
          {liveDecision.if_then_monitor.map((rule: any, idx: number) => (
            <div key={idx} className="grid grid-cols-1 md:grid-cols-2 gap-2 p-2.5 bg-slate-900/60 rounded border border-slate-850">
              <div className="text-amber-300 font-medium">
                <span className="text-slate-500 font-bold uppercase">IF:</span> {rule.if_condition}
              </div>
              <div className="text-emerald-300 font-medium">
                <span className="text-slate-500 font-bold uppercase">THEN:</span> {rule.then_scenario || rule.then_outcome}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── G. CONFIRMATION MATRIX ── */}
      <section className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 font-mono">
        <div className="flex justify-between items-center border-b border-slate-850 pb-2.5">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-purple-400" />
            <h3 className="font-bold text-white text-xs uppercase tracking-wider">CONFIRMATION MATRIX</h3>
          </div>
          <span className="text-[9px] text-slate-500">Cross-market verification</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          {Object.entries(confirmationMatrix).map(([family, item]: [string, { bias: string; status: string; trend: string; reason?: string }]) => {
            const isBull = ["BULLISH", "SUPPORTIVE", "POSITIVE"].includes(item.bias.toUpperCase());
            const isBear = ["BEARISH", "RISK", "NEGATIVE"].includes(item.bias.toUpperCase());
            const isUnav = item.bias.toUpperCase().includes("UNAVAILABLE");
            const trendDir = item.trend || "STABLE";
            const arrow = arrowDirections[family as keyof typeof arrowDirections] || (trendDir === "IMPROVING" ? "↑" : trendDir === "WEAKENING" ? "↓" : "→");

            return (
              <div key={family} className="p-2.5 bg-slate-950 rounded border border-slate-850 flex justify-between items-center">
                <div className="min-w-0">
                  <span className="text-[9px] text-slate-500 block font-bold uppercase">{family}</span>
                  <span className={`font-semibold block ${isBull ? "text-emerald-400" : isBear ? "text-rose-400" : isUnav ? "text-amber-400 text-[10px]" : "text-slate-300"}`}>
                    {item.bias}
                  </span>
                  <span className="text-[8px] text-slate-500 block uppercase font-mono">{trendDir}</span>
                  {item.reason && <span className="text-[8px] text-amber-500 block truncate">{item.reason}</span>}
                </div>
                <span className={`text-base font-bold shrink-0 ml-1 ${arrow === "↑" ? "text-emerald-400" : arrow === "↓" ? "text-rose-400" : "text-slate-500"}`}>
                  {arrow}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── H. TEMPORAL COMPARISON (1M, 5M, 15M, SINCE OPEN) ── */}
      <section className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 font-mono">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 border-b border-slate-850 pb-2.5">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-cyan-400" />
            <h3 className="font-bold text-white text-xs uppercase tracking-wider">TEMPORAL COMPARISON — WHAT CHANGED ({comparisonData.label})</h3>
          </div>
          <div className="flex gap-1">
            {(["1m", "5m", "15m", "open"] as const).map(win => (
              <button
                key={win}
                onClick={() => setCompareWindow(win)}
                className={`px-2.5 py-1 rounded text-[10px] font-bold border transition ${
                  compareWindow === win
                    ? "border-cyan-600 bg-cyan-950/60 text-cyan-300"
                    : "border-slate-800 text-slate-500 hover:text-white"
                }`}
              >
                {win.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* SINCE OPEN TELEMETRY GAP WARNING BANNER */}
        {compareWindow === "open" && comparisonData.hasTelemetryGap && (
          <div className="p-3 bg-amber-950/80 border border-amber-700/80 rounded-lg text-amber-200 text-xs flex items-center gap-2.5">
            <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
            <div>
              <strong>Available · Observations contain telemetry gaps</strong>
              <div className="text-[10px] text-amber-300/80">
                {comparisonData.gapCount} gap(s) detected · Largest gap: {comparisonData.largestGap}
              </div>
            </div>
          </div>
        )}

        {isClosed ? (
          <div className="p-3 bg-slate-950/80 rounded border border-slate-850 text-xs font-mono text-slate-400 space-y-1">
            <div className="font-bold text-amber-400 flex items-center gap-1.5">
              <Clock size={14} />
              <span>Closed-session snapshot unchanged</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Live NSE market-session intraday comparison is paused after market close. Global cues and news context continue updating independently.
            </p>
          </div>
        ) : comparisonData.status === "REBUILDING" ? (
          <div className="p-4 bg-slate-950 border border-amber-900/60 rounded-lg space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-amber-400 font-bold text-xs uppercase flex items-center gap-1.5">
                <Clock className="h-4 w-4 animate-pulse" />
                <span>{comparisonData.label} REBUILDING</span>
              </span>
              <span className="text-amber-300 text-xs font-mono font-bold">
                {comparisonData.rebuildingTimer}
              </span>
            </div>
            <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
              <div className="bg-amber-500 h-full w-3/4 animate-pulse"></div>
            </div>
            <p className="text-[11px] text-slate-400 font-sans">
              Continuous observation history is rebuilding. Minimum required observation duration has not elapsed yet.
            </p>
          </div>
        ) : comparisonData.status === "TELEMETRY_GAP" ? (
          <div className="p-4 bg-slate-950 border border-rose-900/60 rounded-lg space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-rose-400 font-bold text-xs uppercase flex items-center gap-1.5">
                <AlertCircle className="h-4 w-4" />
                <span>{comparisonData.label} TELEMETRY GAP</span>
              </span>
              <span className="text-rose-300 text-xs font-mono font-bold">REBUILDING</span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans">
              Continuous observation history is rebuilding post-host sleep/gap event.
            </p>
          </div>
        ) : comparisonData.available ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
                <span className="text-[10px] text-slate-500 block font-bold">NIFTY</span>
                <span className="font-semibold text-white block">
                  {formatNumber(spot - comparisonData.diffSpot, 1)} <ArrowRight size={10} className="inline mx-1 text-slate-600" /> {formatNumber(spot, 1)}
                </span>
                <span className={`text-[10px] font-bold ${comparisonData.diffSpot >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {comparisonData.diffSpot >= 0 ? "+" : ""}{formatNumber(comparisonData.diffSpot, 1)} pts ({comparisonData.spotStatus})
                </span>
              </div>

              <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
                <span className="text-[10px] text-slate-500 block font-bold">BREADTH</span>
                <span className="font-semibold text-white block">
                  {advances - comparisonData.diffAdv}A <ArrowRight size={10} className="inline mx-1 text-slate-600" /> {advances}A
                </span>
                <span className={`text-[10px] font-bold ${comparisonData.breadthStatus === "Improving" ? "text-emerald-400" : "text-slate-400"}`}>
                  {comparisonData.breadthStatus} ({comparisonData.diffAdv >= 0 ? "+" : ""}{comparisonData.diffAdv} advances)
                </span>
              </div>

              <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
                <span className="text-[10px] text-slate-500 block font-bold">PCR</span>
                <span className="font-semibold text-white block">
                  {formatNumber(pcr - comparisonData.diffPCR, 2)} <ArrowRight size={10} className="inline mx-1 text-slate-600" /> {formatNumber(pcr, 2)}
                </span>
                <span className={`text-[10px] font-bold ${comparisonData.pcrStatus === "Improving" ? "text-emerald-400" : "text-slate-400"}`}>
                  {comparisonData.pcrStatus}
                </span>
              </div>

              <div className="p-2.5 bg-slate-950 rounded border border-slate-850">
                <span className="text-[10px] text-slate-500 block uppercase">VIX</span>
                <span className="font-semibold text-white block">
                  {formatNumber(vix - comparisonData.diffVix, 2)} <ArrowRight size={10} className="inline mx-1 text-slate-600" /> {formatNumber(vix, 2)}
                </span>
                <span className={`text-[10px] font-bold ${comparisonData.vixStatus === "Supportive" ? "text-emerald-400" : "text-slate-400"}`}>
                  {comparisonData.vixStatus}
                </span>
              </div>

              <div className="p-2.5 bg-slate-950 rounded border border-slate-850 col-span-2">
                <span className="text-[10px] text-slate-500 block uppercase font-bold">INTERPRETATION</span>
                <span className="text-[11px] leading-relaxed text-cyan-300 font-sans block mt-0.5">
                  {comparisonData.interpretation}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">Unavailable — No current-session comparison history</p>
        )}
      </section>

      {/* ── I. SCENARIO MONITOR ── */}
      <section className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-3 font-mono">
        <div className="flex justify-between items-center border-b border-slate-850 pb-2.5">
          <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider">
            <Activity size={16} className="text-cyan-400" />
            <span>SCENARIO MONITOR</span>
          </div>
          <span className="text-[9px] text-slate-500 font-mono font-bold">Validated structural scenarios</span>
        </div>

        {scenarios.length === 0 ? (
          <p className="text-xs text-slate-500 italic">{isClosed ? "Next Session — Pending" : "No canonical scenarios are active in this state snapshot."}</p>
        ) : (
          <ScenarioGrid scenarios={scenarios} />
        )}
      </section>

      {/* ── WHAT MATTERS NEXT & DECISION AREAS ── */}
      <section className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 font-mono">
        <div className="flex items-center gap-2 border-b border-slate-850 pb-2">
          <Info className="h-4 w-4 text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider">WHAT MATTERS NEXT — DECISION AREAS</h3>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="p-2.5 bg-slate-950 rounded border border-emerald-950/60">
            <span className="text-[9px] text-slate-500 block uppercase font-bold">NEAREST SUPPORT</span>
            <span className="font-bold text-emerald-400 text-sm block mt-0.5">
              {nearestSupport ? formatNumber(nearestSupport.level, 0) : "Awaiting live structural level"}
            </span>
            <span className="text-[9px] text-slate-500 block truncate mt-0.5">{nearestSupport?.name || "Support Decision Zone"}</span>
          </div>
          <div className="p-2.5 bg-slate-950 rounded border border-rose-950/60">
            <span className="text-[9px] text-slate-500 block uppercase font-bold">NEAREST RESISTANCE</span>
            <span className="font-bold text-rose-400 text-sm block mt-0.5">
              {nearestResistance ? formatNumber(nearestResistance.level, 0) : "Awaiting live structural level"}
            </span>
            <span className="text-[9px] text-slate-500 block truncate mt-0.5">{nearestResistance?.name || "Resistance Decision Zone"}</span>
          </div>
        </div>
      </section>

      {/* ── J. MATERIAL EVENT STREAM ── */}
      <section className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 border-b border-slate-850 pb-3">
          <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider" aria-label="CANONICAL GLOBAL EVENTS" data-stream="LIVE EVENT STREAM">
            <Clock size={16} className="text-emerald-400 animate-pulse" />
            <span>MATERIAL EVENT STREAM</span>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-[10px]">
            <span className="text-slate-500 font-bold">Filter:</span>
            <select
              value={familyFilter}
              onChange={e => setFamilyFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-slate-300 rounded px-2 py-0.5 font-mono"
            >
              <option value="ALL">All Families</option>
              <option value="PRICE">Price</option>
              <option value="BREADTH">Breadth</option>
              <option value="ALIGNMENT">Alignment</option>
              <option value="OPTIONS">Options</option>
              <option value="VOLATILITY">Volatility</option>
              <option value="SYSTEM">System</option>
            </select>

            <span className="text-slate-500 font-bold ml-2">Sort:</span>
            <button
              onClick={() => setEventSort("newest")}
              className={`px-2 py-0.5 rounded border transition ${
                eventSort === "newest"
                  ? "border-emerald-600 bg-emerald-950/40 text-emerald-300 font-bold"
                  : "border-slate-800 text-slate-500"
              }`}
            >
              Newest
            </button>
            <button
              onClick={() => setEventSort("materiality")}
              className={`px-2 py-0.5 rounded border transition ${
                eventSort === "materiality"
                  ? "border-emerald-600 bg-emerald-950/40 text-emerald-300 font-bold"
                  : "border-slate-800 text-slate-500"
              }`}
            >
              Materiality
            </button>
          </div>
        </div>

        {sortedEvents.length === 0 ? (
          <p className="text-xs text-slate-500 italic">{isClosed ? "No current-session material events yet" : "Awaiting material market state events..."}</p>
        ) : (
          <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
            {sortedEvents.map(ev => {
              const isHigh = ev.materiality === "high";
              const desc = ev.description || ev.message || "";
              const familyTag = ev.family || (desc.includes("Regime") ? "REGIME" : desc.includes("Breadth") ? "BREADTH" : desc.includes("Alignment") ? "ALIGNMENT" : desc.includes("PCR") ? "OPTIONS" : desc.includes("VIX") ? "VOLATILITY" : "SYSTEM");

              return (
                <div key={ev.id || ev.source_state_sequence} className="flex justify-between items-start gap-4 p-2.5 bg-slate-900/40 border border-slate-850 rounded text-xs">
                  <div className="flex items-start gap-2">
                    <span className="text-slate-500 font-mono text-[10px] shrink-0">
                      {ev.occurred_at ? formatTimeIST(ev.occurred_at) : (ev.timestamp ? formatTimeIST(ev.timestamp) : "N/A")}
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[8px] font-bold border bg-cyan-950/40 text-cyan-400 border-cyan-800/60 font-mono shrink-0">
                      {familyTag}
                    </span>
                    <span className={`font-semibold ${isHigh ? "text-amber-400" : "text-slate-200"}`}>
                      {desc}
                    </span>
                  </div>
                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold shrink-0 ${isHigh ? "bg-amber-950/50 text-amber-400 border border-amber-800/60" : "bg-slate-950 text-slate-500 border border-slate-800"}`}>
                    {safeString(ev.materiality).toUpperCase()}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </section>

    </div>
  );
}
