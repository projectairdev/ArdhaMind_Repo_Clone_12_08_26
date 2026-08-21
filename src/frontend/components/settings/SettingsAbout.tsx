import React from "react";
import { ShieldCheck, Info, Database, Server, CheckCircle2 } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import { SettingsPresentationState } from "../../utils/canonicalSettingsAdapter";

export function SettingsAbout({ pres }: { pres: SettingsPresentationState }) {
  const ab = pres.about;

  return (
    <div className="space-y-3 font-sans text-left text-[11px] min-w-0">
      {/* ── 1. SYSTEM IDENTITY & VERSION METADATA ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="AIR ARDHAMIND WORKSTATION IDENTITY" eyebrow="1. System Identity" accent="cyan" />
        <div className="p-3 bg-[#0B0D10] space-y-2.5 font-mono text-[10px]">
          <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-[#38BDF8]" />
              <span className="font-bold text-[#E6E8EB] text-xs uppercase">{ab.appName}</span>
            </div>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/30">
              {ab.version}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[9px] text-[#707987]">
            <div className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-1">
              <div className="flex justify-between">
                <span>Application Purpose:</span>
                <span className="font-bold text-[#E6E8EB]">NIFTY 50 READ ONLY Decision Support Workstation</span>
              </div>
              <div className="flex justify-between">
                <span>Active Environment:</span>
                <span className="font-bold text-[#E59700] uppercase">{ab.environment}</span>
              </div>
              <div className="flex justify-between">
                <span>Runtime Binding:</span>
                <span className="text-[#38BDF8]">{ab.runtimePort}</span>
              </div>
            </div>

            <div className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-1">
              <div className="flex justify-between">
                <span>Build Artifact:</span>
                <span className="font-bold text-[#E6E8EB]">{pres.buildHash}</span>
              </div>
              <div className="flex justify-between">
                <span>State Sequence:</span>
                <span className="text-[#00C896] font-bold">#{pres.diagnostics.stateSequence}</span>
              </div>
              <div className="flex justify-between">
                <span>Last Telemetry IST:</span>
                <span className="text-[#E6E8EB]">{pres.lastUpdatedIst}</span>
              </div>
            </div>
          </div>
        </div>
      </Surface>

      {/* ── 2. READ-ONLY INVARIANTS GUARANTEE STATEMENT ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="ABSOLUTE SAFETY &amp; READ-ONLY INVARIANTS" eyebrow="2. Architectural Safeguards" accent="violet" />
        <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[9.5px]">
          <div className="p-2.5 rounded bg-[#00C896]/10 border border-[#00C896]/30 space-y-1">
            <div className="font-bold text-[#00C896] text-[10px] uppercase flex items-center gap-1.5">
              <CheckCircle2 size={13} />
              {ab.readOnlyGuarantees}
            </div>
            <p className="text-[#707987] text-[8.5px] leading-relaxed">
              AIR ArdhaMind operates as an institutional READ ONLY market intelligence terminal. The codebase contains zero order placement, paper trading, order modification, or broker mutation methods.
            </p>
          </div>
        </div>
      </Surface>

      {/* ── 3. DATA SOURCE ATTRIBUTIONS ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="DATA SOURCE &amp; TELEMETRY ATTRIBUTIONS" eyebrow="3. Authorized Feeds" accent="amber" />
        <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[9.5px]">
          <div className="divide-y divide-[#191D23]">
            <div className="py-1.5 flex justify-between">
              <span className="text-[#E6E8EB] font-bold">Zerodha KiteConnect API</span>
              <span className="text-[#707987]">Live NIFTY Spot Quotes, Market Depth &amp; Option Chain OI</span>
            </div>
            <div className="py-1.5 flex justify-between">
              <span className="text-[#E6E8EB] font-bold">Reserve Bank of India (RBI)</span>
              <span className="text-[#707987]">Official Liquidity Operations &amp; Monetary Policy Statements</span>
            </div>
            <div className="py-1.5 flex justify-between">
              <span className="text-[#E6E8EB] font-bold">SEBI Official RSS</span>
              <span className="text-[#707987]">Capital Market Circulars &amp; Derivative Risk Disclosures</span>
            </div>
            <div className="py-1.5 flex justify-between">
              <span className="text-[#E6E8EB] font-bold">MoSPI &amp; Government Feeds</span>
              <span className="text-[#707987]">India WPI/CPI Inflation, IIP Growth &amp; GDP Telemetry</span>
            </div>
            <div className="py-1.5 flex justify-between">
              <span className="text-[#E6E8EB] font-bold">NSE / BSE Official Feeds</span>
              <span className="text-[#707987]">FII/DII Institutional Cash Flow Reports &amp; Index Constituents</span>
            </div>
            <div className="py-1.5 flex justify-between">
              <span className="text-[#E6E8EB] font-bold">OpenAI GPT-4o</span>
              <span className="text-[#707987]">Natural Language Synthesis &amp; Decision Support Telemetry</span>
            </div>
          </div>
        </div>
      </Surface>
    </div>
  );
}

export default SettingsAbout;
