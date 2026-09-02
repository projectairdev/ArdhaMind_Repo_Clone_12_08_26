// src/frontend/layout/DashboardLayout.tsx
import React, { useState } from "react";
import { Calendar, Sliders } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { useNavigation, PrimaryModuleId } from "../context/NavigationContext";
import { WorkstationTopBar } from "../components/WorkstationTopBar";
import { SettingsWorkspace } from "../components/PhaseOneWorkspaces";
import { MarketPulseWorkspace } from "../components/MarketPulseWorkspace";
import { PortfolioWorkspace } from "../components/PortfolioWorkspace";
import { NewsWorkspace } from "../components/news/NewsWorkspace";
import { InspectionSelection, MarketDeepDive, MarketInspectionProvider } from "../context/MarketInspectionContext";
import { MarketGlyph, IntelligenceGlyph, PortfolioGlyph, JournalGlyph } from "../components/ui/VisualAssets";
import LiveAssistantPanel from "../components/LiveAssistantPanel";
import { WorkspaceErrorBoundary } from "../components/ui/WorkspaceErrorBoundary";
import { useCanonicalState } from "../context/CanonicalStateContext";
import { MarketWorkspace as CanonicalMarketWorkspace } from "../components/canonical/MarketWorkspace";
import { MarketIntelligenceWorkspace as CanonicalMarketIntelligenceWorkspace } from "../components/canonical/MarketIntelligenceWorkspace";
import { OptionsIntelligenceWorkspace as CanonicalOptionsWorkspace } from "../components/canonical/OptionsIntelligenceWorkspace";
import { PredictionChartView } from "../components/intelligence/PredictionChartView";

// Primary sidebar modules (4 Official Primary Trading Modules ONLY)
export const PRIMARY_MODULES = [
  { id: "market", label: "MARKET", glyph: MarketGlyph },
  { id: "market_intelligence", label: "MARKET INTELLIGENCE", glyph: IntelligenceGlyph },
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
export type MarketSubTab = "nifty" | "metrics" | "options" | "predictions";
export type NiftySessionMode = "auto" | "pre_market" | "live" | "post_market";

export function DashboardLayout() {
  const { fontClasses } = useTheme();
  const { workspaceContext, marketContext } = useWorkstationState() as any;
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

  const { envelope, isFixtureData, isReplayMode, previewPhase } = useCanonicalState();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [deepDive, setDeepDive] = useState<InspectionSelection | null>(null);

  const fixtureDateDisplay =
    envelope?.session?.completed_session_date ||
    envelope?.session?.active_trading_date ||
    envelope?.session?.calendar_date ||
    "2026-09-01";

  const isFixtureSubstituted = isFixtureData || isReplayMode;

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

        {/* High-Contrast Fixture / Historical Replay Banner (Explicit Replay Only) */}
        {isFixtureSubstituted && (
          <div
            data-testid="fixture-substitution-banner"
            className="border-b border-[#F59E0B]/60 bg-[#F59E0B]/20 px-3.5 py-1.5 text-[11px] text-[#FDE68A] flex items-center justify-between font-mono shrink-0 shadow-md"
          >
            <div className="flex items-center gap-2">
              <span className="rounded bg-[#F59E0B] px-1.5 py-0.5 text-[9px] font-black text-black uppercase tracking-wider">
                FIXTURE DATA ACTIVE
              </span>
              <span>
                <strong>DATA SOURCE:</strong> Fixture reference session (<strong>{fixtureDateDisplay}</strong>). This is <strong>NOT LIVE MARKET DATA</strong>.
              </span>
            </div>
            {previewPhase !== "AUTO" && (
              <span className="text-[10px] text-[#FDE68A] uppercase font-bold">
                Preview Override: {previewPhase}
              </span>
            )}
          </div>
        )}

        {/* Expiry / Session Warning Banner */}
        {workspaceContext.brokerState === "TOKEN_EXPIRED" && (
          <div className="border-b border-[#E5484D]/40 bg-[#E5484D]/10 px-3 py-1.5 text-[11px] text-[#E5484D] flex items-center justify-between font-mono shrink-0">
            <div>
              <strong>KITE SESSION EXPIRED.</strong> Last update: {marketContext.last_tick_time || "—"}. Live
              analysis paused.
            </div>
            <button onClick={openSettingsConsole} className="underline text-red-200 hover:text-white font-bold">
              Open Settings Console
            </button>
          </div>
        )}

        {/* Main Workspace Frame: Sidebar + Content */}
        <div className="flex min-h-0 flex-1 bg-[#050607]">
          {/* Primary Sidebar Module Navigation (4 Primary Modules ONLY - Slim 200px Width) */}
          <aside
            id="workstation-sidebar"
            className={`${
              mobileOpen ? "block" : "hidden"
            } w-[200px] absolute z-40 h-full border-r border-[#191D23] bg-[#050607] px-1.5 py-2.5 lg:static lg:block overflow-y-auto shrink-0`}
          >
            <nav className="space-y-0.5 font-mono">
              {PRIMARY_MODULES.map((module) => {
                const Glyph = module.glyph;
                const isActive = !settingsOpen && activeModule === module.id;
                const labelText = module.label;

                return (
                  <button
                    key={module.id}
                    onClick={() => navigateModule(module.id)}
                    aria-current={isActive ? "page" : undefined}
                    aria-label={labelText}
                    className={`flex h-10 w-full items-center gap-2 rounded-[2px] border-l-2 px-2 text-left text-[11px] font-mono tracking-tight transition-colors whitespace-nowrap ${
                      isActive
                        ? "border-[#38BDF8] bg-[#12151A] text-[#E6E8EB] font-bold"
                        : "border-transparent text-[#707987] hover:bg-[#0E1013] hover:text-[#A5ABB4] font-medium"
                    }`}
                  >
                    <Glyph
                      size={15}
                      className={`shrink-0 ${isActive ? "text-[#38BDF8]" : "text-[#707987]"}`}
                    />
                    <span className="truncate">{labelText}</span>
                  </button>
                );
              })}
            </nav>
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
                    <button
                      onClick={() => navigateMarketSubTab("predictions")}
                      className={`relative h-full px-1 transition ${marketSubTab === "predictions"
                          ? "text-[#E6E8EB] font-bold after:absolute after:inset-x-0 after:bottom-0 after:h-[2px] after:bg-[#F59E0B]"
                          : "text-[#707987] hover:text-[#A5ABB4]"
                        }`}
                    >
                      PREDICTIONS
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
                  <CanonicalMarketIntelligenceWorkspace />
                ) : marketSubTab === "predictions" ? (
                  <PredictionChartView />
                ) : marketSubTab === "options" ? (
                  <CanonicalOptionsWorkspace
                    options={envelope.options}
                    candidateStrike={envelope.decision?.strike_candidates?.[0]}
                  />
                ) : marketSubTab === "metrics" ? (
                  <MarketPulseWorkspace />
                ) : (
                  <CanonicalMarketWorkspace />
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
