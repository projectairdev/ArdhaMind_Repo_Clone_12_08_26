// src/frontend/components/ui/TemporalContextStrip.tsx
import React from "react";
import { Clock, Calendar, ShieldCheck, AlertCircle } from "lucide-react";
import { getTemporalSessionContext } from "../../utils/temporalSessionResolver";

export function TemporalContextStrip({
  canonicalState,
  previewMode = "LIVE",
  customTitle,
}: {
  canonicalState: any;
  previewMode?: "PRE" | "LIVE" | "POST";
  customTitle?: string;
}) {
  const ctx = getTemporalSessionContext(canonicalState, previewMode);

  return (
    <div
      id="temporal-context-strip"
      className="bg-[#0B0D10] border border-[#191D23] rounded-[3px] p-2 sm:p-2.5 font-mono text-[10px] space-y-1.5"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        {/* Market Status & Preview Indicator */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-[#0E1013] border border-[#191D23] px-2 py-0.5 rounded">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                ctx.isLiveSession ? "bg-[#00C896] animate-pulse" : "bg-[#38BDF8]"
              }`}
            />
            <span className={`font-bold uppercase tracking-wider ${ctx.statusColor}`}>
              MARKET: {ctx.displayStatus}
            </span>
          </div>

          {ctx.previewNotice && (
            <span className="bg-[#E59700]/15 border border-[#E59700]/30 text-[#E59700] px-2 py-0.5 rounded font-bold uppercase text-[9px] flex items-center gap-1">
              <AlertCircle size={10} />
              {ctx.previewNotice}
            </span>
          )}

          {customTitle && (
            <span className="text-[#A5ABB4] font-semibold text-[9.5px]">
              {customTitle}
            </span>
          )}
        </div>

        {/* Temporal Dates Cluster */}
        <div className="flex flex-wrap items-center gap-3 text-[9.5px] text-[#707987]">
          <div className="flex items-center gap-1">
            <Calendar size={11} className="text-[#38BDF8]" />
            <span>Last Valid Session:</span>
            <span className="font-bold text-[#E6E8EB]">{ctx.lastValidSessionDate}</span>
          </div>

          <div className="flex items-center gap-1">
            <Calendar size={11} className="text-[#00C896]" />
            <span>Next Session:</span>
            <span className="font-bold text-[#00C896]">{ctx.nextSessionDate}</span>
          </div>

          <div className="flex items-center gap-1 border-l border-[#191D23] pl-2.5">
            <ShieldCheck size={11} className="text-[#8B5CF6]" />
            <span>Validated:</span>
            <span className="text-[#A5ABB4]">{ctx.canonicalValidatedAt}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TemporalContextStrip;
