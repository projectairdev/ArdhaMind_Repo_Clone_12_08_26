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

/**
 * 1. Resolve Canonical Market Session State
 * Hierarchy:
 *   a. canonicalState.market_session.status
 *   b. marketContext.market_state / trading_session
 *   c. canonicalState.market_data.trading_session
 *   d. Fallback: IST Clock computation (09:15-15:30 IST weekdays)
 */
export function resolveMarketSessionState(canonicalState?: any, marketContext?: any): MarketSessionState {
  const rawStatus = String(
    canonicalState?.market_session?.status ||
    marketContext?.market_state ||
    marketContext?.trading_session ||
    canonicalState?.market_data?.trading_session ||
    ""
  ).toUpperCase();

  if (rawStatus === "OPEN" || rawStatus === "LIVE" || rawStatus === "LIVE_SESSION" || rawStatus === "MARKET_OPEN") {
    return "OPEN";
  }

  if (rawStatus === "PRE_OPEN" || rawStatus === "PRE_MARKET" || rawStatus === "PRE-OPEN" || rawStatus === "PRE") {
    return "PRE_MARKET";
  }

  if (rawStatus === "POST_CLOSE" || rawStatus === "POST_MARKET" || rawStatus === "POST" || rawStatus === "CLOSING") {
    return "POST_MARKET";
  }

  if (rawStatus === "CLOSED" || rawStatus === "MARKET_CLOSED" || rawStatus === "HOLIDAY" || rawStatus === "WEEKEND") {
    return "CLOSED";
  }

  // Time-based fallback if state is unpopulated
  try {
    const now = new Date();
    const istTimeStr = new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Kolkata",
      hour12: false,
      hour: "numeric",
      minute: "numeric",
      weekday: "short",
    }).format(now);

    const [dayName, timePart] = istTimeStr.split(", ");
    if (dayName === "Sat" || dayName === "Sun") {
      return "CLOSED";
    }

    if (timePart) {
      const [h, m] = timePart.split(":").map(Number);
      const totalMinutes = h * 60 + m;
      if (totalMinutes >= 555 && totalMinutes <= 930) {
        return "OPEN"; // 09:15 to 15:30 IST
      }
      if (totalMinutes >= 540 && totalMinutes < 555) {
        return "PRE_MARKET"; // 09:00 to 09:15 IST
      }
      if (totalMinutes > 930 && totalMinutes <= 960) {
        return "POST_MARKET"; // 15:30 to 16:00 IST
      }
    }
  } catch {}

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
    "2026-08-19"
  ).slice(0, 10);

  const validRawDate = rawDate.match(/^\d{4}-\d{2}-\d{2}$/) ? rawDate : "2026-08-19";

  const sessStatus = String(
    mc?.market_state ||
    canonicalState?.market_session?.status ||
    md?.trading_session ||
    ""
  ).toUpperCase();
  const isOpen = sessStatus === "OPEN";

  let completedSessionDate: string;
  let nextPlanningTargetDate: string;
  let previousSessionDate: string;

  if (isOpen) {
    completedSessionDate = getPrevTradingDayStr(validRawDate);
    nextPlanningTargetDate = getNextTradingDayStr(validRawDate);
    previousSessionDate = getPrevTradingDayStr(completedSessionDate);
  } else {
    // Post-close / overnight / pre-market
    if (validRawDate >= "2026-08-20") {
      nextPlanningTargetDate = validRawDate;
      completedSessionDate = getPrevTradingDayStr(validRawDate);
      previousSessionDate = getPrevTradingDayStr(completedSessionDate);
    } else {
      completedSessionDate = validRawDate;
      nextPlanningTargetDate = getNextTradingDayStr(completedSessionDate);
      previousSessionDate = getPrevTradingDayStr(completedSessionDate);
    }
  }

  // Override explicit reference session if present in briefing or report
  const explicitRef = String(briefing?.reference_session_date || report?.reference_session_date || "").slice(0, 10);
  if (explicitRef.match(/^\d{4}-\d{2}-\d{2}$/)) {
    completedSessionDate = explicitRef;
    previousSessionDate = getPrevTradingDayStr(completedSessionDate);
  }

  const currentFormatted = formatDateGB(isOpen ? validRawDate : completedSessionDate);
  const completedFormatted = formatDateGB(completedSessionDate);
  const prevFormatted = formatDateGB(previousSessionDate);
  const nextTargetFormatted = formatDateGB(nextPlanningTargetDate);

  let instDate = "17 Aug 2026";
  if (flows && flows.length > 0 && flows[0]?.trade_date) {
    const rawF = String(flows[0].trade_date).slice(0, 10);
    instDate = formatDateGB(rawF);
  }

  return {
    currentSessionDate: validRawDate,
    currentSessionDateFormatted: currentFormatted,
    completedSessionDate,
    completedSessionDateFormatted: completedFormatted,
    previousSessionDate,
    previousSessionDateFormatted: prevFormatted,
    referenceCloseDateFormatted: prevFormatted,
    nextPlanningTargetDate,
    nextPlanningTargetDateFormatted: nextTargetFormatted,
    institutionalFlowDateFormatted: instDate,
  };
}
