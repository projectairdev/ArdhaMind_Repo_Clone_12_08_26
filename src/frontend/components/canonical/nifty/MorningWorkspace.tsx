/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Professional NIFTY Morning Workspace (NIFTY -> MORNING).
 * Unifies PRE_MARKET (<09:00 IST) and PRE_OPEN (09:00-09:15 IST) into a single, high-density institutional workstation:
 * - Top Connected Summary Strip
 * - Main Analytical Surface: CanonicalTradingChart (~65% width, ~560px height) + Right Intelligence Stack (~35% width)
 * - Four/Five Connected Supporting Context Cards of Equal Height
 * - Zero Provider Telemetry Cards on Trader Page (Telemetry preserved in Settings -> Diagnostics)
 * - Unambiguous Titles, Explicit Temporal Provenance, and Clear Session Integrity
 */

import React, { useState } from "react";
import { CanonicalFrontendEnvelope } from "../../../types/canonical";
import { CanonicalTradingChart } from "../chart/CanonicalTradingChart";
import {
  Compass,
  Target,
  Globe,
  Crosshair,
  CheckSquare,
  Layers,
  Sunrise,
  Clock,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { formatNumber } from "../../../utils/safeHelpers";
import { useCanonicalState } from "../../../context/CanonicalStateContext";
import { getCanonicalQuote } from "../../../utils/canonicalQuotes";
import { resolveAuthoritativeMarketState } from "../../../utils/canonicalResolvers";
import { NiftyHeader } from "./NiftyHeader";

export function MorningWorkspace({
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
    2: true,
    3: true,
    4: true,
    5: true,
    6: true,
  });

  const toggleCheck = (i: number) => setChecklist((prev) => ({ ...prev, [i]: !prev[i] }));

  const settledDateDisplay = envelope.settled_session?.session_date
    ? new Date(envelope.settled_session.session_date + "T00:00:00").toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }).toUpperCase()
    : "—";

  return (
    <div className="flex flex-col gap-1.5 font-mono text-[#E6E8EB] select-none">
      {/* 1. TOP CONNECTED SUMMARY STRIP: Hero Quote & Connected Settled Metrics */}
      <NiftyHeader envelope={envelope} marketPhase={isPreOpen ? "PRE_OPEN" : "PRE_MARKET"} />

      {/* 2. MAIN ANALYTICAL SURFACE: Chart (65%) + Right Intelligence Stack (35%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-1.5 items-stretch">
        {/* Left Surface: Multi-TF Canonical Trading Chart */}
        <div className="lg:col-span-8 flex flex-col min-h-[480px] lg:min-h-[560px]">
          <CanonicalTradingChart
            candles={m1Candles}
            priceStructure={price_structure}
            height={560}
            sessionDate={session?.active_trading_date || session?.completed_session_date || "—"}
            marketPhase={session?.market_phase || "PRE_MARKET"}
          />
        </div>

        {/* Right Surface: 4-Card Intelligence Stack */}
        <div className="lg:col-span-4 flex flex-col gap-1.5 h-full">
          {/* Card 1: Market Structure Expectations */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 space-y-1">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 text-[10px]">
              <div className="flex items-center gap-1 font-bold text-[#8B949E] uppercase">
                <Compass className="w-3 h-3 text-[#38BDF8]" />
                <span>MARKET STRUCTURE — {isPreOpen ? "PRE-OPEN AUCTION" : "EXPECTATION"}</span>
              </div>
              <span className="text-[8.5px] px-1.5 py-0.2 rounded-[2px] bg-[#00C896]/15 text-[#00C896] font-bold border border-[#00C896]/30">
                {envelope.regime?.regime_type ? String(envelope.regime.regime_type).replace(/_/g, " ") : "RANGE BOUND"}
              </span>
            </div>

            <div className="space-y-1 text-[10.5px]">
              <div className="flex justify-between items-baseline">
                <span className="font-bold text-[#F0F6FC]">
                  {isPreOpen ? "PRE-OPEN AUCTION READ" : "PRE-MARKET ORIENTATION"}
                </span>
                <span className="text-[10px] text-[#707987]">
                  CONFIDENCE: <strong className="text-[#38BDF8]">{envelope.prediction?.confidence_score ?? "—"}%</strong>
                </span>
              </div>

              <p className="text-[10px] text-[#8B949E] leading-relaxed">
                {envelope.settled_session?.close != null
                  ? `Previous session settled at ${formatNumber(envelope.settled_session.close, 2)} with settled range of ${formatNumber(envelope.settled_session.range_points ?? 0, 1)} pts. Awaiting market open auction.`
                  : "Awaiting market session settlement data and live feed initialization."}
              </p>

              <div className="grid grid-cols-2 gap-1 pt-1 border-t border-[#1C2128] text-[9.5px]">
                <div className="rounded bg-[#12151A] p-1 border border-[#20252E]">
                  <span className="text-[8.5px] text-[#707987] block">GAP STATUS</span>
                  <span className="font-bold text-[#00C896]">
                    {price_structure.change != null ? `${price_structure.change >= 0 ? "+" : ""}${formatNumber(price_structure.change, 2)} PTS` : "AWAITING AUCTION"}
                  </span>
                </div>
                <div className="rounded bg-[#12151A] p-1 border border-[#20252E]">
                  <span className="text-[8.5px] text-[#707987] block">REGIME</span>
                  <span className="font-bold text-[#38BDF8]">
                    {envelope.regime?.regime_type ? String(envelope.regime.regime_type).replace(/_/g, " ") : "RANGE BOUND"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Key Levels (Evidence Based) */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 space-y-1">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 text-[10px] text-[#8B949E] font-bold uppercase">
              <div className="flex items-center gap-1">
                <Target className="w-3 h-3 text-[#38BDF8]" />
                <span>KEY LEVELS (EVIDENCE BASED)</span>
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
              <div className="flex justify-between py-0.5 bg-[#F59E0B]/5 px-1 rounded-[2px] border border-[#F59E0B]/20">
                <span className="text-[#F59E0B] font-bold">Reference Pivot / VWAP</span>
                <span className="font-bold text-[#F59E0B]">
                  {price_structure?.vwap != null ? formatNumber(price_structure.vwap, 2) : (envelope.settled_session?.structural_levels?.pivot != null ? formatNumber(envelope.settled_session.structural_levels.pivot, 2) : (envelope.settled_session?.vwap != null ? formatNumber(envelope.settled_session.vwap, 2) : "—"))}
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#00C896] font-bold">Immediate Support (S1)</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_supports?.[0] != null ? formatNumber(price_structure.key_supports[0], 2) : (envelope.settled_session?.structural_levels?.s1 != null ? formatNumber(envelope.settled_session.structural_levels.s1, 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                <span className="text-[#00C896] font-bold">Major Support (S2)</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_supports?.[1] != null ? formatNumber(price_structure.key_supports[1], 2) : (envelope.settled_session?.structural_levels?.s2 != null ? formatNumber(envelope.settled_session.structural_levels.s2, 2) : "—")}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-[#00C896] font-bold">Support 3 (S3)</span>
                <span className="font-bold text-[#E6E8EB]">
                  {price_structure?.key_supports?.[2] != null ? formatNumber(price_structure.key_supports[2], 2) : (envelope.settled_session?.structural_levels?.s3 != null ? formatNumber(envelope.settled_session.structural_levels.s3, 2) : "—")}
                </span>
              </div>
            </div>
          </div>

          {/* Card 3: Morning Plan / Opening Expectation (Consolidated Single Card) */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 space-y-1">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 text-[10px]">
              <div className="flex items-center gap-1 font-bold text-[#8B949E] uppercase">
                <Crosshair className="w-3 h-3 text-[#38BDF8]" />
                <span>MORNING PLAN / OPENING EXPECTATION</span>
              </div>
              <span className="text-[8.5px] px-1 py-0.2 rounded-[2px] bg-[#161A22] text-[#38BDF8] font-bold border border-[#2B333E]">
                PLAN FIRST
              </span>
            </div>

            <div className="space-y-1 text-[10px]">
              <div className="rounded-[2px] bg-[#00C896]/5 p-1.5 border border-[#00C896]/20">
                <span className="font-bold text-[#00C896] block text-[9.5px]">▲ UPSIDE CONDITION</span>
                <p className="text-[#D1D5DB] text-[10px] mt-0.5 leading-tight">
                  {active_product?.morning_plan?.bullish_scenario?.trigger ? `${active_product.morning_plan.bullish_scenario.trigger}. Target: ${active_product.morning_plan.bullish_scenario.target_area || "R1/R2"}.` : "Sustain above opening reference and break above 15m Opening Range High with breadth expansion."}
                </p>
              </div>

              <div className="rounded-[2px] bg-[#EF4444]/5 p-1.5 border border-[#EF4444]/20">
                <span className="font-bold text-[#EF4444] block text-[9.5px]">▼ DOWNSIDE CONDITION</span>
                <p className="text-[#D1D5DB] text-[10px] mt-0.5 leading-tight">
                  {active_product?.morning_plan?.bearish_scenario?.trigger ? `${active_product.morning_plan.bearish_scenario.trigger}. Target: ${active_product.morning_plan.bearish_scenario.target_area || "S1/S2"}.` : "Rejection at key resistance and breakdown below 15m Opening Range Low."}
                </p>
              </div>

              <div className="rounded-[2px] bg-[#F59E0B]/5 p-1 border border-[#F59E0B]/20 text-[9px] text-[#F59E0B]">
                <strong>INVALIDATION:</strong> {active_product?.morning_plan?.bullish_scenario?.invalidation || (envelope.settled_session?.low ? `Loss of ${formatNumber(envelope.settled_session.low, 2)} session low invalidates bullish bias.` : "Break of session opening floor invalidates opening bias.")}
              </div>
            </div>
          </div>

          {/* Card 4: Pre-Market Action Checklist */}
          <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 space-y-1 flex-1">
            <div className="flex items-center justify-between border-b border-[#1C2128] pb-1 text-[10px] text-[#8B949E] font-bold uppercase">
              <div className="flex items-center gap-1">
                <CheckSquare className="w-3 h-3 text-[#38BDF8]" />
                <span>PRE-MARKET ACTION CHECKLIST</span>
              </div>
              <span className="text-[8.5px] px-1 py-0.2 rounded-[2px] bg-[#161A22] text-[#00C896] border border-[#00C896]/30">
                PLANNING
              </span>
            </div>

            <div className="space-y-1 text-[10px] pt-0.5">
              {[
                { label: "Monitor global cues & overnight market sentiment", defaultDone: false },
                { label: "Track pre-open auction discovery (09:00 - 09:15 IST)", defaultDone: false },
                { label: "Confirm opening reference price & gap vs previous close", defaultDone: false },
                { label: "Map 15-minute Opening Range bounds & settled VWAP", defaultDone: false },
                { label: "Evaluate market breadth & institutional participation", defaultDone: false },
                { label: "Execute only on confirmed rule-based setup", defaultDone: false },
              ].map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => toggleCheck(idx)}
                  className="flex items-center gap-1.5 cursor-pointer hover:bg-[#161A22] p-0.5 rounded-[2px] transition-colors"
                >
                  <div className={`w-3.5 h-3.5 rounded-[2px] flex items-center justify-center border text-[9px] ${checklist[idx] ? "bg-[#00C896]/20 border-[#00C896] text-[#00C896]" : "border-[#3A4250] text-transparent"}`}>
                    ✓
                  </div>
                  <span className={`text-[10px] ${checklist[idx] ? "text-[#00C896]" : "text-[#8B949E]"}`}>
                    {item.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 3. CONNECTED CONTEXT ROW: 4/5 Equal Height Connected Panels */}
      {/* 3. CONNECTED CONTEXT ROW: 4/5 Equal Height Connected Panels */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-1.5 items-stretch">
        {/* Col 1: Global Cues — Overnight */}
        {(() => {
          const rawQuotes = (envelope as any).macro?.quotes || (envelope as any).macro_intelligence?.quotes || (envelope as any).global_market_intelligence?.quotes || {};
          const giftQuote = getCanonicalQuote(rawQuotes, "GIFT_NIFTY");
          const dowQuote = getCanonicalQuote(rawQuotes, "DOW_JONES");
          const nasdaqQuote = getCanonicalQuote(rawQuotes, "NASDAQ");
          const nikkeiQuote = getCanonicalQuote(rawQuotes, "NIKKEI_225");
          const hasQuotes = giftQuote.isAvailable || dowQuote.isAvailable || nasdaqQuote.isAvailable || nikkeiQuote.isAvailable;
          const riskOn = ((giftQuote.changePct ?? 0) >= 0 && (dowQuote.changePct ?? 0) >= 0);

          return (
            <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
              <div className="border-b border-[#1C2128] pb-1 mb-1 flex justify-between items-center text-[10px]">
                <span className="font-bold text-[#8B949E] uppercase flex items-center gap-1">
                  <Globe className="w-3 h-3 text-[#38BDF8]" />
                  GLOBAL CUES — OVERNIGHT
                </span>
                {hasQuotes && (
                  <span className={`text-[8.5px] font-bold ${riskOn ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                    {riskOn ? "RISK-ON" : "RISK-OFF / CAUTION"}
                  </span>
                )}
              </div>

              {hasQuotes ? (
                <div className="space-y-0.5 text-[10px] my-auto">
                  <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                    <span className="text-[#707987]">GIFT NIFTY</span>
                    <div className="flex gap-2">
                      <span className="font-bold text-[#E6E8EB]">{giftQuote.value != null ? giftQuote.value.toLocaleString("en-IN", { minimumFractionDigits: 2 }) : "—"}</span>
                      {giftQuote.changePct != null && (
                        <span className={`font-bold ${giftQuote.changePct >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                          {giftQuote.changePct >= 0 ? "+" : ""}{giftQuote.changePct.toFixed(2)}%
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                    <span className="text-[#707987]">DOW FUTURES</span>
                    <div className="flex gap-2">
                      <span className="font-bold text-[#E6E8EB]">{dowQuote.value != null ? dowQuote.value.toLocaleString("en-IN", { minimumFractionDigits: 2 }) : "—"}</span>
                      {dowQuote.changePct != null && (
                        <span className={`font-bold ${dowQuote.changePct >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                          {dowQuote.changePct >= 0 ? "+" : ""}{dowQuote.changePct.toFixed(2)}%
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex justify-between py-0.5 border-b border-[#161A22]">
                    <span className="text-[#707987]">NASDAQ FUTURES</span>
                    <div className="flex gap-2">
                      <span className="font-bold text-[#E6E8EB]">{nasdaqQuote.value != null ? nasdaqQuote.value.toLocaleString("en-IN", { minimumFractionDigits: 2 }) : "—"}</span>
                      {nasdaqQuote.changePct != null && (
                        <span className={`font-bold ${nasdaqQuote.changePct >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                          {nasdaqQuote.changePct >= 0 ? "+" : ""}{nasdaqQuote.changePct.toFixed(2)}%
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex justify-between py-0.5">
                    <span className="text-[#707987]">NIKKEI 225</span>
                    <div className="flex gap-2">
                      <span className="font-bold text-[#E6E8EB]">{nikkeiQuote.value != null ? nikkeiQuote.value.toLocaleString("en-IN", { minimumFractionDigits: 2 }) : "—"}</span>
                      {nikkeiQuote.changePct != null && (
                        <span className={`font-bold ${nikkeiQuote.changePct >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                          {nikkeiQuote.changePct >= 0 ? "+" : ""}{nikkeiQuote.changePct.toFixed(2)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-4 text-center text-neutral-500 font-mono text-[9.5px]">
                  Awaiting Global Offshore Telemetry
                </div>
              )}

              <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#555E6D]">
                Global Markets Alignment
              </div>
            </div>
          );
        })()}

        {/* Col 2: Institutional Flows — Previous Session */}
        {(() => {
          const flows = envelope.settled_session?.institutional_flows || (envelope as any).macro?.institutional_flows || (envelope as any).macro_intelligence?.institutional_flows || null;
          const fiiNet = flows?.fii_cash_net ?? flows?.fii_net ?? flows?.fii_net_cr;
          const diiNet = flows?.dii_cash_net ?? flows?.dii_net ?? flows?.dii_net_cr;
          const netInst = flows?.net_institutional_cr ?? flows?.net_cr ?? ((fiiNet != null && diiNet != null) ? fiiNet + diiNet : null);
          const retailNet = flows?.retail_net_cr ?? flows?.retail_net ?? null;
          const flowDate = flows?.session_date || flows?.date || (envelope.settled_session?.session_date ? settledDateDisplay : null);
          const hasFlows = fiiNet != null || diiNet != null;

          return (
            <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
              <div className="border-b border-[#1C2128] pb-1 mb-1">
                <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">INSTITUTIONAL FLOWS — PREVIOUS SESSION</span>
                <span className="text-[8.5px] text-[#555E6D]">Last Published: {flowDate || "Awaiting Publication"}</span>
              </div>

              {hasFlows ? (
                <div className="space-y-1 text-[10px] my-auto">
                  <div className="flex justify-between">
                    <span className="text-[#8B949E]">FII (Cash)</span>
                    <span className={`font-bold ${fiiNet != null && fiiNet >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                      {fiiNet != null ? `${fiiNet > 0 ? "+" : ""}${formatNumber(fiiNet, 2)} Cr` : "—"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8B949E]">DII (Cash)</span>
                    <span className={`font-bold ${diiNet != null && diiNet >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                      {diiNet != null ? `${diiNet > 0 ? "+" : ""}${formatNumber(diiNet, 2)} Cr` : "—"}
                    </span>
                  </div>
                  <div className="flex justify-between border-t border-[#1C2128] pt-0.5">
                    <span className="text-[#8B949E]">Net Institutional</span>
                    <span className={`font-bold ${netInst != null && netInst >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                      {netInst != null ? `${netInst > 0 ? "+" : ""}${formatNumber(netInst, 2)} Cr` : "—"}
                    </span>
                  </div>
                  {retailNet != null && (
                    <div className="flex justify-between">
                      <span className="text-[#8B949E]">Retail</span>
                      <span className={`font-bold ${retailNet >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                        {retailNet > 0 ? "+" : ""}{formatNumber(retailNet, 2)} Cr
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-4 text-center text-neutral-500 font-mono text-[9.5px]">
                  Awaiting EOD Institutional Publication
                </div>
              )}

              <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#555E6D]">
                Provisional Cash Segment
              </div>
            </div>
          );
        })()}

        {/* Col 3: Sector Leadership — Previous Session */}
        {(() => {
          const sectorBias = breadth?.sector_bias || (envelope as any).settled_session?.sector_performance || {};
          const leaders: Array<any> = Array.isArray(sectorBias?.leaders) ? sectorBias.leaders : (Array.isArray(sectorBias?.gainers) ? sectorBias.gainers : []);
          const laggards: Array<any> = Array.isArray(sectorBias?.laggards) ? sectorBias.laggards : (Array.isArray(sectorBias?.losers) ? sectorBias.losers : []);
          const hasSectors = leaders.length > 0 || laggards.length > 0;

          return (
            <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
              <div className="border-b border-[#1C2128] pb-1 mb-1">
                <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">SECTOR LEADERSHIP — PREVIOUS SESSION</span>
              </div>

              {hasSectors ? (
                <div className="grid grid-cols-2 gap-1 text-[9.5px] my-auto">
                  <div className="space-y-1">
                    <span className="text-[8.5px] text-[#707987] block font-bold">Leaders</span>
                    {leaders.slice(0, 3).map((item, idx) => {
                      const name = typeof item === "string" ? item : (item.name || item.sector || "SECTOR");
                      const pct = typeof item === "object" ? (item.pct ?? item.change_pct ?? item.changePct) : null;
                      return (
                        <div key={idx} className="flex justify-between">
                          <span className="text-[#C9D1D9] truncate">{name}</span>
                          {pct != null && (
                            <span className="font-bold text-[#00C896]">
                              {pct >= 0 ? "+" : ""}{Number(pct).toFixed(2)}%
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  <div className="space-y-1 border-l border-[#1C2128] pl-1">
                    <span className="text-[8.5px] text-[#707987] block font-bold">Laggards</span>
                    {laggards.slice(0, 3).map((item, idx) => {
                      const name = typeof item === "string" ? item : (item.name || item.sector || "SECTOR");
                      const pct = typeof item === "object" ? (item.pct ?? item.change_pct ?? item.changePct) : null;
                      return (
                        <div key={idx} className="flex justify-between">
                          <span className="text-[#C9D1D9] truncate">{name}</span>
                          {pct != null && (
                            <span className="font-bold text-[#EF4444]">
                              {pct >= 0 ? "+" : ""}{Number(pct).toFixed(2)}%
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="py-4 text-center text-neutral-500 font-mono text-[9.5px]">
                  Awaiting Sector Breadth Data
                </div>
              )}

              <div className="pt-1 border-t border-[#1C2128] text-[8.5px] text-[#555E6D]">
                Relative Strength Ranking
              </div>
            </div>
          );
        })()}

        {/* Col 4: Morning Checklist */}
        <div className="rounded-[3px] border border-[#1E232B] bg-[#0E1013] p-2.5 flex flex-col justify-between">
          <div className="border-b border-[#1C2128] pb-1 mb-1">
            <span className="text-[9.5px] font-bold text-[#8B949E] block uppercase">MORNING CHECKLIST</span>
          </div>

          <div className="space-y-1 text-[9.5px] my-auto">
            {[
              "1. Review overnight & global cues",
              "2. Track pre-open auction (09:00-09:15)",
              "3. Note expected/indicative gap",
              "4. Watch opening range (09:15-09:30)",
              "5. Confirm VWAP behavior",
              "6. Confirm breadth & participation",
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
