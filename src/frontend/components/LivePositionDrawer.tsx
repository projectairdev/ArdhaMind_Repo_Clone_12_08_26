import React, { useState, useEffect } from "react";
import {
  Layers,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Zap,
  Ban,
  Lock,
  LogOut,
  ShieldAlert,
  ShieldCheck,
  Power,
  FileText,
  X
} from "lucide-react";
import { formatNumber } from "../utils/safeHelpers";
import { TradeLineageModal } from "./TradeLineageModal";

export interface OrderItem {
  order_id: string;
  proposal_id: string;
  intent_id: string;
  broker_order_id: string | null;
  contract_symbol: string;
  exchange: string;
  transaction_type: string;
  order_type: string;
  product: string;
  quantity: number;
  filled_quantity: number;
  remaining_quantity?: number;
  price: number;
  average_price: number;
  status: string;
  rejection_reason: string | null;
  cancellation_reason?: string | null;
  provenance?: string;
  placed_at: string;
  updated_at: string;
  raw_payload?: any;
}

export interface PositionItem {
  position_id: string;
  order_id: string;
  contract_symbol: string;
  product: string;
  quantity: number;
  buy_price: number;
  current_ltp: number;
  unrealized_pnl: number;
  stop_loss: number;
  target: number;
  realized_pnl_analytics?: number;
  exit_price?: number | null;
  exit_order_id?: string | null;
  closed_at?: string | null;
  provenance?: string;
  status: string;
  updated_at: string;
}

interface LivePositionDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LivePositionDrawer: React.FC<LivePositionDrawerProps> = ({
  isOpen,
  onClose,
}) => {
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [positions, setPositions] = useState<PositionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"positions" | "orders">("positions");
  const [isActionLoading, setIsActionLoading] = useState<boolean>(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Modals for confirmation & lineage
  const [exitConfirmPos, setExitConfirmPos] = useState<PositionItem | null>(null);
  const [showEmergencyModal, setShowEmergencyModal] = useState<boolean>(false);
  const [emergencyResults, setEmergencyResults] = useState<any[] | null>(null);
  const [selectedProposalForLineage, setSelectedProposalForLineage] = useState<string | null>(null);

  // Safety Status
  const [safetyStatus, setSafetyStatus] = useState<any>(null);
  const [brokerConnected, setBrokerConnected] = useState<boolean>(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [ordRes, posRes, healthRes, safetyRes] = await Promise.all([
        fetch("/api/phase3/orders/recent?limit=25"),
        fetch("/api/phase3/positions"),
        fetch("/api/broker/health"),
        fetch("/api/phase3/safety/status"),
      ]);
      if (ordRes.ok) {
        const ordData = await ordRes.json();
        setOrders(ordData);
      }
      if (posRes.ok) {
        const posData = await posRes.json();
        setPositions(posData);
      }
      if (healthRes.ok) {
        const h = await healthRes.json();
        setBrokerConnected(h.status === "CONNECTED_VERIFIED" || h.execution_verified === true);
      }
      if (safetyRes.ok) {
        const s = await safetyRes.json();
        setSafetyStatus(s);
      }
    } catch (err) {
      console.warn("Failed to fetch orders/positions/safety:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchData();
    }

    const handleWs = (evt: MessageEvent) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === "phase3_order_updated" && msg.data) {
          setOrders((prev) => {
            const idx = prev.findIndex((o) => o.order_id === msg.data.order_id);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = { ...updated[idx], ...msg.data };
              return updated;
            }
            return [msg.data, ...prev];
          });
        }
        if (msg.type === "phase3_positions_updated" && Array.isArray(msg.data)) {
          setPositions(msg.data);
        }
        if (msg.type === "phase3_safety_updated") {
          fetchData();
        }
      } catch {}
    };

    const ws = (window as any).__ARDHA_WS__;
    if (ws && typeof ws.addEventListener === "function") {
      ws.addEventListener("message", handleWs);
      return () => ws.removeEventListener("message", handleWs);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Action: Toggle Kill Switch
  const handleToggleKillSwitch = async () => {
    const currentState = safetyStatus?.kill_switch_active || false;
    const newState = !currentState;
    try {
      setIsActionLoading(true);
      const res = await fetch("/api/phase3/safety/kill-switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: newState })
      });
      const data = await res.json();
      if (data.success) {
        setActionFeedback(`Execution Kill Switch ${newState ? "ACTIVATED" : "DEACTIVATED"}`);
        fetchData();
      }
    } catch (err: any) {
      setActionError(err.message || "Failed to toggle kill switch");
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Cancel Order
  const handleCancelOrder = async (orderId: string) => {
    try {
      setIsActionLoading(true);
      setActionError(null);
      setActionFeedback(null);
      const res = await fetch(`/api/phase3/orders/${orderId}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idempotency_key: `IDEMP-CANCEL-${orderId}-${Date.now()}`
        })
      });
      const data = await res.json();
      if (data.success) {
        setActionFeedback(`Order cancellation requested: ${orderId}`);
        fetchData();
      } else {
        setActionError(data.error || "Order cancellation failed.");
      }
    } catch (err: any) {
      setActionError(err.message || "Network error during cancellation.");
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Exit Single Position
  const handleConfirmExitPosition = async () => {
    if (!exitConfirmPos) return;
    try {
      setIsActionLoading(true);
      setActionError(null);
      setActionFeedback(null);
      const res = await fetch(`/api/phase3/positions/${exitConfirmPos.position_id}/exit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idempotency_key: `IDEMP-EXIT-${exitConfirmPos.position_id}-${Date.now()}`,
          order_type: "MARKET"
        })
      });
      const data = await res.json();
      if (data.success) {
        setActionFeedback(`Position exit order routed to Kite: Order ID ${data.exit_order_id}`);
        setExitConfirmPos(null);
        fetchData();
      } else {
        setActionError(data.error || "Position exit failed.");
      }
    } catch (err: any) {
      setActionError(err.message || "Network error during position exit.");
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Emergency Close All
  const handleConfirmEmergencyCloseAll = async () => {
    try {
      setIsActionLoading(true);
      setActionError(null);
      setActionFeedback(null);
      const res = await fetch("/api/phase3/positions/exit-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idempotency_key: `IDEMP-CLOSEALL-${Date.now()}`
        })
      });
      const data = await res.json();
      if (data.success) {
        setEmergencyResults(data.results || []);
        setActionFeedback(`Emergency Close All dispatched! Processed ${data.total_positions || 0} open positions.`);
        fetchData();
      } else {
        setActionError(data.error || "Emergency close all failed.");
      }
    } catch (err: any) {
      setActionError(err.message || "Network error during emergency close all.");
    } finally {
      setIsActionLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const s = (status || "").toUpperCase();
    switch (s) {
      case "FILLED":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 size={10} /> FILLED
          </span>
        );
      case "PARTIALLY_FILLED":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-blue-500/15 text-blue-400 border border-blue-500/30">
            <Activity size={10} /> PARTIAL FILL
          </span>
        );
      case "OPEN":
      case "SUBMITTED":
      case "ACKNOWLEDGED":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/30">
            <Activity size={10} /> {s}
          </span>
        );
      case "CANCEL_REQUESTED":
      case "EXIT_REQUESTED":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <Clock size={10} className="animate-spin" /> {s}
          </span>
        );
      case "CANCEL_OUTCOME_UNVERIFIED":
      case "EXIT_OUTCOME_UNVERIFIED":
      case "SUBMISSION_OUTCOME_UNVERIFIED":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-purple-500/15 text-purple-400 border border-purple-500/30">
            <AlertTriangle size={10} /> UNVERIFIED
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-gray-500/15 text-[#848E9C] border border-gray-500/30">
            CANCELLED
          </span>
        );
      case "REJECTED":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <XCircle size={10} /> REJECTED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#1E2330] text-[#848E9C]">
            {s}
          </span>
        );
    }
  };

  const getProvenanceBadge = (prov?: string) => {
    if (!prov || prov === "ARDHAMIND") return null;
    return (
      <span className="px-1.5 py-0.2 rounded text-[8.5px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
        {prov === "BROKER_RMS" ? "RMS SQUARE-OFF" : "EXTERNAL BROKER"}
      </span>
    );
  };

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-xs p-0 sm:p-4 animate-in fade-in duration-150">
        <div className="w-full sm:max-w-2xl h-full sm:h-auto sm:max-h-[90vh] bg-[#0E1117] border-l sm:border border-[#232834] sm:rounded-xl shadow-2xl flex flex-col overflow-hidden text-left font-sans text-[12px] text-[#E6E8EB]">
          
          {/* ── HEADER ── */}
          <div className="flex items-center justify-between border-b border-[#1E2330] bg-[#141822] px-4 py-3">
            <div className="flex items-center gap-2.5">
              <div className="flex items-center justify-center w-7 h-7 rounded-md bg-[#38BDF8]/10 border border-[#38BDF8]/30 text-[#38BDF8]">
                <Layers size={16} />
              </div>
              <div>
                <span className="font-mono font-bold tracking-wider text-[13px] text-[#F1F3F5]">
                  TRADE MANAGEMENT & POSITION LEDGER
                </span>
                <p className="text-[10px] text-[#848E9C] font-mono mt-0.5">
                  Execution Safety Circuit Breakers • Lineage Projections • Persistent Idempotency
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={fetchData}
                className="p-1 rounded-md text-[#848E9C] hover:text-white hover:bg-[#1E2330] transition-colors"
                title="Refresh Ledger"
              >
                <RefreshCw size={14} className={loading ? "animate-spin text-[#38BDF8]" : ""} />
              </button>
              <button
                type="button"
                onClick={onClose}
                className="p-1 rounded-md text-[#848E9C] hover:text-white hover:bg-[#1E2330] transition-colors"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* ── SAFETY & CIRCUIT BREAKER BAR ── */}
          <div className="flex items-center justify-between bg-[#0B0E14] border-b border-[#1E2330] px-4 py-2 font-mono text-[10.5px]">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="text-[#707987]">Daily Loss Gate:</span>
                <span className={`font-bold ${safetyStatus?.daily_realized_loss > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                  ₹{safetyStatus?.daily_realized_loss?.toFixed(2) || "0.00"} / ₹{safetyStatus?.daily_loss_limit?.toFixed(0) || "25000"}
                </span>
              </div>

              {safetyStatus?.kill_switch_active && (
                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-600/20 text-rose-400 border border-rose-500/40 animate-pulse flex items-center gap-1">
                  <Power size={10} /> KILL SWITCH ACTIVE
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={isActionLoading}
                onClick={handleToggleKillSwitch}
                className={`px-2 py-0.5 rounded text-[9.5px] font-bold border transition flex items-center gap-1 ${
                  safetyStatus?.kill_switch_active
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/30"
                    : "bg-rose-500/20 text-rose-400 border-rose-500/30 hover:bg-rose-500/30"
                }`}
              >
                <Power size={10} />
                {safetyStatus?.kill_switch_active ? "Deactivate Kill Switch" : "Activate Kill Switch"}
              </button>
            </div>
          </div>

          {/* ── BROKER HEALTH WARNING BANNER ── */}
          {!brokerConnected && (
            <div className="flex items-center justify-between bg-rose-500/15 border-b border-rose-500/30 px-4 py-2 text-rose-400 font-mono text-[11px]">
              <div className="flex items-center gap-2">
                <ShieldAlert size={14} className="shrink-0" />
                <span>
                  <strong>BROKER_STATE_UNVERIFIED:</strong> Kite session offline. New entries & order mutations locked.
                </span>
              </div>
            </div>
          )}

          {/* ── TABS & EMERGENCY ACTION ── */}
          <div className="flex items-center justify-between border-b border-[#1E2330] bg-[#0F121A] px-4">
            <div className="flex items-center">
              <button
                type="button"
                onClick={() => setActiveTab("positions")}
                className={`py-2.5 px-4 font-mono text-[11px] font-bold border-b-2 transition-colors ${
                  activeTab === "positions"
                    ? "border-[#38BDF8] text-[#38BDF8]"
                    : "border-transparent text-[#707987] hover:text-[#E6E8EB]"
                }`}
              >
                Open Positions ({positions.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("orders")}
                className={`py-2.5 px-4 font-mono text-[11px] font-bold border-b-2 transition-colors ${
                  activeTab === "orders"
                    ? "border-[#38BDF8] text-[#38BDF8]"
                    : "border-transparent text-[#707987] hover:text-[#E6E8EB]"
                }`}
              >
                Broker Orders ({orders.length})
              </button>
            </div>

            {positions.length > 0 && (
              <button
                type="button"
                disabled={isActionLoading || !brokerConnected}
                onClick={() => setShowEmergencyModal(true)}
                className="px-2.5 py-1 rounded bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 font-mono text-[10px] font-bold transition flex items-center gap-1.5 disabled:opacity-40"
              >
                <Zap size={11} />
                Emergency Close All
              </button>
            )}
          </div>

          {/* ── FEEDBACK / ERROR NOTIFICATIONS ── */}
          {actionFeedback && (
            <div className="m-3 p-2.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-mono flex items-center gap-2">
              <CheckCircle2 size={13} className="shrink-0" />
              <span>{actionFeedback}</span>
            </div>
          )}
          {actionError && (
            <div className="m-3 p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 text-[11px] font-mono flex items-center gap-2">
              <AlertTriangle size={13} className="shrink-0" />
              <span>{actionError}</span>
            </div>
          )}

          {/* ── CONTENT BODY ── */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            
            {/* POSITIONS TAB */}
            {activeTab === "positions" && (
              <div className="space-y-2.5">
                {positions.length === 0 ? (
                  <div className="text-center py-10 text-[#707987] font-mono text-[11px]">
                    No active open positions on broker.
                  </div>
                ) : (
                  positions.map((pos) => {
                    const isStopBreached = pos.stop_loss > 0 && pos.current_ltp > 0 && pos.current_ltp <= pos.stop_loss;
                    const isTargetReached = pos.target > 0 && pos.current_ltp >= pos.target;
                    const isPnlPositive = pos.unrealized_pnl >= 0;

                    return (
                      <div
                        key={pos.position_id}
                        className="bg-[#12151E] border border-[#1E2330] rounded-lg p-3 space-y-2.5 font-mono text-[11px]"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-[#F1F3F5] text-[12px]">
                              {pos.contract_symbol}
                            </span>
                            <span className="text-[10px] text-[#707987] px-1.5 py-0.2 rounded bg-[#1A1F2C]">
                              {pos.product} • {pos.quantity} Qty
                            </span>
                            {getProvenanceBadge(pos.provenance)}
                          </div>

                          <div className="flex items-center gap-2">
                            {/* Lineage Modal Trigger */}
                            <button
                              type="button"
                              onClick={() => setSelectedProposalForLineage(pos.order_id)}
                              className="px-1.5 py-0.5 rounded bg-[#1A1F2C] hover:bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/30 text-[9.5px] font-bold transition flex items-center gap-1"
                              title="Inspect Full Trade Lineage"
                            >
                              <FileText size={10} /> Lineage
                            </button>

                            {/* Advisory Badges */}
                            {isStopBreached && (
                              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-600/20 text-rose-400 border border-rose-500/40 animate-pulse">
                                <AlertTriangle size={10} /> STOP LOSS ALERT
                              </span>
                            )}
                            {isTargetReached && (
                              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                                <CheckCircle2 size={10} /> TARGET REACHED
                              </span>
                            )}

                            <button
                              type="button"
                              disabled={isActionLoading || !brokerConnected || pos.status === "EXIT_REQUESTED"}
                              onClick={() => setExitConfirmPos(pos)}
                              className="px-2 py-0.5 rounded bg-[#1A1F2C] hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-bold transition flex items-center gap-1 disabled:opacity-40"
                            >
                              <LogOut size={10} /> Exit
                            </button>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-[10px] text-[#848E9C]">
                          <div>
                            <span className="text-[#707987] block">Buy Avg:</span>
                            <span className="text-[#E6E8EB] font-bold">₹{pos.buy_price.toFixed(2)}</span>
                          </div>
                          <div>
                            <span className="text-[#707987] block">Live LTP:</span>
                            <span className="text-[#38BDF8] font-bold">₹{pos.current_ltp.toFixed(2)}</span>
                          </div>
                          <div>
                            <span className="text-[#707987] block">Unrealized P&L:</span>
                            <span className={`font-bold ${isPnlPositive ? "text-emerald-400" : "text-rose-400"}`}>
                              {isPnlPositive ? "+" : ""}₹{pos.unrealized_pnl.toFixed(2)}
                            </span>
                          </div>
                          <div>
                            <span className="text-[#707987] block">Stop Loss:</span>
                            <span className="text-rose-400 font-bold">₹{pos.stop_loss.toFixed(2)}</span>
                          </div>
                          <div>
                            <span className="text-[#707987] block">Target:</span>
                            <span className="text-emerald-400 font-bold">₹{pos.target.toFixed(2)}</span>
                          </div>
                        </div>

                        {pos.status === "EXIT_REQUESTED" && (
                          <div className="p-1.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[10px] flex items-center gap-1.5">
                            <Clock size={11} className="animate-spin" />
                            <span>Exit order submitted to broker. Awaiting reconciliation...</span>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* ORDERS TAB */}
            {activeTab === "orders" && (
              <div className="space-y-2.5">
                {orders.length === 0 ? (
                  <div className="text-center py-10 text-[#707987] font-mono text-[11px]">
                    No broker order records found in database.
                  </div>
                ) : (
                  orders.map((ord) => {
                    const isCancelable = ["OPEN", "SUBMITTED", "ACKNOWLEDGED", "PARTIALLY_FILLED"].includes(ord.status);

                    return (
                      <div
                        key={ord.order_id}
                        className="bg-[#12151E] border border-[#1E2330] rounded-lg p-3 space-y-2 font-mono text-[11px]"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-[#F1F3F5] text-[12px]">
                              {ord.contract_symbol}
                            </span>
                            <span className="text-[10px] text-[#707987] px-1.5 py-0.2 rounded bg-[#1A1F2C]">
                              {ord.product} • {ord.transaction_type} • {ord.order_type}
                            </span>
                            {getProvenanceBadge(ord.provenance)}
                          </div>

                          <div className="flex items-center gap-2">
                            {getStatusBadge(ord.status)}
                            {ord.proposal_id && (
                              <button
                                type="button"
                                onClick={() => setSelectedProposalForLineage(ord.proposal_id)}
                                className="px-1.5 py-0.5 rounded bg-[#1A1F2C] hover:bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/30 text-[9.5px] font-bold transition flex items-center gap-1"
                                title="Inspect Full Trade Lineage"
                              >
                                <FileText size={10} /> Lineage
                              </button>
                            )}
                            {isCancelable && (
                              <button
                                type="button"
                                disabled={isActionLoading || !brokerConnected}
                                onClick={() => handleCancelOrder(ord.order_id)}
                                className="px-2 py-0.5 rounded bg-[#1A1F2C] hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-bold transition disabled:opacity-40"
                              >
                                Cancel
                              </button>
                            )}
                          </div>
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px] text-[#848E9C]">
                          <div>
                            <span className="text-[#707987] block">Filled / Total Qty:</span>
                            <span className="text-[#E6E8EB] font-bold">
                              {ord.filled_quantity} / {ord.quantity} (Rem: {ord.remaining_quantity ?? (ord.quantity - ord.filled_quantity)})
                            </span>
                          </div>
                          <div>
                            <span className="text-[#707987] block">Limit / Avg Price:</span>
                            <span className="text-[#E6E8EB] font-bold">
                              ₹{ord.price.toFixed(2)} / ₹{ord.average_price > 0 ? ord.average_price.toFixed(2) : "--"}
                            </span>
                          </div>
                          <div>
                            <span className="text-[#707987] block">Broker Order ID:</span>
                            <span className="text-[#38BDF8] font-bold">
                              {ord.broker_order_id || "PENDING"}
                            </span>
                          </div>
                          <div>
                            <span className="text-[#707987] block">Placed Time:</span>
                            <span className="text-[#E6E8EB]">
                              {ord.placed_at ? new Date(ord.placed_at).toLocaleTimeString() : "--"}
                            </span>
                          </div>
                        </div>

                        {ord.cancellation_reason && (
                          <div className="p-1.5 rounded bg-gray-500/10 border border-gray-500/20 text-[#848E9C] text-[10px]">
                            <strong>Cancel Note:</strong> {ord.cancellation_reason}
                          </div>
                        )}
                        {ord.rejection_reason && (
                          <div className="p-1.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[10px]">
                            <strong>Rejection:</strong> {ord.rejection_reason}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </div>

          {/* ── MODAL: SINGLE POSITION EXIT CONFIRMATION ── */}
          {exitConfirmPos && (
            <div className="fixed inset-0 z-60 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 animate-in fade-in duration-100">
              <div className="w-full max-w-md bg-[#12151E] border border-rose-500/40 rounded-lg p-4 space-y-3 font-mono text-[11px] text-left">
                <div className="flex items-center gap-2 text-rose-400 font-bold text-[12px]">
                  <LogOut size={16} />
                  <span>CONFIRM POSITION EXIT (SQUARE-OFF)</span>
                </div>
                <p className="text-[#C2C7D0] leading-relaxed">
                  Submit an offsetting MARKET order to Zerodha Kite to close position:
                  <br />
                  <strong className="text-[#F1F3F5]">{exitConfirmPos.contract_symbol}</strong>
                  <br />
                  Quantity: <strong className="text-[#38BDF8]">{exitConfirmPos.quantity} units</strong> ({exitConfirmPos.product})
                  <br />
                  Current LTP: ₹{exitConfirmPos.current_ltp.toFixed(2)} • Est. Unrealized P&L: ₹{exitConfirmPos.unrealized_pnl.toFixed(2)}
                </p>
                <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#1E2330]">
                  <button
                    type="button"
                    onClick={() => setExitConfirmPos(null)}
                    className="px-3 py-1 rounded bg-[#1A1F2C] text-[#848E9C] hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={isActionLoading}
                    onClick={handleConfirmExitPosition}
                    className="px-4 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-1.5"
                  >
                    {isActionLoading ? <RefreshCw size={12} className="animate-spin" /> : <Zap size={12} />}
                    Confirm Exit
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ── MODAL: EMERGENCY CLOSE ALL CONFIRMATION ── */}
          {showEmergencyModal && (
            <div className="fixed inset-0 z-60 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 animate-in fade-in duration-100">
              <div className="w-full max-w-lg bg-[#141822] border border-rose-600 rounded-lg p-5 space-y-4 font-mono text-[11px] text-left">
                <div className="flex items-center gap-2 text-rose-500 font-bold text-[13px]">
                  <AlertTriangle size={18} />
                  <span>EMERGENCY CLOSE ALL POSITIONS</span>
                </div>
                <p className="text-[#E6E8EB] leading-relaxed">
                  This will immediately submit market square-off orders for <strong>ALL {positions.length} ACTIVE POSITIONS</strong> directly to Zerodha Kite Connect.
                </p>

                {emergencyResults && (
                  <div className="p-2.5 rounded bg-[#0E1117] border border-[#232834] max-h-40 overflow-y-auto space-y-1.5 text-[10px]">
                    {emergencyResults.map((r, i) => (
                      <div key={i} className="flex items-center justify-between">
                        <span>{r.tradingsymbol} ({r.quantity} {r.product}):</span>
                        <span className={r.status === "SUBMITTED" ? "text-emerald-400 font-bold" : "text-rose-400"}>
                          {r.status} {r.broker_order_id ? `(#${r.broker_order_id})` : r.error || ""}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#1E2330]">
                  <button
                    type="button"
                    onClick={() => {
                      setShowEmergencyModal(false);
                      setEmergencyResults(null);
                    }}
                    className="px-3 py-1.5 rounded bg-[#1A1F2C] text-[#848E9C] hover:text-white"
                  >
                    Close
                  </button>
                  {!emergencyResults && (
                    <button
                      type="button"
                      disabled={isActionLoading}
                      onClick={handleConfirmEmergencyCloseAll}
                      className="px-4 py-1.5 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-1.5 shadow-lg"
                    >
                      {isActionLoading ? <RefreshCw size={13} className="animate-spin" /> : <Zap size={13} />}
                      Execute Emergency Square-Off
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* ── TRADE LINEAGE MODAL ── */}
      {selectedProposalForLineage && (
        <TradeLineageModal
          isOpen={Boolean(selectedProposalForLineage)}
          onClose={() => setSelectedProposalForLineage(null)}
          proposalId={selectedProposalForLineage}
        />
      )}
    </>
  );
};
