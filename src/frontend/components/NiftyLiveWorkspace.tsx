import React, { useEffect, useRef, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { safeArray, safeNumber, safeString, formatNumber, formatDate } from "../utils/safeHelpers";
import { mapTraderEnum, mapFreshness } from "../utils/traderTerminology";
import { NiftyCandlestickChart } from "./visualizations/NiftyCandlestickChart";
import { OptionChainLadder } from "./visualizations/OptionChainLadder";
import { OpenInterestHeatmap } from "./visualizations/OpenInterestHeatmap";
import { SectorPerformanceChart } from "./visualizations/SectorPerformanceChart";
import { GlobalMarketsDashboard } from "./visualizations/GlobalMarketsDashboard";
import { HistoricalTelemetryCharts } from "./visualizations/HistoricalTelemetryCharts";
import { AIInterpretationCard } from "./AIInterpretationCard";
import { ParticipantPositioningWidget, VolatilityContextWidget } from "./SpecializedIntelligence";
import { ProvenanceLine, SemanticBadge } from "./intelligence/CanonicalPresentation";

export type NiftyLiveView = "overview" | "price-trend" | "options";

function Metric({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return <section className="border-l border-[var(--air-line)] bg-[var(--air-surface)] px-3 py-2.5 text-left first:border-l-0">
    <div className="text-[9px] font-semibold text-slate-500">{label}</div>
    <div className="air-data mt-1 text-sm font-semibold text-white">{value}</div>
    {detail && <div className="mt-1 text-[10px] text-slate-500">{detail}</div>}
  </section>;
}

function useNumericFlash(value: number | null) {
  const previous = useRef<number | null>(null);
  const [flash, setFlash] = useState("");
  useEffect(() => {
    if (value == null) return;
    if (previous.current != null && value !== previous.current) {
      setFlash(value > previous.current ? "air-flash-up" : "air-flash-down");
      const id = setTimeout(() => setFlash(""), 650);
      previous.current = value;
      return () => clearTimeout(id);
    }
    previous.current = value;
  }, [value]);
  return flash;
}

function SpotSummary() {
  const { marketContext, canonicalState } = useWorkstationState() as any;
  const rawSpot = marketContext?.current_spot;
  const spot = rawSpot != null ? safeNumber(rawSpot, 0) : null;
  const dq = canonicalState?.data_quality?.market_data || {};
  const isClosed = Boolean(canonicalState?.market_session?.is_closed || marketContext?.session_mode === "LAST_SESSION" || marketContext?.session_mode === "LAST_VALID_SESSION");
  const hasComparison = typeof marketContext?.spot_change === "number" && typeof marketContext?.spot_change_pct === "number";
  const change = safeNumber(marketContext?.spot_change, 0);
  const flash = useNumericFlash(spot);
  const [showDetails, setShowDetails] = useState(false);

  const qualityStatus = safeString(dq.quality_status).toLowerCase();
  const freshnessStatus = safeString(dq.freshness_status).toLowerCase();
  const hasMaterialWarning = ["stale", "degraded", "partial", "not_configured", "license_required"].some(s => qualityStatus.includes(s) || freshnessStatus.includes(s));

  return <div className={`overflow-hidden rounded-lg border border-[var(--air-line-strong)] bg-[var(--air-surface)] p-4 ${flash}`}>
    <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-3">
      <div>
        <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-cyan-400">
          {isClosed ? `Previous Session · ${dq.observed_at ? formatDate(dq.observed_at) : "Market Closed"}` : "Live Session"}
        </div>
        <h2 className="text-xl font-bold text-white">NIFTY 50</h2>
      </div>
      <div className="air-data text-right">
        <div className="text-3xl font-bold tracking-tight text-white sm:text-4xl">{spot != null ? formatNumber(spot, 2) : "--"}</div>
        <div className="text-xs text-slate-400">{hasComparison ? `${change >= 0 ? "+" : ""}${formatNumber(change, 2)} pts` : "Previous-session comparison unavailable"}</div>
      </div>
    </div>
    <div className="mt-3 flex flex-wrap items-center justify-between gap-4 text-[11px] font-mono text-slate-400">
      <div className="flex flex-wrap items-center gap-3">
        <SemanticBadge value={canonicalState?.market_session?.status || marketContext?.trading_session}/>
        {hasMaterialWarning && (
          <span className="inline-flex items-center gap-1 rounded bg-amber-950/60 px-2 py-0.5 text-[9px] font-bold text-amber-300 border border-amber-800">
            ⚠ {mapTraderEnum(dq.quality_status || dq.freshness_status)}
          </span>
        )}
      </div>
      <button onClick={() => setShowDetails(!showDetails)} className="text-[10px] text-cyan-400 hover:underline flex items-center gap-1 font-mono">
        {showDetails ? "Hide details" : "Data details ⓘ"}
      </button>
    </div>
    {showDetails && (
      <div data-provenance-details className="mt-3 border-t border-slate-800/80 pt-3 text-[10px] space-y-1 text-slate-400 font-mono">
        <div>Source: {dq.source === "kite_historical_api" ? "Kite Historical API" : (dq.source || "Kite API")}</div>
        <div>Observed: {dq.observed_at ? formatDate(dq.observed_at) : "N/A"}</div>
        <div>Data quality: {dq.quality_status === "valid" ? "Validated" : mapTraderEnum(dq.quality_status)}</div>
        <div>Freshness: {isClosed ? "Previous Trading Session" : mapTraderEnum(dq.freshness_status)}</div>
      </div>
    )}
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
    <div className="grid overflow-hidden rounded-lg border border-[var(--air-line)] sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      <Metric label="Market Session" value={mapTraderEnum(canonicalState?.market_session?.status || "UNAVAILABLE")} detail={mapTraderEnum(marketContext?.session_mode || "No observation mode")}/>
      <Metric label="Breadth" value={mapTraderEnum(breadth?.status || "UNAVAILABLE")} detail={`${safeNumber(coverage?.valid, 0)}/50 constituents observed`}/>
      <Metric label="Advances / Declines" value={breadth?.advances != null && breadth?.declines != null ? `${breadth.advances} / ${breadth.declines}` : "UNAVAILABLE"} detail={breadth?.advance_decline_ratio != null ? `A/D ${formatNumber(breadth.advance_decline_ratio, 2)}` : "Minimum coverage: 40/50"}/>
      <Metric label="Sector Coverage" value={sectors.length ? `${sectors.length} indices` : "UNAVAILABLE"} detail="Direct NSE index quotes"/>
      <Metric label="Options Readiness" value={mapTraderEnum(optionStatus)} detail="Detailed options data is isolated to the Options tab."/>
    </div>
    <div className="grid gap-5 lg:grid-cols-2">
      <section className="rounded-lg border border-[var(--air-line)] bg-[var(--air-surface)] p-4 text-left"><div className="flex items-center justify-between border-b border-[var(--air-line)] pb-2"><h3 className="text-[10px] font-bold tracking-wide text-slate-200">Top constituent movers</h3><span className="text-[9px] text-slate-600">{safeNumber(coverage?.valid, 0)}/50 · {mapTraderEnum(breadth?.freshness || "UNAVAILABLE")}</span></div><div className="mt-2 grid grid-cols-2 gap-4">{gainers.length || losers.length ? <>{[["Gainers",gainers,"text-emerald-400","bg-emerald-500/50"],["Losers",losers,"text-rose-400","bg-rose-500/50"]].map(([title,rows,color,bar]:any)=><div key={title}><div className="mb-1 grid grid-cols-[1rem_1fr_auto] gap-2 text-[8px] font-semibold text-slate-600"><span>#</span><span>{title}</span><span>Change</span></div>{rows.map((item:any,index:number)=><div key={`${title}-${item.symbol}-${index}`} className="grid grid-cols-[1rem_1fr_auto] items-center gap-2 border-t border-[var(--air-line)] py-1.5 text-[10px]"><span className="text-slate-600">{index+1}</span><div className="min-w-0"><div className="truncate font-semibold text-slate-200">{safeString(item.symbol)}</div><div className="mt-1 h-0.5 max-w-20 bg-slate-900"><div className={`h-full ${bar}`} style={{width:`${Math.min(100,Math.abs(safeNumber(item.change_pct))*18)}%`}}/></div></div><span className={`air-data font-semibold ${color}`}>{safeNumber(item.change_pct)>=0?"+":""}{formatNumber(item.change_pct,2)}%</span></div>)}</div>)}</> : <p className="col-span-2 text-[10px] text-slate-500">UNAVAILABLE — insufficient constituent observations ({safeNumber(coverage?.valid, 0)}/50).</p>}</div></section>
      <SectorPerformanceChart />
    </div>
    <GlobalMarketsDashboard compact />
    <div className="grid gap-5 lg:grid-cols-2"><ParticipantPositioningWidget compact/><VolatilityContextWidget/></div>
    <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 text-left"><h3 className="text-xs font-bold uppercase text-cyan-300">Headline Risk Summary</h3><div className="mt-2 space-y-1 text-xs text-slate-300">{news.length ? news.slice(0, 3).map((item, index) => <p key={item.id || index}>{safeString(item.headline)} · relevance {formatNumber(item.nifty_relevance_score, 1)}/10</p>) : <p>No headline risk items are available.</p>}</div></section>
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
      <Metric label="EMA 20 / 50" value={marketContext?.ema_20 && marketContext?.ema_50 ? `${formatNumber(marketContext.ema_20, 2)} / ${formatNumber(marketContext.ema_50, 2)}` : "UNAVAILABLE"} detail="Calculated from verified prices"/>
      <Metric label="Trend / Volatility" value={`${mapTraderEnum(marketContext?.market_regime || "UNKNOWN")} · ${mapTraderEnum(marketContext?.trend_direction || "UNKNOWN")} · ${mapTraderEnum(marketContext?.volatility_state || "UNKNOWN")}`}/>
    </div>
    <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 text-left"><h3 className="text-xs font-bold uppercase text-cyan-300">Key Levels to Watch</h3><p className="mt-2 text-xs text-slate-300">Support: {supports.length ? supports.map(v => formatNumber(v, 2)).join(", ") : "UNAVAILABLE"} · Resistance: {resistances.length ? resistances.map(v => formatNumber(v, 2)).join(", ") : "UNAVAILABLE"}</p></section>
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
      <Metric label="Options Snapshot" value={mapTraderEnum(status)} detail={options.timestamp ? `Observed ${formatDate(options.timestamp)}` : "No snapshot timestamp."}/>
      <Metric label="Expiry" value={safeString(options.expiry || options.current_expiry || "UNAVAILABLE")}/>
      <Metric label="PCR / Max Pain" value={options.pcr > 0 || options.max_pain > 0 ? `${formatNumber(options.pcr, 2)} / ${formatNumber(options.max_pain, 0)}` : "UNAVAILABLE"}/>
      <Metric label="Chain Rows / ATM" value={rows.length ? `${rows.length} / ${safeString(options.atm_strike || "UNAVAILABLE")}` : "UNAVAILABLE"}/>
      <Metric label="ATM Option IV" value={safeString(options.iv_status).toUpperCase() === "AVAILABLE" ? `${formatNumber(options.atm_ce_iv, 2)}% / ${formatNumber(options.atm_pe_iv, 2)}%` : "UNAVAILABLE"} detail={`${safeNumber(options.iv_rows, 0)} converged rows`}/>
    </div>
    {status === "UNAVAILABLE" || rows.length === 0 ? <section className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-6 text-left"><h3 className="text-sm font-bold text-amber-300">Options intelligence unavailable</h3><p className="mt-2 text-xs text-slate-400">No option-chain ladder, PCR, Max Pain, IV, OI-change, heatmap, ATM context, expiry and timestamp snapshot is present.</p></section> : <><OptionChainLadder/><OpenInterestHeatmap/></>}
  </div>;
}

export function NiftyLiveWorkspace({ view = "overview" }: { view?: NiftyLiveView }) {
  return <div className="space-y-5">
    {view === "price-trend" ? <PriceTrendPanel /> : view === "options" ? <OptionsPanel /> : <OverviewPanel />}
  </div>;
}
