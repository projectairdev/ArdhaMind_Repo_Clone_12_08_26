/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Central Authoritative Market State & Spot Continuity Engine.
 * Implements a deterministic 5-tier fallback cascade to ensure spot and structural levels
 * never collapse to null or render "Unavailable" when valid session anchors exist.
 */

import { CanonicalFrontendEnvelope } from "../types/canonical";

export interface AuthoritativeBreadthState {
  advances: number | null;
  declines: number | null;
  unchanged: number | null;
  total: number;
  advancePct: number | null;
  ratio: number | null;
  bias: "BULLISH" | "BEARISH" | "NEUTRAL" | "UNAVAILABLE";
  advDecStr: string;
}

export interface AuthoritativeMarketState {
  spot: number | null;
  spotSource: "LIVE" | "AUCTION" | "OPTIONS" | "CANDLE" | "SETTLED";
  settledClose: number | null;
  settledHigh: number | null;
  settledLow: number | null;
  settledVwap: number | null;
  settledRange: number | null;
  change: number | null;
  changePercent: number | null;
  changePct?: number | null;
  displayVix: number | null;
  vix?: number | null;
  prevClose?: number | null;
  sessionDate?: string | null;
  dayHigh?: number | null;
  dayLow?: number | null;
  dayOpen?: number | null;
  vwap?: number | null;
  atr14?: number | null;
  intradayRange?: number | null;
  atrUtilizationPct?: number | null;
  atrUtilizationStr?: string;
  breadth: AuthoritativeBreadthState;
}

export function resolveAuthoritativeMarketState(
  envelope: CanonicalFrontendEnvelope | any | null | undefined
): AuthoritativeMarketState {
  const emptyBreadth: AuthoritativeBreadthState = {
    advances: null,
    declines: null,
    unchanged: null,
    total: 50,
    advancePct: null,
    ratio: null,
    bias: "UNAVAILABLE",
    advDecStr: "—",
  };

  const emptyState: AuthoritativeMarketState = {
    spot: null,
    spotSource: "SETTLED",
    settledClose: null,
    settledHigh: null,
    settledLow: null,
    settledVwap: null,
    settledRange: null,
    change: null,
    changePercent: null,
    changePct: null,
    displayVix: null,
    vix: null,
    prevClose: null,
    sessionDate: null,
    dayHigh: null,
    dayLow: null,
    dayOpen: null,
    vwap: null,
    breadth: emptyBreadth,
  };

  if (!envelope) {
    return emptyState;
  }

  // Honest empty state for a genuine no-session / DEGRADED envelope: the
  // "stream_init" placeholder, or an envelope with no runtime id and no real
  // market data of any kind. Without this guard the tier-1 / tier-5 cascade
  // below would happily surface a stale settled_session.close or
  // price_structure.previous_close (e.g. a leaked 28-Aug fixture value) as a
  // live spot. CanonicalStateContext is the primary gate; this is defence in
  // depth for any other caller.
  const rid = String((envelope as any).runtime_id || "");
  const hasAnyRealData = Boolean(
    (envelope.market?.nifty?.last_price != null && Number(envelope.market.nifty.last_price) > 0) ||
    (envelope.ticks?.nifty?.ltp != null && Number(envelope.ticks.nifty.ltp) > 0) ||
    (Array.isArray(envelope.candles?.["1m"]) && envelope.candles["1m"].length > 0) ||
    (envelope.settled_session?.close != null && Number(envelope.settled_session.close) > 0) ||
    (envelope.price_structure?.last_price != null && Number(envelope.price_structure.last_price) > 0)
  );
  if (rid === "stream_init" || (!rid && !hasAnyRealData)) {
    return emptyState;
  }

  // 1. Prior Settled Session Anchors (Strictly Previous Day)
  const settledClose =
    envelope.settled_session?.close ??
    envelope.price_structure?.previous_close ??
    envelope.market?.nifty?.previous_close ??
    envelope.settled_session?.previous_close ??
    null;

  const rawCandles =
    (Array.isArray(envelope.candles?.["1m"]) && envelope.candles["1m"].length > 0 ? envelope.candles["1m"] : null) ||
    (Array.isArray(envelope.candles?.["5m"]) && envelope.candles["5m"].length > 0 ? envelope.candles["5m"] : null) ||
    (Array.isArray(envelope.market_data?.candles) && envelope.market_data.candles.length > 0 ? envelope.market_data.candles : null) ||
    [];

  let candleHigh: number | null = null;
  let candleLow: number | null = null;
  let candleOpen: number | null = null;

  if (rawCandles.length > 0) {
    const validHighs = rawCandles.map((c: any) => Number(c.high ?? c.h)).filter((v: number) => !isNaN(v) && v > 0);
    const validLows = rawCandles.map((c: any) => Number(c.low ?? c.l)).filter((v: number) => !isNaN(v) && v > 0);
    if (validHighs.length > 0) candleHigh = Number(Math.max(...validHighs).toFixed(2));
    if (validLows.length > 0) candleLow = Number(Math.min(...validLows).toFixed(2));
    const firstC = rawCandles[0];
    if (firstC && (firstC.open != null || firstC.o != null)) {
      const op = Number(firstC.open ?? firstC.o);
      if (!isNaN(op) && op > 0) candleOpen = Number(op.toFixed(2));
    }
  }

  const isLiveTape =
    envelope.session?.market_phase === "LIVE" ||
    envelope.session?.market_phase === "NEAR_CLOSE" ||
    envelope.session?.market_phase === "OPENING_RANGE" ||
    envelope.workspaceContext?.marketState === "OPEN" ||
    envelope.market?.nifty?.quality === "LIVE" ||
    Boolean(envelope.ticks?.nifty?.ltp);

  const rawDayHigh = candleHigh ?? envelope.market?.nifty?.high ?? envelope.price_structure?.day_high ?? envelope.price_structure?.high ?? null;
  const rawDayLow = candleLow ?? envelope.market?.nifty?.low ?? envelope.price_structure?.day_low ?? envelope.price_structure?.low ?? null;
  const rawDayOpen = candleOpen ?? envelope.price_structure?.open ?? envelope.market?.nifty?.open ?? null;

  const dayHigh = rawDayHigh != null ? Number(rawDayHigh) : (isLiveTape ? null : (envelope.settled_session?.high != null ? Number(envelope.settled_session.high) : null));
  const dayLow = rawDayLow != null ? Number(rawDayLow) : (isLiveTape ? null : (envelope.settled_session?.low != null ? Number(envelope.settled_session.low) : null));
  const dayOpen = rawDayOpen != null ? Number(rawDayOpen) : (isLiveTape ? null : (envelope.settled_session?.open != null ? Number(envelope.settled_session.open) : null));
  const vwap = envelope.price_structure?.vwap ?? envelope.market?.nifty?.vwap ?? (isLiveTape ? null : (envelope.settled_session?.vwap ?? null));

  const settledHigh = envelope.settled_session?.high ?? null;
  const settledLow = envelope.settled_session?.low ?? null;
  const settledVwap = envelope.settled_session?.vwap ?? null;
  const settledRange =
    envelope.settled_session?.range ??
    envelope.settled_session?.range_points ??
    (settledHigh != null && settledLow != null ? Number((settledHigh - settledLow).toFixed(1)) : null);

  // 2. Strict 5-Tier Spot Price Cascade
  let spot: number | null = null;
  let spotSource: AuthoritativeMarketState["spotSource"] = "SETTLED";

  const liveTick = envelope.market?.nifty?.last_price ?? envelope.ticks?.nifty?.ltp;
  const priceStructPrice = envelope.price_structure?.last_price ?? envelope.price_structure?.current_price;
  const auctionPrice = envelope.pre_open?.matched_price ?? envelope.price_structure?.open ?? dayOpen;
  const optionsSpot =
    envelope.options?.spot_price ??
    envelope.options_intelligence?.underlying_spot ??
    (envelope.options as any)?.underlying_price;
  const latest1mClose =
    Array.isArray(envelope.candles?.["1m"]) && envelope.candles["1m"].length > 0
      ? envelope.candles["1m"][envelope.candles["1m"].length - 1]?.close ?? envelope.candles["1m"][envelope.candles["1m"].length - 1]?.c
      : null;

  if (liveTick != null && Number(liveTick) > 0) {
    spot = Number(liveTick);
    spotSource = "LIVE";
  } else if (priceStructPrice != null && Number(priceStructPrice) > 0) {
    spot = Number(priceStructPrice);
    spotSource = "LIVE";
  } else if (auctionPrice != null && Number(auctionPrice) > 0) {
    spot = Number(auctionPrice);
    spotSource = "AUCTION";
  } else if (optionsSpot != null && Number(optionsSpot) > 0) {
    spot = Number(optionsSpot);
    spotSource = "OPTIONS";
  } else if (latest1mClose != null && Number(latest1mClose) > 0) {
    spot = Number(latest1mClose);
    spotSource = "CANDLE";
  } else if (envelope.active_product?.tomorrow_plan?.session_summary?.close) {
    spot = Number(envelope.active_product.tomorrow_plan.session_summary.close);
    spotSource = "SETTLED";
  } else if (settledClose != null && Number(settledClose) > 0) {
    spot = Number(settledClose);
    spotSource = "SETTLED";
  }

  // Prevent PrevClose Trap if valid 1m candles are present with newer prices
  if (spot != null && settledClose != null && spot === settledClose && latest1mClose != null && Number(latest1mClose) > 0 && Number(latest1mClose) !== settledClose) {
    spot = Number(latest1mClose);
    spotSource = "CANDLE";
  }

  // 3. Dynamic Deltas (relative to settled previous close)
  let change: number | null = null;
  let changePercent: number | null = null;
  if (spot != null && settledClose != null && settledClose > 0) {
    change = Number((spot - settledClose).toFixed(2));
    changePercent = Number(((change / settledClose) * 100).toFixed(2));
  }

  const rawVix =
    envelope.macro?.india_vix ??
    envelope.market?.vix?.last_price ??
    envelope.market?.vix?.previous_close ??
    (typeof envelope.settled_session?.closing_vix === "object" ? (envelope.settled_session.closing_vix as any)?.vix_close : envelope.settled_session?.closing_vix) ??
    (typeof (envelope.settled_session as any)?.vix === "object" ? (envelope.settled_session as any)?.vix?.vix_close : (envelope.settled_session as any)?.vix) ??
    null;

  const displayVix = rawVix != null ? Number(Number(rawVix).toFixed(2)) : null;

  const sessionDate =
    envelope.session?.active_trading_date ??
    envelope.session?.completed_session_date ??
    envelope.settled_session?.session_date ??
    null;

  // 4. Authoritative Breadth Engine (Single Source of Truth)
  const rawBreadth =
    envelope.breadth ??
    envelope.market?.breadth ??
    envelope.market_data?.breadth ??
    envelope.market_context?.breadth ??
    (envelope as any)?.marketContext?.breadth ??
    (envelope as any)?.workspaceContext?.breadth ??
    envelope.session_stats?.breadth ??
    envelope.settled_session?.closing_breadth ??
    envelope.settled_session?.final_breadth ??
    null;

  let advances: number | null = null;
  let declines: number | null = null;
  let unchanged: number | null = null;

  if (rawBreadth && typeof rawBreadth === "object") {
    advances = rawBreadth.advances != null && !isNaN(Number(rawBreadth.advances)) ? Number(rawBreadth.advances) : null;
    declines = rawBreadth.declines != null && !isNaN(Number(rawBreadth.declines)) ? Number(rawBreadth.declines) : null;
    unchanged = rawBreadth.unchanged != null && !isNaN(Number(rawBreadth.unchanged)) ? Number(rawBreadth.unchanged) : (advances != null && declines != null ? Math.max(0, 50 - advances - declines) : null);
  }

  const total = advances != null && declines != null ? advances + declines + (unchanged ?? 0) : 50;
  const advancePct = advances != null && total > 0 ? Math.round((advances / total) * 100) : (rawBreadth?.advance_pct != null ? Number(rawBreadth.advance_pct) : null);
  const ratio = advances != null && declines != null && declines > 0 ? Number((advances / declines).toFixed(2)) : (rawBreadth?.ratio != null ? Number(rawBreadth.ratio) : null);

  let bias: AuthoritativeBreadthState["bias"] = "UNAVAILABLE";
  if (advances != null && declines != null) {
    if (advances > declines) {
      bias = "BULLISH";
    } else if (declines > advances) {
      bias = "BEARISH";
    } else {
      bias = "NEUTRAL";
    }
  }

  const advDecStr = advances != null && declines != null ? `${advances} / ${declines}` : "—";

  const breadthState: AuthoritativeBreadthState = {
    advances,
    declines,
    unchanged,
    total,
    advancePct,
    ratio,
    bias,
    advDecStr,
  };

  // 5. Authoritative 14D ATR & Utilization Engine
  const rawAtr14 =
    envelope.price_structure?.atr_14 ??
    envelope.market?.nifty?.atr_14 ??
    envelope.market_data?.atr_14 ??
    envelope.volatility_structure?.atr_14 ??
    envelope.session_stats?.atr_14 ??
    envelope.settled_session?.atr_14 ??
    null;

  const atr14 = rawAtr14 != null && !isNaN(Number(rawAtr14)) && Number(rawAtr14) > 0 ? Number(Number(rawAtr14).toFixed(2)) : null;
  const intradayRange = (dayHigh != null && dayLow != null)
    ? Number((dayHigh - dayLow).toFixed(2))
    : (settledRange != null ? settledRange : null);

  const atrUtilizationPct = (intradayRange != null && atr14 != null && atr14 > 0)
    ? Math.min(100, Math.round((intradayRange / atr14) * 100))
    : null;
  const atrUtilizationStr = atrUtilizationPct != null ? `${atrUtilizationPct}%` : "—";

  return {
    spot,
    spotSource,
    settledClose,
    settledHigh,
    settledLow,
    settledVwap,
    settledRange,
    change,
    changePercent,
    changePct: changePercent,
    displayVix,
    vix: displayVix,
    prevClose: settledClose,
    sessionDate,
    dayHigh,
    dayLow,
    dayOpen,
    vwap,
    atr14,
    intradayRange,
    atrUtilizationPct,
    atrUtilizationStr,
    breadth: breadthState,
  };
}
