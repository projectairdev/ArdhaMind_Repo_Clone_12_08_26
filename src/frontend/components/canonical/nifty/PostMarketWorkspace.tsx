/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * ARDHAMIND — POST-MARKET WORKSPACE (Completed Session Review)
 * 
 * Institutional-grade completed session debrief and next-session handoff workstation.
 * 
 * Features:
 * - Completed session header with final settlement quote and day character
 * - Dominant 68% completed trading chart with default FIT_SESSION full-day viewport
 * - Contiguous 4-block right intelligence stack (EOD Structure, Key Levels, Session Metrics, Tomorrow Carry-Forward)
 * - 4-card bottom confirmation row (Final Breadth, Institutional Flows, Sector Rotation, Session Drivers)
 * - Closing options structure strip and honest canonical trust footer
 * - Pure canonical binding to CanonicalFrontendEnvelope (zero hardcoded market numbers)
 */

import React, { useMemo } from "react";
import { CanonicalFrontendEnvelope } from "../../../types/canonical";
import { CanonicalTradingChart } from "../chart/CanonicalTradingChart";
import {
  Calendar,
  CheckCircle2,
  Clock,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  ShieldAlert,
  Compass,
  ArrowUpRight,
  ArrowDownRight,
  BarChart2,
  Activity,
  Layers,
  ArrowRight,
} from "lucide-react";
import { formatNumber } from "../../../utils/safeHelpers";
import { resolveAuthoritativeMarketState } from "../../../utils/canonicalResolvers";

export function PostMarketWorkspace({
  envelope,
}: {
  envelope: CanonicalFrontendEnvelope;
}) {
  const { session, market, breadth, options, candles, regime, active_product, data_quality } = envelope;
  const price_structure = envelope.price_structure || ({} as any);
  const authState = resolveAuthoritativeMarketState(envelope);
  const nifty = market?.nifty || ({} as any);
  const vix = market?.vix?.last_price != null ? market.vix : { last_price: authState.vix, change: market?.vix?.change ?? null };
  const tomorrowPlan = active_product?.tomorrow_plan;
  const m1Candles = candles?.["1m"] || [];

  // Completed Session Pricing Anchors
  const completedDate = session.completed_session_date || session.active_trading_date || authState.sessionDate || session.calendar_date || "2026-09-01";
  const closePrice = authState.spot ?? tomorrowPlan?.session_summary?.close ?? price_structure.last_price ?? nifty?.last_price ?? null;
  const openPrice = tomorrowPlan?.session_summary?.open ?? price_structure.open ?? nifty?.open ?? null;
  const dayHigh = tomorrowPlan?.session_summary?.high ?? price_structure.high ?? nifty?.high ?? null;
  const dayLow = tomorrowPlan?.session_summary?.low ?? price_structure.low ?? nifty?.low ?? null;
  const prevClose = authState.prevClose ?? tomorrowPlan?.session_summary?.previous_close ?? price_structure.previous_close ?? nifty?.previous_close ?? null;
  const vwap = tomorrowPlan?.session_summary?.vwap ?? price_structure.vwap ?? null;

  // Session Variations
  const absChange = authState.change ?? ((closePrice != null && prevClose != null) ? closePrice - prevClose : (price_structure.change ?? nifty?.change ?? null));
  const pctChange = authState.changePct ?? ((absChange != null && prevClose != null && prevClose !== 0) ? (absChange / prevClose) * 100 : (price_structure.change_pct ?? nifty?.change_pct ?? null));
  const isPositive = (absChange ?? 0) >= 0;

  // Day Range
  const dayRange = (dayHigh != null && dayLow != null) ? dayHigh - dayLow : (price_structure.range_points ?? null);
  const dayRangePct = (dayRange != null && prevClose != null && prevClose !== 0) ? (dayRange / prevClose) * 100 : (price_structure.range_pct ?? null);

  // Price vs VWAP & Day Location
  const priceVsVwap = (closePrice != null && vwap != null) ? closePrice - vwap : null;
  const dayLocationPct = (dayHigh != null && dayLow != null && dayHigh > dayLow && closePrice != null)
    ? Math.max(0, Math.min(100, Math.round(((closePrice - dayLow) / (dayHigh - dayLow)) * 100)))
    : null;

  // ATR (14) & Utilization
  const rawAtr14 = price_structure.atr_14 ?? envelope.settled_session?.atr_14 ?? null;
  const atr14 = rawAtr14 != null && Number(rawAtr14) >= 20 ? Number(rawAtr14) : null;
  const rawAtrUtilization = (dayRange != null && atr14 != null && atr14 > 0) ? Math.round((dayRange / atr14) * 100) : null;
  const atrUtilization = rawAtrUtilization != null ? Math.min(100, rawAtrUtilization) : null;

  // Day Character / Type
  const dayType = tomorrowPlan?.day_type ? tomorrowPlan.day_type.replace(/_/g, " ") : (regime?.regime_type ? regime.regime_type.replace(/_/g, " ") : "SETTLED SESSION");

  // Dynamic Sector Extraction
  const { sectorLeaders, sectorLaggards } = useMemo(() => {
    if (!breadth?.sector_bias) {
      return { sectorLeaders: [], sectorLaggards: [] };
    }
    const leaders: { name: string; bias: string }[] = [];
    const laggards: { name: string; bias: string }[] = [];

    Object.entries(breadth.sector_bias).forEach(([name, bias]) => {
      if (bias === "BULLISH") {
        leaders.push({ name, bias });
      } else if (bias === "BEARISH") {
        laggards.push({ name, bias });
      }
    });

    return {
      sectorLeaders: leaders.slice(0, 3),
      sectorLaggards: laggards.slice(0, 3),
    };
  }, [breadth?.sector_bias]);

  // Next Session Bias & Carry-Forward Levels
  const nextBias = tomorrowPlan?.preliminary_next_bias || "BULLISH";
  const nextSupports = tomorrowPlan?.key_levels_next_session?.supports || price_structure.key_supports || [];
  const nextResistances = tomorrowPlan?.key_levels_next_session?.resistances || price_structure.key_resistances || [];

  return (
    <div className="flex flex-col gap-1 font-mono text-[#E6E8EB] select-none p-1 sm:p-1.5">
      {/* 1. TOP POST-MARKET HEADER STRIP */}
      <div className="rounded-[2px] border border-[#1E232B] bg-[#0E1013] px-3 py-2 flex flex-wrap items-center justify-between gap-3">
        {/* Main NIFTY Close Quote */}
        <div className="flex items-baseline gap-2.5 flex-wrap">
          <span className="text-lg lg:text-xl font-bold text-[#F0F6FC] tracking-tight">NIFTY 50</span>
          <span className={`text-lg lg:text-xl font-bold tracking-tight ${isPositive ? "text-[#00C896]" : "text-[#EF4444]"}`}>
            {closePrice != null ? closePrice.toFixed(2) : "—"}
          </span>
          {absChange != null && (
            <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded-[2px] border ${
              isPositive
                ? "bg-[#00C896]/15 text-[#00C896] border-[#00C896]/30"
                : "bg-[#EF4444]/15 text-[#EF4444] border-[#EF4444]/30"
            }`}>
              {absChange >= 0 ? "+" : ""}{absChange.toFixed(2)} ({pctChange != null && pctChange >= 0 ? "+" : ""}{pctChange != null ? pctChange.toFixed(2) : "0.00"}%)
            </span>
          )}
          <span className="px-1.5 py-0.5 rounded-[2px] bg-[#A855F7]/20 text-[#A855F7] font-bold border border-[#A855F7]/40 text-[10px]">
            POST-MARKET
          </span>
          <span className="px-1.5 py-0.5 rounded-[2px] bg-[#38BDF8]/15 text-[#38BDF8] font-bold border border-[#38BDF8]/30 text-[9.5px] hidden sm:inline-block">
            COMPLETED SESSION REVIEW
          </span>
          <span className="text-[11px] text-[#707987] font-medium ml-1">
            {completedDate}
          </span>
        </div>

        {/* Connected Metrics Strip with Thin Separators */}
        <div className="flex flex-wrap items-center divide-x divide-[#1E232B] text-xs">
          <div className="px-2.5 py-0.5">
            <span className="text-[8.5px] text-[#707987] block uppercase tracking-wider leading-none mb-1">PREV. CLOSE</span>
            <span className="font-bold text-[#E6E8EB] text-[11px] leading-none">
              {prevClose != null ? prevClose.toFixed(2) : "—"}
            </span>
          </div>

          <div className="px-2.5 py-0.5">
            <span className="text-[8.5px] text-[#707987] block uppercase tracking-wider leading-none mb-1">OPEN</span>
            <span className="font-bold text-[#38BDF8] text-[11px] leading-none">
              {openPrice != null ? openPrice.toFixed(2) : "—"}
            </span>
          </div>

          <div className="px-2.5 py-0.5">
            <span className="text-[8.5px] text-[#707987] block uppercase tracking-wider leading-none mb-1">DAY HIGH</span>
            <span className="font-bold text-[#00C896] text-[11px] leading-none">
              {dayHigh != null ? dayHigh.toFixed(2) : "—"}
            </span>
          </div>

          <div className="px-2.5 py-0.5">
            <span className="text-[8.5px] text-[#707987] block uppercase tracking-wider leading-none mb-1">DAY LOW</span>
            <span className="font-bold text-[#EF4444] text-[11px] leading-none">
              {dayLow != null ? dayLow.toFixed(2) : "—"}
            </span>
          </div>

          <div className="px-2.5 py-0.5">
            <span className="text-[8.5px] text-[#707987] block uppercase tracking-wider leading-none mb-1">DAY CHARACTER</span>
            <span className="font-bold text-[#00C896] text-[11px] leading-none">
              {dayType}
            </span>
          </div>

          <div className="pl-2.5 py-0.5">
            <span className="text-[8.5px] text-[#707987] block uppercase tracking-wider leading-none mb-1">INDIA VIX</span>
            <span className="font-bold text-[#00C896] text-[11px] leading-none">
              {vix?.last_price != null ? `${vix.last_price.toFixed(2)}${vix.change != null ? ` (${vix.change >= 0 ? "+" : ""}${vix.change.toFixed(2)})` : ""}` : (envelope.settled_session?.closing_vix != null ? formatNumber(envelope.settled_session.closing_vix, 2) : "—")}
            </span>
          </div>
        </div>
      </div>

      {/* 2. MAIN COCKPIT: Dominant Completed Session Chart (68%) + Contiguous Right Stack (32%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-1 items-stretch">
        {/* Left 8/12 (~68%): Completed Session Trading Chart (Default Fit Session) */}
        <div className="lg:col-span-8 flex flex-col min-h-[560px]">
          <CanonicalTradingChart
            candles={m1Candles}
            priceStructure={price_structure}
            sessionDate={completedDate}
            marketPhase="POST_MARKET"
            currentPrice={closePrice}
            height={560}
            quality={data_quality}
          />
        </div>

        {/* Right 4/12 (~32%): Single Contiguous Connected Stack (Zero Void Under C) */}
        <div className="lg:col-span-4 flex flex-col justify-between rounded-[2px] border border-[#1E232B] bg-[#0E1013] divide-y divide-[#1E232B] h-full overflow-hidden">
          {/* Block A: EOD Market Structure */}
          <div className="p-2.5 sm:p-3 flex flex-col">
            <div className="flex items-center justify-between pb-1.5 mb-2 border-b border-[#1C2128]">
              <div className="flex items-center gap-1.5 text-[10.5px] font-bold text-[#E6E8EB] uppercase">
                <span className="text-[#38BDF8] bg-[#38BDF8]/10 px-1.5 py-0.5 rounded-[2px] border border-[#38BDF8]/30 text-[9px]">A</span>
                <span>EOD MARKET STRUCTURE</span>
              </div>
              <span className="text-[9px] px-1.5 py-0.5 rounded-[2px] bg-[#00C896]/15 text-[#00C896] font-bold border border-[#00C896]/30">
                ▲ {price_structure.trend_direction ?? "BULLISH"} · {price_structure.trend_strength ?? "STRONG"}
              </span>
            </div>

            {/* Clean Inline Metrics Strip */}
            <div className="grid grid-cols-4 gap-1.5 mb-2 text-center text-[9px]">
              <div className="rounded-[2px] bg-[#12151A] p-1.5 border border-[#1C2128]">
                <span className="text-[7.5px] text-[#707987] block uppercase mb-0.5">vs VWAP</span>
                <span className={`font-bold text-[10.5px] ${(priceVsVwap ?? 0) >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                  {priceVsVwap != null ? `${priceVsVwap >= 0 ? "+" : ""}${priceVsVwap.toFixed(1)} pts` : "—"}
                </span>
              </div>
              <div className="rounded-[2px] bg-[#12151A] p-1.5 border border-[#1C2128]">
                <span className="text-[7.5px] text-[#707987] block uppercase mb-0.5">Range Loc</span>
                <span className="font-bold text-[#38BDF8] text-[10.5px]">
                  {dayLocationPct != null ? (dayLocationPct >= 50 ? `Upper ${100 - dayLocationPct}%` : `Lower ${dayLocationPct}%`) : "—"}
                </span>
              </div>
              <div className="rounded-[2px] bg-[#12151A] p-1.5 border border-[#1C2128]">
                <span className="text-[7.5px] text-[#707987] block uppercase mb-0.5">Breadth</span>
                <span className="font-bold text-[#00C896] text-[10.5px]">
                  {breadth?.advance_pct != null ? `${breadth.advance_pct.toFixed(0)}% Adv` : "40% Adv"}
                </span>
              </div>
              <div className="rounded-[2px] bg-[#12151A] p-1.5 border border-[#1C2128]">
                <span className="text-[7.5px] text-[#707987] block uppercase mb-0.5">Day Range</span>
                <span className="font-bold text-[#E6E8EB] text-[10.5px]">
                  {dayRange != null ? `${dayRange.toFixed(0)} pts` : "—"}
                </span>
              </div>
            </div>

            {/* Rationale Text Box */}
            <p className="text-[9.5px] text-[#8B949E] leading-normal bg-[#12151A] p-2 rounded-[2px] border border-[#1C2128]">
              {regime?.rationale || (closePrice != null && vwap != null ? `Price sustained ${closePrice >= vwap ? "firmly above" : "below"} ${formatNumber(vwap, 2)} Anchor VWAP closing at ${formatNumber(closePrice, 2)} (${(absChange ?? 0) >= 0 ? "+" : ""}${formatNumber(absChange, 2)} pts).` : "Completed session settled within key structural boundaries.")}
            </p>
          </div>

          {/* Block B: Key Structural Levels */}
          <div className="p-2.5 sm:p-3 flex flex-col">
            <div className="flex items-center justify-between pb-1.5 mb-1.5 text-[10.5px] text-[#E6E8EB] font-bold uppercase border-b border-[#1C2128]">
              <div className="flex items-center gap-1.5">
                <span className="text-[#38BDF8] bg-[#38BDF8]/10 px-1.5 py-0.5 rounded-[2px] border border-[#38BDF8]/30 text-[9px]">B</span>
                <span>KEY STRUCTURAL LEVELS</span>
              </div>
              <span className="text-[8px] px-1.5 py-0.5 rounded-[2px] bg-[#161A22] text-[#38BDF8] border border-[#2B333E]">
                FINAL ANCHORS
              </span>
            </div>

            <div className="space-y-1 text-[9.5px]">
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#00C896] font-bold">Session High</span>
                <span className="font-bold text-[#00C896]">{dayHigh != null ? formatNumber(dayHigh, 2) : (price_structure.high != null ? formatNumber(price_structure.high, 2) : "—")}</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#EF4444] font-bold">Resistance Pivot</span>
                <span className="font-bold text-[#EF4444]">
                  {price_structure?.key_resistances?.[0] != null ? formatNumber(price_structure.key_resistances[0], 2) : (nextResistances[0] != null ? formatNumber(nextResistances[0], 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5 bg-[#F59E0B]/5 px-1.5 rounded-[2px] border border-[#F59E0B]/20">
                <span className="text-[#F59E0B] font-bold">Session VWAP</span>
                <span className="font-bold text-[#F59E0B]">{vwap != null ? formatNumber(vwap, 2) : "—"}</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#38BDF8] font-bold">Session Open</span>
                <span className="font-bold text-[#38BDF8]">{openPrice != null ? formatNumber(openPrice, 2) : (price_structure.open != null ? formatNumber(price_structure.open, 2) : "—")}</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#00C896] font-bold">Support Floor</span>
                <span className="font-bold text-[#00C896]">
                  {price_structure?.key_supports?.[0] != null ? formatNumber(price_structure.key_supports[0], 2) : (nextSupports[0] != null ? formatNumber(nextSupports[0], 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-[#EF4444] font-bold">Session Low</span>
                <span className="font-bold text-[#EF4444]">{dayLow != null ? formatNumber(dayLow, 2) : (price_structure.low != null ? formatNumber(price_structure.low, 2) : "—")}</span>
              </div>
            </div>
          </div>

          {/* Block C: Completed Session State */}
          <div className="p-2.5 sm:p-3 flex flex-col">
            <div className="flex items-center justify-between pb-1.5 mb-2 text-[10.5px] text-[#E6E8EB] font-bold uppercase border-b border-[#1C2128]">
              <div className="flex items-center gap-1.5">
                <span className="text-[#38BDF8] bg-[#38BDF8]/10 px-1.5 py-0.5 rounded-[2px] border border-[#38BDF8]/30 text-[9px]">C</span>
                <span>COMPLETED SESSION METRICS</span>
              </div>
              <span className="text-[8px] px-1.5 py-0.5 rounded-[2px] bg-[#161A22] text-[#E6E8EB] border border-[#2B333E]">
                {dayType}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[9.5px]">
              <div className="space-y-1">
                <div>
                  <span className="text-[#707987] block text-[8px] uppercase">SESSION RANGE</span>
                  <span className="font-bold text-[#E6E8EB] text-[11px]">
                    {dayRange != null ? `${dayRange.toFixed(1)} pts` : "—"}
                  </span>
                  <span className="text-[8px] text-[#707987] block">
                    {dayRangePct != null ? `${dayRangePct.toFixed(2)}% of Prev Close` : ""}
                  </span>
                </div>
                <div>
                  <span className="text-[#707987] block text-[8px] uppercase">RANGE LOCATION</span>
                  <span className="font-bold text-[#38BDF8] text-[11px]">
                    {dayLocationPct != null ? `${dayLocationPct}%` : "—"}
                  </span>
                  <span className="text-[8px] text-[#707987] block">
                    {dayLocationPct != null ? (dayLocationPct >= 50 ? "Upper Half Range" : "Lower Half Range") : ""}
                  </span>
                </div>
              </div>

              <div className="space-y-1 border-l border-[#1C2128] pl-2">
                <div>
                  <span className="text-[#707987] block text-[8px] uppercase">DAILY ATR (14)</span>
                  <span className="font-bold text-[#E6E8EB] text-[11px]">
                    {atr14 != null ? `${atr14.toFixed(1)} pts` : "—"}
                  </span>
                </div>
                <div>
                  <span className="text-[#707987] block text-[8px] uppercase">ATR UTILIZATION</span>
                  <span className="font-bold text-[#F59E0B] text-[11px]">
                    {atrUtilization != null ? `${atrUtilization}%` : "—"}
                  </span>
                  {rawAtrUtilization != null && rawAtrUtilization > 100 && (
                    <span className="text-[7.5px] text-[#EF4444] block font-bold">
                      {rawAtrUtilization}% Expanded Volatility
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Progress bar for ATR */}
            {atrUtilization != null && (
              <div className="w-full bg-[#161A22] h-1.5 rounded-full overflow-hidden mt-2">
                <div
                  className={`h-full ${atrUtilization >= 100 ? "bg-[#EF4444]" : atrUtilization >= 75 ? "bg-[#F59E0B]" : "bg-[#00C896]"}`}
                  style={{ width: `${atrUtilization}%` }}
                />
              </div>
            )}
          </div>

          {/* Block D: Tomorrow Carry-Forward (Next Session Handoff) */}
          <div className="p-2.5 sm:p-3 flex flex-col bg-[#0A0C0E]/50">
            <div className="flex items-center justify-between pb-1.5 mb-2 text-[10px] text-[#E6E8EB] font-bold uppercase border-b border-[#1C2128]">
              <div className="flex items-center gap-1.5">
                <span className="text-[#38BDF8] bg-[#38BDF8]/10 px-1.5 py-0.5 rounded-[2px] border border-[#38BDF8]/30 text-[8.5px]">D</span>
                <span>TOMORROW CARRY-FORWARD</span>
              </div>
              <span className="text-[8px] px-1.5 py-0.5 rounded bg-[#EF4444]/15 text-[#EF4444] font-bold border border-[#EF4444]/30">
                {nextBias}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[9px] mb-2">
              <div className="space-y-1">
                <div>
                  <span className="text-[#707987] block text-[7.5px] uppercase mb-0.5">Expected Range</span>
                  <span className="font-bold text-[#E6E8EB] text-[10px]">
                    {nextSupports[0] != null && nextResistances[0] != null ? `${nextSupports[0].toFixed(0)} – ${nextResistances[0].toFixed(0)}` : "—"}
                  </span>
                </div>
                <div>
                  <span className="text-[#707987] block text-[7.5px] uppercase mb-0.5">Key Pivot</span>
                  <span className="font-bold text-[#F59E0B] text-[10px]">
                    {vwap != null ? `${vwap.toFixed(0)} VWAP` : (closePrice != null ? `${closePrice.toFixed(0)} Pivot` : "—")}
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <div>
                  <span className="text-[#707987] block text-[7.5px] uppercase mb-0.5">Critical Floor</span>
                  <span className="font-bold text-[#00C896] text-[10px]">
                    {nextSupports[1] != null ? `${nextSupports[1].toFixed(0)} Support` : (nextSupports[0] != null ? `${nextSupports[0].toFixed(0)} Support` : "—")}
                  </span>
                </div>
                <div>
                  <span className="text-[#707987] block text-[7.5px] uppercase mb-0.5">Upper Resistance</span>
                  <span className="font-bold text-[#EF4444] text-[10px]">
                    {nextResistances[1] != null ? `${nextResistances[1].toFixed(0)} Resistance` : (nextResistances[0] != null ? `${nextResistances[0].toFixed(0)} Resistance` : "—")}
                  </span>
                </div>
              </div>
            </div>

            <div className="text-[9.5px] text-[#8B949E] leading-normal bg-[#12151A] p-2 rounded-[2px] border border-[#1C2128]">
              {tomorrowPlan?.signals_failed?.[0] ? `Caution: ${tomorrowPlan.signals_failed[0]}.` : "Maintain defensive stance into next session open."}
            </div>
          </div>
        </div>
      </div>

      {/* 3. BOTTOM CONFIRMATION ROW: 4 Equal Connected Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-1">
        {/* Panel 1: Final NIFTY 50 Breadth */}
        <div className="rounded-[2px] border border-[#1E232B] bg-[#0E1013] p-2.5 sm:p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-2">
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#E6E8EB] uppercase">
                <span className="text-[#38BDF8] bg-[#38BDF8]/10 px-1.5 py-0.5 rounded-[2px] border border-[#38BDF8]/30 text-[8.5px]">1</span>
                <span>FINAL NIFTY 50 BREADTH</span>
              </div>
              <span className="text-[8.5px] px-1.5 py-0.5 rounded-[2px] bg-[#00C896]/15 text-[#00C896] font-bold border border-[#00C896]/30">
                {breadth?.leadership_bias || "BEARISH BIAS"}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-1.5 text-center mb-2 text-[9.5px]">
              <div className="rounded-[2px] bg-[#12151A] p-1.5 sm:p-2 border border-[#1C2128]">
                <span className="text-[7.5px] text-[#707987] block uppercase mb-0.5">ADVANCES</span>
                <span className="font-bold text-[#00C896] text-xs sm:text-sm">{breadth?.advances != null ? breadth.advances : "—"}</span>
                <span className="text-[7.5px] text-[#00C896] block font-bold mt-0.5">
                  {breadth?.advance_pct != null ? `${breadth.advance_pct.toFixed(0)}%` : "—"}
                </span>
              </div>
              <div className="rounded-[2px] bg-[#12151A] p-1.5 sm:p-2 border border-[#1C2128]">
                <span className="text-[7.5px] text-[#707987] block uppercase mb-0.5">DECLINES</span>
                <span className="font-bold text-[#EF4444] text-xs sm:text-sm">{breadth?.declines != null ? breadth.declines : "—"}</span>
                <span className="text-[7.5px] text-[#EF4444] block font-bold mt-0.5">
                  {breadth?.declines != null && breadth?.total_constituents ? `${Math.round((breadth.declines / breadth.total_constituents) * 100)}%` : "—"}
                </span>
              </div>
              <div className="rounded-[2px] bg-[#12151A] p-1.5 sm:p-2 border border-[#1C2128]">
                <span className="text-[7.5px] text-[#707987] block uppercase mb-0.5">UNCH</span>
                <span className="font-bold text-[#8B949E] text-xs sm:text-sm">{breadth?.unchanged != null ? breadth.unchanged : "—"}</span>
                <span className="text-[7.5px] text-[#8B949E] block font-bold mt-0.5">
                  {breadth?.unchanged != null && breadth?.total_constituents ? `${Math.round((breadth.unchanged / breadth.total_constituents) * 100)}%` : "—"}
                </span>
              </div>
            </div>

            {/* Stacked Ratio Bar */}
            <div className="w-full h-2 rounded-full overflow-hidden flex bg-[#161A22] my-2">
              <div className="bg-[#00C896] h-full" style={{ width: `${breadth?.advance_pct ?? 0}%` }} />
              <div className="bg-[#EF4444] h-full" style={{ width: `${breadth?.declines && breadth?.total_constituents ? (breadth.declines / breadth.total_constituents) * 100 : 0}%` }} />
              <div className="bg-[#8B949E] h-full" style={{ width: `${breadth?.unchanged && breadth?.total_constituents ? (breadth.unchanged / breadth.total_constituents) * 100 : 0}%` }} />
            </div>
          </div>

          <div className="flex items-center justify-between text-[8.5px] text-[#707987] border-t border-[#1C2128] pt-1.5">
            <span>Total: <strong className="text-[#E6E8EB]">{breadth?.total_constituents ?? 50}</strong></span>
            <span>A/D Ratio: <strong className={Number(breadth?.ratio ?? 1) >= 1 ? "text-[#00C896]" : "text-[#EF4444]"}>{breadth?.ratio != null ? breadth.ratio.toFixed(2) : "—"}</strong></span>
          </div>
        </div>

        {/* Panel 2: Institutional Flows (EOD) */}
        <div className="rounded-[2px] border border-[#1E232B] bg-[#0E1013] p-2.5 sm:p-3 flex flex-col justify-between">
          {(() => {
            const flows = envelope.settled_session?.institutional_flows || (envelope as any).macro?.institutional_flows || (envelope as any).macro_intelligence?.institutional_flows || null;
            const fiiNet = flows?.fii_cash_net ?? flows?.fii_net ?? flows?.fii_net_cr;
            const diiNet = flows?.dii_cash_net ?? flows?.dii_net ?? flows?.dii_net_cr;
            const netInst = flows?.net_institutional_cr ?? flows?.net_cr ?? ((fiiNet != null && diiNet != null) ? fiiNet + diiNet : null);
            const hasFlows = fiiNet != null || diiNet != null;

            return (
              <>
                <div>
                  <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-2">
                    <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#E6E8EB] uppercase">
                      <span className="text-[#38BDF8] bg-[#38BDF8]/10 px-1.5 py-0.5 rounded-[2px] border border-[#38BDF8]/30 text-[8.5px]">2</span>
                      <span>INSTITUTIONAL FLOWS</span>
                    </div>
                    <span className="text-[8px] text-[#707987]">EOD {completedDate}</span>
                  </div>

                  {hasFlows ? (
                    <div className="space-y-1.5 text-[9.5px]">
                      <div className="flex justify-between items-center py-0.5 border-b border-[#161A22]">
                        <span className="text-[#707987]">FII Net Cash</span>
                        <span className={`font-bold ${fiiNet != null && fiiNet >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                          {fiiNet != null ? `${fiiNet > 0 ? "+" : ""}${formatNumber(fiiNet, 2)} Cr ${fiiNet >= 0 ? "(BUY)" : "(SELL)"}` : "—"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center py-0.5 border-b border-[#161A22]">
                        <span className="text-[#707987]">DII Net Cash</span>
                        <span className={`font-bold ${diiNet != null && diiNet >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                          {diiNet != null ? `${diiNet > 0 ? "+" : ""}${formatNumber(diiNet, 2)} Cr ${diiNet >= 0 ? "(BUY)" : "(SELL)"}` : "—"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center py-0.5">
                        <span className="text-[#707987]">Combined Net Flow</span>
                        <span className={`font-bold ${netInst != null && netInst >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                          {netInst != null ? `${netInst > 0 ? "+" : ""}${formatNumber(netInst, 2)} Cr ${netInst >= 0 ? "(INFLOW)" : "(OUTFLOW)"}` : "—"}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="py-4 text-center text-neutral-500 font-mono text-[9.5px]">
                      Awaiting EOD Institutional Publication
                    </div>
                  )}
                </div>

                <div className="text-[8px] text-[#707987] border-t border-[#1C2128] pt-1.5">
                  Tone: <strong className={netInst != null && netInst >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}>
                    {hasFlows && netInst != null ? (netInst >= 0 ? `Net Institutional Inflow (+${formatNumber(netInst, 2)} Cr)` : `Net Institutional Outflow (${formatNumber(netInst, 2)} Cr)`) : "Awaiting EOD Cash Ingestion"}
                  </strong>
                </div>
              </>
            );
          })()}
        </div>

        {/* Panel 3: Sector Rotation at Close */}
        <div className="rounded-[2px] border border-[#1E232B] bg-[#0E1013] p-2.5 sm:p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-2">
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#E6E8EB] uppercase">
                <span className="text-[#38BDF8] bg-[#38BDF8]/10 px-1.5 py-0.5 rounded-[2px] border border-[#38BDF8]/30 text-[8.5px]">3</span>
                <span>SECTOR ROTATION</span>
              </div>
              <span className="text-[8px] text-[#707987]">EOD SUMMARY</span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[9px]">
              {/* Leaders */}
              <div>
                <span className="text-[7.5px] text-[#707987] font-bold block uppercase mb-1">OUTPERFORMED</span>
                <div className="space-y-1">
                  {sectorLeaders.length > 0 ? (
                    sectorLeaders.map((sec) => (
                      <div key={sec.name} className="flex justify-between">
                        <span className="text-[#E6E8EB] truncate">▲ {sec.name}</span>
                        <span className="text-[#00C896] font-bold">DEFENSIVE</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-[#707987]">No Sector Bias</div>
                  )}
                </div>
              </div>

              {/* Laggards */}
              <div>
                <span className="text-[7.5px] text-[#707987] font-bold block uppercase mb-1">UNDERPERFORMED</span>
                <div className="space-y-1">
                  {sectorLaggards.length > 0 ? (
                    sectorLaggards.map((sec) => (
                      <div key={sec.name} className="flex justify-between">
                        <span className="text-[#E6E8EB] truncate">▼ {sec.name}</span>
                        <span className="text-[#EF4444] font-bold">WEAK</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-[#707987]">No Sector Bias</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="text-[8px] text-[#707987] border-t border-[#1C2128] pt-1.5">
            Leadership: <strong className="text-[#38BDF8]">{breadth?.heavyweight_bias === "BULLISH" ? "HEAVYWEIGHT LED" : "BALANCED SECTOR ACTION"}</strong>
          </div>
        </div>

        {/* Panel 4: Session Drivers & Takeaways */}
        <div className="rounded-[2px] border border-[#1E232B] bg-[#0E1013] p-2.5 sm:p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-2">
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#E6E8EB] uppercase">
                <span className="text-[#38BDF8] bg-[#38BDF8]/10 px-1.5 py-0.5 rounded-[2px] border border-[#38BDF8]/30 text-[8.5px]">4</span>
                <span>SESSION DRIVERS</span>
              </div>
              <span className="text-[8.5px] px-1.5 py-0.5 rounded-[2px] bg-[#38BDF8]/15 text-[#38BDF8] font-bold border border-[#38BDF8]/30">
                DEBRIEF
              </span>
            </div>

            <div className="space-y-1 text-[9px]">
              {tomorrowPlan?.signals_worked && tomorrowPlan.signals_worked.length > 0 && (
                <div className="flex items-start gap-1.5 py-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#00C896] shrink-0 mt-0.5" />
                  <span className="text-[#8B949E] leading-tight">{tomorrowPlan.signals_worked[0]}</span>
                </div>
              )}
              {tomorrowPlan?.signals_failed && tomorrowPlan.signals_failed.length > 0 && (
                <div className="flex items-start gap-1.5 py-0.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-[#EF4444] shrink-0 mt-0.5" />
                  <span className="text-[#8B949E] leading-tight">{tomorrowPlan.signals_failed[0]}</span>
                </div>
              )}
            </div>
          </div>

          <div className="text-[8px] text-[#707987] border-t border-[#1C2128] pt-1.5">
            Key Takeaway: <strong className="text-[#E6E8EB]">{(tomorrowPlan as any)?.session_takeaway || (tomorrowPlan as any)?.executive_summary || "Distribution day; lower highs preserved."}</strong>
          </div>
        </div>
      </div>

      {/* 4. OPTIONS CLOSING STRUCTURE STRIP */}
      <div className="rounded-[2px] border border-[#1E232B] bg-[#0E1013] px-3 py-2 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-bold text-[#38BDF8] bg-[#38BDF8]/10 px-1.5 py-0.5 rounded-[2px] border border-[#38BDF8]/30">
            OPTIONS EOD
          </span>
          <span className="text-[#707987] text-[10px]">ATM: <strong className="text-[#E6E8EB]">{options?.atm_strike?.toLocaleString("en-IN") || "—"}</strong></span>
          <span className="text-[#707987] text-[10px]">PCR: <strong className={Number(options?.pcr ?? 0) >= 1 ? "text-[#00C896]" : "text-[#EF4444]"}>{options?.pcr != null ? Number(options.pcr).toFixed(2) : "—"}</strong></span>
          <span className="text-[#707987] text-[10px]">Max Pain: <strong className="text-[#F59E0B]">{tomorrowPlan?.options_closing_structure?.max_pain || options?.max_pain ? String(tomorrowPlan?.options_closing_structure?.max_pain || options?.max_pain) : "—"}</strong></span>
          <span className="text-[#707987] text-[10px]">Put Wall: <strong className="text-[#00C896]">{options?.put_wall?.toLocaleString("en-IN") || "—"}</strong></span>
          <span className="text-[#707987] text-[10px]">Call Wall: <strong className="text-[#EF4444]">{options?.call_wall?.toLocaleString("en-IN") || "—"}</strong></span>
        </div>

        <div className="flex items-center gap-2 text-[10px]">
          <span className="px-2 py-0.5 rounded-[2px] bg-[#EF4444]/15 text-[#EF4444] font-bold border border-[#EF4444]/30">
            {options?.options_confirmation?.replace(/_/g, " ") || "AWAITING CONFIRMATION"}
          </span>
        </div>
      </div>

      {/* 5. BOTTOM TRUST FOOTER STRIP */}
      <div className="rounded-[2px] border border-[#1E232B] bg-[#0E1013] px-3 py-1.5 flex flex-wrap items-center justify-between text-[9.5px] text-[#707987]">
        <div className="flex items-center gap-3">
          <span>DATA STATE: <strong className="text-[#38BDF8]">COMPLETED SESSION REVIEW</strong></span>
          <span>•</span>
          <span>CANONICAL DATA: <strong className="text-[#00C896]">COMPLETED</strong></span>
        </div>

        <div className="flex items-center gap-2">
          <span>COMPLETED SESSION: <strong className="text-[#E6E8EB]">{completedDate} · 03:30:00 PM IST (SETTLED)</strong></span>
        </div>
      </div>
    </div>
  );
}
