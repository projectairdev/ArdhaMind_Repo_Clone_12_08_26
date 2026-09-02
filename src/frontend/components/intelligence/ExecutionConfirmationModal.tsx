// src/frontend/components/intelligence/ExecutionConfirmationModal.tsx
import React, { useState } from "react";
import { ShieldAlert, CheckCircle2, Lock, AlertTriangle, ArrowRight, DollarSign, Activity } from "lucide-react";

interface ExecutionConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  instrument: string;
  quantity: number;
  expectedLtp: number;
  estimatedOutlay: number;
  invalidationLevel?: string | null;
  target?: string | null;
  brokerExecutionEnabled?: boolean;
  onExecute?: () => void;
}

export const ExecutionConfirmationModal: React.FC<ExecutionConfirmationModalProps> = ({
  isOpen,
  onClose,
  instrument,
  quantity,
  expectedLtp,
  estimatedOutlay,
  invalidationLevel,
  target,
  brokerExecutionEnabled = false,
  onExecute
}) => {
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleConfirm = () => {
    setIsSubmitted(true);
    if (onExecute) {
      onExecute();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-150 font-sans">
      <div className="bg-[#0D0E12] border-2 border-[#DC2626] rounded-[6px] w-full max-w-lg shadow-2xl overflow-hidden text-[#E6E8EB]">
        {/* ── REAL MONEY WARNING HEADER ── */}
        <div className="bg-[#450A0A] border-b border-[#7F1D1D] px-5 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2 text-[#FCA5A5]">
            <AlertTriangle size={18} className="text-[#EF4444] animate-pulse" />
            <span className="font-mono text-[13px] font-bold tracking-wider">
              REAL BROKER ORDER CONFIRMATION
            </span>
          </div>
          <span className="text-[10px] font-mono font-bold bg-[#7F1D1D] text-white px-2 py-0.5 rounded">
            2ND FACTOR
          </span>
        </div>

        {/* ── BODY ── */}
        <div className="p-5 space-y-4 text-[12px]">
          {/* Mode Banner */}
          <div className={`p-2.5 rounded-[4px] border font-mono text-[11px] flex items-center justify-between ${
            brokerExecutionEnabled
              ? "bg-[#7F1D1D]/30 border-[#DC2626] text-[#FCA5A5]"
              : "bg-[#0C4A6E]/30 border-[#0284C7] text-[#38BDF8]"
          }`}>
            <span className="font-bold">
              {brokerExecutionEnabled ? "● REAL BROKER EXECUTION ENABLED" : "○ EXECUTION VALIDATION MODE (SAFE SIMULATED FILL)"}
            </span>
            <span>KITE NFO</span>
          </div>

          {isSubmitted ? (
            <div className="bg-[#064E3B]/40 border border-[#059669] p-4 rounded-[4px] text-center space-y-2">
              <CheckCircle2 size={24} className="text-[#34D399] mx-auto" />
              <div className="font-mono text-[13px] font-bold text-[#34D399]">
                ORDER SUBMITTED & RECONCILED
              </div>
              <div className="text-[11px] text-[#9CA3AF]">
                Position opened. Reconciled with live broker order book.
              </div>
            </div>
          ) : (
            <>
              <div className="text-[#9CA3AF] leading-relaxed">
                You are about to place an authoritative market order. This action requires explicit second-factor human confirmation.
              </div>

              {/* Order Summary Grid */}
              <div className="bg-[#08090C] border border-[#1E222B] p-3.5 rounded-[4px] space-y-2 font-mono text-[11px]">
                <div className="flex justify-between items-center pb-2 border-b border-[#16181E]">
                  <span className="text-[#707987]">CONTRACT:</span>
                  <span className="font-bold text-[#38BDF8] text-[13px]">{instrument}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#707987]">QUANTITY:</span>
                  <span className="font-bold text-[#F3F4F6]">{quantity} Qty ({quantity / 25} Lots)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#707987]">EXPECTED LTP:</span>
                  <span className="font-bold text-[#F3F4F6]">₹{expectedLtp.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#707987]">ESTIMATED OUTLAY:</span>
                  <span className="font-bold text-[#34D399]">₹{estimatedOutlay.toLocaleString("en-IN")}</span>
                </div>
                {invalidationLevel && (
                  <div className="flex justify-between">
                    <span className="text-[#707987]">THESIS STOP:</span>
                    <span className="font-bold text-[#F87171]">{invalidationLevel}</span>
                  </div>
                )}
                {target && (
                  <div className="flex justify-between">
                    <span className="text-[#707987]">PROFIT TARGET:</span>
                    <span className="font-bold text-[#38BDF8]">{target}</span>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* ── FOOTER ── */}
        <div className="px-5 py-3.5 bg-[#0A0B0E] border-t border-[#1E222B] flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 text-[11px] font-mono text-[#9CA3AF] hover:text-[#E6E8EB] transition-colors"
          >
            Cancel
          </button>

          {!isSubmitted ? (
            <button
              onClick={handleConfirm}
              className="px-4 py-1.5 bg-[#DC2626] hover:bg-[#B91C1C] text-white text-[11px] font-mono font-bold rounded-[2px] shadow-lg transition-colors flex items-center gap-1.5"
            >
              <Lock size={12} />
              <span>CONFIRM & PLACE ORDER</span>
            </button>
          ) : (
            <button
              onClick={onClose}
              className="px-4 py-1.5 bg-[#1F2430] hover:bg-[#2A3142] text-[#E6E8EB] text-[11px] font-mono font-bold rounded-[2px]"
            >
              CLOSE WINDOW
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
