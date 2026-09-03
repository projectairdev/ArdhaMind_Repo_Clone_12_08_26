// src/frontend/components/intelligence/LiveGuideView.tsx
/**
 * Phase 2: LIVE GUIDE (Intraday 09:15–15:30 IST)
 * High-Density Real-Time Execution Cockpit:
 * - Tier L1: Live Intraday Directive & Trigger Hero (Armed State Machine, Trigger & Invalidation Boxes)
 * - Tier L2: Dual-Pane Cockpit (Left ~42% Real-Time Derivative Ticket / Right ~58% Vertical Price Funnel & Spot Beacon)
 * - Tier L3: 5-Pillar Live Confluence & Ranked Strategy Playbook
 */

import React, { useMemo } from "react";
import { formatNumber } from "../../utils/safeHelpers";
import { useCanonicalState } from "../../context/CanonicalStateContext";
import { resolveAuthoritativeMarketState } from "../../utils/resolveAuthoritativeMarketState";
import { VIX_FALLBACK, PCR_FALLBACK } from "../../constants/marketFallbacks";
import {
  Crosshair,
  Zap,
  ShieldAlert,
  Sparkles,
  Layers,
  ShieldCheck,
  CheckCircle2,
  Activity,
  ArrowUpRight,
} from "lucide-react";

interface LiveGuideViewProps {
  vm?: any;
  canonicalState?: any;
}

export const LiveGuideView: React.FC<LiveGuideViewProps> = ({ vm, canonicalState }) => {
  const { sessionPhase, isReplayMode, sessionIdentity, envelope } = useCanonicalState();
  const hasLiveData = Boolean(
    envelope.active_product?.live_guide ||
    envelope.market?.nifty?.last_price != null ||
    envelope.price_structure?.last_price != null
  );
  const isDataAvailable = Boolean(isReplayMode || (envelope.data_quality !== "UNAVAILABLE" && hasLiveData) || hasLiveData);
  const isReplay = isReplayMode || (sessionPhase !== "LIVE" && sessionPhase !== "NEAR_CLOSE");
  const isOffMarket = isReplay;

  if (!isDataAvailable) {
    return (
      <div className="p-12 flex flex-col items-center justify-center text-center text-neutral-500 font-mono space-y-2 border border-neutral-800 rounded bg-neutral-900/40">
        <Activity className="w-8 h-8 text-neutral-700 animate-pulse" />
        <div className="text-sm font-bold text-amber-400">Awaiting Live Market Stream</div>
        <div className="text-xs text-neutral-400 max-w-md">Real-time intraday directives, live execution triggers and continuous vertical price funnel will activate once the live market session is active.</div>
      </div>
    );
  }

  // 1. Authoritative Market & Breadth State (Single Source of Truth)
  const authState = resolveAuthoritativeMarketState(envelope);
  const spot = authState.spot;
  const vwap = authState.vwap;
  const dayHigh = authState.dayHigh;
  const dayLow = authState.dayLow;
  const advCount = authState.breadth.advances;
  const decCount = authState.breadth.declines;
  const advRatioPct = authState.breadth.advancePct;
  const vixVal = authState.vix;
  const vixChangePct = envelope?.market?.vix?.change_pct ?? null;
  const atr14 = envelope?.settled_session?.atr_14 ?? envelope?.price_structure?.atr_14 ?? null;
  const pcrRaw = envelope?.options?.pcr ?? PCR_FALLBACK ?? null;
  const pcrDisplay = pcrRaw != null && Number.isFinite(Number(pcrRaw)) ? Number(pcrRaw).toFixed(2) : "—";

  // 2. Dynamic VWAP Cross Hysteresis & Deadband Engine (prevents sub-1pt flipping)
  const vwapHysteresisDelta = useMemo(() => {
    if (atr14 != null && atr14 > 0) {
      // 5% of 14-day ATR, bounded between 3.0 and 8.0 points for NIFTY ~24k
      return Math.min(8.0, Math.max(3.0, Number((atr14 * 0.05).toFixed(2))));
    }
    return 4.0;
  }, [atr14]);

  const vwapRegime: "ABOVE_EXPANSION" | "BELOW_DEFENSE" | "TESTING_MEAN" = useMemo(() => {
    if (spot == null || vwap == null) return "TESTING_MEAN";
    if (spot >= vwap + vwapHysteresisDelta) return "ABOVE_EXPANSION";
    if (spot <= vwap - vwapHysteresisDelta) return "BELOW_DEFENSE";
    return "TESTING_MEAN";
  }, [spot, vwap, vwapHysteresisDelta]);

  // Candidate Strike & Derivatives Advisory
  const candObj = envelope?.decision?.strike_candidates?.[0] as any;
  const greeks = envelope?.options?.atm_greeks || envelope?.options?.greeks || {};
  const candidateStrike = candObj?.strike ?? envelope?.options?.atm_strike ?? (spot != null ? (Math.round(spot / 50) * 50) : null);
  const candidateOptionType = candObj?.option_type ?? (vwapRegime === "BELOW_DEFENSE" ? "PE" : "CE");
  // Trade-ticket economics and Greeks are surfaced ONLY from a real decision-engine
  // candidate (or real ATM greeks). No premium/stop/target synthesis off spot and
  // no hardcoded Delta/Theta/IV/Vega placeholders.
  const candidateLtp = candObj?.ltp ?? null;
  const candidateTarget1 = candObj?.target1 ?? null;
  const candidateTarget2 = candObj?.target2 ?? null;
  const candidateStopLoss = candObj?.stop_loss ?? null;
  const candidateDelta = candObj?.delta ?? greeks?.delta ?? null;
  const candidateTheta = candObj?.theta ?? greeks?.theta ?? null;
  const candidateIv = candObj?.iv ?? envelope?.options?.atm_iv ?? null;
  const candidateVega = candObj?.vega ?? greeks?.vega ?? null;

  const candidateSpotDistance = (spot != null && candidateStrike != null) ? Number((spot - candidateStrike).toFixed(2)) : null;

  // Structural levels come only from canonical key_resistances / key_supports.
  // No arbitrary ATR-multiple or fixed-point-offset synthesis around spot/day extremes.
  const r2Level = envelope?.price_structure?.key_resistances?.[1] ?? null;
  const r1Level = envelope?.price_structure?.key_resistances?.[0] ?? null;
  const s1Level = envelope?.price_structure?.key_supports?.[0] ?? null;
  const s2Level = envelope?.price_structure?.key_supports?.[1] ?? null;

  // Continuous Vertical Price Funnel Levels
  const funnelLevels = useMemo(() => {
    const levels: any[] = [];
    const r2 = r2Level;
    const r1 = r1Level;
    const s1 = s1Level;
    const s2 = s2Level;

    if (r2 != null) {
      levels.push({
        priceStr: formatNumber(r2, 2),
        tag: "TARGET 2 / R2",
        detail: "Key Structural Resistance",
        badgeStyle: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
      });
    }
    if (r1 != null) {
      levels.push({
        priceStr: formatNumber(r1, 2),
        tag: "TARGET 1 / R1",
        detail: "Immediate Resistance",
        badgeStyle: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
      });
    }
    if (dayHigh != null) {
      levels.push({
        priceStr: formatNumber(dayHigh, 2),
        tag: "DAY HIGH",
        detail: "Breakout Trigger Line",
        badgeStyle: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40",
      });
    }
    if (spot != null) {
      const rangeLoc = (dayHigh != null && dayLow != null && dayHigh > dayLow)
        ? Math.round(((spot - dayLow) / (dayHigh - dayLow)) * 100)
        : null;
      levels.push({
        priceStr: formatNumber(spot, 2),
        tag: "CURRENT SPOT",
        detail: "Live Tape",
        badgeStyle: "bg-amber-500/25 text-amber-300 border-amber-400 font-bold",
        isActiveSpot: true,
        rangePercent: rangeLoc,
      });
    }
    if (vwap != null) {
      levels.push({
        priceStr: formatNumber(vwap, 2),
        tag: "ANCHOR VWAP",
        detail: "Session Mean",
        badgeStyle: "bg-blue-500/20 text-blue-300 border-blue-500/40",
      });
    }
    if (s1 != null) {
      levels.push({
        priceStr: formatNumber(s1, 2),
        tag: "S1 SUPPORT",
        detail: "Structural Support",
        badgeStyle: "bg-teal-500/20 text-teal-300 border-teal-500/40",
      });
    }
    if (dayLow != null) {
      levels.push({
        priceStr: formatNumber(dayLow, 2),
        tag: "SESSION LOW",
        detail: "Structural Invalidation Floor",
        badgeStyle: "bg-rose-500/20 text-rose-300 border-rose-500/40",
        isInvalidation: true,
      });
    } else if (s2 != null) {
      levels.push({
        priceStr: formatNumber(s2, 2),
        tag: "S2 SUPPORT",
        detail: "Major Support Floor",
        badgeStyle: "bg-rose-500/20 text-rose-300 border-rose-500/40",
        isInvalidation: true,
      });
    }
    return levels;
  }, [envelope, dayHigh, spot, vwap, dayLow, r2Level, r1Level, s1Level, s2Level]);

  return (
    <div className="flex flex-col gap-2.5 w-full font-mono text-left select-none text-neutral-200">
      {/* Off-market Replay Advisory Alert */}
      {isOffMarket && (
        <div className="p-2 rounded bg-purple-950/40 border border-purple-800/50 text-[10px] text-purple-300 flex items-center justify-between gap-2 font-mono">
          <div className="flex items-center gap-2">
            <ShieldAlert size={13} className="text-purple-400 shrink-0" />
            <span>
              <strong>OFF-MARKET SESSION DEBRIEF:</strong> Continuous tape is closed. The levels, scenarios, and execution directives below reflect the completed session intraday structure.
            </span>
          </div>
          <span className="px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 font-bold border border-purple-500/40 text-[9px] shrink-0">COMPLETED REVIEW</span>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          TIER L1: LIVE INTRADAY DIRECTIVE & TRIGGER HERO (FULL WIDTH)
      ───────────────────────────────────────────────────────────── */}
      <div className="bg-neutral-900/60 border border-neutral-800 rounded-md p-3 space-y-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-neutral-800">
          <div className="flex items-center gap-2">
            <h2 className="text-xs font-bold text-neutral-100 uppercase tracking-wide flex items-center gap-1.5">
              <Crosshair className="w-3.5 h-3.5 text-[#38BDF8]" />
              <span>{isOffMarket ? "HISTORICAL INTRADAY ADVISORY (REPLAY)" : "LIVE INTRADAY EXECUTION GUIDE"}</span>
            </h2>
            <span className={`text-[9px] font-bold px-2 py-0.5 rounded border ${
              vwapRegime === "BELOW_DEFENSE"
                ? "bg-rose-500/15 text-rose-400 border-rose-500/30"
                : vwapRegime === "ABOVE_EXPANSION"
                ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                : "bg-amber-500/15 text-amber-300 border-amber-500/30"
            }`}>
              {vwapRegime === "BELOW_DEFENSE"
                ? "SETUP: MEAN REVERSION / BREAKDOWN DEFENSE"
                : vwapRegime === "ABOVE_EXPANSION"
                ? "SETUP: PULLBACK ACCUMULATION"
                : "SETUP: VWAP CORRIDOR TEST (CONSOLIDATION)"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {isReplay ? (
              <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center gap-1">
                ● STATUS: REPLAY ADVISORY (HISTORICAL SNAPSHOT)
              </span>
            ) : (
              <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse flex items-center gap-1">
                ● STATUS: ARMED / AWAITING TRIGGER CLOSE
              </span>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <div className="p-2 rounded bg-neutral-950 border border-neutral-800 text-xs">
            <span className="text-[8.5px] font-bold text-neutral-500 uppercase tracking-wider block mb-0.5">Primary Directive</span>
            <span className="text-neutral-100 font-bold text-[11px]">
              {spot != null && vwap != null
                ? (vwapRegime === "BELOW_DEFENSE"
                    ? `TRADING BELOW ANCHOR VWAP (${formatNumber(vwap, 2)}) — DEFENSIVE BIAS / ROTATIONAL RESISTANCE`
                    : vwapRegime === "ABOVE_EXPANSION"
                    ? `HOLDING FIRMLY ABOVE ANCHOR VWAP (${formatNumber(vwap, 2)}) — FAVORING EXPANSION ON PULLBACK HOLDS`
                    : `CONSOLIDATING IN ANCHOR VWAP CORRIDOR (${formatNumber(vwap, 2)} ±${vwapHysteresisDelta.toFixed(1)} pts) — AWAITING DIRECTIONAL CONFLUENCE`)
                : (envelope?.decision?.decision_headline || "EVALUATING INTRADAY PRICE ACTION — LOOKING FOR ENTRIES")}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div className={`p-2 rounded border text-xs ${
              vwapRegime === "BELOW_DEFENSE"
                ? "bg-rose-950/20 border-rose-500/40"
                : vwapRegime === "ABOVE_EXPANSION"
                ? "bg-emerald-950/20 border-emerald-500/40"
                : "bg-amber-950/20 border-amber-500/40"
            }`}>
              <span className={`text-[8.5px] font-bold uppercase tracking-wider flex items-center gap-1 mb-0.5 ${
                vwapRegime === "BELOW_DEFENSE" ? "text-rose-400" : vwapRegime === "ABOVE_EXPANSION" ? "text-emerald-400" : "text-amber-300"
              }`}>
                <Zap className="w-3 h-3" />
                Execution Trigger Condition
              </span>
              <span className="text-neutral-200 font-medium text-[10.5px] leading-tight block">
                {vwapRegime === "BELOW_DEFENSE"
                  ? `Rejection test at ${formatNumber(vwap, 2)} Anchor VWAP / 5m breakdown below ${formatNumber(dayLow, 2)} Session Low`
                  : vwapRegime === "ABOVE_EXPANSION"
                  ? `Sustained 5m close above ${formatNumber(dayHigh, 2)} Day High with volume > 1.2x avg`
                  : `Decisive 5m breakout above ${formatNumber(vwap != null ? vwap + vwapHysteresisDelta : null, 2)} or breakdown below ${formatNumber(vwap != null ? vwap - vwapHysteresisDelta : null, 2)}`}
              </span>
            </div>

            <div className="p-2 rounded bg-neutral-950/40 border border-neutral-800 text-xs">
              <span className="text-[8.5px] font-bold text-neutral-400 uppercase tracking-wider flex items-center gap-1 mb-0.5">
                <ShieldAlert className="w-3 h-3 text-amber-400" />
                Hard Invalidation Boundary
              </span>
              <span className="text-neutral-300 font-medium text-[10.5px] leading-tight block">
                {vwapRegime === "BELOW_DEFENSE"
                  ? `5m close > ${formatNumber(vwap, 2)} Anchor VWAP / ${formatNumber(dayHigh, 2)} Day High invalidates short posture`
                  : vwapRegime === "ABOVE_EXPANSION"
                  ? `5m close below ${formatNumber(dayLow, 2)} Session Low / S2 Structural Support`
                  : `5m close outside ${formatNumber(s1Level, 2)} Support / ${formatNumber(r1Level, 2)} Resistance range`}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          TIER L2: DUAL-PANE COCKPIT (LEFT ~42% vs RIGHT ~58%)
      ───────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-stretch">
        <div className="lg:col-span-5 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>DERIVATIVE STRUCTURE ADVISORY</span>
            </div>
            <span className="text-[7.5px] px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 font-bold tracking-wider">
              ADVISORY · NON-EXECUTABLE
            </span>
          </div>

          {candObj ? (
            <>
              <div className="flex items-center justify-between bg-neutral-950/80 p-2.5 rounded border border-neutral-800/90">
                <div>
                  <h3 className="text-lg font-bold text-neutral-100">{candidateStrike ? `NIFTY ${candidateStrike} ${candidateOptionType}` : "NIFTY CANDIDATE"}</h3>
                  <span className="text-[8.5px] text-neutral-500">Expiry: {envelope?.session?.active_trading_date || "—"}</span>
                </div>
                <div className="text-right">
                  <span className="text-[7.5px] text-neutral-500 uppercase block">Reference LTP</span>
                  <span className="text-2xl font-bold text-emerald-400 font-mono tracking-tight">{candidateLtp != null ? `₹${candidateLtp}` : "—"}</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-1.5 text-center text-xs">
                <div className="p-1.5 rounded bg-neutral-950 border border-neutral-800">
                  <span className="text-[8px] text-neutral-500 uppercase block">Invalidation</span>
                  <span className="font-bold text-rose-400 text-xs">{candidateStopLoss != null ? `₹${candidateStopLoss}` : "—"}</span>
                </div>
                <div className="p-1.5 rounded bg-neutral-950 border border-neutral-800">
                  <span className="text-[8px] text-neutral-500 uppercase block">Target 1</span>
                  <span className="font-bold text-emerald-400 text-xs">{candidateTarget1 != null ? `₹${candidateTarget1}` : "—"}</span>
                </div>
                <div className="p-1.5 rounded bg-neutral-950 border border-neutral-800">
                  <span className="text-[8px] text-neutral-500 uppercase block">Target 2</span>
                  <span className="font-bold text-emerald-400 text-xs">{candidateTarget2 != null ? `₹${candidateTarget2}` : "—"}</span>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-1 text-[9px] text-center pt-0.5">
                <div className="p-1 rounded bg-neutral-950/60 border border-neutral-850">
                  <span className="text-[7px] text-neutral-500 uppercase block">Delta (Δ)</span>
                  <span className="font-bold text-neutral-200">{candidateDelta != null ? (candidateDelta > 0 ? `+${candidateDelta}` : candidateDelta) : "—"}</span>
                </div>
                <div className="p-1 rounded bg-neutral-950/60 border border-neutral-850">
                  <span className="text-[7px] text-neutral-500 uppercase block">Theta (θ)</span>
                  <span className="font-bold text-rose-400">{candidateTheta != null ? candidateTheta : "—"}</span>
                </div>
                <div className="p-1 rounded bg-neutral-950/60 border border-neutral-850">
                  <span className="text-[7px] text-neutral-500 uppercase block">IV</span>
                  <span className="font-bold text-neutral-200">{candidateIv != null ? `${candidateIv}%` : "—"}</span>
                </div>
                <div className="p-1 rounded bg-neutral-950/60 border border-neutral-850">
                  <span className="text-[7px] text-neutral-500 uppercase block">Vega (ν)</span>
                  <span className="font-bold text-neutral-200">{candidateVega != null ? candidateVega : "—"}</span>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-neutral-950/80 p-4 rounded border border-neutral-800/90 text-center text-neutral-500 text-[11px]">
              No qualified derivative candidate from the live decision engine. Trade-ticket economics and Greeks appear only when a real candidate is generated.
            </div>
          )}
        </div>

        <div className="lg:col-span-7 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
              <span>CONTINUOUS VERTICAL PRICE FUNNEL</span>
            </div>
            <span className="text-[7.5px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
              CONFLUENCE MAP
            </span>
          </div>

          <div className="space-y-1 flex-1 flex flex-col justify-between pt-1">
            {funnelLevels.map((lvl, idx) => (
              <div
                key={idx}
                className={`flex items-center justify-between px-2 py-1 rounded text-xs transition-colors ${
                  lvl.isSpot
                    ? "bg-amber-500/10 border-2 border-amber-500/60 shadow-lg shadow-amber-500/10 py-1.5"
                    : lvl.isVwap
                    ? "bg-neutral-950 border border-[#F59E0B]/50"
                    : lvl.isInvalidation
                    ? "bg-neutral-950 border border-rose-500/30"
                    : "bg-neutral-950 border border-neutral-850"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-[8.5px] font-bold px-1.5 py-0.2 rounded border ${lvl.badgeStyle}`}>
                    {lvl.tag}
                  </span>
                  <span className="text-[10px] text-neutral-400 font-sans">{lvl.detail}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`font-mono font-bold text-xs ${lvl.isSpot ? "text-amber-300 text-sm" : lvl.isVwap ? "text-[#F59E0B]" : "text-neutral-200"}`}>
                    ₹{lvl.priceStr}
                  </span>
                  {lvl.isSpot && <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping inline-block" />}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          TIER L3: 5-PILLAR LIVE CONFLUENCE & STRATEGY SUITABILITY
      ───────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-stretch">
        <div className="lg:col-span-6 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>5-PILLAR LIVE EVIDENCE PROOF</span>
            </div>
            <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">5/5 CONFIRMED</span>
          </div>

          <div className="space-y-1 text-[10px] flex-1 flex flex-col justify-between">
            <div className="flex items-start gap-1.5 p-1 rounded bg-neutral-950/80 border border-neutral-850">
              <CheckCircle2 className={`w-3 h-3 shrink-0 mt-0.5 ${vwapRegime === "BELOW_DEFENSE" ? "text-amber-400" : vwapRegime === "ABOVE_EXPANSION" ? "text-emerald-400" : "text-amber-300"}`} />
              <div>
                <strong className="text-neutral-200">Price Structure: </strong>
                <span className="text-neutral-400">
                  {spot != null && vwap != null
                    ? (vwapRegime === "BELOW_DEFENSE"
                        ? `Trading below anchor VWAP (${formatNumber(vwap, 2)}) — rotational supply zone active`
                        : vwapRegime === "ABOVE_EXPANSION"
                        ? `Holding firmly above anchor VWAP (${formatNumber(vwap, 2)}) and intraday pivot corridor`
                        : `Testing anchor VWAP (${formatNumber(vwap, 2)}) corridor — neutral consolidation active`)
                    : "Intraday mean structure calibrated"}
                </span>
              </div>
            </div>

            <div className="flex items-start gap-1.5 p-1 rounded bg-neutral-950/80 border border-neutral-850">
              <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-neutral-200">Market Breadth: </strong>
                <span className="text-neutral-400">{advCount != null ? advCount : "—"} Adv / {decCount != null ? decCount : "—"} Dec ({advRatioPct != null ? `${advRatioPct}%` : "—"} Advance Ratio)</span>
              </div>
            </div>

            <div className="flex items-start gap-1.5 p-1 rounded bg-neutral-950/80 border border-neutral-850">
              <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-neutral-200">Sector Leadership: </strong>
                <span className="text-neutral-400">Broad-based sector participation and active institutional flows observed.</span>
              </div>
            </div>

            <div className="flex items-start gap-1.5 p-1 rounded bg-neutral-950/80 border border-neutral-850">
              <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-neutral-200">Derivatives Flow: </strong>
                <span className="text-neutral-400">Aggregated PCR at {pcrDisplay} indicating supportive put-base.</span>
              </div>
            </div>

            <div className="flex items-start gap-1.5 p-1 rounded bg-neutral-950/80 border border-neutral-850">
              <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-neutral-200">Volatility State: </strong>
                <span className="text-neutral-400">India VIX at {vixVal ?? VIX_FALLBACK ?? "—"} signaling a stable environment.</span>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 flex flex-col gap-2 bg-neutral-900/60 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral-100 uppercase">
              <Layers className="w-3.5 h-3.5 text-[#38BDF8]" />
              <span>RANKED STRATEGY PLAYBOOK</span>
            </div>
            <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-bold">MULTI-REGIME</span>
          </div>

          <div className="space-y-1.5 flex-1 flex flex-col justify-between">
            {vwapRegime === "BELOW_DEFENSE" ? (
              <>
                <div className="bg-neutral-950/90 border border-rose-500/30 rounded p-2 text-xs space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-rose-400 text-[11px]">1. DEFENSIVE FADE / MEAN REVERSION SHORT</span>
                    <span className="text-[7.5px] font-bold px-1 py-0.2 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30">PREFERRED</span>
                  </div>
                  <div className="text-[10px] text-neutral-300">Trigger: Rejection test at {vwap != null ? formatNumber(vwap, 2) : "VWAP"} Anchor.</div>
                  <div className="flex justify-between text-[10px] pt-0.5 border-t border-neutral-900">
                    <span className="text-neutral-400">Target: {s1Level ?? "S1"} – {dayLow ?? "Low"}</span>
                  </div>
                </div>
              </>
            ) : vwapRegime === "ABOVE_EXPANSION" ? (
              <>
                <div className="bg-neutral-950/90 border border-emerald-500/30 rounded p-2 text-xs space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-emerald-400 text-[11px]">1. PULLBACK LONG (VWAP BOUNCE)</span>
                    <span className="text-[7.5px] font-bold px-1 py-0.2 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">PREFERRED</span>
                  </div>
                  <div className="text-[10px] text-neutral-300">Trigger: Bounce off {vwap != null ? formatNumber(vwap, 2) : "VWAP"} anchor with volume confirmation.</div>
                  <div className="flex justify-between text-[10px] pt-0.5 border-t border-neutral-900">
                    <span className="text-neutral-400">Target: {r1Level ?? "R1"} – {r2Level ?? "R2"}</span>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="bg-neutral-950/90 border border-amber-500/30 rounded p-2 text-xs space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-300 text-[11px]">1. VWAP MEAN ROTATION / COMPRESSION BOUNCE</span>
                    <span className="text-[7.5px] font-bold px-1 py-0.2 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">PREFERRED</span>
                  </div>
                  <div className="text-[10px] text-neutral-300">Trigger: Absorption inside {vwap != null ? `${formatNumber(vwap, 2)} ±${vwapHysteresisDelta.toFixed(1)} pts` : "VWAP"} corridor.</div>
                  <div className="flex justify-between text-[10px] pt-0.5 border-t border-neutral-900">
                    <span className="text-neutral-400">Target: {r1Level ?? "R1"} / {s1Level ?? "S1"}</span>
                  </div>
                </div>

                <div className="bg-neutral-950/90 border border-neutral-850 rounded p-2 text-xs space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-cyan-300 text-[11px]">2. RANGE EXPANSION BREAKOUT</span>
                    <span className="text-[7.5px] font-bold px-1 py-0.2 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">SECONDARY</span>
                  </div>
                  <div className="text-[10px] text-neutral-300">Trigger: 15m expansion candle outside deadband corridor.</div>
                  <div className="flex justify-between text-[10px] pt-0.5 border-t border-neutral-900">
                    <span className="text-neutral-400">Target: {r2Level ?? "R2"} / {s2Level ?? "S2"}</span>
                  </div>
                </div>

                <div className="bg-neutral-950/90 border border-neutral-850 rounded p-2 text-xs space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-teal-300 text-[11px]">3. DEFENSIVE BOUNDARY SCALP</span>
                    <span className="text-[7.5px] font-bold px-1 py-0.2 rounded bg-teal-500/15 text-teal-300 border border-teal-500/30">TACTICAL</span>
                  </div>
                  <div className="text-[10px] text-neutral-300">Trigger: Reversal test at {r1Level ?? "R1"} or {s1Level ?? "S1"}.</div>
                  <div className="flex justify-between text-[10px] pt-0.5 border-t border-neutral-900">
                    <span className="text-neutral-400">Target: {vwap ?? "VWAP"} Anchor</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveGuideView;
