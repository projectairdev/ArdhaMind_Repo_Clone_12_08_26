import React from "react";
import { formatNumber } from "../../utils/safeHelpers";
import type { LucideIcon } from "lucide-react";

export const CARD_BORDER_RADIUS_LEGACY = "rounded-xl";
export const CARD_SHADOW_LEGACY = "shadow-[0_8px_24px_rgba(0,0,0,0.4)]";

export function Surface({
  children,
  className = "",
  as: Tag = "section",
  glow = "none",
  id,
}: {
  children: React.ReactNode;
  className?: string;
  as?: "section" | "div" | "article" | "aside";
  glow?: "none" | "emerald" | "rose" | "amber" | "violet" | "cyan" | "blue";
  key?: React.Key;
  id?: string;
}) {
  const borderStyle =
    glow === "emerald"
      ? "border-[#00C896]/30 border-l-2 border-l-[#00C896]"
      : glow === "rose"
      ? "border-[#E5484D]/30 border-l-2 border-l-[#E5484D]"
      : glow === "amber"
      ? "border-[#E59700]/30 border-l-2 border-l-[#E59700]"
      : glow === "violet"
      ? "border-[#8B5CF6]/30 border-l-2 border-l-[#8B5CF6]"
      : glow === "cyan"
      ? "border-[#38BDF8]/30 border-l-2 border-l-[#38BDF8]"
      : "border-[#242830]";

  return (
    <Tag id={id} className={`rounded-[3px] border bg-[#0B0D10] text-[#E6E8EB] ${borderStyle} ${className}`}>
      {children}
    </Tag>
  );
}

export function SectionHeader({
  title,
  detail,
  action,
  icon: Icon,
  assetIcon: AssetIcon,
  eyebrow,
  accent = "cyan",
}: {
  title: string;
  detail?: string;
  action?: React.ReactNode;
  icon?: LucideIcon;
  assetIcon?: React.ReactNode;
  eyebrow?: string;
  accent?: "emerald" | "cyan" | "amber" | "rose" | "violet" | "blue";
}) {
  const eyebrowColor =
    accent === "emerald"
      ? "text-[#00C896]"
      : accent === "amber"
      ? "text-[#E59700]"
      : accent === "rose"
      ? "text-[#E5484D]"
      : accent === "violet"
      ? "text-[#8B5CF6]"
      : "text-[#38BDF8]";

  return (
    <div className="flex min-h-9 items-center justify-between gap-3 border-b border-[#191D23] bg-[#0E1013] px-3 py-2">
      <div className="flex items-center gap-2 min-w-0">
        {AssetIcon ? (
          <div className="flex h-5 w-5 shrink-0 items-center justify-center">{AssetIcon}</div>
        ) : Icon ? (
          <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-[#242830] bg-[#08090B] text-[#A5ABB4]">
            <Icon size={12} />
          </div>
        ) : null}
        <div className="min-w-0">
          {eyebrow && (
            <span className={`block text-[8px] font-bold uppercase tracking-wider ${eyebrowColor}`}>
              {eyebrow}
            </span>
          )}
          <h2 className="truncate text-[12px] font-semibold text-[#E6E8EB] tracking-tight">{title}</h2>
          {detail && <p className="truncate text-[10px] text-[#707987]">{detail}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

export function MarketValue({
  value,
  decimals = 2,
  suffix = "",
  className = "",
}: {
  value: unknown;
  decimals?: number;
  suffix?: string;
  className?: string;
}) {
  const parsed = value == null || value === "" ? null : Number(value);
  return (
    <span className={`air-data ${className}`}>
      {parsed != null && Number.isFinite(parsed) ? `${formatNumber(parsed, decimals)}${suffix}` : "Unavailable"}
    </span>
  );
}

export function MetricCell({
  label,
  value,
  children,
  tone = "neutral",
}: {
  label: string;
  value?: unknown;
  children?: React.ReactNode;
  tone?: "positive" | "negative" | "warning" | "caution" | "neutral" | "violet" | "cyan";
  key?: React.Key;
}) {
  const toneClass =
    tone === "positive"
      ? "text-[#00C896]"
      : tone === "negative"
      ? "text-[#E5484D]"
      : tone === "warning" || tone === "caution"
      ? "text-[#E59700]"
      : tone === "violet"
      ? "text-[#8B5CF6]"
      : tone === "cyan"
      ? "text-[#38BDF8]"
      : "text-[#E6E8EB]";

  return (
    <div className="min-w-0 px-3 py-2 border-r border-[#191D23] last:border-r-0">
      <div className="truncate text-[9px] font-semibold uppercase text-[#707987] tracking-wider">{label}</div>
      <div className={`mt-0.5 truncate text-[12px] font-medium air-data ${toneClass}`}>
        {children ?? (value == null || value === "" ? "Unavailable" : String(value))}
      </div>
    </div>
  );
}

export function MetricCard({
  label,
  value,
  icon: Icon,
  assetIcon: AssetIcon,
  tone = "neutral",
  detail,
  eyebrow,
  sparkline,
}: {
  label: string;
  value: React.ReactNode;
  icon?: LucideIcon;
  assetIcon?: React.ReactNode;
  tone?: "positive" | "negative" | "warning" | "caution" | "neutral" | "violet" | "cyan";
  detail?: string;
  eyebrow?: string;
  sparkline?: React.ReactNode;
}) {
  const color =
    tone === "positive"
      ? "text-[#00C896]"
      : tone === "negative"
      ? "text-[#E5484D]"
      : tone === "warning" || tone === "caution"
      ? "text-[#E59700]"
      : tone === "violet"
      ? "text-[#8B5CF6]"
      : tone === "cyan"
      ? "text-[#38BDF8]"
      : "text-[#E6E8EB]";

  return (
    <div className="group rounded-[3px] border border-[#242830] bg-[#0B0D10] px-3 py-2 transition-colors hover:bg-[#13161A]">
      <div className="flex items-center justify-between gap-1.5 text-[10px] text-[#A5ABB4]">
        <div className="flex items-center gap-1.5 min-w-0">
          {AssetIcon ? (
            <div className="flex h-5 w-5 shrink-0 items-center justify-center">{AssetIcon}</div>
          ) : Icon ? (
            <Icon size={12} className="text-[#707987] shrink-0" />
          ) : null}
          <div className="min-w-0 truncate">
            {eyebrow && <span className="block text-[8px] font-bold uppercase text-[#707987]">{eyebrow}</span>}
            <span className="truncate uppercase text-[10px] font-medium text-[#A5ABB4]">{label}</span>
          </div>
        </div>
      </div>
      <div className={`air-data mt-1 truncate text-[13px] font-semibold tracking-tight ${color}`}>
        {value ?? "Unavailable"}
      </div>
      {sparkline && <div className="mt-1">{sparkline}</div>}
      {detail && <div className="mt-0.5 truncate text-[9px] text-[#707987]">{detail}</div>}
    </div>
  );
}

export function StatCard({
  title,
  value,
  change,
  changePct,
  icon: Icon,
  assetIcon: AssetIcon,
  tone = "neutral",
  subtitle,
}: {
  title: string;
  value: React.ReactNode;
  change?: number | null;
  changePct?: number | null;
  icon?: LucideIcon;
  assetIcon?: React.ReactNode;
  tone?: "positive" | "negative" | "warning" | "neutral" | "cyan" | "violet";
  subtitle?: string;
}) {
  const toneColor =
    tone === "positive" || (change != null && change > 0)
      ? "text-[#00C896]"
      : tone === "negative" || (change != null && change < 0)
      ? "text-[#E5484D]"
      : tone === "warning"
      ? "text-[#E59700]"
      : tone === "violet"
      ? "text-[#8B5CF6]"
      : tone === "cyan"
      ? "text-[#38BDF8]"
      : "text-[#E6E8EB]";

  return (
    <div className="rounded-[3px] border border-[#242830] bg-[#0B0D10] p-2.5">
      <div className="flex items-center justify-between gap-2 text-[10px] text-[#A5ABB4]">
        <span className="font-semibold uppercase tracking-wider text-[9px] text-[#707987]">{title}</span>
        {AssetIcon ? AssetIcon : Icon ? <Icon size={12} className={toneColor} /> : null}
      </div>
      <div className={`air-data mt-0.5 text-[14px] font-semibold ${toneColor}`}>{value}</div>
      {(change != null || changePct != null || subtitle) && (
        <div className="mt-1 flex items-center justify-between text-[10px] text-[#707987]">
          <span>{subtitle}</span>
          {changePct != null && (
            <span className={`air-data font-medium ${toneColor}`}>
              {changePct > 0 ? "+" : ""}
              {formatNumber(changePct, 2)}%
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export function InsightCard({
  title,
  description,
  badge,
  icon: Icon,
  assetIcon: AssetIcon,
  tone = "neutral",
}: {
  title: string;
  description: string;
  badge?: string;
  icon?: LucideIcon;
  assetIcon?: React.ReactNode;
  tone?: "emerald" | "rose" | "amber" | "violet" | "cyan" | "neutral";
}) {
  return (
    <div className="rounded-[3px] border border-[#242830] bg-[#0B0D10] p-2.5">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          {AssetIcon ? AssetIcon : Icon ? <Icon size={13} className="text-[#A5ABB4]" /> : null}
          <h4 className="text-[11px] font-semibold text-[#E6E8EB]">{title}</h4>
        </div>
        {badge && (
          <span className="rounded-[2px] px-1.5 py-0.5 text-[8px] font-bold uppercase border border-[#242830] bg-[#08090B] text-[#A5ABB4]">
            {badge}
          </span>
        )}
      </div>
      <p className="mt-1 text-[11px] leading-snug text-[#A5ABB4]">{description}</p>
    </div>
  );
}

export function CompactRows({ rows }: { rows: Array<[string, React.ReactNode]> }) {
  return (
    <div className="divide-y divide-[#191D23]">
      {rows.map(([label, value], i) => (
        <div
          key={String(label) + i}
          className="flex min-h-8 items-center justify-between gap-2 px-3 py-1.5 text-[11px] hover:bg-[#13161A] transition-colors"
        >
          <span className="text-[#707987] font-medium truncate max-w-[50%]">{label}</span>
          <span className="air-data max-w-[50%] truncate text-right font-medium text-[#E6E8EB]">
            {value ?? "Unavailable"}
          </span>
        </div>
      ))}
    </div>
  );
}
