/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * EconomicCalendarView.tsx
 * Master Sprint Directive: Dense, Zero-Gap Bloomberg-Style Economic Calendar with Full Dataset Dynamic Binding.
 * 
 * Architecture:
 * - Direct Binding to Complete Canonical Event Store (pres.calendarEvents, ~60–80+ items)
 * - Dynamic Filter Counts: ALL EVENTS ({N}) · HIGH IMPACT & CRITICAL ({N}) · INDIA DIRECT ({N}) · US & GLOBAL ({N})
 * - Dynamic Date Grouping Engine: TODAY (Active Session) · TOMORROW · UPCOMING NEXT WEEK · LATER RELEASES
 * - High-Density Scrollable Table with Sticky Headers: h-[calc(100vh-280px)] min-h-[500px] overflow-y-auto
 * - Dedicated Data Columns: TIME (IST) | REGION | EVENT NAME (with ⓘ) | IMPACT | ACTUAL | CONSENSUS | PREVIOUS | NIFTY TRANSMISSION
 * - Isolated Event Inspection Modal (Description, Source Agency, NIFTY Reaction Matrix, Sensitive Stocks)
 */

import React, { useState, useMemo, useEffect } from "react";
import {
  Clock,
  Search,
  Info,
  X,
  ArrowUpRight,
  TrendingUp,
} from "lucide-react";
import {
  NewsPresentationState,
  CanonicalEconomicEvent,
} from "../../utils/canonicalNewsAdapter";
import { useCanonicalState } from "../../context/CanonicalStateContext";

export interface EconomicCalendarViewProps {
  pres: NewsPresentationState;
}

export const EconomicCalendarView: React.FC<EconomicCalendarViewProps> = ({ pres }) => {
  const [filterType, setFilterType] = useState<"ALL" | "HIGH_IMPACT" | "INDIA" | "GLOBAL">("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeInspectionEvent, setActiveInspectionEvent] = useState<CanonicalEconomicEvent | null>(null);

  let canonicalEnvelope: any = null;
  let sessionDateStr: string | null = null;
  try {
    const canonicalContext = useCanonicalState();
    canonicalEnvelope = canonicalContext?.envelope;
    sessionDateStr = canonicalContext?.sessionIdentity?.sessionDate ?? canonicalEnvelope?.session?.active_trading_date ?? null;
  } catch {
    // Isolated tests
  }

  // Dynamic session reference time: default to active session date 15:30:00 IST
  const sessionRefTime = useMemo(() => {
    const sDate = (pres as any)?.referenceSessionDate || sessionDateStr;
    if (!sDate || sDate === "—") return Date.now();
    return new Date(`${sDate}T10:00:00.000Z`).getTime();
  }, [(pres as any)?.referenceSessionDate, sessionDateStr]);

  // Keyboard escape listener to dismiss modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setActiveInspectionEvent(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // 1. Ingest Full Pipeline Events Dataset (excluding historical entries older than trailing 7-day window)
  const allEvents: CanonicalEconomicEvent[] = useMemo(() => {
    const events = pres?.calendarEvents || [];
    return [...events]
      .filter((ev) => {
        const evTime = new Date(ev.rawTimestamp).getTime();
        const refDay = new Date(sessionRefTime).setHours(0, 0, 0, 0);
        const evDay = new Date(evTime).setHours(0, 0, 0, 0);
        const dayDiff = Math.round((evDay - refDay) / (1000 * 60 * 60 * 24));
        if (dayDiff < -7) {
          return false;
        }
        return true;
      })
      .sort(
        (a, b) => new Date(a.rawTimestamp).getTime() - new Date(b.rawTimestamp).getTime()
      );
  }, [pres?.calendarEvents, sessionRefTime]);

  // Dynamic filter counts
  const totalCount = allEvents.length;
  const highImpactCount = useMemo(
    () => allEvents.filter((ev) => ev.impact === "HIGH" || ev.impact === "CRITICAL").length,
    [allEvents]
  );
  const indiaCount = useMemo(
    () => allEvents.filter((ev) => ev.region === "INDIA" || ev.countryCode === "IN").length,
    [allEvents]
  );
  const globalCount = useMemo(
    () => allEvents.filter((ev) => ev.region !== "INDIA" && ev.countryCode !== "IN").length,
    [allEvents]
  );

  // 2. Filtered Events
  const filteredEvents = useMemo(() => {
    return allEvents.filter((ev) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches =
          ev.eventName.toLowerCase().includes(q) ||
          ev.region.toLowerCase().includes(q) ||
          ev.countryCode.toLowerCase().includes(q) ||
          ev.date.toLowerCase().includes(q) ||
          (ev.transmission && ev.transmission.toLowerCase().includes(q)) ||
          (ev.agency && ev.agency.toLowerCase().includes(q));
        if (!matches) return false;
      }

      if (filterType === "HIGH_IMPACT") return ev.impact === "HIGH" || ev.impact === "CRITICAL";
      if (filterType === "INDIA") return ev.region === "INDIA" || ev.countryCode === "IN";
      if (filterType === "GLOBAL") return ev.region !== "INDIA" && ev.countryCode !== "IN";

      return true;
    });
  }, [allEvents, filterType, searchQuery]);

  // 3. Dynamic "Next Upcoming Release" Selection Engine
  const nextUpcomingEvent = useMemo(() => {
    const upcomingHighImpact = allEvents
      .filter((ev) => {
        const evtTime = new Date(ev.rawTimestamp).getTime();
        return evtTime > sessionRefTime && (ev.impact === "HIGH" || ev.impact === "CRITICAL");
      })
      .sort((a, b) => new Date(a.rawTimestamp).getTime() - new Date(b.rawTimestamp).getTime());

    return upcomingHighImpact[0] || null;
  }, [allEvents, sessionRefTime]);

  // Calculate dynamic countdown string
  const countdownText = useMemo(() => {
    if (!nextUpcomingEvent) return "No immediate release scheduled";
    const evtTime = new Date(nextUpcomingEvent.rawTimestamp).getTime();
    const diffMs = evtTime - sessionRefTime;
    if (diffMs <= 0) return "Releasing Now";

    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (diffHours >= 24) {
      const days = Math.floor(diffHours / 24);
      const remHours = diffHours % 24;
      return `in ${days}d ${remHours}h`;
    }
    return `in ${diffHours}h ${diffMins}m`;
  }, [nextUpcomingEvent, sessionRefTime]);

  // 4. Dynamic Date Grouping Engine
  const groupedEvents = useMemo(() => {
    const groupsMap = new Map<string, { label: string; order: number; events: CanonicalEconomicEvent[] }>();

    filteredEvents.forEach((ev) => {
      const evDate = new Date(ev.rawTimestamp);
      const evDateStr = ev.date;

      const evTime = evDate.getTime();
      const refDay = new Date(sessionRefTime).setHours(0, 0, 0, 0);
      const evDay = new Date(evTime).setHours(0, 0, 0, 0);
      const dayDiff = Math.round((evDay - refDay) / (1000 * 60 * 60 * 24));

      let groupKey: string;
      let groupLabel: string;
      let order: number;

      if (dayDiff === 0 || ev.isToday) {
        groupKey = "TODAY";
        groupLabel = `TODAY (${evDateStr || "Active Session"})`;
        order = 1;
      } else if (dayDiff === 1) {
        groupKey = "TOMORROW";
        groupLabel = `TOMORROW (${evDateStr})`;
        order = 2;
      } else if (dayDiff > 1 && dayDiff <= 7) {
        groupKey = "NEXT_WEEK";
        groupLabel = "UPCOMING NEXT WEEK";
        order = 3;
      } else if (dayDiff < 0) {
        // Restrict completed releases to trailing 7-day window
        if (dayDiff < -7) {
          return;
        }
        groupKey = "PAST";
        groupLabel = "RECENT COMPLETED RELEASES";
        order = 0;
      } else {
        groupKey = "LATER";
        groupLabel = "LATER SCHEDULED RELEASES";
        order = 4;
      }

      if (!groupsMap.has(groupKey)) {
        groupsMap.set(groupKey, { label: groupLabel, order, events: [] });
      }
      groupsMap.get(groupKey)!.events.push(ev);
    });

    return Array.from(groupsMap.values()).sort((a, b) => a.order - b.order);
  }, [filteredEvents]);

  return (
    <div className="w-full flex flex-col gap-2 font-mono text-left select-none text-xs relative">
      {/* ═════════════════════════════════════════════════════════════
          1. DYNAMIC "NEXT UPCOMING RELEASE" COUNTDOWN BANNER
          ═════════════════════════════════════════════════════════════ */}
      {nextUpcomingEvent && (
        <div className="w-full p-2.5 rounded-md bg-amber-950/25 border border-amber-500/40 flex items-center justify-between text-xs font-mono flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-400 animate-pulse shrink-0" />
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-semibold text-neutral-100">
                ⏳ NEXT UPCOMING RELEASE:
              </span>
              <span className="text-amber-300 font-bold">
                {nextUpcomingEvent.eventName}
              </span>
              <span className="text-neutral-400 font-normal">
                ({nextUpcomingEvent.timeIST} IST · {nextUpcomingEvent.date})
              </span>
              {nextUpcomingEvent.consensus && nextUpcomingEvent.consensus !== "—" && (
                <span className="text-neutral-300">
                  | Consensus:{" "}
                  <strong className="text-cyan-300 font-mono">
                    {nextUpcomingEvent.consensus}
                  </strong>{" "}
                  (Prior: {nextUpcomingEvent.previous})
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold border ${
                nextUpcomingEvent.impact === "CRITICAL"
                  ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                  : "bg-amber-500/20 text-amber-300 border-amber-500/40"
              }`}
            >
              {nextUpcomingEvent.impact}
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 tabular-nums">
              {countdownText}
            </span>
          </div>
        </div>
      )}

      {/* ═════════════════════════════════════════════════════════════
          2. HIGH-DENSITY CALENDAR TABLE & TIMELINE
          ═════════════════════════════════════════════════════════════ */}
      <div className="w-full bg-neutral-900/40 border border-neutral-800 rounded-md overflow-hidden flex flex-col">
        {/* Filter Toolbar & Search Bar with Dynamic Counts */}
        <div className="p-2 border-b border-neutral-800/80 bg-neutral-900/60 flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap gap-1 text-[10px]">
            {[
              { id: "ALL", label: `ALL EVENTS (${totalCount})` },
              { id: "HIGH_IMPACT", label: `HIGH IMPACT & CRITICAL (${highImpactCount})` },
              { id: "INDIA", label: `INDIA DIRECT (${indiaCount})` },
              { id: "GLOBAL", label: `US & GLOBAL (${globalCount})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setFilterType(tab.id as any)}
                className={`px-2 py-0.5 rounded font-mono font-medium border transition-colors ${
                  filterType === tab.id
                    ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40 font-bold"
                    : "bg-neutral-950/60 text-neutral-400 hover:text-neutral-200 border-neutral-800/80"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="relative w-56">
            <input
              type="text"
              placeholder="Search release / region / sector..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-neutral-950/60 border border-neutral-800 text-xs px-2 py-1 pl-6 text-neutral-200 focus:outline-none focus:border-cyan-500/50 placeholder:text-neutral-600 font-mono rounded"
            />
            <Search className="w-3 h-3 text-neutral-500 absolute left-1.5 top-2" />
          </div>
        </div>

        {/* Dense Multi-Column Table with Sticky Header and Performant Scrolling */}
        <div className="h-[calc(100vh-280px)] min-h-[500px] overflow-y-auto overflow-x-auto">
          <table className="w-full text-xs font-mono border-collapse text-left">
            <thead className="sticky top-0 z-10 bg-neutral-950/95 backdrop-blur-sm">
              <tr className="border-b border-neutral-800/80 text-[10px] font-mono font-semibold uppercase tracking-wider text-neutral-400">
                <th className="py-2 px-3 whitespace-nowrap">TIME (IST)</th>
                <th className="py-2 px-2.5 whitespace-nowrap">REGION</th>
                <th className="py-2 px-3">EVENT NAME</th>
                <th className="py-2 px-2.5 text-center whitespace-nowrap">IMPACT</th>
                <th className="py-2 px-2.5 text-center whitespace-nowrap">ACTUAL</th>
                <th className="py-2 px-2.5 text-center whitespace-nowrap">CONSENSUS</th>
                <th className="py-2 px-2.5 text-center whitespace-nowrap">PREVIOUS</th>
                <th className="py-2 px-3">NIFTY TRANSMISSION</th>
              </tr>
            </thead>
            <tbody>
              {groupedEvents.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-neutral-500 text-[11px] font-mono">
                    Awaiting economic-calendar provider — no events ingested yet.
                  </td>
                </tr>
              )}
              {groupedEvents.map((group) => (
                <React.Fragment key={group.label}>
                  {/* Timeline Date Group Header Divider */}
                  <tr>
                    <td
                      colSpan={8}
                      className="bg-neutral-900/90 px-3 py-1 text-[11px] font-mono text-cyan-400 font-bold border-y border-neutral-800/80 tracking-wide sticky top-[29px] z-0 backdrop-blur-xs"
                    >
                      {group.label}
                    </td>
                  </tr>

                  {/* Group Event Rows */}
                  {group.events.map((ev) => {
                    const isReleased = ev.status === "RELEASED";
                    const isCritical = ev.impact === "CRITICAL";
                    const isHigh = ev.impact === "HIGH";
                    const isMed = ev.impact === "MEDIUM";

                    return (
                      <tr
                        key={ev.id}
                        className="border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors"
                      >
                        {/* 1. Time (IST) */}
                        <td className="px-3 py-1.5 whitespace-nowrap tabular-nums">
                          <span className="text-cyan-300 font-bold">{ev.timeIST}</span>
                        </td>

                        {/* 2. Region */}
                        <td className="px-2.5 py-1.5 whitespace-nowrap">
                          <span
                            className={`text-[9.5px] px-1.5 py-0.2 rounded font-mono font-semibold border ${
                              ev.region === "INDIA"
                                ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                                : ev.region === "US"
                                ? "bg-blue-500/15 text-blue-300 border-blue-500/30"
                                : ev.region === "EUROZONE" || ev.countryCode === "EU"
                                ? "bg-purple-500/15 text-purple-300 border-purple-500/30"
                                : ev.region === "JAPAN" || ev.countryCode === "JP"
                                ? "bg-red-500/15 text-red-300 border-red-500/30"
                                : ev.region === "CHINA" || ev.countryCode === "CN"
                                ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
                                : "bg-cyan-500/15 text-cyan-300 border-cyan-500/30"
                            }`}
                          >
                            {ev.region}
                          </span>
                        </td>

                        {/* 3. Event Name + Details Button */}
                        <td className="px-3 py-1.5 font-medium text-neutral-100 min-w-[220px]">
                          <div className="flex items-center gap-1.5">
                            <span>{ev.eventName}</span>
                            <button
                              onClick={() => setActiveInspectionEvent(ev)}
                              title="Inspect Event Intelligence"
                              className="p-0.5 rounded bg-neutral-800/80 border border-neutral-700/80 text-cyan-400 hover:text-cyan-300 hover:border-cyan-500/50 transition-colors inline-flex items-center justify-center cursor-pointer shrink-0"
                            >
                              <Info className="w-2.5 h-2.5" />
                            </button>
                          </div>
                        </td>

                        {/* 4. Impact */}
                        <td className="px-2.5 py-1.5 text-center whitespace-nowrap">
                          <span
                            className={`text-[9.5px] px-1.5 py-0.2 rounded font-mono font-semibold border ${
                              isCritical
                                ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                                : isHigh
                                ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                                : isMed
                                ? "bg-teal-500/15 text-teal-300 border-teal-500/30"
                                : "bg-neutral-800 text-neutral-400 border-neutral-700"
                            }`}
                          >
                            {ev.impact}
                          </span>
                        </td>

                        {/* 5. Actual */}
                        <td className="px-2.5 py-1.5 text-center whitespace-nowrap tabular-nums">
                          {isReleased ? (
                            <span
                              className={`font-bold ${
                                ev.actualSurprise === "BEAT"
                                  ? "text-emerald-400"
                                  : ev.actualSurprise === "MISS"
                                  ? "text-rose-400"
                                  : "text-neutral-200"
                              }`}
                            >
                              {ev.actual}
                            </span>
                          ) : (
                            <span className="text-neutral-500 text-[10.5px]">Pending</span>
                          )}
                        </td>

                        {/* 6. Consensus */}
                        <td className="px-2.5 py-1.5 text-center font-semibold text-neutral-200 whitespace-nowrap tabular-nums">
                          {ev.consensus}
                        </td>

                        {/* 7. Previous */}
                        <td className="px-2.5 py-1.5 text-center text-neutral-400 whitespace-nowrap tabular-nums">
                          {ev.previous}
                        </td>

                        {/* 8. NIFTY Transmission */}
                        <td className="px-3 py-1.5 text-[11px] text-neutral-300 font-sans leading-tight">
                          {ev.transmission}
                        </td>
                      </tr>
                    );
                  })}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ═════════════════════════════════════════════════════════════
          3. ISOLATED EVENT INSPECTION MODAL (FIXED INSET OVERLAY)
          ═════════════════════════════════════════════════════════════ */}
      {activeInspectionEvent && (
        <div
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setActiveInspectionEvent(null);
            }
          }}
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
        >
          <div className="bg-neutral-900 border border-neutral-700/80 rounded-lg max-w-xl w-full p-5 shadow-2xl flex flex-col gap-3.5 font-mono text-xs text-left animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-neutral-800 pb-2.5">
              <div className="flex items-center gap-2 text-[11px]">
                <span className="font-bold text-cyan-300 uppercase">
                  {activeInspectionEvent.region}
                </span>
                <span className="text-neutral-600">|</span>
                <span className="text-neutral-400">
                  RELEASE:{" "}
                  <span className="text-neutral-200 tabular-nums">
                    {activeInspectionEvent.timeIST} IST ({activeInspectionEvent.date})
                  </span>
                </span>
                <span
                  className={`text-[9.5px] px-1.5 py-0.2 rounded font-semibold border ${
                    activeInspectionEvent.impact === "CRITICAL"
                      ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                      : activeInspectionEvent.impact === "HIGH"
                      ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                      : "bg-teal-500/15 text-teal-300 border-teal-500/30"
                  }`}
                >
                  {activeInspectionEvent.impact}
                </span>
              </div>

              <button
                onClick={() => setActiveInspectionEvent(null)}
                className="text-neutral-400 hover:text-neutral-100 flex items-center gap-1 font-mono text-xs px-2 py-0.5 rounded hover:bg-neutral-800 transition-colors cursor-pointer"
              >
                <span>Close</span>
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Headline & Source Agency */}
            <div>
              <h2 className="text-sm sm:text-base font-bold text-neutral-100 leading-snug font-sans">
                {activeInspectionEvent.eventName}
              </h2>
              <div className="text-[10px] text-neutral-400 mt-0.5">
                Reporting Agency:{" "}
                <span className="text-cyan-300 font-semibold">{activeInspectionEvent.agency}</span>
              </div>
            </div>

            {/* Ingested Description */}
            <div className="bg-neutral-950/70 border border-neutral-800 p-3 rounded space-y-1">
              <span className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider block">
                MACROECONOMIC DESCRIPTION:
              </span>
              <p className="text-neutral-300 text-[11.5px] leading-relaxed font-sans">
                {activeInspectionEvent.description}
              </p>
            </div>

            {/* Numeric Consensus Strip */}
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="bg-neutral-950/60 p-2 rounded border border-neutral-800">
                <span className="text-[10px] text-neutral-500 uppercase block">ACTUAL:</span>
                <span
                  className={`font-bold tabular-nums text-[12px] ${
                    activeInspectionEvent.status === "RELEASED"
                      ? "text-emerald-400"
                      : "text-neutral-400"
                  }`}
                >
                  {activeInspectionEvent.actual || "Pending"}
                </span>
              </div>
              <div className="bg-neutral-950/60 p-2 rounded border border-neutral-800">
                <span className="text-[10px] text-neutral-500 uppercase block">CONSENSUS:</span>
                <span className="font-bold text-neutral-200 tabular-nums text-[12px]">
                  {activeInspectionEvent.consensus}
                </span>
              </div>
              <div className="bg-neutral-950/60 p-2 rounded border border-neutral-800">
                <span className="text-[10px] text-neutral-500 uppercase block">PREVIOUS:</span>
                <span className="font-bold text-neutral-400 tabular-nums text-[12px]">
                  {activeInspectionEvent.previous}
                </span>
              </div>
            </div>

            {/* Historical NIFTY Reaction Matrix */}
            <div className="bg-neutral-950/60 p-2.5 rounded border border-neutral-800 space-y-1">
              <span className="text-emerald-400 font-semibold text-[10.5px] block uppercase flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-emerald-400" />
                HISTORICAL NIFTY REACTION MATRIX:
              </span>
              <p className="text-neutral-200 text-[11px] font-sans leading-snug">
                {activeInspectionEvent.reactionMatrix}
              </p>
            </div>

            {/* Sensitive Stocks & Transmission */}
            <div className="p-2.5 bg-neutral-950/50 rounded border border-neutral-800/80 text-[11px] space-y-1.5">
              <div className="flex items-center gap-1.5">
                <span className="text-neutral-500 font-semibold">TRANSMISSION:</span>
                <span className="text-neutral-300 font-sans">{activeInspectionEvent.transmission}</span>
              </div>
              {activeInspectionEvent.sensitiveStocks && activeInspectionEvent.sensitiveStocks.length > 0 && (
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-neutral-500 font-semibold">SENSITIVE STOCKS:</span>
                  <div className="flex items-center gap-1 flex-wrap">
                    {activeInspectionEvent.sensitiveStocks.map((stk) => (
                      <span
                        key={stk}
                        className="px-1.5 py-0.2 rounded font-mono text-[10px] font-semibold bg-cyan-950/40 text-cyan-300 border border-cyan-500/30"
                      >
                        {stk}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Action Footer */}
            <div className="flex items-center justify-between pt-2 border-t border-neutral-800">
              <span className="text-[10px] text-neutral-500">
                Press <strong className="text-neutral-400 font-mono">ESC</strong> or click outside to dismiss
              </span>

              {activeInspectionEvent.url && (
                <a
                  href={activeInspectionEvent.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 border border-cyan-500/40 hover:border-cyan-400 px-3 py-1 rounded bg-cyan-950/40 font-semibold transition-colors"
                >
                  <span>Open Official Source Portal</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EconomicCalendarView;
