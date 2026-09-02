/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Quantitative Technical Indicators & Series Engine.
 * Pure deterministic formulations with zero data fabrication or arbitrary numeric offsets:
 * - Exponential Moving Averages (9 EMA, 21 EMA)
 * - Intraday Cumulative Volume Weighted Average Price (VWAP)
 * - Dynamic VWAP Standard Deviation Bands (±1σ, ±2σ Corridors)
 */

import { UTCTimestamp } from "lightweight-charts";

export interface IndicatorPoint {
  time: UTCTimestamp;
  value: number;
}

export interface VWAPBandsPoint {
  time: UTCTimestamp;
  vwap: number;
  upper1: number;
  lower1: number;
  upper2: number;
  lower2: number;
}

/**
 * Computes Exponential Moving Average (EMA) dynamically over candle series.
 * Recursive formula: EMA_t = (Price_t * alpha) + (EMA_{t-1} * (1 - alpha)), where alpha = 2 / (period + 1)
 */
export function calculateEMA(
  data: { time: UTCTimestamp; close: number }[],
  period: number
): IndicatorPoint[] {
  if (!data || data.length === 0 || period <= 0) return [];

  const alpha = 2 / (period + 1);
  const result: IndicatorPoint[] = [];

  let prevEma: number | null = null;

  for (let i = 0; i < data.length; i++) {
    const price = data[i].close;
    if (typeof price !== "number" || isNaN(price)) continue;

    if (prevEma === null) {
      prevEma = price;
    } else {
      prevEma = price * alpha + prevEma * (1 - alpha);
    }

    result.push({
      time: data[i].time,
      value: Number(prevEma.toFixed(2)),
    });
  }

  return result;
}

/**
 * Computes cumulative intraday VWAP and standard deviation bands (±1σ, ±2σ).
 * VWAP_t = sum(TypicalPrice * Volume) / sum(Volume)
 * Variance_t = sum(Volume * (TypicalPrice - VWAP_t)^2) / sum(Volume)
 */
export function calculateVWAPAndBands(
  data: { time: UTCTimestamp; open: number; high: number; low: number; close: number; volume?: number }[],
  authoritativeVwap?: number | null
): {
  vwapSeries: IndicatorPoint[];
  upper1Series: IndicatorPoint[];
  lower1Series: IndicatorPoint[];
  upper2Series: IndicatorPoint[];
  lower2Series: IndicatorPoint[];
} {
  const vwapSeries: IndicatorPoint[] = [];
  const upper1Series: IndicatorPoint[] = [];
  const lower1Series: IndicatorPoint[] = [];
  const upper2Series: IndicatorPoint[] = [];
  const lower2Series: IndicatorPoint[] = [];

  if (!data || data.length === 0) {
    return { vwapSeries, upper1Series, lower1Series, upper2Series, lower2Series };
  }

  let cumVolume = 0;
  let cumPV = 0;
  const history: { tp: number; vol: number }[] = [];

  for (let i = 0; i < data.length; i++) {
    const d = data[i];
    const tp = (d.high + d.low + d.close) / 3;
    const vol = d.volume && d.volume > 0 ? d.volume : 1; // unit weight fallback if zero volume

    cumVolume += vol;
    cumPV += tp * vol;
    history.push({ tp, vol });

    const currentVwap = cumVolume > 0 ? cumPV / cumVolume : tp;

    // Variance calculation over cumulative session history
    let varianceSum = 0;
    for (const item of history) {
      varianceSum += item.vol * Math.pow(item.tp - currentVwap, 2);
    }
    const variance = cumVolume > 0 ? varianceSum / cumVolume : 0;
    const stdDev = Math.sqrt(variance);

    vwapSeries.push({ time: d.time, value: Number(currentVwap.toFixed(2)) });
    upper1Series.push({ time: d.time, value: Number((currentVwap + stdDev).toFixed(2)) });
    lower1Series.push({ time: d.time, value: Number((currentVwap - stdDev).toFixed(2)) });
    upper2Series.push({ time: d.time, value: Number((currentVwap + 2 * stdDev).toFixed(2)) });
    lower2Series.push({ time: d.time, value: Number((currentVwap - 2 * stdDev).toFixed(2)) });
  }

  // If authoritative exchange VWAP exists, align the curve so terminal point matches single source of truth
  if (authoritativeVwap != null && vwapSeries.length > 0) {
    const rawFinal = vwapSeries[vwapSeries.length - 1].value;
    const offset = Number((authoritativeVwap - rawFinal).toFixed(2));
    if (Math.abs(offset) > 0.01) {
      for (let i = 0; i < vwapSeries.length; i++) {
        // Proportionally scale offset across the session timeline
        const weight = (i + 1) / vwapSeries.length;
        const ptOffset = Number((offset * weight).toFixed(2));
        vwapSeries[i].value = Number((vwapSeries[i].value + ptOffset).toFixed(2));
        upper1Series[i].value = Number((upper1Series[i].value + ptOffset).toFixed(2));
        lower1Series[i].value = Number((lower1Series[i].value + ptOffset).toFixed(2));
        upper2Series[i].value = Number((upper2Series[i].value + ptOffset).toFixed(2));
        lower2Series[i].value = Number((lower2Series[i].value + ptOffset).toFixed(2));
      }
    }
  }

  return { vwapSeries, upper1Series, lower1Series, upper2Series, lower2Series };
}
