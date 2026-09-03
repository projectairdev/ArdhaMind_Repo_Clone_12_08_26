/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * EmptyDataState & DataFreshnessIndicator components.
 * Explicitly guards against fake fallback numbers like ₹0 or 0 PCR when data is unavailable.
 */

import React from "react";
import { AlertCircle, Clock, Radio, RefreshCw } from "lucide-react";
import { FeedHealthMetric } from "../../../types/canonical";

export function EmptyDataState({
  title = "Data Unavailable",
  description = "Awaiting live feed or market session initialization.",
  icon,
}: {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center font-mono border border-dashed border-[#242830] rounded-lg bg-[#0B0D10]/50 my-4">
      {icon || <AlertCircle className="w-8 h-8 text-[#707987] mb-2.5" />}
      <h4 className="text-sm font-bold text-[#A5ABB4] mb-1">{title}</h4>
      <p className="text-xs text-[#707987] max-w-sm">{description}</p>
    </div>
  );
}

export function DataFreshnessIndicator({
  metric,
  sourceProvider = "DHAN_HQ",
}: {
  metric?: FeedHealthMetric;
  sourceProvider?: string;
}) {
  if (!metric) {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161A22] border border-[#242830] text-[11px] font-mono text-[#707987]">
        <Radio className="w-3 h-3 text-[#707987]" />
        <span>STANDBY</span>
      </div>
    );
  }

  const ageSeconds = (metric.tick_age_ms / 1000).toFixed(1);

  if (metric.status === "HEALTHY") {
    return (
      <div
        title={`Feed healthy (${metric.ticks_per_second.toFixed(1)} ticks/sec | Latency: ${metric.provider_latency_ms || 0}ms)`}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#00C896]/10 border border-[#00C896]/30 text-[11px] font-mono font-bold text-[#00C896]"
      >
        <span className="w-2 h-2 rounded-full bg-[#00C896] animate-pulse" />
        <span>LIVE · {ageSeconds}s</span>
      </div>
    );
  }

  if (metric.status === "DELAYED") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#F59E0B]/10 border border-[#F59E0B]/30 text-[11px] font-mono font-bold text-[#F59E0B]">
        <Clock className="w-3 h-3" />
        <span>DELAYED · {ageSeconds}s</span>
      </div>
    );
  }

  if (metric.status === "STALE") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#EF4444]/15 border border-[#EF4444]/40 text-[11px] font-mono font-bold text-[#EF4444]">
        <AlertCircle className="w-3 h-3 animate-bounce" />
        <span>STALE · {ageSeconds}s</span>
      </div>
    );
  }

  if (metric.status === "RECOVERING") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#38BDF8]/15 border border-[#38BDF8]/40 text-[11px] font-mono font-bold text-[#38BDF8] animate-pulse">
        <RefreshCw className="w-3 h-3 animate-spin" />
        <span>RECOVERING</span>
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#242830] border border-[#343A46] text-[11px] font-mono text-[#707987]">
      <Radio className="w-3 h-3" />
      <span>DISCONNECTED</span>
    </div>
  );
}
