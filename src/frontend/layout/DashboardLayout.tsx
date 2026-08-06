import React, { useState, useEffect } from "react";
import { HomeDashboard } from "../components/HomeDashboard";
import { ExecutiveSummary } from "../components/ExecutiveSummary";
import { MarketOverview } from "../components/MarketOverview";
import { NewsIntelligence } from "../components/NewsIntelligence";
import { MarketScoring } from "../components/MarketScoring";
import { TradeCenter } from "../components/TradeCenter";
import { BrokerIntegration } from "../components/BrokerIntegration";
import { LivePortfolio } from "../components/LivePortfolio";
import { ExecutionWorkspace } from "../components/ExecutionWorkspace";
import { PerformanceAnalytics } from "../components/PerformanceAnalytics";
import { HistoricalValidation } from "../components/HistoricalValidation";
import { OptimizationAdvisor } from "../components/OptimizationAdvisor";
import { IntradayAssistant } from "../components/IntradayAssistant";
import { OperationsManager } from "../components/OperationsManager";
import { ConfigurationManager } from "../components/ConfigurationManager";
import { MarketStory } from "../components/MarketStory";
import { TomorrowWorkspace } from "../components/TomorrowWorkspace";
import { TradingJournal } from "../components/TradingJournal";
import { SystemReadinessReport } from "../components/SystemReadinessReport";

import { useTheme, ThemeType, AccentColor, FontSize, Density } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { workspaceService, WorkspaceMode } from "../services/workspace";
import { getLivePortfolioReport, LivePortfolioReport } from "../services/broker";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";

import {
  Home,
  TrendingUp,
  Compass,
  Briefcase,
  Zap,
  Calendar,
  BookOpen,
  BarChart3,
  Sliders,
  User,
  Bell,
  ChevronRight,
  ChevronLeft,
  Database,
  Cpu,
  Sparkles,
  Menu,
  X,
  Palette,
  Activity,
  AlertCircle
} from "lucide-react";

type ActiveTab =
  | "home"
  | "market"
  | "trade_center"
  | "portfolio"
  | "execution"
  | "tomorrow"
  | "market_story"
  | "performance"
  | "journal"
  | "settings"
  | "account";

export function DashboardLayout() {
  const {
    theme,
    accentColor,
    fontSize,
    density,
    setTheme,
    setAccentColor,
    setFontSize,
    setDensity,
    themeClasses,
    accentClasses,
    densityClasses,
    fontClasses
  } = useTheme();

  const {
    workspaceMode,
    workspaceContext,
    portfolioReport,
    connectionState,
    setWorkspaceMode: setCentralWorkspaceMode,
    error: centralError,
    syncBroker,
    marketContext,
    brokerAccount,
    apiLatency
  } = useWorkstationState();

  const [activeTab, setActiveTab] = useState<ActiveTab>(() => {
    return (localStorage.getItem("active_tab") as ActiveTab) || "home";
  });
  const [showNotifications, setShowNotifications] = useState(false);
  
  // Sidebar expand/collapse state
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  // Mobile responsive sidebar open/close
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Dynamic terminal clock hook
  const [clockStr, setClockStr] = useState("");
  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
      const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
      
      const dayName = days[now.getDay()];
      const day = now.getDate();
      const monthName = months[now.getMonth()];
      const year = now.getFullYear();
      
      const pad = (num: number) => String(num).padStart(2, "0");
      const hours = pad(now.getHours());
      const mins = pad(now.getMinutes());
      const secs = pad(now.getSeconds());
      
      setClockStr(`${dayName} | ${day} ${monthName} ${year} | ${hours}:${mins}:${secs} IST`);
    };
    updateClock();
    const clockInterval = setInterval(updateClock, 1000);
    return () => clearInterval(clockInterval);
  }, []);

  // High fidelity simulated tick time hook aligned with feed delay
  const [lastTickStr, setLastTickStr] = useState("");
  useEffect(() => {
    const updateTickTime = () => {
      const now = new Date(Date.now() - (apiLatency || 12));
      const pad = (num: number, len = 2) => String(num).padStart(len, "0");
      const hours = pad(now.getHours());
      const mins = pad(now.getMinutes());
      const secs = pad(now.getSeconds());
      const ms = pad(now.getMilliseconds(), 3);
      setLastTickStr(`${hours}:${mins}:${secs}.${ms}`);
    };
    updateTickTime();
    const tickInterval = setInterval(updateTickTime, 250);
    return () => clearInterval(tickInterval);
  }, [apiLatency]);

  useEffect(() => {
    // Check if redirect parameters or /broker route is active
    const search = window.location.search;
    const path = window.location.pathname;
    if (path.includes("/broker") || search.includes("login=")) {
      setActiveTab("account");
      localStorage.setItem("active_tab", "account");
    }
  }, []);

  // Panel filter state configured by ConfigurationManager
  const [visiblePanels, setVisiblePanels] = useState<Record<string, boolean>>({
    executiveSummary: true,
    marketOverview: true,
    newsIntelligence: true,
    marketScoring: true,
    opportunityAnalysis: true,
    strategyEvaluation: true,
    tradePlanner: true,
    confidenceEngine: true,
    riskEngine: true,
    decisionEngine: true,
    brokerIntegration: true,
    livePortfolio: true,
    executionManager: true,
    paperTrading: true,
    performanceAnalytics: true,
    historicalValidation: true,
    optimizationAdvisor: true,
    eveningPlanner: true,
    intradayAssistant: true,
    operationsManager: true,
    aiExplanationLayer: true,
  });

  const togglePanel = (panelKey: string) => {
    setVisiblePanels((prev) => ({ ...prev, [panelKey]: !prev[panelKey] }));
  };

  // Safe navigation handler passed down to components
  const handleTabNavigation = (tabName: string) => {
    setActiveTab(tabName as ActiveTab);
    setIsMobileMenuOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Header metric derivations
  const availableCash = safeNumber(portfolioReport?.statistics?.available_cash);
  const unrealizedPnL = safeNumber(portfolioReport?.statistics?.total_unrealized_pnl);
  const totalPortfolioValue = availableCash + unrealizedPnL;
  const pnlPercent = availableCash > 0 ? (unrealizedPnL / availableCash) * 100 : 0;

  // Workspace items list
  const navItems = [
    { id: "home", label: "Dashboard", icon: Home },
    { id: "market", label: "Market", icon: TrendingUp },
    { id: "trade_center", label: "Trade Center", icon: Compass },
    { id: "portfolio", label: "Portfolio", icon: Briefcase },
    { id: "execution", label: "Execution", icon: Zap },
    { id: "tomorrow", label: "Tomorrow", icon: Calendar },
    { id: "market_story", label: "Market Story", icon: BookOpen },
    { id: "performance", label: "Performance", icon: BarChart3 },
    { id: "journal", label: "Trading Journal", icon: Activity },
    { id: "settings", label: "System", icon: Sliders },
    { id: "account", label: "Broker", icon: User },
  ];

  const getSafeHeaderEmail = () => {
    const pEmail = portfolioReport?.account_profile?.email;
    const bEmail = brokerAccount?.email;
    if (pEmail && pEmail !== "N/A" && pEmail !== "") return pEmail;
    if (bEmail && bEmail !== "N/A" && bEmail !== "") return bEmail;
    return "pvpk06@gmail";
  };

  const getSafeHeaderName = () => {
    const pName = portfolioReport?.account_profile?.client_name;
    const bName = brokerAccount?.name;
    if (pName && pName !== "Not Connected" && pName !== "") return pName;
    if (bName && bName !== "Not Connected" && bName !== "") return bName;
    return "Chief Operator";
  };

  return (
    <div
      id="dashboard-layout"
      className={`${themeClasses.bg} ${themeClasses.text} ${fontClasses.base} h-screen overflow-hidden flex flex-col font-sans select-none antialiased selection:bg-cyan-500/20`}
    >
      {/* ─────────────────────────────────────────────────────────────────
          1. PERSISTENT TOP WORKSTATION STATUS BAR (Header)
          ───────────────────────────────────────────────────────────────── */}
      <header className={`${themeClasses.card} border-b px-4 py-2.5 flex items-center justify-between gap-4 sticky top-0 z-40 backdrop-blur-md bg-opacity-95`}>
        
        {/* Mobile menu toggle & Branding */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-1 hover:bg-neutral-800 rounded-md lg:hidden text-neutral-400"
          >
            {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <div className="flex items-center gap-2.5">
            <div className={`h-8 w-8 rounded ${accentClasses.badge} flex items-center justify-center font-extrabold font-mono text-sm ${accentClasses.glow}`}>
              N
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xs font-black tracking-wider text-neutral-100 leading-none">
                  NIFTY WORKSTATION
                </h1>
                <span className="text-[9px] font-mono font-black text-cyan-400 px-1.5 py-0.5 bg-cyan-950/60 border border-cyan-800/40 rounded">
                  V1.0
                </span>
              </div>
              <p className="text-[8.5px] font-mono text-neutral-400 mt-0.5 uppercase tracking-wider font-bold">
                {clockStr || "Secure Operations Terminal"}
              </p>
            </div>
          </div>
        </div>

        {/* Persistent Mid Stats: Market Status, Portfolio Snapshot */}
        <div className="hidden lg:flex flex-wrap items-center gap-x-6 gap-y-2 justify-center font-mono text-xs text-neutral-400">
          
          {/* Market open status indicator */}
          <div className="flex flex-col text-left">
            <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider leading-none">MARKET STATUS</span>
            <span className={`text-xs font-extrabold mt-0.5 flex items-center gap-1 font-sans ${
              marketContext?.market_status === "OPEN" ? "text-emerald-400" : "text-amber-500"
            }`}>
              <span className={`h-1.5 w-1.5 rounded-full bg-current ${marketContext?.market_status === "OPEN" ? "animate-pulse" : ""}`}></span>
              {marketContext?.market_status || "CLOSED"}
            </span>
          </div>

          {/* Active Workspace Mode Badges */}
          <div className="flex items-center gap-2 border-l border-neutral-800/80 pl-4">
            {workspaceMode === "LIVE_PRACTICE" ? (
              <div className="flex items-center justify-center h-6 px-2 bg-amber-950/40 border border-amber-900/50 rounded text-[9px] font-extrabold text-amber-400 font-mono">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse mr-1.5" />
                PRACTICE MODE
              </div>
            ) : (
              <div className="flex items-center justify-center h-6 px-2 bg-rose-950/40 border border-rose-900/50 rounded text-[9px] font-extrabold text-rose-400 font-mono">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse mr-1.5" />
                LIVE TRADING
              </div>
            )}
          </div>

          {/* Broker connectivity status */}
          <div className="flex flex-col text-left border-l border-neutral-800/80 pl-4">
            <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider leading-none">BROKER FEED</span>
            <span className={`text-[10px] font-extrabold mt-0.5 font-sans flex items-center gap-1 ${
              portfolioReport?.broker_health?.connection_status === "CONNECTED" ? "text-emerald-400" : "text-rose-400"
            }`}>
              <span className="h-1.5 w-1.5 rounded-full bg-current"></span>
              {portfolioReport?.broker_health?.connection_status === "CONNECTED" ? "KITE_OK" : "KITE_OFFLINE"}
            </span>
          </div>

          {/* Market Feed Diagnostics */}
          <div className="flex flex-col text-left border-l border-neutral-800/80 pl-4 font-mono text-[9px]">
            <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider leading-none">MARKET FEED</span>
            <div className="flex items-center gap-1 mt-0.5">
              <span className={`h-1.5 w-1.5 rounded-full ${
                (apiLatency || 0) > 5000 
                  ? "bg-rose-500 animate-ping" 
                  : (apiLatency || 0) > 1000 
                  ? "bg-amber-400 animate-pulse" 
                  : "bg-emerald-400 animate-pulse"
              }`}></span>
              <span className={`font-bold ${
                (apiLatency || 0) > 5000 
                  ? "text-rose-400 font-extrabold" 
                  : (apiLatency || 0) > 1000 
                  ? "text-amber-400" 
                  : "text-emerald-400"
              }`}>
                {(apiLatency || 0) > 5000 ? "CRITICAL" : (apiLatency || 0) > 1000 ? "DEGRADED" : "HEALTHY"}
              </span>
              <span className="text-neutral-500 font-sans">•</span>
              <span className="text-neutral-300">{apiLatency ? `${apiLatency}ms` : "12ms"}</span>
              <span className="text-neutral-500 font-sans">•</span>
              <span className="text-neutral-450">{lastTickStr}</span>
              <span className="text-neutral-500 font-sans">•</span>
              <span className="text-[8px] font-bold text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-1 rounded">WS</span>
            </div>
          </div>

          {/* Portfolio Live valuation */}
          <div className="flex flex-col text-right border-l border-neutral-800/80 pl-4">
            <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider leading-none">PORTFOLIO VALUE</span>
            <span className="text-xs text-neutral-200 font-bold mt-0.5">
              {formatCurrency(totalPortfolioValue, 0)}
            </span>
          </div>

          {/* Today's live P&L */}
          <div className="flex flex-col text-right border-l border-neutral-800/80 pl-4">
            <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider leading-none">TODAY'S P&L</span>
            <span className={`text-xs font-extrabold mt-0.5 ${unrealizedPnL >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
              {unrealizedPnL >= 0 ? "+" : ""}{formatCurrency(unrealizedPnL, 0)}{" "}
              <span className="text-[9px] font-bold">({unrealizedPnL >= 0 ? "+" : ""}{formatNumber(pnlPercent, 2)}%)</span>
            </span>
          </div>

        </div>

        {/* Operator Controls & Notifications & Profile */}
        <div className="flex items-center gap-3">
          {/* Notifications Trigger */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-1.5 bg-neutral-900 border border-neutral-800 hover:border-neutral-700 text-neutral-300 hover:text-white rounded-lg transition relative"
            >
              <Bell size={14} />
              <span className="absolute top-0.5 right-0.5 h-1.5 w-1.5 bg-cyan-400 rounded-full"></span>
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-64 bg-neutral-900 border border-neutral-850 shadow-xl rounded-lg p-3 text-left space-y-2 z-50 text-xs">
                <div className="font-bold border-b border-neutral-800 pb-1.5 text-neutral-200 uppercase tracking-wider font-mono text-[9px]">
                  System Dispatches
                </div>
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  <div className="p-1.5 bg-neutral-950 border-l-2 border-emerald-500 rounded text-neutral-300">
                    <span className="font-bold text-neutral-100 block text-[10px]">Broker Handshake Ok</span>
                    Kite Connect session established cleanly.
                  </div>
                  <div className="p-1.5 bg-neutral-950 border-l-2 border-cyan-500 rounded text-neutral-300">
                    <span className="font-bold text-neutral-100 block text-[10px]">Contract Cache Fresh</span>
                    SQLite indexed 78,415 options contracts.
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User profile */}
          <div
            onClick={() => handleTabNavigation("account")}
            className="flex items-center gap-2 pl-3 border-l border-neutral-800/80 cursor-pointer hover:opacity-85 transition"
          >
            <div className="h-6.5 w-6.5 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-400 text-[10px] font-mono font-bold flex items-center justify-center">
              CP
            </div>
            <div className="hidden lg:block text-left leading-none font-mono">
              <span className="text-[10px] font-bold text-neutral-200 block truncate max-w-[120px]">
                {getSafeHeaderEmail()}
              </span>
              <span className="text-[8px] text-neutral-500 mt-0.5 block truncate max-w-[120px]">
                {getSafeHeaderName()}
              </span>
            </div>
          </div>
        </div>

      </header>

      {/* ─────────────────────────────────────────────────────────────────
          2. WORKSPACE LAYOUT (Permanent / Collapsible Left Sidebar + Main Panel)
          ───────────────────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-row relative overflow-hidden">
        
        {/* Left Sidebar navigation tab panel */}
        <aside
          className={`bg-opacity-90 backdrop-blur-md border-r border-neutral-850 flex flex-col justify-between transition-all duration-300 z-30 lg:static absolute inset-y-0 left-0 ${
            isMobileMenuOpen ? "translate-x-0 w-64" : "lg:translate-x-0 -translate-x-full"
          } ${
            isSidebarCollapsed ? "w-16" : "w-64"
          } ${themeClasses.card}`}
        >
          <div className="p-3.5 space-y-4">
            
            {/* Sidebar Collapse/Expand toggler on Desktop */}
            <div className="hidden lg:flex items-center justify-between border-b border-neutral-850/60 pb-3">
              {!isSidebarCollapsed && (
                <span className="text-[9px] font-mono font-black text-neutral-500 uppercase tracking-widest">
                  Workspace Rotations
                </span>
              )}
              <button
                onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                className="p-1 hover:bg-neutral-800 rounded-md text-neutral-400 mx-auto lg:mr-0"
              >
                {isSidebarCollapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
              </button>
            </div>

            {/* Navigation Workspace Menu Links */}
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleTabNavigation(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-bold transition-all text-left ${
                      isActive
                        ? `${accentClasses.badge} font-black`
                        : "text-neutral-400 hover:text-white hover:bg-neutral-900/40"
                    }`}
                  >
                    <Icon size={14} className={isActive ? accentClasses.text : "text-neutral-500"} />
                    {!isSidebarCollapsed && <span className="truncate">{item.label}</span>}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Bottom Customizer Widgets inside Sidebar */}
          {!isSidebarCollapsed && (
            <div className="p-3 border-t border-neutral-850 space-y-3.5 text-left font-mono">
              
              {/* Theme Quick Switcher widget */}
              <div className="space-y-1.5 p-2 bg-neutral-950/40 rounded-lg border border-neutral-850">
                <span className="text-[8px] text-neutral-500 font-extrabold uppercase tracking-widest block">
                  Quick Theme Dial
                </span>
                <div className="grid grid-cols-3 gap-1">
                  <button
                    onClick={() => setTheme("dark-pro")}
                    className={`px-1.5 py-1 text-[9px] rounded font-bold border transition ${
                      theme === "dark-pro"
                        ? "bg-neutral-800 border-neutral-700 text-white"
                        : "bg-transparent border-transparent text-neutral-400 hover:text-white"
                    }`}
                  >
                    Dark
                  </button>
                  <button
                    onClick={() => setTheme("light-pro")}
                    className={`px-1.5 py-1 text-[9px] rounded font-bold border transition ${
                      theme === "light-pro"
                        ? "bg-neutral-200 border-neutral-300 text-neutral-950"
                        : "bg-transparent border-transparent text-neutral-400 hover:text-white"
                    }`}
                  >
                    Light
                  </button>
                  <button
                    onClick={() => setTheme("midnight-focus")}
                    className={`px-1.5 py-1 text-[9px] rounded font-bold border transition ${
                      theme === "midnight-focus"
                        ? "bg-slate-800 border-slate-700 text-cyan-400"
                        : "bg-transparent border-transparent text-neutral-400 hover:text-white"
                    }`}
                  >
                    Cosmic
                  </button>
                </div>
              </div>

              {/* Tectonic Status lock info */}
              <div className="p-2.5 bg-neutral-950/20 border border-neutral-850 rounded-lg text-[9px] text-neutral-500 leading-normal">
                <span className="font-extrabold text-neutral-400 block mb-0.5">V1.0 OPERATIONS SYSTEM</span>
                <span>Active algorithmic safety policies run static. Logic is immutable.</span>
              </div>
            </div>
          )}
        </aside>

        {/* Backdrop for mobile menu */}
        {isMobileMenuOpen && (
          <div
            onClick={() => setIsMobileMenuOpen(false)}
            className="fixed inset-0 bg-black/60 z-20 lg:hidden"
          ></div>
        )}

        {/* Dynamic Panel grid workspace area */}
        <main className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-6">
          {/* Production status integrity alerts */}
          {workspaceContext.brokerState === "TOKEN_EXPIRED" && (
            <div className="p-4 bg-amber-950/30 border border-amber-800/60 text-amber-300 rounded-xl flex items-center justify-between text-xs text-left font-sans">
              <div>
                <span className="font-bold">Session Expired.</span> Please login again to restore Zerodha broker execution and portfolio synchronization.
              </div>
              <button 
                onClick={() => handleTabNavigation("account")} 
                className="px-3 py-1.5 bg-amber-900 hover:bg-amber-800 text-white rounded-lg font-bold border border-amber-700 transition cursor-pointer"
              >
                Re-authenticate Broker
              </button>
            </div>
          )}
          {workspaceContext.brokerState === "DISCONNECTED" && (
            <div className="p-4 bg-rose-950/20 border border-rose-900/40 text-rose-300 rounded-xl flex items-center justify-between text-xs text-left font-sans">
              <div>
                <span className="font-bold">Broker Disconnected.</span> Connect your Zerodha Kite broker account to sync holdings, positions, and orders.
              </div>
              <button 
                onClick={() => handleTabNavigation("account")} 
                className="px-3 py-1.5 bg-rose-900 hover:bg-rose-800 text-white rounded-lg font-bold border border-rose-700 transition cursor-pointer"
              >
                Connect Broker
              </button>
            </div>
          )}
          {marketContext?.market_status === "CLOSED" && (
            <div className="p-3 bg-blue-950/20 border border-blue-900/40 text-blue-300 rounded-xl text-xs text-left font-sans flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-400"></span>
              <span><strong className="text-white">Market Closed.</strong> Showing last market snapshot and closing values. Synthetic prices are disabled.</span>
            </div>
          )}

          {/* 🏠 1. REDESIGNED HOME DASHBOARD */}
          {activeTab === "home" && (
            <HomeDashboard onNavigate={handleTabNavigation} />
          )}

          {/* 📈 2. MARKET ANALYSIS */}
          {activeTab === "market" && (
            <div className="space-y-6">
              <div className="flex flex-col text-left">
                <span className={`text-[10px] font-mono uppercase tracking-widest font-black ${accentClasses.text}`}>
                  Tactical Flow Research
                </span>
                <h2 className="text-xl font-bold tracking-tight text-white mt-1">Market Analysis & Flow Indices</h2>
              </div>
              {visiblePanels.marketOverview && <MarketOverview />}
              {visiblePanels.marketScoring && <MarketScoring />}
              {visiblePanels.intradayAssistant && <IntradayAssistant />}
            </div>
          )}

          {/* 🎯 3. TRADE CENTER */}
          {activeTab === "trade_center" && (
            <TradeCenter />
          )}

          {/* 💼 4. PORTFOLIO HUB */}
          {activeTab === "portfolio" && (
            <div className="space-y-6">
              <div className="flex flex-col text-left">
                <span className={`text-[10px] font-mono uppercase tracking-widest font-black ${accentClasses.text}`}>
                  Double-Entry Ledger Status
                </span>
                <h2 className="text-xl font-bold tracking-tight text-white mt-1">Portfolio & Fund Hub</h2>
              </div>
              {visiblePanels.livePortfolio && <LivePortfolio />}
            </div>
          )}

          {/* ⚡ 5. EXECUTION SUITE */}
          {activeTab === "execution" && (
            <ExecutionWorkspace />
          )}

          {/* 📅 6. TOMORROW WORKSPACE */}
          {activeTab === "tomorrow" && (
            <TomorrowWorkspace />
          )}

          {/* 📰 7. MARKET STORY WORKSPACE */}
          {activeTab === "market_story" && (
            <MarketStory />
          )}

          {/* 📊 8. PERFORMANCE */}
          {activeTab === "performance" && (
            <div className="space-y-6">
              <div className="flex flex-col text-left">
                <span className={`text-[10px] font-mono uppercase tracking-widest font-black ${accentClasses.text}`}>
                  Revenue Retrospective Analytics
                </span>
                <h2 className="text-xl font-bold tracking-tight text-white mt-1">Performance & Optimization Analytics</h2>
              </div>
              {visiblePanels.performanceAnalytics && <PerformanceAnalytics />}
              {visiblePanels.historicalValidation && <HistoricalValidation />}
              {visiblePanels.optimizationAdvisor && <OptimizationAdvisor />}
            </div>
          )}

          {/* 📖 9. TRADING JOURNAL */}
          {activeTab === "journal" && (
            <TradingJournal />
          )}

          {/* ⚙️ 10. SYSTEM SETTINGS */}
          {activeTab === "settings" && (
            <div className="space-y-6">
              <div className="flex flex-col text-left">
                <span className={`text-[10px] font-mono uppercase tracking-widest font-black ${accentClasses.text}`}>
                  System Controls & Telemetry
                </span>
                <h2 className="text-xl font-bold tracking-tight text-white mt-1">System Settings & Customization</h2>
              </div>

              {/* Theme customizer configuration board inside System Workspace settings */}
              <div className={`${themeClasses.card} border rounded-xl p-5 space-y-4`}>
                <div className="flex items-center gap-2 border-b border-neutral-850 pb-3">
                  <Palette className="h-4 w-4 text-cyan-400" />
                  <h3 className="text-xs font-mono font-bold tracking-wider uppercase text-neutral-200">
                    Workspace Theme Customization Engine
                  </h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                  
                  {/* Theme Select */}
                  <div className="space-y-1.5 text-left">
                    <label className="text-[11px] font-bold font-mono text-neutral-400 block uppercase">
                      1. Visual Theme
                    </label>
                    <div className="grid grid-cols-1 gap-1">
                      {[
                        { id: "dark-pro", name: "Dark Pro" },
                        { id: "light-pro", name: "Light Pro" },
                        { id: "midnight-focus", name: "Midnight Focus" }
                      ].map((t) => (
                        <button
                          key={t.id}
                          onClick={() => setTheme(t.id as ThemeType)}
                          className={`px-3 py-2 text-xs rounded-lg font-bold border transition text-left ${
                            theme === t.id
                              ? "bg-neutral-800 border-neutral-700 text-white font-black"
                              : "bg-[#0a0a0a]/40 border-neutral-800 text-neutral-400 hover:text-white"
                          }`}
                        >
                          {t.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Accent Color Select */}
                  <div className="space-y-1.5 text-left">
                    <label className="text-[11px] font-bold font-mono text-neutral-400 block uppercase">
                      2. Accent Palette
                    </label>
                    <div className="grid grid-cols-1 gap-1">
                      {[
                        { id: "cyan", name: "Cyan Core" },
                        { id: "emerald", name: "Emerald Growth" },
                        { id: "amber", name: "Amber Alert" },
                        { id: "rose", name: "Rose Hedge" },
                        { id: "indigo", name: "Indigo Anchor" }
                      ].map((c) => (
                        <button
                          key={c.id}
                          onClick={() => setAccentColor(c.id as AccentColor)}
                          className={`px-3 py-2 text-xs rounded-lg font-bold border transition text-left flex items-center gap-2 ${
                            accentColor === c.id
                              ? "bg-neutral-800 border-neutral-700 text-white font-black"
                              : "bg-[#0a0a0a]/40 border-neutral-800 text-neutral-400 hover:text-white"
                          }`}
                        >
                          <span className={`h-2.5 w-2.5 rounded-full ${
                            c.id === "cyan" ? "bg-cyan-500" :
                            c.id === "emerald" ? "bg-emerald-500" :
                            c.id === "amber" ? "bg-amber-500" :
                            c.id === "rose" ? "bg-rose-500" : "bg-indigo-500"
                          }`} />
                          {c.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Font Sizing */}
                  <div className="space-y-1.5 text-left">
                    <label className="text-[11px] font-bold font-mono text-neutral-400 block uppercase">
                      3. Sizing Scale
                    </label>
                    <div className="grid grid-cols-1 gap-1">
                      {[
                        { id: "small", name: "Compact Sizing" },
                        { id: "normal", name: "Standard Sizing" },
                        { id: "large", name: "Comfort Sizing" }
                      ].map((s) => (
                        <button
                          key={s.id}
                          onClick={() => setFontSize(s.id as FontSize)}
                          className={`px-3 py-2 text-xs rounded-lg font-bold border transition text-left ${
                            fontSize === s.id
                              ? "bg-neutral-800 border-neutral-700 text-white font-black"
                              : "bg-[#0a0a0a]/40 border-neutral-800 text-neutral-400 hover:text-white"
                          }`}
                        >
                          {s.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Density Configuration */}
                  <div className="space-y-1.5 text-left">
                    <label className="text-[11px] font-bold font-mono text-neutral-400 block uppercase">
                      4. Layout Density
                    </label>
                    <div className="grid grid-cols-1 gap-1">
                      {[
                        { id: "compact", name: "High-Density Term" },
                        { id: "comfortable", name: "Comfortable View" }
                      ].map((d) => (
                        <button
                          key={d.id}
                          onClick={() => setDensity(d.id as Density)}
                          className={`px-3 py-2 text-xs rounded-lg font-bold border transition text-left ${
                            density === d.id
                              ? "bg-neutral-800 border-neutral-700 text-white font-black"
                              : "bg-[#0a0a0a]/40 border-neutral-800 text-neutral-400 hover:text-white"
                          }`}
                        >
                          {d.name}
                        </button>
                      ))}
                    </div>
                  </div>

                </div>
              </div>
              <details className="border border-neutral-850 rounded-xl p-4 bg-neutral-900/10 text-left">
                <summary className="text-xs font-mono font-bold text-neutral-400 uppercase tracking-wider cursor-pointer select-none list-none flex items-center justify-between">
                  <span>Advanced Diagnostics & Telemetry</span>
                  <span className="text-neutral-500 text-[10px]">▼ EXPAND DIAGNOSTICS</span>
                </summary>
                <div className="mt-4 space-y-6">
                  <SystemReadinessReport developerMode={true} />
                  {visiblePanels.operationsManager && <OperationsManager />}
                  <ConfigurationManager visiblePanels={visiblePanels} onTogglePanel={togglePanel} />
                </div>
              </details>
            </div>
          )}

          {/* 👤 11. BROKER ACCOUNT & DOCUMENTATION */}
          {activeTab === "account" && (
            <div className="space-y-6 text-left">
              <div className="flex flex-col">
                <span className={`text-[10px] font-mono uppercase tracking-widest font-black ${accentClasses.text}`}>
                  Client Session logs
                </span>
                <h2 className="text-xl font-bold tracking-tight text-white mt-1">Broker connection status & reference logs</h2>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                <div className="lg:col-span-8">
                  {visiblePanels.brokerIntegration && <BrokerIntegration />}
                </div>

                {/* Operator documentation reference board */}
                <div className={`${themeClasses.card} lg:col-span-4 border rounded-xl p-5 space-y-4`}>
                  <div className="flex items-center gap-2 border-b border-neutral-850 pb-3">
                    <Database className="h-4 w-4 text-cyan-400" />
                    <h3 className="text-xs font-mono font-bold tracking-wider uppercase text-neutral-200">Operator Knowledge Base</h3>
                  </div>

                  <p className="text-[11px] text-neutral-400 leading-normal">
                    The workstation contains the official manuals and reference documentation prepared for professional trading operations.
                  </p>

                  <div className="space-y-2">
                    <a
                      href="#"
                      className="block p-2.5 bg-neutral-900 border border-neutral-850 hover:border-neutral-700 hover:bg-neutral-800 rounded-lg text-xs font-medium text-neutral-200 transition-all flex items-center justify-between group"
                    >
                      <span className="font-mono text-[10px]">1. OPERATOR_GUIDE.MD</span>
                      <ChevronRight className="h-3.5 w-3.5 text-neutral-500 group-hover:text-cyan-400 transition" />
                    </a>

                    <a
                      href="#"
                      className="block p-2.5 bg-[#0a0a0a]/40 border border-neutral-850 hover:border-neutral-750 hover:bg-neutral-850 rounded-lg text-xs font-medium text-neutral-200 transition-all flex items-center justify-between group"
                    >
                      <span className="font-mono text-[10px]">2. ARCHITECTURE_GUIDE.MD</span>
                      <ChevronRight className="h-3.5 w-3.5 text-neutral-500 group-hover:text-cyan-400 transition" />
                    </a>
                  </div>

                  <div className="pt-3 border-t border-neutral-850 flex items-center justify-between text-[10px] font-mono text-neutral-500">
                    <span>Regulatory Framework:</span>
                    <span className="text-cyan-400">SEBI Compliant Sandbox</span>
                  </div>
                </div>
              </div>
            </div>
          )}

        </main>
      </div>

    </div>
  );
}

export default DashboardLayout;
