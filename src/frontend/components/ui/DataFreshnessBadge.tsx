// src/frontend/components/ui/DataFreshnessBadge.tsx
/**
 * DataFreshnessBadge
 * ------------------
 * One shared "as of HH:MM:SS IST" freshness indicator.
 *
 * The timestamp MUST come from the data's own observation / exchange time
 * (e.g. `envelope.market.nifty.exchange_timestamp`, a macro quote's
 * `observation_timestamp`) — never from browser render time or packet-receipt
 * time. Pass that ISO string as `observedAt`.
 *
 * Staleness is judged against a threshold appropriate to the data type:
 *   - "realtime": live tick data (NIFTY spot, India VIX)  → stale after 45s
 *   - "chain":    option-chain aggregates                 → stale after 120s
 *   - "periodic": macro / cross-asset quotes              → stale after 15m
 * A `staleAfterSeconds` prop overrides the preset. Data older than 4x the
 * threshold is flagged "very stale" (red); between 1x and 4x is "stale" (amber).
 *
 * When `observedAt` is missing/unparseable the badge shows an explicit
 * "awaiting data" state rather than a fabricated time.
 */

import React from "react";

export type FreshnessKind = "realtime" | "chain" | "periodic";

const PRESET_THRESHOLD_SECONDS: Record<FreshnessKind, number> = {
  realtime: 45,
  chain: 120,
  periodic: 15 * 60,
};

export interface DataFreshnessBadgeProps {
  /** ISO-8601 observation/exchange timestamp of the underlying data. */
  observedAt?: string | number | Date | null;
  /** Data-type preset that sets the default staleness threshold. */
  kind?: FreshnessKind;
  /** Explicit staleness threshold in seconds (overrides `kind`'s preset). */
  staleAfterSeconds?: number;
  /** Optional short prefix, e.g. "Ticks" → "Ticks as of 14:32:05 IST". */
  label?: string;
  /** Extra freshness text from the source (e.g. quote.freshnessStatus / sessionContext). */
  sourceStatus?: string | null;
  /** Injected clock for tests. Defaults to `Date.now()`. */
  nowMs?: number;
  className?: string;
  /** Compact mode drops the "as of" wording and the seconds. */
  compact?: boolean;
}

function parseMs(value: DataFreshnessBadgeProps["observedAt"]): number | null {
  if (value == null) return null;
  if (value instanceof Date) {
    const t = value.getTime();
    return Number.isFinite(t) ? t : null;
  }
  if (typeof value === "number") {
    // Accept seconds or milliseconds.
    const ms = value < 1e12 ? value * 1000 : value;
    return Number.isFinite(ms) ? ms : null;
  }
  const s = String(value).trim();
  if (!s) return null;
  const t = Date.parse(s);
  return Number.isFinite(t) ? t : null;
}

function istClock(ms: number, withSeconds: boolean): string {
  try {
    return new Date(ms).toLocaleTimeString("en-GB", {
      timeZone: "Asia/Kolkata",
      hour: "2-digit",
      minute: "2-digit",
      ...(withSeconds ? { second: "2-digit" } : {}),
      hour12: false,
    });
  } catch {
    return "--:--";
  }
}

/** IST calendar day (YYYY-MM-DD) for a timestamp, for same-day comparison. */
function istDay(ms: number): string {
  try {
    return new Date(ms).toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });
  } catch {
    return "";
  }
}

/**
 * "HH:MM:SS IST" when the observation is from the current IST day, otherwise
 * "DD MMM HH:MM IST" — a bare time-of-day is misleading next to a "7d ago"
 * staleness marker (the time can read later than the wall clock).
 */
function istStamp(ms: number, nowMs: number, withSeconds: boolean): string {
  const clock = istClock(ms, withSeconds);
  const obsDay = istDay(ms);
  if (obsDay && obsDay === istDay(nowMs)) return `${clock} IST`;
  try {
    const datePart = new Date(ms).toLocaleDateString("en-GB", {
      timeZone: "Asia/Kolkata",
      day: "2-digit",
      month: "short",
    });
    return `${datePart} ${istClock(ms, false)} IST`;
  } catch {
    return `${clock} IST`;
  }
}

function humanizeAge(seconds: number): string {
  if (seconds < 60) return `${Math.max(0, Math.round(seconds))}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)}h ago`;
  return `${Math.round(seconds / 86400)}d ago`;
}

export const DataFreshnessBadge: React.FC<DataFreshnessBadgeProps> = ({
  observedAt,
  kind = "realtime",
  staleAfterSeconds,
  label,
  sourceStatus,
  nowMs,
  className = "",
  compact = false,
}) => {
  const observedMs = parseMs(observedAt);
  const now = nowMs ?? Date.now();
  const threshold = staleAfterSeconds ?? PRESET_THRESHOLD_SECONDS[kind];

  const base =
    "inline-flex items-center gap-1 rounded-[2px] border px-1.5 py-0.5 font-mono text-[8.5px] font-semibold uppercase tracking-wider whitespace-nowrap";

  if (observedMs == null) {
    return (
      <span
        className={`${base} border-neutral-700/50 bg-neutral-800/40 text-neutral-400 ${className}`}
        title="No observation timestamp available for this data"
        data-testid="data-freshness-badge"
        data-freshness="unknown"
      >
        <span aria-hidden>◴</span>
        Awaiting data
      </span>
    );
  }

  const ageSeconds = Math.max(0, (now - observedMs) / 1000);
  const level: "fresh" | "stale" | "very-stale" =
    ageSeconds > threshold * 4 ? "very-stale" : ageSeconds > threshold ? "stale" : "fresh";

  const palette =
    level === "very-stale"
      ? "border-rose-500/40 bg-rose-500/10 text-rose-300"
      : level === "stale"
      ? "border-amber-500/40 bg-amber-500/10 text-amber-300"
      : "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";

  const stamp = istStamp(observedMs, now, !compact);
  const prefix = label ? `${label} ` : "";
  const core = compact ? `${prefix}${stamp}` : `${prefix}as of ${stamp}`;
  const stalePart = level === "fresh" ? "" : ` · ${humanizeAge(ageSeconds)}`;

  return (
    <span
      className={`${base} ${palette} ${className}`}
      title={
        `Observed ${new Date(observedMs).toISOString()} (${humanizeAge(ageSeconds)})` +
        (sourceStatus ? ` — ${sourceStatus}` : "")
      }
      data-testid="data-freshness-badge"
      data-freshness={level}
    >
      <span aria-hidden>{level === "fresh" ? "●" : "▲"}</span>
      {core}
      {stalePart}
      {sourceStatus ? <span className="text-neutral-400 normal-case">· {sourceStatus}</span> : null}
    </span>
  );
};

export default DataFreshnessBadge;
