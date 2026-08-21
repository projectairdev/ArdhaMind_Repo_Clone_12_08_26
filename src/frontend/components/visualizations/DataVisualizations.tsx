/**
 * DataVisualizations.tsx
 * 
 * Data-driven visualization components for ArdhaMind financial terminal.
 * All visualizations operate strictly on canonical data.
 * NO synthetic/fabricated data. If data is unavailable, component collapses gracefully.
 */
import React from "react";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { InstrumentVisual } from "../ui/AuthenticMarketLogo";
import { formatNumber, safeArray } from "../../utils/safeHelpers";
import { SectionHeader, Surface } from "../ui/WorkspacePrimitives";


// ─── MARKET BREADTH METER ─────────────────────────────────────────────────────

interface BreadthMeterProps {
  advances: number | null;
  declines: number | null;
  unchanged?: number | null;
  total?: number | null;
}

export function MarketBreadthMeter({ advances, declines, unchanged, total }: BreadthMeterProps) {
  if (advances == null && declines == null) {
    return (
      <div className="text-[11px] text-slate-500 font-mono py-2">Breadth unavailable</div>
    );
  }

  const adv = Number(advances) || 0;
  const dec = Number(declines) || 0;
  const unch = Number(unchanged) || 0;
  const sum = adv + dec + unch || 1;

  const advPct = Math.round((adv / sum) * 100);
  const decPct = Math.round((dec / sum) * 100);
  const unchPct = Math.max(0, 100 - advPct - decPct);

  const bullish = adv > dec;
  const bearish = dec > adv;

  return (
    <div className="space-y-2.5 py-1">
      {/* Stacked bar */}
      <div className="h-2.5 w-full rounded-full overflow-hidden flex gap-px bg-[#0a0a10]">
        <div
          style={{ width: `${advPct}%` }}
          className="bg-[#00E5A8] rounded-l-full transition-all duration-500"
          title={`Advancing: ${adv}`}
        />
        {unchPct > 0 && (
          <div
            style={{ width: `${unchPct}%` }}
            className="bg-[#39D9FF]/40"
            title={`Unchanged: ${unch}`}
          />
        )}
        <div
          style={{ width: `${decPct}%` }}
          className="bg-[#FF5C77] rounded-r-full transition-all duration-500"
          title={`Declining: ${dec}`}
        />
      </div>

      {/* Labels */}
      <div className="flex items-center justify-between text-[10px] font-mono">
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-[#00E5A8]" />
          <span className="text-[#00E5A8] font-bold">{adv}</span>
          <span className="text-slate-500">ADV</span>
        </div>
        {unch > 0 && (
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-[#39D9FF]/50" />
            <span className="text-slate-400">{unch} UNCH</span>
          </div>
        )}
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500">DEC</span>
          <span className="text-[#FF5C77] font-bold">{dec}</span>
          <span className="h-1.5 w-1.5 rounded-full bg-[#FF5C77]" />
        </div>
      </div>

      {/* Ratio badge */}
      <div className="flex justify-center">
        <span
          className={`rounded-full border px-3 py-0.5 text-[10px] font-bold font-mono ${
            bullish
              ? "border-[#00E5A8]/30 bg-[#00E5A8]/10 text-[#00E5A8]"
              : bearish
              ? "border-[#FF5C77]/30 bg-[#FF5C77]/10 text-[#FF5C77]"
              : "border-[#39D9FF]/30 bg-[#39D9FF]/10 text-[#39D9FF]"
          }`}
        >
          {bullish ? "▲ BROAD ADVANCE" : bearish ? "▼ BROAD DECLINE" : "◆ NEUTRAL"}
          {" · "}
          {advPct}% / {decPct}%
        </span>
      </div>
    </div>
  );
}

// ─── DAY RANGE SLIDER ─────────────────────────────────────────────────────────

interface DayRangeBarProps {
  low: number | null;
  high: number | null;
  current: number | null;
  previousClose?: number | null;
}

export function DayRangeBar({ low, high, current, previousClose }: DayRangeBarProps) {
  if (low == null || high == null || current == null) {
    return (
      <div className="text-[11px] text-slate-500 font-mono py-2">Range unavailable</div>
    );
  }

  const lo = Number(low);
  const hi = Number(high);
  const cur = Number(current);
  const range = hi - lo || 1;

  const curPct = Math.min(100, Math.max(0, ((cur - lo) / range) * 100));
  const pcPct =
    previousClose != null
      ? Math.min(100, Math.max(0, ((Number(previousClose) - lo) / range) * 100))
      : null;

  const fmt = (v: number) =>
    v >= 1000 ? v.toLocaleString("en-IN", { maximumFractionDigits: 1 }) : v.toFixed(2);

  return (
    <div className="space-y-2 py-1">
      <div className="relative h-3 w-full rounded-full bg-[#111118]">
        {/* Gradient fill from lo to hi */}
        <div className="absolute inset-y-0 left-0 right-0 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{
              width: `${curPct}%`,
              background: "linear-gradient(to right, #FF5C77 0%, #FFB84D 50%, #00E5A8 100%)",
            }}
          />
        </div>

        {/* Previous close marker */}
        {pcPct != null && (
          <div
            className="absolute top-1/2 -translate-y-1/2 h-5 w-0.5 bg-[#39D9FF] opacity-80"
            style={{ left: `${pcPct}%` }}
            title={`Prev close: ${fmt(Number(previousClose))}`}
          />
        )}

        {/* Current price thumb */}
        <div
          className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 h-4 w-4 rounded-full border-2 border-[#000] bg-[#FFB84D] shadow-[0_0_6px_#FFB84D]"
          style={{ left: `${curPct}%` }}
          title={`Current: ${fmt(cur)}`}
        />
      </div>

      {/* Labels */}
      <div className="flex justify-between text-[10px] font-mono">
        <div>
          <div className="text-[#FF5C77] font-bold">▼ {fmt(lo)}</div>
          <div className="text-slate-500 text-[9px]">DAY LOW</div>
        </div>
        <div className="text-center">
          <div className="text-[#FFB84D] font-bold">{fmt(cur)}</div>
          <div className="text-slate-500 text-[9px]">CURRENT</div>
        </div>
        <div className="text-right">
          <div className="text-[#00E5A8] font-bold">▲ {fmt(hi)}</div>
          <div className="text-slate-500 text-[9px]">DAY HIGH</div>
        </div>
      </div>
    </div>
  );
}

// ─── SUPPORT / RESISTANCE LEVEL MAP ──────────────────────────────────────────

interface PriceLevelMapProps {
  resistances: number[];
  supports: number[];
  pivot: number | null;
  current: number | null;
}

export function PriceLevelMap({ resistances, supports, pivot, current }: PriceLevelMapProps) {
  const allLevels: Array<{ label: string; price: number; kind: "resistance" | "support" | "pivot" | "current" }> = [];

  resistances.slice(0, 3).forEach((p, i) => {
    if (Number.isFinite(p)) allLevels.push({ label: `R${i + 1}`, price: p, kind: "resistance" });
  });
  if (pivot != null && Number.isFinite(pivot))
    allLevels.push({ label: "Pivot", price: Number(pivot), kind: "pivot" });
  supports.slice(0, 3).forEach((p, i) => {
    if (Number.isFinite(p)) allLevels.push({ label: `S${i + 1}`, price: p, kind: "support" });
  });

  if (allLevels.length === 0) {
    return (
      <div className="text-[11px] text-slate-500 font-mono py-2">Key levels unavailable</div>
    );
  }

  // Sort descending by price
  allLevels.sort((a, b) => b.price - a.price);

  const prices = allLevels.map((l) => l.price);
  const allPrices = current != null ? [...prices, Number(current)] : prices;
  const minP = Math.min(...allPrices);
  const maxP = Math.max(...allPrices);
  const pRange = maxP - minP || 1;

  const fmt = (v: number) =>
    v >= 1000 ? v.toLocaleString("en-IN", { maximumFractionDigits: 0 }) : v.toFixed(1);

  const colorFor = (kind: string) => {
    if (kind === "resistance") return { dot: "bg-[#FF5C77]", text: "text-[#FF5C77]", border: "border-[#FF5C77]/30" };
    if (kind === "support") return { dot: "bg-[#00E5A8]", text: "text-[#00E5A8]", border: "border-[#00E5A8]/30" };
    if (kind === "pivot") return { dot: "bg-[#FFB84D]", text: "text-[#FFB84D]", border: "border-[#FFB84D]/30" };
    return { dot: "bg-[#39D9FF]", text: "text-[#39D9FF]", border: "border-[#39D9FF]/30" };
  };

  return (
    <div className="space-y-1.5 py-1">
      {allLevels.map((level) => {
        const pct = ((level.price - minP) / pRange) * 100;
        const c = colorFor(level.kind);
        const isCurrent =
          current != null && Math.abs(Number(current) - level.price) / pRange < 0.04;

        return (
          <div key={`${level.label}-${level.price}`} className="flex items-center gap-2">
            {/* Label */}
            <span className={`w-10 text-[10px] font-bold font-mono text-right ${c.text}`}>
              {level.label}
            </span>

            {/* Bar track */}
            <div className="flex-1 h-1 rounded-full bg-[#111118] relative">
              <div
                className={`absolute inset-y-0 left-0 rounded-full ${c.dot.replace("bg-", "bg-")}`}
                style={{ width: `${pct}%`, opacity: 0.6 }}
              />
            </div>

            {/* Price + current indicator */}
            <span
              className={`w-20 text-right text-[10px] font-mono font-semibold ${c.text} ${
                isCurrent ? "underline underline-offset-2" : ""
              }`}
            >
              {fmt(level.price)}{isCurrent ? " ◄" : ""}
            </span>
          </div>
        );
      })}

      {/* Current price indicator if not near a level */}
      {current != null && (
        <div className="flex items-center gap-2 border-t border-[#1a1a22] pt-1.5 mt-1.5">
          <span className="w-10 text-[10px] font-bold font-mono text-right text-[#39D9FF]">LTP</span>
          <div className="flex-1 h-0.5 bg-[#39D9FF]/20 relative">
            <div
              className="absolute inset-y-0 left-0 bg-[#39D9FF]"
              style={{ width: `${((Number(current) - minP) / pRange) * 100}%` }}
            />
          </div>
          <span className="w-20 text-right text-[10px] font-mono font-bold text-[#39D9FF]">
            {fmt(Number(current))}
          </span>
        </div>
      )}
    </div>
  );
}

// ─── VIX GAUGE ────────────────────────────────────────────────────────────────

interface VixGaugeProps {
  value: number | null;
  regime?: string | null;
}

export function VixGauge({ value, regime }: VixGaugeProps) {
  if (value == null) {
    return (
      <div className="text-[11px] text-slate-500 font-mono py-2">India VIX unavailable</div>
    );
  }

  const vix = Number(value);
  // VIX scale: 0-10 low, 10-20 normal, 20-30 elevated, 30+ extreme
  const clamped = Math.min(40, Math.max(0, vix));
  const pct = (clamped / 40) * 100;

  const color =
    vix < 12 ? "#00E5A8" : vix < 20 ? "#39D9FF" : vix < 28 ? "#FFB84D" : "#FF5C77";
  const label =
    vix < 12 ? "LOW" : vix < 20 ? "NORMAL" : vix < 28 ? "ELEVATED" : "EXTREME";

  return (
    <div className="space-y-2 py-1">
      {/* Arc gauge (SVG) */}
      <div className="flex justify-center">
        <svg width="120" height="68" viewBox="0 0 120 68" className="overflow-visible">
          {/* Background arc */}
          <path
            d="M 10 60 A 50 50 0 0 1 110 60"
            fill="none"
            stroke="#1a1a22"
            strokeWidth="10"
            strokeLinecap="round"
          />
          {/* Colored fill arc — using stroke-dasharray trick */}
          {(() => {
            const circumference = Math.PI * 50; // half circle
            const dashLen = (pct / 100) * circumference;
            return (
              <path
                d="M 10 60 A 50 50 0 0 1 110 60"
                fill="none"
                stroke={color}
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={`${dashLen} ${circumference}`}
                style={{ transition: "stroke-dasharray 0.6s ease" }}
              />
            );
          })()}
          {/* Value text */}
          <text
            x="60"
            y="58"
            textAnchor="middle"
            fontSize="16"
            fontWeight="bold"
            fill={color}
            fontFamily="monospace"
          >
            {vix.toFixed(2)}
          </text>
        </svg>
      </div>

      {/* Zone labels */}
      <div className="flex justify-between text-[9px] font-mono text-slate-500 px-2">
        <span>LOW</span>
        <span>NORMAL</span>
        <span>HIGH</span>
        <span>EXTREME</span>
      </div>

      {/* Regime badge */}
      <div className="flex justify-center">
        <span
          className="rounded-full border px-3 py-0.5 text-[10px] font-bold font-mono"
          style={{ color, borderColor: `${color}40`, backgroundColor: `${color}10` }}
        >
          {regime || label}
        </span>
      </div>
    </div>
  );
}

// ─── FII / DII FLOW BARS ──────────────────────────────────────────────────────

interface FlowBarProps {
  fiiNet: number | null;
  diiNet: number | null;
  label?: string;
}

export function InstitutionalFlowBars({ fiiNet, diiNet, label }: FlowBarProps) {
  if (fiiNet == null && diiNet == null) {
    return (
      <div className="text-[11px] text-slate-500 font-mono py-2">
        FII/DII flows unavailable
      </div>
    );
  }

  const maxAbs = Math.max(Math.abs(Number(fiiNet) || 0), Math.abs(Number(diiNet) || 0), 1);

  function FlowRow({ label, value }: { label: string; value: number | null }) {
    if (value == null) {
      return (
        <div className="flex items-center gap-2 text-[11px]">
          <span className="w-8 text-right font-mono text-slate-400">{label}</span>
          <span className="flex-1 text-slate-500 font-mono text-[10px]">Not observed</span>
        </div>
      );
    }
    const v = Number(value);
    const pct = Math.min(100, (Math.abs(v) / maxAbs) * 100);
    const positive = v >= 0;
    const fmt = `${positive ? "+" : ""}${v.toLocaleString("en-IN", { maximumFractionDigits: 1 })} Cr`;

    return (
      <div className="space-y-1">
        <div className="flex justify-between text-[10px] font-mono">
          <span className="font-bold text-slate-300">{label}</span>
          <span className={`font-bold ${positive ? "text-[#00C896]" : "text-[#E5484D]"}`}>
            {fmt}
          </span>
        </div>
        <div className="h-2 w-full rounded-full bg-[#111118] overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              positive ? "bg-[#00C896]" : "bg-[#E5484D]"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    );
  }

  const net = (Number(fiiNet) || 0) + (Number(diiNet) || 0);

  return (
    <div className="space-y-3 py-1">
      <FlowRow label="FII" value={fiiNet} />
      <FlowRow label="DII" value={diiNet} />

      {/* Net positioning */}
      {fiiNet != null && diiNet != null && (
        <div className="border-t border-[#1a1a22] pt-2">
          <div className="flex justify-between text-[10px] font-mono text-slate-400">
            <span>Net institutional</span>
            <span
              className={`font-bold ${
                net >= 0 ? "text-[#00C896]" : "text-[#E5484D]"
              }`}
            >
              {net >= 0 ? "+" : ""}
              {net.toLocaleString("en-IN", { maximumFractionDigits: 1 })} Cr
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── OPTIONS CONTEXT SNAPSHOT ──────────────────────────────────────────────────

export interface OptionsSnapshotProps {
  pcr?: number | null;
  maxPain?: number | null;
  atmStrike?: number | null;
  atmIv?: number | null;
}

export function OptionsSnapshot({ pcr, maxPain, atmStrike, atmIv }: OptionsSnapshotProps) {
  return (
    <div className="grid grid-cols-2 gap-2 text-[10px] font-mono py-1">
      <div className="rounded-[3px] border border-[#191D23] bg-[#0E1013] p-2">
        <div className="text-[9px] uppercase font-semibold text-[#707987]">PCR (OI)</div>
        <div className="mt-0.5 text-[12px] font-bold text-[#E6E8EB]">
          {pcr != null ? Number(pcr).toFixed(2) : "Unavailable"}
        </div>
      </div>
      <div className="rounded-[3px] border border-[#191D23] bg-[#0E1013] p-2">
        <div className="text-[9px] uppercase font-semibold text-[#707987]">Max Pain</div>
        <div className="mt-0.5 text-[12px] font-bold text-[#E6E8EB]">
          {maxPain != null ? Number(maxPain).toLocaleString("en-IN", { maximumFractionDigits: 0 }) : "Unavailable"}
        </div>
      </div>
      <div className="rounded-[3px] border border-[#191D23] bg-[#0E1013] p-2">
        <div className="text-[9px] uppercase font-semibold text-[#707987]">ATM Strike</div>
        <div className="mt-0.5 text-[12px] font-bold text-[#38BDF8]">
          {atmStrike != null ? Number(atmStrike).toLocaleString("en-IN", { maximumFractionDigits: 0 }) : "Unavailable"}
        </div>
      </div>
      <div className="rounded-[3px] border border-[#191D23] bg-[#0E1013] p-2">
        <div className="text-[9px] uppercase font-semibold text-[#707987]">ATM IV</div>
        <div className="mt-0.5 text-[12px] font-bold text-[#E59700]">
          {atmIv != null ? `${Number(atmIv).toFixed(1)}%` : "Unavailable"}
        </div>
      </div>
    </div>
  );
}

// ─── PERFORMANCE BAR (for Gainers / Losers) ──────────────────────────────────

interface PerformanceBarProps {
  symbol: string;
  changePct: number | null;
  maxAbs?: number;
  key?: React.Key;
}

export function PerformanceBar({ symbol, changePct, maxAbs = 5 }: PerformanceBarProps) {
  if (changePct == null) {
    return (
      <div className="flex items-center gap-2 h-7 text-[11px]">
        <span className="w-24 truncate font-semibold text-slate-400">{symbol}</span>
        <span className="text-slate-500 font-mono text-[10px]">Unavailable</span>
      </div>
    );
  }

  const v = Number(changePct);
  const positive = v >= 0;
  const pct = Math.min(100, (Math.abs(v) / Math.max(maxAbs, Math.abs(v), 0.01)) * 100);

  return (
    <div className="flex items-center gap-2 h-8 group">
      <InstrumentVisual symbol={symbol} size={18} />
      <span className="w-24 truncate text-[11px] font-semibold text-slate-200 group-hover:text-slate-100 transition-colors">
        {symbol}
      </span>
      <span
        className={`w-16 text-right text-[11px] font-bold font-mono ${
          positive ? "text-[#00E5A8]" : "text-[#FF5C77]"
        }`}
      >
        {positive ? "+" : ""}{v.toFixed(2)}%
      </span>
      <div className="flex-1 h-1.5 rounded-full bg-[#111118] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            positive ? "bg-[#00E5A8]" : "bg-[#FF5C77]"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── GLOBAL MARKET SESSION STRIP ─────────────────────────────────────────────

interface SessionInfo {
  name: string;
  tz: string;
  open: string; // "09:00"
  close: string; // "17:30"
  utcOffset: number; // hours from UTC
}

const GLOBAL_SESSIONS: SessionInfo[] = [
  { name: "Tokyo", tz: "JST", open: "09:00", close: "15:30", utcOffset: 9 },
  { name: "Shanghai", tz: "CST", open: "09:30", close: "15:00", utcOffset: 8 },
  { name: "Hong Kong", tz: "HKT", open: "09:30", close: "16:00", utcOffset: 8 },
  { name: "Mumbai", tz: "IST", open: "09:15", close: "15:30", utcOffset: 5.5 },
  { name: "Frankfurt", tz: "CET", open: "09:00", close: "17:30", utcOffset: 2 },
  { name: "London", tz: "BST", open: "08:00", close: "16:30", utcOffset: 1 },
  { name: "New York", tz: "EDT", open: "09:30", close: "16:00", utcOffset: -4 },
];

function isSessionOpen(session: SessionInfo, utcNow: Date): boolean {
  const localH = utcNow.getUTCHours() + session.utcOffset;
  const localM = utcNow.getUTCMinutes();
  const localMinutes = ((localH * 60 + localM) % 1440 + 1440) % 1440;

  const [openH, openM] = session.open.split(":").map(Number);
  const [closeH, closeM] = session.close.split(":").map(Number);
  const openMinutes = openH * 60 + openM;
  const closeMinutes = closeH * 60 + closeM;

  return localMinutes >= openMinutes && localMinutes < closeMinutes;
}

export function GlobalSessionStrip() {
  const now = new Date();

  return (
    <div className="flex items-center gap-1 overflow-x-auto py-0.5">
      {GLOBAL_SESSIONS.map((session) => {
        const open = isSessionOpen(session, now);
        return (
          <div
            key={session.name}
            className={`flex shrink-0 flex-col items-center rounded-lg border px-2.5 py-1.5 transition-all ${
              open
                ? "border-[#00E5A8]/40 bg-[#00E5A8]/10"
                : "border-[#1c1c24] bg-[#07070a]"
            }`}
          >
            <div
              className={`text-[10px] font-bold font-mono ${
                open ? "text-[#00E5A8]" : "text-slate-400"
              }`}
            >
              {session.name.toUpperCase()}
            </div>
            <div className="flex items-center gap-1 mt-0.5">
              <span
                className={`h-1 w-1 rounded-full ${open ? "bg-[#00E5A8] shadow-[0_0_4px_#00E5A8]" : "bg-slate-600"}`}
              />
              <span className={`text-[9px] font-mono ${open ? "text-[#00E5A8]" : "text-slate-500"}`}>
                {open ? "OPEN" : "CLOSED"}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── INSTRUMENT MONOGRAM FALLBACK ─────────────────────────────────────────────

interface MonogramProps {
  symbol: string;
  size?: number;
  className?: string;
}

export function InstrumentMonogram({ symbol, size = 32, className = "" }: MonogramProps) {
  const sym = symbol.toUpperCase();

  // Derive 2-3 char monogram
  const MONOGRAMS: Record<string, string> = {
    "GIFT_NIFTY": "GN",
    "S&P 500": "SPX",
    "NASDAQ": "NQ",
    "DOW_JONES": "DJI",
    "NIKKEI_225": "N225",
    "HANG_SENG": "HSI",
    "INDIA_VIX": "VIX",
    "USD_INR": "₹",
    "DXY": "DXY",
    "BRENT_CRUDE": "BRN",
    "GOLD": "XAU",
    "US_10Y": "10Y",
    "IN_10Y": "IN10",
  };

  const COLORS: Record<string, { bg: string; text: string; border: string }> = {
    "GN": { bg: "#00E5A8", text: "#000", border: "#00E5A8" },
    "SPX": { bg: "#C084FC", text: "#000", border: "#C084FC" },
    "NQ": { bg: "#39D9FF", text: "#000", border: "#39D9FF" },
    "DJI": { bg: "#60A5FA", text: "#000", border: "#60A5FA" },
    "N225": { bg: "#FF5C77", text: "#fff", border: "#FF5C77" },
    "HSI": { bg: "#F97316", text: "#fff", border: "#F97316" },
    "VIX": { bg: "#FFB84D", text: "#000", border: "#FFB84D" },
    "₹": { bg: "#00E5A8", text: "#000", border: "#00E5A8" },
    "DXY": { bg: "#60A5FA", text: "#fff", border: "#60A5FA" },
    "BRN": { bg: "#9CA3AF", text: "#000", border: "#9CA3AF" },
    "XAU": { bg: "#FFB84D", text: "#000", border: "#FFB84D" },
    "10Y": { bg: "#39D9FF", text: "#000", border: "#39D9FF" },
    "IN10": { bg: "#F59E0B", text: "#000", border: "#F59E0B" },
  };

  const mono = MONOGRAMS[sym] || sym.slice(0, 2);
  const colors = COLORS[mono] || { bg: "#39D9FF", text: "#000", border: "#39D9FF" };

  const fontSize = size <= 24 ? 8 : size <= 32 ? 10 : 12;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={className}
    >
      <rect
        width={size}
        height={size}
        rx={size * 0.25}
        fill={`${colors.bg}20`}
        stroke={`${colors.border}60`}
        strokeWidth="1"
      />
      <text
        x={size / 2}
        y={size / 2 + fontSize * 0.35}
        textAnchor="middle"
        fontSize={fontSize}
        fontWeight="bold"
        fill={colors.bg}
        fontFamily="monospace"
      >
        {mono}
      </text>
    </svg>
  );
}

// ─── SECTOR PERFORMANCE HORIZONTAL BARS ──────────────────────────────────────

interface SectorBarProps {
  name: string;
  changePct: number | null;
  maxAbs?: number;
}

export function SectorPerformanceBar({ name, changePct, maxAbs = 2 }: SectorBarProps) {
  if (changePct == null) {
    return (
      <div className="flex items-center gap-2 h-7 text-[10px] font-mono">
        <span className="w-28 truncate text-slate-400">{name}</span>
        <span className="text-slate-600">—</span>
      </div>
    );
  }

  const v = Number(changePct);
  const positive = v >= 0;
  const pct = Math.min(100, (Math.abs(v) / Math.max(maxAbs, Math.abs(v), 0.01)) * 100);

  return (
    <div className="flex items-center gap-2 h-7">
      <span className="w-28 truncate text-[10px] font-mono text-slate-300">{name}</span>
      <span
        className={`w-14 text-right text-[10px] font-bold font-mono ${
          positive ? "text-[#00E5A8]" : "text-[#FF5C77]"
        }`}
      >
        {positive ? "+" : ""}{v.toFixed(2)}%
      </span>
      <div className="flex-1 relative h-2 rounded-full bg-[#111118] overflow-hidden">
        <div
          className={`absolute inset-y-0 h-full rounded-full ${
            positive ? "bg-[#00E5A8]" : "bg-[#FF5C77]"
          }`}
          style={{ width: `${pct}%`, opacity: 0.8 }}
        />
      </div>
    </div>
  );
}

// ─── COMPACT OBSERVATION STATE (replaces HISTORICAL CHART UNAVAILABLE) ────────

interface ObservationStateProps {
  instrumentName: string;
  value: number | null;
  unit?: string;
  previousSession?: string | null;
  observedAt?: string | null;
  freshnessStatus?: string | null;
  sourceName?: string | null;
}

export function CompactObservationState({
  instrumentName,
  value,
  unit,
  previousSession,
  observedAt,
  freshnessStatus,
  sourceName,
}: ObservationStateProps) {
  const fmt = (v: number) =>
    v >= 1000 ? v.toLocaleString("en-IN", { maximumFractionDigits: 2 }) : v.toFixed(2);

  return (
    <div className="rounded-xl border border-[#1c1c24] bg-[#050508] p-4">
      {/* Divider header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="h-px flex-1 bg-[#1c1c24]" />
        <span className="text-[9px] font-bold font-mono tracking-widest text-slate-500">
          CURRENT OBSERVATION
        </span>
        <div className="h-px flex-1 bg-[#1c1c24]" />
      </div>

      {/* Value display */}
      <div className="text-center mb-4">
        <div className="text-2xl font-bold text-slate-100 air-data">
          {value != null ? `${fmt(value)}${unit ? ` ${unit}` : ""}` : "Unavailable"}
        </div>
        {previousSession && (
          <div className="mt-1 text-[10px] text-slate-400 font-mono">
            Previous session: {previousSession}
          </div>
        )}
      </div>

      {/* Meta grid */}
      <div className="grid grid-cols-3 gap-2 border-t border-[#1a1a22] pt-3">
        {[
          ["Freshness", freshnessStatus],
          ["Observed", observedAt],
          ["Source", sourceName],
        ].map(([label, val]) => (
          <div key={label} className="text-center">
            <div className="text-[9px] font-bold uppercase tracking-wider text-slate-500">
              {label}
            </div>
            <div className="mt-0.5 text-[10px] font-semibold text-slate-300 truncate">
              {val || "—"}
            </div>
          </div>
        ))}
      </div>

      {/* Historical note */}
      <div className="mt-3 border-t border-[#1a1a22] pt-3">
        <p className="text-[10px] text-slate-500 font-mono text-center">
          Historical series · Not available for this observation.
        </p>
      </div>

      <div className="flex items-center gap-2 mt-3">
        <div className="h-px flex-1 bg-[#1c1c24]" />
      </div>
    </div>
  );
}

// ─── COMBINED MARKET MOVERS PANEL ─────────────────────────────────────────────

export function MarketMoversPanel({ gainers, losers }: { gainers: any[]; losers: any[] }) {
  const gList = safeArray(gainers).slice(0, 5);
  const lList = safeArray(losers).slice(0, 5);
  const maxAbsG = Math.max(1, ...gList.map((i: any) => Math.abs(Number(i.change_pct ?? i.change_percent ?? 0))));
  const maxAbsL = Math.max(1, ...lList.map((i: any) => Math.abs(Number(i.change_pct ?? i.change_percent ?? 0))));

  return (
    <Surface className="overflow-hidden h-auto">
      <SectionHeader
        title="Market Movers"
        eyebrow="Top Gainers & Losers"
        accent="emerald"
      />
      <div className="bg-[#0B0D10] grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-[#191D23]">
        {/* Gainers side */}
        <div className="p-2 space-y-1">
          <div className="text-[9px] font-bold uppercase tracking-wider text-[#00C896] px-1 pb-1 flex items-center justify-between border-b border-[#191D23]">
            <span className="flex items-center gap-1">
              <ArrowUpRight size={12} />
              <span>Gainers</span>
            </span>
            <span className="text-[#707987]">Change %</span>
          </div>
          {gList.length ? (
            gList.map((item: any, idx: number) => {
              const sym = String(item.symbol || item.name || "N/A");
              const last = item.last_price ?? item.last ?? item.close;
              const chgPct = item.change_pct ?? item.change_percent;
              const pctVal = chgPct != null ? Math.abs(Number(chgPct)) : 0;
              const barWidth = Math.min(100, (pctVal / maxAbsG) * 100);

              return (
                <div key={sym + idx} className="p-1 hover:bg-[#13161A] text-[11px] font-mono transition-colors rounded-[2px] space-y-0.5">
                  <div className="flex items-center justify-between gap-1.5">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <InstrumentVisual symbol={sym} size={15} className="rounded-full shrink-0" />
                      <span className="font-bold text-[#E6E8EB] truncate">{sym}</span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[#707987] text-[10px]">{last != null ? formatNumber(Number(last), 1) : "—"}</span>
                      <span className="font-bold text-[#00C896] w-14 text-right">
                        {chgPct != null ? `+${formatNumber(Number(chgPct), 2)}%` : "—"}
                      </span>
                    </div>
                  </div>
                  <div className="h-1 w-full bg-[#111118] rounded-full overflow-hidden">
                    <div className="h-full bg-[#00C896] rounded-full" style={{ width: `${barWidth}%` }} />
                  </div>
                </div>
              );
            })
          ) : (
            <div className="py-3 text-center text-[#707987] font-mono text-[10px]">No gainer data</div>
          )}
        </div>

        {/* Losers side */}
        <div className="p-2 space-y-1">
          <div className="text-[9px] font-bold uppercase tracking-wider text-[#E5484D] px-1 pb-1 flex items-center justify-between border-b border-[#191D23]">
            <span className="flex items-center gap-1">
              <ArrowDownRight size={12} />
              <span>Losers</span>
            </span>
            <span className="text-[#707987]">Change %</span>
          </div>
          {lList.length ? (
            lList.map((item: any, idx: number) => {
              const sym = String(item.symbol || item.name || "N/A");
              const last = item.last_price ?? item.last ?? item.close;
              const chgPct = item.change_pct ?? item.change_percent;
              const pctVal = chgPct != null ? Math.abs(Number(chgPct)) : 0;
              const barWidth = Math.min(100, (pctVal / maxAbsL) * 100);

              return (
                <div key={sym + idx} className="p-1 hover:bg-[#13161A] text-[11px] font-mono transition-colors rounded-[2px] space-y-0.5">
                  <div className="flex items-center justify-between gap-1.5">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <InstrumentVisual symbol={sym} size={15} className="rounded-full shrink-0" />
                      <span className="font-bold text-[#E6E8EB] truncate">{sym}</span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[#707987] text-[10px]">{last != null ? formatNumber(Number(last), 1) : "—"}</span>
                      <span className="font-bold text-[#E5484D] w-14 text-right">
                        {chgPct != null ? `${formatNumber(Number(chgPct), 2)}%` : "—"}
                      </span>
                    </div>
                  </div>
                  <div className="h-1 w-full bg-[#111118] rounded-full overflow-hidden">
                    <div className="h-full bg-[#E5484D] rounded-full" style={{ width: `${barWidth}%` }} />
                  </div>
                </div>
              );
            })
          ) : (
            <div className="py-3 text-center text-[#707987] font-mono text-[10px]">No loser data</div>
          )}
        </div>
      </div>
    </Surface>
  );
}

// ─── CONSTITUENT PERFORMANCE / MARKET LEADERSHIP VISUAL ─────────────────────

export function ConstituentPerformanceVisual({
  heavyweights,
  gainers,
  losers,
}: {
  heavyweights?: any[];
  gainers?: any[];
  losers?: any[];
}) {
  const hwList = safeArray(heavyweights);
  const isWeighted = hwList.length > 0 && hwList.some((h: any) => h.pts != null || h.weight != null);

  if (isWeighted) {
    const sorted = [...hwList]
      .sort((a: any, b: any) => Math.abs(b.pts ?? b.change ?? 0) - Math.abs(a.pts ?? a.change ?? 0))
      .slice(0, 5);
    const maxPts = Math.max(1, ...sorted.map((s: any) => Math.abs(Number(s.pts ?? s.change ?? 0))));

    return (
      <Surface className="overflow-hidden h-auto">
        <SectionHeader title="Index Contribution" eyebrow="Market Leadership" accent="amber" />
        <div className="bg-[#0B0D10] p-2 space-y-1.5">
          {sorted.map((item: any, idx: number) => {
            const sym = String(item.symbol || "SYM");
            const pts = Number(item.pts ?? item.change ?? 0);
            const pos = pts >= 0;
            const barWidthPct = Math.min(100, (Math.abs(pts) / maxPts) * 100);

            return (
              <div key={sym + idx} className="flex items-center gap-2 text-[11px] font-mono hover:bg-[#13161A] p-1 rounded transition-colors">
                <InstrumentVisual symbol={sym} size={15} className="rounded-full shrink-0" />
                <span className="w-20 font-bold text-[#E6E8EB] truncate">{sym}</span>
                <div className="flex-1 flex items-center min-w-[60px]">
                  <div className="relative h-2 w-full bg-[#111118] rounded-full overflow-hidden flex items-center">
                    <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-[#242830] z-10" />
                    {pos ? (
                      <div
                        className="absolute left-1/2 top-0 bottom-0 bg-[#00C896] rounded-r-full transition-all duration-300"
                        style={{ width: `${barWidthPct / 2}%` }}
                      />
                    ) : (
                      <div
                        className="absolute right-1/2 top-0 bottom-0 bg-[#E5484D] rounded-l-full transition-all duration-300"
                        style={{ width: `${barWidthPct / 2}%` }}
                      />
                    )}
                  </div>
                </div>
                <span className={`w-16 text-right font-bold ${pos ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                  {pos ? "+" : ""}{formatNumber(pts, 1)} pts
                </span>
              </div>
            );
          })}
        </div>
      </Surface>
    );
  }

  // Fallback: Constituent Performance using top gainers & losers
  const topG = safeArray(gainers).slice(0, 3);
  const topL = safeArray(losers).slice(0, 3);
  const combined = [...topG, ...topL];

  return (
    <Surface className="overflow-hidden h-auto">
      <SectionHeader title="Constituent Performance" eyebrow="Market Leadership" accent="amber" />
      <div className="bg-[#0B0D10] p-2 space-y-1">
        {combined.length ? (
          combined.map((item: any, idx: number) => {
            const sym = String(item.symbol || item.name || "SYM");
            const chgPct = item.change_pct ?? item.change_percent;
            const pos = Number(chgPct ?? 0) >= 0;

            return (
              <div
                key={sym + idx}
                className="flex items-center justify-between gap-2 text-[11px] font-mono hover:bg-[#13161A] p-1.5 rounded transition-colors border-b border-[#191D23] last:border-0"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <InstrumentVisual symbol={sym} size={15} className="rounded-full shrink-0" />
                  <span className="font-bold text-[#E6E8EB] truncate">{sym}</span>
                </div>
                <span className={`font-bold ${pos ? "text-[#00C896]" : "text-[#E5484D]"}`}>
                  {chgPct != null ? `${pos ? "+" : ""}${formatNumber(Number(chgPct), 2)}%` : "—"}
                </span>
              </div>
            );
          })
        ) : (
          <div className="py-3 text-center text-[10px] text-[#707987] font-mono">
            Constituent performance data unavailable
          </div>
        )}
      </div>
    </Surface>
  );
}

// ─── CONFIDENCE GAUGE ────────────────────────────────────────────────────────
export function ConfidenceGauge({ value }: { value: number | string | null }) {
  const valNum = typeof value === "number" ? value : parseFloat(String(value ?? "")) || 65;
  const pct = Math.min(100, Math.max(0, valNum));
  const color = pct >= 70 ? "#00C896" : pct >= 45 ? "#39D9FF" : "#FF5C77";
  const circumference = Math.PI * 26; // radius = 13
  const dashLen = (pct / 100) * circumference;

  return (
    <div className="flex items-center gap-1.5">
      <div className="relative w-9 h-9 flex items-center justify-center">
        <svg width="36" height="36" viewBox="0 0 36 36" className="transform -rotate-90">
          <circle cx="18" cy="18" r="13" fill="none" stroke="#191D23" strokeWidth="3.5" />
          <circle
            cx="18"
            cy="18"
            r="13"
            fill="none"
            stroke={color}
            strokeWidth="3.5"
            strokeDasharray={`${dashLen} ${circumference}`}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <span className="absolute text-[9px] font-bold font-mono text-[#E6E8EB]">{Math.round(pct)}%</span>
      </div>
    </div>
  );
}

// ─── INSTITUTIONAL POSITIONING SPECTRUM BAR ─────────────────────────────────
export function PositioningSpectrumBar({ netValue }: { netValue: number | null }) {
  const net = Number(netValue) || 0;
  const clamped = Math.min(2000, Math.max(-2000, net));
  const pct = ((clamped + 2000) / 4000) * 100;
  const tone = net > 100 ? "BULLISH" : net < -100 ? "BEARISH" : "NEUTRAL";
  const toneColor = net > 100 ? "#00C896" : net < -100 ? "#E5484D" : "#E59700";

  return (
    <div className="space-y-1 pt-1">
      <div className="relative h-2 w-full rounded-full bg-gradient-to-r from-[#E5484D] via-[#E59700] to-[#00C896] overflow-visible">
        <div
          className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 h-3.5 w-3.5 rounded-full border-2 border-[#0B0D10] bg-[#E6E8EB] shadow-[0_0_6px_rgba(255,255,255,0.8)] transition-all duration-500"
          style={{ left: `${pct}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-[8px] font-mono font-bold tracking-wider text-[#707987] uppercase">
        <span>BEARISH</span>
        <span style={{ color: toneColor }}>{tone}</span>
        <span>BULLISH</span>
      </div>
    </div>
  );
}


