import React, { useEffect, useState } from "react";
import { AlertTriangle, Bell, CheckCircle2, Info, Menu, RefreshCw, Settings, X } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState, useBrokerStatus, useMarketData } from "../context/WorkstationStateContext";

function marketLabel(value: string) {
  const norm = (value || "").toUpperCase();
  return ({ PRE_OPEN: "PRE-OPEN", OPEN: "MARKET OPEN", CLOSED: "MARKET CLOSED", HOLIDAY: "TRADING HOLIDAY" } as Record<string, string>)[norm] || "INITIALIZING";
}

export function WorkstationTopBar({ mobileOpen, onToggleMobile, onOpenSettings }: { mobileOpen: boolean; onToggleMobile: () => void; onOpenSettings: () => void }) {
  const { accentClasses } = useTheme();
  const { marketConnection, canonicalState, lastValidState, syncBroker, syncing, lastSyncTime } = useWorkstationState();
  const { data: broker } = useBrokerStatus();
  const { data: market } = useMarketData();

  const [clock, setClock] = useState("");
  const [notifications, setNotifications] = useState(false);
  const [toast, setToast] = useState<{ kind: "info" | "success" | "error"; message: string } | null>(null);
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

  const isClosedSession = marketStateStr === "CLOSED" || marketStateStr === "HOLIDAY" || Boolean(stateObj?.market_session?.is_closed);

  const feed = isClosedSession
    ? "Market Closed" 
    : marketConnection === "DISCONNECTED"
      ? "Offline"
      : marketConnection === "CONNECTING"
        ? "Connecting"
        : feedHealth === "healthy" 
          ? "Live" 
          : feedHealth === "degraded" 
            ? `Delayed${feedLatencyMs ? ` ${Math.ceil(feedLatencyMs / 1000)}s` : ""}` 
            : "Market Closed";

  const providerHealth = { ...(stateObj?.news_intelligence?.provider_health || {}), ...(stateObj?.macro_intelligence?.provider_health || {}) } as Record<string, any>;
  const alerts = Object.entries(providerHealth).filter(([, value]) => !["ready", "disabled", "available"].includes(String(value?.status || "").toLowerCase())).map(([name, value]) => ({ id: `provider-${name}`, kind: "warning", title: String(value?.provider_name || name), detail: String(value?.failure_detail || value?.operational_error_reason || value?.status || "Provider degraded") }));
  if (broker?.status !== "connected") alerts.unshift({ id: "kite", kind: "warning", title: "Kite connection", detail: kite });
  if (!isClosedSession && !["healthy", "ready"].includes(String(feedHealth).toLowerCase())) alerts.unshift({ id: "feed", kind: "error", title: "Market feed", detail: feed });
  const freshness = String(stateObj?.data_quality?.market_data?.freshness_status || "UNAVAILABLE").toUpperCase();
  if (["STALE", "BLOCKED", "UNAVAILABLE"].includes(freshness)) alerts.push({ id: "freshness", kind: "warning", title: "Market-data freshness", detail: freshness });

  const refresh = async () => {
    if (syncing) return;
    setToast({ kind: "info", message: "Canonical refresh started" });
    try { await syncBroker(true); setToast({ kind: "success", message: "Canonical workstation refreshed" }); }
    catch { setToast({ kind: "error", message: "Refresh failed — current validated snapshot retained" }); }
  };
  useEffect(() => { if (!toast || toast.kind === "error") return; const id = setTimeout(() => setToast(null), toast.kind === "success" ? 3200 : 2200); return () => clearTimeout(id); }, [toast]);

  const statusDot = (active: boolean, staticState = false) => <span aria-hidden className={`h-1.5 w-1.5 rounded-full ${active ? "bg-emerald-400" : "bg-slate-600"} ${active && !staticState ? "motion-safe:animate-pulse" : ""}`}/>;
  return <><header data-testid="phase1-top-bar" className="relative z-50 flex min-h-14 items-center gap-2 border-b border-[var(--air-line)] bg-[var(--air-overlay)] px-3 backdrop-blur-md sm:px-4"><button aria-label="Toggle navigation" className="rounded p-1.5 text-slate-400 hover:bg-slate-900 lg:hidden" onClick={onToggleMobile}>{mobileOpen ? <X size={18}/> : <Menu size={18}/>}</button><div className="mr-auto min-w-0"><div className="truncate text-sm font-extrabold tracking-tight text-white">AIR <span className={accentClasses.text}>ArdhaMind</span></div><div className="text-[8px] font-medium tracking-[.16em] text-slate-500">NIFTY INTELLIGENCE · READ ONLY</div></div><div className="hidden items-center gap-2 text-[10px] text-slate-300 md:flex">{statusDot(!isClosedSession, isClosedSession)}<span>{marketLabel(marketStateStr)}</span><span className="text-slate-600">|</span><time className="air-data">{clock}</time></div><div className="hidden items-center gap-1.5 text-[10px] text-slate-400 lg:flex">{statusDot(broker?.status === "connected")}<span>{kite}</span></div><div className="hidden items-center gap-1.5 text-[10px] text-slate-400 xl:flex">{statusDot(!isClosedSession && feed === "Live", isClosedSession)}<span>Market Feed {feed}</span><span className="text-slate-600">·</span><span>{freshness.replaceAll("_", " ")}</span></div><button aria-label="Refresh canonical workstation" onClick={refresh} disabled={syncing} title={lastSyncTime ? `Last refresh ${lastSyncTime}` : "Refresh canonical workstation"} className="rounded border border-[var(--air-line)] p-2 text-slate-400 hover:border-cyan-800 hover:text-cyan-300 disabled:opacity-50"><RefreshCw size={14} className={syncing ? "animate-spin" : ""}/></button><button aria-label={`Notifications${alerts.length ? `, ${alerts.length} active` : ""}`} aria-expanded={notifications} onClick={() => setNotifications(!notifications)} className="relative rounded border border-[var(--air-line)] p-2 text-slate-400 hover:border-cyan-800 hover:text-cyan-300"><Bell size={14}/>{alerts.length > 0 && <span className="absolute -right-1 -top-1 min-w-4 rounded-full bg-amber-500 px-1 text-center text-[8px] font-bold text-slate-950">{alerts.length}</span>}</button><button aria-label="Settings" onClick={onOpenSettings} className="rounded border border-[var(--air-line)] p-2 text-slate-400 hover:border-cyan-800 hover:text-cyan-300"><Settings size={14}/></button></header>{notifications && <aside role="dialog" aria-label="Operational notifications" className="absolute right-3 top-16 z-50 w-[min(24rem,calc(100vw-1.5rem))] overflow-hidden rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-overlay)] shadow-2xl backdrop-blur-xl"><div className="flex items-center justify-between border-b border-[var(--air-line)] px-4 py-3"><div><div className="text-xs font-bold text-white">Operational notifications</div><div className="text-[9px] text-slate-500">Current canonical states · deduplicated</div></div><button aria-label="Close notifications" onClick={() => setNotifications(false)} className="text-slate-500 hover:text-white"><X size={15}/></button></div><div className="max-h-80 overflow-y-auto">{alerts.length ? alerts.map(alert => <div key={alert.id} className="flex gap-3 border-b border-[var(--air-line)] px-4 py-3 last:border-0">{alert.kind === "error" ? <AlertTriangle size={14} className="mt-0.5 text-rose-400"/> : <Info size={14} className="mt-0.5 text-amber-400"/>}<div><div className="text-[10px] font-bold text-slate-200">{alert.title}</div><div className="mt-0.5 text-[9px] text-slate-500">{alert.detail}</div></div></div>) : <div className="flex gap-2 px-4 py-5 text-[10px] text-slate-400"><CheckCircle2 size={14} className="text-emerald-400"/>No active operational alerts.</div>}</div></aside>}{toast && <div role="status" className={`fixed bottom-5 right-5 z-[60] max-w-sm rounded-lg border px-4 py-3 text-xs shadow-xl backdrop-blur ${toast.kind === "error" ? "border-rose-800 bg-rose-950/90 text-rose-200" : toast.kind === "success" ? "border-emerald-800 bg-emerald-950/90 text-emerald-200" : "border-cyan-800 bg-cyan-950/90 text-cyan-200"}`}>{toast.message}</div>}</>;
}
