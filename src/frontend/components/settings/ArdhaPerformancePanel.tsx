// src/frontend/components/settings/ArdhaPerformancePanel.tsx
import React, { useEffect, useState } from "react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";

export interface EvaluationRecord {
  id: string;
  trading_date: string;
  phase: string;
  captured_at: string;
  prediction_at?: string;
  metric: string;
  metric_id?: string;
  schema_version?: number;
  ardha_value: string;
  ardha_value_numeric?: number;
  real_value?: string;
  real_value_numeric?: number;
  evaluated_at?: string;
  result: "HIT" | "NEAR" | "MISS" | "NOT_EVALUABLE" | "PENDING";
  error_value?: number;
  notes?: string;
  pending_reason?: string;
}

export interface DateSummary {
  date: string;
  total_records: number;
  hits: number;
  nears: number;
  misses: number;
  pending: number;
  not_evaluable?: number;
}

type PhaseFilter = "ALL" | "PRE_MARKET" | "EARLY_SESSION" | "LIVE_INTRADAY" | "CLOSE";

export function ArdhaPerformancePanel() {
  const todayStr = new Date().toISOString().split("T")[0];
  const [selectedDate, setSelectedDate] = useState<string>(todayStr);
  const [records, setRecords] = useState<EvaluationRecord[]>([]);
  const [history, setHistory] = useState<DateSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [phaseFilter, setPhaseFilter] = useState<PhaseFilter>("ALL");

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    fetchRecords(selectedDate);
  }, [selectedDate]);

  const fetchHistory = async () => {
    try {
      const res = await fetch("/api/performance/history");
      if (res.ok) {
        const data = await res.json();
        setHistory(data || []);
      }
    } catch (err) {
      console.error("Failed fetching performance history:", err);
    }
  };

  const fetchRecords = async (date: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/performance/records?date=${date}`);
      if (res.ok) {
        const data = await res.json();
        setRecords(data || []);
      } else {
        setRecords([]);
      }
    } catch (err) {
      console.error("Failed fetching performance records:", err);
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  // Filtered records
  const displayedRecords = records.filter((r) => {
    if (phaseFilter === "ALL") return true;
    return r.phase === phaseFilter;
  });

  // Dynamic phase counts for selected date
  const preCount = records.filter((r) => r.phase === "PRE_MARKET").length;
  const openCount = records.filter((r) => r.phase === "EARLY_SESSION").length;
  const liveCount = records.filter((r) => r.phase === "LIVE_INTRADAY").length;
  const closeCount = records.filter((r) => r.phase === "CLOSE").length;

  // Summary counter stats for currently selected date
  const hits = records.filter((r) => r.result === "HIT").length;
  const nears = records.filter((r) => r.result === "NEAR").length;
  const misses = records.filter((r) => r.result === "MISS").length;
  const pending = records.filter((r) => r.result === "PENDING").length;
  const notEvaluable = records.filter((r) => r.result === "NOT_EVALUABLE").length;

  const formatTime = (isoStr?: string) => {
    if (!isoStr) return "--:--";
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
    } catch {
      return "--:--";
    }
  };

  const getBadgeClass = (result: string) => {
    switch (result) {
      case "HIT":
        return "border-[#00C896]/40 bg-[#00C896]/15 text-[#00C896]";
      case "NEAR":
        return "border-[#E59700]/40 bg-[#E59700]/15 text-[#E59700]";
      case "MISS":
        return "border-[#E5484D]/40 bg-[#E5484D]/15 text-[#E5484D]";
      case "NOT_EVALUABLE":
        return "border-[#707987]/40 bg-[#707987]/15 text-[#707987]";
      case "PENDING":
      default:
        return "border-[#38BDF8]/40 bg-[#38BDF8]/15 text-[#38BDF8]";
    }
  };

  return (
    <div id="ardha-performance-panel" className="space-y-2.5 font-sans text-left text-[11px]">
      {/* Date Selector & Counter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#191D23] pb-2 font-mono">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSelectedDate(todayStr)}
            className={`px-2.5 py-1 rounded-[2px] text-[10px] font-bold border transition ${
              selectedDate === todayStr
                ? "border-[#38BDF8] bg-[#38BDF8]/15 text-[#38BDF8]"
                : "border-[#242830] bg-[#08090B] text-[#707987] hover:text-[#A5ABB4]"
            }`}
          >
            TODAY
          </button>

          {history.length > 0 && (
            <select
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-[#08090B] border border-[#242830] text-[#E6E8EB] text-[10px] rounded-[2px] px-2 py-1 focus:outline-none focus:border-[#38BDF8]"
            >
              {!history.some((h) => h.date === todayStr) && (
                <option value={todayStr}>{todayStr} (Today)</option>
              )}
              {history.map((h) => (
                <option key={h.date} value={h.date}>
                  {h.date} ({h.hits}H / {h.misses}M)
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Summary Counter Pills */}
        <div className="flex flex-wrap items-center gap-2 text-[10px]">
          <span className="px-2 py-0.5 rounded-[2px] bg-[#00C896]/15 border border-[#00C896]/30 text-[#00C896] font-bold">
            HITS: {hits}
          </span>
          <span className="px-2 py-0.5 rounded-[2px] bg-[#E59700]/15 border border-[#E59700]/30 text-[#E59700] font-bold">
            NEAR: {nears}
          </span>
          <span className="px-2 py-0.5 rounded-[2px] bg-[#E5484D]/15 border border-[#E5484D]/30 text-[#E5484D] font-bold">
            MISSES: {misses}
          </span>
          <span className="px-2 py-0.5 rounded-[2px] bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8] font-bold">
            PENDING: {pending}
          </span>
          <span className="px-2 py-0.5 rounded-[2px] bg-[#191D23] text-[#707987] font-bold">
            N/A: {notEvaluable}
          </span>
        </div>
      </div>

      {/* Dynamic Phase Filter Controls */}
      <div className="flex items-center gap-1.5 font-mono text-[10px]">
        {(
          [
            { id: "ALL", label: `ALL (${records.length})` },
            { id: "PRE_MARKET", label: `PRE-MARKET (${preCount})` },
            { id: "EARLY_SESSION", label: `OPEN / 15M (${openCount})` },
            { id: "LIVE_INTRADAY", label: `LIVE (${liveCount})` },
            { id: "CLOSE", label: `CLOSE (${closeCount})` },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setPhaseFilter(tab.id as PhaseFilter)}
            className={`px-2.5 py-1 rounded-[2px] font-bold border transition ${
              phaseFilter === tab.id
                ? "border-[#38BDF8] bg-[#38BDF8]/15 text-[#38BDF8]"
                : "border-[#242830] bg-[#08090B] text-[#707987] hover:text-[#A5ABB4]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Evaluation Records Table */}
      <div className="overflow-x-auto rounded-[2px] border border-[#242830]">
        <table className="w-full text-left font-mono text-[10px] border-collapse">
          <thead>
            <tr className="bg-[#0E1013] text-[#707987] uppercase border-b border-[#191D23]">
              <th className="py-2 px-2.5">Time</th>
              <th className="py-2 px-2.5">Phase</th>
              <th className="py-2 px-2.5">Metric &amp; Field</th>
              <th className="py-2 px-2.5">Ardha Value</th>
              <th className="py-2 px-2.5">Real Value</th>
              <th className="py-2 px-2.5">Outcome</th>
              <th className="py-2 px-2.5">Error Delta</th>
              <th className="py-2 px-2.5">Notes &amp; Rule</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#191D23] bg-[#0B0D10]">
            {loading ? (
              <tr>
                <td colSpan={8} className="py-6 text-center text-[#707987]">
                  Loading performance records for {selectedDate}...
                </td>
              </tr>
            ) : displayedRecords.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-6 text-center text-[#707987]">
                  No evaluation records available for {selectedDate} in {phaseFilter} phase.
                </td>
              </tr>
            ) : (
              displayedRecords.map((r) => (
                <tr key={r.id} className="hover:bg-[#13161A] transition">
                  <td className="py-1.5 px-2.5 text-[#707987]">{formatTime(r.captured_at)}</td>
                  <td className="py-1.5 px-2.5 text-[#A5ABB4] uppercase text-[9px]">{r.phase}</td>
                  <td className="py-1.5 px-2.5 text-[#E6E8EB] font-bold">{r.metric}</td>
                  <td className="py-1.5 px-2.5 text-[#38BDF8] font-bold">{r.ardha_value}</td>
                  <td className="py-1.5 px-2.5 text-white font-bold">{r.real_value ?? "--"}</td>
                  <td className="py-1.5 px-2.5">
                    <span
                      className={`inline-block px-1.5 py-0.5 text-[8.5px] font-bold uppercase rounded-[2px] border ${getBadgeClass(
                        r.result
                      )}`}
                    >
                      {r.result}
                    </span>
                  </td>
                  <td className="py-1.5 px-2.5 text-[#707987]">
                    {r.error_value != null && !isNaN(Number(r.error_value))
                      ? `${Number(r.error_value).toFixed(2)} pts`
                      : "--"}
                  </td>
                  <td className="py-1.5 px-2.5 text-[#707987] truncate max-w-[240px]">
                    {r.notes || r.pending_reason || "--"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ArdhaPerformancePanel;
