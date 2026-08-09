// src/frontend/utils/traderTerminology.ts

/**
 * Context-aware trader-facing terminology translation layer.
 * Machine/internal enums and canonical strings remain untouched internally.
 */

export type TermDomain =
  | "confidence"
  | "risk"
  | "impact"
  | "importance"
  | "readiness"
  | "freshness"
  | "positioning"
  | "global"
  | "general";

export function mapTraderEnum(val: unknown, domain: TermDomain = "general"): string {
  if (val === null || val === undefined) return "Unavailable";
  const raw = String(val).trim();
  if (!raw) return "Unavailable";
  const upper = raw.toUpperCase();

  // Context-specific mappings
  if (domain === "confidence") {
    if (upper === "LOW") return "Low Conviction";
    if (upper === "MODERATE") return "Moderate Conviction";
    if (upper === "HIGH") return "High Conviction";
    if (upper === "INSUFFICIENT") return "Insufficient Conviction";
  }

  if (domain === "risk") {
    if (upper === "LOW" || upper === "NORMAL") return "Low Risk";
    if (upper === "MODERATE") return "Moderate Risk";
    if (upper === "ELEVATED" || upper === "ELEVATED_RISK") return "Higher Risk";
    if (upper === "HIGH" || upper === "CRITICAL") return "High Risk";
  }

  if (domain === "impact" || domain === "importance") {
    if (upper === "LOW") return "Low Impact";
    if (upper === "MODERATE") return "Moderate Impact";
    if (upper === "HIGH" || upper === "CRITICAL") return "High Impact";
  }

  if (domain === "global") {
    if (upper === "RISK_ON") return "Positive Global Cues";
    if (upper === "RISK_OFF") return "Weak Global Cues";
  }

  if (domain === "positioning") {
    if (upper === "SHORT_EXCEEDS_LONG") return "Short Positioning Dominant";
    if (upper === "LONG_EXCEEDS_SHORT") return "Long Positioning Dominant";
    if (upper === "NET_SHORT") return "Net Short Bias";
    if (upper === "NET_LONG") return "Net Long Bias";
  }

  // Domain/Context fallback rules & general mappings
  const GENERAL_MAPPINGS: Record<string, string> = {
    // Session & Status
    "MARKET_CLOSED": "Market Closed",
    "CLOSED": "Market Closed",
    "LAST_VALID_SESSION": "Previous Trading Session",
    "LAST_SESSION": "Previous Session",
    "HOLIDAY": "Trading Holiday",
    "WEEKEND": "Market Closed · Weekend",
    "POST_CLOSE": "Market Closed",
    "PRE_OPEN": "Pre-Market",
    "PRE-OPEN": "Pre-Market",
    "MARKET_OPEN": "Market Open",
    "OPEN": "Market Open",
    "VALID": "Validated",
    "VALIDATED": "Validated",
    "NOT_CONFIGURED": "Not Configured",
    "LICENSE_REQUIRED": "Licensed Data Required",
    "PARTIAL_READY": "Partially Ready",
    "PARTIAL": "Partial",
    "READY": "Ready",
    "HEALTHY": "Healthy",
    "PREVIOUS_COMPARISON_NOT_AVAILABLE_YET": "Previous comparison not available yet",
    "UNAVAILABLE": "Unavailable",
    "DEGRADED": "Degraded Data Source",
    "STALE": "Stale Data",

    // Market Alignment / Bias
    "CONFLICTED": "Mixed Signals",
    "MIXED": "Mixed Setup",
    "INSUFFICIENT_EVIDENCE": "No Clear Setup",
    "UNCERTAIN": "No Clear Direction",
    "BULLISH": "Bullish Bias",
    "BEARISH": "Bearish Bias",
    "NEUTRAL": "Neutral",

    // Risk environments
    "RISK_ON": "Risk-On Environment",
    "RISK_OFF": "Risk-Off Environment",

    // Temporal Context & Decision Usability
    "CURRENT_SESSION": "Current Session",
    "PREVIOUS_SESSION": "Previous Trading Session",
    "OVERNIGHT_SINCE_CLOSE": "Since India Close",
    "FOREIGN_SESSION": "Latest Foreign Session",
    "CURRENT_ELIGIBLE": "Current Session Eligible",
    "CONTEXT_ONLY": "Context Only",
    "INELIGIBLE": "Ineligible",
    "PRICE_STRUCTURE": "Price Structure",
    "OPTION_OI": "Option OI",
    "MAX_PAIN": "Max Pain Level",
    "ATM": "ATM Strike",

    // Professional positioning
    "NET_SHORT": "Net Short Bias",
    "NET_LONG": "Net Long Bias",
    "SHORT_EXCEEDS_LONG": "Short Positioning Dominant",
    "LONG_EXCEEDS_SHORT": "Long Positioning Dominant",

    // Workspace & Concept terms
    "INSTITUTIONAL CONTEXT": "FII / DII Positioning",
    "INSTITUTIONAL DERIVATIVES": "FII / DII Positioning",
    "OPENING CONTEXT": "Expected Opening",
    "GLOBAL CONTEXT": "Global Cues",
    "NEWS / EVENT RISK": "News & Event Risk",
    "ACTIVE SCENARIOS": "Possible Market Scenarios",
    "CONFIRMATION": "What Supports the Setup",
    "CONFIRMING SIGNALS": "What Supports This View",
    "CONTRADICTING SIGNALS": "What Goes Against It",
    "INVALIDATION": "What Would Change This View",
    "INVALIDATION / RISK": "What Could Break the Setup",
    "EVIDENCE COMPLETENESS": "Evidence Coverage",
    "NEXT-SESSION SETUP": "Tomorrow's Market Setup",
    "GENUINE KEY LEVELS": "Key Levels to Watch",
  };

  if (GENERAL_MAPPINGS[upper]) return GENERAL_MAPPINGS[upper];
  if (GENERAL_MAPPINGS[raw]) return GENERAL_MAPPINGS[raw];

  return raw
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, l => l.toUpperCase());
}

export function mapTraderLabel(label: unknown): string {
  if (!label) return "";
  return mapTraderEnum(label, "general");
}

export function mapFreshness(freshness: unknown): string {
  if (!freshness) return "Unavailable";
  const str = String(freshness).toUpperCase();
  if (str === "LAST_VALID_SESSION" || str === "PREVIOUS_SESSION") return "Previous Trading Session";
  if (str === "FRESH" || str === "LIVE") return "Live / Current Session";
  if (str === "STALE") return "Stale Data";
  return mapTraderEnum(str, "freshness");
}
