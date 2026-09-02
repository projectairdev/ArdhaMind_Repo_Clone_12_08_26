import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Zap,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  RefreshCw,
  FileCheck2,
  Eye,
  Wallet,
  Layers,
  Activity
} from "lucide-react";
import { Surface } from "./ui/WorkspacePrimitives";
import { formatNumber } from "../utils/safeHelpers";
import { OrderPreviewModal } from "./OrderPreviewModal";
import { LivePositionDrawer } from "./LivePositionDrawer";

export interface TradeProposalPayload {
  proposal_id: string;
  timestamp: string;
  underlying: string;
  setup_type: string;
  direction: "BULLISH" | "BEARISH" | "NEUTRAL" | string;
  strike: number;
  option_type: "CE" | "PE" | "NONE" | string;
  contract_symbol: string;
  entry_price: number;
  stop_loss: number;
  target_1: number;
  target_2: number;
  risk_reward_ratio: number;
  confidence_score: number;
  priority_score: number;
  quality_score: number;
  max_loss_inr: number;
  rationale: string[];
  invalidation_condition: string;
  state:
    | "PROPOSED"
    | "RISK_VALIDATED"
    | "AWAITING_APPROVAL"
    | "INTENT_PREPARED"
    | "SUBMITTED"
    | "DRY_RUN_RECORDED"
    | "EXPIRED"
    | "REJECTED"
    | "NO_TRADE"
    | string;
  lots?: number;
  lot_size: number;
  total_quantity?: number;
  product?: string;
  margin_status?: string;
  required_margin?: number;
  available_margin?: number;
  margin_sufficient?: boolean;
  order_intent?: any;
  risk_evaluation?: any;
  approval_timestamp?: string;
  rejection_reason?: string;
}

interface ActiveOpportunityHeroProps {
  onProposalUpdate?: (proposal: TradeProposalPayload) => void;
}

export const ActiveOpportunityHero: React.FC<ActiveOpportunityHeroProps> = () => {
  const [proposal, setProposal] = useState<TradeProposalPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [selectedLots, setSelectedLots] = useState<number>(1);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState<boolean>(false);
  const [isLedgerOpen, setIsLedgerOpen] = useState<boolean>(false);

  const fetchActiveProposal = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/phase3/proposals/active");
      if (res.ok) {
        const data = await res.json();
        setProposal(data);
        if (data.lots) setSelectedLots(data.lots);
      }
    } catch (err) {
      console.warn("Failed to fetch active proposal:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveProposal();
    const interval = setInterval(fetchActiveProposal, 8000);

    // Listen to WebSocket events if available
    const handleWsEvent = (evt: MessageEvent) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === "phase3_proposal" && msg.data) {
          setProposal(msg.data);
          if (msg.data.lots) setSelectedLots(msg.data.lots);
        }
      } catch {}
    };

    const ws = (window as any).__ARDHA_WS__;
    if (ws && typeof ws.addEventListener === "function") {
      ws.addEventListener("message", handleWsEvent);
      return () => {
        clearInterval(interval);
        ws.removeEventListener("message", handleWsEvent);
      };
    }
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async () => {
    if (!proposal || !proposal.proposal_id) return;
    try {
      setActionLoading(true);
      setActionMessage(null);
      // Ensure validated if in initial PROPOSED state
      if (proposal.state === "PROPOSED") {
        await fetch(`/api/phase3/proposals/${proposal.proposal_id}/validate`, { method: "POST" });
      }
      const res = await fetch(`/api/phase3/proposals/${proposal.proposal_id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lots: selectedLots, product: proposal.product || "NRML" }),
      });
      const data = await res.json();
      if (data.proposal) {
        setProposal(data.proposal);
        setActionMessage("Trade intent prepared & recorded in audit ledger (Dry-Run Mode).");
      }
    } catch (err: any) {
      setActionMessage(`Approval error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!proposal || !proposal.proposal_id) return;
    try {
      setActionLoading(true);
      setActionMessage(null);
      const res = await fetch(`/api/phase3/proposals/${proposal.proposal_id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Trader rejected opportunity proposal" }),
      });
      const data = await res.json();
      if (data.proposal) {
        setProposal(data.proposal);
        setActionMessage("Proposal marked as rejected.");
      }
    } catch (err: any) {
      setActionMessage(`Rejection error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !proposal) {
    return (
      <Surface className="p-3 bg-[#0E1013] border border-[#191D23] flex items-center justify-between text-xs text-[#707987]">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#38BDF8]" />
          <span>Evaluating Phase 3 opportunity stream...</span>
        </div>
        <span className="font-mono text-[10px]">PRE-FLIGHT GATEWAY</span>
      </Surface>
    );
  }

  const isNoTrade =
    !proposal ||
    proposal.state === "NO_TRADE" ||
    proposal.state === "INSUFFICIENT_DATA" ||
    proposal.direction === "NEUTRAL" ||
    proposal.contract_symbol === "NO ACTIVE PROPOSAL" ||
    proposal.setup_type === "NONE" ||
    !proposal.entry_price ||
    proposal.entry_price <= 0 ||
    !proposal.strike ||
    proposal.strike <= 0 ||
    proposal.confidence_score == null ||
    proposal.confidence_score <= 0 ||
    proposal.quality_score == null ||
    proposal.quality_score <= 0 ||
    !proposal.stop_loss ||
    proposal.stop_loss <= 0 ||
    !proposal.target_1 ||
    proposal.target_1 <= 0;
  const isBullish = proposal?.direction?.toUpperCase() === "BULLISH";
  const isApproved = proposal?.state === "DRY_RUN_RECORDED" || proposal?.state === "INTENT_PREPARED";
  const isSubmitted = proposal?.state === "SUBMITTED";
  const isValidated = proposal?.state === "RISK_VALIDATED";
  const isRejected = proposal?.state === "REJECTED";

  const lotSize = proposal?.lot_size || 25;
  const currentQuantity = selectedLots * lotSize;
  const riskPerPoint = Math.max(0, (proposal?.entry_price || 0) - (proposal?.stop_loss || 0));
  const calculatedMaxLoss = Math.round(riskPerPoint * currentQuantity * 100) / 100;

  if (isNoTrade) {
    return (
      <>
        <Surface className="p-3.5 bg-[#0B0D10] border border-[#191D23] rounded-[4px] font-sans text-left">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="p-2 rounded-[2px] bg-[#1E232B] text-[#707987]">
                <ShieldCheck className="w-4 h-4 text-[#707987]" />
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold text-[#E6E8EB] uppercase tracking-wider font-mono">
                    ACTIVE ADVISORY FRAME: STANDBY
                  </span>
                  <span className="px-1.5 py-0.5 rounded-[2px] bg-[#1E232B] text-[#A5ABB4] text-[9px] font-mono font-bold tracking-wider uppercase">
                    NO ACTIVE OPPORTUNITY
                  </span>
                </div>
                <p className="text-[11px] text-[#848E9C] mt-0.5">
                  {proposal?.rationale?.[0] || "No high-conviction trade setup currently meets qualification thresholds (Confluence Score ≥ 65)."}
                </p>
                <p className="text-[10px] text-[#555E6D] mt-0.5 font-mono">
                  Trade proposals are generated only when real market structure, active option chain liquidity, and validated risk/reward boundaries are verified.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setIsLedgerOpen(true)}
                className="px-2.5 py-1 rounded-[2px] bg-[#14171C] hover:bg-[#1E232B] text-[#848E9C] hover:text-[#E6E8EB] text-[10px] font-mono border border-[#191D23] transition flex items-center gap-1"
              >
                <Layers className="w-3 h-3 text-[#38BDF8]" />
                Orders & Positions
              </button>
              <button
                type="button"
                onClick={fetchActiveProposal}
                className="px-2.5 py-1 rounded-[2px] bg-[#14171C] hover:bg-[#1E232B] text-[#A5ABB4] text-[10px] font-mono border border-[#191D23] transition flex items-center gap-1.5"
              >
                <RefreshCw className="w-3 h-3" />
                Scan Now
              </button>
            </div>
          </div>
        </Surface>

        <LivePositionDrawer
          isOpen={isLedgerOpen}
          onClose={() => setIsLedgerOpen(false)}
        />
      </>
    );
  }

  return (
    <>
      <Surface className="overflow-hidden border border-[#262C36] bg-[#0E1013] rounded-[4px] font-sans text-left shadow-lg">
        {/* ── TOP HEADER / GLANCE BAR (3-SECOND READ) ── */}
        <div className="px-3.5 py-2.5 bg-[#12151A] border-b border-[#191D23] flex flex-wrap items-center justify-between gap-3">
          {/* Left: Direction & Contract Symbol */}
          <div className="flex items-center gap-2.5">
            <span
              className={`px-2 py-0.5 rounded-[2px] text-[10px] font-bold font-mono uppercase flex items-center gap-1 ${
                isBullish
                  ? "bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30"
                  : "bg-[#E5484D]/15 text-[#E5484D] border border-[#E5484D]/30"
              }`}
            >
              {isBullish ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {proposal.direction}
            </span>

            <span className="text-[14px] font-bold text-[#E6E8EB] font-mono tracking-wide">
              {proposal.contract_symbol}
            </span>

            <span className="text-[10px] text-[#707987] font-mono hidden sm:inline">
              ({proposal.setup_type.replace(/_/g, " ")})
            </span>
          </div>

          {/* Center: Lots Controller & State Badge */}
          <div className="flex items-center gap-3">
            {/* Interactive Lots Picker */}
            {!isApproved && !isRejected && !isSubmitted && (
              <div className="flex items-center gap-1.5 bg-[#191D23] px-2 py-0.5 rounded border border-[#262D3D]">
                <span className="text-[9px] font-mono text-[#707987] uppercase">Lots:</span>
                {[1, 2, 3, 5, 10].map((l) => (
                  <button
                    key={l}
                    type="button"
                    onClick={() => setSelectedLots(l)}
                    className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-bold transition-all ${
                      selectedLots === l
                        ? "bg-[#38BDF8] text-[#0B0D10]"
                        : "text-[#848E9C] hover:text-white"
                    }`}
                  >
                    {l}
                  </button>
                ))}
              </div>
            )}

            <span
              className={`px-2 py-0.5 rounded-[2px] text-[9px] font-bold font-mono tracking-wider uppercase border ${
                isSubmitted
                  ? "bg-[#38BDF8]/25 text-[#38BDF8] border-[#38BDF8]/50"
                  : isApproved
                  ? "bg-[#00C896]/20 text-[#00C896] border-[#00C896]/40"
                  : isRejected
                  ? "bg-[#E5484D]/20 text-[#E5484D] border-[#E5484D]/40"
                  : isValidated
                  ? "bg-[#38BDF8]/20 text-[#38BDF8] border-[#38BDF8]/40"
                  : "bg-[#F5A623]/20 text-[#F5A623] border-[#F5A623]/40"
              }`}
            >
              {proposal.state}
            </span>

            <span className="text-[10px] font-mono text-[#A5ABB4] bg-[#191D23] px-2 py-0.5 rounded-[2px]">
              Conviction: <strong className="text-[#E6E8EB]">{proposal.confidence_score.toFixed(0)}%</strong>
            </span>
          </div>

          {/* Right: Actions (Preview Modal & Instant Approval) */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsLedgerOpen(true)}
              className="px-2.5 py-1 rounded-[2px] bg-[#14171C] hover:bg-[#1E232B] text-[#848E9C] hover:text-[#E6E8EB] text-[10px] font-mono border border-[#191D23] transition flex items-center gap-1"
            >
              <Layers className="w-3 h-3 text-[#38BDF8]" />
              Orders & Positions
            </button>

            {!isApproved && !isRejected && !isSubmitted && (
              <>
                <button
                  type="button"
                  onClick={handleReject}
                  disabled={actionLoading}
                  className="px-2.5 py-1 rounded-[2px] bg-[#191D23] hover:bg-[#E5484D]/20 hover:text-[#E5484D] text-[#707987] text-[10px] font-mono border border-[#262C36] transition disabled:opacity-50"
                >
                  Reject
                </button>

                <button
                  type="button"
                  onClick={() => setIsPreviewModalOpen(true)}
                  className="px-2.5 py-1 rounded-[2px] bg-[#1A1F2C] hover:bg-[#222838] text-[#38BDF8] font-bold text-[10px] font-mono border border-[#38BDF8]/30 hover:border-[#38BDF8] transition flex items-center gap-1"
                >
                  <Eye className="w-3 h-3" />
                  View Advisory Frame
                </button>

                <button
                  type="button"
                  onClick={handleApprove}
                  disabled={actionLoading}
                  className="px-3.5 py-1 rounded-[2px] bg-[#00C896] hover:bg-[#00D9A3] text-[#08090B] font-bold text-[10px] font-mono transition flex items-center gap-1.5 shadow disabled:opacity-50"
                >
                  {actionLoading ? (
                    <RefreshCw className="w-3 h-3 animate-spin" />
                  ) : (
                    <Zap className="w-3 h-3" />
                  )}
                  Acknowledge Frame ({selectedLots} {selectedLots === 1 ? "Lot" : "Lots"})
                </button>
              </>
            )}

            {isSubmitted && (
              <span className="flex items-center gap-1.5 text-[10px] font-mono text-[#38BDF8] bg-[#38BDF8]/10 border border-[#38BDF8]/30 px-2.5 py-0.5 rounded-[2px]">
                <Activity className="w-3.5 h-3.5" />
                ADVISORY BOUNDS RECORDED
              </span>
            )}

            {isApproved && (
              <span className="flex items-center gap-1.5 text-[10px] font-mono text-[#00C896] bg-[#00C896]/10 border border-[#00C896]/30 px-2.5 py-0.5 rounded-[2px]">
                <CheckCircle2 className="w-3.5 h-3.5" />
                MODEL PARAMETERS ACKNOWLEDGED ({selectedLots} {selectedLots === 1 ? "Lot" : "Lots"})
              </span>
            )}

            {isRejected && (
              <span className="flex items-center gap-1.5 text-[10px] font-mono text-[#E5484D] bg-[#E5484D]/10 border border-[#E5484D]/30 px-2.5 py-0.5 rounded-[2px]">
                <XCircle className="w-3.5 h-3.5" />
                REJECTED
              </span>
            )}
          </div>
        </div>

        {/* ── KEY METRICS STRIP (TRADE LEVELS & POSITION EXPOSURE) ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 divide-x divide-[#191D23] border-b border-[#191D23] bg-[#0B0D10] text-[11px] font-mono">
          <div className="px-3 py-2">
            <div className="text-[#707987] text-[9px] uppercase">Entry Reference</div>
            <div className="text-[13px] font-bold text-[#E6E8EB] mt-0.5">
              ₹{formatNumber(proposal.entry_price, 2)}
            </div>
          </div>

          <div className="px-3 py-2">
            <div className="text-[#707987] text-[9px] uppercase">Invalidation Floor</div>
            <div className="text-[13px] font-bold text-[#E5484D] mt-0.5">
              ₹{formatNumber(proposal.stop_loss, 2)}
            </div>
          </div>

          <div className="px-3 py-2">
            <div className="text-[#707987] text-[9px] uppercase">Target 1 / Target 2</div>
            <div className="text-[13px] font-bold text-[#00C896] mt-0.5">
              ₹{formatNumber(proposal.target_1, 1)} / ₹{formatNumber(proposal.target_2, 1)}
            </div>
          </div>

          <div className="px-3 py-2">
            <div className="text-[#707987] text-[9px] uppercase">Risk : Reward</div>
            <div className="text-[13px] font-bold text-[#38BDF8] mt-0.5">
              1 : {proposal.risk_reward_ratio.toFixed(1)}
            </div>
          </div>

          <div className="px-3 py-2">
            <div className="text-[#707987] text-[9px] uppercase">Exposure ({selectedLots} {selectedLots === 1 ? "Lot" : "Lots"})</div>
            <div className="text-[13px] font-bold text-[#E6E8EB] mt-0.5">
              {currentQuantity} <span className="text-[10px] text-[#707987] font-normal">Qty ({lotSize}/lot)</span>
            </div>
          </div>

          <div className="px-3 py-2">
            <div className="text-[#707987] text-[9px] uppercase">Max Capital Risk</div>
            <div className="text-[13px] font-bold text-[#E5484D] mt-0.5">
              ₹{formatNumber(calculatedMaxLoss, 2)}
            </div>
          </div>
        </div>

        {/* ── 30-SECOND INSPECT: SETUP RATIONALE & INVALIDATION ── */}
        <div className="p-3 bg-[#0E1013] text-[11px]">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-bold text-[#A5ABB4] uppercase tracking-wider font-mono flex items-center gap-1.5">
              <FileCheck2 className="w-3.5 h-3.5 text-[#38BDF8]" />
              Deterministic Rationale & Invalidation Boundary
            </span>
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-[10px] text-[#707987] hover:text-[#E6E8EB] font-mono transition"
            >
              {isExpanded ? "Collapse Details" : "Expand Details"}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {proposal.rationale.slice(0, 3).map((item, idx) => (
              <div
                key={idx}
                className="p-2 rounded-[2px] bg-[#12151A] border border-[#191D23] text-[#C2C7D0] flex items-start gap-2"
              >
                <span className="text-[#38BDF8] font-bold font-mono text-[10px]">0{idx + 1}.</span>
                <p className="leading-snug text-[10.5px]">{item}</p>
              </div>
            ))}
          </div>

          {/* Invalidation Alert */}
          <div className="mt-2 p-2 rounded-[2px] bg-[#E59700]/10 border border-[#E59700]/30 text-[#E59700] flex items-center justify-between gap-2 text-[10.5px]">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-[#F5A623]" />
              <span>
                <strong>Invalidation Trigger:</strong> {proposal.invalidation_condition}
              </span>
            </div>
            <span className="text-[9px] font-mono text-[#A5ABB4] shrink-0">Server-Enforced</span>
          </div>

          {/* Expanded Details: Order Intent & Audit Details */}
          {isExpanded && (
            <div className="mt-2.5 pt-2.5 border-t border-[#191D23] font-mono text-[10px] text-[#A5ABB4] grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <span className="text-[#707987] font-bold block mb-1">PROPOSAL AUDIT METADATA</span>
                <div>Proposal ID: <strong className="text-[#E6E8EB]">{proposal.proposal_id}</strong></div>
                <div>Generated At: {proposal.timestamp}</div>
                <div>Priority Score: {proposal.priority_score} / Quality: {proposal.quality_score}</div>
                {proposal.approval_timestamp && (
                  <div className="text-[#00C896]">Approved At: {proposal.approval_timestamp}</div>
                )}
              </div>

              <div>
                <span className="text-[#707987] font-bold block mb-1">DETERMINISTIC ORDER INTENT</span>
                <div>Exchange/Symbol: NFO:{proposal.contract_symbol.replace(/\s+/g, "")}</div>
                <div>Order Type: LIMIT @ ₹{proposal.entry_price} (Product: {proposal.product || "NRML"})</div>
                <div>Execution Gateway: <strong className="text-[#38BDF8]">AUTHORITATIVE KITE CONNECT ROUTER</strong></div>
              </div>
            </div>
          )}

          {actionMessage && (
            <div className="mt-2 text-[10px] font-mono text-[#38BDF8] bg-[#38BDF8]/10 border border-[#38BDF8]/20 px-2 py-1 rounded-[2px]">
              {actionMessage}
            </div>
          )}
        </div>
      </Surface>

      {/* ── ORDER PREVIEW MODAL ── */}
      {isPreviewModalOpen && proposal && (
        <OrderPreviewModal
          isOpen={isPreviewModalOpen}
          onClose={() => setIsPreviewModalOpen(false)}
          proposal={{
            ...proposal,
            lots: selectedLots,
            total_quantity: currentQuantity,
          }}
          onApproveSuccess={(updatedProp) => {
            setProposal(updatedProp);
            setActionMessage("Trade intent / order recorded successfully.");
          }}
        />
      )}

      {/* ── LIVE ORDER & POSITION LEDGER DRAWER ── */}
      <LivePositionDrawer
        isOpen={isLedgerOpen}
        onClose={() => setIsLedgerOpen(false)}
      />
    </>
  );
};
