/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Canonical State Context & Convergence Provider.
 * Enforces (runtime_id, revision) monotonic progression, server restart auto-recovery,
 * phase-aware intelligence distribution, and 4-mode trader presentation taxonomy.
 * 
 * OPTION A CLEAN BREAK:
 * - Single UI Authority: Canonical UI is the sole rendering architecture.
 * - Single Clock Authority: Exchanges timestamps dictate state; no dual clock.
 * - Honest Empty State: Outside market hours, shows clean awaiting state instead
 *   of automatic 28-Aug fixture substitution.
 * - Replay Mode: Fixture replay is strictly explicit opt-in (?mode=replay or preview override).
 */

import React, { createContext, useContext, useState, useEffect, useMemo, useCallback, ReactNode } from "react";
import { CanonicalFrontendEnvelope, DataQualityStatus, MarketPhase } from "../types/canonical";
import {
  SessionPhase,
  IntelligenceMode,
  DataWindow,
  CanonicalSessionIdentity,
  resolveCanonicalSessionIdentity,
} from "../session/sessionPhaseEngine";
import {
  CANONICAL_FIXTURE_PRE_MARKET,
  CANONICAL_FIXTURE_PRE_OPEN,
  CANONICAL_FIXTURE_OPENING_RANGE,
  CANONICAL_FIXTURE_REGULAR_LIVE,
  CANONICAL_FIXTURE_NEAR_CLOSE,
  CANONICAL_FIXTURE_POST_MARKET,
} from "../data/canonicalFixtures";
import { useSessionPhaseScheduler } from "../hooks/useSessionPhaseScheduler";

export type PresentationMode = "CANONICAL_UI";
export type WorkstationSourceMode = "CANONICAL_LIVE";

// 4 Major Trader Modes
export type TraderMarketMode = "MORNING" | "OPENING" | "LIVE" | "POST_MARKET";

export type PreviewPhaseMode =
  | "AUTO"
  | "MORNING"
  | "OPENING"
  | "LIVE"
  | "POST_MARKET"
  | "PRE_MARKET"
  | "PRE_OPEN"
  | "OPENING_RANGE"
  | "MARKET_OPEN"
  | "NEAR_CLOSE";

export const ENABLE_PHASE_PREVIEW: boolean = (import.meta as any).env?.VITE_ENABLE_PHASE_PREVIEW !== "false";

export const EMPTY_CANONICAL_ENVELOPE: CanonicalFrontendEnvelope = {
  runtime_id: "stream_init",
  state_revision: 0,
  published_at: null as any,
  session: {
    calendar_date: "",
    market_phase: "PRE_MARKET",
    is_trading_day: true,
    active_trading_date: null,
    completed_session_date: "",
    previous_session_date: "",
    next_trading_date: "",
    phase_label: "Awaiting Live Session",
  },
  market: {
    nifty: {
      canonical_instrument_id: "IDX:NSE:NIFTY_50",
      symbol: "NIFTY 50",
      session_date: "",
      last_price: null,
      exchange_timestamp: null,
      received_at: null,
      open: null,
      high: null,
      low: null,
      previous_close: null,
      change: null,
      change_pct: null,
      volume: null,
      oi: null,
      bid: null,
      ask: null,
      spread: null,
      provider: "DHAN_HQ",
      quality: "UNAVAILABLE",
    },
    vix: {
      canonical_instrument_id: "IDX:NSE:INDIA_VIX",
      symbol: "INDIA VIX",
      session_date: "",
      last_price: null,
      exchange_timestamp: null,
      received_at: null,
      open: null,
      high: null,
      low: null,
      previous_close: null,
      change: null,
      change_pct: null,
      volume: null,
      oi: null,
      bid: null,
      ask: null,
      spread: null,
      provider: "DHAN_HQ",
      quality: "UNAVAILABLE",
    },
    state_revision: 0,
    quality: "UNAVAILABLE",
  },
  feed_health: {
    overall_status: "NOT_RUNNING",
    socket_connected: false,
    quality: "UNAVAILABLE",
  },
  candles: {
    "1m": [],
  },
  price_structure: {
    last_price: null,
    open: null,
    high: null,
    low: null,
    previous_close: null,
    change: null,
    change_pct: null,
    range_points: null,
    range_pct: null,
    atr_14: null,
    is_compressed: false,
    opening_range_status: "AWAITING_OPEN",
    or_high: null,
    or_low: null,
    vwap: null,
    vwap_is_genuine: false,
    twap: null,
    trend_direction: "NEUTRAL",
    trend_strength: "LOW",
    swing_high: null,
    swing_low: null,
    key_supports: [],
    key_resistances: [],
    gap_status: "FLAT",
    gap_points: null,
    gap_filled: false,
    quality: "UNAVAILABLE",
  },
  breadth: {
    advances: null as any,
    declines: null as any,
    unchanged: null as any,
    total_constituents: 50,
    ratio: null as any,
    advance_pct: null as any,
    leadership_bias: "NEUTRAL",
    heavyweight_bias: "NEUTRAL",
    sector_bias: {},
    quality: "UNAVAILABLE",
  },
  options: {
    spot_price: null as any,
    expiry: "",
    atm_strike: null as any,
    pcr: null as any,
    max_pain: null as any,
    call_wall: null as any,
    put_wall: null as any,
    total_call_oi: null as any,
    total_put_oi: null as any,
    total_call_volume: null as any,
    total_put_volume: null as any,
    options_confirmation: "NEUTRAL_EXPIRY",
    strike_universe: [],
    quality: "UNAVAILABLE",
  },
  regime: {
    regime_type: "RANGE_BOUND",
    rationale: "Awaiting live market data stream.",
    volatility_state: "NORMAL_VOLATILITY",
  },
  prediction: {
    target_session_date: "",
    phase: "PRE_MARKET",
    direction_bias: "NEUTRAL",
    direction_confidence: 0,
    factor_contributions: [],
    magnitude_distribution: [],
    expected_range_points: 0,
    confidence_score: 0,
    confidence_band: "LOW",
    calibration_maturity: "EXPERIMENTAL",
    quality: "UNAVAILABLE",
    status: "UNAVAILABLE",
    similar_sessions: [],
    volatility_corridor: {},
    is_live_projection: false,
    basis: "UNAVAILABLE",
  },
  decision: {
    decision_state: "WAIT",
    decision_headline: "Awaiting Live Session / Market Stream",
    opportunity_setup: "NO_SETUP",
    trigger_condition: "Awaiting market open observations",
    invalidation_boundary: "N/A",
    confidence_band: "LOW",
    confidence_score: 0,
    risk_level: "NORMAL",
    strategy_suitability: "NO_TRADE",
    strike_candidates: [],
    checklist_items: [],
    bullish_factors: [],
    bearish_factors: [],
    caution_factors: [],
    quality: "UNAVAILABLE",
  },
  active_product: {
    product_type: "MORNING_PLAN",
  },
  settled_session: null,
  data_quality: "UNAVAILABLE",
};

interface CanonicalStateContextType {
  presentationMode: PresentationMode;
  setPresentationMode: (mode: PresentationMode) => void;
  sourceMode: WorkstationSourceMode;
  setSourceMode: (mode: WorkstationSourceMode) => void;
  previewPhase: PreviewPhaseMode;
  setPreviewPhase: (mode: PreviewPhaseMode) => void;
  enablePhasePreview: boolean;
  traderMode: TraderMarketMode;
  envelope: CanonicalFrontendEnvelope;
  isConnected: boolean;
  lastUpdated: Date;
  runtimeId: string;
  stateRevision: number;
  quality: DataQualityStatus;
  marketPhase: MarketPhase;
  isStale: boolean;
  isFixtureData: boolean;
  sessionIdentity: CanonicalSessionIdentity;
  sessionPhase: SessionPhase;
  intelligenceMode: IntelligenceMode;
  dataWindow: DataWindow;
  isReplayMode: boolean;
  settledSession: CanonicalFrontendEnvelope["settled_session"] | null;
  hasSettledSession: boolean;
  isLiveStreaming: boolean;
}

const CanonicalStateContext = createContext<CanonicalStateContextType | null>(null);

function detectInitialReplayMode(): boolean {
  if (typeof window !== "undefined") {
    const search = window.location.search.toLowerCase();
    if (search.includes("mode=replay") || search.includes("replay=true") || search.includes("fixture=true")) {
      return true;
    }
  }
  return false;
}

/** Current calendar date on the exchange (IST), as YYYY-MM-DD. "" if undeterminable. */
function todayIstDateStr(): string {
  try {
    // en-CA locale formats as YYYY-MM-DD
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date());
  } catch {
    return "";
  }
}

/**
 * True only for an envelope that represents the CURRENT trading session's real
 * live stream — not a fixture / replay tape, not the "stream_init" placeholder,
 * and not a stale cache carried over from a previous day.
 *
 * Gates both the sessionStorage rehydration and the live-envelope acceptance so
 * that a genuine no-broker / no-session DEGRADED state falls through to
 * EMPTY_CANONICAL_ENVELOPE (honest empty UI) instead of surfacing yesterday's —
 * or a 28-Aug fixture's — settled close and structural levels as if they were
 * live. Fixture data stays fully usable through the explicit replay/preview
 * paths, which never route through here.
 */
function isCurrentRealEnvelope(env: any): boolean {
  if (!env || typeof env !== "object") return false;
  const rid = String(env.runtime_id || "");
  if (!rid || rid === "stream_init") return false;
  if (rid.startsWith("rt_fixture") || env.is_fixture === true || env.is_replay === true) return false;

  const today = todayIstDateStr();
  if (!today) return true; // cannot prove staleness by date; runtime_id checks above still applied

  const envDate = String(
    env.session?.active_trading_date ||
    env.session?.calendar_date ||
    env.session?.completed_session_date ||
    ""
  ).slice(0, 10);

  // A live envelope for the current session is always stamped with today's IST
  // trading date. An older date means a stale cache — reject it.
  if (envDate !== "" && envDate !== today) return false;

  // Coherence guard: the settled-session anchors must belong to the session the
  // envelope claims. A backend that has no live feed can still assemble an
  // envelope with today's session date but fill settled_session / prices from a
  // days-old snapshot (observed on staging: settled_session.session_date
  // "2026-08-28" while completed_session_date is "2026-09-02", zero candles).
  // If the settled anchors predate the claimed previous session AND there are no
  // intraday candles, the market data is not real — treat it as no session.
  const settledDate = String(env.settled_session?.session_date || "").slice(0, 10);
  const prevSessionDate = String(
    env.session?.previous_session_date || env.session?.completed_session_date || ""
  ).slice(0, 10);
  const hasIntradayCandles = Array.isArray(env.candles?.["1m"]) && env.candles["1m"].length > 0;
  if (settledDate && prevSessionDate && settledDate < prevSessionDate && !hasIntradayCandles) {
    return false;
  }

  return true;
}

export function CanonicalStateProvider({ children }: { children: ReactNode }) {
  const isExplicitReplayInitial = useMemo(() => detectInitialReplayMode(), []);
  const [explicitReplay, setExplicitReplay] = useState<boolean>(isExplicitReplayInitial);
  const [previewPhaseState, setPreviewPhaseState] = useState<PreviewPhaseMode>("AUTO");

  const previewPhase: PreviewPhaseMode = ENABLE_PHASE_PREVIEW ? previewPhaseState : "AUTO";
  const setPreviewPhase = (mode: PreviewPhaseMode) => {
    if (ENABLE_PHASE_PREVIEW) {
      setPreviewPhaseState(mode);
      if (mode !== "AUTO") {
        setExplicitReplay(true);
      }
    }
  };

  const [liveEnvelope, setLiveEnvelope] = useState<CanonicalFrontendEnvelope | null>(() => {
    try {
      if (typeof window !== "undefined" && window.sessionStorage) {
        const cached = sessionStorage.getItem("ardhamind_canonical_envelope");
        if (cached) {
          const parsed = JSON.parse(cached);
          // Only rehydrate a CURRENT real-session envelope. A stale prior-day
          // cache or a persisted fixture must not seed the live envelope.
          if (isCurrentRealEnvelope(parsed)) {
            return parsed;
          }
          sessionStorage.removeItem("ardhamind_canonical_envelope");
        }
      }
    } catch {
      // Ignore sessionStorage access errors
    }
    return null;
  });
  const [lastRuntimeId, setLastRuntimeId] = useState<string>("");
  const [lastRevision, setLastRevision] = useState<number>(0);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [clockTick, setClockTick] = useState<Date>(new Date());

  useEffect(() => {
    const timer = setInterval(() => setClockTick(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const isReplayMode = useMemo(() => {
    return explicitReplay || previewPhase !== "AUTO";
  }, [explicitReplay, previewPhase]);

  const isFixtureData = isReplayMode;

  // Active envelope based on explicit replay override or live state
  const envelope = useMemo<CanonicalFrontendEnvelope>(() => {
    if (previewPhase !== "AUTO") {
      switch (previewPhase) {
        case "MORNING":
        case "PRE_MARKET":
          return CANONICAL_FIXTURE_PRE_MARKET;
        case "PRE_OPEN":
          return CANONICAL_FIXTURE_PRE_OPEN;
        case "OPENING":
        case "OPENING_RANGE":
          return CANONICAL_FIXTURE_OPENING_RANGE;
        case "LIVE":
        case "MARKET_OPEN":
          return CANONICAL_FIXTURE_REGULAR_LIVE;
        case "NEAR_CLOSE":
          return CANONICAL_FIXTURE_NEAR_CLOSE;
        case "POST_MARKET":
          return CANONICAL_FIXTURE_POST_MARKET;
      }
    }

    if (explicitReplay) {
      return CANONICAL_FIXTURE_PRE_MARKET;
    }

    // Accept the live envelope only if it is a current, real-session stream.
    // A stale prior-day cache or a fixture that slipped into liveEnvelope falls
    // through to the honest empty state.
    if (liveEnvelope && isCurrentRealEnvelope(liveEnvelope)) {
      return liveEnvelope;
    }

    return EMPTY_CANONICAL_ENVELOPE;
  }, [previewPhase, explicitReplay, liveEnvelope]);

  const previewMappings = useMemo<{
    preview_sessionPhase?: SessionPhase;
    preview_intelligenceMode?: IntelligenceMode;
  }>(() => {
    switch (previewPhase) {
      case "MORNING":
      case "PRE_MARKET":
        return { preview_sessionPhase: "PRE_MARKET", preview_intelligenceMode: "PRE_COMMIT_PLAN" };
      case "PRE_OPEN":
        return { preview_sessionPhase: "PRE_OPEN", preview_intelligenceMode: "AUCTION_READ" };
      case "OPENING":
      case "OPENING_RANGE":
        return { preview_sessionPhase: "LIVE", preview_intelligenceMode: "OPEN_VALIDATION" };
      case "LIVE":
      case "MARKET_OPEN":
        return { preview_sessionPhase: "LIVE", preview_intelligenceMode: "REGIME_MONITOR" };
      case "NEAR_CLOSE":
        return { preview_sessionPhase: "NEAR_CLOSE", preview_intelligenceMode: "DECISION_WINDOW" };
      case "POST_MARKET":
        return { preview_sessionPhase: "POST_MARKET", preview_intelligenceMode: "OVERNIGHT_SYNTHESIS" };
      case "AUTO":
      default:
        return {};
    }
  }, [previewPhase]);

  const sessionIdentity = useMemo<CanonicalSessionIdentity>(() => {
    return resolveCanonicalSessionIdentity({
      customDate: clockTick,
      preview_sessionPhase: previewMappings.preview_sessionPhase,
      preview_intelligenceMode: previewMappings.preview_intelligenceMode,
      is_replay_mode: isReplayMode,
      envelope,
      isDisconnected: !isConnected,
    });
  }, [clockTick, previewMappings, isReplayMode, envelope, isConnected]);

  // Derive 4-mode trader presentation from active session identity and wall clock
  const traderMode = useMemo<TraderMarketMode>(() => {
    if (previewPhase !== "AUTO") {
      switch (previewPhase) {
        case "MORNING":
        case "PRE_MARKET":
        case "PRE_OPEN":
          return "MORNING";
        case "OPENING":
        case "OPENING_RANGE":
          return "OPENING";
        case "LIVE":
        case "MARKET_OPEN":
        case "NEAR_CLOSE":
          return "LIVE";
        case "POST_MARKET":
          return "POST_MARKET";
      }
    }
    const p = sessionIdentity.sessionPhase;
    if (p === "PRE_MARKET" || p === "PRE_OPEN") return "MORNING";
    if (p === "LIVE") {
      const hhmmss = sessionIdentity.wall_clock_ist;
      if (hhmmss >= "09:15:00" && hhmmss < "09:30:00") return "OPENING";
      return "LIVE";
    }
    if (p === "NEAR_CLOSE") return "LIVE";
    return "POST_MARKET";
  }, [previewPhase, sessionIdentity]);

  const normalizeCanonicalEnvelope = (incoming: Partial<CanonicalFrontendEnvelope>): CanonicalFrontendEnvelope => {
    let safeDataQuality: DataQualityStatus = "UNAVAILABLE";
    if (typeof incoming.data_quality === "string") {
      safeDataQuality = incoming.data_quality as DataQualityStatus;
    } else if (incoming.data_quality && typeof incoming.data_quality === "object") {
      const dqObj = incoming.data_quality as any;
      const status = dqObj.quality_status || dqObj.market_data?.freshness_status || dqObj.market_data?.quality_status || dqObj.status || "VALID";
      safeDataQuality = (String(status).toUpperCase() as DataQualityStatus) || "VALID";
    }

    return {
      ...EMPTY_CANONICAL_ENVELOPE,
      ...incoming,
      data_quality: safeDataQuality,
      session: {
        ...EMPTY_CANONICAL_ENVELOPE.session,
        ...(incoming.session || {}),
      },
      market: {
        ...EMPTY_CANONICAL_ENVELOPE.market,
        ...(incoming.market || {}),
        nifty: {
          ...EMPTY_CANONICAL_ENVELOPE.market.nifty,
          ...(incoming.market?.nifty || {}),
        },
        vix: {
          ...EMPTY_CANONICAL_ENVELOPE.market.vix,
          ...(incoming.market?.vix || {}),
        },
      },
      feed_health: {
        ...EMPTY_CANONICAL_ENVELOPE.feed_health,
        ...(incoming.feed_health || {}),
      },
      candles: {
        ...EMPTY_CANONICAL_ENVELOPE.candles,
        ...(incoming.candles || {}),
      },
      price_structure: {
        ...EMPTY_CANONICAL_ENVELOPE.price_structure,
        ...(incoming.price_structure || {}),
      },
      breadth: {
        ...EMPTY_CANONICAL_ENVELOPE.breadth,
        ...(incoming.breadth || {}),
      },
      options: {
        ...EMPTY_CANONICAL_ENVELOPE.options,
        ...(incoming.options || {}),
      },
      regime: {
        ...EMPTY_CANONICAL_ENVELOPE.regime,
        ...(incoming.regime || {}),
      },
      prediction: {
        ...EMPTY_CANONICAL_ENVELOPE.prediction,
        ...(incoming.prediction || {}),
      },
      decision: {
        ...EMPTY_CANONICAL_ENVELOPE.decision,
        ...(incoming.decision || {}),
      },
      active_product: incoming.active_product || EMPTY_CANONICAL_ENVELOPE.active_product,
    };
  };

  const applyIncomingEnvelope = (incoming: CanonicalFrontendEnvelope): boolean => {
    if (!incoming || !incoming.runtime_id) return false;

    // Guardrail: Enforce sequence ID / state_revision monotonicity to prevent race conditions
    const incomingRev = incoming.state_revision || (incoming as any).sequence_id || 0;
    if (incoming.runtime_id === lastRuntimeId && incomingRev < lastRevision && lastRevision > 0) {
      return false;
    }

    const normalized = normalizeCanonicalEnvelope(incoming);

    setLiveEnvelope((prev) => {
      if (!prev) return normalized;
      const base = normalizeCanonicalEnvelope(prev);

      return {
        ...base,
        ...normalized,
        active_product: normalized.active_product || base.active_product,
        options: (normalized.options && normalized.options.quality !== "UNAVAILABLE") ? normalized.options : (base.options || normalized.options),
        price_structure: (normalized.price_structure && normalized.price_structure.quality !== "UNAVAILABLE") ? normalized.price_structure : (base.price_structure || normalized.price_structure),
        candles: (normalized.candles && (normalized.candles["1m"]?.length ?? 0) > 0) ? normalized.candles : (base.candles || normalized.candles),
        settled_session: normalized.settled_session || base.settled_session,
        data_quality: (normalized.data_quality === "UNAVAILABLE" && base.data_quality === "VALID")
          ? base.data_quality
          : normalized.data_quality,
      };
    });

    setLastRuntimeId(incoming.runtime_id);
    setLastRevision(incomingRev);
    setLastUpdated(new Date());
    setIsConnected(true);

    try {
      const hasValidMarketState = Boolean(
        (incoming.market?.nifty?.last_price != null && Number(incoming.market.nifty.last_price) > 0) ||
        (incoming.settled_session?.close != null && Number(incoming.settled_session.close) > 0) ||
        (incoming.price_structure?.last_price != null && Number(incoming.price_structure.last_price) > 0) ||
        (incoming.price_structure?.previous_close != null && Number(incoming.price_structure.previous_close) > 0)
      );

      if (
        typeof window !== "undefined" &&
        window.sessionStorage &&
        hasValidMarketState &&
        isCurrentRealEnvelope(incoming)
      ) {
        sessionStorage.setItem("ardhamind_canonical_envelope", JSON.stringify(incoming));
      }
    } catch {
      // Ignore sessionStorage quota / permission errors
    }

    return true;
  };

  const fetchLiveEnvelope = useCallback(async (opts?: { forceRefresh?: boolean }) => {
    try {
      const url = opts?.forceRefresh ? "/api/canonical/envelope?refresh=true" : "/api/canonical/envelope";
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (data && data.runtime_id && data.runtime_id !== "stream_init") {
          applyIncomingEnvelope(data);
        }
      }
    } catch {
      // Fallback gracefully
    }
  }, []);

  // Autonomous high-precision client-side IST boundary alarm
  useSessionPhaseScheduler(() => {
    setClockTick(new Date());
    fetchLiveEnvelope({ forceRefresh: true });
  });

  // 1. Real-Time WebSocket Connection for sub-16ms live tick updates
  useEffect(() => {
    let isUnmounted = false;
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWebSocket = () => {
      if (isUnmounted) return;
      try {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/api/ws`;

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (isUnmounted) return;
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          if (isUnmounted) return;
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === "SESSION_PHASE_CHANGED" || msg.type === "session_phase_changed") {
              setClockTick(new Date());
              if (msg.data && msg.data.runtime_id) {
                applyIncomingEnvelope(msg.data);
              } else {
                fetchLiveEnvelope({ forceRefresh: true });
              }
            } else if (msg.type === "canonical_envelope") {
              if (msg.data && msg.data.runtime_id) {
                applyIncomingEnvelope(msg.data);
              }
            } else if (msg.type === "state") {
              // Ignore partial/legacy state messages to prevent competing stream mutations
              if (msg.data?.canonical_state?.runtime_id) {
                applyIncomingEnvelope(msg.data.canonical_state);
              }
            } else if (msg.type === "live_event" || msg.type === "tick") {
              const tick = msg.type === "live_event" ? msg.data : msg.data;
              const rawSym = msg.type === "live_event" ? msg.data?.symbol : msg.symbol;
              const symbol = String(rawSym || "").toUpperCase();

              const price = Number(tick?.price ?? tick?.last_price ?? 0);
              if (price > 0) {
                setLiveEnvelope((prev) => {
                  const base = prev ? normalizeCanonicalEnvelope(prev) : EMPTY_CANONICAL_ENVELOPE;
                  const isNifty = symbol.includes("NIFTY 50") || symbol.includes("NIFTY50") || symbol === "NIFTY";
                  const isVix = symbol.includes("INDIA VIX") || symbol.includes("INDIAVIX") || symbol === "VIX";

                  if (isNifty) {
                    const prevClose = base.market?.nifty?.previous_close ?? base.settled_session?.close ?? base.price_structure?.previous_close;
                    const changePts = prevClose != null ? Number((price - prevClose).toFixed(2)) : (tick.change_points ?? base.market?.nifty?.change);
                    const changePct = prevClose != null && prevClose > 0 ? Number((((price - prevClose) / prevClose) * 100).toFixed(2)) : (tick.change_pct ?? base.market?.nifty?.change_pct);
                    const high = tick.high ?? (base.price_structure?.high != null ? Math.max(base.price_structure.high, price) : price);
                    const low = tick.low ?? (base.price_structure?.low != null ? Math.min(base.price_structure.low, price) : price);

                    // Update forming 1m candle
                    const existing1m = base.candles?.["1m"] ? [...base.candles["1m"]] : [];
                    if (existing1m.length > 0) {
                      const lastIdx = existing1m.length - 1;
                      const lastCandle = { ...existing1m[lastIdx] };
                      lastCandle.close = price;
                      lastCandle.high = Math.max(lastCandle.high, price);
                      lastCandle.low = Math.min(lastCandle.low, price);
                      if (tick.volume) lastCandle.volume = (lastCandle.volume || 0) + Number(tick.volume);
                      existing1m[lastIdx] = lastCandle;
                    } else {
                      const nowIso = new Date().toISOString();
                      existing1m.push({
                        start: nowIso,
                        open: tick.open ?? price,
                        high: high,
                        low: low,
                        close: price,
                        volume: Number(tick.volume || 0),
                        is_forming: true,
                      } as any);
                    }

                    return {
                      ...base,
                      runtime_id: base.runtime_id || "live_stream_runtime",
                      is_live: true,
                      data_quality: "LIVE",
                      feed_health: {
                        overall_status: "HEALTHY",
                        socket_connected: true,
                        quality: "VALID",
                      },
                      market: {
                        ...(base.market || EMPTY_CANONICAL_ENVELOPE.market),
                        nifty: {
                          ...(base.market?.nifty || EMPTY_CANONICAL_ENVELOPE.market.nifty),
                          last_price: price,
                          change: changePts,
                          change_pct: changePct,
                          high: high,
                          low: low,
                          open: tick.open ?? base.market?.nifty?.open ?? price,
                          volume: tick.volume ?? base.market?.nifty?.volume,
                          quality: "LIVE",
                        },
                      },
                      price_structure: {
                        ...(base.price_structure || EMPTY_CANONICAL_ENVELOPE.price_structure),
                        last_price: price,
                        high: high,
                        low: low,
                        change: changePts,
                        change_pct: changePct,
                        quality: "LIVE",
                      },
                      candles: {
                        ...(base.candles || EMPTY_CANONICAL_ENVELOPE.candles),
                        "1m": existing1m,
                      },
                    };
                  } else if (isVix) {
                    return {
                      ...base,
                      market: {
                        ...(base.market || EMPTY_CANONICAL_ENVELOPE.market),
                        vix: {
                          ...(base.market?.vix || EMPTY_CANONICAL_ENVELOPE.market.vix),
                          last_price: price,
                          change: tick.change_points ?? tick.change ?? base.market?.vix?.change,
                          change_pct: tick.change_pct ?? base.market?.vix?.change_pct,
                          quality: "LIVE",
                        },
                      },
                    };
                  }
                  return base;
                });
                setLastUpdated(new Date());
                setIsConnected(true);
              }
            }
          } catch (err) {
            console.warn("WebSocket packet parse error:", err);
          }
        };

        ws.onerror = () => {
          setIsConnected(false);
        };

        ws.onclose = () => {
          if (!isUnmounted) {
            setIsConnected(false);
            reconnectTimeout = setTimeout(connectWebSocket, 2000);
          }
        };
      } catch {
        if (!isUnmounted) {
          reconnectTimeout = setTimeout(connectWebSocket, 2000);
        }
      }
    };

    connectWebSocket();

    return () => {
      isUnmounted = true;
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, []);

  // 2. REST poll fallback ONLY while disconnected or waiting for initial envelope (pauses on tab inactivity)
  useEffect(() => {
    let isMounted = true;
    if (isConnected && liveEnvelope && liveEnvelope.runtime_id !== "stream_init") {
      return;
    }

    const fetchCanonicalState = async () => {
      if (typeof document !== "undefined" && document.hidden) {
        return; // Pause polling on tab inactivity to prevent background thrashing
      }
      try {
        const res = await fetch("/api/canonical/envelope");
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data && data.runtime_id && data.runtime_id !== "stream_init") {
            applyIncomingEnvelope(data);
          }
        }
      } catch {
        // Fallback gracefully
      }
    };

    fetchCanonicalState();
    const interval = setInterval(fetchCanonicalState, 3000);

    const handleVisibilityChange = () => {
      if (typeof document !== "undefined" && !document.hidden) {
        fetchCanonicalState();
      }
    };
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", handleVisibilityChange);
    }

    return () => {
      isMounted = false;
      clearInterval(interval);
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", handleVisibilityChange);
      }
    };
  }, [isConnected, liveEnvelope]);


  const isStale = useMemo(() => {
    const q = envelope.data_quality;
    const feed = envelope.feed_health?.overall_status;
    const hasLivePrice = envelope.market?.nifty?.last_price != null || envelope.price_structure?.last_price != null;
    if (q === "LIVE" || q === "VALID") return false;
    if (hasLivePrice && q !== "STALE" && feed !== "STALE") return false;
    return q === "STALE" || q === "UNAVAILABLE" || feed === "STALE" || feed === "NOT_RUNNING";
  }, [envelope]);

  const value = useMemo(
    () => ({
      presentationMode: "CANONICAL_UI" as PresentationMode,
      setPresentationMode: (_mode: PresentationMode) => {},
      sourceMode: "CANONICAL_LIVE" as WorkstationSourceMode,
      setSourceMode: (_mode: WorkstationSourceMode) => {},
      previewPhase,
      setPreviewPhase,
      enablePhasePreview: ENABLE_PHASE_PREVIEW,
      traderMode,
      envelope,
      isConnected,
      lastUpdated,
      runtimeId: lastRuntimeId || envelope.runtime_id,
      stateRevision: lastRevision || envelope.state_revision,
      quality: envelope.data_quality,
      marketPhase: envelope.session?.market_phase || "PRE_MARKET",
      isStale,
      isFixtureData,
      sessionIdentity,
      sessionPhase: sessionIdentity.sessionPhase,
      intelligenceMode: sessionIdentity.intelligenceMode,
      dataWindow: sessionIdentity.data_window,
      isReplayMode,
      settledSession: envelope.settled_session || null,
      hasSettledSession: Boolean(envelope.settled_session?.close != null || envelope.market?.nifty?.previous_close != null || envelope.price_structure?.previous_close != null),
      isLiveStreaming: Boolean(envelope.data_quality !== "UNAVAILABLE" && (envelope.market?.nifty?.last_price != null || envelope.price_structure?.last_price != null)),
    }),
    [
      previewPhase,
      traderMode,
      envelope,
      isConnected,
      lastUpdated,
      lastRuntimeId,
      lastRevision,
      isStale,
      isFixtureData,
      sessionIdentity,
      isReplayMode,
    ]
  );

  return (
    <CanonicalStateContext.Provider value={value}>
      {children}
    </CanonicalStateContext.Provider>
  );
}

export function useCanonicalState() {
  const context = useContext(CanonicalStateContext);
  if (!context) {
    throw new Error("useCanonicalState must be used within a CanonicalStateProvider");
  }
  return context;
}

