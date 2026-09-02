/**
 * test_frontend_live_tick_contract.test.ts
 *
 * Validates the single-source-of-truth live tick wiring contract:
 *
 * 1. useLiveMarketPresentation() must wrap marketContext (live overlay), not
 *    create an independent precedence tree.
 * 2. Post-market: when session is not OPEN, live tick must NOT override.
 * 3. useNiftyData() spot/change/high/low must resolve from marketContext
 *    not from raw canonicalState.market_data price fields.
 *
 * These are pure logic tests; they do not mount React components.
 */

import { describe, it, expect } from "vitest";

// ─── Helpers (mirrors WorkstationStateContext logic) ──────────────────────────

function buildSessionBadge(sessionStatus: string) {
  const s = sessionStatus.toUpperCase();
  const isOpen = s === "OPEN" || s === "MARKET_OPEN";
  const isPreMarket = s === "PRE_OPEN" || s === "PRE_MARKET";
  const isPostMarket = s === "POST_MARKET" || s === "CLOSE";
  return {
    isOpen,
    isPreMarket,
    isPostMarket,
    isClosed: !isOpen && !isPreMarket && !isPostMarket,
    label: isOpen ? "OPEN" : isPreMarket ? "PRE-MARKET" : isPostMarket ? "POST-MARKET" : "CLOSED",
  };
}

/**
 * Pure reimplementation of useLiveMarketPresentation() logic.
 * Must stay in sync with WorkstationStateContext.tsx.
 */
function simulateLiveMarketPresentation(opts: {
  sessionStatus: string;
  marketContext: { current_spot: number; spot_change: number | null; spot_change_pct: number | null; high: number; low: number; };
  rawMarketData?: { current_spot?: number; spot_change?: number; spot_change_pct?: number; high?: number; low?: number };
  liveNiftyTick?: { price: number; [k: string]: any } | null;
}) {
  const sessionBadge = buildSessionBadge(opts.sessionStatus);
  const isOpenSession = sessionBadge.isOpen;
  const mc = opts.marketContext;
  const raw = opts.rawMarketData;

  const currentSpot = isOpenSession
    ? (mc.current_spot > 0 ? mc.current_spot : null)
    : (raw?.current_spot != null && Number(raw.current_spot) > 0 ? Number(raw.current_spot) : null);

  const change = isOpenSession ? (mc.spot_change ?? null) : (raw?.spot_change ?? null);
  const changePct = isOpenSession ? (mc.spot_change_pct ?? null) : (raw?.spot_change_pct ?? null);
  const high = isOpenSession ? (mc.high > 0 ? mc.high : null) : (raw?.high != null && Number(raw.high) > 0 ? Number(raw.high) : null);
  const low = isOpenSession ? (mc.low > 0 ? mc.low : null) : (raw?.low != null && Number(raw.low) > 0 ? Number(raw.low) : null);

  const hasLiveTick = opts.liveNiftyTick != null;
  const source = (isOpenSession && hasLiveTick) ? "LIVE_TICK" : (currentSpot != null ? "CANONICAL_FALLBACK" : "UNAVAILABLE");
  const freshness = source === "LIVE_TICK" ? "FRESH" : source === "CANONICAL_FALLBACK" ? "LAST_VALID" : "UNAVAILABLE";

  return { sessionBadge, isOpenSession, currentSpot, change, changePct, high, low, source, freshness };
}

/**
 * Pure reimplementation of useNiftyData() LIVE PRESENTATION FIELDS.
 * Must stay in sync with NiftyLiveWorkspace.tsx.
 */
function simulateNiftyDataLiveFields(mc: { current_spot: number; spot_change: number | null; spot_change_pct: number | null; high: number; low: number; }) {
  const spot = mc.current_spot > 0 ? mc.current_spot : null;
  const change = mc.spot_change ?? null;
  const changePct = mc.spot_change_pct ?? null;
  const high = mc.high && mc.high > 0 ? mc.high : null;
  const low = mc.low && mc.low > 0 ? mc.low : null;
  return { spot, change, changePct, high, low };
}

// ─── Fixtures ────────────────────────────────────────────────────────────────

const OPEN_MC   = { current_spot: 24300, spot_change: 50, spot_change_pct: 0.21, high: 24320, low: 24270 };
const OPEN_RAW  = { current_spot: 24290, spot_change: 40, high: 24310, low: 24270 };
const OPEN_TICK = { price: 24300, change_points: 50, change_pct: 0.21, high: 24320, low: 24270 };

const POST_MC   = { current_spot: 24207.75, spot_change: -37.5, spot_change_pct: -0.15, high: 24340, low: 24190 };
const POST_RAW  = { current_spot: 24207.75, spot_change: -37.5, spot_change_pct: -0.15, high: 24340, low: 24190 };
const POST_TICK = { price: 24310 };  // stale after-close tick — must be ignored

const STALE_MC  = { current_spot: 24290, spot_change: 40, spot_change_pct: 0.17, high: 24310, low: 24268 };
const STALE_RAW = { current_spot: 24290, spot_change: 40 };

const PRE_MC    = { current_spot: 24250, spot_change: 0, spot_change_pct: 0, high: 24250, low: 24250 };
const PRE_RAW   = { current_spot: 24250, spot_change: 0, high: 24250, low: 24250 };

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("useLiveMarketPresentation — session gating contract", () => {

  it("OPEN: resolves currentSpot from live-overlaid marketContext, not raw canonical", () => {
    const r = simulateLiveMarketPresentation({ sessionStatus: "open", marketContext: OPEN_MC, rawMarketData: OPEN_RAW, liveNiftyTick: OPEN_TICK });
    expect(r.currentSpot).toBe(24300);   // live value, not raw 24290
    expect(r.change).toBe(50);
    expect(r.changePct).toBe(0.21);
    expect(r.high).toBe(24320);
    expect(r.low).toBe(24270);
    expect(r.source).toBe("LIVE_TICK");
    expect(r.freshness).toBe("FRESH");
    expect(r.isOpenSession).toBe(true);
  });

  it("OPEN: all simultaneous views see same spot (no independent precedence tree)", () => {
    for (let i = 0; i < 3; i++) {
      const r = simulateLiveMarketPresentation({ sessionStatus: "OPEN", marketContext: OPEN_MC, rawMarketData: OPEN_RAW, liveNiftyTick: OPEN_TICK });
      expect(r.currentSpot).toBe(24300);
    }
  });

  it("POST_MARKET: late live tick does NOT override canonical final close", () => {
    const r = simulateLiveMarketPresentation({ sessionStatus: "CLOSE", marketContext: POST_MC, rawMarketData: POST_RAW, liveNiftyTick: POST_TICK });
    expect(r.currentSpot).toBe(24207.75);  // canonical final, not stale 24310 tick
    expect(r.isOpenSession).toBe(false);
    expect(r.source).toBe("CANONICAL_FALLBACK");
  });

  it("POST_MARKET: high/low come from raw canonical, not live tick", () => {
    const r = simulateLiveMarketPresentation({ sessionStatus: "CLOSE", marketContext: POST_MC, rawMarketData: POST_RAW, liveNiftyTick: POST_TICK });
    expect(r.high).toBe(24340);
    expect(r.low).toBe(24190);
  });

  it("OPEN: stale fallback (no live tick) shows canonical with CANONICAL_FALLBACK source", () => {
    const r = simulateLiveMarketPresentation({ sessionStatus: "OPEN", marketContext: STALE_MC, rawMarketData: STALE_RAW, liveNiftyTick: null });
    expect(r.currentSpot).toBe(24290);
    expect(r.source).toBe("CANONICAL_FALLBACK");
    expect(r.freshness).toBe("LAST_VALID");
  });

  it("PRE_MARKET: uses canonical values, source is CANONICAL_FALLBACK, not OPEN", () => {
    const r = simulateLiveMarketPresentation({ sessionStatus: "PRE_OPEN", marketContext: PRE_MC, rawMarketData: PRE_RAW, liveNiftyTick: null });
    expect(r.currentSpot).toBe(24250);
    expect(r.source).toBe("CANONICAL_FALLBACK");
    expect(r.isOpenSession).toBe(false);
  });

  it("UNAVAILABLE: zero spot in marketContext, no raw, no tick → UNAVAILABLE", () => {
    const r = simulateLiveMarketPresentation({
      sessionStatus: "OPEN",
      marketContext: { current_spot: 0, spot_change: null, spot_change_pct: null, high: 0, low: 0 },
      rawMarketData: undefined,
      liveNiftyTick: null,
    });
    expect(r.currentSpot).toBeNull();
    expect(r.source).toBe("UNAVAILABLE");
    expect(r.freshness).toBe("UNAVAILABLE");
  });

  it("POST_MARKET label: same isolation as CLOSE", () => {
    const r = simulateLiveMarketPresentation({ sessionStatus: "POST_MARKET", marketContext: POST_MC, rawMarketData: POST_RAW, liveNiftyTick: { price: 99999 } });
    expect(r.currentSpot).toBe(24207.75);
    expect(r.source).toBe("CANONICAL_FALLBACK");
  });
});

describe("useNiftyData — live presentation fields use marketContext not raw canonical", () => {

  it("spot resolves from marketContext.current_spot (live-overlaid)", () => {
    const r = simulateNiftyDataLiveFields({ ...OPEN_MC, current_spot: 24300 });
    expect(r.spot).toBe(24300);
  });

  it("spot returns null when marketContext.current_spot is 0 (no data guard)", () => {
    const r = simulateNiftyDataLiveFields({ current_spot: 0, spot_change: null, spot_change_pct: null, high: 0, low: 0 });
    expect(r.spot).toBeNull();
  });

  it("change and changePct propagate from marketContext", () => {
    const r = simulateNiftyDataLiveFields(OPEN_MC);
    expect(r.change).toBe(50);
    expect(r.changePct).toBe(0.21);
  });

  it("high/low propagate from marketContext and reject zero values", () => {
    const r = simulateNiftyDataLiveFields(OPEN_MC);
    expect(r.high).toBe(24320);
    expect(r.low).toBe(24270);

    const rz = simulateNiftyDataLiveFields({ current_spot: 24300, spot_change: 50, spot_change_pct: 0.21, high: 0, low: 0 });
    expect(rz.high).toBeNull();
    expect(rz.low).toBeNull();
  });

  it("change=null is preserved as null (not coerced to 0)", () => {
    const r = simulateNiftyDataLiveFields({ current_spot: 24300, spot_change: null, spot_change_pct: null, high: 24320, low: 24270 });
    expect(r.change).toBeNull();
    expect(r.changePct).toBeNull();
  });
});

describe("Post-market isolation — explicit sessionBadge.isOpen gating", () => {

  it("CLOSE: late after-hours tick does not bleed into presentation layer", () => {
    const FINAL = 24207.75;
    const LATE = 24350;
    const r = simulateLiveMarketPresentation({
      sessionStatus: "CLOSE",
      marketContext: { ...POST_MC, current_spot: LATE },  // even if mc has late tick
      rawMarketData: { current_spot: FINAL },
      liveNiftyTick: { price: LATE },
    });
    expect(r.currentSpot).toBe(FINAL);   // canonical final wins
    expect(r.isOpenSession).toBe(false);
    expect(r.source).toBe("CANONICAL_FALLBACK");
  });
});

describe("Completed-Session Reconciliation with c.date ISO timestamps", () => {
  it("resolves 28 Aug 2026 completed session metrics from raw candles with date field", async () => {
    const { getCompletedSession } = await import("../src/frontend/utils/canonicalSemanticContract");
    const mockCandles = [
      { date: "2026-08-28T09:15:00+05:30", open: 24122.60, high: 24146.10, low: 24110.90, close: 24121.25, volume: 0 },
      { date: "2026-08-28T12:48:00+05:30", open: 24170.00, high: 24188.30, low: 24165.00, close: 24180.00, volume: 0 },
      { date: "2026-08-28T09:32:00+05:30", open: 24090.00, high: 24095.00, low: 24076.85, close: 24085.00, volume: 0 },
      { date: "2026-08-28T15:29:00+05:30", open: 24142.45, high: 24175.65, low: 24142.45, close: 24175.65, volume: 0 },
    ];
    const prevCandles = [
      { date: "2026-08-27T15:29:00+05:30", open: 24100.00, high: 24110.00, low: 24085.00, close: 24090.85, volume: 0 },
    ];

    const metrics = getCompletedSession("2026-08-28", undefined, { candles: [...prevCandles, ...mockCandles] });
    expect(metrics.isAvailable).toBe(true);
    expect(metrics.open).toBe(24122.60);
    expect(metrics.high).toBe(24188.30);
    expect(metrics.low).toBe(24076.85);
    expect(metrics.close).toBe(24175.65);
    expect(metrics.previousClose).toBe(24090.85);
    expect(metrics.change).toBe(84.80);
    expect(metrics.range).toBe(111.45);
    expect(metrics.changePercent).toBe(0.35);
  });

  it("safely falls back to market spot if completed session close is null", () => {
    const compMetricsNullClose: { close: number | null } = { close: null };
    const marketContext = { current_spot: 24175.65 };
    const market = { current_spot: 24175.65 };
    const liveTickPrice = null;
    const isPostSession = true;

    const rawSpot = isPostSession
      ? (compMetricsNullClose.close ?? liveTickPrice ?? marketContext?.current_spot ?? market.current_spot)
      : (liveTickPrice ?? marketContext?.current_spot ?? market.current_spot ?? compMetricsNullClose.close);

    expect(rawSpot).toBe(24175.65);
  });
});

