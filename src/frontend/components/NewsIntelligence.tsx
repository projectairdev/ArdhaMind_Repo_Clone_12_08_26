import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { NewsSentimentContext } from "../types";
import { AlertCircle, TrendingUp, TrendingDown, BookOpen, Clock, Activity } from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber,
  formatDate
} from "../utils/safeHelpers";

export function NewsIntelligence() {
  const { newsSentiment: news, syncing: loading, error } = useWorkstationState();

  if (loading) {
    return (
      <div id="news-loading" className="p-6 bg-slate-950 rounded-xl border border-slate-800 animate-pulse space-y-4">
        <div className="h-6 w-1/4 bg-slate-800 rounded"></div>
        <div className="h-32 bg-slate-900 rounded"></div>
      </div>
    );
  }

  if (error || !news) {
    return (
      <div id="news-error" className="p-6 bg-slate-950 rounded-xl border border-rose-950 space-y-3">
        <div className="flex items-center gap-2 text-rose-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold">News Intelligence Down</h3>
        </div>
        <p className="text-xs text-slate-400">{error || "Could not synchronize macro feeds."}</p>
        <button onClick={() => window.location.reload()} className="px-3 py-1.5 bg-slate-900 text-xs text-white border border-slate-800 rounded hover:bg-slate-800">
          Reconnect
        </button>
      </div>
    );
  }

  const overallSentiment = safeNumber(news?.overall_sentiment);
  const sentimentBias = safeString(news?.sentiment_bias, "NEUTRAL");
  const articlesList = safeArray(news?.articles) as any[];

  return (
    <div id="news-intelligence" className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-6">
      {/* Title & Stats */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <BookOpen size={18} className="text-emerald-400" />
          <h3 className="font-bold text-white text-base">News Intelligence Pipeline</h3>
        </div>
        <div className="flex items-center gap-3">
          {/* Sentiment Score badge */}
          <div className="flex items-center gap-2 px-3 py-1 bg-slate-900 rounded border border-slate-800">
            <span className="text-xs text-slate-400 font-mono">Aggregated Sentiment:</span>
            <span className={`text-xs font-mono font-bold flex items-center gap-1 ${
              overallSentiment >= 0.1 ? "text-emerald-400" : overallSentiment <= -0.1 ? "text-rose-400" : "text-slate-400"
            }`}>
              {overallSentiment >= 0.1 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {overallSentiment > 0 ? "+" : ""}{formatNumber(overallSentiment, 2)}
            </span>
          </div>
          {/* Sentiment Bias badge */}
          <span className={`px-2 py-1 text-xs font-mono font-bold rounded border ${
            sentimentBias === "BULLISH"
              ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/50"
              : "bg-rose-950/40 text-rose-400 border-rose-800/50"
          }`}>
            {sentimentBias}
          </span>
        </div>
      </div>

      {/* Panic warning bar */}
      {news?.is_news_panic_active && (
        <div className="flex items-center gap-2 p-3 bg-rose-950/30 border border-rose-800 rounded-lg text-rose-400 text-xs">
          <AlertCircle size={14} className="animate-bounce" />
          <span>NEWS PANIC TRIGGER: Sudden negative macroeconomic shift detected. All option buyers exercise margin buffer halts.</span>
        </div>
      )}

      {/* Articles Stream */}
      <div className="space-y-4">
        <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider">Macro News Stream</h4>
        <div className="grid grid-cols-1 gap-4">
          {articlesList.map((art, idx) => (
            <div key={idx} className="p-4 bg-slate-900/30 hover:bg-slate-900/50 rounded-lg border border-slate-800 transition space-y-2">
              <div className="flex items-start justify-between gap-4">
                <a
                  href={safeString(art?.url)}
                  target="_blank"
                  rel="noreferrer referrer"
                  className="font-medium text-white hover:text-cyan-400 text-sm leading-snug transition"
                >
                  {safeString(art?.headline)}
                </a>
                <span className={`flex-shrink-0 px-1.5 py-0.5 text-[9px] font-mono font-bold rounded ${
                  safeString(art?.severity) === "HIGH" ? "bg-rose-950/60 text-rose-400 border border-rose-800/60" : "bg-slate-800 text-slate-300"
                }`}>
                  {safeString(art?.severity)} IMPACT
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{safeString(art?.summary)}</p>
              {/* Footer details */}
              <div className="flex items-center gap-4 text-[10px] font-mono text-slate-500 pt-1">
                <span className="flex items-center gap-1">
                  <Activity size={10} /> {safeString(art?.source)}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Clock size={10} /> {formatDate(art?.published_at)}
                </span>
                <span>•</span>
                <span className={`font-semibold ${safeNumber(art?.sentiment_score) >= 0.1 ? "text-emerald-400/80" : "text-rose-400/80"}`}>
                  Raw: {safeNumber(art?.sentiment_score) > 0 ? "+" : ""}{formatNumber(art?.sentiment_score, 2)}
                </span>
                <span>•</span>
                <span className="text-slate-400">
                  Decayed: {formatNumber(art?.decayed_sentiment, 2)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default NewsIntelligence;
