/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * ScenarioProjectionOverlay.tsx
 * Institutional Probability Density Fan (Gaussian Cloud) Overlay.
 * 
 * Renders:
 * 1. Shaded Emerald Base Fan (65% Probability) — Gradient polygon fanning to Target 2 (24,250), Target 1 (24,200), & Anchor VWAP.
 * 2. Translucent Rose Invalidation Fan (35% Probability) — Rejection arc dipping to Session Low Floor (24,076.50).
 * 3. Statistical Volatility Envelope (±1σ / ±2σ Corridor: 24,080 to 24,270).
 * 4. Horizontal Structural Dashed Guide Lines (Call Wall, VWAP, Floor, Put Wall).
 * 5. Normalized Historical Analog Curve with minimalist micro-tag.
 */

import React from "react";
import { formatNumber } from "../../../utils/safeHelpers";
import { HorizonProjectionCalibration } from "../../../utils/canonicalIntelligenceAdapter";

export interface ScenarioProjectionOverlayProps {
  calib: HorizonProjectionCalibration;
  spot: number;
  vwap: number;
  lastHistoryX: number;
  lastHistoryY: number;
  finalX: number;
  midForwardX: number;
  getY: (price: number) => number;
  showPrimary?: boolean;
  showAlternate?: boolean;
  showEnvelope?: boolean;
  showAnalog?: boolean;
  showVwapCorridor?: boolean;
}

export const ScenarioProjectionOverlay: React.FC<ScenarioProjectionOverlayProps> = ({
  calib,
  spot,
  vwap,
  lastHistoryX,
  lastHistoryY,
  finalX,
  midForwardX,
  getY,
  showPrimary = true,
  showAlternate = true,
  showEnvelope = true,
  showAnalog = false,
  showVwapCorridor = true,
}) => {
  const primaryTargetY = getY(calib.primaryTarget);
  const altTargetY = getY(calib.alternateTarget);
  const envelopeTopY = getY(calib.envelopeTop);
  const envelopeBottomY = getY(calib.envelopeBottom);
  const vwapY = getY(vwap);
  const analogFinalY = getY(spot + calib.analogOutcome);

  // Structural Levels Coordinates
  const levelTopY = getY(calib.envelopeTop);
  const levelPrimaryY = getY(calib.primaryTarget);
  const levelAltY = getY(calib.alternateTarget);
  const levelBottomY = getY(calib.envelopeBottom);

  return (
    <g className="scenario-projection-overlay pointer-events-none select-none">
      {/* ── 1. HORIZONTAL STRUCTURAL PROJECTION GUIDES ── */}
      <g className="projection-structural-guides opacity-40">
        <line
          x1={lastHistoryX}
          y1={levelTopY}
          x2={finalX}
          y2={levelTopY}
          stroke="#71717a"
          strokeWidth="0.8"
          strokeDasharray="2 2"
        />
        <line
          x1={lastHistoryX}
          y1={levelPrimaryY}
          x2={finalX}
          y2={levelPrimaryY}
          stroke="#10b981"
          strokeWidth="0.8"
          strokeDasharray="2 2"
        />
        <line
          x1={lastHistoryX}
          y1={vwapY}
          x2={finalX}
          y2={vwapY}
          stroke="#06b6d4"
          strokeWidth="0.8"
          strokeDasharray="2 2"
        />
        <line
          x1={lastHistoryX}
          y1={levelAltY}
          x2={finalX}
          y2={levelAltY}
          stroke="#f43f5e"
          strokeWidth="0.8"
          strokeDasharray="2 2"
        />
        <line
          x1={lastHistoryX}
          y1={levelBottomY}
          x2={finalX}
          y2={levelBottomY}
          stroke="#0284c7"
          strokeWidth="0.8"
          strokeDasharray="2 2"
        />
      </g>

      {/* ── 2. VOLATILITY ENVELOPE (±2σ GAUSSIAN CORRIDOR) ── */}
      {showEnvelope && (
        <g className="envelope-layer">
          <polygon
            points={`${lastHistoryX},${lastHistoryY} ${finalX},${envelopeTopY} ${finalX},${envelopeBottomY} ${lastHistoryX},${lastHistoryY}`}
            fill="url(#envelopeGradientNative)"
          />
          <line
            x1={lastHistoryX}
            y1={lastHistoryY}
            x2={finalX}
            y2={envelopeTopY}
            stroke="#d97706"
            strokeWidth="1.2"
            strokeDasharray="3 3"
            strokeOpacity="0.7"
          />
          <line
            x1={lastHistoryX}
            y1={lastHistoryY}
            x2={finalX}
            y2={envelopeBottomY}
            stroke="#d97706"
            strokeWidth="1.2"
            strokeDasharray="3 3"
            strokeOpacity="0.7"
          />
          <text
            x={lastHistoryX + 60}
            y={envelopeTopY - 4}
            textAnchor="start"
            className="text-[8px] fill-amber-300 font-mono"
          >
            +2σ Volatility Envelope ({formatNumber(calib.envelopeTop, 2)})
          </text>
          <text
            x={lastHistoryX + 60}
            y={envelopeBottomY - 4}
            textAnchor="start"
            className="text-[8px] fill-amber-300 font-mono"
          >
            -2σ Volatility Envelope ({formatNumber(calib.envelopeBottom, 2)})
          </text>
        </g>
      )}

      {/* ── 3. HISTORICAL ANALOG OVERLAY (PURPLE GHOST PATH) ── */}
      {showAnalog && (
        <g className="analog-layer">
          <path
            d={`M ${lastHistoryX} ${lastHistoryY} Q ${midForwardX} ${getY(spot + calib.analogOutcome * 0.6)} ${finalX} ${analogFinalY}`}
            fill="none"
            stroke="#c084fc"
            strokeWidth="1.8"
            strokeDasharray="4 4"
            strokeOpacity="0.85"
          />
          <circle cx={finalX} cy={analogFinalY} r="3" fill="#c084fc" />
          <text
            x={finalX - 110}
            y={analogFinalY - 6}
            className="text-[9.5px] font-bold fill-purple-300/90 font-mono"
          >
            Historical Analog Pattern
          </text>
        </g>
      )}

      {/* ── 4. PRIMARY +1σ VOLATILITY CORRIDOR (EMERALD PARAMETRIC FAN) ── */}
      {showPrimary && (
        <g className="primary-cone-layer">
          {/* Shaded Expansion Cone */}
          <polygon
            points={`${lastHistoryX},${lastHistoryY} ${finalX},${getY(calib.primaryTarget + 10)} ${finalX},${getY(calib.primaryTarget - 12)} ${lastHistoryX},${lastHistoryY}`}
            fill="url(#primaryConeGradientNative)"
          />
          {/* Median Trajectory Vector */}
          <path
            d={`M ${lastHistoryX} ${lastHistoryY} C ${midForwardX} ${getY((spot + calib.primaryTarget) / 2)}, ${midForwardX + 20} ${primaryTargetY}, ${finalX} ${primaryTargetY}`}
            fill="none"
            stroke="#10b981"
            strokeWidth="2.5"
          />
          {/* Target Endpoint Marker & Badge */}
          <circle cx={finalX} cy={primaryTargetY} r="4" fill="#10b981" />
          <rect
            x={finalX - 105}
            y={primaryTargetY - 18}
            width="100"
            height="15"
            rx="2"
            fill="#064e3b"
            stroke="#10b981"
            strokeWidth="0.8"
          />
          <text
            x={finalX - 55}
            y={primaryTargetY - 7}
            textAnchor="middle"
            className="text-[8px] font-bold fill-emerald-300 font-mono"
          >
            +1σ CORRIDOR ({formatNumber(calib.primaryTarget, 0)})
          </text>
        </g>
      )}

      {/* ── 5. ALTERNATE -1σ VOLATILITY CORRIDOR (ROSE PARAMETRIC FAN) ── */}
      {showAlternate && (
        <g className="alternate-vector-layer">
          {/* Shaded Invalidation Polygon */}
          <polygon
            points={`${lastHistoryX},${lastHistoryY} ${finalX},${getY(calib.alternateTarget + 8)} ${finalX},${getY(calib.alternateTarget - 8)} ${lastHistoryX},${lastHistoryY}`}
            fill="url(#alternateConeGradientNative)"
          />
          {/* Rejection Curve */}
          <path
            d={`M ${lastHistoryX} ${lastHistoryY} Q ${midForwardX - 10} ${getY(spot + 15)} ${finalX} ${altTargetY}`}
            fill="none"
            stroke="#f43f5e"
            strokeWidth="2"
            strokeDasharray="4 4"
          />
          {/* Endpoint Marker & Offset Badge */}
          <circle cx={finalX} cy={altTargetY} r="3.5" fill="#f43f5e" />
          <rect
            x={finalX - 105}
            y={altTargetY - 16}
            width="100"
            height="15"
            rx="2"
            fill="#4c0519"
            stroke="#f43f5e"
            strokeWidth="0.8"
          />
          <text
            x={finalX - 55}
            y={altTargetY - 5}
            textAnchor="middle"
            className="text-[8px] font-bold fill-rose-300 font-mono"
          >
            -1σ CORRIDOR ({formatNumber(calib.alternateTarget, 0)})
          </text>
        </g>
      )}
    </g>
  );
};

export default ScenarioProjectionOverlay;
