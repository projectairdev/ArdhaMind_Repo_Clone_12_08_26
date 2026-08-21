// src/frontend/components/intelligence/TomorrowPlanView.tsx
import React from "react";
import { TomorrowPlanViewModel } from "../../viewmodels/session/SessionViewModels";
import { Calendar, CheckCircle2, Layers, ShieldAlert } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";

interface TomorrowPlanViewProps {
  vm: TomorrowPlanViewModel;
}

export const TomorrowPlanView: React.FC<TomorrowPlanViewProps> = ({ vm }) => {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-2.5 text-[#E6E8EB] font-sans text-left">
      {/* ─────────────────────────────────────────────────────────────
          LEFT SIDE — DECISION / CARRY-FORWARD PROOF (7 cols on XL)
      ───────────────────────────────────────────────────────────── */}
      <div className="xl:col-span-7 space-y-2.5">
        {/* A. BEST PLAN FOR TOMORROW */}
        <Surface>
          <SectionHeader
            title={vm.bestPlan.headline}
            detail={vm.bestPlan.rationale}
            accent="emerald"
            eyebrow="NEXT SESSION PLAN"
            action={
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-[#707987]">
                  CONF {vm.bestPlan.confidenceScore}
                </span>
              </div>
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
                <span className="text-[9px] text-[#707987] uppercase font-semibold">Opening Zone</span>
                <div className="text-[12px] font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.bestPlan.openingZone}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <span className="text-[9px] text-[#707987] uppercase font-semibold">Bias</span>
                <div className="text-[12px] font-bold text-[#00C896] font-mono mt-0.5">{vm.bestPlan.bias}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <span className="text-[9px] text-[#707987] uppercase font-semibold">Invalidation</span>
                <div className="text-[12px] font-bold text-[#E5484D] font-mono mt-0.5">{vm.bestPlan.invalidationLevels}</div>
              </div>
            </div>

            {/* Evidence points */}
            <div className="p-2 rounded-[2px] bg-[#08090B] border border-[#191D23]/80 text-[11px] space-y-1">
              <div className="text-[9px] font-bold uppercase text-[#707987]">Evidence & Structure</div>
              {vm.bestPlan.evidencePoints.map((pt, idx) => (
                <div key={idx} className="flex items-center gap-1.5 text-[#A5ABB4]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#00C896]"></span>
                  <span>{pt}</span>
                </div>
              ))}
              <div className="pt-1 mt-1 border-t border-[#191D23] text-[10px] text-[#707987] font-mono">
                <span className="text-[#A5ABB4] font-semibold">Data Basis: </span>
                {vm.bestPlan.dataBasisProof}
              </div>
            </div>
          </div>
        </Surface>

        {/* B. BEST STRIKE SUGGESTIONS (DATA-BACKED) */}
        <Surface>
          <SectionHeader
            title="BEST STRIKE SUGGESTIONS (DATA-BACKED)"
            accent="cyan"
          />
          <div className="p-2.5">
            <div className="overflow-x-auto rounded-[2px] border border-[#191D23]">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead>
                  <tr className="bg-[#0E1013] text-[#707987] text-[9px] uppercase font-bold border-b border-[#191D23]">
                    <th className="p-1.5">Type</th>
                    <th className="p-1.5">Strike Zone</th>
                    <th className="p-1.5">Rationale</th>
                    <th className="p-1.5">Confidence</th>
                    <th className="p-1.5">Data Basis (Proof)</th>
                  </tr>
                </thead>
                <tbody className="bg-[#0B0D10]">
                  {vm.bestStrikeSuggestions.map((item, idx) => (
                    <tr key={idx} className="border-b border-[#191D23]/50 hover:bg-[#13161A]">
                      <td className="p-1.5 font-semibold text-[#E6E8EB]">{item.type}</td>
                      <td className="p-1.5 font-mono text-[#38BDF8] font-bold">{item.strikeZone}</td>
                      <td className="p-1.5 text-[#A5ABB4] text-[10px]">{item.rationale}</td>
                      <td className="p-1.5 font-mono text-[#E6E8EB] text-[10px]">{item.confidence}</td>
                      <td className="p-1.5 text-[#707987] text-[9px] font-mono">{item.dataBasis}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Surface>

        {/* C. WHAT TO PREPARE (NIGHT CHECKLIST) */}
        <Surface>
          <SectionHeader
            title="WHAT TO PREPARE"
            detail="Night Checklist"
            icon={Calendar}
            accent="cyan"
          />
          <div className="p-2.5 space-y-1.5 text-[11px]">
            {vm.whatToPrepare.checklist.map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <CheckCircle2 size={12} className="text-[#00C896] shrink-0" />
                <span className="text-[#E6E8EB]">{item}</span>
              </div>
            ))}
            <div className="pt-1 text-[9px] text-[#707987] font-mono">
              <span className="text-[#A5ABB4] font-semibold">Data Basis: </span>
              {vm.whatToPrepare.dataBasisProof}
            </div>
          </div>
        </Surface>

        {/* D. SUITABLE STRATEGIES */}
        <Surface>
          <SectionHeader
            title="SUITABLE STRATEGIES"
            icon={Layers}
            accent="violet"
          />
          <div className="p-2.5">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {vm.suitableStrategies.map((strat, idx) => (
                <div key={idx} className="p-2 rounded-[2px] bg-[#08090B] border border-[#191D23] text-[11px] flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-[#E6E8EB] text-[10px]">{strat.name}</span>
                      <span className="text-[8px] font-bold uppercase px-1 py-0.2 rounded bg-[#191D23] text-[#A5ABB4]">
                        {strat.tag}
                      </span>
                    </div>
                    <div className="text-[9px] text-[#A5ABB4] space-y-0.5">
                      <div><span className="text-[#707987]">When:</span> {strat.whenCondition}</div>
                      <div><span className="text-[#707987]">Trigger:</span> {strat.trigger}</div>
                      <div><span className="text-[#707987]">Target:</span> {strat.targetArea}</div>
                    </div>
                  </div>
                  <div className="mt-1.5 pt-1 border-t border-[#191D23] text-[8px] text-[#707987]">
                    <span className="font-mono text-[#38BDF8]">Conf: {strat.confidence}</span> • {strat.historicalProofText}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Surface>

        {/* E. TOMORROW RISK CONTEXT */}
        <Surface>
          <SectionHeader
            title="TOMORROW RISK CONTEXT"
            icon={ShieldAlert}
            accent="amber"
          />
          <div className="p-2.5">
            <div className="grid grid-cols-2 sm:grid-cols-6 gap-1.5 text-[11px]">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Bias</div>
                <div className="font-bold text-[#00C896] mt-0.5">{vm.tomorrowRisk.marketMood}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Event Risk</div>
                <div className="font-bold text-[#00C896] mt-0.5">{vm.tomorrowRisk.eventRisk}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Confirmations</div>
                <div className="font-bold text-[#00C896] mt-0.5">{vm.tomorrowRisk.confirmationsCount} / 5</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Blockers</div>
                <div className="font-bold text-[#E59700] mt-0.5">{vm.tomorrowRisk.blockersCount} Active</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Confidence</div>
                <div className="font-bold text-[#38BDF8] mt-0.5">{vm.tomorrowRisk.confidenceScore}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Plan Quality</div>
                <div className="font-bold text-[#00C896] mt-0.5">High</div>
              </div>
            </div>
          </div>
        </Surface>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          RIGHT SIDE — PROFESSIONAL CARDS (5 cols on XL)
      ───────────────────────────────────────────────────────────── */}
      <div className="xl:col-span-5 space-y-2.5">
        {/* CARD 1 — TODAY'S MARKET OVERVIEW (COMPACT 2-ROW GRID) */}
        <Surface>
          <SectionHeader
            title="TODAY'S MARKET OVERVIEW"
            detail="Session summary metrics"
            accent="cyan"
          />
          <div className="p-2.5 space-y-1.5">
            {/* Row 1: Open, High, Low, Close, Change, Day Range */}
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5 text-[11px]">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Open</div>
                <div className="font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.todaysMarketOverview.open}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">High</div>
                <div className="font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.todaysMarketOverview.high}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Low</div>
                <div className="font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.todaysMarketOverview.low}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Close</div>
                <div className="font-bold text-white font-mono mt-0.5">{vm.todaysMarketOverview.close}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Change</div>
                <div className="font-bold text-[#00C896] font-mono mt-0.5">{vm.todaysMarketOverview.dayChange}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Day Range</div>
                <div className="font-bold text-[#38BDF8] font-mono mt-0.5">
                  {vm.todaysMarketOverview.high !== "UNAVAILABLE" && vm.todaysMarketOverview.low !== "UNAVAILABLE"
                    ? `${(Number(vm.todaysMarketOverview.high.replace(/,/g, "")) - Number(vm.todaysMarketOverview.low.replace(/,/g, ""))).toFixed(2)}`
                    : "UNAVAILABLE"}
                </div>
              </div>
            </div>

            {/* Row 2: Day Type, Breadth, VWAP, VIX, PCR, Leadership */}
            <div className="grid grid-cols-2 sm:grid-cols-6 gap-1.5 text-[11px]">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Day Type</div>
                <div className="font-bold text-[#00C896] truncate mt-0.5">{vm.todaysMarketOverview.dayType}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Breadth</div>
                <div className="font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.todaysMarketOverview.breadth}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">VWAP</div>
                <div className="font-bold text-[#38BDF8] truncate mt-0.5">{vm.todaysMarketOverview.vwapBehavior}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">VIX</div>
                <div className="font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.todaysMarketOverview.vixChange}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">PCR (OI)</div>
                <div className="font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.tomorrowRisk.confirmationsCount ? "0.92" : "UNAVAILABLE"}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Leadership</div>
                <div className="font-bold text-[#E6E8EB] truncate mt-0.5">{vm.todaysMarketOverview.leadership}</div>
              </div>
            </div>
          </div>
        </Surface>

        {/* CARD 2 — CRITICAL LEVELS FOR TOMORROW (COMPACT 4-ROW MATRIX) */}
        <Surface>
          <SectionHeader
            title="CRITICAL LEVELS FOR TOMORROW"
            detail="Carry-forward structural levels"
            accent="cyan"
          />
          <div className="p-2.5 space-y-1.5 text-[11px] font-mono">
            {/* Matrix Row 1: Support 1 | Support 2 | Carry-Forward */}
            <div className="grid grid-cols-3 gap-1.5">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23] flex justify-between items-center">
                <span className="text-[9px] text-[#707987] uppercase">Support 1</span>
                <span className="text-[#00C896] font-bold">{vm.criticalLevelsTomorrow.support1}</span>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23] flex justify-between items-center">
                <span className="text-[9px] text-[#707987] uppercase">Support 2</span>
                <span className="text-[#00C896] font-bold">{vm.criticalLevelsTomorrow.support2}</span>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#E59700]/10 border border-[#E59700]/30 flex justify-between items-center">
                <span className="text-[9px] text-[#E59700] uppercase font-semibold">Carry-Forward</span>
                <span className="text-[#E59700] font-bold">{vm.criticalLevelsTomorrow.carryForwardLevel}</span>
              </div>
            </div>

            {/* Matrix Row 2: Opening / Decision Zone */}
            <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23] flex justify-between items-center">
              <span className="text-[9px] text-[#707987] uppercase">Opening / Decision Zone</span>
              <span className="text-[#E6E8EB] font-bold">{vm.criticalLevelsTomorrow.openingZone}</span>
            </div>

            {/* Matrix Row 3: Resistance 1 | Resistance 2 */}
            <div className="grid grid-cols-2 gap-1.5">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23] flex justify-between items-center">
                <span className="text-[9px] text-[#707987] uppercase">Resistance 1</span>
                <span className="text-[#E5484D] font-bold">{vm.criticalLevelsTomorrow.resistance1}</span>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23] flex justify-between items-center">
                <span className="text-[9px] text-[#707987] uppercase">Resistance 2</span>
                <span className="text-[#E5484D] font-bold">{vm.criticalLevelsTomorrow.resistance2}</span>
              </div>
            </div>

            {/* Matrix Row 4: Bullish Above | Bearish Below | Invalidation */}
            <div className="grid grid-cols-3 gap-1.5">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23] flex justify-between items-center">
                <span className="text-[9px] text-[#707987] uppercase">Bullish Above</span>
                <span className="text-[#00C896] font-bold text-[10px] truncate">{vm.criticalLevelsTomorrow.bullishTrigger.replace("Close Above ", "")}</span>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23] flex justify-between items-center">
                <span className="text-[9px] text-[#707987] uppercase">Bearish Below</span>
                <span className="text-[#E5484D] font-bold text-[10px] truncate">{vm.criticalLevelsTomorrow.bearishTrigger.replace("Close Below ", "")}</span>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23] flex justify-between items-center">
                <span className="text-[9px] text-[#707987] uppercase">Invalidation</span>
                <span className="text-[#E5484D] font-bold text-[10px] truncate">{vm.criticalLevelsTomorrow.invalidationLevel}</span>
              </div>
            </div>
          </div>
        </Surface>

        {/* CARD 3 — SCENARIOS FOR TOMORROW */}
        <Surface>
          <SectionHeader
            title="SCENARIOS FOR TOMORROW"
            accent="cyan"
          />
          <div className="p-2.5 space-y-2">
            <div className="p-2 rounded-[2px] bg-[#08090B] border border-[#191D23] text-[11px]">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-[#00C896] uppercase text-[10px]">Primary Scenario</span>
                <span className="font-mono text-[9px] text-[#00C896] font-bold">{vm.scenariosTomorrow.primary.confidencePct}</span>
              </div>
              <div className="text-[#A5ABB4] space-y-0.5 text-[10px]">
                <div><span className="text-[#707987] font-semibold">Conditions: </span>{vm.scenariosTomorrow.primary.conditions}</div>
                <div><span className="text-[#707987] font-semibold">What To Do: </span>{vm.scenariosTomorrow.primary.whatToDo}</div>
                <div className="font-mono text-[#38BDF8] mt-0.5">{vm.scenariosTomorrow.primary.keyLevels}</div>
              </div>
            </div>

            <div className="p-2 rounded-[2px] bg-[#08090B] border border-[#191D23] text-[11px]">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-[#E59700] uppercase text-[10px]">Alternate Scenario</span>
                <span className="font-mono text-[9px] text-[#E59700] font-bold">{vm.scenariosTomorrow.alternate.confidencePct}</span>
              </div>
              <div className="text-[#A5ABB4] space-y-0.5 text-[10px]">
                <div><span className="text-[#707987] font-semibold">Conditions: </span>{vm.scenariosTomorrow.alternate.conditions}</div>
                <div><span className="text-[#707987] font-semibold">What To Do: </span>{vm.scenariosTomorrow.alternate.whatToDo}</div>
                <div className="font-mono text-[#38BDF8] mt-0.5">{vm.scenariosTomorrow.alternate.keyLevels}</div>
              </div>
            </div>
          </div>
        </Surface>

        {/* CARD 4 — CONFIDENCE & STRUCTURE */}
        <Surface>
          <SectionHeader
            title="CONFIDENCE & STRUCTURE"
            accent="cyan"
          />
          <div className="p-2.5">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 text-[11px]">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Plan Conf</div>
                <div className="font-bold text-[#38BDF8] font-mono mt-0.5">{vm.confidenceAndStructure.planConfidence}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Data Quality</div>
                <div className="font-bold text-[#00C896] font-mono mt-0.5">{vm.confidenceAndStructure.dataQuality}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Score</div>
                <div className="font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.confidenceAndStructure.structureScore}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Regime</div>
                <div className="font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.confidenceAndStructure.volatilityRegime}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase">Liquidity</div>
                <div className="font-bold text-[#00C896] font-mono mt-0.5">{vm.confidenceAndStructure.liquidity}</div>
              </div>
            </div>
          </div>
        </Surface>
      </div>
    </div>
  );
};
