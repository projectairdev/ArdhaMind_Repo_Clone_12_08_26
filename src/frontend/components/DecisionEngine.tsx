import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { DecisionReport } from "../types";
import { AlertCircle, Cpu } from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString
} from "../utils/safeHelpers";

export function DecisionEngine() {
  const { canonicalState, lastValidState, syncing: loading, error } = useWorkstationState();
  const stateObj = canonicalState ?? lastValidState;

  if (loading) {
    return (
      <div id="decision-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4">
          <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
          <div className="h-44 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (error || !stateObj) {
    return (
      <div id="decision-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold">Decision Engine Unavailable</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Could not coordinate candidate actions."}</p>
        <button onClick={() => window.location.reload()} className="px-3 py-1 bg-slate-900 text-xs text-slate-300 border border-slate-800 rounded">
          Reconnect
        </button>
      </div>
    );
  }

  const scenarios = stateObj?.trade_scenarios || [];

  const candidateDecisions = scenarios.map((sc, idx) => ({
    execution_priority: idx + 1,
    tradingsymbol: sc.scenario_name,
    decision: sc.direction === "BULLISH" ? "BUY" : sc.direction === "BEARISH" ? "SELL" : "WATCH",
    explanation: sc.activation_condition,
    supporting_evidence: safeArray(sc.confirmation_conditions).map(cond => ({
      metric_name: "Confirm",
      metric_value: "",
      message: cond
    })),
    blocking_factors: sc.invalidation_condition ? [{
      metric_name: "Invalidation",
      metric_value: "",
      message: sc.invalidation_condition
    }] : []
  }));

  const overallAction = (stateObj?.decision_support?.blockers?.length > 0 || stateObj?.decision_support?.missing_confirmations?.length > 0)
    ? "HOLD"
    : "MONITOR";

  return (
    <div id="decision-engine" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6 text-left">
      {/* Title */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <Cpu size={18} className="text-cyan-400" />
          <h3 className="font-bold text-white text-base">Routing Decision Engine</h3>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <span className="text-[10px] font-mono text-slate-500 uppercase block">Active Routing Protocol</span>
            <span className="text-lg font-mono font-bold text-cyan-400">{overallAction}</span>
          </div>
        </div>
      </div>

      {/* Decision Routing List Grid */}
      <div className="space-y-4">
        <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider">
          Contract Routing Decision Registry
        </h4>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {candidateDecisions.map((cand, idx) => {
            const supportingEvidence = safeArray(cand?.supporting_evidence) as any[];
            const blockingFactors = safeArray(cand?.blocking_factors) as any[];
            const decisionStr = safeString(cand?.decision);

            return (
              <div key={idx} className="p-4 bg-slate-900/30 rounded-lg border border-slate-800 space-y-4">
                {/* Card top */}
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <span className="text-xs font-mono text-slate-500 uppercase block">SCENARIO PRIORITY #{safeNumber(cand?.execution_priority)}</span>
                    <h5 className="text-sm font-mono font-bold text-white leading-none">{safeString(cand?.tradingsymbol)}</h5>
                  </div>
                  <div className="flex gap-2">
                    <span className={`px-2 py-0.5 text-xs font-mono font-bold rounded uppercase ${
                      decisionStr === "BUY"
                        ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
                        : decisionStr === "WATCH"
                        ? "bg-amber-950/40 text-amber-400 border border-amber-800/30"
                        : "bg-slate-800 text-slate-400 border border-slate-700"
                    }`}>
                      {decisionStr}
                    </span>
                  </div>
                </div>

                {/* Rationale explanation */}
                <p className="text-xs text-slate-300 leading-relaxed">{safeString(cand?.explanation)}</p>

                {/* Support Evidence / Blocking metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800/60">
                  {/* Supporting evidence reasons */}
                  <div className="space-y-1">
                    <span className="text-[9px] font-mono font-bold text-slate-500 uppercase">Supporting Factors</span>
                    {supportingEvidence.length > 0 ? (
                      <div className="space-y-1">
                        {supportingEvidence.map((ev, evIdx) => (
                          <div key={evIdx} className="text-xs text-slate-400 leading-snug">
                            <span className="text-emerald-400 font-bold mr-1">•</span>
                            <span className="font-semibold text-white">{safeString(ev?.metric_name)}: </span>
                            <span>{safeString(ev?.metric_value)}</span> - <span className="text-slate-500">{safeString(ev?.message)}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-[10px] text-slate-500 italic font-mono block">No alignment evidence</span>
                    )}
                  </div>

                  {/* Blocking reasons */}
                  <div className="space-y-1">
                    <span className="text-[9px] font-mono font-bold text-slate-500 uppercase">Blocking Restraints</span>
                    {blockingFactors.length > 0 ? (
                      <div className="space-y-1">
                        {blockingFactors.map((bl, blIdx) => (
                          <div key={blIdx} className="text-xs text-slate-400 leading-snug">
                            <span className="text-rose-400 font-bold mr-1">•</span>
                            <span className="font-semibold text-white">{safeString(bl?.metric_name)}: </span>
                            <span>{safeString(bl?.metric_value)}</span> - <span className="text-rose-400/80">{safeString(bl?.message)}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-[10px] text-emerald-400 font-mono block">✔ No active blockers</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
export { DecisionEngine as DecisionEnginePanel };
export default DecisionEngine;
