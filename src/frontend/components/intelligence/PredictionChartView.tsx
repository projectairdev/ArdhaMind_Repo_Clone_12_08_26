// src/frontend/components/intelligence/PredictionChartView.tsx
/**
 * PREDICTION CHART (Native Candlestick Chart Engine + Forward Projection Overlay)
 * - Left Column (~76%): Candlestick Chart Engine + Forward Corridor Overlay
 * - Right Column (~24%): Compact telemetry cards driven ENTIRELY by the real
 *   backend prediction snapshot (envelope.prediction), produced by
 *   PredictionEngine.generate_prediction and serialized by LivePredictionService.
 *
 * There are no hardcoded scenario probabilities, conviction scores, target
 * prices, or historical analogs in this component. When the model fails to
 * produce a prediction the tab renders an explicit "prediction unavailable"
 * state rather than any fallback numbers.
 */

import React, { useState } from "react";
import { formatNumber } from "../../utils/safeHelpers";
import { useCanonicalState } from "../../context/CanonicalStateContext";
import {
  TrendingUp,
  BarChart3,
  Compass,
  Sparkles,
  ShieldAlert,
  Clock,
} from "lucide-react";
import {
  ScenarioProjectionCanvas,
  HorizonTimeframe,
} from "../canonical/chart/ScenarioProjectionCanvas";
import { resolveAuthoritativeMarketState } from "../../utils/canonicalResolvers";
import type { CanonicalPredictionSnapshot } from "../../types/canonical";

interface PredictionChartViewProps {
  vm?: any;
  canonicalState?: any;
}

const pct = (v: number | null | undefined): string =>
  v == null || Number.isNaN(v) ? "—" : `${Math.round(v * 100)}%`;

export const PredictionChartView: React.FC<PredictionChartViewProps> = ({ vm, canonicalState }) => {
  const [activeTimeframe, setActiveTimeframe] = useState<HorizonTimeframe>("15m");
  const [isMaximized, setIsMaximized] = useState(false);

  let canonicalContext: any = null;
  try {
    canonicalContext = useCanonicalState();
  } catch {
    // Isolated tests
  }

  const { envelope } = canonicalContext || {};
  const authState = resolveAuthoritativeMarketState(envelope);
  const activeSpot = authState.spot ?? (envelope?.price_structure?.last_price != null ? Number(envelope.price_structure.last_price) : null);

  const pred: CanonicalPredictionSnapshot | undefined = envelope?.prediction;
  const predictionUnavailable =
    !pred || pred.status === "UNAVAILABLE" || pred.quality === "UNAVAILABLE";

  // NOTE: this view's right-pane telemetry binds directly to `pred` (the real
  // backend prediction snapshot). The forward chart is owned by
  // <ScenarioProjectionCanvas>, which computes its own calibration and shows an
  // explicit "unavailable" state when no prediction is present.

  const isLiveProjection = Boolean(pred?.is_live_projection);
  const generatedLabel = pred?.generated_at_ist
    ? `${pred.generated_at_ist} IST`
    : pred?.generated_at
    ? new Date(pred.generated_at).toLocaleTimeString("en-GB", { timeZone: "Asia/Kolkata", hour12: false })
    : "—";
  const modelLabel = pred?.model_version ? `model ${pred.model_version}` : "model —";

  return (
    <div className="flex flex-col gap-2.5 p-2.5 w-full bg-neutral-950 text-neutral-200 font-mono text-left select-none">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 w-full">
        {/* ═══ LEFT PANE: CANDLESTICK ENGINE + FORWARD OVERLAY ═══ */}
        <div
          className={`${
            isMaximized ? "lg:col-span-12" : "lg:col-span-9"
          } flex flex-col h-full bg-neutral-900/40 border border-neutral-800 rounded-md p-2 min-h-[500px]`}
        >
          <ScenarioProjectionCanvas
            timeframe={activeTimeframe}
            onTimeframeChange={setActiveTimeframe}
            isMaximized={isMaximized}
            onMaximizeChange={setIsMaximized}
            spot={activeSpot}
            vwap={envelope?.price_structure?.vwap ?? envelope?.settled_session?.vwap ?? authState.vwap}
            dayHigh={envelope?.price_structure?.high ?? envelope?.settled_session?.high ?? authState.dayHigh}
            dayLow={envelope?.price_structure?.low ?? envelope?.settled_session?.low ?? authState.dayLow}
          />
        </div>

        {/* ═══ RIGHT PANE: COMPACT TELEMETRY STACK (real model output) ═══ */}
        {!isMaximized && (
          <div className="lg:col-span-3 flex flex-col gap-2 h-full">
            {predictionUnavailable ? (
              <div className="bg-rose-950/30 border border-rose-500/40 rounded p-3 text-xs font-mono space-y-1.5">
                <div className="flex items-center gap-1.5 text-rose-300 font-bold uppercase text-[10px]">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Prediction Unavailable
                </div>
                <p className="text-neutral-400 text-[9.5px] leading-relaxed">
                  The prediction engine did not return a snapshot for the current state.
                  {pred?.unavailable_reason ? ` (${pred.unavailable_reason})` : ""}
                </p>
                <p className="text-neutral-600 text-[8.5px]">
                  No fallback figures are shown. Retrying on the next model refresh.
                </p>
              </div>
            ) : (
              <>
                {/* CARD 1: SCENARIOS & INVALIDATION */}
                <div className="bg-neutral-900/60 border border-neutral-800 rounded p-2.5 text-xs font-mono space-y-2">
                  <div className="flex items-center justify-between border-b border-neutral-800 pb-1">
                    <span className="text-[10px] font-bold text-neutral-100 uppercase flex items-center gap-1">
                      <TrendingUp className="w-3 h-3 text-emerald-400" />
                      1. Scenarios &amp; Invalidation
                    </span>
                    <span className="text-[7.5px] font-bold px-1.5 py-0.2 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                      {pred?.direction_bias ?? "NEUTRAL"}
                    </span>
                  </div>

                  {!isLiveProjection && (
                    <div className="text-[8px] text-amber-300/90 bg-amber-950/20 border border-amber-500/25 rounded px-1.5 py-1">
                      Outside market hours — projection based on the last completed session
                      {pred?.target_session_date ? ` (${pred.target_session_date})` : ""}.
                    </div>
                  )}

                  <div className="p-1.5 rounded bg-emerald-950/25 border border-emerald-500/30 space-y-0.5 text-[9.5px]">
                    <div className="flex justify-between items-center">
                      <strong className="text-emerald-400">Upside path ({pct(pred?.scenario_up_prob)})</strong>
                      <span className="text-[8px] px-1 py-0.2 rounded bg-emerald-500/20 text-emerald-300">UP</span>
                    </div>
                    <div className="flex justify-between text-neutral-300">
                      <span>Model target:</span>
                      <strong className="text-emerald-300">
                        {pred?.primary_target != null ? formatNumber(pred.primary_target, 2) : "—"}
                      </strong>
                    </div>
                  </div>

                  <div className="p-1.5 rounded bg-rose-950/20 border border-rose-500/30 space-y-0.5 text-[9.5px]">
                    <div className="flex justify-between items-center">
                      <strong className="text-rose-300">Downside path ({pct(pred?.scenario_down_prob)})</strong>
                      <span className="text-[8px] px-1 py-0.2 rounded bg-rose-500/20 text-rose-300">DOWN</span>
                    </div>
                    <div className="flex justify-between text-neutral-300">
                      <span>Range / chop:</span>
                      <strong className="text-neutral-300">{pct(pred?.scenario_range_prob)}</strong>
                    </div>
                  </div>

                  <div className="pt-1 border-t border-neutral-800 flex justify-between items-center text-[9px]">
                    <span className="text-neutral-500">Hard invalidation:</span>
                    <span className="text-rose-400 font-bold">
                      {pred?.invalidation_level != null ? formatNumber(pred.invalidation_level, 2) : "N/A"}
                    </span>
                  </div>
                  {isLiveProjection && pred?.volatility_corridor?.near_level != null && (
                    <div className="flex justify-between items-center text-[9px]">
                      <span className="text-neutral-500">1σ corridor:</span>
                      <span className="text-cyan-300">
                        {formatNumber(pred.volatility_corridor.near_level ?? 0, 2)} – {formatNumber(pred.volatility_corridor.far_level ?? 0, 2)}
                      </span>
                    </div>
                  )}
                </div>

                {/* CARD 2: FACTOR CONFLUENCE (supporting vs caution) */}
                <div className="bg-neutral-900/60 border border-neutral-800 rounded p-2.5 text-xs font-mono space-y-1.5">
                  <div className="flex items-center justify-between border-b border-neutral-800 pb-1">
                    <span className="text-[10px] font-bold text-neutral-100 uppercase flex items-center gap-1">
                      <BarChart3 className="w-3 h-3 text-emerald-400" />
                      2. Factor Confluence
                    </span>
                    <span className="text-[7.5px] font-bold px-1 py-0.2 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      {Math.round(pred?.confidence_score ?? 0)} / 100
                    </span>
                  </div>
                  <div className="space-y-1 text-[9px]">
                    {(pred?.supporting_factors ?? []).slice(0, 4).map((f, i) => (
                      <div key={`s${i}`} className="flex gap-1 text-emerald-300/90">
                        <span className="text-emerald-500">+</span>
                        <span className="text-neutral-300">{f}</span>
                      </div>
                    ))}
                    {(pred?.caution_factors ?? []).slice(0, 4).map((f, i) => (
                      <div key={`c${i}`} className="flex gap-1 text-amber-300/90">
                        <span className="text-amber-500">!</span>
                        <span className="text-neutral-300">{f}</span>
                      </div>
                    ))}
                    {(pred?.supporting_factors ?? []).length === 0 &&
                      (pred?.caution_factors ?? []).length === 0 && (
                        <span className="text-neutral-600 text-[8.5px]">No factor annotations returned.</span>
                      )}
                  </div>
                </div>

                {/* CARD 3: MAGNITUDE DISTRIBUTION */}
                <div className="bg-neutral-900/60 border border-neutral-800 rounded p-2.5 text-xs font-mono space-y-1.5">
                  <div className="flex items-center justify-between border-b border-neutral-800 pb-1">
                    <span className="text-[10px] font-bold text-neutral-100 uppercase flex items-center gap-1">
                      <Compass className="w-3 h-3 text-[#38BDF8]" />
                      3. Magnitude Distribution
                    </span>
                    <span className="text-[7.5px] font-bold px-1 py-0.2 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
                      {pred?.expected_range_points != null ? `±${formatNumber(pred.expected_range_points, 0)} pts` : "—"}
                    </span>
                  </div>
                  <div className="space-y-1 text-[9.5px]">
                    {(pred?.magnitude_distribution ?? []).map((b, i) => {
                      const isMode =
                        b.probability ===
                        Math.max(...(pred?.magnitude_distribution ?? []).map((x) => x.probability));
                      return (
                        <div
                          key={i}
                          className={`p-1 rounded flex justify-between items-center border ${
                            isMode
                              ? "bg-emerald-950/20 border-emerald-500/35"
                              : "bg-neutral-950 border-neutral-850"
                          }`}
                        >
                          <span className={isMode ? "text-emerald-300 font-bold" : "text-neutral-400"}>
                            {b.range_label}
                          </span>
                          <strong className={isMode ? "text-emerald-400 font-bold" : "text-neutral-300"}>
                            {pct(b.probability)}
                            {isMode ? " [MODE]" : ""}
                          </strong>
                        </div>
                      );
                    })}
                    {(pred?.magnitude_distribution ?? []).length === 0 && (
                      <span className="text-neutral-600 text-[8.5px]">No magnitude distribution returned.</span>
                    )}
                  </div>
                </div>

                {/* CARD 4: HISTORICAL ANALOGS (SimilarSessionFinder output) */}
                <div className="bg-neutral-900/60 border border-neutral-800 rounded p-2.5 text-xs font-mono space-y-1.5 flex-1">
                  <div className="flex items-center justify-between border-b border-neutral-800 pb-1">
                    <span className="text-[10px] font-bold text-neutral-100 uppercase flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-amber-400" />
                      4. Historical Analogs
                    </span>
                    <span className="text-[7.5px] font-bold px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                      n={(pred?.similar_sessions ?? []).length}
                    </span>
                  </div>
                  <div className="space-y-1.5 text-[9.5px]">
                    {(pred?.similar_sessions ?? []).length === 0 ? (
                      <span className="text-neutral-600 text-[8.5px] block">
                        No comparable historical sessions found for the current regime.
                      </span>
                    ) : (
                      (pred?.similar_sessions ?? []).map((m, i) => (
                        <div key={i} className="p-1.5 rounded bg-neutral-950 border border-neutral-850 space-y-0.5">
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-neutral-200">{m.session_date}</span>
                            <span className="text-emerald-400 font-bold">{m.similarity_pct}% fit</span>
                          </div>
                          <span className="text-neutral-400 block text-[8.5px]">Regime: {m.regime}</span>
                          <span className="text-cyan-300 block text-[8px]">
                            Move: {m.observed_move_pts >= 0 ? "+" : ""}
                            {formatNumber(m.observed_move_pts, 1)} pts · Range: {formatNumber(m.observed_range_pts, 1)} pts · {m.observed_direction}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* FOOTER: generation timestamp + model version */}
                <div className="flex items-center justify-between text-[8px] text-neutral-500 px-1">
                  <span className="flex items-center gap-1">
                    <Clock className="w-2.5 h-2.5" />
                    Generated {generatedLabel} · {modelLabel}
                  </span>
                  <span>{pred?.calibration_maturity ?? ""}</span>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PredictionChartView;
