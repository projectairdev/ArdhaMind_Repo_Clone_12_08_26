// src/frontend/utils/timeFormatting.ts
import { safeString } from "./safeHelpers";

export function isDateOnly(timestamp: any): boolean {
  if (typeof timestamp !== "string") return false;
  const cleaned = timestamp.trim();
  // If it doesn't contain a colon (time indicator) or contains date only formats
  return !cleaned.includes(":") && !cleaned.includes("T");
}

export function formatTimestampIST(timestamp: any): string {
  if (!timestamp) return "Unavailable";
  const strVal = String(timestamp).trim();
  if (strVal === "0" || strVal.includes("1970-01-01") || strVal.includes("01 Jan, 1970") || strVal.includes("01 Jan 1970")) {
    return "Unavailable";
  }
  try {
    const d = new Date(timestamp);
    if (isNaN(d.getTime())) return "Unavailable";
    if (d.getFullYear() === 1970 && d.getMonth() === 0 && d.getDate() === 1) {
      return "Unavailable";
    }

    const dateStr = d.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      timeZone: "Asia/Kolkata",
    });

    if (isDateOnly(timestamp)) {
      return dateStr;
    }

    const timeStr = d.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
      timeZone: "Asia/Kolkata",
    });
    
    return `${dateStr} · ${timeStr} IST`;
  } catch {
    return "Unavailable";
  }
}

export function formatCompactTimestampIST(timestamp: any): string {
  if (!timestamp) return "Unavailable";
  const strVal = String(timestamp).trim();
  if (strVal === "0" || strVal.includes("1970-01-01") || strVal.includes("01 Jan, 1970") || strVal.includes("01 Jan 1970")) {
    return "Unavailable";
  }
  try {
    const d = new Date(timestamp);
    if (isNaN(d.getTime())) return "Unavailable";
    if (d.getFullYear() === 1970 && d.getMonth() === 0 && d.getDate() === 1) {
      return "Unavailable";
    }
    
    const day = d.toLocaleDateString("en-IN", { day: "2-digit", timeZone: "Asia/Kolkata" });
    const month = d.toLocaleDateString("en-IN", { month: "short", timeZone: "Asia/Kolkata" });
    const dateStr = `${day} ${month}`;

    if (isDateOnly(timestamp)) {
      return dateStr;
    }

    const timeStr = d.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "Asia/Kolkata",
    });
    
    return `${dateStr} · ${timeStr} IST`;
  } catch {
    return "Unavailable";
  }
}

export function formatTimeIST(timestamp: any): string {
  if (!timestamp) return "Unavailable";
  try {
    const d = new Date(timestamp);
    if (isNaN(d.getTime())) return "Unavailable";
    if (d.getFullYear() === 1970 && d.getMonth() === 0 && d.getDate() === 1) {
      return "Unavailable";
    }
    
    return d.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
      timeZone: "Asia/Kolkata",
    }) + " IST";
  } catch {
    return "Unavailable";
  }
}

export function formatRelativeAge(timestamp: any, now = new Date()): string {
  if (!timestamp) return "Unavailable";
  try {
    const d = new Date(timestamp);
    if (isNaN(d.getTime())) return "Unavailable";
    if (d.getFullYear() === 1970 && d.getMonth() === 0 && d.getDate() === 1) {
      return "Unavailable";
    }
    
    const diffMs = now.getTime() - d.getTime();
    if (diffMs < 0) return "0 sec ago";
    
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return `${diffSec} sec ago`;
    
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin} min ago`;
    
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr} hr ago`;
    
    const diffDay = Math.floor(diffHr / 24);
    return `${diffDay} day ago`;
  } catch {
    return "Unavailable";
  }
}
