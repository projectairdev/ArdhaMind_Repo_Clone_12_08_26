/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Flagship NIFTY Institutional Hero Telemetry Strip.
 * Premium Bloomberg/Terminal-grade layout:
 * - Asset Index Identity separated from large Spotlight Spot Price
 * - Dynamic pulse indicator with precise market phase and spot source badge
 * - Borderless floating telemetry ribbon with hairline dividers
 * - Fully envelope-bound & zero hardcoded data
 */

import React from "react";
import { CanonicalFrontendEnvelope, MarketPhase } from "../../../types/canonical";
import { formatNumber } from "../../../utils/safeHelpers";
import { resolveAuthoritativeMarketState } from "../../../utils/resolveAuthoritativeMarketState";
import { useCanonicalState } from "../../../context/CanonicalStateContext";
import { DataFreshnessBadge } from "../../ui/DataFreshnessBadge";

export interface NiftyHeaderProps {
  envelope?: CanonicalFrontendEnvelope;
  marketPhase?: MarketPhase | string;
  spot?: number | null;
  spotSource?: "LIVE" | "AUCTION" | "OPTIONS" | "CANDLE" | "SETTLED";
  settledClose?: number | null;
  settledHigh?: number | null;
  settledLow?: number | null;
  settledVwap?: number | null;
  settledRange?: number | null;
  displayVix?: number | null;
  change?: number | null;
  changePercent?: number | null;
}

export const NiftyHeader: React.FC<NiftyHeaderProps> = ({
  envelope,
  marketPhase,
  spot,
  spotSource,
  settledClose,
  settledHigh,
  settledLow,
  settledVwap,
  settledRange,
  displayVix,
  change,
  changePercent,
}) => {
  let isDisconnected = false;
  try {
    const { isConnected } = useCanonicalState();
    isDisconnected = !isConnected;
  } catch {
    // Context may not be mounted in standalone tests
  }

  const session = envelope?.session;
  const market = envelope?.market;
  const niftyObservedAt =
    market?.nifty?.exchange_timestamp ??
    market?.observed_at ??
    (envelope as any)?.market_observed_at ??
    null;
  const price_structure = envelope?.price_structure;
  const settled = envelope?.settled_session;
  const authState = envelope ? resolveAuthoritativeMarketState(envelope) : ({} as any);

  const activePhase = (marketPhase ?? session?.market_phase ?? "PRE_MARKET") as string;
  const isPreMarket = activePhase === "PRE_MARKET";
  const isPreOpen = activePhase === "PRE_OPEN";
  const isLive = activePhase === "LIVE" || activePhase === "MARKET_OPEN" || activePhase === "OPENING_RANGE";
  const isNearClose = activePhase === "NEAR_CLOSE";
  const isPostMarket = activePhase === "POST_MARKET" || activePhase === "MARKET_CLOSED";

  const resolvedSpot = spot ?? authState.spot ?? market?.nifty?.last_price ?? price_structure?.last_price ?? settled?.close ?? null;
  const resolvedSpotSource = spotSource ?? authState.spotSource ?? (market?.nifty?.last_price ? "LIVE" : "SETTLED");
  const resolvedChange = change ?? authState.change ?? market?.nifty?.change ?? price_structure?.change ?? null;
  const resolvedChangePct = changePercent ?? authState.changePercent ?? authState.changePct ?? market?.nifty?.change_pct ?? price_structure?.change_pct ?? null;

  const resolvedSettledClose =
    settledClose ??
    (isPreMarket || isPreOpen
      ? (authState.spot ?? market?.nifty?.last_price ?? settled?.close)
      : (settled?.close ?? authState.prevClose ?? market?.nifty?.previous_close)) ??
    null;

  const isLiveTape = isLive || isNearClose;
  const resolvedLiveHigh = authState.dayHigh ?? market?.nifty?.high ?? price_structure?.high ?? null;
  const resolvedLiveLow = authState.dayLow ?? market?.nifty?.low ?? price_structure?.low ?? null;
  const resolvedSettledHigh = isLiveTape
    ? resolvedLiveHigh
    : (settledHigh ?? authState.dayHigh ?? price_structure?.high ?? settled?.high ?? null);
  const resolvedSettledLow = isLiveTape
    ? resolvedLiveLow
    : (settledLow ?? authState.dayLow ?? price_structure?.low ?? settled?.low ?? null);
  const resolvedSettledVwap = isLiveTape
    ? (authState.vwap ?? price_structure?.vwap ?? null)
    : (settledVwap ?? authState.vwap ?? price_structure?.vwap ?? settled?.vwap ?? null);
  const resolvedSettledRange =
    (resolvedSettledHigh != null && resolvedSettledLow != null)
      ? Number((resolvedSettledHigh - resolvedSettledLow).toFixed(1))
      : (isLiveTape ? null : (settledRange ?? price_structure?.range_points ?? settled?.range_points ?? null));

  const rawVix =
    authState.vix ??
    market?.vix?.last_price ??
    market?.vix?.previous_close ??
    (typeof settled?.closing_vix === "object" ? (settled.closing_vix as any)?.vix_close : settled?.closing_vix) ??
    (typeof (settled as any)?.vix === "object" ? (settled as any)?.vix?.vix_close : (settled as any)?.vix) ??
    null;

  const resolvedDisplayVix = displayVix ?? rawVix ?? null;
  const isPositive = (resolvedChange ?? 0) >= 0;

  const phaseLabel = isPreMarket
    ? "AWAITING OPEN"
    : isPreOpen
    ? "PRE-OPEN INDICATIVE"
    : isNearClose
    ? "NEAR CLOSE"
    : isPostMarket
    ? "SESSION CLOSED"
    : "LIVE SESSION";

  const pulseColor = isLive
    ? "bg-emerald-400"
    : isPreOpen
    ? "bg-amber-400"
    : isPostMarket
    ? "bg-purple-400"
    : "bg-cyan-400";

  const pulseCoreColor = isLive
    ? "bg-emerald-500"
    : isPreOpen
    ? "bg-amber-500"
    : isPostMarket
    ? "bg-purple-500"
    : "bg-cyan-500";

  return (
    <header className="relative w-full bg-[#0E1013] border border-[#1E232B] rounded-[3px] px-3.5 py-2.5 flex flex-wrap items-center justify-between gap-4 select-none font-mono">
      {/* Feed Disconnected Overlay */}
      {isDisconnected && (
        <div
          data-testid="feed-disconnected-watermark"
          className="absolute inset-0 z-30 bg-black/60 backdrop-blur-[1px] rounded flex items-center justify-center pointer-events-none"
        >
          <div className="border border-[#E5484D] bg-[#E5484D]/25 px-3 py-1 rounded text-[11px] font-black tracking-widest text-[#E5484D] uppercase shadow-2xl">
            FEED DISCONNECTED
          </div>
        </div>
      )}

      {/* ── LEFT: ASSET IDENTITY & SPOT SPOTLIGHT ── */}
      <div className="flex items-center gap-3.5 flex-wrap">
        {/* Asset Identity Block */}
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-mono font-bold tracking-widest text-cyan-400 uppercase bg-cyan-950/40 border border-cyan-800/40 px-1.5 py-0.2 rounded">
              INDEX
            </span>
            <h1 className="text-xs font-black font-mono tracking-wider text-neutral-200 uppercase">
              {isPreOpen ? "INDICATIVE NIFTY" : "NIFTY 50"}
            </h1>
          </div>

          {/* Phase / Market State Capsule */}
          <div className="mt-1 flex items-center gap-1.5 flex-wrap">
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${pulseColor}`} />
              <span className={`relative inline-flex rounded-full h-2 w-2 ${pulseCoreColor}`} />
            </span>
            <span className="text-[9.5px] font-mono font-bold tracking-wider text-neutral-400 uppercase">
              {phaseLabel}
            </span>

            {/* Source Sub-Badge During Live Warmup */}
            {isLive && resolvedSpotSource === "AUCTION" && (
              <span className="px-1.5 py-0.2 rounded text-[8.5px] font-bold tracking-wider text-amber-300 bg-amber-500/15 border border-amber-500/30 uppercase animate-pulse">
                AUCTION DISCOVERY PRINT
              </span>
            )}
            {isLive && resolvedSpotSource === "OPTIONS" && (
              <span className="px-1.5 py-0.2 rounded text-[8.5px] font-bold tracking-wider text-cyan-300 bg-cyan-500/15 border border-cyan-500/30 uppercase animate-pulse">
                SYNTHETIC SPOT
              </span>
            )}

            {/* Data freshness — sourced from the real tick exchange timestamp, not render time */}
            <DataFreshnessBadge
              observedAt={niftyObservedAt}
              kind={isLive || isNearClose ? "realtime" : "periodic"}
              label={isLive || isNearClose ? "Ticks" : "Last tick"}
            />
          </div>
        </div>

        {/* Elegant Hairline Divider */}
        <div className="h-8 w-px bg-neutral-800/80 hidden sm:block" />

        {/* Spot Price Display */}
        <div className="flex items-baseline gap-2.5">
          <span className="text-2xl lg:text-3xl font-black font-mono tracking-tight text-white drop-shadow-[0_2px_10px_rgba(255,255,255,0.08)]">
            {resolvedSpot != null ? formatNumber(resolvedSpot, 2) : "—"}
          </span>

          {/* Session Price Delta (When active change exists) */}
          {resolvedChange != null && (
            <div className={`flex items-center text-xs font-mono font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
              <span>{isPositive ? "+" : ""}{formatNumber(resolvedChange, 2)}</span>
              {resolvedChangePct != null && (
                <span className="ml-1 text-[11px] opacity-80">
                  ({isPositive ? "+" : ""}{formatNumber(resolvedChangePct, 2)}%)
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── RIGHT: MODERN INSTITUTIONAL TELEMETRY RIBBON (BORDERLESS WITH HAIRLINE DIVIDERS) ── */}
      <div className="flex items-center gap-4 lg:gap-6 font-mono flex-wrap">
        {/* Prev Close */}
        <div className="flex flex-col items-end">
          <span className="text-[9.5px] uppercase tracking-widest text-neutral-500 font-semibold">
            Prev Close
          </span>
          <span className="text-xs lg:text-sm font-bold text-neutral-200 mt-0.5">
            {resolvedSettledClose != null ? `₹${formatNumber(resolvedSettledClose, 2)}` : "—"}
          </span>
        </div>

        <div className="h-6 w-px bg-neutral-800/80" />

        {/* Settled Range & High / Low Extents */}
        <div className="flex flex-col items-end">
          <div className="flex items-center gap-1.5">
            <span className="text-[9.5px] uppercase tracking-widest text-neutral-500 font-semibold">
              Range
            </span>
            <span className="text-xs font-bold text-cyan-400">
              {resolvedSettledRange != null ? `${formatNumber(resolvedSettledRange, 1)} pts` : "—"}
            </span>
          </div>
          <div className="text-[10.5px] text-neutral-400 flex items-center gap-1 mt-0.5">
            <span className="text-neutral-500">H:</span>
            <span className="text-neutral-300">{resolvedSettledHigh != null ? formatNumber(resolvedSettledHigh, 1) : "—"}</span>
            <span className="text-neutral-600 mx-0.5">/</span>
            <span className="text-neutral-500">L:</span>
            <span className="text-neutral-300">{resolvedSettledLow != null ? formatNumber(resolvedSettledLow, 1) : "—"}</span>
          </div>
        </div>

        <div className="h-6 w-px bg-neutral-800/80" />

        {/* Settled VWAP */}
        <div className="flex flex-col items-end">
          <span className="text-[9.5px] uppercase tracking-widest text-neutral-500 font-semibold">
            Settled VWAP
          </span>
          <span className="text-xs lg:text-sm font-bold text-amber-400 mt-0.5">
            {resolvedSettledVwap != null ? `₹${formatNumber(resolvedSettledVwap, 2)}` : "—"}
          </span>
        </div>

        <div className="h-6 w-px bg-neutral-800/80" />

        {/* India VIX */}
        <div className="flex flex-col items-end">
          <span className="text-[9.5px] uppercase tracking-widest text-neutral-500 font-semibold">
            India VIX
          </span>
          <span className="text-xs lg:text-sm font-bold text-neutral-200 mt-0.5">
            {resolvedDisplayVix != null ? formatNumber(resolvedDisplayVix, 2) : "—"}
          </span>
          {resolvedDisplayVix == null && <span className="sr-only">VIX Unavailable</span>}
        </div>
      </div>
    </header>
  );
};
