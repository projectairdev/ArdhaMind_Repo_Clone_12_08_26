/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Canonical Morning Plan View (P4).
 * Presents pre-market / pre-open strategic briefing: opening bias, direction probability,
 * magnitude distribution, trading range, support/resistance, scenarios, and first-15-min checklist.
 */

import React from "react";
import { CanonicalMorningPlan, CanonicalPredictionSnapshot } from "../../../types/canonical";
import { MetricCard } from "../ui/MetricCard";
import { DirectionBadge, QualityBadge } from "../ui/Badges";
import { Sunrise, Target, Shield, CheckSquare, Layers, AlertCircle, Compass } from "lucide-react";
import { useCanonicalState } from "../../../context/CanonicalStateContext";
import { resolveAuthoritativeMarketState } from "../../../utils/canonicalResolvers";

export function MorningPlanView({
  plan: propPlan,
  prediction: propPrediction,
}: {
  plan?: CanonicalMorningPlan;
  prediction?: CanonicalPredictionSnapshot;
}) {
  let canonicalContext: any = null;
  try {
    canonicalContext = useCanonicalState();
  } catch {
    // Isolated tests where context is not mounted
  }

  const envelope = canonicalContext?.envelope;
  const authState = resolveAuthoritativeMarketState(envelope);
  const plan = propPlan || envelope?.active_product?.morning_plan;
  const prediction = propPrediction || envelope?.prediction;

  if (!plan) {
    return (
      <div className="p-8 text-center font-mono text-[#707987]">
        Awaiting Morning Plan calculation for the active session.
      </div>
    );
  }

  const referenceClose = authState.prevClose ?? plan.reference_close;

  return (
    <div className="space-y-4 font-mono">
      {/* Top Header Card */}
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1C2128] pb-3 mb-3">
          <div className="flex items-center gap-2">
            <Sunrise className="w-5 h-5 text-[#F59E0B]" />
            <h2 className="text-base font-bold text-[#F0F6FC]">
              PRE-MARKET STRATEGIC PLAN · {plan.session_date || authState.sessionDate || "2026-09-01"}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <DirectionBadge bias={plan.opening_bias} />
            <QualityBadge quality={plan.quality} />
          </div>
        </div>

        {/* Core Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MetricCard
            label="REFERENCE CLOSE"
            value={referenceClose}
            sublabel="Previous session anchor"
          />
          <MetricCard
            label="OPENING BIAS"
            value={`${plan.opening_bias} (${plan.direction_probability}%)`}
            highlight={plan.opening_bias === "BULLISH" ? "green" : plan.opening_bias === "BEARISH" ? "red" : "blue"}
          />
          <MetricCard
            label="EXPECTED RANGE"
            value={plan.expected_trading_range ? `${plan.expected_trading_range.low} – ${plan.expected_trading_range.high}` : "—"}
            sublabel="ATR-based expansion"
          />
          <MetricCard
            label="REGIME EXPECTATION"
            value={plan.regime_expectation.replace(/_/g, " ")}
            sublabel="Volatility context"
          />
        </div>

        {/* Gap Context */}
        {plan.gap_context && (
          <div className="mt-3 rounded bg-[#12151A] p-2.5 border border-[#222832] text-xs text-[#C9D1D9]">
            <span className="font-bold text-[#38BDF8] mr-2">GAP ANALYSIS:</span>
            {plan.gap_context}
          </div>
        )}
      </div>

      {/* Magnitude Probability Distribution (Discrete 5-Bucket Model) */}
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-4">
        <h3 className="text-xs font-bold text-[#8B949E] uppercase tracking-wider mb-3 flex items-center gap-2">
          <Target className="w-4 h-4 text-[#38BDF8]" />
          Intraday Magnitude Distribution (Probabilities Sum to 100%)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {plan.magnitude_distribution.map((bucket, idx) => {
            const pct = Math.round(bucket.probability * 100);
            return (
              <div key={idx} className="rounded bg-[#12151A] p-3 border border-[#222832]">
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-bold text-[#E6E8EB]">{bucket.bucket_name.replace(/_/g, " ")}</span>
                  <span className="font-bold text-[#38BDF8]">{pct}%</span>
                </div>
                <div className="w-full bg-[#1C2128] rounded-full h-2 mb-2">
                  <div
                    className="bg-[#38BDF8] h-2 rounded-full transition-all"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="text-[10px] text-[#707987]">{bucket.range_label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3 Operational Scenarios: Bullish, Bearish, Neutral */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Bullish Scenario */}
        <div className="rounded-lg border border-[#00C896]/30 bg-[#00C896]/5 p-3.5 space-y-2">
          <div className="text-xs font-bold text-[#00C896] uppercase flex items-center gap-1.5 border-b border-[#00C896]/20 pb-2">
            <span>▲ Bullish Scenario</span>
          </div>
          <div className="text-xs space-y-1 text-[#D1D5DB]">
            <p><strong className="text-[#00C896]">Trigger:</strong> {plan.bullish_scenario.trigger}</p>
            <p><strong className="text-[#8B949E]">Target Area:</strong> {plan.bullish_scenario.target_area}</p>
            <p><strong className="text-[#EF4444]">Invalidation:</strong> {plan.bullish_scenario.invalidation}</p>
          </div>
        </div>

        {/* Bearish Scenario */}
        <div className="rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/5 p-3.5 space-y-2">
          <div className="text-xs font-bold text-[#EF4444] uppercase flex items-center gap-1.5 border-b border-[#EF4444]/20 pb-2">
            <span>▼ Bearish Scenario</span>
          </div>
          <div className="text-xs space-y-1 text-[#D1D5DB]">
            <p><strong className="text-[#EF4444]">Trigger:</strong> {plan.bearish_scenario.trigger}</p>
            <p><strong className="text-[#8B949E]">Target Area:</strong> {plan.bearish_scenario.target_area}</p>
            <p><strong className="text-[#00C896]">Invalidation:</strong> {plan.bearish_scenario.invalidation}</p>
          </div>
        </div>

        {/* Neutral Scenario */}
        <div className="rounded-lg border border-[#707987]/30 bg-[#707987]/10 p-3.5 space-y-2">
          <div className="text-xs font-bold text-[#A5ABB4] uppercase flex items-center gap-1.5 border-b border-[#707987]/20 pb-2">
            <span>◆ Neutral / No-Trade</span>
          </div>
          <div className="text-xs space-y-1 text-[#D1D5DB]">
            <p><strong className="text-[#A5ABB4]">Condition:</strong> {plan.neutral_scenario.condition}</p>
            <p><strong className="text-[#8B949E]">Action:</strong> {plan.neutral_scenario.action}</p>
          </div>
        </div>
      </div>

      {/* First 15-Minute Action Checklist */}
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-4">
        <h3 className="text-xs font-bold text-[#8B949E] uppercase tracking-wider mb-3 flex items-center gap-2">
          <CheckSquare className="w-4 h-4 text-[#00C896]" />
          First 15-Minute Market Open Checklist (09:15 – 09:30 IST)
        </h3>
        <div className="space-y-2">
          {plan.first_15m_checklist.map((item, idx) => (
            <div key={idx} className="flex items-start gap-2.5 rounded bg-[#12151A] p-2.5 border border-[#222832] text-xs text-[#E6E8EB]">
              <span className="w-5 h-5 rounded bg-[#1C2128] text-[#38BDF8] flex items-center justify-center font-bold shrink-0 text-[10px]">
                {idx + 1}
              </span>
              <span className="leading-relaxed">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
