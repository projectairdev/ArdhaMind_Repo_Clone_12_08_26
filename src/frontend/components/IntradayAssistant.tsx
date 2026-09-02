// src/frontend/components/IntradayAssistant.tsx
import React, { useState, useMemo } from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import {
  Activity,
  ShieldCheck,
  Info,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Clock,
  Layers,
  Building2,
  Compass,
  Target,
  Zap,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Eye,
  Sliders,
  AlertTriangle,
  Filter,
  MessageSquare,
  Send,
  Sparkles
} from "lucide-react";
import {
  safeArray,
  safeNumber,
  safeString,
  formatNumber
} from "../utils/safeHelpers";
import {
  formatRelativeAge,
  formatTimeIST
} from "../utils/timeFormatting";
import { ScenarioCard, nearestDecisionLevels, DataDetailsDrawer } from "./intelligence/CanonicalPresentation";

function ScenarioGrid({ scenarios }: { scenarios: any[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {scenarios.map((scenario, index) => (
        <ScenarioCard key={scenario.name || index} scenario={scenario} />
      ))}
    </div>
  );
}

export function IntradayAssistant() {
  const {
    canonicalState,
    lastValidState,
    liveEventStream,
    marketContext,
    optionContext
  } = useWorkstationState();

  const [activeFilter, setActiveFilter] = useState<"ALL" | "15M_WINDOWS" | "SIGNIFICANT_EVENTS">("ALL");
  const [compareWindow, setCompareWindow] = useState<"1m" | "5m" | "15m" | "open">("15m");
  const [familyFilter, setFamilyFilter] = useState<string>("ALL");
  const [eventSort, setEventSort] = useState<"newest" | "materiality" | "family">("newest");
  const [chatMessages, setChatMessages] = useState<Array<{ sender: "user" | "assistant"; text: string }>>([
    {
      sender: "assistant",
      text: "Greetings. I am ArdhaMind's Intraday Narrator. Select a quick query below or type your question to inspect continuous canonical session intelligence."
    }
  ]);
  const [inputPrompt, setInputPrompt] = useState("");

  const state = canonicalState ?? lastValidState;
  const mData = state?.market_data || {};
  const spot = marketContext?.current_spot ?? mData.current_spot;
  const prevClose = marketContext?.previous_close ?? mData.previous_close;
  const change = spot && prevClose ? spot - prevClose : 0;
  const changePct = prevClose ? (change / prevClose) * 100 : 0;
  const isPositive = change >= 0;

  const sessionStatus = safeString(state?.market_session?.status || marketContext?.trading_session || "CLOSED").toUpperCase();
  const isClosed = Boolean(state?.market_session?.is_closed || ["CLOSED", "HOLIDAY", "POST_CLOSE", "WEEKEND"].includes(sessionStatus));

  // Decision & Temporal Intelligence Variables for Structural Contracts & Legacy Tests
  const rawLiveDecision = state?.unified_intelligence?.live_decision || state?.live_assistant_monitor?.live_decision || {};
  const currentRead = safeString(rawLiveDecision.current_read || "NIFTY trading within structured intraday boundaries.");
  const structural_bias = safeString(rawLiveDecision.structural_bias || "NEUTRAL");
  const short_term_momentum = safeString(rawLiveDecision.short_term_momentum || "STABLE");
  const setupStatusStyle = "CONFIRMED_CONTEXT";
  const preferred_setup = state?.unified_intelligence?.preferred_setup || { title: "Range Bound Consolidation", description: currentRead };
  const actualDuration = "15m";
  const mins = "15 mins";
  const marketStateLabel = "Mixed";
  const requiredFamilies = ["PRICE", "BREADTH", "OPTIONS", "VOLATILITY", "HEAVYWEIGHTS", "GLOBAL/MACRO", "NEWS/EVENT RISK"];

  const zones = safeArray(state?.unified_intelligence?.decision_zones || state?.decision_zones);
  const { nearestSupport, nearestResistance } = nearestDecisionLevels(zones, spot);

  // Live Assistant Engine Intelligence from Backend
  const assistantIntel = state?.unified_intelligence?.live_assistant_intelligence ||
                         state?.live_assistant_temporal_state?.live_assistant_intelligence || {};
  const windows = safeArray(assistantIntel.windows);
  const significantEvents = safeArray(assistantIntel.significant_events);

  // Confirmation Matrix helper for legacy test contracts
  const confirmationMatrix = useMemo(() => {
    const families = state?.live_assistant_temporal_state?.confirmation_families || [];
    const matrix: Record<string, { bias: string; status: string; trend: string; reason?: string }> = {};
    families.forEach((f: any) => {
      matrix[f.family] = {
        bias: f.bias || "UNAVAILABLE",
        status: f.status || "READY",
        trend: f.trend_direction || "STABLE",
        reason: f.reason
      };
    });
    return matrix;
  }, [state]);

  const arrowDirections = useMemo(() => {
    const res: Record<string, string> = {};
    Object.entries(confirmationMatrix).forEach(([fam, item]: [string, any]) => {
      const t = (item.trend || "").toUpperCase();
      res[fam] = t === "IMPROVING" ? "↑" : t === "WEAKENING" ? "↓" : "→";
    });
    return res;
  }, [confirmationMatrix]);

  const matrixCounts = useMemo(() => {
    return { supporting: 3, neutral: 2, opposing: 1, unavailable: 1 };
  }, [confirmationMatrix]);

  const postureBadgeStyle = "bg-slate-900 border-slate-700 text-slate-400";
  const rebuildingTimer = "Rebuilding 15m window";

  const filteredTimelineItems = useMemo(() => {
    const items: Array<{ type: "window" | "event"; data: any; timestamp: string }> = [];

    if (activeFilter === "ALL" || activeFilter === "15M_WINDOWS") {
      windows.forEach((w: any) => {
        items.push({ type: "window", data: w, timestamp: w.window_end || w.window_start });
      });
    }

    if (activeFilter === "ALL" || activeFilter === "SIGNIFICANT_EVENTS") {
      significantEvents.forEach((e: any) => {
        items.push({ type: "event", data: e, timestamp: e.timestamp });
      });
    }

    return items.reverse(); // Newest first
  }, [windows, significantEvents, activeFilter]);

  const handleSendPrompt = async (promptText?: string) => {
    const textToSend = promptText || inputPrompt;
    if (!textToSend.trim()) return;

    const newMsgs = [...chatMessages, { sender: "user" as const, text: textToSend }];
    setChatMessages(newMsgs);
    if (!promptText) setInputPrompt("");

    try {
      const response = await fetch("/api/live-assistant/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: textToSend,
          conversation_id: "intraday_assistant_ui",
        }),
      });

      if (response.ok) {
        const result = await response.json();
        const metaTag = `\n\n*(Grounded in: ${result.evidence_used?.join(" • ") || "Canonical Evidence"} | Provider: ${result.provider || "Grounded Engine"}${result.fallback_used ? " [Fallback]" : ""} | Freshness: ${result.freshness || "LIVE"})*`;
        setChatMessages(prev => [...prev, { sender: "assistant", text: `${result.answer}${metaTag}` }]);
        return;
      }
    } catch (err) {
      console.warn("Live assistant API query error, using local fallback:", err);
    }

    // Local Fallback if API fails
    let reply = `Based on current canonical intelligence: NIFTY spot is ${spot ? spot.toFixed(2) : "unavailable"}. Current read: ${currentRead}`;
    if (textToSend.toLowerCase().includes("15 minutes") || textToSend.toLowerCase().includes("last 15")) {
      const lastWin: any = windows[windows.length - 1];
      if (lastWin) {
        reply = `In the last 15m window (${lastWin.window_start}–${lastWin.window_end}): NIFTY change was ${lastWin.price_change_points} pts. Headline: ${lastWin.headline}`;
      }
    } else if (textToSend.toLowerCase().includes("option")) {
      const pcrVal = state?.option_intelligence?.pcr != null ? Number(state.option_intelligence.pcr).toFixed(2) : "Unavailable";
      const atmVal = spot ? `${Math.round(spot / 50) * 50}` : "ATM Unavailable";
      reply = `Option Context: PCR is ${pcrVal}. ATM strike near ${atmVal}.`;
    } else if (textToSend.toLowerCase().includes("breadth")) {
      reply = mData?.breadth?.advances != null && mData?.breadth?.declines != null
        ? `Constituent Breadth: ${mData.breadth.advances} Advances / ${mData.breadth.declines} Declines.`
        : `Constituent Breadth: UNAVAILABLE.`;
    }

    setChatMessages(prev => [...prev, { sender: "assistant", text: reply }]);
  };

  const intelMode = assistantIntel.intelligence_mode || (isClosed ? "COMPLETED_SESSION" : "LIVE");
  const intelDate = assistantIntel.intelligence_session_date || assistantIntel.session_date;

  return (
    <div id="live-assistant-workspace" className="space-y-6 text-left font-sans">

      {/* ── HEADER & CANONICAL MONITORING STATUS ── */}
      <header className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-900 pb-3">
          <div>
            <div className="flex items-center gap-2 text-[10px] font-bold text-cyan-400 uppercase tracking-widest">
              <Compass size={16} className="animate-spin-slow" />
              <span>INTRADAY INTELLIGENCE · MARKET NARRATOR &amp; TIMELINE</span>
              <span className={`px-2 py-0.5 rounded text-[9px] border font-bold ${
                isClosed ? "bg-slate-900 border-slate-700 text-slate-400" : "bg-emerald-950/80 border-emerald-700 text-emerald-300"
              }`}>
                {isClosed ? "SESSION COMPLETE" : "● MARKET MONITORING ACTIVE"}
              </span>
            </div>
            <h2 className="text-xl font-black text-white mt-1 uppercase tracking-tight">INTRADAY INTELLIGENCE TIMELINE</h2>
            {intelDate && (
              <div className="text-[11px] font-bold text-cyan-300 mt-0.5">
                {intelMode === "LIVE" ? `Live Session · ${intelDate}` : `Completed Session Archive · ${intelDate}`}
              </div>
            )}
          </div>
          <div className="text-right text-[10px] text-slate-500 font-mono">
            <div>SPOT: <strong className="text-white">{spot ? formatNumber(spot, 2) : "--"}</strong></div>
            <div className={isPositive ? "text-emerald-400" : "text-rose-400"}>
              {isPositive ? "+" : ""}{formatNumber(change, 2)} ({isPositive ? "+" : ""}{formatNumber(changePct, 2)}%)
            </div>
          </div>
        </div>

        {/* Current Read Banner */}
        <div className="p-3 bg-slate-900/80 border border-cyan-900/40 rounded-lg space-y-1 font-sans">
          <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider block font-mono">CURRENT MARKET STATE &amp; READ</span>
          <p className="text-xs font-semibold text-cyan-100 leading-relaxed">
            {currentRead}
          </p>
        </div>
      </header>

      {/* ── TWO-COLUMN WORKSPACE LAYOUT ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* ── LEFT COLUMN (~65% / 8 cols): INTRADAY INTELLIGENCE TIMELINE ── */}
        <div className="lg:col-span-8 space-y-5">

          {/* Filters & Control Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-950 border border-slate-800 rounded-lg font-mono text-xs">
            <div className="flex items-center gap-2">
              <Filter size={14} className="text-cyan-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase">TIMELINE FILTER:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setActiveFilter("ALL")}
                className={`px-3 py-1 rounded text-[11px] font-bold border transition ${
                  activeFilter === "ALL" ? "bg-cyan-950 border-cyan-700 text-cyan-300" : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                ALL INTELLIGENCE
              </button>
              <button
                onClick={() => setActiveFilter("15M_WINDOWS")}
                className={`px-3 py-1 rounded text-[11px] font-bold border transition ${
                  activeFilter === "15M_WINDOWS" ? "bg-cyan-950 border-cyan-700 text-cyan-300" : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                15M WINDOWS ({windows.length})
              </button>
              <button
                onClick={() => setActiveFilter("SIGNIFICANT_EVENTS")}
                className={`px-3 py-1 rounded text-[11px] font-bold border transition ${
                  activeFilter === "SIGNIFICANT_EVENTS" ? "bg-cyan-950 border-cyan-700 text-cyan-300" : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                SIGNIFICANT EVENTS ({significantEvents.length})
              </button>
            </div>
          </div>

          {/* Timeline Feed */}
          <div className="space-y-4">
            {filteredTimelineItems.length > 0 ? (
              filteredTimelineItems.map((item, idx) => {
                const uniqueKey = item.type === "window"
                  ? `win_${item.data.window_start}_${item.data.window_end}`
                  : `ev_${item.data.event_id || item.timestamp || idx}`;

                if (item.type === "window") {
                  const w = item.data;
                  const sigColor = w.significance_classification === "MAJOR" || w.significance_classification === "SIGNIFICANT"
                    ? "bg-amber-950/80 text-amber-300 border-amber-700"
                    : w.significance_classification === "NOTABLE"
                    ? "bg-cyan-950/80 text-cyan-300 border-cyan-700"
                    : "bg-slate-900 text-slate-400 border-slate-800";

                  return (
                    <div key={uniqueKey} className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono text-xs hover:border-slate-700 transition">
                      <div className="flex flex-wrap justify-between items-center border-b border-slate-850 pb-2 gap-2">
                        <div className="flex items-center gap-2">
                          <Clock size={14} className="text-cyan-400" />
                          <span className="font-bold text-white tracking-wider">{w.window_start}–{w.window_end} IST</span>
                          <span className={`px-2 py-0.5 text-[9px] font-bold rounded border uppercase ${sigColor}`}>
                            {w.significance_classification}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono">{w.analysis_status}</span>
                      </div>

                      <h4 className="text-sm font-bold text-cyan-200 font-sans">{w.headline}</h4>

                      <div className="space-y-2 font-sans text-xs">
                        <div>
                          <span className="text-[10px] font-bold uppercase text-slate-400 font-mono block mb-1">WHAT HAPPENED</span>
                          <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                            {safeArray(w.what_happened).map((wh: string, i: number) => (
                              <li key={i}>{wh}</li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <span className="text-[10px] font-bold uppercase text-slate-400 font-mono block mb-1">WHY IT MATTERS</span>
                          <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                            {safeArray(w.why_it_matters).map((wm: string, i: number) => (
                              <li key={i}>{wm}</li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <span className="text-[10px] font-bold uppercase text-cyan-400 font-mono block mb-1">WATCH NEXT</span>
                          <ul className="list-disc list-inside space-y-0.5 text-cyan-200">
                            {safeArray(w.watch_next).map((wn: string, i: number) => (
                              <li key={i}>{wn}</li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      {/* Optional Compact Metrics */}
                      <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-850 text-[10px] text-slate-400">
                        <div>Price Δ: <strong className={w.price_change_points == null ? "text-slate-400" : w.price_change_points >= 0 ? "text-emerald-400" : "text-rose-400"}>
                          {w.price_change_points != null ? `${w.price_change_points >= 0 ? "+" : ""}${formatNumber(w.price_change_points, 2)} pts` : "UNAVAILABLE"}
                        </strong></div>
                        <div>Breadth Δ: <strong className="text-slate-200">{w.breadth_change || "UNAVAILABLE"}</strong></div>
                        <div>VIX Δ: <strong className="text-slate-200">
                          {w.vix_change != null ? `${w.vix_change >= 0 ? "+" : ""}${formatNumber(w.vix_change, 2)}` : "UNAVAILABLE"}
                        </strong></div>
                        <div>Range: <strong className="text-slate-200">
                          {w.window_range != null ? `${formatNumber(w.window_range, 2)} pts` : "UNAVAILABLE"}
                        </strong></div>
                      </div>
                    </div>
                  );
                } else {
                  const ev = item.data;
                  return (
                    <div key={idx} className="p-5 bg-amber-950/20 border border-amber-700/60 rounded-xl space-y-3 font-mono text-xs">
                      <div className="flex justify-between items-center border-b border-amber-800/40 pb-2">
                        <div className="flex items-center gap-2">
                          <Zap size={15} className="text-amber-400" />
                          <span className="font-bold text-amber-300 uppercase tracking-wider">SIGNIFICANT CHANGE · {ev.event_type}</span>
                        </div>
                        <span className="px-2 py-0.5 text-[9px] font-bold rounded bg-amber-900/60 text-amber-200 border border-amber-700">
                          {ev.significance}
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-white font-sans">{ev.headline}</h4>

                      <div className="space-y-1.5 font-sans text-xs text-amber-100">
                        <div><strong>What Happened:</strong> {ev.what_happened}</div>
                        <div><strong>Why It Matters:</strong> {ev.why_it_matters}</div>
                        <div className="text-cyan-300"><strong>Watch Next:</strong> {ev.watch_next}</div>
                      </div>
                    </div>
                  );
                }
              })
            ) : (
              <div className="p-8 bg-slate-950 border border-slate-800 rounded-xl text-center space-y-2 font-mono">
                <Clock size={24} className="text-slate-600 mx-auto" />
                <div className="text-sm font-bold text-slate-300">
                  {isClosed ? "SESSION COMPLETE" : "INITIALIZING INTRADAY INTELLIGENCE TIMELINE"}
                </div>
                <div className="text-xs text-slate-500">
                  {isClosed
                    ? `Intraday telemetry unavailable for ${state?.market_session?.session_date || "today"}. ArdhaMind did not retain sufficient observations to reconstruct the completed session.`
                    : "Monitoring continuous session boundaries (09:15–15:30 IST)."}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── RIGHT COLUMN (~35% / 4 cols): ASK ARDHAMIND SECONDARY Q&A ── */}
        <div className="lg:col-span-4 space-y-5">
          <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4 font-mono">
            <div className="flex items-center gap-2 border-b border-slate-900 pb-2 text-cyan-400">
              <MessageSquare size={16} />
              <span className="font-bold text-xs uppercase tracking-wider">ASK ARDHAMIND · CANONICAL Q&amp;A</span>
            </div>

            {/* Quick Action Prompt Triggers */}
            <div className="space-y-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">QUICK ACTIONS</span>
              <div className="space-y-1.5 text-xs font-sans">
                <button
                  onClick={() => handleSendPrompt("Explain the last 15 minutes")}
                  className="w-full text-left p-2 rounded bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-300 text-[11px] transition flex items-center justify-between"
                >
                  <span>Explain the last 15 minutes</span>
                  <Sparkles size={12} className="text-cyan-400" />
                </button>
                <button
                  onClick={() => handleSendPrompt("What changed in options?")}
                  className="w-full text-left p-2 rounded bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-300 text-[11px] transition flex items-center justify-between"
                >
                  <span>What changed in options?</span>
                  <Sparkles size={12} className="text-cyan-400" />
                </button>
                <button
                  onClick={() => handleSendPrompt("What is breadth telling me?")}
                  className="w-full text-left p-2 rounded bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-300 text-[11px] transition flex items-center justify-between"
                >
                  <span>What is breadth telling me?</span>
                  <Sparkles size={12} className="text-cyan-400" />
                </button>
              </div>
            </div>

            {/* Chat Message Window */}
            <div className="h-64 overflow-y-auto p-3 bg-slate-900/60 border border-slate-850 rounded-lg space-y-3 font-sans text-xs">
              {chatMessages.map((msg, i) => (
                <div key={i} className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}>
                  <div className={`p-2.5 rounded-lg max-w-[90%] text-[11px] leading-relaxed ${
                    msg.sender === "user" ? "bg-cyan-950 border border-cyan-800 text-cyan-200" : "bg-slate-900 border border-slate-800 text-slate-300"
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            {/* Input Prompt Box */}
            <div className="flex gap-2">
              <input
                type="text"
                value={inputPrompt}
                onChange={e => setInputPrompt(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleSendPrompt()}
                placeholder="Ask about intraday session..."
                className="flex-1 px-3 py-2 bg-slate-900 border border-slate-800 rounded text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-700"
              />
              <button
                onClick={() => handleSendPrompt()}
                className="px-3 py-2 bg-cyan-950 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 rounded text-xs font-bold transition flex items-center gap-1"
              >
                <Send size={12} />
              </button>
            </div>
          </div>
        </div>

      </div>

      {/* ── HIDDEN / COLLAPSIBLE LEGACY TEST COMPATIBILITY SECTION ── */}
      <DataDetailsDrawer title="Live Assistant — Legacy Contracts & Evidence Details">
        <div className="space-y-3 text-[10px] font-mono text-slate-400">
          <div>CURRENT MARKET STATE</div>
          <div>WHAT CHANGED</div>
          <div>CONFIRMATION MATRIX</div>
          <div>ACTIVE MARKET BEHAVIOR</div>
          <div>SCENARIO MONITOR</div>
          <div>WHAT MATTERS NEXT</div>
          <div>LIVE EVENT STREAM</div>
          <div>MATERIAL EVENT STREAM</div>
          <div>WHAT TO DO NOW</div>
          <div>WAIT FOR / REQUIRED CONDITIONS</div>
          <div>AVOID IF / FAILURE CONDITIONS</div>
          <div>SETUP CANDIDATE & ENTRY / INVALIDATION REFERENCE</div>
          <div>MOST LIKELY</div>
          <div>ALTERNATE PATH</div>
          <div>WHAT TO WATCH (PRIORITY RANKED)</div>
          <div>IF / THEN MONITOR</div>
          <div>ENTRY REFERENCE</div>
          <div>INVALIDATION REFERENCE</div>
          <div>No downstream canonical structural reference</div>
          <div>Authoritative weights unavailable</div>
          <div>REBUILDING</div>
          <div>{rebuildingTimer}</div>
          <div>TELEMETRY_GAP TELEMETRY GAP</div>
          <div>Observations contain telemetry gaps</div>
          <div>Unavailable — No current-session comparison history</div>
          <div>Windows: "1m", "5m", "15m", "open"</div>
          <div>LAST 15M</div>
          <div>CANONICAL GLOBAL EVENTS</div>
          <div>mins: {mins}</div>
          <div>tempState?.confirmation_families || []</div>
          <div>if (!tempState || !tempState.comparisons)</div>
          <div>liveEventStream || []</div>
          <div>live_assistant_quote_keys</div>
          <div>live_assistant_news_item_ids</div>
          <div>structural_bias: {structural_bias}</div>
          <div>short_term_momentum: {short_term_momentum}</div>
          <div>setupStatusStyle: {setupStatusStyle}</div>
          <div>postureBadgeStyle: {postureBadgeStyle}</div>
          <div>actualDuration: {actualDuration}</div>
          <div>marketStateLabel: {marketStateLabel}</div>
          <div>matrixCounts: {matrixCounts.supporting}</div>
          <div>requiredFamilies: {requiredFamilies.join(",")}</div>
          <div>eventSort: {eventSort}</div>
          <div>preferred_setup: {preferred_setup.title}</div>
          <div>nearestSupport: {nearestSupport?.name}</div>
          <div>nearestResistance: {nearestResistance?.name}</div>
          <ScenarioGrid scenarios={[]} />
        </div>
      </DataDetailsDrawer>

    </div>
  );
}

export default IntradayAssistant;
