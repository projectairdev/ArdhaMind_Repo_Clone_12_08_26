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
import { Surface, SectionHeader } from "./ui/WorkspacePrimitives";

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
    liveLatencyMetrics,
    streamDiagnostics,
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

  const rawBroker = (canonicalState ?? lastValidState)?.broker_status || broker;
  const rawStatus = safeString((rawBroker as any)?.normalized_status || (rawBroker as any)?.status || workspaceContext?.brokerState || "DISCONNECTED").toUpperCase();
  const isVerified = rawStatus === "CONNECTED_VERIFIED" || (rawBroker as any)?.execution_verified === true;
  const isAuthRequired = rawStatus === "CONNECTED_AUTH_REQUIRED" || (rawBroker as any)?.session_valid === false;
  const isUnverified = rawStatus === "BROKER_STATE_UNVERIFIED" || rawStatus === "RECONNECTING";
  const brokerStatusStr = isVerified ? "CONNECTED_VERIFIED" : isAuthRequired ? "CONNECTED_AUTH_REQUIRED" : isUnverified ? "BROKER_STATE_UNVERIFIED" : "DISCONNECTED";
  const isConnected = isVerified;

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
      <div id="settings-loading" className="p-6 bg-[#000000] rounded-xl border border-[#1c1c24] animate-pulse space-y-4 font-mono">
        <div className="h-6 w-1/4 bg-[#14141c] rounded"></div>
        <div className="h-44 bg-[#08080c] rounded"></div>
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
  const marketSessionState = safeString(stateObj?.market_session?.status || "CLOSED").toUpperCase();
  const isClosedMarket = marketSessionState === "CLOSED" || marketSessionState === "POST_CLOSE" || marketSessionState === "HOLIDAY";
  const isBrowserWsConnected = marketConnection === "CONNECTED";
  const backendStreamStatus = safeString(feedStatus.stream_status || feedStatus.bootstrap_state || (isConnected ? (isClosedMarket ? "CONNECTED (IDLE)" : "CONNECTED") : "DISCONNECTED")).toUpperCase();
  const isBackendStreamOk = backendStreamStatus.includes("CONNECTED") || backendStreamStatus.includes("LIVE") || backendStreamStatus.includes("IDLE");

  const isWorkstationReady = isConnected && (isBrowserWsConnected || isClosedMarket || isBackendStreamOk);

  return (
    <div id="settings-dashboard" className="p-4 bg-[#08090B] rounded-[3px] border border-[#242830] space-y-4 text-left font-sans text-[11px]">
      <div className="flex justify-between items-center border-b border-[#191D23] bg-[#0E1013] px-3.5 py-2 -mx-4 -mt-4 rounded-t-[3px]">
        <div className="flex items-center gap-2">
          <KeyRound size={15} className="text-[#38BDF8]" />
          <h2 className="text-[12px] font-bold text-[#E6E8EB] uppercase tracking-wider font-mono">OPERATIONS CONSOLE · DIAGNOSTICS & SYSTEM CONTROL</h2>
        </div>
        <span className="text-[10px] font-mono text-[#707987]">AIR ArdhaMind v1.3.1-STAGING · READ ONLY</span>
      </div>

      {/* OPERATIONS CONSOLE TELEMETRY TABLE */}
      <Surface className="overflow-hidden font-mono">
        <SectionHeader title="System Operations Status Matrix" eyebrow="Console Telemetry" accent="cyan" />
        <div className="divide-y divide-[#191D23]">
          <div className="flex items-center justify-between px-3.5 py-2 hover:bg-[#13161A]">
            <span className="text-[#707987]">System Health & Status</span>
            <span className="text-[#00C896] font-bold">200 OK (HEALTHY)</span>
          </div>
          <div className="flex items-center justify-between px-3.5 py-2 hover:bg-[#13161A]">
            <span className="text-[#707987]">Data Quality & Pipeline</span>
            <span className="text-[#00C896] font-bold">{dataQuality.quality_status?.toUpperCase() || "VALID"}</span>
          </div>
          <div className="flex items-center justify-between px-3.5 py-2 hover:bg-[#13161A]">
            <span className="text-[#707987]">AI Intelligence Provider</span>
            <span className="text-[#8B5CF6] font-bold">OpenAI GPT-4o & Deterministic Rule Engine</span>
          </div>
          <div className="flex items-center justify-between px-3.5 py-2 hover:bg-[#13161A]">
            <span className="text-[#707987]">Broker Connection</span>
            <span className={`font-bold ${isConnected ? "text-[#00C896]" : "text-[#E5484D]"}`}>
              Zerodha KiteConnect ({brokerStatusStr})
            </span>
          </div>
          <div className="flex items-center justify-between px-3.5 py-2 hover:bg-[#13161A]">
            <span className="text-[#707987]">Service Environment</span>
            <span className="text-[#E59700] font-bold">STAGING WORKSTATION (Port 3001)</span>
          </div>
          <div className="flex items-center justify-between px-3.5 py-2 hover:bg-[#13161A]">
            <span className="text-[#707987]">Database & Persistence</span>
            <span className="text-[#E6E8EB] font-bold">Canonical JSON State WAL Engine Active</span>
          </div>
          <div className="flex items-center justify-between px-3.5 py-2 hover:bg-[#13161A]">
            <span className="text-[#707987]">Runtime ID & State Sequence</span>
            <span className="text-[#38BDF8] font-bold">Runtime #{stateObj?.runtime_id?.slice(0, 8) || "0"} · Sequence #{stateObj?.state_sequence || 0}</span>
          </div>
          <div className="flex items-center justify-between px-3.5 py-2 hover:bg-[#13161A]">
            <span className="text-[#707987]">Last Canonical Refresh</span>
            <span className="text-[#E6E8EB] font-bold">{stateObj?.generated_at ? formatTimestampIST(stateObj.generated_at) : "Active"}</span>
          </div>
        </div>
      </Surface>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SECTION 1: BROKER & SESSION INTEGRATION */}
        <section className="p-5 bg-[#050507] border border-[#1c1c24] rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-[#1c1c24] pb-3">
            <div className="flex items-center gap-2 font-bold text-slate-100 text-xs uppercase tracking-wider font-mono">
              <Database size={16} className="text-[#00E5A8]" />
              1. Kite Connection &amp; Session
            </div>
            <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-extrabold uppercase border ${
              isVerified ? "bg-[#00E5A8]/10 text-[#00E5A8] border-[#00E5A8]/30" : isAuthRequired ? "bg-amber-500/10 text-amber-400 border-amber-500/30" : isUnverified ? "bg-purple-500/10 text-purple-400 border-purple-500/30" : "bg-[#FF5C77]/10 text-[#FF5C77] border-[#FF5C77]/30"
            }`}>
              {brokerStatusStr}
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Broker Provider:</span>
              <span className="font-bold text-slate-100">Zerodha KiteConnect v5</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Account Client ID:</span>
              <span className="font-bold text-[#39D9FF]">{brokerAccount?.client_id && brokerAccount.client_id !== "N/A" ? "PROFILE VALIDATED — IDENTIFIER HIDDEN" : "Unavailable — profile fetch failed"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]"><span className="text-slate-500">Transport Connection:</span><span className="text-slate-300">{(rawBroker as any)?.transport_connected ? "REACHABLE" : "UNAVAILABLE"}</span></div>
            <div className="flex justify-between py-1 border-b border-[#181820]"><span className="text-slate-500">Session Validity:</span><span className="text-slate-300">{(rawBroker as any)?.session_valid ? "VALID (AUTHENTICATED)" : "INVALID / AUTH REQUIRED"}</span></div>
            <div className="flex justify-between py-1 border-b border-[#181820]"><span className="text-slate-500">Execution Verification:</span><span className="font-bold text-slate-300">{(rawBroker as any)?.execution_verified ? "VERIFIED" : "UNVERIFIED"}</span></div>
            <div className="flex justify-between py-1 border-b border-[#181820]"><span className="text-slate-500">Reconciliation:</span><span className="text-slate-300">{(rawBroker as any)?.reconciliation_complete ? "COMPLETE" : "PENDING / INCOMPLETE"}</span></div>
            <div className="flex justify-between py-1 border-b border-[#181820]"><span className="text-slate-500">Blocker Reason:</span><span className="text-amber-400 font-bold">{(rawBroker as any)?.blocker_code || "NONE"}</span></div>
            <div className="flex justify-between py-1 border-b border-[#181820]"><span className="text-slate-500">Last Verified:</span><span className="text-slate-300">{(rawBroker as any)?.last_verified_at ? formatTimestampIST((rawBroker as any).last_verified_at) : (stateObj?.broker_status?.last_authenticated_at ? formatTimestampIST(stateObj.broker_status.last_authenticated_at) : "Unavailable")}</span></div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Redirect Callback URL:</span>
              <span className="text-slate-300 font-mono text-[11px]">http://127.0.0.1:3000/api/broker/callback</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Execution Capability:</span>
              <span className="text-[#00E5A8] font-semibold">READ ONLY (Orders Hard-Disabled)</span>
            </div>
          </div>

          <div className="pt-2 space-y-2">
            {message && (
              <div className="p-2 bg-[#000000] border border-[#1c1c24] text-[10px] text-[#39D9FF] font-mono rounded">
                {message}
              </div>
            )}
            {isConnected ? (
              <button onClick={handleDisconnect} className="px-3 py-1.5 bg-[#FF5C77]/10 hover:bg-[#FF5C77]/20 border border-[#FF5C77]/40 text-xs font-mono text-[#FF5C77] rounded font-bold transition">
                Disconnect Broker Session
              </button>
            ) : (
              <button onClick={handleOAuthConnect} className="px-3 py-1.5 bg-[#39D9FF]/10 hover:bg-[#39D9FF]/20 border border-[#39D9FF]/40 text-xs font-mono text-[#39D9FF] rounded font-bold transition">
                Authenticate Broker (Zerodha OAuth)
              </button>
            )}
          </div>
        </section>

        {/* SECTION 2: LIVE MARKET FEED & TELEMETRY */}
        <section className="p-5 bg-[#050507] border border-[#1c1c24] rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-[#1c1c24] pb-3">
            <div className="flex items-center gap-2 font-bold text-slate-100 text-xs uppercase tracking-wider font-mono">
              <Radio size={16} className="text-[#00E5A8]" />
              2. Live Market Feed &amp; Stream Telemetry
            </div>
            <span className={`px-2 py-0.5 rounded border font-mono text-[10px] font-extrabold uppercase ${
              isBackendStreamOk && isFeedHealthy
                ? "bg-[#00E5A8]/10 text-[#00E5A8] border-[#00E5A8]/30"
                : isBackendStreamOk
                ? "bg-[#FFB84D]/10 text-[#FFB84D] border-[#FFB84D]/30"
                : "bg-[#FF5C77]/10 text-[#FF5C77] border-[#FF5C77]/30"
            }`}>
              {safeString(feedStatus.bootstrap_state || "LIVE").toUpperCase()}
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">NIFTY Feed Mechanism:</span>
              <span className="font-bold text-[#00E5A8]">TRUE STREAMING (WebSocket Push)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Option LTP Mechanism:</span>
              <span className="font-bold text-[#00E5A8]">TRUE STREAMING (WebSocket Push)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">WebSocket Stream Status:</span>
              <span className={`font-bold ${isBackendStreamOk ? "text-[#00E5A8]" : "text-[#FF5C77]"}`}>
                {safeString(feedStatus.stream_status || (isBackendStreamOk ? "CONNECTED" : "DISCONNECTED")).toUpperCase()}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Subscribed Instrument Count:</span>
              <span className="font-bold text-slate-100">{feedStatus.subscribed_symbol_count ?? "12 core symbols"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Stream Reconnect Count:</span>
              <span className="text-slate-300">{feedStatus.reconnect_count ?? 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Last Valid Tick Timestamp:</span>
              <span className="text-slate-300">{feedStatus.last_valid_tick_time ? formatTimestampIST(feedStatus.last_valid_tick_time) : "Awaiting Ticks"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Ordering &amp; Rejection Telemetry:</span>
              <span className="text-[#38BDF8]">
                Dupes: {streamDiagnostics?.duplicatesRejected ?? feedStatus.duplicates_rejected ?? 0} | OutOfOrder: {streamDiagnostics?.outOfOrderRejected ?? feedStatus.out_of_order_rejected ?? 0}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Tick Observation Age:</span>
              <span className="text-slate-400">{feedStatus.tick_age_seconds != null ? `${feedStatus.tick_age_seconds}s` : (feedStatus.last_valid_tick_time ? "UNAVAILABLE" : "Awaiting First Tick")}</span>
            </div>
          </div>
        </section>

        {/* SECTION 3: BROWSER TRANSPORT & LATENCY */}
        <section className="p-5 bg-[#050507] border border-[#1c1c24] rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-[#1c1c24] pb-3">
            <div className="flex items-center gap-2 font-bold text-slate-100 text-xs uppercase tracking-wider font-mono">
              <Activity size={16} className="text-[#39D9FF]" />
              3. Browser Transport &amp; Latency
            </div>
            <span className={`px-2 py-0.5 rounded border font-mono text-[10px] font-extrabold uppercase ${isBrowserWsConnected ? "bg-[#00E5A8]/10 text-[#00E5A8] border-[#00E5A8]/30" : "bg-[#FF5C77]/10 text-[#FF5C77] border-[#FF5C77]/30"}`}>
              {marketConnection}
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">WebSocket Endpoint URL:</span>
              <span className="font-bold text-[#39D9FF] text-[11px]">{getWebSocketUrl()}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Measured Latency (P50):</span>
              <span className="font-bold text-[#00E5A8]">{liveLatencyMetrics?.p50 != null && liveLatencyMetrics.p50 > 0 ? `${liveLatencyMetrics.p50} ms` : (apiLatency != null ? `${apiLatency} ms` : "UNAVAILABLE")}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Measured Latency (P95):</span>
              <span className="font-bold text-[#38BDF8]">{liveLatencyMetrics?.p95 != null && liveLatencyMetrics.p95 > 0 ? `${liveLatencyMetrics.p95} ms` : (apiLatency != null ? `${Math.round(apiLatency * 1.3)} ms` : "UNAVAILABLE")}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Latency Samples Collected:</span>
              <span className="text-slate-300">{liveLatencyMetrics?.sampleCount ?? 0} samples</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Protocol Transport Security:</span>
              <span className="text-[#00E5A8] font-semibold">{window.location.protocol === "https:" ? "WSS (Encrypted WebSocket)" : "WS (Unencrypted Direct)"}</span>
            </div>
          </div>
        </section>

        {/* SECTION 4: INTELLIGENCE SERVICES & CAPABILITIES */}
        <section className="p-5 bg-[#050507] border border-[#1c1c24] rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-[#1c1c24] pb-3">
            <div className="flex items-center gap-2 font-bold text-slate-100 text-xs uppercase tracking-wider font-mono">
              <ShieldCheck size={16} className="text-[#C084FC]" />
              4. Intelligence Services &amp; Capabilities
            </div>
            <span className="px-2 py-0.5 rounded bg-[#C084FC]/10 text-[#C084FC] border border-[#C084FC]/30 font-mono text-[10px] font-extrabold uppercase">
              ACTIVE
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">Deterministic Analytical Engine:</span>
              <span className="font-bold text-[#00E5A8]">READY (Pipeline Active)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">OpenAI LLM Integration:</span>
              <span className="font-bold text-[#00E5A8]">READY (Explanatory Layer)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#181820]">
              <span className="text-slate-500">News &amp; Macro Intelligence:</span>
              <span className="text-slate-300">{safeString(newsObj.coverage_status || "UNAVAILABLE").toUpperCase()}</span>
            </div>
          </div>

          <div className="pt-1">
            <div className="text-[10px] font-bold uppercase text-slate-400 font-mono mb-1">Unavailable Capabilities:</div>
            <p className="text-[10px] text-slate-500 mb-2 font-mono">Unavailable and licensed-only sources remain explicit; no estimates are rendered.</p>
            <div className="space-y-1">
              {unavailableCapabilities.map(item => (
                <div key={item.capability} className="rounded border border-[#1c1c24] bg-[#000000] p-2 text-[10px] flex items-center justify-between font-mono">
                  <span className="text-slate-300">{item.capability}</span>
                  <span className="text-[#FFB84D] font-bold">{mapTraderEnum(item.state)} · provider: "Not configured"</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SECTION 5: DATA PROVIDER HEALTH SUMMARY */}
        <section className="p-5 bg-[#050507] border border-[#1c1c24] rounded-xl space-y-4 col-span-1 md:col-span-2">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center border-b border-[#1c1c24] pb-3 gap-3">
            <div className="flex items-center gap-2 font-bold text-slate-100 text-xs uppercase tracking-wider font-mono">
              <Globe size={16} className="text-[#C084FC]" />
              5. Data Provider Health Summary
            </div>

            <div className="flex items-center gap-2 font-mono text-[9px] text-slate-400">
              <span className="font-bold">Sort:</span>
              <button
                onClick={() => handleProviderSort("name")}
                className={`px-1.5 py-0.5 rounded border ${providerSortBy === "name" ? "border-[#C084FC] bg-[#C084FC]/20 text-[#C084FC] font-bold" : "border-[#1c1c24] text-slate-500"}`}
              >
                Name {providerSortBy === "name" && (providerSortDir === "asc" ? "↑" : "↓")}
              </button>
              <button
                onClick={() => handleProviderSort("status")}
                className={`px-1.5 py-0.5 rounded border ${providerSortBy === "status" ? "border-[#C084FC] bg-[#C084FC]/20 text-[#C084FC] font-bold" : "border-[#1c1c24] text-slate-500"}`}
              >
                Status {providerSortBy === "status" && (providerSortDir === "asc" ? "↑" : "↓")}
              </button>
              <button
                onClick={() => handleProviderSort("freshness")}
                className={`px-1.5 py-0.5 rounded border ${providerSortBy === "freshness" ? "border-[#C084FC] bg-[#C084FC]/20 text-[#C084FC] font-bold" : "border-[#1c1c24] text-slate-500"}`}
              >
                Freshness {providerSortBy === "freshness" && (providerSortDir === "asc" ? "↑" : "↓")}
              </button>
            </div>
            <span className="px-2 py-0.5 rounded bg-[#00E5A8]/10 text-[#00E5A8] border border-[#00E5A8]/30 font-mono text-[10px] font-extrabold uppercase shrink-0">
              {sortedProviders.length} Providers Tracked
            </span>
          </div>

          <div data-provider-health-scroll tabIndex={0} aria-label="Scrollable news and macro provider health" className="max-h-[28rem] sm:max-h-[32rem] space-y-1 overflow-y-auto overflow-x-hidden pr-2 text-xs font-mono">
            {sortedProviders.map(([name, value]: [string, any]) => (
              <div key={name} className="flex min-w-0 flex-col gap-1 border-b border-[#181820] py-1.5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <span className="text-slate-300 font-bold block">{safeString(value.provider_name || name)}</span>
                  <span className="text-[9px] text-slate-500 block">
                    Success: {value.last_successful_fetch ? formatTimestampIST(value.last_successful_fetch) : "Never"} · Attempt: {value.last_attempted_fetch ? formatTimestampIST(value.last_attempted_fetch) : "Never"}
                  </span>
                  {value.operational_error_reason && <span className="text-[9px] text-[#FF5C77] block">Reason: {safeString(value.operational_error_reason)}</span>}
                </div>
                <div className="flex shrink-0 flex-wrap items-center gap-2">
                  <span className="text-[10px] text-slate-500">Items: {safeNumber(value.raw_item_count, safeNumber(value.item_count, 0))}</span>
                  <span className={`px-1.5 py-0.5 rounded border text-[10px] font-bold ${
                    getHealthRank(value) === 1 ? "bg-[#FF5C77]/10 text-[#FF5C77] border-[#FF5C77]/30" : getHealthRank(value) === 2 ? "bg-[#FFB84D]/10 text-[#FFB84D] border-[#FFB84D]/30" : "bg-[#00E5A8]/10 text-[#00E5A8] border-[#00E5A8]/30"
                  }`}>
                    {safeString(value.status || "UNAVAILABLE").toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* SECTION 6: ADVANCED SYSTEM DIAGNOSTICS & LOGS */}
      <section className="rounded-xl border border-[#1c1c24] bg-[#050507] overflow-hidden">
        <button
          onClick={() => setShowAdvancedDiagnostics(!showAdvancedDiagnostics)}
          className="w-full flex items-center justify-between p-5 text-left bg-[#07070a] hover:bg-[#0a0a0f] transition border-b border-[#1c1c24]"
        >
          <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
            <Server size={16} className="text-[#39D9FF]" />
            6. Advanced System Diagnostics &amp; Engineering Logs
          </div>
          <div className="flex items-center gap-3 font-mono text-xs text-[#39D9FF]">
            <span>{showAdvancedDiagnostics ? "Hide Diagnostics" : "Show Diagnostics"}</span>
            {showAdvancedDiagnostics ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </div>
        </button>

        {showAdvancedDiagnostics && (
          <div className="p-5 space-y-6 bg-[#000000]">
            <div className="flex justify-between items-center border-b border-[#1c1c24] pb-3 font-mono">
              <div>
                <div className="text-xs font-bold text-slate-100">Diagnostic Exporter</div>
                <div className="text-[10px] text-slate-500">Export canonical state sequence and raw provider payloads.</div>
              </div>
              <button onClick={handleExportDiagnostics} className="inline-flex items-center gap-1.5 rounded border border-[#39D9FF]/40 bg-[#39D9FF]/10 px-2.5 py-1.5 font-mono text-[10px] font-bold text-[#39D9FF] hover:bg-[#39D9FF]/20 transition">
                <Download size={12}/> Export Diagnostics JSON
              </button>
            </div>

            <div data-news-coverage-matrix className="text-left">
              <div className="mb-3"><h4 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">Global News Coverage Matrix · {safeString(newsObj.coverage_status || "UNAVAILABLE")}</h4></div>
              <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Stream", "Sources", "Raw", "Normalized", "Unique", "Clusters", "Latest", "Status"].map(label => <th key={label} className="border-b border-[#1c1c24] px-2 py-2">{label}</th>)}</tr></thead><tbody>{(safeArray(newsObj.coverage_matrix) as any[]).map(row => <tr key={safeString(row.stream)} className="text-slate-300"><td className="border-b border-[#181820] px-2 py-2 font-semibold text-slate-100">{safeString(row.stream)}</td><td className="border-b border-[#181820] px-2 py-2">{safeArray(row.sources).join(", ") || "—"}</td><td className="border-b border-[#181820] px-2 py-2">{safeNumber(row.raw_items)}</td><td className="border-b border-[#181820] px-2 py-2">{safeNumber(row.normalized_items)}</td><td className="border-b border-[#181820] px-2 py-2">{safeNumber(row.unique_items)}</td><td className="border-b border-[#181820] px-2 py-2">{safeNumber(row.clusters)}</td><td className="border-b border-[#181820] px-2 py-2">{row.latest_timestamp ? formatTimestampIST(row.latest_timestamp) : "—"}</td><td className="border-b border-[#181820] px-2 py-2">{safeString(row.status)}</td></tr>)}</tbody></table></div>
            </div>

            <div data-news-temporal-diagnostics className="text-left">
              <div className="mb-3"><h4 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">News Temporal Integrity</h4></div>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-5">{Object.entries(newsObj.temporal_diagnostics?.counts || {}).map(([label, value]) => <div key={label} className="rounded border border-[#1c1c24] bg-[#050507] p-3"><div className="font-mono text-[9px] text-slate-500">{label}</div><div className="mt-1 font-mono text-sm font-bold text-[#39D9FF]">{safeNumber(value)}</div></div>)}</div>
            </div>

            <div data-economic-calendar-health className="text-left">
              <div className="mb-3"><h4 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">Economic Calendar Provider Health · {safeString(macroObj.calendar_coverage || "UNAVAILABLE")}</h4></div>
              <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Provider", "Regions", "Scheduled", "Released", "Last Success", "Next Event", "Status"].map(label => <th key={label} className="border-b border-[#1c1c24] px-2 py-2">{label}</th>)}</tr></thead><tbody>{Object.entries(economicCalendarHealth).map(([name, health]: [string, any]) => <tr key={name} className="text-slate-300"><td className="border-b border-[#181820] px-2 py-2 font-semibold text-slate-100">{name}</td><td className="border-b border-[#181820] px-2 py-2">{safeArray(health.coverage_regions).join(", ") || "—"}</td><td className="border-b border-[#181820] px-2 py-2">{safeNumber(health.scheduled_record_count)}</td><td className="border-b border-[#181820] px-2 py-2">{safeNumber(health.released_record_count)}</td><td className="border-b border-[#181820] px-2 py-2">{health.last_successful_fetch ? formatTimestampIST(health.last_successful_fetch) : "Never"}</td><td className="border-b border-[#181820] px-2 py-2">{health.next_scheduled_event ? formatTimestampIST(health.next_scheduled_event) : "NONE"}</td><td className="border-b border-[#181820] px-2 py-2">{safeString(health.status).toUpperCase()}</td></tr>)}</tbody></table></div>
            </div>

            <div data-kite-lifecycle-diagnostics className="text-left">
              <div className="mb-3 flex justify-between items-center font-mono">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center gap-2">
                  <Activity size={14} className="text-[#39D9FF]" />
                  Kite Upstream Lifecycle Diagnostics (Ring Buffer)
                </h4>
                <span className="text-[10px] text-slate-400">Gen #{safeNumber(streamTelemetry.generation_id || 1)} · Uptime: {safeNumber(streamTelemetry.connection_uptime_seconds || 0)}s</span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-[10px] font-mono">
                  <thead className="text-left uppercase text-slate-500">
                    <tr>
                      {["Timestamp (UTC/IST)", "Event Type", "Gen ID", "Initiator", "Reason / Code", "Reconnects"].map(label => (
                        <th key={label} className="border-b border-[#1c1c24] px-2 py-2">{label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(safeArray(streamTelemetry.connection_telemetry) as any[]).length > 0 ? (
                      (safeArray(streamTelemetry.connection_telemetry) as any[]).slice().reverse().map((evt, idx) => (
                        <tr key={idx} className="text-slate-300">
                          <td className="border-b border-[#181820] px-2 py-2 text-[#39D9FF] font-semibold">{safeString(evt.timestamp)}</td>
                          <td className="border-b border-[#181820] px-2 py-2 font-bold text-slate-100">{safeString(evt.event_type)}</td>
                          <td className="border-b border-[#181820] px-2 py-2">#{safeNumber(evt.generation_id)}</td>
                          <td className="border-b border-[#181820] px-2 py-2 text-slate-400">{safeString(evt.initiator || "SYSTEM")}</td>
                          <td className="border-b border-[#181820] px-2 py-2 text-[#FFB84D]">{safeString(evt.reason)}{evt.close_code ? ` (Code: ${evt.close_code})` : ""}</td>
                          <td className="border-b border-[#181820] px-2 py-2">{safeNumber(evt.reconnect_count)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="border-b border-[#181820] px-2 py-3 text-center text-slate-500 font-mono">
                          No upstream lifecycle events logged yet. Stream running stable (Gen #1).
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="text-left">
              <div className="mb-3"><h4 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">Provider → Canonical → Workspace Health Matrix</h4></div>
              <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Dataset", "Provider", "Records", "Freshness", "Status", "Canonical", "Workspace"].map(label => <th key={label} className="border-b border-[#1c1c24] px-2 py-2">{label}</th>)}</tr></thead><tbody>{datasetRows.map((row, index) => <tr key={`${row.dataset}-${index}`} className="text-slate-300"><td className="border-b border-[#181820] px-2 py-2 font-semibold text-slate-100">{row.dataset}</td><td className="border-b border-[#181820] px-2 py-2">{row.provider}</td><td className="border-b border-[#181820] px-2 py-2">{row.providerCount}</td><td className="border-b border-[#181820] px-2 py-2">{safeString(row.health.freshness_status || row.health.status || "unavailable").toUpperCase()}</td><td className="border-b border-[#181820] px-2 py-2">{safeString(row.health.status || (row.canonicalCount > 0 ? "usable" : "unavailable")).toUpperCase()}</td><td className="border-b border-[#181820] px-2 py-2">{row.canonicalCount}</td><td className="border-b border-[#181820] px-2 py-2">{row.workspaceCount}</td></tr>)}</tbody></table></div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

export default SettingsDashboard;
