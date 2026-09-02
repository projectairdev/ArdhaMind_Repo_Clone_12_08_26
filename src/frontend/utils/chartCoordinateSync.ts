/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * chartCoordinateSync.ts
 * Utilities for synchronizing probabilistic forward projection overlays with 
 * financial chart coordinate systems (Price-to-Y and Time-to-X geometry).
 */

import { HorizonProjectionCalibration } from "./canonicalIntelligenceAdapter";

export interface ChartProjectionBounds {
  width: number;
  height: number;
  padding: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
  minPrice: number;
  maxPrice: number;
  totalBars: number;
  historyBars: number;
}

/**
 * Calculates Y coordinate for a given price level.
 */
export function priceToYCoordinate(
  price: number,
  minPrice: number,
  maxPrice: number,
  height: number,
  paddingTop: number,
  paddingBottom: number
): number {
  const availableHeight = height - paddingTop - paddingBottom;
  const ratio = (price - minPrice) / (maxPrice - minPrice);
  return height - paddingBottom - ratio * availableHeight;
}

/**
 * Calculates X coordinate for a given bar index.
 */
export function barIndexToXCoordinate(
  barIndex: number,
  totalBars: number,
  width: number,
  paddingLeft: number,
  paddingRight: number
): number {
  const availableWidth = width - paddingLeft - paddingRight;
  return paddingLeft + (barIndex / totalBars) * availableWidth;
}

/**
 * Generates forward whitespace candle timestamps for Lightweight Charts.
 */
export function generateForwardWhitespaceBars(
  lastTimestampSec: number,
  forwardBarCount: number,
  stepSeconds: number = 300
): number[] {
  const bars: number[] = [];
  for (let i = 1; i <= forwardBarCount; i++) {
    bars.push(lastTimestampSec + i * stepSeconds);
  }
  return bars;
}
