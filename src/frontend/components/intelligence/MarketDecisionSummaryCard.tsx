// src/frontend/components/intelligence/MarketDecisionSummaryCard.tsx
import React from "react";
import { MarketDecisionSummaryViewModel } from "../../viewmodels/session/SessionViewModels";
import { ShieldAlert, CheckCircle2, Clock, AlertTriangle, XCircle, Info, Zap } from "lucide-react";

interface MarketDecisionSummaryCardProps {
  summary?: MarketDecisionSummaryViewModel | null;
  subTabTitle?: string;
}

export const MarketDecisionSummaryCard: React.FC<MarketDecisionSummaryCardProps> = ({
  summary,
  subTabTitle = "LIVE GUIDE"
}) => {
  if (!summary) {
    return (
      <div className="mb-3 bg-[#0D0E12] border border-[#1E222B] rounded-[4px] p-3 text-[#707987] font-mono text-[11px] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock size={13} className="text-[#38BDF8]" />
          <span>INITIALIZING TRADER DECISION SUMMARY...</span>
        </div>
        <span className="text-[10px] text-[#4B5563]">AWAITING CANONICAL EVALUATION</span>
      </div>
    );
  }

  const {
    bias,
    setup,
    strike,
    entry_condition,
    confidence,
    liquidity,
    data_quality,
    risk,
    status,
    invalidation,
    supporting_evidence,
    blocking_reasons
  } = summary;

  // Status Badge Styling
  const getStatusBadge = (st: string) => {
    switch (st) {
      case "READY_FOR_APPROVAL":
        return {
          bg: "bg-[#064E3B]/40 border-[#059669]",
          text: "text-[#34D399]",
          icon: <CheckCircle2 size={12} className="text-[#34D399]" />,
          label: "READY FOR APPROVAL"
        };
      case "WATCH":
        return {
          bg: "bg-[#0C4A6E]/40 border-[#0284C7]",
          text: "text-[#38BDF8]",
          icon: <Clock size={12} className="text-[#38BDF8]" />,
          label: "WATCH"
        };
      case "QUALIFYING":
        return {
          bg: "bg-[#78350F]/40 border-[#D97706]",
          text: "text-[#FBBF24]",
          icon: <Zap size={12} className="text-[#FBBF24]" />,
          label: "QUALIFYING"
        };
      case "BLOCKED":
        return {
          bg: "bg-[#7F1D1D]/40 border-[#DC2626]",
          text: "text-[#F87171]",
          icon: <ShieldAlert size={12} className="text-[#F87171]" />,
          label: "BLOCKED"
        };
      case "MARKET_CLOSED":
        return {
          bg: "bg-[#1E222B]/60 border-[#374151]",
          text: "text-[#9CA3AF]",
          icon: <Info size={12} className="text-[#9CA3AF]" />,
          label: "MARKET CLOSED"
        };
      case "INVALIDATED":
        return {
          bg: "bg-[#450A0A]/60 border-[#991B1B]",
          text: "text-[#FCA5A5]",
          icon: <XCircle size={12} className="text-[#FCA5A5]" />,
          label: "INVALIDATED"
        };
      default:
        return {
          bg: "bg-[#1E222B] border-[#374151]",
          text: "text-[#D1D5DB]",
          icon: <Clock size={12} className="text-[#9CA3AF]" />,
          label: st || "WAITING"
        };
    }
  };

  // Bias Badge Styling
  const getBiasBadge = (b?: string | null) => {
    switch (b) {
      case "BULLISH":
        return "bg-[#064E3B]/50 text-[#34D399] border-[#059669]/60";
      case "BEARISH":
        return "bg-[#7F1D1D]/50 text-[#F87171] border-[#DC2626]/60";
      case "NEUTRAL":
      case "MIXED":
        return "bg-[#1E293B]/50 text-[#94A3B8] border-[#475569]/60";
      default:
        return "bg-[#181A20] text-[#6B7280] border-[#2D333F]";
    }
  };

  const statusBadge = getStatusBadge(status);

  return (
    <div className="mb-3 bg-[#0B0C0E] border border-[#1E222B] rounded-[4px] p-3 text-[#E6E8EB] font-sans shadow-sm">
      {/* ─────────────────────────────────────────────────────────────
          ROW 1: PRIMARY (BIAS, SETUP, STATUS)
      ───────────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-[#1A1D24]">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider rounded-[2px] border ${getBiasBadge(bias.value)}`}>
            {bias.value || "BIAS UNAVAILABLE"}
          </span>
          <span className="text-[13px] font-bold tracking-wide text-[#F3F4F6]">
            {setup.value && setup.value !== "NO_VALID_SETUP" ? setup.value : "OBSERVING STRUCTURAL CONTEXT"}
          </span>
        </div>

        <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-[2px] border text-[10px] font-mono font-bold tracking-wider ${statusBadge.bg} ${statusBadge.text}`}>
          {statusBadge.icon}
          <span>{statusBadge.label}</span>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          ROW 2: TRADE (STRIKE & ENTRY CONDITION)
      ───────────────────────────────────────────────────────────── */}
      <div className="py-2.5 border-b border-[#1A1D24] grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
        <div className="md:col-span-4 flex flex-col">
          <span className="text-[10px] font-mono uppercase text-[#707987] tracking-wider mb-0.5">TARGET CONTRACT / STRIKE</span>
          <div className="text-[13px] font-mono font-bold text-[#38BDF8]">
            {strike.status === "AVAILABLE" && strike.value ? (
              strike.value
            ) : strike.status === "REQUIRES_LIVE_OPTIONS" ? (
              <span className="text-[#6B7280] text-[11px]">REQUIRES LIVE OPTIONS</span>
            ) : strike.status === "WAITING_FOR_OPTIONS_CONFIRMATION" ? (
              <span className="text-[#F59E0B] text-[11px]">WAITING OPTIONS CONFIRMATION</span>
            ) : (
              <span className="text-[#6B7280] text-[11px]">NOT QUALIFIED</span>
            )}
          </div>
        </div>

        <div className="md:col-span-8 flex flex-col">
          <span className="text-[10px] font-mono uppercase text-[#707987] tracking-wider mb-0.5">ENTRY TRIGGER STATEMENT</span>
          <div className="text-[12px] text-[#D1D5DB] leading-relaxed">
            {entry_condition.value?.formatted_statement || (
              <span className="text-[#6B7280] font-mono text-[11px]">
                {status === "MARKET_CLOSED"
                  ? "Next-session execution trigger requires pre-market discovery."
                  : "Awaiting valid trigger formation inside key decision zones."}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          ROW 3: QUALITY STRIP (CONFIDENCE, LIQUIDITY, DATA QUALITY, RISK)
      ───────────────────────────────────────────────────────────── */}
      <div className="py-2 border-b border-[#1A1D24] grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
        <div className="flex flex-col bg-[#08090B] px-2 py-1 rounded-[2px] border border-[#16181E]">
          <span className="text-[9px] uppercase text-[#707987]">CONFIDENCE</span>
          <span className="font-bold text-[#E6E8EB]">
            {confidence.value !== null ? `${confidence.value}%` : "UNAVAILABLE"}
          </span>
        </div>

        <div className="flex flex-col bg-[#08090B] px-2 py-1 rounded-[2px] border border-[#16181E]">
          <span className="text-[9px] uppercase text-[#707987]">LIQUIDITY</span>
          <span className={`font-bold ${
            liquidity.value === "EXCELLENT" || liquidity.value === "GOOD"
              ? "text-[#34D399]"
              : liquidity.value === "FAIR"
              ? "text-[#FBBF24]"
              : "text-[#9CA3AF]"
          }`}>
            {liquidity.value || "UNAVAILABLE"}
          </span>
        </div>

        <div className="flex flex-col bg-[#08090B] px-2 py-1 rounded-[2px] border border-[#16181E]">
          <span className="text-[9px] uppercase text-[#707987]">DATA QUALITY</span>
          <span className={`font-bold ${
            data_quality.value === "HIGH"
              ? "text-[#38BDF8]"
              : data_quality.value === "MEDIUM"
              ? "text-[#FBBF24]"
              : "text-[#F87171]"
          }`}>
            {data_quality.value || "DEGRADED"}
          </span>
        </div>

        <div className="flex flex-col bg-[#08090B] px-2 py-1 rounded-[2px] border border-[#16181E]">
          <span className="text-[9px] uppercase text-[#707987]">OVERALL RISK</span>
          <span className={`font-bold ${
            risk.value === "LOW" || risk.value === "MODERATE"
              ? "text-[#34D399]"
              : risk.value === "HIGH"
              ? "text-[#F59E0B]"
              : "text-[#F87171]"
          }`}>
            {risk.value || "MODERATE"}
          </span>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          ROW 4: DETAIL (INVALIDATION, EVIDENCE, BLOCKING REASONS)
      ───────────────────────────────────────────────────────────── */}
      <div className="pt-2 flex flex-col gap-1.5 text-[11px]">
        {invalidation && (
          <div className="flex items-center gap-1.5 text-[#9CA3AF]">
            <span className="text-[10px] font-mono uppercase text-[#F87171] font-bold">INVALIDATION:</span>
            <span>{invalidation}</span>
          </div>
        )}

        {supporting_evidence && supporting_evidence.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
            <span className="text-[10px] font-mono uppercase text-[#707987] font-bold mr-1">EVIDENCE:</span>
            {supporting_evidence.map((chip, idx) => (
              <span key={idx} className="bg-[#12141A] text-[#93C5FD] border border-[#1F2430] px-1.5 py-0.5 text-[10px] font-mono rounded-[2px]">
                {chip}
              </span>
            ))}
          </div>
        )}

        {blocking_reasons && blocking_reasons.length > 0 && status !== "READY_FOR_APPROVAL" && status !== "MARKET_CLOSED" && (
          <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[#FCA5A5] text-[10px] font-mono">
            <AlertTriangle size={11} className="text-[#F87171]" />
            <span className="font-bold">WAITING FOR:</span>
            {blocking_reasons.map((reason, idx) => (
              <span key={idx} className="bg-[#450A0A]/50 border border-[#7F1D1D] px-1.5 py-0.5 rounded-[2px]">
                {reason.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
