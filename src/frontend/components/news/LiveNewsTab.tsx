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
  Calendar,
  X,
  Search,
  Radio,
  Eye,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import {
  CanonicalNewsStory,
  NewsPresentationState,
  CanonicalEconomicEvent,
} from "../../utils/canonicalNewsAdapter";

export function LiveNewsTab({
  pres,
  onSelectSubTab,
}: {
  pres: NewsPresentationState;
  onSelectSubTab?: (tab: "live_news" | "catalysts" | "calendar") => void;
}) {
  const [filterType, setFilterType] = useState<
    "ALL" | "HIGH IMPACT" | "POSITIVE" | "NEGATIVE" | "OFFICIAL" | "EARNINGS" | "MACRO"
  >("ALL");
  const feedListRef = useRef<HTMLDivElement>(null);

  // Modals for interactive "VIEW ALL" / "VIEW ANALYSIS" workflows
  const [showAllNewsModal, setShowAllNewsModal] = useState(false);
  const [showSectorModal, setShowSectorModal] = useState(false);
  const [showRelatedModal, setShowRelatedModal] = useState(false);
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const handleFilterChange = (
    t: "ALL" | "HIGH IMPACT" | "POSITIVE" | "NEGATIVE" | "OFFICIAL" | "EARNINGS" | "MACRO"
  ) => {
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
    if (filterType === "EARNINGS")
      return story.category === "CORPORATE_NIFTY" || story.affectedCompanies.length > 0;
    if (filterType === "MACRO")
      return (
        story.category === "INDIA_MACRO" ||
        story.category === "US_MACRO" ||
        story.category === "RBI_MONETARY" ||
        story.category === "FED_MONETARY"
      );
    return true;
  });

  const modalFilteredFeed = pres.liveFeed.filter((story) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      story.headline.toLowerCase().includes(q) ||
      story.publisher.toLowerCase().includes(q) ||
      story.whyItMatters.toLowerCase().includes(q) ||
      story.affectedCompanies.some((c) => c.toLowerCase().includes(q)) ||
      story.affectedSectors.some((s) => s.toLowerCase().includes(q))
    );
  });

  const topStory = pres.topStory;
  // 3-4 secondary/related stories for related coverage
  const relatedStories = pres.liveFeed.filter((s) => s.id !== topStory?.id).slice(0, 3);

  // Official source count
  const officialStoryCount = pres.liveFeed.filter((s) => s.sourceType === "OFFICIAL").length;
  const officialPct =
    pres.liveFeed.length > 0 ? Math.round((officialStoryCount / pres.liveFeed.length) * 100) : 0;

  // Next 3 upcoming events for timeline
  const upcomingTimelineEvents = pres.calendarEvents
    .filter((e) => e.isFuture || e.status === "UPCOMING")
    .slice(0, 3);

  return (
    <div className="space-y-2.5 font-sans text-left text-[11px] min-w-0">
      {/* ── 1. TOP SUMMARY STRIP — HIGH-DENSITY METRICS-ALIGNED STRIP ── */}
      <Surface className="overflow-hidden">
        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-[#191D23] bg-[#0B0D10] p-2 items-center font-mono">
          {/* 1. MARKET NEWS TONE */}
          <div className="px-2.5 py-1 space-y-0.5">
            <div className="text-[8.5px] font-bold uppercase text-[#707987] tracking-wider flex items-center justify-between">
              <span>MARKET NEWS TONE</span>
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  pres.marketTone === "POSITIVE"
                    ? "bg-[#00C896] animate-pulse"
                    : pres.marketTone === "NEGATIVE"
                    ? "bg-[#E5484D] animate-pulse"
                    : "bg-[#E59700]"
                }`}
              />
            </div>
            <div
              className={`text-xs sm:text-[13px] font-black uppercase ${
                pres.marketTone === "POSITIVE"
                  ? "text-[#00C896]"
                  : pres.marketTone === "NEGATIVE"
                  ? "text-[#E5484D]"
                  : "text-[#E59700]"
              }`}
            >
              {pres.marketTone}
            </div>
            <div className="text-[7.5px] text-[#707987] truncate">Weighted directional score</div>
          </div>

          {/* 2. HIGH IMPACT */}
          <div className="px-2.5 py-1 space-y-0.5">
            <div className="text-[8.5px] font-bold uppercase text-[#707987] tracking-wider">
              HIGH IMPACT
            </div>
            <div className="text-xs sm:text-[13px] font-black text-[#38BDF8] air-data">
              {pres.highImpactCount} Active
            </div>
            <div className="text-[7.5px] text-[#707987] truncate">Market-moving catalysts</div>
          </div>

          {/* 3. DIRECTION BREAKDOWN */}
          <div className="px-2.5 py-1 space-y-0.5">
            <div className="text-[8.5px] font-bold uppercase text-[#707987] tracking-wider">
              DIRECTION BREAKDOWN
            </div>
            <div className="text-xs sm:text-[13px] font-black flex items-center gap-1.5">
              <span className="text-[#00C896]">{pres.positiveCount} POS</span>
              <span className="text-[#707987]">/</span>
              <span className="text-[#E5484D]">{pres.negativeCount} NEG</span>
            </div>
            {/* Mini Segmented Bar */}
            <div className="h-1.5 w-full bg-[#191D23] rounded-full overflow-hidden flex gap-0.5">
              <div
                style={{
                  width: `${
                    pres.liveFeed.length > 0
                      ? Math.round((pres.positiveCount / pres.liveFeed.length) * 100)
                      : 33
                  }%`,
                }}
                className="h-full bg-[#00C896]"
              />
              <div
                style={{
                  width: `${
                    pres.liveFeed.length > 0
                      ? Math.round((pres.neutralCount / pres.liveFeed.length) * 100)
                      : 34
                  }%`,
                }}
                className="h-full bg-[#E59700]"
              />
              <div
                style={{
                  width: `${
                    pres.liveFeed.length > 0
                      ? Math.round((pres.negativeCount / pres.liveFeed.length) * 100)
                      : 33
                  }%`,
                }}
                className="h-full bg-[#E5484D]"
              />
            </div>
          </div>

          {/* 4. MOST AFFECTED SECTOR */}
          <div className="px-2.5 py-1 space-y-0.5">
            <div className="text-[8.5px] font-bold uppercase text-[#707987] tracking-wider">
              MOST AFFECTED SECTOR
            </div>
            <div className="text-xs sm:text-[13px] font-black text-[#E6E8EB] truncate flex items-center gap-1">
              <Building2 size={11} className="text-[#38BDF8] shrink-0" />
              <span>{pres.mostAffectedSector}</span>
            </div>
            <div className="text-[7.5px] text-[#707987] truncate">Highest story concentration</div>
          </div>

          {/* 5. NEXT MAJOR EVENT */}
          <div className="px-2.5 py-1 space-y-0.5">
            <div className="text-[8.5px] font-bold uppercase text-[#707987] tracking-wider">
              NEXT MAJOR EVENT
            </div>
            <div className="text-xs sm:text-[12px] font-bold text-[#E59700] truncate flex items-center gap-1">
              <Calendar size={11} className="text-[#E59700] shrink-0" />
              <span>
                {pres.nextMajorEvent
                  ? `${pres.nextMajorEvent.timeIST} (${pres.nextMajorEvent.region})`
                  : "—"}
              </span>
            </div>
            <div className="text-[7.5px] text-[#707987] truncate">
              {pres.nextMajorEvent ? pres.nextMajorEvent.eventName : "No major event scheduled"}
            </div>
          </div>

          {/* 6. NEWS RISK */}
          <div className="px-2.5 py-1 space-y-0.5">
            <div className="text-[8.5px] font-bold uppercase text-[#707987] tracking-wider">
              NEWS RISK
            </div>
            <div
              className={`text-xs sm:text-[13px] font-black uppercase ${
                pres.newsRisk === "HIGH"
                  ? "text-[#E5484D]"
                  : pres.newsRisk === "ELEVATED"
                  ? "text-[#E59700]"
                  : "text-[#00C896]"
              }`}
            >
              {pres.newsRisk}
            </div>
            <div className="text-[7.5px] text-[#707987] truncate">Event density classification</div>
          </div>
        </div>
      </Surface>

      {/* ── 2. UPPER 3-COLUMN WORKSTATION GRID (CONTENT-DRIVEN NATURAL HEIGHT) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(310px,1fr)_minmax(380px,1.3fr)] xl:grid-cols-[330px_minmax(0,1fr)_330px] gap-2.5 items-start min-w-0">
        {/* ── LEFT COLUMN: LIVE NEWS FEED ── */}
        <Surface className="overflow-hidden flex flex-col min-w-0">
          {/* Header & Filter Bar */}
          <div className="flex flex-wrap items-center justify-between border-b border-[#191D23] bg-[#0E1013] px-3 py-2 font-mono shrink-0 gap-1.5">
            <div className="flex items-center gap-1.5 shrink-0">
              <Zap size={13} className="text-[#38BDF8] shrink-0" />
              <span className="font-bold text-[#E6E8EB] text-xs uppercase whitespace-nowrap shrink-0">LIVE NEWS FEED</span>
              <span className="text-[9px] text-[#707987] font-bold shrink-0">
                ({filteredFeed.length})
              </span>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1 text-[8.5px] flex-wrap justify-end">
              {(
                [
                  "ALL",
                  "HIGH IMPACT",
                  "POSITIVE",
                  "NEGATIVE",
                  "OFFICIAL",
                  "EARNINGS",
                  "MACRO",
                ] as const
              ).map((t) => (
                <button
                  key={t}
                  onClick={() => handleFilterChange(t)}
                  className={`px-1.5 py-0.5 rounded font-bold transition ${
                    filterType === t
                      ? "bg-[#242830] text-[#38BDF8] border border-[#38BDF8]/40"
                      : "text-[#707987] hover:text-[#E6E8EB]"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Story Card List (Max height 460px with bounded scroll) */}
          <div
            ref={feedListRef}
            className="p-2 bg-[#0B0D10] space-y-1.5 font-mono text-[10px] max-h-[460px] overflow-y-auto custom-terminal-scrollbar"
            style={{
              scrollbarWidth: "thin",
              scrollbarColor: "#242830 #0B0D10",
            }}
          >
            {filteredFeed.length > 0 ? (
              filteredFeed.map((story) => (
                <div
                  key={story.id}
                  className="p-2 rounded bg-[#0E1013] border border-[#191D23] hover:border-[#38BDF8]/40 transition space-y-1 min-w-0"
                >
                  {/* Top Line: Source • Timestamp */}
                  <div className="flex items-center justify-between text-[8px] font-bold">
                    <span
                      className={`truncate max-w-[170px] uppercase ${
                        story.sourceType === "OFFICIAL"
                          ? "text-[#8B5CF6] font-bold flex items-center gap-1"
                          : "text-[#707987]"
                      }`}
                    >
                      {story.sourceType === "OFFICIAL" && <ShieldCheck size={8} />}
                      {story.publisher} • {story.displayRowTime || story.publishedTimeIST}
                    </span>
                    <span className="text-[#38BDF8] shrink-0 font-mono">[{story.region}]</span>
                  </div>

                  {/* Headline: 2 lines clamp */}
                  <div className="font-bold text-[#E6E8EB] text-[11px] leading-tight line-clamp-2 break-words">
                    {story.headline}
                  </div>

                  {/* Secondary: Matched constituents or NIFTY relevance */}
                  <div className="text-[8.5px] text-[#A5ABB4] leading-snug line-clamp-1">
                    {story.affectedCompanies.length > 0 ? (
                      <span>
                        Direct NIFTY constituent match:{" "}
                        <strong className="text-[#38BDF8]">
                          {story.affectedCompanies.join(", ")}
                        </strong>
                      </span>
                    ) : (
                      <span>{story.whyItMatters}</span>
                    )}
                  </div>

                  {/* Bottom Tags */}
                  <div className="flex items-center justify-between pt-1 border-t border-[#191D23] text-[7.5px] font-bold">
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className="bg-[#191D23] text-[#A5ABB4] px-1 py-0.2 rounded uppercase">
                        {story.category.replace(/_/g, " ")}
                      </span>
                      <span
                        className={`px-1 py-0.2 rounded uppercase ${
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
                        className={`px-1 py-0.2 rounded uppercase ${
                          story.expectedDirection === "POSITIVE"
                            ? "bg-[#00C896]/20 text-[#00C896]"
                            : story.expectedDirection === "NEGATIVE"
                            ? "bg-[#E5484D]/20 text-[#E5484D]"
                            : "bg-[#E59700]/20 text-[#E59700]"
                        }`}
                      >
                        {story.expectedDirection === "POSITIVE"
                          ? "POS ↑"
                          : story.expectedDirection === "NEGATIVE"
                          ? "NEG ↓"
                          : "NEU ↔"}
                      </span>
                    </div>

                    {story.url && (
                      <a
                        href={story.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#38BDF8] hover:underline flex items-center gap-0.5 shrink-0"
                      >
                        <span>Source</span>
                        <ExternalLink size={7.5} />
                      </a>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-[#707987] font-mono text-[10px] space-y-1">
                <div className="text-[#38BDF8] font-bold">NO MATCHING LIVE STORIES</div>
                <div>No stories currently match the selected filter criteria.</div>
              </div>
            )}
          </div>

          {/* Left Rail Action Footer: VIEW ALL NEWS */}
          <div className="p-2 border-t border-[#191D23] bg-[#0E1013] flex justify-between items-center text-[9px] font-mono">
            <span className="text-[#707987]">{pres.liveFeed.length} Stories Ingested</span>
            <button
              onClick={() => setShowAllNewsModal(true)}
              className="text-[#38BDF8] font-bold hover:underline flex items-center gap-1"
            >
              <span>VIEW ALL NEWS</span>
              <span>→</span>
            </button>
          </div>
        </Surface>

        {/* ── CENTER COLUMN: TOP STORY + WHY IT MATTERS + IMPACT CONTEXT + RELATED COVERAGE ── */}
        <div className="space-y-2.5 min-w-0 items-start">
          {/* A. Dominant Top Story of the Session */}
          <Surface className="overflow-hidden border border-[#38BDF8]/30">
            <SectionHeader
              title="TOP STORY OF THE SESSION"
              eyebrow="Highest NIFTY Impact"
              accent="cyan"
            />
            <div className="p-3 bg-[#0B0D10] space-y-2 font-mono">
              {topStory ? (
                <>
                  <div className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1.5">
                    <div className="flex items-center justify-between flex-wrap gap-1">
                      <span className="text-[9px] font-bold text-[#8B5CF6] bg-[#8B5CF6]/15 px-2 py-0.5 rounded flex items-center gap-1">
                        <ShieldCheck size={9} />
                        {topStory.publisher}
                      </span>
                      <span className="text-[9px] text-[#707987] font-bold">
                        {topStory.displayTopStoryTime || topStory.publishedTimeIST}
                      </span>
                    </div>

                    <h2 className="text-xs sm:text-[13.5px] font-bold text-[#E6E8EB] leading-snug break-words">
                      {topStory.headline}
                    </h2>

                    {/* Impact & Relevance Badges */}
                    <div className="flex items-center gap-1.5 text-[8.5px] font-bold flex-wrap">
                      <span className="text-[#E5484D] bg-[#E5484D]/20 px-1.5 py-0.5 rounded">
                        {topStory.impactStrength} IMPACT
                      </span>
                      <span className="text-[#00C896] bg-[#00C896]/20 px-1.5 py-0.5 rounded">
                        {topStory.expectedDirection} DIRECTION
                      </span>
                      <span className="text-[#38BDF8] bg-[#38BDF8]/20 px-1.5 py-0.5 rounded">
                        RELEVANCE: {Math.round(topStory.niftyRelevance * 100)}%
                      </span>
                    </div>

                    <div className="text-[10px] text-[#A5ABB4] leading-relaxed pt-1 border-t border-[#191D23]/60">
                      {topStory.summary}
                    </div>
                  </div>

                  {/* B. WHY IT MATTERS TO NIFTY (Proof-Oriented Transmission Mechanism) */}
                  <div className="p-2.5 rounded bg-[#38BDF8]/10 border border-[#38BDF8]/30 space-y-1">
                    <div className="text-[9px] font-bold text-[#38BDF8] uppercase tracking-wider flex items-center gap-1.5">
                      <Info size={11} />
                      <span>WHY IT MATTERS TO NIFTY</span>
                    </div>
                    <div className="text-[10.5px] text-[#E6E8EB] leading-relaxed font-sans font-semibold">
                      {topStory.whyItMatters ||
                        "Provides direct directional input for NIFTY constituent valuation."}
                    </div>
                    {topStory.affectedCompanies.length > 0 && (
                      <div className="text-[8.5px] text-[#707987] pt-0.5">
                        Exposed Constituents:{" "}
                        <strong className="text-[#38BDF8]">
                          {topStory.affectedCompanies.join(", ")}
                        </strong>
                      </div>
                    )}
                  </div>

                  {/* Story Action Link */}
                  <div className="flex items-center justify-between text-[9px] text-[#707987] font-mono pt-0.5">
                    <div>
                      <span>
                        Sector:{" "}
                        <strong className="text-[#E6E8EB]">
                          {topStory.affectedSectors.join(", ")}
                        </strong>
                      </span>
                    </div>
                    {topStory.url && (
                      <a
                        href={topStory.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#38BDF8] font-bold hover:underline flex items-center gap-1"
                      >
                        <span>Read full verified story</span>
                        <ExternalLink size={9.5} />
                      </a>
                    )}
                  </div>
                </>
              ) : (
                <div className="py-8 text-center text-[#707987] font-mono">
                  <div className="text-[#E59700] font-bold text-[11px]">
                    CANONICAL NEWS FEED UNAVAILABLE
                  </div>
                  <div className="text-[9px] mt-0.5">
                    Live session stories are currently synchronizing with broker feeds.
                  </div>
                </div>
              )}
            </div>
          </Surface>

          {/* C. CANONICAL IMPACT CONTEXT */}
          <Surface className="overflow-hidden">
            <SectionHeader
              title="CANONICAL IMPACT CONTEXT"
              eyebrow="Session Intelligence Telemetry"
              accent="cyan"
            />
            <div className="p-2.5 bg-[#0B0D10] space-y-2 font-mono text-[9px]">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5">
                  <div className="text-[7.5px] text-[#707987] uppercase font-bold">
                    Primary Sector
                  </div>
                  <div className="font-bold text-[#38BDF8] text-[10.5px] truncate">
                    {topStory?.affectedSectors?.join(", ") || "BROAD_MARKET"}
                  </div>
                </div>
                <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5">
                  <div className="text-[7.5px] text-[#707987] uppercase font-bold">
                    Impact Duration
                  </div>
                  <div className="font-bold text-[#00C896] text-[10.5px] truncate">
                    {topStory?.impactDuration || "INTRADAY"}
                  </div>
                </div>
                <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5">
                  <div className="text-[7.5px] text-[#707987] uppercase font-bold">
                    Source Quality
                  </div>
                  <div className="font-bold text-[#8B5CF6] text-[9.5px] truncate flex items-center gap-1">
                    <ShieldCheck size={9} />
                    <span>
                      {topStory?.sourceType === "OFFICIAL" ? "OFFICIAL" : "VERIFIED MEDIA"}
                    </span>
                  </div>
                </div>
                <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5">
                  <div className="text-[7.5px] text-[#707987] uppercase font-bold">Relevance</div>
                  <div className="font-bold text-[#38BDF8] text-[10.5px]">
                    {topStory ? `${Math.round(topStory.niftyRelevance * 100)}%` : "—"}
                  </div>
                </div>
                <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5">
                  <div className="text-[7.5px] text-[#707987] uppercase font-bold">Direction</div>
                  <div className="font-bold text-[#00C896] text-[10.5px]">
                    {topStory?.expectedDirection || "NEUTRAL"}
                  </div>
                </div>
                <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5">
                  <div className="text-[7.5px] text-[#707987] uppercase font-bold">
                    Historical Impact
                  </div>
                  <div className="font-bold text-[#707987] text-[9.5px]">UNAVAILABLE</div>
                </div>
              </div>
            </div>
          </Surface>

          {/* D. RELATED SESSION COVERAGE */}
          {relatedStories.length > 0 && (
            <Surface className="overflow-hidden">
              <SectionHeader
                title="RELATED SESSION COVERAGE"
                eyebrow="Key Parallel Catalysts"
                accent="cyan"
              />
              <div className="p-2 bg-[#0B0D10] space-y-1.5 font-mono text-[9px]">
                {relatedStories.map((s) => (
                  <div
                    key={s.id}
                    className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] hover:border-[#242830] transition space-y-0.5"
                  >
                    <div className="flex items-center justify-between text-[7.5px]">
                      <span className="text-[#38BDF8] font-bold">{s.publisher}</span>
                      <span className="text-[#707987]">
                        {s.displayRowTime || s.publishedTimeIST}
                      </span>
                    </div>
                    <div className="font-bold text-[#E6E8EB] text-[10px] leading-tight truncate">
                      {s.headline}
                    </div>
                    <div className="flex items-center justify-between text-[7.5px] text-[#707987]">
                      <span>{s.category.replace(/_/g, " ")}</span>
                      <span
                        className={`font-bold ${
                          s.expectedDirection === "POSITIVE"
                            ? "text-[#00C896]"
                            : s.expectedDirection === "NEGATIVE"
                            ? "text-[#E5484D]"
                            : "text-[#E59700]"
                        }`}
                      >
                        {s.expectedDirection}
                      </span>
                    </div>
                  </div>
                ))}

                <div className="pt-1 flex justify-end">
                  <button
                    onClick={() => setShowRelatedModal(true)}
                    className="text-[#38BDF8] font-bold text-[8.5px] hover:underline flex items-center gap-1"
                  >
                    <span>VIEW FULL RELATED COVERAGE</span>
                    <span>→</span>
                  </button>
                </div>
              </div>
            </Surface>
          )}
        </div>

        {/* ── RIGHT COLUMN: MARKET IMPACT SUMMARY -> SECTOR NEWS IMPACT -> EVENT TIMELINE ── */}
        <div className="space-y-2.5 min-w-0 items-start col-span-1 lg:col-span-2 xl:col-span-1">
          {/* 1. MARKET IMPACT SUMMARY */}
          <Surface className="overflow-hidden">
            <SectionHeader
              title="MARKET IMPACT SUMMARY"
              eyebrow="Story Distribution"
              accent="cyan"
            />
            <div className="p-2.5 bg-[#0B0D10] grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-2 gap-1.5 font-mono text-[9.5px]">
              <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                <div className="text-[7.5px] text-[#707987] font-bold uppercase">High Impact</div>
                <div className="font-bold text-[#E5484D] text-xs sm:text-[13px] air-data">
                  {pres.impactCounts.high}
                </div>
              </div>
              <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                <div className="text-[7.5px] text-[#707987] font-bold uppercase">
                  Medium Impact
                </div>
                <div className="font-bold text-[#E59700] text-xs sm:text-[13px] air-data">
                  {pres.impactCounts.medium}
                </div>
              </div>
              <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                <div className="text-[7.5px] text-[#707987] font-bold uppercase">Low Impact</div>
                <div className="font-bold text-[#38BDF8] text-xs sm:text-[13px] air-data">
                  {pres.impactCounts.low}
                </div>
              </div>
              <div className="p-2 rounded bg-[#0E1013] border border-[#191D23]">
                <div className="text-[7.5px] text-[#707987] font-bold uppercase">
                  Official Source %
                </div>
                <div className="font-bold text-[#8B5CF6] text-xs sm:text-[13px] air-data">
                  {officialPct}%
                </div>
              </div>
            </div>
          </Surface>

          {/* 2. SECTOR NEWS IMPACT */}
          <Surface className="overflow-hidden">
            <SectionHeader
              title="SECTOR NEWS IMPACT"
              eyebrow="Weighted Story Impact"
              accent="cyan"
            />
            <div className="p-2.5 bg-[#0B0D10] space-y-1.5 font-mono text-[9px]">
              {pres.sectorImpactRows && pres.sectorImpactRows.length > 0 ? (
                pres.sectorImpactRows.map((row) => (
                  <div key={row.sector} className="space-y-0.5">
                    <div className="flex justify-between items-center text-[8.5px]">
                      <span className="text-[#E6E8EB] font-bold">{row.sector}</span>
                      <span
                        className={`font-bold text-[8px] px-1 py-0.2 rounded ${
                          row.tone === "POSITIVE"
                            ? "bg-[#00C896]/20 text-[#00C896]"
                            : row.tone === "NEGATIVE"
                            ? "bg-[#E5484D]/20 text-[#E5484D]"
                            : "bg-[#E59700]/20 text-[#E59700]"
                        }`}
                      >
                        {row.tone}
                      </span>
                    </div>
                    {/* Visual Impact Bar */}
                    <div className="h-1.5 w-full bg-[#191D23] rounded-full overflow-hidden flex">
                      <div
                        style={{ width: `${row.barPercent}%` }}
                        className={`h-full rounded ${
                          row.tone === "POSITIVE"
                            ? "bg-gradient-to-r from-[#00C896]/50 to-[#00C896]"
                            : row.tone === "NEGATIVE"
                            ? "bg-gradient-to-r from-[#E5484D]/50 to-[#E5484D]"
                            : "bg-gradient-to-r from-[#E59700]/50 to-[#E59700]"
                        }`}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-2 text-center text-[#707987] italic text-[8.5px]">
                  Sector signals aggregating...
                </div>
              )}

              <div className="pt-1.5 border-t border-[#191D23] flex justify-end">
                <button
                  onClick={() => setShowSectorModal(true)}
                  className="text-[#38BDF8] font-bold text-[8.5px] hover:underline flex items-center gap-1"
                >
                  <span>VIEW SECTOR ANALYSIS</span>
                  <span>→</span>
                </button>
              </div>
            </div>
          </Surface>

          {/* 3. EVENT TIMELINE */}
          <Surface className="overflow-hidden">
            <SectionHeader
              title="EVENT TIMELINE"
              eyebrow="Upcoming Catalyst Schedule"
              accent="amber"
            />
            <div className="p-2.5 bg-[#0B0D10] space-y-1.5 font-mono text-[9px]">
              {upcomingTimelineEvents.length > 0 ? (
                upcomingTimelineEvents.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] flex items-center justify-between gap-1.5"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-1">
                        <span className="text-[#38BDF8] font-bold text-[8.5px]">
                          {ev.timeIST}
                        </span>
                        <span className="text-[7.5px] bg-[#191D23] text-[#707987] px-1 rounded font-bold">
                          {ev.region}
                        </span>
                      </div>
                      <div className="font-bold text-[#E6E8EB] text-[9.5px] truncate">
                        {ev.eventName}
                      </div>
                    </div>
                    <span
                      className={`text-[8px] font-bold px-1.5 py-0.5 rounded shrink-0 ${
                        ev.impact === "HIGH"
                          ? "bg-[#E5484D]/20 text-[#E5484D]"
                          : "bg-[#E59700]/20 text-[#E59700]"
                      }`}
                    >
                      {ev.impact}
                    </span>
                  </div>
                ))
              ) : (
                <div className="py-3 text-center text-[#707987] italic text-[8.5px]">
                  No upcoming calendar releases for today.
                </div>
              )}

              <div className="pt-1.5 border-t border-[#191D23] flex justify-end">
                <button
                  onClick={() => {
                    if (onSelectSubTab) onSelectSubTab("calendar");
                  }}
                  className="text-[#38BDF8] font-bold text-[8.5px] hover:underline flex items-center gap-1"
                >
                  <span>VIEW FULL CALENDAR</span>
                  <span>→</span>
                </button>
              </div>
            </div>
          </Surface>
        </div>
      </div>

      {/* ── 3. LOWER INTELLIGENCE TIER (WHAT CHANGED + NIFTY IMPACT WATCHLIST + PROVIDER HEALTH) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.3fr_330px] gap-2.5 items-stretch min-w-0">
        {/* ── SECTION A: WHAT CHANGED SINCE LAST CHECK ── */}
        <Surface className="overflow-hidden flex flex-col justify-between">
          <SectionHeader
            title="WHAT CHANGED SINCE LAST CHECK"
            eyebrow="Session Intelligence Shifts"
            accent="cyan"
          />
          <div className="p-2.5 bg-[#0B0D10] flex-1 flex flex-col justify-between space-y-2 font-mono text-[9px]">
            {/* Baseline timestamp */}
            <div className="flex items-center justify-between text-[8px] text-[#707987] border-b border-[#191D23] pb-1">
              <span>Baseline: {pres.whatChangedBaseline}</span>
              <span className="text-[#38BDF8] font-bold">Active Comparison</span>
            </div>

            {/* Delta Rows */}
            <div className="space-y-1.5 flex-1">
              {pres.whatChangedItems && pres.whatChangedItems.length > 0 ? (
                pres.whatChangedItems.map((item) => (
                  <div
                    key={item.id}
                    className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5"
                  >
                    <div className="flex justify-between items-center text-[7.5px]">
                      <span className="text-[#707987] font-bold">{item.category}</span>
                      <span className="text-[#707987]">{item.time}</span>
                    </div>
                    <div className="flex items-center justify-between text-[9.5px]">
                      <span className="text-[#707987] truncate max-w-[45%]">{item.before}</span>
                      <ArrowRight size={10} className="text-[#38BDF8] shrink-0 mx-1" />
                      <span
                        className={`font-bold truncate max-w-[45%] ${
                          item.tone === "POSITIVE"
                            ? "text-[#00C896]"
                            : item.tone === "NEGATIVE"
                            ? "text-[#E5484D]"
                            : item.tone === "AMBER"
                            ? "text-[#E59700]"
                            : "text-[#38BDF8]"
                        }`}
                      >
                        {item.after}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-4 text-center text-[#707987] italic text-[9px]">
                  Comparison unavailable — awaiting sequential state snapshot.
                </div>
              )}
            </div>

            <div className="text-[7.5px] text-[#707987] pt-1 border-t border-[#191D23]">
              Deterministic sequence tracking · Zero fabricated deltas
            </div>
          </div>
        </Surface>

        {/* ── SECTION B: NIFTY IMPACT WATCHLIST ── */}
        <Surface className="overflow-hidden flex flex-col justify-between">
          <SectionHeader
            title="NIFTY IMPACT WATCHLIST"
            eyebrow="Constituents &amp; Sectors with Highest News Exposure"
            accent="cyan"
          />
          <div className="p-2.5 bg-[#0B0D10] flex-1 flex flex-col justify-between space-y-2 font-mono text-[9px]">
            {/* Watchlist Rows */}
            <div className="space-y-1.5 flex-1">
              {pres.impactWatchlist && pres.impactWatchlist.length > 0 ? (
                pres.impactWatchlist.slice(0, 4).map((item) => (
                  <div
                    key={item.id}
                    className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] hover:border-[#38BDF8]/40 transition space-y-0.5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-[#E6E8EB] text-[10.5px]">
                          {item.symbol}
                        </span>
                        <span className="text-[7.5px] text-[#707987] bg-[#191D23] px-1 rounded">
                          {item.sector}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span
                          className={`text-[7.5px] font-bold px-1 py-0.2 rounded ${
                            item.impact === "HIGH"
                              ? "bg-[#E5484D]/20 text-[#E5484D]"
                              : "bg-[#E59700]/20 text-[#E59700]"
                          }`}
                        >
                          {item.impact}
                        </span>
                        <span
                          className={`text-[7.5px] font-bold px-1 py-0.2 rounded ${
                            item.direction === "POSITIVE"
                              ? "bg-[#00C896]/20 text-[#00C896]"
                              : item.direction === "NEGATIVE"
                              ? "bg-[#E5484D]/20 text-[#E5484D]"
                              : "bg-[#E59700]/20 text-[#E59700]"
                          }`}
                        >
                          {item.direction}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[8px] text-[#707987] pt-0.5">
                      <span className="text-[#A5ABB4] truncate">{item.whyWatch}</span>
                      <span className="text-[#38BDF8] shrink-0 font-bold ml-1">
                        {item.storyCount} {item.storyCount === 1 ? "story" : "stories"}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-4 text-center text-[#707987] italic text-[9px]">
                  Aggregating constituent news exposure...
                </div>
              )}
            </div>

            <div className="text-[7.5px] text-[#707987] pt-1 border-t border-[#191D23] flex justify-between">
              <span>Ranked by verified impact &amp; constituent exposure</span>
              <span>Deduplicated distinct evidence</span>
            </div>
          </div>
        </Surface>

        {/* ── SECTION C: PROVIDER & SOURCE HEALTH (ALIGNED LOWER RIGHT) ── */}
        <Surface className="overflow-hidden flex flex-col justify-between">
          <SectionHeader
            title="PROVIDER &amp; SOURCE HEALTH"
            eyebrow="Ingestion Status &amp; Latency"
            accent="cyan"
          />
          <div className="p-2.5 bg-[#0B0D10] flex-1 flex flex-col justify-between space-y-1.5 font-mono text-[8.5px]">
            <div className="space-y-1">
              {pres.providerHealthList.map((p, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-1.5 rounded bg-[#0E1013] border border-[#191D23]"
                >
                  <div>
                    <div className="font-bold text-[#E6E8EB] flex items-center gap-1 text-[9px]">
                      <span>{p.providerName}</span>
                      {p.isOfficial && <ShieldCheck size={9} className="text-[#8B5CF6]" />}
                    </div>
                    <div className="text-[7.5px] text-[#707987]">
                      {p.publisherLabel} • {p.lastSuccessTime}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[7.5px] font-bold text-[#00C896] bg-[#00C896]/20 px-1.5 py-0.5 rounded uppercase">
                      {p.status}
                    </span>
                    <div className="text-[7.5px] text-[#707987] mt-0.5">{p.itemCount} items</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-1 border-t border-[#191D23] flex justify-end">
              <button
                onClick={() => setShowSourceModal(true)}
                className="text-[#38BDF8] font-bold text-[8.5px] hover:underline flex items-center gap-1"
              >
                <span>VIEW SOURCE MONITOR</span>
                <span>→</span>
              </button>
            </div>
          </div>
        </Surface>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════════
          MODALS / DRAWERS FOR COMPREHENSIVE DRILL-DOWNS
          ═══════════════════════════════════════════════════════════════════════ */}

      {/* MODAL 1: VIEW ALL NEWS */}
      {showAllNewsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0B0D10] border border-[#242830] rounded-lg max-w-4xl w-full max-h-[85vh] flex flex-col overflow-hidden shadow-2xl font-mono">
            <div className="flex items-center justify-between p-3 border-b border-[#191D23] bg-[#0E1013]">
              <div className="flex items-center gap-2">
                <Zap size={14} className="text-[#38BDF8]" />
                <h3 className="font-bold text-[#E6E8EB] text-xs uppercase">
                  COMPLETE SESSION NEWS ARCHIVE ({pres.liveFeed.length} Stories)
                </h3>
              </div>
              <button
                onClick={() => setShowAllNewsModal(false)}
                className="text-[#707987] hover:text-[#E6E8EB] p-1 rounded"
              >
                <X size={15} />
              </button>
            </div>

            {/* Search Input */}
            <div className="p-3 border-b border-[#191D23] bg-[#08090B] flex items-center gap-2">
              <Search size={13} className="text-[#707987]" />
              <input
                type="text"
                placeholder="Search headlines, constituents, or themes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-transparent text-[11px] text-[#E6E8EB] placeholder-[#707987] focus:outline-none"
              />
            </div>

            {/* List */}
            <div className="p-3 space-y-2 overflow-y-auto flex-1 text-[10px]">
              {modalFilteredFeed.map((story) => (
                <div
                  key={story.id}
                  className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] space-y-1"
                >
                  <div className="flex items-center justify-between text-[8.5px] font-bold">
                    <span className="text-[#8B5CF6]">
                      {story.publisher} • {story.displayRowTime || story.publishedTimeIST}
                    </span>
                    <span className="text-[#38BDF8]">[{story.category}]</span>
                  </div>
                  <div className="font-bold text-[#E6E8EB] text-[11.5px]">{story.headline}</div>
                  <div className="text-[9px] text-[#A5ABB4]">{story.summary}</div>
                  <div className="text-[9px] text-[#38BDF8] bg-[#38BDF8]/10 p-1.5 rounded">
                    <strong>NIFTY Impact:</strong> {story.whyItMatters}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: SECTOR ANALYSIS */}
      {showSectorModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0B0D10] border border-[#242830] rounded-lg max-w-xl w-full p-4 space-y-3 font-mono shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
              <div className="font-bold text-[#E6E8EB] text-xs flex items-center gap-1.5">
                <Building2 size={13} className="text-[#38BDF8]" />
                <span>DETAILED SECTOR NEWS IMPACT MATRIX</span>
              </div>
              <button
                onClick={() => setShowSectorModal(false)}
                className="text-[#707987] hover:text-[#E6E8EB]"
              >
                <X size={15} />
              </button>
            </div>
            <div className="space-y-2 text-[10px]">
              {pres.sectorImpactRows?.map((row) => (
                <div
                  key={row.sector}
                  className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] flex justify-between items-center"
                >
                  <div>
                    <div className="font-bold text-[#E6E8EB] text-[11px]">{row.sector}</div>
                    <div className="text-[8.5px] text-[#707987]">{row.count} Stories Ingested</div>
                  </div>
                  <span
                    className={`font-bold px-2 py-0.5 rounded text-[9px] ${
                      row.tone === "POSITIVE"
                        ? "bg-[#00C896]/20 text-[#00C896]"
                        : row.tone === "NEGATIVE"
                        ? "bg-[#E5484D]/20 text-[#E5484D]"
                        : "bg-[#E59700]/20 text-[#E59700]"
                    }`}
                  >
                    {row.tone}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: RELATED COVERAGE */}
      {showRelatedModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0B0D10] border border-[#242830] rounded-lg max-w-2xl w-full p-4 space-y-3 font-mono shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
              <div className="font-bold text-[#E6E8EB] text-xs flex items-center gap-1.5">
                <Layers size={13} className="text-[#38BDF8]" />
                <span>FULL SESSION RELATED COVERAGE</span>
              </div>
              <button
                onClick={() => setShowRelatedModal(false)}
                className="text-[#707987] hover:text-[#E6E8EB]"
              >
                <X size={15} />
              </button>
            </div>
            <div className="space-y-2 text-[10px] max-h-[60vh] overflow-y-auto">
              {pres.liveFeed.slice(0, 8).map((story) => (
                <div
                  key={story.id}
                  className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5"
                >
                  <div className="flex justify-between text-[8px] text-[#707987]">
                    <span className="text-[#38BDF8] font-bold">{story.publisher}</span>
                    <span>{story.displayRowTime || story.publishedTimeIST}</span>
                  </div>
                  <div className="font-bold text-[#E6E8EB] text-[10.5px]">{story.headline}</div>
                  <div className="text-[8.5px] text-[#A5ABB4]">{story.whyItMatters}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* MODAL 4: SOURCE MONITOR */}
      {showSourceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0B0D10] border border-[#242830] rounded-lg max-w-lg w-full p-4 space-y-3 font-mono shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
              <div className="font-bold text-[#E6E8EB] text-xs flex items-center gap-1.5">
                <Radio size={13} className="text-[#38BDF8]" />
                <span>INGESTION PROVIDER HEALTH MONITOR</span>
              </div>
              <button
                onClick={() => setShowSourceModal(false)}
                className="text-[#707987] hover:text-[#E6E8EB]"
              >
                <X size={15} />
              </button>
            </div>
            <div className="space-y-2 text-[10px]">
              {pres.providerHealthList.map((p, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded bg-[#0E1013] border border-[#191D23] flex justify-between items-center"
                >
                  <div>
                    <div className="font-bold text-[#E6E8EB] text-[11px]">{p.providerName}</div>
                    <div className="text-[8px] text-[#707987]">
                      {p.publisherLabel} • Last sync: {p.lastSuccessTime}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[8px] font-bold text-[#00C896] bg-[#00C896]/20 px-1.5 py-0.5 rounded uppercase">
                      {p.status}
                    </span>
                    <div className="text-[8px] text-[#707987] mt-0.5">{p.itemCount} items</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LiveNewsTab;
