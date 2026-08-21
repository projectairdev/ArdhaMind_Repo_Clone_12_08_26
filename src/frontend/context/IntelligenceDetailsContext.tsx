import React, { createContext, useContext, useState, useRef, useEffect, ReactNode } from "react";
import { createPortal } from "react-dom";
import { X, ChevronRight, ChevronDown, CheckCircle2, AlertTriangle, Shield, Info, HelpCircle } from "lucide-react";
import { IntelligenceExplanation, ExplanationEvidence } from "../components/ui/IntelligenceDetails";

interface IntelligenceDetailsContextValue {
  activeExplanation: IntelligenceExplanation | null;
  openExplanation: (explanation: IntelligenceExplanation, triggerElement?: HTMLElement | null) => void;
  closeExplanation: () => void;
  isOpen: boolean;
}

const IntelligenceDetailsContext = createContext<IntelligenceDetailsContextValue | undefined>(undefined);

export function useIntelligenceDetails() {
  const context = useContext(IntelligenceDetailsContext);
  if (!context) {
    throw new Error("useIntelligenceDetails must be used within an IntelligenceDetailsProvider");
  }
  return context;
}

interface IntelligenceDetailsProviderProps {
  children: ReactNode;
}

export function IntelligenceDetailsProvider({ children }: IntelligenceDetailsProviderProps) {
  const [activeExplanation, setActiveExplanation] = useState<IntelligenceExplanation | null>(null);
  const [showAllEvidence, setShowAllEvidence] = useState(false);
  const [showMethodology, setShowMethodology] = useState(false);
  const [showProvenance, setShowProvenance] = useState(false);

  const triggerRef = useRef<HTMLElement | null>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const openExplanation = (explanation: IntelligenceExplanation, triggerElement?: HTMLElement | null) => {
    if (triggerElement) {
      triggerRef.current = triggerElement;
    }
    setActiveExplanation(explanation);
    setShowAllEvidence(false);
    setShowMethodology(false);
    setShowProvenance(false);
  };

  const closeExplanation = () => {
    setActiveExplanation(null);
    if (triggerRef.current) {
      triggerRef.current.focus();
    }
  };

  // Keyboard Escape & focus management
  useEffect(() => {
    if (!activeExplanation) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        closeExplanation();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    setTimeout(() => {
      closeButtonRef.current?.focus();
    }, 40);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [activeExplanation]);

  const getBadgeStyle = (tone?: string) => {
    switch (tone) {
      case "positive":
        return "bg-[#00C896]/15 text-[#00C896] border-[#00C896]/30";
      case "negative":
        return "bg-[#E5484D]/15 text-[#E5484D] border-[#E5484D]/30";
      case "warning":
        return "bg-[#E59700]/15 text-[#E59700] border-[#E59700]/30";
      case "cyan":
        return "bg-[#38BDF8]/15 text-[#38BDF8] border-[#38BDF8]/30";
      default:
        return "bg-[#242830] text-[#A5ABB4] border-[#343A46]";
    }
  };

  // Combine and sort evidence: Opposing first (failed gates), then Supporting, then Neutral, then Unavailable
  const allEvidence: ExplanationEvidence[] = activeExplanation
    ? [
        ...(activeExplanation.why.opposingEvidence || []),
        ...(activeExplanation.why.supportingEvidence || []),
        ...(activeExplanation.why.neutralEvidence || []),
      ]
    : [];

  const visibleEvidence = showAllEvidence ? allEvidence : allEvidence.slice(0, 4);
  const hasMoreEvidence = allEvidence.length > 4;

  return (
    <IntelligenceDetailsContext.Provider
      value={{
        activeExplanation,
        openExplanation,
        closeExplanation,
        isOpen: activeExplanation !== null,
      }}
    >
      {children}

      {/* Global Lightweight Inspector Drawer Portal */}
      {activeExplanation &&
        typeof document !== "undefined" &&
        createPortal(
          <div
            className="fixed inset-0 z-[9999] flex justify-end"
            role="dialog"
            aria-modal="true"
            aria-label={`Explain ${activeExplanation.label}`}
          >
            {/* Extremely subtle transparent backdrop - no blur, background cards stay fully visible */}
            <div
              className="fixed inset-0 bg-black/20 transition-opacity animate-in fade-in duration-150"
              onClick={closeExplanation}
              aria-hidden="true"
            />

            {/* Compact Right-Side Inspector Drawer (~440px wide) */}
            <div
              ref={drawerRef}
              className="relative z-10 w-full sm:w-[440px] max-w-[92vw] h-full bg-[#0B0D10] border-l border-[#242830] shadow-2xl flex flex-col font-mono text-[#E6E8EB] overflow-hidden animate-in slide-in-from-right duration-150 ease-out"
            >
              {/* 1. Compact Sticky Header (~70px) */}
              <div className="flex items-center justify-between border-b border-[#242830] bg-[#0E1013] px-3.5 py-2.5 shrink-0">
                <div className="space-y-0.5 min-w-0 pr-2">
                  <div className="text-[9px] font-bold uppercase text-[#707987] tracking-wider truncate">
                    INSPECTOR • {activeExplanation.label}
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs sm:text-sm font-extrabold text-[#E6E8EB] truncate">
                      {activeExplanation.value}
                    </span>
                    {activeExplanation.badge && (
                      <span
                        className={`text-[8.5px] font-bold px-1.5 py-0.2 rounded border ${getBadgeStyle(
                          activeExplanation.badgeTone
                        )}`}
                      >
                        {activeExplanation.badge}
                      </span>
                    )}
                  </div>
                </div>

                <button
                  ref={closeButtonRef}
                  onClick={closeExplanation}
                  aria-label="Close explainability inspector"
                  className="p-1 rounded text-[#707987] hover:text-[#E6E8EB] hover:bg-[#191D23] transition focus:outline-none focus:ring-1 focus:ring-[#38BDF8] shrink-0"
                >
                  <X size={15} />
                </button>
              </div>

              {/* 2. Scrollable Body with Clean Density */}
              <div className="flex-1 overflow-y-auto p-3.5 space-y-3 text-left">
                {/* WHAT DOES THIS MEAN? */}
                <div className="space-y-1 bg-[#0E1013] p-2.5 rounded border border-[#191D23]">
                  <div className="text-[9px] font-bold uppercase text-[#38BDF8] tracking-wider flex items-center gap-1">
                    <ChevronRight size={11} />
                    <span>WHAT DOES THIS MEAN?</span>
                  </div>
                  <p className="text-[10.5px] text-[#E6E8EB] leading-snug font-sans pl-1">
                    {activeExplanation.what.summary}
                  </p>
                  {activeExplanation.what.currentImplication && (
                    <div className="text-[9.5px] text-[#00C896] bg-[#00C896]/10 px-2 py-1.5 rounded border border-[#00C896]/20 font-mono mt-1">
                      <strong>Implication: </strong>
                      {activeExplanation.what.currentImplication}
                    </div>
                  )}
                </div>

                {/* WHY ARDHAMIND REACHED THIS CONCLUSION */}
                <div className="space-y-1.5 bg-[#0E1013] p-2.5 rounded border border-[#191D23]">
                  <div className="text-[9px] font-bold uppercase text-[#E59700] tracking-wider flex items-center gap-1">
                    <ChevronRight size={11} />
                    <span>WHY</span>
                  </div>

                  {activeExplanation.why.summary && (
                    <p className="text-[10px] text-[#A5ABB4] leading-snug font-sans pl-1">
                      {activeExplanation.why.summary}
                    </p>
                  )}

                  {/* Compact Evidence Rows */}
                  <div className="space-y-1 text-[9.5px] pt-0.5">
                    {visibleEvidence.map((item, idx) => (
                      <div
                        key={idx}
                        className={`flex items-start justify-between gap-1.5 p-1.5 rounded border ${
                          item.type === "SUPPORTING"
                            ? "bg-[#08090B] border-[#00C896]/20"
                            : item.type === "OPPOSING"
                            ? "bg-[#08090B] border-[#E5484D]/20"
                            : "bg-[#08090B] border-[#191D23]"
                        }`}
                      >
                        <div className="flex items-start gap-1.5 min-w-0">
                          <span
                            className={`font-bold shrink-0 ${
                              item.type === "SUPPORTING"
                                ? "text-[#00C896]"
                                : item.type === "OPPOSING"
                                ? "text-[#E5484D]"
                                : "text-[#E59700]"
                            }`}
                          >
                            {item.symbol}
                          </span>
                          <div className="min-w-0">
                            <span className="font-bold text-[#E6E8EB]">{item.factor}: </span>
                            <span className="text-[#A5ABB4] font-sans">{item.detail}</span>
                          </div>
                        </div>
                        <span
                          className={`text-[7.5px] font-bold px-1 py-0.2 rounded shrink-0 ${
                            item.type === "SUPPORTING"
                              ? "bg-[#00C896]/15 text-[#00C896]"
                              : item.type === "OPPOSING"
                              ? "bg-[#E5484D]/15 text-[#E5484D]"
                              : "bg-[#E59700]/15 text-[#E59700]"
                          }`}
                        >
                          {item.type}
                        </span>
                      </div>
                    ))}

                    {/* Expand/Collapse Toggle for extra evidence */}
                    {hasMoreEvidence && (
                      <button
                        onClick={() => setShowAllEvidence(!showAllEvidence)}
                        className="text-[8.5px] text-[#38BDF8] hover:underline pt-0.5 pl-1 flex items-center gap-0.5"
                      >
                        {showAllEvidence
                          ? "▲ Show fewer evidence rows"
                          : `▼ View all evidence (+${allEvidence.length - 4} more)`}
                      </button>
                    )}
                  </div>
                </div>

                {/* NEXT TRIGGER / WHAT CHANGES THIS VIEW (If applicable) */}
                {activeExplanation.nextTrigger && (
                  <div className="bg-[#13161A] p-2.5 rounded border border-[#38BDF8]/30 space-y-0.5 text-[9.5px]">
                    <div className="text-[8px] font-bold uppercase text-[#38BDF8] tracking-wider">
                      NEXT QUALIFICATION TRIGGER
                    </div>
                    <div className="text-[#E6E8EB] font-semibold">{activeExplanation.nextTrigger}</div>
                  </div>
                )}

                {/* CONFIDENCE & RISK COMPACT ROW */}
                {(activeExplanation.confidence || activeExplanation.risk) && (
                  <div className="grid grid-cols-2 gap-2 bg-[#0E1013] p-2.5 rounded border border-[#191D23] text-[9.5px]">
                    {activeExplanation.confidence && (
                      <div className="space-y-0.5">
                        <div className="text-[8px] font-bold uppercase text-[#707987]">CONFIDENCE</div>
                        <div className="text-xs font-bold text-[#E6E8EB]">
                          {activeExplanation.confidence.score != null
                            ? `${activeExplanation.confidence.score}% (${activeExplanation.confidence.label})`
                            : activeExplanation.confidence.label}
                        </div>
                      </div>
                    )}

                    {activeExplanation.risk && (
                      <div className="space-y-0.5">
                        <div className="text-[8px] font-bold uppercase text-[#707987]">RISK LEVEL</div>
                        <div className="text-xs font-bold text-[#E59700]">{activeExplanation.risk.level}</div>
                      </div>
                    )}
                  </div>
                )}

                {/* COLLAPSIBLE 1: TECHNICAL DETAILS & METHODOLOGY */}
                <div className="border border-[#191D23] rounded bg-[#0E1013] overflow-hidden text-[9px]">
                  <button
                    onClick={() => setShowMethodology(!showMethodology)}
                    className="w-full flex items-center justify-between p-2 text-left text-[#707987] hover:text-[#E6E8EB] hover:bg-[#13161A] transition"
                  >
                    <span className="font-bold uppercase tracking-wider">VIEW TECHNICAL DETAILS &amp; METHODOLOGY</span>
                    {showMethodology ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                  </button>

                  {showMethodology && (
                    <div className="p-2.5 border-t border-[#191D23] space-y-1.5 text-[#A5ABB4] font-sans">
                      {activeExplanation.why.derivation && (
                        <div>
                          <strong className="text-[#E6E8EB] font-mono">Engine Rule / Derivation: </strong>
                          <span className="font-mono text-[#707987]">{activeExplanation.why.derivation}</span>
                        </div>
                      )}
                      {activeExplanation.confidence?.thresholds && (
                        <div>
                          <strong className="text-[#E6E8EB] font-mono">Confidence Thresholds: </strong>
                          <span className="font-mono text-[#707987]">{activeExplanation.confidence.thresholds}</span>
                        </div>
                      )}
                      {activeExplanation.provenance.methodology && (
                        <div>
                          <strong className="text-[#E6E8EB] font-mono">Methodology: </strong>
                          <span>{activeExplanation.provenance.methodology}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* COLLAPSIBLE 2: SOURCE & PROVENANCE */}
                <div className="border border-[#191D23] rounded bg-[#0E1013] overflow-hidden text-[9px]">
                  <button
                    onClick={() => setShowProvenance(!showProvenance)}
                    className="w-full flex items-center justify-between p-2 text-left text-[#707987] hover:text-[#E6E8EB] hover:bg-[#13161A] transition"
                  >
                    <span className="font-bold uppercase tracking-wider">VIEW SOURCE &amp; PROVENANCE</span>
                    {showProvenance ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                  </button>

                  {showProvenance && (
                    <div className="p-2.5 border-t border-[#191D23] space-y-1 text-[#A5ABB4]">
                      {activeExplanation.provenance.sessionDate && (
                        <div>Ref Session: <span className="text-[#E6E8EB]">{activeExplanation.provenance.sessionDate}</span></div>
                      )}
                      {activeExplanation.provenance.targetSession && (
                        <div>Target Session: <span className="text-[#00C896]">{activeExplanation.provenance.targetSession}</span></div>
                      )}
                      {activeExplanation.provenance.freshness && (
                        <div>Freshness: <span className="text-[#E6E8EB]">{activeExplanation.provenance.freshness}</span></div>
                      )}
                      {activeExplanation.provenance.canonicalSources && (
                        <div>Sources: <span className="text-[#E6E8EB]">{activeExplanation.provenance.canonicalSources.join(" • ")}</span></div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* 3. Minimal Bottom Action Bar */}
              <div className="border-t border-[#242830] bg-[#0E1013] px-3.5 py-2 flex items-center justify-between text-[9px] text-[#707987] shrink-0">
                <span>Press ESC to close</span>
                <button
                  onClick={closeExplanation}
                  className="px-2 py-0.5 rounded bg-[#191D23] hover:bg-[#242830] text-[#E6E8EB] font-bold transition focus:outline-none"
                >
                  Close
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </IntelligenceDetailsContext.Provider>
  );
}
