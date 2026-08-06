// src/frontend/services/dashboard.ts
import {
  MarketScore,
  OpportunityContext,
  StrategyEvaluation,
  ConfidenceReport,
  RiskReport,
  DecisionReport,
  OperationsReport,
  ConfigurationReport,
  ExplanationReport,
} from "../types";

export async function getMarketScore(): Promise<MarketScore> {
  const resp = await fetch("/api/dashboard/market-score");
  if (!resp.ok) {
    throw new Error(`Failed to fetch market score: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getOpportunityContext(): Promise<OpportunityContext> {
  const resp = await fetch("/api/dashboard/opportunity-context");
  if (!resp.ok) {
    throw new Error(`Failed to fetch opportunity context: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getStrategyEvaluation(): Promise<StrategyEvaluation> {
  const resp = await fetch("/api/dashboard/strategy-evaluation");
  if (!resp.ok) {
    throw new Error(`Failed to fetch strategy evaluation: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getConfidenceReport(): Promise<ConfidenceReport> {
  const resp = await fetch("/api/dashboard/confidence-report");
  if (!resp.ok) {
    throw new Error(`Failed to fetch confidence report: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getRiskReport(): Promise<RiskReport> {
  const resp = await fetch("/api/dashboard/risk-report");
  if (!resp.ok) {
    throw new Error(`Failed to fetch risk report: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getDecisionReport(): Promise<DecisionReport> {
  const resp = await fetch("/api/dashboard/decision-report");
  if (!resp.ok) {
    throw new Error(`Failed to fetch decision report: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getOperationsReport(): Promise<OperationsReport> {
  const resp = await fetch("/api/dashboard/operations-report");
  if (!resp.ok) {
    throw new Error(`Failed to fetch operations report: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getConfigurationReport(): Promise<ConfigurationReport> {
  const resp = await fetch("/api/dashboard/configuration-report");
  if (!resp.ok) {
    throw new Error(`Failed to fetch configuration report: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getExplanationReport(): Promise<ExplanationReport> {
  const resp = await fetch("/api/dashboard/explanation-report");
  if (!resp.ok) {
    throw new Error(`Failed to fetch explanation report: ${resp.statusText}`);
  }
  return resp.json();
}
