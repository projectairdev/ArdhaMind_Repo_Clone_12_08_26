// src/frontend/components/TradeCenter.tsx
import React, { useState } from "react";
import { useTheme } from "../context/ThemeContext";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { TradeCandidate, CandidateDecision, StrategyScore } from "../types";
import {
  Compass,
  AlertCircle,
  CheckCircle,
  Zap,
  Target,
  ShieldAlert,
  Award,
  Sparkles,
  ArrowUpRight,
  TrendingUp,
  Activity
} from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatCurrency
} from "../utils/safeHelpers";
import { resolveMarketSessionState } from "../utils/canonicalSemanticContract";

export function TradeCenter() {
  const { themeClasses, fontClasses, accentClasses } = useTheme();
  const {
    canonicalState,
    opportunityContext: opp,
    strategyEvaluation: evals,
    confidenceReport: conf,
    riskReport: risk,
    decisionReport: decision,
    tradePlan: plan,
    marketContext,
    optionContext,
    brokerAccount,
    portfolioReport,
    apiLatency,
    loading,
    error,
    syncBroker
  } = useWorkstationState();

  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);

  if (loading && !plan) {
    return (
      <div id="trade-center-loading" className="space-y-6 animate-pulse p-2 text-left">
        <div className="h-20 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-64 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
          <div className="h-64 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
          <div className="h-64 bg-neutral-900 border border-neutral-850 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div id="trade-center-error" className="p-8 bg-neutral-950 border border-rose-900 rounded-xl text-center space-y-4 max-w-xl mx-auto my-12 text-left">
        <AlertCircle size={40} className="text-rose-500 mx-auto" />
        <h3 className="text-base font-bold text-white">Opportunities Pipeline Down</h3>
        <p className="text-xs text-neutral-400">{error || "Could not retrieve real-time candidate trade plans."}</p>
        <button
          onClick={() => syncBroker(true)}
          className="px-4 py-2 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 text-xs font-mono rounded text-white transition cursor-pointer"
        >
          Retry Pipeline Sync
        </button>
      </div>
    );
  }

  const acceptedCandidates = safeArray(plan?.accepted_candidates) as TradeCandidate[];
  const activeId = selectedCandidateId || (acceptedCandidates[0]?.candidate_id);
  const activeCandidate = (acceptedCandidates.find(c => c.candidate_id === activeId) || acceptedCandidates[0]) as TradeCandidate | undefined;
  const activeDecision = (safeArray(decision?.candidate_decisions) as CandidateDecision[]).find(d => d.candidate_id === activeCandidate?.candidate_id);

  // Production Integrity (Rule 2): React does NOT calculate trading values.
  // SL, Target, and Confidence all come from the backend pipelines:
  //   - stop_loss_price  → RiskPipeline (risk_report.approved_candidates)
  //   - target_price     → RiskPipeline (risk_report.approved_candidates)
  //   - confidence_score → ConfidencePipeline (confidence_report.confidence_scores)
  const entryPrice = activeCandidate ? safeNumber((activeCandidate as any).entry_premium || (activeCandidate as any).premium) : null;
  
  // Read SL/Target from the backend-approved candidate entry in risk_report
  const activeRiskCandidate = safeArray(risk?.approved_candidates).find(
    (c: any) => c?.candidate_id === activeCandidate?.candidate_id
  ) as any | undefined;
  const stopLoss: number | null = activeRiskCandidate?.stop_loss_price ?? null;
  const profitTarget: number | null = activeRiskCandidate?.target_price ?? null;

  // Confidence: from confidence_report keyed by candidate_id
  const confidenceScoreMap = conf?.confidence_scores as Record<string, number> | undefined;
  const confidenceScore: number | null = activeCandidate
    ? (confidenceScoreMap?.[activeCandidate.candidate_id] ?? null)
    : null;

  // 1. Canonical Market Closed check
  const canonicalSession = resolveMarketSessionState(canonicalState, marketContext);
  const isMarketClosed = canonicalSession === "CLOSED" || canonicalSession === "POST_MARKET";
  
  // 2. Feed status validation (Broker Status, Option Chain, Spot and Latency)
  const isFeedCritical = apiLatency !== null && apiLatency > 5000;
  const isBrokerDisconnected = !brokerAccount || !brokerAccount.user_id;
  const isOptionChainStale = !optionContext?.timestamp;
  const isSpotStale = !marketContext?.timestamp;
  
  const liveRecommendationsUnavailable = !isMarketClosed && (isFeedCritical || isBrokerDisconnected || isOptionChainStale || isSpotStale);

  return (
    <div id="trade-center-terminal" className={`space-y-6 text-left ${fontClasses.base}`}>
      
      {/* ── Title & Ticker ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-neutral-850 pb-4 gap-4">
        <div>
          <span className={`text-[10px] font-mono uppercase tracking-widest font-extrabold ${accentClasses.text}`}>
            Opportunity Assessment & Planning
          </span>
          <h2 className="text-xl sm:text-2xl font-black tracking-tight mt-1 flex items-center gap-2">
            <Compass className="h-5.5 w-5.5 text-amber-400" />
            Alpha Generation Trade Center
          </h2>
          <p className="text-xs text-neutral-400 mt-0.5">
            Identify high probability candidates, evaluate active momentum strategies, and audit risk bounds.
          </p>
        </div>
      </div>

      {/* ── Tomorrow Planning / Feed Status Banners ── */}
      {isMarketClosed && (
        <div id="tomorrow-planning-banner" className="bg-amber-950/20 border border-amber-900/60 p-3 rounded-lg flex items-center gap-3 text-xs text-amber-300 font-mono">
          <Zap size={16} className="text-amber-400 animate-pulse flex-shrink-0" />
          <div>
            <span className="font-extrabold uppercase mr-1.5">[Tomorrow Planning Mode Active]</span>
            Market Closed. Recommendations generated using previous session's closing data. Generated At {marketContext?.timestamp || "End of Day"}.
          </div>
        </div>
      )}

      {liveRecommendationsUnavailable ? (
        <div id="stale-feed-alert" className="p-8 bg-neutral-950 border border-red-950 rounded-xl text-center space-y-4 max-w-xl mx-auto my-12 text-left font-mono">
          <ShieldAlert size={40} className="text-red-500 mx-auto animate-bounce" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wide">Live recommendations unavailable</h3>
          <p className="text-xs text-neutral-400 leading-relaxed">
            The telemetry feed is currently stale or broker connection is inactive. Live options candidate scoring is suspended to prevent routing on delayed price ticks.
          </p>
          <button
            onClick={() => syncBroker(true)}
            className="px-4 py-2 bg-neutral-900 border border-neutral-800 text-xs text-white rounded hover:bg-neutral-800 cursor-pointer font-bold"
          >
            Reconnect & Pull Fresh Feeds
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT COLUMN: Accepted Candidates Grid */}
        <div className="lg:col-span-7 space-y-6">
          <div className={`${themeClasses.card} border rounded-xl p-5 space-y-4`}>
            <div className="flex items-center justify-between border-b border-neutral-900 pb-2">
              <div className="flex items-center gap-2">
                <CheckCircle size={15} className="text-emerald-400" />
                <h3 className="font-mono text-xs font-extrabold uppercase tracking-wider text-neutral-200">
                  Accepted Candidates ({acceptedCandidates.length})
                </h3>
              </div>
            </div>

            <div className="overflow-x-auto rounded border border-neutral-900 bg-neutral-950/20">
              <table className="w-full text-left border-collapse min-w-[500px]">
                <thead>
                  <tr className="border-b border-neutral-900 bg-neutral-900/50 text-[10px] font-mono text-neutral-500 uppercase">
                    <th className="px-4 py-2 text-center">Rank</th>
                    <th className="px-4 py-2">Symbol</th>
                    <th className="px-4 py-2">Strategy</th>
                    <th className="px-4 py-2">Strike</th>
                    <th className="px-4 py-2">Type</th>
                    <th className="px-4 py-2 text-right">Score</th>
                  </tr>
                </thead>
                <tbody className="text-xs font-mono text-neutral-300">
                  {acceptedCandidates.map((cand) => (
                    <tr
                      key={safeString(cand?.candidate_id)}
                      onClick={() => setSelectedCandidateId(safeString(cand?.candidate_id))}
                      className={`border-b border-neutral-900 hover:bg-neutral-900/40 cursor-pointer transition-all ${
                        activeId === cand.candidate_id ? "bg-neutral-900/80 text-white font-bold" : ""
                      }`}
                    >
                      <td className="px-4 py-3 text-center">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                          activeId === cand.candidate_id ? "bg-cyan-950 text-cyan-400" : "bg-neutral-900 text-neutral-500"
                        }`}>
                          #{safeNumber(cand?.rank)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-cyan-400 font-semibold">{safeString(cand?.tradingsymbol)}</td>
                      <td className="px-4 py-3 text-neutral-400">{safeString(cand?.strategy_name)}</td>
                      <td className="px-4 py-3 text-white">{formatNumber(cand?.strike)}</td>
                      <td className={`px-4 py-3 font-black ${safeString(cand?.instrument_type) === "CE" ? "text-emerald-400" : "text-rose-400"}`}>
                        {safeString(cand?.instrument_type)}
                      </td>
                      <td className="px-4 py-3 text-right text-cyan-400 font-bold">{formatNumber(cand?.ranking_score, 1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Strategy Evaluation comparison */}
          <div className={`${themeClasses.card} border rounded-xl p-5 space-y-4`}>
            <div className="flex items-center gap-2 border-b border-neutral-900 pb-2">
              <Target size={15} className="text-emerald-400" />
              <h3 className="font-mono text-xs font-extrabold uppercase tracking-wider text-neutral-200">
                Strategy Suitability Matrix
              </h3>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {(safeArray(evals?.evaluations) as StrategyScore[]).map((item: StrategyScore, idx) => (
                <div key={idx} className="p-3 bg-neutral-900/40 border border-neutral-850 rounded-lg space-y-2">
                  <div className="flex items-center justify-between border-b border-neutral-900 pb-1">
                    <span className="text-xs font-bold text-white font-mono">{safeString(item?.strategy_name)}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-bold ${
                      safeString(item?.suitability_level) === "HIGH" ? "bg-emerald-950/60 text-emerald-400" : "bg-cyan-950/60 text-cyan-400"
                    }`}>
                      {safeString(item?.suitability_level)}
                    </span>
                  </div>
                  <div className="space-y-1">
                    {safeArray(item?.reasons).slice(0, 2).map((r, rIdx) => (
                      <p key={rIdx} className="text-[10px] text-neutral-400 leading-snug flex items-start gap-1 font-mono">
                        <span className="text-cyan-400">•</span>
                        <span>{safeString(r?.message)}</span>
                      </p>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Target setup, Confidence & Reasoning */}
        <div className="lg:col-span-5 space-y-6">
          {activeCandidate && (
            <div className={`${themeClasses.card} border rounded-xl p-5 space-y-4 relative overflow-hidden`}>
              <div className="absolute top-0 right-0 h-24 w-24 bg-cyan-500/2 rounded-full blur-2xl"></div>
              
              <div className="border-b border-neutral-900 pb-2 flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-neutral-400 uppercase">
                  Target Tactical Setup
                </span>
                <span className="text-[9px] font-mono bg-cyan-950/60 text-cyan-400 border border-cyan-800/40 px-2 py-0.5 rounded uppercase font-bold">
                  Active Focus
                </span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                <div className="flex justify-between border-b border-neutral-900 pb-2">
                  <span className="text-neutral-500">Trading Symbol:</span>
                  <span className="text-cyan-400 font-bold">{safeString(activeCandidate.tradingsymbol)}</span>
                </div>
                <div className="flex justify-between border-b border-neutral-900 pb-2">
                  <span className="text-neutral-500">Implied Strategy:</span>
                  <span className="text-white font-bold">{safeString(activeCandidate.strategy_name)}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 pt-2 text-center">
                  <div className="p-2.5 bg-neutral-900/60 border border-neutral-850 rounded-lg">
                    <span className="text-[9px] text-neutral-500 block uppercase font-bold">Entry SL Limit</span>
                    <span className="text-sm font-bold text-white block mt-0.5">{formatCurrency(entryPrice, 1)}</span>
                  </div>
                  <div className="p-2.5 bg-neutral-900/60 border border-neutral-850 rounded-lg">
                    <span className="text-[9px] text-rose-400/80 block uppercase font-bold">Stop Loss</span>
                    <span className="text-sm font-bold text-rose-400 block mt-0.5">{formatCurrency(stopLoss, 1)}</span>
                  </div>
                  <div className="p-2.5 bg-neutral-900/60 border border-neutral-850 rounded-lg">
                    <span className="text-[9px] text-emerald-400/80 block uppercase font-bold">Target Out</span>
                    <span className="text-sm font-bold text-emerald-400 block mt-0.5">{formatCurrency(profitTarget, 1)}</span>
                  </div>
                </div>
              </div>
              
              {activeCandidate?.expiry_reason && (
                <div className="bg-neutral-950/60 p-3 rounded-lg border border-neutral-850 text-neutral-300 leading-relaxed font-sans text-xs mt-3">
                  <span className="font-mono text-[9px] text-cyan-400 block uppercase font-bold mb-1">Expiry Selection Justification:</span>
                  <div className="whitespace-pre-line text-[11px] font-mono leading-relaxed text-neutral-400">{safeString(activeCandidate.expiry_reason)}</div>
                </div>
              )}
            </div>
          )}

          {/* Risk core metrics */}
          <div className={`${themeClasses.card} border rounded-xl p-5 space-y-4`}>
            <div className="flex items-center gap-2 border-b border-neutral-900 pb-2">
              <ShieldAlert size={15} className="text-rose-500" />
              <h3 className="font-mono text-xs font-extrabold uppercase tracking-wider text-neutral-200">
                Risk Engine Thresholds
              </h3>
            </div>
            
            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between items-center border-b border-neutral-900 pb-2">
                <span className="text-neutral-500">Max Risk Per Trade:</span>
                <span className="text-rose-400 font-bold">{formatCurrency(risk?.summary?.max_risk_per_trade_inr)}</span>
              </div>
              <div className="flex justify-between items-center border-b border-neutral-900 pb-2">
                <span className="text-neutral-500">Drawdown Circuit Limit:</span>
                <span className="text-white font-semibold">{formatCurrency(risk?.summary?.drawdown_limit_inr)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-neutral-500">Leverage Safety Cap:</span>
                <span className="text-emerald-400 font-bold">1.50x Max</span>
              </div>
            </div>
          </div>

          {/* AI Confidence & Explanations */}
          <div className={`${themeClasses.card} border rounded-xl p-5 space-y-4`}>
            <div className="flex items-center gap-2 border-b border-neutral-900 pb-2">
              <Sparkles size={15} className="text-cyan-400" />
              <h3 className="font-mono text-xs font-extrabold uppercase tracking-wider text-neutral-200">
                AI Inference Confidence
              </h3>
            </div>

            <div className="space-y-4 font-mono text-xs">
              <div className="flex justify-between items-center">
                <span className="text-neutral-500">Confidence Score:</span>
                <span className="text-emerald-400 font-bold">{formatNumber(confidenceScore, 1)}%</span>
              </div>
              <div className="h-1.5 w-full bg-neutral-900 rounded overflow-hidden">
                <div
                  className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${confidenceScore ?? 0}%` }}
                ></div>
              </div>
              
              {activeDecision?.explanation && (
                <div className="bg-neutral-900/50 p-3 rounded-lg border border-neutral-850 text-neutral-300 leading-relaxed font-sans text-xs">
                  <span className="font-mono text-[9px] text-neutral-500 block uppercase font-bold mb-1">Gemini AI Rationale:</span>
                  {safeString(activeDecision.explanation)}
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
      )}
    </div>
  );
}

export default TradeCenter;
