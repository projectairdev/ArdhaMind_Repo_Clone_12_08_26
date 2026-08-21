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
  ShieldCheck,
  ShieldAlert,
  Power,
  Zap,
  LogOut,
  FileText,
  DollarSign,
  Lock,
  ExternalLink
} from "lucide-react";
import { Surface, SectionHeader, MetricCell } from "./ui/WorkspacePrimitives";
import { LivePositionDrawer, OrderItem, PositionItem } from "./LivePositionDrawer";
import { TradeLineageModal } from "./TradeLineageModal";
import { ActiveOpportunityHero } from "./ActiveOpportunityHero";

export function PortfolioWorkspace() {
  const [positions, setPositions] = useState<PositionItem[]>([]);
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [journalEntries, setJournalEntries] = useState<any[]>([]);
  const [journalSummary, setJournalSummary] = useState<any>(null);
  const [safetyStatus, setSafetyStatus] = useState<any>(null);
  const [brokerHealth, setBrokerHealth] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isReconciling, setIsReconciling] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  // Modals
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [selectedProposalId, setSelectedProposalId] = useState<string | null>(null);
  const [exitConfirmPos, setExitConfirmPos] = useState<PositionItem | null>(null);
  const [showEmergencyModal, setShowEmergencyModal] = useState<boolean>(false);
  const [isActionLoading, setIsActionLoading] = useState<boolean>(false);

  const fetchPortfolioData = async () => {
    try {
      setLoading(true);
      const [stateRes, journalRes, summaryRes, safetyRes, healthRes] = await Promise.all([
        fetch("/api/phase3/state"),
        fetch("/api/phase3/journal?limit=10"),
        fetch("/api/phase3/journal/analytics/summary"),
        fetch("/api/phase3/safety/status"),
        fetch("/api/broker/health"),
      ]);

      if (stateRes.ok) {
        const s = await stateRes.json();
        setPositions(s.open_positions || []);
        setOrders(s.pending_orders || []);
      }
      if (journalRes.ok) {
        const j = await journalRes.json();
        setJournalEntries(j.entries || []);
      }
      if (summaryRes.ok) {
        const sum = await summaryRes.json();
        setJournalSummary(sum);
      }
      if (safetyRes.ok) {
        const sf = await safetyRes.json();
        setSafetyStatus(sf);
      }
      if (healthRes.ok) {
        const h = await healthRes.json();
        setBrokerHealth(h);
      }
    } catch (err) {
      console.warn("Failed fetching Portfolio data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolioData();

    const handleWs = (evt: MessageEvent) => {
      try {
        const msg = JSON.parse(evt.data);
        if (
          msg.type === "phase3_order_updated" ||
          msg.type === "phase3_positions_updated" ||
          msg.type === "phase3_safety_updated"
        ) {
          fetchPortfolioData();
        }
      } catch {}
    };

    const ws = (window as any).__ARDHA_WS__;
    if (ws && typeof ws.addEventListener === "function") {
      ws.addEventListener("message", handleWs);
      return () => ws.removeEventListener("message", handleWs);
    }
  }, []);

  // Trigger manual reconciliation
  const handleReconcile = async () => {
    try {
      setIsReconciling(true);
      setActionError(null);
      setActionFeedback(null);
      const res = await fetch("/api/phase3/orders/reconcile", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        setActionFeedback("Broker reconciliation sweep completed.");
        fetchPortfolioData();
      } else {
        setActionError(data.error || "Reconciliation failed.");
      }
    } catch (err: any) {
      setActionError(err.message || "Network error during reconciliation.");
    } finally {
      setIsReconciling(false);
    }
  };

  // Toggle Kill Switch
  const handleToggleKillSwitch = async () => {
    const currentState = safetyStatus?.kill_switch_active || false;
    const newState = !currentState;
    try {
      setIsActionLoading(true);
      const res = await fetch("/api/phase3/safety/kill-switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: newState }),
      });
      const data = await res.json();
      if (data.success) {
        setActionFeedback(`Execution Kill Switch ${newState ? "ACTIVATED" : "DEACTIVATED"}`);
        fetchPortfolioData();
      }
    } catch (err: any) {
      setActionError(err.message || "Failed toggling kill switch");
    } finally {
      setIsActionLoading(false);
    }
  };

  // Cancel single order
  const handleCancelOrder = async (orderId: string) => {
    try {
      setIsActionLoading(true);
      setActionError(null);
      const res = await fetch(`/api/phase3/orders/${orderId}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idempotency_key: `IDEMP-CANCEL-${orderId}-${Date.now()}` }),
      });
      const data = await res.json();
      if (data.success) {
        setActionFeedback(`Order cancellation requested: ${orderId}`);
        fetchPortfolioData();
      } else {
        setActionError(data.error || "Order cancellation failed.");
      }
    } catch (err: any) {
      setActionError(err.message || "Error cancelling order");
    } finally {
      setIsActionLoading(false);
    }
  };

  // Single position exit
  const handleConfirmExitPosition = async () => {
    if (!exitConfirmPos) return;
    try {
      setIsActionLoading(true);
      setActionError(null);
      const res = await fetch(`/api/phase3/positions/${exitConfirmPos.position_id}/exit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idempotency_key: `IDEMP-EXIT-${exitConfirmPos.position_id}-${Date.now()}`,
          order_type: "MARKET",
        }),
      });
      const data = await res.json();
      if (data.success) {
        setActionFeedback(`Position exit order routed to Kite: Order ID ${data.exit_order_id}`);
        setExitConfirmPos(null);
        fetchPortfolioData();
      } else {
        setActionError(data.error || "Position exit failed.");
      }
    } catch (err: any) {
      setActionError(err.message || "Error exiting position");
    } finally {
      setIsActionLoading(false);
    }
  };

  // Emergency Close All
  const handleConfirmEmergencyCloseAll = async () => {
    try {
      setIsActionLoading(true);
      setActionError(null);
      const res = await fetch("/api/phase3/positions/exit-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idempotency_key: `IDEMP-CLOSEALL-${Date.now()}` }),
      });
      const data = await res.json();
      if (data.success) {
        setActionFeedback(`Emergency Close All dispatched for ${data.total_positions || 0} positions.`);
        setShowEmergencyModal(false);
        fetchPortfolioData();
      } else {
        setActionError(data.error || "Emergency Close All failed.");
      }
    } catch (err: any) {
      setActionError(err.message || "Error executing emergency close all");
    } finally {
      setIsActionLoading(false);
    }
  };

  const rawHealthStatus = String(brokerHealth?.status || brokerHealth?.connection_status || "").toUpperCase();
  const normalizedBrokerStatus = brokerHealth?.normalized_status || (
    rawHealthStatus === "CONNECTED_VERIFIED" || brokerHealth?.execution_verified === true
      ? "CONNECTED_VERIFIED"
      : brokerHealth?.session_valid === false || brokerHealth?.authenticated === false || rawHealthStatus === "CONNECTED_AUTH_REQUIRED" || brokerHealth?.blocker_code === "AUTH_REQUIRED"
      ? "CONNECTED_AUTH_REQUIRED"
      : rawHealthStatus === "BROKER_STATE_UNVERIFIED" || rawHealthStatus === "RECONNECTING" || rawHealthStatus === "CONNECTED" || brokerHealth?.reconciliation_complete === false
      ? "BROKER_STATE_UNVERIFIED"
      : "DISCONNECTED"
  );
  const isBrokerAuth = normalizedBrokerStatus === "CONNECTED_VERIFIED";
  const isAuthRequired = normalizedBrokerStatus === "CONNECTED_AUTH_REQUIRED";
  const isUnverified = normalizedBrokerStatus === "BROKER_STATE_UNVERIFIED";
  const totalUnrealizedPnl = positions.reduce((acc, p) => acc + (p.unrealized_pnl || 0), 0);

  return (
    <div id="portfolio-workspace" className="space-y-3 font-sans text-left text-[11px]">
      
      {/* ── HEADER BANNER & EXECUTION SAFETY GATES ── */}
      <Surface className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#191D23] bg-[#0E1013] px-3.5 py-2.5">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-6 h-6 rounded bg-[#38BDF8]/10 border border-[#38BDF8]/30 text-[#38BDF8]">
              <Layers size={14} />
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#F1F3F5] font-mono">
                PORTFOLIO & EXECUTION MANAGEMENT
              </span>
              <span className="ml-2 rounded-[2px] bg-[#08090B] px-1.5 py-0.5 text-[9px] font-bold text-[#38BDF8] border border-[#242830] font-mono">
                PHASE 3 ACTIVE
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 font-mono text-[10px]">
            {/* Authoritative Normalized Broker Status */}
            {isAuthRequired ? (
              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                <ShieldAlert size={10} /> AUTH_REQUIRED / BROKER_UNVERIFIED
              </span>
            ) : isUnverified ? (
              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-purple-500/15 text-purple-400 border border-purple-500/30 flex items-center gap-1">
                <ShieldAlert size={10} /> BROKER_STATE_UNVERIFIED
              </span>
            ) : safetyStatus?.kill_switch_active ? (
              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-rose-600/20 text-rose-400 border border-rose-500/40 animate-pulse flex items-center gap-1">
                <Power size={10} /> KILL_SWITCH_ACTIVE
              </span>
            ) : isBrokerAuth ? (
              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                <ShieldCheck size={10} /> BROKER_AUTHENTICATED (KITE)
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30 flex items-center gap-1">
                <ShieldAlert size={10} /> BROKER_DISCONNECTED
              </span>
            )}

            {/* Sync Broker Button */}
            <button
              type="button"
              disabled={isReconciling}
              onClick={handleReconcile}
              className="px-2.5 py-1 rounded bg-[#13161A] hover:bg-[#1A1F2C] text-[#38BDF8] border border-[#38BDF8]/30 font-bold transition flex items-center gap-1.5 disabled:opacity-40"
              title="Run Authoritative Reconciliation Sweep"
            >
              <RefreshCw size={11} className={isReconciling ? "animate-spin" : ""} />
              <span>Sync Broker</span>
            </button>

            {/* Kill Switch Button */}
            <button
              type="button"
              disabled={isActionLoading}
              onClick={handleToggleKillSwitch}
              className={`px-2.5 py-1 rounded font-bold border transition flex items-center gap-1.5 ${
                safetyStatus?.kill_switch_active
                  ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/30"
                  : "bg-rose-500/20 text-rose-400 border-rose-500/30 hover:bg-rose-500/30"
              }`}
            >
              <Power size={11} />
              <span>{safetyStatus?.kill_switch_active ? "Resume Entries" : "Kill Switch"}</span>
            </button>
          </div>
        </div>

        {/* Top Metric Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-[#191D23] bg-[#0B0D10]">
          <MetricCell
            label="Live Open Positions"
            value={`${positions.length} Active`}
            tone={positions.length > 0 ? "positive" : "neutral"}
          />
          <MetricCell
            label="Total Unrealized P&L"
            value={`${totalUnrealizedPnl >= 0 ? "+" : ""}₹${totalUnrealizedPnl.toFixed(2)}`}
            tone={totalUnrealizedPnl >= 0 ? "positive" : "negative"}
          />
          <MetricCell
            label="Daily Realized Loss Gate"
            value={`₹${(safetyStatus?.daily_realized_loss || 0).toFixed(2)} / ₹${(safetyStatus?.daily_loss_limit || 25000).toFixed(0)}`}
            tone={(safetyStatus?.daily_realized_loss || 0) > 0 ? "negative" : "neutral"}
          />
          <MetricCell
            label="Execution State"
            value={safetyStatus?.kill_switch_active ? "BLOCKED (Kill Switch)" : !isBrokerAuth ? "AUTH_REQUIRED" : "PRE-FLIGHT GUARDED"}
            tone={safetyStatus?.kill_switch_active || !isBrokerAuth ? "negative" : "positive"}
          />
        </div>
      </Surface>

      {/* Action feedback / error notifications */}
      {actionFeedback && (
        <div className="p-2.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-mono flex items-center gap-2">
          <CheckCircle2 size={13} className="shrink-0" />
          <span>{actionFeedback}</span>
        </div>
      )}
      {actionError && (
        <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 text-[11px] font-mono flex items-center gap-2">
          <AlertTriangle size={13} className="shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* ── PHASE 3 PROPOSED TRADE ACTION AREA ── */}
      <ActiveOpportunityHero />

      {/* ── ACTIVE POSITIONS SECTION ── */}
      <Surface className="overflow-hidden font-mono">
        <div className="flex items-center justify-between border-b border-[#191D23] bg-[#0E1013] px-3.5 py-2">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#A5ABB4]">
              LIVE BROKER POSITIONS ({positions.length})
            </span>
          </div>
          {positions.length > 0 && (
            <button
              type="button"
              disabled={isActionLoading || !isBrokerAuth}
              onClick={() => setShowEmergencyModal(true)}
              className="px-2 py-0.5 rounded bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 text-[9.5px] font-bold transition flex items-center gap-1"
            >
              <Zap size={10} /> Emergency Close All
            </button>
          )}
        </div>

        {positions.length === 0 ? (
          <div className="py-8 text-center text-[#707987] font-mono text-[11px]">
            0 Open Positions on Broker — Live execution portfolio is currently flat.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[11px]">
              <thead>
                <tr className="border-b border-[#191D23] bg-[#0E1013] text-[9px] uppercase tracking-wider text-[#707987]">
                  <th className="py-2 px-3.5 font-semibold">Contract Symbol</th>
                  <th className="py-2 px-3.5 font-semibold">Product</th>
                  <th className="py-2 px-3.5 font-semibold">Quantity</th>
                  <th className="py-2 px-3.5 font-semibold">Buy Avg</th>
                  <th className="py-2 px-3.5 font-semibold">Live LTP</th>
                  <th className="py-2 px-3.5 font-semibold">Unrealized P&L</th>
                  <th className="py-2 px-3.5 font-semibold">Stop Loss</th>
                  <th className="py-2 px-3.5 font-semibold">Target</th>
                  <th className="py-2 px-3.5 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#191D23]">
                {positions.map((pos) => {
                  const isStopBreached = pos.stop_loss > 0 && pos.current_ltp > 0 && pos.current_ltp <= pos.stop_loss;
                  const isTargetReached = pos.target > 0 && pos.current_ltp >= pos.target;
                  const isPnlPositive = pos.unrealized_pnl >= 0;

                  return (
                    <tr key={pos.position_id} className="hover:bg-[#13161A] transition-colors">
                      <td className="py-2.5 px-3.5 font-bold text-[#F1F3F5] flex items-center gap-1.5">
                        <span>{pos.contract_symbol}</span>
                        {isStopBreached && (
                          <span className="px-1 py-0.2 rounded text-[8px] font-bold bg-rose-600/20 text-rose-400 border border-rose-500/40 animate-pulse">
                            STOP
                          </span>
                        )}
                        {isTargetReached && (
                          <span className="px-1 py-0.2 rounded text-[8px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                            TARGET
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3.5 text-[#848E9C]">{pos.product}</td>
                      <td className="py-2.5 px-3.5 font-bold text-[#E6E8EB]">{pos.quantity}</td>
                      <td className="py-2.5 px-3.5 text-[#E6E8EB]">₹{pos.buy_price.toFixed(2)}</td>
                      <td className="py-2.5 px-3.5 text-[#38BDF8] font-bold">₹{pos.current_ltp.toFixed(2)}</td>
                      <td className={`py-2.5 px-3.5 font-bold ${isPnlPositive ? "text-emerald-400" : "text-rose-400"}`}>
                        {isPnlPositive ? "+" : ""}₹{pos.unrealized_pnl.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3.5 text-rose-400">₹{pos.stop_loss.toFixed(2)}</td>
                      <td className="py-2.5 px-3.5 text-emerald-400">₹{pos.target.toFixed(2)}</td>
                      <td className="py-2.5 px-3.5 text-right space-x-1.5">
                        <button
                          type="button"
                          onClick={() => setSelectedProposalId(pos.order_id)}
                          className="px-2 py-0.5 rounded bg-[#1A1F2C] hover:bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/30 text-[9.5px] font-bold transition"
                          title="Inspect Lineage"
                        >
                          Lineage
                        </button>
                        <button
                          type="button"
                          disabled={isActionLoading || !isBrokerAuth || pos.status === "EXIT_REQUESTED"}
                          onClick={() => setExitConfirmPos(pos)}
                          className="px-2 py-0.5 rounded bg-[#1A1F2C] hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[9.5px] font-bold transition disabled:opacity-40"
                        >
                          Exit
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Surface>

      {/* ── ACTIVE BROKER ORDERS SECTION ── */}
      <Surface className="overflow-hidden font-mono">
        <div className="flex items-center justify-between border-b border-[#191D23] bg-[#0E1013] px-3.5 py-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#A5ABB4]">
            ACTIVE BROKER ORDER BOOK ({orders.length})
          </span>
          <button
            type="button"
            onClick={() => setIsDrawerOpen(true)}
            className="px-2 py-0.5 rounded bg-[#13161A] hover:bg-[#1A1F2C] text-[#38BDF8] border border-[#38BDF8]/30 text-[9.5px] font-bold transition flex items-center gap-1"
          >
            <ExternalLink size={10} /> Open Live Drawer
          </button>
        </div>

        {orders.length === 0 ? (
          <div className="py-6 text-center text-[#707987] font-mono text-[11px]">
            0 Active Orders in Broker Order Book.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[11px]">
              <thead>
                <tr className="border-b border-[#191D23] bg-[#0E1013] text-[9px] uppercase tracking-wider text-[#707987]">
                  <th className="py-2 px-3.5 font-semibold">Contract</th>
                  <th className="py-2 px-3.5 font-semibold">Type</th>
                  <th className="py-2 px-3.5 font-semibold">Product</th>
                  <th className="py-2 px-3.5 font-semibold">Filled / Total</th>
                  <th className="py-2 px-3.5 font-semibold">Limit Price</th>
                  <th className="py-2 px-3.5 font-semibold">Broker ID</th>
                  <th className="py-2 px-3.5 font-semibold">Status</th>
                  <th className="py-2 px-3.5 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#191D23]">
                {orders.map((ord) => {
                  const isCancelable = ["OPEN", "SUBMITTED", "ACKNOWLEDGED", "PARTIALLY_FILLED"].includes(ord.status);
                  return (
                    <tr key={ord.order_id} className="hover:bg-[#13161A] transition-colors">
                      <td className="py-2 px-3.5 font-bold text-[#F1F3F5]">{ord.contract_symbol}</td>
                      <td className="py-2 px-3.5 text-[#848E9C]">{ord.transaction_type} • {ord.order_type}</td>
                      <td className="py-2 px-3.5 text-[#848E9C]">{ord.product}</td>
                      <td className="py-2 px-3.5 font-bold text-[#E6E8EB]">
                        {ord.filled_quantity} / {ord.quantity} (Rem: {ord.remaining_quantity ?? (ord.quantity - ord.filled_quantity)})
                      </td>
                      <td className="py-2 px-3.5 text-[#E6E8EB]">₹{ord.price.toFixed(2)}</td>
                      <td className="py-2 px-3.5 text-[#38BDF8]">{ord.broker_order_id || "PENDING"}</td>
                      <td className="py-2 px-3.5">
                        <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#1A1F2C] text-[#38BDF8] border border-[#38BDF8]/30">
                          {ord.status}
                        </span>
                      </td>
                      <td className="py-2 px-3.5 text-right space-x-1.5">
                        {ord.proposal_id && (
                          <button
                            type="button"
                            onClick={() => setSelectedProposalId(ord.proposal_id)}
                            className="px-2 py-0.5 rounded bg-[#1A1F2C] hover:bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/30 text-[9.5px] font-bold transition"
                          >
                            Lineage
                          </button>
                        )}
                        {isCancelable && (
                          <button
                            type="button"
                            disabled={isActionLoading || !isBrokerAuth}
                            onClick={() => handleCancelOrder(ord.order_id)}
                            className="px-2 py-0.5 rounded bg-[#1A1F2C] hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[9.5px] font-bold transition disabled:opacity-40"
                          >
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Surface>

      {/* ── EXECUTION JOURNAL & PERFORMANCE LINEAGE SUMMARY (M5) ── */}
      <Surface className="overflow-hidden font-mono">
        <div className="flex items-center justify-between border-b border-[#191D23] bg-[#0E1013] px-3.5 py-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#A5ABB4]">
            CLOSED TRADE EXECUTION JOURNAL & LINEAGE (M5)
          </span>
          {journalSummary && (
            <div className="flex items-center gap-3 text-[10px]">
              <span className="text-[#707987]">
                Total Trades: <strong className="text-[#E6E8EB]">{journalSummary.total_trades || 0}</strong>
              </span>
              <span className="text-[#707987]">
                Win Rate: <strong className="text-emerald-400">{journalSummary.win_rate_pct || 0}%</strong>
              </span>
              <span className="text-[#707987]">
                Realized P&L: <strong className={(journalSummary.total_realized_pnl || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}>
                  ₹{(journalSummary.total_realized_pnl || 0).toFixed(2)}
                </strong>
              </span>
            </div>
          )}
        </div>

        {journalEntries.length === 0 ? (
          <div className="py-6 text-center text-[#707987] font-mono text-[11px]">
            No completed trade journal records found for current session.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[11px]">
              <thead>
                <tr className="border-b border-[#191D23] bg-[#0E1013] text-[9px] uppercase tracking-wider text-[#707987]">
                  <th className="py-2 px-3.5 font-semibold">Date</th>
                  <th className="py-2 px-3.5 font-semibold">Contract</th>
                  <th className="py-2 px-3.5 font-semibold">Setup</th>
                  <th className="py-2 px-3.5 font-semibold">Avg Entry</th>
                  <th className="py-2 px-3.5 font-semibold">Avg Exit</th>
                  <th className="py-2 px-3.5 font-semibold">Slippage</th>
                  <th className="py-2 px-3.5 font-semibold">Realized P&L</th>
                  <th className="py-2 px-3.5 font-semibold">R-Multiple</th>
                  <th className="py-2 px-3.5 font-semibold">Reason</th>
                  <th className="py-2 px-3.5 font-semibold text-right">Audit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#191D23]">
                {journalEntries.map((j) => (
                  <tr key={j.journal_id} className="hover:bg-[#13161A] transition-colors">
                    <td className="py-2 px-3.5 text-[#848E9C]">{j.trading_session_date}</td>
                    <td className="py-2 px-3.5 font-bold text-[#F1F3F5]">{j.contract_symbol}</td>
                    <td className="py-2 px-3.5 text-[#848E9C]">{j.setup_type}</td>
                    <td className="py-2 px-3.5 text-[#E6E8EB]">₹{j.weighted_average_entry.toFixed(2)}</td>
                    <td className="py-2 px-3.5 text-[#E6E8EB]">₹{j.weighted_average_exit > 0 ? j.weighted_average_exit.toFixed(2) : "--"}</td>
                    <td className={`py-2 px-3.5 font-bold ${j.entry_slippage_pts > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                      {j.entry_slippage_pts >= 0 ? "+" : ""}{j.entry_slippage_pts.toFixed(1)} pts
                    </td>
                    <td className={`py-2 px-3.5 font-bold ${j.realized_trade_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {j.realized_trade_pnl >= 0 ? "+" : ""}₹{j.realized_trade_pnl.toFixed(2)}
                    </td>
                    <td className="py-2 px-3.5 font-bold text-[#E6E8EB]">{j.realized_r_multiple.toFixed(2)}R</td>
                    <td className="py-2 px-3.5 text-[#707987] text-[10px]">{j.closing_reason}</td>
                    <td className="py-2 px-3.5 text-right">
                      <button
                        type="button"
                        onClick={() => setSelectedProposalId(j.proposal_id)}
                        className="px-2 py-0.5 rounded bg-[#1A1F2C] hover:bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/30 text-[9.5px] font-bold transition"
                      >
                        Inspect Lineage
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Surface>

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
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#1E2330]">
              <button
                type="button"
                onClick={() => setShowEmergencyModal(false)}
                className="px-3 py-1.5 rounded bg-[#1A1F2C] text-[#848E9C] hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isActionLoading}
                onClick={handleConfirmEmergencyCloseAll}
                className="px-4 py-1.5 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-1.5 shadow-lg"
              >
                {isActionLoading ? <RefreshCw size={13} className="animate-spin" /> : <Zap size={13} />}
                Execute Emergency Square-Off
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── LIVE POSITION DRAWER ── */}
      <LivePositionDrawer isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} />

      {/* ── TRADE LINEAGE MODAL ── */}
      {selectedProposalId && (
        <TradeLineageModal
          isOpen={Boolean(selectedProposalId)}
          onClose={() => setSelectedProposalId(null)}
          proposalId={selectedProposalId}
        />
      )}
    </div>
  );
}

export default PortfolioWorkspace;
