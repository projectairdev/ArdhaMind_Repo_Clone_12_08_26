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
  return <div id="dashboard-layout" className={`${themeClasses.bg} ${themeClasses.text} ${fontClasses.base} flex h-screen flex-col overflow-hidden bg-[var(--air-bg)]`}>
    <WorkstationTopBar mobileOpen={mobile} onToggleMobile={()=>setMobile(!mobile)} onOpenSettings={()=>navigate("settings")}/>
    {workspaceContext.brokerState === "TOKEN_EXPIRED" && <div className="border-b border-rose-900 bg-rose-950/30 px-4 py-3 text-xs text-rose-300"><strong>KITE SESSION EXPIRED.</strong> Last successful update: {marketContext.last_tick_time || "Unavailable"}. Live analysis is paused. Open Settings to reconnect.</div>}
    {workspaceContext.marketState === "CLOSED" && <div className="border-b border-blue-900 bg-blue-950/20 px-4 py-2 text-xs text-blue-300">MARKET CLOSED · Showing only the final validated snapshot where available. Live confirmation language is disabled.</div>}
    <div className="flex min-h-0 flex-1"><aside className={`${mobile?"block":"hidden"} absolute z-40 h-full w-60 border-r border-[var(--air-line)] bg-[var(--air-surface)] px-2.5 py-3 lg:static lg:block`}><div className="mb-2 px-2 text-[8px] font-semibold tracking-[.18em] text-slate-600">WORKSPACES</div><nav className="space-y-0.5">{PRIMARY_WORKSPACES.map(item=><button key={item.id} onClick={()=>navigate(item.id)} aria-current={active===item.id?"page":undefined} className={`group flex w-full items-center gap-2.5 rounded-md border-l-2 px-2.5 py-2 text-left text-[11px] font-semibold transition ${active===item.id?`border-cyan-400 bg-cyan-950/20 ${accentClasses.text}`:"border-transparent text-slate-500 hover:bg-slate-900/70 hover:text-slate-200"}`}><item.icon size={14} className={active===item.id?"text-cyan-400":"text-slate-600 group-hover:text-slate-400"}/>{item.label}</button>)}</nav><div className="mt-5 border-t border-[var(--air-line)] px-2 pt-3 text-[9px] leading-relaxed text-slate-600"><span className="font-semibold text-slate-500">READ ONLY</span><br/>Decision intelligence only. Execution and order management are unavailable.</div></aside>
      <main className="air-grid min-w-0 flex-1 overflow-y-auto p-3 sm:p-5 lg:p-6">{active==="nifty-live"?<NiftyLiveWorkspace/>:active==="pre-market"?<PreMarketPlannerWorkspace/>:active==="todays-analysis"?<TodaysAnalysisWorkspace/>:active==="news-updates"?<NewsUpdatesWorkspace/>:active==="live-assistant"?<LiveAssistantWorkspace/>:<SettingsWorkspace/>}</main>
    </div>
  </div>;
}
export default DashboardLayout;
