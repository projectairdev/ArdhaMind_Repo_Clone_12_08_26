/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * sessionPhaseEngine.ts
 * Authoritative Single-Source Dual-Clock System for AIR ArdhaMind:
 * 1. sessionPhase — Exchange Truth (Market Data Legality & Freshness)
 * 2. intelligenceMode — Ardha Cognitive Job (Intelligence synthesis & guidance)
 */

export type SessionPhase =
  | "PRE_MARKET"   // 06:00–09:00 IST
  | "PRE_OPEN"     // 09:00–09:15 IST
  | "LIVE"         // 09:15–15:25 IST
  | "NEAR_CLOSE"   // 15:25–15:40 IST
  | "POST_MARKET"; // 15:40–06:00 IST next day

export type IntelligenceMode =
  | "OVERNIGHT_SYNTHESIS" // 15:40 → 08:30 (What happened, what matters, working thesis)
  | "PRE_COMMIT_PLAN"     // 08:30 → 09:00 (1 bias, 2 scenarios, hard invalidation)
  | "AUCTION_READ"        // 09:00 → 09:15 (Indicative/gap vs prior close, auction stress on plan)
  | "OPEN_VALIDATION"     // 09:15 → 09:30 (First 15m OR verdict: CONFIRMED / WEAKENED / INVALIDATED)
  | "REGIME_MONITOR"      // 09:30 → 14:45 (Regime + structure; quiet unless state changes)
  | "DECISION_WINDOW"     // 14:45 → 15:25 (What would change my mind before close?)
  | "CLOSE_TRANSFER";     // 15:25 → 15:40+ (Hand off to overnight synthesis: EOD structure, plan score)

export type DataWindow =
  | "SETTLED_COMPLETED"  // Last completed session (e.g. 28 Aug 2026 EOD)
  | "PRE_OPEN_AUCTION"   // Pre-open indicative snapshot
  | "SESSION_SO_FAR";    // Continuous live forming session

export interface CanonicalSessionIdentity {
  wall_clock_ist: string;               // "06:45:12 IST"
  calendar_date: string;                // "2026-08-31"
  calendar_date_formatted: string;      // "31 Aug 2026"
  sessionPhase: SessionPhase;
  intelligenceMode: IntelligenceMode;
  phase_label: string;
  intelligence_label: string;
  completed_session_date: string;       // "2026-08-28"
  completed_session_date_formatted: string; // "28 Aug 2026"
  active_trading_date: string;          // "2026-08-31"
  active_trading_date_formatted: string;// "31 Aug 2026"
  next_trading_date: string;            // "2026-09-01"
  next_trading_date_formatted: string;  // "01 Sep 2026"
  is_weekend: boolean;
  is_holiday: boolean;
  is_replay_mode: boolean;
  data_window: DataWindow;
  preview_sessionPhase?: SessionPhase;
  preview_intelligenceMode?: IntelligenceMode;
  is_client_time_fallback?: boolean;
}

// 2026 Scheduled NSE Exchange Holidays
// 2026 NSE equity/derivatives trading holidays — weekday closures only.
// Kept in sync with src/market_data/session/exchange_calendar.py and
// src/broker/services/market_status_service.py. Movable-feast names are
// indicative; the date is authoritative. (Aug 15 falls on a Saturday in 2026
// and is not a trading-day closure.)
export const NSE_HOLIDAYS_2026 = new Set<string>([
  "2026-01-26", // Republic Day
  "2026-03-03", // Holi
  "2026-03-26", // NSE trading holiday (movable feast)
  "2026-03-31", // Id-Ul-Fitr (Ramzan Id)
  "2026-04-03", // Good Friday
  "2026-04-14", // Dr. Baba Saheb Ambedkar Jayanti
  "2026-05-01", // Maharashtra Day
  "2026-05-28", // Bakri Id (Id-ul-Zuha)
  "2026-06-26", // Muharram
  "2026-09-14", // Ganesh Chaturthi
  "2026-10-02", // Mahatma Gandhi Jayanti
  "2026-10-20", // Dussehra (Vijaya Dashami)
  "2026-11-10", // Diwali - Laxmi Pujan
  "2026-11-24", // Guru Nanak Jayanti
  "2026-12-25", // Christmas
]);

/**
 * Parses and formats Date strictly in Asia/Kolkata timezone.
 */
export function getCanonicalIstNow(customDate?: Date): {
  nowIst: Date;
  dateStr: string;
  timeStr: string;
  timeStr12: string;
  hhmmss: string;
  dayOfWeek: number;
  isWeekday: boolean;
  isWeekend: boolean;
  isoDate: string;
  formattedDate: string;
} {
  const now = customDate || new Date();
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
  let month = "08", day = "31", year = "2026", hour = "06", minute = "00", second = "00";
  if (match) {
    [, month, day, year, hour, minute, second] = match;
  }

  const isoDate = `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
  const hhmmss = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}:${second.padStart(2, "0")}`;
  const nowIst = new Date(Date.UTC(parseInt(year, 10), parseInt(month, 10) - 1, parseInt(day, 10), parseInt(hour, 10), parseInt(minute, 10), parseInt(second, 10)));
  const dayOfWeek = nowIst.getUTCDay(); // 0 = Sun, 6 = Sat
  const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
  const isWeekday = !isWeekend;

  const formattedDate = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(now);

  const timeStr12 = new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  }).format(now).toUpperCase();

  return {
    nowIst,
    dateStr: isoDate,
    timeStr: `${hhmmss} IST`,
    timeStr12,
    hhmmss,
    dayOfWeek,
    isWeekday,
    isWeekend,
    isoDate,
    formattedDate,
  };
}

/**
 * Format any ISO date or timestamp into "28 Aug 2026"
 */
export function formatSessionDateIST(dateOrIso?: string | Date | null): string {
  if (!dateOrIso) return "28 Aug 2026";
  const d = typeof dateOrIso === "string" ? new Date(dateOrIso) : dateOrIso;
  if (isNaN(d.getTime())) return String(dateOrIso);
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(d);
}

/**
 * Calculate previous valid NSE trading day (skipping weekends & holidays)
 */
export function getPreviousNseTradingDay(startDate: Date = new Date()): { iso: string; formatted: string } {
  const current = new Date(startDate);
  current.setDate(current.getDate() - 1);

  for (let i = 0; i < 30; i++) {
    const day = current.getDay();
    const isoDate = current.toISOString().split("T")[0];
    if (day !== 0 && day !== 6 && !NSE_HOLIDAYS_2026.has(isoDate)) {
      return {
        iso: isoDate,
        formatted: formatSessionDateIST(current),
      };
    }
    current.setDate(current.getDate() - 1);
  }
  return { iso: "2026-08-28", formatted: "28 Aug 2026" };
}

/**
 * Calculate next valid NSE trading day (skipping weekends & holidays)
 */
export function getNextNseTradingDay(startDate: Date = new Date()): { iso: string; formatted: string } {
  const current = new Date(startDate);
  current.setDate(current.getDate() + 1);

  for (let i = 0; i < 30; i++) {
    const day = current.getDay();
    const isoDate = current.toISOString().split("T")[0];
    if (day !== 0 && day !== 6 && !NSE_HOLIDAYS_2026.has(isoDate)) {
      return {
        iso: isoDate,
        formatted: formatSessionDateIST(current),
      };
    }
    current.setDate(current.getDate() + 1);
  }
  return { iso: "2026-09-01", formatted: "01 Sep 2026" };
}

/**
 * A) Resolve Exchange sessionPhase (Exchange Truth & Data Legality)
 * Incorporates marketSessionStatus alongside time-of-day bounds.
 */
export function resolveSessionPhase(
  hhmmss: string,
  isWeekday: boolean,
  isHoliday: boolean,
  marketSessionStatus?: string
): SessionPhase {
  const normStatus = (marketSessionStatus || "").toUpperCase();

  // Explicit active market session overrides (e.g. Muhurat, Disaster Recovery, Special Session)
  if (
    normStatus === "OPEN" ||
    normStatus === "LIVE" ||
    normStatus === "SPECIAL_SESSION" ||
    normStatus === "MUHURAT" ||
    normStatus === "DR_SESSION" ||
    normStatus === "SPECIAL_OPEN"
  ) {
    if (hhmmss >= "15:25:00" && hhmmss < "15:40:00") {
      return "NEAR_CLOSE";
    }
    return "LIVE";
  }

  if (normStatus === "PRE_OPEN" && hhmmss < "09:15:00") {
    return "PRE_OPEN";
  }

  if ((normStatus === "PRE_MARKET" || normStatus === "EARLY_IDLE") && hhmmss < "09:00:00") {
    return "PRE_MARKET";
  }

  if (normStatus === "POST_CLOSE" && hhmmss >= "15:25:00" && hhmmss < "15:40:00") {
    return "NEAR_CLOSE";
  }

  if (isHoliday || !isWeekday) {
    return "POST_MARKET"; // Market closed / weekend -> Settled debrief substrate
  }
  if (hhmmss < "09:00:00") {
    return "PRE_MARKET"; // 06:00–09:00 IST
  }
  if (hhmmss >= "09:00:00" && hhmmss < "09:15:00") {
    return "PRE_OPEN"; // 09:00–09:15 IST (Auction)
  }
  if (hhmmss >= "09:15:00" && hhmmss < "15:25:00") {
    return "LIVE"; // 09:15–15:25 IST
  }
  if (hhmmss >= "15:25:00" && hhmmss < "15:40:00") {
    return "NEAR_CLOSE"; // 15:25–15:40 IST
  }
  return "POST_MARKET"; // 15:40–06:00 IST next day
}

/**
 * B) Resolve Ardha intelligenceMode (Cognitive Job)
 * Incorporates marketSessionStatus alongside time-of-day bounds.
 */
export function resolveIntelligenceMode(
  hhmmss: string,
  isWeekday: boolean,
  isHoliday: boolean,
  marketSessionStatus?: string
): IntelligenceMode {
  const normStatus = (marketSessionStatus || "").toUpperCase();

  // Explicit active market session overrides (e.g. Muhurat, Disaster Recovery, Special Session)
  if (
    normStatus === "OPEN" ||
    normStatus === "LIVE" ||
    normStatus === "SPECIAL_SESSION" ||
    normStatus === "MUHURAT" ||
    normStatus === "DR_SESSION" ||
    normStatus === "SPECIAL_OPEN"
  ) {
    if (hhmmss >= "09:15:00" && hhmmss < "09:30:00") {
      return "OPEN_VALIDATION";
    }
    if (hhmmss >= "14:45:00" && hhmmss < "15:25:00") {
      return "DECISION_WINDOW";
    }
    if (hhmmss >= "15:25:00" && hhmmss < "15:40:00") {
      return "CLOSE_TRANSFER";
    }
    return "REGIME_MONITOR";
  }

  if (normStatus === "PRE_OPEN" && hhmmss < "09:15:00") {
    return "AUCTION_READ";
  }

  if (normStatus === "PRE_MARKET" && hhmmss < "09:00:00") {
    return "PRE_COMMIT_PLAN";
  }

  if (isHoliday || !isWeekday) {
    return "OVERNIGHT_SYNTHESIS"; // Weekend / holiday -> Carry forward thesis
  }
  if (hhmmss < "08:30:00") {
    return "OVERNIGHT_SYNTHESIS"; // 15:40 → 08:30 IST
  }
  if (hhmmss >= "08:30:00" && hhmmss < "09:00:00") {
    return "PRE_COMMIT_PLAN"; // 08:30 → 09:00 IST
  }
  if (hhmmss >= "09:00:00" && hhmmss < "09:15:00") {
    return "AUCTION_READ"; // 09:00 → 09:15 IST
  }
  if (hhmmss >= "09:15:00" && hhmmss < "09:30:00") {
    return "OPEN_VALIDATION"; // 09:15 → 09:30 IST (First 15m OR verdict)
  }
  if (hhmmss >= "09:30:00" && hhmmss < "14:45:00") {
    return "REGIME_MONITOR"; // 09:30 → 14:45 IST
  }
  if (hhmmss >= "14:45:00" && hhmmss < "15:25:00") {
    return "DECISION_WINDOW"; // 14:45 → 15:25 IST
  }
  if (hhmmss >= "15:25:00" && hhmmss < "15:40:00") {
    return "CLOSE_TRANSFER"; // 15:25 → 15:40 IST
  }
  return "OVERNIGHT_SYNTHESIS"; // 15:40 → 08:30 IST
}

/**
 * Maps human-readable label for sessionPhase
 */
export function getPhaseLabel(phase: SessionPhase): string {
  switch (phase) {
    case "PRE_MARKET":
      return "Pre-Market Preparation (06:00–09:00 IST)";
    case "PRE_OPEN":
      return "Pre-Open Auction Window (09:00–09:15 IST)";
    case "LIVE":
      return "Live Continuous Trading (09:15–15:25 IST)";
    case "NEAR_CLOSE":
      return "Closing Settlement Window (15:25–15:40 IST)";
    case "POST_MARKET":
      return "Post-Market Completed Session Review (15:40–06:00 IST)";
  }
}

/**
 * Maps human-readable label for intelligenceMode
 */
export function getIntelligenceLabel(mode: IntelligenceMode): string {
  switch (mode) {
    case "OVERNIGHT_SYNTHESIS":
      return "Overnight Synthesis (Macro & Carry Levels)";
    case "PRE_COMMIT_PLAN":
      return "Pre-Commit Plan (Scenarios & Invalidation)";
    case "AUCTION_READ":
      return "Auction Read (Opening Gap vs Plan)";
    case "OPEN_VALIDATION":
      return "Open Validation (15m OR Confirmation)";
    case "REGIME_MONITOR":
      return "Regime Monitor (Intraday Confluence)";
    case "DECISION_WINDOW":
      return "Decision Window (Pre-Close Execution Guard)";
    case "CLOSE_TRANSFER":
      return "Close Transfer (EOD Debrief & Hand-off)";
  }
}

/**
 * Resolve Data Window from phase and mode
 */
export function resolveDataWindow(
  phase: SessionPhase,
  intelMode: IntelligenceMode,
  isReplay: boolean
): DataWindow {
  if (isReplay) {
    if (phase === "PRE_MARKET" || phase === "POST_MARKET") return "SETTLED_COMPLETED";
    if (phase === "PRE_OPEN") return "PRE_OPEN_AUCTION";
    return "SESSION_SO_FAR";
  }

  if (phase === "POST_MARKET" || intelMode === "OVERNIGHT_SYNTHESIS" || intelMode === "PRE_COMMIT_PLAN") {
    return "SETTLED_COMPLETED";
  }
  if (phase === "PRE_OPEN" || intelMode === "AUCTION_READ") {
    return "PRE_OPEN_AUCTION";
  }
  return "SESSION_SO_FAR";
}

/**
 * PRIMARY AUTHORITATIVE ENTRY POINT: CanonicalSessionIdentity
 */
export function resolveCanonicalSessionIdentity(params?: {
  customDate?: Date;
  preview_sessionPhase?: SessionPhase;
  preview_intelligenceMode?: IntelligenceMode;
  is_replay_mode?: boolean;
  envelope?: any;
  canonicalState?: any;
  marketSessionStatus?: string;
  isDisconnected?: boolean;
}): CanonicalSessionIdentity {
  // Authoritative Date resolution
  let resolvedDate = params?.customDate;
  let isFallback = false;

  if (!resolvedDate) {
    const rawTs =
      params?.canonicalState?.generated_at ||
      params?.canonicalState?.data_quality?.market_data?.observed_at ||
      params?.canonicalState?.market_data?.observed_at ||
      params?.envelope?.published_at ||
      params?.envelope?.market?.nifty?.exchange_timestamp;

    if (rawTs) {
      const parsed = new Date(rawTs);
      if (!isNaN(parsed.getTime())) {
        resolvedDate = parsed;
      }
    }
  }

  if (!resolvedDate) {
    resolvedDate = new Date();
    if (params?.isDisconnected) {
      isFallback = true;
    }
  }

  const { nowIst, isoDate, formattedDate, hhmmss, isWeekday, isWeekend } = getCanonicalIstNow(resolvedDate);
  const isHoliday = NSE_HOLIDAYS_2026.has(isoDate);

  const marketStatus =
    params?.marketSessionStatus ||
    params?.canonicalState?.market_session?.status ||
    params?.envelope?.session?.market_phase;

  // Computed exchange phase & cognitive mode
  const naturalPhase = resolveSessionPhase(hhmmss, isWeekday, isHoliday, marketStatus);
  const naturalIntelMode = resolveIntelligenceMode(hhmmss, isWeekday, isHoliday, marketStatus);

  const effectivePhase = params?.preview_sessionPhase ?? naturalPhase;
  const effectiveIntelMode = params?.preview_intelligenceMode ?? naturalIntelMode;
  const isReplay = params?.is_replay_mode === true || params?.preview_sessionPhase != null;

  // Resolve session date lineage
  const completedSession = getPreviousNseTradingDay(nowIst);
  const nextSession = getNextNseTradingDay(nowIst);

  const activeTradingDate = isWeekend || isHoliday ? completedSession.iso : isoDate;
  const activeTradingDateFormatted = isWeekend || isHoliday ? completedSession.formatted : formattedDate;

  const dataWindow = resolveDataWindow(effectivePhase, effectiveIntelMode, isReplay);

  return {
    wall_clock_ist: `${hhmmss} IST`,
    calendar_date: isoDate,
    calendar_date_formatted: formattedDate,
    sessionPhase: effectivePhase,
    intelligenceMode: effectiveIntelMode,
    phase_label: getPhaseLabel(effectivePhase),
    intelligence_label: getIntelligenceLabel(effectiveIntelMode),
    completed_session_date: completedSession.iso,
    completed_session_date_formatted: completedSession.formatted,
    active_trading_date: activeTradingDate,
    active_trading_date_formatted: activeTradingDateFormatted,
    next_trading_date: nextSession.iso,
    next_trading_date_formatted: nextSession.formatted,
    is_weekend: isWeekend,
    is_holiday: isHoliday,
    is_replay_mode: isReplay,
    data_window: dataWindow,
    preview_sessionPhase: params?.preview_sessionPhase,
    preview_intelligenceMode: params?.preview_intelligenceMode,
    is_client_time_fallback: isFallback || params?.isDisconnected === true,
  };
}
