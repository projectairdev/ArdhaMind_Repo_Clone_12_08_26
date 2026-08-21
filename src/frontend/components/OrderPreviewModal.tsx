import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  X,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  Wallet,
  Coins,
  Scale,
  Clock,
  Loader2,
  Lock,
  Zap,
  ChevronRight,
  AlertCircle
} from "lucide-react";

interface OrderPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  proposal: any;
  onApproveSuccess: (updatedProposal: any) => void;
}

export const OrderPreviewModal: React.FC<OrderPreviewModalProps> = ({
  isOpen,
  onClose,
  proposal,
  onApproveSuccess,
}) => {
  if (!isOpen || !proposal) return null;

  const [selectedLots, setSelectedLots] = useState<number>(proposal.lots || 1);
  const [productType, setProductType] = useState<"NRML" | "MIS">(
    (proposal.product as "NRML" | "MIS") || "NRML"
  );
  const [isMarginLoading, setIsMarginLoading] = useState<boolean>(false);
  const [marginData, setMarginData] = useState<{
    status: string;
    required_margin: number;
    available_margin: number | null;
    margin_sufficient: boolean | null;
    failure_reason?: string;
  } | null>(null);
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isLiveExecuting, setIsLiveExecuting] = useState<boolean>(false);
  const [showLiveConfirmStep, setShowLiveConfirmStep] = useState<boolean>(false);
  const [brokerVerified, setBrokerVerified] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetch("/api/broker/health")
      .then(res => res.json())
      .then(h => {
        if (active) setBrokerVerified(h.status === "CONNECTED_VERIFIED" || h.execution_verified === true);
      })
      .catch(() => { if (active) setBrokerVerified(false); });
    return () => { active = false; };
  }, [isOpen]);

  const lotSize = proposal.lot_size || 25;
  const totalQuantity = selectedLots * lotSize;
  const entryPrice = proposal.entry_price || 0;
  const stopLoss = proposal.stop_loss || 0;
  const target1 = proposal.target_1 || 0;
  const target2 = proposal.target_2 || 0;
  const riskPerUnit = Math.max(0, entryPrice - stopLoss);
  const totalRiskInr = Math.round(riskPerUnit * totalQuantity * 100) / 100;
  const approxRequiredMargin = Math.round(entryPrice * totalQuantity * 100) / 100;

  // Fetch live margin validation whenever lots or productType change
  useEffect(() => {
    let isMounted = true;
    const fetchMargin = async () => {
      setIsMarginLoading(true);
      try {
        const res = await fetch(`/api/phase3/proposals/${proposal.proposal_id}/margin`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lots: selectedLots, product: productType }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (isMounted) {
          setMarginData({
            status: data.margin_status || "MARGIN_UNAVAILABLE",
            required_margin: data.required_margin ?? approxRequiredMargin,
            available_margin: data.available_margin ?? null,
            margin_sufficient: data.margin_sufficient ?? null,
            failure_reason: data.failure_reason,
          });
        }
      } catch (err: any) {
        if (isMounted) {
          setMarginData({
            status: "MARGIN_UNAVAILABLE",
            required_margin: approxRequiredMargin,
            available_margin: null,
            margin_sufficient: null,
            failure_reason: err.message || "Failed to reach margin validation service",
          });
        }
      } finally {
        if (isMounted) setIsMarginLoading(false);
      }
    };

    fetchMargin();
    return () => {
      isMounted = false;
    };
  }, [proposal.proposal_id, selectedLots, productType, approxRequiredMargin]);

  // Dry-Run Approval
  const handleConfirmDryRun = async () => {
    setIsApproving(true);
    setActionError(null);
    setActionSuccessMessage(null);
    try {
      const res = await fetch(`/api/phase3/proposals/${proposal.proposal_id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lots: selectedLots, product: productType }),
      });
      const data = await res.json();
      if (data.success && data.proposal) {
        onApproveSuccess(data.proposal);
        onClose();
      } else {
        setActionError(data.error || "Failed to record dry-run approval.");
      }
    } catch (err: any) {
      setActionError(err.message || "Network error during dry-run approval.");
    } finally {
      setIsApproving(false);
    }
  };

  // Live Execution (Phase 3 Milestone 3)
  const handleConfirmLiveExecution = async () => {
    setIsLiveExecuting(true);
    setActionError(null);
    setActionSuccessMessage(null);
    try {
      const res = await fetch("/api/phase3/orders/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          proposal_id: proposal.proposal_id,
          lots: selectedLots,
          product: productType,
          intent_id: proposal.order_intent?.intent_id,
        }),
      });
      const data = await res.json();
      if (data.success && data.order) {
        setActionSuccessMessage(
          `Live order placed successfully! Broker Order ID: ${data.order.broker_order_id || "ACKNOWLEDGED"}`
        );
        if (data.proposal) {
          onApproveSuccess(data.proposal);
        }
        setTimeout(() => {
          onClose();
        }, 1500);
      } else {
        setActionError(data.error || "Live execution failed at broker gateway.");
      }
    } catch (err: any) {
      setActionError(err.message || "Network error during live execution dispatch.");
    } finally {
      setIsLiveExecuting(false);
    }
  };

  const isBullish = proposal.direction === "BULLISH";
  const isNoTrade = proposal.state === "NO_TRADE";
  const isInsufficientMargin = marginData?.margin_sufficient === false;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-[#0E1117] border border-[#232834] rounded-xl shadow-2xl overflow-hidden text-left font-sans text-[12px] text-[#E6E8EB] animate-in fade-in zoom-in-95 duration-150">
        
        {/* ── MODAL HEADER ── */}
        <div className="flex items-center justify-between border-b border-[#1E2330] bg-[#141822] px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-7 h-7 rounded-md bg-[#38BDF8]/10 border border-[#38BDF8]/30 text-[#38BDF8]">
              <Layers size={16} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold tracking-wider text-[13px] text-[#F1F3F5]">
                  PRE-FLIGHT ORDER PREVIEW
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    isBullish
                      ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                      : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                  }`}
                >
                  {isBullish ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                  {proposal.direction}
                </span>
              </div>
              <p className="text-[10px] text-[#848E9C] font-mono mt-0.5">
                Contract: <strong className="text-[#38BDF8]">{proposal.contract_symbol}</strong> • ID: {proposal.proposal_id}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-md text-[#848E9C] hover:text-white hover:bg-[#1E2330] transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* ── MODE BANNER ── */}
        <div className="flex items-center justify-between bg-[#38BDF8]/10 border-b border-[#38BDF8]/20 px-5 py-2 text-[#38BDF8] text-[11px] font-mono">
          <div className="flex items-center gap-2">
            <Lock size={14} className="shrink-0" />
            <span>
              <strong>EXECUTION GATEWAY:</strong> Dual-Mode Server-Authoritative Execution
            </span>
          </div>
          <span className="text-[10px] text-[#848E9C] font-bold">
            Phase 3 Gateway
          </span>
        </div>

        {/* ── BODY CONTENT ── */}
        <div className="p-5 space-y-4">
          {/* 1. Lot Size & Quantity Controller */}
          <div className="bg-[#12151E] border border-[#1E2330] rounded-lg p-3.5 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1E2330] pb-2">
              <span className="text-[11px] font-bold text-[#848E9C] tracking-wide font-mono">
                POSITION SIZING & PRODUCT
              </span>
              <div className="flex items-center gap-1.5 text-[11px] font-mono">
                <span className="text-[#707987]">Lot Size:</span>
                <span className="text-[#38BDF8] font-bold">{lotSize} Qty/Lot</span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
              {/* Lots selector */}
              <div>
                <label className="block text-[10px] text-[#707987] font-mono mb-1.5 uppercase">
                  Select Order Lots
                </label>
                <div className="flex items-center gap-1.5">
                  {[1, 2, 3, 5, 10].map((lot) => (
                    <button
                      key={lot}
                      type="button"
                      onClick={() => setSelectedLots(lot)}
                      className={`px-3 py-1.5 rounded text-[11px] font-mono font-bold transition-all ${
                        selectedLots === lot
                          ? "bg-[#38BDF8] text-[#0B0D10] shadow-sm scale-105"
                          : "bg-[#1A1F2C] text-[#848E9C] hover:text-[#E6E8EB] hover:bg-[#222838] border border-[#262D3D]"
                      }`}
                    >
                      {lot} {lot === 1 ? "Lot" : "Lots"}
                    </button>
                  ))}
                </div>
              </div>

              {/* Product Type (NRML vs MIS) */}
              <div>
                <label className="block text-[10px] text-[#707987] font-mono mb-1.5 uppercase">
                  Product Type
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setProductType("NRML")}
                    className={`flex-1 py-1.5 rounded text-[11px] font-mono font-bold border transition-colors ${
                      productType === "NRML"
                        ? "bg-[#38BDF8]/15 border-[#38BDF8] text-[#38BDF8]"
                        : "bg-[#1A1F2C] border-[#262D3D] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    NRML (Carry)
                  </button>
                  <button
                    type="button"
                    onClick={() => setProductType("MIS")}
                    className={`flex-1 py-1.5 rounded text-[11px] font-mono font-bold border transition-colors ${
                      productType === "MIS"
                        ? "bg-[#38BDF8]/15 border-[#38BDF8] text-[#38BDF8]"
                        : "bg-[#1A1F2C] border-[#262D3D] text-[#707987] hover:text-[#E6E8EB]"
                    }`}
                  >
                    MIS (Intraday)
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 2. Order Parameters Matrix */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="bg-[#12151E] border border-[#1E2330] rounded-lg p-2.5">
              <span className="text-[9px] text-[#707987] font-mono uppercase block">Total Quantity</span>
              <span className="text-[14px] font-bold font-mono text-[#F1F3F5]">{totalQuantity}</span>
              <span className="text-[9px] text-[#707987] font-mono block">units</span>
            </div>

            <div className="bg-[#12151E] border border-[#1E2330] rounded-lg p-2.5">
              <span className="text-[9px] text-[#707987] font-mono uppercase block">Limit Entry Ref</span>
              <span className="text-[14px] font-bold font-mono text-[#38BDF8]">₹{entryPrice.toFixed(2)}</span>
              <span className="text-[9px] text-[#707987] font-mono block">per unit</span>
            </div>

            <div className="bg-[#12151E] border border-[#1E2330] rounded-lg p-2.5">
              <span className="text-[9px] text-[#707987] font-mono uppercase block">Stop Loss</span>
              <span className="text-[14px] font-bold font-mono text-rose-400">₹{stopLoss.toFixed(2)}</span>
              <span className="text-[9px] text-rose-400/80 font-mono block">(-₹{riskPerUnit.toFixed(1)}/unit)</span>
            </div>

            <div className="bg-[#12151E] border border-[#1E2330] rounded-lg p-2.5">
              <span className="text-[9px] text-[#707987] font-mono uppercase block">Max INR Risk</span>
              <span className="text-[14px] font-bold font-mono text-rose-400">₹{totalRiskInr.toLocaleString()}</span>
              <span className="text-[9px] text-[#707987] font-mono block">R:R 1:{proposal.risk_reward_ratio?.toFixed(1) || "1.8"}</span>
            </div>
          </div>

          {/* 3. Kite Read-Only Margin Validation Strip */}
          <div className="bg-[#12151E] border border-[#1E2330] rounded-lg p-3.5 space-y-2.5">
            <div className="flex items-center justify-between border-b border-[#1E2330] pb-1.5">
              <div className="flex items-center gap-1.5 text-[11px] font-bold font-mono text-[#E6E8EB]">
                <Wallet size={14} className="text-[#38BDF8]" />
                <span>ZERODHA KITE MARGIN VALIDATION</span>
              </div>
              <div className="flex items-center gap-1.5">
                {isMarginLoading ? (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[#38BDF8]">
                    <Loader2 size={12} className="animate-spin" /> Fetching Margin...
                  </span>
                ) : marginData?.status === "AVAILABLE" ? (
                  marginData?.margin_sufficient ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono font-bold">
                      <ShieldCheck size={12} /> MARGIN SUFFICIENT
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30 text-[10px] font-mono font-bold">
                      <ShieldAlert size={12} /> INSUFFICIENT BALANCE
                    </span>
                  )
                ) : (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 text-[10px] font-mono font-bold">
                    <AlertCircle size={12} /> MARGIN UNAVAILABLE (OFFLINE)
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 font-mono text-[11px]">
              <div>
                <span className="text-[10px] text-[#707987] block">Required Margin:</span>
                <span className="text-[13px] font-bold text-[#F1F3F5]">
                  ₹{(marginData?.required_margin ?? approxRequiredMargin).toLocaleString()}
                </span>
              </div>

              <div>
                <span className="text-[10px] text-[#707987] block">Available Funds:</span>
                <span className="text-[13px] font-bold text-[#38BDF8]">
                  {marginData?.available_margin !== null && marginData?.available_margin !== undefined
                    ? `₹${marginData.available_margin.toLocaleString()}`
                    : "UNAVAILABLE"}
                </span>
              </div>

              <div>
                <span className="text-[10px] text-[#707987] block">Order Type / Exchange:</span>
                <span className="text-[12px] font-semibold text-[#848E9C]">
                  LIMIT / NFO ({productType})
                </span>
              </div>
            </div>

            {isInsufficientMargin && (
              <div className="flex items-center gap-2 p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[10px] font-mono">
                <AlertTriangle size={14} className="shrink-0" />
                <span>
                  Available margin is below the required amount of ₹{(marginData?.required_margin ?? approxRequiredMargin).toLocaleString()}. Execution is blocked.
                </span>
              </div>
            )}
          </div>

          {/* 4. Live Confirmation Step Overlay */}
          {showLiveConfirmStep && (
            <div className="p-3.5 rounded-lg bg-[#E5484D]/10 border border-[#E5484D]/30 space-y-2 text-[11px] font-mono animate-in fade-in duration-100">
              <div className="flex items-center gap-2 text-rose-400 font-bold">
                <AlertTriangle size={16} />
                <span>CONFIRM LIVE BROKER ORDER PLACEMENT</span>
              </div>
              <p className="text-[#C2C7D0] text-[10.5px]">
                You are about to route a <strong>LIVE REAL-MONEY ORDER</strong> to Zerodha Kite Connect:
                <br />
                <span className="text-[#38BDF8] font-bold">{proposal.contract_symbol}</span> • BUY {totalQuantity} units @ ₹{entryPrice} (NRML)
                <br />
                Max Risk: <span className="text-rose-400 font-bold">₹{totalRiskInr.toLocaleString()}</span>
              </p>
              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  disabled={isLiveExecuting}
                  onClick={handleConfirmLiveExecution}
                  className="px-4 py-1.5 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold text-[11px] transition shadow flex items-center gap-1.5"
                >
                  {isLiveExecuting ? <Loader2 size={13} className="animate-spin" /> : <Zap size={13} />}
                  Confirm & Dispatch to Zerodha
                </button>
                <button
                  type="button"
                  onClick={() => setShowLiveConfirmStep(false)}
                  className="px-3 py-1.5 rounded bg-[#1A1F2C] text-[#848E9C] hover:text-white text-[11px]"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Success or Error messages */}
          {actionSuccessMessage && (
            <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-mono flex items-center gap-2">
              <CheckCircle2 size={14} className="shrink-0" />
              <span>{actionSuccessMessage}</span>
            </div>
          )}

          {actionError && (
            <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[11px] font-mono flex items-center gap-2">
              <AlertTriangle size={14} className="shrink-0" />
              <span>{actionError}</span>
            </div>
          )}
        </div>

        {/* ── MODAL FOOTER ── */}
        <div className="flex items-center justify-between border-t border-[#1E2330] bg-[#141822] px-5 py-3.5 gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-[#1A1F2C] border border-[#262D3D] text-[#848E9C] hover:text-white hover:bg-[#222838] font-mono text-[11px] font-bold transition-colors"
          >
            Cancel
          </button>

          <div className="flex items-center gap-2">
            {/* Dry-Run Approval */}
            <button
              type="button"
              disabled={isApproving || isLiveExecuting || isNoTrade || isInsufficientMargin}
              onClick={handleConfirmDryRun}
              className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg font-mono text-[11px] font-bold transition-all shadow-md ${
                isInsufficientMargin
                  ? "bg-gray-800 text-gray-500 cursor-not-allowed border border-gray-700"
                  : isApproving
                  ? "bg-emerald-600/50 text-white cursor-wait"
                  : "bg-emerald-500 hover:bg-emerald-400 text-[#0B0D10]"
              }`}
            >
              {isApproving ? (
                <Loader2 size={13} className="animate-spin" />
              ) : (
                <CheckCircle2 size={13} />
              )}
              <span>Dry-Run Approval ({selectedLots} {selectedLots === 1 ? "Lot" : "Lots"})</span>
            </button>

            {/* Live Broker Execution Trigger */}
            {!showLiveConfirmStep && (
              <button
                type="button"
                disabled={isApproving || isLiveExecuting || isNoTrade || isInsufficientMargin || !brokerVerified}
                title={!brokerVerified ? "Broker unverified — execution blocked" : "Submit Live Order (Kite)"}
                onClick={() => setShowLiveConfirmStep(true)}
                className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg font-mono text-[11px] font-bold transition-all shadow-md ${
                  isInsufficientMargin || !brokerVerified
                    ? "bg-gray-800 text-gray-500 cursor-not-allowed border border-gray-700"
                    : "bg-rose-600 hover:bg-rose-500 text-white"
                }`}
              >
                <Zap size={13} />
                <span>{brokerVerified ? "Submit Live Order (Kite)" : "Broker Unverified (Disabled)"}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
