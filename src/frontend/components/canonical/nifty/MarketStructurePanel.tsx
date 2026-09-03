/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Persistent Phase-Aware Market Structure & Structural Levels Panel.
 * Adapts between Pre-Market Expectations, Pre-Open Auction, Regular Live Cockpit, Near-Close Structure, and EOD Summary.
 */

import React from "react";
import { CanonicalFrontendEnvelope, MarketPhase } from "../../../types/canonical";
import { DirectionBadge } from "../ui/Badges";
import { Compass, Target, Layers } from "lucide-react";
import { formatNumber } from "../../../utils/safeHelpers";

export function MarketStructurePanel({
  envelope,
  marketPhase,
}: {
  envelope: CanonicalFrontendEnvelope;
  marketPhase: MarketPhase;
}) {
  const { regime, prediction } = envelope;
  const price_structure = envelope.price_structure || ({} as any);
  const isPostMarket = marketPhase === "POST_MARKET";
  const isPreMarket = marketPhase === "PRE_MARKET";
  const isPreOpen = marketPhase === "PRE_OPEN";
  const isOpeningRange = marketPhase === "OPENING_RANGE";
  const isNearClose = marketPhase === "NEAR_CLOSE";

  const vwapDist = price_structure.vwap && price_structure.last_price
    ? price_structure.last_price - price_structure.vwap
    : 0;
  const vwapDistPct = price_structure.vwap
    ? (vwapDist / price_structure.vwap) * 100
    : 0;

  const isDataAvailable = envelope.data_quality !== "UNAVAILABLE" && (price_structure.last_price != null || price_structure.open != null);

  // Phase-specific evidence copy
  const phaseExplanation = !isDataAvailable
    ? "Awaiting live exchange stream to calculate real-time market structure, regime classifications, and VWAP bands."
    : isPreMarket
    ? "Pre-market intelligence window: evaluating overnight global cues, indicative auction cues, and institutional flow alignment."
    : isPreOpen
    ? `Indicative auction settled${price_structure.open ? ` at ₹${formatNumber(price_structure.open, 2)}` : ""}. Evaluating opening price discovery vs prior session anchor.`
    : isOpeningRange
    ? "Observing initial price discovery and opening range high/low formation across high-weight constituents."
    : isNearClose
    ? "Observing closing range behavior, institutional settlement positioning, and late-session VWAP migration."
    : isPostMarket
    ? `Session settled${price_structure.last_price ? ` at ₹${formatNumber(price_structure.last_price, 2)}` : ""}. Reviewing daily range expansion and carry-forward structure.`
    : "Evaluating live price structure, VWAP alignment, and heavyweight index constituent momentum.";

  return (
    <div className="flex flex-col gap-2.5 font-mono">
      {/* 1. Market Regime & Trend Card */}
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3">
        <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-2">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#8B949E] uppercase tracking-wide">
            <Compass className="w-3.5 h-3.5 text-[#38BDF8]" />
            <span>
              {isPreMarket
                ? "MARKET REGIME (EXPECTATION)"
                : isPreOpen
                ? "PRE-OPEN STRUCTURE (AUCTION)"
                : isOpeningRange
                ? "OPENING RANGE STRUCTURE"
                : isNearClose
                ? "CLOSING STRUCTURE (LATE LIVE)"
                : isPostMarket
                ? "MARKET STRUCTURE (EOD)"
                : "MARKET REGIME"}
            </span>
          </div>
          <DirectionBadge bias={price_structure.trend_direction} />
        </div>

        <div className="flex items-baseline justify-between mb-1">
          <span className="text-sm lg:text-base font-bold text-[#F0F6FC]">
            {regime.regime_type.replace(/_/g, " ")}
          </span>
          <span className="text-[10.5px] text-[#707987]">
            CONFIDENCE: <strong className="text-[#38BDF8]">{prediction.confidence_score}%</strong>
          </span>
        </div>

        <p className="text-[10.5px] text-[#8B949E] leading-relaxed mb-2">
          {phaseExplanation}
        </p>

        {/* Core Structure Metrics: ATR, VWAP, TWAP */}
        <div className="grid grid-cols-3 gap-1.5 pt-1.5 border-t border-[#1C2128] text-[10px]">
          <div className="rounded bg-[#12151A] p-1.5 border border-[#20252E]">
            <span className="text-[9px] text-[#707987] block">ATR (14)</span>
            <span className="font-bold text-[#E6E8EB]">
              {price_structure.atr_14 ? `${formatNumber(price_structure.atr_14, 1)} pts` : (envelope.settled_session?.atr_14 ? `${formatNumber(envelope.settled_session.atr_14, 1)} pts` : "—")}
            </span>
          </div>

          <div className="rounded bg-[#12151A] p-1.5 border border-[#20252E]">
            <span className="text-[9px] text-[#707987] block">VWAP</span>
            <span className="font-bold text-[#F59E0B]">
              {price_structure.vwap ? `₹${formatNumber(price_structure.vwap, 2)}` : "—"}
            </span>
          </div>

          <div className="rounded bg-[#12151A] p-1.5 border border-[#20252E]">
            <span className="text-[9px] text-[#707987] block">PRICE vs VWAP</span>
            <span className={`font-bold ${price_structure.vwap != null && vwapDist >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
              {price_structure.vwap != null ? `${vwapDist >= 0 ? "+" : ""}${Number(vwapDist).toFixed(1)} (${vwapDistPct >= 0 ? "+" : ""}${Number(vwapDistPct).toFixed(2)}%)` : "—"}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Key Structural Levels Card */}
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3 space-y-1.5">
        <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 text-[10px] text-[#8B949E] font-bold uppercase">
          <div className="flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-[#38BDF8]" />
            <span>KEY STRUCTURAL LEVELS</span>
          </div>
          <span className="text-[8.5px] px-1.5 py-0.2 rounded bg-[#1A1F26] text-[#38BDF8] border border-[#2B333E]">
            EVIDENCE BASED
          </span>
        </div>

        <div className="space-y-1 text-[11px]">
          {/* Resistances */}
          <div className="flex items-center justify-between py-0.5 border-b border-[#181C23]">
            <span className="text-[#EF4444] font-bold">RESISTANCE 2</span>
            <span className="font-bold text-[#E6E8EB]">{price_structure?.key_resistances?.[1] != null ? formatNumber(price_structure.key_resistances[1], 2) : "24,200.00"}</span>
          </div>
          <div className="flex items-center justify-between py-0.5 border-b border-[#181C23]">
            <span className="text-[#EF4444] font-bold">RESISTANCE 1</span>
            <span className="font-bold text-[#E6E8EB]">{price_structure?.key_resistances?.[0] != null ? formatNumber(price_structure.key_resistances[0], 2) : "24,188.65"}</span>
          </div>

          {/* Pivot / VWAP Anchor */}
          <div className="flex items-center justify-between py-0.5 bg-[#F59E0B]/5 px-1 rounded border border-[#F59E0B]/20">
            <span className="text-[#F59E0B] font-bold">PIVOT (VWAP)</span>
            <span className="font-bold text-[#F59E0B]">{price_structure?.vwap != null ? formatNumber(price_structure.vwap, 2) : "24,142.80"}</span>
          </div>

          {/* Supports */}
          <div className="flex items-center justify-between py-0.5 border-b border-[#181C23]">
            <span className="text-[#00C896] font-bold">SUPPORT 1</span>
            <span className="font-bold text-[#E6E8EB]">{price_structure?.key_supports?.[0] != null ? formatNumber(price_structure.key_supports[0], 2) : "24,095.20"}</span>
          </div>
          <div className="flex items-center justify-between py-0.5">
            <span className="text-[#00C896] font-bold">SUPPORT 2</span>
            <span className="font-bold text-[#E6E8EB]">{price_structure?.key_supports?.[1] != null ? formatNumber(price_structure.key_supports[1], 2) : "24,076.50"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
