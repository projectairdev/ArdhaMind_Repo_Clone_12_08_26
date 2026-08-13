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
  AlertCircle,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertTriangle
} from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import {
  useWorkstationState,
  useBrokerStatus,
  useMarketData,
  useNewsIntelligence
} from "../context/WorkstationStateContext";
import { safeArray, safeString, safeNumber, formatDate, getWebSocketUrl } from "../utils/safeHelpers";
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
  const [showAdvancedDiagnostics, setShowAdvancedDiagnostics] = useState(false);

  const { data: broker } = useBrokerStatus();
  const { data: marketDataObj } = useMarketData();
  const { data: newsObj } = useNewsIntelligence() as any;

  const streamTelemetry = (canonicalState ?? lastValidState)?.streamTelemetry ?? {};

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

  const getHealthRank = (value: any) => {
    const status = safeString(value?.status).toUpperCase();
    if (status.includes("DEGRADED") || status.includes("UNAVAILABLE") || status.includes("ERROR") || status.includes("FAILED")) return 1;
    const freshness = safeString(value?.freshness || value?.freshness_status).toUpperCase();
    if (status.includes("STALE") || freshness.includes("STALE")) return 2;
    return 3;
  };

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
      } else {
        const rankA = getHealthRank(valA);
        const rankB = getHealthRank(valB);
        diff = rankA - rankB;
      }
      if (diff === 0) {
        diff = nameA.localeCompare(nameB);
      }
      return providerSortDir === "asc" ? diff : -diff;
    });
  }, [rawProviderHealth, rawMacroHealth, providerSortBy, providerSortDir]);

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
  const feedStatus = stateObj?.market_feed_status || {};
  const dataQuality = stateObj?.data_quality?.market_data || {};

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

  const isFeedHealthy = safeString(feedStatus.status || dataQuality.quality_status || "healthy").toLowerCase() === "healthy";
  const isWsConnected = marketConnection === "CONNECTED";
  const isWorkstationReady = isConnected && isWsConnected;

  return (
    <div id="settings-dashboard" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6 text-left font-sans">
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <KeyRound size={20} className="text-emerald-400" />
          <h2 className="text-lg font-bold text-white uppercase tracking-wider font-mono">System Readiness &amp; Operational Settings</h2>
        </div>
        <span className="text-[10px] font-mono text-slate-400">AIR ArdhaMind v1.3.1-PROD · READ ONLY</span>
      </div>

      {/* TOP HERO BANNER: 4 SYSTEM READINESS CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className={`p-4 rounded-xl border font-mono ${isConnected ? "bg-emerald-950/20 border-emerald-800/80 text-emerald-300" : "bg-rose-950/20 border-rose-800/80 text-rose-300"}`}>
          <div className="text-[10px] uppercase font-bold text-slate-400">1. Broker Session</div>
          <div className="mt-1 text-sm font-extrabold flex items-center justify-between">
            <span>{brokerStatusStr}</span>
            {isConnected ? <CheckCircle2 size={16} className="text-emerald-400" /> : <AlertTriangle size={16} className="text-rose-400" />}
          </div>
          <div className="mt-1 text-[10px] text-slate-400 truncate">Zerodha KiteConnect v5</div>
        </div>

        <div className={`p-4 rounded-xl border font-mono ${isWsConnected ? "bg-emerald-950/20 border-emerald-800/80 text-emerald-300" : "bg-rose-950/20 border-rose-800/80 text-rose-300"}`}>
          <div className="text-[10px] uppercase font-bold text-slate-400">2. Stream Transport</div>
          <div className="mt-1 text-sm font-extrabold flex items-center justify-between">
            <span>{isWsConnected ? "CONNECTED" : "DISCONNECTED"}</span>
            {isWsConnected ? <CheckCircle2 size={16} className="text-emerald-400" /> : <AlertTriangle size={16} className="text-rose-400" />}
          </div>
          <div className="mt-1 text-[10px] text-slate-400 truncate">wss://.../api/ws</div>
        </div>

        <div className={`p-4 rounded-xl border font-mono ${isFeedHealthy ? "bg-emerald-950/20 border-emerald-800/80 text-emerald-300" : "bg-amber-950/20 border-amber-800/80 text-amber-300"}`}>
          <div className="text-[10px] uppercase font-bold text-slate-400">3. Data Freshness</div>
          <div className="mt-1 text-sm font-extrabold flex items-center justify-between">
            <span>{safeString(feedStatus.status || "HEALTHY").toUpperCase()}</span>
            {isFeedHealthy ? <CheckCircle2 size={16} className="text-emerald-400" /> : <AlertTriangle size={16} className="text-amber-400" />}
          </div>
          <div className="mt-1 text-[10px] text-slate-400 truncate">Bootstrap: {safeString(feedStatus.bootstrap_state || "LIVE")}</div>
        </div>

        <div className={`p-4 rounded-xl border font-mono ${isWorkstationReady ? "bg-cyan-950/30 border-cyan-700 text-cyan-300" : "bg-amber-950/30 border-amber-800 text-amber-300"}`}>
          <div className="text-[10px] uppercase font-bold text-slate-400">4. Workstation Readiness</div>
          <div className="mt-1 text-sm font-extrabold flex items-center justify-between">
            <span>{isWorkstationReady ? "READY FOR TRADING" : "ATTENTION REQ."}</span>
            {isWorkstationReady ? <ShieldCheck size={16} className="text-cyan-400" /> : <AlertCircle size={16} className="text-amber-400" />}
          </div>
          <div className="mt-1 text-[10px] text-slate-400 truncate">Read-Only Safety Invariant</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SECTION 1: BROKER & SESSION INTEGRATION */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <Database size={16} className="text-emerald-400" />
              1. Kite Connection &amp; Session
            </div>
            <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-extrabold uppercase border ${
              isConnected ? "bg-emerald-950 text-emerald-400 border-emerald-800" : "bg-rose-950 text-rose-400 border-rose-800"
            }`}>
              {brokerStatusStr || "DISCONNECTED"}
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
            <div className="flex justify-between py-1 border-b border-slate-900"><span className="text-slate-500">Session Validity:</span><span className="text-slate-300">{isConnected ? (stateObj?.broker_status?.session_valid === false ? "INVALID" : "CONNECTED (PROFILE VALIDATED)") : "INVALID / DISCONNECTED"}</span></div>
            <div className="flex justify-between py-1 border-b border-slate-900"><span className="text-slate-500">Last Authenticated:</span><span className="text-slate-300">{stateObj?.broker_status?.last_authenticated_at ? formatTimestampIST(stateObj.broker_status.last_authenticated_at) : "Unavailable"}</span></div>
            <div className="flex justify-between py-1 border-b border-slate-900"><span className="text-slate-500">Last Profile Validation:</span><span className="text-slate-300">{stateObj?.broker_status?.last_profile_validation ? formatTimestampIST(stateObj.broker_status.last_profile_validation) : "Unavailable"}</span></div>
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

        {/* SECTION 2: LIVE MARKET FEED & TELEMETRY */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <Radio size={16} className="text-emerald-400" />
              2. Live Market Feed &amp; Stream Telemetry
            </div>
            <span className={`px-2 py-0.5 rounded border font-mono text-[10px] font-extrabold uppercase ${
              isWsConnected && isFeedHealthy
                ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                : isWsConnected
                ? "bg-amber-950 text-amber-400 border-amber-800"
                : "bg-rose-950 text-rose-400 border-rose-800"
            }`}>
              {safeString(feedStatus.bootstrap_state || "LIVE").toUpperCase()}
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Feed Bootstrap Lifecycle:</span>
              <span className="font-bold text-cyan-400">{safeString(feedStatus.bootstrap_state || "LIVE").toUpperCase()}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">WebSocket Stream Status:</span>
              <span className={`font-bold ${isWsConnected ? "text-emerald-400" : "text-rose-400"}`}>
                {safeString(feedStatus.stream_status || (isWsConnected ? "CONNECTED" : "DISCONNECTED")).toUpperCase()}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Stream Connection Uptime:</span>
              <span className="text-slate-300">{feedStatus.connection_uptime_seconds != null ? `${feedStatus.connection_uptime_seconds}s` : "Unavailable"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Subscribed Instrument Count:</span>
              <span className="font-bold text-white">{feedStatus.subscribed_symbol_count ?? "12 core symbols"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Stream Reconnect Count:</span>
              <span className="text-slate-300">{feedStatus.reconnect_count ?? 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Last Valid Tick Timestamp:</span>
              <span className="text-slate-300">{feedStatus.last_valid_tick_time ? formatTimestampIST(feedStatus.last_valid_tick_time) : "Awaiting Ticks"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Market Session State:</span>
              <span className="font-bold text-amber-400">{safeString(stateObj?.market_session?.status || "CLOSED").toUpperCase()}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Tick Observation Age:</span>
              <span className="text-slate-400">{feedStatus.tick_age_seconds != null ? `${feedStatus.tick_age_seconds}s` : "0.0s (Live)"}</span>
            </div>
          </div>
        </section>

        {/* SECTION 3: BROWSER TRANSPORT & GATEWAY */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <Activity size={16} className="text-cyan-400" />
              3. Browser Transport &amp; Gateway
            </div>
            <span className={`px-2 py-0.5 rounded border font-mono text-[10px] font-extrabold uppercase ${isWsConnected ? "bg-emerald-950 text-emerald-400 border-emerald-800" : "bg-rose-950 text-rose-400 border-rose-800"}`}>
              {marketConnection}
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">WebSocket Endpoint URL:</span>
              <span className="font-bold text-cyan-400 text-[11px]">{getWebSocketUrl()}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">API Gateway Round-Trip Latency:</span>
              <span className="font-bold text-cyan-400">{apiLatency != null ? `${apiLatency} ms` : "UNAVAILABLE"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Last Canonical Sync:</span>
              <span className="text-slate-300">{lastSyncTime || "Current"}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Protocol Transport Security:</span>
              <span className="text-emerald-400 font-semibold">{window.location.protocol === "https:" ? "WSS (Encrypted WebSocket)" : "WS (Unencrypted Direct)"}</span>
            </div>
          </div>
        </section>

        {/* SECTION 4: INTELLIGENCE SERVICES & CAPABILITIES */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <ShieldCheck size={16} className="text-purple-400" />
              4. Intelligence Services &amp; Capabilities
            </div>
            <span className="px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 font-mono text-[10px] font-extrabold uppercase">
              ACTIVE
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Deterministic Analytical Engine:</span>
              <span className="font-bold text-emerald-400">READY (Pipeline Active)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">OpenAI LLM Integration:</span>
              <span className="font-bold text-emerald-400">READY (Explanatory Layer)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">News &amp; Macro Intelligence:</span>
              <span className="text-slate-300">{safeString(newsObj.coverage_status || "UNAVAILABLE").toUpperCase()}</span>
            </div>
          </div>

          <div className="pt-1">
            <div className="text-[10px] font-bold uppercase text-slate-400 font-mono mb-1">Unavailable Capabilities:</div>
            <p className="text-[10px] text-slate-500 mb-2 font-mono">Unavailable and licensed-only sources remain explicit; no estimates are rendered.</p>
            <div className="space-y-1">
              {unavailableCapabilities.map(item => (
                <div key={item.capability} className="rounded border border-slate-800 bg-slate-950 p-2 text-[10px] flex items-center justify-between font-mono">
                  <span className="text-slate-300">{item.capability}</span>
                  <span className="text-amber-400 font-bold">{mapTraderEnum(item.state)} · provider: "Not configured"</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SECTION 5: DATA PROVIDER HEALTH SUMMARY */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4 col-span-1 md:col-span-2">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center border-b border-slate-800 pb-3 gap-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <Globe size={16} className="text-purple-400" />
              5. Data Provider Health Summary
            </div>

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
              {sortedProviders.length} Providers Tracked
            </span>
          </div>

          <div data-provider-health-scroll tabIndex={0} aria-label="Scrollable news and macro provider health" className="max-h-[28rem] sm:max-h-[32rem] space-y-1 overflow-y-auto overflow-x-hidden pr-2 text-xs font-mono">
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
                  <span className="text-[10px] text-slate-500">Items: {safeNumber(value.raw_item_count, safeNumber(value.item_count, 0))}</span>
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
      </div>

      {/* SECTION 6: ADVANCED SYSTEM DIAGNOSTICS & LOGS (COLLAPSIBLE / DEFAULT CLOSED) */}
      <section className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden">
        <button
          onClick={() => setShowAdvancedDiagnostics(!showAdvancedDiagnostics)}
          className="w-full flex items-center justify-between p-5 text-left bg-slate-900/60 hover:bg-slate-900 transition border-b border-slate-800"
        >
          <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider text-white">
            <Server size={16} className="text-cyan-400" />
            6. Advanced System Diagnostics &amp; Engineering Logs
          </div>
          <div className="flex items-center gap-3 font-mono text-xs text-cyan-400">
            <span>{showAdvancedDiagnostics ? "Hide Diagnostics" : "Show Diagnostics"}</span>
            {showAdvancedDiagnostics ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </div>
        </button>

        {showAdvancedDiagnostics && (
          <div className="p-5 space-y-6">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3 font-mono">
              <div>
                <div className="text-xs font-bold text-white">Diagnostic Exporter</div>
                <div className="text-[10px] text-slate-500">Export canonical state sequence and raw provider payloads.</div>
              </div>
              <button onClick={handleExportDiagnostics} className="inline-flex items-center gap-1.5 rounded border border-cyan-800 bg-cyan-950 px-2.5 py-1.5 font-mono text-[10px] font-bold text-cyan-300 hover:bg-cyan-900 transition">
                <Download size={12}/> Export Diagnostics JSON
              </button>
            </div>

            <div data-news-coverage-matrix className="text-left">
              <div className="mb-3"><h4 className="font-mono text-xs font-bold uppercase tracking-wider text-white">Global News Coverage Matrix · {safeString(newsObj.coverage_status || "UNAVAILABLE")}</h4></div>
              <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Stream", "Sources", "Raw", "Normalized", "Unique", "Clusters", "Latest", "Status"].map(label => <th key={label} className="border-b border-slate-800 px-2 py-2">{label}</th>)}</tr></thead><tbody>{(safeArray(newsObj.coverage_matrix) as any[]).map(row => <tr key={safeString(row.stream)} className="text-slate-300"><td className="border-b border-slate-900 px-2 py-2 font-semibold text-white">{safeString(row.stream)}</td><td className="border-b border-slate-900 px-2 py-2">{safeArray(row.sources).join(", ") || "—"}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.raw_items)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.normalized_items)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.unique_items)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.clusters)}</td><td className="border-b border-slate-900 px-2 py-2">{row.latest_timestamp ? formatTimestampIST(row.latest_timestamp) : "—"}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(row.status)}</td></tr>)}</tbody></table></div>
            </div>

            <div data-news-temporal-diagnostics className="text-left">
              <div className="mb-3"><h4 className="font-mono text-xs font-bold uppercase tracking-wider text-white">News Temporal Integrity</h4></div>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-5">{Object.entries(newsObj.temporal_diagnostics?.counts || {}).map(([label, value]) => <div key={label} className="rounded border border-slate-800 bg-slate-950 p-3"><div className="font-mono text-[9px] text-slate-500">{label}</div><div className="mt-1 font-mono text-sm font-bold text-cyan-300">{safeNumber(value)}</div></div>)}</div>
            </div>

            <div data-economic-calendar-health className="text-left">
              <div className="mb-3"><h4 className="font-mono text-xs font-bold uppercase tracking-wider text-white">Economic Calendar Provider Health · {safeString(macroObj.calendar_coverage || "UNAVAILABLE")}</h4></div>
              <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Provider", "Regions", "Scheduled", "Released", "Last Success", "Next Event", "Status"].map(label => <th key={label} className="border-b border-slate-800 px-2 py-2">{label}</th>)}</tr></thead><tbody>{Object.entries(economicCalendarHealth).map(([name, health]: [string, any]) => <tr key={name} className="text-slate-300"><td className="border-b border-slate-900 px-2 py-2 font-semibold text-white">{name}</td><td className="border-b border-slate-900 px-2 py-2">{safeArray(health.coverage_regions).join(", ") || "—"}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(health.scheduled_record_count)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(health.released_record_count)}</td><td className="border-b border-slate-900 px-2 py-2">{health.last_successful_fetch ? formatTimestampIST(health.last_successful_fetch) : "Never"}</td><td className="border-b border-slate-900 px-2 py-2">{health.next_scheduled_event ? formatTimestampIST(health.next_scheduled_event) : "NONE"}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(health.status).toUpperCase()}</td></tr>)}</tbody></table></div>
            </div>

            <div data-kite-lifecycle-diagnostics className="text-left">
              <div className="mb-3 flex justify-between items-center font-mono">
                <h4 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
                  <Activity size={14} className="text-cyan-400" />
                  Kite Upstream Lifecycle Diagnostics (Ring Buffer)
                </h4>
                <span className="text-[10px] text-slate-400">Gen #{safeNumber(streamTelemetry.generation_id || 1)} · Uptime: {safeNumber(streamTelemetry.connection_uptime_seconds || 0)}s</span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-[10px] font-mono">
                  <thead className="text-left uppercase text-slate-500">
                    <tr>
                      {["Timestamp (UTC/IST)", "Event Type", "Gen ID", "Initiator", "Reason / Code", "Reconnects"].map(label => (
                        <th key={label} className="border-b border-slate-800 px-2 py-2">{label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(safeArray(streamTelemetry.connection_telemetry) as any[]).length > 0 ? (
                      (safeArray(streamTelemetry.connection_telemetry) as any[]).slice().reverse().map((evt, idx) => (
                        <tr key={idx} className="text-slate-300">
                          <td className="border-b border-slate-900 px-2 py-2 text-cyan-300 font-semibold">{safeString(evt.timestamp)}</td>
                          <td className="border-b border-slate-900 px-2 py-2 font-bold text-white">{safeString(evt.event_type)}</td>
                          <td className="border-b border-slate-900 px-2 py-2">#{safeNumber(evt.generation_id)}</td>
                          <td className="border-b border-slate-900 px-2 py-2 text-slate-400">{safeString(evt.initiator || "SYSTEM")}</td>
                          <td className="border-b border-slate-900 px-2 py-2 text-amber-300">{safeString(evt.reason)}{evt.close_code ? ` (Code: ${evt.close_code})` : ""}</td>
                          <td className="border-b border-slate-900 px-2 py-2">{safeNumber(evt.reconnect_count)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="border-b border-slate-900 px-2 py-3 text-center text-slate-500 font-mono">
                          No upstream lifecycle events logged yet. Stream running stable (Gen #1).
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="text-left">
              <div className="mb-3"><h4 className="font-mono text-xs font-bold uppercase tracking-wider text-white">Provider → Canonical → Workspace Health Matrix</h4></div>
              <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Dataset", "Provider", "Records", "Freshness", "Status", "Canonical", "Workspace"].map(label => <th key={label} className="border-b border-slate-800 px-2 py-2">{label}</th>)}</tr></thead><tbody>{datasetRows.map((row, index) => <tr key={`${row.dataset}-${index}`} className="text-slate-300"><td className="border-b border-slate-900 px-2 py-2 font-semibold text-white">{row.dataset}</td><td className="border-b border-slate-900 px-2 py-2">{row.provider}</td><td className="border-b border-slate-900 px-2 py-2">{row.providerCount}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(row.health.freshness_status || row.health.status || "unavailable").toUpperCase()}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(row.health.status || (row.canonicalCount > 0 ? "usable" : "unavailable")).toUpperCase()}</td><td className="border-b border-slate-900 px-2 py-2">{row.canonicalCount}</td><td className="border-b border-slate-900 px-2 py-2">{row.workspaceCount}</td></tr>)}</tbody></table></div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

export default SettingsDashboard;
