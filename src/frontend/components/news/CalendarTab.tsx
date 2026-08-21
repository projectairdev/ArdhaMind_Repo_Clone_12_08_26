import React, { useState } from "react";
import { Calendar, Clock, Globe, ShieldCheck, Filter, CheckCircle2 } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import { NewsPresentationState, CanonicalEconomicEvent } from "../../utils/canonicalNewsAdapter";

export function CalendarTab({ pres }: { pres: NewsPresentationState }) {
  const [regionFilter, setRegionFilter] = useState<"ALL" | "INDIA" | "US" | "GLOBAL">("ALL");
  const [impactFilter, setImpactFilter] = useState<"ALL" | "HIGH">("ALL");

  const filteredEvents = pres.calendarEvents.filter((ev) => {
    if (regionFilter === "INDIA" && ev.region !== "INDIA" && ev.countryCode !== "IN") return false;
    if (regionFilter === "US" && ev.region !== "US" && ev.countryCode !== "US") return false;
    if (regionFilter === "GLOBAL" && (ev.region === "INDIA" || ev.region === "US" || ev.countryCode === "IN" || ev.countryCode === "US")) return false;

    if (impactFilter === "HIGH" && ev.impact !== "HIGH") return false;

    return true;
  });

  // Reorder presentation: UPCOMING FIRST, then COMPLETED
  const upcomingEvents = filteredEvents.filter((e) => e.status === "UPCOMING" || e.isFuture);
  const completedEvents = filteredEvents.filter((e) => e.status === "COMPLETED" && !e.isFuture);

  const renderEventRows = (eventList: CanonicalEconomicEvent[]) => (
    <tbody className="divide-y divide-[#14171D]">
      {eventList.map((ev) => (
        <tr key={ev.id} className="hover:bg-[#0E1013] transition font-mono">
          <td className="py-1.5 px-2 font-bold text-[#E6E8EB] whitespace-nowrap">{ev.date}</td>
          <td className="py-1.5 px-2 text-[#38BDF8] font-bold whitespace-nowrap">{ev.timeIST}</td>
          <td className="py-1.5 px-2 font-bold text-[#707987] whitespace-nowrap">
            <span
              className={`px-1 py-0.5 rounded text-[8px] ${
                ev.region === "INDIA"
                  ? "bg-[#00C896]/15 text-[#00C896]"
                  : ev.region === "US"
                  ? "bg-[#38BDF8]/15 text-[#38BDF8]"
                  : "bg-[#8B5CF6]/15 text-[#8B5CF6]"
              }`}
            >
              {ev.region}
            </span>
          </td>
          <td className="py-1.5 px-2 font-bold text-[#E6E8EB]">{ev.eventName}</td>
          <td className="py-1.5 px-2 text-center whitespace-nowrap">
            <span
              className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${
                ev.impact === "HIGH"
                  ? "bg-[#E5484D]/20 text-[#E5484D]"
                  : ev.impact === "MEDIUM"
                  ? "bg-[#E59700]/20 text-[#E59700]"
                  : "bg-[#38BDF8]/20 text-[#38BDF8]"
              }`}
            >
              {ev.impact}
            </span>
          </td>
          <td className="py-1.5 px-2 text-center whitespace-nowrap">
            <span
              className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${
                ev.status === "UPCOMING"
                  ? "bg-[#38BDF8]/20 text-[#38BDF8]"
                  : "bg-[#00C896]/20 text-[#00C896]"
              }`}
            >
              {ev.status}
            </span>
          </td>
          <td className="py-1.5 px-2 text-right text-[#707987] air-data whitespace-nowrap hidden lg:table-cell">{ev.previous}</td>
          <td className="py-1.5 px-2 text-right text-[#707987] air-data whitespace-nowrap hidden lg:table-cell">{ev.consensus}</td>
          <td className="py-1.5 px-2 text-right font-bold text-[#E6E8EB] air-data whitespace-nowrap hidden lg:table-cell">{ev.actual}</td>
        </tr>
      ))}
    </tbody>
  );

  return (
    <div className="space-y-3 font-sans text-left text-[11px] min-w-0">
      {/* 9. CALENDAR TABLE */}
      <Surface className="overflow-hidden min-w-0">
        <div className="flex flex-wrap items-center justify-between border-b border-[#191D23] bg-[#0E1013] px-3 py-2 font-mono gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <Calendar size={14} className="text-[#38BDF8] shrink-0" />
            <h1 className="text-xs font-bold text-[#E6E8EB] uppercase truncate">ECONOMIC &amp; CORPORATE CALENDAR</h1>
            <span className="text-[9px] text-[#707987] font-bold shrink-0">({filteredEvents.length} Scheduled Releases)</span>
          </div>

          <div className="flex items-center gap-3 text-[9px] flex-wrap justify-end">
            <div className="flex items-center gap-1">
              <span className="text-[#707987]">Region:</span>
              {(["ALL", "INDIA", "US", "GLOBAL"] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setRegionFilter(r)}
                  className={`px-1.5 py-0.5 rounded font-semibold transition ${
                    regionFilter === r ? "bg-[#242830] text-[#E6E8EB]" : "text-[#707987] hover:text-[#A5ABB4]"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1">
              <span className="text-[#707987]">Impact:</span>
              <button
                onClick={() => setImpactFilter(impactFilter === "ALL" ? "HIGH" : "ALL")}
                className={`px-1.5 py-0.5 rounded font-semibold transition ${
                  impactFilter === "HIGH" ? "bg-[#E5484D]/20 text-[#E5484D]" : "text-[#707987] hover:text-[#A5ABB4]"
                }`}
              >
                HIGH ONLY
              </button>
            </div>
          </div>
        </div>

        <div className="p-2 sm:p-3 bg-[#0B0D10] font-mono text-[10px] space-y-4 min-w-0">
          {/* ── SECTION 1: UPCOMING EVENTS (PRIORITIZED FIRST) ── */}
          <div className="space-y-1.5 min-w-0">
            <div className="flex items-center justify-between border-b border-[#191D23] pb-1">
              <span className="font-bold text-[#38BDF8] text-[10px] uppercase flex items-center gap-1.5">
                <Clock size={12} />
                UPCOMING EVENTS ({upcomingEvents.length})
              </span>
              <span className="text-[8px] text-[#707987]">Prioritized Session Releases</span>
            </div>

            <div className="overflow-x-auto min-w-0">
              <table className="w-full text-left table-auto">
                <thead>
                  <tr className="border-b border-[#191D23] bg-[#0E1013] text-[#707987] text-[8px] sm:text-[9px] uppercase tracking-wider">
                    <th className="py-1.5 px-2">Date</th>
                    <th className="py-1.5 px-2">Time IST</th>
                    <th className="py-1.5 px-2">Region</th>
                    <th className="py-1.5 px-2">Event Name</th>
                    <th className="py-1.5 px-2 text-center">Impact</th>
                    <th className="py-1.5 px-2 text-center">Status</th>
                    <th className="py-1.5 px-2 text-right hidden lg:table-cell">Previous</th>
                    <th className="py-1.5 px-2 text-right hidden lg:table-cell">Consensus</th>
                    <th className="py-1.5 px-2 text-right hidden lg:table-cell">Actual</th>
                  </tr>
                </thead>
                {upcomingEvents.length > 0 ? (
                  renderEventRows(upcomingEvents)
                ) : (
                  <tbody>
                    <tr>
                      <td colSpan={9} className="py-3 text-center text-[#707987] font-mono text-[9px] italic">
                        No upcoming events scheduled matching selected filters.
                      </td>
                    </tr>
                  </tbody>
                )}
              </table>
            </div>
          </div>

          {/* ── SECTION 2: COMPLETED EVENTS (RENDERED SECOND) ── */}
          {completedEvents.length > 0 && (
            <div className="space-y-1.5 min-w-0 pt-2 border-t border-[#191D23]">
              <div className="flex items-center justify-between border-b border-[#191D23] pb-1">
                <span className="font-bold text-[#707987] text-[10px] uppercase flex items-center gap-1.5">
                  <CheckCircle2 size={12} className="text-[#00C896]" />
                  COMPLETED EVENTS ({completedEvents.length})
                </span>
                <span className="text-[8px] text-[#707987]">Historical Telemetry</span>
              </div>

              <div className="overflow-x-auto min-w-0">
                <table className="w-full text-left table-auto">
                  <thead>
                    <tr className="border-b border-[#191D23] bg-[#0E1013] text-[#707987] text-[8px] sm:text-[9px] uppercase tracking-wider">
                      <th className="py-1.5 px-2">Date</th>
                      <th className="py-1.5 px-2">Time IST</th>
                      <th className="py-1.5 px-2">Region</th>
                      <th className="py-1.5 px-2">Event Name</th>
                      <th className="py-1.5 px-2 text-center">Impact</th>
                      <th className="py-1.5 px-2 text-center">Status</th>
                      <th className="py-1.5 px-2 text-right hidden lg:table-cell">Previous</th>
                      <th className="py-1.5 px-2 text-right hidden lg:table-cell">Consensus</th>
                      <th className="py-1.5 px-2 text-right hidden lg:table-cell">Actual</th>
                    </tr>
                  </thead>
                  {renderEventRows(completedEvents)}
                </table>
              </div>
            </div>
          )}
        </div>
      </Surface>
    </div>
  );
}

export default CalendarTab;
