import React, { useState, useRef } from "react";
import {
  Clock,
  ExternalLink,
  ShieldCheck,
  Zap,
  Activity,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Info,
  Building2,
  TrendingUp,
  TrendingDown,
  Layers,
} from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import { CanonicalNewsStory, NewsPresentationState } from "../../utils/canonicalNewsAdapter";

export function LiveNewsTab({ pres }: { pres: NewsPresentationState }) {
  const [filterType, setFilterType] = useState<"ALL" | "HIGH IMPACT" | "POSITIVE" | "NEGATIVE" | "OFFICIAL">("ALL");
  const feedListRef = useRef<HTMLDivElement>(null);

  const handleFilterChange = (t: "ALL" | "HIGH IMPACT" | "POSITIVE" | "NEGATIVE" | "OFFICIAL") => {
    setFilterType(t);
    if (feedListRef.current) {
      feedListRef.current.scrollTop = 0;
    }
  };

  const filteredFeed = pres.liveFeed.filter((story) => {
    if (filterType === "HIGH IMPACT") return story.impactStrength === "HIGH";
    if (filterType === "POSITIVE") return story.expectedDirection === "POSITIVE";
    if (filterType === "NEGATIVE") return story.expectedDirection === "NEGATIVE";
    if (filterType === "OFFICIAL") return story.sourceType === "OFFICIAL";
    return true;
  });

  const topStory = pres.topStory;
  // Up to 2-3 additional recent canonical stories for center column context if present
  const secondaryStories = pres.liveFeed.filter((s) => s.id !== topStory?.id).slice(0, 2);

  return (
    <div className="space-y-2.5 font-sans text-left text-[11px] min-w-0">
      {/* ── 7A. TOP SUMMARY STRIP — RESPONSIVE GRID ── */}
      <Surface className="overflow-hidden">
        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-[#191D23] bg-[#0B0D10] p-2 items-center font-mono">
          {/* 1. MARKET NEWS TONE */}
          <div className="px-2 py-1 space-y-0.5">
            <div className="text-[8px] font-bold uppercase text-[#707987] tracking-wider">MARKET NEWS TONE</div>
            <div className={`text-xs sm:text-sm font-extrabold uppercase ${pres.marketTone === "POSITIVE" ? "text-[#00C896]" : pres.marketTone === "NEGATIVE" ? "text-[#E5484D]" : "text-[#E59700]"}`}>
              {pres.marketTone}
            </div>
            <div className="text-[7px] text-[#707987] truncate">Weighted directional score</div>
          </div>

          {/* 2. HIGH IMPACT STORIES */}
          <div className="px-2 py-1 space-y-0.5">
            <div className="text-[8px] font-bold uppercase text-[#707987] tracking-wider">HIGH IMPACT</div>
            <div className="text-xs sm:text-sm font-extrabold text-[#38BDF8] air-data">{pres.highImpactCount} Active</div>
            <div className="text-[7px] text-[#707987] truncate">Market-moving catalysts</div>
          </div>

          {/* 3. POSITIVE / NEGATIVE */}
          <div className="px-2 py-1 space-y-0.5">
            <div className="text-[8px] font-bold uppercase text-[#707987] tracking-wider">DIRECTION BREAKDOWN</div>
            <div className="text-xs sm:text-sm font-extrabold flex items-center gap-1">
              <span className="text-[#00C896]">{pres.positiveCount} POS</span>
              <span className="text-[#707987]">/</span>
              <span className="text-[#E5484D]">{pres.negativeCount} NEG</span>
            </div>
            <div className="text-[7px] text-[#707987] truncate">{pres.neutralCount} Neutral stories</div>
          </div>

          {/* 4. MOST AFFECTED SECTOR */}
          <div className="px-2 py-1 space-y-0.5">
            <div className="text-[8px] font-bold uppercase text-[#707987] tracking-wider">MOST AFFECTED SECTOR</div>
            <div className="text-xs sm:text-sm font-extrabold text-[#E6E8EB] truncate">{pres.mostAffectedSector}</div>
            <div className="text-[7px] text-[#707987] truncate">Highest story concentration</div>
          </div>

          {/* 5. NEXT MAJOR EVENT */}
          <div className="px-2 py-1 space-y-0.5">
            <div className="text-[8px] font-bold uppercase text-[#707987] tracking-wider">NEXT MAJOR EVENT</div>
            <div className="text-xs font-bold text-[#E59700] truncate">
              {pres.nextMajorEvent ? `${pres.nextMajorEvent.timeIST} (${pres.nextMajorEvent.region})` : "—"}
            </div>
            <div className="text-[7px] text-[#707987] truncate">
              {pres.nextMajorEvent ? pres.nextMajorEvent.eventName : "No major event scheduled"}
            </div>
          </div>

          {/* 6. NEWS RISK */}
          <div className="px-2 py-1 space-y-0.5">
            <div className="text-[8px] font-bold uppercase text-[#707987] tracking-wider">NEWS RISK</div>
            <div className={`text-xs sm:text-sm font-extrabold uppercase ${pres.newsRisk === "HIGH" ? "text-[#E5484D]" : pres.newsRisk === "ELEVATED" ? "text-[#E59700]" : "text-[#00C896]"}`}>
              {pres.newsRisk}
            </div>
            <div className="text-[7px] text-[#707987] truncate">Event density classification</div>
          </div>
        </div>
      </Surface>

      {/* ── MAIN CONTENT GRID: ADAPTIVE 3-COLUMN (XL) / 2-COLUMN (LG) / 1-COLUMN ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(320px,1.1fr)_minmax(380px,1.3fr)] xl:grid-cols-[minmax(320px,1.1fr)_minmax(380px,1.3fr)_minmax(280px,0.9fr)] gap-2.5 items-start min-w-0">
        
        {/* ── LEFT COLUMN: LIVE NEWS FEED (BOUNDED INTERNAL SCROLL) ── */}
        <Surface className="overflow-hidden flex flex-col h-[calc(100vh-210px)] min-h-[500px] min-w-0">
          {/* STICKY HEADER & FILTERS — UNTRUNCATED HEADER */}
          <div className="flex flex-wrap items-center justify-between border-b border-[#191D23] bg-[#0E1013] px-3 py-1.5 font-mono shrink-0 gap-1.5">
            <div className="flex items-center gap-1.5 shrink-0">
              <Zap size={13} className="text-[#38BDF8] shrink-0" />
              <span className="font-bold text-[#E6E8EB] text-xs uppercase whitespace-nowrap shrink-0">LIVE NEWS FEED</span>
              <span className="text-[9px] text-[#707987] font-bold shrink-0">({filteredFeed.length})</span>
            </div>

            {/* Filter Bar */}
            <div className="flex items-center gap-1 text-[8px] sm:text-[9px] flex-wrap justify-end">
              {(["ALL", "HIGH IMPACT", "POSITIVE", "NEGATIVE", "OFFICIAL"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => handleFilterChange(t)}
                  className={`px-1.5 py-0.5 rounded font-semibold transition ${
                    filterType === t
                      ? "bg-[#242830] text-[#E6E8EB]"
                      : "text-[#707987] hover:text-[#A5ABB4]"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* INDEPENDENTLY SCROLLABLE STORY LIST — DENSE PADDING */}
          <div
            ref={feedListRef}
            className="p-2 bg-[#0B0D10] space-y-1.5 font-mono text-[10px] min-h-0 flex-1 overflow-y-auto custom-terminal-scrollbar"
            style={{
              scrollbarWidth: "thin",
              scrollbarColor: "#242830 #0B0D10",
            }}
          >
            {filteredFeed.length > 0 ? (
              filteredFeed.map((story) => (
                <div
                  key={story.id}
                  className="p-2 rounded bg-[#0E1013] border border-[#191D23] hover:border-[#242830] transition space-y-1 min-w-0"
                >
                  <div className="flex items-center justify-between gap-1 flex-wrap">
                    <div className="flex items-center gap-1.5 flex-wrap min-w-0">
                      <span className="text-[8.5px] font-bold text-[#38BDF8] flex items-center gap-1 shrink-0">
                        <Clock size={9} />
                        {story.displayRowTime || story.publishedTimeIST}
                      </span>
                      <span
                        className={`text-[7.5px] font-bold px-1 rounded uppercase truncate max-w-[110px] ${
                          story.sourceType === "OFFICIAL"
                            ? "bg-[#8B5CF6]/20 text-[#8B5CF6] border border-[#8B5CF6]/30"
                            : "bg-[#191D23] text-[#A5ABB4]"
                        }`}
                      >
                        {story.publisher}
                      </span>
                      <span className="text-[7px] font-bold text-[#38BDF8] bg-[#38BDF8]/10 px-1 rounded uppercase border border-[#38BDF8]/20 shrink-0">
                        {story.category}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 shrink-0">
                      <span
                        className={`text-[7.5px] font-bold px-1 py-0.5 rounded ${
                          story.impactStrength === "HIGH"
                            ? "bg-[#E5484D]/20 text-[#E5484D]"
                            : story.impactStrength === "MEDIUM"
                            ? "bg-[#E59700]/20 text-[#E59700]"
                            : "bg-[#38BDF8]/20 text-[#38BDF8]"
                        }`}
                      >
                        {story.impactStrength}
                      </span>
                      <span
                        className={`text-[7.5px] font-bold px-1 py-0.5 rounded ${
                          story.expectedDirection === "POSITIVE"
                            ? "bg-[#00C896]/20 text-[#00C896]"
                            : story.expectedDirection === "NEGATIVE"
                            ? "bg-[#E5484D]/20 text-[#E5484D]"
                            : "bg-[#E59700]/20 text-[#E59700]"
                        }`}
                      >
                        {story.expectedDirection === "POSITIVE" ? "POS ↑" : story.expectedDirection === "NEGATIVE" ? "NEG ↓" : "NEU ↔"}
                      </span>
                    </div>
                  </div>

                  <div className="font-bold text-[#E6E8EB] text-[10.5px] leading-snug break-words">
                    {story.headline}
                  </div>

                  <div className="text-[8.5px] text-[#707987] leading-tight break-words">
                    {story.whyItMatters}
                  </div>

                  <div className="flex items-center justify-between text-[7.5px] text-[#707987] pt-0.5 border-t border-[#191D23] font-mono">
                    <span className="truncate">Sectors: {story.affectedSectors.join(", ")}</span>
                    {story.url && (
                      <a
                        href={story.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#38BDF8] font-bold hover:underline flex items-center gap-0.5 shrink-0 ml-1"
                      >
                        <span>Article</span>
                        <ExternalLink size={8} />
                      </a>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="py-6 text-center text-[#707987] italic">No stories matching active filter criteria.</div>
            )}
          </div>
        </Surface>

        {/* ── CENTER COLUMN: TOP STORY + CANONICAL CONTEXT + SECONDARY STORIES ── */}
        <div className="space-y-2.5 min-w-0 items-start">
          <Surface className="overflow-hidden">
            <SectionHeader title="TOP STORY OF THE SESSION" eyebrow="Highest NIFTY Impact" accent="amber" />
            <div className="p-2.5 bg-[#0B0D10] space-y-2 font-mono">
              {topStory ? (
                <>
                  <div className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1.5">
                    <div className="flex items-center justify-between flex-wrap gap-1">
                      <span className="text-[8.5px] font-bold text-[#38BDF8] bg-[#38BDF8]/15 px-1.5 py-0.5 rounded">
                        {topStory.publisher}
                      </span>
                      <span className="text-[8.5px] text-[#707987] font-bold">
                        {topStory.displayTopStoryTime || topStory.publishedTimeIST}
                      </span>
                    </div>

                    <h2 className="text-xs sm:text-[13px] font-bold text-[#E6E8EB] leading-snug break-words">
                      {topStory.headline}
                    </h2>

                    <div className="flex items-center gap-1 text-[8px] font-bold flex-wrap">
                      <span className="text-[#E5484D] bg-[#E5484D]/20 px-1 py-0.5 rounded">
                        {topStory.impactStrength} IMPACT
                      </span>
                      <span className="text-[#00C896] bg-[#00C896]/20 px-1 py-0.5 rounded">
                        {topStory.expectedDirection} DIRECTION
                      </span>
                      <span className="text-[#38BDF8] bg-[#38BDF8]/20 px-1 py-0.5 rounded">
                        RELEVANCE: {Math.round(topStory.niftyRelevance * 100)}%
                      </span>
                    </div>

                    <div className="text-[9.5px] text-[#A5ABB4] leading-relaxed pt-0.5">
                      {topStory.summary}
                    </div>
                  </div>

                  {/* WHY IT MATTERS BOX */}
                  <div className="p-2 rounded bg-[#38BDF8]/10 border border-[#38BDF8]/30 space-y-0.5">
                    <div className="text-[8.5px] font-bold text-[#38BDF8] uppercase tracking-wider flex items-center gap-1">
                      <Info size={10} />
                      <span>WHY IT MATTERS TO NIFTY</span>
                    </div>
                    <div className="text-[9.5px] text-[#E6E8EB] leading-relaxed">
                      {topStory.whyItMatters}
                    </div>
                  </div>

                  {/* Affected Companies & Action Link */}
                  <div className="flex items-center justify-between text-[8.5px] text-[#707987] font-mono pt-0.5">
                    <div>
                      {topStory.affectedCompanies.length > 0 && (
                        <span>Constituents: <strong className="text-[#E6E8EB]">{topStory.affectedCompanies.join(", ")}</strong></span>
                      )}
                    </div>
                    {topStory.url && (
                      <a
                        href={topStory.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#38BDF8] font-bold hover:underline flex items-center gap-1"
                      >
                        <span>Read full story</span>
                        <ExternalLink size={9} />
                      </a>
                    )}
                  </div>
                </>
              ) : (
                <div className="py-6 text-center text-[#707987]">No top story available.</div>
              )}
            </div>
          </Surface>

          {/* DENSE CANONICAL IMPACT CONTEXT CARD */}
          <Surface className="overflow-hidden">
            <SectionHeader title="CANONICAL IMPACT CONTEXT" eyebrow="Session Intelligence Telemetry" accent="cyan" />
            <div className="p-2.5 bg-[#0B0D10] space-y-1.5 font-mono text-[8.5px]">
              <div className="grid grid-cols-2 gap-1.5">
                <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23]">
                  <div className="text-[7.5px] text-[#707987] uppercase font-bold">Primary Sector</div>
                  <div className="font-bold text-[#38BDF8] mt-0.5">{topStory?.affectedSectors?.join(", ") || "BROAD_MARKET"}</div>
                </div>
                <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23]">
                  <div className="text-[7.5px] text-[#707987] uppercase font-bold">Impact Duration</div>
                  <div className="font-bold text-[#00C896] mt-0.5">{topStory?.impactDuration || "INTRADAY"}</div>
                </div>
              </div>

              <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] flex items-center justify-between">
                <span className="text-[#707987]">Source Quality Status:</span>
                <span className="font-bold text-[#8B5CF6] flex items-center gap-1">
                  <ShieldCheck size={9} />
                  {topStory?.sourceType === "OFFICIAL" ? "OFFICIAL REGULATORY RELEASE" : "VERIFIED FINANCIAL PRESS"}
                </span>
              </div>
            </div>
          </Surface>

          {/* SECONDARY CURRENT SESSION STORIES (ONLY RENDERED IF CANONICAL DATA EXISTS) */}
          {secondaryStories.length > 0 && (
            <Surface className="overflow-hidden">
              <SectionHeader title="RELATED SESSION COVERAGE" eyebrow="Key Parallel Catalysts" accent="violet" />
              <div className="p-2 bg-[#0B0D10] space-y-1.5 font-mono text-[9px]">
                {secondaryStories.map((s) => (
                  <div key={s.id} className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5">
                    <div className="flex items-center justify-between text-[7.5px]">
                      <span className="text-[#38BDF8] font-bold">{s.publisher}</span>
                      <span className="text-[#707987]">{s.displayRowTime}</span>
                    </div>
                    <div className="font-bold text-[#E6E8EB] text-[9.5px] leading-tight truncate">{s.headline}</div>
                  </div>
                ))}
              </div>
            </Surface>
          )}
        </div>

        {/* ── RIGHT COLUMN: MARKET IMPACT SUMMARY -> SECTOR NEWS IMPACT -> PROVIDER HEALTH ── */}
        <div className="space-y-2.5 min-w-0 items-start col-span-1 lg:col-span-2 xl:col-span-1">
          {/* 1. MARKET IMPACT SUMMARY */}
          <Surface className="overflow-hidden">
            <SectionHeader title="MARKET IMPACT SUMMARY" eyebrow="Story Distribution" accent="cyan" />
            <div className="p-2 bg-[#0B0D10] grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-2 gap-1.5 font-mono text-[9.5px]">
              <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23]">
                <div className="text-[7.5px] text-[#707987] font-bold uppercase">High Impact</div>
                <div className="font-bold text-[#E5484D] text-xs sm:text-sm air-data">{pres.impactCounts.high}</div>
              </div>
              <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23]">
                <div className="text-[7.5px] text-[#707987] font-bold uppercase">Medium Impact</div>
                <div className="font-bold text-[#E59700] text-xs sm:text-sm air-data">{pres.impactCounts.medium}</div>
              </div>
              <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23]">
                <div className="text-[7.5px] text-[#707987] font-bold uppercase">Low Impact</div>
                <div className="font-bold text-[#38BDF8] text-xs sm:text-sm air-data">{pres.impactCounts.low}</div>
              </div>
              <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23]">
                <div className="text-[7.5px] text-[#707987] font-bold uppercase">Total Stories</div>
                <div className="font-bold text-[#E6E8EB] text-xs sm:text-sm air-data">{pres.impactCounts.total}</div>
              </div>
            </div>
          </Surface>

          {/* 2. SECTOR NEWS IMPACT */}
          <Surface className="overflow-hidden">
            <SectionHeader title="SECTOR NEWS IMPACT" eyebrow="Aggregated Signals" accent="violet" />
            <div className="p-2 bg-[#0B0D10] space-y-0.5 font-mono text-[8.5px]">
              {Object.entries(pres.sectorImpactMap).map(([sector, tone]) => (
                <div key={sector} className="flex justify-between items-center py-0.5 border-b border-[#191D23]">
                  <span className="text-[#E6E8EB] font-bold">{sector}</span>
                  <span
                    className={`font-bold px-1 py-0.5 rounded text-[7.5px] ${
                      tone === "POSITIVE"
                        ? "bg-[#00C896]/20 text-[#00C896]"
                        : tone === "NEGATIVE"
                        ? "bg-[#E5484D]/20 text-[#E5484D]"
                        : "bg-[#E59700]/20 text-[#E59700]"
                    }`}
                  >
                    {tone}
                  </span>
                </div>
              ))}
            </div>
          </Surface>

          {/* 3. PROVIDER & SOURCE HEALTH — PLACED IMMEDIATELY AFTER SECTOR IMPACT */}
          <Surface className="overflow-hidden">
            <SectionHeader title="PROVIDER &amp; SOURCE HEALTH" eyebrow="Ingestion Status" accent="cyan" />
            <div className="p-2 bg-[#0B0D10] space-y-1 font-mono text-[8.5px]">
              {pres.providerHealthList.map((p, i) => (
                <div key={i} className="flex items-center justify-between p-1 rounded bg-[#0E1013] border border-[#191D23]">
                  <div>
                    <div className="font-bold text-[#E6E8EB] flex items-center gap-1">
                      <span>{p.providerName}</span>
                      {p.isOfficial && <ShieldCheck size={9} className="text-[#8B5CF6]" />}
                    </div>
                    <div className="text-[7.5px] text-[#707987]">{p.publisherLabel}</div>
                  </div>
                  <div className="text-right">
                    <span className="text-[7.5px] font-bold text-[#00C896] bg-[#00C896]/20 px-1 py-0.5 rounded uppercase">
                      {p.status}
                    </span>
                    <div className="text-[7.5px] text-[#707987] mt-0.5">{p.itemCount} items</div>
                  </div>
                </div>
              ))}
            </div>
          </Surface>
        </div>
      </div>
    </div>
  );
}

export default LiveNewsTab;
