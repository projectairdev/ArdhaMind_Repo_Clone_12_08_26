// src/frontend/utils/symbolNormalizer.ts

export const CANONICAL_INDEX_SYMBOLS = {
  NIFTY_50: "NSE:NIFTY 50",
  INDIA_VIX: "NSE:INDIA VIX",
  NIFTY_BANK: "NSE:NIFTY BANK",
  NIFTY_FIN_SERVICE: "NSE:NIFTY FIN SERVICE",
  NIFTY_MID_SELECT: "NSE:NIFTY MID SELECT",
} as const;

const SYMBOL_MAPPING: Record<string, string> = {
  "NIFTY 50": "NSE:NIFTY 50",
  "NIFTY": "NSE:NIFTY 50",
  "NIFTY50": "NSE:NIFTY 50",
  "NSE:NIFTY 50": "NSE:NIFTY 50",
  "NSE:NIFTY50": "NSE:NIFTY 50",
  "INDIA VIX": "NSE:INDIA VIX",
  "INDIAVIX": "NSE:INDIA VIX",
  "NSE:INDIA VIX": "NSE:INDIA VIX",
  "NSE:INDIAVIX": "NSE:INDIA VIX",
  "NIFTY BANK": "NSE:NIFTY BANK",
  "BANKNIFTY": "NSE:NIFTY BANK",
  "NSE:NIFTY BANK": "NSE:NIFTY BANK",
  "NSE:BANKNIFTY": "NSE:NIFTY BANK",
  "NIFTY FIN SERVICE": "NSE:NIFTY FIN SERVICE",
  "FINNIFTY": "NSE:NIFTY FIN SERVICE",
  "NSE:NIFTY FIN SERVICE": "NSE:NIFTY FIN SERVICE",
  "NSE:FINNIFTY": "NSE:NIFTY FIN SERVICE",
  "NIFTY MID SELECT": "NSE:NIFTY MID SELECT",
  "MIDCPNIFTY": "NSE:NIFTY MID SELECT",
  "NSE:NIFTY MID SELECT": "NSE:NIFTY MID SELECT",
  "NSE:MIDCPNIFTY": "NSE:NIFTY MID SELECT",
};

/**
 * Single canonical normalization boundary for instrument keys.
 * Maps all raw symbol aliases to their authoritative canonical identifier.
 */
export function normalizeInstrumentKey(rawSymbol?: string | null): string {
  if (!rawSymbol) return "";
  const s = String(rawSymbol).trim();
  const upper = s.toUpperCase();
  if (SYMBOL_MAPPING[upper]) {
    return SYMBOL_MAPPING[upper];
  }
  return s;
}

/**
 * Checks if symbol is canonical NIFTY 50.
 */
export function isCanonicalNifty(symbol?: string | null): boolean {
  return normalizeInstrumentKey(symbol) === "NSE:NIFTY 50";
}

/**
 * Checks if symbol is canonical INDIA VIX.
 */
export function isCanonicalVix(symbol?: string | null): boolean {
  return normalizeInstrumentKey(symbol) === "NSE:INDIA VIX";
}
