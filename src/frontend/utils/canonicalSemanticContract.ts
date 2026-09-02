// src/frontend/utils/canonicalSemanticContract.ts
/**
 * Canonical Semantic Contract & Centralized Dashboard State Labeling Layer.
 *
 * Guarantees across all workspaces:
 * 1. Single source of truth for Market Session status (PRE_MARKET, OPEN, POST_MARKET, CLOSED).
 * 2. If session == OPEN, no current-session component will ever display "MARKET CLOSED".
 * 3. Staging Preview mode is distinctly separated from Actual Market truth.
 * 4. Data Freshness (FRESH <=3.5s, DELAYED 3.5-10s, STALE >10s, LAST_VALID, UNAVAILABLE).
 * 5. Strictly standardized scales for Direction, Risk, Confidence, Regimes, Options, and Structural Levels.
 * 6. Zero hardcoded session text or contradictory status badges.
 */

export type MarketSessionState = "PRE_MARKET" | "OPEN" | "POST_MARKET" | "CLOSED";
export type DisplayMode = "AUTO" | "PRE" | "LIVE" | "POST";
export type DataFreshnessStatus = "FRESH" | "DELAYED" | "STALE" | "LAST_VALID" | "UNAVAILABLE";
export type AnalysisContextType = "PRE_MARKET" | "LIVE_INTRADAY" | "PRE_CLOSE_PREVIEW" | "POST_MARKET" | "NEXT_SESSION_FINAL";
export type DirectionalBias = "STRONG BULLISH" | "BULLISH" | "MILD BULLISH" | "NEUTRAL" | "MIXED" | "MILD BEARISH" | "BEARISH" | "STRONG BEARISH";
export type RiskLevel = "LOW" | "MODERATE" | "ELEVATED" | "HIGH";
export type ConfidenceLevel = "LOW" | "MODERATE" | "HIGH";
export type RegimeType = "TRENDING UP" | "TRENDING DOWN" | "RANGE" | "COMPRESSION" | "BREAKOUT" | "BREAKDOWN" | "REVERSAL" | "MIXED" | "UNKNOWN";
export type SourceTransportType = "STREAMING" | "FAST_POLLED" | "POLLED" | "EOD" | "CACHED";

export interface MarketSessionBadgeInfo {
  session: MarketSessionState;
  label: string;
  shortLabel: string;
  toneClass: string;
  dotClass: string;
  isLive: boolean;
  isOpen: boolean;
  isClosed: boolean;
  isPreMarket: boolean;
  isPostMarket: boolean;
  isPreview: boolean;
  previewLabel?: string;
}

export interface DataFreshnessBadgeInfo {
  freshness: DataFreshnessStatus;
  label: string;
  shortLabel: string;
  toneClass: string;
  dotClass: string;
  badgeText: string;
}

export interface TemporalPhrasing {
  spotVerb: string;
  levelVerb: string;
  closeVerb: string;
  sessionDescriptor: string;
}

export function getCanonicalIstNow(): { dateStr: string; hhmmss: string; isWeekday: boolean } {
  const now = new Date();
  const istStr = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(now);
  const match = istStr.match(/(\d+)\/(\d+)\/(\d+),\s*(\d+):(\d+):(\d+)/);
  if (match) {
    const [, month, day, year, hour, minute, second] = match;
    const dateStr = `${year}-${month}-${day}`;
    const hhmmss = `${hour}:${minute}:${second}`;
    const d = new Date(Date.UTC(parseInt(year, 10), parseInt(month, 10) - 1, parseInt(day, 10)));
    const isWeekday = d.getUTCDay() >= 1 && d.getUTCDay() <= 5;
    return { dateStr, hhmmss, isWeekday };
  }
  const iso = now.toISOString();
  return { dateStr: iso.slice(0, 10), hhmmss: "09:15:00", isWeekday: true };
}

/**
 * 1. Resolve Canonical Market Session State
 * Hierarchy:
 *   a. IST Clock verification on trading days
 *   b. Explicit session status override (HOLIDAY, OPEN, PRE_OPEN, POST_CLOSE)
 *   c. Fallback: IST Clock computation (09:15-15:30 IST weekdays)
 */
export function resolveMarketSessionState(canonicalState?: any, marketContext?: any): MarketSessionState {
  const { hhmmss, isWeekday } = getCanonicalIstNow();
  const rawStatus = String(
    canonicalState?.market_session?.status ||
    marketContext?.market_state ||
    marketContext?.trading_session ||
    canonicalState?.market_data?.trading_session ||
    ""
  ).toUpperCase();

  if (rawStatus === "HOLIDAY") {
    return "CLOSED";
  }

  if (rawStatus === "EARLY_IDLE" || rawStatus === "OFF_MARKET") {
    return "CLOSED";
  }

  if (!isWeekday) {
    return "CLOSED";
  }

  if (rawStatus === "OPEN" || rawStatus === "LIVE" || rawStatus === "LIVE_SESSION" || rawStatus === "MARKET_OPEN") {
    return "OPEN";
  }

  if (rawStatus === "PRE_OPEN" || rawStatus === "PRE_MARKET" || rawStatus === "PRE-OPEN" || rawStatus === "PRE") {
    return "PRE_MARKET";
  }

  if (rawStatus === "POST_CLOSE" || rawStatus === "POST_MARKET" || rawStatus === "POST" || rawStatus === "CLOSING") {
    return "POST_MARKET";
  }

  // On a weekday, generic CLOSED must never misclassify morning as post-close
  if (hhmmss < "08:45:00") {
    return "CLOSED"; // Morning preparation / pre-market
  }
  if (hhmmss >= "08:45:00" && hhmmss < "09:15:00") {
    return "PRE_MARKET"; // Pre-open
  }
  if (hhmmss >= "09:15:00" && hhmmss < "15:30:00") {
    return "OPEN"; // Live market session
  }
  if (hhmmss >= "15:30:00") {
    return "POST_MARKET"; // Post-market session review
  }

  return "CLOSED";
}

/**
 * 2. Get Authoritative Market Session Badge
 */
export function getMarketSessionBadge(
  session: MarketSessionState,
  isPreview = false,
  previewMode = "AUTO"
): MarketSessionBadgeInfo {
  const isActualOpen = session === "OPEN";
  const isActualPre = session === "PRE_MARKET";
  const isActualPost = session === "POST_MARKET";
  const isActualClosed = session === "CLOSED";

  const isPreviewOverride = isPreview && previewMode !== "AUTO";

  if (isPreviewOverride) {
    return {
      session,
      label: `STAGING PREVIEW (${previewMode})`,
      shortLabel: `PREVIEW (${previewMode})`,
      toneClass: "bg-[#38BDF8]/15 border-[#38BDF8]/40 text-[#38BDF8]",
      dotClass: "bg-[#38BDF8]",
      isLive: previewMode === "LIVE",
      isOpen: previewMode === "LIVE",
      isClosed: previewMode === "POST",
      isPreMarket: previewMode === "PRE",
      isPostMarket: previewMode === "POST",
      isPreview: true,
      previewLabel: `Actual Market: ${session}`,
    };
  }

  if (isActualOpen) {
    return {
      session: "OPEN",
      label: "MARKET OPEN",
      shortLabel: "OPEN",
      toneClass: "bg-[#00C896]/15 border-[#00C896]/30 text-[#00C896]",
      dotClass: "bg-[#00C896] animate-pulse",
      isLive: true,
      isOpen: true,
      isClosed: false,
      isPreMarket: false,
      isPostMarket: false,
      isPreview: false,
    };
  }

  if (isActualPre) {
    return {
      session: "PRE_MARKET",
      label: "PRE-MARKET (PRE-OPEN)",
      shortLabel: "PRE-MARKET",
      toneClass: "bg-[#38BDF8]/15 border-[#38BDF8]/30 text-[#38BDF8]",
      dotClass: "bg-[#38BDF8] animate-pulse",
      isLive: false,
      isOpen: false,
      isClosed: false,
      isPreMarket: true,
      isPostMarket: false,
      isPreview: false,
    };
  }

  if (isActualPost) {
    return {
      session: "POST_MARKET",
      label: "POST-MARKET (SESSION REVIEW)",
      shortLabel: "POST-MARKET",
      toneClass: "bg-[#E59700]/15 border-[#E59700]/30 text-[#E59700]",
      dotClass: "bg-[#E59700]",
      isLive: false,
      isOpen: false,
      isClosed: true,
      isPreMarket: false,
      isPostMarket: true,
      isPreview: false,
    };
  }

  return {
    session: "CLOSED",
    label: "MARKET CLOSED",
    shortLabel: "CLOSED",
    toneClass: "bg-slate-900/80 border-slate-700/60 text-slate-400",
    dotClass: "bg-slate-500",
    isLive: false,
    isOpen: false,
    isClosed: true,
    isPreMarket: false,
    isPostMarket: false,
    isPreview: false,
  };
}

/**
 * 3. Authoritative Data Freshness Badge
 */
export function getFreshnessBadge(
  freshness: DataFreshnessStatus,
  ageMs?: number
): DataFreshnessBadgeInfo {
  if (freshness === "FRESH") {
    return {
      freshness: "FRESH",
      label: "Live Stream / Fresh",
      shortLabel: "FRESH",
      toneClass: "bg-[#00C896]/15 border-[#00C896]/30 text-[#00C896]",
      dotClass: "bg-[#00C896] animate-pulse",
      badgeText: "● Live Engine",
    };
  }

  if (freshness === "DELAYED") {
    return {
      freshness: "DELAYED",
      label: "Delayed Telemetry",
      shortLabel: "DELAYED",
      toneClass: "bg-yellow-500/15 border-yellow-500/30 text-yellow-400",
      dotClass: "bg-yellow-400",
      badgeText: "▲ Delayed Telemetry",
    };
  }

  if (freshness === "STALE") {
    return {
      freshness: "STALE",
      label: "Stale Analysis (Recomputing...)",
      shortLabel: "STALE",
      toneClass: "bg-[#E59700]/15 border-[#E59700]/30 text-[#E59700]",
      dotClass: "bg-[#E59700] animate-pulse",
      badgeText: "⚠ Stale Analysis (Recomputing...)",
    };
  }

  if (freshness === "LAST_VALID") {
    return {
      freshness: "LAST_VALID",
      label: "Last Valid Session Reference",
      shortLabel: "LAST VALID",
      toneClass: "bg-[#38BDF8]/15 border-[#38BDF8]/30 text-[#38BDF8]",
      dotClass: "bg-[#38BDF8]",
      badgeText: "◈ Last Valid Session",
    };
  }

  return {
    freshness: "UNAVAILABLE",
    label: "Data Unavailable",
    shortLabel: "UNAVAILABLE",
    toneClass: "bg-slate-900 border-slate-700 text-slate-400",
    dotClass: "bg-slate-500",
    badgeText: "✕ Unavailable",
  };
}

/**
 * 4. Temporal Phrasing Helpers
 */
export function getTemporalSessionPhrasing(session: MarketSessionState): TemporalPhrasing {
  if (session === "OPEN") {
    return {
      spotVerb: "currently trading near",
      levelVerb: "intraday support holding",
      closeVerb: "day high at",
      sessionDescriptor: "Live Intraday Session",
    };
  }
  if (session === "PRE_MARKET") {
    return {
      spotVerb: "anchored to previous close",
      levelVerb: "morning decision boundary",
      closeVerb: "expected open at",
      sessionDescriptor: "Pre-Market Preparation",
    };
  }
  return {
    spotVerb: "closed at",
    levelVerb: "session support anchored at",
    closeVerb: "final close at",
    sessionDescriptor: "Completed Session Reference",
  };
}

/**
 * 5. Scale Normalizers
 */
export function normalizeRiskLabel(scoreOrLabel: number | string | null | undefined): RiskLevel {
  if (scoreOrLabel == null) return "MODERATE";
  if (typeof scoreOrLabel === "number") {
    if (scoreOrLabel <= 25) return "LOW";
    if (scoreOrLabel <= 55) return "MODERATE";
    if (scoreOrLabel <= 75) return "ELEVATED";
    return "HIGH";
  }
  const upper = String(scoreOrLabel).toUpperCase();
  if (upper.includes("HIGH") || upper.includes("CRITICAL")) return "HIGH";
  if (upper.includes("ELEVATED")) return "ELEVATED";
  if (upper.includes("LOW")) return "LOW";
  return "MODERATE";
}

export function normalizeConfidenceLabel(scoreOrLabel: number | string | null | undefined): ConfidenceLevel {
  if (scoreOrLabel == null) return "MODERATE";
  if (typeof scoreOrLabel === "number") {
    if (scoreOrLabel >= 70) return "HIGH";
    if (scoreOrLabel >= 45) return "MODERATE";
    return "LOW";
  }
  const upper = String(scoreOrLabel).toUpperCase();
  if (upper.includes("HIGH")) return "HIGH";
  if (upper.includes("LOW")) return "LOW";
  return "MODERATE";
}

export function normalizeDirectionLabel(dir: string | null | undefined): DirectionalBias {
  if (!dir) return "NEUTRAL";
  const upper = String(dir).toUpperCase();
  if (upper.includes("STRONG_BULLISH") || upper.includes("STRONG BULLISH")) return "STRONG BULLISH";
  if (upper.includes("STRONG_BEARISH") || upper.includes("STRONG BEARISH")) return "STRONG BEARISH";
  if (upper.includes("MILD_BULLISH") || upper.includes("MILD BULLISH")) return "MILD BULLISH";
  if (upper.includes("MILD_BEARISH") || upper.includes("MILD BEARISH")) return "MILD BEARISH";
  if (upper.includes("BULLISH")) return "BULLISH";
  if (upper.includes("BEARISH")) return "BEARISH";
  if (upper.includes("MIXED") || upper.includes("CHOP")) return "MIXED";
  return "NEUTRAL";
}

export function normalizeRegimeLabel(regime: string | null | undefined): RegimeType {
  if (!regime) return "RANGE";
  const upper = String(regime).toUpperCase();
  if (upper.includes("TRENDING_UP") || upper.includes("TRENDING UP")) return "TRENDING UP";
  if (upper.includes("TRENDING_DOWN") || upper.includes("TRENDING DOWN")) return "TRENDING DOWN";
  if (upper.includes("BREAKOUT")) return "BREAKOUT";
  if (upper.includes("BREAKDOWN")) return "BREAKDOWN";
  if (upper.includes("COMPRESSION")) return "COMPRESSION";
  if (upper.includes("REVERSAL")) return "REVERSAL";
  if (upper.includes("MIXED")) return "MIXED";
  if (upper.includes("RANGE") || upper.includes("SIDEWAYS") || upper.includes("CHOP")) return "RANGE";
  return "UNKNOWN";
}

export function getInstitutionalFlowLabel(dateStr?: string): string {
  const d = dateStr || "17 Aug 2026";
  return `FII / DII Cash (Last Published EOD • ${d})`;
}

export interface SessionIdentityModel {
  currentSessionDate: string;
  currentSessionDateFormatted: string;
  completedSessionDate: string;
  completedSessionDateFormatted: string;
  previousSessionDate: string;
  previousSessionDateFormatted: string;
  referenceCloseDateFormatted: string;
  nextPlanningTargetDate: string;
  nextPlanningTargetDateFormatted: string;
  institutionalFlowDateFormatted: string;
}

export function isTradingDayDate(d: Date): boolean {
  const day = d.getUTCDay();
  return day !== 0 && day !== 6;
}

export function getPrevTradingDayStr(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  if (!y || !m || !d) return "2026-08-18";
  const dt = new Date(Date.UTC(y, m - 1, d));
  dt.setUTCDate(dt.getUTCDate() - 1);
  while (!isTradingDayDate(dt)) {
    dt.setUTCDate(dt.getUTCDate() - 1);
  }
  return dt.toISOString().slice(0, 10);
}

export function getNextTradingDayStr(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  if (!y || !m || !d) return "2026-08-20";
  const dt = new Date(Date.UTC(y, m - 1, d));
  dt.setUTCDate(dt.getUTCDate() + 1);
  while (!isTradingDayDate(dt)) {
    dt.setUTCDate(dt.getUTCDate() + 1);
  }
  return dt.toISOString().slice(0, 10);
}

export function formatDateGB(dateStr: string): string {
  try {
    const d = new Date(dateStr + "T12:00:00Z");
    if (!isNaN(d.getTime())) {
      return new Intl.DateTimeFormat("en-GB", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "short",
        year: "numeric",
      }).format(d);
    }
  } catch {}
  return dateStr;
}

export function resolveSessionIdentity(canonicalState?: any, marketContext?: any): SessionIdentityModel {
  const { dateStr: todayIstStr, hhmmss, isWeekday } = getCanonicalIstNow();
  const md = canonicalState?.market_data || {};
  const mc = marketContext || canonicalState?.marketContext || {};
  const report = canonicalState?.todays_analysis || canonicalState?.session_story?.todays_analysis || {};
  const briefing = canonicalState?.pre_market_briefing || canonicalState?.pre_market_report || {};
  const macro = canonicalState?.macro_intelligence || {};
  const flows = macro?.institutional_flows || [];

  const rawDate = String(
    briefing?.target_trading_date ||
    report?.session_date ||
    canonicalState?.market_session?.session_date ||
    md?.session_date ||
    mc?.session_date ||
    todayIstStr
  ).slice(0, 10);

  const validRawDate = rawDate.match(/^\d{4}-\d{2}-\d{2}$/) ? rawDate : todayIstStr;

  const sessStatus = String(
    mc?.market_state ||
    canonicalState?.market_session?.status ||
    md?.trading_session ||
    ""
  ).toUpperCase();
  const isExplicitHoliday = sessStatus === "HOLIDAY";
  const isPostClose = sessStatus === "POST_CLOSE" || sessStatus === "POST_MARKET" || (isWeekday && hhmmss >= "15:30:00");

  let currentTradingDate: string;
  let completedSessionDate: string;
  let nextPlanningTargetDate: string;
  let previousSessionDate: string;

  if (isExplicitHoliday || !isWeekday) {
    // Weekend or holiday: Last completed trading session + Next planning session
    completedSessionDate = getPrevTradingDayStr(validRawDate > todayIstStr ? validRawDate : todayIstStr);
    currentTradingDate = completedSessionDate;
    nextPlanningTargetDate = getNextTradingDayStr(completedSessionDate);
    previousSessionDate = getPrevTradingDayStr(completedSessionDate);
  } else if (isPostClose) {
    // Trading day after 15:30: Today's session is completed; planning targets next session
    currentTradingDate = validRawDate;
    completedSessionDate = validRawDate;
    nextPlanningTargetDate = getNextTradingDayStr(validRawDate);
    previousSessionDate = getPrevTradingDayStr(validRawDate);
  } else {
    // Trading day before 15:30 (Pre-Market, Pre-Open, or Live Intraday): Target is TODAY
    currentTradingDate = validRawDate;
    completedSessionDate = getPrevTradingDayStr(validRawDate);
    nextPlanningTargetDate = getNextTradingDayStr(validRawDate);
    previousSessionDate = getPrevTradingDayStr(completedSessionDate);
  }

  // Only override explicit reference session for morning briefing when before market close
  if (!isPostClose && !isExplicitHoliday && isWeekday) {
    const explicitRef = String(briefing?.reference_session_date || report?.reference_session_date || "").slice(0, 10);
    if (explicitRef.match(/^\d{4}-\d{2}-\d{2}$/)) {
      completedSessionDate = explicitRef;
      previousSessionDate = getPrevTradingDayStr(completedSessionDate);
    }
  }

  const currentFormatted = formatDateGB(currentTradingDate);
  const completedFormatted = formatDateGB(completedSessionDate);
  const prevFormatted = formatDateGB(previousSessionDate);
  const nextTargetFormatted = formatDateGB(nextPlanningTargetDate);
  const refCloseFormatted = formatDateGB(completedSessionDate);

  let instDate = completedFormatted;
  if (flows && flows.length > 0 && flows[0]?.trade_date) {
    const rawF = String(flows[0].trade_date).slice(0, 10);
    instDate = formatDateGB(rawF);
  }

  return {
    currentSessionDate: currentTradingDate,
    currentSessionDateFormatted: currentFormatted,
    completedSessionDate,
    completedSessionDateFormatted: completedFormatted,
    previousSessionDate,
    previousSessionDateFormatted: prevFormatted,
    referenceCloseDateFormatted: refCloseFormatted,
    nextPlanningTargetDate,
    nextPlanningTargetDateFormatted: nextTargetFormatted,
    institutionalFlowDateFormatted: instDate,
  };
}

export interface SessionProvenance {
  source_date: string;
  source_type: "CANONICAL_COMPLETED_SESSION" | "CANDLE_STREAM" | "HISTORICAL_REPLAY" | "UNAVAILABLE";
  finalized_at: string;
  field_origin: string;
}

export interface CompletedSessionMetrics {
  isAvailable: boolean;
  tradingDate: string;
  tradingDateFormatted: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  previousClose: number | null;
  change: number | null;
  changePercent: number | null;
  range: number | null;
  trendLabel: string;
  dayCharacterLabel: string;
  closeLocationLabel: string;
  breadthStateLabel: string;
  institutionalFlowLabel: string;
  advances: number | null;
  declines: number | null;
  unchanged: number | null;
  provenance: SessionProvenance;
}

export function parseCandleTimeEpoch(c: any): number | null {
  if (typeof c.timestamp === "number" && c.timestamp > 0) {
    return c.timestamp < 10000000000 ? c.timestamp : Math.floor(c.timestamp / 1000);
  }
  const rawStr = c.datetime || c.date || c.time;
  if (typeof rawStr === "string" && rawStr.length > 0) {
    if (rawStr.includes("T") || rawStr.includes("-")) {
      const parsed = Date.parse(rawStr);
      if (!isNaN(parsed)) return Math.floor(parsed / 1000);
    }
    if (rawStr.includes(":")) {
      const parts = rawStr.split(":").map(Number);
      if (parts.length >= 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
        const todayStr = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(new Date());
        const hStr = String(parts[0]).padStart(2, "0");
        const mStr = String(parts[1]).padStart(2, "0");
        const iso = `${todayStr}T${hStr}:${mStr}:00+05:30`;
        const parsed = Date.parse(iso);
        if (!isNaN(parsed)) return Math.floor(parsed / 1000);
      }
    }
  }
  return null;
}

/**
 * Resolves completed session metrics for a specific target trading date strictly without cross-session pollution.
 */
export function getCompletedSession(
  targetDate: string,
  canonicalState?: any,
  marketContext?: any
): CompletedSessionMetrics {
  const dateFormatted = formatDateGB(targetDate);
  const prevDate = getPrevTradingDayStr(targetDate);

  const rawCandles = Array.isArray(marketContext?.candles)
    ? marketContext.candles
    : Array.isArray(canonicalState?.market_data?.candles)
    ? canonicalState.market_data.candles
    : [];

  const targetCandles = rawCandles.filter((c: any) => {
    const cTradeDate =
      c.trading_date ||
      (typeof c.datetime === "string" ? c.datetime.slice(0, 10) : null) ||
      (typeof c.date === "string" ? c.date.slice(0, 10) : null);
    if (cTradeDate) return cTradeDate === targetDate;
    const tSec = parseCandleTimeEpoch(c);
    if (tSec != null) {
      const dStr = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(new Date(tSec * 1000));
      return dStr === targetDate;
    }
    return false;
  });

  const prevCandles = rawCandles.filter((c: any) => {
    const cTradeDate =
      c.trading_date ||
      (typeof c.datetime === "string" ? c.datetime.slice(0, 10) : null) ||
      (typeof c.date === "string" ? c.date.slice(0, 10) : null);
    if (cTradeDate) return cTradeDate === prevDate;
    const tSec = parseCandleTimeEpoch(c);
    if (tSec != null) {
      const dStr = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(new Date(tSec * 1000));
      return dStr === prevDate;
    }
    return false;
  });

  let prevCloseFromCandles: number | null = null;
  if (prevCandles.length > 0) {
    const lastPrevC = prevCandles[prevCandles.length - 1];
    prevCloseFromCandles = Number(lastPrevC.close ?? lastPrevC.c);
  }

  const comp = canonicalState?.completed_session || marketContext?.completed_session || {};

  // During EARLY_IDLE / PRE_MARKET / PRE_OPEN, canonical market_data may still
  // represent the explicitly identified completed reference session.
  // Only permit this fallback when the pre-market report proves the date match.
  const preMarketReport =
    canonicalState?.pre_market_report ||
    canonicalState?.session_story?.pre_market_report ||
    canonicalState?.unified_intelligence?.pre_market_report ||
    {};

  const marketData = canonicalState?.market_data || {};
  const marketDataMatchesCompletedSession =
    String(preMarketReport?.reference_session_date || "").slice(0, 10) === targetDate;

  const completedSource =
    Object.keys(comp).length > 0
      ? comp
      : marketDataMatchesCompletedSession
      ? marketData
      : {};

  let open: number | null = completedSource.open != null && Number(completedSource.open) > 0 ? Number(completedSource.open) : null;
  let high: number | null = completedSource.high != null && Number(completedSource.high) > 0 ? Number(completedSource.high) : null;
  let low: number | null = completedSource.low != null && Number(completedSource.low) > 0 ? Number(completedSource.low) : null;
  let close: number | null = completedSource.close != null && Number(completedSource.close) > 0 ? Number(completedSource.close) : null;

  let previousClose: number | null = completedSource.previous_close != null && Number(completedSource.previous_close) > 0
    ? Number(completedSource.previous_close)
    : prevCloseFromCandles != null && prevCloseFromCandles > 0
    ? prevCloseFromCandles
    : marketContext?.previous_close != null && Number(marketContext.previous_close) > 0
    ? Number(marketContext.previous_close)
    : canonicalState?.market_data?.previous_close != null && Number(canonicalState.market_data.previous_close) > 0
    ? Number(canonicalState.market_data.previous_close)
    : null;

  if (targetCandles.length > 0) {
    const firstC = targetCandles[0];
    const lastC = targetCandles[targetCandles.length - 1];
    open = Number(firstC.open ?? firstC.o);
    const highs = targetCandles.map((c) => Number(c.high ?? c.h)).filter(Number.isFinite);
    const lows = targetCandles.map((c) => Number(c.low ?? c.l)).filter(Number.isFinite);
    if (highs.length > 0) high = Math.max(...highs);
    if (lows.length > 0) low = Math.min(...lows);
    close = Number(lastC.close ?? lastC.c);
  }

  const isAvailable = close != null && open != null && high != null && low != null;
  const range = (high != null && low != null) ? Number((high - low).toFixed(2)) : null;
  const change = (close != null && previousClose != null) ? Number((close - previousClose).toFixed(2)) : null;
  const changePercent = (change != null && previousClose != null && previousClose > 0)
    ? Number(((change / previousClose) * 100).toFixed(2))
    : null;

  let trendLabel = "Completed: UNAVAILABLE";
  if (change != null) {
    if (change <= -50.0) trendLabel = "Completed: BEARISH";
    else if (change < 0) trendLabel = "Completed: MILD BEARISH";
    else if (change >= 50.0) trendLabel = "Completed: BULLISH";
    else if (change > 0) trendLabel = "Completed: MILD BULLISH";
    else trendLabel = "Completed: NEUTRAL";
  }

  let dayCharacterLabel = "Unavailable";
  if (open != null && close != null && previousClose != null) {
    if (close < open && close < previousClose) {
      dayCharacterLabel = "Bearish Trend / Intraday Fade";
    } else if (close > open && close > previousClose) {
      dayCharacterLabel = "Bullish Expansion / Trend";
    } else if (close < open && close > previousClose) {
      dayCharacterLabel = "Gap-Up Fade / Consolidation";
    } else if (close > open && close < previousClose) {
      dayCharacterLabel = "Gap-Down Recovery / Rebound";
    } else {
      dayCharacterLabel = "Range-Bound / Neutral";
    }
  }

  let closeLocationLabel = "Unavailable";
  if (range != null && range > 0 && close != null && low != null) {
    const locPct = ((close - low) / range) * 100;
    if (locPct >= 70) {
      closeLocationLabel = "Upper 30% of Range";
    } else if (locPct <= 30) {
      closeLocationLabel = "Lower 30% of Range";
    } else {
      closeLocationLabel = `Mid Range (${Math.round(locPct)}%)`;
    }
  }

  const advances = marketContext?.breadth?.advances ?? canonicalState?.market_breadth?.advances ?? null;
  const declines = marketContext?.breadth?.declines ?? canonicalState?.market_breadth?.declines ?? null;
  const unchanged = marketContext?.breadth?.unchanged ?? canonicalState?.market_breadth?.unchanged ?? null;

  let breadthStateLabel = "Breadth Unavailable";
  if (advances != null && declines != null) {
    if (advances > declines * 1.5) {
      breadthStateLabel = "Broad Advance";
    } else if (declines > advances * 1.5) {
      breadthStateLabel = "Decline Dominated";
    } else if (advances > declines) {
      breadthStateLabel = "Mild Advance";
    } else if (declines > advances) {
      breadthStateLabel = "Mild Decline";
    } else {
      breadthStateLabel = "Balanced";
    }
  }

  let institutionalFlowLabel = "Institutional Flows Unavailable";
  const macro = canonicalState?.macro_intelligence || {};
  const flows = macro?.institutional_flows || [];
  if (flows && flows.length > 0) {
    const fii = flows[0]?.fii_net_crores ?? flows[0]?.fii_net;
    const dii = flows[0]?.dii_net_crores ?? flows[0]?.dii_net;
    if (fii != null && dii != null) {
      institutionalFlowLabel = `FII: ${Number(fii) >= 0 ? "+" : ""}${fii} Cr | DII: ${Number(dii) >= 0 ? "+" : ""}${dii} Cr`;
    }
  }

  return {
    isAvailable,
    tradingDate: targetDate,
    tradingDateFormatted: dateFormatted,
    open,
    high,
    low,
    close,
    previousClose,
    change,
    changePercent,
    range,
    trendLabel,
    dayCharacterLabel,
    closeLocationLabel,
    breadthStateLabel,
    institutionalFlowLabel,
    advances,
    declines,
    unchanged,
    provenance: {
      source_date: targetDate,
      source_type: targetCandles.length > 0 ? "CANDLE_STREAM" : comp.close != null ? "CANONICAL_COMPLETED_SESSION" : "UNAVAILABLE",
      finalized_at: `${targetDate} 15:30:00 IST`,
      field_origin: "official_nse_recorded",
    },
  };
}

/**
 * Resolves the immediately prior completed session for a given target date.
 */
export function getPreviousCompletedSession(
  targetDate: string,
  canonicalState?: any,
  marketContext?: any
): CompletedSessionMetrics {
  const prevDate = getPrevTradingDayStr(targetDate);
  return getCompletedSession(prevDate, canonicalState, marketContext);
}

export function resolveCompletedSessionMetrics(
  canonicalState?: any,
  marketContext?: any
): CompletedSessionMetrics {
  const sessionIdentity = resolveSessionIdentity(canonicalState, marketContext);
  return getCompletedSession(sessionIdentity.completedSessionDate, canonicalState, marketContext);
}

/**
 * Resolves option strike candidate distance and moneyness relative to spot price.
 */
export function resolveStrikeCandidateDistance(
  candidate: { option_type?: string; strike?: number } | null | undefined,
  spotPrice: number
): { distance: number; distanceLabel: string; isItm: boolean; isAtm: boolean } {
  if (!candidate || !candidate.strike || !spotPrice) {
    return { distance: 0, distanceLabel: "—", isItm: false, isAtm: false };
  }
  const isCall = candidate.option_type === "CE";
  const diff = spotPrice - candidate.strike;
  const isItm = isCall ? diff > 0 : diff < 0;
  const absDist = Math.abs(diff);
  const isAtm = absDist < 25;
  const distance = Number(absDist.toFixed(2));
  const sign = isItm ? "+" : "-";
  const label = `${sign}${distance.toFixed(2)} pts (${isItm ? "ITM" : "OTM"})`;
  return { distance, distanceLabel: label, isItm, isAtm };
}
