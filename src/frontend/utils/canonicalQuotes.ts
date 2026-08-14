// src/frontend/utils/canonicalQuotes.ts
/**
 * Single-Source-of-Truth Canonical Cross-Asset Quote Resolver for ArdhaMind.
 * Standardizes cross-asset quote extraction for MarketPulseWorkspace and MacroIntelligence.
 */

export type CanonicalQuoteView = {
  canonicalKey: string;
  displayName: string;
  value: number | null;
  change: number | null;
  changePct: number | null;
  sourceName: string | null;
  observedAt: string | null;
  freshnessStatus: string | null;
  sessionContext: string | null;
  currency?: string | null;
  unit?: string | null;
  isAvailable: boolean;
};

const EXPLICIT_ALIAS_MAP: Record<string, { aliases: string[]; displayName: string; unit?: string }> = {
  GIFT_NIFTY: { aliases: ["GIFT_NIFTY", "GIFT NIFTY", "GIFT"], displayName: "GIFT Nifty", unit: "pts" },
  "S&P 500": { aliases: ["S&P 500", "SP500", "^GSPC", "S&P_500"], displayName: "S&P 500" },
  NASDAQ: { aliases: ["NASDAQ", "Nasdaq", "^IXIC"], displayName: "Nasdaq" },
  DOW_JONES: { aliases: ["DOW_JONES", "DOW", "Dow Jones", "^DJI"], displayName: "Dow" },
  NIKKEI_225: { aliases: ["NIKKEI_225", "NIKKEI", "Nikkei 225", "^N225"], displayName: "Nikkei 225" },
  HANG_SENG: { aliases: ["HANG_SENG", "HANG SENG", "Hang Seng", "^HSI"], displayName: "Hang Seng" },
  BRENT_CRUDE: { aliases: ["BRENT_CRUDE", "BRENT", "Brent Crude", "BZ=F"], displayName: "Brent Crude", unit: "$/bbl" },
  GOLD: { aliases: ["GOLD", "Gold", "GC=F"], displayName: "Gold", unit: "$/oz" },
  USD_INR: { aliases: ["USD_INR", "USD/INR", "USDINR", "USDINR=X"], displayName: "USD/INR", unit: "INR" },
  DXY: { aliases: ["DXY", "US Dollar Index", "DX-Y.NYB"], displayName: "DXY" },
  US_10Y: { aliases: ["US_10Y", "US10Y", "US 10Y Yield", "US 10Y", "TNX", "^TNX"], displayName: "US 10Y Yield", unit: "%" },
};

export function getCanonicalQuote(
  quotes: Record<string, any> | undefined | null,
  canonicalKey: string
): CanonicalQuoteView {
  const meta = EXPLICIT_ALIAS_MAP[canonicalKey] || {
    aliases: [canonicalKey],
    displayName: canonicalKey,
  };

  const unavailableView: CanonicalQuoteView = {
    canonicalKey,
    displayName: meta.displayName,
    value: null,
    change: null,
    changePct: null,
    sourceName: null,
    observedAt: null,
    freshnessStatus: null,
    sessionContext: null,
    currency: null,
    unit: meta.unit || null,
    isAvailable: false,
  };

  if (!quotes || typeof quotes !== "object") {
    return unavailableView;
  }

  let foundRaw: any = null;

  // 1. Explicit finite alias lookup
  for (const alias of meta.aliases) {
    if (quotes[alias]) {
      foundRaw = quotes[alias];
      break;
    }
  }

  // 2. Exact normalized fallback if alias array did not hit
  if (!foundRaw) {
    const normTarget = canonicalKey.toUpperCase().replace(/[^A-Z0-9]/g, "");
    for (const [k, v] of Object.entries(quotes)) {
      const normK = k.toUpperCase().replace(/[^A-Z0-9]/g, "");
      if (normK === normTarget) {
        foundRaw = v;
        break;
      }
    }
  }

  if (!foundRaw) {
    return unavailableView;
  }

  const rawVal = foundRaw.price ?? foundRaw.value ?? foundRaw.last_price;
  if (rawVal == null || !Number.isFinite(Number(rawVal)) || Number(rawVal) <= 0) {
    return unavailableView;
  }

  const value = Number(rawVal);
  const change = foundRaw.change != null && Number.isFinite(Number(foundRaw.change)) ? Number(foundRaw.change) : null;
  const changePct = foundRaw.change_pct != null && Number.isFinite(Number(foundRaw.change_pct)) ? Number(foundRaw.change_pct) : null;

  return {
    canonicalKey,
    displayName: foundRaw.name || foundRaw.displayName || meta.displayName,
    value,
    change,
    changePct,
    sourceName: foundRaw.source_name || foundRaw.source || null,
    observedAt: foundRaw.observation_timestamp || foundRaw.observed_at || foundRaw.observedAt || null,
    freshnessStatus: foundRaw.freshness_status || foundRaw.freshness || null,
    sessionContext: getGlobalSessionLabel(canonicalKey, foundRaw),
    currency: foundRaw.currency || null,
    unit: meta.unit || null,
    isAvailable: true,
  };
}

export function getGlobalSessionLabel(key: string, q: any): string {
  if (!q) return "Observation Pending";

  const isAvail = q.isAvailable ?? (q.price != null || q.value != null || q.price_str != null);
  if (!isAvail) return "Observation Pending";

  const upperKey = key.toUpperCase();
  const freshnessStr = String(q.freshness_status || q.freshnessStatus || q.freshness || q.session_context || "").toUpperCase();

  if (freshnessStr.includes("STALE")) return "Stale Data";

  if (upperKey.includes("S&P") || upperKey.includes("NASDAQ") || upperKey.includes("DOW")) {
    return "Previous US Session";
  }
  if (upperKey.includes("NIKKEI") || upperKey.includes("HANG_SENG") || upperKey.includes("HANGSENG") || upperKey.includes("HSI") || upperKey.includes("N225")) {
    return "Current Asian Session";
  }
  if (upperKey.includes("GIFT")) {
    const sessStr = String(q.source_session || q.session_label || q.source_session_detail || "").toUpperCase();
    if (sessStr.includes("CLOSED")) return "Previous Session / Market Closed";
    if (sessStr.includes("PRE_OPEN") || sessStr.includes("PRE-OPEN")) return "Current Pre-Open Session";
    if (sessStr.includes("OPEN")) return "Current Session";
    return q.source_session ? String(q.source_session) : "Current Session";
  }
  if (upperKey.includes("BRENT") || upperKey.includes("GOLD") || upperKey.includes("USD_INR") || upperKey.includes("DXY") || upperKey.includes("US_10Y")) {
    return "Global Telemetry";
  }
  if (freshnessStr.includes("LAST_VALID") || freshnessStr.includes("PREVIOUS")) {
    return "Previous Trading Session";
  }
  return "Global Telemetry";
}
