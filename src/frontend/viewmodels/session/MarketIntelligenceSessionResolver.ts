// src/frontend/viewmodels/session/MarketIntelligenceSessionResolver.ts

export type MarketIntelligenceSubTab = "MORNING_PLAN" | "LIVE_GUIDE" | "TOMORROW_PLAN";
export type MarketIntelligencePreviewMode = "AUTO" | "MORNING_PLAN" | "LIVE_GUIDE" | "TOMORROW_PLAN";

export type SessionLifecycleStage =
  | "PREPARING"
  | "MORNING_PLAN_ACTIVE"
  | "LIVE_GUIDE_ACTIVE"
  | "LIVE_GUIDE_CLOSING_BUILD"
  | "TOMORROW_PLAN_ACTIVE";

export interface SessionTimingState {
  currentIstTimeStr: string;
  currentIstHHMMSS: string;
  lifecycleStage: SessionLifecycleStage;
  effectiveSubTab: MarketIntelligenceSubTab;
  autoResolvedSubTab: MarketIntelligenceSubTab;
  previewMode: MarketIntelligencePreviewMode;
  isClosedSession: boolean;
  marketStatusText: string;
}

/**
 * Gets canonical IST Date accurately.
 */
export function getCanonicalIstDate(customDate?: Date): Date {
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
  return new Date(now.getTime() + 5.5 * 60 * 60 * 1000);
}

/**
 * Resolves session timing and dynamic subtab based on exact IST boundary rules.
 */
export function resolveMarketIntelligenceSession(params?: {
  customDate?: Date;
  marketSessionState?: any;
  previewMode?: MarketIntelligencePreviewMode;
}): SessionTimingState {
  const preview = params?.previewMode || "AUTO";
  const nowIst = getCanonicalIstDate(params?.customDate);
  const hour = nowIst.getUTCHours();
  const minute = nowIst.getUTCMinutes();
  const second = nowIst.getUTCSeconds();
  const hhmmss = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}:${String(second).padStart(2, "0")}`;
  const timeStr = `${hhmmss} IST`;

  const mStatus = String(params?.marketSessionState?.status || "").toUpperCase();
  const isClosed = Boolean(
    params?.marketSessionState?.is_closed ||
    ["CLOSED", "HOLIDAY", "WEEKEND", "POST_CLOSE"].includes(mStatus)
  );

  let lifecycleStage: SessionLifecycleStage;
  let autoResolvedSubTab: MarketIntelligenceSubTab;

  if (isClosed && hhmmss < "09:00:00") {
    // Post-close / carry-forward until next pre-open
    lifecycleStage = "TOMORROW_PLAN_ACTIVE";
    autoResolvedSubTab = "TOMORROW_PLAN";
  } else if (hhmmss < "09:10:00") {
    // 00:00:00 - 09:09:59 IST: Preparing
    lifecycleStage = "PREPARING";
    autoResolvedSubTab = "MORNING_PLAN";
  } else if (hhmmss >= "09:10:00" && hhmmss <= "09:14:58") {
    // 09:10:00 - 09:14:58 IST: Morning Plan
    lifecycleStage = "MORNING_PLAN_ACTIVE";
    autoResolvedSubTab = "MORNING_PLAN";
  } else if (hhmmss >= "09:14:59" && hhmmss < "15:25:00") {
    // 09:14:59 - 15:24:59 IST: Live Guide
    lifecycleStage = "LIVE_GUIDE_ACTIVE";
    autoResolvedSubTab = "LIVE_GUIDE";
  } else if (hhmmss >= "15:25:00" && hhmmss <= "15:29:59") {
    // 15:25:00 - 15:29:59 IST: Live Guide + Closing Build
    lifecycleStage = "LIVE_GUIDE_CLOSING_BUILD";
    autoResolvedSubTab = "LIVE_GUIDE";
  } else {
    // 15:30:00 onward: Tomorrow Plan
    lifecycleStage = "TOMORROW_PLAN_ACTIVE";
    autoResolvedSubTab = "TOMORROW_PLAN";
  }

  // Determine effective subtab (respecting preview override if set)
  let effectiveSubTab: MarketIntelligenceSubTab = autoResolvedSubTab;
  if (preview === "MORNING_PLAN") effectiveSubTab = "MORNING_PLAN";
  else if (preview === "LIVE_GUIDE") effectiveSubTab = "LIVE_GUIDE";
  else if (preview === "TOMORROW_PLAN") effectiveSubTab = "TOMORROW_PLAN";

  let marketStatusText = "MARKET OPEN";
  if (isClosed) {
    marketStatusText = mStatus === "HOLIDAY" ? "MARKET HOLIDAY" : "MARKET CLOSED";
  } else if (hhmmss < "09:15:00") {
    marketStatusText = "PRE-OPEN";
  }

  return {
    currentIstTimeStr: timeStr,
    currentIstHHMMSS: hhmmss,
    lifecycleStage,
    effectiveSubTab,
    autoResolvedSubTab,
    previewMode: preview,
    isClosedSession: isClosed,
    marketStatusText,
  };
}
