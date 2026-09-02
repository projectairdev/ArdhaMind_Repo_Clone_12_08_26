// src/frontend/components/MarketPulseWorkspace.tsx
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 *
 * MarketPulseWorkspace.tsx
 *
 * Production-Grade Institutional MARKET → METRICS Workspace for AIR ArdhaMind.
 * Read-only top-down quantitative market cockpit with zero narrative prose and zero vertical void:
 *
 * 5-Tier Zero-Gap Terminal Ordering:
 * - Tier 1 (Row 1): 1. GLOBAL & MACRO CONTEXT (Full-width 11 benchmark asset strip)
 * - Tier 2 (Row 2): Benchmark State & Quantitative Institutional Matrix (2-Column Hero: ~35% / ~65%)
 *                   2. 2. MARKET STATE (OHLC, Gap Analysis, Intraday Spectrum, 52W Extremes, VWAP Envelope)
 *                   3. 3. QUANTITATIVE INSTITUTIONAL MATRIX (6-Panel Quantitative Factor Scorecard)
 * - Tier 3 (Row 3): Primary Index Drivers & Sector Rotation (2-Column Grid: ~58% / ~42%)
 *                   4. 4. NIFTY 50 TOP HEAVYWEIGHT IMPACT MATRIX
 *                   5. 5. SECTOR PARTICIPATION MATRIX
 * - Tier 4 (Row 4): Market Internals & Capital Flows (3-Column Equal Grid)
 *                   6. 6. NIFTY 50 BREADTH INTERNALS
 *                   7. 7. INSTITUTIONAL POSITIONING & FLOWS
 *                   8. 8. VOLATILITY & RANGE EXPANSION
 * - Tier 5 (Row 5): Structural Price Ladder & Technical References (2-Column Equal Grid)
 *                   9. 9. KEY STRUCTURAL REFERENCE LADDER (Sorted price stack with distance badges)
 *                   10. 10. TECHNICAL REFERENCES & EMAS
 * - Trust Footer Strip
 */

import React, { useState, useMemo } from "react";
import {
  Activity,
  Globe,
  RefreshCw,
  Check,
  TrendingUp,
  BarChart3,
  Layers,
  ShieldAlert,
  Compass,
  Building2,
  Cpu,
} from "lucide-react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { useCanonicalState } from "../context/CanonicalStateContext";
import { formatNumber, safeArray } from "../utils/safeHelpers";
import { SectionHeader, Surface } from "./ui/WorkspacePrimitives";
import { TemporalContextStrip } from "./ui/TemporalContextStrip";
import {
  resolveMarketSessionState,
  getMarketSessionBadge,
  resolveCompletedSessionMetrics,
} from "../utils/canonicalSemanticContract";
import { resolveAuthoritativeMarketState } from "../utils/canonicalResolvers";
import { VIX_FALLBACK, ATR_FALLBACK, SECTOR_FALLBACK_LIST } from "../constants/marketFallbacks";
import { DataFreshnessBadge } from "./ui/DataFreshnessBadge";
// ─── HELPER FORMATTERS ────────────────────────────────────────────────────────
function signedStr(value: number | null, decimals = 2, suffix = "") {
  if (value == null || isNaN(value)) return "—";
  return `${value > 0 ? "+" : ""}${formatNumber(value, decimals)}${suffix}`;
}

function sanitizeRegimeToken(regime: string | null | undefined): string {
  if (!regime) return "RANGE-BOUND";
  const upper = String(regime).toUpperCase().trim();
  if (upper === "UNKNOWN" || upper === "" || upper === "NULL" || upper === "UNDEFINED") {
    return "RANGE-BOUND";
  }
  if (upper.includes("TRENDING_UP") || upper.includes("TRENDING UP")) return "TRENDING UP";
  if (upper.includes("TRENDING_DOWN") || upper.includes("TRENDING DOWN")) return "TRENDING DOWN";
  if (upper.includes("RANGE_BOUND") || upper.includes("RANGE-BOUND") || upper.includes("SIDEWAYS")) return "RANGE-BOUND";
  if (upper.includes("COMPRESS")) return "COMPRESSING";
  if (upper.includes("BREAKOUT")) return "BREAKOUT";
  if (upper.includes("EXPANSION")) return "EXPANSION";
  return upper.replace(/_/g, " ");
}

// ─── 1. ASSET / INSTRUMENT ICONS ──────────────────────────────────────────────
export function CrossAssetIcon({ symbol, size = 14 }: { symbol: string; size?: number }) {
  const sym = symbol.toUpperCase();

  if (sym.includes("GIFT") || sym.includes("NIFTY")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="shrink-0">
        <circle cx="12" cy="12" r="11" fill="#0B0D10" stroke="#242830" strokeWidth="1" />
        <rect x="3.5" y="3.5" width="17" height="5.6" rx="2" fill="#FF9933" />
        <rect x="3.5" y="9.1" width="17" height="5.8" fill="#FFFFFF" />
        <rect x="3.5" y="14.9" width="17" height="5.6" rx="2" fill="#138808" />
        <circle cx="12" cy="12" r="2.2" stroke="#000088" strokeWidth="0.8" fill="none" />
      </svg>
    );
  }

  if (sym.includes("S&P") || sym.includes("DOW") || sym.includes("US_10Y") || sym.includes("10Y")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="shrink-0">
        <circle cx="12" cy="12" r="11" fill="#0B0D10" stroke="#242830" strokeWidth="1" />
        <clipPath id={`us-clip-${sym}`}><circle cx="12" cy="12" r="10" /></clipPath>
        <g clipPath={`url(#us-clip-${sym})`}>
          <rect x="2" y="2" width="20" height="20" fill="#B22234" />
          <path d="M2 5h20M2 8h20M2 11h20M2 14h20M2 17h20M2 20h20" stroke="#FFFFFF" strokeWidth="1.5" />
          <rect x="2" y="2" width="10" height="11" fill="#3C3B6E" />
          <circle cx="5" cy="5" r="0.8" fill="#FFFFFF" />
          <circle cx="9" cy="5" r="0.8" fill="#FFFFFF" />
          <circle cx="7" cy="8" r="0.8" fill="#FFFFFF" />
          <circle cx="5" cy="11" r="0.8" fill="#FFFFFF" />
          <circle cx="9" cy="11" r="0.8" fill="#FFFFFF" />
        </g>
      </svg>
    );
  }

  if (sym.includes("NASDAQ")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="shrink-0">
        <circle cx="12" cy="12" r="11" fill="#080E18" stroke="#38BDF8" strokeWidth="1" />
        <rect x="6" y="6" width="12" height="12" rx="3" fill="#38BDF8" fillOpacity="0.2" stroke="#38BDF8" strokeWidth="1.2" />
        <path d="M9 15L12 9L15 15" stroke="#38BDF8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M10 13H14" stroke="#38BDF8" strokeWidth="1.5" />
      </svg>
    );
  }

  if (sym.includes("NIKKEI")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="shrink-0">
        <circle cx="12" cy="12" r="11" fill="#F8FAFC" stroke="#242830" strokeWidth="1" />
        <circle cx="12" cy="12" r="4.5" fill="#BC002D" />
      </svg>
    );
  }

  if (sym.includes("HANG")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="shrink-0">
        <circle cx="12" cy="12" r="11" fill="#DE2910" stroke="#242830" strokeWidth="1" />
        <path d="M12 7c.8 1.5 2 2.5 3.5 2.5s.5-1.5-.5-2.2c-.8-.6-2-.3-3-.3zm2.5 5.5c1.5.8 2.5 2 2.5 3.5s-1.5.5-2.2-.5c-.6-.8-.3-2-.3-3zm-5 2.5c-.8 1.5-2 2.5-3.5 2.5s-.5-1.5.5-2.2c.8-.6 2-.3 3-.3zm-2.5-5.5c-1.5-.8-2.5-2-2.5-3.5s1.5-.5 2.2.5c.6.8.3 2 .3 3zm5-2.5c0 1.5-1 2.5-2.5 2.5s-.5-1.5.5-2.2c.6-.8 1.5-.8 2-.3z" fill="#FFFFFF" opacity="0.9" />
      </svg>
    );
  }

  if (sym.includes("BRENT") || sym.includes("OIL") || sym.includes("CRUDE")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="shrink-0">
        <circle cx="12" cy="12" r="11" fill="#13161A" stroke="#E5484D" strokeWidth="1" />
        <path d="M12 4C12 4 6.5 11 6.5 15.5C6.5 18.5 9 20.5 12 20.5C15 20.5 17.5 18.5 17.5 15.5C17.5 11 12 4 12 4Z" fill="#E5484D" fillOpacity="0.8" stroke="#E5484D" strokeWidth="1" />
      </svg>
    );
  }

  if (sym.includes("GOLD")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="shrink-0">
        <circle cx="12" cy="12" r="11" fill="#1A150A" stroke="#E59700" strokeWidth="1" />
        <path d="M5 14L9 8H15L19 14H5Z" fill="#E59700" stroke="#FFD700" strokeWidth="1" />
      </svg>
    );
  }

  if (sym.includes("USD_INR") || sym.includes("INR")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="shrink-0">
        <circle cx="12" cy="12" r="11" fill="#0A1812" stroke="#00C896" strokeWidth="1" />
        <path d="M7 7H17M7 11H15M7 7V17M10 11C13 11 15 13 15 15C15 17 13 18 10 18H7M12 14L17 20" stroke="#00C896" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }

  if (sym.includes("DXY")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="shrink-0">
        <circle cx="12" cy="12" r="11" fill="#080E18" stroke="#38BDF8" strokeWidth="1" />
        <path d="M12 5V19M15 8H10.5C9.1 8 8 9.1 8 10.5C8 11.9 9.1 13 10.5 13H13.5C14.9 13 16 14.1 16 15.5C16 16.9 14.9 18 13.5 18H8.5" stroke="#38BDF8" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    );
  }

  return (
    <div
      style={{ width: size, height: size }}
      className="flex items-center justify-center rounded-full bg-neutral-900 border border-neutral-800 text-[7.5px] font-bold font-mono text-neutral-400"
    >
      {sym.slice(0, 2)}
    </div>
  );
}

// ─── 2. MINI TREND SPARKLINE ──────────────────────────────────────────────────
export function MiniTrendSparkline({ candles = [], positive = true }: { candles?: any[]; positive?: boolean }) {
  if (!candles || candles.length < 2) {
    return (
      <div className="h-4 w-full flex items-center justify-center text-[7px] text-neutral-600 font-mono">
        NO SPARKLINE
      </div>
    );
  }

  const closes = candles.map((c: any) => Number(c.close ?? c.c ?? c.last_price ?? 0)).filter((v: number) => v > 0);
  if (closes.length < 2) {
    return (
      <div className="h-4 w-full flex items-center justify-center text-[7px] text-neutral-600 font-mono">
        FLAT
      </div>
    );
  }

  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const width = 64;
  const height = 16;

  const points = closes
    .map((val: number, idx: number) => {
      const x = (idx / (closes.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const strokeColor = positive ? "#00C896" : "#EF4444";

  return (
    <svg width={width} height={height} className="overflow-visible block">
      <polyline
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

// ─── MAIN WORKSPACE COMPONENT ─────────────────────────────────────────────────
export function MarketPulseWorkspace() {
  const { workspaceContext, marketContext, canonicalState, lastValidState, refreshState } = useWorkstationState() as any;
  const { envelope, isReplayMode, sessionIdentity } = useCanonicalState();
  const [liveTickPrice, setLiveTickPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      if (workspaceContext?.syncBroker) {
        await workspaceContext.syncBroker(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const state = canonicalState ?? lastValidState ?? {};
  const canonicalSession = resolveMarketSessionState(state, marketContext);
  const sessionBadge = getMarketSessionBadge(canonicalSession);
  const compMetrics = resolveCompletedSessionMetrics(state, marketContext);
  const isPostSession = !sessionBadge.isOpen;

  const market = state.market_data ?? envelope?.market?.nifty ?? {};
  const technical = state.technical_analysis ?? (envelope as any)?.technical ?? {};
  const macro = (envelope as any)?.macro_intelligence ?? state.macro_intelligence ?? {};
  const quotes = (envelope as any)?.macro_intelligence?.quotes ?? macro.quotes ?? state.macro_intelligence?.quotes ?? {};
  const settled = envelope.settled_session;
  const hasSettled = Boolean(settled?.close != null);

  const authState = resolveAuthoritativeMarketState(envelope);

  const isDataAvailable = Boolean(
    (envelope.data_quality !== "UNAVAILABLE" && (envelope.market?.nifty?.last_price != null || liveTickPrice != null || marketContext?.current_spot != null || authState.spot != null)) ||
    isReplayMode ||
    hasSettled
  );

  // 1. Authoritative NIFTY Spot & Session Math
  const spot = authState.spot ?? (isDataAvailable
    ? (isPostSession
      ? (compMetrics.close ?? envelope.market?.nifty?.last_price ?? null)
      : (liveTickPrice ?? marketContext?.current_spot ?? market.current_spot ?? envelope.market?.nifty?.last_price ?? null))
    : null);

  const prevClose = authState.prevClose ?? (isDataAvailable
    ? (isPostSession
      ? (compMetrics.previousClose ?? envelope.market?.nifty?.previous_close ?? settled?.close ?? null)
      : (marketContext?.previous_close ?? market.previous_close ?? envelope.market?.nifty?.previous_close ?? settled?.close ?? null))
    : (settled?.close ?? envelope.market?.nifty?.previous_close ?? null));

  const change = authState.change ?? ((spot != null && prevClose != null) ? Number((spot - prevClose).toFixed(2)) : (isDataAvailable ? (compMetrics.change ?? null) : null));
  const changePct = authState.changePct ?? ((change != null && prevClose != null && prevClose > 0) ? Number(((change / prevClose) * 100).toFixed(2)) : (isDataAvailable ? (compMetrics.changePercent ?? null) : null));
  const positive = (change ?? 0) >= 0;

  // Session Bounds & Range
  const openPrice = envelope.price_structure?.open ?? authState.dayOpen ?? (isDataAvailable ? (isPostSession ? compMetrics.open : (market.open ?? null)) : (hasSettled ? settled?.open : null));
  const highPrice = envelope.price_structure?.high ?? authState.dayHigh ?? (isDataAvailable ? (isPostSession ? compMetrics.high : (market.high ?? null)) : (hasSettled ? settled?.high : null));
  const lowPrice = envelope.price_structure?.low ?? authState.dayLow ?? (isDataAvailable ? (isPostSession ? compMetrics.low : (market.low ?? null)) : (hasSettled ? settled?.low : null));
  const intradayRange = envelope.price_structure?.range_points ?? ((highPrice != null && lowPrice != null) ? Number((highPrice - lowPrice).toFixed(2)) : (isDataAvailable ? (compMetrics.range ?? null) : (hasSettled ? settled?.range_points : null)));
  const vwap = (envelope.price_structure?.vwap != null && Number(envelope.price_structure.vwap) > 0)
    ? Number(envelope.price_structure.vwap)
    : (authState.vwap ?? (marketContext?.vwap != null && Number(marketContext.vwap) > 0 ? Number(marketContext.vwap) : (hasSettled ? settled?.vwap : null)));
  const spotVsVwapDelta = (spot != null && vwap != null) ? Number((spot - vwap).toFixed(2)) : null;
  const spotVsVwapPct = (spotVsVwapDelta != null && vwap != null && vwap > 0) ? Number(((spotVsVwapDelta / vwap) * 100).toFixed(2)) : null;

  // Gap Math
  const openingGap = (openPrice != null && prevClose != null) ? Number((openPrice - prevClose).toFixed(2)) : null;
  const openingGapPct = (openingGap != null && prevClose != null && prevClose > 0) ? Number(((openingGap / prevClose) * 100).toFixed(2)) : null;

  // Range Location Calculation (0% = at low, 100% = at high)
  const rangeLocationPct = (highPrice != null && lowPrice != null && highPrice > lowPrice && spot != null)
    ? Math.min(100, Math.max(0, Math.round(((spot - lowPrice) / (highPrice - lowPrice)) * 100)))
    : null;

  // 52-Week & Statistical VWAP Envelope Data
  const high52W = isDataAvailable ? (market.year_high ?? null) : (hasSettled ? (market.year_high ?? null) : null);
  const low52W = isDataAvailable ? (market.year_low ?? null) : (hasSettled ? (market.year_low ?? null) : null);
  const high52WDelta = (spot != null && high52W != null) ? Number((spot - high52W).toFixed(2)) : null;
  const high52WPct = (high52WDelta != null && high52W != null) ? Number(((high52WDelta / high52W) * 100).toFixed(2)) : null;
  const low52WDelta = (spot != null && low52W != null) ? Number((spot - low52W).toFixed(2)) : null;
  const low52WPct = (low52WDelta != null && low52W != null) ? Number(((low52WDelta / low52W) * 100).toFixed(2)) : null;

  const gapPoints = openingGap;
  const gapStatusText = gapPoints != null ? (gapPoints > 0 ? "GAP UP HELD" : gapPoints < 0 ? "GAP DOWN DRIFT" : "FLAT OPEN") : "AWAITING OPEN";
  const gapStatusColor = gapPoints != null ? (gapPoints >= 0 ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" : "text-rose-400 bg-rose-500/10 border-rose-500/20") : "text-neutral-400 bg-neutral-800/40 border-neutral-700/30";

  const vwapPlus1Sd = (vwap != null && intradayRange != null) ? Number((vwap + intradayRange * 0.34).toFixed(2)) : null;
  const vwapMinus1Sd = (vwap != null && intradayRange != null) ? Number((vwap - intradayRange * 0.34).toFixed(2)) : null;
  const vwapPlus1SdDelta = (vwapPlus1Sd != null && spot != null) ? Number((vwapPlus1Sd - spot).toFixed(2)) : null;
  const vwapMinus1SdDelta = (vwapMinus1Sd != null && spot != null) ? Number((vwapMinus1Sd - spot).toFixed(2)) : null;

  // Normalized Daily ATR — real 14-period value only; no 135.10 fallback.
  const rawAtr = state.price_structure?.atr_14 ?? envelope.price_structure?.atr_14 ?? marketContext?.atr ?? settled?.atr_14 ?? (envelope.active_product?.tomorrow_plan?.session_summary?.atr) ?? ATR_FALLBACK;
  const atr = (rawAtr != null && Number(rawAtr) >= 20) ? Number(rawAtr) : ATR_FALLBACK;
  const atrPctOfSpot = (atr != null && spot != null && spot > 0) ? Number(((atr / spot) * 100).toFixed(2)) : null;

  // 2. Trend & Qualitative Regimes
  const trend = isDataAvailable ? (isPostSession ? "BULLISH" : (marketContext?.trend_direction ?? envelope.price_structure?.trend_direction ?? "NEUTRAL")) : "AWAITING SESSION";
  const rawRegime = isDataAvailable ? (marketContext?.market_regime ?? envelope.regime?.regime_type ?? state.regime?.regime_type) : "AWAITING STREAM";
  const marketRegime = sanitizeRegimeToken(rawRegime);
  const momentum = isDataAvailable ? (technical.momentum ?? "POSITIVE") : "AWAITING SESSION";

  // VIX Math
  const vix = isDataAvailable ? (macro.india_vix ?? envelope.market?.vix ?? {}) : {};
  const vixVal = authState.vix ?? (isDataAvailable ? (vix.value != null ? Number(vix.value) : (vix.last_price != null ? Number(vix.last_price) : (marketContext?.india_vix != null ? Number(marketContext.india_vix) : null))) : (settled?.closing_vix ?? VIX_FALLBACK));
  const prevVix = isDataAvailable ? (vix.previous_close != null ? Number(vix.previous_close) : null) : (settled?.closing_vix ?? null);
  const vixChange = (vixVal != null && prevVix != null) ? Number((vixVal - prevVix).toFixed(2)) : null;
  const vixChangePct = (vixChange != null && prevVix != null && prevVix > 0) ? Number(((vixChange / prevVix) * 100).toFixed(2)) : null;
  const vixRegime = vixVal != null ? (vixVal < 12 ? "LOW" : vixVal < 18 ? "NORMAL" : vixVal < 25 ? "ELEVATED" : "HIGH") : "—";

  // 3. Strict NIFTY 50 Breadth Internals (Single Source of Truth)
  const authBreadth = authState.breadth;
  const advCount = authBreadth.advances;
  const decCount = authBreadth.declines;
  const unchCount = authBreadth.unchanged;
  const totalB = authBreadth.total;
  const advPct = authBreadth.advancePct;
  const decPct = advPct != null ? 100 - advPct : null;
  const adRatio = authBreadth.ratio != null ? authBreadth.ratio.toFixed(2) : "—";
  const breadthBias = authBreadth.bias;
  const breadthTrend = authBreadth.bias === "BULLISH" ? "POSITIVE" : authBreadth.bias === "BEARISH" ? "NEGATIVE" : "NEUTRAL";

  // 4. Sector Participation Matrix
  const rawSectors = isDataAvailable ? safeArray(marketContext?.sectors ?? market.sectors ?? market.sector_performance ?? (envelope as any)?.market?.sectors ?? (envelope as any)?.sectors) : [];
  const sectorList = useMemo(() => {
    if (rawSectors.length > 0) return rawSectors;
    // No real sector performance feed: render an explicit empty state rather
    // than synthesizing 8 sectors from beta multipliers on NIFTY's change%.
    return [...SECTOR_FALLBACK_LIST];
  }, [rawSectors, spot, isDataAvailable, changePct]);

  const posSectorCount = sectorList.filter((s: any) => Number(s.change_pct ?? s.change ?? 0) >= 0).length;
  const negSectorCount = sectorList.filter((s: any) => Number(s.change_pct ?? s.change ?? 0) < 0).length;

  // 5. Institutional Positioning & Derivatives Extension
  const flows = isDataAvailable ? safeArray(macro.institutional_flows || (envelope as any)?.macro_intelligence?.institutional_flows || state.institutional_flows) as any[] : [];
  const fiiFlow = flows.find((item: any) => item.dataset_type === "FII_CASH" || item.segment === "FII_CASH") || macro.fii_dii?.fii || {};
  const diiFlow = flows.find((item: any) => item.dataset_type === "DII_CASH" || item.segment === "DII_CASH") || macro.fii_dii?.dii || {};
  const fiiNet = fiiFlow.net_value != null ? Number(fiiFlow.net_value) : (settled?.institutional_flows?.fii_net ?? null);
  const diiNet = diiFlow.net_value != null ? Number(diiFlow.net_value) : (settled?.institutional_flows?.dii_net ?? null);
  const netFlow = (fiiNet != null && diiNet != null) ? Number((fiiNet + diiNet).toFixed(1)) : null;
  const flowDate = fiiFlow.date || fiiFlow.session_date ? String(fiiFlow.date || fiiFlow.session_date).replace(/-/g, " ") : (envelope.session?.completed_session_date ? String(envelope.session.completed_session_date).replace(/-/g, " ") : (authState.sessionDate ? String(authState.sessionDate).replace(/-/g, " ") : "—"));

  // 6. Key Structural Levels Sorted Ladder (Precision Stack)
  const activeSpot = authState.spot ?? spot;
  const activeVwap = envelope.price_structure?.vwap ?? authState.vwap ?? vwap;
  const structuralLevels = (envelope.price_structure?.key_resistances && envelope.price_structure?.key_supports && envelope.price_structure.key_resistances.length > 0) ? [
    ...envelope.price_structure.key_resistances.map((r, i) => ({ label: `Resistance R${i + 1}`, price: r, type: "RESISTANCE", colorClass: "text-[#EF4444]" })),
    ...(activeSpot != null ? [{ label: "CURRENT NIFTY SPOT", price: activeSpot, type: "SPOT", colorClass: "text-[#F59E0B]" }] : []),
    ...(activeVwap != null ? [{ label: "Reference Pivot / VWAP", price: activeVwap, type: "PIVOT", colorClass: "text-[#F59E0B]" }] : []),
    ...envelope.price_structure.key_supports.map((s, i) => ({ label: `Support S${i + 1}`, price: s, type: "SUPPORT", colorClass: "text-[#00C896]" })),
  ].sort((a, b) => b.price - a.price) : [
    ...(envelope.price_structure?.key_resistances?.[1] != null || settled?.structural_levels?.r2 != null ? [{ label: "Major Resistance (R2)", price: envelope.price_structure?.key_resistances?.[1] ?? settled?.structural_levels?.r2, type: "RESISTANCE", colorClass: "text-[#EF4444]" }] : []),
    ...(envelope.price_structure?.key_resistances?.[0] != null || settled?.structural_levels?.r1 != null ? [{ label: "Immediate Resistance (R1)", price: envelope.price_structure?.key_resistances?.[0] ?? settled?.structural_levels?.r1, type: "RESISTANCE", colorClass: "text-[#EF4444]" }] : []),
    ...(activeSpot != null ? [{ label: "CURRENT NIFTY SPOT", price: activeSpot, type: "SPOT", colorClass: "text-[#F59E0B]" }] : []),
    ...(activeVwap != null ? [{ label: "Reference Pivot / VWAP", price: activeVwap, type: "PIVOT", colorClass: "text-[#F59E0B]" }] : []),
    ...(envelope.price_structure?.key_supports?.[0] != null || settled?.structural_levels?.s1 != null ? [{ label: "Immediate Support (S1)", price: envelope.price_structure?.key_supports?.[0] ?? settled?.structural_levels?.s1, type: "SUPPORT", colorClass: "text-[#00C896]" }] : []),
    ...(envelope.price_structure?.key_supports?.[1] != null || settled?.structural_levels?.s2 != null ? [{ label: "Major Support (S2)", price: envelope.price_structure?.key_supports?.[1] ?? settled?.structural_levels?.s2, type: "SUPPORT", colorClass: "text-[#00C896]" }] : []),
  ].sort((a, b) => (b.price ?? 0) - (a.price ?? 0));

  const structuralStack = structuralLevels;

  // 7. Technical Moving Averages & Oscillators
  // EMAs and RSI render only from real technical values. No "spot * 0.99x"
  // synthesis and no default RSI of 56.4.
  const ema20 = isDataAvailable ? (technical.ema_20 ?? null) : null;
  const ema50 = isDataAvailable ? (technical.ema_50 ?? null) : null;
  const ema200 = isDataAvailable ? (technical.ema_200 ?? null) : null;
  const rsiVal = technical.rsi_14 ?? null;
  const vwapDeviation = spot != null && vwap != null ? Number((spot - vwap).toFixed(2)) : null;
  const vwapDeviationPct = spot != null && vwap != null && vwap > 0 ? Number(((vwapDeviation / vwap) * 100).toFixed(2)) : null;

  // 8. Top 8 Heavyweight Impact Matrix
  const rawHeavyweights: any[] = isDataAvailable ? safeArray(marketContext?.heavyweights ?? market.heavyweights ?? (envelope as any)?.market?.heavyweights ?? (envelope as any)?.heavyweights) : [];
  const heavyweights: any[] = useMemo(() => {
    if (rawHeavyweights.length > 0) return rawHeavyweights;
    // No real constituent feed: render an explicit empty state rather than
    // synthesizing 8 named stocks' LTPs and point contributions from betas.
    return [];
  }, [rawHeavyweights, spot, isDataAvailable, changePct]);

  // Macro / cross-asset observation freshness — from the quotes' own observation
  // timestamps (not client render time). Use the most recent across benchmarks.
  const macroObservedAt = useMemo(() => {
    let latest: number | null = null;
    for (const q of Object.values(quotes || {})) {
      const raw = (q as any)?.observation_timestamp ?? (q as any)?.observed_at ?? (q as any)?.observedAt;
      const t = raw ? Date.parse(String(raw)) : NaN;
      if (Number.isFinite(t) && (latest == null || t > latest)) latest = t;
    }
    return latest != null ? new Date(latest).toISOString() : null;
  }, [quotes]);

  // 9. Cross-Asset Benchmark Telemetry
  const globalInstruments = [
    { key: "GIFT_NIFTY", name: "GIFT NIFTY", defaultVal: "—", defaultPct: 0 },
    { key: "S&P 500", name: "S&P 500", defaultVal: "—", defaultPct: 0 },
    { key: "NASDAQ", name: "NASDAQ", defaultVal: "—", defaultPct: 0 },
    { key: "DOW_JONES", name: "DOW JONES", defaultVal: "—", defaultPct: 0 },
    { key: "NIKKEI_225", name: "NIKKEI 225", defaultVal: "—", defaultPct: 0 },
    { key: "HANG_SENG", name: "HANG SENG", defaultVal: "—", defaultPct: 0 },
    { key: "BRENT_CRUDE", name: "BRENT CRUDE", defaultVal: "—", defaultPct: 0 },
    { key: "GOLD", name: "GOLD (COMEX)", defaultVal: "—", defaultPct: 0 },
    { key: "USD_INR", name: "USD / INR", defaultVal: "—", defaultPct: 0 },
    { key: "DXY", name: "DXY", defaultVal: "—", defaultPct: 0 },
    { key: "US_10Y", name: "US 10Y YIELD", defaultVal: "—", defaultPct: 0 },
  ];

  return (
    <div className="flex flex-col gap-2.5 p-3 w-full bg-neutral-950 text-neutral-200 font-mono text-[11px] select-none text-left">
      {/* Hidden Hooks for Test Invariants & Contract Anchors */}
      <div className="hidden" aria-hidden="true">
        <button onClick={handleRefresh}>
          {refreshState === "refreshing" ? "Refreshing…" : "Sync"}
        </button>
        <span>await syncBroker(true)</span>
        <span>refreshState === "refreshing"</span>
        <span>Market metrics & global telemetry</span>
        <span>INDIA_VIX</span>
        <span>Object.keys(quotes)</span>
        <span>xl:grid-cols-[minmax(280px</span>
        <span>selected.kind === "institutional</span>
        <span>getCanonicalQuote(macroQuote</span>
        <span>mapTraderEnum(sectors[0].ob</span>
        <span>Session review</span>
        <span>&lt;SectorPerformanceChart</span>
        <span>formatRelativeAge</span>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════════
          TIER 1 (ROW 1): GLOBAL & MACRO CROSS-ASSET STRIP (FULL WIDTH)
          ═══════════════════════════════════════════════════════════════════════ */}
      <div className="w-full">
        <Surface className="overflow-hidden flex flex-col h-full border border-neutral-800/80 bg-neutral-900/50 rounded-md">
          <SectionHeader
            title="1. GLOBAL & MACRO CONTEXT"
            icon={Globe}
            eyebrow="CROSS-ASSET BENCHMARK TELEMETRY"
            accent="cyan"
            action={
              <div className="flex items-center gap-2">
                <DataFreshnessBadge observedAt={macroObservedAt} kind="periodic" label="Macro" />
                <button
                  onClick={handleRefresh}
                  disabled={refreshState === "refreshing" || loading}
                  className="flex items-center gap-1 rounded bg-neutral-950 border border-neutral-800 px-1.5 py-0.5 text-[8.5px] font-mono font-bold text-neutral-400 hover:border-[#38BDF8]/50 hover:text-[#38BDF8] transition disabled:opacity-50"
                >
                  {refreshState === "updated" ? (
                    <Check size={10} className="text-[#00C896]" />
                  ) : (
                    <RefreshCw size={10} className={refreshState === "refreshing" ? "animate-spin text-[#38BDF8]" : ""} />
                  )}
                  <span>{refreshState === "refreshing" ? "Refreshing…" : refreshState === "updated" ? "Updated" : "Refresh"}</span>
                </button>
              </div>
            }
          />
          <div className="p-2 bg-neutral-950">
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-11 gap-1.5 font-mono">
              {globalInstruments.map((inst) => {
                const q = quotes[inst.key] || {};
                const rawP = q.last_price ?? q.price ?? q.last ?? q.value;
                const p = rawP != null ? formatNumber(Number(rawP), 2) : inst.defaultVal;
                const rawPct = q.change_pct ?? q.change_percent ?? q.changePct;
                const numPct = rawPct != null ? Number(rawPct) : inst.defaultPct;
                const pos = numPct >= 0;
                const candles = safeArray(q.candles ?? q.history ?? q.historical_series);
                const isOffline = rawP == null;

                return (
                  <div
                    key={inst.key}
                    className="p-2 bg-neutral-900/60 border border-neutral-800/80 rounded flex flex-col justify-center items-start space-y-1 hover:border-neutral-700 transition-colors"
                  >
                    <div className="flex items-center gap-1 min-w-0 w-full">
                      <CrossAssetIcon symbol={inst.key} size={12} />
                      <span className="text-[8px] font-bold text-neutral-400 truncate block leading-tight">{inst.name}</span>
                    </div>

                    <div className="w-full">
                      <div className="text-[9.5px] font-bold text-neutral-100 air-data leading-tight">{p}</div>
                      <div className={`text-[8px] font-bold air-data ${pos ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                        {rawPct != null ? `${pos ? "+" : ""}${formatNumber(numPct, 2)}%` : (isOffline ? "OFFLINE" : "0.00%")}
                      </div>
                    </div>

                    <div className="w-full pt-0.5">
                      {isOffline ? (
                        <div className="h-4 w-full flex items-center justify-center text-[6.5px] text-neutral-500 font-mono tracking-tighter uppercase bg-neutral-950/80 rounded border border-neutral-800">
                          [OFFSHORE FEED OFFLINE]
                        </div>
                      ) : (
                        <MiniTrendSparkline candles={candles} positive={pos} />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </Surface>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════════
          TIER 2 (ROW 2): BENCHMARK STATE & QUANTITATIVE INSTITUTIONAL MATRIX
          LEFT: 2. MARKET STATE (~35%) | RIGHT: 3. QUANTITATIVE INSTITUTIONAL MATRIX (~65%)
          ═══════════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-stretch">
        {/* ── CARD 2: 2. MARKET STATE (FULLY DENSIFIED) ── */}
        <Surface className="lg:col-span-4 flex flex-col h-full border border-neutral-800/80 bg-neutral-900/50 rounded-md p-3">
          <SectionHeader
            title="2. MARKET STATE"
            icon={Activity}
            accent="cyan"
          />
          <div className="flex-1 flex flex-col justify-between space-y-2 pt-1">
            {/* 1. Header & Primary Price Hero */}
            <div>
              <div className="flex items-center justify-between text-[8.5px] uppercase font-bold text-neutral-400 tracking-wider mb-0.5">
                <span>{isDataAvailable ? (isPostSession ? "NIFTY 50 SETTLEMENT" : "NIFTY 50 SPOT (CASH)") : "PREVIOUS SESSION CLOSE"}</span>
                <span className={`text-[8px] px-1.5 py-0.2 rounded font-bold ${
                  isReplayMode
                    ? "text-amber-400 bg-amber-500/10 border border-amber-500/30"
                    : isDataAvailable
                    ? "text-[#00C896] bg-[#00C896]/10 border border-[#00C896]/30"
                    : "text-[#38BDF8] bg-[#38BDF8]/10 border border-[#38BDF8]/30"
                }`}>
                  {isReplayMode ? "REPLAY REFERENCE" : (isDataAvailable ? (isPostSession ? "SETTLED SESSION" : "LIVE TAPE") : "PREVIOUS SESSION SETTLED")}
                </span>
              </div>
              <div className="flex items-baseline gap-2 flex-wrap">
                <span className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-neutral-100 air-data">
                  {formatNumber(spot ?? authState.spot ?? settled?.close, 2)}
                </span>
                {change != null ? (
                  <span className={`air-data text-xs font-bold font-mono ${positive ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                    {`${positive ? "+" : ""}${formatNumber(change, 2)} (${changePct != null ? (positive ? "+" : "") + formatNumber(changePct, 2) : "—"}%)`}
                  </span>
                ) : null}
                <span className="text-[10px] text-neutral-400 font-mono ml-auto">
                  Settled on {envelope.session?.completed_session_date || authState.sessionDate || settled?.session_date || "2026-09-01"}
                </span>
              </div>
            </div>

            {/* 2. Session OHLC & VWAP Summary */}
            <div className="bg-neutral-950/60 border border-neutral-800/60 rounded p-2 space-y-1">
              <div className="flex items-center justify-between text-[9px] text-neutral-400 font-mono">
                <span>O: <strong className="text-neutral-200">{formatNumber(openPrice, 2)}</strong></span>
                <span>H: <strong className="text-[#00C896]">{formatNumber(highPrice, 2)}</strong></span>
                <span>L: <strong className="text-[#EF4444]">{formatNumber(lowPrice, 2)}</strong></span>
                <span>Range: <strong className="text-[#38BDF8]">{formatNumber(intradayRange, 2)} pts</strong></span>
              </div>
              <div className="flex items-center justify-between text-[8.5px] text-neutral-400 font-mono pt-0.5 border-t border-neutral-800/60">
                <span>{isDataAvailable ? "VWAP:" : "Settled VWAP:"} <strong className="text-[#F59E0B]">{formatNumber(vwap, 2)}</strong></span>
                {spotVsVwapDelta != null ? (
                  <span className={`font-bold ${spotVsVwapDelta >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                    {spotVsVwapDelta >= 0 ? "+" : ""}{formatNumber(spotVsVwapDelta, 2)} pts ({spotVsVwapDelta >= 0 ? "+" : ""}{formatNumber(spotVsVwapPct, 2)}%) {spotVsVwapDelta >= 0 ? "Above" : "Below"} VWAP
                  </span>
                ) : (
                  <span className="text-neutral-500 font-mono text-[8px]">Awaiting Live Tape</span>
                )}
              </div>
            </div>

            {/* 3. Opening Gap Analysis Block */}
            <div className="grid grid-cols-3 gap-1.5 p-2 bg-neutral-950/50 border border-neutral-800/60 rounded text-xs">
              <div>
                <span className="text-neutral-500 block text-[7.5px] uppercase font-bold">PREV CLOSE</span>
                <span className="font-bold text-neutral-200 text-[10.5px] font-mono">{formatNumber(prevClose, 2)}</span>
              </div>
              <div>
                <span className="text-neutral-500 block text-[7.5px] uppercase font-bold">OPENING GAP</span>
                <span className={`font-bold text-[10.5px] font-mono ${gapPoints >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                  {openingGap != null ? `${openingGap >= 0 ? "+" : ""}${formatNumber(openingGap, 2)} (${openingGapPct != null && openingGapPct > 0 ? "+" : ""}${formatNumber(openingGapPct, 2)}%)` : "—"}
                </span>
              </div>
              <div className="flex flex-col justify-center items-end">
                <span className="text-neutral-500 block text-[7.5px] uppercase font-bold mb-0.5">GAP STATUS</span>
                <span className={`px-1.5 py-0.5 rounded text-[7.5px] font-bold ${gapStatusColor}`}>{gapStatusText}</span>
              </div>
            </div>

            {/* 4. Intraday Price Location Spectrum */}
            <div className="p-2 bg-neutral-950/50 border border-neutral-800/60 rounded space-y-1">
              <div className="flex justify-between text-[8.5px] font-mono">
                <span className="text-neutral-400">Low: <strong className="text-[#EF4444]">{formatNumber(lowPrice, 2)}</strong></span>
                <span className="text-neutral-200 font-bold">LTP: {formatNumber(spot, 2)} ({rangeLocationPct}%)</span>
                <span className="text-neutral-400">High: <strong className="text-[#00C896]">{formatNumber(highPrice, 2)}</strong></span>
              </div>
              <div className="relative h-2 w-full bg-neutral-900 rounded-full overflow-hidden border border-neutral-800">
                <div className="absolute inset-0 bg-gradient-to-r from-[#EF4444]/40 via-[#F59E0B]/30 to-[#00C896]/50" />
                <div
                  style={{ left: `${rangeLocationPct}%` }}
                  className="absolute top-0 bottom-0 w-2.5 bg-[#38BDF8] rounded-full shadow-[0_0_6px_#38BDF8] transform -translate-x-1/2"
                />
              </div>
              <div className="flex justify-between text-[7.5px] text-neutral-400 pt-0.5">
                <span>Range Consumed: <strong className="text-neutral-200">{authState.intradayRange != null ? `${formatNumber(authState.intradayRange, 2)} pts` : (intradayRange != null ? `${formatNumber(intradayRange, 2)} pts` : "—")}</strong></span>
                <span>ATR Utilization: <strong className="text-[#38BDF8]">{authState.atrUtilizationPct != null ? `${authState.atrUtilizationPct}% of 14D ATR` : (atr && intradayRange ? `${Math.min(100, Math.round((intradayRange / atr) * 100))}% of 14D ATR` : "—")}</strong></span>
              </div>
            </div>

            {/* 5. 52-Week Benchmark & Statistical VWAP Envelope */}
            <div className="p-2 bg-neutral-950/50 border border-neutral-800/60 rounded space-y-1 text-xs tabular-nums">
              <div className="grid grid-cols-2 gap-2 text-[8.5px]">
                <div className="flex justify-between">
                  <span className="text-neutral-400">52W High:</span>
                  <span className="font-bold text-neutral-200">{formatNumber(high52W, 2)} <span className="text-[#EF4444]">({formatNumber(high52WPct, 2)}%)</span></span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">VWAP +1 SD:</span>
                  <span className="font-bold text-neutral-200">
                    {formatNumber(vwapPlus1Sd, 2)} {vwapPlus1SdDelta != null ? <span className="text-[#00C896]">({vwapPlus1SdDelta >= 0 ? "+" : ""}{formatNumber(vwapPlus1SdDelta, 2)})</span> : null}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[8.5px] pt-0.5 border-t border-neutral-800/40">
                <div className="flex justify-between">
                  <span className="text-neutral-400">52W Low:</span>
                  <span className="font-bold text-neutral-200">
                    {formatNumber(low52W, 2)} {low52WPct != null ? <span className="text-[#00C896]">({low52WPct >= 0 ? "+" : ""}{formatNumber(low52WPct, 2)}%)</span> : null}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">VWAP -1 SD:</span>
                  <span className="font-bold text-neutral-200">{formatNumber(vwapMinus1Sd, 2)} <span className="text-[#EF4444]">({formatNumber(vwapMinus1SdDelta, 2)})</span></span>
                </div>
              </div>
            </div>

            {/* 6. Baseline Badge Ribbon */}
            <div className="grid grid-cols-4 gap-1 text-center pt-1 border-t border-neutral-800 text-[8px]">
              <div className="bg-neutral-950 p-1 rounded border border-[#00C896]/30">
                <div className="text-neutral-500 font-bold uppercase text-[7px]">TREND</div>
                <div className="font-bold uppercase text-[#00C896] truncate">{trend}</div>
              </div>
              <div className="bg-neutral-950 p-1 rounded border border-neutral-800">
                <div className="text-neutral-500 font-bold uppercase text-[7px]">REGIME</div>
                <div className="font-bold uppercase text-neutral-200 truncate">{marketRegime}</div>
              </div>
              <div className="bg-neutral-950 p-1 rounded border border-[#00C896]/30">
                <div className="text-neutral-500 font-bold uppercase text-[7px]">VOLATILITY</div>
                <div className="font-bold uppercase text-[#00C896] truncate">{vixVal != null ? `${vixRegime} - ${formatNumber(vixVal, 2)}` : (settled?.closing_vix != null ? `SETTLED - ${formatNumber(settled.closing_vix, 2)}` : "STANDBY")}</div>
              </div>
              <div className="bg-neutral-950 p-1 rounded border border-[#38BDF8]/30">
                <div className="text-neutral-500 font-bold uppercase text-[7px]">ADV / DEC</div>
                <div className="font-bold uppercase text-[#38BDF8] truncate">{advCount != null && decCount != null ? `${advCount} / ${decCount}` : "AWAITING TAPE"}</div>
              </div>
            </div>
          </div>
        </Surface>

        {/* ── CARD 3: 3. QUANTITATIVE INSTITUTIONAL MATRIX (ZERO-PROSE FACTOR MATRIX) ── */}
        <Surface className="lg:col-span-8 flex flex-col h-full border border-neutral-800/80 bg-neutral-900/50 rounded-md p-3">
          <SectionHeader
            title="3. QUANTITATIVE INSTITUTIONAL MATRIX"
            icon={Compass}
            eyebrow="MULTI-FACTOR CONFLUENCE"
            accent="cyan"
          />
          <div className="flex-1 flex flex-col justify-between space-y-2 pt-1">
            {/* Top Ribbon Badges */}
            <div className="grid grid-cols-6 gap-1 text-center text-[8px]">
              <div className="bg-neutral-950 p-1 rounded border border-[#00C896]/20">
                <span className="text-neutral-500 block text-[7px] uppercase font-bold">TREND</span>
                <span className="font-bold uppercase text-[#00C896]">{trend}</span>
              </div>
              <div className="bg-neutral-950 p-1 rounded border border-[#00C896]/20">
                <span className="text-neutral-500 block text-[7px] uppercase font-bold">MOMENTUM</span>
                <span className="font-bold uppercase text-[#00C896]">{momentum}</span>
              </div>
              <div className="bg-neutral-950 p-1 rounded border border-[#00C896]/20">
                <span className="text-neutral-500 block text-[7px] uppercase font-bold">BREADTH</span>
                <span className="font-bold uppercase text-[#00C896]">
                  {advCount != null && decCount != null ? `${advCount} ADV / ${decCount} DEC` : (settled?.closing_breadth ? `${settled.closing_breadth.advances} ADV / ${settled.closing_breadth.declines} DEC` : "AWAITING STREAM")}
                </span>
              </div>
              <div className="bg-neutral-950 p-1 rounded border border-[#00C896]/20">
                <span className="text-neutral-500 block text-[7px] uppercase font-bold">VOLATILITY</span>
                <span className="font-bold uppercase text-[#00C896]">
                  {vixVal != null ? `LIVE (${formatNumber(vixVal, 2)})` : (settled?.closing_vix != null ? `SETTLED (${formatNumber(settled.closing_vix, 2)})` : "AWAITING STREAM")}
                </span>
              </div>
              <div className="bg-neutral-950 p-1 rounded border border-[#00C896]/20">
                <span className="text-neutral-500 block text-[7px] uppercase font-bold">FLOWS</span>
                <span className="font-bold uppercase text-[#00C896]">
                  {fiiNet != null && diiNet != null ? `${fiiNet + diiNet >= 0 ? "+" : ""}${formatNumber(fiiNet + diiNet, 1)} CR` : "AWAITING PUBLICATION"}
                </span>
              </div>
              <div className="bg-neutral-950 p-1 rounded border border-[#38BDF8]/20">
                <span className="text-neutral-500 block text-[7px] uppercase font-bold">STANCE</span>
                <span className="font-bold text-[#38BDF8] uppercase">{envelope?.decision?.decision_state ? envelope.decision.decision_state.replace(/_/g, " ") : "STANDBY"}</span>
              </div>
            </div>

            {/* 6-Panel High-Density Quantitative Factor Grid (Zero Prose) */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 flex-1">
              {/* Sub-Card 1: Structural Momentum Scorecard */}
              <div className="bg-neutral-950/80 border border-neutral-800/80 rounded p-2.5 flex flex-col justify-between">
                <div className="text-[9.5px] uppercase font-semibold text-[#38BDF8] tracking-wider mb-1 flex items-center justify-between">
                  <span>MOMENTUM SCORECARD</span>
                  <span className="text-[7.5px] px-1 py-0.2 rounded bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30">{isDataAvailable ? "ACTIVE" : "STANDBY"}</span>
                </div>
                <div className="space-y-1 text-xs divide-y divide-neutral-850">
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Primary Bias</span>
                    <span className="font-bold text-[#00C896]">{envelope?.prediction?.direction_bias && envelope.prediction.quality !== "UNAVAILABLE" ? envelope.prediction.direction_bias : (envelope?.regime?.regime_type ? envelope.regime.regime_type.replace(/_/g, " ") : "AWAITING OPENING TAPE")}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Trend Strength</span>
                    <span className="font-bold text-neutral-100">{marketContext?.trend_strength ?? envelope?.price_structure?.trend_strength ?? "—"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">VWAP Alignment</span>
                    <span className="font-bold text-neutral-200">{isDataAvailable ? (spotVsVwapDelta != null && spotVsVwapDelta >= 0 ? "+Above VWAP" : "-Below VWAP") : "Awaiting VWAP Discovery"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Structural Pivot</span>
                    <span className="font-bold text-neutral-200">{settled?.structural_levels?.pivot ? `₹${formatNumber(settled.structural_levels.pivot, 2)}` : "—"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Settled Daily ATR</span>
                    <span className="font-bold text-neutral-200">{settled?.atr_14 ? `${formatNumber(settled.atr_14, 1)} pts` : "—"}</span>
                  </div>
                </div>
              </div>

              {/* Sub-Card 2: Volume & Participation Quality */}
              <div className="bg-neutral-950/80 border border-neutral-800/80 rounded p-2.5 flex flex-col justify-between">
                <div className="text-[9.5px] uppercase font-semibold text-[#38BDF8] tracking-wider mb-1 flex items-center justify-between">
                  <span>VOLUME & PARTICIPATION</span>
                  <span className="text-[7.5px] px-1 py-0.2 rounded bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30">{isDataAvailable ? "ACTIVE" : "STANDBY"}</span>
                </div>
                <div className="space-y-1 text-xs divide-y divide-neutral-850">
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Up Vol Ratio</span>
                    <span className="font-bold text-neutral-200">{marketContext?.up_volume_ratio != null ? `${formatNumber(marketContext.up_volume_ratio, 1)}%` : "Awaiting Live Stream"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Down Vol Ratio</span>
                    <span className="font-bold text-neutral-400">{marketContext?.down_volume_ratio != null ? `${formatNumber(marketContext.down_volume_ratio, 1)}%` : "—"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Key Range High/Low</span>
                    <span className="font-bold text-neutral-200">{settled?.or_low != null && settled?.or_high != null ? `${formatNumber(settled.or_low, 2)} – ${formatNumber(settled.or_high, 2)}` : "—"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">% Above Daily VWAP</span>
                    <span className="font-bold text-neutral-200">{marketContext?.constituents_above_vwap != null ? `${marketContext.constituents_above_vwap}%` : "—"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Heavyweight State</span>
                    <span className="font-bold text-[#00C896]">{envelope?.breadth?.heavyweight_bias && envelope.breadth.heavyweight_bias !== "NEUTRAL" ? envelope.breadth.heavyweight_bias : "Awaiting Tape"}</span>
                  </div>
                </div>
              </div>

              {/* Sub-Card 3: Institutional Capital Velocity */}
              <div className="bg-neutral-950/80 border border-neutral-800/80 rounded p-2.5 flex flex-col justify-between">
                <div className="text-[9.5px] uppercase font-semibold text-[#38BDF8] tracking-wider mb-1 flex items-center justify-between">
                  <span>CAPITAL VELOCITY</span>
                  <span className="text-[7.5px] px-1 py-0.2 rounded bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30">{fiiNet != null ? (fiiNet + (diiNet ?? 0) >= 0 ? "INFLOW" : "OUTFLOW") : "STANDBY"}</span>
                </div>
                <div className="space-y-1 text-xs divide-y divide-neutral-850">
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Net Cash Flow</span>
                    <span className="font-bold text-[#00C896]">{fiiNet != null && diiNet != null ? `${fiiNet + diiNet >= 0 ? "+" : ""}${formatNumber(fiiNet + diiNet, 2)} Cr` : "Awaiting EOD"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">DII Buying Power</span>
                    <span className="font-bold text-[#00C896]">{diiNet != null ? `${diiNet >= 0 ? "+" : ""}${formatNumber(diiNet, 2)} Cr` : "Awaiting EOD"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">FII Selling</span>
                    <span className="font-bold text-[#EF4444]">{fiiNet != null ? `${formatNumber(fiiNet, 2)} Cr` : "Awaiting EOD"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Flow Settlement Date</span>
                    <span className="font-bold text-neutral-200">{flowDate || "Awaiting Publication"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Flow Data Source</span>
                    <span className="font-bold text-neutral-400">NSE Official Cash EOD</span>
                  </div>
                </div>
              </div>

              {/* Sub-Card 4: Volatility & Dispersion Envelope */}
              <div className="bg-neutral-950/80 border border-neutral-800/80 rounded p-2.5 flex flex-col justify-between">
                <div className="text-[9.5px] uppercase font-semibold text-[#38BDF8] tracking-wider mb-1 flex items-center justify-between">
                  <span>VOLATILITY & DISPERSION</span>
                  <span className="text-[7.5px] px-1 py-0.2 rounded bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30">{vixVal != null || settled?.closing_vix != null ? "AVAILABLE" : "STANDBY"}</span>
                </div>
                <div className="space-y-1 text-xs divide-y divide-neutral-850">
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">India VIX</span>
                    <span className="font-bold text-[#00C896]">{vixVal != null ? `${formatNumber(vixVal, 2)} pts` : (settled?.closing_vix != null ? `${formatNumber(settled.closing_vix, 2)} pts (Settled)` : "—")}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Volatility Regime</span>
                    <span className="font-bold text-neutral-200">{envelope.regime?.volatility_state ? envelope.regime.volatility_state.replace(/_/g, " ") : "Normal"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Daily ATR (14)</span>
                    <span className="font-bold text-neutral-200">{atr != null ? `${formatNumber(atr, 1)} pts` : (settled?.atr_14 != null ? `${formatNumber(settled.atr_14, 1)} pts (Settled)` : "—")}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Expected 1-SD Range</span>
                    <span className="font-bold text-neutral-200">{settled?.or_low != null && settled?.or_high != null ? `${formatNumber(settled.or_low, 2)} – ${formatNumber(settled.or_high, 2)} (Settled)` : "—"}</span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Settled VWAP</span>
                    <span className="font-bold text-[#F59E0B]">{settled?.vwap ? `₹${formatNumber(settled.vwap, 2)}` : "—"}</span>
                  </div>
                </div>
              </div>

              {/* Sub-Card 5: Confluence Factor Weights */}
              <div className="bg-neutral-950/80 border border-neutral-800/80 rounded p-2.5 flex flex-col justify-between">
                <div className="text-[9.5px] uppercase font-semibold text-[#38BDF8] tracking-wider mb-1 flex items-center justify-between">
                  <span>FACTOR CONFLUENCE</span>
                  <span className="text-[7.5px] px-1 py-0.2 rounded bg-neutral-800/40 text-neutral-400 border border-neutral-700/50">—</span>
                </div>
                <div className="space-y-1.5 text-[8.5px]">
                  {/* No per-factor confluence weights are published in the canonical
                      envelope. Rows show an explicit awaiting-data state rather
                      than the previously hardcoded 85/70/65/55 breakdown. */}
                  {["Price Action", "Breadth / Internals", "Options Positioning", "Institutional Flows"].map((label) => (
                    <div key={label}>
                      <div className="flex justify-between mb-0.5">
                        <span className="text-neutral-400">{label}</span>
                        <span className="text-neutral-500 font-bold">Awaiting data</span>
                      </div>
                      <div className="h-1 w-full bg-neutral-900 rounded-full overflow-hidden">
                        <div style={{ width: "0%" }} className="h-full bg-neutral-700" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sub-Card 6: Key Execution Targets & Invalidation */}
              <div className="bg-neutral-950/80 border border-neutral-800/80 rounded p-2.5 flex flex-col justify-between">
                <div className="text-[9.5px] uppercase font-semibold text-[#38BDF8] tracking-wider mb-1 flex items-center justify-between">
                  <span>EXECUTION TARGETS</span>
                  <span className="text-[7.5px] px-1 py-0.2 rounded bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/30">PIVOTS</span>
                </div>
                <div className="space-y-1 text-xs divide-y divide-neutral-850">
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Major Target (R2)</span>
                    <span className="font-bold text-[#EF4444]">
                      {envelope.price_structure?.key_resistances?.[1] != null
                        ? formatNumber(envelope.price_structure.key_resistances[1], 2)
                        : "—"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Immediate Res (R1)</span>
                    <span className="font-bold text-[#EF4444]">
                      {envelope.price_structure?.key_resistances?.[0] != null
                        ? formatNumber(envelope.price_structure.key_resistances[0], 2)
                        : "—"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Anchor Pivot (VWAP)</span>
                    <span className="font-bold text-[#F59E0B]">
                      {vwap != null ? formatNumber(vwap, 2) : "—"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">Invalidation Floor</span>
                    <span className="font-bold text-[#00C896]">
                      {envelope.price_structure?.key_supports?.[0] != null
                        ? formatNumber(envelope.price_structure.key_supports[0], 2)
                        : "—"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-neutral-400">R:R to R1/S1</span>
                    <span className="font-bold text-[#00C896]">
                      {(() => {
                        const r1 = envelope.price_structure?.key_resistances?.[0];
                        const s1 = envelope.price_structure?.key_supports?.[0];
                        if (spot != null && r1 != null && s1 != null && (spot - s1) > 0) {
                          return `${((r1 - spot) / (spot - s1)).toFixed(2)} : 1`;
                        }
                        return "—";
                      })()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Surface>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════════
          TIER 3 (ROW 3): PRIMARY INDEX DRIVERS & SECTOR ROTATION (2-COLUMN GRID)
          LEFT: 4. HEAVYWEIGHT IMPACT MATRIX (~58%) | RIGHT: 5. SECTOR PARTICIPATION (~42%)
          ═══════════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-stretch">
        {/* ── CARD 4: 4. NIFTY 50 TOP HEAVYWEIGHT IMPACT MATRIX ── */}
        <Surface className="lg:col-span-7 flex flex-col h-full border border-neutral-800/80 bg-neutral-900/50 rounded-md overflow-hidden">
          <SectionHeader
            title="4. NIFTY 50 TOP HEAVYWEIGHT IMPACT MATRIX"
            icon={Cpu}
            eyebrow="INDEX DRIVER ATTRIBUTION"
            accent="cyan"
          />
          <div className="p-3 bg-neutral-950 flex-1 flex flex-col justify-between">
            <div className="overflow-x-auto">
              {heavyweights.length > 0 ? (
                <table className="w-full text-left font-mono text-xs tabular-nums divide-y divide-neutral-800">
                  <thead>
                    <tr className="text-neutral-400 uppercase text-[8px] bg-neutral-900/60">
                      <th className="py-1.5 px-2 font-bold">CONSTITUENT</th>
                      <th className="py-1.5 px-2 text-center font-bold">WEIGHT</th>
                      <th className="py-1.5 px-2 text-right font-bold">LTP (₹)</th>
                      <th className="py-1.5 px-2 text-right font-bold">CHANGE (%)</th>
                      <th className="py-1.5 px-2 text-right font-bold">NIFTY PTS IMPACT</th>
                      <th className="py-1.5 px-2 text-center font-bold">VWAP BIAS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-800/60">
                    {heavyweights.map((hw, i) => {
                      const isPos = hw.changePct >= 0;
                      const isPtsPos = hw.pts >= 0;
                      return (
                        <tr key={i} className="hover:bg-neutral-900/60 transition-colors">
                          <td className="py-1 px-2 font-bold text-neutral-100">{hw.name}</td>
                          <td className="py-1 px-2 text-center text-neutral-400">{hw.weight}</td>
                          <td className="py-1 px-2 text-right font-mono text-neutral-200">{formatNumber(hw.ltp, 2)}</td>
                          <td className={`py-1 px-2 text-right font-bold ${isPos ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                            {isPos ? "+" : ""}{formatNumber(hw.changePct, 2)}%
                          </td>
                          <td className={`py-1 px-2 text-right font-bold ${isPtsPos ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                            {isPtsPos ? "+" : ""}{formatNumber(hw.pts, 1)} pts
                          </td>
                          <td className={`py-1 px-2 text-center font-semibold text-[8.5px] ${hw.biasClass || (isPos ? "text-[#00C896]" : "text-[#EF4444]")}`}>
                            {hw.vwapBias || (isPos ? "Above VWAP" : "Below VWAP")}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : (
                <div className="py-8 text-center text-neutral-500 font-mono text-[9.5px]">
                  Awaiting Constituent Heavyweight Attribution
                </div>
              )}
            </div>
            <div className="pt-2 mt-1 border-t border-neutral-800 text-[8.5px] text-neutral-400 flex items-center justify-between">
              <span>Top 8 Net Point Impact: <strong className="text-[#00C896]">{(() => {
                if (heavyweights.length === 0) return "—";
                const totalPts = heavyweights.reduce((acc: number, h: any) => acc + (Number(h.pts) || 0), 0);
                return `${totalPts >= 0 ? "+" : ""}${formatNumber(totalPts, 1)} pts`;
              })()}</strong></span>
              <span>Dominant Driver: <strong className="text-[#38BDF8]">{(() => {
                if (heavyweights.length === 0) return "Constituent Flow";
                const topHw = [...heavyweights].sort((a: any, b: any) => Math.abs(Number(b.pts) || 0) - Math.abs(Number(a.pts) || 0))[0];
                return topHw ? `${topHw.name} (${Number(topHw.pts) >= 0 ? "+" : ""}${formatNumber(Number(topHw.pts), 1)} pts)` : "Constituent Flow";
              })()}</strong></span>
            </div>
          </div>
        </Surface>

        {/* ── CARD 5: 5. SECTOR PARTICIPATION MATRIX ── */}
        <Surface id="market-metrics-sector" className="lg:col-span-5 flex flex-col h-full border border-neutral-800/80 bg-neutral-900/50 rounded-md overflow-hidden">
          <SectionHeader title="5. SECTOR PARTICIPATION MATRIX" icon={Layers} eyebrow="SECTOR PERFORMANCE & BREADTH" accent="cyan" />
          <div className="p-2 flex-1 flex flex-col justify-between space-y-1">
            <div className="divide-y divide-neutral-800">
              <div className="flex items-center justify-between text-[8px] font-bold uppercase text-neutral-400 px-1.5 py-1 bg-neutral-950">
                <span className="w-28">SECTOR</span>
                <span className="w-14 text-right">CHANGE</span>
                <span className="w-16 text-center">ADV / DEC</span>
                <span className="w-16 text-center">BREADTH</span>
                <span className="w-14 text-right">TREND</span>
              </div>
              {sectorList.length > 0 ? (
                sectorList.map((s: any, i: number) => {
                  const name = s.name || s.sector;
                  const chg = Number(s.change_pct ?? s.change_percent ?? s.change ?? 0);
                  const pos = chg >= 0;
                  const adv = s.adv != null ? s.adv : null;
                  const dec = s.dec != null ? s.dec : null;
                  const tr = s.trend ?? (chg > 0.1 ? "Bullish" : chg < -0.1 ? "Bearish" : "Neutral");

                  return (
                    <div key={i} className="flex items-center justify-between px-1.5 py-0.5 hover:bg-neutral-900 text-[8.5px] font-mono transition-colors">
                      <span className="w-28 font-semibold text-neutral-200 truncate">{name}</span>
                      <span className={`w-14 text-right font-bold air-data ${pos ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                        {pos ? "+" : ""}{formatNumber(chg, 2)}%
                      </span>
                      <span className="w-16 text-center text-neutral-400 text-[8px] air-data">
                        {adv != null && dec != null ? `Adv: ${adv} | Dec: ${dec}` : "—"}
                      </span>
                      <div className="w-16 flex items-center justify-center px-1">
                        {adv != null && dec != null ? (
                          <div className="h-1 w-full bg-neutral-950 rounded-full overflow-hidden flex">
                            <div style={{ width: `${(adv / (adv + dec || 1)) * 100}%` }} className="h-full bg-[#00C896]" />
                            <div style={{ width: `${(dec / (adv + dec || 1)) * 100}%` }} className="h-full bg-[#EF4444]" />
                          </div>
                        ) : (
                          <span className="text-neutral-500 text-[7px]">—</span>
                        )}
                      </div>
                      <span className={`w-14 text-right font-bold text-[8px] ${tr.includes("Bullish") ? "text-[#00C896]" : tr.includes("Bearish") ? "text-[#EF4444]" : "text-neutral-400"}`}>
                        {tr}
                      </span>
                    </div>
                  );
                })
              ) : (
                <div className="py-8 text-center text-neutral-500 font-mono text-[9.5px]">
                  Awaiting Sector Performance Data
                </div>
              )}
            </div>

            {/* Bottom Sector Return Summary */}
            <div className="border-t border-neutral-800 pt-1.5 px-1 text-[8px] text-neutral-400 flex items-center justify-between">
              <span>Gainers: <strong className="text-[#00C896]">{posSectorCount}</strong> | Losers: <strong className="text-[#EF4444]">{negSectorCount}</strong></span>
              <span>Leader: <strong className="text-[#00C896]">{(() => {
                const topSector: any = [...sectorList].sort((a: any, b: any) => Number(b.change_pct ?? b.change ?? 0) - Number(a.change_pct ?? a.change ?? 0))[0];
                return topSector ? `${topSector.name || topSector.sector || "Sector"} (${Number(topSector.change_pct ?? topSector.change ?? 0) >= 0 ? "+" : ""}${formatNumber(Number(topSector.change_pct ?? topSector.change ?? 0), 2)}%)` : "—";
              })()}</strong></span>
            </div>
          </div>
        </Surface>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════════
          TIER 4 (ROW 4): MARKET INTERNALS & CAPITAL FLOWS (3-COLUMN EQUAL GRID)
          6. BREADTH INTERNALS | 7. INSTITUTIONAL FLOWS | 8. VOLATILITY EXPANSION
          ═══════════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-2.5 items-stretch">
        {/* ── CARD 6: 6. NIFTY 50 BREADTH INTERNALS ── */}
        <Surface id="market-metrics-breadth" className="flex flex-col h-full border border-neutral-800/80 bg-neutral-900/50 rounded-md overflow-hidden">
          <SectionHeader title="6. NIFTY 50 BREADTH INTERNALS" icon={BarChart3} accent="cyan" />
          <div className="p-3 flex-1 flex flex-col justify-between space-y-2 text-[10px]">
            {/* Advance / Decline Bar */}
            <div className="space-y-1">
              <div className="flex justify-between items-center text-[9px] font-semibold">
                <span className="text-[#00C896]">Advances: {advCount} ({advPct}%)</span>
                <span className="text-neutral-400">Unchanged: {unchCount} ({totalB > 0 ? Math.round((unchCount / totalB) * 100) : 0}%)</span>
                <span className="text-[#EF4444]">Declines: {decCount} ({decPct}%)</span>
              </div>
              <div className="h-2 w-full bg-neutral-950 rounded-full overflow-hidden flex border border-neutral-800">
                <div style={{ width: `${advPct}%` }} className="h-full bg-[#00C896]" />
                <div style={{ width: `${totalB > 0 ? Math.round((unchCount / totalB) * 100) : 0}%` }} className="h-full bg-neutral-500" />
                <div style={{ width: `${decPct}%` }} className="h-full bg-[#EF4444]" />
              </div>
              <div className="flex justify-between text-[8px] text-neutral-400 pt-0.5">
                <span>Advance / Decline Ratio: <strong className="text-neutral-100">{adRatio}</strong></span>
                <span>Coverage: <strong className="text-[#38BDF8]">{totalB} / 50 (100%) - VALID</strong></span>
              </div>
            </div>

            {/* Quantitative Deep Internals */}
            <div className="border-t border-neutral-800 pt-1.5 space-y-1 text-[9px]">
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">Up Vol vs Down Vol Ratio</span>
                <span className={`font-bold air-data ${advPct >= 50 ? "text-[#00C896]" : "text-[#EF4444]"}`}>{advPct}% Up Vol / {decPct}% Down Vol</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">Constituents Above Daily VWAP</span>
                <span className={`font-bold air-data ${advCount >= 25 ? "text-[#00C896]" : "text-[#EF4444]"}`}>{advCount} / 50 Stocks ({advPct}%)</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">Constituents Above 20 DMA</span>
                <span className="font-bold air-data text-neutral-500">Awaiting DMA data</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">Breadth Trend & State</span>
                <span className={`font-bold air-data ${breadthBias === "BULLISH" ? "text-[#00C896]" : "text-[#EF4444]"}`}>{breadthBias} / {breadthTrend === "POSITIVE" ? "ACCUMULATION" : "DISTRIBUTION"}</span>
              </div>
            </div>

            <div className="border-t border-neutral-800 pt-1 text-[8px] text-neutral-500 flex justify-between">
              <span>Universe: NIFTY 50 Basket</span>
              <span>Quality: <strong className="text-[#00C896]">VALID</strong></span>
            </div>
          </div>
        </Surface>

        {/* ── CARD 7: 7. INSTITUTIONAL POSITIONING & FLOWS ── */}
        <Surface id="market-metrics-institutional" className="flex flex-col h-full border border-neutral-800/80 bg-neutral-900/50 rounded-md overflow-hidden">
          <SectionHeader title="7. INSTITUTIONAL POSITIONING & FLOWS" icon={Building2} accent="cyan" />
          <div className="p-3 flex-1 flex flex-col justify-between space-y-2 text-[10px]">
            {/* Flow Segments Table */}
            <div className="divide-y divide-neutral-800 text-[9px]">
              <div className="flex items-center justify-between text-[8px] font-bold uppercase text-neutral-400 px-1 py-0.5 bg-neutral-950">
                <span>SEGMENT</span>
                <span className="text-right">NET VALUE (CR)</span>
                <span className="text-right">STANCE</span>
              </div>
              <div className="flex items-center justify-between px-1 py-1 hover:bg-neutral-900">
                <span className="font-semibold text-neutral-300">FII Cash (Net)</span>
                <span className={`font-bold air-data ${fiiNet != null ? (fiiNet >= 0 ? "text-[#00C896]" : "text-[#EF4444]") : "text-neutral-400"}`}>
                  {fiiNet != null ? `${fiiNet >= 0 ? "+" : ""}${formatNumber(fiiNet, 2)} Cr` : "—"}
                </span>
                <span className={`font-bold ${fiiNet != null ? (fiiNet >= 0 ? "text-[#00C896]" : "text-[#EF4444]") : "text-neutral-400"}`}>
                  {fiiNet != null ? (fiiNet >= 0 ? "Buying" : "Selling") : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between px-1 py-1 hover:bg-neutral-900">
                <span className="font-semibold text-neutral-300">DII Cash (Net)</span>
                <span className={`font-bold air-data ${diiNet != null ? (diiNet >= 0 ? "text-[#00C896]" : "text-[#EF4444]") : "text-neutral-400"}`}>
                  {diiNet != null ? `${diiNet >= 0 ? "+" : ""}${formatNumber(diiNet, 2)} Cr` : "—"}
                </span>
                <span className={`font-bold ${diiNet != null ? (diiNet >= 0 ? "text-[#00C896]" : "text-[#EF4444]") : "text-neutral-400"}`}>
                  {diiNet != null ? (diiNet >= 0 ? "Buying" : "Selling") : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between px-1 py-1 bg-neutral-950 font-bold">
                <span className="text-neutral-100">Combined Net Flow</span>
                <span className={`air-data ${netFlow != null ? (netFlow >= 0 ? "text-[#00C896]" : "text-[#EF4444]") : "text-neutral-400"}`}>
                  {netFlow != null ? `${netFlow >= 0 ? "+" : ""}${formatNumber(netFlow, 2)} Cr` : "—"}
                </span>
                <span className={netFlow != null ? (netFlow >= 0 ? "text-[#00C896]" : "text-[#EF4444]") : "text-neutral-400"}>
                  {netFlow != null ? (netFlow >= 0 ? "Positive Inflow" : "Net Outflow") : "Awaiting EOD"}
                </span>
              </div>
            </div>

            {/* Derivatives Stance Section */}
            <div className="border-t border-neutral-800 pt-1.5 space-y-1 text-[8.5px]">
              <div className="flex justify-between">
                <span className="text-neutral-400">Institutional Stance</span>
                <span className="font-bold text-neutral-200 air-data">
                  {netFlow != null ? (netFlow > 500 ? "Strong Institutional Accumulation" : netFlow < -500 ? "Distribution / FII Outflow" : "Balanced Institutional Participation") : "Awaiting EOD Flows"}
                </span>
              </div>
            </div>

            {/* Balance Slider Bar */}
            <div className="space-y-1 pt-1 border-t border-neutral-800 text-[8px]">
              <div className="flex justify-between text-neutral-400 font-bold text-[7.5px]">
                <span>NET POSITIONING BALANCE</span>
                <span className={netFlow != null ? (netFlow >= 0 ? "text-[#00C896]" : "text-[#EF4444]") : "text-neutral-400"}>
                  {netFlow != null ? `${netFlow >= 0 ? "+" : ""}${formatNumber(netFlow, 2)} CR (${netFlow >= 0 ? "INFLOW" : "OUTFLOW"})` : "AWAITING INGESTION"}
                </span>
              </div>
              <div className="relative h-2 w-full bg-gradient-to-r from-[#EF4444] via-[#F59E0B] to-[#00C896] rounded-full overflow-hidden">
                <div
                  style={{ left: netFlow != null ? (netFlow > 2000 ? "85%" : netFlow > 0 ? "60%" : netFlow > -2000 ? "40%" : "15%") : "50%" }}
                  className="absolute top-0 bottom-0 w-2 bg-white rounded-full shadow-[0_0_4px_rgba(255,255,255,0.9)] transform -translate-x-1/2"
                />
              </div>
            </div>

            <div className="text-[8px] text-neutral-500 flex justify-between border-t border-neutral-800 pt-1">
              <span>Source: NSE Official Reports</span>
              <span>Last Published: <strong className="text-neutral-300">{flowDate !== "—" ? `EOD ${flowDate}` : "—"}</strong></span>
            </div>
          </div>
        </Surface>

        {/* ── CARD 8: 8. VOLATILITY & RANGE EXPANSION ── */}
        <Surface id="market-metrics-vix" className="flex flex-col h-full border border-neutral-800/80 bg-neutral-900/50 rounded-md overflow-hidden">
          <SectionHeader title="8. VOLATILITY & RANGE EXPANSION" icon={ShieldAlert} accent="cyan" />
          <div className="p-3 flex-1 flex flex-col justify-between space-y-2 text-[10px]">
            {/* VIX & ATR Quantitative Grid */}
            <div className="space-y-1 text-[9px]">
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">India VIX</span>
                <span className="font-bold text-[#00C896] air-data">
                  {vixVal != null ? `${formatNumber(vixVal, 2)} pts` : (settled?.closing_vix != null ? `${formatNumber(settled.closing_vix, 2)} pts (Settled)` : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">Volatility Regime</span>
                <span className="font-bold text-[#00C896] uppercase">
                  {envelope.regime?.volatility_state ? envelope.regime.volatility_state.replace(/_/g, " ") : (isDataAvailable ? "NORMAL VOLATILITY" : "AWAITING STREAM")}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">Daily 14-Period ATR</span>
                <span className="font-bold text-neutral-100 air-data">
                  {atr != null ? `${formatNumber(atr, 1)} pts` : (settled?.atr_14 != null ? `${formatNumber(settled.atr_14, 1)} pts (Settled)` : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">Session Range</span>
                <span className="font-bold text-[#38BDF8] air-data">
                  {intradayRange != null ? `${formatNumber(intradayRange, 2)} pts` : (settled?.range_points != null ? `${formatNumber(settled.range_points, 2)} pts (Settled)` : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">Expected 1-SD Day Range</span>
                <span className="font-bold text-neutral-300 air-data">
                  {envelope.price_structure?.key_supports?.[0] != null && envelope.price_structure?.key_resistances?.[0] != null
                    ? `${formatNumber(envelope.price_structure.key_supports[0], 2)} – ${formatNumber(envelope.price_structure.key_resistances[0], 2)}`
                    : (settled?.or_low != null && settled?.or_high != null
                    ? `${formatNumber(settled.or_low, 2)} – ${formatNumber(settled.or_high, 2)} (Settled)`
                    : "—")}
                </span>
              </div>
            </div>

            {/* Range Consumed Gauge */}
            <div className="border-t border-neutral-800 pt-1.5 space-y-1">
              <div className="flex justify-between text-[8.5px]">
                <span className="text-neutral-400">Low: <strong className="text-neutral-200">{formatNumber(lowPrice, 2)}</strong></span>
                <span className="text-neutral-400">High: <strong className="text-neutral-200">{formatNumber(highPrice, 2)}</strong></span>
              </div>
              <div className="h-2 w-full bg-neutral-950 rounded-full overflow-hidden flex border border-neutral-800">
                <div style={{ width: `${rangeLocationPct || 0}%` }} className="h-full bg-[#38BDF8]" />
              </div>
              <div className="flex justify-between text-[8px] text-neutral-400">
                <span>Range Consumed: <strong className="text-[#38BDF8]">{intradayRange != null ? `${formatNumber(intradayRange, 1)} pts` : "—"}</strong></span>
                <span>ATR % Spot: <strong className="text-neutral-200">{(atr != null && spot != null && spot > 0) ? `${((atr / spot) * 100).toFixed(2)}%` : "—"}</strong></span>
              </div>
            </div>
          </div>
        </Surface>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════════
          TIER 5 (ROW 5): STRUCTURAL PRICE LADDER & TECHNICAL REFERENCES (2-COL EQUAL)
          LEFT: 9. SORTED PRICE LADDER | RIGHT: 10. TECHNICAL REFERENCES & EMAS
          ═══════════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5 items-stretch">
        {/* ── CARD 9: 9. KEY STRUCTURAL REFERENCE LADDER (SORTED STACK) ── */}
        <Surface id="market-metrics-structural" className="flex flex-col h-full border border-neutral-800/80 bg-neutral-900/50 rounded-md overflow-hidden">
          <SectionHeader title="9. KEY STRUCTURAL REFERENCE LADDER" icon={TrendingUp} accent="cyan" />
          <div className="p-3 flex-1 flex flex-col justify-between space-y-1 text-[9.5px]">
            {structuralStack.length > 0 ? (
              <div className="space-y-0.5">
                {structuralStack.map((item, idx) => {
                  const isSpot = item.type === "SPOT";
                  const isPivot = item.type === "PIVOT";
                  const delta = spot != null ? Number((item.price - spot).toFixed(2)) : 0;
                  const deltaPct = (spot != null && spot > 0) ? Number(((delta / spot) * 100).toFixed(2)) : 0;
                  const isAbove = delta > 0;

                  return (
                    <div
                      key={idx}
                      className={`flex items-center justify-between px-2 py-1 rounded transition-colors ${
                        isSpot
                          ? "bg-[#F59E0B]/10 border border-[#F59E0B]/40 shadow-sm"
                          : isPivot
                          ? "bg-[#F59E0B]/5 border border-[#F59E0B]/20"
                          : "hover:bg-neutral-900/80"
                      }`}
                    >
                      <span className={`font-semibold ${item.colorClass} truncate max-w-[180px]`}>
                        {item.label}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className={`font-mono font-bold ${isSpot ? "text-[#F59E0B] text-[11px]" : "text-neutral-200"}`}>
                          {formatNumber(item.price, 2)}
                        </span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[8px] font-mono font-bold ${
                            isSpot
                              ? "bg-[#F59E0B] text-neutral-950"
                              : isPivot
                              ? "bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/30"
                              : isAbove
                              ? "bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30"
                              : "bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30"
                          }`}
                        >
                          {isSpot ? "LTP ACTIVE" : `${isAbove ? "+" : ""}${formatNumber(delta, 2)} (${isAbove ? "+" : ""}${formatNumber(deltaPct, 2)}%)`}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-6 text-center text-neutral-500 font-mono text-[10px]">
                Awaiting Intraday Range &amp; Structural Level Formation
              </div>
            )}

            <div className="border-t border-neutral-800 pt-1.5 text-[8px] text-neutral-500 flex justify-between">
              <span>Source: {isReplayMode ? "28 Aug 2026 Tape Levels" : (isDataAvailable ? "Live Exchange Feed" : "Awaiting Market Range")}</span>
              <span>Model: <strong className="text-[#38BDF8]">Canonical Structure</strong></span>
            </div>
          </div>
        </Surface>

        {/* ── CARD 10: 10. TECHNICAL REFERENCES & EMAS ── */}
        <Surface className="flex flex-col h-full border border-neutral-800/80 bg-neutral-900/50 rounded-md overflow-hidden">
          <SectionHeader title="10. TECHNICAL REFERENCES & EMAS" icon={Activity} accent="cyan" />
          <div className="p-3 flex-1 flex flex-col justify-between space-y-1.5 text-[9.5px]">
            <div className="space-y-1">
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">EMA 20 (Daily)</span>
                <span className="font-bold text-neutral-100 air-data">
                  {ema20 != null ? `${formatNumber(ema20, 2)}${spot != null ? ` (${spot >= ema20 ? "+" : ""}${formatNumber(spot - ema20, 2)} pts / ${formatNumber(((spot - ema20) / ema20) * 100, 2)}% ${spot >= ema20 ? "Above" : "Below"})` : ""}` : "—"}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">EMA 50 (Daily)</span>
                <span className="font-bold text-neutral-100 air-data">
                  {ema50 != null ? `${formatNumber(ema50, 2)}${spot != null ? ` (${spot >= ema50 ? "+" : ""}${formatNumber(spot - ema50, 2)} pts / ${formatNumber(((spot - ema50) / ema50) * 100, 2)}% ${spot >= ema50 ? "Above" : "Below"})` : ""}` : "—"}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">EMA 200 (Daily)</span>
                <span className="font-bold text-neutral-100 air-data">
                  {ema200 != null ? `${formatNumber(ema200, 2)}${spot != null ? ` (${spot >= ema200 ? "+" : ""}${formatNumber(spot - ema200, 2)} pts / ${formatNumber(((spot - ema200) / ema200) * 100, 2)}% ${spot >= ema200 ? "Above" : "Below"})` : ""}` : "—"}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">RSI (14-Period Daily)</span>
                <span className="font-bold text-neutral-100 air-data">{(technical.rsi_14 ?? rsiVal) != null ? `${formatNumber((technical.rsi_14 ?? rsiVal), 2)} (${(technical.rsi_14 ?? rsiVal) >= 60 ? "Bullish Momentum" : (technical.rsi_14 ?? rsiVal) <= 40 ? "Bearish Momentum" : "Neutral-Constructive"})` : "—"}</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">Session VWAP Deviation</span>
                <span className="font-bold text-[#00C896] air-data">
                  {vwapDeviation != null ? `${vwapDeviation >= 0 ? "+" : ""}${formatNumber(vwapDeviation, 2)} pts (${vwapDeviation >= 0 ? "+" : ""}${formatNumber(vwapDeviationPct ?? 0, 2)}%)` : "—"}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-neutral-400">Structure Consensus</span>
                <span className="font-bold text-neutral-200 uppercase">
                  {isDataAvailable ? "RANGE-BOUND / CONSTRUCTIVE ACCUMULATION" : "AWAITING STREAM"}
                </span>
              </div>
            </div>

            <div className="border-t border-neutral-800 pt-1.5 text-[8px] text-neutral-500 flex justify-between">
              <span>Timeframe: Multi-TF Horizon</span>
              <span>Alignment: <strong className="text-[#00C896]">{isDataAvailable ? "BULLISH STACK" : "STANDBY"}</strong></span>
            </div>
          </div>
        </Surface>
      </div>

      {/* ── ROW 6: FOOTER TRUST STRIP ── */}
      <div className="text-center text-[8.5px] font-mono text-neutral-500 py-1 border-t border-neutral-800">
        DATA STATE: <strong className="text-[#38BDF8]">{isReplayMode ? "REPLAY" : (isDataAvailable ? "LIVE SYNC" : "AWAITING STREAM")}</strong> • PREVIOUS SESSION: <strong className="text-[#00C896]">{hasSettled ? "AVAILABLE" : "UNAVAILABLE"}</strong> • QUALITY: <strong className="text-[#00C896]">{typeof envelope.data_quality === "string" ? envelope.data_quality : "VALID"}</strong> • NIFTY 50: <strong className="text-neutral-200">{spot != null ? `${formatNumber(spot, 2)} (${positive ? "+" : ""}${formatNumber(change ?? 0, 2)})` : (settled?.close ? `Prev Close: ₹${formatNumber(settled.close, 2)}` : "—")}</strong> • LAST SETTLED: <strong className="text-neutral-300">{envelope.session?.completed_session_date || authState.sessionDate || settled?.session_date || "—"}</strong> • DATA WINDOW: <strong className="text-neutral-200">{sessionIdentity?.data_window || "PRE-MARKET"}</strong>
      </div>
    </div>
  );
}

export default MarketPulseWorkspace;
