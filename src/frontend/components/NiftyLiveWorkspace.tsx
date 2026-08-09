import React from "react";
import { ShieldCheck } from "lucide-react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { safeArray, safeNumber, safeString, formatNumber, formatDate } from "../utils/safeHelpers";
import { NiftyCandlestickChart } from "./visualizations/NiftyCandlestickChart";
import { OptionChainLadder } from "./visualizations/OptionChainLadder";
import { OpenInterestHeatmap } from "./visualizations/OpenInterestHeatmap";
import { SectorPerformanceChart } from "./visualizations/SectorPerformanceChart";
import { GlobalMarketsDashboard } from "./visualizations/GlobalMarketsDashboard";
import { HistoricalTelemetryCharts } from "./visualizations/HistoricalTelemetryCharts";
import { AIInterpretationCard } from "./AIInterpretationCard";
import { ParticipantPositioningWidget, VolatilityContextWidget } from "./SpecializedIntelligence";

export type NiftyLiveView = "overview" | "price-trend" | "options";

function Metric({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 text-left">
    <div className="text-[10px] font-mono font-bold uppercase text-cyan-400">{label}</div>
    <div className="mt-2 text-sm font-semibold text-white">{value}</div>
    {detail && <div className="mt-1 text-[10px] text-slate-500">{detail}</div>}
  </section>;
}

function SpotSummary() {
  const { marketContext, canonicalState } = useWorkstationState() as any;
  const rawSpot = marketContext?.current_spot;
  const spot = rawSpot != null ? safeNumber(rawSpot, 0) : null;
  const dq = canonicalState?.data_quality?.market_data || {};
  const isClosed = Boolean(canonicalState?.market_session?.is_closed || marketContext?.session_mode === "LAST_SESSION");
  const hasComparison = typeof marketContext?.spot_change === "number" && typeof marketContext?.spot_change_pct === "number";
  const change = safeNumber(marketContext?.spot_change, 0);
  return <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-950 to-slate-900 p-5">
    <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-3">
      <div><div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-cyan-400">{isClosed ? "Canonical Last Session Summary" : "Canonical Live Summary"}</div><h2 className="text-xl font-bold text-white">NIFTY 50 SPOT {isClosed ? "(CLOSE)" : ""}</h2></div>
      <div className="text-right font-mono"><div className="text-2xl font-bold text-white">{spot != null ? formatNumber(spot, 2) : "--"}</div><div className="text-xs text-slate-400">{hasComparison ? `${change >= 0 ? "+" : ""}${formatNumber(change, 2)} pts` : "Previous-session comparison unavailable"}</div></div>
    </div>
    <div className="mt-3 flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-400">
      <span className="flex items-center gap-1 font-semibold text-emerald-400"><ShieldCheck size={13}/>Quality: {dq.quality_status === "valid" ? "VALIDATED" : safeString(dq.quality_status || "UNAVAILABLE").toUpperCase()}</span>
      <span>Session: {safeString(canonicalState?.market_session?.status || marketContext?.trading_session || "UNAVAILABLE").toUpperCase()}</span>
      <span>Source: {safeString(dq.source || "UNAVAILABLE")}</span>
      <span>Observed: {dq.observed_at ? formatDate(dq.observed_at) : "UNAVAILABLE"}</span>
      <span className="text-amber-400">{isClosed ? "MARKET_CLOSED" : safeString(dq.freshness_status).toUpperCase()}</span>
    </div>
  </div>;
}

function OverviewPanel() {
  const { marketContext, optionContext, canonicalState } = useWorkstationState() as any;
  const news = safeArray(canonicalState?.news_intelligence?.items) as any[];
  const sectors = safeArray(marketContext?.sectors);
  const breadth = marketContext?.breadth || {};
  const coverage = breadth?.coverage || {};
  const gainers = safeArray(breadth?.top_gainers) as any[];
  const losers = safeArray(breadth?.top_losers) as any[];
  const optionStatus = safeString(canonicalState?.option_intelligence?.status || optionContext?.status || "unavailable").toUpperCase();
  return <div data-nifty-panel="overview" className="space-y-5">
    <SpotSummary />
    <div className="grid gap-4 md:grid-cols-5">
      <Metric label="Market Session" value={safeString(canonicalState?.market_session?.status || "UNAVAILABLE").toUpperCase()} detail={safeString(marketContext?.session_mode || "No observation mode")}/>
      <Metric label="Breadth" value={safeString(breadth?.status || "UNAVAILABLE").toUpperCase()} detail={`${safeNumber(coverage?.valid, 0)}/50 constituents observed`}/>
      <Metric label="Advances / Declines" value={breadth?.advances != null && breadth?.declines != null ? `${breadth.advances} / ${breadth.declines}` : "UNAVAILABLE"} detail={breadth?.advance_decline_ratio != null ? `A/D ${formatNumber(breadth.advance_decline_ratio, 2)}` : "Minimum coverage: 40/50"}/>
      <Metric label="Sector Coverage" value={sectors.length ? `${sectors.length} indices` : "UNAVAILABLE"} detail="Direct Kite NSE index quotes"/>
      <Metric label="Options Readiness" value={optionStatus} detail="Detailed options data is isolated to the Options tab."/>
    </div>
    <div className="grid gap-5 lg:grid-cols-2">
      <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 text-left"><h3 className="text-xs font-bold uppercase text-cyan-300">Top Constituent Movers</h3><div className="mt-2 text-xs text-slate-300">{gainers.length || losers.length ? <>{gainers.map((item, index) => <p key={`g-${index}`} className="text-emerald-400">{safeString(item.symbol)} +{formatNumber(item.change_pct, 2)}%</p>)}{losers.map((item, index) => <p key={`l-${index}`} className="text-rose-400">{safeString(item.symbol)} {formatNumber(item.change_pct, 2)}%</p>)}</> : <p>UNAVAILABLE — insufficient validated constituent observations ({safeNumber(coverage?.valid, 0)}/50).</p>}</div></section>
      <SectorPerformanceChart />
    </div>
    <GlobalMarketsDashboard compact />
    <div className="grid gap-5 lg:grid-cols-2"><ParticipantPositioningWidget compact/><VolatilityContextWidget/></div>
    <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 text-left"><h3 className="text-xs font-bold uppercase text-cyan-300">Headline Risk Summary</h3><div className="mt-2 space-y-1 text-xs text-slate-300">{news.length ? news.slice(0, 3).map((item, index) => <p key={item.id || index}>{safeString(item.headline)} · relevance {formatNumber(item.nifty_relevance_score, 1)}/10</p>) : <p>No verified headline risk items are available.</p>}</div></section>
    <AIInterpretationCard title="Market Narrative" sectionKey="market_narrative" />
  </div>;
}

function PriceTrendPanel() {
  const { marketContext } = useWorkstationState() as any;
  const candles = safeArray(marketContext?.candles) as any[];
  const highs = candles.map(c => safeNumber(c.h, NaN)).filter(Number.isFinite);
  const lows = candles.map(c => safeNumber(c.l, NaN)).filter(Number.isFinite);
  const supports = safeArray(marketContext?.support_levels).filter(v => Number.isFinite(Number(v)));
  const resistances = safeArray(marketContext?.resistance_levels).filter(v => Number.isFinite(Number(v)));
  return <div data-nifty-panel="price-trend" className="space-y-5">
    <NiftyCandlestickChart />
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <Metric label="Session High / Low" value={highs.length && lows.length ? `${formatNumber(Math.max(...highs), 2)} / ${formatNumber(Math.min(...lows), 2)}` : "UNAVAILABLE"}/>
      <Metric label="VWAP" value={safeNumber(marketContext?.vwap, 0) > 0 ? formatNumber(marketContext.vwap, 2) : "UNAVAILABLE"}/>
      <Metric label="EMA 20 / 50" value={marketContext?.ema_20 && marketContext?.ema_50 ? `${formatNumber(marketContext.ema_20, 2)} / ${formatNumber(marketContext.ema_50, 2)}` : "UNAVAILABLE"} detail="No derived EMA is fabricated."/>
      <Metric label="Trend / Volatility" value={`${safeString(marketContext?.market_regime || "UNKNOWN")} · ${safeString(marketContext?.trend_direction || "UNKNOWN")} · ${safeString(marketContext?.volatility_state || "UNKNOWN")}`}/>
    </div>
    <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 text-left"><h3 className="text-xs font-bold uppercase text-cyan-300">Deterministic Levels</h3><p className="mt-2 text-xs text-slate-300">Support: {supports.length ? supports.map(v => formatNumber(v, 2)).join(", ") : "UNAVAILABLE"} · Resistance: {resistances.length ? resistances.map(v => formatNumber(v, 2)).join(", ") : "UNAVAILABLE"}</p></section>
    <HistoricalTelemetryCharts />
  </div>;
}

function OptionsPanel() {
  const { canonicalState, optionContext } = useWorkstationState() as any;
  const options = canonicalState?.option_intelligence || optionContext || {};
  const status = safeString(options.status || "unavailable").toUpperCase();
  const rows = safeArray(options.chain || options.option_chain || options.strikes);
  return <div data-nifty-panel="options" className="space-y-5">
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Metric label="Options Snapshot" value={status} detail={options.timestamp ? `Observed ${formatDate(options.timestamp)}` : "No validated snapshot timestamp."}/>
      <Metric label="Expiry" value={safeString(options.expiry || options.current_expiry || "UNAVAILABLE")}/>
      <Metric label="PCR / Max Pain" value={options.pcr > 0 || options.max_pain > 0 ? `${formatNumber(options.pcr, 2)} / ${formatNumber(options.max_pain, 0)}` : "UNAVAILABLE"}/>
      <Metric label="Chain Rows / ATM" value={rows.length ? `${rows.length} / ${safeString(options.atm_strike || "UNAVAILABLE")}` : "UNAVAILABLE"}/>
      <Metric label="ATM Option IV" value={safeString(options.iv_status).toUpperCase() === "AVAILABLE" ? `${formatNumber(options.atm_ce_iv, 2)}% / ${formatNumber(options.atm_pe_iv, 2)}%` : "UNAVAILABLE"} detail={`${safeNumber(options.iv_rows, 0)} converged rows`}/>
    </div>
    {status === "UNAVAILABLE" || rows.length === 0 ? <section className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-6 text-left"><h3 className="text-sm font-bold text-amber-300">Options intelligence unavailable</h3><p className="mt-2 text-xs text-slate-400">No validated option-chain ladder, PCR, Max Pain, IV, OI-change, heatmap, ATM context, expiry and timestamp snapshot is present.</p></section> : <><OptionChainLadder/><OpenInterestHeatmap/></>}
  </div>;
}

export function NiftyLiveWorkspace({ view = "overview" }: { view?: NiftyLiveView }) {
  if (view === "price-trend") return <PriceTrendPanel />;
  if (view === "options") return <OptionsPanel />;
  return <OverviewPanel />;
}
