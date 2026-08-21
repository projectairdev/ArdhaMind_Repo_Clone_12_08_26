// src/frontend/utils/briefingTimeResolver.ts
/**
 * Authoritative Briefing Time & Session Resolver for AIR ArdhaMind.
 *
 * Provides a single, centralized truth for:
 *  1. Sidebar briefing item label ("PRE-MARKET BRIEFING" vs "POST-MARKET BRIEFING")
 *  2. Default briefing workspace subview ("MORNING" vs "POST_MARKET")
 *  3. Post-market briefing report lifecycle state (PREPARING, SNAPSHOT_FROZEN, AWAITING_OFFICIAL_CLOSE, FINAL_RECONCILED, NO_TRADING_SESSION)
 */

export type SidebarBriefingLabel = "PRE-MARKET BRIEFING" | "POST-MARKET BRIEFING";
export type BriefingDefaultSubview = "MORNING" | "POST_MARKET";
export type PostMarketLifecycleState =
  | "NOT_APPLICABLE"
  | "PREPARING"
  | "SNAPSHOT_FROZEN"
  | "AWAITING_OFFICIAL_CLOSE"
  | "FINAL_RECONCILED"
  | "DEGRADED"
  | "NO_TRADING_SESSION";

export interface BriefingPresentationMode {
  sidebarLabel: SidebarBriefingLabel;
  defaultSubview: BriefingDefaultSubview;
  postMarketLifecycleState: PostMarketLifecycleState;
  currentIstTimeStr: string;
  currentIstHHMM: string;
  isTradingDay: boolean;
}

/**
 * Gets current IST Date object accurately.
 */
export function getCanonicalIstDate(customDate?: Date): Date {
  const now = customDate || new Date();
  // Format to Asia/Kolkata timezone string and reconstruct Date
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

  // istStr format: "MM/DD/YYYY, HH:mm:ss" or similar
  const match = istStr.match(/(\d+)\/(\d+)\/(\d+),\s*(\d+):(\d+):(\d+)/);
  if (match) {
    const [, month, day, year, hour, minute, second] = match;
    return new Date(
      Date.UTC(
        parseInt(year, 10),
        parseInt(month, 10) - 1,
        parseInt(day, 10),
        parseInt(hour, 10),
        parseInt(minute, 10),
        parseInt(second, 10)
      )
    );
  }
  // Fallback UTC+5:30 offset adjustment
  return new Date(now.getTime() + 5.5 * 60 * 60 * 1000);
}

/**
 * Resolves authoritative briefing presentation mode based on IST time and calendar session.
 */
export function resolveBriefingPresentationMode(params?: {
  customDate?: Date;
  marketSessionState?: any;
  isTradingDayOverride?: boolean;
}): BriefingPresentationMode {
  const nowIst = getCanonicalIstDate(params?.customDate);
  const hour = nowIst.getUTCHours();
  const minute = nowIst.getUTCMinutes();
  const hhmm = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;

  // Determine if today is a trading day (Monday - Friday, excluding holidays)
  const dayOfWeek = nowIst.getUTCDay(); // 0 = Sun, 6 = Sat
  let isTradingDay = dayOfWeek >= 1 && dayOfWeek <= 5;
  if (params?.isTradingDayOverride !== undefined) {
    isTradingDay = params.isTradingDayOverride;
  } else if (params?.marketSessionState) {
    const mStatus = params.marketSessionState.status || "";
    if (mStatus === "holiday" || mStatus === "weekend") {
      isTradingDay = false;
    }
  }

  // 15:00 IST boundary rule
  const isPost1500 = hhmm >= "15:00";

  const sidebarLabel: SidebarBriefingLabel = isPost1500
    ? "POST-MARKET BRIEFING"
    : "PRE-MARKET BRIEFING";

  const defaultSubview: BriefingDefaultSubview = isPost1500 ? "POST_MARKET" : "MORNING";

  let postMarketLifecycleState: PostMarketLifecycleState = "NOT_APPLICABLE";

  if (!isTradingDay && isPost1500) {
    postMarketLifecycleState = "NO_TRADING_SESSION";
  } else if (isPost1500) {
    if (hhmm < "15:20") {
      postMarketLifecycleState = "PREPARING";
    } else if (hhmm < "15:30") {
      postMarketLifecycleState = "SNAPSHOT_FROZEN";
    } else {
      postMarketLifecycleState = "FINAL_RECONCILED";
    }
  }

  return {
    sidebarLabel,
    defaultSubview,
    postMarketLifecycleState,
    currentIstTimeStr: `${hhmm} IST`,
    currentIstHHMM: hhmm,
    isTradingDay,
  };
}
