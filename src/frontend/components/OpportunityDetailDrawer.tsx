import React from "react";
import { X, ShieldAlert, ArrowUpRight, ArrowDownRight, Clock, Target, AlertTriangle, Cpu, CheckCircle2, History } from "lucide-react";
import { CanonicalOpportunity } from "../types";

interface OpportunityDetailDrawerProps {
  opportunity: CanonicalOpportunity | null;
  onClose: () => void;
}

export function OpportunityDetailDrawer({ opportunity, onClose }: OpportunityDetailDrawerProps) {
  if (!opportunity) return null;

  const isBullish = opportunity.direction === "BULLISH";

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs font-mono">
      <div className="w-full max-w-2xl bg-[#0B0D10] border-l border-[#242830] h-full flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#242830] bg-[#050607]">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded ${isBullish ? "bg-[#00C896]/15 text-[#00C896]" : "bg-[#E5484D]/15 text-[#E5484D]"}`}>
              {isBullish ? <ArrowUpRight size={20} /> : <ArrowDownRight size={20} />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold text-white tracking-tight">{opportunity.setup_type}</span>
                <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                  opportunity.status === "TRADE_READY" ? "bg-[#00C896]/20 text-[#00C896] border border-[#00C896]/40" :
                  opportunity.status === "QUALIFIED" ? "bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/40" :
                  opportunity.status === "BLOCKED" ? "bg-[#E59700]/20 text-[#E59700] border border-[#E59700]/40" :
                  "bg-gray-800 text-gray-400"
                }`}>
                  {opportunity.status}
                </span>
              </div>
              <p className="text-[11px] text-[#707987]">ID: {opportunity.opportunity_id} · Detector: {opportunity.source_detector}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded text-[#707987] hover:text-white hover:bg-[#191D23] transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6 text-[12px]">
          {/* Status Reason Banner */}
          <div className="bg-[#13161A] border border-[#242830] p-3.5 rounded">
            <span className="text-[#707987] text-[10px] uppercase font-bold tracking-wider">Status Rationale</span>
            <p className="text-white mt-1 font-sans text-xs leading-relaxed">{opportunity.status_reason}</p>
          </div>

          {/* Core Metrics Grid */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-[#050607] border border-[#191D23] p-3 rounded text-center">
              <span className="text-[10px] text-[#707987] block">CONFIDENCE</span>
              <span className="text-lg font-bold text-[#38BDF8]">
                {opportunity.confidence_score != null ? opportunity.confidence_score.toFixed(0) : "--"} / 100
              </span>
            </div>
            <div className="bg-[#050607] border border-[#191D23] p-3 rounded text-center">
              <span className="text-[10px] text-[#707987] block">QUALITY SCORE</span>
              <span className="text-lg font-bold text-[#00C896]">
                {opportunity.quality_score != null ? opportunity.quality_score.toFixed(0) : "--"} / 100
              </span>
            </div>
            <div className="bg-[#050607] border border-[#191D23] p-3 rounded text-center">
              <span className="text-[10px] text-[#707987] block">REWARD : RISK</span>
              <span className="text-lg font-bold text-[#E6E8EB]">1 : {opportunity.reward_risk_ratio ?? "--"}</span>
            </div>
          </div>

          {/* Level Rationale */}
          <div className="border border-[#242830] rounded bg-[#08090B] p-4 space-y-3">
            <div className="flex items-center gap-2 text-white font-bold text-xs border-b border-[#191D23] pb-2">
              <Target size={14} className="text-[#38BDF8]" />
              <span>Target & Invalidation Levels</span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-[#707987] text-[10px]">ENTRY REFERENCE</span>
                <p className="text-white font-bold">
                  ₹{opportunity.entry_reference != null ? opportunity.entry_reference.toFixed(2) : "--"}
                </p>
                <span className="text-[10px] text-[#505763]">
                  Zone: ₹{opportunity.entry_zone_low != null ? opportunity.entry_zone_low.toFixed(0) : "--"} - ₹
                  {opportunity.entry_zone_high != null ? opportunity.entry_zone_high.toFixed(0) : "--"}
                </span>
              </div>
              <div>
                <span className="text-[#707987] text-[10px]">INVALIDATION (SL)</span>
                <p className="text-[#E5484D] font-bold">
                  ₹{opportunity.invalidation_level != null ? opportunity.invalidation_level.toFixed(2) : "--"}
                </p>
              </div>
              <div>
                <span className="text-[#707987] text-[10px]">TARGET 1</span>
                <p className="text-[#00C896] font-bold">
                  ₹{opportunity.target_zone_1 != null ? opportunity.target_zone_1.toFixed(2) : "--"}
                </p>
              </div>
              <div>
                <span className="text-[#707987] text-[10px]">TARGET 2</span>
                <p className="text-[#00C896] font-bold">
                  ₹{opportunity.target_zone_2 != null ? opportunity.target_zone_2.toFixed(2) : "--"}
                </p>
              </div>
            </div>
          </div>

          {/* Supporting & Conflicting Evidence */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#00C896]/5 border border-[#00C896]/20 p-3.5 rounded space-y-2">
              <span className="text-[11px] font-bold text-[#00C896] flex items-center gap-1.5">
                <CheckCircle2 size={13} /> Supporting Evidence
              </span>
              <ul className="space-y-1.5 text-[11px] text-gray-300 font-sans">
                {opportunity.confirmation_signals.map((sig, idx) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <span className="text-[#00C896]">•</span>
                    <span>{sig}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-[#E5484D]/5 border border-[#E5484D]/20 p-3.5 rounded space-y-2">
              <span className="text-[11px] font-bold text-[#E5484D] flex items-center gap-1.5">
                <AlertTriangle size={13} /> Conflicting Signals
              </span>
              <ul className="space-y-1.5 text-[11px] text-gray-300 font-sans">
                {opportunity.conflicting_signals.length > 0 ? (
                  opportunity.conflicting_signals.map((conf, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-[#E5484D]">•</span>
                      <span>{conf}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-gray-500 italic">No major conflicting signals</li>
                )}
              </ul>
            </div>
          </div>

          {/* Version & Audit Specs */}
          <div className="border border-[#242830] rounded p-3.5 bg-[#050607] space-y-2 text-[10.5px] text-[#707987]">
            <div className="flex items-center gap-2 text-white font-bold text-xs">
              <Cpu size={13} className="text-[#8B5CF6]" />
              <span>Engine Version Specs</span>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-1">
              <div>Detector Version: <span className="text-white font-bold">{opportunity.detector_version}</span></div>
              <div>Scoring Version: <span className="text-white font-bold">{opportunity.scoring_version || "1.0.0"}</span></div>
              <div>Qualification Version: <span className="text-white font-bold">{opportunity.qualification_version || "1.0.0"}</span></div>
              <div>Config Version: <span className="text-white font-bold">{opportunity.config_version || "1.0.0"}</span></div>
            </div>
          </div>

          {/* Lifecycle History */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-white font-bold text-xs">
              <History size={13} className="text-[#38BDF8]" />
              <span>Lifecycle Transition History</span>
            </div>
            <div className="border border-[#242830] rounded bg-[#050607] divide-y divide-[#191D23]">
              {opportunity.transition_history.map((t, idx) => (
                <div key={idx} className="p-3 flex items-center justify-between text-[11px]">
                  <div>
                    <span className="text-gray-400 font-bold">{t.previous_status}</span>
                    <span className="text-[#707987] mx-1.5">→</span>
                    <span className="text-[#38BDF8] font-bold">{t.new_status}</span>
                    <p className="text-[10px] text-gray-500 font-sans mt-0.5">{t.reason}</p>
                  </div>
                  <span className="text-[9.5px] text-[#505763]">{new Date(t.timestamp).toLocaleTimeString("en-IN")}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer CTA (Read-Only Informational) */}
        <div className="p-4 border-t border-[#242830] bg-[#050607] flex items-center justify-between">
          <span className="text-[10px] text-[#707987]">Phase 3.1 Informational Intelligence (No Broker Execution)</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-[#191D23] border border-[#242830] text-white hover:bg-[#242830] transition text-xs font-bold"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
