// src/frontend/components/BrokerIntegration.tsx
import React, { useEffect, useState } from "react";
import {
  connectBroker,
  getBrokerConfig,
} from "../services/broker";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { WorkspaceMode } from "../services/workspace";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";
import {
  AlertCircle,
  Landmark,
  ShieldCheck,
  Key,
  RefreshCw,
  Activity,
  Clock,
  Unlock,
  LogOut,
  CheckCircle2,
  AlertTriangle,
  Sliders,
  Settings,
  Terminal,
  Cpu,
  RefreshCcw,
  Lock,
  User,
  Zap,
  Check,
  HelpCircle,
  Info,
  Layers,
  XCircle,
  FileText,
  TrendingUp,
  UserCheck,
  ShieldAlert
} from "lucide-react";

export function BrokerIntegration() {
  const {
    workspaceMode,
    brokerAccount: account,
    brokerFunds: funds,
    portfolioReport: report,
    loading,
    syncing,
    error,
    lastSyncTime,
    apiLatency,
    allowLiveTrading: allowLiveTradingSession,
    setWorkspaceMode,
    syncBroker,
    logoutBroker,
    setAllowLiveTrading,
    setError
  } = useWorkstationState();

  // Connection Manager States
  const [apiKey, setApiKey] = useState<string>("");
  const [accessToken, setAccessToken] = useState<string>("");
  const [persistKey, setPersistKey] = useState<boolean>(true);
  const [persistToken, setPersistToken] = useState<boolean>(false);
  const [loginMessage, setLoginMessage] = useState<string>("");
  const [showToken, setShowToken] = useState<boolean>(false);
  
  // Transition safety modals
  const [showLiveModal, setShowLiveModal] = useState<boolean>(false);
  const [showPracticeModal, setShowPracticeModal] = useState<boolean>(false);

  // Load saved configuration on startup
  useEffect(() => {
    async function loadConfig() {
      try {
        const config = await getBrokerConfig();
        if (config.api_key) {
          setApiKey(config.api_key);
        }
        setPersistToken(config.access_token_saved);
      } catch (err: any) {
        console.error("Failed to load broker config:", err);
      }
    }
    loadConfig();
  }, []);

  const brokerHealth = report?.broker_health;
  const isSessionValid = brokerHealth?.session_valid ?? false;
  const isConnected = brokerHealth?.connection_status === "CONNECTED";
  const isProfileLoaded = account && account.client_id !== "N/A" && account.client_id !== "";
  const areFundsLoaded = funds && funds.available_cash > 0;

  const handleConnect = async () => {
    if (!apiKey.trim()) {
      setError("API Key is required to connect.");
      return;
    }
    if (!accessToken.trim()) {
      setError("Access Token is required to connect.");
      return;
    }

    setLoginMessage("Connecting to Zerodha Kite gateways...");
    setError(null);
    try {
      const res = await connectBroker(
        apiKey.trim(),
        accessToken.trim(),
        persistKey,
        persistToken
      );
      if (res.error) {
        setError(res.error);
        setLoginMessage("");
      } else {
        // [V1.3.1 FIX] Do NOT call syncBroker(true) here.
        // syncBroker was fetching GET /api/workspace which returned stale DISCONNECTED state.
        // The server now broadcasts an auth_event via WebSocket immediately after login.
        // WorkstationStateContext handles it → entire workstation updates in <100ms automatically.
        setLoginMessage("Connected. Dashboard updating...");
        setAccessToken("");
      }
    } catch (err: any) {
      setError(err.message || "Failed to establish connection.");
      setLoginMessage("");
    }
  };

  const handleDisconnect = async () => {
    setLoginMessage("Disconnecting from Zerodha...");
    setError(null);
    try {
      await logoutBroker();
      setLoginMessage("Session disconnected successfully.");
    } catch (err: any) {
      setError(err.message || "Disconnect failed.");
    }
  };

  const handleValidateSession = async () => {
    setLoginMessage("Validating active KiteConnect session...");
    setError(null);
    try {
      await syncBroker(true);
      if (isSessionValid) {
        setLoginMessage("Kite session is valid and active.");
      } else {
        setError("Kite session is invalid or expired.");
        setLoginMessage("");
      }
    } catch (err: any) {
      setError(err.message || "Session validation failed.");
      setLoginMessage("");
    }
  };

  const triggerGlobalSync = async () => {
    await syncBroker(true);
    window.dispatchEvent(new CustomEvent("broker-sync"));
  };

  const handleModeChange = async (newMode: WorkspaceMode) => {
    setError(null);
    const res = await setWorkspaceMode(newMode);
    if (!res.success) {
      setError(res.error || `Transition to ${newMode} blocked by safety guard.`);
    }
  };

  const handleModeCardClick = (newMode: WorkspaceMode) => {
    if (newMode === "LIVE_TRADING") {
      setShowLiveModal(true);
    } else {
      handleModeChange("LIVE_PRACTICE");
    }
  };

  const handleRuntimeToggle = async (enabled: boolean) => {
    await setAllowLiveTrading(enabled);
    setLoginMessage(enabled ? "Live Execution Gateway Authorized." : "Live Execution Gateway Blocked.");
  };

  return (
    <div id="broker-integration" className="space-y-6 max-w-6xl mx-auto py-2 px-1">
      {/* Header & Quick Status Banner */}
      <div id="connection-header" className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-900 pb-5">
        <div className="text-left space-y-1">
          <div className="flex items-center gap-2">
            <Sliders size={20} className="text-cyan-400" />
            <h1 className="text-lg font-bold text-white tracking-tight">KiteConnect Broker Gateway</h1>
          </div>
          <p className="text-xs text-slate-400">
            Configure direct access tokens, inspect telemetry state, and authorize order execution parameters.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {lastSyncTime && (
            <div className="hidden sm:flex flex-col items-end text-right font-mono text-[10px] text-slate-500">
              <span>Synced: {lastSyncTime}</span>
              <span>Latency: {apiLatency ? `${apiLatency}ms` : "0ms (Local)"}</span>
            </div>
          )}
          
          <button
            id="sync-broker-btn"
            onClick={triggerGlobalSync}
            disabled={syncing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 hover:bg-slate-850 text-slate-300 hover:text-white font-semibold text-xs font-mono transition-all duration-150 disabled:opacity-50"
          >
            <RefreshCw size={13} className={syncing ? "animate-spin text-cyan-400" : "text-slate-400"} />
            Sync Gateway
          </button>
        </div>
      </div>

      {/* Global Error Alert */}
      {error && (
        <div id="global-error-alert" className="p-4 bg-rose-950/15 border border-rose-900/40 rounded-xl flex items-start gap-3 text-left animate-in fade-in duration-200">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">Gateway Synchronization Exception</h4>
            <p className="text-[11px] text-rose-300 leading-normal font-mono">{error}</p>
          </div>
        </div>
      )}

      {/* Workspace Operating Mode Selection */}
      <div id="mode-selector-section" className="space-y-3">
        <h2 className="text-xs font-black tracking-widest text-slate-400 uppercase text-left">
          Select Active Workspace Mode
        </h2>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Practice Portfolio Card */}
          <div
            id="mode-paper-trading-card"
            onClick={() => handleModeCardClick("LIVE_PRACTICE")}
            className={`relative p-4 rounded-xl border text-left cursor-pointer transition-all duration-200 flex flex-col justify-between h-40 hover:-translate-y-0.5 ${
              workspaceMode === "LIVE_PRACTICE"
                ? "bg-slate-900/80 border-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.1)]"
                : "bg-slate-950/40 border-slate-900 hover:border-slate-800"
            }`}
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`px-2 py-0.5 text-[9px] font-mono font-black rounded ${
                  workspaceMode === "LIVE_PRACTICE" ? "bg-amber-950/60 text-amber-400 border border-amber-900/40" : "bg-slate-900 text-slate-500"
                }`}>
                  LIVE_DATA_PAPER
                </span>
                <Clock size={16} className={workspaceMode === "LIVE_PRACTICE" ? "text-amber-400" : "text-slate-600"} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-white">Practice Mode</h3>
                <p className="text-[11px] text-slate-400 mt-1 leading-normal">
                  Stream real-time exchange quotes and portfolio balances but match order executions locally against virtual ledger.
                </p>
              </div>
            </div>
            <div className="border-t border-slate-900/60 pt-2.5 flex items-center justify-between font-mono text-[9px] text-slate-500">
              <span>Feed: Real-time NSE</span>
              <span>Exec: Paper Ledger</span>
            </div>
          </div>

          {/* Live Production Card */}
          <div
            id="mode-live-trading-card"
            onClick={() => handleModeCardClick("LIVE_TRADING")}
            className={`relative p-4 rounded-xl border text-left cursor-pointer transition-all duration-200 flex flex-col justify-between h-40 hover:-translate-y-0.5 ${
              workspaceMode === "LIVE_TRADING"
                ? "bg-red-950/10 border-rose-500/50 shadow-[0_0_20px_rgba(239,68,68,0.1)]"
                : "bg-slate-950/40 border-slate-900 hover:border-slate-800"
            }`}
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`px-2 py-0.5 text-[9px] font-mono font-black rounded ${
                  workspaceMode === "LIVE_TRADING" ? "bg-rose-950/60 text-rose-400 border border-rose-900/40" : "bg-slate-900 text-slate-500"
                }`}>
                  LIVE_EXECUTION
                </span>
                <Zap size={16} className={workspaceMode === "LIVE_TRADING" ? "text-rose-400 animate-pulse" : "text-slate-600"} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-white">Live Production Terminal</h3>
                <p className="text-[11px] text-slate-400 mt-1 leading-normal">
                  Route order execution packets directly to Zerodha Kite gateways. Places real-market trade orders with actual capital.
                </p>
              </div>
            </div>
            <div className="border-t border-slate-900/60 pt-2.5 flex items-center justify-between font-mono text-[9px] text-slate-500">
              <span>Feed: Real-time NSE</span>
              <span>Exec: Kite Gateway</span>
            </div>
          </div>
        </div>
      </div>

      {/* Connection Layout Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* SECTION 1: Broker Credentials */}
        <div id="section-credentials" className="lg:col-span-7 p-5 bg-slate-950 rounded-xl border border-slate-900 text-left space-y-4">
          <div className="border-b border-slate-900 pb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Key size={15} className="text-cyan-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">Section 1: Broker Credentials</h3>
            </div>
            <span className="text-[9px] font-mono bg-slate-900 text-slate-400 px-2 py-0.5 rounded uppercase">
              Connection Settings
            </span>
          </div>

          <div className="space-y-4 pt-1">
            <div className="space-y-1">
              <label htmlFor="kite-api-key-input" className="text-[10px] text-slate-500 font-mono block uppercase">Kite API Key</label>
              <input
                id="kite-api-key-input"
                type="text"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your Zerodha Kite API Key"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-white text-xs font-mono focus:border-cyan-500/50 focus:outline-none transition-colors"
              />
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label htmlFor="kite-access-token-input" className="text-[10px] text-slate-500 font-mono block uppercase">Kite Access Token</label>
                <button
                  id="toggle-token-visibility-btn"
                  onClick={() => setShowToken(!showToken)}
                  className="text-[9px] font-mono text-cyan-500 hover:text-cyan-400"
                >
                  {showToken ? "HIDE" : "SHOW"}
                </button>
              </div>
              <input
                id="kite-access-token-input"
                type={showToken ? "text" : "password"}
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                placeholder="Paste your active access token here"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-white text-xs font-mono focus:border-cyan-500/50 focus:outline-none transition-colors"
              />
            </div>

            {/* Persistence Opt-Ins */}
            <div id="persistence-checkboxes" className="grid grid-cols-2 gap-4 pt-1">
              <label htmlFor="persist-key-checkbox" className="flex items-start gap-2 cursor-pointer select-none">
                <input
                  id="persist-key-checkbox"
                  type="checkbox"
                  checked={persistKey}
                  onChange={(e) => setPersistKey(e.target.checked)}
                  className="mt-1 rounded bg-slate-900 border-slate-800 text-cyan-600 focus:ring-cyan-500/50 focus:ring-offset-slate-950 h-3.5 w-3.5"
                />
                <div className="space-y-0.5">
                  <span className="text-xs font-medium text-white block">Persist API Key</span>
                  <span className="text-[9px] text-slate-500 block leading-tight">Saves the API Key across browser sessions.</span>
                </div>
              </label>

              <label htmlFor="persist-token-checkbox" className="flex items-start gap-2 cursor-pointer select-none">
                <input
                  id="persist-token-checkbox"
                  type="checkbox"
                  checked={persistToken}
                  onChange={(e) => setPersistToken(e.target.checked)}
                  className="mt-1 rounded bg-slate-900 border-slate-800 text-cyan-600 focus:ring-cyan-500/50 focus:ring-offset-slate-950 h-3.5 w-3.5"
                />
                <div className="space-y-0.5">
                  <span className="text-xs font-medium text-white block">Persist Access Token</span>
                  <span className="text-[9px] text-slate-500 block leading-tight">Keep session active for 24 hours (Optional).</span>
                </div>
              </label>
            </div>

            {/* Action Buttons */}
            <div id="credentials-actions" className="flex flex-wrap items-center gap-3 pt-3 border-t border-slate-900">
              <button
                id="connect-broker-btn"
                onClick={handleConnect}
                disabled={syncing || !apiKey.trim() || !accessToken.trim()}
                className="flex-1 min-w-[120px] flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-mono transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <CheckCircle2 size={13} />
                Connect Broker
              </button>

              <button
                id="validate-session-btn"
                onClick={handleValidateSession}
                disabled={syncing || !isSessionValid}
                className="flex-1 min-w-[120px] flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-bold rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 font-mono transition-all disabled:opacity-40"
              >
                <Activity size={13} className="text-cyan-400" />
                Validate Session
              </button>

              <button
                id="disconnect-broker-btn"
                onClick={handleDisconnect}
                disabled={syncing || !isSessionValid}
                className="flex-1 min-w-[120px] flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-bold rounded-lg bg-rose-950/20 hover:bg-rose-950/40 border border-rose-900/40 text-rose-300 hover:text-rose-200 font-mono transition-all disabled:opacity-40"
              >
                <LogOut size={13} />
                Disconnect Broker
              </button>
            </div>

            {/* Live Trading Authorization Stopgap */}
            {workspaceMode === "LIVE_TRADING" && (
              <div id="live-order-safety-section" className="flex items-center justify-between p-3 rounded-lg border border-slate-900 bg-slate-900/20 pt-2">
                <div>
                  <div className="text-xs font-mono text-white font-bold uppercase flex items-center gap-1.5">
                    <ShieldAlert size={13} className="text-rose-400" />
                    Authorize Live Orders
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Toggle runtime permission to dispatch genuine order packets to NSE/BSE</div>
                </div>
                
                <button
                  id="runtime-trading-toggle-btn"
                  type="button"
                  onClick={() => handleRuntimeToggle(!allowLiveTradingSession)}
                  className={`px-3 py-1.5 rounded text-[10px] font-bold font-mono border transition-all ${
                    allowLiveTradingSession
                      ? "bg-emerald-950/40 text-emerald-400 border-emerald-900/50"
                      : "bg-slate-900 text-slate-400 border-slate-800"
                  }`}
                >
                  {allowLiveTradingSession ? "LIVE_ENABLED" : "LIVE_BLOCKED"}
                </button>
              </div>
            )}

            {loginMessage && (
              <div id="login-status-message" className="p-3 bg-slate-900 border border-slate-850 rounded-lg text-[11px] font-mono text-slate-300">
                {loginMessage}
              </div>
            )}
          </div>
        </div>

        {/* SECTION 2: Connection Status */}
        <div id="section-connection-status" className="lg:col-span-5 p-5 bg-slate-950 rounded-xl border border-slate-900 text-left space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="border-b border-slate-900 pb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity size={15} className="text-emerald-400" />
                <h3 className="font-bold text-white text-xs uppercase tracking-wider">Section 2: Connection Status</h3>
              </div>
              <span className="text-[9px] font-mono bg-slate-900 text-slate-400 px-2 py-0.5 rounded uppercase">
                Telemetry
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs pt-1">
              <div className="flex justify-between items-center border-b border-slate-900 pb-2">
                <span className="text-slate-500 uppercase text-[9px]">Gateway Link:</span>
                <div className="flex items-center gap-1.5">
                  <span className={`inline-block h-2 w-2 rounded-full ${
                    isConnected ? "bg-emerald-500 animate-pulse" : "bg-slate-600"
                  }`} />
                  <span className={`font-bold uppercase text-[10px] ${
                    isConnected ? "text-emerald-400" : "text-slate-500"
                  }`}>
                    {isConnected ? "CONNECTED" : "DISCONNECTED"}
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center border-b border-slate-900 pb-2">
                <span className="text-slate-500 uppercase text-[9px]">Authentication Status:</span>
                <span className={`font-semibold text-[10px] ${
                  isSessionValid ? "text-emerald-400" : "text-amber-500"
                }`}>
                  {isSessionValid ? "AUTHORIZED" : "UNAUTHORIZED"}
                </span>
              </div>

              <div className="flex justify-between items-center border-b border-slate-900 pb-2">
                <span className="text-slate-500 uppercase text-[9px]">Token Validity:</span>
                <span className={`font-semibold text-[10px] ${
                  isSessionValid ? "text-emerald-400" : "text-rose-400"
                }`}>
                  {isSessionValid ? "VALID_SESSION" : "EXPIRED_OR_MISSING"}
                </span>
              </div>

              <div className="flex justify-between items-center border-b border-slate-900 pb-2">
                <span className="text-slate-500 uppercase text-[9px]">Gateway Latency:</span>
                <span className="text-white text-[10px] font-bold">
                  {apiLatency ? `${apiLatency} ms` : "0 ms (Sim)"}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-500 uppercase text-[9px]">Last State Sync:</span>
                <span className="text-slate-300 text-[10px] font-semibold">
                  {lastSyncTime || "NEVER"}
                </span>
              </div>
            </div>
          </div>

          <div id="status-card-footer" className="p-3 bg-slate-900/30 border border-slate-900 rounded-lg mt-4">
            <div className="flex items-start gap-2 text-[10px] text-slate-400 leading-normal">
              <Info size={14} className="text-cyan-400 shrink-0 mt-0.5" />
              <span>
                {workspaceMode === "LIVE_TRADING"
                  ? "Gateway is operating in Live Execution mode. Real trades are directed to Zerodha exchange gates."
                  : "Gateway is in simulation mode. Accounts operate on local virtual ledgers."}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid for Section 3 & Section 4 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* SECTION 3: Authenticated Profile */}
        <div id="section-profile" className="p-5 bg-slate-950 rounded-xl border border-slate-900 text-left space-y-4">
          <div className="border-b border-slate-900 pb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <User size={15} className="text-cyan-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">Section 3: Authenticated Profile</h3>
            </div>
            <span className="text-[9px] font-mono bg-slate-900 text-slate-400 px-2 py-0.5 rounded uppercase">
              Operator
            </span>
          </div>

          {isProfileLoaded ? (
            <div className="space-y-3 font-mono text-xs pt-1">
              <div className="flex justify-between border-b border-slate-900 pb-2">
                <span className="text-slate-500 uppercase text-[9px]">Operator Name:</span>
                <span className="text-white font-bold">{safeString(account?.name)}</span>
              </div>
              <div className="flex justify-between border-b border-slate-900 pb-2">
                <span className="text-slate-500 uppercase text-[9px]">Client ID:</span>
                <span className="text-white font-semibold">{safeString(account?.client_id)}</span>
              </div>
              <div className="flex justify-between border-b border-slate-900 pb-2">
                <span className="text-slate-500 uppercase text-[9px]">Email Address:</span>
                <span className="text-white font-semibold">{safeString(account?.email)}</span>
              </div>
              <div className="flex justify-between border-b border-slate-900 pb-2">
                <span className="text-slate-500 uppercase text-[9px]">Broker Identity:</span>
                <span className="text-cyan-400 font-bold uppercase">{safeString(account?.broker, "Zerodha Kite")}</span>
              </div>
              <div className="flex justify-between border-b border-slate-900 pb-2">
                <span className="text-slate-500 uppercase text-[9px]">Available Exchanges:</span>
                <span className="text-white font-semibold uppercase">NSE, BSE, NFO</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 uppercase text-[9px]">Product Categories:</span>
                <span className="text-white font-semibold uppercase">CNC, MIS, NRML</span>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center space-y-2">
              <UserCheck size={24} className="text-slate-700 mx-auto" />
              <p className="text-xs text-slate-500 font-mono">Profile telemetry unavailable. Establish a live broker connection.</p>
            </div>
          )}
        </div>

        {/* SECTION 4: Account Summary */}
        <div id="section-account-summary" className="p-5 bg-slate-950 rounded-xl border border-slate-900 text-left space-y-4">
          <div className="border-b border-slate-900 pb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Landmark size={15} className="text-cyan-400" />
              <h3 className="font-bold text-white text-xs uppercase tracking-wider">Section 4: Account Summary</h3>
            </div>
            <span className="text-[9px] font-mono bg-slate-900 text-slate-400 px-2 py-0.5 rounded uppercase">
              Balances
            </span>
          </div>

          <div className="space-y-4 pt-1">
            {/* Capital Allocation Telemetry */}
            {funds ? (
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-900/30 rounded-lg border border-slate-900 font-mono">
                  <span className="text-[9px] text-slate-500 uppercase block mb-1">Available Cash</span>
                  <span className="text-sm font-extrabold text-white">
                    {formatCurrency(funds.available_cash, 2)}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/30 rounded-lg border border-slate-900 font-mono">
                  <span className="text-[9px] text-slate-500 uppercase block mb-1">Margins Balance Limit</span>
                  <span className="text-sm font-extrabold text-white">
                    {formatCurrency(funds.margins, 2)}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/30 rounded-lg border border-slate-900 font-mono">
                  <span className="text-[9px] text-slate-500 uppercase block mb-1">Utilized Margin</span>
                  <span className={`text-sm font-extrabold ${safeNumber(funds.utilized_margin) > 0 ? "text-rose-400" : "text-slate-400"}`}>
                    {formatCurrency(funds.utilized_margin, 2)}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/30 rounded-lg border border-slate-900 font-mono">
                  <span className="text-[9px] text-slate-500 uppercase block mb-1">Available Margin Space</span>
                  <span className="text-sm font-extrabold text-emerald-400">
                    {formatCurrency(funds.available_margin, 2)}
                  </span>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-slate-900/10 border border-slate-900 rounded-lg text-center">
                <p className="text-xs text-slate-500 font-mono">No cash allocation metrics loaded.</p>
              </div>
            )}

            {/* Counts of portfolio segments */}
            {report ? (
              <div className="grid grid-cols-4 gap-2 pt-1 font-mono text-center">
                <div className="p-2 bg-slate-900/20 border border-slate-900 rounded-lg">
                  <span className="text-lg font-black text-white">{safeArray(report.holdings).length}</span>
                  <span className="text-[8px] text-slate-500 uppercase block mt-0.5">Holdings</span>
                </div>
                <div className="p-2 bg-slate-900/20 border border-slate-900 rounded-lg">
                  <span className="text-lg font-black text-white">{safeArray(report.positions?.net).length}</span>
                  <span className="text-[8px] text-slate-500 uppercase block mt-0.5">Positions</span>
                </div>
                <div className="p-2 bg-slate-900/20 border border-slate-900 rounded-lg">
                  <span className="text-lg font-black text-white">
                    {safeArray(report.orders?.all_orders || (report.orders as any)?.open_orders || (report.orders as any)?.open).length}
                  </span>
                  <span className="text-[8px] text-slate-500 uppercase block mt-0.5">Orders Today</span>
                </div>
                <div className="p-2 bg-slate-900/20 border border-slate-900 rounded-lg">
                  <span className="text-lg font-black text-white">{safeArray(report.trades).length}</span>
                  <span className="text-[8px] text-slate-500 uppercase block mt-0.5">Trades Today</span>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-slate-900/10 border border-slate-900 rounded-lg text-center">
                <p className="text-xs text-slate-500 font-mono">Connect broker to audit portfolio counts.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ⚠ LIVE MODE TRANSITION MODAL */}
      {showLiveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border border-rose-900/60 rounded-xl shadow-2xl p-6 text-left space-y-4 font-sans">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
              <div className="h-9 w-9 rounded-lg bg-rose-950/60 border border-rose-800/40 flex items-center justify-center text-rose-500">
                <AlertCircle size={20} />
              </div>
              <div>
                <h3 className="text-sm font-black text-white uppercase tracking-wider">
                  ⚠ LIVE TRADING
                </h3>
              </div>
            </div>

            <p className="text-xs text-neutral-300 leading-relaxed font-mono">
              You are about to enable <strong>REAL ORDER EXECUTION</strong>.<br />
              Real money is at risk.<br /><br />
              Practice mode uses virtual execution.<br />
              Continue?
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowLiveModal(false)}
                className="px-4 py-2 bg-neutral-950 hover:bg-neutral-850 border border-neutral-800 hover:border-neutral-700 text-neutral-300 hover:text-white text-xs font-bold rounded-lg uppercase tracking-wider transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowLiveModal(false);
                  handleModeChange("LIVE_TRADING");
                }}
                className="px-4 py-2 bg-rose-900 hover:bg-rose-800 text-white text-xs font-extrabold rounded-lg uppercase tracking-wider border border-rose-700 hover:border-rose-600 shadow-lg shadow-rose-950/50 transition-all cursor-pointer"
              >
                Enter Live Trading
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default BrokerIntegration;
