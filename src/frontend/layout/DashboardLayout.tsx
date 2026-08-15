import React, { useEffect, useState, useMemo } from "react";
import { Activity, Briefcase, Newspaper, Radio, Sliders, X, Sparkles, Compass, Layers, Calendar, BarChart2 } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { WorkstationTopBar } from "../components/WorkstationTopBar";
import { NiftyLiveWorkspace } from "../components/NiftyLiveWorkspace";
import { PreMarketPlannerWorkspace } from "../components/PreMarketPlannerWorkspace";
import { TodaysAnalysisWorkspace, LiveAssistantWorkspace, NewsUpdatesWorkspace, SettingsWorkspace } from "../components/PhaseOneWorkspaces";
import { MarketPulseWorkspace } from "../components/MarketPulseWorkspace";
import { OptionsWorkspace } from "../components/OptionsWorkspace";
import { PortfolioWorkspace } from "../components/PortfolioWorkspace";
import { SettingsDashboard } from "../components/SettingsDashboard";

// Exactly 4 primary sidebar modules as required by current sprint
export const PRIMARY_MODULES = [
  { id: "market", label: "MARKET", icon: Radio },
  { id: "intelligence", label: "INTELLIGENCE", icon: Activity },
  { id: "portfolio", label: "PORTFOLIO", icon: Briefcase },
  { id: "journal", label: "JOURNAL", icon: Newspaper },
] as const;

// Legacy export compatibility structures
export const NAVIGATION_GROUPS = [
  {
    category: "MARKET",
    items: [
      { id: "nifty-live", label: "Market Command", icon: Radio },
      { id: "market-pulse", label: "Market Pulse", icon: Calendar },
    ]
  },
  {
    category: "INTELLIGENCE",
    items: [
      { id: "live-assistant", label: "Intraday Intelligence", icon: Activity },
      { id: "todays-analysis", label: "Session Intelligence", icon: Activity },
      { id: "forward-outlook", label: "Scenario Outlook", icon: Compass },
    ]
  },
  {
    category: "PLANNING",
    items: [
      { id: "pre-market-planner", label: "Pre-Market Intelligence", icon: Layers },
    ]
  },
  {
    category: "INFORMATION",
    items: [
      { id: "news-updates", label: "Intelligence Feed", icon: Newspaper },
    ]
  },
  {
    category: "SYSTEM",
    items: [
      { id: "settings", label: "System Control", icon: Sliders },
    ]
  }
] as const;

export const PRIMARY_WORKSPACES = [
  { id: "nifty-live", label: "Market Command", icon: Radio },
  { id: "market-pulse", label: "Market Pulse", icon: Calendar },
  { id: "live-assistant", label: "Intraday Intelligence", icon: Activity },
  { id: "todays-analysis", label: "Session Intelligence", icon: Activity },
  { id: "forward-outlook", label: "Scenario Outlook", icon: Compass },
  { id: "pre-market-planner", label: "Pre-Market Intelligence", icon: Layers },
  { id: "news-updates", label: "Intelligence Feed", icon: Newspaper },
  { id: "settings", label: "System Control", icon: Sliders },
] as const;

export type WorkspaceId = typeof PRIMARY_WORKSPACES[number]["id"];
export type PrimaryModuleId = typeof PRIMARY_MODULES[number]["id"];
export type MarketSubTab = "nifty" | "metrics" | "options";
export type NiftySessionMode = "auto" | "pre_market" | "live" | "post_market";

export function DashboardLayout() {
  const { themeClasses, accentClasses, fontClasses } = useTheme();
  const { workspaceContext, marketContext, canonicalState, lastValidState } = useWorkstationState() as any;

  // Active module & sub-tab states
  const [activeModule, setActiveModule] = useState<PrimaryModuleId>(() => {
    const saved = localStorage.getItem("active_module") || localStorage.getItem("active_tab") || "market";
    if (["intelligence", "journal", "portfolio"].includes(saved)) return saved as PrimaryModuleId;
    return "market";
  });

  const [marketSubTab, setMarketSubTab] = useState<MarketSubTab>(() => {
    const savedTab = localStorage.getItem("active_market_tab") || localStorage.getItem("active_tab");
    if (savedTab === "market-pulse" || savedTab === "metrics") return "metrics";
    if (savedTab === "options") return "options";
    return "nifty";
  });

  const [niftyModeOverride, setNiftyModeOverride] = useState<NiftySessionMode>("auto");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);

  // Compute canonical session mode for NIFTY dynamic workspace
  const computedNiftyMode = useMemo<"pre_market" | "live" | "post_market">( () => {
    if (niftyModeOverride !== "auto") return niftyModeOverride;

    const stateObj = canonicalState ?? lastValidState;
    const mStatus = stateObj?.market_session?.status || "closed";
    const isClosed = Boolean(stateObj?.market_session?.is_closed || mStatus === "closed" || mStatus === "holiday" || mStatus === "weekend");

    // Check IST time
    const now = new Date();
    const istTimeStr = new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Kolkata", hour12: false, hour: "numeric", minute: "numeric" }).format(now);
    const [h, m] = istTimeStr.split(":").map(Number);
    const totalMinutes = h * 60 + m;

    if (mStatus === "pre_open" || (totalMinutes >= 360 && totalMinutes < 555 && !mStatus.includes("open"))) {
      return "pre_market";
    }
    if (mStatus === "open" || (totalMinutes >= 555 && totalMinutes <= 930 && !isClosed)) {
      return "live";
    }
    return "post_market";
  }, [niftyModeOverride, canonicalState, lastValidState]);

  const navigateModule = (id: PrimaryModuleId) => {
    setActiveModule(id);
    localStorage.setItem("active_module", id);
    setMobileOpen(false);
  };

  const navigateMarketSubTab = (tab: MarketSubTab) => {
    setMarketSubTab(tab);
    localStorage.setItem("active_market_tab", tab);
  };

  return (
    <div id="dashboard-layout" className={`${themeClasses.bg} ${themeClasses.text} ${fontClasses.base} flex h-screen flex-col overflow-hidden bg-[#0b0f19]`}>
      {/* Global Top Bar */}
      <WorkstationTopBar
        mobileOpen={mobileOpen}
        onToggleMobile={() => setMobileOpen(!mobileOpen)}
        onOpenSettings={() => setSettingsModalOpen(true)}
        onOpenAssistant={() => navigateModule("intelligence")}
      />

      {/* Expiry / Session Warning Banner */}
      {workspaceContext.brokerState === "TOKEN_EXPIRED" && (
        <div className="border-b border-rose-900/80 bg-rose-950/40 px-4 py-2.5 text-xs text-rose-300 flex items-center justify-between font-mono">
          <div>
            <strong>KITE SESSION EXPIRED.</strong> Last update: {marketContext.last_tick_time || "Unavailable"}. Live analysis paused.
          </div>
          <button onClick={() => setSettingsModalOpen(true)} className="underline text-rose-200 hover:text-white">
            Open Settings to Reconnect
          </button>
        </div>
      )}

      {/* Main Workspace Frame: Sidebar + Content */}
      <div className="flex min-h-0 flex-1">
        {/* Primary Sidebar Module Navigation (Exactly 4 items) */}
        <aside className={`${mobileOpen ? "block" : "hidden"} absolute z-40 h-full w-56 border-r border-slate-800/80 bg-[#0f172a] px-2.5 py-4 lg:static lg:block overflow-y-auto`}>
          <div className="mb-3 px-3 text-[9px] font-mono font-bold tracking-[0.2em] text-slate-500 uppercase">
            PRIMARY MODULES
          </div>
          <nav className="space-y-1">
            {PRIMARY_MODULES.map(module => {
              const Icon = module.icon;
              const isActive = activeModule === module.id;
              return (
                <button
                  key={module.id}
                  onClick={() => navigateModule(module.id)}
                  aria-current={isActive ? "page" : undefined}
                  className={`group flex w-full items-center gap-3 rounded-lg border-l-2 px-3 py-2.5 text-left text-xs font-bold transition ${
                    isActive
                      ? "border-cyan-400 bg-cyan-950/30 text-cyan-300 shadow-sm"
                      : "border-transparent text-slate-400 hover:bg-slate-900/80 hover:text-slate-200"
                  }`}
                >
                  <Icon size={16} className={isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"} />
                  <span className="tracking-wide">{module.label}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Workspace Content Region */}
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden bg-[#0b0f19]">
          {/* Secondary Navigation Sub-Bar (For MARKET module: NIFTY | METRICS | OPTIONS) */}
          {activeModule === "market" && (
            <div className="flex items-center justify-between border-b border-slate-800/80 bg-[#0f172a]/90 px-4 py-2 backdrop-blur">
              <div className="flex items-center gap-1.5 font-mono text-xs">
                <button
                  onClick={() => navigateMarketSubTab("nifty")}
                  className={`rounded-md px-3 py-1 font-bold transition ${
                    marketSubTab === "nifty"
                      ? "bg-cyan-950 text-cyan-300 border border-cyan-800/80"
                      : "text-slate-400 hover:bg-slate-900 hover:text-white"
                  }`}
                >
                  NIFTY
                </button>
                <button
                  onClick={() => navigateMarketSubTab("metrics")}
                  className={`rounded-md px-3 py-1 font-bold transition ${
                    marketSubTab === "metrics"
                      ? "bg-cyan-950 text-cyan-300 border border-cyan-800/80"
                      : "text-slate-400 hover:bg-slate-900 hover:text-white"
                  }`}
                >
                  METRICS
                </button>
                <button
                  onClick={() => navigateMarketSubTab("options")}
                  className={`rounded-md px-3 py-1 font-bold transition ${
                    marketSubTab === "options"
                      ? "bg-cyan-950 text-cyan-300 border border-cyan-800/80"
                      : "text-slate-400 hover:bg-slate-900 hover:text-white"
                  }`}
                >
                  OPTIONS
                </button>
              </div>

              {/* Session Controls when on NIFTY */}
              {marketSubTab === "nifty" && (
                <div className="hidden sm:flex items-center gap-1.5 text-[10px] font-mono">
                  <span className="text-slate-500 mr-1">Session Mode:</span>
                  <button
                    onClick={() => setNiftyModeOverride("auto")}
                    className={`px-2 py-0.5 rounded border transition ${
                      niftyModeOverride === "auto" ? "bg-cyan-950 text-cyan-300 border-cyan-800 font-bold" : "bg-slate-950 text-slate-400 border-slate-800"
                    }`}
                  >
                    Auto ({computedNiftyMode === "live" ? "Live" : computedNiftyMode === "pre_market" ? "Pre-Mkt" : "Post-Mkt"})
                  </button>
                  <button
                    onClick={() => setNiftyModeOverride("pre_market")}
                    className={`px-2 py-0.5 rounded border transition ${
                      niftyModeOverride === "pre_market" ? "bg-cyan-950 text-cyan-300 border-cyan-800 font-bold" : "bg-slate-950 text-slate-400 border-slate-800"
                    }`}
                  >
                    Pre-Market
                  </button>
                  <button
                    onClick={() => setNiftyModeOverride("live")}
                    className={`px-2 py-0.5 rounded border transition ${
                      niftyModeOverride === "live" ? "bg-cyan-950 text-cyan-300 border-cyan-800 font-bold" : "bg-slate-950 text-slate-400 border-slate-800"
                    }`}
                  >
                    NIFTY Live
                  </button>
                  <button
                    onClick={() => setNiftyModeOverride("post_market")}
                    className={`px-2 py-0.5 rounded border transition ${
                      niftyModeOverride === "post_market" ? "bg-cyan-950 text-cyan-300 border-cyan-800 font-bold" : "bg-slate-950 text-slate-400 border-slate-800"
                    }`}
                  >
                    Post-Market
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Main Scrollable Content View */}
          <main className="air-grid min-w-0 flex-1 overflow-y-auto p-3 sm:p-5 lg:p-6">
            {activeModule === "market" ? (
              marketSubTab === "nifty" ? (
                computedNiftyMode === "pre_market" ? (
                  <PreMarketPlannerWorkspace />
                ) : computedNiftyMode === "live" ? (
                  <NiftyLiveWorkspace />
                ) : (
                  <TodaysAnalysisWorkspace />
                )
              ) : marketSubTab === "metrics" ? (
                <MarketPulseWorkspace />
              ) : (
                <OptionsWorkspace />
              )
            ) : activeModule === "intelligence" ? (
              <LiveAssistantWorkspace />
            ) : activeModule === "portfolio" ? (
              <PortfolioWorkspace />
            ) : (
              <NewsUpdatesWorkspace />
            )}
          </main>
        </div>
      </div>

      {/* Settings Modal */}
      {settingsModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-800 bg-[#0f172a] shadow-2xl p-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <Sliders size={18} className="text-cyan-400" />
                <h2 className="text-base font-bold text-white tracking-tight">System Control & Settings</h2>
              </div>
              <button
                onClick={() => setSettingsModalOpen(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-900 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>
            <SettingsDashboard />
          </div>
        </div>
      )}
    </div>
  );
}

export default DashboardLayout;
