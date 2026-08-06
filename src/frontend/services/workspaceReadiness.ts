export type PhaseOneWorkspace = "nifty-live" | "pre-market" | "todays-analysis" | "news-updates" | "live-assistant" | "settings";

export interface WorkspaceReadiness {
  accessible: boolean;
  reason: string;
}

export function evaluateWorkspaceReadiness(workspace: PhaseOneWorkspace, available: { market: boolean; options: boolean; history: boolean; news: boolean; analysis: boolean }): WorkspaceReadiness {
  if (workspace === "nifty-live" || workspace === "settings") return { accessible: true, reason: "" };
  if (workspace === "pre-market") return available.history ? { accessible: true, reason: "" } : { accessible: false, reason: "Waiting for historical data or a final validated session snapshot." };
  if (workspace === "todays-analysis") return available.market ? { accessible: true, reason: "" } : { accessible: false, reason: "Waiting for validated market context." };
  if (workspace === "news-updates") return available.news ? { accessible: true, reason: "" } : { accessible: false, reason: "News provider unavailable." };
  return available.market && available.options && available.analysis ? { accessible: true, reason: "" } : { accessible: false, reason: "Waiting for fresh market, option-chain and analytical outputs." };
}

