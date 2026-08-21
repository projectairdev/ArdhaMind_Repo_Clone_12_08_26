// Asset registry - tracks all downloaded authentic market assets
// Sources documented in MANIFEST.json
// 
// IMPORTANT: Assets sourced from Wikimedia Commons (public domain / CC0 / freely licensed).
// Corporate logos remain trademarked by their respective owners.
// Use only in referential/data-display contexts.
//
// Thumbnail note: Wikimedia now restricts thumbnail pixel widths to an allowed list.
// Direct SVG/full-resolution downloads used instead.

export const ASSET_BASE = '/assets/';

export const MarketAssets = {
  // ── Exchanges ──────────────────────────────────────────────────────────────
  /** National Stock Exchange of India — SVG monogram fallback (official logo not on Wikimedia) */
  NSE: { path: 'exchanges/nse.svg', fallback: 'NSE', type: 'svg' as const, status: 'monogram' as const },

  // ── Indices ─────────────────────────────────────────────────────────────────
  /** S&P Global Ratings logo — Wikimedia Commons, public domain */
  SP_GLOBAL: { path: 'indices/sp_global.svg', fallback: 'SPX', type: 'svg' as const, status: 'downloaded' as const },
  /** Standard & Poor's wordmark — Wikimedia Commons, public domain */
  SP500: { path: 'indices/sp500.svg', fallback: 'SPX', type: 'svg' as const, status: 'downloaded' as const },
  /** NASDAQ logo — Wikimedia Commons, public domain */
  NASDAQ: { path: 'indices/nasdaq.svg', fallback: 'NQ', type: 'svg' as const, status: 'downloaded' as const },
  /** Dow Jones & Company logo — Wikimedia Commons, public domain */
  DOW_JONES: { path: 'indices/dow_jones.svg', fallback: 'DJIA', type: 'svg' as const, status: 'downloaded' as const },
  /** Nikkei Inc. logo — Wikimedia Commons, public domain */
  NIKKEI: { path: 'indices/nikkei.svg', fallback: 'N225', type: 'svg' as const, status: 'downloaded' as const },
  /** Hang Seng Index — SVG monogram fallback (official logo not on Wikimedia) */
  HANG_SENG: { path: 'indices/hang_seng.svg', fallback: 'HSI', type: 'svg' as const, status: 'monogram' as const },

  // ── Commodities ─────────────────────────────────────────────────────────────
  /** Gold bullion photograph — Wikimedia Commons, CC BY-SA 3.0 */
  GOLD: { path: 'commodities/gold.jpg', fallback: 'XAU', type: 'jpg' as const, status: 'downloaded' as const },
  /** Brent crude — Oil Platform P-51 photograph — Wikimedia Commons, CC BY-SA 3.0 */
  BRENT: { path: 'commodities/brent_crude.jpg', fallback: 'BRN', type: 'jpg' as const, status: 'downloaded' as const },

  // ── Currencies ──────────────────────────────────────────────────────────────
  /** Indian Rupee symbol SVG — Wikimedia Commons, public domain */
  INR: { path: 'currencies/inr.svg', fallback: '₹', type: 'svg' as const, status: 'downloaded' as const },
  /** Flag of India SVG — Wikimedia Commons, public domain */
  INDIA_FLAG: { path: 'currencies/india_flag.svg', fallback: 'IN', type: 'svg' as const, status: 'downloaded' as const },
  /** US Flag SVG (DoS ECA Color Standard) — Wikimedia Commons, public domain */
  USD: { path: 'currencies/usd.svg', fallback: '$', type: 'svg' as const, status: 'downloaded' as const },

  // ── Institutions & Regulators ──────────────────────────────────────────────
  RBI: { path: 'institutions/rbi.svg', fallback: 'RBI', type: 'svg' as const, status: 'downloaded' as const },
  SEBI: { path: 'institutions/sebi.svg', fallback: 'SEBI', type: 'svg' as const, status: 'downloaded' as const },
  FED: { path: 'institutions/fed.svg', fallback: 'FED', type: 'svg' as const, status: 'downloaded' as const },
  ECB: { path: 'institutions/ecb.svg', fallback: 'ECB', type: 'svg' as const, status: 'downloaded' as const },
  BSE: { path: 'exchanges/bse.svg', fallback: 'BSE', type: 'svg' as const, status: 'downloaded' as const },
  ZERODHA: { path: 'institutions/zerodha.svg', fallback: 'ZERODHA', type: 'svg' as const, status: 'downloaded' as const },
  OPENAI: { path: 'institutions/openai.svg', fallback: 'OPENAI', type: 'svg' as const, status: 'downloaded' as const },

  // ── Publishers ──────────────────────────────────────────────────────────────
  REUTERS: { path: 'publishers/reuters.svg', fallback: 'REUTERS', type: 'svg' as const, status: 'downloaded' as const },
  BLOOMBERG: { path: 'publishers/bloomberg.svg', fallback: 'BLOOMBERG', type: 'svg' as const, status: 'downloaded' as const },

  // ── Companies ───────────────────────────────────────────────────────────────
  APOLLOHOSP: { path: 'companies/apollohosp.svg', fallback: 'APOLLO', type: 'svg' as const, status: 'downloaded' as const },
  BHARTIARTL: { path: 'companies/bhartiartl.svg', fallback: 'AIRTEL', type: 'svg' as const, status: 'downloaded' as const },
  TMPV: { path: 'companies/tmpv.svg', fallback: 'TMPV', type: 'svg' as const, status: 'downloaded' as const },
  JIOFIN: { path: 'companies/jiofin.svg', fallback: 'JIOFIN', type: 'svg' as const, status: 'downloaded' as const },
  RELIANCE: { path: 'companies/reliance.svg', fallback: 'RELIANCE', type: 'svg' as const, status: 'downloaded' as const },
  HDFCBANK: { path: 'companies/hdfcbank.svg', fallback: 'HDFC', type: 'svg' as const, status: 'downloaded' as const },
  ICICIBANK: { path: 'companies/icicibank.svg', fallback: 'ICICI', type: 'svg' as const, status: 'downloaded' as const },
  TCS: { path: 'companies/tcs.svg', fallback: 'TCS', type: 'svg' as const, status: 'downloaded' as const },
  INFY: { path: 'companies/infy.svg', fallback: 'INFY', type: 'svg' as const, status: 'downloaded' as const },
} as const;

export type AssetKey = keyof typeof MarketAssets;
export type AssetStatus = 'downloaded' | 'monogram' | 'failed';

/** Returns the full asset URL for use in <img src> or CSS background-image */
export function assetUrl(key: AssetKey): string {
  return `${ASSET_BASE}${MarketAssets[key].path}`;
}

/** Returns true if this asset was successfully downloaded from an official source */
export function isAuthentic(key: AssetKey): boolean {
  return MarketAssets[key].status === 'downloaded';
}
