// src/frontend/components/visualizations/HistoricalTelemetryCharts.tsx
import React from "react";
import { Clock } from "lucide-react";

export function HistoricalTelemetryCharts() {
  return (
    <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 text-left font-mono text-xs">
      <div className="flex items-center gap-2 text-amber-400 font-bold"><Clock size={16}/><span>Historical Telemetry & Sentiment Trends</span></div>
      <p className="text-slate-400">Historical telemetry unavailable — no verified canonical time-series observations.</p>
    </div>
  );
}
