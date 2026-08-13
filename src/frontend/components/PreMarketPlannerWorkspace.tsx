// src/frontend/components/PreMarketPlannerWorkspace.tsx
import React, { useState } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { formatDate, formatDateTimeIST, formatNumber, safeArray, safeString } from "../utils/safeHelpers";
import { GlobalCuesWidget, InstitutionalFlowWidget } from "./MacroIntelligence";
import { ParticipantPositioningWidget, VolatilityContextWidget } from "./SpecializedIntelligence";
import { PreMarketIntelligenceView } from "./UnifiedIntelligencePanel";
import { TomorrowsOutlookCard } from "./intelligence/TomorrowsOutlookCard";
import { Layers, ShieldCheck, Compass, AlertTriangle, TrendingUp, TrendingDown, Clock, Activity, Target } from "lucide-react";

function TabButton({ value, active, onClick }: { key?: string; value: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-lg border px-3.5 py-1.5 text-xs font-bold font-mono transition ${
        active ? "border-cyan-700 bg-cyan-950/40 text-cyan-300 shadow-sm" : "border-slate-800 bg-slate-900/60 text-slate-400 hover:text-slate-200"
      }`}
    >
      {value}
    </button>
  );
}

function Card({ title, children, tone = "default" }: { key?: string; title: string; children: React.ReactNode; tone?: "default" | "warning" | "danger" | "success" }) {
  const color = tone === "danger"
    ? "border-rose-900/50 bg-rose-950/20 text-rose-200"
    : tone === "warning"
    ? "border-amber-900/50 bg-amber-950/20 text-amber-200"
    : tone === "success"
    ? "border-emerald-900/50 bg-emerald-950/20 text-emerald-200"
    : "border-slate-800 bg-slate-950/60 text-slate-300";

  return (
    <section className={`rounded-xl border p-5 text-left ${color}`}>
      <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono mb-2">{title}</h3>
      <div className="text-xs leading-relaxed font-sans">{children}</div>
    </section>
  );
}

export function PreMarketPlannerWorkspace() {
  const [tab, setTab] = useState("Pre-Market Thesis");
  const { canonicalState } = useWorkstationState() as any;

  const preMarketReport = canonicalState?.pre_market_report || canonicalState?.session_story?.pre_market_report || {};
  const market = canonicalState?.market_data || {};
  const macro = canonicalState?.macro_intelligence || {};
  const news = safeArray(canonicalState?.news_intelligence?.items) as any[];
  const clusters = safeArray(canonicalState?.news_intelligence?.event_clusters) as any[];
  const quotes = macro.quotes || {};
  const macroWorkspace = macro.workspace_context || {};
  const sinceCloseQuoteKeys = new Set(safeArray(macroWorkspace.since_india_close_quote_keys).map(String));
  const sinceCloseQuotes = Object.entries(quotes).filter(([key]) => sinceCloseQuoteKeys.has(key)).map(([, quote]) => quote as any);
  const flows = safeArray(macro.institutional_flows) as any[];
  const events = safeArray(macro.economic_events) as any[];
  const corporate = (safeArray(macro.official_india_events) as any[]).filter(event => ["CORPORATE_ANNOUNCEMENT", "EARNINGS", "CORPORATE_ACTION", "BOARD_MEETING"].includes(safeString(event.event_category).toUpperCase()));

  const istDay = (value: string | Date) => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(value));
  const todayEvents = events.filter(event => istDay(event.scheduled_at_ist || event.scheduled_at) === istDay(new Date()));
  const highImpactToday = todayEvents.filter(event => ["HIGH", "CRITICAL"].includes(safeString(event.impact_level).toUpperCase()));
  const nextHigh = events.filter(event => ["HIGH", "CRITICAL"].includes(safeString(event.impact_level).toUpperCase()) && new Date(event.scheduled_at).getTime() >= Date.now()).sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())[0];

  const candles = safeArray(market.candles) as any[];
  const high = candles.length ? Math.max(...candles.map(c => Number(c.h))) : null;
  const low = candles.length ? Math.min(...candles.map(c => Number(c.l))) : null;
  const readiness = canonicalState?.workspace_readiness?.pre_market_850_readiness || {};
  const readinessMeta = new Set(["is_full_premarket_ready", "overall_state", "ready_inputs", "unavailable_inputs", "blocked_inputs"]);
  const missing = Object.entries(readiness).filter(([key, value]) => !readinessMeta.has(key) && value !== "READY").map(([key]) => key.replaceAll("_", " "));
  const openingGap = macro.opening_gap || {};
  const optionReady = safeString(canonicalState?.option_intelligence?.status).toLowerCase() === "ready";
  const marketReady = Boolean(market.current_spot && canonicalState?.data_quality?.market_data?.quality_status === "valid");
  const operationalState = marketReady && optionReady && news.length > 0 && Object.keys(quotes).length >= 10 && flows.length > 0 && events.length > 0 ? "Ready" : marketReady || news.length > 0 || Object.keys(quotes).length > 0 ? "Partial" : "Not Ready";
  const temporal = canonicalState?.news_intelligence?.workspace_temporal || {};
  const sinceCloseIds = new Set(safeArray(temporal.since_close_item_ids).map(String));
  const sinceCloseClusterIds = new Set(safeArray(temporal.since_close_cluster_ids).map(String));
  const sinceClose = news.filter(item => sinceCloseIds.has(String(item.id)));
  const overnightClusters = clusters.filter(cluster =>
    sinceCloseClusterIds.has(String(cluster.event_cluster_id)) &&
    (["HIGH", "CRITICAL"].includes(safeString(cluster.impact_level).toUpperCase()) || Number(cluster.nifty_relevance) >= 6)
  ).slice(0, 6);

  const giftContext = preMarketReport.gift_nifty_context || {};
  const globalContext = preMarketReport.global_context || {};
  const instContext = preMarketReport.institutional_context || {};
  const levels = preMarketReport.critical_levels || {};
  const validation = preMarketReport.opening_validation || {};

  const bias = preMarketReport.opening_bias || "NEUTRAL / MIXED OPENING";
  const setup = preMarketReport.session_setup || "RANGE_BOUND_SETUP";
  const confidence = preMarketReport.overall_confidence || "MODERATE";
  const setupScoreVal = preMarketReport["setup_score"] ?? 0.0;
  const isFrozen = Boolean(preMarketReport.is_frozen);

  const bullishEv = safeArray(preMarketReport.bullish_evidence);
  const bearishEv = safeArray(preMarketReport.bearish_evidence);
  const neutralEv = safeArray(preMarketReport.neutralizing_factors);
  const whyToday = safeArray(preMarketReport.why_today);
  const timeline = safeArray(preMarketReport.event_timeline);
  const sectors = safeArray(preMarketReport.sector_watch);
  const heavyweights = safeArray(preMarketReport.heavyweight_watch);

  return (
    <div id="pre-market-planner-workspace" className="space-y-6 text-left font-sans">
      {/* ── HEADER & PRE-MARKET THESIS HERO BANNER ── */}
      <header className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-900 pb-3">
          <div>
            <div className="flex items-center gap-2 text-[10px] font-bold text-cyan-400 uppercase tracking-widest">
              <Layers size={16} className="animate-spin-slow" />
              <span>PRE-MARKET PLANNER · PRE-SESSION SETUP INTELLIGENCE</span>
              <span className={`px-2 py-0.5 rounded text-[9px] border font-bold ${
                isFrozen ? "bg-amber-950/80 border-amber-700 text-amber-300" : "bg-emerald-950/80 border-emerald-700 text-emerald-300"
              }`}>
                {isFrozen ? "● PRE-MARKET THESIS FROZEN" : "● ACTIVE PRE-MARKET EVALUATION"}
              </span>
            </div>
            <h2 className="text-xl font-black text-white mt-1 uppercase tracking-tight">PRE-SESSION MARKET THESIS & SETUP</h2>
          </div>
          <div className="text-right text-[10px] text-slate-400 font-mono space-y-0.5">
            <div>DATE: <strong className="text-white">{preMarketReport.target_trading_date || "CURRENT"}</strong></div>
            <div>GENERATED: <strong className="text-cyan-300">{preMarketReport.generated_at ? preMarketReport.generated_at.slice(11, 19) + " UTC" : "Live"}</strong></div>
          </div>
        </div>

        {/* HERO METRICS GRID */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-1">
          <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg">
            <span className="text-[9px] uppercase font-bold text-slate-500 block mb-1">PRE-MARKET BIAS</span>
            <span className={`text-sm font-black uppercase ${
              setupScoreVal > 15 ? "text-emerald-400" : setupScoreVal < -15 ? "text-rose-400" : "text-amber-400"
            }`}>
              {bias}
            </span>
          </div>

          <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg">
            <span className="text-[9px] uppercase font-bold text-slate-500 block mb-1">EXPECTED OPENING</span>
            <span className="text-sm font-black text-cyan-300 uppercase">
              {preMarketReport.opening_character || "FLAT_OPEN"}
            </span>
            <span className="text-[10px] text-slate-400 block font-mono">
              ~{giftContext.implied_gap_points != null ? (giftContext.implied_gap_points >= 0 ? "+" : "") + giftContext.implied_gap_points.toFixed(2) : "0.00"} pts
            </span>
          </div>

          <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg">
            <span className="text-[9px] uppercase font-bold text-slate-500 block mb-1">POTENTIAL SETUP</span>
            <span className="text-sm font-black text-indigo-300 uppercase">
              {setup.replace("_", " ")}
            </span>
          </div>

          <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg">
            <span className="text-[9px] uppercase font-bold text-slate-500 block mb-1">SETUP SCORE / CONFIDENCE</span>
            <div className="flex items-center gap-2">
              <span className="text-base font-black text-white font-mono">{setupScoreVal > 0 ? "+" : ""}{setupScoreVal.toFixed(1)}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                confidence === "HIGH" ? "border-emerald-700 bg-emerald-950/60 text-emerald-300" : "border-amber-700 bg-amber-950/60 text-amber-300"
              }`}>
                {confidence} CONFIDENCE
              </span>
            </div>
          </div>
        </div>

        {/* OPENING VALIDATION BANNER IF FROZEN */}
        {validation.summary && (
          <div className="p-2.5 bg-slate-900/90 border border-cyan-800/60 rounded-lg text-xs font-mono flex items-center justify-between text-cyan-200">
            <span className="flex items-center gap-2">
              <ShieldCheck size={14} className="text-cyan-400" />
              <strong>OPENING VALIDATION:</strong> {validation.summary}
            </span>
            <span className="text-[10px] text-slate-400 uppercase font-bold">{validation.status}</span>
          </div>
        )}
      </header>

      {/* ── WORKSPACE NAVIGATION TABS ── */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
        {["Pre-Market Thesis", "Evening Outlook", "8:50 AM Briefing", "Opening Checklist"].map(value => (
          <TabButton key={value} value={value} active={tab === value} onClick={() => setTab(value)} />
        ))}
      </div>

      {/* ── TAB 1: PRE-MARKET THESIS ── */}
      {tab === "Pre-Market Thesis" && (
        <div data-premarket-panel="thesis" className="space-y-5">
          {/* WHY TODAY MATTERS */}
          <Card title="WHY TODAY MATTERS — SESSION CATALYSTS">
            {whyToday.length > 0 ? (
              <ul className="space-y-1.5 list-disc list-inside text-slate-200">
                {whyToday.map((item: string, idx: number) => (
                  <li key={idx} className="leading-relaxed"><strong className="text-white">{item}</strong></li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-400">Pre-market session catalysts evaluated from canonical telemetry.</p>
            )}
          </Card>

          {/* EVIDENCE TRIO: BULLISH / BEARISH / NEUTRALIZING */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card title="BULLISH EVIDENCE" tone="success">
              {bullishEv.length > 0 ? (
                <ul className="space-y-1 list-disc list-inside text-emerald-200 text-[11px]">
                  {bullishEv.map((ev: string, idx: number) => <li key={idx}>{ev}</li>)}
                </ul>
              ) : <p className="text-slate-500 italic">No positive pre-market evidence.</p>}
            </Card>

            <Card title="BEARISH EVIDENCE" tone="danger">
              {bearishEv.length > 0 ? (
                <ul className="space-y-1 list-disc list-inside text-rose-200 text-[11px]">
                  {bearishEv.map((ev: string, idx: number) => <li key={idx}>{ev}</li>)}
                </ul>
              ) : <p className="text-slate-500 italic">No negative pre-market evidence.</p>}
            </Card>

            <Card title="NEUTRALIZING / RISKS" tone="warning">
              {neutralEv.length > 0 ? (
                <ul className="space-y-1 list-disc list-inside text-amber-200 text-[11px]">
                  {neutralEv.map((ev: string, idx: number) => <li key={idx}>{ev}</li>)}
                </ul>
              ) : <p className="text-slate-500 italic">No neutralizing factors reported.</p>}
            </Card>
          </div>

          {/* GLOBAL & GIFT NIFTY EXACT DATE/TIME TRUTH */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
            <Card title="GIFT NIFTY & OPENING GAP">
              <div className="space-y-1.5 text-slate-300">
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span>GIFT NIFTY PRICE:</span>
                  <strong className="text-white">{giftContext.gift_price ? formatNumber(giftContext.gift_price, 2) : "UNAVAILABLE"}</strong>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span>IMPLIED OPENING GAP:</span>
                  <strong className={giftContext.implied_gap_points >= 0 ? "text-emerald-400" : "text-rose-400"}>
                    {giftContext.implied_gap_points >= 0 ? "+" : ""}{formatNumber(giftContext.implied_gap_points, 2)} pts ({giftContext.implied_gap_percent >= 0 ? "+" : ""}{formatNumber(giftContext.implied_gap_percent, 2)}%)
                  </strong>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span>OBSERVED AT:</span>
                  <span className="text-cyan-300">{giftContext.observed_at}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span>CHECKED AT:</span>
                  <span className="text-slate-400">{giftContext.checked_at}</span>
                </div>
                <div className="flex justify-between">
                  <span>FRESHNESS / SOURCE:</span>
                  <span className="text-amber-300 font-bold">{giftContext.freshness} · {giftContext.source_session}</span>
                </div>
              </div>
            </Card>

            <Card title="INSTITUTIONAL POSITIONING & VOLATILITY">
              <div className="space-y-1.5 text-slate-300">
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span>FII CASH NET FLOW:</span>
                  <strong className={instContext.fii_net_crores >= 0 ? "text-emerald-400" : "text-rose-400"}>
                    {instContext.fii_net_crores >= 0 ? "+" : ""}{formatNumber(instContext.fii_net_crores, 1)} Cr
                  </strong>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span>DII CASH NET FLOW:</span>
                  <strong className={instContext.dii_net_crores >= 0 ? "text-emerald-400" : "text-rose-400"}>
                    {instContext.dii_net_crores >= 0 ? "+" : ""}{formatNumber(instContext.dii_net_crores, 1)} Cr
                  </strong>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span>FLOW TRADING DATE:</span>
                  <span className="text-cyan-300">{instContext.trading_date}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span>INDIA VIX:</span>
                  <strong className="text-white">{formatNumber(preMarketReport.volatility_context?.vix, 2)} ({preMarketReport.volatility_context?.regime})</strong>
                </div>
                <div className="flex justify-between">
                  <span>OPTION PCR:</span>
                  <strong className="text-cyan-300">{formatNumber(preMarketReport.options_context?.pcr, 2)}</strong>
                </div>
              </div>
            </Card>
          </div>

          {/* CRITICAL PRE-SESSION LEVELS */}
          <Card title="CRITICAL PRE-SESSION LEVELS (CANONICAL BOUNDARIES)">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
              <div className="p-2 bg-slate-900 border border-slate-800 rounded">
                <span className="text-[10px] text-slate-500 block">PREVIOUS CLOSE</span>
                <strong className="text-white text-sm">{formatNumber(levels.previous_close, 2)}</strong>
              </div>
              <div className="p-2 bg-slate-900 border border-slate-800 rounded">
                <span className="text-[10px] text-slate-500 block">GAP REFERENCE</span>
                <strong className="text-cyan-300 text-sm">{formatNumber(levels.gap_reference, 2)}</strong>
              </div>
              <div className="p-2 bg-slate-900 border border-slate-800 rounded">
                <span className="text-[10px] text-emerald-400 block">IMMEDIATE SUPPORT</span>
                <strong className="text-emerald-300 text-sm">{formatNumber(levels.immediate_support, 2)}</strong>
              </div>
              <div className="p-2 bg-slate-900 border border-slate-800 rounded">
                <span className="text-[10px] text-rose-400 block">IMMEDIATE RESISTANCE</span>
                <strong className="text-rose-300 text-sm">{formatNumber(levels.immediate_resistance, 2)}</strong>
              </div>
            </div>
          </Card>

          {/* SECTOR & HEAVYWEIGHT WATCH */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card title="SECTORS TO WATCH">
              <div className="space-y-2">
                {sectors.map((sec: any, idx: number) => (
                  <div key={idx} className="border-b border-slate-800/60 pb-1.5 last:border-0">
                    <div className="flex justify-between font-bold text-slate-200">
                      <span>{sec.sector}</span>
                      <span className="text-cyan-300 font-mono text-[10px] uppercase">{sec.posture}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Sensitivity: {sec.sensitivity}</div>
                  </div>
                ))}
              </div>
            </Card>

            <Card title="HEAVYWEIGHT CONSTITUENTS WATCH">
              <div className="space-y-2">
                {heavyweights.map((hw: any, idx: number) => (
                  <div key={idx} className="border-b border-slate-800/60 pb-1.5 last:border-0">
                    <div className="flex justify-between font-bold text-slate-200">
                      <span>{hw.symbol}</span>
                      <span className="text-slate-400 font-mono text-[10px]">{hw.relevance}</span>
                    </div>
                    <div className="text-[10px] text-cyan-200 mt-0.5">Catalyst: {hw.catalyst}</div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* EVENT TIMELINE */}
          <Card title="TODAY'S EVENT TIMELINE (EXACT IST TIMES)">
            {timeline.length > 0 ? (
              <div className="space-y-2 font-mono text-xs">
                {timeline.map((ev: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between border-b border-slate-900 pb-1.5 last:border-0">
                    <span className="text-cyan-300 font-bold">{ev.time_ist}</span>
                    <span className="text-slate-300 font-bold">{ev.country} · {ev.event_name}</span>
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                      ev.impact === "CRITICAL" ? "bg-rose-950 text-rose-300 border border-rose-800" : "bg-slate-900 text-slate-400"
                    }`}>
                      {ev.impact}
                    </span>
                  </div>
                ))}
              </div>
            ) : <p className="text-slate-500">No scheduled macro events reported today.</p>}
          </Card>
        </div>
      )}

      {/* ── TAB 2: EVENING OUTLOOK ── */}
      {tab === "Evening Outlook" && (
        <div data-premarket-panel="evening" className="space-y-4">
          <TomorrowsOutlookCard intelligence={canonicalState?.unified_intelligence} macro={macro} />
          <PreMarketIntelligenceView />
          <div className="grid gap-4 md:grid-cols-2">
            <Card title="Previous Session Summary">NIFTY closed at {market.current_spot ? formatNumber(market.current_spot, 2) : "UNAVAILABLE"}. High {high != null ? formatNumber(high, 2) : "UNAVAILABLE"}, low {low != null ? formatNumber(low, 2) : "UNAVAILABLE"}; source Kite Historical API.</Card>
            <Card title="Developments Since Close">{sinceClose.length ? `${sinceClose.length} verified developments since the last market observation.` : "No verified developments since close."}</Card>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Card title="Global Cues Since Close">{sinceCloseQuotes.length ? sinceCloseQuotes.slice(0, 6).map(q => `${safeString(q.name)} ${Number(q.change_pct) >= 0 ? "+" : ""}${formatNumber(q.change_pct, 2)}% vs source previous close (${safeString(q.freshness_status)})`).join(" · ") : "No global-market observations newer than the last Indian market observation are available."}</Card>
            <Card title="Latest News Since Close">{sinceClose.length ? sinceClose.slice(0, 5).map(item => safeString(item.headline)).join(" · ") : "No verified news since close."}</Card>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Card title="Overnight Risk Factors">{sinceClose.filter(item => ["Geopolitics", "Crude", "Currency/Yields", "Global Markets"].includes(safeString(item.category))).slice(0, 4).map(item => safeString(item.headline)).join(" · ") || "No verified overnight risk story is available."}</Card>
            <Card title="Key Factors to Watch" tone="warning">{missing.length ? missing.join(", ") : "No setup gaps reported."} · Opening gap remains unknown until a genuine pre-open observation exists.</Card>
          </div>
          <Card title="Overnight Risk Events">
            {overnightClusters.length ? (
              <div className="overflow-x-auto">
                <div className="min-w-[42rem]">
                  <div className="grid grid-cols-[5rem_7rem_1fr_10rem_8rem] gap-2 border-b border-slate-800 pb-1 text-[8px] font-semibold text-slate-600">
                    <span>SEVERITY</span><span>CATEGORY</span><span>DEVELOPMENT</span><span>TRANSMISSION</span><span>TIME</span>
                  </div>
                  {overnightClusters.map(cluster => (
                    <div key={cluster.event_cluster_id} data-overnight-cluster={cluster.event_cluster_id} className="grid grid-cols-[5rem_7rem_1fr_10rem_8rem] items-start gap-2 border-b border-slate-900 py-2 text-[9px] last:border-0">
                      <span className={safeString(cluster.impact_level).toUpperCase() === "HIGH" ? "text-rose-300" : "text-amber-300"}>{safeString(cluster.impact_level)}</span>
                      <span className="text-slate-400">{safeString(cluster.category)}</span>
                      <span className="font-medium text-slate-200">{safeString(cluster.canonical_headline)}</span>
                      <span className="text-cyan-300">{safeArray(cluster.affected_channels).join(", ") || "UNAVAILABLE"}</span>
                      <span className="air-data text-slate-500">{formatDate(cluster.last_updated)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : "No meaningful verified event cluster has updated since the previous Indian market close."}
          </Card>
        </div>
      )}

      {/* ── TAB 3: 8:50 AM BRIEFING ── */}
      {tab === "8:50 AM Briefing" && (
        <div data-premarket-panel="briefing-850" className="space-y-4">
          <GlobalCuesWidget />
          <div className="grid gap-4 md:grid-cols-3">
            <div data-briefing-category="cash-flow"><InstitutionalFlowWidget /></div>
            <div data-briefing-category="derivative-positioning"><ParticipantPositioningWidget compact /></div>
            <div data-briefing-category="volatility"><VolatilityContextWidget /></div>
          </div>
          <Card title="Overnight News & Updates">{sinceClose.length ? sinceClose.slice(0, 5).map(item => safeString(item.headline)).join(" · ") : "No verified overnight news available."}</Card>
          <Card title="Today's Key Scheduled Events">
            {highImpactToday.length ? (
              <div className="space-y-3">
                {highImpactToday.map(event => (
                  <div key={event.event_id} data-premarket-economic-event={event.event_id} className="border-b border-slate-800 pb-2 last:border-0">
                    <div className="font-bold text-white">{formatDateTimeIST(event.scheduled_at_ist || event.scheduled_at)} · {safeString(event.country)} · {safeString(event.event_name)}</div>
                    <div className="mt-1 font-mono text-[10px]">{safeString(event.impact_level)} · Forecast: {event.forecast ?? "UNAVAILABLE"}{event.forecast != null ? safeString(event.unit) : ""} · Previous: {event.previous ?? "UNAVAILABLE"}{event.previous != null ? safeString(event.unit) : ""} · NIFTY {formatNumber(event.nifty_relevance, 1)}/10</div>
                    <div className="mt-1 text-cyan-200">Channels: {safeArray(event.affected_channels).join(", ") || "UNAVAILABLE"}</div>
                  </div>
                ))}
              </div>
            ) : "No HIGH/CRITICAL economic event is scheduled today."}
          </Card>
          <div className="grid gap-4 md:grid-cols-2">
            <Card title="Next Scheduled Event">{nextHigh ? `${safeString(nextHigh.country)} · ${safeString(nextHigh.event_name)} · ${formatDateTimeIST(nextHigh.scheduled_at_ist || nextHigh.scheduled_at)}` : "NONE"}</Card>
            <Card title="Corporate Announcements & Events">{corporate.length ? corporate.slice(0, 5).map(event => `${safeString(event.symbol)} · ${safeString(event.event_category)}`).join(" · ") : "UNAVAILABLE — no corporate events returned."}</Card>
          </div>
          <Card title="Expected Opening Gap" tone={openingGap.status === "READY" ? "default" : "warning"}>
            {openingGap.status === "READY" ? `${safeString(openingGap.classification)} · ${Number(openingGap.gap_points) >= 0 ? "+" : ""}${formatNumber(openingGap.gap_points, 2)} points (${Number(openingGap.gap_pct) >= 0 ? "+" : ""}${formatNumber(openingGap.gap_pct, 2)}%). ${safeString(openingGap.disclaimer)}` : "UNAVAILABLE until eligible GIFT Nifty and reference observations are present."}
          </Card>
        </div>
      )}

      {/* ── TAB 4: OPENING CHECKLIST ── */}
      {tab === "Opening Checklist" && (
        <div data-premarket-panel="opening-checklist" className="space-y-4">
          <Card title={`Setup Status: ${operationalState}`} tone={operationalState === "Not Ready" ? "danger" : operationalState === "Partial" ? "warning" : "default"}>Pre-open status derived from current session records.</Card>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {[
              ["Broker Connected", safeString(canonicalState?.broker_status?.status || "unavailable").toUpperCase()],
              ["Market Feed", safeString(canonicalState?.market_feed_status?.status || "unavailable").toUpperCase()],
              ["Options Snapshot", optionReady ? "AVAILABLE" : "UNAVAILABLE"],
              ["News Freshness", safeString(canonicalState?.news_intelligence?.freshness || "unavailable").toUpperCase()],
              ["Macro Freshness", safeString(macro.domain_freshness?.global_quotes || "unavailable").toUpperCase()],
              ["Events Due Today", todayEvents.length ? String(todayEvents.length) : "NONE"]
            ].map(([label, value]) => <Card key={label} title={label}>{value}</Card>)}
          </div>
          <Card title="Event Risk Today">
            {todayEvents.length ? (
              <div className="grid gap-2 md:grid-cols-2">
                {["BEFORE_OPEN", "DURING_SESSION", "AFTER_CLOSE", "OVERNIGHT"].map(bucket => {
                  const grouped = todayEvents.filter(event => safeString(event.session_timing) === bucket && ["HIGH", "CRITICAL"].includes(safeString(event.impact_level).toUpperCase()));
                  return (
                    <div key={bucket}>
                      <span className="font-bold text-cyan-300">{bucket.replace("_", " ")}:</span> {grouped.length ? grouped.map(event => `${safeString(event.event_name)} at ${formatDateTimeIST(event.scheduled_at_ist || event.scheduled_at)}`).join(" · ") : "No major events"}
                    </div>
                  );
                })}
              </div>
            ) : "No economic event is scheduled today."}
          </Card>
          <div className="grid gap-4 md:grid-cols-2">
            <Card title="Risk Warnings & Invalidation" tone="danger">
              Do not enable intraday confirmation if the broker/feed disconnects, timestamps become stale, the opening gap invalidates last-session structure, or options remain unavailable.
            </Card>
            <Card title="Missing Critical Data" tone="warning">
              {missing.length ? missing.join(", ") : "None reported."}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
