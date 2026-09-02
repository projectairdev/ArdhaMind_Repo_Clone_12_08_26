// src/frontend/components/intelligence/TomorrowPlanView.tsx
/**
 * Phase 3: TOMORROW PLAN (Post-Market 15:30+ IST)
 * Post-Market Debrief & Multi-Session Carry-Forward Cockpit:
 * - Tier T1: Session Post-Mortem & Settlement Hero (Final Tape Metrics, Range, ATR Utilization)
 * - Tier T2: Prediction Accuracy Audit & Diagnostic Breakdown (What Worked vs What Failed)
 * - Tier T3: Next Session Carry-Forward Roadmap & Multi-Session Playbook
 */

import React from "react";
import { formatNumber } from "../../utils/safeHelpers";
import { useCanonicalState } from "../../context/CanonicalStateContext";
import { resolveAuthoritativeMarketState } from "../../utils/canonicalResolvers";
import { ATR_FALLBACK } from "../../constants/marketFallbacks";
import {
  Moon,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ShieldCheck,
  TrendingUp,
  Target,
  ArrowUpRight,
  Sparkles,
} from "lucide-react";

interface TomorrowPlanViewProps {
  vm?: any;
  canonicalState?: any;
}

export const TomorrowPlanView: React.FC<TomorrowPlanViewProps> = ({ vm, canonicalState }) => {
  let canonicalContext: any = null;
  try {
    canonicalContext = useCanonicalState();
  } catch {
    // isolated tests
  }

  const isReplayMode = canonicalContext?.isReplayMode ?? false;
  const envelope = canonicalContext?.envelope ?? canonicalState ?? {};
  const hasSettledData = Boolean(
    envelope.active_product?.tomorrow_plan ||
    envelope.settled_session?.close != null ||
    envelope.market?.nifty?.last_price != null ||
    envelope.price_structure?.last_price != null
  );
  const isDataAvailable = Boolean(isReplayMode || (envelope.data_quality !== "UNAVAILABLE" && hasSettledData) || hasSettledData);

  if (!isDataAvailable) {
    return (
      <div className="p-12 flex flex-col items-center justify-center text-center text-neutral-500 font-mono space-y-2 border border-neutral-800 rounded bg-neutral-900/40">
        <Moon className="w-8 h-8 text-neutral-700 animate-pulse" />
        <div className="text-sm font-bold text-amber-400">Awaiting Completed Session Settlement</div>
        <div className="text-xs text-neutral-400 max-w-md">Post-market debrief, final settlement analytics and carry-forward blueprint will generate after the market close (15:30 IST).</div>
      </div>
    );
  }

  const authState = resolveAuthoritativeMarketState(envelope);
  const settlement = authState.spot ?? envelope?.market?.nifty?.last_price ?? envelope?.price_structure?.last_price ?? envelope?.settled_session?.close ?? null;
  const prevClose = authState.prevClose ?? envelope?.market?.nifty?.previous_close ?? envelope?.settled_session?.previous_close ?? null;
  const changePts = (settlement != null && prevClose != null) ? Number((settlement - prevClose).toFixed(2)) : (authState.change ?? null);
  const changePct = (changePts != null && prevClose != null && prevClose > 0) ? Number(((changePts / prevClose) * 100).toFixed(2)) : (authState.changePct ?? null);
  const sessionLow = envelope?.price_structure?.low ?? authState.dayLow ?? envelope?.market?.nifty?.low ?? envelope?.settled_session?.low ?? null;
  const sessionHigh = envelope?.price_structure?.high ?? authState.dayHigh ?? envelope?.market?.nifty?.high ?? envelope?.settled_session?.high ?? null;
  const sessionRange = (sessionHigh != null && sessionLow != null) ? Number((sessionHigh - sessionLow).toFixed(2)) : null;
  const rawExpectedAtr = envelope?.price_structure?.atr_14 ?? envelope?.settled_session?.atr_14 ?? (envelope.active_product?.tomorrow_plan?.session_summary?.atr) ?? ATR_FALLBACK;
  const expectedAtr = rawExpectedAtr != null && Number(rawExpectedAtr) >= 20 ? Number(rawExpectedAtr) : ATR_FALLBACK;
  const priorVwap = envelope?.price_structure?.vwap ?? authState.vwap ?? envelope?.settled_session?.vwap ?? null;

  // Real post-market prediction audit data (no canned commentary / calibration score).
  const tomorrowPlan: any = envelope.active_product?.tomorrow_plan ?? null;
  const predictionOutcome: any = tomorrowPlan?.prediction_outcome ?? null;
  const signalsWorked: string[] = Array.isArray(tomorrowPlan?.signals_worked) ? tomorrowPlan.signals_worked : [];
  const signalsFailed: string[] = Array.isArray(tomorrowPlan?.signals_failed) ? tomorrowPlan.signals_failed : [];

  // Next-session carry-forward levels — real values only (no hardcoded pivots).
  const nextResistances: number[] = Array.isArray(tomorrowPlan?.key_levels_next_session?.resistances)
    ? tomorrowPlan.key_levels_next_session.resistances.filter((n: any) => typeof n === "number" && Number.isFinite(n))
    : [];
  const nextSupports: number[] = Array.isArray(tomorrowPlan?.key_levels_next_session?.supports)
    ? tomorrowPlan.key_levels_next_session.supports.filter((n: any) => typeof n === "number" && Number.isFinite(n))
    : [];
  const nextBias: string | null = typeof tomorrowPlan?.preliminary_next_bias === "string" ? tomorrowPlan.preliminary_next_bias : null;
  const breakoutPivot: number | null = nextResistances[0] ?? null;
  const bedrockSupport: number | null = nextSupports[nextSupports.length - 1] ?? nextSupports[0] ?? null;

  return (
    <div className="flex flex-col gap-2.5 w-full font-mono text-left select-none text-neutral-200">
      {/* ─────────────────────────────────────────────────────────────
          TIER T1: SESSION POST-MORTEM & SETTLEMENT HERO (FULL WIDTH)
      ───────────────────────────────────────────────────────────── */}
      <div className="bg-neutral-900/60 border border-neutral-800 rounded-md p-3 space-y-2.5">
        {/* Header Ribbon */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-neutral-800">
          <div className="flex items-center gap-2">
            <h2 className="text-xs font-bold text-neutral-100 uppercase tracking-wide flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-[#818CF8]" />
              <span>SESSION DEBRIEF &amp; NEXT-DAY STRATEGIC BLUEPRINT</span>
            </h2>
            <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-neutral-950 border border-neutral-700 text-neutral-300">
              SETTLED {authState.sessionDate || "—"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              ● PRELIMINARY BIAS: {typeof envelope.decision?.bias === "string" ? envelope.decision.bias : "CARRY-FORWARD"}
            </span>
          </div>
        </div>

        {/* Final Tape Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 pt-0.5">
          <div className="p-2.5 rounded bg-neutral-950 border border-neutral-850 space-y-0.5">
            <span className="text-[9px] text-neutral-500 uppercase block">Official Settlement</span>
            <div className="flex items-baseline gap-1.5">
              <strong className="text-base text-neutral-100 font-bold">{formatNumber(settlement, 2)}</strong>
              {changePts != null ? (
                <span className={`${changePts >= 0 ? "text-emerald-400" : "text-rose-400"} font-bold text-xs`}>
                  {changePts >= 0 ? "+" : ""}{formatNumber(changePts, 2)} ({changePct != null ? (changePct >= 0 ? "+" : "") + formatNumber(changePct, 2) : "—"}%)
                </span>
              ) : null}
            </div>
            <span className="text-[8px] text-neutral-500">
              {priorVwap != null ? `${settlement != null && settlement >= priorVwap ? "Above" : "Below"} Anchor VWAP ${formatNumber(priorVwap, 2)}` : "VWAP unavailable"}
            </span>
          </div>

          <div className="p-2.5 rounded bg-neutral-950 border border-neutral-850 space-y-0.5">
            <span className="text-[9px] text-neutral-500 uppercase block">Session Price Extremes</span>
            <strong className="text-sm text-neutral-100 font-bold block">
              {sessionLow != null && sessionHigh != null ? `${formatNumber(sessionLow, 2)} ── ${formatNumber(sessionHigh, 2)}` : (settlement != null ? `~${formatNumber(settlement, 2)}` : "Unavailable")}
            </strong>
            {sessionRange != null ? <span className="text-[8px] text-cyan-300">Total Range: {formatNumber(sessionRange, 2)} pts</span> : null}
          </div>

          <div className="p-2.5 rounded bg-neutral-950 border border-neutral-850 space-y-0.5">
            <span className="text-[9px] text-neutral-500 uppercase block">Daily ATR Utilization</span>
            <div className="flex items-baseline gap-1.5">
              <strong className="text-sm text-emerald-400 font-bold">
                {sessionRange != null && expectedAtr != null ? `${((sessionRange / expectedAtr) * 100).toFixed(1)}% Consumed` : "100.0% Consumed"}
              </strong>
            </div>
            <span className="text-[8px] text-neutral-400">
              {sessionRange != null ? `${formatNumber(sessionRange, 2)} pts vs ` : ""}{expectedAtr != null ? `${formatNumber(expectedAtr, 2)} Expected` : "Historical ATR"}
            </span>
          </div>

          <div className="p-2.5 rounded bg-neutral-950 border border-neutral-850 space-y-0.5">
            <span className="text-[9px] text-neutral-500 uppercase block">Tomorrow Setup Posture</span>
            <div className="flex items-baseline gap-1.5">
              <strong className="text-sm text-neutral-100 font-bold">
                {nextBias ? `${nextBias} CARRY-FORWARD` : "Awaiting Next-Session Plan"}
              </strong>
            </div>
            <span className="text-[8px] text-emerald-400 font-bold">
              {nextResistances.length > 0
                ? `Resistance Zone: ${nextResistances.slice(0, 2).map((r) => formatNumber(r, 2)).join(" – ")}`
                : "Carry-forward levels pending"}
            </span>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          TIER T2: PREDICTION ACCURACY AUDIT & DIAGNOSTIC POST-MORTEM (2-COLUMN GRID)
      ───────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-stretch">
        {/* Left Pane (~50%): PREDICTION OUTCOME & AUDIT SCORECARD */}
        <div className="lg:col-span-6 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>PREDICTION OUTCOME &amp; AUDIT SCORECARD</span>
            </div>
            <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-neutral-800 text-neutral-400 border border-neutral-700 font-bold">
              Insufficient Track Record (n=1)
            </span>
          </div>

          <div className="space-y-1.5 text-[10.5px] flex-1 flex flex-col justify-between">
            {predictionOutcome ? (
              <>
                <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
                  <span className="text-neutral-400">Directional Forecast</span>
                  <strong className={predictionOutcome.direction_accurate ? "text-emerald-400" : "text-rose-400"}>
                    {String(predictionOutcome.predicted_bias ?? "—")} vs {String(predictionOutcome.actual_bias ?? "—")} ── {predictionOutcome.direction_accurate ? "HIT" : "MISS"}
                  </strong>
                </div>
                <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
                  <span className="text-neutral-400">Range Magnitude Accuracy</span>
                  <strong className="text-neutral-100">
                    {predictionOutcome.actual_range_points != null && predictionOutcome.expected_range_points != null
                      ? `${formatNumber(predictionOutcome.actual_range_points, 2)} pts actual vs ${formatNumber(predictionOutcome.expected_range_points, 2)} pts expected`
                      : "—"}
                  </strong>
                </div>
                <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
                  <span className="text-neutral-400">Magnitude Bucket</span>
                  <strong className="text-neutral-100">{predictionOutcome.magnitude_bucket_hit ?? "—"}</strong>
                </div>
                <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
                  <span className="text-neutral-400">Track Record</span>
                  <strong className="text-neutral-100 text-[10px]">
                    {predictionOutcome.sample_size != null ? `n=${predictionOutcome.sample_size} session${predictionOutcome.sample_size === 1 ? "" : "s"}` : "—"}
                  </strong>
                </div>
              </>
            ) : (
              <div className="p-3 rounded bg-neutral-950 border border-neutral-850 text-center text-neutral-500">
                No prediction outcome has been recorded for this session yet.
              </div>
            )}
          </div>
        </div>

        {/* Right Pane (~50%): WHAT WORKED VS WHAT FAILED */}
        <div className="lg:col-span-6 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <Target className="w-3.5 h-3.5 text-[#38BDF8]" />
              <span>WHAT WORKED VS WHAT FAILED (DIAGNOSTIC)</span>
            </div>
            <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-bold">
              SESSION POST-MORTEM
            </span>
          </div>

          <div className="space-y-1.5 text-[10px] flex-1 flex flex-col justify-between">
            <div className="p-1.5 rounded bg-neutral-950 border border-emerald-500/20 space-y-0.5">
              <span className="text-[8.5px] font-bold text-emerald-400 uppercase block">Signals That Functioned Correctly</span>
              {signalsWorked.length > 0 ? (
                signalsWorked.map((s, i) => (
                  <div key={i} className="text-neutral-300 leading-tight">• {s}</div>
                ))
              ) : (
                <div className="text-neutral-500 leading-tight">No signal diagnostics recorded for this session.</div>
              )}
            </div>

            <div className="p-1.5 rounded bg-neutral-950 border border-amber-500/20 space-y-0.5">
              <span className="text-[8.5px] font-bold text-amber-400 uppercase block">Friction &amp; Key Observations</span>
              {signalsFailed.length > 0 ? (
                signalsFailed.map((s, i) => (
                  <div key={i} className="text-neutral-300 leading-tight">• {s}</div>
                ))
              ) : (
                <div className="text-neutral-500 leading-tight">No friction diagnostics recorded for this session.</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          TIER T3: NEXT SESSION CARRY-FORWARD ROADMAP & SWING PLAYBOOK (2-COLUMN GRID)
      ───────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-stretch">
        {/* Left Pane (~50%): KEY CARRY-FORWARD REFERENCE PIVOTS */}
        <div className="lg:col-span-6 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <Layers className="w-3.5 h-3.5 text-[#38BDF8]" />
              <span>KEY CARRY-FORWARD REFERENCE PIVOTS</span>
            </div>
            <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-bold">
              NEXT SESSION MAP
            </span>
          </div>

          <div className="space-y-1 text-[10.5px] flex-1 flex flex-col justify-between">
            <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
              <span className="text-emerald-400 font-bold">Immediate Breakout Pivot</span>
              <div className="text-right">
                <strong className="text-neutral-100">{breakoutPivot != null ? formatNumber(breakoutPivot, 2) : "—"}</strong>
                <span className="text-[8.5px] text-neutral-500 block">
                  {nextResistances[1] != null ? `${formatNumber(nextResistances[1], 2)} Next Resistance` : "Next-session resistance"}
                </span>
              </div>
            </div>

            <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
              <span className="text-cyan-300 font-bold">Key Session Pivot (Anchor)</span>
              <div className="text-right">
                <strong className="text-neutral-100">{formatNumber(priorVwap, 2)}</strong>
                <span className="text-[8.5px] text-neutral-500 block">Settled VWAP Baseline</span>
              </div>
            </div>

            <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
              <span className="text-rose-400 font-bold">Critical Invalidation Floor</span>
              <div className="text-right">
                <strong className="text-neutral-100">{formatNumber(sessionLow, 2)}</strong>
                <span className="text-[8.5px] text-neutral-500 block">Session Day Low Floor</span>
              </div>
            </div>

            <div className="p-1.5 rounded bg-neutral-950 border border-neutral-850 flex justify-between items-center">
              <span className="text-[#00C896] font-bold">Bedrock Support</span>
              <div className="text-right">
                <strong className="text-neutral-100">{bedrockSupport != null ? formatNumber(bedrockSupport, 2) : "—"}</strong>
                <span className="text-[8.5px] text-neutral-500 block">Next-session support floor</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Pane (~50%): MULTI-SESSION / BTST STRATEGY SUITABILITY */}
        <div className="lg:col-span-6 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>MULTI-SESSION / BTST STRATEGY SUITABILITY</span>
            </div>
            <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 font-bold">
              SWING RANKED
            </span>
          </div>

          <div className="space-y-1.5 flex-1 flex flex-col justify-center">
            {/* The canonical tomorrow-plan does not (yet) publish ranked
                multi-session strategy candidates. No fabricated strategy cards,
                star ratings, confidence % or price targets are shown. */}
            <div className="bg-neutral-950/90 border border-neutral-850 rounded p-3 text-center text-neutral-500 text-[10.5px] leading-relaxed">
              Multi-session / BTST strategy suitability will populate once the
              post-market plan produces ranked candidates. No pre-computed
              strategy targets are shown.
              {nextResistances.length > 0 || nextSupports.length > 0 ? (
                <span className="block mt-1 text-neutral-400 text-[9px]">
                  Carry-forward reference levels available in the left pane.
                </span>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TomorrowPlanView;
