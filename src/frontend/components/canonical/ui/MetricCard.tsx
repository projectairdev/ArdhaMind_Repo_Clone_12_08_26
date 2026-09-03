/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Reusable MetricCard for Presentation Layer.
 * Renders metrics with clean typography, change indicators, quality labels, and optional provenance popovers.
 */

import React, { ReactNode } from "react";
import { ProvenancePopover, ProvenanceDetails } from "./ProvenancePopover";
import { QualityBadge } from "./Badges";
import { DataQualityStatus } from "../../../types/canonical";

interface MetricCardProps {
  label: string;
  value: string | number | null | undefined;
  unit?: string;
  delta?: {
    points: number | null;
    percent: number | null;
    direction?: "up" | "down" | "neutral";
  };
  sublabel?: string;
  quality?: DataQualityStatus;
  provenance?: ProvenanceDetails;
  highlight?: "none" | "green" | "red" | "blue" | "amber";
  className?: string;
  badge?: ReactNode;
}

export function MetricCard({
  label,
  value,
  unit,
  delta,
  sublabel,
  quality,
  provenance,
  highlight = "none",
  className = "",
  badge,
}: MetricCardProps) {
  const isAvailable = value !== null && value !== undefined && value !== "";

  const highlightBorder =
    highlight === "green"
      ? "border-[#00C896]/30 bg-[#00C896]/5"
      : highlight === "red"
      ? "border-[#EF4444]/30 bg-[#EF4444]/5"
      : highlight === "blue"
      ? "border-[#38BDF8]/30 bg-[#38BDF8]/5"
      : highlight === "amber"
      ? "border-[#F59E0B]/30 bg-[#F59E0B]/5"
      : "border-[#1E232B] bg-[#0E1013]";

  return (
    <div
      className={`rounded-md border p-3 font-mono transition-all hover:border-[#2C3440] ${highlightBorder} ${className}`}
    >
      <div className="flex items-center justify-between gap-1 mb-1">
        <span className="text-[11px] font-semibold text-[#8B949E] tracking-tight uppercase">
          {label}
        </span>
        <div className="flex items-center gap-1">
          {badge}
          {quality && quality !== "VALID" && <QualityBadge quality={quality} />}
          {provenance && <ProvenancePopover details={provenance} />}
        </div>
      </div>

      <div className="flex items-baseline gap-1.5">
        {isAvailable ? (
          <>
            <span className="text-lg lg:text-xl font-bold tracking-tight text-[#E6E8EB]">
              {typeof value === "number" ? value.toLocaleString("en-IN") : value}
            </span>
            {unit && <span className="text-xs text-[#707987] font-normal">{unit}</span>}
          </>
        ) : (
          <span className="text-lg font-semibold text-[#505763]">—</span>
        )}
      </div>

      {(delta || sublabel) && (
        <div className="mt-1 flex items-center justify-between text-[10px]">
          {delta && delta.points !== null && (
            <span
              className={`font-semibold ${
                delta.points > 0
                  ? "text-[#00C896]"
                  : delta.points < 0
                  ? "text-[#EF4444]"
                  : "text-[#8B949E]"
              }`}
            >
              {delta.points > 0 ? "+" : ""}
              {delta.points.toFixed(2)} {delta.percent !== null && `(${delta.percent > 0 ? "+" : ""}${delta.percent.toFixed(2)}%)`}
            </span>
          )}
          {sublabel && <span className="text-[#707987] truncate">{sublabel}</span>}
        </div>
      )}
    </div>
  );
}
