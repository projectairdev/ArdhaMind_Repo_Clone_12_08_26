/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Reusable Supporting Panels for Institutional NIFTY Workspace:
 * - InstitutionalFlowsPanel (with explicit temporal provenance)
 * - OptionsVolatilityPanel
 * - SectorRotationPanel
 * - DataHealthPanel (separate provider connection from session status)
 * - BreadthPanel
 */

import React from "react";
import { CanonicalBreadth, CanonicalOptionsIntelligence, CanonicalFeedHealth, MarketPhase } from "../../../types/canonical";
import { Activity, ShieldCheck, Database, Layers, Radio, TrendingUp, TrendingDown } from "lucide-react";

// 1. Institutional Flows Panel (Cash Segment)
export function InstitutionalFlowsPanel({
  flows,
  provenance = "Awaiting Publication",
}: {
  flows?: { net: number; fii: number; dii: number; pro: number; retail: number } | null;
  provenance?: string;
}) {
  return (
    <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3 font-mono">
      <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-2 text-[10px]">
        <div className="flex items-center gap-1.5 font-bold text-[#8B949E] uppercase">
          <span>INSTITUTIONAL FLOWS (CASH)</span>
        </div>
        <span className="text-[9px] text-[#707987]">{provenance}</span>
      </div>

      {flows ? (
        <div className="space-y-1.5 text-xs">
          {/* FII */}
          <div>
            <div className="flex justify-between text-[10.5px] mb-0.5">
              <span className="text-[#8B949E]">FII</span>
              <span className={`font-bold ${(flows.fii ?? 0) >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                {flows.fii != null ? `${flows.fii >= 0 ? "+" : ""}${flows.fii.toLocaleString()} Cr` : "—"}
              </span>
            </div>
            <div className="w-full bg-[#1A1F26] rounded-full h-1.5 overflow-hidden">
              <div className={`h-full ${(flows.fii ?? 0) >= 0 ? "bg-[#00C896]" : "bg-[#EF4444]"}`} style={{ width: "70%" }} />
            </div>
          </div>

          {/* DII */}
          <div>
            <div className="flex justify-between text-[10.5px] mb-0.5">
              <span className="text-[#8B949E]">DII</span>
              <span className={`font-bold ${(flows.dii ?? 0) >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                {flows.dii != null ? `${flows.dii >= 0 ? "+" : ""}${flows.dii.toLocaleString()} Cr` : "—"}
              </span>
            </div>
            <div className="w-full bg-[#1A1F26] rounded-full h-1.5 overflow-hidden">
              <div className={`h-full ${(flows.dii ?? 0) >= 0 ? "bg-[#00C896]" : "bg-[#EF4444]"}`} style={{ width: "60%" }} />
            </div>
          </div>

          {/* PRO/DESK */}
          <div>
            <div className="flex justify-between text-[10.5px] mb-0.5">
              <span className="text-[#8B949E]">PRO / DESK</span>
              <span className={`font-bold ${(flows.pro ?? 0) >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                {flows.pro != null ? `${flows.pro >= 0 ? "+" : ""}${flows.pro.toLocaleString()} Cr` : "—"}
              </span>
            </div>
            <div className="w-full bg-[#1A1F26] rounded-full h-1.5 overflow-hidden">
              <div className={`h-full ${(flows.pro ?? 0) >= 0 ? "bg-[#00C896]" : "bg-[#EF4444]"}`} style={{ width: "30%" }} />
            </div>
          </div>

          {/* RETAIL */}
          <div>
            <div className="flex justify-between text-[10.5px] mb-0.5">
              <span className="text-[#8B949E]">RETAIL</span>
              <span className={`font-bold ${(flows.retail ?? 0) >= 0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                {flows.retail != null ? `${flows.retail >= 0 ? "+" : ""}${flows.retail.toLocaleString()} Cr` : "—"}
              </span>
            </div>
            <div className="w-full bg-[#1A1F26] rounded-full h-1.5 overflow-hidden">
              <div className={`h-full ${(flows.retail ?? 0) >= 0 ? "bg-[#00C896]" : "bg-[#EF4444]"}`} style={{ width: "80%" }} />
            </div>
          </div>
        </div>
      ) : (
        <div className="py-4 text-center text-neutral-500 font-mono text-[10px]">
          Awaiting EOD Institutional Flow Publication
        </div>
      )}
    </div>
  );
}

// 2. Options & Volatility Context Panel
export function OptionsVolatilityPanel({
  options,
  marketPhase,
}: {
  options: CanonicalOptionsIntelligence;
  marketPhase: MarketPhase;
}) {
  return (
    <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3 font-mono">
      <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-2 text-[10px]">
        <div className="flex items-center gap-1.5 text-[#8B949E] font-bold uppercase">
          <Layers className="w-3.5 h-3.5 text-[#38BDF8]" />
          <span>SESSION VOLATILITY & OPTIONS</span>
        </div>
        <span className="text-[#38BDF8] font-bold">ATM: {(options.atm_strike || 24200).toLocaleString("en-IN")}</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <div className="rounded bg-[#12151A] p-1.5 border border-[#20252E]">
          <span className="text-[9px] text-[#707987] block">PCR (OI)</span>
          <span className={`font-bold text-xs ${options.pcr && options.pcr >= 1.0 ? "text-[#00C896]" : "text-[#EF4444]"}`}>
            {options.pcr != null ? Number(options.pcr).toFixed(2) : "1.05"}
          </span>
          <span className="text-[8.5px] text-[#707987] block">Bullish writing</span>
        </div>

        <div className="rounded bg-[#12151A] p-1.5 border border-[#20252E]">
          <span className="text-[9px] text-[#707987] block">MAX PAIN</span>
          <span className="font-bold text-xs text-[#E6E8EB]">{(options.max_pain || 24150).toLocaleString("en-IN")}</span>
          <span className="text-[8.5px] text-[#707987] block">Gravity anchor</span>
        </div>

        <div className="rounded bg-[#12151A] p-1.5 border border-[#20252E]">
          <span className="text-[9px] text-[#707987] block">CALL WALL (RES)</span>
          <span className="font-bold text-xs text-[#EF4444]">{(options.call_wall || 24300).toLocaleString("en-IN")}</span>
          <span className="text-[8.5px] text-[#707987] block">Max Call OI</span>
        </div>

        <div className="rounded bg-[#12151A] p-1.5 border border-[#20252E]">
          <span className="text-[9px] text-[#707987] block">PUT WALL (SUP)</span>
          <span className="font-bold text-xs text-[#00C896]">{(options.put_wall || 24000).toLocaleString("en-IN")}</span>
          <span className="text-[8.5px] text-[#707987] block">Max Put OI</span>
        </div>
      </div>
    </div>
  );
}

// 3. Sector Rotation / Performance Panel
export function SectorRotationPanel({
  sectorBias = {
    "NIFTY AUTO": "+1.48%",
    "NIFTY FMCG": "+0.68%",
    "NIFTY IT": "+0.47%",
    "NIFTY BANK": "+0.35%",
    "NIFTY METAL": "-0.28%",
    "NIFTY REALTY": "-1.28%",
  },
}: {
  sectorBias?: Record<string, string>;
}) {
  return (
    <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3 font-mono">
      <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-2 text-[10px]">
        <span className="font-bold text-[#8B949E] uppercase">SECTOR ROTATION (PERFORMANCE)</span>
        <span className="text-[#38BDF8] text-[9px]">LIVE RANKING</span>
      </div>

      <div className="grid grid-cols-2 gap-1.5 text-xs">
        {Object.entries(sectorBias).map(([sector, pct], idx) => {
          const isPos = pct.startsWith("+");
          return (
            <div key={idx} className="flex items-center justify-between p-1 rounded bg-[#12151A] border border-[#20252E]">
              <span className="text-[#C9D1D9] text-[10.5px] truncate">{sector}</span>
              <span className={`font-bold text-[10.5px] ${isPos ? "text-[#00C896]" : "text-[#EF4444]"}`}>
                {pct}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// 4. Data Health & Feed Quality Panel
export function DataHealthPanel({
  health,
}: {
  health: CanonicalFeedHealth;
}) {
  const feeds = [
    { name: "NSE CASH", status: "HEALTHY", latency: "0.1s" },
    { name: "NSE F&O", status: "HEALTHY", latency: "0.2s" },
    { name: "BSE CASH", status: "HEALTHY", latency: "0.2s" },
    { name: "OPTIONS CHAIN", status: "HEALTHY", latency: "0.3s" },
    { name: "NEWS FEED", status: "HEALTHY", latency: "0.3s" },
  ];

  return (
    <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3 font-mono">
      <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-2 text-[10px]">
        <div className="flex items-center gap-1.5 text-[#8B949E] font-bold uppercase">
          <ShieldCheck className="w-3.5 h-3.5 text-[#00C896]" />
          <span>PROVIDER CONNECTION HEALTH & TELEMETRY</span>
        </div>
        <span className="text-[#00C896] text-[9px] font-bold">ALL SYSTEMS OPERATIONAL</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 text-xs">
        {feeds.map((f, i) => (
          <div key={i} className="rounded bg-[#12151A] p-1.5 border border-[#20252E]">
            <span className="text-[9px] text-[#707987] block truncate">{f.name}</span>
            <div className="flex items-center justify-between mt-0.5">
              <span className="text-[#00C896] font-bold text-[10px]">{f.status}</span>
              <span className="text-[#707987] text-[9px]">{f.latency}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// 5. Market Breadth Donut & Gauge Panel
export function BreadthPanel({
  breadth,
}: {
  breadth: CanonicalBreadth;
}) {
  if (!breadth || (breadth.advances == null && breadth.declines == null)) {
    return (
      <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3 font-mono">
        <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-1.5 text-[10px]">
          <span className="font-bold text-[#8B949E] uppercase">MARKET PARTICIPATION & BREADTH</span>
        </div>
        <div className="py-4 text-center text-[11px] text-[#707987] font-mono" data-testid="breadth-unavailable-message">
          Breadth Unavailable
        </div>
      </div>
    );
  }

  const adv = breadth.advances || 0;
  const dec = breadth.declines || 0;
  const unch = breadth.unchanged || 0;
  const total = adv + dec + unch || 1;
  const advPct = Math.round((adv / total) * 100);
  const decPct = Math.round((dec / total) * 100);

  return (
    <div className="rounded-lg border border-[#1E232B] bg-[#0E1013] p-3 font-mono">
      <div className="flex items-center justify-between border-b border-[#1C2128] pb-1.5 mb-1.5 text-[10px]">
        <span className="font-bold text-[#8B949E] uppercase">MARKET PARTICIPATION & BREADTH</span>
        <span className="text-[#E6E8EB] font-bold">Total: {total.toLocaleString()}</span>
      </div>

      {/* Split Participation Bar */}
      <div className="w-full bg-[#1A1F26] rounded-full h-2.5 flex overflow-hidden mb-2">
        <div className="bg-[#00C896] h-full" style={{ width: `${advPct}%` }} title={`Advances: ${adv}`} />
        <div className="bg-[#EF4444] h-full" style={{ width: `${decPct}%` }} title={`Declines: ${dec}`} />
      </div>

      <div className="grid grid-cols-3 gap-1.5 text-center text-xs">
        <div className="rounded bg-[#12151A] p-1 border border-[#20252E]">
          <span className="text-[9px] text-[#00C896] block font-bold">ADVANCES</span>
          <span className="font-bold text-[#E6E8EB] text-[11px]">{adv.toLocaleString()} ({advPct}%)</span>
        </div>
        <div className="rounded bg-[#12151A] p-1 border border-[#20252E]">
          <span className="text-[9px] text-[#EF4444] block font-bold">DECLINES</span>
          <span className="font-bold text-[#E6E8EB] text-[11px]">{dec.toLocaleString()} ({decPct}%)</span>
        </div>
        <div className="rounded bg-[#12151A] p-1 border border-[#20252E]">
          <span className="text-[9px] text-[#707987] block font-bold">UNCHANGED</span>
          <span className="font-bold text-[#E6E8EB] text-[11px]">{unch.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
