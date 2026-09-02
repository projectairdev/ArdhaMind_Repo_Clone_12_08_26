/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * ScenarioProjectionCanvas.tsx
 * Institutional Candlestick Chart Engine with Synchronized Forward Projection Corridor Overlay.
 * 
 * Features:
 * - Real 5m institutional green/red candlesticks from session open (09:15) to current live spot (14:00 / 24,175.65).
 * - Real volume histogram docked at chart base.
 * - Anchor VWAP overlay line (24,142.80 / #06b6d4).
 * - Day High (24,188.65) and Day Low (24,076.50) dashed level lines.
 * - +1σ Volatility Corridor, -1σ Volatility Corridor, and ±2σ Volatility Envelope.
 * - Forward time-scale extension with Probabilistic Projection Corridor Overlay.
 * - Multi-Horizon Timeframe Engine (1m, 5m, 15m, 1D).
 * - Interactive Crosshair & Candle Inspector.
 * - Fullscreen Maximize Mode with Opaque DOM Isolation.
 */

import React, { useState, useEffect, useMemo } from "react";
import { formatNumber } from "../../../utils/safeHelpers";
import {
  Maximize2,
  Minimize2,
} from "lucide-react";
import {
  HorizonProjectionCalibration,
  getHorizonCalibration,
} from "../../../utils/canonicalIntelligenceAdapter";
import { ScenarioProjectionOverlay } from "./ScenarioProjectionOverlay";
import { useCanonicalState } from "../../../context/CanonicalStateContext";
import { resolveAuthoritativeMarketState } from "../../../utils/canonicalResolvers";

export type HorizonTimeframe = "1m" | "5m" | "15m" | "1D";

export interface Candlestick5m {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  vwap: number;
}

export interface ScenarioProjectionCanvasProps {
  timeframe?: HorizonTimeframe;
  onTimeframeChange?: (tf: HorizonTimeframe) => void;
  isMaximized?: boolean;
  onMaximizeChange?: (maximized: boolean) => void;
  spot?: number | null;
  vwap?: number | null;
  dayHigh?: number | null;
  dayLow?: number | null;
}

export const ScenarioProjectionCanvas: React.FC<ScenarioProjectionCanvasProps> = ({
  timeframe: propTimeframe,
  onTimeframeChange,
  isMaximized: propIsMaximized,
  onMaximizeChange,
  spot,
  vwap,
  dayHigh,
  dayLow,
}) => {
  const [internalTimeframe, setInternalTimeframe] = useState<HorizonTimeframe>("15m");
  const activeTimeframe = propTimeframe ?? internalTimeframe;

  const setTimeframe = (tf: HorizonTimeframe) => {
    setInternalTimeframe(tf);
    onTimeframeChange?.(tf);
  };

  // Layer Visibility States
  const [showPrimary, setShowPrimary] = useState(true);
  const [showAlternate, setShowAlternate] = useState(true);
  const [showEnvelope, setShowEnvelope] = useState(true);
  const [showAnalog, setShowAnalog] = useState(false);
  const [showVwap, setShowVwap] = useState(true);
  const [internalMaximized, setInternalMaximized] = useState(false);

  // Active Inspected Candle from Crosshair
  const [hoveredCandle, setHoveredCandle] = useState<Candlestick5m | null>(null);

  const { sessionPhase, isReplayMode, envelope } = useCanonicalState();
  const isLiveTape = sessionPhase === "LIVE" && !isReplayMode;

  const authState = resolveAuthoritativeMarketState(envelope);
  const activeSpot: number | null = spot ?? authState.spot ?? (envelope?.price_structure?.last_price != null ? Number(envelope.price_structure.last_price) : null);

  const isMaximized = propIsMaximized ?? internalMaximized;

  const toggleMaximize = (val: boolean) => {
    setInternalMaximized(val);
    onMaximizeChange?.(val);
  };

  // Reset all layers to default
  const handleReset = () => {
    setShowPrimary(true);
    setShowAlternate(true);
    setShowEnvelope(true);
    setShowAnalog(false);
    setShowVwap(true);
    setTimeframe("15m");
  };

  // Escape key listener for fullscreen exit
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isMaximized) {
        toggleMaximize(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isMaximized]);

  // Early return empty-state guard if session spot data is awaiting
  if (activeSpot == null) {
    return (
      <div
        className={`w-full flex flex-col items-center justify-center bg-neutral-950 rounded border border-neutral-850 p-12 text-center text-neutral-500 font-mono space-y-2 select-none ${
          isMaximized
            ? "fixed inset-0 z-50 bg-neutral-950 p-4 w-screen h-screen overflow-hidden"
            : "h-full min-h-[480px]"
        }`}
      >
        <div className="text-xs font-bold text-neutral-400">Awaiting session projection stream</div>
        <div className="text-[10px] text-neutral-600">Probabilistic volatility cones and scenario trajectories will populate upon market price hydration.</div>
      </div>
    );
  }

  const activeVwap = vwap ?? envelope?.price_structure?.vwap ?? authState.vwap ?? activeSpot;
  const activeHigh = dayHigh ?? envelope?.price_structure?.high ?? authState.dayHigh ?? (activeSpot + 50);
  const activeLow = dayLow ?? envelope?.price_structure?.low ?? authState.dayLow ?? (activeSpot - 50);
  const activePrevClose = envelope?.price_structure?.previous_close ?? authState.prevClose ?? activeSpot;

  // Horizon-Specific Calibration Engine
  const calib: HorizonProjectionCalibration = useMemo(() => {
    return getHorizonCalibration(activeTimeframe, 1, activeSpot, activeVwap, activeHigh, activeLow, activePrevClose, authState.atr14 ?? undefined, envelope?.prediction ?? null);
  }, [activeTimeframe, activeSpot, activeVwap, activeHigh, activeLow, activePrevClose, authState.atr14, envelope?.prediction]);

  // Canvas Dimensions
  const width = isMaximized ? 1200 : 920;
  const height = isMaximized ? 650 : 460;
  const padding = { top: 35, right: 145, bottom: 45, left: 55 };

  // Price Bounds from Calibration
  const minPrice = calib.minPrice;
  const maxPrice = calib.maxPrice;

  const getY = (price: number) => {
    const ratio = (price - minPrice) / (maxPrice - minPrice);
    return height - padding.bottom - ratio * (height - padding.top - padding.bottom);
  };

  // Total horizontal slots: 26 total slots (16 historical 5m candles + 10 forward projection bars)
  const totalSlots = 26;
  const historySplitIndex = 16;

  const getX = (slotIndex: number) => {
    return padding.left + (slotIndex / totalSlots) * (width - padding.left - padding.right);
  };

  // Authentic 5-Minute OHLC Candlestick Series (Dynamic from envelope with clean baseline fallback)
  const candles5m: Candlestick5m[] = useMemo(() => {
    const raw = envelope?.candles?.["5m"] || [];
    if (Array.isArray(raw) && raw.length > 0) {
      return raw.slice(-16).map((c: any) => ({
        time: c.start ? String(c.start).slice(11, 16) : (c.time ? String(c.time).slice(11, 16) : "14:00"),
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
        volume: c.volume || 800000,
        vwap: c.vwap || (c.high + c.low + c.close) / 3,
      }));
    }
    return [];
  }, [envelope?.candles]);

  const lastHistoryX = getX(historySplitIndex);
  const lastHistoryY = getY(activeSpot);
  const finalX = getX(totalSlots);
  const midForwardX = getX(historySplitIndex + 5);

  // Volume Bar Geometry
  const maxVolume = useMemo(() => Math.max(...candles5m.map((c) => c.volume)), [candles5m]);
  const volumeHeightMax = 50;

  // Only draw the forward projection (target lines, corridor fan, model pivots)
  // when a real backend prediction snapshot supplied the numbers. Otherwise the
  // geometric base is a placeholder and must not be shown as if it were analysis.
  const projectionReady = calib.predictionAvailable;

  // Collision-Safe Right Y-Axis Levels Filtering.
  // Without a real prediction, drop the projected target / pivot lines and keep
  // only observed structural references (spot, VWAP, day high, session low).
  const renderedGridLevels = useMemo(() => {
    const structuralOnly = projectionReady
      ? calib.gridLevels
      : calib.gridLevels.filter((g) =>
          /Current Spot|Current Settlement|Anchor VWAP|Day High|Session Low|Prev Close/i.test(g.label)
        );
    const sorted = [...structuralOnly].sort((a, b) => getY(a.price) - getY(b.price));
    const result: typeof sorted = [];
    for (let i = 0; i < sorted.length; i++) {
      const current = sorted[i];
      const currentY = getY(current.price);
      const prev = result[result.length - 1];
      if (prev) {
        const prevY = getY(prev.price);
        if (Math.abs(currentY - prevY) < 14) {
          if (current.isSpot || current.label.includes("Target") || current.label.includes("Day High")) {
            if (!prev.isSpot) {
              result[result.length - 1] = current;
            }
          }
          continue;
        }
      }
      result.push(current);
    }
    return result;
  }, [calib.gridLevels, projectionReady, height, minPrice, maxPrice]);

  return (
    <div
      className={`w-full flex flex-col bg-neutral-950 rounded border border-neutral-850 p-2.5 pr-4 select-none font-mono ${
        isMaximized
          ? "fixed inset-0 z-50 bg-neutral-950 p-4 flex flex-col w-screen h-screen overflow-hidden"
          : "h-full min-h-[480px]"
      }`}
    >
      {/* ── TOOLBAR & CONTROLS HEADER ── */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-800/90 pb-2 mb-2">
        {/* Left: Horizon Selector & Core Layer Toggles */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Horizon Selector */}
          <div className="flex items-center bg-neutral-900 rounded p-0.5 border border-neutral-800">
            {(["1m", "5m", "15m", "1D"] as HorizonTimeframe[]).map((h) => (
              <button
                key={h}
                onClick={() => setTimeframe(h)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono transition-all ${
                  activeTimeframe === h
                    ? "bg-cyan-500/20 text-cyan-400 font-bold shadow-sm"
                    : "text-neutral-400 hover:text-neutral-200"
                }`}
              >
                {h}
              </button>
            ))}
          </div>

          <div className="h-3 w-px bg-neutral-800" />

          {/* Compact Layer Toggles */}
          <div className="flex items-center gap-1.5 font-mono text-[10px] flex-wrap">
            <button
              onClick={() => setShowPrimary(!showPrimary)}
              className={`px-1.5 py-0.5 rounded font-bold border transition-colors ${
                showPrimary
                  ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                  : "bg-neutral-900 text-neutral-500 border-neutral-800 hover:text-neutral-300"
              }`}
            >
              +1σ Corridor
            </button>
            <button
              onClick={() => setShowAlternate(!showAlternate)}
              className={`px-1.5 py-0.5 rounded font-bold border transition-colors ${
                showAlternate
                  ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                  : "bg-neutral-900 text-neutral-500 border-neutral-800 hover:text-neutral-300"
              }`}
            >
              -1σ Corridor
            </button>
            <button
              onClick={() => setShowEnvelope(!showEnvelope)}
              className={`px-1.5 py-0.5 rounded font-bold border transition-colors ${
                showEnvelope
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                  : "bg-neutral-900 text-neutral-500 border-neutral-800 hover:text-neutral-300"
              }`}
            >
              ±2σ Envelope
            </button>
            <button
              onClick={() => setShowAnalog(!showAnalog)}
              className={`px-1.5 py-0.5 rounded font-bold border transition-colors ${
                showAnalog
                  ? "bg-purple-500/20 text-purple-300 border-purple-500/40"
                  : "bg-neutral-900 text-neutral-500 border-neutral-800 hover:text-neutral-300"
              }`}
            >
              Analog
            </button>
            <button
              onClick={() => setShowVwap(!showVwap)}
              className={`px-1.5 py-0.5 rounded font-bold border transition-colors ${
                showVwap
                  ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
                  : "bg-neutral-900 text-neutral-500 border-neutral-800 hover:text-neutral-300"
              }`}
            >
              VWAP
            </button>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            title="Reset to default view"
            className="px-2 py-1 text-neutral-400 hover:text-neutral-200 font-mono text-[11px]"
          >
            Reset
          </button>
          <button
            onClick={() => toggleMaximize(!isMaximized)}
            className="px-2 py-1 bg-neutral-900 border border-neutral-800 hover:border-neutral-700 text-cyan-400 rounded font-mono text-[11px] transition-colors"
          >
            {isMaximized ? "Restore" : "Maximize"}
          </button>
        </div>
      </div>

      {/* ── CANDLE INSPECTOR HEADER ON HOVER ── */}
      {hoveredCandle && (
        <div className="flex items-center gap-3 text-[10px] text-neutral-400 border-b border-neutral-850 pb-1 mb-1 px-1 min-h-[20px]">
          <span className="text-neutral-200 font-bold">TIME: {hoveredCandle.time}</span>
          <span>O: <strong className="text-neutral-100">{formatNumber(hoveredCandle.open, 2)}</strong></span>
          <span>H: <strong className="text-emerald-400">{formatNumber(hoveredCandle.high, 2)}</strong></span>
          <span>L: <strong className="text-rose-400">{formatNumber(hoveredCandle.low, 2)}</strong></span>
          <span>C: <strong className={hoveredCandle.close >= hoveredCandle.open ? "text-emerald-400" : "text-rose-400"}>{formatNumber(hoveredCandle.close, 2)}</strong></span>
          <span>VOL: <strong className="text-cyan-300">{(hoveredCandle.volume / 100000).toFixed(2)}L</strong></span>
          <span>VWAP: <strong className="text-amber-300">{formatNumber(hoveredCandle.vwap, 2)}</strong></span>
        </div>
      )}

      {/* ── SVG CANDLESTICK + PROJECTION ENGINE ── */}
      <div className="flex-1 w-full relative min-h-[380px]">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-full text-xs font-mono"
          preserveAspectRatio="xMidYMid meet"
          onMouseLeave={() => setHoveredCandle(null)}
        >
          <defs>
            <linearGradient id="primaryConeGradientNative" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.05" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.25" />
            </linearGradient>

            <linearGradient id="alternateConeGradientNative" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.03" />
              <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.15" />
            </linearGradient>

            <linearGradient id="envelopeGradientNative" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#d97706" stopOpacity="0.02" />
              <stop offset="100%" stopColor="#d97706" stopOpacity="0.08" />
            </linearGradient>
          </defs>

          {/* ── 1. BACKGROUND HORIZONTAL GRID LINES & LABELS ── */}
          {renderedGridLevels.map((lvl) => {
            const y = getY(lvl.price);
            return (
              <g key={lvl.price}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  className={`${lvl.color}`}
                  strokeWidth={lvl.isSpot ? "1.5" : "1"}
                  strokeDasharray={lvl.isSpot ? "none" : "3 3"}
                />
                <text
                  x={width - padding.right + 6}
                  y={y + 3.5}
                  className={`text-[8.5px] font-mono font-bold fill-current ${lvl.text}`}
                >
                  {lvl.label}
                </text>
              </g>
            );
          })}

          {/* ── 2. DAY HIGH & DAY LOW STRUCTURAL REFERENCE LINES ── */}
          <line
            x1={padding.left}
            y1={getY(dayHigh)}
            x2={width - padding.right}
            y2={getY(dayHigh)}
            stroke="#06b6d4"
            strokeWidth="1.2"
            strokeDasharray="4 2"
            strokeOpacity="0.6"
          />
          <line
            x1={padding.left}
            y1={getY(dayLow)}
            x2={width - padding.right}
            y2={getY(dayLow)}
            stroke="#f43f5e"
            strokeWidth="1.2"
            strokeDasharray="4 2"
            strokeOpacity="0.6"
          />

          {/* ── 3. VOLUME HISTOGRAM DOCKED AT BOTTOM ── */}
          <g className="volume-histogram">
            {candles5m.map((c, i) => {
              const cx = getX(i);
              const barHeight = (c.volume / maxVolume) * volumeHeightMax;
              const yTop = height - padding.bottom - barHeight;
              const isBull = c.close >= c.open;
              return (
                <rect
                  key={c.time}
                  x={cx - 5}
                  y={yTop}
                  width="10"
                  height={barHeight}
                  fill={isBull ? "#10b981" : "#f43f5e"}
                  fillOpacity="0.25"
                />
              );
            })}
          </g>

          {/* ── 4. ANCHOR VWAP LINE ── */}
          {showVwap && (
            <path
              d={candles5m.map((c, i) => {
                const x = getX(i);
                const y = getY(c.vwap);
                return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
              }).join(" ")}
              fill="none"
              stroke="#06b6d4"
              strokeWidth="1.6"
            />
          )}

          {/* ── 5. REAL 5-MINUTE CANDLESTICKS ── */}
          <g className="candlesticks">
            {candles5m.map((c, i) => {
              const cx = getX(i);
              const highY = getY(c.high);
              const lowY = getY(c.low);
              const openY = getY(c.open);
              const closeY = getY(c.close);
              const isBull = c.close >= c.open;
              const bodyTop = Math.min(openY, closeY);
              const bodyHeight = Math.max(Math.abs(closeY - openY), 2);
              const color = isBull ? "#10b981" : "#f43f5e";

              return (
                <g
                  key={c.time}
                  className="cursor-pointer transition-opacity hover:opacity-80"
                  onMouseEnter={() => setHoveredCandle(c)}
                >
                  {/* Upper and Lower Wick */}
                  <line
                    x1={cx}
                    y1={highY}
                    x2={cx}
                    y2={lowY}
                    stroke={color}
                    strokeWidth="1.5"
                  />
                  {/* Candle Body */}
                  <rect
                    x={cx - 5.5}
                    y={bodyTop}
                    width="11"
                    height={bodyHeight}
                    fill={color}
                    rx="1"
                  />
                </g>
              );
            })}
          </g>

          {/* ── 6. TIMELINE SEPARATOR (14:00 LIVE TAPE BEACON) ── */}
          <line
            x1={lastHistoryX}
            y1={padding.top}
            x2={lastHistoryX}
            y2={height - padding.bottom}
            stroke="#eab308"
            strokeWidth="1.5"
            strokeDasharray="4 4"
            strokeOpacity="0.8"
          />
          <text
            x={lastHistoryX}
            y={padding.top - 8}
            textAnchor="middle"
            className="text-[9px] font-bold fill-amber-300"
          >
            ▼ {(calib.ticks.find((t) => t.isLive)?.text ?? "NOW (LIVE)").replace(" (LIVE)", "")} ({isLiveTape ? "LIVE TAPE" : "SESSION AS-OF REFERENCE"})
          </text>

          {/* Live Spot Pulsing Beacon */}
          <circle cx={lastHistoryX} cy={lastHistoryY} r="7" fill="#fbbf24" fillOpacity="0.35" className="animate-ping" />
          <circle cx={lastHistoryX} cy={lastHistoryY} r="3.5" fill="#fbbf24" />

          {/* ── 7. SYNCHRONIZED FORWARD PROJECTION CORRIDOR OVERLAY ──
                Only drawn when a real prediction snapshot is available. */}
          {projectionReady ? (
            <ScenarioProjectionOverlay
              calib={calib}
              spot={activeSpot}
              vwap={activeVwap}
              lastHistoryX={lastHistoryX}
              lastHistoryY={lastHistoryY}
              finalX={finalX}
              midForwardX={midForwardX}
              getY={getY}
              showPrimary={showPrimary}
              showAlternate={showAlternate}
              showEnvelope={showEnvelope}
              showAnalog={showAnalog}
              showVwapCorridor={showVwap}
            />
          ) : (
            <g>
              <rect
                x={lastHistoryX}
                y={padding.top}
                width={Math.max(0, finalX - lastHistoryX)}
                height={height - padding.top - padding.bottom}
                fill="#0a0a0a"
                fillOpacity="0.45"
              />
              <text
                x={(lastHistoryX + finalX) / 2}
                y={padding.top + (height - padding.top - padding.bottom) / 2}
                textAnchor="middle"
                className="text-[9px] font-mono font-bold fill-neutral-500"
              >
                Forward projection unavailable
              </text>
              <text
                x={(lastHistoryX + finalX) / 2}
                y={padding.top + (height - padding.top - padding.bottom) / 2 + 14}
                textAnchor="middle"
                className="text-[7.5px] font-mono fill-neutral-600"
              >
                Awaiting prediction model — no target shown
              </text>
            </g>
          )}

          {/* ── 8. BOTTOM TIME SCALE TICKS ── */}
          {calib.ticks.map((t) => {
            const x = getX((t.slot / 20) * totalSlots);
            return (
              <text
                key={t.text}
                x={x}
                y={height - padding.bottom + 18}
                textAnchor={t.anchor as any}
                className={`text-[8.5px] font-mono ${t.isLive ? "fill-amber-300 font-bold" : "fill-neutral-500"}`}
              >
                {t.text}
              </text>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

export default ScenarioProjectionCanvas;
