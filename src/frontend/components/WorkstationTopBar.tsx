import React, { useEffect, useState } from "react";
import { Bell, Menu, Settings, X } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";

function marketLabel(value: string) {
  return ({ PRE_OPEN: "PRE-OPEN", OPEN: "MARKET OPEN", CLOSED: "MARKET CLOSED", HOLIDAY: "TRADING HOLIDAY" } as Record<string, string>)[value] || "INITIALIZING";
}

export function WorkstationTopBar({ mobileOpen, onToggleMobile, onOpenSettings }: { mobileOpen: boolean; onToggleMobile: () => void; onOpenSettings: () => void }) {
  const { accentClasses } = useTheme();
  const { workspaceContext, marketContext, connectionState } = useWorkstationState();
  const [clock, setClock] = useState("");
  const [notifications, setNotifications] = useState(false);
  useEffect(() => { const tick = () => setClock(new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(new Date()) + " IST"); tick(); const id = setInterval(tick, 1000); return () => clearInterval(id); }, []);
  const kite = workspaceContext.brokerState === "TOKEN_EXPIRED" ? "Kite Session Expired" : workspaceContext.brokerState === "CONNECTED" ? "Kite Connected" : "Kite Disconnected";
  const feed = workspaceContext.marketState === "CLOSED" ? "Market Closed" : connectionState === "CONNECTED" && marketContext.feed_health === "HEALTHY" ? "Live" : connectionState === "CONNECTED" && marketContext.feed_health === "DEGRADED" ? `Delayed${marketContext.feed_latency_ms ? ` ${Math.ceil(marketContext.feed_latency_ms / 1000)}s` : ""}` : connectionState === "DISCONNECTED" ? "Lost" : "Initializing";
  return <><header data-testid="phase1-top-bar" className="flex min-h-16 items-center gap-3 border-b border-neutral-800 bg-neutral-950/90 px-4"><button aria-label="Toggle navigation" className="lg:hidden" onClick={onToggleMobile}>{mobileOpen ? <X /> : <Menu />}</button><div className="mr-auto"><div className="font-black text-white">AIR <span className={accentClasses.text}>ArdhaMind</span></div><div className="text-[9px] uppercase tracking-widest text-neutral-500">Live intelligence · Read only</div></div><div className="hidden text-xs text-neutral-300 md:block">{marketLabel(workspaceContext.marketState)} · {clock}</div><div className="hidden text-xs text-neutral-400 lg:block">{kite}</div><div className="hidden text-xs text-neutral-400 lg:block">Market Feed · {feed}</div><button aria-label="Notifications" onClick={() => setNotifications(!notifications)} className="rounded border border-neutral-800 p-2"><Bell size={15} /></button><button aria-label="Settings" onClick={onOpenSettings} className="rounded border border-neutral-800 p-2"><Settings size={15} /></button></header>{notifications && <div className="absolute right-16 top-16 z-50 w-72 rounded-lg border border-neutral-800 bg-neutral-950 p-4 text-xs text-neutral-400 shadow-xl">No unread intelligence alerts.</div>}</>;
}

