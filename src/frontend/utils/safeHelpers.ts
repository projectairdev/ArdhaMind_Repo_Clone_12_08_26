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

export function formatCurrency(val: any, fractionDigits = 0): string {
  if (val === null || val === undefined || val === "") return "—";
  const num = Number(val);
  if (isNaN(num)) return "—";
  try {
    return num.toLocaleString("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: fractionDigits,
      minimumFractionDigits: fractionDigits,
    }).replace("INR", "₹").trim();
  } catch {
    return `₹${num.toFixed(fractionDigits)}`;
  }
}

export function formatNumber(val: any, fractionDigits = 0): string {
  if (val === null || val === undefined || val === "") return "—";
  const num = Number(val);
  if (isNaN(num)) return "—";
  try {
    return num.toLocaleString("en-IN", {
      maximumFractionDigits: fractionDigits,
      minimumFractionDigits: fractionDigits,
    });
  } catch {
    return num.toFixed(fractionDigits);
  }
}

export function formatPercent(val: any, fractionDigits = 2): string {
  if (val === null || val === undefined || val === "") return "—";
  const num = Number(val);
  if (isNaN(num)) return "—";
  try {
    return `${num.toLocaleString("en-IN", {
      maximumFractionDigits: fractionDigits,
      minimumFractionDigits: fractionDigits,
    })}%`;
  } catch {
    return `${num.toFixed(fractionDigits)}%`;
  }
}

export function formatDate(val: any, fallback = "N/A"): string {
  if (!val) return fallback;
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return fallback;
    return d.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return fallback;
  }
}
