// src/frontend/components/intelligence/LiveGuideView.tsx
import React from "react";
import { LiveGuideViewModel } from "../../viewmodels/session/SessionViewModels";
import { Hourglass, ShieldAlert, TrendingUp, TrendingDown, Layers, ArrowUpRight } from "lucide-react";
import { useNavigation } from "../../context/NavigationContext";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";

interface LiveGuideViewProps {
  vm: LiveGuideViewModel;
}

export const LiveGuideView: React.FC<LiveGuideViewProps> = ({ vm }) => {
  const { setActiveModule } = useNavigation();

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-2.5 text-[#E6E8EB] font-sans text-left">
      {/* ─────────────────────────────────────────────────────────────
          LEFT SIDE — DECISION / INTRADAY ANALYSIS (7 cols on XL)
      ───────────────────────────────────────────────────────────── */}
      <div className="xl:col-span-7 space-y-2.5">
        {/* A. BEST ACTION NOW */}
        <Surface glow={vm.bestActionNow.status === "SETUP QUALIFIED" ? "emerald" : "amber"}>
          <SectionHeader
            title="BEST ACTION NOW"
            accent="amber"
            action={
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-bold text-[#E59700] bg-[#E59700]/10 px-1.5 py-0.5 rounded-[2px] border border-[#E59700]/30">
                  {vm.bestActionNow.status}
                </span>
                <span className="text-[10px] font-mono text-[#707987]">
                  CONF {vm.bestActionNow.confidenceScore}
                </span>
              </div>
            }
          />
          <div className="p-2.5 space-y-2">
            <div className="text-[12px] font-semibold text-white">
              {vm.bestActionNow.headline}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[11px]">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <span className="text-[9px] text-[#707987] uppercase font-semibold">Next Trigger</span>
                <div className="text-[11px] font-bold text-[#00C896] mt-0.5">{vm.bestActionNow.nextTrigger}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <span className="text-[9px] text-[#707987] uppercase font-semibold">Invalidation</span>
                <div className="text-[11px] font-bold text-[#E5484D] mt-0.5">{vm.bestActionNow.invalidation}</div>
              </div>
            </div>

            <div className="text-[10px] text-[#A5ABB4] bg-[#08090B] p-1.5 rounded-[2px] border border-[#191D23]/60">
              <span className="font-semibold text-[#E6E8EB]">Rationale: </span>
              {vm.bestActionNow.rationale}
            </div>
          </div>
        </Surface>

        {/* B. CURRENT MARKET STATE */}
        <Surface>
          <SectionHeader
            title="CURRENT MARKET STATE"
            accent="cyan"
            action={
              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#00C896]/10 text-[#00C896] border border-[#00C896]/30 font-bold">
                ● {vm.currentMarketState.bias}
              </span>
            }
          />
          <div className="p-2.5">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 text-[11px]">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Structure</div>
                <div className="font-bold text-white font-mono mt-0.5">{vm.currentMarketState.priceStructure}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Breadth</div>
                <div className="font-bold text-[#00C896] font-mono mt-0.5">{vm.currentMarketState.marketBreadth}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">VWAP Status</div>
                <div className="font-bold text-[#38BDF8] font-mono mt-0.5">{vm.currentMarketState.vwapStatus}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Momentum</div>
                <div className="font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.currentMarketState.momentum}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">VIX</div>
                <div className="font-bold text-[#E6E8EB] font-mono mt-0.5">{vm.currentMarketState.vixStr}</div>
              </div>
            </div>
          </div>
        </Surface>

        {/* C. PRIMARY SCENARIO */}
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
                  CONF {vm.primaryScenario.confidencePct}
                </span>
              </div>
            }
          />
          <div className="p-2.5 space-y-1.5 text-[11px]">
            <div><span className="text-[#707987] font-semibold">Plan: </span>{vm.primaryScenario.plan}</div>
            <div><span className="text-[#707987] font-semibold">Conditions: </span>{vm.primaryScenario.conditions}</div>
            <div><span className="text-[#707987] font-semibold">What To Do: </span>{vm.primaryScenario.whatToDo}</div>
            <div><span className="text-[#707987] font-semibold">Key Levels: </span><span className="font-mono text-[#38BDF8]">{vm.primaryScenario.keyLevels}</span></div>
            <div><span className="text-[#707987] font-semibold">Invalidation: </span><span className="font-mono text-[#E5484D]">{vm.primaryScenario.invalidation}</span></div>

            <div className="flex flex-wrap gap-1 pt-1.5 border-t border-[#191D23]">
              <span className="text-[9px] text-[#707987] font-semibold self-center mr-1">Evidence:</span>
              {vm.primaryScenario.evidenceTags.map((tag, idx) => (
                <span key={idx} className="text-[8px] font-mono px-1.5 py-0.2 rounded bg-[#08090B] text-[#A5ABB4] border border-[#191D23]">
                  ✓ {tag}
                </span>
              ))}
            </div>
          </div>
        </Surface>

        {/* D. ALTERNATE SCENARIO */}
        <Surface>
          <SectionHeader
            title="ALTERNATE SCENARIO"
            icon={TrendingDown}
            accent="rose"
            action={
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-bold text-[#E59700] bg-[#E59700]/10 px-1.5 py-0.5 rounded-[2px] border border-[#E59700]/30">
                  {vm.alternateScenario.name.toUpperCase()}
                </span>
                <span className="text-[10px] font-mono text-[#707987]">
                  CONF {vm.alternateScenario.confidencePct}
                </span>
              </div>
            }
          />
          <div className="p-2.5 space-y-1.5 text-[11px]">
            <div><span className="text-[#707987] font-semibold">Plan: </span>{vm.alternateScenario.plan}</div>
            <div><span className="text-[#707987] font-semibold">Conditions: </span>{vm.alternateScenario.conditions}</div>
            <div><span className="text-[#707987] font-semibold">What To Do: </span>{vm.alternateScenario.whatToDo}</div>
            <div><span className="text-[#707987] font-semibold">Key Levels: </span><span className="font-mono text-[#38BDF8]">{vm.alternateScenario.keyLevels}</span></div>
            <div><span className="text-[#707987] font-semibold">Invalidation: </span><span className="font-mono text-[#E5484D]">{vm.alternateScenario.invalidation}</span></div>

            <div className="flex flex-wrap gap-1 pt-1.5 border-t border-[#191D23]">
              <span className="text-[9px] text-[#707987] font-semibold self-center mr-1">Evidence:</span>
              {vm.alternateScenario.evidenceTags.map((tag, idx) => (
                <span key={idx} className="text-[8px] font-mono px-1.5 py-0.2 rounded bg-[#08090B] text-[#A5ABB4] border border-[#191D23]">
                  ✓ {tag}
                </span>
              ))}
            </div>
          </div>
        </Surface>

        {/* E. KEY LEVELS & REAL VALUE SUGGESTIONS */}
        <Surface>
          <SectionHeader
            title="KEY LEVELS & REAL VALUE SUGGESTIONS"
            accent="cyan"
          />
          <div className="p-2.5">
            <div className="overflow-x-auto rounded-[2px] border border-[#191D23]">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead>
                  <tr className="bg-[#0E1013] text-[#707987] text-[9px] uppercase font-bold border-b border-[#191D23]">
                    <th className="p-1.5">Type</th>
                    <th className="p-1.5">Level / Zone</th>
                    <th className="p-1.5">Conviction</th>
                    <th className="p-1.5">Why This Level Matters</th>
                    <th className="p-1.5">Data Basis</th>
                  </tr>
                </thead>
                <tbody className="bg-[#0B0D10]">
                  {vm.keyLevelsValueSuggestions.map((item, idx) => (
                    <tr key={idx} className="border-b border-[#191D23]/50 hover:bg-[#13161A]">
                      <td className="p-1.5 font-semibold text-[#E6E8EB]">{item.zone}</td>
                      <td className="p-1.5 font-mono text-[#38BDF8] font-bold">{item.upper}</td>
                      <td className="p-1.5">
                        <span className={`text-[8px] font-bold px-1 py-0.2 rounded ${
                          item.conviction === "High" ? "bg-[#00C896]/15 text-[#00C896]" :
                          item.conviction === "Moderate" ? "bg-[#E59700]/15 text-[#E59700]" :
                          "bg-[#191D23] text-[#707987]"
                        }`}>
                          {item.conviction}
                        </span>
                      </td>
                      <td className="p-1.5 text-[#A5ABB4] text-[10px]">{item.rationale}</td>
                      <td className="p-1.5 text-[#707987] text-[9px] font-mono">{item.dataBasis}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Surface>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          RIGHT SIDE — PROFESSIONAL CARDS (5 cols on XL)
      ───────────────────────────────────────────────────────────── */}
      <div className="xl:col-span-5 space-y-2.5">
        {/* CARD 1 — LIVE MARKET METRICS */}
        <Surface>
          <SectionHeader
            title="MARKET METRICS"
            accent="cyan"
            action={
              <span className={`text-[9px] font-mono uppercase px-1.5 py-0.2 rounded font-bold border ${
                vm.liveMetrics.isLive
                  ? "bg-[#00C896]/10 text-[#00C896] border-[#00C896]/30"
                  : "bg-[#707987]/15 text-[#A5ABB4] border-[#191D23]"
              }`}>
                ● {vm.liveMetrics.freshnessLabel || "LIVE"}
              </span>
            }
          />
          <div className="p-2.5">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 text-[11px]">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">NIFTY 50</div>
                <div className="font-bold text-white font-mono">{vm.liveMetrics.niftySpot}</div>
                <div className="text-[9px] text-[#00C896] font-mono">{vm.liveMetrics.niftyChange}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">BANK NIFTY</div>
                <div className="font-bold text-white font-mono">{vm.liveMetrics.bankNiftySpot}</div>
                <div className="text-[9px] text-[#00C896] font-mono">{vm.liveMetrics.bankNiftyChange}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">INDIA VIX</div>
                <div className="font-bold text-white font-mono">{vm.liveMetrics.indiaVix}</div>
                <div className="text-[9px] text-[#00C896] font-mono">{vm.liveMetrics.indiaVixChange}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">RSI (NIFTY)</div>
                <div className="font-bold text-[#E6E8EB] font-mono">{vm.liveMetrics.rsiMomentum}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">PCR (OI)</div>
                <div className="font-bold text-[#E6E8EB] font-mono">{vm.liveMetrics.pcr}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">MARKET BREADTH</div>
                <div className="font-bold text-[#00C896] font-mono">{vm.liveMetrics.breadth}</div>
                <div className="text-[9px] text-[#707987] font-mono">{vm.liveMetrics.breadthAdvDec}</div>
              </div>
            </div>
          </div>
        </Surface>

        {/* CARD 2 — REAL-TIME WATCHLIST */}
        <Surface>
          <SectionHeader
            title="REAL-TIME WATCHLIST"
            detail="What's moving now"
            accent="cyan"
          />
          <div className="p-2.5">
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <div className="text-[9px] uppercase font-bold text-[#707987] mb-1">Leading Sectors</div>
                <div className="space-y-1 text-[#00C896] font-medium text-[10px]">
                  {vm.realTimeWatchlist.leadingSectors.map((s, idx) => (
                    <div key={idx} className="p-1 rounded-[2px] bg-[#08090B] border border-[#191D23]">▲ {s}</div>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-[9px] uppercase font-bold text-[#707987] mb-1">Lagging Sectors</div>
                <div className="space-y-1 text-[#E5484D] font-medium text-[10px]">
                  {vm.realTimeWatchlist.laggingSectors.map((s, idx) => (
                    <div key={idx} className="p-1 rounded-[2px] bg-[#08090B] border border-[#191D23]">▼ {s}</div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Surface>

        {/* CARD 3 — SUITABLE STRATEGIES NOW */}
        <Surface>
          <SectionHeader
            title="SUITABLE STRATEGIES NOW"
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
                      <span className="text-[#E59700] text-[9px]">
                        {"★".repeat(strat.suitabilityStars || 3)}
                      </span>
                    </div>
                    <div className="text-[9px] text-[#A5ABB4] space-y-0.5">
                      <div><span className="text-[#707987]">When:</span> {strat.whenCondition}</div>
                      <div><span className="text-[#707987]">Trigger:</span> {strat.trigger}</div>
                      <div><span className="text-[#707987]">Target:</span> {strat.targetArea}</div>
                    </div>
                  </div>
                  <div className="mt-1.5 pt-1 border-t border-[#191D23] text-[8px] text-[#707987]">
                    <span className="font-mono text-[#38BDF8]">R:R {strat.riskReward}</span> • Conf: {strat.confidence}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Surface>

        {/* CARD 4 — QUALIFIED OPPORTUNITY STATUS */}
        <Surface>
          <SectionHeader
            title="QUALIFIED OPPORTUNITY STATUS"
            accent="emerald"
            action={
              vm.opportunityStatus.hasTrade ? (
                <button
                  onClick={() => setActiveModule("portfolio")}
                  className="flex items-center gap-1 text-[9px] font-bold px-2 py-0.5 rounded-[2px] bg-[#00C896]/15 text-[#00C896] border border-[#00C896]/30 hover:bg-[#00C896]/25"
                >
                  VIEW IN PORTFOLIO <ArrowUpRight size={10} />
                </button>
              ) : (
                <span className="text-[9px] font-mono text-[#707987]">INFORMATIONAL</span>
              )
            }
          />
          <div className="p-2.5 space-y-2">
            <div className="grid grid-cols-5 gap-1 text-center text-[10px] py-1.5 px-1 bg-[#08090B] rounded-[2px] border border-[#191D23]">
              <div className="p-0.5">
                <div className="w-4 h-4 rounded-full bg-[#00C896]/20 border border-[#00C896]/40 text-[#00C896] text-[8px] font-bold flex items-center justify-center mx-auto mb-0.5">1</div>
                <div className="text-[8px] text-[#707987]">IDEA</div>
              </div>
              <div className="p-0.5">
                <div className="w-4 h-4 rounded-full bg-[#E59700]/20 border border-[#E59700]/40 text-[#E59700] text-[8px] font-bold flex items-center justify-center mx-auto mb-0.5">2</div>
                <div className="text-[8px] text-[#E59700] font-semibold">CONDITIONS</div>
              </div>
              <div className="p-0.5">
                <div className="w-4 h-4 rounded-full bg-[#191D23] text-[#707987] text-[8px] font-bold flex items-center justify-center mx-auto mb-0.5">3</div>
                <div className="text-[8px] text-[#707987]">CONFIRM</div>
              </div>
              <div className="p-0.5">
                <div className="w-4 h-4 rounded-full bg-[#191D23] text-[#707987] text-[8px] font-bold flex items-center justify-center mx-auto mb-0.5">4</div>
                <div className="text-[8px] text-[#707987]">QUALIFIED</div>
              </div>
              <div className="p-0.5">
                <div className="w-4 h-4 rounded-full bg-[#191D23] text-[#707987] text-[8px] font-bold flex items-center justify-center mx-auto mb-0.5">5</div>
                <div className="text-[8px] text-[#707987]">ACTION</div>
              </div>
            </div>
            <div className="text-[10px] text-[#A5ABB4] bg-[#08090B] p-1.5 rounded-[2px] border border-[#191D23]/60">
              {vm.opportunityStatus.summary}
            </div>
          </div>
        </Surface>

        {/* CARD 5 — RISK CONTEXT */}
        <Surface>
          <SectionHeader
            title="RISK CONTEXT"
            icon={ShieldAlert}
            accent="amber"
          />
          <div className="p-2.5">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-[11px] mb-2">
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Global Cues</div>
                <div className="font-bold text-[#00C896]">{vm.riskContext.globalCues}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">News / Events</div>
                <div className="font-bold text-[#E6E8EB]">{vm.riskContext.newsSentiment}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Volatility</div>
                <div className="font-bold text-[#38BDF8]">{vm.riskContext.volatilityExpectation}</div>
              </div>
              <div className="p-1.5 rounded-[2px] bg-[#08090B] border border-[#191D23]">
                <div className="text-[9px] text-[#707987] uppercase font-semibold">Market Risk</div>
                <div className="font-bold text-[#E59700]">{vm.riskContext.overallRisk}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-1 pt-1.5 border-t border-[#191D23]">
              <span className="text-[9px] text-[#707987] font-semibold self-center mr-1">Proof:</span>
              {vm.riskContext.proofBadges.map((badge, idx) => (
                <span key={idx} className="text-[8px] font-mono px-1.5 py-0.2 rounded bg-[#08090B] text-[#A5ABB4] border border-[#191D23]">
                  ✓ {badge}
                </span>
              ))}
            </div>
          </div>
        </Surface>
      </div>
    </div>
  );
};
