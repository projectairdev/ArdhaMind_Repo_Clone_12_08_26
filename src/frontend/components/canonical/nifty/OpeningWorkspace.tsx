/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Professional NIFTY Opening Workspace (NIFTY -> OPENING).
 * Represents the first 15 minutes of continuous NSE trading (09:15 – 09:30 IST):
 * - Focus: "Is the opening move being confirmed?"
 * - Top Summary Strip: NIFTY 50, Open, OR High, OR Low, OR Range, VIX, Time Elapsed & Remaining
 * - Main Analytical Surface: CanonicalTradingChart (~65% width, ~560px height) + Right Intelligence Stack (~35% width)
 *   - Card 1: MARKET STRUCTURE — LIVE (OPENING RANGE)
 *   - Card 2: KEY LEVELS (Evidence Based with ORH, ORL, VWAP, S/R)
 *   - Card 3: OPENING RANGE TRACKER (Start, End, Elapsed, Remaining, ORH, ORL, Range, Position in OR)
 *   - Card 4: OPENING EXPECTATION & PLAN (Confirmation First, Upside/Downside/Invalidation Scenarios)
 * - Bottom Connected Context Row (4 equal height panels):
 *   - GLOBAL CONTEXT
 *   - INSTITUTIONAL FLOWS — PREVIOUS SESSION
 *   - SECTOR LEADERSHIP — SINCE OPEN
 *   - OPENING CHECKLIST (09:15 – 09:30)
 * - Zero Provider Telemetry Cards on Trader Page
 */

import React, { useState, useMemo } from "react";
import { CanonicalFrontendEnvelope } from "../../../types/canonical";
import { CanonicalTradingChart } from "../chart/CanonicalTradingChart";
import {
  Compass,
  Target,
  Globe,
  Crosshair,
  Clock,
  Layers,
  Activity,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Sliders,
} from "lucide-react";
import { formatNumber } from "../../../utils/safeHelpers";
import { useCanonicalState } from "../../../context/CanonicalStateContext";

export function OpeningWorkspace({
  envelope,
}: {
  envelope: CanonicalFrontendEnvelope;
}) {
  const { session, market, breadth, options, candles, data_quality } = envelope;
  const price_structure = envelope.price_structure || ({} as any);
  const nifty = market?.nifty || ({} as any);
  const vix = market?.vix || ({} as any);
  const m1Candles = candles?.["1m"] || [];

  let isReplay = false;
  let sessionIdentity: any = null;
  try {
    const context = useCanonicalState();
    isReplay = context.isReplayMode || context.isFixtureData;
    sessionIdentity = context.sessionIdentity;
  } catch {
    // Isolated tests
  }

  const [checklist, setChecklist] = useState<Record<number, boolean>>({
    0: true,
    1: true,
    2: false,
    3: false,
    4: false,
    5: false,
  });

  const toggleCheck = (i: number) => setChecklist((prev) => ({ ...prev, [i]: !prev[i] }));

  // Opening Range Calculations
  const orHigh = price_structure.or_high ?? null;
  const orLow = price_structure.or_low ?? null;
  const currentPrice = nifty.last_price ?? null;
  const openPrice = price_structure.open ?? null;
  const prevClose = price_structure.previous_close ?? envelope.settled_session?.close ?? null;
  const orRange = (orHigh != null && orLow != null) ? Math.max(0.1, orHigh - orLow) : null;
  const orRangePct = (orRange != null && openPrice != null && openPrice > 0) ? (orRange / openPrice) * 100 : null;

  // Position in Opening Range (0% to 100%)
  const positionInOr = useMemo(() => {
    if (currentPrice == null || orLow == null || orRange == null || orRange <= 0) return 50;
    const raw = ((currentPrice - orLow) / orRange) * 100;
    return Math.max(0, Math.min(100, Math.round(raw)));
  }, [currentPrice, orLow, orRange]);

  const isOrComplete =
    price_structure.opening_range_status === "CONFIRMED_BREAKOUT_UP" ||
    price_structure.opening_range_status === "CONFIRMED_BREAKOUT_DOWN" ||
    price_structure.opening_range_status === "FAILED_BREAKOUT" ||
    session?.market_phase === "MARKET_OPEN";

  return (
    <div className="flex flex-col gap-1.5 font-mono text-[#E6E8EB] select-none">
      {/* 1. TOP HEADER STRIP: Hero Price & Connected Metric Cells */}
      <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] px-3 py-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Main NIFTY Quote */}
          <div className="flex items-baseline gap-2.5">
            <span className="text-xl lg:text-2xl font-bold text-[#F0F6FC] tracking-tight">NIFTY 50</span>
            <span className={`text-xl lg:text-2xl font-bold tracking-tight ${(nifty.change ?? 0) >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
              {currentPrice != null ? formatNumber(currentPrice, 2) : "Unavailable"}
            </span>
            <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded-[2px] ${(nifty.change ?? 0) >= 0 ? "bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30" : "bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30"}`}>
              {nifty.change != null ? `${nifty.change >= 0 ? "+" : ""}${formatNumber(nifty.change, 2)} (${nifty.change_pct != null ? (nifty.change_pct >= 0 ? "+" : "") + formatNumber(nifty.change_pct, 2) : "0.00"}%)` : "—"}
            </span>
          </div>

          {/* Connected Metrics Cells */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <div className="rounded-[2px] bg-[#12151A] px-2 py-1 border border-[#222832]">
              <span className="text-[9px] text-[#707987] block uppercase">PREV. CLOSE</span>
              <span className="font-bold text-[#E6E8EB] text-[11px]">
                {prevClose != null ? formatNumber(prevClose, 2) : "—"}
              </span>
            </div>

            <div className="rounded-[2px] bg-[#12151A] px-2 py-1 border border-[#222832]">
              <span className="text-[9px] text-[#707987] block uppercase">OPEN</span>
              <span className="font-bold text-[#38BDF8] text-[11px]">
                {openPrice != null ? formatNumber(openPrice, 2) : "—"}
              </span>
            </div>

            <div className="rounded-[2px] bg-[#12151A] px-2 py-1 border border-[#222832]">
              <span className="text-[9px] text-[#707987] block uppercase">HIGH (OR)</span>
              <span className="font-bold text-[#00C896] text-[11px]">
                {orHigh != null ? formatNumber(orHigh, 2) : "—"}
              </span>
            </div>

            <div className="rounded-[2px] bg-[#12151A] px-2 py-1 border border-[#222832]">
              <span className="text-[9px] text-[#707987] block uppercase">LOW (OR)</span>
              <span className="font-bold text-[#EF4444] text-[11px]">
                {orLow != null ? formatNumber(orLow, 2) : "—"}
              </span>
            </div>

            <div className="rounded-[2px] bg-[#12151A] px-2.5 py-1 border border-[#222832]">
              <span className="text-[9px] text-[#707987] block uppercase">OR RANGE</span>
              <span className="font-bold text-[#E6E8EB] text-[11px]">
                {orRange != null ? `${formatNumber(orRange, 2)} (${orRangePct != null ? formatNumber(orRangePct, 2) : "0.00"}%)` : "—"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. MAIN ANALYTICAL SURFACE: Multi-TF Chart (65%) + Right 4-Card Stack (35%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-1.5 items-stretch">
        {/* Left Surface: Multi-TF Canonical Trading Chart */}
        <div className="lg:col-span-8 flex flex-col min-h-[480px] lg:min-h-[560px]">
          <CanonicalTradingChart
            candles={m1Candles}
            priceStructure={price_structure}
            height={560}
            sessionDate={session?.active_trading_date || session?.completed_session_date || "—"}
            marketPhase={session?.market_phase || "OPENING_RANGE"}
          />
        </div>

        {/* Right Surface: 4-Card Intelligence Stack */}
        <div className="lg:col-span-4 flex flex-col gap-1.5 h-full">
          {/* Card 1: Market Structure Expectations */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 space-y-1">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 text-[10px]">
              <div className="flex items-center gap-1 font-bold text-[#8B949E] uppercase">
                <Compass className="w-3 h-3 text-[#38BDF8]" />
                <span>OPENING RANGE STRUCTURE</span>
              </div>
              <span className="text-[8.5px] px-1.5 py-0.2 rounded-[2px] bg-[#00C896]/15 text-[#00C896] font-bold border border-[#00C896]/30">
                {envelope.regime?.regime_type ? String(envelope.regime.regime_type).replace(/_/g, " ") : "FORMING"}
              </span>
            </div>

            <div className="flex items-baseline justify-between mb-0.5 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-[#707987]">BIAS (OR):</span>
                <span className="font-bold text-[#00C896]">
                  {price_structure.opening_range_status ? String(price_structure.opening_range_status).replace(/_/g, " ") : "EVALUATING"}
                </span>
              </div>
              <span className="text-[10px] text-[#707987]">
                Confidence: <strong className="text-[#38BDF8]">{envelope.prediction?.confidence_score ?? "—"}%</strong>
              </span>
            </div>

            <p className="text-[10px] text-[#8B949E] leading-tight mb-2">
              {currentPrice != null && price_structure.vwap != null
                ? `Trading at ${positionInOr}% of Opening Range vs VWAP (${(currentPrice - price_structure.vwap) >= 0 ? "+" : ""}${formatNumber(currentPrice - price_structure.vwap, 1)} pts).`
                : "Awaiting live opening range formation."}
            </p>

            <div className="grid grid-cols-3 gap-1 pt-1 border-t border-[#1C2128] text-[9.5px]">
              <div className="rounded-[2px] bg-[#12151A] p-1 border border-[#20252E]">
                <span className="text-[8.5px] text-[#707987] block truncate">BREADTH</span>
                <span className="font-bold text-[#00C896]">{breadth.advance_pct != null ? `${formatNumber(breadth.advance_pct, 0)}%` : "—"}</span>
              </div>
              <div className="rounded-[2px] bg-[#12151A] p-1 border border-[#20252E]">
                <span className="text-[8.5px] text-[#707987] block">OR Status</span>
                <span className="font-bold text-[#38BDF8]">{isOrComplete ? "LOCKED" : "FORMING"}</span>
              </div>
              <div className="rounded-[2px] bg-[#12151A] p-1 border border-[#20252E]">
                <span className="text-[8.5px] text-[#707987] block">Regime</span>
                <span className="font-bold text-[#00C896]">{envelope.regime?.regime_type ? String(envelope.regime.regime_type).replace(/_/g, " ") : "RANGE BOUND"}</span>
              </div>
            </div>
          </div>

          {/* Card 2: Key Levels (Evidence Based) */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 space-y-1">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 text-[10px] text-[#8B949E] font-bold uppercase">
              <div className="flex items-center gap-1">
                <Target className="w-3 h-3 text-[#38BDF8]" />
                <span>KEY LEVELS</span>
              </div>
              <span className="text-[8.5px] px-1 py-0.2 rounded-[2px] bg-[#161A22] text-[#38BDF8] border border-[#2B333E]">
                {envelope.settled_session ? "SETTLED LEVELS" : "EVIDENCE BASED"}
              </span>
            </div>

            <div className="space-y-0.5 text-[10.5px]">
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#EF4444] font-bold">Major Resistance (R2)</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_resistances?.[1] != null ? formatNumber(price_structure.key_resistances[1], 2) : (envelope.settled_session?.structural_levels?.r2 != null ? formatNumber(envelope.settled_session.structural_levels.r2, 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#EF4444] font-bold">Immediate Resistance (R1)</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_resistances?.[0] != null ? formatNumber(price_structure.key_resistances[0], 2) : (envelope.settled_session?.structural_levels?.r1 != null ? formatNumber(envelope.settled_session.structural_levels.r1, 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22] bg-[#00C896]/5 px-1 rounded-[2px]">
                <span className="text-[#00C896] font-bold">Opening Range High (ORH)</span>
                <span className="font-bold text-[#00C896]">{orHigh != null ? formatNumber(orHigh, 2) : "—"}</span>
              </div>
              <div className="flex justify-between py-0.5 bg-[#F59E0B]/5 px-1 rounded-[2px] border border-[#F59E0B]/20">
                <span className="text-[#F59E0B] font-bold">Reference Pivot / VWAP</span>
                <span className="font-bold text-[#F59E0B]">
                  {price_structure?.vwap != null ? formatNumber(price_structure.vwap, 2) : (envelope.settled_session?.structural_levels?.pivot != null ? formatNumber(envelope.settled_session.structural_levels.pivot, 2) : (envelope.settled_session?.vwap != null ? formatNumber(envelope.settled_session.vwap, 2) : "—"))}
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22] bg-[#EF4444]/5 px-1 rounded-[2px]">
                <span className="text-[#EF4444] font-bold">Opening Range Low (ORL)</span>
                <span className="font-bold text-[#EF4444]">{orLow != null ? formatNumber(orLow, 2) : "—"}</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#00C896] font-bold">Immediate Support (S1)</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_supports?.[0] != null ? formatNumber(price_structure.key_supports[0], 2) : (envelope.settled_session?.structural_levels?.s1 != null ? formatNumber(envelope.settled_session.structural_levels.s1, 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-[#00C896] font-bold">Major Support (S2)</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_supports?.[1] != null ? formatNumber(price_structure.key_supports[1], 2) : (envelope.settled_session?.structural_levels?.s2 != null ? formatNumber(envelope.settled_session.structural_levels.s2, 2) : "—")}
                </span>
              </div>
            </div>
          </div>

          {/* Card 3: Opening Range Tracker */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 space-y-1">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 text-[10px] text-[#8B949E] font-bold uppercase">
              <div className="flex items-center gap-1">
                <Activity className="w-3 h-3 text-[#38BDF8]" />
                <span>OPENING RANGE TRACKER</span>
              </div>
              <span className={`text-[8.5px] px-1 py-0.2 rounded-[2px] font-bold border ${
                isOrComplete
                  ? "bg-[#00C896]/15 text-[#00C896] border-[#00C896]/30"
                  : "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30"
              }`}>
                {isOrComplete ? "COMPLETE" : "FORMING"}
              </span>
            </div>

            <div className="space-y-0.5 text-[10px]">
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#707987]">OR Start Time</span>
                <span className="font-bold text-[#E6E8EB]">09:15:00</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#707987]">OR End Time</span>
                <span className="font-bold text-[#E6E8EB]">09:30:00</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#707987]">OR High</span>
                <span className="font-bold text-[#00C896]">{orHigh != null ? formatNumber(orHigh, 2) : "—"}</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#707987]">OR Low</span>
                <span className="font-bold text-[#EF4444]">{orLow != null ? formatNumber(orLow, 2) : "—"}</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#707987]">OR Range</span>
                <span className="font-bold text-[#E6E8EB]">{orRange != null ? `${formatNumber(orRange, 2)} (${orRangePct != null ? formatNumber(orRangePct, 2) : "0.00"}%)` : "—"}</span>
              </div>
              <div className="flex items-center justify-between pt-1">
                <span className="text-[#707987] text-[9.5px]">Position in OR</span>
                <div className="flex items-center gap-2 w-32">
                  <div className="flex-1 h-1.5 bg-[#1C2128] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#00C896] rounded-full transition-all duration-300"
                      style={{ width: `${positionInOr}%` }}
                    />
                  </div>
                  <span className="text-[9.5px] font-bold text-[#00C896]">{positionInOr}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Card 4: Opening Expectation & Plan */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 space-y-1">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 text-[10px]">
              <div className="flex items-center gap-1 font-bold text-[#8B949E] uppercase">
                <Crosshair className="w-3 h-3 text-[#38BDF8]" />
                <span>OPENING EXPECTATION & PLAN</span>
              </div>
              <span className="text-[8.5px] px-1 py-0.2 rounded-[2px] bg-[#161A22] text-[#38BDF8] font-bold border border-[#2B333E]">
                CONFIRMATION FIRST
              </span>
            </div>

            <div className="space-y-1 text-[10px]">
              <div className="rounded-[2px] bg-[#00C896]/5 p-1.5 border border-[#00C896]/20">
                <span className="font-bold text-[#00C896] block text-[9.5px]">UPSIDE SCENARIO</span>
                <p className="text-[#D1D5DB] text-[10px] mt-0.5 leading-tight">
                  {orHigh != null ? `Sustain above OR High ${formatNumber(orHigh, 2)} with volume expansion.` : "Sustain above 15m Opening Range High with confirmed volume."}
                </p>
              </div>

              <div className="rounded-[2px] bg-[#EF4444]/5 p-1.5 border border-[#EF4444]/20">
                <span className="font-bold text-[#EF4444] block text-[9.5px]">DOWNSIDE SCENARIO</span>
                <p className="text-[#D1D5DB] text-[10px] mt-0.5 leading-tight">
                  {orLow != null ? `Break below OR Low ${formatNumber(orLow, 2)} with institutional selling.` : "Break below 15m Opening Range Low with tape rejection."}
                </p>
              </div>

              <div className="pt-0.5 text-[9px] text-[#707987]">
                <span>Invalidation: <strong className="text-[#EF4444]">{envelope.settled_session?.low != null ? `Loss of ${formatNumber(envelope.settled_session.low, 2)} on sustained basis` : "Loss of session opening reference"}</strong></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. CONNECTED CONTEXT ROW: 4 Equal Height Connected Panels */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-1.5 items-stretch">
        {/* Col 1: Global Context */}
        <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
          <div className="border-b border-[#1C2128] pb-1 mb-1 flex justify-between items-center text-[10px]">
            <span className="font-bold text-[#8B949E] uppercase flex items-center gap-1">
              <Globe className="w-3 h-3 text-[#38BDF8]" />
              GLOBAL CONTEXT
            </span>
            <span className="text-[8.5px] text-[#38BDF8] font-bold">MONITORING</span>
          </div>

          <div className="text-[9.5px] my-auto text-neutral-400">
            Awaiting market open macro data stream.
          </div>

          <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#555E6D]">
            Intraday Global Watch
          </div>
        </div>

        {/* Col 2: Institutional Flows — Previous Session */}
        <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
          <div className="border-b border-[#1C2128] pb-1 mb-1">
            <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">INSTITUTIONAL FLOWS</span>
            <span className="text-[8.5px] text-[#555E6D]">{envelope.settled_session?.session_date || "Awaiting Publication"}</span>
          </div>

          <div className="space-y-1.5 text-[10.5px] my-auto">
            <div className="flex justify-between">
              <span className="text-[#8B949E]">FII (Cash)</span>
              <span className="font-bold text-[#EF4444]">{envelope.settled_session?.institutional_flows?.fii_net != null ? `${formatNumber(envelope.settled_session.institutional_flows.fii_net, 1)} Cr` : "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8B949E]">DII (Cash)</span>
              <span className="font-bold text-[#00C896]">{envelope.settled_session?.institutional_flows?.dii_net != null ? `${formatNumber(envelope.settled_session.institutional_flows.dii_net, 1)} Cr` : "—"}</span>
            </div>
            <div className="flex justify-between border-t border-[#1C2128] pt-0.5">
              <span className="text-[#8B949E]">Net Institutional</span>
              <span className="font-bold text-[#00C896]">{envelope.settled_session?.institutional_flows?.net != null ? `${formatNumber(envelope.settled_session.institutional_flows.net, 1)} Cr` : "—"}</span>
            </div>
          </div>

          <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#555E6D]">
            NSE Official Cash EOD
          </div>
        </div>

        {/* Col 3: Sector Leadership */}
        <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
          <div className="border-b border-[#1C2128] pb-1 mb-1">
            <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">SECTOR LEADERSHIP</span>
          </div>

          <div className="text-[9.5px] my-auto text-neutral-400">
            Awaiting opening sector leadership stream.
          </div>

          <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#555E6D]">
            Since Open (Intraday Basis)
          </div>
        </div>

        {/* Col 4: Opening Checklist (09:15 - 09:30) */}
        <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
          <div className="border-b border-[#1C2128] pb-1 mb-1">
            <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">OPENING CHECKLIST (09:15 - 09:30)</span>
          </div>

          <div className="space-y-1 text-[9.5px] my-auto">
            {[
              "1. Track OR High / OR Low",
              "2. Confirm VWAP behavior",
              "3. Watch price near OR extremes",
              "4. Confirm NIFTY breadth",
              "5. Confirm sector participation",
              "6. Wait for breakout/rejection confirmation",
            ].map((text, idx) => (
              <label
                key={idx}
                className="flex items-center gap-1.5 cursor-pointer text-[#C9D1D9] hover:text-[#E6E8EB]"
              >
                <input
                  type="checkbox"
                  checked={Boolean(checklist[idx])}
                  onChange={() => toggleCheck(idx)}
                  className="accent-[#00C896] w-3 h-3 cursor-pointer"
                />
                <span className={`truncate text-[9.5px] ${checklist[idx] ? "text-[#00C896]" : ""}`}>{text}</span>
              </label>
            ))}
          </div>

          <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#00C896]">
            Checklist Active
          </div>
        </div>
      </div>

      {/* 4. BOTTOM TRUST FOOTER */}
      <div className="flex flex-wrap items-center justify-between px-3 py-1 rounded-[2px] border border-[#1E232B] bg-[#0E1013] text-[9.5px] text-[#707987]">
        <div className="flex items-center gap-3">
          <span>DATA STATE: <strong className="text-[#38BDF8]">{isReplay ? "REPLAY" : (data_quality === "UNAVAILABLE" ? "AWAITING STREAM" : "LIVE FEED")}</strong></span>
          <span>•</span>
          <span>PREVIOUS SESSION: <strong className="text-[#00C896]">{envelope.settled_session ? "AVAILABLE" : "UNAVAILABLE"}</strong></span>
          <span>•</span>
          <span>LAST SETTLED: <strong className="text-neutral-300">{envelope.settled_session?.session_date ? String(envelope.settled_session.session_date).toUpperCase() : "—"}</strong></span>
          <span>•</span>
          <span>CANONICAL DATA: <strong className={data_quality === "VALID" ? "text-[#00C896]" : "text-amber-400"}>{typeof data_quality === "string" ? data_quality : "VALID"}</strong></span>
        </div>

        <div className="flex items-center gap-1.5 text-[#707987]">
          <span>Source: <strong className="text-[#8B949E]">{isReplay ? "Historical Fixture" : "NSE Real-Time Feed"}</strong></span>
        </div>
      </div>
    </div>
  );
}
