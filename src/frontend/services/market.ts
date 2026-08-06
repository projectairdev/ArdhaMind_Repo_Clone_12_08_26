// src/frontend/services/market.ts
import { MarketContext, OptionContext } from "../types";

export async function getMarketContext(): Promise<MarketContext> {
  const resp = await fetch("/api/market");
  if (!resp.ok) {
    throw new Error(`Failed to fetch market context: ${resp.statusText}`);
  }
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data.market_context;
}

export async function getOptionContext(): Promise<OptionContext> {
  const resp = await fetch("/api/market");
  if (!resp.ok) {
    throw new Error(`Failed to fetch option context: ${resp.statusText}`);
  }
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data.option_context;
}
