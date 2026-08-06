import React, { useEffect, useState } from "react";
import { Activity, BookOpen, Calendar, Newspaper, Radio, Sliders } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { LiveAssistantWorkspace, NewsUpdatesWorkspace, NiftyLiveWorkspace, PreMarketPlannerWorkspace, SettingsWorkspace, TodaysAnalysisWorkspace } from "../components/PhaseOneWorkspaces";
import { WorkstationTopBar } from "../components/WorkstationTopBar";

export const PRIMARY_WORKSPACES = [
  { id: "nifty-live", label: "NIFTY Live", icon: Radio },
  { id: "pre-market", label: "Pre-Market Planner", icon: Calendar },
  { id: "todays-analysis", label: "Today’s Analysis", icon: BookOpen },
  { id: "news-updates", label: "NEWS & UPDATES", icon: Newspaper },
  { id: "live-assistant", label: "Live Assistant", icon: Activity },
  { id: "settings", label: "Settings", icon: Sliders },
] as const;
type WorkspaceId = typeof PRIMARY_WORKSPACES[number]["id"];

const legacyRedirects: Record<string, WorkspaceId> = { home: "nifty-live", market: "nifty-live", tomorrow: "pre-market", market_story: "todays-analysis", journal: "live-assistant", account: "settings", system: "settings", trade_center: "nifty-live", portfolio: "nifty-live", execution: "nifty-live", performance: "nifty-live" };

export function DashboardLayout() {
  const { themeClasses, accentClasses, fontClasses } = useTheme();
  const { workspaceContext, marketContext } = useWorkstationState();
  const [active, setActive] = useState<WorkspaceId>(() => { const saved = localStorage.getItem("active_tab") || "nifty-live"; return legacyRedirects[saved] || (PRIMARY_WORKSPACES.some(x=>x.id===saved) ? saved as WorkspaceId : "nifty-live"); });
  const [mobile, setMobile] = useState(false);
  useEffect(()=>{ if(window.location.pathname.includes("/broker")||window.location.search.includes("login=")) setActive("settings"); },[]);
  const navigate=(id:WorkspaceId)=>{setActive(id);localStorage.setItem("active_tab",id);setMobile(false);};
  return <div id="dashboard-layout" className={`${themeClasses.bg} ${themeClasses.text} ${fontClasses.base} flex h-screen flex-col overflow-hidden`}>
    <WorkstationTopBar mobileOpen={mobile} onToggleMobile={()=>setMobile(!mobile)} onOpenSettings={()=>navigate("settings")}/>
    {workspaceContext.brokerState === "TOKEN_EXPIRED" && <div className="border-b border-rose-900 bg-rose-950/30 px-4 py-3 text-xs text-rose-300"><strong>KITE SESSION EXPIRED.</strong> Last successful update: {marketContext.last_tick_time || "Unavailable"}. Live analysis is paused. Open Settings to reconnect.</div>}
    {workspaceContext.marketState === "CLOSED" && <div className="border-b border-blue-900 bg-blue-950/20 px-4 py-2 text-xs text-blue-300">MARKET CLOSED · Showing only the final validated snapshot where available. Live confirmation language is disabled.</div>}
    <div className="flex min-h-0 flex-1"><aside className={`${mobile?"block":"hidden"} absolute z-40 h-full w-64 border-r border-neutral-800 bg-neutral-950 p-3 lg:static lg:block`}><nav className="space-y-1">{PRIMARY_WORKSPACES.map(item=><button key={item.id} onClick={()=>navigate(item.id)} className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-xs font-bold ${active===item.id?accentClasses.badge:"text-neutral-400 hover:bg-neutral-900"}`}><item.icon size={15}/>{item.label}</button>)}</nav><div className="mt-6 rounded-lg border border-neutral-800 p-3 text-[10px] text-neutral-500">No execution, paper portfolio, or order management is available.</div></aside>
      <main className="min-w-0 flex-1 overflow-y-auto p-4 sm:p-6">{active==="nifty-live"?<NiftyLiveWorkspace/>:active==="pre-market"?<PreMarketPlannerWorkspace/>:active==="todays-analysis"?<TodaysAnalysisWorkspace/>:active==="news-updates"?<NewsUpdatesWorkspace/>:active==="live-assistant"?<LiveAssistantWorkspace/>:<SettingsWorkspace/>}</main>
    </div>
  </div>;
}
export default DashboardLayout;
