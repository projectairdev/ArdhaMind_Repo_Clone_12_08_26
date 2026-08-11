// src/frontend/components/NewsIntelligence.tsx
import React, { useState, useMemo } from "react";
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
  Info,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  stripHtml,
  formatNumber,
  formatDate
} from "../utils/safeHelpers";
import {
  formatTimestampIST,
  formatRelativeAge
} from "../utils/timeFormatting";
import { SemanticBadge } from "./intelligence/CanonicalPresentation";

export function NewsIntelligence() {
  const { canonicalState, lastValidState, syncing: loading, diagnosticsError } = useWorkstationState();
  const [activeTab, setActiveTab] = useState<"market-moving" | "latest" | "events" | "corporate">("market-moving");
  const [sortBy, setSortBy] = useState<"impact" | "relevance" | "newest" | "verification" | "authority">("impact");
  const [filterCategory, setFilterCategory] = useState<string>("ALL");
  const [watchQuery, setWatchQuery] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState<string | null>(null);
  const [eventWindow, setEventWindow] = useState<"TODAY" | "TOMORROW" | "THIS WEEK" | "ALL">("TODAY");
  const [eventFilter, setEventFilter] = useState("ALL");
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

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

  const toggleExpand = (cardId: string) => {
    setExpandedCards(prev => ({ ...prev, [cardId]: !prev[cardId] }));
  };

  // ── ALL useMemo hooks declared before any conditional return ──────────────
  // They read null-safely so they produce stable empty results during loading.

  const rawItems = safeArray(state?.news_intelligence?.items) as any[];

  // 1. Dynamic category extraction for filters
  const uniqueCategories = useMemo(() => {
    const cats = new Set<string>();
    rawItems.forEach(item => {
      if (item.category) cats.add(String(item.category).toUpperCase());
    });
    return Array.from(cats).sort();
  }, [rawItems]);

  // Sort value helpers (plain functions — not hooks)
  const getImpactVal = (item: any) => {
    const imp = String(item.impact_strength || item.impact_level || "LOW").toUpperCase();
    if (imp.includes("CRIT") || imp.includes("HIGH")) return 3;
    if (imp.includes("MOD") || imp.includes("MED")) return 2;
    return 1;
  };
  const getVerificationVal = (item: any) => {
    const status = safeString(item.verification_status).toUpperCase();
    if (["CONFIRMED", "VERIFIED"].includes(status)) return 3;
    if (status === "DEVELOPING") return 2;
    if (status === "UNVERIFIED") return 1;
    return 0;
  };
  const getAuthorityVal = (item: any) => {
    const tier = safeString(item.source_tier).toUpperCase();
    if (tier.startsWith("TIER_A")) return 4;
    if (tier.startsWith("TIER_B")) return 3;
    if (tier.startsWith("TIER_C")) return 2;
    if (tier.startsWith("TIER_D")) return 1;
    return 0;
  };
  const publicationTime = (item: any) => {
    const parsed = Date.parse(item.published_at || item.normalized_timestamp || "");
    return Number.isFinite(parsed) ? parsed : Number.NEGATIVE_INFINITY;
  };
  const getDirectionBadge = (dir: string, impStr?: string) => {
    const d = safeString(dir).toUpperCase();
    const imp = impStr ? ` · ${safeString(impStr).toUpperCase()} IMPACT` : "";
    if (d === "POSITIVE") return <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">POSITIVE{imp}</span>;
    if (d === "NEGATIVE") return <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold rounded bg-rose-950/60 text-rose-400 border border-rose-800/60">NEGATIVE{imp}</span>;
    if (d === "MIXED") return <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold rounded bg-amber-950/60 text-amber-400 border border-amber-800/60">MIXED{imp}</span>;
    return <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold rounded bg-slate-800 text-slate-400 border border-slate-700">UNCERTAIN{imp}</span>;
  };

  // 2. Filter and sort items dynamically
  const sortedAndFilteredItems = useMemo(() => {
    let list = [...rawItems];
    if (filterCategory !== "ALL") {
      list = list.filter(item => String(item.category).toUpperCase() === filterCategory);
    }
    const query = watchQuery.toLowerCase().trim();
    if (query) {
      list = list.filter(item =>
        safeString(item.headline).toLowerCase().includes(query) ||
        safeString(item.summary_snippet).toLowerCase().includes(query) ||
        safeArray(item.affected_symbols).some(sym => safeString(sym).toLowerCase().includes(query)) ||
        safeArray(item.affected_channels).some(ch => safeString(ch).toLowerCase().includes(query))
      );
    }
    list.sort((a, b) => {
      let diff = 0;
      if (sortBy === "impact") {
        diff = getImpactVal(b) - getImpactVal(a);
      } else if (sortBy === "relevance") {
        diff = safeNumber(b.nifty_relevance_score) - safeNumber(a.nifty_relevance_score);
      } else if (sortBy === "newest") {
        diff = publicationTime(b) - publicationTime(a);
      } else if (sortBy === "verification") {
        diff = getVerificationVal(b) - getVerificationVal(a);
      } else if (sortBy === "authority") {
        diff = getAuthorityVal(b) - getAuthorityVal(a);
      }
      if (diff === 0) diff = safeNumber(b.nifty_relevance_score) - safeNumber(a.nifty_relevance_score);
      if (diff === 0) diff = publicationTime(b) - publicationTime(a);
      if (diff === 0) diff = safeString(a.id).localeCompare(safeString(b.id));
      return diff;
    });
    return list;
  }, [rawItems, filterCategory, watchQuery, sortBy]);

  // 3. Tab-aware render slice
  const renderItems = useMemo(() => {
    return activeTab === "market-moving" || activeTab === "latest"
      ? sortedAndFilteredItems
      : [];
  }, [activeTab, sortedAndFilteredItems]);

  // Events filtering
  const istDateKey = (value: string | Date) => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(value));
  const todayKey = istDateKey(new Date());
  const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowKey = istDateKey(tomorrow);
  const weekEnd = new Date(); weekEnd.setDate(weekEnd.getDate() + 7);
  const rawEvents = safeArray(state?.macro_intelligence?.economic_events) as any[];

  const sortedEvents = useMemo(() => {
    const filtered = rawEvents.filter(event => {
      const eventDate = new Date(event.scheduled_at_ist || event.scheduled_at);
      const key = istDateKey(eventDate);
      const inWindow = eventWindow === "ALL" || (eventWindow === "TODAY" ? key === todayKey : eventWindow === "TOMORROW" ? key === tomorrowKey : eventDate >= new Date(`${todayKey}T00:00:00+05:30`) && eventDate <= weekEnd);
      const region = safeString(event.region).toUpperCase();
      const impact = safeString(event.impact_level).toUpperCase();
      const matches = eventFilter === "ALL" || eventFilter === region || (eventFilter === "HIGH IMPACT" && ["HIGH", "CRITICAL"].includes(impact)) || (eventFilter === "NIFTY RELEVANT" && safeNumber(event.nifty_relevance) >= 7);
      return inWindow && matches;
    });
    return [...filtered].sort((a, b) => {
      const timeA = new Date(a.scheduled_at_ist || a.scheduled_at || 0).getTime();
      const timeB = new Date(b.scheduled_at_ist || b.scheduled_at || 0).getTime();
      let diff = timeA - timeB;
      if (diff === 0) {
        const impA = String(a.impact_level).toUpperCase().includes("HIGH") ? 2 : 1;
        const impB = String(b.impact_level).toUpperCase().includes("HIGH") ? 2 : 1;
        diff = impB - impA;
      }
      return diff;
    });
  }, [rawEvents, eventWindow, eventFilter, todayKey, tomorrowKey, weekEnd]);

  // 5. Corporate actions sorted by relevance DESC → newest DESC
  const rawNewsCorporates = safeArray(state?.news_intelligence?.corporate_items) as any[];
  const rawActionCorporates = (safeArray(state?.macro_intelligence?.corporate_actions) as any[]).map(action => ({
    id: action.id,
    company_symbol: action.symbol,
    headline: `${safeString(action.company_name || action.symbol)} — ${safeString(action.action_type)}`,
    description: action.details,
    published_at: action.ex_date,
    source_name: action.source_name,
    expected_direction: "uncertain",
  }));
  const rawOfficialCorporates = (safeArray(state?.macro_intelligence?.official_india_events) as any[])
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
  const rawCorporates = [...rawOfficialCorporates, ...rawActionCorporates, ...rawNewsCorporates]
    .filter((item, index, all) => all.findIndex(other => safeString(other.id) === safeString(item.id)) === index);

  const sortedCorporates = useMemo(() => {
    return [...rawCorporates].sort((a, b) => {
      const relevanceA = safeNumber(a.relevance_score || a.nifty_relevance_score || (String(a.impact_level).toUpperCase().includes("HIGH") ? 8 : 4));
      const relevanceB = safeNumber(b.relevance_score || b.nifty_relevance_score || (String(b.impact_level).toUpperCase().includes("HIGH") ? 8 : 4));
      let diff = relevanceB - relevanceA;
      if (diff === 0) diff = new Date(b.published_at || 0).getTime() - new Date(a.published_at || 0).getTime();
      return diff;
    });
  }, [rawCorporates]);
  // ── End hooks section ──────────────────────────────────────────────────────

  if (loading && !news) {
    return (
      <div id="news-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4 font-mono">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-32 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (!news) {
    return (
      <div id="news-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3 font-mono">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold text-sm">News Intelligence Offline</h3>
        </div>
        <p className="text-xs text-slate-400">{diagnosticsError || "No canonical news snapshot is available."}</p>
        <button onClick={() => window.location.reload()} className="px-3 py-1.5 bg-slate-900 text-xs text-white border border-slate-800 rounded hover:bg-slate-800 transition">
          Reconnect
        </button>
      </div>
    );
  }

  // Plain derivations — fine below the guard since they are not hooks
  const items = rawItems;
  const clusters = (safeArray(news.event_clusters) as any[]).sort((a, b) => safeNumber(b.priority_score) - safeNumber(a.priority_score));
  const events = rawEvents;
  const filteredEvents = sortedEvents; // already filtered and sorted above
  const corporates = rawCorporates;

  const degradedProviders = Object.values(news.provider_health || {}).filter((health: any) => !["ready", "disabled"].includes(safeString(health.status).toLowerCase())) as any[];

  return (
    <div id="news-intelligence" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6">
      {/* Title & Stats */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <BookOpen size={18} className="text-emerald-400" />
          <h3 className="font-bold text-white text-base">Market-Moving News & Updates</h3>
        </div>

        {/* Actions & Health Status */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1 bg-slate-900 hover:bg-slate-800 text-xs text-white border border-slate-800 rounded transition disabled:opacity-50 font-mono"
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

      {degradedProviders.length > 0 && <details className="rounded-lg border border-amber-900/40 bg-amber-950/10 px-3 py-2 text-xs text-amber-300 font-mono"><summary className="cursor-pointer font-semibold">Partial provider coverage · {degradedProviders.length} provider{degradedProviders.length === 1 ? "" : "s"} degraded</summary><div className="mt-2 space-y-1 text-[10px] text-amber-200">{degradedProviders.map(provider => <div key={safeString(provider.provider_name)}>{safeString(provider.provider_name)} · {safeString(provider.operational_error_reason || provider.status)}</div>)}<div className="text-slate-500">Healthy-provider items remain available.</div></div></details>}

      {/* Tabs list */}
      <div className="flex flex-wrap gap-1 border-b border-slate-900 pb-1">
        <button
          onClick={() => setActiveTab("market-moving")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-medium border-b-2 transition ${
            activeTab === "market-moving" ? "border-emerald-500 text-white bg-slate-900/50" : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Activity size={13} />
          <span>Market-moving</span>
        </button>
        <button
          onClick={() => setActiveTab("latest")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-medium border-b-2 transition ${
            activeTab === "latest" ? "border-emerald-500 text-white bg-slate-900/50" : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Clock size={13} />
          <span>Latest</span>
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
      </div>

      {/* Filters and Sorting (Visible for News lists) */}
      {(activeTab === "market-moving" || activeTab === "latest") && (
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 bg-slate-900/40 p-3 rounded-lg border border-slate-850 font-mono text-xs">
          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <span className="text-slate-500">Filter Category:</span>
            <select
              value={filterCategory}
              onChange={e => setFilterCategory(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-white px-2 py-1 rounded focus:outline-none"
            >
              <option value="ALL">All Categories</option>
              {uniqueCategories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Watchlist Query Search */}
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded px-2 py-1 w-full md:w-64">
            <Search size={14} className="text-slate-500 shrink-0" />
            <input
              type="text"
              placeholder="Search watchlist symbols..."
              value={watchQuery}
              onChange={e => setWatchQuery(e.target.value)}
              className="bg-transparent border-none text-white focus:outline-none text-[11px] w-full placeholder-slate-600"
            />
            {watchQuery && (
              <button onClick={() => setWatchQuery("")} className="text-[10px] text-slate-500 hover:text-white font-bold font-mono">Clear</button>
            )}
          </div>

          {/* Sorting */}
          <div className="flex items-center gap-2">
            <span className="text-slate-500">Sort By:</span>
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as any)}
              className="bg-slate-950 border border-slate-800 text-white px-2 py-1 rounded focus:outline-none"
            >
              <option value="impact">Impact DESC</option>
              <option value="relevance">Relevance DESC</option>
              <option value="newest">Newest First</option>
              <option value="verification">Verification</option>
              <option value="authority">Source Authority</option>
            </select>
          </div>
        </div>
      )}

      {/* Tab Contents */}
      <div className="space-y-4">
        {/* News Feed Tab (Market Moving / Latest) */}
        {(activeTab === "market-moving" || activeTab === "latest") && (
          <div className="overflow-hidden rounded-lg border border-[var(--air-line)] bg-[var(--air-surface)]">
            {renderItems.length === 0 ? (
              <p className="text-xs text-slate-500 italic p-4">No matching news items found.</p>
            ) : (
              renderItems.map((item, idx) => {
                const cardId = item.id || `news-${idx}`;
                const isExpanded = !!expandedCards[cardId];
                const cleanHeadline = stripHtml(item.headline);
                const relativeAge = formatRelativeAge(item.published_at);
                const isConfirmed = ["confirmed", "verified"].includes(safeString(item.verification_status).toLowerCase());

                return (
                  <article key={cardId} data-event-cluster={item.event_cluster_id || item.duplicate_group_id || undefined} className="border-b border-[var(--air-line)] px-4 py-3 last:border-0 hover:bg-slate-900/40 transition">
                    {/* TOP BADGES */}
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex flex-wrap gap-2 items-center">
                        {getDirectionBadge(item.expected_direction, item.impact_strength || item.impact_level)}
                        <span className={`px-1.5 py-0.5 text-[8px] rounded uppercase font-bold border ${
                          isConfirmed ? "bg-emerald-950/60 border-emerald-800 text-emerald-400" : "bg-amber-950/60 border-amber-800 text-amber-400"
                        }`}>
                          {safeString(item.verification_status || "UNVERIFIED")}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-500 shrink-0">
                        {item.source_name} · {relativeAge}
                      </span>
                    </div>

                    {/* HEADLINE */}
                    <h4 className="mt-2 text-sm font-semibold leading-snug">
                      <a
                        href={safeString(item.original_url || item.discovery_url)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-white hover:text-cyan-400 transition"
                      >
                        {cleanHeadline}
                      </a>
                    </h4>

                    {/* CONCISE WHY IT MATTERS */}
                    {item.why_it_matters && (
                      <p className="mt-1.5 text-xs text-cyan-300/90 leading-relaxed font-medium">
                        <span className="font-semibold text-cyan-400 uppercase tracking-wider text-[9px] font-mono">Why it matters:</span> {safeString(item.why_it_matters)}
                      </p>
                    )}

                    {/* EXPAND DETAILS TRIGGER */}
                    <div className="mt-2 flex justify-start">
                      <button
                        onClick={() => toggleExpand(cardId)}
                        className="flex items-center gap-1 text-[10px] font-mono font-bold text-slate-500 hover:text-cyan-400 transition"
                      >
                        {isExpanded ? (
                          <>Hide details <ChevronUp size={12} /></>
                        ) : (
                          <>View details <ChevronDown size={12} /></>
                        )}
                      </button>
                    </div>

                    {/* EXPANDED DETAILS */}
                    {isExpanded && (
                      <div className="mt-3 p-3 bg-slate-950/60 rounded border border-slate-900 text-xs font-mono text-slate-400 space-y-2">
                        {/* Summary Block */}
                        <div className="space-y-1 font-sans">
                          <span className="text-[9px] text-slate-500 font-bold font-mono uppercase block">Summary Description</span>
                          <p className="text-slate-300 text-[11px] leading-relaxed">
                            {stripHtml(item.summary_snippet || item.summary || item.description || "No full summary snippet was provided.")}
                          </p>
                        </div>

                        {/* Tech Metadata Grid */}
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 border-t border-slate-900 pt-2 text-[10px]">
                          <div>Source Authority: <span className="text-slate-200">{safeString(item.source_tier || "UNAVAILABLE")}</span></div>
                          <div>Relevance Score: <span className="text-slate-200">{formatNumber(item.nifty_relevance_score, 1)}/10</span></div>
                          <div>Verification: <span className="text-slate-200">{safeString(item.verification_status)}</span></div>
                          <div>First Seen: <span className="text-slate-200">{formatTimestampIST(item.first_seen)}</span></div>
                          <div>Published at: <span className="text-slate-200">{formatTimestampIST(item.published_at)}</span></div>
                          <div>Canonical Category: <span className="text-slate-200">{safeString(item.category).toUpperCase()}</span></div>
                        </div>

                        <div className="border-t border-slate-900 pt-1.5 text-[9px] text-slate-500 space-y-0.5">
                          <div>Affected Channels: {safeArray(item.affected_channels).join(", ") || "UNAVAILABLE"}</div>
                          <div>Affected Symbols: {safeArray(item.affected_symbols).join(", ") || "UNAVAILABLE"}</div>
                          <div>Discovery Stream: {safeString(item.discovery_stream || "UNAVAILABLE")}</div>
                          {item.discovery_category && <div>Discovery Category: {safeString(item.discovery_category)}</div>}
                        </div>
                      </div>
                    )}
                  </article>
                );
              })
            )}
          </div>
        )}

        {/* Events Tab */}
        {activeTab === "events" && (
          <div className="space-y-4">
            <div className="flex gap-2.5 p-3.5 bg-cyan-950/20 border border-cyan-900 rounded-lg text-cyan-400 text-xs">
              <Info size={16} className="mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-bold">Economic calendar scope:</span> This tab uses only canonical timed economic-calendar records. Published news articles are not recast as future events.
              </div>
            </div>

            <div className="grid gap-2 lg:grid-cols-[auto_1fr] font-mono text-xs">
              <div aria-label="Event date window" className="flex flex-wrap gap-1.5">{["TODAY", "TOMORROW", "THIS WEEK", "ALL"].map(value => <button key={value} onClick={() => setEventWindow(value as any)} className={`rounded border px-2.5 py-1 text-[10px] font-bold ${eventWindow === value ? "border-cyan-600 bg-cyan-950/40 text-cyan-300" : "border-slate-800 text-slate-400"}`}>{value}</button>)}</div>
              <div aria-label="Event region and relevance filters" className="flex flex-wrap gap-1.5 lg:justify-end">{["ALL", "INDIA", "US", "EUROPE", "ASIA", "HIGH IMPACT", "NIFTY RELEVANT"].map(value => <button key={value} onClick={() => setEventFilter(value)} className={`rounded border px-2.5 py-1 text-[10px] font-bold ${eventFilter === value ? "border-emerald-600 bg-emerald-950/40 text-emerald-300" : "border-slate-800 text-slate-400"}`}>{value}</button>)}</div>
            </div>

            {filteredEvents.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No canonical events match this window and filter.</p>
            ) : (
              <div className="overflow-hidden rounded-lg border border-slate-900 bg-slate-950">
                {filteredEvents.map((ev, idx) => (
                  <div key={ev.event_id || idx} className="border-b border-slate-900 p-3 last:border-0 hover:bg-slate-900/30 transition">
                    <div className="flex flex-col md:flex-row md:justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 font-mono text-[9px] uppercase">{safeString(ev.country)} · {safeString(ev.impact_level)}</span>
                          <span className="text-sm font-semibold text-white">{safeString(ev.event_name)}</span>
                        </div>
                        <p className="text-xs text-slate-400">{safeString(ev.reasoning || `${safeString(ev.country)} economic release`)}</p>
                      </div>
                      <div className="flex flex-row md:flex-col items-start md:items-end gap-3 md:gap-1 text-[11px] font-mono text-slate-400">
                        <span className="font-bold text-white">{formatTimestampIST(ev.scheduled_at_ist || ev.scheduled_at)}</span>
                        <span className="uppercase text-emerald-400 font-bold">{safeString(ev.status)}</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 border-t border-slate-900 mt-2 pt-2 text-[10px] font-mono md:grid-cols-5">
                      <span>Previous: {ev.previous ?? "UNAVAILABLE"}{ev.previous != null ? safeString(ev.unit) : ""}</span>
                      <span>Forecast: {ev.forecast ?? "UNAVAILABLE"}{ev.forecast != null ? safeString(ev.unit) : ""}</span>
                      <span>Actual: {ev.actual ?? "UNAVAILABLE"}{ev.actual != null ? safeString(ev.unit) : ""}</span>
                      <span>NIFTY: {formatNumber(ev.nifty_relevance, 1)}/10</span>
                      <span>Channels: {safeArray(ev.affected_channels).join(", ") || "UNAVAILABLE"}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Corporate Announcements Tab */}
        {activeTab === "corporate" && (
          <div className="space-y-4">
            <div className="flex gap-2.5 p-3.5 bg-cyan-950/20 border border-cyan-900 rounded-lg text-cyan-400 text-xs">
              <Info size={16} className="mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-bold">Corporate scope:</span> Official NSE corporate actions and categorized company/earnings discovery items are shown here; the live-news list is not duplicated.
              </div>
            </div>

            {corporates.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No corporate announcements found.</p>
            ) : (
              <div className="space-y-2">
                {corporates.map((ann, idx) => (
                  <div key={ann.id || idx} className="p-4 bg-slate-900/30 border border-slate-800 rounded-lg space-y-2">
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex items-center gap-2">
                        <span className="px-1.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 font-mono text-[9px] font-bold">{safeString(ann.company_symbol)}</span>
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
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
