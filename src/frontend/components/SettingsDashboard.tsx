// src/frontend/components/SettingsDashboard.tsx
import React, { useState } from "react";
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

export function SettingsDashboard() {
  const { themeClasses, accentClasses } = useTheme();
  const {
    workspaceContext,
    brokerAccount,
    canonicalState,
    syncBroker,
    apiLatency,
    marketConnection,
    lastSyncTime
  } = useWorkstationState() as any;

  const { data: broker } = useBrokerStatus();
  const { data: market } = useMarketData();
  const { data: news } = useNewsIntelligence();

  const [message, setMessage] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

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

  const handleRefreshAll = async () => {
    if (refreshing) return;
    setRefreshing(true);
    setMessage("Syncing canonical workstation telemetry...");
    try {
      await syncBroker(true);
      setMessage("Workstation telemetry synchronized successfully.");
    } catch (err: any) {
      setMessage(`Refresh error: ${err.message}`);
    } finally {
      setRefreshing(false);
    }
  };

  const handleExportDiagnostics = () => {
    const diagnosticPayload = {
      timestamp: new Date().toISOString(),
      workspaceContext,
      brokerStatus: broker,
      marketData: market,
      dataQuality: canonicalState?.data_quality,
      newsTemporalDiagnostics: canonicalState?.news_intelligence?.temporal_diagnostics,
      schema_version: canonicalState?.schema_version || "2.0.0",
      runtime_id: canonicalState?.runtime_id || null
    };
    const blob = new Blob([JSON.stringify(diagnosticPayload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ardhamind_diagnostics_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const newsObj = canonicalState?.news_intelligence || {};
  const newsItems = Number(newsObj.items?.length || news?.items?.length || 0);
  const providerHealth = newsObj.provider_health || {};
  const macroObj = canonicalState?.macro_intelligence || {};
  const macroHealth = macroObj.provider_health || {};
  const globalHealth = macroHealth.global_market_provider || {};
  const flowHealth = macroHealth.institutional_flow_provider || {};
  const calendarHealth = macroHealth.corporate_calendar_provider || {};
  const economicCalendarHealth = macroObj.calendar_provider_health || {};
  const economicEvents = safeArray(macroObj.economic_events) as any[];
  const quotes = macroObj.quotes || {};
  const quoteStatus = macroObj.quote_status || {};
  const workspaceQuoteKeys = new Set(safeArray(macroObj.workspace_context?.current_context_quote_keys).map(String));
  const participantHealth = macroHealth.nse_participant_derivatives_provider?.dataset_health || {};
  const derivatives = macroObj.institutional_derivatives || {};
  const vix = macroObj.india_vix || canonicalState?.market_data?.india_vix_context || {};
  const rate = macroObj.risk_free_rate || {};
  const providerContracts = macroObj.provider_contracts || {};
  const datasetRows = [
    { dataset: "NIFTY historical candles", provider: "Kite Historical API", providerCount: Number(canonicalState?.market_data?.candles?.length || 0), canonicalCount: Number(canonicalState?.market_data?.candles?.length || 0), workspaceCount: Number(canonicalState?.market_data?.candles?.length || 0), health: canonicalState?.data_quality?.market_data || {} },
    ...[["GIFT Nifty", "GIFT_NIFTY"], ["S&P 500", "S&P 500"], ["Nasdaq", "NASDAQ"], ["Dow", "DOW_JONES"], ["Nikkei", "NIKKEI_225"], ["Hang Seng", "HANG_SENG"], ["Brent", "BRENT_CRUDE"], ["Gold", "GOLD"], ["USD/INR", "USD_INR"], ["DXY", "DXY"], ["US 10Y", "US_10Y"]].map(([dataset, symbol]) => { const quote = quotes[symbol]; const status = quoteStatus[symbol] || {}; return { dataset, provider: quote ? `${safeString(quote.source_name)} (${safeString(quote.source_symbol)})` : symbol === "GIFT_NIFTY" ? "No genuine provider configured" : "Yahoo Finance Public Feed", providerCount: quote ? 1 : 0, canonicalCount: quote ? 1 : 0, workspaceCount: workspaceQuoteKeys.has(symbol) ? 1 : 0, health: { ...globalHealth, status: safeString(status.status || "unavailable").toLowerCase(), operational_error_reason: status.reason || globalHealth.operational_error_reason, failure_detail: quote ? `Observed ${safeString(quote.observation_timestamp)}; freshness ${safeString(quote.freshness_status)}; source session ${safeString(quote.source_session)}` : status.reason || "No validated observation." } }; }),
    { dataset: "FII/DII", provider: "NSE fiidiiTradeReact", providerCount: safeNumber(flowHealth.item_count, 0), canonicalCount: Number(macroObj.institutional_flows?.length || 0), workspaceCount: Number(macroObj.institutional_flows?.length || 0), health: flowHealth },
    { dataset: "NSE participant Open Interest", provider: "NSE Clearing official archive", providerCount: safeNumber(participantHealth.OPEN_INTEREST?.record_count, 0), canonicalCount: safeArray(derivatives.open_interest?.records).length, workspaceCount: safeArray(derivatives.open_interest?.records).length, health: { status: participantHealth.OPEN_INTEREST?.status, last_successful_fetch: participantHealth.OPEN_INTEREST?.last_success, last_attempted_fetch: participantHealth.OPEN_INTEREST?.last_attempt, operational_error_reason: participantHealth.OPEN_INTEREST?.failure_reason, failure_detail: `Latest session ${safeString(participantHealth.OPEN_INTEREST?.latest_session)}; freshness ${safeString(participantHealth.OPEN_INTEREST?.freshness)}.` } },
    { dataset: "NSE participant Trading Volume", provider: "NSE Clearing official archive", providerCount: safeNumber(participantHealth.VOLUME?.record_count, 0), canonicalCount: safeArray(derivatives.volume?.records).length, workspaceCount: safeArray(derivatives.volume?.records).length, health: { status: participantHealth.VOLUME?.status, last_successful_fetch: participantHealth.VOLUME?.last_success, last_attempted_fetch: participantHealth.VOLUME?.last_attempt, operational_error_reason: participantHealth.VOLUME?.failure_reason, failure_detail: `Latest session ${safeString(participantHealth.VOLUME?.latest_session)}; freshness ${safeString(participantHealth.VOLUME?.freshness)}.` } },
    { dataset: "India VIX", provider: `${safeString(vix.source)} (${safeString(vix.source_symbol)})`, providerCount: vix.value != null ? 1 : 0, canonicalCount: vix.value != null ? 1 : 0, workspaceCount: vix.value != null ? 1 : 0, health: { status: safeString(vix.status).toLowerCase(), last_successful_fetch: vix.retrieved_at, last_attempted_fetch: vix.last_attempt || vix.retrieved_at, operational_error_reason: vix.failure_reason, failure_detail: `Observed ${safeString(vix.observation_timestamp)}; freshness ${safeString(vix.freshness)}; regime ${safeString(vix.regime)}.` } },
    { dataset: "INR risk-free rate", provider: `${safeString(rate.source)} (${safeString(rate.tenor)})`, providerCount: rate.rate != null ? 1 : 0, canonicalCount: rate.rate != null ? 1 : 0, workspaceCount: rate.rate != null ? 1 : 0, health: { status: safeString(rate.status).toLowerCase(), last_successful_fetch: rate.retrieved_at, last_attempted_fetch: rate.last_attempt || rate.retrieved_at, operational_error_reason: rate.failure_reason, failure_detail: `Observed ${safeString(rate.observation_date)}; freshness ${safeString(rate.freshness)}.` } },
    { dataset: "GIFT Nifty provider", provider: "GiftNiftyProvider", providerCount: 0, canonicalCount: 0, workspaceCount: 0, health: { status: safeString(providerContracts.gift_nifty?.status).toLowerCase(), operational_error_reason: providerContracts.gift_nifty?.failure_reason, failure_detail: "Disabled provider contract; no substitute requests are made." } },
    { dataset: "NIFTY weights provider", provider: "NiftyWeightsProvider", providerCount: 0, canonicalCount: 0, workspaceCount: 0, health: { status: safeString(providerContracts.nifty_weights?.status).toLowerCase(), operational_error_reason: providerContracts.nifty_weights?.failure_reason, failure_detail: "Official full weights require a licensed source; no estimates are rendered." } },
    ...Object.entries(economicCalendarHealth).map(([name, health]: [string, any]) => { const canonicalCount = economicEvents.filter(event => (safeArray(event.provider_provenance) as any[]).some(provenance => safeString(provenance.provider_id) === name)).length; return { dataset: `Economic calendar: ${name}`, provider: safeString(health.provider_name || name), providerCount: safeNumber(health.item_count, 0), canonicalCount, workspaceCount: canonicalCount, health }; }),
    { dataset: "Corporate actions", provider: "NSE Corporate Actions", providerCount: safeNumber(calendarHealth.item_count, 0), canonicalCount: Number(macroObj.corporate_actions?.length || 0), workspaceCount: Number(macroObj.corporate_actions?.length || 0), health: calendarHealth },
    { dataset: "Earnings calendar", provider: "Not configured", providerCount: 0, canonicalCount: Number(macroObj.earnings_events?.length || 0), workspaceCount: Number(macroObj.earnings_events?.length || 0), health: { status: "unavailable", operational_error_reason: "provider_not_configured", failure_detail: "No real earnings-calendar provider is configured." } },
    { dataset: "IPO calendar", provider: "Not configured", providerCount: 0, canonicalCount: Number(macroObj.ipo_events?.length || 0), workspaceCount: Number(macroObj.ipo_events?.length || 0), health: { status: "unavailable", operational_error_reason: "provider_not_configured", failure_detail: "No real IPO-calendar provider is configured." } },
    ...(safeArray(macroObj.dataset_health) as any[]).map(row => ({ dataset: `Official India: ${safeString(row.dataset)}`, provider: safeString(row.provider), providerCount: safeNumber(row.provider_count, 0), canonicalCount: safeNumber(row.canonical_count, 0), workspaceCount: safeNumber(row.canonical_count, 0), health: { status: row.status, last_successful_fetch: row.last_successful_fetch, last_attempted_fetch: row.last_attempted_fetch, operational_error_reason: row.failure_reason, failure_detail: row.failure_detail } })),
    ...Object.entries(providerHealth).map(([name, health]: [string, any]) => ({ dataset: `News: ${name}`, provider: safeString(health.provider_name || name), providerCount: safeNumber(health.item_count, 0), canonicalCount: (safeArray(newsObj.items) as any[]).filter(item => safeString(item.provider_id || item.discovered_via) === name).length, workspaceCount: (safeArray(newsObj.items) as any[]).filter(item => safeString(item.provider_id || item.discovered_via) === name).length, health })),
  ];

  return (
    <div id="settings-dashboard" className="space-y-6 text-left font-sans">

      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
        <div>
          <h3 className="font-extrabold text-white text-sm uppercase tracking-wider font-mono">
            System Operations & Canonical Diagnostics
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Monitor real-time gateway health, broker session parameters, and data provider states.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefreshAll}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-cyan-300 rounded font-semibold transition"
          >
            <RefreshCw size={13} className={refreshing ? "animate-spin" : ""} />
            Refresh Telemetry
          </button>
          <button
            onClick={handleExportDiagnostics}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-white rounded font-semibold transition"
          >
            <Download size={13} />
            Export Diagnostics
          </button>
        </div>
      </div>

      {message && (
        <div className="p-3 bg-cyan-950/40 border border-cyan-800/60 rounded-lg text-xs font-mono text-cyan-300 flex items-center gap-2">
          <ShieldCheck size={15} />
          <span>{message}</span>
        </div>
      )}

      {/* Grid Architecture */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* SECTION 1: BROKER CONNECTION */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <KeyRound size={16} className="text-cyan-400" />
              1. Broker Gateway Connection
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
              <span className="font-bold text-cyan-400">{brokerAccount?.client_id && brokerAccount.client_id !== "N/A" ? brokerAccount.client_id : "Unavailable — profile fetch failed"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900"><span className="text-slate-500">Session Validity:</span><span className="text-slate-300">{isConnected ? (canonicalState?.broker_status?.session_valid === false ? "INVALID" : "CONNECTED (PROFILE VALIDATED)") : "INVALID / DISCONNECTED"}</span></div>
            <div className="flex justify-between py-1 border-b border-slate-900"><span className="text-slate-500">Last Authenticated:</span><span className="text-slate-300">{canonicalState?.broker_status?.last_authenticated_at ? formatDate(canonicalState.broker_status.last_authenticated_at) : "Unavailable"}</span></div>
            <div className="flex justify-between py-1 border-b border-slate-900"><span className="text-slate-500">Last Profile Validation:</span><span className="text-slate-300">{canonicalState?.broker_status?.last_profile_validation ? formatDate(canonicalState.broker_status.last_profile_validation) : "Unavailable"}</span></div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Redirect Callback URL:</span>
              <span className="text-slate-300 font-mono text-[11px]">http://127.0.0.1:3000/api/broker/callback</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Execution Capability:</span>
              <span className="text-emerald-400 font-semibold">READ ONLY (Orders Hard-Disabled)</span>
            </div>
          </div>

          <div className="pt-2">
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
              <span className="text-slate-400">{formatDate(canonicalState?.generated_at)}</span>
            </div>
          </div>
        </section>

        {/* SECTION 3: NEWS INTELLIGENCE PROVIDERS */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <Globe size={16} className="text-purple-400" />
              3. News & Macro Provider Health
            </div>
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono text-[10px] font-extrabold uppercase">
              {safeString(newsObj.coverage_status || "UNAVAILABLE").toUpperCase()} ({newsItems} items)
            </span>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            {Object.entries({ ...providerHealth, ...macroHealth }).map(([name, value]: [string, any]) => (
              <div key={name} className="flex justify-between items-center py-1 border-b border-slate-900">
                <div><span className="text-slate-300 font-bold block">{safeString(value.provider_name || name)}</span><span className="text-[9px] text-slate-500 block">Success: {value.last_successful_fetch ? formatDate(value.last_successful_fetch) : "Never"} · Attempt: {value.last_attempted_fetch ? formatDate(value.last_attempted_fetch) : "Never"}</span>{value.operational_error_reason && <span className="text-[9px] text-rose-400 block">Reason: {safeString(value.operational_error_reason)}</span>}</div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500" title={`Raw ${safeNumber(value.raw_item_count)} · Normalized ${safeNumber(value.normalized_item_count)} · Unique ${safeNumber(value.unique_item_count)} · Clusters ${safeNumber(value.event_cluster_count)} · Streams ${safeArray(value.discovery_streams).join(", ") || "N/A"} · Rate ${safeString(value.rate_limit_state || "N/A")}`}>R {safeNumber(value.raw_item_count, safeNumber(value.item_count, 0))} · N {safeNumber(value.normalized_item_count)} · U {safeNumber(value.unique_item_count)} · C {safeNumber(value.event_cluster_count)} · {safeString(value.rate_limit_state || "N/A")}</span>
                  <span className="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] font-bold">
                    {safeString(value.status || "UNAVAILABLE").toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* SECTION 4: DIAGNOSTICS & SYSTEM INFO */}
        <section className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider font-mono">
              <Server size={16} className="text-cyan-400" />
              4. Diagnostics & System Telemetry
            </div>
            <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono text-[10px] font-extrabold uppercase">
              HEALTHY
            </span>
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
        <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Stream", "Sources", "Raw", "Normalized", "Unique", "Clusters", "Latest", "Status"].map(label => <th key={label} className="border-b border-slate-800 px-2 py-2">{label}</th>)}</tr></thead><tbody>{(safeArray(newsObj.coverage_matrix) as any[]).map(row => <tr key={safeString(row.stream)} className="text-slate-300"><td className="border-b border-slate-900 px-2 py-2 font-semibold text-white">{safeString(row.stream)}</td><td className="border-b border-slate-900 px-2 py-2">{safeArray(row.sources).join(", ") || "—"}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.raw_items)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.normalized_items)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.unique_items)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(row.clusters)}</td><td className="border-b border-slate-900 px-2 py-2">{row.latest_timestamp ? formatDate(row.latest_timestamp) : "—"}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(row.status)}</td></tr>)}</tbody></table></div>
      </section>

      <section data-news-temporal-diagnostics className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-left">
        <div className="mb-4"><h3 className="font-mono text-xs font-bold uppercase tracking-wider text-white">News Temporal Integrity</h3><p className="mt-1 text-[10px] text-slate-500">Publication-time eligibility is recomputed independently of fetch and cache timestamps.</p></div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">{Object.entries(newsObj.temporal_diagnostics?.counts || {}).map(([label, value]) => <div key={label} className="rounded border border-slate-800 bg-slate-950 p-3"><div className="font-mono text-[9px] text-slate-500">{label}</div><div className="mt-1 font-mono text-sm font-bold text-cyan-300">{safeNumber(value)}</div></div>)}</div>
        <div className="mt-4 grid gap-2 text-[10px] font-mono text-slate-400 md:grid-cols-3"><span>Window: {safeNumber(newsObj.current_window_hours)}h</span><span>Oldest current: {newsObj.temporal_diagnostics?.oldest_current_timestamp ? formatDate(newsObj.temporal_diagnostics.oldest_current_timestamp) : "NONE"}</span><span>Newest current: {newsObj.temporal_diagnostics?.newest_current_timestamp ? formatDate(newsObj.temporal_diagnostics.newest_current_timestamp) : "NONE"}</span></div>
      </section>

      <section data-economic-calendar-health className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-left">
        <div className="mb-4"><h3 className="font-mono text-xs font-bold uppercase tracking-wider text-white">Economic Calendar Provider Health · {safeString(macroObj.calendar_coverage || "UNAVAILABLE")}</h3><p className="mt-1 text-[10px] text-slate-500">READY requires at least one usable NIFTY-relevant record with an exact timezone-aware schedule.</p></div>
        <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Provider", "Regions", "Scheduled", "Released", "Last Success", "Next Event", "Rate Limit", "Status", "Failure"].map(label => <th key={label} className="border-b border-slate-800 px-2 py-2">{label}</th>)}</tr></thead><tbody>{Object.entries(economicCalendarHealth).map(([name, health]: [string, any]) => <tr key={name} className="text-slate-300"><td className="border-b border-slate-900 px-2 py-2 font-semibold text-white">{name}</td><td className="border-b border-slate-900 px-2 py-2">{safeArray(health.coverage_regions).join(", ") || "—"}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(health.scheduled_record_count)}</td><td className="border-b border-slate-900 px-2 py-2">{safeNumber(health.released_record_count)}</td><td className="border-b border-slate-900 px-2 py-2">{health.last_successful_fetch ? formatDate(health.last_successful_fetch) : "Never"}</td><td className="border-b border-slate-900 px-2 py-2">{health.next_scheduled_event ? formatDate(health.next_scheduled_event) : "NONE"}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(health.rate_limit_state || "UNAVAILABLE")}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(health.status).toUpperCase()}</td><td className="max-w-xs border-b border-slate-900 px-2 py-2 text-rose-300">{safeString(health.failure_detail || health.operational_error_reason || "—")}</td></tr>)}</tbody></table></div>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-left">
        <div className="mb-4"><h3 className="font-mono text-xs font-bold uppercase tracking-wider text-white">5. Provider → Canonical → Workspace Health Matrix</h3><p className="mt-1 text-[10px] text-slate-500">A provider is usable only when valid records survive into the canonical state and the target workspace.</p></div>
        <div className="overflow-x-auto"><table className="min-w-full text-[10px] font-mono"><thead className="text-left uppercase text-slate-500"><tr>{["Dataset", "Provider", "Records", "Last Success", "Last Attempt", "Freshness", "Status", "Failure Reason", "Canonical", "Workspace"].map(label => <th key={label} className="border-b border-slate-800 px-2 py-2">{label}</th>)}</tr></thead><tbody>{datasetRows.map((row, index) => <tr key={`${row.dataset}-${index}`} className="text-slate-300"><td className="border-b border-slate-900 px-2 py-2 font-semibold text-white">{row.dataset}</td><td className="border-b border-slate-900 px-2 py-2">{row.provider}</td><td className="border-b border-slate-900 px-2 py-2">{row.providerCount}</td><td className="border-b border-slate-900 px-2 py-2">{row.health.last_successful_fetch ? formatDate(row.health.last_successful_fetch) : "Never"}</td><td className="border-b border-slate-900 px-2 py-2">{row.health.last_attempted_fetch ? formatDate(row.health.last_attempted_fetch) : "Never"}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(row.health.freshness_status || row.health.status || "unavailable").toUpperCase()}</td><td className="border-b border-slate-900 px-2 py-2">{safeString(row.health.status || (row.canonicalCount > 0 ? "usable" : "unavailable")).toUpperCase()}</td><td className="max-w-xs border-b border-slate-900 px-2 py-2 text-rose-300">{safeString(row.health.failure_detail || row.health.operational_error_reason || "—")}</td><td className="border-b border-slate-900 px-2 py-2">{row.canonicalCount}</td><td className="border-b border-slate-900 px-2 py-2">{row.workspaceCount}</td></tr>)}</tbody></table></div>
      </section>
    </div>
  );
}

export default SettingsDashboard;
