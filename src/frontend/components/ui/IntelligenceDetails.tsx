import React, { useRef } from "react";
import { Info } from "lucide-react";
import { useIntelligenceDetails } from "../../context/IntelligenceDetailsContext";

export interface ExplanationEvidence {
  type: "SUPPORTING" | "OPPOSING" | "NEUTRAL" | "UNAVAILABLE";
  symbol: "+" | "-" | "•" | "?";
  factor: string;
  detail: string;
}

export interface IntelligenceExplanation {
  id: string;
  conclusionKey: string;
  label: string;
  value: string;
  badge?: string;
  badgeTone?: "positive" | "negative" | "warning" | "neutral" | "cyan";

  what: {
    summary: string;
    traderMeaning: string;
    currentImplication: string;
  };

  why: {
    summary: string;
    supportingEvidence?: ExplanationEvidence[];
    opposingEvidence?: ExplanationEvidence[];
    neutralEvidence?: ExplanationEvidence[];
    unavailableEvidence?: string[];
    derivation?: string;
  };

  nextTrigger?: string;

  confidence?: {
    score: number | null;
    label: string;
    thresholds?: string;
  };

  risk?: {
    level: string;
    drivers?: string[];
  };

  provenance: {
    sessionDate?: string;
    targetSession?: string;
    observedAt?: string;
    generatedAt?: string;
    freshness?: string;
    stateSequence?: number;
    canonicalSources?: string[];
    methodology?: string;
  };
}

interface IntelligenceDetailsProps {
  explanation?: IntelligenceExplanation | null;
  className?: string;
  buttonClassName?: string;
  ariaLabel?: string;
}

export function IntelligenceDetails({
  explanation,
  className = "",
  buttonClassName = "",
  ariaLabel,
}: IntelligenceDetailsProps) {
  const { openExplanation, activeExplanation } = useIntelligenceDetails();
  const triggerRef = useRef<HTMLButtonElement>(null);

  if (!explanation) return null;

  const accessibleName = ariaLabel || `Explain ${explanation.label || "conclusion"}`;
  const isCurrentActive = activeExplanation?.id === explanation.id || activeExplanation?.conclusionKey === explanation.conclusionKey;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    openExplanation(explanation, triggerRef.current);
  };

  return (
    <div className={`relative inline-flex items-center align-middle ${className}`}>
      <button
        ref={triggerRef}
        type="button"
        onClick={handleClick}
        aria-label={accessibleName}
        aria-haspopup="dialog"
        title={accessibleName}
        className={`group relative p-1 rounded-full transition flex items-center justify-center focus:outline-none focus:ring-1 focus:ring-[#38BDF8] shrink-0 ${
          isCurrentActive
            ? "text-[#38BDF8] bg-[#38BDF8]/20 ring-1 ring-[#38BDF8]"
            : "text-[#707987] hover:text-[#38BDF8] hover:bg-[#191D23]"
        } ${buttonClassName}`}
      >
        <Info size={13} className="pointer-events-none" />
      </button>
    </div>
  );
}

export default IntelligenceDetails;
