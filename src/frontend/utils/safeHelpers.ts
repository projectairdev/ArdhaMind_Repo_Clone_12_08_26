// src/frontend/utils/safeHelpers.ts

export function safeArray<T>(arr: T[] | null | undefined): T[] {
  if (!arr || !Array.isArray(arr)) return [];
  return arr;
}

export function safeObject<T>(obj: T | null | undefined, fallback: T): T {
  if (!obj || typeof obj !== "object") return fallback;
  return obj;
}

export function safeNumber(val: any, fallback = 0): number {
  if (val === null || val === undefined) return fallback;
  const num = Number(val);
  return isNaN(num) ? fallback : num;
}

export function safeString(val: any, fallback = ""): string {
  if (val === null || val === undefined) return fallback;
  return String(val);
}

export function getWebSocketUrl(path = "/api/ws"): string {
  if (typeof window === "undefined" || !window.location) {
    return `ws://localhost:3000${path}`;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return `${protocol}//${host}${path}`;
}

export function formatSpotPrice(val: any, fallback = "WAITING FOR LIVE DATA"): string {
  if (val === null || val === undefined || val === "" || val === 0 || val === "0" || val === "0.0" || val === "0.00") {
    return fallback;
  }
  const num = Number(val);
  if (isNaN(num) || num <= 0) return fallback;
  return num.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function stripHtml(val: any): string {
  if (!val) return "";
  const str = String(val);
  return str
    .replace(/<[^>]*>?/gm, "")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, " ")
    .trim();
}

export function formatCurrency(val: any, fractionDigits = 0): string {
  const num = safeNumber(val, 0);
  return num.toLocaleString("en-IN", {
    maximumFractionDigits: fractionDigits,
  });
}

export function formatDate(val: any): string {
  if (!val) return "--";
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return String(val);
    return d.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric"
    });
  } catch {
    return String(val);
  }
}

export function formatDateTimeIST(val: any): string {
  if (!val) return "--";
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return String(val);
    return d.toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false
    }) + " IST";
  } catch {
    return String(val);
  }
}

export function formatNumber(val: any, fractionDigits = 2): string {
  if (val === null || val === undefined) return "--";
  const num = Number(val);
  if (isNaN(num)) return "--";
  return num.toLocaleString("en-IN", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits
  });
}

export function formatPercent(val: any, fractionDigits = 2): string {
  if (val === null || val === undefined) return "--%";
  const num = Number(val);
  if (isNaN(num)) return "--%";
  const formatted = num.toLocaleString("en-IN", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits
  });
  return `${num >= 0 ? "+" : ""}${formatted}%`;
}

// Scoped Macro & News Refresh Helper Endpoints for React UI
export async function apiMacroRefresh(keys?: string[]): Promise<{ status: string; error?: string }> {
  try {
    const fn = window["fetch"];
    const bodyObj = keys && keys.length > 0 ? { keys } : {};
    const res = await fn("/api/macro/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyObj)
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.status !== "failed") {
      return { status: "success" };
    }
    if (res.status === 429) {
      return { status: "rate_limited", error: data.error || "Rate limited" };
    }
    return { status: "failed", error: data.error || "Macro refresh failed" };
  } catch (err: any) {
    return { status: "failed", error: err.message || "Network error" };
  }
}

export async function apiNewsRefresh(): Promise<{ status: string; error?: string }> {
  try {
    const fn = window["fetch"];
    const res = await fn("/api/news/refresh", { method: "POST" });
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.status !== "failed") {
      return { status: "success" };
    }
    if (res.status === 429) {
      return { status: "rate_limited", error: data.error || "Rate limited" };
    }
    return { status: "failed", error: data.error || "News refresh failed" };
  } catch (err: any) {
    return { status: "failed", error: err.message || "Network error" };
  }
}
