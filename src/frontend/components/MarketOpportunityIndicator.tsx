import React, { useState, useEffect } from "react";
import { Zap, ArrowRight } from "lucide-react";
import { Surface } from "./ui/WorkspacePrimitives";
import { useNavigation } from "../context/NavigationContext";
import { TradeProposalPayload } from "./ActiveOpportunityHero";

export const MarketOpportunityIndicator: React.FC = () => {
  const [proposal, setProposal] = useState<TradeProposalPayload | null>(null);
  const { navigateTo } = useNavigation();

  useEffect(() => {
    const fetchActiveProposal = async () => {
      try {
        const res = await fetch("/api/phase3/proposals/active");
        if (res.ok) {
          const data = await res.json();
          setProposal(data);
        }
      } catch (err) {
        console.warn("Failed fetching active proposal for market indicator:", err);
      }
    };

    fetchActiveProposal();

    const handleWsEvent = (evt: MessageEvent) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === "phase3_proposal" && msg.data) {
          setProposal(msg.data);
        }
      } catch {}
    };

    const ws = (window as any).__ARDHA_WS__;
    if (ws && typeof ws.addEventListener === "function") {
      ws.addEventListener("message", handleWsEvent);
      return () => ws.removeEventListener("message", handleWsEvent);
    }
  }, []);

  const isNoTrade =
    !proposal ||
    proposal.state === "NO_TRADE" ||
    proposal.state === "EXPIRED" ||
    proposal.state === "REJECTED" ||
    proposal.direction === "NEUTRAL";

  if (isNoTrade) {
    return null;
  }

  const isBullish = proposal.direction?.toUpperCase() === "BULLISH";

  return (
    <Surface className="overflow-hidden border border-[#38BDF8]/30 bg-[#0E1013] px-3.5 py-2">
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex items-center gap-2.5 font-mono text-[11px]">
          <span className="flex items-center justify-center w-5 h-5 rounded bg-[#38BDF8]/10 text-[#38BDF8]">
            <Zap size={12} className="animate-pulse" />
          </span>
          <span className="font-bold text-[#E6E8EB] uppercase tracking-wider">
            TRADE OPPORTUNITY DETECTED
          </span>
          <span
            className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase font-mono ${
              isBullish
                ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
            }`}
          >
            {proposal.direction} {proposal.underlying} {proposal.strike} {proposal.option_type}
          </span>
          <span className="text-[10px] text-[#707987] hidden sm:inline font-sans">
            Setup: <strong className="text-[#E6E8EB]">{proposal.setup_type || "NIFTY Strategy"}</strong>
          </span>
        </div>

        <button
          type="button"
          onClick={() => navigateTo({ workspace: "portfolio" })}
          className="px-3 py-1 rounded bg-[#38BDF8]/10 hover:bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/40 font-mono text-[10px] font-bold transition flex items-center gap-1.5 cursor-pointer"
        >
          <span>View in Portfolio</span>
          <ArrowRight size={11} />
        </button>
      </div>
    </Surface>
  );
};
