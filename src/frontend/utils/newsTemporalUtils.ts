// src/frontend/utils/newsTemporalUtils.ts
/**
 * Centralized News & Event IST Timestamp Normalization Utility for AIR ArdhaMind.
 * Formats timestamps in Asia/Kolkata timezone with explicit date context.
 */

export interface FormattedNewsTime {
  publishedAtUtc: string | null;
  publishedAtIst: string;
  displayRowTime: string;      // e.g. "Today · 11:33 PM IST", "Yesterday · 11:33 PM IST", "15 Aug · 11:33 PM IST", "15 Aug 2025 · 11:33 PM IST"
  displayTopStoryTime: string; // e.g. "17 Aug 2026 · 11:33 PM IST"
  isToday: boolean;
  isYesterday: boolean;
  isValid: boolean;
}

export function formatNewsTimestamp(
  rawPublishedAt: string | null | undefined,
  rawObservedAt?: string | null | undefined
): FormattedNewsTime {
  if (!rawPublishedAt && !rawObservedAt) {
    return {
      publishedAtUtc: null,
      publishedAtIst: "Time unavailable",
      displayRowTime: "Time unavailable",
      displayTopStoryTime: "Time unavailable",
      isToday: false,
      isYesterday: false,
      isValid: false,
    };
  }

  const targetStr = rawPublishedAt || rawObservedAt;
  const isObservedOnly = !rawPublishedAt && Boolean(rawObservedAt);
  const dateObj = new Date(targetStr!);

  if (isNaN(dateObj.getTime())) {
    return {
      publishedAtUtc: null,
      publishedAtIst: "Time unavailable",
      displayRowTime: "Time unavailable",
      displayTopStoryTime: "Time unavailable",
      isToday: false,
      isYesterday: false,
      isValid: false,
    };
  }

  // Get current date parts in Asia/Kolkata
  const now = new Date();
  const timeZone = "Asia/Kolkata";

  const getParts = (d: Date) => {
    const formatter = new Intl.DateTimeFormat("en-US", {
      timeZone,
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
      second: "numeric",
      hour12: true,
    });
    const parts = formatter.formatToParts(d);
    const obj: Record<string, string> = {};
    parts.forEach((p) => {
      obj[p.type] = p.value;
    });
    return obj;
  };

  const storyParts = getParts(dateObj);
  const nowParts = getParts(now);

  const storyYear = parseInt(storyParts.year, 10);
  const storyMonth = parseInt(storyParts.month, 10);
  const storyDay = parseInt(storyParts.day, 10);

  const nowYear = parseInt(nowParts.year, 10);
  const nowMonth = parseInt(nowParts.month, 10);
  const nowDay = parseInt(nowParts.day, 10);

  // Compute yesterday's date in IST
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const yesterdayParts = getParts(yesterday);
  const yestYear = parseInt(yesterdayParts.year, 10);
  const yestMonth = parseInt(yesterdayParts.month, 10);
  const yestDay = parseInt(yesterdayParts.day, 10);

  const isToday = storyYear === nowYear && storyMonth === nowMonth && storyDay === nowDay;
  const isYesterday = storyYear === yestYear && storyMonth === yestMonth && storyDay === yestDay;
  const isSameYear = storyYear === nowYear;

  const clockTimeIST = new Intl.DateTimeFormat("en-IN", {
    timeZone,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(dateObj);

  const shortDateStr = new Intl.DateTimeFormat("en-GB", {
    timeZone,
    day: "2-digit",
    month: "short",
  }).format(dateObj);

  const fullDateStr = new Intl.DateTimeFormat("en-GB", {
    timeZone,
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(dateObj);

  let displayRowTime = "";

  if (isToday) {
    displayRowTime = `Today · ${clockTimeIST} IST`;
  } else if (isYesterday) {
    displayRowTime = `Yesterday · ${clockTimeIST} IST`;
  } else if (isSameYear) {
    displayRowTime = `${shortDateStr} · ${clockTimeIST} IST`;
  } else {
    displayRowTime = `${fullDateStr} · ${clockTimeIST} IST`;
  }

  if (isObservedOnly) {
    displayRowTime = `Observed: ${clockTimeIST} IST`;
  }

  const displayTopStoryTime = `${fullDateStr} · ${clockTimeIST} IST`;

  return {
    publishedAtUtc: dateObj.toISOString(),
    publishedAtIst: `${fullDateStr} ${clockTimeIST} IST`,
    displayRowTime,
    displayTopStoryTime,
    isToday,
    isYesterday,
    isValid: true,
  };
}
