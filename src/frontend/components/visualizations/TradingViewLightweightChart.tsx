import React, { useEffect, useRef, useState } from "react";
import { createChart, ColorType, CandlestickSeries, LineSeries } from "lightweight-charts";
import { useWorkstationState } from "../../context/WorkstationStateContext";
import { safeNumber, safeString, formatNumber, formatDate } from "../../utils/safeHelpers";
import { AlertTriangle, Layers } from "lucide-react";

interface FormattedCandle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export function TradingViewLightweightChart({ height = 340 }: { height?: number }) {
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
        background: { type: ColorType.Solid, color: "#0b0f19" },
        textColor: "#94a3b8",
        fontSize: 11,
        fontFamily: "'JetBrains Mono', monospace, sans-serif",
      },
      grid: {
        vertLines: { color: "#1e293b", style: 1 },
        horzLines: { color: "#1e293b", style: 1 },
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: "#334155",
      },
      rightPriceScale: {
        borderColor: "#334155",
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      crosshair: {
        vertLine: {
          color: "#0284c7",
          width: 1,
          style: 3,
        },
        horzLine: {
          color: "#0284c7",
          width: 1,
          style: 3,
        },
      },
    });

    chartInstanceRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });
    candlestickSeriesRef.current = candleSeries;

    const vwapSeries = chart.addSeries(LineSeries, {
      color: "#f59e0b",
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
    if (rawCandles.length > 0) {
      const formattedCandles: FormattedCandle[] = rawCandles.map((c: any, index: number) => {
        let timeVal: any = c.time || c.timestamp;
        if (typeof timeVal === "string" && timeVal.includes(":")) {
          const today = new Date();
          const [h, m] = timeVal.split(":").map(Number);
          today.setHours(h, m, 0, 0);
          timeVal = Math.floor(today.getTime() / 1000);
        } else if (typeof timeVal === "number" && timeVal < 10000000000) {
          timeVal = timeVal;
        } else {
          timeVal = Math.floor(Date.now() / 1000) - (rawCandles.length - index) * 300;
        }
        return {
          time: timeVal,
          open: safeNumber(c.o, spot),
          high: safeNumber(c.h, spot),
          low: safeNumber(c.l, spot),
          close: safeNumber(c.c, spot),
        };
      });

      const uniqueSorted: FormattedCandle[] = Array.from(
        new Map<number, FormattedCandle>(formattedCandles.map(item => [item.time, item])).values()
      ).sort((a, b) => a.time - b.time);

      candlestickSeriesRef.current.setData(uniqueSorted);

      if (vwapSeriesRef.current && showVwap && vwap > 0) {
        const vwapData = uniqueSorted.map(item => ({
          time: item.time,
          value: vwap,
        }));
        vwapSeriesRef.current.setData(vwapData);
      } else if (vwapSeriesRef.current) {
        vwapSeriesRef.current.setData([]);
      }
    }
  }, [marketContext, spot, vwap, showVwap]);

  if (!isAvailable) {
    return (
      <div className="p-5 bg-[var(--air-surface)] border border-[var(--air-line-strong)] rounded-xl space-y-2 text-left font-mono text-xs">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <AlertTriangle size={15} />
          <span>NIFTY Intraday Chart Unavailable</span>
        </div>
        <p className="text-slate-400 text-[11px]">
          No live NIFTY observation detected from canonical market feed. Connect Kite broker or await market snapshot.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-[var(--air-surface)] border border-[var(--air-line-strong)] rounded-xl space-y-3 text-left font-sans">
      <div className="flex flex-wrap justify-between items-center border-b border-slate-800/80 pb-2.5 gap-2">
        <div className="flex items-center gap-2">
          <Layers size={16} className="text-cyan-400" />
          <h3 className="font-bold text-white text-xs uppercase tracking-wider font-mono">
            NIFTY 50 Live Chart <span className="text-[9px] font-normal text-slate-400">(TradingView Lightweight)</span>
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          {vwap > 0 && (
            <button
              onClick={() => setShowVwap(!showVwap)}
              className={`px-2 py-0.5 rounded border text-[10px] font-bold transition ${
                showVwap ? "bg-amber-950/60 text-amber-400 border-amber-800" : "bg-slate-950 text-slate-500 border-slate-800"
              }`}
            >
              VWAP ({formatNumber(vwap, 1)})
            </button>
          )}
          <span className="px-2 py-0.5 rounded bg-slate-950 text-emerald-400 border border-slate-800 text-[10px] uppercase font-bold">
            Canonical Feed · {dq.observed_at ? formatDate(dq.observed_at) : "Live"}
          </span>
        </div>
      </div>

      <div className="relative w-full rounded-lg bg-slate-950 border border-slate-800 overflow-hidden">
        <div ref={chartContainerRef} className="w-full" style={{ height: `${height}px` }} />
      </div>
    </div>
  );
}
