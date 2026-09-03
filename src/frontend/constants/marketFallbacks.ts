/**
 * marketFallbacks.ts — single source of truth for "no real data" fallbacks of
 * market metrics that are surfaced on more than one workspace tab.
 *
 * Policy
 * ------
 * The workstation must never fabricate a plausible-looking market number. When a
 * metric is genuinely unavailable, the UI shows an explicit "awaiting data" / "—"
 * state instead. Every value here is therefore `null` (empty list for the sector
 * list).
 *
 * Why a module of `null`s
 * -----------------------
 * Previously each tab carried its own inline fallback for these metrics and they
 * had drifted apart (India VIX fell back to 10.68 on one tab, 12.5 on another,
 * 13.20 on a third; PCR to 0.94 / 1.08 / 1.02; ATR to 135.10 or `spot * 0.006`).
 * Routing every call site through these named exports guarantees that:
 *   1. every tab resolves the same value at the same moment, and
 *   2. if the "no fabrication" policy is ever deliberately reversed for one
 *      metric, it changes in exactly one place.
 *
 * Do not put a non-null number here without a concrete, documented reason
 * (e.g. a value used purely as a math divisor that can never be null — such a
 * case should keep its own clearly-commented local constant instead).
 */

/** India VIX — shown on MarketPulse, Options Intelligence and Live Guide tabs. */
export const VIX_FALLBACK: number | null = null;

/** Put-Call Ratio (PCR) — shown on MarketPulse, Options Intelligence and Live Guide tabs. */
export const PCR_FALLBACK: number | null = null;

/** Daily ATR(14) in points — shown on MarketPulse, Live, Tomorrow Plan and the horizon chart. */
export const ATR_FALLBACK: number | null = null;

/** Sector-performance list used when no real sector feed is present. */
export const SECTOR_FALLBACK_LIST: readonly unknown[] = [];
