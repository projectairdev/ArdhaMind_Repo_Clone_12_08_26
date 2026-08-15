import React, { useEffect, useRef, useState, useMemo } from "react";
import { ShieldCheck } from "lucide-react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { safeArray, safeNumber, safeString, formatNumber, formatDate } from "../utils/safeHelpers";
import { formatTimestampIST } from "../utils/timeFormatting";
import { mapTraderEnum } from "../utils/traderTerminology";
import { NiftyCandlestickChart } from "./visualizations/NiftyCandlestickChart";
import { SectorPerformanceChart } from "./visualizations/SectorPerformanceChart";
import { DecisionAreasPanel, DecisionZonesPanel, SemanticBadge } from "./intelligence/CanonicalPresentation";

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

export function SpotSummary() {
  const { marketContext, canonicalState } = useWorkstationState() as any;
  const rawSpot = marketContext?.current_spot;
  const spot = rawSpot != null ? safeNumber(rawSpot, 0) : null;
  const dq = canonicalState?.data_quality?.market_data || {};
  const isClosed = Boolean(
    canonicalState?.market_session?.is_closed ||
    canonicalState?.market_session?.status === "CLOSED" ||
    canonicalState?.market_session?.status === "HOLIDAY" ||
    canonicalState?.market_session?.status === "WEEKEND" ||
    marketContext?.session_mode === "LAST_SESSION" ||
    marketContext?.session_mode === "LAST_VALID_SESSION"
  );
  const mData = canonicalState?.market_data || {};
  const rawChange = marketContext?.spot_change ?? mData.change_points ?? mData.spot_change;
  const rawChangePct = marketContext?.spot_change_pct ?? mData.change_percent ?? mData.spot_change_pct;
  const prevClose = marketContext?.previous_close ?? mData.previous_close;
  const hasComparison = typeof rawChange === "number" && typeof rawChangePct === "number";
  const change = safeNumber(rawChange, 0);
  const changePct = safeNumber(rawChangePct, 0);
  const isPositive = change >= 0;
  const flash = useNumericFlash(spot);

  return (
    <div className={`overflow-hidden rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-surface)] p-4 shadow-sm ${flash}`}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white tracking-tight font-sans">NIFTY 50</h2>
            <SemanticBadge value={canonicalState?.market_session?.status || marketContext?.trading_session} />
          </div>
          <div className="text-[10px] font-mono text-slate-400 mt-0.5">
            {isClosed ? `Session Close · ${dq.observed_at ? formatTimestampIST(dq.observed_at) : "Market Closed"}` : "Live Market Stream"}
          </div>
        </div>

        <div className="air-data text-right flex items-baseline gap-4">
          <div>
            <span className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              {spot != null ? formatNumber(spot, 2) : "--"}
            </span>
          </div>
          <div className={`text-xs font-mono font-bold ${hasComparison ? (isPositive ? "text-emerald-400" : "text-rose-400") : "text-slate-400"}`}>
            {hasComparison ? (
              <span>
                {isPositive ? "+" : ""}{formatNumber(change, 2)} pts ({isPositive ? "+" : ""}{formatNumber(changePct, 2)}%)
                {prevClose ? <span className="ml-2 text-[10px] text-slate-500 font-normal">Prev: {formatNumber(prevClose, 2)}</span> : null}
              </span>
            ) : (
              "Comparison Unavailable"
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function NiftyLiveWorkspace() {
  return (
    <div className="space-y-4 font-sans text-left">
      {/* 1. NIFTY Current Spot & Change Header */}
      <SpotSummary />

      {/* 2. Visually Dominant TradingView Live Chart */}
      <div className="rounded-xl overflow-hidden border border-[var(--air-line-strong)] shadow-sm">
        <NiftyCandlestickChart />
      </div>

      {/* 3. Decision Zones & Key Levels + Sector Performance Grid */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-surface)] p-4">
          <DecisionZonesPanel />
        </div>
        <div className="rounded-xl border border-[var(--air-line-strong)] bg-[var(--air-surface)] p-4">
          <SectorPerformanceChart />
        </div>
      </div>
    </div>
  );
}

export default NiftyLiveWorkspace;
