/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Reusable Badges for Canonical Presentation Layer.
 * Implements StatusBadge, QualityBadge, RiskBadge, and DirectionBadge.
 */

import React from "react";
import { DecisionState, DataQualityStatus, RiskLevel, DirectionBias, ConfidenceBand } from "../../../types/canonical";
import { ShieldAlert, ShieldCheck, Clock, AlertTriangle, CheckCircle, XCircle, Info, Zap } from "lucide-react";

export function StatusBadge({ status }: { status: DecisionState }) {
  switch (status) {
    case "READY_FOR_HUMAN_REVIEW":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#00C896]/15 border border-[#00C896]/40 text-[#00C896] text-[11px] font-mono font-bold tracking-wide">
          <Zap className="w-3 h-3 animate-pulse" />
          READY FOR HUMAN REVIEW
        </span>
      );
    case "WATCH":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#38BDF8]/15 border border-[#38BDF8]/40 text-[#38BDF8] text-[11px] font-mono font-bold tracking-wide">
          <Info className="w-3 h-3" />
          WATCH
        </span>
      );
    case "WAIT":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#F59E0B]/15 border border-[#F59E0B]/40 text-[#F59E0B] text-[11px] font-mono font-bold tracking-wide">
          <Clock className="w-3 h-3" />
          WAIT (CONFIRMING)
        </span>
      );
    case "NO_TRADE":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#707987]/20 border border-[#707987]/40 text-[#A5ABB4] text-[11px] font-mono font-bold tracking-wide">
          <XCircle className="w-3 h-3" />
          NO TRADE (GATED)
        </span>
      );
    case "INVALIDATED":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#EF4444]/15 border border-[#EF4444]/40 text-[#EF4444] text-[11px] font-mono font-bold tracking-wide">
          <AlertTriangle className="w-3 h-3" />
          INVALIDATED
        </span>
      );
    case "BLOCKED":
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#E5484D]/20 border border-[#E5484D]/50 text-[#E5484D] text-[11px] font-mono font-bold tracking-wide">
          <ShieldAlert className="w-3 h-3" />
          BLOCKED (SAFETY GATE)
        </span>
      );
  }
}

export function QualityBadge({ quality }: { quality: DataQualityStatus }) {
  switch (quality) {
    case "VALID":
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#00C896]/10 border border-[#00C896]/30 text-[#00C896] text-[10px] font-mono font-semibold">
          <CheckCircle className="w-2.5 h-2.5" />
          LIVE
        </span>
      );
    case "DELAYED":
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#F59E0B]/10 border border-[#F59E0B]/30 text-[#F59E0B] text-[10px] font-mono font-semibold">
          <Clock className="w-2.5 h-2.5" />
          DELAYED
        </span>
      );
    case "STALE":
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444] text-[10px] font-mono font-bold">
          <AlertTriangle className="w-2.5 h-2.5" />
          STALE
        </span>
      );
    case "RECOVERING":
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8] text-[10px] font-mono font-bold animate-pulse">
          <Clock className="w-2.5 h-2.5" />
          RECOVERING
        </span>
      );
    case "SESSION_MISMATCH":
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#EF4444]/20 border border-[#EF4444]/50 text-[#EF4444] text-[10px] font-mono font-bold">
          <AlertTriangle className="w-2.5 h-2.5" />
          MISMATCH
        </span>
      );
    case "COMPLETED":
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#707987]/15 border border-[#707987]/30 text-[#A5ABB4] text-[10px] font-mono font-semibold">
          COMPLETED
        </span>
      );
    case "UNAVAILABLE":
    default:
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#242830] border border-[#343A46] text-[#707987] text-[10px] font-mono font-medium">
          UNAVAILABLE
        </span>
      );
  }
}

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  switch (risk) {
    case "LOW":
      return (
        <span className="px-2 py-0.5 rounded bg-[#00C896]/10 text-[#00C896] text-[11px] font-mono font-bold">
          LOW RISK
        </span>
      );
    case "NORMAL":
      return (
        <span className="px-2 py-0.5 rounded bg-[#38BDF8]/10 text-[#38BDF8] text-[11px] font-mono font-bold">
          NORMAL RISK
        </span>
      );
    case "ELEVATED":
      return (
        <span className="px-2 py-0.5 rounded bg-[#F59E0B]/10 text-[#F59E0B] text-[11px] font-mono font-bold">
          ELEVATED RISK
        </span>
      );
    case "EXTREME":
    case "CIRCUIT_RISK":
      return (
        <span className="px-2 py-0.5 rounded bg-[#EF4444]/20 text-[#EF4444] text-[11px] font-mono font-bold">
          EXTREME RISK
        </span>
      );
    default:
      return <span className="px-2 py-0.5 rounded bg-[#242830] text-[#707987] text-[11px] font-mono">UNKNOWN</span>;
  }
}

export function DirectionBadge({ bias }: { bias: DirectionBias }) {
  switch (bias) {
    case "BULLISH":
      return (
        <span className="px-2 py-0.5 rounded bg-[#00C896]/15 border border-[#00C896]/40 text-[#00C896] text-[11px] font-mono font-bold">
          ▲ BULLISH
        </span>
      );
    case "BEARISH":
      return (
        <span className="px-2 py-0.5 rounded bg-[#EF4444]/15 border border-[#EF4444]/40 text-[#EF4444] text-[11px] font-mono font-bold">
          ▼ BEARISH
        </span>
      );
    case "NEUTRAL":
      return (
        <span className="px-2 py-0.5 rounded bg-[#38BDF8]/15 border border-[#38BDF8]/40 text-[#38BDF8] text-[11px] font-mono font-bold">
          ◆ NEUTRAL
        </span>
      );
    case "UNCERTAIN":
    default:
      return (
        <span className="px-2 py-0.5 rounded bg-[#707987]/20 border border-[#707987]/40 text-[#A5ABB4] text-[11px] font-mono font-semibold">
          ? UNCERTAIN
        </span>
      );
  }
}

export function ConfidenceBadge({ band, score }: { band: ConfidenceBand; score?: number }) {
  const colorClass =
    band === "HIGH"
      ? "text-[#00C896] bg-[#00C896]/10 border-[#00C896]/30"
      : band === "MEDIUM"
      ? "text-[#38BDF8] bg-[#38BDF8]/10 border-[#38BDF8]/30"
      : "text-[#F59E0B] bg-[#F59E0B]/10 border-[#F59E0B]/30";

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-mono font-bold ${colorClass}`}>
      {band} CONFIDENCE {score !== undefined ? `(${score}%)` : ""}
    </span>
  );
}
