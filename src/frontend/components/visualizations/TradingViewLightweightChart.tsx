import React, { useEffect, useRef, useState } from "react";
import { createChart, ColorType, CandlestickSeries, LineSeries } from "lightweight-charts";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { safeNumber, safeString, formatNumber, formatDate } from "../../utils/safeHelpers";
import { resolveSessionIdentity } from "../../utils/canonicalSemanticContract";
import { AlertTriangle, Layers } from "lucide-react";

export type ChartTimeframe = "1m" | "5m" | "15m" | "1H" | "1D";

export interface FormattedCandle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export function parseCandleTime(c: any): number | null {
  if (typeof c.timestamp === "number" && c.timestamp > 0) {
    return c.timestamp < 10000000000 ? c.timestamp : Math.floor(c.timestamp / 1000);
  }
  const rawStr = c.datetime || c.time;
  if (typeof rawStr === "string" && rawStr.length > 0) {
    if (rawStr.includes("T") || rawStr.includes("-")) {
      const parsed = Date.parse(rawStr);
      if (!isNaN(parsed)) return Math.floor(parsed / 1000);
    }
    if (rawStr.includes(":")) {
      const parts = rawStr.split(":").map(Number);
      if (parts.length >= 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
        const todayStr = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(new Date());
        const hStr = String(parts[0]).padStart(2, "0");
        const mStr = String(parts[1]).padStart(2, "0");
        const iso = `${todayStr}T${hStr}:${mStr}:00+05:30`;
        const parsed = Date.parse(iso);
        if (!isNaN(parsed)) return Math.floor(parsed / 1000);
      }
    }
  }
  return null;
}

export function aggregateCandlesByTimeframe(
  candles: any[],
  timeframe: ChartTimeframe,
  fallbackSpot: number
): FormattedCandle[] {
  const parsedItems: Array<{ timeSec: number; open: number; high: number; low: number; close: number }> = [];

  for (let i = 0; i < candles.length; i++) {
    const c = candles[i];
    const tSec = parseCandleTime(c);
    if (tSec == null) continue;
    const open = safeNumber(c.o ?? c.open, fallbackSpot);
    const high = Math.max(open, safeNumber(c.h ?? c.high, open));
    const low = Math.min(open, safeNumber(c.l ?? c.low, open));
    const close = safeNumber(c.c ?? c.close, open);
    parsedItems.push({ timeSec: tSec, open, high, low, close });
  }

  if (!parsedItems.length) return [];

  // Sort raw items by time ascending
  parsedItems.sort((a, b) => a.timeSec - b.timeSec);

  if (timeframe === "1m") {
    return parsedItems.map((item) => ({
      time: item.timeSec,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }));
  }

  const bucketMinutes = timeframe === "5m" ? 5 : timeframe === "15m" ? 15 : timeframe === "1H" ? 60 : 1440;
  const bucketMap = new Map<number, FormattedCandle>();

  for (const item of parsedItems) {
    const dateObj = new Date(item.timeSec * 1000);
    const istParts = new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Kolkata",
      hour: "numeric",
      minute: "numeric",
      hour12: false,
      year: "numeric",
      month: "numeric",
      day: "numeric",
    }).formatToParts(dateObj);

    let year = dateObj.getUTCFullYear();
    let month = dateObj.getUTCMonth();
    let day = dateObj.getUTCDate();
    let hour = dateObj.getUTCHours();
    let minute = dateObj.getUTCMinutes();

    for (const p of istParts) {
      if (p.type === "year") year = Number(p.value);
      if (p.type === "month") month = Number(p.value) - 1;
      if (p.type === "day") day = Number(p.value);
      if (p.type === "hour") hour = Number(p.value) % 24;
      if (p.type === "minute") minute = Number(p.value);
    }

    let bucketSec: number;
    if (timeframe === "1D") {
      const istMidnightIso = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}T00:00:00+05:30`;
      bucketSec = Math.floor(Date.parse(istMidnightIso) / 1000);
    } else {
      const minutesPastMidnight = hour * 60 + minute;
      const sessionStart = 9 * 60 + 15; // 09:15 IST = 555 min
      let bucketStartMin: number;
      if (minutesPastMidnight < sessionStart) {
        bucketStartMin = sessionStart;
      } else {
        const elapsed = minutesPastMidnight - sessionStart;
        const bucketIndex = Math.floor(elapsed / bucketMinutes);
        bucketStartMin = sessionStart + bucketIndex * bucketMinutes;
      }
      const bHour = Math.floor(bucketStartMin / 60);
      const bMin = bucketStartMin % 60;
      const bIso = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}T${String(bHour).padStart(2, "0")}:${String(bMin).padStart(2, "0")}:00+05:30`;
      bucketSec = Math.floor(Date.parse(bIso) / 1000);
    }

    const existing = bucketMap.get(bucketSec);
    if (!existing) {
      bucketMap.set(bucketSec, {
        time: bucketSec,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      });
    } else {
      existing.high = Math.max(existing.high, item.high);
      existing.low = Math.min(existing.low, item.low);
      existing.close = item.close;
    }
  }

  return Array.from(bucketMap.values()).sort((a, b) => a.time - b.time);
}

export function TradingViewLightweightChart({
  height = 360,
  embedded = false,
  timeframe = "15m",
}: {
  height?: number;
  embedded?: boolean;
  timeframe?: ChartTimeframe;
}) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<any>(null);
  const candlestickSeriesRef = useRef<any>(null);
  const vwapSeriesRef = useRef<any>(null);

  const { marketContext, canonicalState } = useWorkstationState() as any;
  const rawSpot = marketContext?.current_spot;
  const isAvailable = Boolean(rawSpot && marketContext?.last_tick_time);
  const spot = safeNumber(rawSpot, 0);
  const vwap = safeNumber(marketContext?.vwap, 0);
  const dq = canonicalState?.data_quality?.market_data || {};

  const [showVwap, setShowVwap] = useState(true);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#08090b" },
        textColor: "#707987",
        fontSize: 10,
        fontFamily: "'JetBrains Mono', monospace, sans-serif",
      },
      grid: {
        vertLines: { color: "#13161A", style: 1 },
        horzLines: { color: "#13161A", style: 1 },
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      localization: {
        timeFormatter: (timestamp: number) => {
          const d = new Date(timestamp * 1000);
          return new Intl.DateTimeFormat("en-IN", {
            timeZone: "Asia/Kolkata",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
            day: "2-digit",
            month: "short",
            year: "numeric",
          }).format(d);
        },
        dateFormat: "dd MMM yyyy",
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: "#191D23",
        tickMarkFormatter: (timestamp: number) => {
          const d = new Date(timestamp * 1000);
          return new Intl.DateTimeFormat("en-IN", {
            timeZone: "Asia/Kolkata",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          }).format(d);
        },
      },
      rightPriceScale: {
        borderColor: "#191D23",
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      crosshair: {
        vertLine: {
          color: "#38BDF8",
          width: 1,
          style: 3,
        },
        horzLine: {
          color: "#38BDF8",
          width: 1,
          style: 3,
        },
      },
    });

    chartInstanceRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#00C896",
      downColor: "#E5484D",
      borderVisible: false,
      wickUpColor: "#00C896",
      wickDownColor: "#E5484D",
    });
    candlestickSeriesRef.current = candleSeries;

    const vwapSeries = chart.addSeries(LineSeries, {
      color: "#E59700",
      lineWidth: 1,
      lineStyle: 2,
    });
    vwapSeriesRef.current = vwapSeries;

    const handleResize = () => {
      if (chartContainerRef.current && chartInstanceRef.current) {
        chartInstanceRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartInstanceRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!candlestickSeriesRef.current) return;

    const rawCandles = Array.isArray(marketContext?.candles) ? marketContext.candles : [];

    // Resolve target completed session date to filter candles strictly
    const sessionIdentity = resolveSessionIdentity(canonicalState, marketContext);
    const targetSessionDate = sessionIdentity.completedSessionDate;

    const filteredCandles = rawCandles.filter((c: any) => {
      const cTradeDate = c.trading_date || (typeof c.datetime === "string" ? c.datetime.slice(0, 10) : null);
      if (cTradeDate) {
        return cTradeDate === targetSessionDate;
      }
      const tSec = parseCandleTime(c);
      if (tSec != null) {
        const dStr = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(new Date(tSec * 1000));
        return dStr === targetSessionDate;
      }
      return true;
    });

    const activeCandles = filteredCandles.length > 0 ? filteredCandles : rawCandles;

    if (activeCandles.length > 0) {
      const aggregated = aggregateCandlesByTimeframe(activeCandles, timeframe, spot);
      candlestickSeriesRef.current.setData(aggregated);

      if (chartInstanceRef.current && aggregated.length > 0) {
        chartInstanceRef.current.timeScale().fitContent();
      }

      if (vwapSeriesRef.current && showVwap && vwap > 0) {
        const vwapData = aggregated.map((item) => ({
          time: item.time,
          value: vwap,
        }));
        vwapSeriesRef.current.setData(vwapData);
      } else if (vwapSeriesRef.current) {
        vwapSeriesRef.current.setData([]);
      }
    }
  }, [marketContext, canonicalState, spot, vwap, showVwap, timeframe]);

  if (!isAvailable) {
    return (
      <div className={`p-4 bg-[#08090B] space-y-1.5 text-left font-mono text-[11px] ${embedded ? "" : "rounded-lg border border-[#242830]"}`}>
        <div className="flex items-center gap-2 text-[#E59700] font-bold">
          <AlertTriangle size={14} />
          <span>NIFTY Intraday Chart Stream Idle</span>
        </div>
        <p className="text-[#707987] text-[10px]">
          No live NIFTY tick stream detected. Connect Kite broker or await session snapshot.
        </p>
      </div>
    );
  }

  if (embedded) {
    return (
      <div className="relative w-full overflow-hidden bg-[#08090B]">
        {vwap > 0 && (
          <div className="absolute top-2 right-2 z-10">
            <button
              onClick={() => setShowVwap(!showVwap)}
              className={`px-2 py-0.5 rounded-[2px] border text-[9px] font-mono font-semibold transition ${
                showVwap
                  ? "bg-[#E59700]/20 text-[#E59700] border-[#E59700]/40"
                  : "bg-[#0E1013] text-[#707987] border-[#242830]"
              }`}
            >
              VWAP ({formatNumber(vwap, 1)})
            </button>
          </div>
        )}
        <div ref={chartContainerRef} className="w-full" style={{ height: `${height}px` }} />
      </div>
    );
  }

  return (
    <div className="p-3 bg-[#0B0D10] border border-[#242830] rounded-[3px] space-y-2 text-left font-sans">
      <div className="flex flex-wrap justify-between items-center border-b border-[#191D23] pb-2 gap-2">
        <div className="flex items-center gap-2">
          <Layers size={14} className="text-[#38BDF8]" />
          <h3 className="font-bold text-[#E6E8EB] text-[11px] uppercase tracking-wider font-mono">
            NIFTY 50 Intraday Chart ({timeframe})
          </h3>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          {vwap > 0 && (
            <button
              onClick={() => setShowVwap(!showVwap)}
              className={`px-2 py-0.5 rounded border text-[9px] font-bold transition ${
                showVwap
                  ? "bg-[#E59700]/20 text-[#E59700] border-[#E59700]/40"
                  : "bg-[#0E1013] text-[#707987] border-[#242830]"
              }`}
            >
              VWAP ({formatNumber(vwap, 1)})
            </button>
          )}
          <span className="px-2 py-0.5 rounded bg-[#08090B] text-[#00C896] border border-[#242830] text-[9px] font-bold">
            Live Stream · {dq.observed_at ? formatDate(dq.observed_at) : "Active"}
          </span>
        </div>
      </div>

      <div className="relative w-full rounded-[2px] bg-[#08090B] border border-[#191D23] overflow-hidden">
        <div ref={chartContainerRef} className="w-full" style={{ height: `${height}px` }} />
      </div>
    </div>
  );
}
