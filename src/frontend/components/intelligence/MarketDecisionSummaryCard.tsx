// src/frontend/components/intelligence/MarketDecisionSummaryCard.tsx
import React, { useState } from "react";
import { MarketDecisionSummaryViewModel } from "../../viewmodels/session/SessionViewModels";
import { ShieldAlert, CheckCircle2, Clock, AlertTriangle, XCircle, Info, Zap, ChevronDown, ChevronUp, ArrowRight, Target, Shield, Crosshair } from "lucide-react";

import { TradeApprovalModal } from "./TradeApprovalModal";

interface MarketDecisionSummaryCardProps {
  summary?: MarketDecisionSummaryViewModel | null;
  subTabTitle?: string;
}

export const MarketDecisionSummaryCard: React.FC<MarketDecisionSummaryCardProps> = ({
  summary,
  subTabTitle = "LIVE GUIDE"
}) => {
  const [showStrikeDetails, setShowStrikeDetails] = useState<boolean>(false);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState<boolean>(false);

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
    target,
    risk_reward,
    strike_strength,
    entry_quality,
    nearby_strikes,
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
      case "QUALIFIED":
        return {
          bg: "bg-[#065F46]/40 border-[#10B981]",
          text: "text-[#6EE7B7]",
          icon: <CheckCircle2 size={12} className="text-[#6EE7B7]" />,
          label: "QUALIFIED SETUP"
        };
      case "CONDITIONS_PENDING":
        return {
          bg: "bg-[#78350F]/40 border-[#D97706]",
          text: "text-[#FBBF24]",
          icon: <Zap size={12} className="text-[#FBBF24]" />,
          label: "CONDITIONS PENDING"
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

  const getBiasBadge = (b?: string | null) => {
    switch (b) {
      case "BULLISH":
        return "bg-[#064E3B]/50 text-[#34D399] border-[#059669]/60";
      case "BEARISH":
        return "bg-[#7F1D1D]/50 text-[#F87171] border-[#DC2626]/60";
      case "NEUTRAL":
      case "NEUTRAL_RANGE":
      case "MIXED":
        return "bg-[#1E293B]/50 text-[#94A3B8] border-[#475569]/60";
      default:
        return "bg-[#181A20] text-[#6B7280] border-[#2D333F]";
    }
  };

  const statusBadge = getStatusBadge(status);

  return (
    <div className="mb-3 bg-[#0B0C0E] border border-[#1E222B] rounded-[4px] p-3.5 text-[#E6E8EB] font-sans shadow-md">
      <TradeApprovalModal
        isOpen={isApprovalModalOpen}
        onClose={() => setIsApprovalModalOpen(false)}
        summary={summary}
      />

      {/* ─────────────────────────────────────────────────────────────
          HEADER ROW: BIAS, SETUP, APPROVAL STATUS & REVIEW ACTION
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

        <div className="flex items-center gap-2">
          {status === "READY_FOR_APPROVAL" && (
            <button
              onClick={() => setIsApprovalModalOpen(true)}
              className="px-2.5 py-0.5 rounded-[2px] border border-[#059669] bg-[#065F46] hover:bg-[#047857] text-white text-[10px] font-mono font-bold tracking-wider transition-colors shadow-sm animate-pulse"
            >
              REVIEW TRADE
            </button>
          )}

          <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-[2px] border text-[10px] font-mono font-bold tracking-wider ${statusBadge.bg} ${statusBadge.text}`}>
            {statusBadge.icon}
            <span>{statusBadge.label}</span>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          ROW 2: TRADE GEOMETRY (STRIKE, ENTRY TRIGGER, TARGETS, R:R)
      ───────────────────────────────────────────────────────────── */}
      <div className="py-2.5 border-b border-[#1A1D24] grid grid-cols-1 md:grid-cols-12 gap-3 items-start">
        {/* Recommended Strike */}
        <div className="md:col-span-4 flex flex-col bg-[#0E1015] p-2 rounded-[3px] border border-[#1A1E27]">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[9px] font-mono uppercase text-[#707987] tracking-wider">TARGET STRIKE</span>
            {strike_strength && (
              <span className="text-[9px] font-mono font-bold text-[#34D399] bg-[#064E3B]/40 px-1 rounded">
                STR: {strike_strength.score != null && Number.isFinite(Number(strike_strength.score))
                  ? Number(strike_strength.score).toFixed(0)
                  : "—"} ({strike_strength.band || "UNAVAILABLE"})
              </span>
            )}
          </div>
          <div className="text-[14px] font-mono font-bold text-[#38BDF8]">
            {strike.status === "AVAILABLE" && strike.value ? (
              strike.value
            ) : (
              <span className="text-[#6B7280] text-[11px]">{strike.status.replace(/_/g, " ")}</span>
            )}
          </div>
          {strike_strength && (
            <div className="text-[10px] font-mono text-[#94A3B8] mt-1 flex items-center justify-between">
              <span>Δ {strike_strength.delta != null && Number.isFinite(Number(strike_strength.delta))
                ? Number(strike_strength.delta).toFixed(2)
                : "—"}</span>
              <span>Req: {strike_strength.required_nifty_move != null && Number.isFinite(Number(strike_strength.required_nifty_move))
                ? `${Number(strike_strength.required_nifty_move).toFixed(0)} pts`
                : "—"}</span>
            </div>
          )}
        </div>

        {/* Entry Condition & Targets */}
        <div className="md:col-span-8 flex flex-col justify-between h-full">
          <div>
            <span className="text-[9px] font-mono uppercase text-[#707987] tracking-wider mb-0.5 block">ENTRY TRIGGER</span>
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

          <div className="grid grid-cols-3 gap-2 mt-2 pt-2 border-t border-[#16181E] text-[10px] font-mono">
            <div>
              <span className="text-[#707987] block">TARGET</span>
              <span className="text-[#34D399] font-bold">{target || "—"}</span>
            </div>
            <div>
              <span className="text-[#707987] block">RISK / REWARD</span>
              <span className="text-[#38BDF8] font-bold">{risk_reward || "—"}</span>
            </div>
            <div>
              <span className="text-[#707987] block">INVALIDATION</span>
              <span className="text-[#F87171] font-bold truncate block">{invalidation || "—"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          ROW 3: QUALITY STRIP (CONFIDENCE, ENTRY QUALITY, LIQUIDITY, DATA)
      ───────────────────────────────────────────────────────────── */}
      <div className="py-2 border-b border-[#1A1D24] grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
        <div className="flex flex-col bg-[#08090B] px-2 py-1 rounded-[2px] border border-[#16181E]">
          <span className="text-[9px] uppercase text-[#707987]">CONFIDENCE</span>
          <span className="font-bold text-[#E6E8EB]">
            {confidence.value !== null ? `${confidence.value}%` : "UNAVAILABLE"}
          </span>
        </div>

        <div className="flex flex-col bg-[#08090B] px-2 py-1 rounded-[2px] border border-[#16181E]">
          <span className="text-[9px] uppercase text-[#707987]">ENTRY QUALITY</span>
          <span className={`font-bold ${
            entry_quality?.band === "EXCELLENT" || entry_quality?.band === "GOOD"
              ? "text-[#34D399]"
              : entry_quality?.band === "WAIT"
              ? "text-[#FBBF24]"
              : "text-[#F87171]"
          }`}>
            {entry_quality?.band || "UNAVAILABLE"}
          </span>
        </div>

        <div className="flex flex-col bg-[#08090B] px-2 py-1 rounded-[2px] border border-[#16181E]">
          <span className="text-[9px] uppercase text-[#707987]">LIQUIDITY</span>
          <span className={`font-bold ${
            liquidity.value === "STRONG" || liquidity.value === "EXCELLENT" || liquidity.value === "GOOD"
              ? "text-[#34D399]"
              : liquidity.value === "ACCEPTABLE" || liquidity.value === "FAIR"
              ? "text-[#FBBF24]"
              : "text-[#9CA3AF]"
          }`}>
            {liquidity.value || "UNAVAILABLE"}
          </span>
        </div>

        <div className="flex flex-col bg-[#08090B] px-2 py-1 rounded-[2px] border border-[#16181E]">
          <span className="text-[9px] uppercase text-[#707987]">DATA QUALITY</span>
          <span className={`font-bold ${
            data_quality.value === "FULL" || data_quality.value === "HIGH"
              ? "text-[#38BDF8]"
              : data_quality.value === "GOOD" || data_quality.value === "MEDIUM"
              ? "text-[#FBBF24]"
              : "text-[#F87171]"
          }`}>
            {data_quality.value || "DEGRADED"}
          </span>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          ROW 4: NEARBY STRIKE COMPARISON (COLLAPSIBLE SHORTLIST)
      ───────────────────────────────────────────────────────────── */}
      {nearby_strikes && nearby_strikes.length > 0 && (
        <div className="py-2 border-b border-[#1A1D24]">
          <button
            onClick={() => setShowStrikeDetails(!showStrikeDetails)}
            className="w-full flex items-center justify-between text-[10px] font-mono text-[#94A3B8] hover:text-[#E6E8EB] transition-colors"
          >
            <span className="font-bold uppercase tracking-wider flex items-center gap-1">
              <Crosshair size={11} className="text-[#38BDF8]" />
              COMPARE NEARBY STRIKES ({nearby_strikes.length})
            </span>
            <span className="flex items-center gap-1 text-[9px] text-[#6B7280]">
              {showStrikeDetails ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </span>
          </button>

          {showStrikeDetails && (
            <div className="mt-2 space-y-1.5 font-mono text-[10px]">
              {nearby_strikes.map((stk, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded-[2px] border flex flex-wrap items-center justify-between gap-2 ${
                    idx === 0
                      ? "bg-[#0D1520] border-[#0284C7]/50 text-[#E0F2FE]"
                      : "bg-[#090A0D] border-[#16181E] text-[#9CA3AF]"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[#F3F4F6]">{stk.symbol}</span>
                    <span className="text-[#94A3B8]">
                      LTP: {stk.ltp != null && Number.isFinite(Number(stk.ltp))
                        ? `₹${Number(stk.ltp).toFixed(1)}`
                        : "—"}
                    </span>
                    <span className="text-[#38BDF8]">
                      Score: {stk.strength_score != null && Number.isFinite(Number(stk.strength_score))
                        ? Number(stk.strength_score).toFixed(0)
                        : "—"} ({stk.strength_band || "UNAVAILABLE"})
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-[9px]">
                    {stk.delta != null && Number.isFinite(Number(stk.delta)) && (
                      <span>Δ {Number(stk.delta).toFixed(2)}</span>
                    )}
                    {stk.spread_pct != null && Number.isFinite(Number(stk.spread_pct)) && (
                      <span>Spread: {Number(stk.spread_pct).toFixed(2)}%</span>
                    )}
                    <span className={`${stk.premium_risk === "LOW" ? "text-[#34D399]" : stk.premium_risk === "MEDIUM" ? "text-[#FBBF24]" : "text-[#F87171]"}`}>
                      Risk: {stk.premium_risk}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          ROW 5: EVIDENCE & APPROVAL BLOCKERS
      ───────────────────────────────────────────────────────────── */}
      <div className="pt-2 flex flex-col gap-1.5 text-[11px]">
        {supporting_evidence && supporting_evidence.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
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
            <span className="font-bold">APPROVAL BLOCKERS:</span>
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
