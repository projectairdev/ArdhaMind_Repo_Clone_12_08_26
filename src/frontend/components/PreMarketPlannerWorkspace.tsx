// src/frontend/components/PreMarketPlannerWorkspace.tsx
import React, { useState } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { formatDate, formatDateTimeIST, formatNumber, safeArray, safeString } from "../utils/safeHelpers";
import { GlobalCuesWidget, InstitutionalFlowWidget } from "./MacroIntelligence";
import { ParticipantPositioningWidget, VolatilityContextWidget } from "./SpecializedIntelligence";
import { PreMarketIntelligenceView } from "./UnifiedIntelligencePanel";
import { TomorrowsOutlookCard } from "./intelligence/TomorrowsOutlookCard";
import { Layers, ShieldCheck, Compass, AlertTriangle, TrendingUp, TrendingDown, Clock, Activity, Target } from "lucide-react";
import { InstrumentVisual } from "./ui/AuthenticMarketLogo";
import { GlobalSessionStrip } from "./visualizations/DataVisualizations";
import { Surface, SectionHeader, MetricCell, CompactRows } from "./ui/WorkspacePrimitives";


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

// ─── GLOBAL CUE CARDS ────────────────────────────────────────────────────────

/**
 * Displays global market cue observations as compact visual cards.
 *
 * Data truth rules:
 * - Shows "NOT OBSERVED" when value is genuinely unavailable
 * - Zero IS data — never shown as "unavailable"
 * - Never fabricates values
 */
function GlobalCueCards({ quotes }: { quotes: any[] }) {
  if (!quotes || quotes.length === 0) {
    return (
      <div className="rounded border border-[#1a1a24] bg-[#050507] p-3 text-center text-[11px] text-slate-500 font-mono">
        No global market observations available for this session.
      </div>
    );
  }

  const PRIORITY_KEYS = ["S&P 500", "NASDAQ", "DOW_JONES", "NIKKEI_225", "HANG_SENG", "GIFT_NIFTY", "BRENT_CRUDE", "GOLD", "USD_INR", "DXY"];

  const sorted = [...quotes].sort((a, b) => {
    const ai = PRIORITY_KEYS.indexOf(a.canonical_key || a.name || "");
    const bi = PRIORITY_KEYS.indexOf(b.canonical_key || b.name || "");
    if (ai === -1 && bi === -1) return 0;
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  return (
    <div className="rounded border border-[#1a1a24] bg-[#050507] overflow-x-auto">
      <table className="w-full text-left font-mono text-[11px]">
        <thead>
          <tr className="border-b border-[#181820] bg-[#07070a] text-[9px] uppercase tracking-wider text-slate-400">
            <th className="py-2 px-3 font-semibold">Asset / Instrument</th>
            <th className="py-2 px-3 font-semibold text-right">Value</th>
            <th className="py-2 px-3 font-semibold text-right">Change</th>
            <th className="py-2 px-3 font-semibold text-right">Session / Freshness</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#14141c]">
          {sorted.slice(0, 12).map((q, i) => {
            const key = q.canonical_key || q.name || `q${i}`;
            const displayName = q.display_name || q.name || key;
            const value = q.value ?? q.price ?? q.close;
            const changePct = q.change_pct ?? q.change_percent;
            const positive = changePct != null && Number(changePct) >= 0;
            const isUnavailable = value == null;

            return (
              <tr key={key} className="hover:bg-[#09090d] transition-colors">
                <td className="py-2 px-3">
                  <div className="flex items-center gap-2">
                    <InstrumentVisual symbol={key} size={20} />
                    <span className="font-semibold text-slate-200">{displayName}</span>
                  </div>
                </td>
                <td className="py-2 px-3 text-right air-data font-bold text-slate-100">
                  {isUnavailable ? <span className="text-slate-500">Unavailable</span> : formatNumber(Number(value), 2)}
                </td>
                <td className="py-2 px-3 text-right air-data font-bold">
                  {changePct != null ? (
                    <span className={positive ? "text-[#00E5A8]" : "text-[#FF5C77]"}>
                      {positive ? "+" : ""}{formatNumber(Number(changePct), 2)}%
                    </span>
                  ) : (
                    <span className="text-slate-500">—</span>
                  )}
                </td>
                <td className="py-2 px-3 text-right text-[10px] text-slate-400">
                  {q.freshness_status || q.session_context || "Observed"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── MAIN WORKSPACE ────────────────────────────────────────────────────────────

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

  const targetSessionDate = preMarketReport.target_trading_date || canonicalState?.market_session?.session_date;
  const istDay = (value: string | Date) => {
    try {
      return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(value));
    } catch (e) {
      return safeString(value).slice(0, 10);
    }
  };
  const todayEvents = events.filter(event => {
    const evDate = istDay(event.scheduled_at_ist || event.scheduled_at);
    return targetSessionDate ? evDate === targetSessionDate : evDate === istDay(new Date());
  });
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
  const isSessionClosed = Boolean(canonicalState?.market_session?.is_closed || preMarketReport.analysis_status === "SESSION_COMPLETE");

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
      <Surface className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#191D23] bg-[#0E1013] px-3.5 py-2">
          <div className="flex items-center gap-2 text-[11px] font-bold text-[#E6E8EB] font-mono uppercase tracking-wider">
            <Layers size={14} className="text-[#38BDF8]" />
            <span>PRE-MARKET BRIEF · {preMarketReport.target_trading_date || "LATEST SESSION"}</span>
            <span className={`px-1.5 py-0.2 rounded-[2px] text-[9px] font-bold border ${
              isFrozen ? "bg-[#E59700]/10 border-[#E59700]/40 text-[#E59700]" : "bg-[#00C896]/10 border-[#00C896]/40 text-[#00C896]"
            }`}>
              {isFrozen ? "FROZEN SESSION THESIS" : "ACTIVE EVALUATION"}
            </span>
          </div>
          <div className="text-right text-[10px] text-[#A5ABB4] font-mono">
            GENERATED: <strong className="text-[#38BDF8]">{preMarketReport.generated_at ? preMarketReport.generated_at.slice(11, 19) + " UTC" : "Canonical"}</strong>
          </div>
        </div>

        {/* HERO METRICS STRIP */}
        <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-[#191D23] bg-[#0B0D10]">
          <MetricCell label="Pre-Market Bias">
            <span className={`text-[12px] font-bold uppercase ${
              setupScoreVal > 15 ? "text-[#00C896]" : setupScoreVal < -15 ? "text-[#E5484D]" : "text-[#E59700]"
            }`}>
              {bias}
            </span>
          </MetricCell>

          <MetricCell label="Expected Opening">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-bold text-[#38BDF8] uppercase">
                {preMarketReport.opening_character || "UNCERTAIN"}
              </span>
              <span className="text-[10px] text-[#A5ABB4] font-mono">
                {giftContext.implied_gap_points != null ? `${giftContext.implied_gap_points >= 0 ? "+" : ""}${giftContext.implied_gap_points.toFixed(1)} pts` : ""}
              </span>
            </div>
          </MetricCell>

          <MetricCell label="Session Setup">
            <span className="text-[12px] font-semibold text-[#E6E8EB] uppercase">
              {setup.replace("_", " ")}
            </span>
          </MetricCell>

          <MetricCell label="Setup Score / Confidence">
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-bold text-[#E6E8EB] font-mono">{setupScoreVal > 0 ? "+" : ""}{setupScoreVal.toFixed(1)}</span>
              <span className="text-[9px] font-semibold text-[#A5ABB4]">
                ({confidence} CONFIDENCE)
              </span>
            </div>
          </MetricCell>
        </div>

        {/* OPENING VALIDATION BANNER */}
        {validation.summary && (
          <div className="px-3 py-1.5 bg-[#0E1013] border-t border-[#191D23] text-[10px] font-mono flex items-center justify-between text-[#A5ABB4]">
            <span className="flex items-center gap-1.5">
              <ShieldCheck size={13} className="text-[#38BDF8]" />
              <strong className="text-[#E6E8EB]">OPENING VALIDATION:</strong> {validation.summary}
            </span>
            <span className="text-[9px] text-[#707987] uppercase font-bold">{validation.status}</span>
          </div>
        )}
      </Surface>

      {/* ── WORKSPACE NAVIGATION TABS ── */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
        {[
          { id: "Pre-Market Thesis", label: isFrozen || isSessionClosed ? `Pre-Market Thesis · FINALIZED SESSION (${preMarketReport.target_trading_date || "CURRENT"})` : `Pre-Market Thesis (${preMarketReport.target_trading_date || "CURRENT"})` },
          { id: "Evening Outlook", label: `Evening Outlook · NEXT TRADING SESSION` },
          { id: "8:50 AM Briefing", label: `8:50 AM Briefing · PENDING until generated` },
          { id: "Opening Checklist", label: `Opening Checklist · PENDING until applicable` }
        ].map(item => (
          <TabButton key={item.id} value={item.label} active={tab === item.id} onClick={() => setTab(item.id)} />
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
                  <strong className={giftContext.implied_gap_points == null ? "text-amber-400" : giftContext.implied_gap_points >= 0 ? "text-emerald-400" : "text-rose-400"}>
                    {giftContext.implied_gap_points != null
                      ? `${giftContext.implied_gap_points >= 0 ? "+" : ""}${formatNumber(giftContext.implied_gap_points, 2)} pts (${giftContext.implied_gap_percent != null && giftContext.implied_gap_percent >= 0 ? "+" : ""}${formatNumber(giftContext.implied_gap_percent, 2)}%)`
                      : "UNAVAILABLE"}
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
                <strong className="text-white text-sm">{formatNumber(levels.previous_close ?? market.previous_close ?? market.prev_close, 2)}</strong>
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
            <div className="col-span-full">
              <Card title="Global Cues Since Close">
                <GlobalCueCards quotes={sinceCloseQuotes} />
              </Card>
            </div>
            <Card title="Latest News Since Close">{sinceClose.length ? sinceClose.slice(0, 5).map(item => safeString(item.headline)).join(" · ") : "No verified news since close."}</Card>
          </div>

          {/* Global Market Session Strip */}
          <div className="rounded-xl border border-[#1c1c24] bg-[#050507] p-4">
            <div className="text-[9px] font-bold uppercase tracking-wider text-slate-500 mb-3">Global Market Sessions</div>
            <GlobalSessionStrip />
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
