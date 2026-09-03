/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * CatalystsMatrixView.tsx
 * Master Sprint Directive: Dense, Zero-Gap Bloomberg-Style Macro Balance Sheet with Isolated Inspection Modal.
 * 
 * Architecture:
 * - Top 5-Factor Macro Ribbon: Single unified horizontal ribbon with hairline dividers (grid-cols-5 divide-x)
 * - 2-Column Balanced Ledger: Strictly rigid, equal-height list items (Zero accordion layout drift):
 *   * Left Column (~50%): MARKET UPSIDE TAILWINDS (5 Active Drivers)
 *   * Right Column (~50%): DOWNSIDE VULNERABILITIES & RISK MITIGATION (with inline ↳ Mitigation Guardrails)
 *   * Top-Right Metadata Bar: Source + inline ↗ link | DISCOVERED: DD:MM:YY HH:mm:ss IST | Impact Badge | [ⓘ Inspect]
 * - Isolated Intelligence Modal (fixed inset-0 z-50): Full narrative body, quantitative triggers, historical analog, and source actions without disrupting the underlying grid.
 */

import React, { useState, useEffect, useMemo } from "react";
import {
  TrendingUp,
  AlertTriangle,
  ExternalLink,
  Info,
  X,
  FileText,
  Sparkles,
  ArrowUpRight,
  ShieldCheck,
  Zap,
} from "lucide-react";
import {
  NewsPresentationState,
  formatDiscoveryTimestamp,
} from "../../utils/canonicalNewsAdapter";

export interface CatalystsMatrixViewProps {
  pres: NewsPresentationState;
}

interface CatalystDetailItem {
  id: string;
  type: "TAILWIND" | "RISK";
  title: string;
  publisher: string;
  timestamp: string;
  url: string;
  impact: string;
  transmission: string;
  exposureOrGuardrail: string;
  guardrailLabel?: string;
  narrative: string;
  quantitativeTrigger: string;
  analogReference: string;
}

export const CatalystsMatrixView: React.FC<CatalystsMatrixViewProps> = ({ pres }) => {
  const [activeInspectionCatalyst, setActiveInspectionCatalyst] = useState<CatalystDetailItem | null>(null);

  // Keyboard escape listener to dismiss modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setActiveInspectionCatalyst(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // The 5 macro-force category labels are static, but their state/impact
  // assessments are NOT published in the canonical news presentation. Rather
  // than fabricate "SUPPORTIVE / High" verdicts, each force renders an explicit
  // "AWAITING" state until a real macro-context binding exists.
  const macroForces = useMemo(() => {
    const NEUTRAL = {
      state: "AWAITING",
      impact: "—",
      stateColor: "text-neutral-500",
      impactBadge: "bg-neutral-800/40 text-neutral-400 border-neutral-700/50",
    };
    return [
      { id: "force-1", num: 1, name: "RBI Liquidity & Stance", ...NEUTRAL },
      { id: "force-2", num: 2, name: "US & Global Markets", ...NEUTRAL },
      { id: "force-3", num: 3, name: "Institutional Flows", ...NEUTRAL },
      { id: "force-4", num: 4, name: "Crude Oil & Energy", ...NEUTRAL },
      { id: "force-5", num: 5, name: "USD / INR & FX", ...NEUTRAL },
    ];
  }, []);

  const upsideTailwinds: CatalystDetailItem[] = useMemo(() => {
    const stories = pres?.stories || [];
    const positive = stories.filter((s) => s.expectedDirection === "POSITIVE");
    if (positive.length > 0) {
      return positive.slice(0, 5).map((s) => ({
        id: s.id,
        type: "TAILWIND" as const,
        title: s.headline,
        publisher: s.publisher || "VERIFIED MEDIA",
        timestamp: s.publishedAt,
        url: s.url || "",
        impact: `${s.impactStrength || "HIGH"} IMPACT`,
        transmission: s.whyItMatters || s.summary,
        exposureOrGuardrail: s.affectedSectors?.length ? s.affectedSectors.join(", ") : "Broad Market",
        narrative: s.summary,
        quantitativeTrigger: `Relevance: ${s.niftyRelevance}% · Impact: ${s.impactDuration}`,
        analogReference: `Category: ${s.category.replace(/_/g, " ")}`,
      }));
    }
    return [];
  }, [pres?.stories]);

  const downsideRisks: CatalystDetailItem[] = useMemo(() => {
    const stories = pres?.stories || [];
    const negative = stories.filter((s) => s.expectedDirection === "NEGATIVE" || s.expectedDirection === "MIXED");
    if (negative.length > 0) {
      return negative.slice(0, 5).map((s) => ({
        id: s.id,
        type: "RISK" as const,
        title: s.headline,
        publisher: s.publisher || "VERIFIED MEDIA",
        timestamp: s.publishedAt,
        url: s.url || "",
        impact: `${s.impactStrength || "MEDIUM"} RISK`,
        transmission: s.whyItMatters || s.summary,
        guardrailLabel: "Impact Exposure:",
        exposureOrGuardrail: s.affectedSectors?.length ? s.affectedSectors.join(", ") : "Market Baseline",
        narrative: s.summary,
        quantitativeTrigger: `Relevance: ${s.niftyRelevance}% · Impact: ${s.impactDuration}`,
        analogReference: `Category: ${s.category.replace(/_/g, " ")}`,
      }));
    }
    return [];
  }, [pres?.stories]);

  return (
    <div className="w-full flex flex-col gap-2 font-mono text-left select-none text-xs relative">
      {/* ═════════════════════════════════════════════════════════════
          1. TOP SECTION: 5-FACTOR MACRO FORCES GAUGE (Flat Unified Ribbon)
          ═════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 divide-x divide-neutral-800/80 bg-neutral-900/50 border border-neutral-800/80 rounded-md overflow-hidden w-full">
        {macroForces.map((force) => (
          <div
            key={force.id}
            className="px-2.5 py-1.5 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between text-[10px] text-neutral-400 uppercase font-mono">
              <span>
                {force.num}. {force.name}
              </span>
              <span className={`text-[9px] px-1 py-0.2 rounded font-mono font-medium border ${force.impactBadge}`}>
                {force.impact}
              </span>
            </div>
            <div className={`text-xs font-bold font-mono ${force.stateColor} mt-0.5 truncate`}>
              {force.state}
            </div>
          </div>
        ))}
      </div>

      {/* ═════════════════════════════════════════════════════════════
          2. MAIN BODY: 2-COLUMN BALANCED LEDGER (Rigid & Equal-Height)
          ═════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5 items-stretch">
        {/* ─────────────────────────────────────────────────────────────
            LEFT COLUMN (~50%): MARKET UPSIDE TAILWINDS
            ───────────────────────────────────────────────────────────── */}
        <div className="flex flex-col bg-neutral-900/40 border border-neutral-800 rounded-md p-3">
          {/* Section Header */}
          <div className="flex items-center justify-between border-b border-neutral-800/80 pb-1.5 mb-1">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              MARKET UPSIDE TAILWINDS (5 ACTIVE DRIVERS)
            </span>
            <span className="text-[9.5px] px-1.5 py-0.2 rounded font-mono font-medium border bg-emerald-500/15 text-emerald-300 border-emerald-500/30">
              DOMINANT VECTOR
            </span>
          </div>

          {/* Symmetrical Catalyst Rows */}
          <div className="divide-y divide-neutral-800/60 flex-1 flex flex-col justify-between">
            {upsideTailwinds.length > 0 ? (
              upsideTailwinds.map((tw) => (
                <div
                  key={tw.id}
                  className="py-2 space-y-1 first:pt-1 last:pb-0 rounded px-1 transition-colors hover:bg-neutral-800/20"
                >
                  {/* Metadata Header: Source Name + inline ↗ link | DISCOVERED: DD:MM:YY HH:mm:ss IST | Impact Badge | Inspect Button */}
                  <div className="flex items-center justify-between text-[10px] whitespace-nowrap overflow-x-auto gap-2">
                    <div className="flex items-center gap-1.5 text-neutral-400 shrink-0">
                      <a
                        href={
                          tw.url ||
                          `https://www.google.com/search?q=${encodeURIComponent(
                            tw.title + " " + tw.publisher
                          )}`
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-bold text-cyan-300 hover:text-cyan-200 uppercase transition-colors inline-flex items-center gap-0.5 cursor-pointer"
                      >
                        <span>{tw.publisher}</span>
                        <ExternalLink className="w-2.5 h-2.5 text-cyan-400" />
                      </a>
                      <span className="text-neutral-600">|</span>
                      <span>
                        DISCOVERED:{" "}
                        <span className="text-neutral-300 tabular-nums">
                          {formatDiscoveryTimestamp(tw.timestamp)}
                        </span>
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      <span className="text-[9.5px] px-1.5 py-0.2 rounded font-mono font-medium border bg-emerald-500/15 text-emerald-300 border-emerald-500/30">
                        {tw.impact}
                      </span>
                      <button
                        onClick={() => setActiveInspectionCatalyst(tw)}
                        title="Inspect Catalyst Details"
                        className="p-1 rounded bg-neutral-800/80 border border-neutral-700/80 text-cyan-400 hover:text-cyan-300 hover:border-cyan-500/50 transition-colors inline-flex items-center justify-center cursor-pointer"
                      >
                        <Info className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Title */}
                  <div className="text-xs font-semibold text-neutral-100 leading-snug">
                    {tw.title}
                  </div>

                  {/* Transmission */}
                  <p className="text-[11px] text-neutral-400 leading-tight font-sans">
                    {tw.transmission}
                  </p>

                  {/* Exposure Tag */}
                  <div className="text-[10px] font-mono text-cyan-400 pt-0.5 flex items-center gap-1">
                    <span className="text-neutral-500">Exposure:</span>
                    <span className="text-cyan-300 font-semibold">{tw.exposureOrGuardrail}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 text-center text-neutral-500 font-mono text-xs">
                Awaiting Catalysts Tailwinds Ingestion
              </div>
            )}
          </div>
        </div>

        {/* ─────────────────────────────────────────────────────────────
            RIGHT COLUMN (~50%): DOWNSIDE VULNERABILITIES & RISK MITIGATION
            ───────────────────────────────────────────────────────────── */}
        <div className="flex flex-col bg-neutral-900/40 border border-neutral-800 rounded-md p-3">
          {/* Section Header */}
          <div className="flex items-center justify-between border-b border-neutral-800/80 pb-1.5 mb-1">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              DOWNSIDE VULNERABILITIES &amp; RISK MITIGATION
            </span>
            <span className="text-[9.5px] px-1.5 py-0.2 rounded font-mono font-medium border bg-amber-500/15 text-amber-300 border-amber-500/30">
              CONTAINED RISK
            </span>
          </div>

          {/* Symmetrical Risk Rows with Inline Mitigations */}
          <div className="divide-y divide-neutral-800/60 flex-1 flex flex-col justify-between">
            {downsideRisks.length > 0 ? (
              downsideRisks.map((risk) => (
                <div
                  key={risk.id}
                  className="py-2 space-y-1 first:pt-1 last:pb-0 rounded px-1 transition-colors hover:bg-neutral-800/20"
                >
                  {/* Metadata Header: Source Name + inline ↗ link | DISCOVERED: DD:MM:YY HH:mm:ss IST | Impact Badge | Inspect Button */}
                  <div className="flex items-center justify-between text-[10px] whitespace-nowrap overflow-x-auto gap-2">
                    <div className="flex items-center gap-1.5 text-neutral-400 shrink-0">
                      <a
                        href={
                          risk.url ||
                          `https://www.google.com/search?q=${encodeURIComponent(
                            risk.title + " " + risk.publisher
                          )}`
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-bold text-rose-300 hover:text-rose-200 uppercase transition-colors inline-flex items-center gap-0.5 cursor-pointer"
                      >
                        <span>{risk.publisher}</span>
                        <ExternalLink className="w-2.5 h-2.5 text-rose-400" />
                      </a>
                      <span className="text-neutral-600">|</span>
                      <span>
                        DISCOVERED:{" "}
                        <span className="text-neutral-300 tabular-nums">
                          {formatDiscoveryTimestamp(risk.timestamp)}
                        </span>
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      <span className="text-[9.5px] px-1.5 py-0.2 rounded font-mono font-medium border bg-rose-500/15 text-rose-300 border-rose-500/30">
                        {risk.impact}
                      </span>
                      <button
                        onClick={() => setActiveInspectionCatalyst(risk)}
                        title="Inspect Catalyst Details"
                        className="p-1 rounded bg-neutral-800/80 border border-neutral-700/80 text-rose-400 hover:text-rose-300 hover:border-rose-500/50 transition-colors inline-flex items-center justify-center cursor-pointer"
                      >
                        <Info className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Title */}
                  <div className="text-xs font-semibold text-neutral-100 leading-snug">
                    {risk.title}
                  </div>

                  {/* Transmission */}
                  <p className="text-[11px] text-neutral-400 leading-tight font-sans">
                    {risk.transmission}
                  </p>

                  {/* Inline Mitigation Sub-Row */}
                  <div className="text-[11px] text-emerald-400 font-mono flex items-start gap-1 pt-0.5 leading-tight">
                    <span className="text-emerald-500 shrink-0">↳</span>
                    <span>
                      <strong className="text-emerald-300 font-semibold">{risk.guardrailLabel || "Mitigation:"}</strong>{" "}
                      <span className="text-neutral-300 font-sans">{risk.exposureOrGuardrail}</span>
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 text-center text-neutral-500 font-mono text-xs">
                Awaiting Catalysts Risk Items Ingestion
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ═════════════════════════════════════════════════════════════
          3. ISOLATED INTELLIGENCE MODAL (FIXED INSET OVERLAY · ZERO ACCORDION DRIFT)
          ═════════════════════════════════════════════════════════════ */}
      {activeInspectionCatalyst && (
        <div
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setActiveInspectionCatalyst(null);
            }
          }}
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
        >
          <div className="bg-neutral-900 border border-neutral-700/80 rounded-lg max-w-xl w-full p-5 shadow-2xl flex flex-col gap-3.5 font-mono text-xs text-left animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-neutral-800 pb-2.5">
              <div className="flex items-center gap-2 text-[11px]">
                <span className="font-bold text-neutral-200 uppercase">
                  {activeInspectionCatalyst.publisher}
                </span>
                <span className="text-neutral-600">|</span>
                <span className="text-neutral-400">
                  DISCOVERED:{" "}
                  <span className="text-neutral-200 tabular-nums">
                    {formatDiscoveryTimestamp(activeInspectionCatalyst.timestamp)}
                  </span>
                </span>
                <span
                  className={`text-[9.5px] px-1.5 py-0.2 rounded font-semibold border ${
                    activeInspectionCatalyst.type === "TAILWIND"
                      ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                      : "bg-rose-500/15 text-rose-300 border-rose-500/30"
                  }`}
                >
                  {activeInspectionCatalyst.impact}
                </span>
              </div>

              <button
                onClick={() => setActiveInspectionCatalyst(null)}
                className="text-neutral-400 hover:text-neutral-100 flex items-center gap-1 font-mono text-xs px-2 py-0.5 rounded hover:bg-neutral-800 transition-colors"
              >
                <span>Close</span>
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Headline */}
            <h2 className="text-sm sm:text-base font-bold text-neutral-100 leading-snug font-sans">
              {activeInspectionCatalyst.title}
            </h2>

            {/* Ingested Story Body / Narrative */}
            <div className="bg-neutral-950/70 border border-neutral-800 p-3 rounded space-y-1">
              <span className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider block">
                FULL INGESTED NARRATIVE:
              </span>
              <p className="text-neutral-300 text-[11.5px] leading-relaxed font-sans">
                {activeInspectionCatalyst.narrative}
              </p>
            </div>

            {/* Transmission Pathway */}
            <div className="space-y-1">
              <span className="text-[10px] text-neutral-400 font-semibold uppercase tracking-wider block">
                TRANSMISSION PATHWAY:
              </span>
              <p className="text-neutral-300 text-[11px] leading-relaxed font-sans bg-neutral-950/40 p-2 rounded border border-neutral-800/60">
                {activeInspectionCatalyst.transmission}
              </p>
            </div>

            {/* Quantitative Triggers & Historical Analog Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="bg-neutral-950/60 p-2.5 rounded border border-neutral-800 space-y-1">
                <span className="text-cyan-400 font-semibold text-[10.5px] block uppercase">
                  QUANTITATIVE TRIGGERS:
                </span>
                <span className="text-neutral-200 text-[11px] font-sans block leading-snug">
                  {activeInspectionCatalyst.quantitativeTrigger}
                </span>
              </div>

              <div className="bg-neutral-950/60 p-2.5 rounded border border-neutral-800 space-y-1">
                <span className="text-teal-400 font-semibold text-[10.5px] block uppercase">
                  HISTORICAL ANALOG:
                </span>
                <span className="text-neutral-200 text-[11px] font-sans block leading-snug">
                  {activeInspectionCatalyst.analogReference}
                </span>
              </div>
            </div>

            {/* Exposure or Mitigation Strip */}
            <div className="p-2 bg-neutral-950/50 rounded border border-neutral-800/80 text-[11px] flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="text-neutral-500 font-semibold">
                  {activeInspectionCatalyst.type === "TAILWIND" ? "EXPOSURE:" : "GUARDRAIL:"}
                </span>
                <span
                  className={`font-semibold ${
                    activeInspectionCatalyst.type === "TAILWIND"
                      ? "text-cyan-300"
                      : "text-emerald-300 font-sans"
                  }`}
                >
                  {activeInspectionCatalyst.exposureOrGuardrail}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-2 border-t border-neutral-800">
              <span className="text-[10px] text-neutral-500">
                Press <strong className="text-neutral-400 font-mono">ESC</strong> or click outside to dismiss
              </span>

              <a
                href={
                  activeInspectionCatalyst.url ||
                  `https://www.google.com/search?q=${encodeURIComponent(
                    activeInspectionCatalyst.title + " " + activeInspectionCatalyst.publisher
                  )}`
                }
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 border border-cyan-500/40 hover:border-cyan-400 px-3 py-1 rounded bg-cyan-950/40 font-semibold transition-colors"
              >
                <span>Open Full Source Article</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CatalystsMatrixView;
