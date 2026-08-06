import React, { useEffect, useState } from "react";
import { Bell, Menu, Settings, X } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState, useBrokerStatus, useMarketData } from "../context/WorkstationStateContext";

function marketLabel(value: string) {
  const norm = (value || "").toUpperCase();
  return ({ PRE_OPEN: "PRE-OPEN", OPEN: "MARKET OPEN", CLOSED: "MARKET CLOSED", HOLIDAY: "TRADING HOLIDAY" } as Record<string, string>)[norm] || "INITIALIZING";
}

export function WorkstationTopBar({ mobileOpen, onToggleMobile, onOpenSettings }: { mobileOpen: boolean; onToggleMobile: () => void; onOpenSettings: () => void }) {
  const { accentClasses } = useTheme();
  const { connectionState, marketConnection, canonicalState, lastValidState } = useWorkstationState();
  const { data: broker } = useBrokerStatus();
  const { data: market } = useMarketData();

  const [clock, setClock] = useState("");
  const [notifications, setNotifications] = useState(false);
  useEffect(() => { const tick = () => setClock(new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(new Date()) + " IST"); tick(); const id = setInterval(tick, 1000); return () => clearInterval(id); }, []);

  const stateObj = canonicalState ?? lastValidState;
  const mStatus = stateObj?.market_session?.status || "closed";
  const marketStateStr = mStatus === "open" ? "OPEN" : mStatus === "holiday" ? "HOLIDAY" : "CLOSED";

  const kite = broker?.status === "session_expired" 
    ? "Kite Session Expired" 
    : broker?.status === "connected" 
      ? "Kite Connected" 
      : "Kite Disconnected";

  const feedHealth = stateObj?.market_feed_status?.status || "offline";
  const feedLatencyMs = stateObj?.data_quality?.market_data?.age_seconds ? stateObj.data_quality.market_data.age_seconds * 1000 : 0;

  const feed = marketStateStr === "CLOSED" 
    ? "Market Closed" 
    : marketConnection === "DISCONNECTED"
      ? "Lost"
      : marketConnection === "CONNECTING"
        ? "Initializing"
        : feedHealth === "healthy" 
          ? "Live" 
          : feedHealth === "degraded" 
            ? `Delayed${feedLatencyMs ? ` ${Math.ceil(feedLatencyMs / 1000)}s` : ""}` 
            : "Initializing";

  return <><header data-testid="phase1-top-bar" className="flex min-h-16 items-center gap-3 border-b border-neutral-800 bg-neutral-950/90 px-4"><button aria-label="Toggle navigation" className="lg:hidden" onClick={onToggleMobile}>{mobileOpen ? <X /> : <Menu />}</button><div className="mr-auto"><div className="font-black text-white">AIR <span className={accentClasses.text}>ArdhaMind</span></div><div className="text-[9px] uppercase tracking-widest text-neutral-500">Live intelligence · Read only</div></div><div className="hidden text-xs text-neutral-300 md:block">{marketLabel(marketStateStr)} · {clock}</div><div className="hidden text-xs text-neutral-400 lg:block">{kite}</div><div className="hidden text-xs text-neutral-400 lg:block">Market Feed · {feed}</div><button aria-label="Notifications" onClick={() => setNotifications(!notifications)} className="rounded border border-neutral-800 p-2"><Bell size={15} /></button><button aria-label="Settings" onClick={onOpenSettings} className="rounded border border-neutral-800 p-2"><Settings size={15} /></button></header>{notifications && <div className="absolute right-16 top-16 z-50 w-72 rounded-lg border border-neutral-800 bg-neutral-950 p-4 text-xs text-neutral-400 shadow-xl">No unread intelligence alerts.</div>}</>;
}

