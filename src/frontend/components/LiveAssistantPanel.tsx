// src/frontend/components/LiveAssistantPanel.tsx
import React, { useState, useRef, useEffect } from "react";
import { Sparkles, X, Send, Bot, User, ShieldCheck, RefreshCw, Maximize2, Minimize2, ChevronDown, ChevronUp } from "lucide-react";
import { useNavigation } from "../context/NavigationContext";
import { useWorkstationState } from "../context/WorkstationStateContext";

import {
  resolveSessionIdentity,
  resolveCompletedSessionMetrics,
} from "../utils/canonicalSemanticContract";
import { getTemporalSessionContext } from "../utils/temporalSessionResolver";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  metadata?: {
    intent?: string[];
    answer_act?: string;
    evidence_used?: string[];
    freshness?: string;
    provider?: string;
    fallback_used?: boolean;
    data_sufficiency?: string;
    drivers?: string[];
  };
}

function FormattedMarkdown({ content }: { content: string }) {
  if (!content) return null;
  const lines = content.split("\n");

  return (
    <div className="space-y-1.5 leading-relaxed text-[11px] font-medium font-sans text-[#e6e8eb]">
      {lines.map((line, idx) => {
        if (!line.trim()) return <div key={idx} className="h-1" />;
        const formattedLine = line
          .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
          .replace(/`([^`]+)`/g, "<code class='bg-[#191D23] px-1 py-0.5 rounded text-[#38BDF8] font-mono text-[10px]'>$1</code>");

        if (line.trim().startsWith("•") || line.trim().startsWith("-")) {
          return (
            <div key={idx} className="flex items-start gap-1.5 pl-1.5">
              <span className="text-[#38BDF8] font-bold">›</span>
              <span dangerouslySetInnerHTML={{ __html: formattedLine.replace(/^[-•]\s*/, "") }} />
            </div>
          );
        }

        return <p key={idx} dangerouslySetInnerHTML={{ __html: formattedLine }} />;
      })}
    </div>
  );
}

export function LiveAssistantPanel() {
  const { setAssistantOpen, assistantExpanded, toggleAssistantExpanded, activeModule } = useNavigation();
  const { canonicalState, lastValidState, marketContext } = useWorkstationState();

  const state = canonicalState ?? lastValidState;
  const sessionIdentity = resolveSessionIdentity(state, marketContext);
  const compMetrics = resolveCompletedSessionMetrics(state, marketContext);
  const temporalCtx = getTemporalSessionContext(state);
  const isPostMarket = temporalCtx.displayStatus === "POST-MARKET" || (state?.market_session?.status || "").toUpperCase() === "POST_CLOSE";
  const isPreMarket = temporalCtx.displayStatus === "PRE-MARKET";
  const isLive = temporalCtx.displayStatus === "LIVE";
  const sessionStatus = (state?.market_session?.status || temporalCtx.displayStatus || "CLOSED").toUpperCase();

  const [inputPrompt, setInputPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSuggested, setShowSuggested] = useState(true);
  const [showMetadata, setShowMetadata] = useState<Record<string, boolean>>({});

  const welcomeText = isPostMarket
    ? `Today's session (${sessionIdentity.completedSessionDateFormatted}) is complete. ${
        compMetrics.close != null
          ? `Final Close: ${compMetrics.close.toFixed(2)}${compMetrics.change != null ? ` (${compMetrics.change >= 0 ? "+" : ""}${compMetrics.change.toFixed(2)})` : ""}.`
          : "Final close data is not yet available."
      } I can help review today's market drivers, evaluate options positioning, or analyze setups for the next session (${sessionIdentity.nextPlanningTargetDateFormatted}).`
    : isPreMarket
    ? `Good morning. Market Intelligence pre-market baseline for ${sessionIdentity.currentSessionDateFormatted} is active. Ask me about the expected open, options positioning, morning thesis, or key corridor levels.`
    : `ArdhaMind Live Assistant is active and grounded in live canonical session intelligence (${sessionIdentity.currentSessionDateFormatted}). Ask me about current market regime, setup status, PCR, sectors, or execution readiness.`;

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "msg-welcome",
      sender: "assistant",
      text: welcomeText,
      timestamp: new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" }),
      metadata: {
        evidence_used: ["Market State", "Session Resolver", "Completed Session Metrics"],
        freshness: isPostMarket ? "POST_MARKET" : (isPreMarket ? "PRE_MARKET" : "LIVE"),
        provider: "Canonical Engine"
      }
    }
  ]);

  const chatScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages, loading]);

  // Session-Appropriate Dynamic Suggestions
  const quickQuestions = isPostMarket
    ? [
        "Review today's completed session",
        "What drove today's market action?",
        "What is the setup for tomorrow's plan?",
        "What are the key options levels for next session?"
      ]
    : isPreMarket
    ? [
        "What are we expecting at open?",
        "What is the morning bias?",
        "What are the key corridor levels?",
        "Is the broker connected?"
      ]
    : [
        "What is happening now?",
        "Is there a qualified trade?",
        "What is PCR and Max Pain?",
        "Which sectors are leading?"
      ];

  const handleSendQuery = async (text?: string) => {
    const queryText = (text || inputPrompt).trim();
    if (!queryText || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: queryText,
      timestamp: new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" })
    };

    setChatMessages(prev => [...prev, userMsg]);
    if (!text) setInputPrompt("");
    setLoading(true);
    setShowSuggested(false); // Hide suggested pills after conversation begins

    try {
      const response = await fetch("/api/live-assistant/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: queryText,
          conversation_id: "panel_session",
          ui_context: {
            workspace: activeModule,
            session_status: sessionStatus
          }
        }),
      });

      if (response.ok) {
        const result = await response.json();
        let cleanAnswer = (result.answer || "No response received.")
          .replace(/\bNone\b/g, "unavailable")
          .replace(/\bnull\b/g, "unavailable");

        const assistantMsg: ChatMessage = {
          id: `asst-${Date.now()}`,
          sender: "assistant",
          text: cleanAnswer,
          timestamp: new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" }),
          metadata: {
            intent: result.intent,
            answer_act: result.answer_act,
            evidence_used: result.evidence_used,
            freshness: result.freshness,
            provider: result.provider,
            fallback_used: result.fallback_used,
            data_sufficiency: result.data_sufficiency,
            drivers: result.drivers,
          }
        };

        setChatMessages(prev => [...prev, assistantMsg]);
      } else {
        throw new Error(`API response status ${response.status}`);
      }
    } catch (err) {
      console.warn("Live Assistant query failed, using grounded fallback:", err);
      const fallbackMsg: ChatMessage = {
        id: `asst-fb-${Date.now()}`,
        sender: "assistant",
        text: `ArdhaMind canonical evidence confirms ${sessionStatus} session context. Live NIFTY spot or setup information remains available in the primary workspace.`,
        timestamp: new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" }),
        metadata: {
          evidence_used: ["Canonical State Fallback"],
          freshness: sessionStatus,
          provider: "Deterministic Fallback",
          fallback_used: true
        }
      };
      setChatMessages(prev => [...prev, fallbackMsg]);
    } finally {
      setLoading(false);
    }
  };

  const toggleMsgMetadata = (id: string) => {
    setShowMetadata(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <aside
      id="live-assistant-card"
      className={`fixed right-4 top-14 bottom-4 z-40 ${
        assistantExpanded ? "w-[50vw] min-w-[520px] max-w-[calc(100vw-2rem)]" : "w-[440px] max-w-[calc(100vw-2rem)]"
      } bg-[#0E1013] border border-[#242830] rounded-xl shadow-[0_20px_60px_rgba(0,0,0,0.85)] backdrop-blur-md flex flex-col overflow-hidden transition-all duration-200 ease-in-out`}
    >
      {/* ── FLOATING CARD HEADER ── */}
      <div className="px-4 py-3 border-b border-[#242830] bg-[#0B0D10] flex items-center justify-between shrink-0 select-none">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-[#8B5CF6]/15 border border-[#8B5CF6]/30 text-[#8B5CF6]">
            <Sparkles size={15} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-extrabold uppercase tracking-wide text-[#e6e8eb]">
                ARDHAMIND LIVE ASSISTANT
              </h3>
              <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-[#8B5CF6]/20 border border-[#8B5CF6]/30 text-[#8B5CF6]">
                COPILOT
              </span>
            </div>
            <div className="flex items-center gap-2 text-[9px] font-mono text-[#707987]">
              <span className="flex items-center gap-1 text-[#00C896] font-bold">
                <span className="h-1.5 w-1.5 rounded-full bg-[#00C896] animate-pulse" />
                GROUNDED
              </span>
              <span>·</span>
              <span className="uppercase text-[#38BDF8]">
                CONTEXT: {activeModule.replace("_", " ")}
              </span>
            </div>
          </div>
        </div>

        {/* Header Action Buttons */}
        <div className="flex items-center gap-1 text-[#707987]">
          <button
            onClick={toggleAssistantExpanded}
            title={assistantExpanded ? "Collapse to card width" : "Expand to half-screen width"}
            className="p-1.5 rounded-md hover:text-[#e6e8eb] hover:bg-[#13161A] transition cursor-pointer"
          >
            {assistantExpanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          </button>
          <button
            onClick={() => setAssistantOpen(false)}
            title="Close Live Assistant Card"
            className="p-1.5 rounded-md hover:text-[#e6e8eb] hover:bg-[#13161A] transition cursor-pointer"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* ── CONVERSATION THREAD SCROLL AREA ── */}
      <div ref={chatScrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-xs">
        {chatMessages.map(msg => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
          >
            {/* Sender Metadata Line */}
            <div className="flex items-center gap-1 text-[9px] font-mono text-[#707987] mb-1 px-1">
              {msg.sender === "user" ? (
                <><span>TRADER</span><User size={10} /></>
              ) : (
                <>
                  <Bot size={10} className="text-[#8B5CF6]" />
                  <span className="text-[#8B5CF6] font-bold">ARDHAMIND</span>
                </>
              )}
              <span>·</span>
              <span>{msg.timestamp}</span>
            </div>

            {/* Conversational Bubble */}
            <div
              className={`p-3.5 rounded-lg max-w-[92%] leading-relaxed ${
                msg.sender === "user"
                  ? "bg-[#06b6d4]/10 border border-[#06b6d4]/30 text-[#e6e8eb]"
                  : "bg-[#13161A] border border-[#242830] text-[#e6e8eb]"
              }`}
            >
              <FormattedMarkdown content={msg.text} />

              {/* Subordinate Grounding Footer */}
              {msg.metadata && msg.sender === "assistant" && (
                <div className="mt-2.5 pt-2 border-t border-[#242830]/80">
                  <button
                    onClick={() => toggleMsgMetadata(msg.id)}
                    className="flex items-center gap-1.5 text-[8.5px] font-mono text-[#707987] hover:text-[#38BDF8] transition cursor-pointer"
                  >
                    <ShieldCheck size={10} className="text-[#00C896]" />
                    <span>Grounded • {msg.metadata.evidence_used?.length || 1} sources • {msg.metadata.freshness || "LIVE"}</span>
                    {showMetadata[msg.id] ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                  </button>

                  {showMetadata[msg.id] && (
                    <div className="mt-2 p-2 rounded bg-[#0B0D10] border border-[#242830] text-[8.5px] font-mono text-[#A5ABB4] space-y-1">
                      <div><strong>Act:</strong> <span className="text-[#38BDF8]">{msg.metadata.answer_act || "SUMMARY"}</span> | <strong>Sufficiency:</strong> <span className="text-[#00C896]">{msg.metadata.data_sufficiency || "SUFFICIENT"}</span></div>
                      <div><strong>Sources:</strong> {msg.metadata.evidence_used?.join(", ") || "Canonical Evidence"}</div>
                      <div><strong>Provider:</strong> {msg.metadata.provider || "Engine"} {msg.metadata.fallback_used && "[Fallback Active]"}</div>
                      {msg.metadata.drivers && msg.metadata.drivers.length > 0 && <div><strong>Ranked Drivers:</strong> {msg.metadata.drivers.join(" • ")}</div>}
                      {msg.metadata.intent && <div><strong>Intents:</strong> {msg.metadata.intent.join(", ")}</div>}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading Spinner */}
        {loading && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-[#13161A] border border-[#242830] text-[#06b6d4] text-[11px] font-mono w-max">
            <RefreshCw size={12} className="animate-spin" />
            <span>Retrieving canonical evidence &amp; structuring response...</span>
          </div>
        )}
      </div>

      {/* ── SUGGESTED QUESTIONS (Collapsible) ── */}
      <div className="px-4 py-2 bg-[#0B0D10] border-t border-[#242830] shrink-0">
        <div className="flex items-center justify-between mb-1 font-mono">
          <span className="text-[9px] font-bold uppercase text-[#707987]">
            SUGGESTED CONTEXTUAL QUESTIONS
          </span>
          <button
            onClick={() => setShowSuggested(prev => !prev)}
            className="text-[9px] text-[#38BDF8] hover:underline cursor-pointer"
          >
            {showSuggested ? "Hide" : "Show"}
          </button>
        </div>

        {showSuggested && (
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {quickQuestions.map((q, idx) => (
              <button
                key={idx}
                disabled={loading}
                onClick={() => handleSendQuery(q)}
                className="px-2.5 py-1 bg-[#13161A] hover:bg-[#191D23] border border-[#242830] hover:border-[#38BDF8]/40 text-[#e6e8eb] text-[10px] rounded-md transition text-left cursor-pointer disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ── MODERN COMPOSER ── */}
      <div className="p-3 bg-[#0B0D10] border-t border-[#242830] shrink-0 flex gap-2 items-center">
        <input
          type="text"
          value={inputPrompt}
          disabled={loading}
          onChange={e => setInputPrompt(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !loading && handleSendQuery()}
          placeholder="Ask ArdhaMind about session, setups, risk, options..."
          className="flex-1 px-3.5 py-2.5 bg-[#13161A] border border-[#242830] rounded-lg text-xs text-[#e6e8eb] placeholder-[#707987] focus:outline-none focus:border-[#38BDF8] transition"
        />
        <button
          onClick={() => handleSendQuery()}
          disabled={loading || !inputPrompt.trim()}
          className="p-2.5 bg-[#8B5CF6]/20 hover:bg-[#8B5CF6]/30 border border-[#8B5CF6]/40 text-[#8B5CF6] hover:text-white rounded-lg transition disabled:opacity-40 cursor-pointer shrink-0"
        >
          <Send size={15} />
        </button>
      </div>
    </aside>
  );
}

export default LiveAssistantPanel;
