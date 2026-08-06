// src/frontend/services/planner.ts
import {
  TradePlan,
  EveningReport,
  IntradayReport,
  ValidationReport,
  OptimizationReport,
} from "../types";

export async function getTradePlan(): Promise<TradePlan> {
  const resp = await fetch("/api/planner/trade-plan");
  if (!resp.ok) {
    throw new Error(`Failed to fetch trade plan: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getEveningReport(): Promise<EveningReport> {
  const resp = await fetch("/api/evening-report");
  if (!resp.ok) {
    throw new Error(`Failed to fetch evening report: ${resp.statusText}`);
  }
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data;
}

export async function getIntradayReport(): Promise<IntradayReport> {
  const resp = await fetch("/api/planner/intraday-report");
  if (!resp.ok) {
    throw new Error(`Failed to fetch intraday report: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getValidationReport(): Promise<ValidationReport> {
  const resp = await fetch("/api/planner/validation-report");
  if (!resp.ok) {
    throw new Error(`Failed to fetch validation report: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getOptimizationReport(): Promise<OptimizationReport> {
  const resp = await fetch("/api/planner/optimization-report");
  if (!resp.ok) {
    throw new Error(`Failed to fetch optimization report: ${resp.statusText}`);
  }
  return resp.json();
}
