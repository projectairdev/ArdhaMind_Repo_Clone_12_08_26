import React, { useEffect, useState } from "react";
import { Activity, BookOpen, Calendar, Compass, Layers, Newspaper, Radio, Sliders } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  NiftyLiveWorkspace,
  LiveAssistantWorkspace,
  TodaysAnalysisWorkspace,
  ForwardOutlookWorkspace,
  NewsUpdatesWorkspace,
  SettingsWorkspace
} from "../components/PhaseOneWorkspaces";
import { PreMarketPlannerWorkspace } from "../components/PreMarketPlannerWorkspace";
import { MarketPulseWorkspace } from "../components/MarketPulseWorkspace";
import { WorkstationTopBar } from "../components/WorkstationTopBar";

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
      { id: "todays-analysis", label: "Session Intelligence", icon: BookOpen },
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
  { id: "todays-analysis", label: "Session Intelligence", icon: BookOpen },
  { id: "forward-outlook", label: "Scenario Outlook", icon: Compass },
  { id: "pre-market-planner", label: "Pre-Market Intelligence", icon: Layers },
  { id: "news-updates", label: "Intelligence Feed", icon: Newspaper },
  { id: "settings", label: "System Control", icon: Sliders },
] as const;

type WorkspaceId = typeof PRIMARY_WORKSPACES[number]["id"];

const legacyRedirects: Record<string, WorkspaceId> = {
  home: "nifty-live",
  market: "nifty-live",
  "market-pulse": "market-pulse",
  "pre-market": "pre-market-planner",
  "pre-market-planner": "pre-market-planner",
  tomorrow: "pre-market-planner",
  "forward-outlook": "forward-outlook",
  market_story: "todays-analysis",
  journal: "live-assistant",
  account: "settings",
  system: "settings",
  trade_center: "nifty-live",
  portfolio: "nifty-live",
  execution: "nifty-live",
  performance: "nifty-live"
};

export function DashboardLayout() {
  const { themeClasses, accentClasses, fontClasses } = useTheme();
  const { workspaceContext, marketContext } = useWorkstationState();
  const [active, setActive] = useState<WorkspaceId>(() => {
    const saved = localStorage.getItem("active_tab") || "nifty-live";
    return legacyRedirects[saved] || (PRIMARY_WORKSPACES.some(x => x.id === saved) ? (saved as WorkspaceId) : "nifty-live");
  });
  const [mobile, setMobile] = useState(false);

  useEffect(() => {
    if (window.location.pathname.includes("/broker") || window.location.search.includes("login=")) {
      setActive("settings");
    }
  }, []);

  const navigate = (id: WorkspaceId) => {
    setActive(id);
    localStorage.setItem("active_tab", id);
    setMobile(false);
  };

  return (
    <div id="dashboard-layout" className={`${themeClasses.bg} ${themeClasses.text} ${fontClasses.base} flex h-screen flex-col overflow-hidden bg-[var(--air-bg)]`}>
      <WorkstationTopBar mobileOpen={mobile} onToggleMobile={() => setMobile(!mobile)} />
      {workspaceContext.brokerState === "TOKEN_EXPIRED" && (
        <div className="border-b border-rose-900 bg-rose-950/30 px-4 py-3 text-xs text-rose-300">
          <strong>KITE SESSION EXPIRED.</strong> Last successful update: {marketContext.last_tick_time || "Unavailable"}. Live analysis is paused. Open System Control to reconnect.
        </div>
      )}
      <div className="flex min-h-0 flex-1">
        <aside className={`${mobile ? "block" : "hidden"} absolute z-40 h-full w-60 border-r border-[var(--air-line)] bg-[var(--air-surface)] px-2.5 py-3 lg:static lg:block overflow-y-auto`}>
          <div className="space-y-4">
            {NAVIGATION_GROUPS.map(group => (
              <div key={group.category}>
                <div className="mb-1 px-2.5 text-[9px] font-bold tracking-[.18em] text-slate-500 uppercase">{group.category}</div>
                <nav className="space-y-0.5">
                  {group.items.map(item => (
                    <button
                      key={item.id}
                      onClick={() => navigate(item.id)}
                      aria-current={active === item.id ? "page" : undefined}
                      className={`group flex w-full items-center gap-2.5 rounded-md border-l-2 px-2.5 py-1.5 text-left text-[11px] font-semibold transition ${
                        active === item.id
                          ? `border-cyan-400 bg-cyan-950/20 ${accentClasses.text}`
                          : "border-transparent text-slate-500 hover:bg-slate-900/70 hover:text-slate-200"
                      }`}
                    >
                      <item.icon size={14} className={active === item.id ? "text-cyan-400" : "text-slate-600 group-hover:text-slate-400"} />
                      {item.label}
                    </button>
                  ))}
                </nav>
              </div>
            ))}
          </div>
        </aside>
        <main className="air-grid min-w-0 flex-1 overflow-y-auto p-3 sm:p-5 lg:p-6">
          {active === "nifty-live" ? (
            <NiftyLiveWorkspace />
          ) : active === "live-assistant" ? (
            <LiveAssistantWorkspace />
          ) : active === "todays-analysis" ? (
            <TodaysAnalysisWorkspace />
          ) : active === "forward-outlook" ? (
            <ForwardOutlookWorkspace />
          ) : active === "pre-market-planner" ? (
            <PreMarketPlannerWorkspace />
          ) : active === "market-pulse" ? (
            <MarketPulseWorkspace />
          ) : active === "news-updates" ? (
            <NewsUpdatesWorkspace />
          ) : (
            <SettingsWorkspace />
          )}
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;
