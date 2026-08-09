// src/frontend/components/AIInterpretationCard.tsx
import React, { useEffect, useState } from "react";
import { Sparkles, Info, AlertCircle } from "lucide-react";
import { OpenAIInterpretationBadge } from "./OpenAIInterpretationBadge";

interface Props {
  title: string;
  sectionKey: "market_narrative" | "why_today" | "pre_market_narrative" | "todays_analysis_narrative" | "end_of_day_summary";
}

export function AIInterpretationCard({ title, sectionKey }: Props) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch("/api/interpretation/generate", { method: "POST" })
      .then((res) => res.json())
      .then((resData) => {
        setData(resData);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [sectionKey]);

  const textContent = data ? data[sectionKey] : "Canonical state interpretation pending...";
  const isFallback = data?.fallback_active ?? true;

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 text-left font-sans">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Sparkles size={15} className="text-cyan-400" />
          <h4 className="font-bold text-white text-xs uppercase tracking-wider font-mono">{title}</h4>
        </div>
        <OpenAIInterpretationBadge />
      </div>

      {loading ? (
        <div className="h-12 bg-slate-950 rounded animate-pulse"></div>
      ) : (
        <div className="space-y-2">
          <p className="text-xs text-slate-300 font-sans leading-relaxed">{textContent}</p>

          {isFallback && (
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-amber-400/90 pt-1">
              <Info size={12} />
              <span>Bounded Fallback: Explanation derived from canonical deterministic context.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
