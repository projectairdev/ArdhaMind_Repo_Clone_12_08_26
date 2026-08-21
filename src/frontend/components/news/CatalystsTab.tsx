import React from "react";
import { Zap, ShieldCheck, TrendingUp, TrendingDown, Clock, Activity, AlertCircle, Building2, Info } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import { NewsPresentationState } from "../../utils/canonicalNewsAdapter";

export function CatalystsTab({ pres }: { pres: NewsPresentationState }) {
  const activeDrivers = pres.topDrivers.filter((d) => d.active);

  return (
    <div className="space-y-3 font-sans text-left text-[11px] min-w-0">
      {/* 8A. TOP MARKET DRIVERS — RESPONSIVE AUTO-FIT GRID */}
      <Surface className="overflow-hidden">
        <SectionHeader title="TOP MARKET DRIVERS" eyebrow="Evidence-Backed Active Forces" accent="violet" />
        <div className="p-3 bg-[#0B0D10] grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2.5 font-mono text-[10px]">
          {activeDrivers.length > 0 ? (
            activeDrivers.map((d) => (
              <div key={d.rank} className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="w-4 h-4 rounded-full bg-[#8B5CF6]/20 text-[#8B5CF6] flex items-center justify-center font-bold text-[9px]">
                    {d.rank}
                  </span>
                  <span className={`text-[8px] font-bold px-1 rounded ${d.impact === "HIGH" ? "bg-[#E5484D]/20 text-[#E5484D]" : "bg-[#E59700]/20 text-[#E59700]"}`}>
                    {d.impact} IMPACT
                  </span>
                </div>
                <div className="font-bold text-[#E6E8EB] text-[11px] truncate">{d.name}</div>
                <div className="flex items-center justify-between text-[9px]">
                  <span className="text-[#00C896] font-bold">STATE: {d.state}</span>
                  <span className={`font-bold ${d.direction === "POSITIVE" ? "text-[#00C896]" : d.direction === "NEGATIVE" ? "text-[#E5484D]" : "text-[#E59700]"}`}>
                    {d.direction}
                  </span>
                </div>
                <div className="text-[8px] text-[#707987] leading-tight break-words">{d.whyItMatters}</div>
              </div>
            ))
          ) : (
            <div className="py-3 col-span-full text-center text-[#707987] font-mono text-[9px] italic bg-[#0E1013] rounded border border-[#191D23] px-3">
              No active evidence-backed market drivers currently identified.
            </div>
          )}
        </div>
      </Surface>

      {/* 8B. POSITIVE CATALYSTS vs 8C. NEGATIVE CATALYSTS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-start min-w-0">
        {/* POSITIVE CATALYSTS */}
        <Surface className="overflow-hidden flex flex-col min-w-0">
          <SectionHeader title="POSITIVE CATALYSTS" eyebrow="Market Upside Drivers" accent="cyan" />
          <div className="p-2.5 bg-[#0B0D10] space-y-2 font-mono text-[10px]">
            {pres.positiveCatalysts.length > 0 ? (
              pres.positiveCatalysts.map((story) => (
                <div key={story.id} className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1 min-w-0">
                  <div className="flex items-center justify-between text-[8px]">
                    <span className="text-[#38BDF8] font-bold truncate">{story.publisher}</span>
                    <span className="text-[#00C896] font-bold shrink-0 ml-1">POSITIVE ↑</span>
                  </div>
                  <div className="font-bold text-[#E6E8EB] text-[10px] break-words">{story.headline}</div>
                  <div className="text-[8px] text-[#707987] leading-relaxed break-words">{story.whyItMatters}</div>
                </div>
              ))
            ) : (
              <div className="py-3 text-center text-[#707987] font-mono text-[9px] italic bg-[#0E1013] rounded border border-[#191D23] px-3">
                No active positive catalysts identified for this session.
              </div>
            )}
          </div>
        </Surface>

        {/* NEGATIVE CATALYSTS */}
        <Surface className="overflow-hidden flex flex-col min-w-0">
          <SectionHeader title="NEGATIVE CATALYSTS & RISKS" eyebrow="Downside Vulnerabilities" accent="amber" />
          <div className="p-2.5 bg-[#0B0D10] space-y-2 font-mono text-[10px]">
            {pres.negativeCatalysts.length > 0 ? (
              pres.negativeCatalysts.map((story) => (
                <div key={story.id} className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1 min-w-0">
                  <div className="flex items-center justify-between text-[8px]">
                    <span className="text-[#38BDF8] font-bold truncate">{story.publisher}</span>
                    <span className="text-[#E5484D] font-bold shrink-0 ml-1">NEGATIVE ↓</span>
                  </div>
                  <div className="font-bold text-[#E6E8EB] text-[10px] break-words">{story.headline}</div>
                  <div className="text-[8px] text-[#707987] leading-relaxed break-words">{story.whyItMatters}</div>
                </div>
              ))
            ) : (
              <div className="py-3 text-center text-[#707987] font-mono text-[9px] italic bg-[#0E1013] rounded border border-[#191D23] px-3">
                No active negative catalysts identified for this session.
              </div>
            )}
          </div>
        </Surface>
      </div>

      {/* 8D. REGULATORY & POLICY CATALYSTS vs 8E. CARRY-FORWARD RISKS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-start min-w-0">
        {/* REGULATORY / POLICY */}
        <Surface className="overflow-hidden flex flex-col min-w-0">
          <SectionHeader title="REGULATORY & POLICY CATALYSTS" eyebrow="Official Telemetry" accent="violet" />
          <div className="p-2.5 bg-[#0B0D10] space-y-2 font-mono text-[10px]">
            {pres.regulatoryCatalysts.length > 0 ? (
              pres.regulatoryCatalysts.map((story) => (
                <div key={story.id} className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1 min-w-0">
                  <div className="flex items-center justify-between text-[8px]">
                    <span className="text-[#8B5CF6] font-bold flex items-center gap-1 truncate">
                      <ShieldCheck size={10} className="shrink-0" />
                      <span className="truncate">{story.publisher}</span>
                    </span>
                    <span className="text-[#38BDF8] shrink-0 ml-1">{story.displayRowTime || story.publishedTimeIST}</span>
                  </div>
                  <div className="font-bold text-[#E6E8EB] text-[10px] break-words">{story.headline}</div>
                  <div className="text-[8px] text-[#707987] leading-relaxed break-words">{story.summary}</div>
                </div>
              ))
            ) : (
              <div className="py-3 text-center text-[#707987] font-mono text-[9px] italic bg-[#0E1013] rounded border border-[#191D23] px-3">
                No active regulatory or policy catalysts.
              </div>
            )}
          </div>
        </Surface>

        {/* CARRY-FORWARD RISKS */}
        <Surface className="overflow-hidden flex flex-col min-w-0">
          <SectionHeader title="CARRY-FORWARD RISKS" eyebrow="Overnight &amp; Session Exposure" accent="amber" />
          <div className="p-2.5 bg-[#0B0D10] space-y-2 font-mono text-[10px]">
            {pres.carryForwardRisks.length > 0 ? (
              pres.carryForwardRisks.map((risk, i) => (
                <div key={i} className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1 min-w-0">
                  <div className="flex items-center justify-between text-[8px]">
                    <span className="font-bold text-[#E6E8EB] truncate">{risk.title}</span>
                    <span className={`font-bold px-1 rounded shrink-0 ml-1 ${risk.riskLevel === "RED" ? "bg-[#E5484D]/20 text-[#E5484D]" : "bg-[#E59700]/20 text-[#E59700]"}`}>
                      {risk.riskLevel}
                    </span>
                  </div>
                  <div className="text-[8px] text-[#707987] leading-relaxed break-words">{risk.detail}</div>
                </div>
              ))
            ) : (
              <div className="py-3 text-center text-[#707987] font-mono text-[9px] italic bg-[#0E1013] rounded border border-[#191D23] px-3">
                No material carry-forward risks currently identified.
              </div>
            )}
          </div>
        </Surface>
      </div>
    </div>
  );
}

export default CatalystsTab;
