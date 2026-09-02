/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Phase-Specific Supporting Panels:
 * - OvernightGlobalCuesPanel (Pre-Market / Pre-Open)
 * - PreMarketPlanPanel (Pre-Market)
 * - PostMarketSummaryPanel (Post-Market / EOD)
 * - NearCloseWatchPanel (Near-Close)
 */

import React, { useState } from "react";
import { CanonicalMorningPlan, CanonicalTomorrowPlan } from "../../../types/canonical";
import { Globe, CheckSquare, Moon, Clock, Award, Shield, AlertTriangle, ArrowRight, Zap } from "lucide-react";

// 1. Overnight & Global Cues Panel (Pre-Market / Pre-Open)
export function OvernightGlobalCuesPanel({ cues }: { cues?: Array<{ name: string; value: string; change: string; isPos: boolean }> }) {
  const hasCues = cues && cues.length > 0;

  return (
    <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3.5 font-mono">
      <div className="flex items-center justify-between border-b border-[#1C2128] pb-2 mb-2.5 text-[10.5px]">
        <div className="flex items-center gap-1.5 font-bold text-[#8B949E] uppercase">
          <Globe className="w-3.5 h-3.5 text-[#38BDF8]" />
          <span>GLOBAL CUES & OVERNIGHT CONTEXT</span>
        </div>
        <span className="px-1.5 py-0.5 rounded bg-[#161A22] text-[#38BDF8] text-[9.5px] font-bold">
          {hasCues ? "MACRO FEED ACTIVE" : "AWAITING MACRO FEED"}
        </span>
      </div>

      {hasCues ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          {cues.map((c, i) => (
            <div key={i} className="rounded bg-[#12151A] p-2 border border-[#20252E]">
              <span className="text-[9.5px] text-[#707987] block truncate">{c.name}</span>
              <div className="flex items-baseline justify-between mt-0.5">
                <span className="font-bold text-[#E6E8EB] text-[11px]">{c.value}</span>
                <span className={`font-bold text-[10px] ${c.isPos ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                  {c.change}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-4 text-center text-xs text-neutral-500">
          Awaiting real-time global indices and institutional macro tape feed.
        </div>
      )}
    </div>
  );
}

// 2. Pre-Market Plan & Checklist Panel (Pre-Market)
export function PreMarketPlanPanel({
  plan,
}: {
  plan?: CanonicalMorningPlan;
}) {
  const [checkedState, setCheckedState] = useState<Record<number, boolean>>({});

  const toggleCheck = (idx: number) => {
    setCheckedState((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const checklist = plan?.first_15m_checklist || [
    "Confirm opening price & gap stability vs reference close",
    "Track opening range high and low (09:15–09:30 IST)",
    "Watch key structural pivot levels & settled VWAP",
    "Monitor market breadth & heavyweight sector participation",
    "Align with global cues & institutional tape conviction",
    "Execute only on confirmed trigger condition & defined risk",
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono">
      {/* Plan for the open */}
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3.5 space-y-2">
        <div className="flex items-center justify-between border-b border-[#1C2128] pb-2 text-[10.5px]">
          <span className="font-bold text-[#8B949E] uppercase">PRE-MARKET STRATEGIC PLAN</span>
          <span className="text-[#38BDF8] text-[9.5px] font-bold">PLAN FIRST</span>
        </div>

        <div className="space-y-2 text-xs">
          <div className="rounded bg-[#00C896]/5 p-2 border border-[#00C896]/20">
            <span className="font-bold text-[#00C896] block text-[10.5px]">▲ BULLISH SCENARIO</span>
            <p className="text-[#D1D5DB] text-[11px] mt-0.5">
              {plan?.bullish_scenario?.trigger || "Sustain above opening reference and break above 15m Opening Range High with breadth expansion."}
            </p>
          </div>

          <div className="rounded bg-[#EF4444]/5 p-2 border border-[#EF4444]/20">
            <span className="font-bold text-[#EF4444] block text-[10.5px]">▼ BEARISH SCENARIO</span>
            <p className="text-[#D1D5DB] text-[11px] mt-0.5">
              {plan?.bearish_scenario?.trigger || "Breakdown below opening support and sustained rejection below 15m Opening Range Low."}
            </p>
          </div>
        </div>
      </div>

      {/* Interactive First 15-Minute Checklist */}
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3.5">
        <div className="flex items-center justify-between border-b border-[#1C2128] pb-2 mb-2 text-[10.5px]">
          <div className="flex items-center gap-1.5 font-bold text-[#8B949E] uppercase">
            <CheckSquare className="w-3.5 h-3.5 text-[#00C896]" />
            <span>FIRST 15 MINUTES CHECKLIST (09:15 – 09:30)</span>
          </div>
        </div>

        <div className="space-y-1.5 text-xs">
          {checklist.map((item, idx) => (
            <label
              key={idx}
              className="flex items-start gap-2 p-1.5 rounded hover:bg-[#14171E] transition cursor-pointer"
            >
              <input
                type="checkbox"
                checked={Boolean(checkedState[idx])}
                onChange={() => toggleCheck(idx)}
                className="mt-0.5 accent-[#00C896] cursor-pointer"
              />
              <span className={`text-[11px] leading-relaxed ${checkedState[idx] ? "text-[#00C896] line-through opacity-70" : "text-[#E6E8EB]"}`}>
                {item}
              </span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}

// 3. Post-Market Summary & Debrief Panel (Post-Market)
export function PostMarketSummaryPanel({
  plan,
}: {
  plan?: CanonicalTomorrowPlan;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono">
      {/* What Drove the Session */}
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3.5 space-y-2">
        <div className="border-b border-[#1C2128] pb-2 text-[10.5px] font-bold text-[#8B949E] uppercase">
          WHAT DROVE THE SESSION
        </div>
        <div className="space-y-1.5 text-xs text-[#D1D5DB]">
          <p className="text-[11px]"><strong className="text-[#00C896]">Key Positives:</strong> BFSI & PSU Banks showed relative strength early in morning session.</p>
          <p className="text-[11px]"><strong className="text-[#EF4444]">Key Negatives:</strong> Global cues weak, FII selling broke VWAP support (24,350), IT and Realty declined.</p>
          <p className="text-[11px]"><strong className="text-[#38BDF8]">Key Takeaway:</strong> Distribution day with lower highs; defensive sectors outperformed.</p>
        </div>
      </div>

      {/* Important News Timeline */}
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3.5 space-y-2">
        <div className="border-b border-[#1C2128] pb-2 text-[10.5px] font-bold text-[#8B949E] uppercase">
          IMPORTANT NEWS (TIMELINE)
        </div>
        <div className="space-y-1.5 text-xs text-[#A5ABB4]">
          <div className="flex gap-2">
            <span className="text-[#38BDF8] font-bold shrink-0">15:32</span>
            <span>RBI keeps repo rate unchanged at 6.50%</span>
          </div>
          <div className="flex gap-2">
            <span className="text-[#38BDF8] font-bold shrink-0">14:18</span>
            <span>India Q1 GDP growth comes in at 6.7% vs 6.5% est</span>
          </div>
          <div className="flex gap-2">
            <span className="text-[#38BDF8] font-bold shrink-0">12:45</span>
            <span>Global cues mixed; US markets trade lower</span>
          </div>
        </div>
      </div>

      {/* Tomorrow Reference / Carry Forward */}
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3.5 space-y-2">
        <div className="border-b border-[#1C2128] pb-2 text-[10.5px] font-bold text-[#8B949E] uppercase">
          TOMORROW REFERENCE (CARRY FORWARD)
        </div>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between">
            <span className="text-[#707987]">TREND BIAS:</span>
            <span className="font-bold text-[#EF4444]">NEUTRAL TO WEAK</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#707987]">EXPECTED RANGE:</span>
            <span className="font-bold text-[#E6E8EB]">24,050 – 24,650</span>
          </div>
          <div className="pt-1.5 border-t border-[#1C2128] text-[10.5px] text-[#8B949E]">
            Key Pivot: <strong className="text-[#F59E0B]">24,350</strong> | Critical Support: <strong className="text-[#00C896]">24,100</strong>
          </div>
        </div>
      </div>
    </div>
  );
}

// 4. Near-Close Watch Panel (Near-Close)
export function NearCloseWatchPanel() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono">
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3.5 space-y-2">
        <div className="border-b border-[#1C2128] pb-2 text-[10.5px] font-bold text-[#8B949E] uppercase">
          WHAT TO WATCH INTO THE CLOSE
        </div>
        <div className="space-y-1 text-xs text-[#D1D5DB]">
          <p className="text-[11px]">• Nifty holding firmly above VWAP (24,506); watch 24,580 breakout.</p>
          <p className="text-[11px]">• Bank Nifty near day's highs; PSU banks leading intraday volume.</p>
          <p className="text-[11px]">• Close above 24,540 sets up higher open structure for next session.</p>
        </div>
      </div>

      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3.5 space-y-2">
        <div className="border-b border-[#1C2128] pb-2 text-[10.5px] font-bold text-[#8B949E] uppercase">
          LIKELY DAY CHARACTER
        </div>
        <div className="text-xs">
          <span className="text-base font-bold text-[#00C896] block">TREND DAY (UP)</span>
          <p className="text-[#A5ABB4] text-[11px] mt-1 leading-relaxed">
            Strong buying from open, pullbacks bought aggressively, trend held through afternoon.
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3.5 space-y-2">
        <div className="border-b border-[#1C2128] pb-2 text-[10.5px] font-bold text-[#8B949E] uppercase">
          CLOSING STRENGTH
        </div>
        <div className="text-xs">
          <span className="text-sm font-bold text-[#00C896]">STRONG CLOSE</span>
          <span className="text-[10.5px] text-[#707987] block mt-0.5">Price closing in upper 15% of day's range</span>
          <div className="w-full bg-[#1A1F26] rounded-full h-2 mt-2">
            <div className="bg-[#00C896] h-full rounded-full" style={{ width: "88%" }} />
          </div>
        </div>
      </div>
    </div>
  );
}
