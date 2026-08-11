// src/frontend/components/SettingsDashboard.tsx
import React, { useState, useMemo } from "react";
import {
  KeyRound,
  Database,
  Activity,
  ShieldCheck,
  RefreshCw,
  Download,
  Server,
  Globe,
  Radio,
  Clock,
  AlertCircle
} from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import {
  useWorkstationState,
  useBrokerStatus,
  useMarketData,
  useNewsIntelligence
} from "../context/WorkstationStateContext";
import { safeArray, safeString, safeNumber, formatDate } from "../utils/safeHelpers";
import { formatTimestampIST } from "../utils/timeFormatting";
import { mapTraderEnum } from "../utils/traderTerminology";

export function SettingsDashboard() {
  const { themeClasses, accentClasses } = useTheme();
  const {
    workspaceContext,
    brokerAccount,
    canonicalState,
    lastValidState,
    marketConnection,
    apiLatency,
    lastSyncTime,
    setError,
    syncBroker
  } = useWorkstationState() as any;

  const [providerSortBy, setProviderSortBy] = useState<"status" | "freshness" | "name">("status");
  const [providerSortDir, setProviderSortDir] = useState<"asc" | "desc">("asc");
  const [message, setMessage] = useState<string | null>(null);

  const { data: broker } = useBrokerStatus();
  const { data: marketDataObj } = useMarketData();
  const { data: newsObj } = useNewsIntelligence() as any;

  const brokerStatusStr = safeString(broker?.status || workspaceContext?.brokerState || "DISCONNECTED").toUpperCase();
  const isConnected = brokerStatusStr === "CONNECTED";

  const handleOAuthConnect = async () => {
    try {
      setMessage("Redirecting to official Zerodha OAuth login...");
      const res = await fetch("/api/broker/login-url");
      const body = await res.json();
      if (body && body.login_url) {
        window.location.href = body.login_url;
      } else {
        setMessage(body.error || "Failed to generate Zerodha login URL.");
      }
    } catch (err: any) {
      setMessage(err.message || "OAuth initiation failed.");
    }
  };

  const handleDisconnect = async () => {
    try {
      setMessage("Disconnecting broker session...");
      await fetch("/api/broker/logout", { method: "POST" });
      await syncBroker(true);
      setMessage("Broker session disconnected.");
    } catch (err: any) {
      setMessage(err.message || "Disconnect failed.");
    }
  };

  // ── ALL hooks must be declared before any conditional return ──────────────
  // getHealthRank is a plain function, not a hook — defined here so sortedProviders can use it.
  const getHealthRank = (value: any) => {
    const status = safeString(value?.status).toUpperCase();
    if (status.includes("DEGRADED") || status.includes("UNAVAILABLE") || status.includes("ERROR") || status.includes("FAILED")) return 1;
    const freshness = safeString(value?.freshness || value?.freshness_status).toUpperCase();
    if (status.includes("STALE") || freshness.includes("STALE")) return 2;
    return 3;
  };

  // Derived null-safe refs used by sortedProviders — safe for empty/loading state
  const rawProviderHealth = (canonicalState ?? lastValidState)?.news_intelligence?.provider_health ?? {};
  const rawMacroHealth = (canonicalState ?? lastValidState)?.macro_intelligence?.provider_health ?? {};

  const sortedProviders = useMemo(() => {
    const entries = Object.entries({ ...rawProviderHealth, ...rawMacroHealth });
    return entries.sort((a: any, b: any) => {
      const nameA = a[0];
      const nameB = b[0];
      const valA = a[1];
      const valB = b[1];
      let diff = 0;
      if (providerSortBy === "name") {
        diff = nameA.localeCompare(nameB);
      } else if (providerSortBy === "freshness") {
        const fA = safeString(valA.freshness || valA.freshness_status).toUpperCase();
        const fB = safeString(valB.freshness || valB.freshness_status).toUpperCase();
        diff = fA.localeCompare(fB);
      } else { // status
        const rankA = getHealthRank(valA);
        const rankB = getHealthRank(valB);
        diff = rankA - rankB;
      }
      if (diff === 0) {
        diff = nameA.localeCompare(nameB); // stable tie-breaker
      }
      return providerSortDir === "asc" ? diff : -diff;
    });
  }, [rawProviderHealth, rawMacroHealth, providerSortBy, providerSortDir]);
  // ── End hooks section ──────────────────────────────────────────────────────

  if (!canonicalState && !lastValidState) {
    return (
      <div id="settings-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4 font-mono">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-44 bg-slate-900 rounded"></div>
      </div>
    );
  }

  const stateObj = canonicalState || lastValidState;
  const providerHealth = rawProviderHealth;
  const macroObj = stateObj?.macro_intelligence || {};
  const macroHealth = rawMacroHealth;
  const economicCalendarHealth = macroObj.economic_calendar_health || {};
  const newsItems = safeArray(stateObj?.news_intelligence?.items).length;
  const brokerStatus = {
    status: brokerStatusStr,
    session_valid: stateObj?.broker_status?.session_valid ?? false,
    reconnect_required: stateObj?.broker_status?.reconnect_required ?? false,
    last_successful_update: stateObj?.broker_status?.last_successful_update ?? null,
  };
  const unavailableCapabilities = [
    { capability: "Licensed institutional terminal feed", state: "LICENSE_REQUIRED", provider: "Not configured" },
    { capability: "Secondary broker execution adapter", state: "NOT_CONFIGURED", provider: "Not configured" },
  ];

  const handleExportDiagnostics = () => {
    const diagnostics = {
      schema_version: stateObj?.schema_version,
      runtime_id: stateObj?.runtime_id,
      state_sequence: stateObj?.state_sequence,
      generated_at: stateObj?.generated_at,
      brokerStatus,
      market_session: stateObj?.market_session,
      market_feed_status: stateObj?.market_feed_status,
      provider_health: { news: providerHealth, macro: macroHealth },
    };
    const href = URL.createObjectURL(new Blob([JSON.stringify(diagnostics, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = "ardhamind-diagnostics.json";
    anchor.click();
    URL.revokeObjectURL(href);
  };

  const datasetRows = [
    { dataset: "NIFTY Spot Index", provider: "Zerodha Kite Quote", providerCount: marketDataObj ? 1 : 0, canonicalCount: stateObj?.market_data?.current_spot ? 1 : 0, workspaceCount: marketDataObj?.current_spot ? 1 : 0, health: stateObj?.market_feed_status || {} },
    { dataset: "Constituent Breadth", provider: "Zerodha Kite Multi-Quote", providerCount: safeNumber(stateObj?.market_data?.breadth?.coverage?.valid), canonicalCount: stateObj?.market_data?.breadth?.advances != null ? 1 : 0, workspaceCount: marketDataObj?.breadth?.advances != null ? 1 : 0, health: stateObj?.market_feed_status || {} },
    { dataset: "Option Chain Matrix", provider: "Zerodha Kite Depth & OI", providerCount: safeNumber(stateObj?.option_intelligence?.strikes?.length) * 2, canonicalCount: stateObj?.option_intelligence?.strikes?.length || 0, workspaceCount: safeArray(stateObj?.option_intelligence?.strikes).length, health: stateObj?.option_intelligence?.provider_health?.option_chain_provider || {} },
    { dataset: "FII / DII Cash Flows", provider: "NSE Official Report Ingestion", providerCount: safeArray(stateObj?.macro_intelligence?.institutional_flows).length, canonicalCount: safeArray(stateObj?.macro_intelligence?.institutional_flows).length, workspaceCount: safeArray(stateObj?.macro_intelligence?.institutional_flows).length, health: stateObj?.macro_intelligence?.provider_health?.institutional_flow_provider || {} },
    { dataset: "Global Equities & Commodities", provider: "Yahoo Finance API Ingestion", providerCount: Object.keys(stateObj?.macro_intelligence?.quotes || {}).length, canonicalCount: Object.keys(stateObj?.macro_intelligence?.quotes || {}).length, workspaceCount: Object.keys(stateObj?.macro_intelligence?.quotes || {}).length, health: stateObj?.macro_intelligence?.provider_health?.global_quotes_provider || {} },
  ];

  const handleProviderSort = (key: typeof providerSortBy) => {
    if (providerSortBy === key) {
      setProviderSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setProviderSortBy(key);
      setProviderSortDir("asc");
    }
  };

  return (
    <div id="settings-dashboard" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6 text-left font-sans">
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <KeyRound size={20} className="text-emerald-400" />
          <h2 className="text-lg font-bold text-white uppercase tracking-wider font-mono">System Settings &amp; Diagnostics</h2>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SECTION 1: BROKER CONNECTIVITY */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <Database size={16} className="text-emerald-400" />
              1. Kite Connection
            </div>
            <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-extrabold uppercase border ${
              isConnected ? "bg-emerald-950 text-emerald-400 border-emerald-800" : "bg-rose-950 text-rose-400 border-rose-800"
            }`}>
              {brokerStatusStr}
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Broker Provider:</span>
              <span className="font-bold text-white">Zerodha KiteConnect v5</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Account Client ID:</span>
              <span className="font-bold text-cyan-400">{brokerAccount?.client_id && brokerAccount.client_id !== "N/A" ? "PROFILE VALIDATED — IDENTIFIER HIDDEN" : "Unavailable — profile fetch failed"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900"><span className="text-slate-500">Session Validity:</span><span className="text-slate-300">{isConnected ? (canonicalState?.broker_status?.session_valid === false ? "INVALID" : "CONNECTED (PROFILE VALIDATED)") : "INVALID / DISCONNECTED"}</span></div>
            <div className="flex justify-between py-1 border-b border-slate-900"><span className="text-slate-500">Last Authenticated:</span><span className="text-slate-300">{canonicalState?.broker_status?.last_authenticated_at ? formatTimestampIST(canonicalState.broker_status.last_authenticated_at) : "Unavailable"}</span></div>
            <div className="flex justify-between py-1 border-b border-slate-900"><span className="text-slate-500">Last Profile Validation:</span><span className="text-slate-300">{canonicalState?.broker_status?.last_profile_validation ? formatTimestampIST(canonicalState.broker_status.last_profile_validation) : "Unavailable"}</span></div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Redirect Callback URL:</span>
              <span className="text-slate-300 font-mono text-[11px]">http://127.0.0.1:3000/api/broker/callback</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Execution Capability:</span>
              <span className="text-emerald-400 font-semibold">READ ONLY (Orders Hard-Disabled)</span>
            </div>
          </div>

          <div className="pt-2 space-y-2">
            {message && (
              <div className="p-2 bg-slate-950 border border-slate-900 text-[10px] text-cyan-400 font-mono rounded">
                {message}
              </div>
            )}
            {isConnected ? (
              <button onClick={handleDisconnect} className="px-3 py-1.5 bg-rose-950 hover:bg-rose-900 border border-rose-800 text-xs font-mono text-rose-300 rounded font-bold transition">
                Disconnect Broker Session
              </button>
            ) : (
              <button onClick={handleOAuthConnect} className="px-3 py-1.5 bg-cyan-900 hover:bg-cyan-800 border border-cyan-700 text-xs font-mono text-white rounded font-bold transition">
                Authenticate Broker (Zerodha OAuth)
              </button>
            )}
          </div>
        </section>

        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-3 col-span-1 md:col-span-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-white font-mono">Unavailable Capabilities</h3>
          <p className="text-[10px] text-slate-500">Unavailable and licensed-only sources remain explicit; no estimates are rendered.</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {unavailableCapabilities.map(item => <div key={item.capability} className="rounded border border-slate-800 bg-slate-950 p-3 text-xs"><div className="font-semibold text-slate-300">{item.capability}</div><div className="mt-1 font-mono text-[10px] text-amber-400">{mapTraderEnum(item.state)} · {item.provider}</div></div>)}
          </div>
        </section>

        {/* SECTION 2: MARKET DATA FEEDS */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <Radio size={16} className="text-emerald-400" />
              2. Market Data Feeds & WebSocket
            </div>
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono text-[10px] font-extrabold uppercase">
              {safeString(canonicalState?.market_feed_status?.status || "UNAVAILABLE").toUpperCase()}
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">WebSocket Transport:</span>
              <span className="font-bold text-emerald-400">{marketConnection === "CONNECTED" ? "CONNECTED (ws://localhost:3000)" : marketConnection}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Market Session State:</span>
              <span className="font-bold text-amber-400">{safeString(canonicalState?.market_session?.status || "CLOSED").toUpperCase()}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Option Chain Aggregate:</span>
              <span className="text-slate-300">{safeString(canonicalState?.option_intelligence?.status || "UNAVAILABLE").toUpperCase()}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Last Observation Timestamp:</span>
              <span className="text-slate-400">{formatTimestampIST(canonicalState?.generated_at)}</span>
            </div>
          </div>
        </section>

        {/* SECTION 3: NEWS INTELLIGENCE PROVIDERS */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4 col-span-1 md:col-span-2">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center border-b border-slate-800 pb-3 gap-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <Globe size={16} className="text-purple-400" />
              3. News &amp; Macro Provider Health
            </div>

            {/* Sorting controls */}
            <div className="flex items-center gap-2 font-mono text-[9px] text-slate-400">
              <span className="font-bold">Sort:</span>
              <button
                onClick={() => handleProviderSort("name")}
                className={`px-1.5 py-0.5 rounded border ${providerSortBy === "name" ? "border-purple-600 bg-purple-950/40 text-purple-300 font-bold" : "border-slate-800 text-slate-500"}`}
              >
                Name {providerSortBy === "name" && (providerSortDir === "asc" ? "↑" : "↓")}
              </button>
              <button
                onClick={() => handleProviderSort("status")}
                className={`px-1.5 py-0.5 rounded border ${providerSortBy === "status" ? "border-purple-600 bg-purple-950/40 text-purple-300 font-bold" : "border-slate-800 text-slate-500"}`}
              >
                Status {providerSortBy === "status" && (providerSortDir === "asc" ? "↑" : "↓")}
              </button>
              <button
                onClick={() => handleProviderSort("freshness")}
                className={`px-1.5 py-0.5 rounded border ${providerSortBy === "freshness" ? "border-purple-600 bg-purple-950/40 text-purple-300 font-bold" : "border-slate-800 text-slate-500"}`}
              >
                Freshness {providerSortBy === "freshness" && (providerSortDir === "asc" ? "↑" : "↓")}
              </button>
            </div>
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono text-[10px] font-extrabold uppercase shrink-0">
              {safeString(newsObj.coverage_status || "UNAVAILABLE").toUpperCase()} ({newsItems} items)
            </span>
          </div>

          <div data-provider-health-scroll tabIndex={0} aria-label="Scrollable news and macro provider health" className="max-h-[28rem] space-y-1 overflow-y-auto overflow-x-hidden pr-2 text-xs font-mono sm:max-h-[32rem]">
            {sortedProviders.map(([name, value]: [string, any]) => (
              <div key={name} className="flex min-w-0 flex-col gap-1 border-b border-slate-900 py-1.5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <span className="text-slate-300 font-bold block">{safeString(value.provider_name || name)}</span>
                  <span className="text-[9px] text-slate-500 block">
                    Success: {value.last_successful_fetch ? formatTimestampIST(value.last_successful_fetch) : "Never"} · Attempt: {value.last_attempted_fetch ? formatTimestampIST(value.last_attempted_fetch) : "Never"}
                  </span>
                  {value.operational_error_reason && <span className="text-[9px] text-rose-400 block">Reason: {safeString(value.operational_error_reason)}</span>}
                </div>
                <div className="flex shrink-0 flex-wrap items-center gap-2">
                  <span className="text-[10px] text-slate-500" title={`Raw ${safeNumber(value.raw_item_count)} · Normalized ${safeNumber(value.normalized_item_count)} · Unique ${safeNumber(value.unique_item_count)} · Clusters ${safeNumber(value.event_cluster_count)} · Streams ${safeArray(value.discovery_streams).join(", ") || "N/A"} · Rate ${safeString(value.rate_limit_state || "N/A")}`}>R {safeNumber(value.raw_item_count, safeNumber(value.item_count, 0))} · N {safeNumber(value.normalized_item_count)} · U {safeNumber(value.unique_item_count)} · C {safeNumber(value.event_cluster_count)} · {safeString(value.rate_limit_state || "N/A")}</span>
                  <span className={`px-1.5 py-0.5 rounded border text-[10px] font-bold ${
                    getHealthRank(value) === 1 ? "bg-rose-950 text-rose-400 border-rose-800" : getHealthRank(value) === 2 ? "bg-amber-955/60 text-amber-400 border-amber-800" : "bg-emerald-950 text-emerald-400 border-emerald-800"
                  }`}>
                    {safeString(value.status || "UNAVAILABLE").toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* SECTION 4: DIAGNOSTICS & SYSTEM INFO */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4 col-span-1 md:col-span-2">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <Server size={16} className="text-cyan-400" />
              4. Diagnostics & System Telemetry
            </div>
            <button onClick={handleExportDiagnostics} className="inline-flex items-center gap-1.5 rounded border border-cyan-800 bg-cyan-950 px-2 py-1 font-mono text-[10px] font-bold text-cyan-300"><Download size={12}/>Export Diagnostics</button>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">API Gateway Latency:</span>
              <span className="font-bold text-cyan-400">{apiLatency != null ? `${apiLatency} ms` : "UNAVAILABLE"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900"><span className="text-slate-500">Last Successful UI Refresh:</span><span className="text-slate-300">{lastSyncTime || "Unavailable"}</span></div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Canonical State Schema:</span>
              <span className="font-bold text-white">{safeString(canonicalState?.schema_version || "UNAVAILABLE")}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Application Version:</span>
              <span className="font-bold text-white">v1.3.1-PROD</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Runtime Target ID:</span>
              <span className="text-slate-400">{safeString(canonicalState?.runtime_id || "UNAVAILABLE")}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Environment Profile:</span>
              <span className="text-cyan-300 font-bold">LIVE INTELLIGENCE · READ ONLY</span>
            </div>
          </div>
        </section>
      </div>

      <section data-news-coverage-matrix className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-left">
        <div className="mb-4"><h3 className="font-mono text-xs font-bold uppercase tracking-wider text-white">Global News Coverage Matrix · {safeString(newsObj.coverage_status || "UNAVAILABLE")}</h3><p className="mt-1 text-[10px] text-slate-500">A stream can be healthy with zero current stories when its bounded query completed successfully.</p></div>
        <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Stream", "Sources", "Raw", "Normalized", "Unique", "Clusters", "Latest", "Status"].map(label => <th key={label} className="border-b border-slate-800 px-2 py-2">{label}</th>)}</tr></thead><tbody>{(safeArray(newsObj.coverage_matrix) as any[]).map(row => <tr key={safeString(row.stream)} className="text-slate-300"><td className="border-b border-slate-900 px-2 py-2 font-semibold text-white">{safeString(row.stream)}</td><td className="border-b border-slate-900 px-2 py-2">{safeArray(row.sources).join(", ") || "—"}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.raw_items)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.normalized_items)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.unique_items)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.clusters)}</td><td className="border-b border-slate-900 px-2 py-2">{row.latest_timestamp ? formatTimestampIST(row.latest_timestamp) : "—"}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(row.status)}</td></tr>)}</tbody></table></div>
      </section>

      <section data-news-temporal-diagnostics className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-left">
        <div className="mb-4"><h3 className="font-mono text-xs font-bold uppercase tracking-wider text-white">News Temporal Integrity</h3><p className="mt-1 text-[10px] text-slate-500">Publication-time eligibility is recomputed independently of fetch and cache timestamps.</p></div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">{Object.entries(newsObj.temporal_diagnostics?.counts || {}).map(([label, value]) => <div key={label} className="rounded border border-slate-800 bg-slate-950 p-3"><div className="font-mono text-[9px] text-slate-500">{label}</div><div className="mt-1 font-mono text-sm font-bold text-cyan-300">{safeNumber(value)}</div></div>)}</div>
        <div className="mt-4 grid gap-2 text-[10px] font-mono text-slate-400 md:grid-cols-3"><span>Window: {safeNumber(newsObj.current_window_hours)}h</span><span>Oldest current: {newsObj.temporal_diagnostics?.oldest_current_timestamp ? formatTimestampIST(newsObj.temporal_diagnostics.oldest_current_timestamp) : "NONE"}</span><span>Newest current: {newsObj.temporal_diagnostics?.newest_current_timestamp ? formatTimestampIST(newsObj.temporal_diagnostics.newest_current_timestamp) : "NONE"}</span></div>
      </section>

      <section data-economic-calendar-health className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-left">
        <div className="mb-4"><h3 className="font-mono text-xs font-bold uppercase tracking-wider text-white">Economic Calendar Provider Health · {safeString(macroObj.calendar_coverage || "UNAVAILABLE")}</h3><p className="mt-1 text-[10px] text-slate-500">READY requires at least one usable NIFTY-relevant record with an exact timezone-aware schedule.</p></div>
        <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Provider", "Regions", "Scheduled", "Released", "Last Success", "Next Event", "Rate Limit", "Status", "Failure"].map(label => <th key={label} className="border-b border-slate-800 px-2 py-2">{label}</th>)}</tr></thead><tbody>{Object.entries(economicCalendarHealth).map(([name, health]: [string, any]) => <tr key={name} className="text-slate-300"><td className="border-b border-slate-900 px-2 py-2 font-semibold text-white">{name}</td><td className="border-b border-slate-900 px-2 py-2">{safeArray(health.coverage_regions).join(", ") || "—"}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(health.scheduled_record_count)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(health.released_record_count)}</td><td className="border-b border-slate-900 px-2 py-2">{health.last_successful_fetch ? formatTimestampIST(health.last_successful_fetch) : "Never"}</td><td className="border-b border-slate-900 px-2 py-2">{health.next_scheduled_event ? formatTimestampIST(health.next_scheduled_event) : "NONE"}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(health.rate_limit_state || "UNAVAILABLE")}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(health.status).toUpperCase()}</td><td className="max-w-xs border-b border-slate-900 px-2 py-2 text-rose-300">{safeString(health.failure_detail || health.operational_error_reason || "—")}</td></tr>)}</tbody></table></div>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-left">
        <div className="mb-4"><h3 className="font-mono text-xs font-bold uppercase tracking-wider text-white">5. Provider → Canonical → Workspace Health Matrix</h3><p className="mt-1 text-[10px] text-slate-500">A provider is usable only when valid records survive into the canonical state and the target workspace.</p></div>
        <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Dataset", "Provider", "Records", "Last Success", "Last Attempt", "Freshness", "Status", "Failure Reason", "Canonical", "Workspace"].map(label => <th key={label} className="border-b border-slate-800 px-2 py-2">{label}</th>)}</tr></thead><tbody>{datasetRows.map((row, index) => <tr key={`${row.dataset}-${index}`} className="text-slate-300"><td className="border-b border-slate-900 px-2 py-2 font-semibold text-white">{row.dataset}</td><td className="border-b border-slate-900 px-2 py-2">{row.provider}</td><td className="border-b border-slate-900 px-2 py-2">{row.providerCount}</td><td className="border-b border-slate-900 px-2 py-2">{row.health.last_successful_fetch ? formatTimestampIST(row.health.last_successful_fetch) : "Never"}</td><td className="border-b border-slate-900 px-2 py-2">{row.health.last_attempted_fetch ? formatTimestampIST(row.health.last_attempted_fetch) : "Never"}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(row.health.freshness_status || row.health.status || "unavailable").toUpperCase()}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(row.health.status || (row.canonicalCount > 0 ? "usable" : "unavailable")).toUpperCase()}</td><td className="max-w-xs border-b border-slate-900 px-2 py-2 text-rose-300">{safeString(row.health.failure_detail || row.health.operational_error_reason || "—")}</td><td className="border-b border-slate-900 px-2 py-2">{row.canonicalCount}</td><td className="border-b border-slate-900 px-2 py-2">{row.workspaceCount}</td></tr>)}</tbody></table></div>
      </section>
    </div>
  );
}

export default SettingsDashboard;
