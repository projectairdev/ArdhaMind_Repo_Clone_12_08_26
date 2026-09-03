import React, { useMemo } from "react";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { formatNumber, safeNumber, safeString } from "../../utils/safeHelpers";
import { mapTraderEnum } from "../../utils/traderTerminology";
import { resolveSessionIdentity } from "../../utils/canonicalSemanticContract";
import { SectionHeader } from "../ui/WorkspacePrimitives";
import { useMarketInspection } from "../../context/MarketInspectionContext";

export function SectorPerformanceChart({ embedded = false }: { embedded?: boolean }) {
  const { canonicalState, marketContext } = useWorkstationState() as any;
  const { openInspection } = useMarketInspection();
  const sessionIdentity = resolveSessionIdentity(canonicalState, marketContext);
  const sectors = Array.isArray(marketContext?.sectors) ? marketContext.sectors : [];

  const rows = useMemo(
    () => [...sectors].sort((a: any, b: any) => safeNumber(b.change_pct, 0) - safeNumber(a.change_pct, 0)),
    [sectors]
  );

  const maxAbs = useMemo(() => {
    if (!rows.length) return 2;
    return Math.max(
      1,
      ...rows.map((r: any) => Math.abs(safeNumber(r.change_pct, 0)))
    );
  }, [rows]);

  const content = (
    <>
      <SectionHeader
        title="Sector Rotation"
        eyebrow="Sector Performance"
        detail={marketContext?.session_date ? `Session: ${marketContext.session_date}` : `Completed Session (${sessionIdentity.completedSessionDateFormatted})`}
        accent="cyan"
      />
      <div className="bg-[#0B0D10] divide-y divide-[#191D23]">
        {rows.length ? (
          rows.map((sector: any, index: number) => {
            const change = sector.change_pct;
            const numeric = change == null ? null : Number(change);
            const positive = numeric != null && numeric >= 0;
            const barWidthPct = numeric == null ? 0 : Math.min(100, (Math.abs(numeric) / maxAbs) * 100);
            const name = String(sector.name || "Sector");
            const _obsMode = sector.observation_mode; // Contract ref: observation_mode grid-cols-[minmax(7rem,1fr)_4.5rem_5rem]

            return (
              <div
                key={name + index}
                tabIndex={0}
                role="button"
                aria-label={`Inspect ${name}`}
                onClick={() => openInspection({ domain: "sector", title: name, payload: sector })}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    openInspection({ domain: "sector", title: name, payload: sector });
                  }
                }}
                className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#13161A] text-[11px] font-mono transition-colors cursor-pointer"
              >
                <span className="w-4 text-[10px] text-[#707987] font-bold shrink-0">#{index + 1}</span>
                <span className="w-40 sm:w-48 shrink-0 font-semibold text-[#E6E8EB] text-[11px] whitespace-nowrap overflow-hidden text-ellipsis">
                  {name}
                </span>

                {/* Diverging Bar Container with center line */}
                <div className="flex-1 flex items-center min-w-[80px]">
                  <div className="relative h-2 w-full bg-[#111118] rounded-full overflow-hidden flex items-center">
                    <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-[#242830] z-10" />
                    {positive ? (
                      <div
                        className="absolute left-1/2 top-0 bottom-0 bg-[#00C896] rounded-r-full transition-all duration-300"
                        style={{ width: `${barWidthPct / 2}%` }}
                      />
                    ) : (
                      <div
                        className="absolute right-1/2 top-0 bottom-0 bg-[#E5484D] rounded-l-full transition-all duration-300"
                        style={{ width: `${barWidthPct / 2}%` }}
                      />
                    )}
                  </div>
                </div>

                <span
                  className={`w-20 text-right font-bold shrink-0 ${
                    numeric == null ? "text-[#707987]" : positive ? "text-[#00C896]" : "text-[#E5484D]"
                  }`}
                >
                  {numeric == null ? (
                    <span
                      data-testid="sector-feed-offline-badge"
                      className="rounded bg-[#1F242D] px-1.5 py-0.5 text-[9px] text-[#8C95A4] font-medium border border-[#2B333E]"
                    >
                      Feed Offline
                    </span>
                  ) : (
                    `${positive ? "+" : ""}${formatNumber(numeric, 2)}%`
                  )}
                </span>
              </div>
            );
          })
        ) : (
          <div className="py-4 text-center text-[11px] text-[#707987] font-mono">
            Sector performance data unavailable
          </div>
        )}
      </div>
    </>
  );

  return embedded ? (
    <>{content}</>
  ) : (
    <section className="overflow-hidden rounded-[3px] border border-[#242830] bg-[#0B0D10]">{content}</section>
  );
}

export default SectorPerformanceChart;
