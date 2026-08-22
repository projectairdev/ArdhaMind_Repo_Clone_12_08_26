// src/frontend/utils/temporalSessionResolver.ts
/**
 * Canonical Temporal Session Resolver for AIR ArdhaMind
 * 
 * Provides single-source-of-truth session dates, source observation timestamps,
 * and canonical validation times across all active Ardha workspaces.
 */

export interface TemporalSessionContext {
  wallClockIst: string;
  isWeekend: boolean;
  isMarketClosed: boolean;
  isLiveSession: boolean;
  displayStatus: "LIVE" | "PRE-MARKET" | "POST-MARKET" | "LAST VALID SESSION" | "NEXT SESSION PREVIEW" | "WEEKEND" | "HOLIDAY" | "STALE" | "DEGRADED";
  statusColor: string; // Tailwind color string
  lastValidSessionDate: string; // e.g. "21 Aug 2026"
  nextSessionDate: string;      // e.g. "24 Aug 2026"
  canonicalValidatedAt: string; // e.g. "21 Aug 2026 · 15:30:08 IST"
  previewNotice?: string;       // e.g. "STAGING PREVIEW · NEXT SESSION PREVIEW"
  freshness: "LIVE" | "FRESH" | "STALE" | "DEGRADED" | "UNAVAILABLE";
}

// 2026 Scheduled NSE Exchange Holidays
const NSE_HOLIDAYS_2026 = new Set<string>([
  "2026-01-26", // Republic Day
  "2026-03-03", // Holi
  "2026-03-20", // Id-Ul-Fitr
  "2026-04-03", // Good Friday
  "2026-04-14", // Ambedkar Jayanti
  "2026-05-01", // Maharashtra Day
  "2026-08-15", // Independence Day
  "2026-10-02", // Gandhi Jayanti
  "2026-10-20", // Dussehra
  "2026-11-08", // Diwali Balipratipada
  "2026-11-23", // Guru Nanak Jayanti
  "2026-12-25", // Christmas
]);

/**
 * Format a Date or ISO string into canonical "22 Aug 2026"
 */
export function formatDateIST(input?: string | number | Date | null): string {
  if (!input) return "Unavailable";
  const date = new Date(input);
  if (isNaN(date.getTime())) return String(input);

  // Format in Asia/Kolkata timezone
  const options: Intl.DateTimeFormatOptions = {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  };
  return new Intl.DateTimeFormat("en-IN", options).format(date);
}

/**
 * Format a Date or ISO string into canonical "15:30 IST" or "3:30:08 PM IST"
 */
export function formatTimeIST(input?: string | number | Date | null, includeSeconds = false): string {
  if (!input) return "Unavailable";
  const date = new Date(input);
  if (isNaN(date.getTime())) return String(input);

  const options: Intl.DateTimeFormatOptions = {
    hour: "2-digit",
    minute: "2-digit",
    second: includeSeconds ? "2-digit" : undefined,
    hour12: false,
    timeZone: "Asia/Kolkata",
  };
  return `${new Intl.DateTimeFormat("en-IN", options).format(date)} IST`;
}

/**
 * Format full canonical timestamp: "21 Aug 2026 · 15:30:08 IST"
 */
export function formatFullIST(input?: string | number | Date | null): string {
  if (!input) return "Unavailable";
  const date = new Date(input);
  if (isNaN(date.getTime())) return String(input);
  return `${formatDateIST(date)} · ${formatTimeIST(date, true)}`;
}

/**
 * Returns true if the given YYYY-MM-DD string or Date is a Saturday or Sunday
 */
export function isWeekendDay(input?: string | Date): boolean {
  const d = input ? new Date(input) : new Date();
  const day = d.getDay();
  return day === 0 || day === 6; // 0 = Sunday, 6 = Saturday
}

/**
 * Returns true if the given YYYY-MM-DD string is a scheduled NSE holiday
 */
export function isNseHoliday(dateStr: string): boolean {
  return NSE_HOLIDAYS_2026.has(dateStr);
}

/**
 * Calculate the next valid NSE trading day (skipping weekends and holidays)
 */
export function getNextTradingDay(startDate: Date = new Date()): string {
  const current = new Date(startDate);
  current.setDate(current.getDate() + 1); // Start with next day

  while (true) {
    const day = current.getDay();
    const isoDate = current.toISOString().split("T")[0];
    if (day !== 0 && day !== 6 && !NSE_HOLIDAYS_2026.has(isoDate)) {
      return formatDateIST(current);
    }
    current.setDate(current.getDate() + 1);
  }
}

/**
 * Calculate the previous valid NSE trading day (skipping weekends and holidays)
 */
export function getPreviousTradingDay(startDate: Date = new Date()): string {
  const current = new Date(startDate);
  current.setDate(current.getDate() - 1); // Start with previous day

  while (true) {
    const day = current.getDay();
    const isoDate = current.toISOString().split("T")[0];
    if (day !== 0 && day !== 6 && !NSE_HOLIDAYS_2026.has(isoDate)) {
      return formatDateIST(current);
    }
    current.setDate(current.getDate() - 1);
  }
}

/**
 * Authoritative temporal resolver for active workstation state
 */
export function getTemporalSessionContext(
  canonicalState: any,
  previewMode: "PRE" | "LIVE" | "POST" = "LIVE"
): TemporalSessionContext {
  const now = new Date();
  const isWeekend = isWeekendDay(now);

  // Extract canonical session properties
  const sessionObj = canonicalState?.market_session || {};
  const statusStr = String(sessionObj.status || "").toLowerCase();
  const isClosed = sessionObj.is_closed ?? (statusStr !== "open");

  // Determine active display status
  let displayStatus: TemporalSessionContext["displayStatus"] = "LAST VALID SESSION";
  let statusColor = "text-[#707987]"; // neutral gray

  if (statusStr === "open") {
    displayStatus = "LIVE";
    statusColor = "text-[#00C896]";
  } else if (isWeekend) {
    displayStatus = "WEEKEND";
    statusColor = "text-[#38BDF8]";
  } else if (statusStr === "holiday") {
    displayStatus = "HOLIDAY";
    statusColor = "text-[#E59700]";
  } else if (statusStr === "pre_market") {
    displayStatus = "PRE-MARKET";
    statusColor = "text-[#38BDF8]";
  } else if (statusStr === "post_market") {
    displayStatus = "POST-MARKET";
    statusColor = "text-[#8B5CF6]";
  }

  // Resolve session dates
  let lastValidSessionDate = formatDateIST(canonicalState?.pre_market_report?.critical_levels?.reference_close_date) || "21 Aug 2026";
  if (lastValidSessionDate === "Unavailable" || !lastValidSessionDate) {
    lastValidSessionDate = getPreviousTradingDay(now);
  }

  let nextSessionDate = sessionObj.next_session_date ? formatDateIST(sessionObj.next_session_date) : getNextTradingDay(now);

  // Resolve canonical validation time
  const valTime = canonicalState?.last_updated_ist || canonicalState?.lastUpdatedIst || canonicalState?.canonical_committed_at;
  const canonicalValidatedAt = valTime ? formatFullIST(valTime) : `${lastValidSessionDate} · 15:30:00 IST`;

  // Preview notice if staging preview is active outside live market
  let previewNotice: string | undefined = undefined;
  if (isClosed) {
    if (previewMode === "PRE") {
      previewNotice = `STAGING PREVIEW · NEXT SESSION PREVIEW (${nextSessionDate})`;
    } else if (previewMode === "POST") {
      previewNotice = `STAGING PREVIEW · LAST SESSION REVIEW (${lastValidSessionDate})`;
    } else if (previewMode === "LIVE") {
      previewNotice = `STAGING PREVIEW · MARKET CLOSED (${displayStatus})`;
    }
  }

  const freshness: TemporalSessionContext["freshness"] = statusStr === "open" ? "LIVE" : "FRESH";

  return {
    wallClockIst: formatTimeIST(now, true),
    isWeekend,
    isMarketClosed: isClosed,
    isLiveSession: statusStr === "open",
    displayStatus,
    statusColor,
    lastValidSessionDate,
    nextSessionDate,
    canonicalValidatedAt,
    previewNotice,
    freshness,
  };
}
