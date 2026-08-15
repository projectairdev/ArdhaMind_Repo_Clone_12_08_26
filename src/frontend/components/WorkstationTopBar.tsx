import React, { useEffect, useState } from "react";
import { AlertTriangle, Bell, CheckCircle2, Info, Menu, RefreshCw, X, Sliders, Activity, Radio, Shield } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState, useBrokerStatus } from "../context/WorkstationStateContext";
import { mapTraderEnum, getTraderMarketStatus } from "../utils/traderTerminology";
import { formatTimestampIST } from "../utils/timeFormatting";

function marketLabel(value: string, observedAt?: string | null) {
  return getTraderMarketStatus(value, observedAt);
}

type ToastState = { kind: "info" | "success" | "error"; message: string };
type OperationalAlert = { id: string; kind: "warning" | "error"; title: string; detail: string; timestamp: string };

interface WorkstationTopBarProps {
  mobileOpen: boolean;
  onToggleMobile: () => void;
  onOpenSettings?: () => void;
  onOpenAssistant?: () => void;
}

export function WorkstationTopBar({
  mobileOpen,
  onToggleMobile,
  onOpenSettings,
  onOpenAssistant
}: WorkstationTopBarProps) {
  const { accentClasses } = useTheme();
  const { marketConnection, canonicalState, lastValidState, syncBroker, syncing, lastSyncTime } = useWorkstationState();
  const { data: broker } = useBrokerStatus();
  const [clock, setClock] = useState("");
  const [notifications, setNotifications] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);

  useEffect(() => {
    if ((import.meta as any).env?.VITE_STAGING_MODE === "true") {
      document.title = "[STAGING] AIR ArdhaMind";
    }
    const tick = () =>
      setClock(
        new Intl.DateTimeFormat("en-IN", {
          timeZone: "Asia/Kolkata",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false
        }).format(new Date()) + " IST"
      );
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const stateObj = canonicalState ?? lastValidState;
  const mStatus = stateObj?.market_session?.status || "closed";
  const marketStateStr = mStatus === "open" ? "OPEN" : mStatus === "holiday" ? "HOLIDAY" : mStatus === "pre_open" ? "PRE_OPEN" : "CLOSED";
  const isClosedSession = marketStateStr === "CLOSED" || marketStateStr === "HOLIDAY" || Boolean(stateObj?.market_session?.is_closed);
  const isAuthValid = broker?.status === "connected" || broker?.session_valid === true;
  const isAuthRequired = broker?.status === "session_expired" || broker?.status === "token_expired" || broker?.reconnect_required === true;
  const kite = isAuthRequired ? "Auth Required" : isAuthValid ? (isClosedSession ? "Authenticated" : "Connected") : "Disconnected";

  const feedHealth = stateObj?.market_feed_status?.status || "offline";
  const feedLatencyMs = stateObj?.data_quality?.market_data?.age_seconds ? stateObj.data_quality.market_data.age_seconds * 1000 : 0;
  const coreFeedReady = Boolean(stateObj?.market_data?.current_spot || stateObj?.market_data?.status === "ready" || feedHealth === "healthy" || feedHealth === "ready");
  const feed = isClosedSession ? "Idle" : marketConnection === "DISCONNECTED" ? "Offline" : marketConnection === "CONNECTING" ? "Reconnecting" : coreFeedReady ? "LIVE" : feedHealth === "degraded" ? `Delayed${feedLatencyMs ? ` ${Math.ceil(feedLatencyMs / 1000)}s` : ""}` : "Degraded";

  const providerHealth = { ...(stateObj?.news_intelligence?.provider_health || {}), ...(stateObj?.macro_intelligence?.provider_health || {}) } as Record<string, any>;
  const degradedProviders = Object.entries(providerHealth).filter(([, value]) => !["ready", "disabled", "available"].includes(String(value?.status || "").toLowerCase()));
  const notificationTime = stateObj?.generated_at ? formatTimestampIST(stateObj.generated_at) : (lastSyncTime || "Current state");
  const alerts: OperationalAlert[] = [];
  if (degradedProviders.length) alerts.push({ id: "provider-summary", kind: "warning", title: `${degradedProviders.length} provider${degradedProviders.length === 1 ? "" : "s"} degraded`, detail: degradedProviders.map(([name, value]) => String(value?.provider_name || name)).join(", "), timestamp: notificationTime });
  if (broker?.status !== "connected") alerts.unshift({ id: "kite", kind: "warning", title: "Kite connection", detail: kite, timestamp: notificationTime });
  if (!isClosedSession && !["healthy", "ready"].includes(String(feedHealth).toLowerCase())) alerts.unshift({ id: "feed", kind: "error", title: "Market feed", detail: feed, timestamp: notificationTime });
  const freshness = String(stateObj?.data_quality?.market_data?.freshness_status || "UNAVAILABLE").toUpperCase();
  if (["STALE", "BLOCKED", "UNAVAILABLE"].includes(freshness)) alerts.push({ id: "freshness", kind: "warning", title: "Market-data freshness", detail: mapTraderEnum(freshness), timestamp: notificationTime });

  const showToast = (next: ToastState) => setToast(current => current?.kind === next.kind && current.message === next.message ? current : next);
  const refresh = async () => {
    if (syncing || refreshing) return;
    setRefreshing(true);
    showToast({ kind: "info", message: "Checking canonical stream…" });
    try {
      await syncBroker(true);
      const time = new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(new Date());
      showToast(degradedProviders.length ? { kind: "info", message: `Partial canonical view · ${degradedProviders.length} provider${degradedProviders.length === 1 ? "" : "s"} degraded` } : { kind: "success", message: `Canonical stream current · ${time} IST` });
    } catch { showToast({ kind: "error", message: "Refresh failed · existing snapshot preserved" }); }
    finally { setRefreshing(false); }
  };
  useEffect(() => { if (!toast) return; const id = setTimeout(() => setToast(null), toast.kind === "error" ? 4500 : toast.kind === "success" ? 3200 : 2800); return () => clearTimeout(id); }, [toast]);

  const statusDot = (active: boolean, staticState = false) => (
    <span aria-hidden className={`h-2 w-2 rounded-full ${active ? "bg-emerald-400" : "bg-slate-500"} ${active && !staticState ? "motion-safe:animate-pulse" : ""}`} />
  );

  return (
    <>
      <header data-testid="phase1-top-bar" className="relative z-50 flex min-h-14 items-center justify-between gap-2 border-b border-[var(--air-line)] bg-[var(--air-overlay)] px-3 backdrop-blur-md sm:px-4">
        {/* Left Brand & Mobile Nav */}
        <div className="flex items-center gap-3">
          <button aria-label="Toggle navigation" title="Toggle navigation" className="rounded p-1.5 text-slate-400 hover:bg-slate-900 lg:hidden" onClick={onToggleMobile}>
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <div className="truncate text-sm font-extrabold tracking-tight text-white flex items-center gap-1.5">
            <span>AIR <span className={accentClasses.text}>ArdhaMind</span></span>
            {(import.meta as any).env?.VITE_STAGING_MODE === "true" && (
              <span className="rounded bg-amber-500/20 px-1.5 py-0.5 text-[9px] font-mono font-bold tracking-wider text-amber-400 border border-amber-500/40">
                STAGING
              </span>
            )}
          </div>
        </div>

        {/* Center/Right Global Status & Primary Actions Bar */}
        {/* Exactly: Market Status | Broker Status | Assistant | Settings */}
        <div className="flex items-center gap-2 font-mono text-xs">
          {/* 1. Market Status */}
          <div data-market-session-status className="flex items-center gap-1.5 rounded-lg bg-slate-950 px-2.5 py-1 border border-slate-800 text-[10px] text-slate-300">
            {statusDot(!isClosedSession, isClosedSession)}
            <span>Market: <strong className="text-white uppercase">{marketLabel(mStatus, stateObj?.market_session?.observed_at)}</strong></span>
          </div>

          {/* 2. Broker Status */}
          <div className="hidden sm:flex items-center gap-1.5 rounded-lg bg-slate-950 px-2.5 py-1 border border-slate-800 text-[10px] text-slate-300">
            {statusDot(isAuthValid)}
            <span>Broker: <strong className={isAuthValid ? "text-emerald-400" : "text-amber-400"}>{kite}</strong></span>
          </div>

          {/* 3. Assistant Trigger */}
          <button
            onClick={onOpenAssistant}
            title="Open Intraday Decision Assistant"
            className="flex items-center gap-1.5 rounded-lg bg-indigo-950/60 hover:bg-indigo-900/80 px-2.5 py-1 border border-indigo-800 text-[10px] font-semibold text-indigo-300 transition"
          >
            <Activity size={13} className="text-indigo-400" />
            <span className="hidden md:inline font-sans">Assistant</span>
          </button>

          {/* 4. Settings Trigger */}
          <button
            onClick={onOpenSettings}
            title="System Control & Settings"
            className="flex items-center gap-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 px-2.5 py-1 border border-slate-700 text-[10px] font-semibold text-slate-200 transition"
          >
            <Sliders size={13} className="text-cyan-400" />
            <span className="hidden md:inline font-sans">Settings</span>
          </button>

          {/* Stream Refresh & Operational Bell */}
          <button
            aria-label="Refresh canonical workstation"
            onClick={refresh}
            disabled={syncing || refreshing}
            title={lastSyncTime ? `Last canonical update ${lastSyncTime}` : "Check canonical stream"}
            className="rounded-lg border border-slate-800 bg-slate-950 p-1.5 text-slate-400 hover:border-cyan-800 hover:text-cyan-300 disabled:opacity-50"
          >
            <RefreshCw size={13} className={syncing || refreshing ? "animate-spin" : ""} />
          </button>

          <button
            aria-label={`Notifications${alerts.length ? `, ${alerts.length} active` : ""}`}
            title="Operational notifications"
            aria-expanded={notifications}
            onClick={() => setNotifications(!notifications)}
            className="relative rounded-lg border border-slate-800 bg-slate-950 p-1.5 text-slate-400 hover:border-cyan-800 hover:text-cyan-300"
          >
            <Bell size={13} />
            {alerts.length > 0 && (
              <span className="absolute -right-1 -top-1 min-w-3.5 rounded-full bg-amber-500 px-1 text-center text-[8px] font-bold text-slate-950">
                {alerts.length}
              </span>
            )}
          </button>
        </div>
      </header>

      {notifications && (
        <aside role="dialog" aria-label="Operational notifications" className="absolute right-3 top-16 z-50 w-[min(24rem,calc(100vw-1.5rem))] overflow-hidden rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-overlay)] shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-[var(--air-line)] px-4 py-3">
            <div>
              <div className="text-xs font-bold text-white">Operational notifications</div>
              <div className="text-[9px] text-slate-500">Current canonical states · deduplicated</div>
            </div>
            <button aria-label="Close notifications" title="Close notifications" onClick={() => setNotifications(false)} className="text-slate-500 hover:text-white">
              <X size={15} />
            </button>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {alerts.length ? (
              alerts.map(alert => (
                <div key={alert.id} className="flex gap-3 border-b border-[var(--air-line)] px-4 py-3 last:border-0">
                  {alert.kind === "error" ? <AlertTriangle size={14} className="mt-0.5 shrink-0 text-rose-400" /> : <Info size={14} className="mt-0.5 shrink-0 text-amber-400" />}
                  <div className="min-w-0">
                    <div className="text-[10px] font-bold text-slate-200">{alert.title}</div>
                    <div className="mt-0.5 break-words text-[9px] text-slate-500">{alert.detail}</div>
                    <time className="mt-1 block truncate text-[8px] text-slate-600">{alert.timestamp}</time>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex gap-2 px-4 py-5 text-[10px] text-slate-400">
                <CheckCircle2 size={14} className="text-emerald-400" />
                No active operational alerts.
              </div>
            )}
          </div>
        </aside>
      )}

      {toast && (
        <div role="status" aria-live="polite" className={`fixed bottom-5 right-5 z-[60] max-w-sm rounded-lg border px-4 py-3 text-xs shadow-xl backdrop-blur ${toast.kind === "error" ? "border-rose-800 bg-rose-950/90 text-rose-200" : toast.kind === "success" ? "border-emerald-800 bg-emerald-950/90 text-emerald-200" : "border-cyan-800 bg-cyan-950/90 text-cyan-200"}`}>
          {toast.message}
        </div>
      )}
    </>
  );
}
