/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Reusable DecisionSummary Hero Component & StrikeCandidateCard.
 * Prominently presents decision status, active setup, trigger condition, invalidation boundary,
 * risk, confidence, candidate strikes, and explicit safety alerts.
 */

import React from "react";
import {
  CanonicalDecisionSnapshot,
  StrikeCandidate,
  DirectionBias,
} from "../../../types/canonical";
import { StatusBadge, RiskBadge, DirectionBadge, ConfidenceBadge, QualityBadge } from "./Badges";
import { Zap, ShieldAlert, Crosshair, AlertTriangle, CheckCircle2, TrendingUp, HelpCircle } from "lucide-react";

export function DecisionSummary({
  decision,
  niftyBias,
  isStale = false,
}: {
  decision: CanonicalDecisionSnapshot;
  niftyBias?: DirectionBias;
  isStale?: boolean;
}) {
  const activeStatus = isStale ? "BLOCKED" : decision.decision_state;

  return (
    <div className={`rounded-lg border p-4 font-mono transition-all ${
      activeStatus === "READY_FOR_HUMAN_REVIEW"
        ? "border-[#00C896]/40 bg-[#00C896]/5 shadow-[0_0_20px_rgba(0,200,150,0.05)]"
        : activeStatus === "BLOCKED"
        ? "border-[#E5484D]/40 bg-[#E5484D]/10"
        : "border-[#1E232B] bg-[#0E1013]"
    }`}>
      {/* Top Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1C2128] pb-3 mb-3">
        <div className="flex items-center gap-2.5">
          <StatusBadge status={activeStatus} />
          {niftyBias && <DirectionBadge bias={niftyBias} />}
          <QualityBadge quality={decision.quality} />
        </div>

        <div className="flex items-center gap-2">
          <ConfidenceBadge band={decision.confidence_band} score={decision.confidence_score} />
          <RiskBadge risk={decision.risk_level} />
        </div>
      </div>

      {/* Stale Warning Banner if Stale */}
      {isStale && (
        <div className="mb-3 rounded bg-[#EF4444]/15 border border-[#EF4444]/40 p-2.5 text-xs text-[#EF4444] flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>
            <strong>DATA FEED STALE / UNAVAILABLE.</strong> Decision state is safely BLOCKED. Active trade recommendations are revoked.
          </span>
        </div>
      )}

      {/* Decision Headline & Setup */}
      <div className="mb-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-[#8B949E] uppercase tracking-wide">
          <Crosshair className="w-3.5 h-3.5 text-[#38BDF8]" />
          Setup: <span className="text-[#E6E8EB]">{decision.opportunity_setup.replace(/_/g, " ")}</span>
        </div>
        <h3 className="text-base lg:text-lg font-bold text-[#F0F6FC] mt-0.5">
          {decision.decision_headline || "Market evaluation active."}
        </h3>
      </div>

      {/* Core Operational Grid: Trigger vs Invalidation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-[#1C2128]">
        {/* Trigger Condition */}
        <div className="rounded bg-[#12151A] p-2.5 border border-[#222832]">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[#00C896] flex items-center gap-1.5 mb-1">
            <Zap className="w-3 h-3" />
            Execution Trigger Condition
          </div>
          <p className="text-xs text-[#D1D5DB] leading-relaxed">
            {decision.trigger_condition || "Observe opening range."}
          </p>
        </div>

        {/* Invalidation Boundary */}
        <div className="rounded bg-[#12151A] p-2.5 border border-[#222832]">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[#EF4444] flex items-center gap-1.5 mb-1">
            <ShieldAlert className="w-3 h-3" />
            Invalidation Boundary
          </div>
          <p className="text-xs text-[#D1D5DB] leading-relaxed">
            {decision.invalidation_boundary || "Structure break below support."}
          </p>
        </div>
      </div>
    </div>
  );
}

export function StrikeCandidateCard({
  candidate,
}: {
  candidate: StrikeCandidate;
}) {
  return (
    <div className="rounded-lg border border-[#222832] bg-[#0E1013] p-3.5 font-mono">
      <div className="flex items-center justify-between border-b border-[#1C2128] pb-2.5 mb-2.5">
        <div className="flex items-center gap-2">
          <span className="text-base font-bold text-[#F0F6FC]">
            {candidate.strike} {candidate.option_type}
          </span>
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
            candidate.option_type === "CE"
              ? "bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30"
              : "bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30"
          }`}>
            {candidate.option_type === "CE" ? "CALL OPTION" : "PUT OPTION"}
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-[#8B949E]">LTP:</span>
          <span className="text-[#F0F6FC] font-bold text-sm">
            {candidate.ltp !== null ? `₹${candidate.ltp.toFixed(2)}` : "—"}
          </span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-3 gap-2 text-[11px] mb-3">
        <div className="rounded bg-[#14171E] p-2 border border-[#20252E]">
          <span className="text-[10px] text-[#707987] block">LIQUIDITY</span>
          <span className="font-bold text-[#E6E8EB]">{candidate.liquidity}</span>
        </div>
        <div className="rounded bg-[#14171E] p-2 border border-[#20252E]">
          <span className="text-[10px] text-[#707987] block">STRENGTH</span>
          <span className="font-bold text-[#E6E8EB]">{candidate.strength}</span>
        </div>
        <div className="rounded bg-[#14171E] p-2 border border-[#20252E]">
          <span className="text-[10px] text-[#707987] block">SPOT DISTANCE</span>
          <span className="font-bold text-[#E6E8EB]">{candidate.distance_from_spot > 0 ? `+${candidate.distance_from_spot}` : candidate.distance_from_spot} pts</span>
        </div>
      </div>

      {/* Why Candidate Section */}
      <div className="space-y-1.5 text-xs">
        <span className="text-[10px] font-bold text-[#38BDF8] uppercase tracking-wide block">
          Why Candidate:
        </span>
        {candidate.rationale.map((r, i) => (
          <div key={i} className="flex items-start gap-1.5 text-[#C9D1D9]">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#00C896] shrink-0 mt-0.5" />
            <span>{r}</span>
          </div>
        ))}
      </div>

      {/* Key Risks */}
      {candidate.risks.length > 0 && (
        <div className="mt-2.5 pt-2 border-t border-[#1C2128] space-y-1 text-xs">
          <span className="text-[10px] font-bold text-[#F59E0B] uppercase tracking-wide block">
            Key Risks:
          </span>
          {candidate.risks.map((risk, i) => (
            <div key={i} className="flex items-start gap-1.5 text-[#8B949E]">
              <AlertTriangle className="w-3.5 h-3.5 text-[#F59E0B] shrink-0 mt-0.5" />
              <span>{risk}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
