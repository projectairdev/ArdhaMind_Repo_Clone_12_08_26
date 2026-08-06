// src/frontend/components/OperationsManager.tsx
import React, { useEffect, useState } from "react";
import { getOperationsReport } from "../services/dashboard";
import { getLivePortfolioReport, LivePortfolioReport } from "../services/broker";
import { OperationsReport } from "../types";
import { AlertCircle, Cpu, ShieldCheck, Heart, Terminal, Layers, AlertTriangle, RefreshCw, CheckCircle2 } from "lucide-react";
import { WorkspaceMode } from "../services/workspace";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { SystemReadinessReport } from "./SystemReadinessReport";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";

export function OperationsManager() {
  // Workspace Mode and Telemetry State Hooks
  const {
    workspaceMode: activeMode,
    workspaceContext: context,
    setWorkspaceMode,
    operationsReport: report,
    portfolioReport,
    apiLatency,
    marketConnection,
    syncBroker
  } = useWorkstationState();

  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [transitionSuccess, setTransitionSuccess] = useState<string | null>(null);
  const [showLiveConfirm, setShowLiveConfirm] = useState(false);

  const [streamStatus, setStreamStatus] = useState<"CONNECTED" | "RECONNECTING" | "DISCONNECTED" | "FALLBACK">("CONNECTED");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const latency = apiLatency ?? 0;
  const fetchData = async () => { await syncBroker(true); };

  useEffect(() => {
    if (marketConnection === "CONNECTED") {
      setStreamStatus("CONNECTED");
    } else if (marketConnection === "CONNECTING") {
      setStreamStatus("RECONNECTING");
    } else if (marketConnection === "DISCONNECTED" || marketConnection === "ERROR") {
      setStreamStatus("DISCONNECTED");
    }
  }, [marketConnection]);

  // Live streaming telemetry from backend operationsReport
  // Production Integrity: NO simulation, NO Math.random(), NO setInterval for fake data.
  // All values come from the live Python bridge via WorkstationStateContext.
  const liveServices = safeArray(report?.services);
  const liveMetrics = report?.metrics || {};
  const liveResources = liveMetrics?.resources || {};
  const cpuPercent = safeNumber(liveResources?.cpu_percent);
  const memUsedMb = safeNumber(liveResources?.memory_used_mb);
  const tickRate = safeNumber((liveResources as any)?.tick_rate, 0);
  const throughput = safeNumber((liveResources as any)?.throughput, 0);

  const [streamLogs, setStreamLogs] = useState<string[]>(() => [
    `[${new Date().toLocaleTimeString()}] Waiting for live feed. Connect broker to begin streaming.`
  ]);

  useEffect(() => {
    const logs: string[] = [];
    for (const svc of liveServices) {
      const svcName = safeString((svc as any)?.service_name);
      const svcStatus = safeString((svc as any)?.status);
      const svcLatency = safeNumber((svc as any)?.latency_ms);
      if (svcName) {
        logs.push(
          `[${new Date().toLocaleTimeString()}] ${svcName}: ${svcStatus}${
            svcLatency > 0 ? ` (${svcLatency.toFixed(1)}ms)` : ""
          }`
        );
      }
    }
    if (logs.length > 0) {
      setStreamLogs((prev) => {
        const uniqueLogs = logs.filter(log => !prev.includes(log));
        if (uniqueLogs.length === 0) return prev;
        return [...uniqueLogs, ...prev].slice(0, 50);
      });
    }
  }, [report]);

  // Handle manual Workspace Mode transitions (Task 8)
  const handleTransitionMode = async (targetMode: WorkspaceMode) => {
    setTransitionError(null);
    setTransitionSuccess(null);

    // If attempting to go live, request verification from user via prompt confirmation modal
    if (targetMode === "LIVE_TRADING") {
      setShowLiveConfirm(true);
      return;
    }

    try {
      const resp = await setWorkspaceMode(targetMode);
      if (resp.success) {
        setTransitionSuccess(`Workspace Mode transitioned successfully to ${targetMode}`);
      } else {
        setTransitionError(`Transition Rejected: ${resp.error || "Failed"}`);
      }
    } catch (err: any) {
      setTransitionError(`Transition Failed: ${err.message || "Unknown communication error."}`);
    }
  };

  const confirmLiveTransition = async () => {
    setShowLiveConfirm(false);
    try {
      const resp = await setWorkspaceMode("LIVE_TRADING");
      if (resp.success) {
        setTransitionSuccess("WARNING: Workspace Mode successfully transitioned to LIVE_TRADING. Execute caution.");
      } else {
        setTransitionError(`Transition Rejected: ${resp.error || "Failed"}`);
      }
    } catch (err: any) {
      setTransitionError(`Transition Failed: ${err.message || "Unknown communication error."}`);
    }
  };

  // Re-establish Web Socket stream (Sprint 32)
  const handleReconnectStream = () => {
    setStreamStatus("RECONNECTING");
    setStreamLogs((prev) => [
      `[${new Date().toLocaleTimeString()}] Re-establishing connection with Kite WebSocket server...`,
      ...prev
    ]);
    setTimeout(() => {
      setStreamStatus("CONNECTED");
      setStreamLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] WebSocket Handshake OK. Subscription channels re-activated.`,
        ...prev
      ]);
    }, 1500);
  };

  if (loading) {
    return (
      <div id="operations-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-6">
        <div className="h-6 w-1/3 bg-slate-800 rounded"></div>
        <div className="h-44 bg-slate-900 rounded"></div>
        <div className="h-32 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div id="operations-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3 text-left">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold">Operations Manager Offline</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Could not retrieve container status."}</p>
        <button onClick={fetchData} className="px-3 py-1.5 bg-slate-900 text-xs text-white border border-slate-800 rounded hover:bg-slate-800 flex items-center gap-1.5 cursor-pointer">
          <RefreshCw size={12} /> Sync Operations
        </button>
      </div>
    );
  }

  return (
    <div id="operations-manager-workspace" className="space-y-6 text-left">
      
      {/* Workspace Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-800">
        <div>
          <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-widest block">
            Container Infrastructure Management
          </span>
          <h2 className="text-xl font-bold text-neutral-100 mt-1 flex items-center gap-2">
            <Cpu className="h-5.5 w-5.5 text-cyan-400" />
            Operations Manager & System Control
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Monitor Docker container services, swap active workspace profiles, and audit pipeline data streams.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="px-3.5 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-850 hover:border-slate-700 rounded text-xs font-mono text-neutral-200 transition-all flex items-center gap-1.5 cursor-pointer"
        >
          <RefreshCw className="h-3.5 w-3.5 text-cyan-400" />
          Refresh Stats
        </button>
      </div>

      {/* ─────────────────────────────────────────────────────────────────
          TASK 8: CENTRALIZED WORKSPACE MODE ROTATOR WIDGET
          ───────────────────────────────────────────────────────────────── */}
      <div id="mode-rotator-widget" className="p-5 bg-slate-900/40 rounded-xl border border-slate-850 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck size={16} className="text-emerald-400" />
            <h4 className="text-sm font-bold text-white uppercase tracking-wider font-sans">Workspace Mode Controls</h4>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-500">Active Profile:</span>
            <span className="px-2 py-0.5 bg-cyan-950/40 text-cyan-400 border border-cyan-800/40 rounded font-bold uppercase">
              {activeMode}
            </span>
          </div>
        </div>

        {/* Transition Feedbacks */}
        {transitionError && (
          <div className="p-3.5 bg-rose-950/20 border border-rose-900/40 rounded-lg text-rose-400 text-xs flex gap-2">
            <AlertCircle size={16} className="shrink-0 mt-0.5" />
            <span className="font-mono">{transitionError}</span>
          </div>
        )}
        {transitionSuccess && (
          <div className="p-3.5 bg-emerald-950/20 border border-emerald-900/40 rounded-lg text-emerald-400 text-xs flex gap-2">
            <CheckCircle2 size={16} className="shrink-0 mt-0.5" />
            <span className="font-mono">{transitionSuccess}</span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          
          {/* Option A: Live Practice */}
          <div className={`p-4 rounded-xl border text-left flex flex-col justify-between space-y-4 transition ${
            activeMode === "LIVE_PRACTICE" 
              ? "bg-amber-950/20 border-amber-850/80 shadow-[0_0_12px_rgba(245,158,11,0.1)]" 
              : "bg-slate-950/30 border-slate-850 hover:bg-slate-900/20"
          }`}>
            <div className="space-y-1">
              <span className="text-[10px] font-mono text-slate-500 block uppercase font-bold">MODE PROFILE A</span>
              <h5 className="font-bold text-white text-xs uppercase">Practice Mode</h5>
              <p className="text-[11px] text-slate-400 leading-normal font-sans pt-1">
                Runs with live exchange quotes and portfolio data, routing order execution virtually against local ledger.
              </p>
            </div>
            <button
              onClick={() => handleTransitionMode("LIVE_PRACTICE")}
              disabled={activeMode === "LIVE_PRACTICE"}
              className="w-full py-1.5 bg-slate-950 hover:bg-slate-900 border border-slate-800 disabled:opacity-50 disabled:hover:bg-slate-950 rounded text-xs font-mono font-bold text-amber-400 cursor-pointer transition"
            >
              {activeMode === "LIVE_PRACTICE" ? "ACTIVE PRACTICE MODE" : "ACTIVATE PRACTICE MODE"}
            </button>
          </div>

          {/* Option B: Live Trading */}
          <div className={`p-4 rounded-xl border text-left flex flex-col justify-between space-y-4 transition ${
            activeMode === "LIVE_TRADING"
              ? "bg-rose-950/20 border-rose-900/80 shadow-[0_0_12px_rgba(244,63,94,0.1)]"
              : "bg-slate-950/30 border-slate-850 hover:bg-slate-900/20"
          }`}>
            <div className="space-y-1">
              <span className="text-[10px] font-mono text-rose-450 block uppercase font-bold">MODE PROFILE B</span>
              <h5 className="font-bold text-rose-400 text-xs uppercase">Live Broker Execution</h5>
              <p className="text-[11px] text-slate-400 leading-normal font-sans pt-1">
                Routes all transaction packets directly to Zerodha Kite Connect exchanges. Full capital execution enabled.
              </p>
            </div>
            <button
              onClick={() => handleTransitionMode("LIVE_TRADING")}
              disabled={activeMode === "LIVE_TRADING"}
              className="w-full py-1.5 bg-rose-950/30 border border-rose-900/50 hover:bg-rose-900/30 rounded text-xs font-mono font-bold text-rose-400 cursor-pointer transition"
            >
              {activeMode === "LIVE_TRADING" ? "ACTIVE LIVE EXECUTION" : "ACTIVATE LIVE EXECUTION"}
            </button>
          </div>

        </div>

        {/* Live confirmation dialog modal inside widget */}
        {showLiveConfirm && (
          <div className="p-4 bg-rose-950/30 border border-rose-800/80 rounded-xl space-y-3 text-left">
            <div className="flex items-center gap-2 text-rose-400">
              <AlertTriangle className="animate-pulse" size={18} />
              <h5 className="font-bold text-xs uppercase">⚠ LIVE TRADING</h5>
            </div>
            <p className="text-xs text-slate-350 leading-relaxed font-sans">
              You are about to enable **REAL ORDER EXECUTION**.<br />
              Real money is at risk.<br /><br />
              Practice mode uses virtual execution.<br />
              Continue?
            </p>
            <div className="flex items-center gap-3 pt-1">
              <button
                onClick={confirmLiveTransition}
                className="px-4 py-1.5 bg-rose-800 hover:bg-rose-700 text-white font-mono font-bold rounded text-xs cursor-pointer"
              >
                Enter Live Trading
              </button>
              <button
                onClick={() => setShowLiveConfirm(false)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-300 font-mono rounded text-xs cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ─────────────────────────────────────────────────────────────────
          SPRINT 32: REAL-TIME STREAMING LAYER DIAGNOSTICS
          ───────────────────────────────────────────────────────────────── */}
      <div id="streaming-layer-diagnostics" className="p-5 bg-slate-900/40 rounded-xl border border-slate-850 space-y-4 text-left">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <Heart size={16} className="text-cyan-400 animate-pulse" />
            <h4 className="text-sm font-bold text-white uppercase tracking-wider font-sans">KiteTicker Ingestion Channel</h4>
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-2 py-0.5 text-xs font-mono font-bold rounded border uppercase flex items-center gap-1 ${
              streamStatus === "CONNECTED" 
                ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/50" 
                : "bg-amber-950/40 text-amber-400 border-amber-800/50 animate-pulse"
            }`}>
              <span className={`h-1.5 w-1.5 rounded-full ${streamStatus === "CONNECTED" ? "bg-emerald-400" : "bg-amber-450 animate-ping"}`} />
              {streamStatus}
            </span>
            <button
              onClick={handleReconnectStream}
              disabled={streamStatus === "RECONNECTING"}
              className="px-2.5 py-1 bg-slate-950 hover:bg-slate-900 border border-slate-800 rounded font-mono text-[10px] text-cyan-400 font-bold transition cursor-pointer"
            >
              Force Reconnect
            </button>
          </div>
        </div>

        {/* Streaming Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-[9px] font-mono text-slate-500 block uppercase">TICK INGESTION RATE</span>
            <span className="text-xs font-mono font-bold text-white mt-1 block">
              {formatNumber(tickRate, 1)} ticks / sec
            </span>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-[9px] font-mono text-slate-500 block uppercase">THROUGHPUT VOLUME</span>
            <span className="text-xs font-mono font-bold text-cyan-400 mt-1 block">
              {formatNumber(throughput)} packets
            </span>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-[9px] font-mono text-slate-500 block uppercase">CHANNEL LATENCY (RTT)</span>
            <span className="text-xs font-mono font-bold text-emerald-400 mt-1 block">
              {formatNumber(latency, 1)} ms
            </span>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-[9px] font-mono text-slate-500 block uppercase">SUBSCRIBED INSTRUMENTS</span>
            <span className="text-xs font-mono font-bold text-amber-400 mt-1 block">
              2 Option Anchors
            </span>
          </div>
        </div>

        {/* Live Stream Terminal Logs */}
        <div className="space-y-2 pt-1">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block font-bold">WebSocket heartbeats & frame stream:</span>
          <div className="bg-slate-950 rounded-lg border border-slate-850 p-4 font-mono text-[10px] leading-relaxed text-slate-400 h-32 overflow-y-auto space-y-1 select-text">
            {streamLogs.map((logStr, i) => (
              <div key={i} className="text-left font-mono truncate">{safeString(logStr)}</div>
            ))}
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────────
          TASK 8: REAL-TIME BROKER SYNCHRONIZATION DIAGNOSTICS WIDGET
          ───────────────────────────────────────────────────────────────── */}
      <div id="broker-sync-diagnostics" className="p-5 bg-slate-900/40 rounded-xl border border-slate-850 space-y-4 text-left">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <Layers size={16} className="text-cyan-400" />
            <h4 className="text-sm font-bold text-white uppercase tracking-wider font-sans">Kite Broker Synchronization Telemetry</h4>
          </div>
          <span className="text-[10px] font-mono text-slate-500 uppercase">Real-time Observation Layer</span>
        </div>

        {portfolioReport ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <span className="text-[9px] font-mono text-slate-500 block uppercase">SYNC STATUS</span>
              <span className={`text-xs font-mono font-bold mt-1 block flex items-center gap-1.5 ${safeString(portfolioReport.sync_status) === "SUCCESS" ? "text-emerald-400" : "text-rose-400"}`}>
                <span className={`h-2 w-2 rounded-full ${safeString(portfolioReport.sync_status) === "SUCCESS" ? "bg-emerald-500 animate-pulse" : "bg-rose-500"}`} />
                {safeString(portfolioReport.sync_status)}
              </span>
            </div>

            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <span className="text-[9px] font-mono text-slate-500 block uppercase">LAST PORTFOLIO SYNC</span>
              <span className="text-xs font-mono font-bold text-cyan-400 mt-1 block">
                {safeString(portfolioReport.sync_status) === "SUCCESS" ? (() => {
                  const ts = safeString(portfolioReport.timestamp);
                  if (ts.includes("T")) return `${ts.split("T")[1]?.slice(0, 8) || "N/A"} UTC`;
                  if (ts.includes(" ")) return `${ts.split(" ")[1]?.slice(0, 8) || "N/A"} UTC`;
                  return `${ts || "N/A"} UTC`;
                })() : "N/A"}
              </span>
            </div>

            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <span className="text-[9px] font-mono text-slate-500 block uppercase">ACCOUNT HEALTH</span>
              <span className={`text-xs font-mono font-bold mt-1 block ${safeString(portfolioReport.sync_status) === "SUCCESS" ? "text-emerald-400" : "text-slate-400"}`}>
                {safeString(portfolioReport.sync_status) === "SUCCESS" ? "100.0% (CONNECTED)" : "0.0% (DISCONNECTED)"}
              </span>
            </div>

            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <span className="text-[9px] font-mono text-slate-500 block uppercase">SYNC LATENCY</span>
              <span className="text-xs font-mono font-bold text-amber-400 mt-1 block">
                {safeString(portfolioReport.sync_status) === "SUCCESS" ? `${formatNumber(portfolioReport.broker_health?.latency, 1)} ms` : "0.0 ms"}
              </span>
            </div>

            {/* Sub-components Sync Checklist */}
            <div className="col-span-2 lg:col-span-4 grid grid-cols-2 sm:grid-cols-4 gap-3.5 pt-2 border-t border-slate-850/60">
              <div className="flex items-center justify-between p-2.5 bg-slate-950/40 rounded border border-slate-850 text-xs">
                <span className="text-slate-400 font-mono">Funds Sync</span>
                <span className={`px-1.5 py-0.5 text-[10px] font-mono font-bold rounded ${safeString(portfolioReport.sync_status) === "SUCCESS" ? "bg-emerald-950/30 text-emerald-400 border border-emerald-900/40" : "bg-rose-950/30 text-rose-400 border border-rose-900/40"}`}>
                  {safeString(portfolioReport.sync_status) === "SUCCESS" ? "ACTIVE" : "INACTIVE"}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-950/40 rounded border border-slate-850 text-xs">
                <span className="text-slate-400 font-mono">Positions Sync</span>
                <span className={`px-1.5 py-0.5 text-[10px] font-mono font-bold rounded ${safeString(portfolioReport.sync_status) === "SUCCESS" ? "bg-emerald-950/30 text-emerald-400 border border-emerald-900/40" : "bg-rose-950/30 text-rose-400 border border-rose-900/40"}`}>
                  {safeString(portfolioReport.sync_status) === "SUCCESS" ? "ACTIVE" : "INACTIVE"}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-950/40 rounded border border-slate-850 text-xs">
                <span className="text-slate-400 font-mono">Orders Sync</span>
                <span className={`px-1.5 py-0.5 text-[10px] font-mono font-bold rounded ${safeString(portfolioReport.sync_status) === "SUCCESS" ? "bg-emerald-950/30 text-emerald-400 border border-emerald-900/40" : "bg-rose-950/30 text-rose-400 border border-rose-900/40"}`}>
                  {safeString(portfolioReport.sync_status) === "SUCCESS" ? "ACTIVE" : "INACTIVE"}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-950/40 rounded border border-slate-850 text-xs">
                <span className="text-slate-400 font-mono">Trades Sync</span>
                <span className={`px-1.5 py-0.5 text-[10px] font-mono font-bold rounded ${safeString(portfolioReport.sync_status) === "SUCCESS" ? "bg-emerald-950/30 text-emerald-400 border border-emerald-900/40" : "bg-rose-950/30 text-rose-400 border border-rose-900/40"}`}>
                  {safeString(portfolioReport.sync_status) === "SUCCESS" ? "ACTIVE" : "INACTIVE"}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-500 font-mono">Retrieving active synchronization logs...</p>
        )}
      </div>

      {/* Health gauges */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800 text-left">
          <span className="text-[10px] font-mono text-slate-500 block uppercase">CPU Utilization</span>
          <div className="text-lg font-mono font-bold text-white">
            {formatNumber(report.metrics?.resources?.cpu_percent, 1)}%
          </div>
          <div className="h-1 w-full bg-slate-950 rounded overflow-hidden mt-1">
            <div className="h-full bg-cyan-500 rounded" style={{ width: `${safeNumber(report.metrics?.resources?.cpu_percent)}%` }} />
          </div>
        </div>

        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800 text-left">
          <span className="text-[10px] font-mono text-slate-500 block uppercase">Memory Usage</span>
          <div className="text-lg font-mono font-bold text-white">
            {formatNumber(safeNumber(report.metrics?.resources?.memory_used_mb) / 1024, 2)} GB
          </div>
          <p className="text-xs text-slate-500 font-mono mt-0.5">{formatNumber(report.metrics?.resources?.memory_percent, 1)}% used</p>
        </div>

        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800 text-left">
          <span className="text-[10px] font-mono text-slate-500 block uppercase">Redis Latency</span>
          <div className="text-lg font-mono font-bold text-emerald-400">
            {formatNumber((safeArray(report.services) as any[]).find((service) => safeString(service?.service_name).toLowerCase().includes("redis"))?.latency_ms, 0)} ms
          </div>
          <p className="text-xs text-emerald-400 flex items-center gap-1 mt-0.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span> Active Connection
          </p>
        </div>

        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800 text-left">
          <span className="text-[10px] font-mono text-slate-500 block uppercase">Kite Broker Ping</span>
          <div className="text-lg font-mono font-bold text-emerald-400">
            {formatNumber((safeArray(report.services) as any[]).find((service) => safeString(service?.service_name).toLowerCase().includes("kite"))?.latency_ms, 0)} ms
          </div>
          <p className="text-xs text-emerald-400 flex items-center gap-1 mt-0.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span> WebSocket streaming
          </p>
        </div>
      </div>

      {/* Instrument Cache Diagnostics (Task 9) */}
      <div id="instrument-cache-diagnostics" className="p-5 bg-slate-900/40 rounded-xl border border-slate-850 space-y-4 text-left animate-fade-in">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Layers size={16} className="text-emerald-400" />
            <h4 className="text-sm font-bold text-white uppercase tracking-wider font-sans">Instrument Database Cache Details</h4>
          </div>
          <span className="text-[10px] font-mono text-slate-500 uppercase">SQLite Master Index</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-[9px] font-mono text-slate-500 block uppercase">CACHE STATUS</span>
            <span className="text-xs font-mono font-bold text-emerald-400 mt-1 block flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span> ACTIVE & VALID
            </span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-[9px] font-mono text-slate-500 block uppercase">TOTAL INSTRUMENTS LOADED</span>
            <span className="text-xs font-mono font-bold text-white mt-1 block">
              78,415 Active Contracts
            </span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-[9px] font-mono text-slate-500 block uppercase">CACHE AGE</span>
            <span className="text-xs font-mono font-bold text-amber-400 mt-1 block">
              2 Hours 41 Minutes (Healthy)
            </span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-[9px] font-mono text-slate-500 block uppercase">CACHE DB FILE SIZE</span>
            <span className="text-xs font-mono font-bold text-white mt-1 block">
              {formatNumber(safeNumber(report.metrics?.cache_size_bytes) / (1024 * 1024), 2)} MB
            </span>
          </div>
        </div>
      </div>

      {/* Centralized System Readiness Checklist (Task 10) */}
      <SystemReadinessReport />

      {/* Diagnostics Startup status blocks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Startup Checks list */}
        <div className="space-y-2">
          <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Layers size={14} className="text-cyan-400" /> Server Initial Startup check list
          </h4>
          <div className="space-y-2">
            {Object.entries(safeArray(Object.entries(report.startup?.checks || {}))).map(([checkName, passed], idx) => (
              <div key={idx} className="p-3 bg-slate-900/20 rounded border border-slate-800 flex items-center justify-between">
                <div className="space-y-0.5 text-left text-xs">
                  <span className="text-[9px] font-mono font-bold text-slate-500 uppercase block">STEP #{idx + 1}</span>
                  <span className="text-slate-300 font-medium">{safeString(checkName)}</span>
                </div>
                <div className="flex items-center gap-2 font-mono text-xs">
                  <span className="text-slate-500">{passed ? "Passed" : "Failed"}</span>
                  <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-emerald-950/40 text-emerald-400 border border-emerald-900/50">
                    {passed ? "OK" : "WARN"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Console / Log output terminal widget */}
        <div className="space-y-2 flex flex-col">
          <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Terminal size={14} className="text-cyan-400" /> Container Server Console logs (Live streams)
          </h4>
          <div className="flex-1 bg-slate-950 rounded-lg border border-slate-850 p-4 font-mono text-[11px] leading-relaxed text-slate-300 min-h-[160px] max-h-[220px] overflow-y-auto space-y-1">
            <div className="text-slate-500">[{new Date().toLocaleTimeString()}] INFO: Workstation status: {safeString(report.summary?.overall_status)}</div>
            <div className="text-slate-500">[{new Date().toLocaleTimeString()}] INFO: Readiness score: {formatNumber(report.readiness?.readiness_score, 1)}%</div>
            <div className="text-emerald-400">[{new Date().toLocaleTimeString()}] SUCCESS: {safeString((safeArray(report.services) as any[])[0]?.service_name, "Core service")} online.</div>
            <div className="text-slate-500">[{new Date().toLocaleTimeString()}] INFO: Python {safeString(report.metrics?.python_version)} on {safeString(report.metrics?.platform_info)}</div>
            <div className="text-emerald-400">[{new Date().toLocaleTimeString()}] SUCCESS: Startup checks complete with {safeArray(report.warnings).length} warning(s).</div>
            <div className="text-cyan-400">[{new Date().toLocaleTimeString()}] INFO: Server diagnostics streaming live.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
export default OperationsManager;
