// src/frontend/components/intelligence/MorningPlanView.tsx
import React from "react";
import { MorningPlanViewModel } from "../../viewmodels/session/SessionViewModels";
import { TrendingUp, TrendingDown, Clock, ShieldAlert, Layers } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";

interface MorningPlanViewProps {
  vm: MorningPlanViewModel;
}

export const MorningPlanView: React.FC<MorningPlanViewProps> = ({ vm }) => {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-2.5 text-[#E6E8EB] font-sans text-left">
      {/* ─────────────────────────────────────────────────────────────
          LEFT SIDE — DECISION & PROOF (7 cols on XL)
      ───────────────────────────────────────────────────────────── */}
      <div className="xl:col-span-7 space-y-2.5">
        {/* A. BEST PLAN AT OPEN */}
        <Surface>
          <SectionHeader
            title="BEST PLAN AT OPEN"
            detail="Execute with discipline. Adapt if evidence changes."
            accent="amber"
            action={
              <span className="text-[10px] font-mono text-[#707987]">
                Snapshot {vm.snapshotTimestamp}
              </span>
            }
          />
          <div className="p-2.5 space-y-2">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 text-[11px]">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <span className="text-[9px] text-[#707987] uppercase font-semibold">Spot (Index)</span>
                <div className="text-[12px] font-bold text-white font-mono mt-0.5">{vm.bestPlan.spotIndex}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <span className="text-[9px] text-[#707987] uppercase font-semibold">Carry-Forward</span>
                <div className="text-[12px] font-bold text-[#E59700] font-mono mt-0.5">{vm.bestPlan.carryForwardLevel}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <span className="text-[9px] text-[#707987] uppercase font-semibold">Opening Range</span>
                <div className="text-[12px] font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.bestPlan.openingRangeEst}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <span className="text-[9px] text-[#707987] uppercase font-semibold">Preferred Bias</span>
                <div className="text-[12px] font-bold text-[#00C896] font-mono mt-0.5">{vm.bestPlan.preferredBias}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <span className="text-[9px] text-[#707987] uppercase font-semibold">Invalidation</span>
                <div className="text-[12px] font-bold text-[#E5484D] font-mono mt-0.5">{vm.bestPlan.invalidation}</div>
              </div>
            </div>

            <div className="text-[11px] text-[#A5ABB4] bg-[#08090B] p-2 rounded-[2px] border border-[#191D23]/60">
              <span className="font-semibold text-[#E6E8EB]">Rationale: </span>
              {vm.bestPlan.rationale}
            </div>
          </div>
        </Surface>

        {/* B. PRIMARY SCENARIO */}
        <Surface>
          <SectionHeader
            title="PRIMARY SCENARIO"
            icon={TrendingUp}
            accent="emerald"
            action={
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-bold text-[#00C896] bg-[#00C896]/10 px-1.5 py-0.5 rounded-[2px] border border-[#00C896]/30">
                  {vm.primaryScenario.name.toUpperCase()}
                </span>
                <span className="text-[10px] font-mono text-[#707987]">
                  CONF {vm.primaryScenario.confidencePct.replace("% CONFIDENCE", "%")}
                </span>
              </div>
            }
          />
          <div className="p-2.5 space-y-2 text-[11px]">
            <div className="space-y-1">
              <div><span className="text-[#707987] font-semibold">Plan: </span><span className="text-[#E6E8EB]">{vm.primaryScenario.plan}</span></div>
              <div><span className="text-[#707987] font-semibold">Data Basis: </span><span className="text-[#A5ABB4]">{vm.primaryScenario.dataBasis}</span></div>
            </div>

            <div className="overflow-x-auto rounded-[2px] border border-[#191D23]">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead>
                  <tr className="bg-[#0E1013] text-[#707987] text-[9px] uppercase font-bold border-b border-[#191D23]">
                    <th className="p-1.5">Evidence (Snapshot)</th>
                    {vm.primaryScenario.evidenceTable.map((row, idx) => (
                      <th key={idx} className="p-1.5">{row.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-[#0B0D10]">
                  <tr>
                    <td className="p-1.5 font-mono text-[10px] text-[#707987]">Values</td>
                    {vm.primaryScenario.evidenceTable.map((row, idx) => (
                      <td key={idx} className="p-1.5 font-mono text-[#E6E8EB] text-[10px]">{row.value}</td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="text-[10px] text-[#707987] italic">
              {vm.primaryScenario.historicalProofText}
            </div>
          </div>
        </Surface>

        {/* C. ALTERNATE SCENARIO */}
        <Surface>
          <SectionHeader
            title="ALTERNATE SCENARIO"
            icon={TrendingDown}
            accent="rose"
            action={
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-bold text-[#E5484D] bg-[#E5484D]/10 px-1.5 py-0.5 rounded-[2px] border border-[#E5484D]/30">
                  {vm.alternateScenario.name.toUpperCase()}
                </span>
                <span className="text-[10px] font-mono text-[#707987]">
                  CONF {vm.alternateScenario.confidencePct.replace("% CONFIDENCE", "%")}
                </span>
              </div>
            }
          />
          <div className="p-2.5 space-y-2 text-[11px]">
            <div className="space-y-1">
              <div><span className="text-[#707987] font-semibold">Plan: </span><span className="text-[#E6E8EB]">{vm.alternateScenario.plan}</span></div>
              <div><span className="text-[#707987] font-semibold">Data Basis: </span><span className="text-[#A5ABB4]">{vm.alternateScenario.dataBasis}</span></div>
            </div>

            <div className="overflow-x-auto rounded-[2px] border border-[#191D23]">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead>
                  <tr className="bg-[#0E1013] text-[#707987] text-[9px] uppercase font-bold border-b border-[#191D23]">
                    <th className="p-1.5">Evidence (Snapshot)</th>
                    {vm.alternateScenario.evidenceTable.map((row, idx) => (
                      <th key={idx} className="p-1.5">{row.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-[#0B0D10]">
                  <tr>
                    <td className="p-1.5 font-mono text-[10px] text-[#707987]">Values</td>
                    {vm.alternateScenario.evidenceTable.map((row, idx) => (
                      <td key={idx} className="p-1.5 font-mono text-[#E6E8EB] text-[10px]">{row.value}</td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="text-[10px] text-[#707987] italic">
              {vm.alternateScenario.historicalProofText}
            </div>
          </div>
        </Surface>

        {/* D. WHAT TO WATCH IN FIRST 15 MINUTES */}
        <Surface>
          <SectionHeader
            title="WHAT TO WATCH IN FIRST 15 MINUTES"
            icon={Clock}
            accent="cyan"
          />
          <div className="p-2.5">
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-1.5 text-[11px]">
              {vm.whatToWatchFirst15Min.map((item, idx) => (
                <div key={idx} className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                  <div className="font-semibold text-[#E6E8EB] text-[11px] truncate">{item.title}</div>
                  <div className="text-[9px] text-[#707987] truncate">{item.condition}</div>
                  <div className="mt-1">
                    <span className="text-[8px] font-bold px-1 py-0.2 rounded bg-[#191D23] text-[#38BDF8]">
                      {item.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Surface>

        {/* E. SUITABLE STRATEGIES */}
        <Surface>
          <SectionHeader
            title="SUITABLE STRATEGIES"
            detail="Based on active scenario"
            icon={Layers}
            accent="violet"
          />
          <div className="p-2.5">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {vm.suitableStrategies.map((strat, idx) => (
                <div key={idx} className="p-2 rounded-[2px] bg-[#08090B] border border-[#191D23] flex flex-col justify-between text-[11px]">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-[#E6E8EB]">{strat.name}</span>
                      <span className={`text-[8px] font-bold uppercase px-1 py-0.2 rounded ${
                        strat.tag === "Preferred" ? "bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30" :
                        strat.tag === "Alternate" ? "bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/30" :
                        "bg-[#E59700]/15 text-[#E59700] border border-[#E59700]/30"
                      }`}>
                        {strat.tag}
                      </span>
                    </div>
                    <div className="text-[10px] text-[#A5ABB4] space-y-0.5">
                      <div><span className="text-[#707987]">When:</span> {strat.whenCondition}</div>
                      <div><span className="text-[#707987]">Trigger:</span> {strat.trigger}</div>
                      <div><span className="text-[#707987]">Target:</span> {strat.targetArea}</div>
                    </div>
                  </div>
                  <div className="mt-1.5 pt-1.5 border-t border-[#191D23] text-[9px] text-[#707987]">
                    <span className="font-mono text-[#38BDF8]">Conf: {strat.confidence}</span> • {strat.historicalProofText}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Surface>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          RIGHT SIDE — PROFESSIONAL CARDS (5 cols on XL)
      ───────────────────────────────────────────────────────────── */}
      <div className="xl:col-span-5 space-y-2.5">
        {/* CARD 1 — YESTERDAY'S MARKET INFO */}
        <Surface>
          <SectionHeader
            title={`YESTERDAY'S MARKET INFO (${vm.yesterdaysInfo.sessionDate})`}
            accent="cyan"
          />
          <div className="p-2.5">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-[11px]">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Close</div>
                <div className="font-bold text-white font-mono">{vm.yesterdaysInfo.close}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">High</div>
                <div className="font-bold text-white font-mono">{vm.yesterdaysInfo.high}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Low</div>
                <div className="font-bold text-white font-mono">{vm.yesterdaysInfo.low}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Change</div>
                <div className="font-bold text-[#00C896] font-mono">{vm.yesterdaysInfo.change}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Adv / Dec</div>
                <div className="font-bold text-[#E6E8EB] font-mono">{vm.yesterdaysInfo.advDec}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">VWAP</div>
                <div className="font-bold text-[#E6E8EB] font-mono">{vm.yesterdaysInfo.vwap}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">FII Cash</div>
                <div className="font-bold text-[#00C896] font-mono">{vm.yesterdaysInfo.fiiCashCr}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">DII Cash</div>
                <div className="font-bold text-[#00C896] font-mono">{vm.yesterdaysInfo.diiCashCr}</div>
              </div>
            </div>
          </div>
        </Surface>

        {/* CARD 2 — TODAY'S MARKET OPEN (09:00 - 09:08) */}
        <Surface>
          <SectionHeader
            title={`TODAY'S MARKET OPEN (${vm.todaysOpen.windowLabel})`}
            accent="amber"
            action={
              <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-[#E59700]/10 text-[#E59700] border border-[#E59700]/30 font-bold">
                FROZEN SNAPSHOT
              </span>
            }
          />
          <div className="p-2.5">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-[11px]">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Open</div>
                <div className="font-bold text-white font-mono">{vm.todaysOpen.open}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">High</div>
                <div className="font-bold text-white font-mono">{vm.todaysOpen.high}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Low</div>
                <div className="font-bold text-white font-mono">{vm.todaysOpen.low}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">VWAP</div>
                <div className="font-bold text-[#E6E8EB] font-mono">{vm.todaysOpen.vwap}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Range</div>
                <div className="font-bold text-[#38BDF8] font-mono">{vm.todaysOpen.rangePts}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Breadth</div>
                <div className="font-bold text-[#E6E8EB] font-mono">{vm.todaysOpen.breadth}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">PCR</div>
                <div className="font-bold text-[#E6E8EB] font-mono">{vm.todaysOpen.pcr}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">DII Cash</div>
                <div className="font-bold text-[#00C896] font-mono">{vm.todaysOpen.diiCashCr}</div>
              </div>
            </div>
          </div>
        </Surface>

        {/* CARD 3 — KEY LEVELS & DECISION ZONE */}
        <Surface>
          <SectionHeader
            title="KEY LEVELS & DECISION ZONE"
            accent="cyan"
          />
          <div className="p-2.5">
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              {/* Levels */}
              <div className="space-y-1">
                <div className="text-[9px] uppercase font-bold text-[#707987] mb-0.5">Levels</div>
                <div className="flex justify-between p-1 rounded-[2px] bg-[#08090B] border border-[#191D23] font-mono">
                  <span className="text-[#707987]">Resistance 2</span>
                  <span className="text-[#E5484D] font-bold">{vm.keyLevelsDecisionZone.resistance2}</span>
                </div>
                <div className="flex justify-between p-1 rounded-[2px] bg-[#08090B] border border-[#191D23] font-mono">
                  <span className="text-[#707987]">Resistance 1</span>
                  <span className="text-[#E5484D] font-bold">{vm.keyLevelsDecisionZone.resistance1}</span>
                </div>
                <div className="flex justify-between p-1 rounded-[2px] bg-[#E59700]/10 border border-[#E59700]/30 font-mono">
                  <span className="text-[#E59700] font-semibold">Decision Zone</span>
                  <span className="text-[#E59700] font-bold">{vm.keyLevelsDecisionZone.pivotDecisionZone}</span>
                </div>
                <div className="flex justify-between p-1 rounded-[2px] bg-[#08090B] border border-[#191D23] font-mono">
                  <span className="text-[#707987]">Support 1</span>
                  <span className="text-[#00C896] font-bold">{vm.keyLevelsDecisionZone.support1}</span>
                </div>
                <div className="flex justify-between p-1 rounded-[2px] bg-[#08090B] border border-[#191D23] font-mono">
                  <span className="text-[#707987]">Support 2</span>
                  <span className="text-[#00C896] font-bold">{vm.keyLevelsDecisionZone.support2}</span>
                </div>
              </div>

              {/* Decision Guide */}
              <div className="space-y-1">
                <div className="text-[9px] uppercase font-bold text-[#707987] mb-0.5">Decision Guide</div>
                <div className="flex justify-between p-1 rounded-[2px] bg-[#08090B] border border-[#191D23] font-mono">
                  <span className="text-[#707987]">Bullish Above</span>
                  <span className="text-[#00C896] font-bold">{vm.keyLevelsDecisionZone.bullishAbove}</span>
                </div>
                <div className="flex justify-between p-1 rounded-[2px] bg-[#08090B] border border-[#191D23] font-mono">
                  <span className="text-[#707987]">Bearish Below</span>
                  <span className="text-[#E5484D] font-bold">{vm.keyLevelsDecisionZone.bearishBelow}</span>
                </div>
                <div className="flex justify-between p-1 rounded-[2px] bg-[#08090B] border border-[#191D23] font-mono">
                  <span className="text-[#707987]">Invalidation</span>
                  <span className="text-[#E5484D] font-bold">{vm.keyLevelsDecisionZone.invalidationLevel}</span>
                </div>
                <div className="flex justify-between p-1 rounded-[2px] bg-[#08090B] border border-[#191D23] font-mono">
                  <span className="text-[#707987]">Must Hold</span>
                  <span className="text-[#00C896] font-bold">{vm.keyLevelsDecisionZone.mustHoldLevel}</span>
                </div>
                <div className="flex justify-between p-1 rounded-[2px] bg-[#08090B] border border-[#191D23] font-mono">
                  <span className="text-[#707987]">Trend Filter</span>
                  <span className="text-[#38BDF8] font-bold">{vm.keyLevelsDecisionZone.trendFilter}</span>
                </div>
              </div>
            </div>
          </div>
        </Surface>

        {/* CARD 4 — MORNING RISK CONTEXT */}
        <Surface>
          <SectionHeader
            title="MORNING RISK CONTEXT"
            icon={ShieldAlert}
            accent="amber"
          />
          <div className="p-2.5">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-[11px] mb-2">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Global Cues</div>
                <div className="font-bold text-[#00C896]">{vm.morningRisk.globalCues}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Nifty VIX</div>
                <div className="font-bold text-white font-mono">{vm.morningRisk.vixValue}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Event Risk</div>
                <div className="font-bold text-[#00C896]">{vm.morningRisk.eventRisk}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Overall Risk</div>
                <div className="font-bold text-[#00C896]">{vm.morningRisk.overallRisk}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-1 pt-1.5 border-t border-[#191D23]">
              <span className="text-[9px] text-[#707987] font-semibold self-center mr-1">Proof:</span>
              {vm.morningRisk.proofBadges.map((badge, idx) => (
                <span key={idx} className="text-[8px] font-mono px-1.5 py-0.2 rounded bg-[#08090B] text-[#A5ABB4] border border-[#191D23]">
                  ✓ {badge}
                </span>
              ))}
            </div>
          </div>
        </Surface>

        {/* CARD 5 — DATA-BACKED VALUE SUGGESTIONS */}
        <Surface>
          <SectionHeader
            title="DATA-BACKED VALUE SUGGESTIONS"
            accent="cyan"
            action={<span className="text-[10px] font-mono text-[#707987]">09:02 AM IST</span>}
          />
          <div className="p-2.5">
            <div className="overflow-x-auto rounded-[2px] border border-[#191D23]">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead>
                  <tr className="bg-[#0E1013] text-[#707987] text-[9px] uppercase font-bold border-b border-[#191D23]">
                    <th className="p-1.5">Zone</th>
                    <th className="p-1.5">Upper</th>
                    <th className="p-1.5">Lower</th>
                    <th className="p-1.5">Conviction</th>
                    <th className="p-1.5">Rationale / Proof</th>
                  </tr>
                </thead>
                <tbody className="bg-[#0B0D10]">
                  {vm.dataBackedValueSuggestions.map((item, idx) => (
                    <tr key={idx} className="border-b border-[#191D23]/50 hover:bg-[#13161A]">
                      <td className="p-1.5 font-semibold text-[#E6E8EB]">{item.zone}</td>
                      <td className="p-1.5 font-mono text-[#A5ABB4]">{item.upper}</td>
                      <td className="p-1.5 font-mono text-[#A5ABB4]">{item.lower}</td>
                      <td className="p-1.5">
                        <span className={`text-[8px] font-bold px-1 py-0.2 rounded ${
                          item.conviction === "High" ? "bg-[#00C896]/15 text-[#00C896]" :
                          item.conviction === "Moderate" ? "bg-[#E59700]/15 text-[#E59700]" :
                          "bg-[#191D23] text-[#707987]"
                        }`}>
                          {item.conviction}
                        </span>
                      </td>
                      <td className="p-1.5 text-[#707987] text-[10px]">{item.rationale}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Surface>
      </div>
    </div>
  );
};
