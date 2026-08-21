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
  ArrowRight,
  ShieldCheck,
  Zap,
  Tag,
  MessageSquare,
  Plus,
  X,
  FileText,
  DollarSign
} from "lucide-react";

export interface JournalRecord {
  journal_id: string;
  proposal_id: string;
  source_opportunity_id?: string;
  trading_session_date: string;
  underlying: string;
  contract_symbol: string;
  expiry?: string;
  strike?: number;
  option_type?: string;
  direction: string;
  setup_type: string;
  proposal_created_at: string;
  approved_at?: string;
  entry_submitted_at?: string;
  opened_at?: string;
  closed_at?: string;
  duration_seconds?: number;
  entry_order_ids: string[];
  exit_order_ids: string[];
  entry_fills: any[];
  exit_fills: any[];
  proposed_entry: number;
  weighted_average_entry: number;
  proposed_stop: number;
  proposed_target_1: number;
  proposed_target_2: number;
  weighted_average_exit: number;
  entry_quantity: number;
  exit_quantity: number;
  confidence_at_entry: number;
  priority_at_entry: number;
  market_regime_at_entry?: string;
  briefing_id_at_entry?: string;
  scenario_id_at_entry?: string;
  prediction_snapshot_id_at_entry?: string;
  closing_reason: string;
  trader_overrides: string[];
  provenance: string;
  entry_slippage_pts: number;
  entry_slippage_pct: number;
  exit_slippage_pts: number;
  exit_slippage_pct: number;
  hold_duration: number;
  planned_risk: number;
  realized_trade_pnl: number;
  planned_rr: number;
  realized_r_multiple: number;
  status: string;
  notes?: any[];
}

interface TradeLineageModalProps {
  isOpen: boolean;
  onClose: () => void;
  proposalId?: string;
  journalId?: string;
}

export const TradeLineageModal: React.FC<TradeLineageModalProps> = ({
  isOpen,
  onClose,
  proposalId,
  journalId,
}) => {
  const [journal, setJournal] = useState<JournalRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [newNoteText, setNewNoteText] = useState<string>("");
  const [newNoteTag, setNewNoteTag] = useState<string>("");
  const [isSubmittingNote, setIsSubmittingNote] = useState<boolean>(false);

  const fetchJournal = async () => {
    try {
      setLoading(true);
      let url = "";
      if (journalId) {
        url = `/api/phase3/journal/${journalId}`;
      } else if (proposalId) {
        url = `/api/phase3/journal/JRN-${proposalId}`;
      }
      if (!url) return;

      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setJournal(data);
      }
    } catch (err) {
      console.warn("Failed to fetch journal lineage:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && (proposalId || journalId)) {
      fetchJournal();
    }
  }, [isOpen, proposalId, journalId]);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!journal || !newNoteText.trim()) return;
    try {
      setIsSubmittingNote(true);
      const tags = newNoteTag.trim() ? [newNoteTag.trim()] : ["REVIEW"];
      const res = await fetch(`/api/phase3/journal/${journal.journal_id}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note_text: newNoteText.trim(), tags })
      });
      if (res.ok) {
        setNewNoteText("");
        setNewNoteTag("");
        fetchJournal();
      }
    } catch (err) {
      console.warn("Failed to add note:", err);
    } finally {
      setIsSubmittingNote(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-70 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-3xl bg-[#0E1117] border border-[#232834] rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden text-left font-sans text-[12px] text-[#E6E8EB]">
        
        {/* ── HEADER ── */}
        <div className="flex items-center justify-between border-b border-[#1E2330] bg-[#141822] px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-7 h-7 rounded-md bg-[#38BDF8]/10 border border-[#38BDF8]/30 text-[#38BDF8]">
              <Layers size={16} />
            </div>
            <div>
              <span className="font-mono font-bold tracking-wider text-[13px] text-[#F1F3F5]">
                TRADE EXECUTION LINEAGE & JOURNAL
              </span>
              <p className="text-[10px] text-[#848E9C] font-mono mt-0.5">
                Immutable Lifecycle • Fill-Weighted Analytics • Directional Slippage
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={fetchJournal}
              className="p-1 rounded-md text-[#848E9C] hover:text-white hover:bg-[#1E2330] transition-colors"
              title="Refresh Lineage"
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

        {/* ── BODY ── */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {loading && !journal ? (
            <div className="text-center py-12 text-[#707987] font-mono text-[11px] flex items-center justify-center gap-2">
              <RefreshCw size={14} className="animate-spin text-[#38BDF8]" />
              <span>Loading trade execution lineage...</span>
            </div>
          ) : !journal ? (
            <div className="text-center py-12 text-[#707987] font-mono text-[11px]">
              No trade journal lineage found for this record.
            </div>
          ) : (
            <>
              {/* ── METADATA BAR ── */}
              <div className="bg-[#12151E] border border-[#1E2330] rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-3 font-mono text-[11px]">
                <div className="flex items-center gap-2.5">
                  <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/30">
                    {journal.contract_symbol}
                  </span>
                  <span className="text-[#848E9C]">
                    Setup: <strong className="text-[#E6E8EB]">{journal.setup_type}</strong>
                  </span>
                  <span className="text-[#848E9C]">
                    Session: <strong className="text-[#E6E8EB]">{journal.trading_session_date}</strong>
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#1A1F2C] text-[#848E9C]">
                    Reason: {journal.closing_reason}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#1A1F2C] text-[#848E9C]">
                    Origin: {journal.provenance}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    journal.status === "CLOSED"
                      ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                      : "bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/30"
                  }`}>
                    {journal.status}
                  </span>
                </div>
              </div>

              {/* ── LIFECYCLE PROGRESSION CARDS ── */}
              <div className="bg-[#141822] border border-[#1E2330] rounded-lg p-4 font-mono text-[10px] space-y-3">
                <div className="text-[#848E9C] font-bold uppercase tracking-wider text-[10px]">
                  EXECUTION LIFECYCLE LINEAGE
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5">
                  {/* Phase 1: Opportunity & Proposal */}
                  <div className="bg-[#0E1117] border border-[#1E2330] rounded p-2.5 space-y-1">
                    <div className="text-[#38BDF8] font-bold flex items-center gap-1">
                      <Zap size={11} /> 1. PROPOSAL
                    </div>
                    <div className="text-[#848E9C]">ID: <span className="text-[#E6E8EB]">{journal.proposal_id.slice(0, 14)}...</span></div>
                    <div className="text-[#848E9C]">Created: <span className="text-[#E6E8EB]">{journal.proposal_created_at ? new Date(journal.proposal_created_at).toLocaleTimeString() : "--"}</span></div>
                    <div className="text-[#848E9C]">Confidence: <span className="text-emerald-400">{(journal.confidence_at_entry * 100).toFixed(0)}%</span></div>
                  </div>

                  {/* Phase 2: Approval */}
                  <div className="bg-[#0E1117] border border-[#1E2330] rounded p-2.5 space-y-1">
                    <div className="text-[#38BDF8] font-bold flex items-center gap-1">
                      <ShieldCheck size={11} /> 2. APPROVAL
                    </div>
                    <div className="text-[#848E9C]">Approved: <span className="text-[#E6E8EB]">{journal.approved_at ? new Date(journal.approved_at).toLocaleTimeString() : "PENDING"}</span></div>
                    <div className="text-[#848E9C]">Planned Entry: <span className="text-[#E6E8EB]">₹{journal.proposed_entry.toFixed(2)}</span></div>
                    <div className="text-[#848E9C]">Planned Stop: <span className="text-rose-400">₹{journal.proposed_stop.toFixed(2)}</span></div>
                  </div>

                  {/* Phase 3: Live Broker Entry */}
                  <div className="bg-[#0E1117] border border-[#1E2330] rounded p-2.5 space-y-1">
                    <div className="text-[#38BDF8] font-bold flex items-center gap-1">
                      <Activity size={11} /> 3. BROKER ENTRY
                    </div>
                    <div className="text-[#848E9C]">Orders: <span className="text-[#E6E8EB]">{journal.entry_order_ids.length} orders</span></div>
                    <div className="text-[#848E9C]">Avg Fill: <span className="text-[#38BDF8] font-bold">₹{journal.weighted_average_entry.toFixed(2)}</span></div>
                    <div className="text-[#848E9C]">Slippage: <span className={journal.entry_slippage_pts > 0 ? "text-rose-400" : "text-emerald-400"}>{journal.entry_slippage_pts >= 0 ? "+" : ""}{journal.entry_slippage_pts} pts</span></div>
                  </div>

                  {/* Phase 4: Position Exit & Outcome */}
                  <div className="bg-[#0E1117] border border-[#1E2330] rounded p-2.5 space-y-1">
                    <div className="text-[#38BDF8] font-bold flex items-center gap-1">
                      <CheckCircle2 size={11} /> 4. EXIT & OUTCOME
                    </div>
                    <div className="text-[#848E9C]">Avg Exit: <span className="text-[#E6E8EB]">₹{journal.weighted_average_exit > 0 ? journal.weighted_average_exit.toFixed(2) : "--"}</span></div>
                    <div className="text-[#848E9C]">Realized P&L: <span className={`font-bold ${journal.realized_trade_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>₹{journal.realized_trade_pnl.toFixed(2)}</span></div>
                    <div className="text-[#848E9C]">Realized R: <span className="text-[#E6E8EB] font-bold">{journal.realized_r_multiple.toFixed(2)}R</span></div>
                  </div>
                </div>
              </div>

              {/* ── EXECUTION QUALITY METRICS ── */}
              <div className="bg-[#12151E] border border-[#1E2330] rounded-lg p-4 font-mono text-[11px] space-y-2.5">
                <div className="text-[#848E9C] font-bold uppercase tracking-wider text-[10px]">
                  OBJECTIVE EXECUTION QUALITY & SLIPPAGE
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[10px]">
                  <div>
                    <span className="text-[#707987] block">Entry Slippage:</span>
                    <span className={`font-bold ${journal.entry_slippage_pts > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                      {journal.entry_slippage_pts >= 0 ? "+" : ""}{journal.entry_slippage_pts.toFixed(2)} pts ({journal.entry_slippage_pct.toFixed(2)}%)
                    </span>
                  </div>
                  <div>
                    <span className="text-[#707987] block">Exit Slippage:</span>
                    <span className={`font-bold ${journal.exit_slippage_pts > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                      {journal.exit_slippage_pts >= 0 ? "+" : ""}{journal.exit_slippage_pts.toFixed(2)} pts ({journal.exit_slippage_pct.toFixed(2)}%)
                    </span>
                  </div>
                  <div>
                    <span className="text-[#707987] block">Planned Risk (INR):</span>
                    <span className="text-[#E6E8EB] font-bold">₹{journal.planned_risk.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-[#707987] block">Duration:</span>
                    <span className="text-[#E6E8EB]">
                      {journal.duration_seconds ? `${Math.round(journal.duration_seconds)}s` : "--"}
                    </span>
                  </div>
                </div>
              </div>

              {/* ── TRADER NOTES (MUTABLE LOG) ── */}
              <div className="bg-[#12151E] border border-[#1E2330] rounded-lg p-4 font-mono text-[11px] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-[#848E9C] font-bold uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                    <MessageSquare size={12} /> TRADER POST-MORTEM NOTES ({journal.notes?.length || 0})
                  </div>
                </div>

                {journal.notes && journal.notes.length > 0 ? (
                  <div className="space-y-2 max-h-36 overflow-y-auto">
                    {journal.notes.map((n: any) => (
                      <div key={n.note_id} className="p-2.5 rounded bg-[#0E1117] border border-[#1E2330] space-y-1">
                        <div className="flex items-center justify-between text-[9px] text-[#707987]">
                          <span>{new Date(n.created_at).toLocaleString()}</span>
                          <span className="px-1.5 py-0.2 rounded bg-[#1A1F2C] text-[#38BDF8]">
                            {n.tags?.join(", ") || "GENERAL"}
                          </span>
                        </div>
                        <p className="text-[#E6E8EB] text-[11px] leading-relaxed">{n.note_text}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-[#707987] text-[10px]">No notes recorded yet. Add a review note below.</div>
                )}

                {/* Add Note Form */}
                <form onSubmit={handleAddNote} className="space-y-2 pt-2 border-t border-[#1E2330]">
                  <textarea
                    rows={2}
                    value={newNoteText}
                    onChange={(e) => setNewNoteText(e.target.value)}
                    placeholder="Enter post-trade analysis, execution discipline notes, or observations..."
                    className="w-full bg-[#0E1117] border border-[#1E2330] rounded p-2 text-[#E6E8EB] text-[11px] focus:outline-hidden focus:border-[#38BDF8]"
                  />
                  <div className="flex items-center justify-between gap-2">
                    <input
                      type="text"
                      value={newNoteTag}
                      onChange={(e) => setNewNoteTag(e.target.value)}
                      placeholder="Tag (e.g. SLIPPAGE, DISCIPLINE)"
                      className="bg-[#0E1117] border border-[#1E2330] rounded px-2 py-1 text-[#E6E8EB] text-[10px] w-48 focus:outline-hidden focus:border-[#38BDF8]"
                    />
                    <button
                      type="submit"
                      disabled={isSubmittingNote || !newNoteText.trim()}
                      className="px-3 py-1 rounded bg-[#38BDF8]/20 hover:bg-[#38BDF8]/30 text-[#38BDF8] border border-[#38BDF8]/30 font-bold transition flex items-center gap-1 disabled:opacity-40"
                    >
                      {isSubmittingNote ? <RefreshCw size={11} className="animate-spin" /> : <Plus size={11} />}
                      Add Note
                    </button>
                  </div>
                </form>
              </div>
            </>
          )}
        </div>

        {/* ── FOOTER ── */}
        <div className="border-t border-[#1E2330] bg-[#141822] px-5 py-3 flex items-center justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-[#1A1F2C] text-[#848E9C] hover:text-white font-mono text-[11px]"
          >
            Close Lineage
          </button>
        </div>

      </div>
    </div>
  );
};
