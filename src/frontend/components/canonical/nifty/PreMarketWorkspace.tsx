/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Tight Connected Pre-Market Workspace (NIFTY -> MORNING -> PRE-MARKET).
 * Exactly matches approved reference design:
 * - Institutional connected card grid (zero dead space, 4-6px gutters, 2-4px radius)
 * - Single workstation feel: Top strip -> Main cockpit (Chart 65% + Right 35%) -> Bottom 5-column row -> Trust footer
 * - Zero provider telemetry cards on trader page
 * - Unambiguous card titles and temporal provenance
 */

import React, { useState } from "react";
import { CanonicalFrontendEnvelope } from "../../../types/canonical";
import { CanonicalNiftyChart } from "../CanonicalNiftyChart";
import { DirectionBadge } from "../ui/Badges";
import { Compass, Target, Globe, Crosshair, CheckSquare, Layers, ShieldCheck, CheckCircle2 } from "lucide-react";
import { useCanonicalState } from "../../../context/CanonicalStateContext";
import { formatNumber } from "../../../utils/safeHelpers";
import { resolveAuthoritativeMarketState } from "../../../utils/canonicalResolvers";
import { NiftyHeader } from "./NiftyHeader";

export function PreMarketWorkspace({
  envelope,
}: {
  envelope: CanonicalFrontendEnvelope;
}) {
  const { session, market, breadth, active_product, candles, data_quality } = envelope;
  const price_structure = envelope.price_structure || ({} as any);
  const nifty = market?.nifty;
  const vix = market?.vix;
  const m1Candles = (candles?.["1m"] && candles["1m"].length > 0)
    ? candles["1m"]
    : (candles?.["5m"] && candles["5m"].length > 0)
    ? candles["5m"]
    : ((envelope.candles as any)?.baseline && (envelope.candles as any).baseline.length > 0)
    ? (envelope.candles as any).baseline
    : ((envelope.settled_session as any)?.candles || []);
  const isPreOpen = session?.market_phase === "PRE_OPEN";
  const plan = active_product?.morning_plan;

  const authState = resolveAuthoritativeMarketState(envelope);
  const settledClose = (envelope.session?.market_phase === "PRE_MARKET" || envelope.session?.market_phase === "PRE_OPEN") ? (authState.spot ?? nifty?.last_price ?? envelope.settled_session?.close) : (envelope.settled_session?.close ?? authState.prevClose ?? nifty?.previous_close);
  const displaySpot = authState.spot ?? nifty?.last_price ?? price_structure?.last_price ?? settledClose ?? envelope?.settled_session?.close ?? null;
  const displayVix = authState.vix ?? vix?.last_price ?? vix?.previous_close ?? (typeof envelope.settled_session?.closing_vix === "object" ? (envelope.settled_session.closing_vix as any)?.vix_close : envelope.settled_session?.closing_vix) ?? (typeof (envelope.settled_session as any)?.vix === "object" ? (envelope.settled_session as any)?.vix?.vix_close : (envelope.settled_session as any)?.vix) ?? null;
  const settledHigh = authState.dayHigh ?? envelope.settled_session?.high;
  const settledLow = authState.dayLow ?? envelope.settled_session?.low;
  const settledVwap = authState.vwap ?? envelope.settled_session?.vwap;
  const settledRange = (settledHigh != null && settledLow != null) ? Number((settledHigh - settledLow).toFixed(1)) : (envelope.settled_session?.range_points ?? price_structure.range_points);
  const settledAtr = price_structure.atr_14 ?? envelope.settled_session?.atr_14;

  let isReplay = false;
  let sessionIdentity: any = null;
  try {
    const context = useCanonicalState();
    isReplay = context.isReplayMode || context.isFixtureData;
    sessionIdentity = context.sessionIdentity;
  } catch {
    // Isolated tests
  }

  const [checkedItems1, setCheckedItems1] = useState<Record<number, boolean>>({
    0: true,
    1: true,
    2: true,
    3: true,
    4: true,
    5: true,
    6: true,
  });
  const [checkedItems2, setCheckedItems2] = useState<Record<number, boolean>>({});

  const toggleCheck1 = (i: number) => setCheckedItems1((prev) => ({ ...prev, [i]: !prev[i] }));
  const toggleCheck2 = (i: number) => setCheckedItems2((prev) => ({ ...prev, [i]: !prev[i] }));

  const settledDateDisplay = envelope.settled_session?.session_date
    ? new Date(envelope.settled_session.session_date + "T00:00:00").toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }).toUpperCase()
    : "—";

  return (
    <div className="flex flex-col gap-1.5 font-mono text-[#E6E8EB] select-none">
      {/* 1. TOP HEADER STRIP: Modernized Hero Quote & Connected Settled Metrics */}
      <NiftyHeader envelope={envelope} marketPhase={isPreOpen ? "PRE_OPEN" : "PRE_MARKET"} />

      {/* 2. MAIN COCKPIT GRID: Left Chart (65%) + Right Intelligence Stack (35%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-1.5 items-stretch">
        {/* Left 8/12 (~65%): Main Pre-Market NIFTY Chart */}
        <div className="lg:col-span-8 flex flex-col min-h-[460px]">
          <CanonicalNiftyChart
            candles={m1Candles}
            sessionDate={session?.active_trading_date || session?.completed_session_date || "—"}
            marketPhase="PRE_MARKET"
            currentPrice={nifty?.last_price ?? (null as any)}
            previousClose={settledClose ?? (null as any)}
            vwap={price_structure.vwap ?? envelope.settled_session?.vwap ?? (null as any)}
            orHigh={price_structure.or_high ?? envelope.settled_session?.or_high ?? (null as any)}
            orLow={price_structure.or_low ?? envelope.settled_session?.or_low ?? (null as any)}
            supports={price_structure.key_supports?.length ? price_structure.key_supports : (envelope.settled_session?.structural_levels?.s1 ? [envelope.settled_session.structural_levels.s1, envelope.settled_session.structural_levels.s2].filter(Boolean) as number[] : [])}
            resistances={price_structure.key_resistances?.length ? price_structure.key_resistances : (envelope.settled_session?.structural_levels?.r1 ? [envelope.settled_session.structural_levels.r1, envelope.settled_session.structural_levels.r2].filter(Boolean) as number[] : [])}
            quality={data_quality}
          />
        </div>

        {/* Right 4/12 (~35%): Stacked Pre-Market Context Cards */}
        <div className="lg:col-span-4 flex flex-col gap-1.5 justify-between">
          {/* Card 1: Market Structure (Expectation) */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 mb-1.5">
              <div className="flex items-center gap-1 text-[10.5px] font-bold text-[#8B949E] uppercase">
                <Compass className="w-3 h-3 text-[#38BDF8]" />
                <span>MARKET REGIME (EXPECTATION)</span>
              </div>
              <span className="text-[9px] px-1.5 py-0.2 rounded-[2px] bg-[#00C896]/15 text-[#00C896] font-bold border border-[#00C896]/30">
                {envelope.regime?.regime_type ? String(envelope.regime.regime_type).replace(/_/g, " ") : "RANGE BOUND"}
              </span>
            </div>

            <div className="flex items-baseline justify-between mb-0.5">
              <span className="text-sm font-bold text-[#F0F6FC]">
                {isPreOpen ? "PRE-OPEN READ" : "PRE-MARKET ORIENTATION"}
              </span>
              <span className="text-[10px] text-[#707987]">
                CONFIDENCE: <strong className="text-[#38BDF8]">{envelope.prediction?.confidence_score ?? "—"}%</strong>
              </span>
            </div>

            <p className="text-[10px] text-[#8B949E] leading-tight mb-2">
              {settledClose != null
                ? `Previous session settled at ${formatNumber(settledClose, 2)} with settled range of ${settledRange != null ? formatNumber(settledRange, 1) : "—"} pts. Awaiting market open auction.`
                : "Awaiting market session settlement data and live feed initialization."}
            </p>

            <div className="grid grid-cols-3 gap-1 pt-1 border-t border-[#1C2128] text-[9.5px]">
              <div className="rounded-[2px] bg-[#12151A] p-1 border border-[#20252E]">
                <span className="text-[8.5px] text-[#707987] block">ATR (14)</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure.atr_14 != null ? `${formatNumber(price_structure.atr_14, 1)} pts` : (envelope.settled_session?.atr_14 != null ? `${formatNumber(envelope.settled_session.atr_14, 1)} pts` : "—")}
                </span>
              </div>
              <div className="rounded-[2px] bg-[#12151A] p-1 border border-[#20252E]">
                <span className="text-[8.5px] text-[#707987] block">VWAP (Settled)</span>
                <span className="font-bold text-[#F59E0B]">
                  {price_structure.vwap != null ? formatNumber(price_structure.vwap, 2) : (envelope.settled_session?.vwap != null ? formatNumber(envelope.settled_session.vwap, 2) : "—")}
                </span>
              </div>
              <div className="rounded-[2px] bg-[#12151A] p-1 border border-[#20252E]">
                <span className="text-[8.5px] text-[#707987] block">GAP STATUS</span>
                <span className="font-bold text-[#00C896]">
                  {price_structure.change != null ? `${price_structure.change >= 0 ? "+" : ""}${formatNumber(price_structure.change, 2)}` : "—"}
                </span>
              </div>
            </div>
          </div>

          {/* Card 2: Key Levels */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 space-y-1">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 text-[10px] text-[#8B949E] font-bold uppercase">
              <div className="flex items-center gap-1">
                <Target className="w-3 h-3 text-[#38BDF8]" />
                <span>KEY STRUCTURAL LEVELS</span>
              </div>
              <span className="text-[8.5px] px-1 py-0.2 rounded-[2px] bg-[#161A22] text-[#38BDF8] border border-[#2B333E]">
                {envelope.settled_session ? "SETTLED LEVELS" : "EVIDENCE BASED"}
              </span>
            </div>

            <div className="space-y-0.5 text-[10.5px]">
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#EF4444] font-bold">RESISTANCE 2</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_resistances?.[1] != null ? formatNumber(price_structure.key_resistances[1], 2) : (envelope.settled_session?.structural_levels?.r2 != null ? formatNumber(envelope.settled_session.structural_levels.r2, 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#EF4444] font-bold">RESISTANCE 1</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_resistances?.[0] != null ? formatNumber(price_structure.key_resistances[0], 2) : (envelope.settled_session?.structural_levels?.r1 != null ? formatNumber(envelope.settled_session.structural_levels.r1, 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5 bg-[#F59E0B]/5 px-1 rounded-[2px] border border-[#F59E0B]/20">
                <span className="text-[#F59E0B] font-bold">PIVOT (VWAP)</span>
                <span className="font-bold text-[#F59E0B]">
                  {price_structure?.vwap != null ? formatNumber(price_structure.vwap, 2) : (envelope.settled_session?.structural_levels?.pivot != null ? formatNumber(envelope.settled_session.structural_levels.pivot, 2) : (envelope.settled_session?.vwap != null ? formatNumber(envelope.settled_session.vwap, 2) : "—"))}
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#00C896] font-bold">SUPPORT 1</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_supports?.[0] != null ? formatNumber(price_structure.key_supports[0], 2) : (envelope.settled_session?.structural_levels?.s1 != null ? formatNumber(envelope.settled_session.structural_levels.s1, 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#00C896] font-bold">SUPPORT 2</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_supports?.[1] != null ? formatNumber(price_structure.key_supports[1], 2) : (envelope.settled_session?.structural_levels?.s2 != null ? formatNumber(envelope.settled_session.structural_levels.s2, 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-[#00C896] font-bold">SUPPORT 3</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_supports?.[2] != null ? formatNumber(price_structure.key_supports[2], 2) : (envelope.settled_session?.structural_levels?.s3 != null ? formatNumber(envelope.settled_session.structural_levels.s3, 2) : "—")}
                </span>
              </div>
            </div>
          </div>

          {/* Card 3: Global Cues & Overnight Context */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 mb-1 text-[10px]">
              <div className="flex items-center gap-1 font-bold text-[#8B949E] uppercase">
                <Globe className="w-3 h-3 text-[#38BDF8]" />
                <span>INSTITUTIONAL POSITIONING & FLOWS</span>
              </div>
              <span className="text-[8.5px] px-1 py-0.2 rounded-[2px] bg-[#161A22] text-[#38BDF8] font-bold">
                {envelope.settled_session?.institutional_flows?.fii_net != null ? "EOD SETTLED" : "AWAITING PUBLICATION"}
              </span>
            </div>

            <div className="space-y-0.5 text-[10px]">
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#707987]">FII (CASH)</span>
                <div className="flex gap-2">
                  <span className={`font-bold ${(envelope.settled_session?.institutional_flows?.fii_net ?? 0) >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                    {envelope.settled_session?.institutional_flows?.fii_net != null ? `${formatNumber(envelope.settled_session.institutional_flows.fii_net, 1)} Cr` : "—"}
                  </span>
                </div>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#707987]">DII (CASH)</span>
                <div className="flex gap-2">
                  <span className={`font-bold ${(envelope.settled_session?.institutional_flows?.dii_net ?? 0) >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                    {envelope.settled_session?.institutional_flows?.dii_net != null ? `${formatNumber(envelope.settled_session.institutional_flows.dii_net, 1)} Cr` : "—"}
                  </span>
                </div>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#707987]">NET FLOW</span>
                <div className="flex gap-2">
                  <span className={`font-bold ${(envelope.settled_session?.institutional_flows?.net ?? 0) >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                    {envelope.settled_session?.institutional_flows?.net != null ? `${formatNumber(envelope.settled_session.institutional_flows.net, 1)} Cr` : "—"}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center pt-1 border-t border-[#1C2128] text-[8.5px] text-[#555E6D] mt-0.5">
              <span>(NSE Official Cash Segment)</span>
              <span>Settled Date: {envelope.settled_session?.session_date || "—"}</span>
            </div>
          </div>

          {/* Card 4: Pre-Market Strategic Plan (Opening Scenarios) */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 space-y-1">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 text-[10px]">
              <div className="flex items-center gap-1 font-bold text-[#8B949E] uppercase">
                <Crosshair className="w-3 h-3 text-[#38BDF8]" />
                <span>PRE-MARKET STRATEGIC PLAN</span>
              </div>
              <span className="text-[8.5px] px-1 py-0.2 rounded-[2px] bg-[#161A22] text-[#38BDF8] font-bold border border-[#2B333E]">
                PLAN FIRST
              </span>
            </div>

            <div className="space-y-1 text-[10px]">
              <div className="rounded-[2px] bg-[#00C896]/5 p-1.5 border border-[#00C896]/20">
                <span className="font-bold text-[#00C896] block text-[9.5px]">▲ BULLISH SCENARIO</span>
                <p className="text-[#D1D5DB] text-[10px] mt-0.5 leading-tight">
                  {plan?.bullish_scenario?.trigger || "Sustain above opening reference and break above 15m Opening Range High with breadth expansion."}
                </p>
              </div>

              <div className="rounded-[2px] bg-[#EF4444]/5 p-1.5 border border-[#EF4444]/20">
                <span className="font-bold text-[#EF4444] block text-[9.5px]">▼ BEARISH SCENARIO</span>
                <p className="text-[#D1D5DB] text-[10px] mt-0.5 leading-tight">
                  {plan?.bearish_scenario?.trigger || "Rejection at key resistance and breakdown below 15m Opening Range Low."}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. BOTTOM ROW: 5-Column Connected Grid with Equal Heights */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-1.5 items-stretch">
        {/* Col 1: Market Breadth Expectation */}
        <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
          <div className="border-b border-[#1C2128] pb-1 mb-1.5">
            <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">MARKET BREADTH</span>
            <span className="text-[8.5px] text-[#555E6D]">{envelope.settled_session?.closing_breadth ? "Settled Previous Session" : "Awaiting Stream"}</span>
          </div>

          <div className="space-y-0.5 text-[9.5px] my-auto">
            <div className="flex justify-between">
              <span className="text-[#00C896] font-bold">Advances</span>
              <span className="font-bold text-[#E6E8EB]">{envelope.settled_session?.closing_breadth?.advances ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#EF4444] font-bold">Declines</span>
              <span className="font-bold text-[#E6E8EB]">{envelope.settled_session?.closing_breadth?.declines ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#707987] font-bold">Unchanged</span>
              <span className="font-bold text-[#E6E8EB]">{(envelope.settled_session?.closing_breadth as any)?.unchanged ?? "—"}</span>
            </div>
          </div>

          <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#555E6D]">
            Coverage: NIFTY 50 Universe
          </div>
        </div>

        {/* Col 2: Institutional Flows (Prev Session) */}
        <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
          <div className="border-b border-[#1C2128] pb-1 mb-1">
            <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">INSTITUTIONAL FLOWS</span>
            <span className="text-[8.5px] text-[#555E6D]">{envelope.settled_session?.session_date || "Awaiting Publication"}</span>
          </div>

          <div className="space-y-1 text-[10px] my-auto">
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

        {/* Col 3: Sector Watch */}
        <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
          <div className="border-b border-[#1C2128] pb-1 mb-1">
            <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">SECTOR PARTICIPATION</span>
          </div>

          <div className="text-[9.5px] my-auto text-neutral-400">
            Awaiting market open sector stream.
          </div>

          <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#555E6D]">
            Relative Strength Ranking
          </div>
        </div>

        {/* Col 4: Pre-Market Plan */}
        <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
          <div className="border-b border-[#1C2128] pb-1 mb-1">
            <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">PRE-MARKET PLAN</span>
          </div>

          <div className="space-y-1 text-[9.5px] my-auto">
            {[
              "1. Monitor global cues & overnight market tone",
              "2. Track pre-open auction discovery (09:00-09:15)",
              "3. Confirm opening reference price & gap",
              "4. Map key structural levels & settled VWAP",
              "5. Align with sector participation",
              "6. Execute only on confirmed rule-based setup",
            ].map((text, idx) => (
              <label
                key={idx}
                className="flex items-center gap-1.5 cursor-pointer text-[#C9D1D9] hover:text-[#E6E8EB]"
              >
                <input
                  type="checkbox"
                  checked={Boolean(checkedItems1[idx])}
                  onChange={() => toggleCheck1(idx)}
                  className="accent-[#00C896] w-3 h-3 cursor-pointer"
                />
                <span className={`truncate text-[9.5px] ${checkedItems1[idx] ? "text-[#00C896]" : ""}`}>{text}</span>
              </label>
            ))}
          </div>

          <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#00C896]">
            Plan Verification
          </div>
        </div>

        {/* Col 5: First 15-Minute Checklist */}
        <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
          <div className="border-b border-[#1C2128] pb-1 mb-1">
            <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">FIRST 15-MINUTE CHECKLIST (09:15 - 09:30)</span>
          </div>

          <div className="space-y-1 text-[9.5px] my-auto">
            {[
              "Confirm opening range high & low",
              "Track volume & breadth",
              "Watch VWAP & key pivot levels",
              "Identify opening momentum",
              "Avoid early over-trading",
              "Execute with discipline",
            ].map((text, idx) => (
              <label
                key={idx}
                className="flex items-center gap-1.5 cursor-pointer text-[#8B949E] hover:text-[#E6E8EB]"
              >
                <input
                  type="checkbox"
                  checked={Boolean(checkedItems2[idx])}
                  onChange={() => toggleCheck2(idx)}
                  className="accent-[#38BDF8] w-3 h-3 cursor-pointer"
                />
                <span className={`truncate text-[9.5px] ${checkedItems2[idx] ? "text-[#38BDF8] line-through" : ""}`}>{text}</span>
              </label>
            ))}
          </div>

          <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#707987]">
            Awaiting 09:15 IST
          </div>
        </div>
      </div>

      {/* 4. BOTTOM TRUST FOOTER: Minimal single strip (Zero telemetry clutter!) */}
      <div className="flex flex-wrap items-center justify-between px-3 py-1 rounded-[2px] border border-[#1E232B] bg-[#0E1013] text-[9.5px] text-[#707987]">
        <div className="flex items-center gap-3">
          <span>DATA STATE: <strong className="text-[#38BDF8]">{isReplay ? "REPLAY" : (data_quality === "UNAVAILABLE" ? "AWAITING STREAM" : "LIVE FEED")}</strong></span>
          <span>•</span>
          <span>PREVIOUS SESSION: <strong className={envelope.settled_session ? "text-[#00C896]" : "text-neutral-400"}>{envelope.settled_session ? "AVAILABLE" : "UNAVAILABLE"}</strong></span>
          <span>•</span>
          <span>LAST SETTLED: <strong className="text-neutral-300">{settledDateDisplay}</strong></span>
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
