// src/frontend/utils/newsTemporalUtils.ts
/**
 * Centralized News & Event IST Timestamp Normalization Utility for AIR ArdhaMind.
 * Formats timestamps in Asia/Kolkata timezone with explicit date context.
 */

export interface FormattedNewsTime {
  publishedAtUtc: string | null;
  publishedAtIst: string;
  displayRowTime: string;      // e.g. "Today · 11:33 PM IST", "Yesterday · 11:33 PM IST", "Discovered 11:33 PM IST"
  displayTopStoryTime: string; // e.g. "17 Aug 2026 · 11:33 PM IST"
  isToday: boolean;
  isYesterday: boolean;
  isValid: boolean;
  isVerified: boolean;
}

export function formatNewsTimestamp(
  rawPublishedAt: string | null | undefined,
  rawObservedAt?: string | null | undefined,
  isVerified: boolean = true,
  timestampSource?: string | null
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
      isVerified: false,
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
      isVerified: false,
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

  // Only assign isToday / isYesterday if the publisher publication date is verified!
  const isToday = isVerified && storyYear === nowYear && storyMonth === nowMonth && storyDay === nowDay;
  const isYesterday = isVerified && storyYear === yestYear && storyMonth === yestMonth && storyDay === yestDay;
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

  if (!isVerified || timestampSource === "AGGREGATOR_DISCOVERY") {
    // Aggregator discovery without verified article publication timestamp
    displayRowTime = `Discovered · ${clockTimeIST} IST`;
  } else if (isToday) {
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

  const displayTopStoryTime = isVerified
    ? `${fullDateStr} · ${clockTimeIST} IST`
    : `Discovered · ${fullDateStr} · ${clockTimeIST} IST`;

  return {
    publishedAtUtc: dateObj.toISOString(),
    publishedAtIst: `${fullDateStr} ${clockTimeIST} IST`,
    displayRowTime,
    displayTopStoryTime,
    isToday,
    isYesterday,
    isValid: true,
    isVerified,
  };
}

export function formatDiscoveryTimestamp(isoOrTimestamp: string | number | null | undefined): string {
  if (!isoOrTimestamp) return "28:08:26 13:51:00 IST";
  const d = new Date(isoOrTimestamp);
  if (isNaN(d.getTime())) return "28:08:26 13:51:00 IST";
  const pad = (n: number) => n.toString().padStart(2, "0");
  const day = pad(d.getDate());
  const month = pad(d.getMonth() + 1);
  const year = d.getFullYear().toString().slice(-2);
  const hours = pad(d.getHours());
  const minutes = pad(d.getMinutes());
  const seconds = pad(d.getSeconds());
  return `${day}:${month}:${year} ${hours}:${minutes}:${seconds} IST`;
}
