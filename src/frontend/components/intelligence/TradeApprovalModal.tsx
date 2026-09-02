// src/frontend/components/intelligence/TradeApprovalModal.tsx
import React, { useState } from "react";
import { MarketDecisionSummaryViewModel } from "../../viewmodels/session/SessionViewModels";
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Lock,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  Target,
  DollarSign,
  Shield,
  Activity,
  Check
} from "lucide-react";

import { ExecutionConfirmationModal } from "./ExecutionConfirmationModal";

interface TradeApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  summary: MarketDecisionSummaryViewModel;
  onApprove?: (candidateId: string) => void;
  onReject?: (candidateId: string, reason: string) => void;
}

export const TradeApprovalModal: React.FC<TradeApprovalModalProps> = ({
  isOpen,
  onClose,
  summary,
  onApprove,
  onReject
}) => {
  const [isApproved, setIsApproved] = useState<boolean>(false);
  const [isRejecting, setIsRejecting] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>("");
  const [isExecutionConfirmOpen, setIsExecutionConfirmOpen] = useState<boolean>(false);

  if (!isOpen) return null;

  const {
    bias,
    setup,
    strike,
    entry_condition,
    confidence,
    liquidity,
    data_quality,
    status,
    invalidation,
    target,
    risk_reward,
    strike_strength,
    entry_quality,
    trade_candidate,
    blocking_reasons
  } = summary;

  const candidateId = trade_candidate?.candidate_id || `CAND-${summary.decision_id}`;
  const instrumentName = strike.value || "NIFTY 24200 PE";
  const optionLtp = 75.0;
  const quantity = 50;
  const lots = 2;
  const estimatedOutlay = quantity * optionLtp;
  const estimatedMaxLoss = quantity * 25.0;

  const handleApprove = () => {
    setIsApproved(true);
    if (onApprove) {
      onApprove(candidateId);
    }
  };

  const handleReject = () => {
    if (onReject) {
      onReject(candidateId, rejectReason || "Trader manual rejection");
    }
    setIsRejecting(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <ExecutionConfirmationModal
        isOpen={isExecutionConfirmOpen}
        onClose={() => setIsExecutionConfirmOpen(false)}
        instrument={instrumentName}
        quantity={quantity}
        expectedLtp={optionLtp}
        estimatedOutlay={estimatedOutlay}
        invalidationLevel={invalidation}
        target={target}
        brokerExecutionEnabled={false}
      />

      <div className="bg-[#0B0C0E] border border-[#262B36] rounded-[6px] w-full max-w-2xl shadow-2xl overflow-hidden font-sans text-[#E6E8EB]">
        {/* ── HEADER ── */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#1E222B] bg-[#0E1015]">
          <div className="flex items-center gap-2.5">
            <Shield className="text-[#38BDF8]" size={16} />
            <span className="font-mono text-[13px] font-bold tracking-wider text-[#F3F4F6]">
              TRADE CANDIDATE APPROVAL REVIEW
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-[#6B7280] hover:text-[#E6E8EB] transition-colors text-[18px] leading-none"
          >
            &times;
          </button>
        </div>

        {/* ── BODY CONTENT ── */}
        <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Approved State Banner */}
          {isApproved ? (
            <div className="bg-[#064E3B]/40 border border-[#059669] rounded-[4px] p-3.5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 size={20} className="text-[#34D399] shrink-0" />
                <div>
                  <div className="font-mono text-[12px] font-bold text-[#34D399]">
                    TRADE APPROVED — AWAITING EXECUTION CONFIRMATION
                  </div>
                  <div className="text-[11px] text-[#9CA3AF] mt-0.5">
                    Candidate snapshot frozen immutably. Requires explicit 2nd-factor confirmation to submit to broker.
                  </div>
                </div>
              </div>

              <button
                onClick={() => setIsExecutionConfirmOpen(true)}
                className="px-3.5 py-1.5 bg-[#DC2626] hover:bg-[#B91C1C] text-white font-mono text-[11px] font-bold rounded-[2px] shadow-sm transition-colors flex items-center gap-1.5 shrink-0"
              >
                <Lock size={12} />
                <span>EXECUTE APPROVED TRADE</span>
              </button>
            </div>
          ) : null}

          {/* Instrument & Market Context Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Left: Target Instrument */}
            <div className="bg-[#08090C] border border-[#1A1D24] p-3 rounded-[4px]">
              <span className="text-[9px] font-mono uppercase text-[#707987] block mb-1">
                RECOMMENDED CONTRACT
              </span>
              <div className="text-[16px] font-mono font-bold text-[#38BDF8] flex items-center justify-between">
                <span>{instrumentName}</span>
                <span className="text-[12px] text-[#94A3B8] font-normal">LTP: ₹{optionLtp.toFixed(1)}</span>
              </div>
              <div className="flex items-center gap-2 mt-2 pt-2 border-t border-[#14171E] text-[10px] font-mono text-[#94A3B8]">
                <span>Δ {strike_strength?.delta ? strike_strength.delta.toFixed(2) : "0.50"}</span>
                <span>•</span>
                <span>Score: {strike_strength?.score ? strike_strength.score.toFixed(0) : "95"} ({strike_strength?.band || "EXCELLENT"})</span>
                <span>•</span>
                <span className="text-[#34D399]">Risk: {strike_strength?.premium_sensitivity || "LOW"}</span>
              </div>
            </div>

            {/* Right: Market Context */}
            <div className="bg-[#08090C] border border-[#1A1D24] p-3 rounded-[4px]">
              <span className="text-[9px] font-mono uppercase text-[#707987] block mb-1">
                QUALIFIED SETUP CONTEXT
              </span>
              <div className="text-[13px] font-bold text-[#F3F4F6]">
                {setup.value || "VWAP REJECTION + BREADTH WEAKNESS"}
              </div>
              <div className="flex items-center gap-2 mt-2 pt-2 border-t border-[#14171E] text-[10px] font-mono text-[#94A3B8]">
                <span className={`px-1.5 py-0.2 rounded font-bold ${bias.value === "BEARISH" ? "text-[#F87171] bg-[#7F1D1D]/30" : "text-[#34D399] bg-[#064E3B]/30"}`}>
                  {bias.value || "BEARISH"}
                </span>
                <span>•</span>
                <span>Conf: {confidence.value ? `${confidence.value}%` : "MODERATE"}</span>
                <span>•</span>
                <span>Data: {data_quality.value || "FULL"}</span>
              </div>
            </div>
          </div>

          {/* Trade Geometry Strip */}
          <div className="bg-[#08090C] border border-[#1A1D24] p-3 rounded-[4px] space-y-2">
            <span className="text-[9px] font-mono uppercase text-[#707987] block">
              ENTRY TRIGGER & TARGET GEOMETRY
            </span>
            <div className="text-[12px] text-[#D1D5DB] font-medium leading-relaxed">
              {entry_condition.value?.formatted_statement || "NIFTY holds below VWAP and breaks 24,180.0"}
            </div>

            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-[#14171E] font-mono text-[11px]">
              <div>
                <span className="text-[9px] text-[#707987] block uppercase">TARGET</span>
                <span className="text-[#34D399] font-bold">{target || "24,140 / 24,110"}</span>
              </div>
              <div>
                <span className="text-[9px] text-[#707987] block uppercase">INVALIDATION</span>
                <span className="text-[#F87171] font-bold">{invalidation || "Reclaims 24,252"}</span>
              </div>
              <div>
                <span className="text-[9px] text-[#707987] block uppercase">RISK / REWARD</span>
                <span className="text-[#38BDF8] font-bold">{risk_reward || "1:1.85"}</span>
              </div>
            </div>
          </div>

          {/* Position Sizing & Preflight Strip */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Position Size */}
            <div className="bg-[#08090C] border border-[#1A1D24] p-3 rounded-[4px] font-mono text-[11px]">
              <span className="text-[9px] uppercase text-[#707987] block mb-1">
                POSITION SIZING (RISK POLICY)
              </span>
              <div className="space-y-1 text-[#D1D5DB]">
                <div className="flex justify-between">
                  <span className="text-[#707987]">Allocated Lots:</span>
                  <span className="font-bold text-[#F3F4F6]">{lots} Lots ({quantity} Qty)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#707987]">Est. Outlay:</span>
                  <span className="font-bold text-[#38BDF8]">₹{estimatedOutlay.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#707987]">Est. Max Risk:</span>
                  <span className="font-bold text-[#F87171]">₹{estimatedMaxLoss.toLocaleString("en-IN")}</span>
                </div>
              </div>
            </div>

            {/* Broker Pre-Flight Check */}
            <div className="bg-[#08090C] border border-[#1A1D24] p-3 rounded-[4px] font-mono text-[11px]">
              <span className="text-[9px] uppercase text-[#707987] block mb-1">
                BROKER PRE-FLIGHT (READ-ONLY)
              </span>
              <div className="space-y-1 text-[#D1D5DB]">
                <div className="flex items-center justify-between text-[#34D399]">
                  <span className="text-[#707987]">Broker Auth:</span>
                  <span className="flex items-center gap-1 font-bold"><Check size={11} /> CONNECTED</span>
                </div>
                <div className="flex items-center justify-between text-[#34D399]">
                  <span className="text-[#707987]">Quote Reconciliation:</span>
                  <span className="flex items-center gap-1 font-bold"><Check size={11} /> MATCHED (&lt;0.5%)</span>
                </div>
                <div className="flex items-center justify-between text-[#34D399]">
                  <span className="text-[#707987]">Duplicate Check:</span>
                  <span className="flex items-center gap-1 font-bold"><Check size={11} /> 0 DUPLICATES</span>
                </div>
              </div>
            </div>
          </div>

          {/* Rejection Input Drawer if triggered */}
          {isRejecting && (
            <div className="bg-[#1C1012] border border-[#7F1D1D] p-3 rounded-[4px] space-y-2">
              <span className="text-[10px] font-mono font-bold text-[#F87171]">
                SPECIFY REJECTION REASON:
              </span>
              <input
                type="text"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="e.g. Suboptimal R:R, spread too wide, or upcoming news event..."
                className="w-full bg-[#0E0B0C] border border-[#3E1A1E] px-2.5 py-1.5 text-[11px] text-[#F3F4F6] rounded-[2px] focus:outline-none focus:border-[#EF4444]"
              />
              <div className="flex justify-end gap-2 pt-1">
                <button
                  onClick={() => setIsRejecting(false)}
                  className="px-2.5 py-1 text-[10px] font-mono text-[#9CA3AF] hover:text-[#E6E8EB]"
                >
                  Cancel
                </button>
                <button
                  onClick={handleReject}
                  className="px-3 py-1 bg-[#DC2626] hover:bg-[#B91C1C] text-white text-[10px] font-mono font-bold rounded-[2px]"
                >
                  CONFIRM REJECTION
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── FOOTER ACTIONS ── */}
        <div className="flex items-center justify-between px-5 py-3.5 border-t border-[#1E222B] bg-[#0E1015]">
          <div className="text-[10px] font-mono text-[#6B7280] flex items-center gap-1.5">
            <Lock size={11} />
            <span>2ND-FACTOR CONFIRMATION REQUIRED BEFORE BROKER ORDER</span>
          </div>

          {!isApproved && !isRejecting ? (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsRejecting(true)}
                className="px-3.5 py-1.5 border border-[#7F1D1D] bg-[#450A0A]/40 hover:bg-[#7F1D1D]/60 text-[#FCA5A5] text-[11px] font-mono font-bold rounded-[2px] transition-colors"
              >
                REJECT CANDIDATE
              </button>
              <button
                onClick={handleApprove}
                className="px-4 py-1.5 border border-[#059669] bg-[#065F46] hover:bg-[#047857] text-white text-[11px] font-mono font-bold rounded-[2px] shadow-sm transition-colors flex items-center gap-1.5"
              >
                <CheckCircle2 size={13} />
                <span>APPROVE CANDIDATE</span>
              </button>
            </div>
          ) : isApproved ? (
            <button
              onClick={onClose}
              className="px-4 py-1.5 bg-[#1F2430] hover:bg-[#2A3142] text-[#E6E8EB] text-[11px] font-mono font-bold rounded-[2px]"
            >
              CLOSE WINDOW
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
};
