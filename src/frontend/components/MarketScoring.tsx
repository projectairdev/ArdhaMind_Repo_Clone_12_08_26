// src/frontend/components/MarketScoring.tsx
import React from "react";
import { useWorkstationState, useMarketScore } from "../context/WorkstationStateContext";
import { AlertTriangle, BarChart3, CheckSquare, Zap, Activity } from "lucide-react";
import {
  safeNumber,
  safeString,
  formatNumber
} from "../utils/safeHelpers";

export function MarketScoring() {
  const { loading, error, syncBroker } = useWorkstationState();
  const { data: score } = useMarketScore();

  if (loading && !score) {
    return (
      <div id="scoring-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-40 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (error || !score) {
    return (
      <div id="scoring-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertTriangle size={18} />
          <h3 className="font-semibold">Scoring Engine Unresponsive</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Pipeline is offline."}</p>
        <button onClick={() => syncBroker(true)} className="px-3 py-1 bg-slate-900 text-xs text-slate-300 rounded border border-slate-800">
          Reinitialize Scoring
        </button>
      </div>
    );
  }

  // Helper to render score bars
  const ScoreMeter = ({ label, value, max = 100 }: { label: string; value: number; max?: number }) => {
    const safeVal = safeNumber(value);
    const pct = Math.min(100, Math.max(0, (safeVal / max) * 100));
    return (
      <div className="space-y-1">
        <div className="flex justify-between text-xs font-mono">
          <span className="text-slate-400">{label}</span>
          <span className="text-white font-bold">{formatNumber(safeVal, 1)}</span>
        </div>
        <div className="h-1.5 w-full bg-slate-900 rounded overflow-hidden">
          <div
            className={`h-full rounded transition-all duration-500 ${
              pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-cyan-500" : "bg-amber-500"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    );
  };

  const overallTrendScore = safeNumber(score?.trend?.overall_trend_score);
  const overallOptionScore = safeNumber(score?.options?.overall_option_score);

  return (
    <div id="market-scoring" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6">
      {/* Title & Overall Score Banner */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <BarChart3 size={18} className="text-cyan-400" />
          <h3 className="font-bold text-white text-base">Market Scoring Engine</h3>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <span className="text-[10px] font-mono text-slate-500 uppercase block">AGGREGATED INDEX GRADE</span>
            <span className="text-2xl font-mono font-extrabold text-cyan-400">
              {safeString(score?.letter_grade, "N/A")} <span className="text-sm font-semibold text-slate-400">({formatNumber(score?.overall_score, 1)})</span>
            </span>
          </div>
          <span className="px-2.5 py-1.5 text-xs font-mono font-bold bg-slate-900 text-slate-300 border border-slate-800 rounded">
            {safeString(score?.classification, "SIDEWAYS")}
          </span>
        </div>
      </div>

      {/* Grid of Sub-Scores modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* Trend Score */}
        <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-800 space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-emerald-400 border-b border-slate-800 pb-2">
            <Zap size={13} />
            <span>TREND SUB-SCORE: {formatNumber(overallTrendScore, 1)}</span>
          </div>
          <div className="space-y-2">
            <ScoreMeter label="EMA Alignment" value={safeNumber(score?.trend?.ema_alignment_score)} />
            <ScoreMeter label="ADX Power Force" value={safeNumber(score?.trend?.adx_score)} />
            <ScoreMeter label="15m Slope Velocity" value={safeNumber(score?.trend?.slope_score)} />
            <ScoreMeter label="Momentum Indicator" value={safeNumber(score?.trend?.momentum_score)} />
          </div>
        </div>

        {/* Options Score */}
        <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-800 space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-cyan-400 border-b border-slate-800 pb-2">
            <Activity size={13} />
            <span>OPTIONS SUB-SCORE: {formatNumber(overallOptionScore, 1)}</span>
          </div>
          <div className="space-y-2">
            <ScoreMeter label="Put-Call Ratio (PCR)" value={safeNumber(score?.options?.pcr_score)} />
            <ScoreMeter label="Max Pain Proximity" value={safeNumber(score?.options?.max_pain_score)} />
            <ScoreMeter label="OI Structure Build" value={safeNumber(score?.options?.oi_structure_score)} />
            <ScoreMeter label="IV Environments" value={safeNumber(score?.options?.iv_score)} />
          </div>
        </div>

        {/* Volatility & Liquidity */}
        <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-800 space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-amber-400 border-b border-slate-800 pb-2">
            <CheckSquare size={13} />
            <span>VOL / LIQ CONFLUENCE</span>
          </div>
          <div className="space-y-2">
            <ScoreMeter label="ATR Deviation Safety" value={safeNumber(score?.volatility?.overall_volatility_score)} />
            <ScoreMeter label="Orderbook Spreads" value={safeNumber(score?.liquidity?.spread_score)} />
            <ScoreMeter label="Contract Volumes" value={safeNumber(score?.liquidity?.volume_score)} />
            <ScoreMeter label="Expiry Days Factor" value={safeNumber(score?.expiry?.overall_expiry_score)} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default MarketScoring;
