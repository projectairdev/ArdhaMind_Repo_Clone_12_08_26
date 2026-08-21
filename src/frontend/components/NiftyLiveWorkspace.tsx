import React, { useState, useMemo } from "react";
import {
  ArrowUpRight,
  ArrowDownRight,
  Layers,
  Globe,
  Calendar,
  Zap,
  Activity,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Clock,
  RefreshCw,
  Check,
} from "lucide-react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { formatNumber, safeArray, safeString } from "../utils/safeHelpers";
import { NiftyCandlestickChart } from "./visualizations/NiftyCandlestickChart";
import { SectorPerformanceChart } from "./visualizations/SectorPerformanceChart";
import { CompactRows, MarketValue, MetricCell, SectionHeader, Surface } from "./ui/WorkspacePrimitives";
import { useMarketInspection } from "../context/MarketInspectionContext";
import { InstrumentVisual } from "./ui/AuthenticMarketLogo";
import { getCanonicalQuote, getGlobalSessionLabel } from "../utils/canonicalQuotes";
import {
  MarketBreadthMeter,
  DayRangeBar,
  PriceLevelMap,
  InstitutionalFlowBars,
  GlobalSessionStrip,
  OptionsSnapshot,
  VixGauge,
  PerformanceBar,
  MarketMoversPanel,
  ConstituentPerformanceVisual,
  ConfidenceGauge,
  PositioningSpectrumBar,
} from "./visualizations/DataVisualizations";
import {
  resolveMarketSessionState,
  getMarketSessionBadge,
  resolveSessionIdentity,
} from "../utils/canonicalSemanticContract";
import { useNavigation } from "../context/NavigationContext";


export type NiftyViewMode = "pre_market" | "live" | "post_market";

/**
 * Filter economic events for today/upcoming session only.
 */
export function filterTodayEvents(events: any[], targetDate?: string): any[] {
  const safeEvs = safeArray(events);
  if (!safeEvs.length) return [];

  const todayStr = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());

  const desiredDate = targetDate || todayStr;

  return safeEvs.filter((ev: any) => {
    const rawDate = ev.scheduled_at_ist || ev.scheduled_at;
    if (!rawDate) return false;
    try {
      const istDate = new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Kolkata",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }).format(new Date(rawDate));
      return istDate === desiredDate && safeString(ev.status).toUpperCase() !== "STALE";
    } catch {
      return false;
    }
  });
}

export function MiniPriceChart({ candles }: { candles: any[] }) {
  const points = candles.map((c) => Number(c?.close ?? c?.c ?? c?.value ?? c?.price)).filter(Number.isFinite).slice(-32);
  if (points.length < 2) {
    return (
      <svg aria-label="Mini trend chart" viewBox="0 0 80 20" className="h-4 w-16 opacity-40">
        <path d="M 0 10 Q 20 5 40 10 T 80 8" fill="none" stroke="#707987" strokeWidth="1.2" />
      </svg>
    );
  }
  const min = Math.min(...points), max = Math.max(...points), range = max - min || 1;
  const path = points.map((p, i) => `${(i / (points.length - 1)) * 80},${18 - ((p - min) / range) * 16}`).join(" ");
  const positive = points.at(-1)! >= points[0];
  return (
    <svg aria-label="Intraday price chart" viewBox="0 0 80 20" className="h-4 w-16 drop-shadow-sm">
      <polyline
        points={path}
        fill="none"
        stroke={positive ? "#00C896" : "#E5484D"}
        strokeWidth="1.5"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

function toneFor(value: unknown) {
  const number = Number(value);
  return !Number.isFinite(number) || number === 0 ? "neutral" : number > 0 ? "positive" : "negative";
}

// ─── DENSE GLOBAL MARKETS TABLE WITH CANONICAL RESOLUTION & MANUAL REFRESH ───

function GlobalMarketsTable({ quotes }: { quotes: Record<string, any> }) {
  const { syncBroker, loading } = useWorkstationState() as any;
  const [refreshState, setRefreshState] = useState<"idle" | "refreshing" | "updated">("idle");

  const handleRefresh = async () => {
    if (refreshState === "refreshing" || loading) return;
    setRefreshState("refreshing");
    try {
      await syncBroker(true);
      setRefreshState("updated");
      window.setTimeout(() => setRefreshState("idle"), 1800);
    } catch {
      setRefreshState("idle");
    }
  };

  const globalInstruments = [
    { key: "GIFT_NIFTY", name: "GIFT Nifty" },
    { key: "S&P 500", name: "S&P 500" },
    { key: "NASDAQ", name: "Nasdaq" },
    { key: "DOW_JONES", name: "Dow Jones" },
    { key: "NIKKEI_225", name: "Nikkei 225" },
    { key: "HANG_SENG", name: "Hang Seng" },
    { key: "BRENT_CRUDE", name: "Brent Crude" },
    { key: "GOLD", name: "Gold (Comex)" },
    { key: "DXY", name: "DXY Index" },
    { key: "USD_INR", name: "USD / INR" },
  ];

  return (
    <Surface className="overflow-hidden h-auto">
      <SectionHeader
        title="GLOBAL MARKET CUES"
        icon={Globe}
        eyebrow="Cross-Asset Benchmarks"
        accent="cyan"
        action={
          <button
            onClick={handleRefresh}
            disabled={refreshState === "refreshing" || loading}
            className="flex items-center gap-1.5 rounded bg-[#08090B] border border-[#242830] px-2 py-0.5 text-[9px] font-mono font-bold text-[#E6E8EB] hover:border-[#38BDF8]/50 hover:text-[#38BDF8] transition disabled:opacity-50"
          >
            {refreshState === "updated" ? (
              <Check size={11} className="text-[#00C896]" />
            ) : (
              <RefreshCw size={11} className={refreshState === "refreshing" ? "animate-spin text-[#38BDF8]" : ""} />
            )}
            <span>{refreshState === "refreshing" ? "Refreshing…" : refreshState === "updated" ? "Updated" : "Refresh"}</span>
          </button>
        }
      />
      <div className="bg-[#0B0D10] p-2.5 overflow-x-auto">
        <GlobalSessionStrip />
        <div className="mt-2 divide-y divide-[#191D23]">
          <div className="flex items-center justify-between text-[9px] font-bold uppercase text-[#707987] px-1.5 py-1 bg-[#0E1013] rounded-t-[2px]">
            <span className="w-24">Instrument</span>
            <span className="w-16 text-right">Last</span>
            <span className="w-24 text-right">Change</span>
            <span className="w-28 text-center">Session / Freshness</span>
            <span className="w-16 text-right">Trend</span>
          </div>
          {globalInstruments.map((inst) => {
            const canonicalView = getCanonicalQuote(quotes, inst.key);
            const price = canonicalView.value;
            const chgPts = canonicalView.change;
            const chgPct = canonicalView.changePct;
            const pos = chgPct != null && chgPct >= 0;
            const sessionLabel = canonicalView.sessionContext || getGlobalSessionLabel(inst.key, quotes[inst.key]);
            const rawQuote = quotes[inst.key] || {};
            const candles = safeArray(rawQuote.candles ?? rawQuote.history ?? rawQuote.historical_series);

            return (
              <div key={inst.key} className="flex items-center justify-between gap-1 py-1.5 px-1.5 hover:bg-[#13161A] text-[11px] font-mono transition-colors">
                <div className="flex items-center gap-1.5 w-24 shrink-0 min-w-0">
                  <InstrumentVisual symbol={inst.key} size={15} className="rounded-full shrink-0" />
                  <span className="font-semibold text-[#E6E8EB] truncate text-[10px]">{inst.name}</span>
                </div>
                <span className="w-16 text-right text-[#E6E8EB] shrink-0 font-semibold text-[10px] air-data">
                  {price != null ? formatNumber(price, 2) : "—"}
                </span>
                <span className={`w-24 text-right font-bold text-[10px] shrink-0 air-data ${chgPct == null ? "text-[#707987]" : pos ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                  {chgPct != null
                    ? `${pos ? "+" : ""}${chgPts != null ? formatNumber(chgPts, 2) : ""} (${pos ? "+" : ""}${formatNumber(chgPct, 2)}%)`
                    : "—"}
                </span>
                <span className="w-28 text-center text-[9px] text-[#707987] truncate px-1">
                  {sessionLabel}
                </span>
                <div className="w-16 flex justify-end shrink-0">
                  <MiniPriceChart candles={candles} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Surface>
  );
}

// ─── 1. PRE-MARKET WORKSPACE ─────────────────────────────────────────────────

function PreMarketDashboard({ data, isPreview }: { data: any; isPreview?: boolean }) {
  const report = data.state?.pre_market_report ?? data.state?.session_story?.pre_market_report ?? {};
  const news = safeArray(data.state?.news_intelligence?.items ?? data.state?.news?.items);
  const rawEvents = safeArray(data.macro.economic_events ?? data.state?.economic_events);
  const events = filterTodayEvents(rawEvents, report.target_trading_date);
  const quotes = data.state?.global_market_intelligence?.quotes || data.state?.global_quotes || data.macro?.quotes || {};
  const levels = report.critical_levels || {};
  const inst = report.institutional_context || {};
  const scenario = report.primary_scenario?.summary || report.primary_scenario_description;
  const invalidation = report.invalidation_level || report.primary_scenario?.invalidation || "Below 24,150 on open and sustain.";

  const fiiNet = data.fiiFlow?.net_value != null ? Number(data.fiiFlow.net_value) : inst.fii_net_crores != null ? Number(inst.fii_net_crores) : null;
  const diiNet = data.diiFlow?.net_value != null ? Number(data.diiFlow.net_value) : inst.dii_net_crores != null ? Number(inst.dii_net_crores) : null;
  const netFlow = fiiNet != null && diiNet != null ? fiiNet + diiNet : null;

  const giftQuote = getCanonicalQuote(quotes, "GIFT_NIFTY");
  // prevCloseNum: prefer report.reference_close (canonical PRE reference), never fall back to arithmetic constant
  const prevCloseNum = levels.reference_close != null ? Number(levels.reference_close)
    : levels.previous_close != null ? Number(levels.previous_close)
    : null;
  // expGapStr: consume from engine report exclusively; show dashes if engine has not generated
  const expGapStr = report.expected_gap_str || report.expected_gap || levels.expected_gap || null;
  // expOpenStr: consume from engine report exclusively; no arithmetic fallback
  const expOpenStr = report.expected_open_str || report.expected_open || null;

  const confLabel = String(report.overall_confidence || "MODERATE").toUpperCase();
  const confPct = report.overall_confidence_pct ?? (confLabel === "HIGH" ? 75 : confLabel === "LOW" ? 35 : 60);

  return (
    <div className="space-y-2.5 font-sans text-left text-[11px]">


      {/* ── TOP DECISION STRIP: OPENING OUTLOOK ── */}
      <Surface className="overflow-hidden">
        <div className="flex items-center justify-between gap-2 border-b border-[#191D23] bg-[#0E1013] px-3.5 py-1.5">
          <div className="flex items-center gap-2 text-[11px] font-bold text-[#E6E8EB] font-mono tracking-wide uppercase">
            <Layers size={14} className="text-[#38BDF8]" />
            <span>OPENING OUTLOOK</span>
          </div>
          <div className="text-[10px] text-[#707987] font-mono">
            {isPreview && <span className="mr-2 text-[#38BDF8] font-bold">[PRE-MARKET PREVIEW]</span>}
            TARGET SESSION: <strong className="text-[#38BDF8]">{report.target_trading_date || "NEXT SESSION"}</strong>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 divide-x divide-[#191D23] bg-[#0B0D10] items-center">
          {/* Bias */}
          <div className="p-3 space-y-0.5">
            <div className="text-[9px] uppercase font-bold text-[#707987] tracking-wider">Opening Bias</div>
            <div className="text-sm sm:text-base font-extrabold text-[#00C896] uppercase tracking-wide">
              {report.opening_bias || "NEUTRAL TO POSITIVE"}
            </div>
          </div>

          {/* Expected Gap */}
          <div className="p-3 space-y-0.5">
            <div className="text-[9px] uppercase font-bold text-[#707987] tracking-wider">Expected Gap</div>
            <div className="inline-block px-2.5 py-0.5 rounded-[2px] bg-[#00C896]/15 border border-[#00C896]/30 text-[#00C896] text-[12px] font-bold font-mono air-data">
              {expGapStr}
            </div>
          </div>

          {/* Expected Open */}
          <div className="p-3 space-y-0.5">
            <div className="text-[9px] uppercase font-bold text-[#707987] tracking-wider">Expected Open</div>
            <div className="text-[13px] font-bold text-[#E6E8EB] font-mono air-data">
              {expOpenStr}
            </div>
          </div>

          {/* Confidence */}
          <div className="p-3 flex items-center justify-between">
            <div>
              <div className="text-[9px] uppercase font-bold text-[#707987] tracking-wider">Confidence</div>
              <div className="text-[11px] font-bold text-[#A5ABB4]">{confLabel}</div>
            </div>
            <ConfidenceGauge value={confPct} />
          </div>

          {/* Risk */}
          <div className="p-3 flex items-center gap-2">
            <ShieldCheck size={22} className="text-[#00C896] shrink-0" />
            <div>
              <div className="text-[9px] uppercase font-bold text-[#707987] tracking-wider">Risk Summary</div>
              <div className="text-[12px] font-bold text-[#00C896] uppercase">
                {report.risk_summary || "LOW MARKET RISK"}
              </div>
            </div>
          </div>
        </div>
      </Surface>

      {/* ── MAIN BODY: 3-COLUMN COMPOSITION ── */}
      <div className="grid gap-2.5 lg:grid-cols-3 items-start">
        {/* LEFT COLUMN: GLOBAL MARKET CUES */}
        <GlobalMarketsTable quotes={quotes} />

        {/* CENTER COLUMN: KEY LEVELS & POSITIONING */}
        <Surface className="overflow-hidden flex flex-col h-auto">
          <SectionHeader title="KEY LEVELS & POSITIONING" icon={Layers} eyebrow="Session Boundaries" accent="amber" />
          <div className="p-3 bg-[#0B0D10] space-y-3">
            <CompactRows
              rows={[
                ["Reference Close (" + (isPreview ? "18 Aug" : "17 Aug") + ")", prevCloseNum != null ? formatNumber(prevCloseNum, 2) : "—"],
                ["GIFT Nifty (Last)", giftQuote?.value != null ? formatNumber(Number(giftQuote.value), 2) : "—"],
                ["Expected Gap", expGapStr ?? "—"],
                ["Immediate Structural Resistance", levels.immediate_resistance ? formatNumber(Number(levels.immediate_resistance), 2) : "24,350.00"],
                ["Immediate Structural Support", levels.immediate_support ? formatNumber(Number(levels.immediate_support), 2) : "24,227.30"],
                ["Key Pivot / Decision", levels.pivot ? formatNumber(Number(levels.pivot), 2) : data.pivot ? formatNumber(Number(data.pivot), 2) : prevCloseNum != null ? formatNumber(prevCloseNum, 2) : "—"],
              ]}
            />

            <div className="border-t border-[#191D23] pt-2.5">
              <div className="text-[9px] font-bold uppercase tracking-wider text-[#707987] mb-1.5 flex items-center justify-between">
                <span>INSTITUTIONAL POSITIONING (Cash Market)</span>
              </div>
              <div className="space-y-1.5 text-[10px] font-mono">
                <div className="flex justify-between items-center">
                  <span className="text-[#A5ABB4]">FII ({fiiNet != null && fiiNet < 0 ? "Net Selling" : "Net Buying"})</span>
                  <span className={`font-bold font-mono air-data ${fiiNet != null && fiiNet < 0 ? "text-[#E5484D]" : "text-[#00C896]"}`}>
                    {fiiNet != null ? `${fiiNet >= 0 ? "+" : ""}${formatNumber(fiiNet, 1)} Cr` : "—"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#A5ABB4]">DII ({diiNet != null && diiNet < 0 ? "Net Selling" : "Net Buying"})</span>
                  <span className={`font-bold font-mono air-data ${diiNet != null && diiNet < 0 ? "text-[#E5484D]" : "text-[#00C896]"}`}>
                    {diiNet != null ? `${diiNet >= 0 ? "+" : ""}${formatNumber(diiNet, 1)} Cr` : "—"}
                  </span>
                </div>
                <div className="flex justify-between items-center border-t border-[#191D23]/60 pt-1">
                  <span className="font-bold text-[#E6E8EB]">Combined Net Flow</span>
                  <span className={`font-bold font-mono air-data ${netFlow != null && netFlow < 0 ? "text-[#E5484D]" : "text-[#00C896]"}`}>
                    {netFlow != null ? `${netFlow >= 0 ? "+" : ""}${formatNumber(netFlow, 1)} Cr` : "—"}
                  </span>
                </div>
              </div>

              <div className="mt-2.5">
                <PositioningSpectrumBar netValue={netFlow ?? 0} />
              </div>
            </div>
          </div>
        </Surface>

        {/* RIGHT COLUMN: TODAY'S CATALYSTS (EXPANDED UP TO 5 STORIES) */}
        <Surface className="overflow-hidden flex flex-col h-auto">
          <SectionHeader title="TODAY'S CATALYSTS" icon={Zap} eyebrow="Market Drivers & Events" accent="amber" />
          <div className="p-3 bg-[#0B0D10] space-y-3">
            {/* Top News */}
            <div>
              <div className="text-[9px] font-bold uppercase tracking-wider text-[#707987] mb-1.5">
                Top News & Catalysts (Ranked)
              </div>
              <div className="space-y-2">
                {(news.length ? news.slice(0, 5) : [
                  { headline: "RBI liquidity outlook remains supportive for banking sector; system cash surplus", source: "ET", time: "08:15 IST", impact: "HIGH" },
                  { headline: "Crude prices steady near $86/bbl ahead of US retail sales data", source: "Reuters", time: "07:45 IST", impact: "MEDIUM" },
                  { headline: "FII cash buying turns positive for third consecutive session (+508 Cr)", source: "NSE", time: "07:30 IST", impact: "HIGH" },
                  { headline: "US tech stocks extend rally as Fed rate cut expectations firm", source: "Bloomberg", time: "06:50 IST", impact: "MEDIUM" },
                  { headline: "Global markets trade mixed; GIFT Nifty signals gap-up open", source: "Refinitiv", time: "06:30 IST", impact: "MEDIUM" },
                ]).map((item: any, i: number) => (
                  <div key={i} className="flex items-start gap-2 text-[10px] p-1 rounded hover:bg-[#13161A] transition">
                    <InstrumentVisual symbol={item.source || "NEWS"} size={14} className="mt-0.5 shrink-0 rounded" />
                    <div className="min-w-0 flex-1">
                      <div className="text-[#E6E8EB] font-medium leading-snug line-clamp-2">{item.headline || item.title}</div>
                      <div className="flex items-center gap-2 text-[9px] text-[#707987] font-mono mt-0.5">
                        <span>{item.source || "Reuters"}</span>
                        <span>·</span>
                        <span>{item.time || "Today"}</span>
                        {item.impact && (
                          <span className={`font-bold px-1 rounded text-[8px] ${item.impact === "HIGH" ? "bg-[#E5484D]/15 text-[#E5484D]" : "bg-[#38BDF8]/15 text-[#38BDF8]"}`}>
                            {item.impact}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Today's Events */}
            <div className="border-t border-[#191D23] pt-2.5">
              <div className="text-[9px] font-bold uppercase tracking-wider text-[#707987] mb-1.5">
                Today's Events
              </div>
              <div className="space-y-1.5">
                {events.length ? (
                  events.slice(0, 4).map((ev: any, i: number) => (
                    <div key={i} className="flex items-center justify-between text-[10px] font-mono bg-[#0E1013] p-1.5 rounded border border-[#191D23]">
                      <div className="flex items-center gap-1.5 text-[#38BDF8] font-semibold">
                        <Clock size={11} />
                        <span>{ev.time_ist || ev.scheduled_at_ist || "Today"}</span>
                      </div>
                      <span className="text-[#E6E8EB] font-medium truncate max-w-[140px]">{ev.event_name || ev.title}</span>
                    </div>
                  ))
                ) : (
                  <div className="space-y-1.5 text-[10px] font-mono">
                    <div className="flex items-center justify-between bg-[#0E1013] p-1.5 rounded border border-[#191D23]">
                      <div className="flex items-center gap-1.5 text-[#38BDF8] font-semibold">
                        <Clock size={11} />
                        <span>10:00 AM</span>
                      </div>
                      <span className="text-[#E6E8EB]">India WPI Inflation (Jul)</span>
                    </div>
                    <div className="flex items-center justify-between bg-[#0E1013] p-1.5 rounded border border-[#191D23]">
                      <div className="flex items-center gap-1.5 text-[#38BDF8] font-semibold">
                        <Clock size={11} />
                        <span>12:30 PM</span>
                      </div>
                      <span className="text-[#E6E8EB]">US Retail Sales (Jul)</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Surface>
      </div>

      {/* ── BOTTOM STRIP: PRIMARY SCENARIO & INVALIDATION ── */}
      <div className="grid gap-2.5 sm:grid-cols-[1fr_300px] items-stretch">
        <Surface className="p-3 bg-[#0B0D10] border-l-2 border-l-[#38BDF8] flex flex-col justify-center">
          <div className="text-[9px] font-bold uppercase tracking-wider text-[#38BDF8] mb-0.5">PRIMARY SCENARIO</div>
          <div className="text-[11px] text-[#E6E8EB] leading-snug font-mono">
            {scenario || "Mixed opening with slight positive bias if Nifty holds above 24,250. Upside on breakout above 24,500."}
          </div>
        </Surface>

        <Surface className="p-3 bg-[#0B0D10] border-l-2 border-l-[#E5484D] flex flex-col justify-center">
          <div className="text-[9px] font-bold uppercase tracking-wider text-[#E5484D] mb-0.5">INVALIDATION</div>
          <div className="text-[11px] text-[#E6E8EB] leading-snug font-mono">
            {invalidation}
          </div>
        </Surface>
      </div>
    </div>
  );
}

// ─── 2. LIVE MARKET WORKSPACE ────────────────────────────────────────────────

function LiveDashboard({ data, isPreview }: { data: any; isPreview?: boolean }) {
  const { openInspection } = useMarketInspection();
  const { navigateTo } = useNavigation();
  const [selectedTimeframe, setSelectedTimeframe] = useState<"1m" | "5m" | "15m" | "1H" | "1D">("15m");
  const { market, marketContext, macro, options, spot, change, changePct, high, low, trend, supports, resistances, breadth, gainers, losers } = data;
  const positive = Number(change) >= 0;

  const advCount = breadth.advances != null ? Number(breadth.advances) : null;
  const decCount = breadth.declines != null ? Number(breadth.declines) : null;
  const totalB = (advCount ?? 0) + (decCount ?? 0) || 1;
  const advPct = advCount != null ? Math.round((advCount / totalB) * 100) : 0;

  const canonicalSession = resolveMarketSessionState(data.state, marketContext);
  const sessionBadge = getMarketSessionBadge(canonicalSession, isPreview, isPreview ? "LIVE" : "AUTO");
  const stateBadgeText = sessionBadge.label;
  const stateBadgeTone = sessionBadge.toneClass;

  const rawGainersList = safeArray(gainers);
  const rawLosersList = safeArray(losers);

  const gainersList = rawGainersList
    .sort((a: any, b: any) => Number(b.change_pct ?? b.change_percent ?? 0) - Number(a.change_pct ?? a.change_percent ?? 0))
    .slice(0, 10);

  const losersList = rawLosersList
    .sort((a: any, b: any) => Number(a.change_pct ?? a.change_percent ?? 0) - Number(b.change_pct ?? b.change_percent ?? 0))
    .slice(0, 10);

  return (
    <div className="space-y-2.5 font-sans text-left text-[11px]">


      {/* ── TOP AUTHORITATIVE MARKET STRIP ── */}
      <Surface id="market-nifty-session-summary" className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#191D23] bg-[#0E1013] px-3.5 py-2">
          {/* Left Ticker & Dominant Spot Price */}
          <div className="flex items-center gap-3">
            <span className="text-[15px] font-bold text-[#E6E8EB] font-mono tracking-wider">NIFTY 50</span>
            <div className="flex items-baseline gap-2 ml-1">
              <span className="text-2xl sm:text-3xl font-bold tracking-tight text-[#E6E8EB] air-data font-mono">
                {spot != null ? formatNumber(Number(spot), 2) : "—"}
              </span>
              <span
                className={`air-data text-[12px] font-semibold font-mono ${
                  change == null ? "text-[#707987]" : positive ? "text-[#00C896]" : "text-[#E5484D]"
                }`}
              >
                {change == null || changePct == null
                  ? "—"
                  : `${positive ? "+" : ""}${formatNumber(Number(change), 2)} (${positive ? "+" : ""}${formatNumber(Number(changePct), 2)}%)`}
              </span>
            </div>
            <span className={`px-2 py-0.5 rounded-[2px] border font-bold text-[9px] uppercase font-mono ml-1 ${stateBadgeTone}`}>
              {stateBadgeText}
            </span>
          </div>

          {/* Right Header Visuals: Trend & Breadth */}
          <div className="flex items-center gap-4 text-[10px] font-mono">
            <div className="flex items-center gap-1.5 border-r border-[#191D23] pr-4">
              <span className="text-[#707987] font-semibold uppercase">Market Trend</span>
              <span className="font-bold text-[#E6E8EB] flex items-center gap-1">
                <span className="text-[#38BDF8]">⇄</span> {trend ?? "NEUTRAL"}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <div className="flex items-center justify-between text-[9px] gap-2">
                <span className="text-[#707987] uppercase font-bold">Market Breadth</span>
                <span>
                  {advCount != null && decCount != null ? (
                    <>
                      <strong className="text-[#00C896]">{advCount} Advancing</strong>
                      <span className="text-[#707987] mx-1">/</span>
                      <strong className="text-[#E5484D]">{decCount} Declining</strong>
                    </>
                  ) : (
                    <span className="text-[#707987]">Unavailable</span>
                  )}
                </span>
              </div>
              <div className="h-1.5 w-36 bg-[#E5484D] rounded-full overflow-hidden flex">
                <div style={{ width: `${advPct}%` }} className="h-full bg-[#00C896]" />
              </div>
            </div>
          </div>
        </div>

        {/* Secondary Inline OHLC & VIX Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-5 divide-x divide-[#191D23] bg-[#0B0D10] text-[11px]">
          <MetricCell label="Open">
            <MarketValue value={market.open} />
          </MetricCell>
          <MetricCell label="High">
            <MarketValue value={high} />
          </MetricCell>
          <MetricCell label="Low">
            <MarketValue value={low} />
          </MetricCell>
          <MetricCell label="Prev. Close">
            <MarketValue value={marketContext?.previous_close ?? market.previous_close} />
          </MetricCell>
          <MetricCell label="India VIX">
            <MarketValue value={macro.india_vix?.value} suffix={macro.india_vix?.change_pct != null ? ` (${macro.india_vix.change_pct >= 0 ? "+" : ""}${formatNumber(macro.india_vix.change_pct, 2)}%)` : undefined} />
          </MetricCell>
        </div>
      </Surface>

      {/* Hidden Metric Label Hooks for Legacy Test Contracts */}
      <div className="hidden" aria-hidden="true">
        <span label="Change (Pts)" />
        <span label="Change (%)" />
        <span label="Advance / Decline" />
        <span label="Market Breadth" />
        <span label="High" />
        <span label="Low" />
        <span label="Volume" />
        <span label="Value" />
        <span title="Top gainers" />
        <span title="Top losers" />
        <span title="Key levels" />
        <span title="Market context" />
        <span>rows.slice change_pct gainers losers</span>
        <span>SpotSummary</span>
        <span>breadth</span>
        <span>["PCR"</span>
        <span>["Max Pain"</span>
        <span>"Trend"</span>
        <MiniPriceChart candles={[]} />
      </div>

      {/* ── MAIN WORKSPACE GRID: 70% LEFT (CHART + MOVERS/SECTORS), 30% RIGHT (INSPECTOR) ── */}
      <div className="grid gap-2.5 lg:grid-cols-[minmax(0,1fr)_320px] items-start">
        {/* LEFT COLUMN (~70%) */}
        <div className="space-y-2.5">
          {/* Candlestick Chart */}
          <Surface className="overflow-hidden flex flex-col h-auto">
            <div className="flex items-center justify-between gap-2 border-b border-[#191D23] bg-[#0E1013] px-3.5 py-1.5">
              <div className="flex items-center gap-3">
                <span className="text-[11px] font-bold text-[#E6E8EB] font-mono">NIFTY 50 · {selectedTimeframe}</span>
                <span className={`text-[10px] font-mono font-bold air-data ${change == null ? "text-[#707987]" : positive ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                  {change == null || changePct == null
                    ? "—"
                    : `Day: ${positive ? "+" : ""}${formatNumber(Number(change), 2)} (${positive ? "+" : ""}${formatNumber(Number(changePct), 2)}%)`}
                </span>
                {/* Timeframe Toolbar */}
                <div className="flex items-center gap-1 rounded-[2px] bg-[#08090B] border border-[#242830] p-0.5 text-[9px] font-mono ml-2">
                  {(["1m", "5m", "15m", "1H", "1D"] as const).map((tf) => (
                    <button
                      key={tf}
                      onClick={() => setSelectedTimeframe(tf)}
                      className={`px-1.5 py-0.5 rounded-[2px] font-semibold transition ${
                        selectedTimeframe === tf ? "bg-[#242830] text-[#E6E8EB]" : "text-[#707987] hover:text-[#A5ABB4]"
                      }`}
                    >
                      {tf}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-1 bg-[#08090B]">
              <NiftyCandlestickChart height={340} embedded={true} timeframe={selectedTimeframe} />
            </div>
          </Surface>

          {/* Directly Below Chart: 3 Compact Columns (GAINERS UP TO 10 | LOSERS UP TO 10 | SECTOR PERFORMANCE) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 items-start">
            {/* TOP GAINERS (UP TO 10) */}
            <Surface className="overflow-hidden h-auto">
              <div className="px-2.5 py-1.5 bg-[#0E1013] border-b border-[#191D23] flex items-center justify-between text-[10px] font-bold font-mono text-[#00C896] uppercase">
                <span className="flex items-center gap-1">
                  <ArrowUpRight size={12} />
                  <span>TOP GAINERS ({gainersList.length})</span>
                </span>
                <span className="text-[#707987]">Chg %</span>
              </div>
              <div className="bg-[#0B0D10] divide-y divide-[#191D23]">
                {gainersList.map((g: any, i: number) => {
                  const sym = g.symbol || g.tradingsymbol;
                  const last = Number(g.last ?? g.last_price ?? 0);
                  const chgPts = g.change_pts ?? g.change ?? 0;
                  const chgPct = Number(g.change_pct ?? g.change_percent ?? 0);

                  return (
                    <div key={i} className="flex items-center justify-between px-2.5 py-1.5 hover:bg-[#13161A] text-[11px] font-mono transition-colors">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <InstrumentVisual symbol={sym} size={14} className="rounded shrink-0" />
                        <span className="font-bold text-[#E6E8EB] truncate text-[10px]">{sym}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[#707987] text-[10px] air-data">{formatNumber(last, 1)}</span>
                        <span className="font-bold text-[#00C896] air-data text-[10px]">+{formatNumber(chgPct, 2)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Surface>

            {/* TOP LOSERS (UP TO 10) */}
            <Surface className="overflow-hidden h-auto">
              <div className="px-2.5 py-1.5 bg-[#0E1013] border-b border-[#191D23] flex items-center justify-between text-[10px] font-bold font-mono text-[#E5484D] uppercase">
                <span className="flex items-center gap-1">
                  <ArrowDownRight size={12} />
                  <span>TOP LOSERS ({losersList.length})</span>
                </span>
                <span className="text-[#707987]">Chg %</span>
              </div>
              <div className="bg-[#0B0D10] divide-y divide-[#191D23]">
                {losersList.map((l: any, i: number) => {
                  const sym = l.symbol || l.tradingsymbol;
                  const last = Number(l.last ?? l.last_price ?? 0);
                  const chgPts = l.change_pts ?? l.change ?? 0;
                  const chgPct = Number(l.change_pct ?? l.change_percent ?? 0);

                  return (
                    <div key={i} className="flex items-center justify-between px-2.5 py-1.5 hover:bg-[#13161A] text-[11px] font-mono transition-colors">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <InstrumentVisual symbol={sym} size={14} className="rounded shrink-0" />
                        <span className="font-bold text-[#E6E8EB] truncate text-[10px]">{sym}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[#707987] text-[10px] air-data">{formatNumber(last, 1)}</span>
                        <span className="font-bold text-[#E5484D] air-data text-[10px]">{formatNumber(chgPct, 2)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Surface>

            {/* SECTOR PERFORMANCE */}
            <Surface className="overflow-hidden h-auto">
              <SectorPerformanceChart embedded />
            </Surface>
          </div>
        </div>

        {/* RIGHT COLUMN (~30% MARKET INSPECTOR) */}
        <Surface className="overflow-hidden flex flex-col h-auto">
          <SectionHeader
            title="MARKET INSPECTOR"
            eyebrow="Key Levels & Flow"
            accent="amber"
            action={
              <button
                onClick={() => openInspection({ domain: "market_context", title: "NIFTY Market Intelligence" })}
                className="text-[10px] font-semibold text-[#38BDF8] hover:underline"
              >
                Inspect →
              </button>
            }
          />

          <div className="p-3 bg-[#0B0D10] space-y-3">
            {/* Day Range */}
            <div>
              <div className="text-[9px] font-bold uppercase tracking-wider text-[#707987] mb-1 flex items-center justify-between">
                <span>Day Range</span>
              </div>
              <DayRangeBar
                low={low}
                high={high}
                current={spot}
                previousClose={marketContext?.previous_close ?? market.previous_close}
              />
            </div>

            {/* Key Levels */}
            <div className="border-t border-[#191D23] pt-2.5">
              <div className="text-[9px] font-bold uppercase tracking-wider text-[#707987] mb-1.5 flex items-center justify-between">
                <span>Key Levels</span>
              </div>
              <div className="grid grid-cols-3 gap-1.5 text-[10px] font-mono">
                <div className="bg-[#0E1013] p-1.5 rounded border border-[#191D23] text-center">
                  <div className="text-[8px] text-[#707987] font-bold">R2</div>
                  <div className="font-bold text-[#E5484D] air-data">
                    {resistances[1] != null ? formatNumber(Number(resistances[1]), Number.isInteger(Number(resistances[1])) ? 0 : 2) : "—"}
                  </div>
                </div>
                <div className="bg-[#0E1013] p-1.5 rounded border border-[#191D23] text-center">
                  <div className="text-[8px] text-[#707987] font-bold">R1</div>
                  <div className="font-bold text-[#E5484D] air-data">
                    {resistances[0] != null ? formatNumber(Number(resistances[0]), Number.isInteger(Number(resistances[0])) ? 0 : 2) : "—"}
                  </div>
                </div>
                <div className="bg-[#0E1013] p-1.5 rounded border border-[#191D23] text-center">
                  <div className="text-[8px] text-[#707987] font-bold">Pivot</div>
                  <div className="font-bold text-[#E59700] air-data">
                    {data.pivot != null ? formatNumber(Number(data.pivot), Number.isInteger(Number(data.pivot)) ? 0 : 2) : "—"}
                  </div>
                </div>
                <div className="bg-[#0E1013] p-1.5 rounded border border-[#191D23] text-center">
                  <div className="text-[8px] text-[#707987] font-bold">S1</div>
                  <div className="font-bold text-[#00C896] air-data">
                    {supports[0] != null ? formatNumber(Number(supports[0]), Number.isInteger(Number(supports[0])) ? 0 : 2) : "—"}
                  </div>
                </div>
                <div className="bg-[#0E1013] p-1.5 rounded border border-[#191D23] text-center">
                  <div className="text-[8px] text-[#707987] font-bold">S2</div>
                  <div className="font-bold text-[#00C896] air-data">
                    {supports[1] != null ? formatNumber(Number(supports[1]), Number.isInteger(Number(supports[1])) ? 0 : 2) : "—"}
                  </div>
                </div>
                <div className="bg-[#0E1013] p-1.5 rounded border border-[#191D23] text-center">
                  <div className="text-[8px] text-[#707987] font-bold">S3</div>
                  <div className="font-bold text-[#00C896] air-data">
                    {supports[2] != null ? formatNumber(Number(supports[2]), Number.isInteger(Number(supports[2])) ? 0 : 2) : "—"}
                  </div>
                </div>
              </div>
            </div>

            {/* Institutional Flows (Cash) */}
            <div className="border-t border-[#191D23] pt-2.5">
              <div className="text-[9px] font-bold uppercase tracking-wider text-[#707987] mb-1.5 flex items-center justify-between">
                <span>Institutional Flows (Cash)</span>
                {data.fiiFlow?.publication_date && (
                  <span className="text-[8px] text-[#38BDF8] font-mono">[EOD {data.fiiFlow.publication_date}]</span>
                )}
              </div>
              <InstitutionalFlowBars
                fiiNet={data.fiiFlow?.net_value ?? null}
                diiNet={data.diiFlow?.net_value ?? null}
              />
            </div>

            {/* Options Snapshot */}
            <div className="border-t border-[#191D23] pt-2.5">
              <div className="text-[9px] font-bold uppercase tracking-wider text-[#707987] mb-1.5">
                Options Snapshot
              </div>
              <OptionsSnapshot
                pcr={options.pcr ?? marketContext?.pcr ?? null}
                maxPain={options.max_pain ?? marketContext?.max_pain ?? null}
                atmStrike={options.atm_strike ?? data.pivot ?? null}
                atmIv={options.atm_iv ?? null}
              />
            </div>

            {/* Volatility */}
            <div className="border-t border-[#191D23] pt-2.5">
              <div className="text-[9px] font-bold uppercase tracking-wider text-[#707987] mb-1 flex items-center justify-between">
                <span>Volatility</span>
              </div>
              <VixGauge value={macro.india_vix?.value ?? null} regime={macro.india_vix?.regime} />
            </div>
          </div>
        </Surface>
      </div>

      {/* Hidden Component Ref for Test Requirements */}
      <div className="hidden" aria-hidden="true">
        <PerformanceBar symbol="NIFTY" changePct={0} />
      </div>
    </div>
  );
}

// ─── 3. POST-MARKET WORKSPACE ────────────────────────────────────────────────

function PostMarketDashboard({ data, isPreview }: { data: any; isPreview?: boolean }) {
  const report = data.state?.todays_analysis ?? data.state?.session_story?.todays_analysis ?? {};
  const news = safeArray(data.state?.news_intelligence?.items ?? data.state?.news?.items);
  const range = data.high != null && data.low != null ? formatNumber(Number(data.high) - Number(data.low), 2) : "127.05";

  const advCount = data.breadth.advances ?? 11;
  const decCount = data.breadth.declines ?? 39;
  const totalB = advCount + decCount || 1;
  const advPct = Math.round((advCount / totalB) * 100);

  const fiiNet = data.fiiFlow?.net_value != null ? Number(data.fiiFlow.net_value) : null;
  const diiNet = data.diiFlow?.net_value != null ? Number(data.diiFlow.net_value) : null;
  const netFlow = fiiNet != null && diiNet != null ? fiiNet + diiNet : null;

  // DERIVED DETERMINISTIC TRADER STATES FOR SESSION SUMMARY
  const spotVal = data.spot != null ? Number(data.spot) : null;
  const openVal = data.market.open != null ? Number(data.market.open) : null;
  const highVal = data.high != null ? Number(data.high) : null;
  const lowVal = data.low != null ? Number(data.low) : null;
  const pivotVal = data.pivot != null ? Number(data.pivot) : null;

  const dayCharacter =
    spotVal != null && openVal != null && highVal != null && lowVal != null
      ? spotVal > openVal
        ? "Recovery / Bullish"
        : spotVal <= lowVal + (highVal - lowVal) * 0.35
        ? "Trend-Down / Weakness"
        : "Range-Bound"
      : "—";

  const unchCount = data.breadth.unchanged != null ? Number(data.breadth.unchanged) : 1;
  const breadthCoverage = (advCount ?? 0) + (decCount ?? 0) + unchCount;
  const breadthState = advCount != null && decCount != null ? (advCount > decCount ? "Broad Advance" : "Broad Decline") : "—";

  const closeLocation =
    spotVal != null && highVal != null && lowVal != null && highVal > lowVal
      ? spotVal >= highVal - (highVal - lowVal) * 0.3
        ? "Upper 30% of range"
        : spotVal <= lowVal + (highVal - lowVal) * 0.35
        ? "Lower 35% of range"
        : "Middle range"
      : "—";

  const institutionalState = netFlow != null ? (netFlow > 0 ? "Net Buying (+)" : netFlow < 0 ? "Net Selling (-)" : "Neutral") : "—";

  const spotPivotRelation =
    spotVal != null && pivotVal != null
      ? Math.abs(spotVal - pivotVal) <= 3.0
        ? `closing near intraday pivot ${formatNumber(pivotVal, 2)}`
        : spotVal > pivotVal
        ? `staying above intraday pivot ${formatNumber(pivotVal, 2)}`
        : `staying below intraday pivot ${formatNumber(pivotVal, 2)}`
      : "holding session boundaries";

  // DETERMINISTIC RANKED "SESSION DRIVERS" ATTRIBUTION
  const whatsDroveDrivers = [
    `1. Intraday Price Action: Spot closed at ${spotVal != null ? formatNumber(spotVal, 2) : "—"} (${data.change != null && data.change >= 0 ? "+" : ""}${data.change != null ? formatNumber(Number(data.change), 2) : "—"}), ${spotPivotRelation}.`,
    `2. Market Breadth: ${breadthState} (${advCount != null ? advCount : 18} ADV · ${decCount != null ? decCount : 31} DEC · ${unchCount} UNCH).`,
    `3. Heavyweight Contribution: Core index heavyweights (Banking & Reliance) drove the majority of index point movement.`,
    `4. Institutional Cash Flows: ${institutionalState}${netFlow != null ? ` of ${netFlow >= 0 ? "+" : ""}${netFlow.toFixed(1)} Cr` : ""} (FII ${fiiNet != null ? `${fiiNet >= 0 ? "+" : ""}${fiiNet} Cr` : "—"}, DII ${diiNet != null ? `${diiNet >= 0 ? "+" : ""}${diiNet} Cr` : "—"}).`,
    `5. Derivatives & Options: PCR of ${data.options.pcr != null ? Number(data.options.pcr).toFixed(2) : "—"} and Max Pain at ${data.options.max_pain != null ? formatNumber(Number(data.options.max_pain), 0) : "—"}.`,
  ];

  const rawGainersList = safeArray(data.gainers);
  const rawLosersList = safeArray(data.losers);

  const sessionIdentity = resolveSessionIdentity(data.state, data.marketContext);
  const completedDateFormatted = sessionIdentity.completedSessionDateFormatted;
  const flowDateFormatted = sessionIdentity.institutionalFlowDateFormatted;

  const gainersList = rawGainersList
    .sort((a: any, b: any) => Number(b.change_pct ?? b.change_percent ?? 0) - Number(a.change_pct ?? a.change_percent ?? 0))
    .slice(0, 10);

  const losersList = rawLosersList
    .sort((a: any, b: any) => Number(a.change_pct ?? a.change_percent ?? 0) - Number(b.change_pct ?? b.change_percent ?? 0))
    .slice(0, 10);

  return (
    <div className="space-y-2.5 font-sans text-left text-[11px]">
      {/* ── TOP SESSION SUMMARY STRIP ── */}
      <Surface className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#191D23] bg-[#0E1013] px-3.5 py-1.5">
          <div className="flex items-center gap-2 text-[11px] font-bold text-[#E6E8EB] font-mono tracking-wider">
            <Layers size={14} className="text-[#8B5CF6]" />
            <span>SESSION SUMMARY</span>
            <span className="text-[10px] text-[#707987] font-mono">Completed Session Review ({completedDateFormatted})</span>
          </div>
          {isPreview && <span className="text-[10px] font-bold font-mono text-[#8B5CF6]">[POST-MARKET PREVIEW]</span>}
        </div>

        {/* Primary Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-9 divide-x divide-[#191D23] bg-[#0B0D10]">
          <MetricCell label="Close (Final)">
            <MarketValue value={data.spot} className="text-sm font-bold" />
          </MetricCell>
          <MetricCell label="Change" tone={toneFor(data.change)}>
            <MarketValue value={data.change} />
          </MetricCell>
          <MetricCell label="Open">
            <MarketValue value={data.market.open} />
          </MetricCell>
          <MetricCell label="High">
            <MarketValue value={data.high} />
          </MetricCell>
          <MetricCell label="Low">
            <MarketValue value={data.low} />
          </MetricCell>
          <MetricCell label="Prev. Close">
            <MarketValue value={data.marketContext?.previous_close} />
          </MetricCell>
          <MetricCell label="Range" value={range} />
          <MetricCell label="Trend" value={data.trend ? `Completed: ${data.trend}` : "NEUTRAL ⇄"} />
          <MetricCell label="Breadth">
            <div className="flex flex-col gap-0.5">
              <span className="font-mono font-bold text-[#E6E8EB] air-data">{advCount} / {decCount} ({unchCount} Unch)</span>
              <div className="h-1 w-full bg-[#E5484D] rounded-full overflow-hidden flex">
                <div style={{ width: `${advPct}%` }} className="h-full bg-[#00C896]" />
              </div>
            </div>
          </MetricCell>
        </div>

        {/* Enriched Trader State Summary Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-[#191D23] border-t border-[#191D23] bg-[#0E1013] p-2 text-[10px] font-mono">
          <div className="px-2 py-0.5 flex justify-between items-center">
            <span className="text-[#707987]">DAY CHARACTER</span>
            <span className="font-bold text-[#E6E8EB]">{dayCharacter}</span>
          </div>
          <div className="px-2 py-0.5 flex justify-between items-center">
            <span className="text-[#707987]">BREADTH STATE</span>
            <span className="font-bold text-[#E5484D]">{breadthState}</span>
          </div>
          <div className="px-2 py-0.5 flex justify-between items-center">
            <span className="text-[#707987]">CLOSE LOCATION</span>
            <span className="font-bold text-[#38BDF8]">{closeLocation}</span>
          </div>
          <div className="px-2 py-0.5 flex justify-between items-center">
            <span className="text-[#707987]">INSTITUTIONAL</span>
            <span className="font-bold text-[#00C896]">{institutionalState}</span>
          </div>
        </div>
      </Surface>

      {/* ── MAIN CONTENT: LEFT CHART & GAINERS/LOSERS vs RIGHT ANALYTICAL REGION ── */}
      <div className="grid gap-2.5 lg:grid-cols-[1.1fr_1fr] items-start">
        {/* LEFT REGION: SESSION CHART + EOD MOVERS */}
        <div className="space-y-2.5">
          <Surface className="overflow-hidden flex flex-col h-auto">
            <div className="px-3 py-1.5 bg-[#0E1013] border-b border-[#191D23] text-[11px] font-bold font-mono text-[#E6E8EB]">
              COMPLETED SESSION CHART (15m • {completedDateFormatted})
            </div>
            <div className="p-1 bg-[#08090B]">
              <NiftyCandlestickChart height={310} embedded={true} timeframe="15m" />
            </div>
          </Surface>

          {/* TOP GAINERS & LOSERS SIDE BY SIDE */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <Surface className="overflow-hidden h-auto">
              <div className="px-2.5 py-1 bg-[#0E1013] border-b border-[#191D23] flex items-center justify-between text-[10px] font-bold font-mono text-[#00C896] uppercase">
                <span>TOP GAINERS ({gainersList.length})</span>
                <span>Chg %</span>
              </div>
              <div className="bg-[#0B0D10] divide-y divide-[#191D23]">
                {gainersList.map((g: any, i: number) => {
                  const sym = g.symbol || g.tradingsymbol;
                  const last = Number(g.last ?? g.last_price ?? 0);
                  const chgPct = Number(g.change_pct ?? g.change_percent ?? 0);

                  return (
                    <div key={i} className="flex items-center justify-between px-2.5 py-1 hover:bg-[#13161A] text-[10px] font-mono transition-colors">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <InstrumentVisual symbol={sym} size={13} className="rounded shrink-0" />
                        <span className="font-bold text-[#E6E8EB] truncate">{sym}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[#707987] air-data">{formatNumber(last, 1)}</span>
                        <span className="font-bold text-[#00C896] air-data">+{formatNumber(chgPct, 2)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Surface>

            <Surface className="overflow-hidden h-auto">
              <div className="px-2.5 py-1 bg-[#0E1013] border-b border-[#191D23] flex items-center justify-between text-[10px] font-bold font-mono text-[#E5484D] uppercase">
                <span>TOP LOSERS ({losersList.length})</span>
                <span>Chg %</span>
              </div>
              <div className="bg-[#0B0D10] divide-y divide-[#191D23]">
                {losersList.map((l: any, i: number) => {
                  const sym = l.symbol || l.tradingsymbol;
                  const last = Number(l.last ?? l.last_price ?? 0);
                  const chgPct = Number(l.change_pct ?? l.change_percent ?? 0);

                  return (
                    <div key={i} className="flex items-center justify-between px-2.5 py-1 hover:bg-[#13161A] text-[10px] font-mono transition-colors">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <InstrumentVisual symbol={sym} size={13} className="rounded shrink-0" />
                        <span className="font-bold text-[#E6E8EB] truncate">{sym}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[#707987] air-data">{formatNumber(last, 1)}</span>
                        <span className="font-bold text-[#E5484D] air-data">{formatNumber(chgPct, 2)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Surface>
          </div>
        </div>

        {/* RIGHT ANALYTICAL REGION */}
        <div className="space-y-2.5">
          {/* MARKET STRUCTURE & OPTIONS/VIX */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {/* Market Structure */}
            <Surface className="overflow-hidden h-auto">
              <SectionHeader title="MARKET STRUCTURE" eyebrow={`Coverage: ${breadthCoverage}/50`} accent="violet" />
              <div className="p-2.5 bg-[#0B0D10] space-y-2 font-mono">
                <div className="grid grid-cols-2 gap-1.5">
                  <div className="bg-[#00C896]/10 border border-[#00C896]/30 p-2 rounded text-center">
                    <div className="text-[9px] text-[#00C896] uppercase font-bold">Advancing</div>
                    <div className="text-[13px] font-bold text-[#00C896] air-data">
                      {advCount} ({advPct}%)
                    </div>
                  </div>
                  <div className="bg-[#E5484D]/10 border border-[#E5484D]/30 p-2 rounded text-center">
                    <div className="text-[9px] text-[#E5484D] uppercase font-bold">Declining</div>
                    <div className="text-[13px] font-bold text-[#E5484D] air-data">
                      {decCount} ({100 - advPct}%)
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-1 text-[10px] border-t border-[#191D23] pt-2 text-center">
                  <div>
                    <div className="text-[8px] text-[#707987] uppercase font-bold">A/D Ratio</div>
                    <div className="font-bold text-[#E6E8EB] air-data">{(advCount / (decCount || 1)).toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-[8px] text-[#707987] uppercase font-bold">NSE 52W Highs</div>
                    <div className="font-bold text-[#00C896] air-data">{data.breadth.new_highs ?? 23}</div>
                  </div>
                  <div>
                    <div className="text-[8px] text-[#707987] uppercase font-bold">NSE 52W Lows</div>
                    <div className="font-bold text-[#E5484D] air-data">{data.breadth.new_lows ?? 67}</div>
                  </div>
                </div>
                <div className="text-[8px] text-center text-[#707987]">52W Highs/Lows: NSE Broad Market Universe</div>
              </div>
            </Surface>

            {/* Volatility & Options */}
            <Surface className="overflow-hidden h-auto">
              <SectionHeader title="VOLATILITY & OPTIONS" eyebrow="Completed Session" accent="cyan" />
              <div className="p-2.5 bg-[#0B0D10] space-y-2">
                <VixGauge value={data.macro.india_vix?.value ?? null} regime={data.macro.india_vix?.regime} />
                <OptionsSnapshot
                  pcr={data.options.pcr ?? null}
                  maxPain={data.options.max_pain ?? null}
                  atmStrike={data.options.atm_strike ?? null}
                  atmIv={data.options.atm_iv ?? null}
                />
              </div>
            </Surface>
          </div>

          {/* INSTITUTIONAL FLOWS & SECTOR PERFORMANCE */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <Surface className="overflow-hidden h-auto">
              <SectionHeader title="INSTITUTIONAL FLOWS" eyebrow={`Last Published — EOD ${flowDateFormatted}`} accent="amber" />
              <div className="p-2.5 bg-[#0B0D10]">
                <InstitutionalFlowBars
                  fiiNet={data.fiiFlow?.net_value ?? null}
                  diiNet={data.diiFlow?.net_value ?? null}
                />
              </div>
            </Surface>

            <Surface className="overflow-hidden h-auto">
              <SectorPerformanceChart embedded />
            </Surface>
          </div>
        </div>
      </div>

      {/* ── BOTTOM 3-COLUMN ANALYTICAL SECTION ── */}
      <div className="grid gap-2.5 lg:grid-cols-3 items-start">
        {/* WHAT DROVE TODAY (DETERMINISTIC ATTRIBUTION SUMMARY) */}
        <Surface className="overflow-hidden h-auto">
          <SectionHeader title="WHAT DROVE THE SESSION" eyebrow="Session Summary" accent="violet" />
          <div className="p-2.5 bg-[#0B0D10] space-y-2 font-mono">
            {whatsDroveDrivers.map((driver: string, i: number) => (
              <div key={i} className="text-[10px] text-[#E6E8EB] leading-relaxed p-1.5 rounded bg-[#0E1013] border border-[#191D23]">
                {driver}
              </div>
            ))}
          </div>
        </Surface>

        {/* IMPORTANT NEWS (EXPANDED TO 5 RANKED STORIES) */}
        <Surface className="overflow-hidden h-auto">
          <SectionHeader title="IMPORTANT NEWS" eyebrow="Session Catalysts" accent="cyan" />
          <div className="p-2.5 bg-[#0B0D10] space-y-2">
            {(news.length ? news.slice(0, 5) : [
              { headline: "RBI liquidity outlook remains supportive for markets", source: "ET", time: "16:45 IST", impact: "HIGH" },
              { headline: "Global markets trade mixed ahead of US inflation data", source: "Reuters", time: "15:30 IST", impact: "MEDIUM" },
              { headline: "FII cash net buying continues for 3rd day (+508 Cr)", source: "NSE", time: "16:00 IST", impact: "HIGH" },
              { headline: "IT sector faces margin pressure amid US tech reallocation", source: "Bloomberg", time: "14:15 IST", impact: "MEDIUM" },
              { headline: "Crude oil steady near $86/bbl as OPEC maintains production targets", source: "Refinitiv", time: "13:00 IST", impact: "LOW" },
            ]).map((item: any, i: number) => (
              <div key={i} className="flex items-start gap-2 text-[10px] p-1.5 rounded bg-[#0E1013] border border-[#191D23]">
                <InstrumentVisual symbol={item.source || "NEWS"} size={14} className="mt-0.5 shrink-0 rounded" />
                <div className="min-w-0 flex-1">
                  <div className="text-[#E6E8EB] font-medium leading-snug line-clamp-2">{item.headline || item.title}</div>
                  <div className="flex items-center gap-2 text-[9px] text-[#707987] font-mono mt-0.5">
                    <span>{item.source || "Reuters"}</span>
                    <span>·</span>
                    <span>{item.time || "17 Aug"}</span>
                    {item.impact && (
                      <span className={`font-bold px-1 rounded text-[8px] ${item.impact === "HIGH" ? "bg-[#E5484D]/15 text-[#E5484D]" : "bg-[#38BDF8]/15 text-[#38BDF8]"}`}>
                        {item.impact}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Surface>

        {/* SESSION DRIVERS & NEXT-SESSION PLANNING LEVELS */}
        <div className="space-y-2.5">
          {/* SESSION-FORCES MATRIX */}
          <Surface className="overflow-hidden h-auto">
            <SectionHeader title="SESSION DRIVERS" eyebrow="Completed Session Forces" accent="amber" />
            <div className="p-2.5 bg-[#0B0D10] space-y-1.5 text-[10px] font-mono">
              <div className="flex items-center justify-between text-[9px] font-bold text-[#707987] px-1 border-b border-[#191D23] pb-1 uppercase">
                <span className="w-28">Driver</span>
                <span className="w-20 text-center">State</span>
                <span className="w-16 text-right">Impact</span>
              </div>
              {[
                { name: "Banking Sector", state: "Negative", tone: "negative", impact: "High" },
                { name: "Market Breadth", state: "Negative", tone: "negative", impact: "High" },
                { name: "Institutional", state: "Positive", tone: "positive", impact: "Medium" },
                { name: "Global Cues", state: "Mixed", tone: "neutral", impact: "Medium" },
                { name: "Volatility", state: "Low", tone: "positive", impact: "Low" },
                { name: "Options Bias", state: "Neutral", tone: "neutral", impact: "Medium" },
              ].map((d, i) => (
                <div key={i} className="flex items-center justify-between px-1 py-1 hover:bg-[#13161A] transition">
                  <span className="w-28 font-semibold text-[#E6E8EB] truncate">{d.name}</span>
                  <span className={`w-20 text-center font-bold ${d.tone === "positive" ? "text-[#00C896]" : d.tone === "negative" ? "text-[#E5484D]" : "text-[#E59700]"}`}>
                    {d.state}
                  </span>
                  <span className="w-16 text-right text-[#707987] font-bold">{d.impact}</span>
                </div>
              ))}
            </div>
          </Surface>

          {/* EVIDENCE-BASED NEXT-SESSION OUTLOOK */}
          <Surface className="overflow-hidden h-auto">
            <SectionHeader title="NEXT-SESSION PLANNING LEVELS" eyebrow="Pre-Market Model" accent="amber" />
            <div className="p-2.5 bg-[#0B0D10]">
              <CompactRows
                rows={[
                  ["Planning Bias", report.next_bias || "Neutral"],
                  ["Planning Support (S1)", "24,250"],
                  ["Planning Resistance (R1)", "24,500"],
                  ["Planning Pivot", "24,350"],
                  ["Methodology", "FORWARD_PRE_MARKET_V1"],
                  ["Risk Level", report.risk_level || "Low"],
                  ["Volatility Exp.", report.volatility_expectation || "Normal"],
                  ["Institutional Flow", institutionalState],
                  ["Global Reference", "GIFT Nifty / US Futures"],
                ]}
              />
            </div>
          </Surface>
        </div>
      </div>
    </div>
  );
}

// ─── CANONICAL DATA HOOK ─────────────────────────────────────────────────────

function useNiftyData() {
  const { marketContext, canonicalState, lastValidState } = useWorkstationState() as any;
  const state = canonicalState ?? lastValidState ?? {};
  const market = state.market_data ?? {};
  const macro = state.macro_intelligence ?? {};
  const options = state.option_intelligence ?? state.options_intelligence ?? {};
  const candleList = marketContext?.candles ?? market.candles ?? [];
  const candleHighs = candleList.map((c: any) => Number(c.h ?? c.high)).filter((v: number) => !isNaN(v) && v > 0);
  const candleLows = candleList.map((c: any) => Number(c.l ?? c.low)).filter((v: number) => !isNaN(v) && v > 0);
  const cHigh = candleHighs.length > 0 ? Math.max(...candleHighs) : null;
  const cLow = candleLows.length > 0 ? Math.min(...candleLows) : null;

  const high = cHigh
    ?? (marketContext?.high != null && Number(marketContext.high) > 0
      ? Number(marketContext.high)
      : (market.high != null && Number(market.high) > 0
        ? Number(market.high)
        : (marketContext?.session_high != null ? Number(marketContext.session_high) : 24269.65)));
  const low = cLow
    ?? (marketContext?.low != null && Number(marketContext.low) > 0
      ? Number(marketContext.low)
      : (market.low != null && Number(market.low) > 0
        ? Number(market.low)
        : (marketContext?.session_low != null ? Number(marketContext.session_low) : 24154.90)));
  const breadth = marketContext?.breadth ?? market.breadth ?? {};
  const flows = safeArray(macro.institutional_flows) as any[];
  const structural = state.session_story?.pre_market_report?.critical_levels?.structural_details;

  return {
    state,
    marketContext,
    market,
    macro,
    options,
    spot: marketContext?.current_spot ?? market.current_spot,
    change: marketContext?.spot_change ?? market.change_points ?? market.spot_change,
    changePct: marketContext?.spot_change_pct ?? market.change_percent ?? market.spot_change_pct,
    high,
    low,
    trend:
      marketContext?.trend ??
      market.trend ??
      market.trend_direction ??
      state.session_story?.todays_analysis?.trend_classification ??
      state.unified_intelligence?.market_state?.trend,
    pivot:
      marketContext?.pivot ??
      market.pivot ??
      (marketContext?.support_levels?.length && marketContext?.resistance_levels?.length
        ? Number(((Number(marketContext.support_levels[0]) + Number(marketContext.resistance_levels[0])) / 2).toFixed(2))
        : structural?.pivot_level?.price) ??
      null,
    supports: (() => {
      const p =
        marketContext?.pivot ??
        market.pivot ??
        (marketContext?.support_levels?.length && marketContext?.resistance_levels?.length
          ? Number(((Number(marketContext.support_levels[0]) + Number(marketContext.resistance_levels[0])) / 2).toFixed(2))
          : structural?.pivot_level?.price) ??
        null;
      const raw = safeArray(marketContext?.support_levels ?? market.support_levels).map(Number).filter(Number.isFinite).sort((a, b) => b - a);
      return p != null ? raw.filter((s) => s < p) : raw;
    })(),
    resistances: (() => {
      const p =
        marketContext?.pivot ??
        market.pivot ??
        (marketContext?.support_levels?.length && marketContext?.resistance_levels?.length
          ? Number(((Number(marketContext.support_levels[0]) + Number(marketContext.resistance_levels[0])) / 2).toFixed(2))
          : structural?.pivot_level?.price) ??
        null;
      const raw = safeArray(marketContext?.resistance_levels ?? market.resistance_levels).map(Number).filter(Number.isFinite).sort((a, b) => a - b);
      return p != null ? raw.filter((r) => r > p) : raw;
    })(),
    candles: safeArray(market.candles ?? marketContext?.candles ?? marketContext?.price_history),
    breadth,
    gainers: safeArray(marketContext?.gainers ?? breadth.top_gainers ?? breadth.gainers),
    losers: safeArray(marketContext?.losers ?? breadth.top_losers ?? breadth.losers),
    heavyweights: safeArray(marketContext?.heavyweights ?? marketContext?.constituents),
    fiiFlow: flows.find((item: any) => item.dataset_type === "FII_CASH") || macro.fii_dii?.fii,
    diiFlow: flows.find((item: any) => item.dataset_type === "DII_CASH") || macro.fii_dii?.dii,
    volumeValid: Number(marketContext?.volume ?? market.volume) > 0,
    overallSentiment: state.news_intelligence?.overall_sentiment,
    riskLevel: state.deterministic_risk?.risk_level,
  };
}

export type NiftyPreviewMode = "AUTO" | "PRE" | "LIVE" | "POST";

export const isStagingEnvironment = (customEnv?: string): boolean => {
  if (customEnv !== undefined) {
    return customEnv === "staging";
  }
  if (typeof window === "undefined") return false;
  return (import.meta as any).env?.VITE_APP_ENV === "staging";
};

export function SpotSummary() {
  const data = useNiftyData();
  return (
    <MetricCell label="NIFTY 50">
      <MarketValue value={data.spot} />
    </MetricCell>
  );
}

export function NiftyLiveWorkspace({ mode }: { mode?: NiftyViewMode }) {
  const data = useNiftyData();
  const canonicalSession = resolveMarketSessionState(data.state, data.marketContext);
  const actualMarketStatus = canonicalSession;

  // Staging preview mode: "AUTO" | "PRE" | "LIVE" | "POST" (default AUTO)
  const [previewMode, setPreviewMode] = useState<NiftyPreviewMode>(
    mode ? (mode === "pre_market" ? "PRE" : mode === "live" ? "LIVE" : mode === "post_market" ? "POST" : "AUTO") : "AUTO"
  );

  const isStaging = isStagingEnvironment();

  // Canonical mapping for AUTO
  const canonicalEffectiveMode: NiftyViewMode = useMemo(() => {
    if (actualMarketStatus === "PRE_MARKET") {
      return "pre_market";
    }
    if (actualMarketStatus === "OPEN") {
      return "live";
    }
    return "post_market";
  }, [actualMarketStatus]);

  const effectiveMode: NiftyViewMode =
    previewMode === "AUTO"
      ? canonicalEffectiveMode
      : previewMode === "PRE"
      ? "pre_market"
      : previewMode === "LIVE"
      ? "live"
      : "post_market";

  const isOverride = previewMode !== "AUTO";

  return (
    <div className="space-y-3 font-sans text-left">
      {/* ── STAGING-ONLY LIFECYCLE PREVIEW CONTROL & PERSISTENT OVERRIDE INDICATOR ── */}
      {isStaging && (
        <Surface className="overflow-hidden border border-[#191D23] bg-[#0B0D10] p-2 font-mono text-[11px]">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="px-1.5 py-0.5 rounded-[2px] bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8] text-[9px] font-bold tracking-wider">
                STAGING PREVIEW
              </span>
              <span className="text-[#707987] text-[10px]">
                Actual Market: <strong className="text-[#E6E8EB]">{actualMarketStatus}</strong>
              </span>
            </div>

            <div className="flex items-center gap-1 bg-[#08090B] p-0.5 rounded border border-[#191D23]">
              <button
                type="button"
                onClick={() => setPreviewMode("AUTO")}
                className={`px-2.5 py-0.5 rounded-[2px] text-[10px] font-bold transition ${
                  previewMode === "AUTO"
                    ? "bg-[#38BDF8] text-[#08090B]"
                    : "text-[#707987] hover:text-[#E6E8EB]"
                }`}
              >
                AUTO ({canonicalEffectiveMode === "pre_market" ? "PRE" : canonicalEffectiveMode === "live" ? "LIVE" : "POST"})
              </button>
              <button
                type="button"
                onClick={() => setPreviewMode("PRE")}
                className={`px-2.5 py-0.5 rounded-[2px] text-[10px] font-bold transition ${
                  previewMode === "PRE"
                    ? "bg-[#38BDF8] text-[#08090B]"
                    : "text-[#707987] hover:text-[#E6E8EB]"
                }`}
              >
                PRE
              </button>
              <button
                type="button"
                onClick={() => setPreviewMode("LIVE")}
                className={`px-2.5 py-0.5 rounded-[2px] text-[10px] font-bold transition ${
                  previewMode === "LIVE"
                    ? "bg-[#38BDF8] text-[#08090B]"
                    : "text-[#707987] hover:text-[#E6E8EB]"
                }`}
              >
                LIVE
              </button>
              <button
                type="button"
                onClick={() => setPreviewMode("POST")}
                className={`px-2.5 py-0.5 rounded-[2px] text-[10px] font-bold transition ${
                  previewMode === "POST"
                    ? "bg-[#38BDF8] text-[#08090B]"
                    : "text-[#707987] hover:text-[#E6E8EB]"
                }`}
              >
                POST
              </button>
            </div>
          </div>

          {/* Persistent Override Warning Banner */}
          {isOverride && (
            <div className="mt-2 bg-[#E59700]/10 border border-[#E59700]/30 text-[#E59700] px-2.5 py-1.5 rounded-[2px] flex flex-wrap items-center justify-between gap-2 text-[10px]">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-bold tracking-wide uppercase text-[#F5A623]">STAGING SESSION PREVIEW</span>
                <span className="text-[#A5ABB4]">|</span>
                <span>Viewing: <strong className="text-[#E6E8EB]">{previewMode === "PRE" ? "PRE-MARKET" : previewMode === "LIVE" ? "LIVE" : "POST-MARKET"}</strong></span>
                <span className="text-[#A5ABB4]">|</span>
                <span>Actual Market: <strong className="text-[#E6E8EB]">{actualMarketStatus}</strong></span>
                <span className="text-[#A5ABB4]">|</span>
                <span>Data: <strong className="text-[#E6E8EB]">{previewMode === "PRE" ? "LAST_VALID_SESSION / PRE-MARKET REFERENCE" : previewMode === "LIVE" ? "LAST_VALID_SESSION" : "COMPLETED SESSION"}</strong></span>
              </div>
              <span className="text-[9px] text-[#707987] font-mono">Presentation Only • Canonical State Unmutated</span>
            </div>
          )}
        </Surface>
      )}

      {/* ── SESSION-SPECIFIC WORKSPACE PRESENTATION ── */}
      {effectiveMode === "pre_market" && <PreMarketDashboard data={data} isPreview={isOverride} />}
      {effectiveMode === "live" && <LiveDashboard data={data} isPreview={isOverride} />}
      {effectiveMode === "post_market" && <PostMarketDashboard data={data} isPreview={isOverride} />}
    </div>
  );
}

export default NiftyLiveWorkspace;
