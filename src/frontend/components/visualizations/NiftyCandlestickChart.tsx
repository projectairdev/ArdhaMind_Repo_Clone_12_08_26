import React from "react";
import { TradingViewLightweightChart } from "./TradingViewLightweightChart";

export function NiftyCandlestickChart({
  height = 380,
  embedded = true,
  timeframe = "15m",
}: {
  height?: number;
  embedded?: boolean;
  timeframe?: "1m" | "5m" | "15m" | "1H" | "1D";
}) {
  return <TradingViewLightweightChart height={height} embedded={embedded} timeframe={timeframe} />;
}
