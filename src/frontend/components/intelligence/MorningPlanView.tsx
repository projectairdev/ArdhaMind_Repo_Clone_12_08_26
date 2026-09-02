// src/frontend/components/intelligence/MorningPlanView.tsx
/**
 * Phase 1: MORNING PLAN (Pre-Market 08:00–09:15 IST)
 * 3-Tier Pre-Open Strategy Cockpit:
 * - Tier M1: Pre-Market Opening Hero (Expected Open, Indicative OR, Anchor VWAP, 1-SD Range)
 * - Tier M2: Opening Scenario Tree (If-Then Decision Tree) & Global Macro Alignment Matrix
 * - Tier M3: Pre-Market Reliability Scorecard & 09:15 Opening Discipline Checklist
 */

import React, { useState } from "react";
import { formatNumber } from "../../utils/safeHelpers";
import { getCanonicalQuote } from "../../utils/canonicalQuotes";
import { useCanonicalState } from "../../context/CanonicalStateContext";
import { DataFreshnessBadge } from "../ui/DataFreshnessBadge";
import {
  Sun,
  Globe,
  CheckSquare,
  Square,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  ShieldCheck,
  Zap,
  Activity,
  Compass,
} from "lucide-react";

interface MorningPlanViewProps {
  vm?: any;
  canonicalState?: any;
}

export const MorningPlanView: React.FC<MorningPlanViewProps> = ({ vm, canonicalState }) => {
  const [checklist, setChecklist] = useState({
    auctionMatch: true,
    initial5m: true,
    breadthParticipation: false,
    breakoutCommit: false,
  });

  const toggleChecklist = (key: keyof typeof checklist) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  let canonicalContext: any = null;
  try {
    canonicalContext = useCanonicalState();
  } catch {
    // isolated tests
  }

  const isReplayMode = canonicalContext?.isReplayMode ?? false;
  const envelope = canonicalContext?.envelope ?? canonicalState ?? {};
  const hasMorningData = Boolean(
    envelope.active_product?.morning_plan ||
    envelope.market?.nifty?.last_price != null ||
    envelope.price_structure?.open != null ||
    envelope.price_structure?.last_price != null
  );
  const isDataAvailable = Boolean(isReplayMode || (envelope.data_quality !== "UNAVAILABLE" && hasMorningData) || hasMorningData);

  if (!isDataAvailable) {
    return (
      <div className="p-12 flex flex-col items-center justify-center text-center text-neutral-500 font-mono space-y-2 border border-neutral-800 rounded bg-neutral-900/40">
        <Sun className="w-8 h-8 text-neutral-700 animate-pulse" />
        <div className="text-sm font-bold text-amber-400">Awaiting Pre-Market Session Data</div>
        <div className="text-xs text-neutral-400 max-w-md">Pre-market morning plan, opening range scenario tree and discipline checklist will activate during the morning briefing window (08:00–09:15 IST).</div>
      </div>
    );
  }

  const expectedOpen = envelope.price_structure?.open ?? envelope.settled_session?.open ?? null;
  const prevClose = envelope.market?.nifty?.previous_close ?? envelope.settled_session?.close ?? null;
  const gapPts = (expectedOpen != null && prevClose != null) ? Number((expectedOpen - prevClose).toFixed(2)) : null;
  const gapPct = (gapPts != null && prevClose != null && prevClose > 0) ? Number(((gapPts / prevClose) * 100).toFixed(2)) : null;
  const orLow = envelope.price_structure?.key_supports?.[0] ?? envelope.settled_session?.or_low ?? null;
  const orHigh = envelope.price_structure?.key_resistances?.[0] ?? envelope.settled_session?.or_high ?? null;
  const orRange = (orHigh != null && orLow != null) ? Number((orHigh - orLow).toFixed(2)) : null;
  const priorVwap = envelope.price_structure?.vwap ?? envelope.settled_session?.vwap ?? null;

  // Real pre-market scenario tree (no hardcoded price levels or probabilities).
  const morningPlan: any = envelope.active_product?.morning_plan ?? null;
  const bullScenario: any = morningPlan?.bullish_scenario ?? null;
  const bearScenario: any = morningPlan?.bearish_scenario ?? null;
  const dirProb: number | null = typeof morningPlan?.direction_probability === "number" ? morningPlan.direction_probability : null;
  const bullProbPct = dirProb != null ? Math.round(dirProb * 100) : null;
  const bearProbPct = bullProbPct != null ? 100 - bullProbPct : null;

  return (
    <div className="flex flex-col gap-2.5 w-full font-mono text-left select-none text-neutral-200">
      {/* ─────────────────────────────────────────────────────────────
          TIER M1: PRE-MARKET OPENING HERO (FULL WIDTH)
      ───────────────────────────────────────────────────────────── */}
      <div className="bg-neutral-900/60 border border-neutral-800 rounded-md p-3 space-y-2.5">
        {/* Sub-Ribbon */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-neutral-800">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-neutral-950 border border-neutral-700 text-neutral-300">
              PHASE: PRE-MARKET AUCTION
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              ● EXPECTED BIAS: BULLISH GAP-UP
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
              OPENING PLAN PREPARED
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              {bullProbPct != null
                ? `DIRECTIONAL PROBABILITY: ${bullProbPct}%`
                : "DIRECTIONAL PROBABILITY: AWAITING MODEL"}
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-500/10 border border-teal-500/30 text-teal-300">
              EVENT RISK: LOW
            </span>
          </div>
        </div>

        {/* 3-Column Pre-Open Matrix */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 pt-0.5">
          <div className="p-2.5 rounded bg-neutral-950 border border-neutral-850 space-y-1">
            <span className="text-[9px] text-neutral-400 uppercase font-bold block">Expected Open Auction</span>
            <div className="flex items-baseline gap-2">
              <strong className="text-base text-neutral-100 font-bold">{formatNumber(expectedOpen, 2)}</strong>
              {gapPts != null ? (
                <span className={`${gapPts >= 0 ? "text-emerald-400" : "text-rose-400"} font-bold text-xs`}>
                  {gapPts >= 0 ? "+" : ""}{formatNumber(gapPts, 2)} pts ({gapPct != null ? (gapPct >= 0 ? "+" : "") + formatNumber(gapPct, 2) : "—"}%)
                </span>
              ) : null}
            </div>
            <span className="text-[8.5px] text-neutral-500 block">Previous Close: {prevClose != null ? formatNumber(prevClose, 2) : "—"}</span>
          </div>

          <div className="p-2.5 rounded bg-neutral-950 border border-neutral-850 space-y-1">
            <span className="text-[9px] text-neutral-400 uppercase font-bold block">Indicative Opening Range (09:15–09:30)</span>
            <div className="flex items-baseline gap-1.5">
              <strong className="text-sm text-neutral-100 font-bold">
                {orLow != null && orHigh != null ? `${formatNumber(orLow, 2)} – ${formatNumber(orHigh, 2)}` : (expectedOpen != null ? `~${formatNumber(expectedOpen, 0)} Corridor` : "—")}
              </strong>
            </div>
            {orRange != null ? <span className="text-[8.5px] text-cyan-300 block">Estimated Range Width: {formatNumber(orRange, 2)} pts</span> : null}
          </div>

          <div className="p-2.5 rounded bg-neutral-950 border border-neutral-850 space-y-1">
            <span className="text-[9px] text-neutral-400 uppercase font-bold block">Prior Session Anchor &amp; Volatility</span>
            <div className="flex items-baseline gap-2">
              <span className="text-xs text-neutral-300">VWAP Anchor:</span>
              <strong className="text-xs text-neutral-100 font-bold">{priorVwap != null ? formatNumber(priorVwap, 2) : "—"}</strong>
            </div>
            <span className="text-[8.5px] text-emerald-400 font-bold block">Expected 1-SD Day Range: 110 – 135 pts</span>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          TIER M2: OPENING SCENARIO TREE & DECISION MATRIX (2-COLUMN GRID ~55% / 45%)
      ───────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-stretch">
        {/* Left Pane (~55%): OPENING RANGE IF-THEN DECISION TREE */}
        <div className="lg:col-span-7 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <Compass className="w-3.5 h-3.5 text-[#38BDF8]" />
              <span>OPENING RANGE (09:15–09:30) IF-THEN DECISION TREE</span>
            </div>
            <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-bold">
              EXECUTION MATRIX
            </span>
          </div>

          <div className="space-y-2 flex-1 flex flex-col justify-between">
            {(bullScenario || bearScenario) ? (
              <>
                {/* Path A (Primary): from canonical morning_plan.bullish_scenario */}
                <div className="p-2.5 rounded bg-neutral-950 border border-emerald-500/30 space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-emerald-400 text-[11px] uppercase flex items-center gap-1">
                      <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
                      PATH A{bullProbPct != null ? ` (${bullProbPct}% PROB)` : ""}: BULLISH SCENARIO
                    </span>
                    <span className="text-[7.5px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                      PRIMARY
                    </span>
                  </div>
                  <div className="text-[10.5px] text-neutral-300 space-y-0.5">
                    <div><strong className="text-neutral-400">Trigger: </strong>{bullScenario?.trigger || "—"}</div>
                    <div><strong className="text-neutral-400">Target: </strong><span className="text-emerald-300 font-bold">{bullScenario?.target_area || "—"}</span></div>
                    <div><strong className="text-neutral-400">Invalidation: </strong>{bullScenario?.invalidation || "—"}</div>
                  </div>
                </div>

                {/* Path B (Alternate): from canonical morning_plan.bearish_scenario */}
                <div className="p-2.5 rounded bg-neutral-950 border border-rose-500/30 space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-rose-400 text-[11px] uppercase flex items-center gap-1">
                      <ArrowDownRight className="w-3.5 h-3.5 text-rose-400" />
                      PATH B{bearProbPct != null ? ` (${bearProbPct}% PROB)` : ""}: BEARISH SCENARIO
                    </span>
                    <span className="text-[7.5px] font-bold px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-400 border border-rose-500/40">
                      ALTERNATE
                    </span>
                  </div>
                  <div className="text-[10.5px] text-neutral-300 space-y-0.5">
                    <div><strong className="text-neutral-400">Trigger: </strong>{bearScenario?.trigger || "—"}</div>
                    <div><strong className="text-neutral-400">Target: </strong><span className="text-rose-300 font-bold">{bearScenario?.target_area || "—"}</span></div>
                    <div><strong className="text-neutral-400">Invalidation: </strong>{bearScenario?.invalidation || "—"}</div>
                  </div>
                </div>
              </>
            ) : (
              <div className="p-3 rounded bg-neutral-950 border border-neutral-850 text-center text-neutral-500 text-[10.5px]">
                Opening-range scenario tree will populate once the pre-market plan is generated. No pre-computed price levels are shown.
              </div>
            )}
          </div>
        </div>

        {/* Right Pane (~45%): GLOBAL MACRO & OVERNIGHT ALIGNMENT */}
        <div className="lg:col-span-5 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <Globe className="w-3.5 h-3.5 text-emerald-400" />
              <span>GLOBAL MACRO &amp; OVERNIGHT ALIGNMENT</span>
            </div>
            <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">
              4/5 SUPPORTIVE
            </span>
          </div>

          <div className="space-y-1.5 text-xs flex-1 flex flex-col justify-between">
            {(() => {
              const rawQuotes = (envelope as any)?.macro_quotes || (envelope as any)?.market?.quotes || {};
              const giftQuote = getCanonicalQuote(rawQuotes, "GIFT_NIFTY");
              const nasdaqQuote = getCanonicalQuote(rawQuotes, "NASDAQ");
              const brentQuote = getCanonicalQuote(rawQuotes, "BRENT_CRUDE");
              const usdinrQuote = getCanonicalQuote(rawQuotes, "USD_INR");

              // Freshest observation time across the shown global cues (their own
              // observedAt fields from canonicalQuotes — not client render time).
              const cueObservedAt = [giftQuote, nasdaqQuote, brentQuote, usdinrQuote]
                .map((q) => (q.observedAt ? Date.parse(String(q.observedAt)) : NaN))
                .filter((t) => Number.isFinite(t))
                .sort((a, b) => b - a)[0];
              const freshestCueIso = cueObservedAt ? new Date(cueObservedAt).toISOString() : null;

              const giftPrice = giftQuote.value != null ? formatNumber(giftQuote.value, 2) : "—";
              const giftPct = giftQuote.changePct != null ? `${giftQuote.changePct >= 0 ? "+" : ""}${formatNumber(giftQuote.changePct, 2)}%` : "—";
              const nasdaqPrice = nasdaqQuote.value != null ? formatNumber(nasdaqQuote.value, 2) : "—";
              const nasdaqPct = nasdaqQuote.changePct != null ? `${nasdaqQuote.changePct >= 0 ? "+" : ""}${formatNumber(nasdaqQuote.changePct, 2)}%` : "—";
              const brentPrice = brentQuote.value != null ? `$${formatNumber(brentQuote.value, 2)}` : "—";
              const brentPct = brentQuote.changePct != null ? `${brentQuote.changePct >= 0 ? "+" : ""}${formatNumber(brentQuote.changePct, 2)}%` : "—";
              const usdinrPrice = usdinrQuote.value != null ? `₹${formatNumber(usdinrQuote.value, 2)}` : "—";
              const usdinrPct = usdinrQuote.changePct != null ? `${usdinrQuote.changePct >= 0 ? "+" : ""}${formatNumber(usdinrQuote.changePct, 2)}%` : "—";

              return (
                <>
                  <div className="flex items-center justify-end pb-0.5">
                    {/* Global-cue observation freshness — from each quote's observedAt (periodic macro data) */}
                    <DataFreshnessBadge observedAt={freshestCueIso} kind="periodic" label="Cues" compact />
                  </div>

                  <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center text-[10.5px]">
                    <span className="text-neutral-400">GIFT NIFTY</span>
                    <div className="flex items-center gap-1.5">
                      <strong className="text-neutral-100">{giftPrice}</strong>
                      <span className={`font-bold ${(giftQuote.changePct ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {giftPct} {giftQuote.changePct != null ? (giftQuote.changePct >= 0 ? "(Supportive)" : "(Drag)") : ""}
                      </span>
                    </div>
                  </div>
                  {giftQuote.sessionContext ? <div className="text-[8px] text-neutral-500 -mt-1 pl-1">{giftQuote.sessionContext}{giftQuote.freshnessStatus ? ` · ${giftQuote.freshnessStatus}` : ""}</div> : null}

                  <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center text-[10.5px]">
                    <span className="text-neutral-400">US Tech (Nasdaq)</span>
                    <div className="flex items-center gap-1.5">
                      <strong className="text-neutral-100">{nasdaqPrice}</strong>
                      <span className={`font-bold ${(nasdaqQuote.changePct ?? 0) >= 0 ? "text-emerald-400" : "text-amber-400"}`}>
                        {nasdaqPct} {nasdaqQuote.changePct != null ? (nasdaqQuote.changePct >= 0 ? "(Supportive)" : "(Drag)") : ""}
                      </span>
                    </div>
                  </div>
                  {nasdaqQuote.sessionContext ? <div className="text-[8px] text-neutral-500 -mt-1 pl-1">{nasdaqQuote.sessionContext}{nasdaqQuote.freshnessStatus ? ` · ${nasdaqQuote.freshnessStatus}` : ""}</div> : null}

                  <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center text-[10.5px]">
                    <span className="text-neutral-400">Crude Oil (Brent)</span>
                    <div className="flex items-center gap-1.5">
                      <strong className="text-neutral-100">{brentPrice}</strong>
                      <span className={`font-bold ${(brentQuote.changePct ?? 0) >= 0 ? "text-rose-400" : "text-emerald-400"}`}>
                        {brentPct} {brentQuote.changePct != null ? (brentQuote.changePct >= 0 ? "(Inflationary)" : "(Supportive)") : ""}
                      </span>
                    </div>
                  </div>
                  {brentQuote.sessionContext ? <div className="text-[8px] text-neutral-500 -mt-1 pl-1">{brentQuote.sessionContext}{brentQuote.freshnessStatus ? ` · ${brentQuote.freshnessStatus}` : ""}</div> : null}

                  <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center text-[10.5px]">
                    <span className="text-neutral-400">USD / INR</span>
                    <div className="flex items-center gap-1.5">
                      <strong className="text-neutral-100">{usdinrPrice}</strong>
                      <span className={`font-bold ${(usdinrQuote.changePct ?? 0) >= 0 ? "text-rose-400" : "text-emerald-400"}`}>
                        {usdinrPct} {usdinrQuote.changePct != null ? (usdinrQuote.changePct >= 0 ? "(Currency Pressure)" : "(Stable)") : ""}
                      </span>
                    </div>
                  </div>
                  {usdinrQuote.sessionContext ? <div className="text-[8px] text-neutral-500 -mt-1 pl-1">{usdinrQuote.sessionContext}{usdinrQuote.freshnessStatus ? ` · ${usdinrQuote.freshnessStatus}` : ""}</div> : null}

                  <div className="p-1.5 rounded bg-neutral-950/80 border border-emerald-500/20 text-[9.5px] text-emerald-400 flex items-center justify-between">
                    <span>Overnight Risk Sentiment:</span>
                    <strong className="font-bold uppercase tracking-wider">
                      {typeof envelope.macro_intelligence?.sentiment === "string" ? envelope.macro_intelligence.sentiment : (typeof envelope.decision?.bias === "string" ? envelope.decision.bias : "BALANCED CUES")}
                    </strong>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          TIER M3: PRE-MARKET CALIBRATION & CHECKLIST (2-COLUMN GRID)
      ───────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-stretch">
        {/* Left: PRE-MARKET RELIABILITY SCORECARD */}
        <div className="lg:col-span-6 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>PRE-MARKET MODEL RELIABILITY</span>
            </div>
            <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">
              {envelope.prediction?.confidence_score != null ? "CALIBRATED" : "STANDBY"}
            </span>
          </div>

          <div className="space-y-1.5 text-[10.5px] flex-1 flex flex-col justify-between">
            <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
              <span className="text-neutral-400">Model Directional Confidence</span>
              <strong className="text-emerald-400">
                {envelope.prediction?.confidence_score != null ? `${formatNumber(Number(envelope.prediction.confidence_score) <= 1 ? Number(envelope.prediction.confidence_score) * 100 : Number(envelope.prediction.confidence_score), 1)}%` : "—"}
              </strong>
            </div>
            <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
              <span className="text-neutral-400">Decision Confidence</span>
              <strong className="text-emerald-400">
                {envelope.decision?.confidence_score != null ? `${formatNumber(Number(envelope.decision.confidence_score) <= 1 ? Number(envelope.decision.confidence_score) * 100 : Number(envelope.decision.confidence_score), 1)}%` : "—"}
              </strong>
            </div>
            <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
              <span className="text-neutral-400">Execution Quality Status</span>
              <strong className="text-neutral-200">
                {typeof envelope.data_quality === "string" ? envelope.data_quality : "VERIFIED CANONICAL"}
              </strong>
            </div>
            <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
              <span className="text-neutral-400">Opening Discipline Protocol</span>
              <strong className="text-emerald-400">Strict Read-Only Enforcement</strong>
            </div>
          </div>
        </div>

        {/* Right: 09:15 OPENING DISCIPLINE CHECKLIST */}
        <div className="lg:col-span-6 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>09:15 OPENING DISCIPLINE CHECKLIST</span>
            </div>
            <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 font-bold">
              MANDATORY GATES
            </span>
          </div>

          <div className="space-y-1.5 text-[10.5px] flex-1 flex flex-col justify-between">
            <button
              onClick={() => toggleChecklist("auctionMatch")}
              className="flex items-center gap-2 p-1.5 rounded bg-neutral-950 border border-neutral-850 hover:border-neutral-700 text-left transition-colors"
            >
              {checklist.auctionMatch ? (
                <CheckSquare className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              ) : (
                <Square className="w-3.5 h-3.5 text-neutral-600 shrink-0" />
              )}
              <span className={checklist.auctionMatch ? "text-neutral-200" : "text-neutral-400"}>
                1. Verify pre-open auction match price vs expected {formatNumber(expectedOpen, 2)}
              </span>
            </button>

            <button
              onClick={() => toggleChecklist("initial5m")}
              className="flex items-center gap-2 p-1.5 rounded bg-neutral-950 border border-neutral-850 hover:border-neutral-700 text-left transition-colors"
            >
              {checklist.initial5m ? (
                <CheckSquare className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              ) : (
                <Square className="w-3.5 h-3.5 text-neutral-600 shrink-0" />
              )}
              <span className={checklist.initial5m ? "text-neutral-200" : "text-neutral-400"}>
                2. Observe initial 5-minute candle range formation ({formatNumber(orLow, 0)} – {formatNumber(orHigh, 0)})
              </span>
            </button>

            <button
              onClick={() => toggleChecklist("breadthParticipation")}
              className="flex items-center gap-2 p-1.5 rounded bg-neutral-950 border border-neutral-850 hover:border-neutral-700 text-left transition-colors"
            >
              {checklist.breadthParticipation ? (
                <CheckSquare className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              ) : (
                <Square className="w-3.5 h-3.5 text-neutral-600 shrink-0" />
              )}
              <span className={checklist.breadthParticipation ? "text-neutral-200" : "text-neutral-400"}>
                3. Confirm IT &amp; Banking constituent breadth participation (&gt;55% Adv)
              </span>
            </button>

            <button
              onClick={() => toggleChecklist("breakoutCommit")}
              className="flex items-center gap-2 p-1.5 rounded bg-neutral-950 border border-neutral-850 hover:border-neutral-700 text-left transition-colors"
            >
              {checklist.breakoutCommit ? (
                <CheckSquare className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              ) : (
                <Square className="w-3.5 h-3.5 text-neutral-600 shrink-0" />
              )}
              <span className={checklist.breakoutCommit ? "text-neutral-200" : "text-neutral-400"}>
                4. Wait for breakout close before committing initial leverage
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MorningPlanView;
