/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Flagship Financial Trading Chart Engine (TradingView Lightweight Charts v5).
 * High-performance, institutional-grade candlestick charting workstation:
 * - Powered by TradingView Lightweight Charts (HTML5 Canvas high-DPI rendering)
 * - Focused View (Default rolling ~90–120m) & Fit Session (Full-day context)
 * - Visible-Range Y-Axis Autoscale (Distant levels do NOT distort vertical scale)
 * - Off-Screen Structural Level Badges (Floating edge indicators for Day H/L, OR H/L)
 * - Native Synchronized Activity / Volume Histogram (NIFTY 50 AGGREGATE ACTIVITY)
 * - Distinct Amber VWAP Line Series
 * - Proximity-Governed Structural Level Price Lines
 * - Interactive Crosshair with Instant Legend Bar Inspection
 * - High-Value Event Markers (ORH BREAK, VWAP HOLD, DAY HIGH TEST)
 * - Fullscreen Analyst Mode
 */

import React, { useState, useMemo, useRef, useEffect } from "react";
import {
  createChart,
  ColorType,
  LineStyle,
  CrosshairMode,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  createSeriesMarkers,
  UTCTimestamp,
  IChartApi,
  ISeriesApi,
  IPriceLine,
  MouseEventParams,
} from "lightweight-charts";
import {
  CanonicalCandle,
  CanonicalPriceStructure,
  MarketPhase,
  DataQualityStatus,
} from "../../../types/canonical";
import { useCanonicalState } from "../../../context/CanonicalStateContext";
import { SessionPhase, IntelligenceMode, DataWindow } from "../../../session/sessionPhaseEngine";
import {
  adaptCanonicalToChart,
} from "./chartAdapter";
import { formatNumber } from "../../../utils/safeHelpers";
import { calculateEMA, calculateVWAPAndBands } from "../../../utils/indicators";
import { resolveAuthoritativeMarketState } from "../../../utils/resolveAuthoritativeMarketState";
import {
  Maximize2,
  Minimize2,
  ArrowUpRight,
  ArrowDownRight,
  CandlestickChart,
} from "lucide-react";


export interface CanonicalTradingChartProps {
  candles: CanonicalCandle[];
  priceStructure: CanonicalPriceStructure;
  sessionDate: string;
  marketPhase: MarketPhase;
  currentPrice?: number | null;
  formingCandle?: CanonicalCandle | null;
  height?: number;
  quality?: DataQualityStatus;
  onTimeframeChange?: (tf: string) => void;
}

export function CanonicalTradingChart({
  candles = [],
  priceStructure,
  sessionDate,
  marketPhase,
  currentPrice,
  formingCandle,
  height = 560,
  quality = "VALID",
  onTimeframeChange,
}: CanonicalTradingChartProps) {
  let canonicalContext: any = null;
  try {
    canonicalContext = useCanonicalState();
  } catch {
    // Isolated tests where context is not mounted
  }

  const sessionIdentity = canonicalContext?.sessionIdentity;
  const activeSessionPhase: SessionPhase = sessionIdentity?.sessionPhase ?? (
    marketPhase === "POST_MARKET" || marketPhase === "MARKET_CLOSED" ? "POST_MARKET" :
    marketPhase === "PRE_MARKET" ? "PRE_MARKET" :
    marketPhase === "PRE_OPEN" ? "PRE_OPEN" :
    marketPhase === "NEAR_CLOSE" ? "NEAR_CLOSE" : "LIVE"
  );
  const activeIntelMode: IntelligenceMode = sessionIdentity?.intelligenceMode ?? (
    activeSessionPhase === "POST_MARKET" ? "OVERNIGHT_SYNTHESIS" :
    activeSessionPhase === "PRE_MARKET" ? "PRE_COMMIT_PLAN" :
    activeSessionPhase === "PRE_OPEN" ? "AUCTION_READ" :
    activeSessionPhase === "NEAR_CLOSE" ? "DECISION_WINDOW" : "REGIME_MONITOR"
  );
  const activeDataWindow: DataWindow = sessionIdentity?.data_window ?? (
    activeSessionPhase === "POST_MARKET" || activeSessionPhase === "PRE_MARKET" ? "SETTLED_COMPLETED" :
    activeSessionPhase === "PRE_OPEN" ? "PRE_OPEN_AUCTION" : "SESSION_SO_FAR"
  );
  const isReplayMode: boolean = sessionIdentity?.is_replay_mode ?? (
    activeSessionPhase === "POST_MARKET" || activeSessionPhase === "PRE_MARKET"
  );

  const isLiveTape = activeSessionPhase === "LIVE" || activeSessionPhase === "NEAR_CLOSE";
  const isPostReview = activeSessionPhase === "POST_MARKET" || activeDataWindow === "SETTLED_COMPLETED" || activeIntelMode === "OVERNIGHT_SYNTHESIS" || activeIntelMode === "CLOSE_TRANSFER";
  const isPreMarketBaseline = activeSessionPhase === "PRE_MARKET" || activeIntelMode === "PRE_COMMIT_PLAN";
  const isPreOpenAuction = activeSessionPhase === "PRE_OPEN" || activeIntelMode === "AUCTION_READ";
  const isOpenValidation = activeIntelMode === "OPEN_VALIDATION";

  // Automatic Viewport and TF Selection based on Session/Intel Mode
  const defaultViewMode = (isPostReview || isPreMarketBaseline) ? "FIT_SESSION" : "FOCUS";
  const defaultTf = (isPostReview || isPreMarketBaseline) ? "5m" : "1m";

  const [selectedTf, setSelectedTf] = useState<string>(defaultTf);
  const [userOverrodeTf, setUserOverrodeTf] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<"FOCUS" | "FIT_SESSION">(defaultViewMode);
  const [userOverrodeViewMode, setUserOverrodeViewMode] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // Sync mode changes when session identity changes (unless user explicitly interacted)
  useEffect(() => {
    if (!userOverrodeViewMode) {
      setViewMode((isPostReview || isPreMarketBaseline) ? "FIT_SESSION" : "FOCUS");
    }
  }, [isPostReview, isPreMarketBaseline, userOverrodeViewMode]);

  useEffect(() => {
    if (!userOverrodeTf) {
      setSelectedTf((isPostReview || isPreMarketBaseline) ? "5m" : "1m");
    }
  }, [isPostReview, isPreMarketBaseline, userOverrodeTf]);

  // Dynamic Strategic Layer Toggles
  const [showLevels, setShowLevels] = useState<boolean>(false); // Secondary levels off by default
  const [showVwap, setShowVwap] = useState<boolean>(true);      // Core decision line
  const [showBands, setShowBands] = useState<boolean>(false);   // ±1σ, ±2σ Volatility Corridors
  const [showWalls, setShowWalls] = useState<boolean>(false);   // Options Strike Walls
  const [showEmas, setShowEmas] = useState<boolean>(false);     // 9 & 21 EMAs
  const [showActivity, setShowActivity] = useState<boolean>(true);
  const [showEvents, setShowEvents] = useState<boolean>(false); // Quiet by default (toggleable)

  // Active Candle Inspection / Crosshair State
  const [inspectedCandle, setInspectedCandle] = useState<{
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    isBullish: boolean;
  } | null>(null);

  // Chart Container and Instances Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const vwapSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const upper1SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const lower1SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const upper2SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const lower2SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const ema9SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const activitySeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const markersPrimitiveRef = useRef<any>(null);
  const priceLinesRef = useRef<IPriceLine[]>([]);
  const lastRenderedTfRef = useRef<string | null>(null);
  const lastRenderedSessionRef = useRef<string | null>(null);
  const lastRenderedCountRef = useRef<number>(0);
  const prevShowVwapRef = useRef<boolean>(showVwap);
  const prevShowBandsRef = useRef<boolean>(showBands);
  const prevShowEmasRef = useRef<boolean>(showEmas);
  const prevShowActivityRef = useRef<boolean>(showActivity);

  // Adapt Canonical Data
  const chartModel = useMemo(() => {
    return adaptCanonicalToChart(candles, priceStructure, sessionDate, marketPhase, formingCandle, selectedTf);
  }, [candles, priceStructure, sessionDate, marketPhase, formingCandle, selectedTf]);

  const rawCandles = chartModel.candles;
  const totalCandles = rawCandles.length;

  // Dynamic Options Strike Walls & Official Settlement Values
  const envelope = canonicalContext?.envelope;
  const authState = resolveAuthoritativeMarketState(envelope);
  const optionsIntel = envelope?.options_intelligence ?? envelope?.option_chain ?? envelope?.options;
  const callWall = optionsIntel?.call_wall ?? null;
  const putWall = optionsIntel?.put_wall ?? null;
  const maxPain = optionsIntel?.max_pain ?? null;
  const settledClosePrice = envelope?.settled_session?.close ?? null;
  const settledVwapPrice = envelope?.settled_session?.vwap ?? null;

  // Key Structural Level Values (Pure canonical binding, no literals)
  const dayHigh = priceStructure.high ?? authState.dayHigh ?? null;
  const dayLow = priceStructure.low ?? authState.dayLow ?? null;
  const orHigh = priceStructure.or_high ?? null;
  const orLow = priceStructure.or_low ?? null;
  const openVal = priceStructure.open ?? authState.dayOpen ?? null;
  const prevCloseVal = priceStructure.previous_close ?? authState.prevClose ?? null;
  const vwapVal = authState.vwap ?? priceStructure.vwap ?? null;
  const effectivePrice = currentPrice ?? priceStructure.last_price ?? authState.spot ?? null;
  const priceVsVwap = (effectivePrice != null && vwapVal != null) ? effectivePrice - vwapVal : null;
  const priceVsVwapPct = (priceVsVwap != null && vwapVal != null && vwapVal !== 0) ? (priceVsVwap / vwapVal) * 100 : null;

  // Compute Active / Visible Window Range for Focus View vs Fit Session
  const focusWindowCandles = useMemo(() => {
    if (totalCandles <= 60) return rawCandles;
    // Focus View displays last 100 candles (~1.7 hours of active trading)
    return rawCandles.slice(Math.max(0, totalCandles - 100));
  }, [rawCandles, totalCandles]);

  const visibleMinMax = useMemo(() => {
    const targetSet = viewMode === "FOCUS" ? focusWindowCandles : rawCandles;
    if (targetSet.length === 0) return { min: 24400, max: 24650 };
    const min = Math.min(...targetSet.map((c) => c.low));
    const max = Math.max(...targetSet.map((c) => c.high));
    return { min, max };
  }, [viewMode, focusWindowCandles, rawCandles]);

  // Compute Off-Screen Structural Level Badges (Distant levels rendered on chart perimeter)
  const { offScreenAbove, offScreenBelow } = useMemo(() => {
    const above: { id: string; label: string; price: number; delta: number; color: string }[] = [];
    const below: { id: string; label: string; price: number; delta: number; color: string }[] = [];

    // Proximity margin: levels outside visibleMinMax + margin are marked off-screen
    const margin = (visibleMinMax.max - visibleMinMax.min) * 0.05;
    const effectiveMin = visibleMinMax.min - margin;
    const effectiveMax = visibleMinMax.max + margin;

    // Check Day / OR High Collision
    const isSoFar = activeDataWindow === "SESSION_SO_FAR" || (!isPostReview && !isPreMarketBaseline);
    if (dayHigh && orHigh && Math.abs(dayHigh - orHigh) < 0.5) {
      if (dayHigh > effectiveMax) {
        above.push({
          id: "day_or_high",
          label: isSoFar ? "DAY / OR HIGH (SO FAR)" : "DAY / OR HIGH",
          price: dayHigh,
          delta: dayHigh - (effectivePrice ?? 0),
          color: "#38BDF8",
        });
      }
    } else {
      if (dayHigh && dayHigh > effectiveMax) {
        above.push({
          id: "day_high",
          label: isSoFar ? "DAY HIGH (SO FAR)" : "DAY HIGH",
          price: dayHigh,
          delta: dayHigh - (effectivePrice ?? 0),
          color: "#00C896",
        });
      }
      if (orHigh && orHigh > effectiveMax) {
        above.push({
          id: "orh",
          label: isSoFar ? "OR HIGH (SO FAR)" : "OR HIGH",
          price: orHigh,
          delta: orHigh - (effectivePrice ?? 0),
          color: "#00C896",
        });
      }
    }

    // Check Day / OR Low Collision
    if (dayLow && orLow && Math.abs(dayLow - orLow) < 0.5) {
      if (dayLow < effectiveMin) {
        below.push({
          id: "day_or_low",
          label: isSoFar ? "DAY / OR LOW (SO FAR)" : "DAY / OR LOW",
          price: dayLow,
          delta: dayLow - (effectivePrice ?? 0),
          color: "#38BDF8",
        });
      }
    } else {
      if (dayLow && dayLow < effectiveMin) {
        below.push({
          id: "day_low",
          label: isSoFar ? "DAY LOW (SO FAR)" : "DAY LOW",
          price: dayLow,
          delta: dayLow - (effectivePrice ?? 0),
          color: "#EF4444",
        });
      }
      if (orLow && orLow < effectiveMin) {
        below.push({
          id: "orl",
          label: "OR LOW",
          price: orLow,
          delta: orLow - (effectivePrice ?? 0),
          color: "#EF4444",
        });
      }
    }

    // Check Prev Close
    if (showLevels && prevCloseVal && (prevCloseVal > effectiveMax || prevCloseVal < effectiveMin)) {
      (prevCloseVal > effectiveMax ? above : below).push({
        id: "prev_close",
        label: "PREV CLOSE",
        price: prevCloseVal,
        delta: prevCloseVal - (effectivePrice ?? 0),
        color: "#8B949E",
      });
    }

    return { offScreenAbove: above, offScreenBelow: below };
  }, [dayHigh, dayLow, orHigh, orLow, prevCloseVal, showLevels, visibleMinMax, effectivePrice]);

  // Convert raw candles to Lightweight Charts format with strict integer Unix seconds, deduplication, and ascending sorting
  const chartData = useMemo(() => {
    const stepSeconds = selectedTf === "3m" ? 180 : selectedTf === "5m" ? 300 : selectedTf === "15m" ? 900 : (selectedTf === "1h" || selectedTf === "1H" || selectedTf === "60m") ? 3600 : selectedTf === "1D" ? 86400 : 60;
    const candleMap = new Map<number, (typeof rawCandles)[0]>();
    const now = new Date();
    const dynamicBaseEpoch = Math.floor(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), 3, 45, 0)).getTime() / 1000);

    rawCandles.forEach((c, i) => {
      let timeSec: number;
      if (c.time && (typeof c.time === "number" || !isNaN(Number(c.time)))) {
        const num = Number(c.time);
        timeSec = num > 10000000000 ? Math.floor(num / 1000) : num;
      } else if (c.time && (c.time.includes("T") || c.time.includes(" "))) {
        const d = new Date(c.time);
        const parsed = Math.floor(d.getTime() / 1000);
        timeSec = !isNaN(parsed) && parsed > 0 ? parsed : (dynamicBaseEpoch + i * stepSeconds);
      } else {
        timeSec = dynamicBaseEpoch + i * stepSeconds;
      }
      candleMap.set(timeSec, c);
    });

    const sortedTimes = Array.from(candleMap.keys()).sort((a, b) => a - b);
    return sortedTimes.map((t) => {
      const c = candleMap.get(t)!;
      return {
        time: t as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
        volume: c.volume,
        displayTime: c.displayTime,
      };
    });
  }, [rawCandles, selectedTf]);

  // Technical Indicators: EMAs, Authentic Cumulative VWAP, and Dynamic Standard Deviation Bands
  const { ema9Data, ema21Data, vwapCalculatedData, upper1Data, lower1Data, upper2Data, lower2Data } = useMemo(() => {
    if (chartData.length === 0) {
      return {
        ema9Data: [],
        ema21Data: [],
        vwapCalculatedData: [],
        upper1Data: [],
        lower1Data: [],
        upper2Data: [],
        lower2Data: [],
      };
    }

    const ema9 = calculateEMA(chartData, 9);
    const ema21 = calculateEMA(chartData, 21);
    const bands = calculateVWAPAndBands(chartData, vwapVal);

    return {
      ema9Data: ema9,
      ema21Data: ema21,
      vwapCalculatedData: bands.vwapSeries,
      upper1Data: bands.upper1Series,
      lower1Data: bands.lower1Series,
      upper2Data: bands.upper2Series,
      lower2Data: bands.lower2Series,
    };
  }, [chartData, vwapVal]);

  // Activity / Volume Histogram Data Points (TradingView Translucent Palette)
  const activityData = useMemo(() => {
    return chartData.map((d) => ({
      time: d.time,
      value: d.volume || 0,
      color: d.close >= d.open ? "rgba(8, 153, 129, 0.4)" : "rgba(242, 54, 69, 0.4)",
    }));
  }, [chartData]);

  // High-Value Event Markers (ORH BREAK, VWAP HOLD, DAY HIGH TEST)
  const eventMarkers = useMemo(() => {
    if (!showEvents || chartModel.events.length === 0 || chartData.length === 0) return [];
    return chartModel.events.slice(-3).map((evt) => {
      const c = chartData[Math.min(chartData.length - 1, evt.candleIndex)] || chartData[0];
      return {
        time: c.time,
        position: evt.direction === "UP" ? ("belowBar" as const) : ("aboveBar" as const),
        color: "#38BDF8",
        shape: evt.direction === "UP" ? ("arrowUp" as const) : ("arrowDown" as const),
        text: evt.label,
      };
    });
  }, [showEvents, chartModel.events, chartData]);

  // 1. Initialize Lightweight Charts on Mount
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#0B0E14" },
        textColor: "#848E9C",
        fontSize: 11,
        fontFamily: "JetBrains Mono, Menlo, ui-monospace, SFMono-Regular, Monaco, Consolas, monospace",
      },
      grid: {
        vertLines: { color: "rgba(43, 43, 67, 0.3)", style: LineStyle.Dotted },
        horzLines: { color: "rgba(43, 43, 67, 0.3)", style: LineStyle.Dotted },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "#758696",
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: "#1E232B",
        },
        horzLine: {
          color: "#758696",
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: "#1E232B",
        },
      },
      rightPriceScale: {
        borderColor: "#2B2B43",
        scaleMargins: {
          top: 0.08,    // 8% margin at top
          bottom: 0.22, // 22% margin at bottom (leaves clear space for volume)
        },
        autoScale: true,
      },
      localization: {
        locale: "en-IN",
        timeFormatter: (time: number) => {
          const date = new Date(time * 1000);
          return new Intl.DateTimeFormat("en-IN", {
            timeZone: "Asia/Kolkata",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          }).format(date);
        },
      },
      timeScale: {
        rightOffset: 5,
        barSpacing: 12,              // Generous bar width so candles breathe
        minBarSpacing: 6,
        fixLeftEdge: true,           // Pins the first candle (09:15) to the left edge
        fixRightEdge: true,          // Pins the last candle (15:30) to the right edge
        lockVisibleTimeRangeOnResize: true,
        timeVisible: true,
        secondsVisible: false,
        borderVisible: true,
        borderColor: "#2B2B43",
        tickMarkFormatter: (time: number) => {
          const date = new Date(time * 1000);
          return new Intl.DateTimeFormat("en-IN", {
            timeZone: "Asia/Kolkata",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          }).format(date);
        },
      },
      handleScroll: true,
      handleScale: true,
    });

    // Add Candlestick Series (TradingView Standard Colors)
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#089981",          // TradingView standard emerald
      downColor: "#F23645",        // TradingView standard coral red
      borderVisible: true,
      borderUpColor: "#089981",
      borderDownColor: "#F23645",
      wickUpColor: "#089981",
      wickDownColor: "#F23645",
      priceLineVisible: true,
      priceLineColor: "#089981",
      priceLineWidth: 1,
      priceLineStyle: LineStyle.Dotted,
      title: "",
    });

    // Add VWAP Series
    const vwapSeries = chart.addSeries(LineSeries, {
      color: "#EAB308",
      lineWidth: 2,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      title: "VWAP",
    });

    // Add Bands Series (±1σ, ±2σ)
    const upper1Series = chart.addSeries(LineSeries, {
      color: "rgba(56, 189, 248, 0.45)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      title: "+1σ",
    });

    const lower1Series = chart.addSeries(LineSeries, {
      color: "rgba(56, 189, 248, 0.45)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      title: "-1σ",
    });

    const upper2Series = chart.addSeries(LineSeries, {
      color: "rgba(245, 158, 11, 0.45)",
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      title: "+2σ",
    });

    const lower2Series = chart.addSeries(LineSeries, {
      color: "rgba(245, 158, 11, 0.45)",
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      title: "-2σ",
    });

    // Add 9 & 21 EMA Series
    const ema9Series = chart.addSeries(LineSeries, {
      color: "#38BDF8",
      lineWidth: 1,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      title: "9 EMA",
    });

    const ema21Series = chart.addSeries(LineSeries, {
      color: "#F59E0B",
      lineWidth: 1,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      title: "21 EMA",
    });

    // Add Synchronized Activity / Volume Histogram Series (Isolated scale, bottom 18%)
    const activitySeries = chart.addSeries(HistogramSeries, {
      priceScaleId: "volume",
      priceFormat: {
        type: "volume",
      },
      priceLineVisible: false,
      lastValueVisible: false,
      baseLineVisible: false,
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: {
        top: 0.82,    // Starts at 82% height
        bottom: 0.0,  // Anchored strictly to bottom edge
      },
    });

    // Crosshair inspection listener
    chart.subscribeCrosshairMove((param: MouseEventParams) => {
      if (!param.time || !param.seriesData) {
        setInspectedCandle(null);
        return;
      }
      const data = param.seriesData.get(candleSeries) as any;
      if (data && typeof data.close === "number") {
        const actData = param.seriesData.get(activitySeries) as any;
        const matching = chartData.find((c) => c.time === param.time);
        setInspectedCandle({
          time: matching?.displayTime || "15:30",
          open: data.open,
          high: data.high,
          low: data.low,
          close: data.close,
          volume: actData?.value || matching?.volume || 0,
          isBullish: data.close >= data.open,
        });
      }
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    vwapSeriesRef.current = vwapSeries;
    upper1SeriesRef.current = upper1Series;
    lower1SeriesRef.current = lower1Series;
    upper2SeriesRef.current = upper2Series;
    lower2SeriesRef.current = lower2Series;
    ema9SeriesRef.current = ema9Series;
    ema21SeriesRef.current = ema21Series;
    activitySeriesRef.current = activitySeries;

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        requestAnimationFrame(() => {
          if (containerRef.current && chartRef.current) {
            const width = containerRef.current.clientWidth;
            const height = containerRef.current.clientHeight;
            if (width > 0 && height > 0) {
              chartRef.current.applyOptions({
                width,
                height,
              });
            }
          }
        });
      }
    };

    // Immediate initial sizing
    handleResize();

    let resizeObserver: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined" && containerRef.current) {
      resizeObserver = new ResizeObserver(() => {
        handleResize();
      });
      resizeObserver.observe(containerRef.current);
    }
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      if (markersPrimitiveRef.current) {
        try {
          if (typeof markersPrimitiveRef.current.detach === "function") {
            markersPrimitiveRef.current.detach();
          }
        } catch {
          // ignore cleanup errors
        }
        markersPrimitiveRef.current = null;
      }
      chart.remove();
      chartRef.current = null;
    };
  }, []);

  // 2. Push Incremental / Updated Data to Series
  useEffect(() => {
    if (!candleSeriesRef.current || !vwapSeriesRef.current || !activitySeriesRef.current) return;

    const isFullReload =
      lastRenderedTfRef.current !== selectedTf ||
      lastRenderedSessionRef.current !== sessionDate ||
      prevShowVwapRef.current !== showVwap ||
      prevShowBandsRef.current !== showBands ||
      prevShowEmasRef.current !== showEmas ||
      prevShowActivityRef.current !== showActivity ||
      lastRenderedCountRef.current === 0 ||
      chartData.length === 0 ||
      chartData.length < lastRenderedCountRef.current ||
      chartData.length > lastRenderedCountRef.current + 1;

    if (isFullReload) {
      candleSeriesRef.current.setData(chartData as any);
      vwapSeriesRef.current.setData(showVwap ? (vwapCalculatedData as any) : []);
      upper1SeriesRef.current?.setData(showBands ? (upper1Data as any) : []);
      lower1SeriesRef.current?.setData(showBands ? (lower1Data as any) : []);
      upper2SeriesRef.current?.setData(showBands ? (upper2Data as any) : []);
      lower2SeriesRef.current?.setData(showBands ? (lower2Data as any) : []);
      ema9SeriesRef.current?.setData(showEmas ? (ema9Data as any) : []);
      ema21SeriesRef.current?.setData(showEmas ? (ema21Data as any) : []);
      activitySeriesRef.current.setData(showActivity ? (activityData as any) : []);

      lastRenderedTfRef.current = selectedTf;
      lastRenderedSessionRef.current = sessionDate;
      lastRenderedCountRef.current = chartData.length;
      prevShowVwapRef.current = showVwap;
      prevShowBandsRef.current = showBands;
      prevShowEmasRef.current = showEmas;
      prevShowActivityRef.current = showActivity;

      // Apply View Mode viewport on full reload
      if (chartRef.current && chartData.length > 0) {
        if (viewMode === "FOCUS") {
          const visibleBars = Math.min(chartData.length, 100);
          chartRef.current.timeScale().setVisibleLogicalRange({
            from: chartData.length - visibleBars,
            to: chartData.length + 5,
          });
        } else {
          chartRef.current.timeScale().fitContent();
        }
      }
    } else {
      // Incremental tick update: use .update() with latest in-progress candle and overlays
      // If a new candle just opened (count increased by 1), ensure previous bar is confirmed
      if (chartData.length === lastRenderedCountRef.current + 1 && chartData.length >= 2) {
        const prevCandle = chartData[chartData.length - 2];
        candleSeriesRef.current.update(prevCandle as any);
        if (showVwap && vwapCalculatedData.length >= 2) {
          vwapSeriesRef.current.update(vwapCalculatedData[vwapCalculatedData.length - 2] as any);
        }
        if (showBands && upper1Data.length >= 2) {
          upper1SeriesRef.current?.update(upper1Data[upper1Data.length - 2] as any);
          lower1SeriesRef.current?.update(lower1Data[lower1Data.length - 2] as any);
          upper2SeriesRef.current?.update(upper2Data[upper2Data.length - 2] as any);
          lower2SeriesRef.current?.update(lower2Data[lower2Data.length - 2] as any);
        }
        if (showEmas && ema9Data.length >= 2) {
          ema9SeriesRef.current?.update(ema9Data[ema9Data.length - 2] as any);
          ema21SeriesRef.current?.update(ema21Data[ema21Data.length - 2] as any);
        }
        if (showActivity && activityData.length >= 2) {
          activitySeriesRef.current.update(activityData[activityData.length - 2] as any);
        }
      }

      // Update current in-progress candle and overlays
      const lastCandle = chartData[chartData.length - 1];
      if (lastCandle) {
        candleSeriesRef.current.update(lastCandle as any);
        if (showVwap && vwapCalculatedData.length > 0) {
          vwapSeriesRef.current.update(vwapCalculatedData[vwapCalculatedData.length - 1] as any);
        }
        if (showBands && upper1Data.length > 0) {
          upper1SeriesRef.current?.update(upper1Data[upper1Data.length - 1] as any);
          lower1SeriesRef.current?.update(lower1Data[lower1Data.length - 1] as any);
          upper2SeriesRef.current?.update(upper2Data[upper2Data.length - 1] as any);
          lower2SeriesRef.current?.update(lower2Data[lower2Data.length - 1] as any);
        }
        if (showEmas && ema9Data.length > 0) {
          ema9SeriesRef.current?.update(ema9Data[ema9Data.length - 1] as any);
          ema21SeriesRef.current?.update(ema21Data[ema21Data.length - 1] as any);
        }
        if (showActivity && activityData.length > 0) {
          activitySeriesRef.current.update(activityData[activityData.length - 1] as any);
        }
        lastRenderedCountRef.current = chartData.length;
      }
    }

    // Fail-safe Event Markers using Lightweight Charts v5 createSeriesMarkers Primitive
    try {
      if (candleSeriesRef.current) {
        if (!markersPrimitiveRef.current) {
          if (typeof createSeriesMarkers === "function") {
            markersPrimitiveRef.current = createSeriesMarkers(
              candleSeriesRef.current,
              eventMarkers
            );
          }
        } else {
          if (typeof markersPrimitiveRef.current.setMarkers === "function") {
            markersPrimitiveRef.current.setMarkers(eventMarkers);
          }
        }
      }
    } catch (err) {
      console.warn("Chart event markers initialization failed (non-fatal):", err);
    }
  }, [
    chartData,
    vwapCalculatedData,
    upper1Data,
    lower1Data,
    upper2Data,
    lower2Data,
    ema9Data,
    ema21Data,
    activityData,
    eventMarkers,
    viewMode,
    selectedTf,
    sessionDate,
    showVwap,
    showBands,
    showEmas,
    showActivity,
  ]);


  // 3. Render Nearby Proximity Price Lines, Strike Walls & Settlement References
  useEffect(() => {
    if (!candleSeriesRef.current) return;

    // Clear previous price lines
    priceLinesRef.current.forEach((pl) => {
      candleSeriesRef.current?.removePriceLine(pl);
    });
    priceLinesRef.current = [];

    // Proximity margin around visible range
    const margin = (visibleMinMax.max - visibleMinMax.min) * 0.15;
    const minProximity = visibleMinMax.min - margin;
    const maxProximity = visibleMinMax.max + margin;

    const addIfNearby = (price: number, label: string, color: string, style: LineStyle = LineStyle.Dashed, width: 1 | 2 = 1) => {
      if (price >= minProximity && price <= maxProximity) {
        const pl = candleSeriesRef.current?.createPriceLine({
          price,
          color,
          lineWidth: width,
          lineStyle: style,
          axisLabelVisible: true,
          title: label,
        });
        if (pl) priceLinesRef.current.push(pl);
      }
    };

    // Primary Core Lines (When nearby)
    if (dayHigh) addIfNearby(dayHigh, "DAY HIGH", "#00C896");
    if (dayLow) addIfNearby(dayLow, "DAY LOW", "#EF4444");
    if (orHigh && Math.abs(orHigh - (dayHigh ?? 0)) > 0.5) addIfNearby(orHigh, "OR HIGH", "#38BDF8");
    if (orLow && Math.abs(orLow - (dayLow ?? 0)) > 0.5) addIfNearby(orLow, "OR LOW", "#38BDF8");

    // Secondary Overlays (When Levels enabled)
    if (showLevels) {
      if (openVal) addIfNearby(openVal, "OPEN", "#38BDF8");
      if (prevCloseVal) addIfNearby(prevCloseVal, "PREV CLOSE", "#8B949E", LineStyle.Dotted);
      if (priceStructure.key_resistances?.[0]) {
        addIfNearby(priceStructure.key_resistances[0], "IMM RES", "#EF4444");
      }
      if (priceStructure.key_supports?.[0]) {
        addIfNearby(priceStructure.key_supports[0], "IMM SUP", "#00C896");
      }
    }

    // Walls: Dynamic Options Strike Levels (When Walls enabled)
    if (showWalls) {
      if (callWall != null) {
        addIfNearby(callWall, `CALL WALL ${callWall}`, "#EF4444", LineStyle.Solid, 2);
      }
      if (putWall != null) {
        addIfNearby(putWall, `PUT WALL ${putWall}`, "#00C896", LineStyle.Solid, 2);
      }
      if (maxPain != null) {
        addIfNearby(maxPain, `MAX PAIN ${maxPain}`, "#8B5CF6", LineStyle.Dashed, 1);
      }
    }

    // Official Settled Session Close Reference Line
    if (settledClosePrice != null && (isPostReview || isPreMarketBaseline)) {
      addIfNearby(settledClosePrice, "SETTLED CLOSE", "#26a69a", LineStyle.Dashed, 1);
    }

    // Official Settled VWAP Reference Line (When off-market/baseline)
    if (settledVwapPrice != null && (isPostReview || isPreMarketBaseline) && showVwap) {
      addIfNearby(settledVwapPrice, "SETTLED VWAP", "#F59E0B", LineStyle.Dotted, 1);
    }
  }, [
    dayHigh,
    dayLow,
    orHigh,
    orLow,
    openVal,
    prevCloseVal,
    showLevels,
    showWalls,
    showVwap,
    callWall,
    putWall,
    maxPain,
    settledClosePrice,
    settledVwapPrice,
    visibleMinMax,
    priceStructure?.key_resistances,
    priceStructure?.key_supports,
    activeDataWindow,
    isPostReview,
    isPreMarketBaseline,
  ]);

  // 4. Timeframe change handler
  const handleTfChange = (tf: string) => {
    setUserOverrodeTf(true);
    setSelectedTf(tf);
    onTimeframeChange?.(tf);
    requestAnimationFrame(() => {
      if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
      }
    });
  };

  const handleViewModeChange = (mode: "FOCUS" | "FIT_SESSION") => {
    setUserOverrodeViewMode(true);
    setViewMode(mode);
    if (chartRef.current && chartData.length > 0) {
      if (mode === "FOCUS") {
        const visibleBars = Math.min(chartData.length, 60);
        chartRef.current.timeScale().setVisibleLogicalRange({
          from: chartData.length - visibleBars,
          to: chartData.length + 5,
        });
      } else {
        chartRef.current.timeScale().fitContent();
      }
    }
  };

  // Active Candle for Inspection (Defaults to completed closing candle on idle)
  const defaultLast = chartData[chartData.length - 1] || {
    time: undefined,
    open: openVal ?? null,
    high: dayHigh ?? null,
    low: dayLow ?? null,
    close: effectivePrice ?? null,
    volume: null,
    displayTime: (isPostReview || isPreMarketBaseline) ? "15:30" : "09:15",
  };

  const seriesEndTime = useMemo(() => {
    if (chartData.length === 0) return null;
    const last = chartData[chartData.length - 1];
    return last.displayTime;
  }, [chartData]);

  const isMidSessionSnapshot = useMemo(() => {
    if (!seriesEndTime) return false;
    return (
      chartData.length < 375 &&
      seriesEndTime < "15:29" &&
      (isLiveTape || isReplayMode)
    );
  }, [seriesEndTime, chartData.length, isLiveTape, isReplayMode]);

  const chartModeLabel = useMemo(() => {
    if (activeSessionPhase === "PRE_MARKET") return "PRE-MARKET BASELINE";
    if (activeSessionPhase === "PRE_OPEN") return "PRE-OPEN AUCTION";
    if (isOpenValidation) return "1m · OPEN VALIDATION";
    if (isPostReview) return `${selectedTf} · POST REVIEW`;
    if (isMidSessionSnapshot) {
      return `${selectedTf} · ${isLiveTape && !isReplayMode ? "LIVE" : "REPLAY"} · AS OF ${seriesEndTime} IST`;
    }
    if (isLiveTape && isReplayMode) return `${selectedTf} · REPLAY`;
    if (isLiveTape) return `${selectedTf} · LIVE`;
    return `${selectedTf} · BASELINE`;
  }, [activeSessionPhase, isOpenValidation, isPostReview, isLiveTape, isReplayMode, selectedTf, isMidSessionSnapshot, seriesEndTime]);

  return (
    <div
      className={`flex flex-col rounded-[2px] border border-[#1E232B] bg-[#08090B] font-mono overflow-hidden select-none transition-all ${
        isFullscreen ? "fixed inset-0 z-50 p-2 shadow-2xl bg-[#08090B]" : "h-full w-full"
      }`}
      style={{ minHeight: isFullscreen ? "100vh" : `${height}px` }}
    >
      {/* 1. TOP CHART TOOLBAR: Single-Row Consolidated Controls */}
      <div className="flex flex-wrap items-center justify-between border-b border-[#1C2128] px-2.5 py-1 bg-[#0E1013] text-xs">
        <div className="flex items-center gap-2 sm:gap-2.5 flex-wrap">
          {/* Timeframe Selector */}
          <div className="flex items-center gap-0.5 bg-[#14181F] rounded-[2px] p-0.5 border border-[#20252E]">
            {["1m", "3m", "5m", "15m", "1h", "1D"].map((tf) => (
              <button
                key={tf}
                onClick={() => handleTfChange(tf)}
                className={`px-1.5 py-0.2 rounded-[2px] text-[9.5px] font-bold transition-all ${
                  selectedTf === tf
                    ? "bg-[#38BDF8] text-[#050607]"
                    : "text-[#8B949E] hover:text-[#E6E8EB]"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* Dynamic Strategic Layer Toggles: [ Levels ] [ VWAP ] [ Bands ] [ Walls ] [ EMAs ] [ Events ] */}
          <div className="hidden sm:flex items-center gap-1 text-[9.5px] flex-wrap">
            <button
              onClick={() => setShowLevels(!showLevels)}
              className={`px-1.5 py-0.2 rounded-[2px] border transition-colors ${
                showLevels
                  ? "bg-[#1C2128] text-[#38BDF8] border-[#38BDF8]/40 font-bold"
                  : "text-[#707987] border-[#222832]"
              }`}
              title="Toggle Secondary Levels (Open, Prev Close, S/R)"
            >
              Levels
            </button>
            <button
              onClick={() => setShowVwap(!showVwap)}
              className={`px-1.5 py-0.2 rounded-[2px] border transition-colors ${
                showVwap
                  ? "bg-[#1C2128] text-[#F59E0B] border-[#F59E0B]/40 font-bold"
                  : "text-[#707987] border-[#222832]"
              }`}
              title="Toggle Cumulative Intraday VWAP"
            >
              VWAP
            </button>
            <button
              onClick={() => setShowBands(!showBands)}
              className={`px-1.5 py-0.2 rounded-[2px] border transition-colors ${
                showBands
                  ? "bg-[#1C2128] text-[#38BDF8] border-[#38BDF8]/40 font-bold"
                  : "text-[#707987] border-[#222832]"
              }`}
              title="Toggle VWAP Standard Deviation Bands (±1σ, ±2σ)"
            >
              Bands
            </button>
            <button
              onClick={() => setShowWalls(!showWalls)}
              className={`px-1.5 py-0.2 rounded-[2px] border transition-colors ${
                showWalls
                  ? "bg-[#1C2128] text-[#8B5CF6] border-[#8B5CF6]/40 font-bold"
                  : "text-[#707987] border-[#222832]"
              }`}
              title="Toggle Options Strike Walls (Call Wall, Put Wall, Max Pain)"
            >
              Walls
            </button>
            <button
              onClick={() => setShowEmas(!showEmas)}
              className={`px-1.5 py-0.2 rounded-[2px] border transition-colors ${
                showEmas
                  ? "bg-[#1C2128] text-[#00C896] border-[#00C896]/40 font-bold"
                  : "text-[#707987] border-[#222832]"
              }`}
              title="Toggle 9 & 21 Exponential Moving Averages"
            >
              EMAs
            </button>
            <button
              onClick={() => setShowEvents(!showEvents)}
              className={`px-1.5 py-0.2 rounded-[2px] border transition-colors ${
                showEvents
                  ? "bg-[#1C2128] text-[#38BDF8] border-[#38BDF8]/40 font-bold"
                  : "text-[#707987] border-[#222832]"
              }`}
              title="Toggle High-Value Event Markers"
            >
              Events
            </button>
          </div>
        </div>

        {/* View Mode & Actions (Focus View vs Fit Session) */}
        <div className="flex items-center gap-1.5">
          <div className="flex items-center gap-0.5 bg-[#14181F] rounded-[2px] p-0.5 border border-[#20252E]">
            <button
              onClick={() => handleViewModeChange("FOCUS")}
              className={`px-1.5 py-0.2 rounded-[2px] text-[9.5px] font-bold transition-all ${
                viewMode === "FOCUS"
                  ? "bg-[#00C896] text-[#050607]"
                  : "text-[#8B949E] hover:text-[#E6E8EB]"
              }`}
              title="Focus View: Rolling recent 90-120m with tight price autoscale"
            >
              Focus
            </button>
            <button
              onClick={() => handleViewModeChange("FIT_SESSION")}
              className={`px-1.5 py-0.2 rounded-[2px] text-[9.5px] font-bold transition-all ${
                viewMode === "FIT_SESSION"
                  ? "bg-[#38BDF8] text-[#050607]"
                  : "text-[#8B949E] hover:text-[#E6E8EB]"
              }`}
              title="Fit Session: Show full day trajectory (09:15 to current)"
            >
              Fit Session
            </button>
          </div>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="text-[#8B949E] hover:text-[#E6E8EB] p-1 rounded-[2px] hover:bg-[#1C2128]"
            title={isFullscreen ? "Exit Fullscreen (Esc)" : "Fullscreen Analyst Mode"}
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* 2. REAL-TIME CANDLE INSPECTION BAR (Active strictly on crosshair hover) */}
      {inspectedCandle && (
        <div className="flex flex-wrap items-center justify-between border-b border-[#14181F] px-2.5 py-1 bg-[#0A0C0E] text-[9.5px] text-[#8B949E]">
          <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
            <span className="text-[#38BDF8] font-bold">{inspectedCandle.time}</span>
            <span>O <strong className="text-[#E6E8EB]">{inspectedCandle.open != null ? formatNumber(inspectedCandle.open, 2) : "—"}</strong></span>
            <span>H <strong className="text-[#00C896]">{inspectedCandle.high != null ? formatNumber(inspectedCandle.high, 2) : "—"}</strong></span>
            <span>L <strong className="text-[#EF4444]">{inspectedCandle.low != null ? formatNumber(inspectedCandle.low, 2) : "—"}</strong></span>
            <span>C <strong className={inspectedCandle.isBullish ? "text-[#00C896]" : "text-[#EF4444]"}>{inspectedCandle.close != null ? formatNumber(inspectedCandle.close, 2) : "—"}</strong></span>
            {showActivity && inspectedCandle.volume != null && Number(inspectedCandle.volume) > 0 && (
              <span>Vol <strong className="text-[#A5ABB4]">{(Number(inspectedCandle.volume) / 1000).toFixed(1)}K</strong></span>
            )}
            {showVwap && vwapVal != null && (
              <span>
                VWAP <strong className="text-[#F59E0B]">{formatNumber(vwapVal, 2)}</strong>
              </span>
            )}
            {priceVsVwap != null && priceVsVwapPct != null && (
              <span className={`${priceVsVwap >= 0 ? "text-[#00C896]" : "text-[#EF4444]"} font-bold`}>
                {priceVsVwap >= 0 ? "+" : ""}{formatNumber(priceVsVwap, 2)} ({priceVsVwapPct >= 0 ? "+" : ""}{formatNumber(priceVsVwapPct, 2)}%)
              </span>
            )}
          </div>
        </div>
      )}

      {/* 3. LIGHTWEIGHT CHARTS CANVAS CONTAINER WITH OFF-SCREEN EDGE BADGES */}
      <div className="relative flex-1 w-full h-full min-h-[500px] bg-[#08090B]">
        {/* Floating Top Edge Badges (Levels off-screen above active range) */}
        {offScreenAbove.length > 0 && (
          <div className="absolute top-2 left-3 z-10 flex items-center gap-1.5 pointer-events-none">
            {offScreenAbove.map((badge) => {
              const isMerged = badge.color === "#38BDF8";
              return (
                <div
                  key={badge.id}
                  className={`flex items-center gap-1 px-1.5 py-0.5 rounded-[2px] bg-[#0E1013]/90 text-[8.5px] font-bold shadow-md ${
                    isMerged
                      ? "border border-cyan-500 text-cyan-300"
                      : "border border-[#00C896]/40 text-[#00C896]"
                  }`}
                >
                  <ArrowUpRight className={`w-3 h-3 ${isMerged ? "text-cyan-300" : "text-[#00C896]"}`} />
                  <span>{badge.label}: {badge.price.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  <span className="text-[#707987] font-normal">(+{badge.delta != null ? Number(badge.delta).toFixed(2) : "—"})</span>
                </div>
              );
            })}
          </div>
        )}

        {/* Floating Bottom Edge Badges (Levels off-screen below active range) */}
        {offScreenBelow.length > 0 && (
          <div className="absolute bottom-16 left-3 z-10 flex items-center gap-1.5 pointer-events-none">
            {offScreenBelow.map((badge) => {
              const isMerged = badge.color === "#38BDF8";
              return (
                <div
                  key={badge.id}
                  className={`flex items-center gap-1 px-1.5 py-0.5 rounded-[2px] bg-[#0E1013]/90 text-[8.5px] font-bold shadow-md ${
                    isMerged
                      ? "border border-cyan-500 text-cyan-300"
                      : "border border-[#EF4444]/40 text-[#EF4444]"
                  }`}
                >
                  <ArrowDownRight className={`w-3 h-3 ${isMerged ? "text-cyan-300" : "text-[#EF4444]"}`} />
                  <span>{badge.label}: {badge.price.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  <span className="text-[#707987] font-normal">({badge.delta != null ? Number(badge.delta).toFixed(2) : "—"})</span>
                </div>
              );
            })}
          </div>
        )}

        {/* Activity Histogram Label Overlay */}
        {showActivity && (
          <div className="absolute bottom-5 left-3 z-10 pointer-events-none text-[8px] text-[#555E6D] font-bold">
            NIFTY 50 AGGREGATE ACTIVITY
          </div>
        )}

        {/* Primary Lightweight Charts Mounting Div */}
        <div ref={containerRef} className="relative w-full h-full min-h-[500px] bg-neutral-950 rounded border border-neutral-800" />

        {/* Explicit empty state — with zero candles the chart canvas would
            otherwise mount blank. Distinguishes completed-session historical review
            from live market feed awaiting data. */}
        {totalCandles === 0 && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center text-center text-neutral-500 font-mono space-y-2 bg-neutral-950/80 rounded pointer-events-none">
            <CandlestickChart className="w-9 h-9 text-neutral-700 animate-pulse" />
            <div className="text-xs text-neutral-400 font-bold">
              {isPostReview || isReplayMode || isPreMarketBaseline
                ? "No completed session candle data available"
                : "Awaiting live candle data"}
            </div>
            <div className="text-[10px] text-neutral-600 max-w-xs">
              {isPostReview || isReplayMode || isPreMarketBaseline
                ? `Historical candles for ${sessionDate || "completed session"} (${selectedTf}) were not recorded or are unavailable.`
                : "Intraday candles, VWAP and structural levels will render once the market feed is streaming."}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

