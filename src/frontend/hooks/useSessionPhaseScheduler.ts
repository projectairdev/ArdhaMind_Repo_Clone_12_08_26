/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * High-Precision Client-Side Session Phase Scheduler Hook.
 * Computes exact milliseconds remaining until the nearest IST session boundary:
 * - 08:00:00 IST (Pre-Market Start / Baseline Hydration)
 * - 09:15:00 IST (Live Market Continuous Trading Start)
 * - 15:30:00 IST (Post-Market EOD Synthesis Start)
 * 
 * Sets an autonomous target timer (setTimeout) + 5-second interval fallback
 * to trigger seamless zero-refresh UI cutover.
 */

import { useEffect, useCallback } from "react";

export interface SessionBoundaryPlan {
  nextBoundaryName: "PRE_MARKET" | "LIVE" | "POST_MARKET";
  msUntilBoundary: number;
  boundaryTimeIST: string;
}

export function computeNextISTSessionBoundary(nowDate: Date = new Date()): SessionBoundaryPlan {
  // Convert current UTC time to IST components
  const istOffsetMs = 5.5 * 60 * 60 * 1000;
  const nowUtc = nowDate.getTime();
  const nowIstMs = nowUtc + istOffsetMs;
  const nowIst = new Date(nowIstMs);

  const hours = nowIst.getUTCHours();
  const minutes = nowIst.getUTCMinutes();
  const seconds = nowIst.getUTCSeconds();
  const currentTotalSeconds = hours * 3600 + minutes * 60 + seconds;

  // Boundaries in seconds from midnight IST:
  // 08:00:00 -> 8 * 3600 = 28800
  // 09:15:00 -> 9 * 3600 + 15 * 60 = 33300
  // 15:30:00 -> 15 * 3600 + 30 * 60 = 55800
  const BOUNDARIES: { name: "PRE_MARKET" | "LIVE" | "POST_MARKET"; timeStr: string; sec: number }[] = [
    { name: "PRE_MARKET", timeStr: "08:00:00", sec: 28800 },
    { name: "LIVE", timeStr: "09:15:00", sec: 33300 },
    { name: "POST_MARKET", timeStr: "15:30:00", sec: 55800 },
  ];

  let next = BOUNDARIES.find((b) => b.sec > currentTotalSeconds);
  let secondsRemaining = 0;

  if (next) {
    secondsRemaining = next.sec - currentTotalSeconds;
  } else {
    // Past 15:30, next boundary is 08:00:00 tomorrow
    next = BOUNDARIES[0];
    secondsRemaining = (86400 - currentTotalSeconds) + next.sec;
  }

  const msRemaining = Math.max(100, secondsRemaining * 1000 - nowIst.getUTCMilliseconds());

  return {
    nextBoundaryName: next.name,
    msUntilBoundary: msRemaining,
    boundaryTimeIST: next.timeStr,
  };
}

export function useSessionPhaseScheduler(onPhaseBoundaryTrigger: () => void) {
  const triggerTransition = useCallback(() => {
    onPhaseBoundaryTrigger();
  }, [onPhaseBoundaryTrigger]);

  useEffect(() => {
    let timer: any = null;
    let heartbeat: any = null;
    let lastBoundary = "";

    const scheduleNextBoundary = () => {
      if (timer) clearTimeout(timer);
      const plan = computeNextISTSessionBoundary();
      
      // Arm the timer with a small 50ms buffer to ensure wall-clock is strictly past the boundary
      timer = setTimeout(() => {
        triggerTransition();
        scheduleNextBoundary();
      }, plan.msUntilBoundary + 50);
    };

    scheduleNextBoundary();

    // 5-second interval fallback to guard against background tab throttling and clock drift
    heartbeat = setInterval(() => {
      const plan = computeNextISTSessionBoundary();
      if (plan.msUntilBoundary <= 5000 && plan.boundaryTimeIST !== lastBoundary) {
        lastBoundary = plan.boundaryTimeIST;
        triggerTransition();
      }
    }, 5000);

    return () => {
      if (timer) clearTimeout(timer);
      if (heartbeat) clearInterval(heartbeat);
    };
  }, [triggerTransition]);
}
