import React, { useState } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  AlertCircle,
  BookOpen,
  Clock,
  Activity,
  Layers,
  Calendar,
  Briefcase,
  Search,
  RefreshCw,
  Info
} from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  stripHtml,
  formatNumber,
  formatDate,
  formatDateTimeIST
} from "../utils/safeHelpers";
import { SemanticBadge } from "./intelligence/CanonicalPresentation";

export function NewsIntelligence() {
  const { canonicalState, lastValidState, syncing: loading, diagnosticsError } = useWorkstationState();
  const [activeTab, setActiveTab] = useState<"live" | "impact" | "events" | "corporate" | "watchlist">("live");
  const [watchQuery, setWatchQuery] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState<string | null>(null);
  const [eventWindow, setEventWindow] = useState<"TODAY" | "TOMORROW" | "THIS WEEK">("TODAY");
  const [eventFilter, setEventFilter] = useState("ALL");

  const state = canonicalState ?? lastValidState;
  const news = state?.news_intelligence;

  // Manual Refresh rate limiter & polling
  const handleManualRefresh = async () => {
    if (refreshing) return;
    setRefreshing(true);
    setRefreshStatus("Initiating refresh...");
    try {
      const res = await fetch("/api/news/refresh", { method: "POST" });
      const body = await res.json();
      if (res.status === 429) {
        setRefreshStatus("Rate limit: max once per minute.");
        setRefreshing(false);
        return;
      }
      if (!res.ok) {
        setRefreshStatus(`Failed: ${body.error || "Unknown error"}`);
        setRefreshing(false);
        return;
      }
      setRefreshStatus("Refresh running in background...");

      // Poll status
      const interval = setInterval(async () => {
        try {
          const statusRes = await fetch("/api/news/refresh/status");
          const statusData = await statusRes.json();
          if (statusData.status === "completed") {
            setRefreshStatus("Refresh completed!");
            setRefreshing(false);
            clearInterval(interval);
          } else if (statusData.status === "failed") {
            setRefreshStatus(`Refresh failed: ${statusData.error}`);
            setRefreshing(false);
            clearInterval(interval);
          }
        } catch {
          setRefreshStatus("Polling failed.");
          setRefreshing(false);
          clearInterval(interval);
        }
      }, 2000);
    } catch (err: any) {
      setRefreshStatus(`Error: ${err.message}`);
      setRefreshing(false);
    }
  };

  if (loading && !news) {
    return (
      <div id="news-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-32 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (!news) {
    return (
      <div id="news-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold">News Intelligence Offline</h3>
        </div>
        <p className="text-xs text-slate-400">{diagnosticsError || "No canonical news snapshot is available."}</p>
        <button onClick={() => window.location.reload()} className="px-3 py-1.5 bg-slate-900 text-xs text-white border border-slate-800 rounded hover:bg-slate-800">
          Reconnect
        </button>
      </div>
    );
  }

  const items = safeArray(news.items) as any[];
  const clusters = (safeArray(news.event_clusters) as any[]).sort((a, b) => safeNumber(b.priority_score) - safeNumber(a.priority_score));
  const liveItems = [...items].sort((a, b) => safeNumber(a.age_seconds, Number.MAX_SAFE_INTEGER) - safeNumber(b.age_seconds, Number.MAX_SAFE_INTEGER) || safeNumber(b.nifty_relevance_score) - safeNumber(a.nifty_relevance_score));
  const events = safeArray(state?.macro_intelligence?.economic_events) as any[];
  const istDateKey = (value: string | Date) => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(value));
  const todayKey = istDateKey(new Date());
  const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowKey = istDateKey(tomorrow);
  const weekEnd = new Date(); weekEnd.setDate(weekEnd.getDate() + 7);
  const filteredEvents = events.filter(event => {
    const eventDate = new Date(event.scheduled_at_ist || event.scheduled_at);
    const key = istDateKey(eventDate);
    const inWindow = eventWindow === "TODAY" ? key === todayKey : eventWindow === "TOMORROW" ? key === tomorrowKey : eventDate >= new Date(`${todayKey}T00:00:00+05:30`) && eventDate <= weekEnd;
    const region = safeString(event.region).toUpperCase();
    const impact = safeString(event.impact_level).toUpperCase();
    const matches = eventFilter === "ALL" || eventFilter === region || (eventFilter === "HIGH IMPACT" && ["HIGH", "CRITICAL"].includes(impact)) || (eventFilter === "NIFTY RELEVANT" && safeNumber(event.nifty_relevance) >= 7);
    return inWindow && matches;
  });
  const newsCorporates = safeArray(news.corporate_items) as any[];
  const actionCorporates = (safeArray(state?.macro_intelligence?.corporate_actions) as any[]).map(action => ({
    id: action.id,
    company_symbol: action.symbol,
    headline: `${safeString(action.company_name || action.symbol)} — ${safeString(action.action_type)}`,
    description: action.details,
    published_at: action.ex_date,
    source_name: action.source_name,
    expected_direction: "uncertain",
  }));
  const officialCorporates = (safeArray(state?.macro_intelligence?.official_india_events) as any[])
    .filter(event => ["CORPORATE_ANNOUNCEMENT", "EARNINGS", "BOARD_MEETING"].includes(safeString(event.event_category).toUpperCase()))
    .map(event => ({
      id: event.id,
      company_symbol: event.symbol,
      headline: event.headline,
      description: event.description,
      published_at: event.published_at || event.effective_date,
      source_name: event.source_name,
      expected_direction: "uncertain",
    }));
  const corporates = [...officialCorporates, ...actionCorporates, ...newsCorporates]
    .filter((item, index, all) => all.findIndex(other => safeString(other.id) === safeString(item.id)) === index);
  const degradedProviders = Object.values(news.provider_health || {}).filter((health: any) => !["ready", "disabled"].includes(safeString(health.status).toLowerCase())) as any[];

  // Filter watchlist items
  const watchlistFiltered = items.filter(item => {
    const q = watchQuery.toLowerCase().trim();
    if (!q) return safeArray(item.affected_symbols).length > 0;
    return (
      safeString(item.headline).toLowerCase().includes(q) ||
      safeString(item.summary_snippet).toLowerCase().includes(q) ||
      safeArray(item.affected_symbols).some(sym => safeString(sym).toLowerCase().includes(q)) ||
      safeArray(item.affected_channels).some(channel => safeString(channel).toLowerCase().includes(q)) ||
      safeString(item.discovery_stream).toLowerCase().includes(q) ||
      safeString(item.category).toLowerCase().includes(q)
    );
  });

  const getDirectionBadge = (dir: string) => {
    const d = safeString(dir).toUpperCase();
    if (d === "POSITIVE") return <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">POSITIVE</span>;
    if (d === "NEGATIVE") return <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold rounded bg-rose-950/60 text-rose-400 border border-rose-800/60">NEGATIVE</span>;
    if (d === "MIXED") return <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold rounded bg-amber-950/60 text-amber-400 border border-amber-800/60">MIXED</span>;
    return <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold rounded bg-slate-800 text-slate-400 border border-slate-700">UNCERTAIN</span>;
  };

  return (
    <div id="news-intelligence" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6">
      {/* Title & Stats */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <BookOpen size={18} className="text-emerald-400" />
          <h3 className="font-bold text-white text-base">Operational News Hub</h3>
        </div>

        {/* Actions & Health Status */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1 bg-slate-900 hover:bg-slate-800 text-xs text-white border border-slate-800 rounded transition disabled:opacity-50"
          >
            <RefreshCw size={12} className={refreshing ? "animate-spin" : ""} />
            <span>{refreshing ? "Refreshing..." : "Manual Fetch"}</span>
          </button>
          {refreshStatus && (
            <span className="text-[10px] font-mono text-slate-400 max-w-[150px] truncate">{refreshStatus}</span>
          )}
          <div className="flex items-center gap-1.5"><SemanticBadge value={news.coverage_status} kind="readiness"/><SemanticBadge value={news.freshness} kind="freshness"/></div>
        </div>
      </div>

      {degradedProviders.length > 0 && <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-3 text-xs text-amber-300">Partial provider coverage: {degradedProviders.map(p => `${safeString(p.provider_name)} (${safeString(p.operational_error_reason || p.status)})`).join(" · ")}. Healthy-provider items remain available below.</div>}

      {/* Tabs list */}
      <div className="flex flex-wrap gap-1 border-b border-slate-900 pb-1">
        <button
          onClick={() => setActiveTab("live")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-medium border-b-2 transition ${
            activeTab === "live" ? "border-emerald-500 text-white bg-slate-900/50" : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Activity size={13} />
          <span>Market-moving</span>
        </button>
        <button
          onClick={() => setActiveTab("impact")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-medium border-b-2 transition ${
            activeTab === "impact" ? "border-emerald-500 text-white bg-slate-900/50" : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Layers size={13} />
          <span>Market Impact</span>
        </button>
        <button
          onClick={() => setActiveTab("events")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-medium border-b-2 transition ${
            activeTab === "events" ? "border-emerald-500 text-white bg-slate-900/50" : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Calendar size={13} />
          <span>Events</span>
        </button>
        <button
          onClick={() => setActiveTab("corporate")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-medium border-b-2 transition ${
            activeTab === "corporate" ? "border-emerald-500 text-white bg-slate-900/50" : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Briefcase size={13} />
          <span>Corporate</span>
        </button>
        <button
          onClick={() => setActiveTab("watchlist")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-medium border-b-2 transition ${
            activeTab === "watchlist" ? "border-emerald-500 text-white bg-slate-900/50" : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Search size={13} />
          <span>Watchlist</span>
        </button>
      </div>

      {/* Tab Contents */}
      <div className="space-y-4">
        {/* Live Feed Tab */}
        {activeTab === "live" && (
          <div className="space-y-4">
            {liveItems.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No news items ingested. Try triggering a Manual Fetch.</p>
            ) : (
              liveItems.map((item, idx) => (
                <div key={item.id || idx} className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg space-y-2 hover:bg-slate-900/60 transition">
                  <div className="flex justify-between items-start gap-4">
                    <a
                      href={safeString(item.original_url || item.discovery_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-white hover:text-cyan-400 transition"
                    >
                      {stripHtml(item.headline)}
                    </a>
                    {getDirectionBadge(item.expected_direction)}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{stripHtml(item.summary_snippet || item.summary || item.description)}</p>
                  {item.why_it_matters && <p className="text-xs text-cyan-300"><span className="font-semibold">Why it matters:</span> {safeString(item.why_it_matters)}</p>}

                  {/* Item badges */}
                  <div className="flex flex-wrap items-center gap-3 pt-2 text-[10px] font-mono text-slate-500 border-t border-slate-900">
                    <span className="flex items-center gap-1 text-slate-400 font-semibold uppercase">{safeString(item.source_name)}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1 uppercase">{safeString(item.category)}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock size={10} /> {formatDateTimeIST(item.published_at)}
                    </span>
                    <span>•</span>
                    <span className="bg-slate-950 px-1.5 py-0.5 rounded text-slate-400 border border-slate-800">
                      RELEVANCE: {formatNumber(item.nifty_relevance_score, 1)}/10
                    </span>
                    <span>IMPORTANCE: {safeString(item.impact_strength || "UNAVAILABLE").toUpperCase()}</span>
                    <span>TIER: {safeString(item.source_tier || "UNAVAILABLE")}</span>
                    <span>STREAM: {safeString(item.discovery_stream || "UNAVAILABLE")}</span>
                    <span>TIME: {safeString(item.temporal_class || "UNAVAILABLE")}</span>
                    {item.discovery_category && <span>DISCOVERY: {safeString(item.discovery_category)}</span>}
                    <span>•</span>
                    <span className={`px-1 rounded uppercase font-semibold ${
                      safeString(item.verification_status) === "confirmed" ? "bg-emerald-950/45 text-emerald-400" : "bg-amber-950/45 text-amber-400"
                    }`}>
                      {safeString(item.verification_status)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Market Impact Tab */}
        {activeTab === "impact" && (
          <div className="space-y-4">
            {clusters.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No distinct NIFTY-relevant event clusters are available.</p>
            ) : (
              clusters.map((cluster, idx) => (
                <div key={cluster.event_cluster_id || idx} data-event-cluster={cluster.event_cluster_id} className="p-4 bg-slate-900/50 border border-slate-800 rounded-lg space-y-3">
                  <div className="flex justify-between items-start gap-4">
                    <div><div className="text-[9px] font-mono uppercase tracking-wider text-cyan-400">Canonical Event · {safeString(cluster.category)}</div><span className="text-sm font-semibold text-white">{safeString(cluster.canonical_headline)}</span></div>
                    {getDirectionBadge(cluster.expected_direction)}
                  </div>
                  <p className="text-xs leading-relaxed text-cyan-200"><span className="font-semibold">Why it matters:</span> {safeString(cluster.reasoning)}</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 bg-slate-950 rounded border border-slate-800 text-xs">
                    <div className="space-y-1">
                      <div className="flex justify-between py-0.5">
                        <span className="text-slate-500 font-mono">Impact:</span>
                        <span className="font-semibold text-amber-400 font-mono">{safeString(cluster.impact_level)}</span>
                      </div>
                      <div className="flex justify-between py-0.5">
                        <span className="text-slate-500 font-mono">NIFTY Relevance:</span>
                        <span className="font-semibold text-cyan-400 font-mono">{formatNumber(cluster.nifty_relevance, 1)}/10</span>
                      </div>
                      <div className="flex justify-between py-0.5">
                        <span className="text-slate-500 font-mono">Confirmation:</span>
                        <span className="font-semibold text-slate-300 font-mono">{safeString(cluster.verification_strength)}</span>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between py-0.5">
                        <span className="text-slate-500 font-mono">First seen:</span><span className="text-slate-300 font-mono">{formatDateTimeIST(cluster.first_seen)}</span>
                      </div>
                      <div className="flex justify-between py-0.5">
                        <span className="text-slate-500 font-mono">Last updated:</span><span className="text-slate-300 font-mono">{formatDateTimeIST(cluster.last_updated)}</span>
                      </div>
                      <div className="flex justify-between py-0.5">
                        <span className="text-slate-500 font-mono">Articles:</span><span className="text-slate-300 font-mono">{safeNumber(cluster.article_count)} · {safeArray(cluster.publishers).join(", ")}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-[10px] font-mono text-slate-400">Affected channels: {safeArray(cluster.affected_channels).join(", ") || "UNAVAILABLE"}</div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Events Tab */}
        {activeTab === "events" && (
          <div className="space-y-4">
            {/* Partial warning */}
            <div className="flex gap-2.5 p-3.5 bg-cyan-950/20 border border-cyan-900 rounded-lg text-cyan-400 text-xs">
              <Info size={16} className="mt-0.5 flex-shrink-0" />
              <div>
              <span className="font-bold">Economic calendar scope:</span> This tab uses only canonical timed economic-calendar records. Published news articles are not recast as future events.
              </div>
            </div>

            <div className="flex flex-wrap gap-2" data-calendar-filters>
              {["TODAY", "TOMORROW", "THIS WEEK"].map(value => <button key={value} onClick={() => setEventWindow(value as any)} className={`rounded border px-2.5 py-1 text-[10px] font-bold ${eventWindow === value ? "border-cyan-600 bg-cyan-950/40 text-cyan-300" : "border-slate-800 text-slate-400"}`}>{value}</button>)}
              {["ALL", "INDIA", "US", "EUROPE", "ASIA", "HIGH IMPACT", "NIFTY RELEVANT"].map(value => <button key={value} onClick={() => setEventFilter(value)} className={`rounded border px-2.5 py-1 text-[10px] font-bold ${eventFilter === value ? "border-emerald-600 bg-emerald-950/40 text-emerald-300" : "border-slate-800 text-slate-400"}`}>{value}</button>)}
            </div>

            {filteredEvents.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No canonical events match this window and filter.</p>
            ) : (
              filteredEvents.map((ev, idx) => (
                <div key={ev.event_id || idx} data-economic-event={ev.event_id} className="p-4 bg-slate-900/30 border border-slate-800 rounded-lg space-y-3">
                  <div className="flex flex-col md:flex-row md:justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 font-mono text-[9px] uppercase">{safeString(ev.country)} · {safeString(ev.impact_level)}</span>
                      <span className="text-sm font-semibold text-white">{safeString(ev.event_name)}</span>
                    </div>
                    <p className="text-xs text-slate-400">{safeString(ev.reasoning || `${safeString(ev.country)} economic release`)}</p>
                  </div>
                  <div className="flex flex-row md:flex-col items-start md:items-end gap-3 md:gap-1 text-[11px] font-mono text-slate-400">
                    <span className="font-bold text-white">{formatDateTimeIST(ev.scheduled_at_ist || ev.scheduled_at)}</span>
                    <span className="uppercase text-emerald-400">{safeString(ev.status)}</span>
                  </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 border-t border-slate-800 pt-2 text-[10px] font-mono md:grid-cols-5">
                    <span>Previous: {ev.previous ?? "UNAVAILABLE"}{ev.previous != null ? safeString(ev.unit) : ""}</span>
                    <span>Forecast: {ev.forecast ?? "UNAVAILABLE"}{ev.forecast != null ? safeString(ev.unit) : ""}</span>
                    <span>Actual: {ev.actual ?? "UNAVAILABLE"}{ev.actual != null ? safeString(ev.unit) : ""}</span>
                    <span>NIFTY: {formatNumber(ev.nifty_relevance, 1)}/10</span>
                    <span>Channels: {safeArray(ev.affected_channels).join(", ") || "UNAVAILABLE"}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Corporate Announcements Tab */}
        {activeTab === "corporate" && (
          <div className="space-y-4">
            {/* Partial warning */}
            <div className="flex gap-2.5 p-3.5 bg-cyan-950/20 border border-cyan-900 rounded-lg text-cyan-400 text-xs">
              <Info size={16} className="mt-0.5 flex-shrink-0" />
              <div>
              <span className="font-bold">Corporate scope:</span> Official NSE corporate actions and categorized company/earnings discovery items are shown here; the live-news list is not duplicated.
              </div>
            </div>

            {corporates.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No corporate announcements found.</p>
            ) : (
              corporates.map((ann, idx) => (
                <div key={ann.id || idx} className="p-4 bg-slate-900/30 border border-slate-800 rounded-lg space-y-2">
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 rounded bg-amber-955/50 text-amber-400 font-mono text-[10px] font-semibold">{safeString(ann.company_symbol)}</span>
                      <span className="text-sm font-semibold text-white">{safeString(ann.headline)}</span>
                    </div>
                    {getDirectionBadge(ann.expected_direction)}
                  </div>
                  <p className="text-xs text-slate-400">{safeString(ann.description)}</p>
                  <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500">
                    <span>Source: {safeString(ann.source_name)}</span>
                    <span>•</span>
                    <span>{formatDate(ann.published_at)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Watchlist Tab */}
        {activeTab === "watchlist" && (
          <div className="space-y-4">
            <div className="flex gap-3 bg-slate-900 border border-slate-800 rounded-lg p-2.5 items-center">
              <Search size={16} className="text-slate-400" />
              <input
                type="text"
                placeholder="Search symbol (e.g. RELIANCE, HDFCBANK) or keyword..."
                value={watchQuery}
                onChange={(e) => setWatchQuery(e.target.value)}
                className="bg-transparent border-none text-xs text-white placeholder-slate-500 w-full focus:outline-none"
              />
              {watchQuery && (
                <button onClick={() => setWatchQuery("")} className="text-xs text-slate-400 hover:text-white">Clear</button>
              )}
            </div>

            <div className="space-y-4">
              {watchlistFiltered.length === 0 ? (
                <p className="text-xs text-slate-500 italic">{watchQuery ? `No matched articles found matching "${watchQuery}".` : "No symbol-linked watchlist items are available. Enter a symbol, category or provider to filter the canonical feed."}</p>
              ) : (
                watchlistFiltered.map((item, idx) => (
                  <div key={item.id || idx} className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg space-y-2">
                    <div className="flex justify-between items-start gap-4">
                      <a
                        href={safeString(item.original_url || item.discovery_url)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-white hover:text-cyan-400 transition"
                      >
                        {safeString(item.headline)}
                      </a>
                      {getDirectionBadge(item.expected_direction)}
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{safeString(item.summary_snippet)}</p>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500 pt-1">
                      <span className="font-semibold text-slate-400 uppercase">{safeString(item.source_name)}</span>
                      <span>•</span>
                      <span>{formatDate(item.published_at)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default NewsIntelligence;
