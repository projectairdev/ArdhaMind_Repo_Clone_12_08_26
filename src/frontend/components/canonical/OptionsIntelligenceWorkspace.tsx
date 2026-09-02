/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Canonical Options Intelligence Workspace (P7).
 * Institutional 3-Column Cockpit with ITM Shading, Micro-OI Bars, and Dense Quantitative Derivatives Architecture.
 */

import React, { useState, useMemo } from "react";
import { CanonicalOptionsIntelligence, StrikeCandidate, StrikeRow } from "../../types/canonical";
import { useCanonicalState } from "../../context/CanonicalStateContext";
import { CANONICAL_28_AUG_STRIKE_UNIVERSE } from "../../data/canonicalFixtures";
import { resolveStrikeCandidateDistance } from "../../utils/canonicalSemanticContract";
import { resolveAuthoritativeMarketState } from "../../utils/canonicalResolvers";
import { formatNumber } from "../../utils/safeHelpers";
import { PCR_FALLBACK } from "../../constants/marketFallbacks";
import { DataFreshnessBadge } from "../ui/DataFreshnessBadge";
import {
  Layers,
  ChevronDown,
  ShieldCheck,
  TrendingUp,
  Activity,
  BarChart2,
  Compass,
} from "lucide-react";

interface OptionsWorkspaceProps {
  options?: CanonicalOptionsIntelligence;
  candidateStrike?: StrikeCandidate | null;
}

export function OptionsIntelligenceWorkspace({
  options: propOptions,
  candidateStrike: propCandidateStrike,
}: OptionsWorkspaceProps = {}) {
  const { envelope, isReplayMode } = useCanonicalState();
  const authState = resolveAuthoritativeMarketState(envelope);
  const options = propOptions || envelope.options || {} as CanonicalOptionsIntelligence;
  const candidateStrike = propCandidateStrike !== undefined
    ? propCandidateStrike
    : (envelope.decision?.strike_candidates?.[0] || null);

  // Spot Resolution across live, post-market and settled envelopes
  const resolvedSpot = Number(options?.spot_price)
    || Number((options as any)?.underlying_price)
    || Number((options as any)?.underlying_spot)
    || authState.spot
    || Number(envelope?.market?.nifty?.last_price)
    || Number(envelope?.price_structure?.last_price)
    || Number(envelope?.settled_session?.close)
    || null;

  const hasChainData = (Array.isArray(options?.strike_universe) && options.strike_universe.length > 0)
    || Number(options?.pcr) > 0
    || Number(options?.atm_strike) > 0
    || Number(options?.max_pain) > 0;

  const isDataAvailable = Boolean(isReplayMode || (options?.quality !== "UNAVAILABLE" && (resolvedSpot != null || hasChainData)) || resolvedSpot != null);

  // Expiry & Filter Controls
  const activeExpiry = envelope.options?.expiry || options.expiry || authState.sessionDate || "—";
  const [selectedExpiry, setSelectedExpiry] = useState<string>(activeExpiry);
  const [chainViewMode, setChainViewMode] = useState<"TABLE" | "HEATMAP" | "CHANGE">("TABLE");
  const [strikeFilterMode, setStrikeFilterMode] = useState<"NEAR_ATM" | "ALL">("NEAR_ATM");
  const [selectedStrike, setSelectedStrike] = useState<number | null>(null);

  const spotPrice = isDataAvailable ? resolvedSpot : null;
  const prevClose = isDataAvailable ? (authState.prevClose ?? envelope?.market?.nifty?.previous_close ?? envelope?.settled_session?.close ?? envelope?.price_structure?.previous_close ?? null) : null;
  const netChange = (spotPrice != null && prevClose != null) ? spotPrice - prevClose : (authState.change ?? envelope?.market?.nifty?.change ?? envelope?.price_structure?.change ?? null);
  const netChangePct = (netChange != null && prevClose != null && prevClose > 0) ? (netChange / prevClose) * 100 : (authState.changePct ?? envelope?.market?.nifty?.change_pct ?? envelope?.price_structure?.change_pct ?? null);
  const isPositive = (netChange ?? 0) >= 0;

  const atmStrike = isDataAvailable ? (options.atm_strike || (spotPrice ? Math.round(spotPrice / 50) * 50 : null)) : null;
  // Max pain and call/put walls come only from the real option-chain aggregate.
  // No "atmStrike ± 50/200" arithmetic-offset synthesis.
  const maxPain = isDataAvailable ? (options.max_pain || null) : null;
  const callWall = isDataAvailable ? (options.call_wall || null) : null;
  const putWall = isDataAvailable ? (options.put_wall || null) : null;
  const pcr = isDataAvailable ? (Number(options.pcr) > 0 ? Number(options.pcr) : PCR_FALLBACK) : PCR_FALLBACK;
  const totalCallOiCr = isDataAvailable ? (Number(options.total_call_oi) > 0 ? Number(options.total_call_oi) / 10000000 : null) : null;
  const totalPutOiCr = isDataAvailable ? (Number(options.total_put_oi) > 0 ? Number(options.total_put_oi) / 10000000 : null) : null;
  const totalOiCr = (totalCallOiCr != null && totalPutOiCr != null) ? (totalCallOiCr + totalPutOiCr) : null;
  const callRatioPct = (totalCallOiCr != null && totalOiCr != null && totalOiCr > 0) ? Math.round((totalCallOiCr / totalOiCr) * 100) : null;
  const putRatioPct = (callRatioPct != null) ? 100 - callRatioPct : null;

  // Resolve Strike Universe
  const strikes: StrikeRow[] = useMemo(() => {
    let raw = (Array.isArray(options.strike_universe) && options.strike_universe.length > 0)
      ? options.strike_universe
      : [];

    // No live option-chain: render an empty ladder ("Awaiting option chain")
    // rather than synthesizing 11 strikes with Gaussian-curve OI and
    // time-decay premiums. Replay mode still uses its recorded fixture.
    if (raw.length === 0 && isReplayMode) {
      raw = CANONICAL_28_AUG_STRIKE_UNIVERSE;
    }

    return raw.map((s: any) => {
      const strikeVal = Number(s.strike);
      const isAtm = Boolean(s.is_atm || s.isAtm || (atmStrike != null && strikeVal === atmStrike));

      // Only real per-strike values are surfaced; missing fields stay null/0
      // so downstream cells render "—" instead of a fabricated figure.
      const ce_ltp = s.ce_ltp ?? s.callLtp ?? s.call_ltp ?? null;
      const pe_ltp = s.pe_ltp ?? s.putLtp ?? s.put_ltp ?? null;

      const ce_oi = s.ce_oi ?? s.callOi ?? s.call_oi ?? null;
      const pe_oi = s.pe_oi ?? s.putOi ?? s.put_oi ?? null;
      const ce_oi_change = s.ce_oi_change ?? s.callChg ?? s.call_oi_change ?? null;
      const pe_oi_change = s.pe_oi_change ?? s.putChg ?? s.put_oi_change ?? null;
      const ce_iv = s.ce_iv ?? s.callIv ?? s.call_iv ?? s.iv ?? s.implied_volatility ?? null;
      const pe_iv = s.pe_iv ?? s.putIv ?? s.put_iv ?? s.iv ?? s.implied_volatility ?? null;
      const ce_buildup = s.ce_buildup ?? s.callBuildup ?? (ce_oi_change != null ? (ce_oi_change > 0 ? "LONG_BUILDUP" : "SHORT_COVERING") : "NEUTRAL");
      const pe_buildup = s.pe_buildup ?? s.putBuildup ?? (pe_oi_change != null ? (pe_oi_change > 0 ? "SHORT_BUILDUP" : "LONG_UNWINDING") : "NEUTRAL");

      return {
        strike: strikeVal,
        ce_oi: Number(ce_oi) || 0,
        pe_oi: Number(pe_oi) || 0,
        ce_oi_change: Number(ce_oi_change) || 0,
        pe_oi_change: Number(pe_oi_change) || 0,
        ce_ltp: ce_ltp != null ? Number(Number(ce_ltp).toFixed(2)) : null,
        pe_ltp: pe_ltp != null ? Number(Number(pe_ltp).toFixed(2)) : null,
        ce_iv: ce_iv != null ? Number(Number(ce_iv).toFixed(2)) : null,
        pe_iv: pe_iv != null ? Number(Number(pe_iv).toFixed(2)) : null,
        ce_buildup: String(ce_buildup || "NEUTRAL"),
        pe_buildup: String(pe_buildup || "NEUTRAL"),
        is_atm: isAtm,
        is_call_wall: Boolean(s.is_call_wall || s.isCallWall || (callWall != null && strikeVal === callWall)),
        is_put_wall: Boolean(s.is_put_wall || s.isPutWall || (putWall != null && strikeVal === putWall)),
      };
    });
  }, [options.strike_universe, isReplayMode, resolvedSpot, atmStrike, callWall, putWall]);

  // Filter strikes
  const displayedStrikes = useMemo(() => {
    let list = [...strikes].sort((a, b) => a.strike - b.strike);
    if (strikeFilterMode === "NEAR_ATM" && atmStrike != null) {
      list = list.filter((s) => Math.abs(s.strike - atmStrike) <= 300);
    }
    return list;
  }, [strikes, strikeFilterMode, atmStrike]);

  // Strike immediately above the real live spot — the divider row renders before
  // it so the spot line sits at its true position in the ladder for any spot.
  // Falls back to the strike nearest spot when spot is above the whole ladder.
  const spotLineStrike = useMemo(() => {
    if (spotPrice == null || displayedStrikes.length === 0) return null;
    const above = displayedStrikes.find((s) => s.strike >= spotPrice);
    if (above) return above.strike;
    return displayedStrikes[displayedStrikes.length - 1].strike;
  }, [displayedStrikes, spotPrice]);

  // Selected Strike Data
  const selectedStrikeRow = useMemo(() => {
    if (!strikes.length) return null;
    return strikes.find((s) => s.strike === selectedStrike) || strikes.find((s) => atmStrike != null && s.strike === atmStrike) || strikes[0];
  }, [strikes, selectedStrike, atmStrike]);

  const authoritativeSpot = spotPrice ?? authState.spot ?? null;
  const selectedDist = (selectedStrike != null && authoritativeSpot != null) ? selectedStrike - authoritativeSpot : null;
  const selectedDistPct = (selectedDist != null && authoritativeSpot != null && authoritativeSpot > 0) ? (selectedDist / authoritativeSpot) * 100 : null;

  // Max OI for Heatmap & Progress Bar normalization
  const maxOiInUniverse = useMemo(() => {
    let m = 1;
    strikes.forEach((s) => {
      if ((s.ce_oi || 0) > m) m = s.ce_oi || 1;
      if ((s.pe_oi || 0) > m) m = s.pe_oi || 1;
    });
    return m;
  }, [strikes]);

  // Dynamic Candidate Distance Resolution & LTP Synchronization
  const candidateStrikeInfo = useMemo(() => {
    let cand = candidateStrike || (envelope as any)?.decision?.strike_candidates?.[0];
    if (!cand && isReplayMode) {
      cand = {
        canonical_id: `OPT:NSE:NIFTY:${authState.sessionDate || "2026-09-01"}:CE:24050`,
        option_type: "CE" as const,
        strike: 24050,
        ltp: 88.50,
        distance_from_spot: -5.80,
        liquidity: "HIGH" as const,
        strength: "STRONG" as const,
        oi_context: "ATM_MOMENTUM_PLAY",
        iv: 13.8,
        spread: 1.2,
        rationale: ["At-the-money call strike captures upside breakout toward pivot."],
        risks: ["Loss of opening support invalidates setup."],
      };
    }
    // No synthesized advisory candidate: if the decision engine returns no
    // real strike_candidate (and we are not in replay), the advisory panel
    // renders its explicit "no qualified candidate" state.

    if (!cand) return null;

    // Sync candidate LTP with actual strike row in ladder
    const matchingRow = strikes.find((s) => s.strike === cand!.strike);
    const liveLtp = matchingRow
      ? (cand.option_type === "CE" ? matchingRow.ce_ltp : matchingRow.pe_ltp)
      : cand.ltp;

    const syncedCand = {
      ...cand,
      ltp: liveLtp != null ? liveLtp : cand.ltp,
    };

    const { distanceLabel, isItm } = resolveStrikeCandidateDistance(syncedCand, spotPrice ?? authoritativeSpot ?? 0);
    return {
      cand: syncedCand,
      distanceLabel,
      isItm,
    };
  }, [candidateStrike, spotPrice, isReplayMode, strikes, envelope, atmStrike, authState]);

  return (
    <div className="flex flex-col gap-2.5 p-3 w-full bg-neutral-950 text-neutral-200 font-sans">
      {/* ========================================================================= */}
      {/* TIER 1: DERIVATIVES STATE STRIP (Top Full-Width Banner)                    */}
      {/* ========================================================================= */}
      <div className="w-full bg-neutral-900/60 border border-neutral-800 rounded-md p-2.5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-400">
            Derivatives State
          </span>
          {/* Option-chain snapshot time — from the provider's snapshot timestamp, not render time */}
          <DataFreshnessBadge
            observedAt={
              (envelope as any)?.options?.observed_at ??
              (envelope as any)?.market?.nifty?.exchange_timestamp ??
              (envelope as any)?.market_observed_at ??
              null
            }
            kind="chain"
            label="Chain"
          />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-9 gap-2 text-xs font-mono">
          {/* 1. EXPIRY */}
          <div className="flex flex-col gap-0.5 bg-neutral-950/60 border border-neutral-800/80 rounded p-1.5">
            <span className="text-[10px] text-neutral-400 uppercase tracking-wider">EXPIRY</span>
            <span className="font-bold text-neutral-200 text-[11px] truncate">
              {options.expiry || (isReplayMode ? "28 Aug 2026" : "03 Sep 2026")}
            </span>
            <span className="text-[9px] text-cyan-400">{isReplayMode ? "Current Weekly" : "Active Weekly (03 Sep)"}</span>
          </div>

          {/* 2. SPOT */}
          <div className="flex flex-col gap-0.5 bg-neutral-950/60 border border-neutral-800/80 rounded p-1.5">
            <span className="text-[10px] text-neutral-400 uppercase tracking-wider">SPOT</span>
            <span className="font-bold text-emerald-400 text-[12px] tabular-nums">
              {spotPrice != null ? spotPrice.toLocaleString("en-IN", { minimumFractionDigits: 2 }) : "Unavailable"}
            </span>
            <span className="text-[9px] text-emerald-400 tabular-nums">
              {netChange != null ? `${isPositive ? "+" : ""}${netChange.toFixed(2)} (${isPositive ? "+" : ""}${(netChangePct ?? 0).toFixed(2)}%)` : "—"}
            </span>
          </div>

          {/* 3. ATM STRIKE */}
          <div className="flex flex-col gap-0.5 bg-neutral-950/60 border border-neutral-800/80 rounded p-1.5">
            <span className="text-[10px] text-neutral-400 uppercase tracking-wider">ATM STRIKE</span>
            <span className="font-bold text-cyan-300 text-[12px] tabular-nums">
              {atmStrike != null ? atmStrike.toLocaleString("en-IN") : "—"}
            </span>
            <span className="text-[9px] text-neutral-400">ATM Reference</span>
          </div>

          {/* 4. PCR (OI) */}
          <div className="flex flex-col gap-0.5 bg-neutral-950/60 border border-neutral-800/80 rounded p-1.5">
            <span className="text-[10px] text-neutral-400 uppercase tracking-wider">PCR (OI)</span>
            <span className="font-bold text-emerald-400 text-[12px] tabular-nums">
              {pcr != null ? pcr.toFixed(2) : "—"}
            </span>
            <span className="text-[9px] text-emerald-400 truncate">
              {pcr != null ? (pcr >= 1 ? "Bullish Put Writing" : "Call Heavy") : "Awaiting chain"}
            </span>
          </div>

          {/* 5. MAX PAIN */}
          <div className="flex flex-col gap-0.5 bg-neutral-950/60 border border-neutral-800/80 rounded p-1.5">
            <span className="text-[10px] text-neutral-400 uppercase tracking-wider">MAX PAIN</span>
            <span className="font-bold text-amber-400 text-[12px] tabular-nums">
              {maxPain != null ? maxPain.toLocaleString("en-IN") : "—"}
            </span>
            <span className="text-[9px] text-neutral-400">Pin Gravity</span>
          </div>

          {/* 6. ATM IV */}
          <div className="flex flex-col gap-0.5 bg-neutral-950/60 border border-neutral-800/80 rounded p-1.5">
            <span className="text-[10px] text-neutral-400 uppercase tracking-wider">ATM IV</span>
            <span className="font-bold text-neutral-200 text-[12px] tabular-nums">
              {options?.atm_iv != null ? `${formatNumber(Number(options.atm_iv), 2)}%` : (envelope?.market?.india_vix?.last_price != null ? `${formatNumber(envelope.market.india_vix.last_price, 2)}% (VIX)` : "—")}
            </span>
            <span className="text-[9px] text-cyan-400">{options?.atm_iv != null ? "Implied Vol" : (envelope?.market?.india_vix?.last_price != null ? "VIX Proxy" : "Implied Vol")}</span>
          </div>

          {/* 7. TOTAL CALL OI */}
          <div className="flex flex-col gap-0.5 bg-neutral-950/60 border border-neutral-800/80 rounded p-1.5">
            <span className="text-[10px] text-rose-400/90 uppercase tracking-wider">TOTAL CALL OI</span>
            <span className="font-bold text-rose-400 text-[12px] tabular-nums">
              {totalCallOiCr != null ? `${totalCallOiCr.toFixed(2)} Cr` : "—"}
            </span>
            <span className="text-[9px] text-neutral-400">{callRatioPct != null ? `${callRatioPct}% of Total` : "—"}</span>
          </div>

          {/* 8. TOTAL PUT OI */}
          <div className="flex flex-col gap-0.5 bg-neutral-950/60 border border-neutral-800/80 rounded p-1.5">
            <span className="text-[10px] text-emerald-400/90 uppercase tracking-wider">TOTAL PUT OI</span>
            <span className="font-bold text-emerald-400 text-[12px] tabular-nums">
              {totalPutOiCr != null ? `${totalPutOiCr.toFixed(2)} Cr` : "—"}
            </span>
            <span className="text-[9px] text-neutral-400">{putRatioPct != null ? `${putRatioPct}% of Total` : "—"}</span>
          </div>

          {/* 9. OI SKEW / BIAS */}
          <div className="flex flex-col gap-0.5 bg-neutral-950/60 border border-neutral-800/80 rounded p-1.5">
            <span className="text-[10px] text-neutral-400 uppercase tracking-wider">OI SKEW / BIAS</span>
            <span className={`font-bold text-[11px] truncate ${pcr != null && pcr >= 1 ? "text-emerald-400" : pcr != null ? "text-rose-400" : "text-neutral-400"}`}>
              {options?.options_confirmation?.replace(/_/g, " ") || (pcr != null ? (pcr >= 1 ? "BULLISH BIAS" : "BEARISH BIAS") : "AWAITING CHAIN")}
            </span>
            <span className="text-[9px] text-neutral-400">{pcr != null ? (pcr >= 1 ? "Put Writing Lead" : "Call Writing Lead") : "—"}</span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TIER 2: 3-COLUMN COCKPIT GRID (Left 25% | Center 50% | Right 25%)         */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-stretch">
        {/* ----------------------------------------------------------------------- */}
        {/* LEFT COLUMN (lg:col-span-3): POSITIONING MAP                           */}
        {/* ----------------------------------------------------------------------- */}
        <div className="lg:col-span-3 flex flex-col gap-2.5 h-full bg-neutral-900/50 border border-neutral-800 rounded-md p-3">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
            <div className="flex items-center gap-1.5">
              <BarChart2 className="w-3.5 h-3.5 text-cyan-400" />
              <h3 className="text-xs font-bold text-neutral-200 tracking-wider uppercase font-mono">
                Positioning Map
              </h3>
            </div>
            <span className="text-[10px] font-mono text-neutral-400 bg-neutral-800 px-1.5 py-0.5 rounded">
              DERIVATIVES
            </span>
          </div>

          {/* Expiry Selector Dropdown */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-mono text-neutral-400 uppercase">EXPIRY CONTRACT</span>
            <div className="relative">
              <select
                value={selectedExpiry}
                onChange={(e) => setSelectedExpiry(e.target.value)}
                className="w-full bg-neutral-950 border border-neutral-800 rounded px-2.5 py-1.5 text-xs font-mono text-neutral-200 appearance-none cursor-pointer focus:outline-none focus:border-cyan-500"
              >
                {Array.isArray((options as any)?.expiries) && (options as any).expiries.length > 0 ? (
                  (options as any).expiries.map((exp: string, idx: number) => (
                    <option key={exp} value={exp}>
                      {exp} {idx === 0 ? "(Active)" : ""}
                    </option>
                  ))
                ) : (
                  <option value={activeExpiry}>{activeExpiry}</option>
                )}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-neutral-400 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>

          {/* Call vs Put OI Ratio Block */}
          <div className="flex flex-col gap-1.5 bg-neutral-950/70 border border-neutral-800/80 rounded p-2.5 font-mono text-xs">
            <div className="flex justify-between items-center text-[10px]">
              <span className="text-neutral-400">TOTAL OPEN INTEREST</span>
              <span className="text-neutral-200 font-bold">{totalOiCr != null ? `${totalOiCr.toFixed(2)} Cr` : "—"}</span>
            </div>
            {/* Visual Dual-Tone Progress Bar */}
            <div className="w-full h-3 bg-neutral-900 rounded overflow-hidden flex border border-neutral-800">
              <div
                style={{ width: `${callRatioPct || 50}%` }}
                className="h-full bg-rose-500/80 flex items-center justify-center text-[8px] font-bold text-white transition-all"
              >
                {callRatioPct != null ? `CE ${callRatioPct}%` : "CE —"}
              </div>
              <div
                style={{ width: `${putRatioPct || 50}%` }}
                className="h-full bg-emerald-500/80 flex items-center justify-center text-[8px] font-bold text-white transition-all"
              >
                {putRatioPct != null ? `PE ${putRatioPct}%` : "PE —"}
              </div>
            </div>
            <div className="flex justify-between items-center text-[10px] pt-0.5">
              <span className="text-rose-400 font-bold">Calls: {totalCallOiCr != null ? `${totalCallOiCr.toFixed(2)} Cr` : "—"}</span>
              <span className="text-emerald-400 font-bold">Puts: {totalPutOiCr != null ? `${totalPutOiCr.toFixed(2)} Cr` : "—"}</span>
            </div>
          </div>

          {/* Key Concentrations */}
          <div className="flex flex-col gap-2 font-mono text-xs flex-1">
            <span className="text-[10px] text-neutral-400 uppercase tracking-wider font-bold">
              KEY DERIVATIVE CONCENTRATIONS
            </span>

            {/* Call Wall */}
            <div className="flex items-center justify-between p-2 bg-rose-950/20 border border-rose-800/40 rounded">
              <div className="flex flex-col">
                <span className="text-[10px] text-rose-400 font-bold">CALL WALL (RESISTANCE)</span>
                <span className="text-neutral-200 text-xs font-bold tabular-nums">
                  {callWall != null ? callWall.toLocaleString("en-IN") : "—"}
                </span>
              </div>
              <span className="text-[10px] font-bold bg-rose-500/20 border border-rose-500/40 text-rose-300 px-2 py-0.5 rounded">
                {callWall != null && spotPrice != null ? `+${(callWall - spotPrice).toFixed(0)} pts` : "—"}
              </span>
            </div>

            {/* Put Wall */}
            <div className="flex items-center justify-between p-2 bg-emerald-950/20 border border-emerald-800/40 rounded">
              <div className="flex flex-col">
                <span className="text-[10px] text-emerald-400 font-bold">PUT WALL (SUPPORT)</span>
                <span className="text-neutral-200 text-xs font-bold tabular-nums">
                  {putWall != null ? putWall.toLocaleString("en-IN") : "—"}
                </span>
              </div>
              <span className="text-[10px] font-bold bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 px-2 py-0.5 rounded">
                {putWall != null && spotPrice != null ? `${(putWall - spotPrice).toFixed(0)} pts` : "—"}
              </span>
            </div>

            {/* Max Pain Pin */}
            <div className="flex items-center justify-between p-2 bg-amber-950/20 border border-amber-800/40 rounded">
              <div className="flex flex-col">
                <span className="text-[10px] text-amber-400 font-bold">MAX PAIN PIN</span>
                <span className="text-neutral-200 text-xs font-bold tabular-nums">
                  {maxPain != null ? maxPain.toLocaleString("en-IN") : "—"}
                </span>
              </div>
              <span className="text-[10px] font-bold bg-amber-500/20 border border-amber-500/40 text-amber-300 px-2 py-0.5 rounded">
                {maxPain != null && spotPrice != null ? `${(maxPain - spotPrice).toFixed(0)} pts` : "—"}
              </span>
            </div>

            {/* Range Bracket Window */}
            <div className="p-2 bg-neutral-950/80 border border-neutral-800 rounded mt-auto">
              <div className="flex justify-between items-center text-[10px] text-neutral-400">
                <span>ESTABLISHED DERIVATIVES RANGE</span>
                <span className="text-cyan-400 font-bold">{callWall != null && putWall != null ? `${callWall - putWall} PTS` : "—"}</span>
              </div>
              <div className="text-center font-bold text-xs text-neutral-200 mt-0.5">
                {putWall != null && callWall != null ? `${putWall.toLocaleString("en-IN")} – ${callWall.toLocaleString("en-IN")}` : "Awaiting Stream"}
              </div>
            </div>
          </div>
        </div>

        {/* ----------------------------------------------------------------------- */}
        {/* CENTER COLUMN (lg:col-span-6): SMART OPTION CHAIN LADDER               */}
        {/* ----------------------------------------------------------------------- */}
        <div className="lg:col-span-6 flex flex-col h-full bg-neutral-900/50 border border-neutral-800 rounded-md p-3">
          {/* Header with View Controls */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-800 pb-2.5 mb-2 font-mono">
            <div className="flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <h3 className="text-xs font-bold text-neutral-200 tracking-wide uppercase">
                SMART OPTION CHAIN <span className="text-cyan-400 font-normal">[{selectedExpiry || "LIVE"}]</span>
              </h3>
            </div>

            <div className="flex items-center gap-2 text-[10px]">
              {/* Filter: Near ATM vs All */}
              <div className="flex bg-neutral-950 p-0.5 rounded border border-neutral-800">
                <button
                  onClick={() => setStrikeFilterMode("NEAR_ATM")}
                  className={`px-2 py-0.5 rounded font-bold transition-colors ${
                    strikeFilterMode === "NEAR_ATM"
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                      : "text-neutral-400 hover:text-neutral-200"
                  }`}
                >
                  NEAR ATM (±300)
                </button>
                <button
                  onClick={() => setStrikeFilterMode("ALL")}
                  className={`px-2 py-0.5 rounded font-bold transition-colors ${
                    strikeFilterMode === "ALL"
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                      : "text-neutral-400 hover:text-neutral-200"
                  }`}
                >
                  ALL STRIKES
                </button>
              </div>

              {/* View Mode Buttons */}
              <div className="flex bg-neutral-950 p-0.5 rounded border border-neutral-800">
                {(["TABLE", "HEATMAP", "CHANGE"] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => setChainViewMode(m)}
                    className={`px-2 py-0.5 rounded font-bold transition-colors ${
                      chainViewMode === m
                        ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                        : "text-neutral-400 hover:text-neutral-200"
                    }`}
                  >
                    {m === "TABLE" ? "Table" : m === "HEATMAP" ? "OI Heatmap" : "OI Change"}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Option Chain Table Container */}
          <div className="overflow-x-auto flex-1 bg-neutral-950 border border-neutral-800 rounded min-h-[380px] max-h-[460px] flex flex-col justify-center">
            {displayedStrikes.length === 0 ? (
              <div className="p-12 flex flex-col items-center justify-center text-center text-neutral-500 font-mono space-y-2">
                <Layers className="w-8 h-8 text-neutral-700 animate-pulse" />
                <div className="text-xs text-neutral-400 font-bold">Awaiting live derivatives stream / Option chain data</div>
                <div className="text-[10px] text-neutral-600">Option strikes, open interest and Greek metrics will populate upon market connection.</div>
              </div>
            ) : (
            <table className="w-full text-[11px] tabular-nums font-mono border-collapse text-left select-none">
              <thead className="sticky top-0 z-10 bg-neutral-900 border-b border-neutral-800 text-[10px] uppercase font-bold tracking-tight text-neutral-400">
                <tr>
                  <th colSpan={4} className="py-1.5 px-2 text-center text-rose-400 bg-rose-950/30 border-r border-neutral-800">
                    CALLS (CE)
                  </th>
                  <th className="py-1.5 px-2.5 text-center text-cyan-300 bg-neutral-900 border-r border-neutral-800">
                    STRIKE
                  </th>
                  <th colSpan={4} className="py-1.5 px-2 text-center text-emerald-400 bg-emerald-950/30">
                    PUTS (PE)
                  </th>
                </tr>
                <tr className="bg-neutral-950/90 text-neutral-400 border-b border-neutral-800 text-[9.5px]">
                  {chainViewMode === "TABLE" ? (
                    <>
                      <th className="py-1 px-1.5 text-right text-rose-400/90">OI (L)</th>
                      <th className="py-1 px-1.5 text-right text-rose-400/90">ΔOI (L)</th>
                      <th className="py-1 px-1.5 text-right text-neutral-200">LTP (₹)</th>
                      <th className="py-1 px-1.5 text-right text-cyan-400 border-r border-neutral-800">IV (%)</th>
                      <th className="py-1 px-2 text-center text-neutral-200 bg-neutral-900/90 border-r border-neutral-800">STRIKE</th>
                      <th className="py-1 px-1.5 text-left text-cyan-400">IV (%)</th>
                      <th className="py-1 px-1.5 text-left text-neutral-200">LTP (₹)</th>
                      <th className="py-1 px-1.5 text-left text-emerald-400/90">ΔOI (L)</th>
                      <th className="py-1 px-1.5 text-left text-emerald-400/90">OI (L)</th>
                    </>
                  ) : chainViewMode === "HEATMAP" ? (
                    <>
                      <th className="py-1 px-2 text-right text-rose-400">OI (Lakh)</th>
                      <th colSpan={3} className="py-1 px-2 text-right text-rose-400/80 border-r border-neutral-800">
                        CALL CONCENTRATION
                      </th>
                      <th className="py-1 px-2 text-center text-neutral-200 bg-neutral-900/90 border-r border-neutral-800">STRIKE</th>
                      <th colSpan={3} className="py-1 px-2 text-left text-emerald-400/80">
                        PUT CONCENTRATION
                      </th>
                      <th className="py-1 px-2 text-left text-emerald-400">OI (Lakh)</th>
                    </>
                  ) : (
                    <>
                      <th className="py-1 px-2 text-right text-rose-400">CE ΔOI (L)</th>
                      <th colSpan={3} className="py-1 px-2 text-right text-neutral-300 border-r border-neutral-800">
                        CE BUILDUP
                      </th>
                      <th className="py-1 px-2 text-center text-neutral-200 bg-neutral-900/90 border-r border-neutral-800">STRIKE</th>
                      <th colSpan={3} className="py-1 px-2 text-left text-neutral-300">
                        PE BUILDUP
                      </th>
                      <th className="py-1 px-2 text-left text-emerald-400">PE ΔOI (L)</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800/80">
                {displayedStrikes.map((s) => {
                  const strikePx = s.strike;
                  const isAtm = strikePx === atmStrike || s.is_atm;
                  const isCallWallStrike = strikePx === callWall || s.is_call_wall;
                  const isPutWallStrike = strikePx === putWall || s.is_put_wall;
                  const isSelected = strikePx === selectedStrike;

                  // ITM Detection
                  const isCallItm = strikePx < spotPrice;
                  const isPutItm = strikePx > spotPrice;

                  const cOiLakh = (s.ce_oi || 0) / 100000;
                  const cOiChgLakh = (s.ce_oi_change || 0) / 100000;
                  const pOiLakh = (s.pe_oi || 0) / 100000;
                  const pOiChgLakh = (s.pe_oi_change || 0) / 100000;

                  const cHeatPct = Math.min(100, Math.round(((s.ce_oi || 0) / maxOiInUniverse) * 100));
                  const pHeatPct = Math.min(100, Math.round(((s.pe_oi || 0) / maxOiInUniverse) * 100));

                  // Micro-OI Progress Bar widths
                  const cOiBarWidth = Math.min(100, Math.round(((s.ce_oi || 0) / maxOiInUniverse) * 100));
                  const pOiBarWidth = Math.min(100, Math.round(((s.pe_oi || 0) / maxOiInUniverse) * 100));

                  // Spot line at its true position in the ladder (strike just above live spot)
                  const showSpotLineBefore = spotLineStrike != null && strikePx === spotLineStrike;

                  return (
                    <React.Fragment key={strikePx}>
                      {showSpotLineBefore && spotPrice != null && (
                        <tr className="bg-emerald-500/10 border-y-2 border-emerald-500/80">
                          <td colSpan={9} className="py-1 text-center font-bold text-[10px] text-emerald-300 tracking-wider">
                            ─── SPOT: {spotPrice.toLocaleString("en-IN", { minimumFractionDigits: 2 })} {netChange != null && netChangePct != null ? `(${netChange >= 0 ? "+" : ""}${netChange.toFixed(2)} / ${netChangePct >= 0 ? "+" : ""}${netChangePct.toFixed(2)}%)` : ""} ───
                          </td>
                        </tr>
                      )}
                      <tr
                        onClick={() => setSelectedStrike(strikePx)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-cyan-500/20 ring-1 ring-cyan-400"
                            : isAtm
                            ? "bg-amber-500/10"
                            : isCallWallStrike
                            ? "bg-rose-950/20"
                            : isPutWallStrike
                            ? "bg-emerald-950/20"
                            : "hover:bg-neutral-900/60"
                        }`}
                      >
                        {chainViewMode === "TABLE" ? (
                          <>
                            {/* CE Columns with ITM Shading & Micro-OI Bar */}
                            <td className={`py-1.5 px-1.5 text-right font-bold relative overflow-hidden ${
                              isCallItm ? "bg-neutral-900/60" : "bg-neutral-950"
                            }`}>
                              <div
                                style={{ width: `${cOiBarWidth}%` }}
                                className="absolute top-0 right-0 h-full bg-rose-500/15 pointer-events-none"
                              />
                              <span className="relative z-10 text-neutral-200">{cOiLakh.toFixed(2)}</span>
                            </td>
                            <td className={`py-1.5 px-1.5 text-right font-bold ${
                              isCallItm ? "bg-neutral-900/60" : "bg-neutral-950"
                            } ${cOiChgLakh >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                              {cOiChgLakh >= 0 ? "+" : ""}{cOiChgLakh.toFixed(2)}
                            </td>
                            <td className={`py-1.5 px-1.5 text-right font-bold text-neutral-100 ${
                              isCallItm ? "bg-neutral-900/60" : "bg-neutral-950"
                            }`}>
                              {s.ce_ltp != null ? s.ce_ltp.toFixed(2) : "—"}
                            </td>
                            <td className={`py-1.5 px-1.5 text-right text-cyan-300/90 border-r border-neutral-800 ${
                              isCallItm ? "bg-neutral-900/60" : "bg-neutral-950"
                            }`}>
                              {s.ce_iv != null ? `${s.ce_iv.toFixed(1)}%` : "—"}
                            </td>

                            {/* Center Strike Column */}
                            <td className={`py-1.5 px-2 text-center font-bold border-r border-neutral-800 bg-neutral-900/90 ${
                              isAtm
                                ? "text-amber-300"
                                : isCallWallStrike
                                ? "text-rose-400"
                                : isPutWallStrike
                                ? "text-emerald-400"
                                : "text-neutral-200"
                            }`}>
                              <div className="flex items-center justify-center gap-1">
                                <span>{strikePx.toLocaleString("en-IN")}</span>
                                {isAtm && (
                                  <span className="bg-amber-500/10 border border-amber-500/80 text-amber-300 text-[8px] px-1 py-0.2 rounded font-bold">
                                    ATM
                                  </span>
                                )}
                                {isCallWallStrike && (
                                  <span className="bg-rose-500/15 border border-rose-500/40 text-rose-400 text-[8px] px-1 py-0.2 rounded font-bold">
                                    CALL WALL
                                  </span>
                                )}
                                {isPutWallStrike && (
                                  <span className="bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 text-[8px] px-1 py-0.2 rounded font-bold">
                                    PUT WALL
                                  </span>
                                )}
                              </div>
                            </td>

                            {/* PE Columns with ITM Shading & Micro-OI Bar */}
                            <td className={`py-1.5 px-1.5 text-left text-cyan-300/90 ${
                              isPutItm ? "bg-neutral-900/60" : "bg-neutral-950"
                            }`}>
                              {s.pe_iv != null ? `${s.pe_iv.toFixed(1)}%` : "—"}
                            </td>
                            <td className={`py-1.5 px-1.5 text-left font-bold text-neutral-100 ${
                              isPutItm ? "bg-neutral-900/60" : "bg-neutral-950"
                            }`}>
                              {s.pe_ltp != null ? s.pe_ltp.toFixed(2) : "—"}
                            </td>
                            <td className={`py-1.5 px-1.5 text-left font-bold ${
                              isPutItm ? "bg-neutral-900/60" : "bg-neutral-950"
                            } ${pOiChgLakh >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                              {pOiChgLakh >= 0 ? "+" : ""}{pOiChgLakh.toFixed(2)}
                            </td>
                            <td className={`py-1.5 px-1.5 text-left font-bold relative overflow-hidden ${
                              isPutItm ? "bg-neutral-900/60" : "bg-neutral-950"
                            }`}>
                              <div
                                style={{ width: `${pOiBarWidth}%` }}
                                className="absolute top-0 left-0 h-full bg-emerald-500/15 pointer-events-none"
                              />
                              <span className="relative z-10 text-neutral-200">{pOiLakh.toFixed(2)}</span>
                            </td>
                          </>
                        ) : chainViewMode === "HEATMAP" ? (
                          <>
                            <td className="py-1.5 px-2 text-right font-bold text-neutral-200">
                              {cOiLakh.toFixed(2)}
                            </td>
                            <td colSpan={3} className="py-1.5 px-2 text-right border-r border-neutral-800 pr-2">
                              <div className="w-full bg-neutral-900 h-3 rounded overflow-hidden flex justify-end">
                                <div style={{ width: `${cHeatPct}%` }} className="h-full bg-rose-500/80 rounded" />
                              </div>
                            </td>

                            {/* Strike Center */}
                            <td className={`py-1.5 px-2 text-center font-bold border-r border-neutral-800 bg-neutral-900/90 ${
                              isAtm ? "text-amber-300" : "text-neutral-200"
                            }`}>
                              <div className="flex items-center justify-center gap-1">
                                <span>{strikePx.toLocaleString("en-IN")}</span>
                                {isAtm && <span className="bg-amber-500/20 text-amber-300 text-[8px] px-1 rounded">ATM</span>}
                              </div>
                            </td>

                            <td colSpan={3} className="py-1.5 px-2 text-left pl-2">
                              <div className="w-full bg-neutral-900 h-3 rounded overflow-hidden flex justify-start">
                                <div style={{ width: `${pHeatPct}%` }} className="h-full bg-emerald-500/80 rounded" />
                              </div>
                            </td>
                            <td className="py-1.5 px-2 text-left font-bold text-neutral-200">
                              {pOiLakh.toFixed(2)}
                            </td>
                          </>
                        ) : (
                          <>
                            <td className={`py-1.5 px-2 text-right font-bold ${cOiChgLakh >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                              {cOiChgLakh >= 0 ? "+" : ""}{cOiChgLakh.toFixed(2)}
                            </td>
                            <td colSpan={3} className="py-1.5 px-2 text-right border-r border-neutral-800">
                              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                s.ce_buildup === "LONG_BUILDUP"
                                  ? "bg-emerald-500/15 text-emerald-400"
                                  : s.ce_buildup === "HEAVY_CALL_WRITING" || s.ce_buildup === "SHORT_BUILDUP"
                                  ? "bg-rose-500/15 text-rose-400"
                                  : "bg-neutral-800 text-neutral-400"
                              }`}>
                                {s.ce_buildup.replace(/_/g, " ")}
                              </span>
                            </td>

                            {/* Strike Center */}
                            <td className="py-1.5 px-2 text-center font-bold border-r border-neutral-800 bg-neutral-900/90 text-neutral-200">
                              {strikePx.toLocaleString("en-IN")}
                            </td>

                            <td colSpan={3} className="py-1.5 px-2 text-left">
                              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                s.pe_buildup === "AGGRESSIVE_WRITING" || s.pe_buildup === "SHORT_BUILDUP"
                                  ? "bg-emerald-500/15 text-emerald-400"
                                  : s.pe_buildup === "LONG_UNWINDING" || s.pe_buildup === "SHORT_COVERING"
                                  ? "bg-rose-500/15 text-rose-400"
                                  : "bg-neutral-800 text-neutral-400"
                              }`}>
                                {s.pe_buildup.replace(/_/g, " ")}
                              </span>
                            </td>
                            <td className={`py-1.5 px-2 text-left font-bold ${pOiChgLakh >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                              {pOiChgLakh >= 0 ? "+" : ""}{pOiChgLakh.toFixed(2)}
                            </td>
                          </>
                        )}
                      </tr>
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
            )}
          </div>

          <div className="flex justify-between items-center text-[10px] font-mono text-neutral-400 px-1 pt-1">
            <span>Click any strike row to inspect Call/Put Greeks and positioning delta</span>
            <span>Data: NSE NIFTY 50 Options · Sub-second Stream</span>
          </div>
        </div>

        {/* ----------------------------------------------------------------------- */}
        {/* RIGHT COLUMN (lg:col-span-3): OPTIONS INSPECTOR & SETUP                 */}
        {/* ----------------------------------------------------------------------- */}
        <div className="lg:col-span-3 flex flex-col gap-2.5 h-full">
          {/* Sub-Card 1: SELECTED STRIKE INSPECTOR */}
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-md p-3 flex flex-col gap-2 font-mono">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
              <div className="flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                <h3 className="text-xs font-bold text-neutral-200 tracking-wider uppercase">
                  Strike Inspector
                </h3>
              </div>
              <span className="text-[10px] text-cyan-300 font-bold bg-cyan-500/10 border border-cyan-500/30 px-1.5 py-0.5 rounded">
                {selectedStrike != null ? selectedStrike.toLocaleString("en-IN") : "—"} {selectedStrike != null && selectedStrike === atmStrike ? "(ATM)" : ""}
              </span>
            </div>

            {selectedStrikeRow ? (
              <>
                {/* Selected Strike Hero */}
                <div className="flex justify-between items-center bg-neutral-950 p-2 rounded border border-neutral-800/80 text-xs">
                  <span className="text-neutral-400">Distance from Spot:</span>
                  <span className={`font-bold tabular-nums ${(selectedDist ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {selectedDist != null ? `${selectedDist >= 0 ? "+" : ""}${selectedDist.toFixed(2)} pts (${selectedDist >= 0 ? "+" : ""}${(selectedDistPct ?? 0).toFixed(2)}%)` : "—"}
                  </span>
                </div>

                {/* Side-by-Side Call vs Put Metrics */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {/* Call Side */}
                  <div className="bg-rose-950/20 border border-rose-900/40 rounded p-2 flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-rose-400 border-b border-rose-900/40 pb-1">
                      CALL (CE)
                    </span>
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="text-neutral-400">LTP:</span>
                      <span className="font-bold text-neutral-100 tabular-nums">
                        ₹{selectedStrikeRow.ce_ltp != null ? selectedStrikeRow.ce_ltp.toFixed(2) : "—"}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="text-neutral-400">OI:</span>
                      <span className="font-bold text-neutral-200 tabular-nums">
                        {((selectedStrikeRow.ce_oi || 0) / 100000).toFixed(2)} L
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="text-neutral-400">IV:</span>
                      <span className="font-bold text-cyan-400 tabular-nums">
                        {selectedStrikeRow.ce_iv != null ? `${selectedStrikeRow.ce_iv.toFixed(1)}%` : "—"}
                      </span>
                    </div>
                  </div>

                  {/* Put Side */}
                  <div className="bg-emerald-950/20 border border-emerald-900/40 rounded p-2 flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-emerald-400 border-b border-emerald-900/40 pb-1">
                      PUT (PE)
                    </span>
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="text-neutral-400">LTP:</span>
                      <span className="font-bold text-neutral-100 tabular-nums">
                        ₹{selectedStrikeRow.pe_ltp != null ? selectedStrikeRow.pe_ltp.toFixed(2) : "—"}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="text-neutral-400">OI:</span>
                      <span className="font-bold text-neutral-200 tabular-nums">
                        {((selectedStrikeRow.pe_oi || 0) / 100000).toFixed(2)} L
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="text-neutral-400">IV:</span>
                      <span className="font-bold text-cyan-400 tabular-nums">
                        {selectedStrikeRow.pe_iv != null ? `${selectedStrikeRow.pe_iv.toFixed(1)}%` : "—"}
                      </span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="py-6 text-center text-neutral-500 font-mono text-[10px]">
                Awaiting option chain strike selection
              </div>
            )}
          </div>

          {/* Sub-Card 2: TRADE SETUP & DERIVATIVE CANDIDATE */}
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-md p-3 flex flex-col gap-2 font-mono flex-1">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
              <div className="flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-cyan-400" />
                <h3 className="text-xs font-bold text-neutral-200 tracking-wider uppercase">
                  Primary Candidate
                </h3>
              </div>
              <span className="text-[9px] text-neutral-400 bg-neutral-800 px-1.5 py-0.5 rounded">
                ADVISORY
              </span>
            </div>

            {candidateStrikeInfo ? (
              <>
                {/* Candidate Header */}
                <div className="flex items-center justify-between bg-cyan-950/20 border border-cyan-800/40 p-2 rounded text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-cyan-300 text-sm">
                      {candidateStrikeInfo.cand.strike} {candidateStrikeInfo.cand.option_type}
                    </span>
                    <span className="text-[9px] bg-cyan-500/20 text-cyan-300 px-1 py-0.2 rounded font-bold">
                      {candidateStrikeInfo.cand.option_type === "CE" ? "CALL OPTION" : "PUT OPTION"}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-neutral-400 block">LTP</span>
                    <span className="text-sm font-bold text-neutral-100 tabular-nums">
                      ₹{candidateStrikeInfo.cand.ltp?.toFixed(2) || "—"}
                    </span>
                  </div>
                </div>

                {/* Key Candidate Metrics */}
                <div className="grid grid-cols-3 gap-1.5 text-center text-[10px]">
                  <div className="bg-neutral-950 p-1.5 rounded border border-neutral-800">
                    <span className="text-neutral-400 block">LIQUIDITY</span>
                    <span className="text-emerald-400 font-bold">{candidateStrikeInfo.cand.liquidity || "HIGH"}</span>
                  </div>
                  <div className="bg-neutral-950 p-1.5 rounded border border-neutral-800">
                    <span className="text-neutral-400 block">STRENGTH</span>
                    <span className="text-cyan-300 font-bold">{candidateStrikeInfo.cand.strength || "STRONG"}</span>
                  </div>
                  <div className="bg-neutral-950 p-1.5 rounded border border-neutral-800">
                    <span className="text-neutral-400 block">SPOT DISTANCE</span>
                    <span className="text-emerald-400 font-bold tabular-nums">
                      {candidateStrikeInfo.distanceLabel}
                    </span>
                  </div>
                </div>

                {/* Why Candidate & Risk */}
                <div className="flex flex-col gap-1.5 text-[11px] pt-1">
                  <div className="bg-neutral-950/80 p-2 rounded border border-neutral-800/80">
                    <span className="text-[10px] text-cyan-400 font-bold block mb-0.5">RATIONALE</span>
                    <p className="text-neutral-300 text-[10.5px] leading-relaxed">
                      {candidateStrikeInfo.cand.rationale?.[0] || "Targeting breakout confirmation aligned with underlying momentum."}
                    </p>
                  </div>
                  <div className="bg-neutral-950/80 p-2 rounded border border-neutral-800/80">
                    <span className="text-[10px] text-rose-400 font-bold block mb-0.5">KEY RISK</span>
                    <p className="text-neutral-400 text-[10.5px] leading-relaxed">
                      {candidateStrikeInfo.cand.risks?.[0] || "Loss of opening support invalidates setup."}
                    </p>
                  </div>
                </div>
              </>
            ) : (
              <div className="py-8 text-center text-neutral-500 font-mono text-[10.5px]">
                Awaiting derivative candidate generation from live market decision window
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TIER 3: DERIVATIVES EVIDENCE & STRUCTURE SUMMARY (Full-Width Bottom Grid)  */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {/* Left Card: WHAT CHANGED (DERIVATIVES EVIDENCE) */}
        <div className="bg-neutral-900/50 border border-neutral-800 rounded-md p-3 flex flex-col gap-2 font-mono">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
            <div className="flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
              <h3 className="text-xs font-bold text-neutral-200 tracking-wider uppercase">
                What Changed (Derivatives Evidence)
              </h3>
            </div>
            <span className="text-[10px] text-emerald-400 bg-emerald-950/30 border border-emerald-800/40 px-1.5 py-0.5 rounded font-bold">
              {isReplayMode ? "VERIFIED TAPE" : (isDataAvailable ? "LIVE DERIVATIVES" : "STANDBY")}
            </span>
          </div>

          {isDataAvailable ? (
            <div className="flex flex-col gap-1.5 text-xs text-neutral-300 pt-1">
              <div className="flex items-start gap-2 bg-neutral-950/60 p-2 rounded border border-neutral-800/80">
                <span className="text-rose-400 font-bold">•</span>
                <div>
                  <strong className="text-neutral-400 text-[10.5px] mr-1">WALL STATUS:</strong>
                  <span className="text-rose-400 font-bold">{callWall != null ? `${callWall.toLocaleString("en-IN")} CE Call Wall` : "Call Wall Forming"}</span>
                  <span className="text-neutral-400 mx-1">|</span>
                  <span className="text-emerald-400 font-bold">{putWall != null ? `${putWall.toLocaleString("en-IN")} PE Put Wall` : "Put Wall Forming"}</span>
                </div>
              </div>
              <div className="flex items-start gap-2 bg-neutral-950/60 p-2 rounded border border-neutral-800/80">
                <span className="text-emerald-400 font-bold">•</span>
                <div>
                  <strong className="text-neutral-400 text-[10.5px] mr-1">PCR BIAS:</strong>
                  <span className="text-neutral-200">{pcr != null ? `PCR at ${pcr.toFixed(2)} indicating ${pcr >= 1 ? "supportive Put writing" : "overhead Call pressure"}` : "Awaiting calculation"}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-6 text-center text-neutral-500 font-mono text-xs">
              Awaiting live option chain stream to evaluate derivatives buildup and institutional walls.
            </div>
          )}
        </div>

        {/* Right Card: STRIKE STRUCTURE SUMMARY */}
        <div className="bg-neutral-900/50 border border-neutral-800 rounded-md p-3 flex flex-col gap-2 font-mono">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <h3 className="text-xs font-bold text-neutral-200 tracking-wider uppercase">
                Strike Structure Summary
              </h3>
            </div>
            <span className="text-[10px] text-cyan-400 bg-neutral-800 px-1.5 py-0.5 rounded">
              3-PILLAR STRUCTURE
            </span>
          </div>

          {/* 3-Column Snapshot */}
          <div className="grid grid-cols-3 gap-2 pt-1">
            {/* PUT SUPPORT */}
            <div className="bg-emerald-950/20 border border-emerald-800/40 rounded p-2 text-center flex flex-col gap-0.5">
              <span className="text-[10px] text-emerald-400 font-bold">PUT SUPPORT</span>
              <span className="text-sm font-bold text-neutral-100 tabular-nums">{putWall != null ? putWall.toLocaleString("en-IN") : "—"}</span>
              <span className="text-[9px] text-emerald-400">{putWall != null && spotPrice != null ? `${(putWall - spotPrice).toFixed(0)} pts` : "—"}</span>
            </div>

            {/* SPOT / ATM */}
            <div className="bg-amber-950/20 border border-amber-800/40 rounded p-2 text-center flex flex-col gap-0.5">
              <span className="text-[10px] text-amber-400 font-bold">SPOT / ATM</span>
              <span className="text-sm font-bold text-neutral-100 tabular-nums">
                {spotPrice != null ? spotPrice.toLocaleString("en-IN", { minimumFractionDigits: 2 }) : "—"} / {atmStrike != null ? atmStrike.toLocaleString("en-IN") : "—"}
              </span>
              <span className="text-[9px] text-amber-400">Max Pain: {maxPain != null ? maxPain.toLocaleString("en-IN") : "—"}</span>
            </div>

            {/* CALL RESISTANCE */}
            <div className="bg-rose-950/20 border border-rose-800/40 rounded p-2 text-center flex flex-col gap-0.5">
              <span className="text-[10px] text-rose-400 font-bold">CALL RESISTANCE</span>
              <span className="text-sm font-bold text-neutral-100 tabular-nums">{callWall != null ? callWall.toLocaleString("en-IN") : "—"}</span>
              <span className="text-[9px] text-rose-400">{callWall != null && spotPrice != null ? `+${(callWall - spotPrice).toFixed(0)} pts` : "—"}</span>
            </div>
          </div>

          {/* Footer Strip */}
          <div className="bg-neutral-950 p-2 rounded border border-neutral-800 text-[11px] flex justify-between items-center text-neutral-300 mt-auto">
            <span>PCR: <strong className={pcr != null && pcr >= 1 ? "text-emerald-400" : (pcr != null ? "text-rose-400" : "text-neutral-400")}>{pcr != null ? pcr.toFixed(2) : "—"}</strong></span>
            <span>OI Skew: <strong className={pcr != null && pcr >= 1 ? "text-emerald-400" : (pcr != null ? "text-rose-400" : "text-neutral-400")}>
              {options?.options_confirmation?.replace(/_/g, " ") || (pcr != null ? (pcr >= 1 ? "BULLISH CONFIRMATION" : "BEARISH BIAS") : (isDataAvailable ? "BALANCED" : "STANDBY"))}
            </strong></span>
            <span>Range: <strong className="text-cyan-300">{putWall != null && callWall != null ? `${putWall.toLocaleString("en-IN")} – ${callWall.toLocaleString("en-IN")}` : "—"}</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OptionsIntelligenceWorkspace;
