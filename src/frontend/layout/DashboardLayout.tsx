// src/frontend/layout/DashboardLayout.tsx
import React, { useEffect, useState, useMemo } from "react";
import { Compass, Layers, Calendar, Sliders, BookOpen, Target, Settings as SettingsIcon, ChevronLeft, ChevronRight } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { useNavigation, PrimaryModuleId } from "../context/NavigationContext";
import { WorkstationTopBar } from "../components/WorkstationTopBar";
import { NiftyLiveWorkspace } from "../components/NiftyLiveWorkspace";
import { SettingsWorkspace } from "../components/PhaseOneWorkspaces";
import { MarketPulseWorkspace } from "../components/MarketPulseWorkspace";
import { OptionsWorkspace } from "../components/OptionsWorkspace";
import { PortfolioWorkspace } from "../components/PortfolioWorkspace";
import { MarketIntelligenceWorkspace } from "../components/MarketIntelligenceWorkspace";
import { TradingCheatsheetWorkspace } from "../components/TradingCheatsheetWorkspace";
import { NewsWorkspace, NewsSubTab } from "../components/news/NewsWorkspace";
import { ArdhaPerformanceWorkspace } from "../components/ArdhaPerformanceWorkspace";
import { InspectionSelection, MarketDeepDive, MarketInspectionProvider } from "../context/MarketInspectionContext";
import { MarketGlyph, IntelligenceGlyph, PortfolioGlyph, JournalGlyph } from "../components/ui/VisualAssets";
import LiveAssistantPanel from "../components/LiveAssistantPanel";
import { resolveBriefingPresentationMode } from "../utils/briefingTimeResolver";
import { WorkspaceErrorBoundary } from "../components/ui/WorkspaceErrorBoundary";

// Primary sidebar modules (5 Official Primary Trading Modules)
export const PRIMARY_MODULES = [
  { id: "market", label: "MARKET", glyph: MarketGlyph },
  { id: "market_intelligence", label: "MARKET INTELLIGENCE", glyph: IntelligenceGlyph },
  { id: "trading_cheatsheet", label: "TRADING CHEATSHEET", glyph: BookOpen },
  { id: "news", label: "NEWS & UPDATES", glyph: JournalGlyph },
  { id: "portfolio", label: "PORTFOLIO", glyph: PortfolioGlyph },
] as const;

// Legacy export compatibility structures for tests
export const NAVIGATION_GROUPS = [
  {
    category: "MARKET",
    items: [
      { id: "nifty-live", label: "Market Command", icon: MarketGlyph },
      { id: "market-pulse", label: "Market Pulse", icon: Calendar },
    ],
  },
  {
    category: "INTELLIGENCE",
    items: [
      { id: "market-intelligence", label: "Market Intelligence", icon: IntelligenceGlyph },
    ],
  },
  {
    category: "INFORMATION",
    items: [
      { id: "news-updates", label: "Intelligence Feed", icon: JournalGlyph },
    ],
  },
  {
    category: "SYSTEM",
    items: [
      { id: "settings", label: "System Control", icon: Sliders },
    ],
  },
] as const;

export const PRIMARY_WORKSPACES = [
  { id: "nifty-live", label: "Market Command", icon: MarketGlyph },
  { id: "market-pulse", label: "Market Pulse", icon: Calendar },
  { id: "market-intelligence", label: "Market Intelligence", icon: IntelligenceGlyph },
  { id: "news-updates", label: "Intelligence Feed", icon: JournalGlyph },
  { id: "settings", label: "System Control", icon: Sliders },
] as const;

export type WorkspaceId = (typeof PRIMARY_WORKSPACES)[number]["id"];
export type MarketSubTab = "nifty" | "metrics" | "options";
export type NiftySessionMode = "auto" | "pre_market" | "live" | "post_market";

export function DashboardLayout() {
  const { fontClasses } = useTheme();
  const { workspaceContext, marketContext, canonicalState, lastValidState } = useWorkstationState() as any;
  const {
    activeModule,
    marketSubTab,
    newsSubTab,
    settingsOpen,
    settingsSubTab,
    assistantOpen,
    navigateTo,
    setNewsSubTab,
    setSettingsOpen,
    setSettingsSubTab,
  } = useNavigation();

  const isStagingMode = (import.meta as any).env?.VITE_STAGING_MODE === "true";

  const [niftyModeOverride, setNiftyModeOverride] = useState<NiftySessionMode>("auto");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [deepDive, setDeepDive] = useState<InspectionSelection | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("ardhamind_sidebar_collapsed") === "true";
    }
    return false;
  });

  const toggleSidebarCollapse = () => {
    setIsSidebarCollapsed((prev) => {
      const next = !prev;
      if (typeof window !== "undefined") {
        localStorage.setItem("ardhamind_sidebar_collapsed", String(next));
      }
      return next;
    });
  };

  // Compute canonical session mode for dynamic workspaces
  const computedNiftyMode = useMemo<"pre_market" | "live" | "post_market">(() => {
    if (niftyModeOverride !== "auto" && isStagingMode) return niftyModeOverride;

    const stateObj = canonicalState ?? lastValidState;
    const mStatus = stateObj?.market_session?.status || "closed";
    const isClosed = Boolean(
      stateObj?.market_session?.is_closed || mStatus === "closed" || mStatus === "holiday" || mStatus === "weekend"
    );

    const now = new Date();
    const istTimeStr = new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Kolkata",
      hour12: false,
      hour: "numeric",
      minute: "numeric",
    }).format(now);
    const [h, m] = istTimeStr.split(":").map(Number);
    const totalMinutes = h * 60 + m;

    if (mStatus === "pre_open" || (totalMinutes >= 360 && totalMinutes < 555 && !mStatus.includes("open"))) {
      return "pre_market";
    }
    if (mStatus === "open" || (totalMinutes >= 555 && totalMinutes <= 930 && !isClosed)) {
      return "live";
    }
    return "post_market";
  }, [niftyModeOverride, canonicalState, lastValidState, isStagingMode]);

  const [nowTick, setNowTick] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setNowTick(new Date()), 10000);
    return () => clearInterval(timer);
  }, []);

  const briefingPresentationMode = useMemo(() => {
    const stateObj = canonicalState ?? lastValidState;
    return resolveBriefingPresentationMode({
      customDate: nowTick,
      marketSessionState: stateObj?.market_session,
    });
  }, [nowTick, canonicalState, lastValidState]);

  // Unified Authoritative Navigation Handlers
  const navigateModule = (id: PrimaryModuleId) => {
    setDeepDive(null);
    navigateTo({ workspace: id });
    setMobileOpen(false);
  };

  const navigateMarketSubTab = (tab: MarketSubTab) => {
    setDeepDive(null);
    navigateTo({ workspace: "market", tab });
    setMobileOpen(false);
  };

  const openSettingsConsole = () => {
    setDeepDive(null);
    navigateTo({ workspace: "settings", tab: "overview" });
    setMobileOpen(false);
  };

  return (
    <MarketInspectionProvider onViewDetails={setDeepDive}>
      <div
        id="dashboard-layout"
        className={`${fontClasses.base} ardha-app flex h-screen flex-col overflow-hidden bg-[#050607] text-[#E6E8EB] font-sans`}
      >
        {/* Global Top Bar */}
        <WorkstationTopBar
          mobileOpen={mobileOpen}
          onToggleMobile={() => setMobileOpen(!mobileOpen)}
          onOpenSettings={openSettingsConsole}
          settingsOpen={settingsOpen}
        />

        {/* Expiry / Session Warning Banner */}
        {workspaceContext.brokerState === "TOKEN_EXPIRED" && (
          <div className="border-b border-[#E5484D]/40 bg-[#E5484D]/10 px-3 py-1.5 text-[11px] text-[#E5484D] flex items-center justify-between font-mono shrink-0">
            <div>
              <strong>KITE SESSION EXPIRED.</strong> Last update: {marketContext.last_tick_time || "Unavailable"}. Live
              analysis paused.
            </div>
            <button onClick={openSettingsConsole} className="underline text-red-200 hover:text-white font-bold">
              Open Settings Console
            </button>
          </div>
        )}

        {/* Main Workspace Frame: Sidebar + Content */}
        <div className="flex min-h-0 flex-1 bg-[#050607]">
          {/* Primary Sidebar Module Navigation */}
          <aside
            id="workstation-sidebar"
            className={`${mobileOpen ? "block" : "hidden"} ${
              isSidebarCollapsed ? "w-[58px]" : "w-[230px] sm:w-[240px]"
            } absolute z-40 h-full border-r border-[#191D23] bg-[#050607] px-2 py-3 lg:static lg:flex lg:flex-col lg:justify-between overflow-y-auto shrink-0 transition-[width] duration-200`}
          >
            {/* Upper Navigation List */}
            <nav className="space-y-1 font-mono">
              {PRIMARY_MODULES.map((module) => {
                const Glyph = module.glyph;
                const isActive = !settingsOpen && activeModule === module.id;
                const labelText = module.label;

                return (
                  <div key={module.id} className="relative group">
                    <button
                      onClick={() => navigateModule(module.id)}
                      aria-current={isActive ? "page" : undefined}
                      aria-label={labelText}
                      className={`flex h-11 w-full items-center ${
                        isSidebarCollapsed ? "justify-center px-0" : "gap-3 px-3"
                      } rounded-[3px] border-l-2 text-left text-[11px] font-bold tracking-wide transition-colors ${
                        isActive
                          ? "border-[#38BDF8] bg-[#12151A] text-[#E6E8EB]"
                          : "border-transparent text-[#707987] hover:bg-[#0E1013] hover:text-[#A5ABB4]"
                      }`}
                    >
                      <Glyph
                        size={17}
                        className={`shrink-0 ${isActive ? "text-[#38BDF8]" : "text-[#707987] group-hover:text-[#A5ABB4]"}`}
                      />
                      {!isSidebarCollapsed && <span className="truncate">{labelText}</span>}
                    </button>

                    {/* Hover Tooltip when collapsed */}
                    {isSidebarCollapsed && (
                      <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 hidden group-hover:flex items-center z-50 pointer-events-none">
                        <div className="rounded border border-[#242830] bg-[#0E1013] px-2 py-1 text-[10px] font-mono text-[#E6E8EB] shadow-xl whitespace-nowrap">
                          {labelText}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </nav>

            {/* Bottom Section: Settings & Collapse Button */}
            <div className="pt-2 border-t border-[#191D23] space-y-1 font-mono">
              {/* Settings Item */}
              <div className="relative group">
                <button
                  onClick={openSettingsConsole}
                  aria-current={settingsOpen ? "page" : undefined}
                  aria-label="Settings"
                  className={`flex h-11 w-full items-center ${
                    isSidebarCollapsed ? "justify-center px-0" : "gap-3 px-3"
                  } rounded-[3px] border-l-2 text-left text-[11px] font-bold tracking-wide transition-colors ${
                    settingsOpen
                      ? "border-[#38BDF8] bg-[#12151A] text-[#E6E8EB]"
                      : "border-transparent text-[#707987] hover:bg-[#0E1013] hover:text-[#A5ABB4]"
                  }`}
                >
                  <SettingsIcon
                    size={17}
                    className={`shrink-0 ${settingsOpen ? "text-[#38BDF8]" : "text-[#707987] group-hover:text-[#A5ABB4]"}`}
                  />
                  {!isSidebarCollapsed && <span className="truncate">SETTINGS</span>}
                </button>

                {isSidebarCollapsed && (
                  <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 hidden group-hover:flex items-center z-50 pointer-events-none">
                    <div className="rounded border border-[#242830] bg-[#0E1013] px-2 py-1 text-[10px] font-mono text-[#E6E8EB] shadow-xl whitespace-nowrap">
                      Settings
                    </div>
                  </div>
                )}
              </div>

              {/* Collapse / Expand Toggle */}
              <div className="relative group hidden lg:block">
                <button
                  onClick={toggleSidebarCollapse}
                  aria-label={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                  className={`flex h-9 w-full items-center ${
                    isSidebarCollapsed ? "justify-center" : "justify-end px-3"
                  } rounded-[3px] text-[#707987] hover:bg-[#0E1013] hover:text-[#E6E8EB] transition`}
                >
                  {isSidebarCollapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
                </button>

                {isSidebarCollapsed && (
                  <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 hidden group-hover:flex items-center z-50 pointer-events-none">
                    <div className="rounded border border-[#242830] bg-[#0E1013] px-2 py-1 text-[9.5px] font-mono text-[#E6E8EB] shadow-xl whitespace-nowrap">
                      Expand Sidebar
                    </div>
                  </div>
                )}
              </div>
            </div>
          </aside>

          {/* Workspace Content Region */}
          <div className="flex min-w-0 flex-1 flex-col overflow-hidden bg-[#08090B]">
            {/* Secondary Navigation Sub-Bar */}
            {(!settingsOpen && activeModule === "market") && (
              <div className="relative flex h-8 shrink-0 items-center justify-between border-b border-[#242830] bg-[#0B0D10] px-4 text-[11px] font-mono">
                {/* MARKET Sub-Tabs */}
                {activeModule === "market" && (
                  <div className="flex h-full items-center gap-6 font-semibold">
                    <button
                      onClick={() => navigateMarketSubTab("nifty")}
                      className={`relative h-full px-1 transition ${marketSubTab === "nifty"
                          ? "text-[#E6E8EB] font-bold after:absolute after:inset-x-0 after:bottom-0 after:h-[2px] after:bg-[#00C896]"
                          : "text-[#707987] hover:text-[#A5ABB4]"
                        }`}
                    >
                      NIFTY
                    </button>
                    <button
                      onClick={() => navigateMarketSubTab("metrics")}
                      className={`relative h-full px-1 transition ${marketSubTab === "metrics"
                          ? "text-[#E6E8EB] font-bold after:absolute after:inset-x-0 after:bottom-0 after:h-[2px] after:bg-[#38BDF8]"
                          : "text-[#707987] hover:text-[#A5ABB4]"
                        }`}
                    >
                      METRICS
                    </button>
                    <button
                      onClick={() => navigateMarketSubTab("options")}
                      className={`relative h-full px-1 transition ${marketSubTab === "options"
                          ? "text-[#E6E8EB] font-bold after:absolute after:inset-x-0 after:bottom-0 after:h-[2px] after:bg-[#8B5CF6]"
                          : "text-[#707987] hover:text-[#A5ABB4]"
                        }`}
                    >
                      OPTIONS
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* MAIN WORKSPACE COMPONENT RENDERER */}
            <main className="min-w-0 flex-1 overflow-y-auto bg-[#08090B] p-2.5 sm:p-3 lg:p-3.5">
              <WorkspaceErrorBoundary key={settingsOpen ? "settings" : activeModule} workspaceName={settingsOpen ? "SETTINGS" : String(activeModule).toUpperCase()}>
                {settingsOpen ? (
                  <SettingsWorkspace
                    subTab={settingsSubTab}
                    onSelectSubTab={setSettingsSubTab}
                    onBack={() => setSettingsOpen(false)}
                  />
                ) : activeModule === "trading_cheatsheet" ? (
                  <TradingCheatsheetWorkspace />
                ) : activeModule === "news" || (activeModule as string) === "journal" ? (
                  <NewsWorkspace subTab={newsSubTab} onSelectSubTab={setNewsSubTab} />
                ) : activeModule === "portfolio" ? (
                  <PortfolioWorkspace />
                ) : (activeModule as string) === "ardha_performance" ? (
                  <SettingsWorkspace
                    subTab="diagnostics"
                    onSelectSubTab={setSettingsSubTab}
                    onBack={() => setSettingsOpen(false)}
                  />
                ) : activeModule === "market_intelligence" ||
                   (activeModule as string) === "market_intelligence_v2" ||
                   (activeModule as string) === "intelligence" ||
                   (activeModule as string) === "pre_market_briefing" ||
                   (activeModule as string) === "market_insights" ? (
                  <MarketIntelligenceWorkspace />
                ) : marketSubTab === "metrics" ? (
                  <MarketPulseWorkspace />
                ) : marketSubTab === "options" ? (
                  <OptionsWorkspace />
                ) : (
                  <NiftyLiveWorkspace />
                )}
              </WorkspaceErrorBoundary>
            </main>
          </div>
        </div>

        {/* Global Contextual Live Assistant Right-Side Panel */}
        {assistantOpen && <LiveAssistantPanel />}

        {/* Deep Dive Inspection Modal */}
        {deepDive && <MarketDeepDive selection={deepDive} onBack={() => setDeepDive(null)} />}
      </div>
    </MarketInspectionProvider>
  );
}

export default DashboardLayout;
