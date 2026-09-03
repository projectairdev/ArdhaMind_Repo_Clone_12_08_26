import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { X } from "lucide-react";
import { useWorkstationState } from "./WorkstationStateContext";
import { formatNumber, safeArray, safeString } from "../utils/safeHelpers";
import { formatTimestampIST } from "../utils/timeFormatting";
import { CompactRows, SectionHeader, Surface } from "../components/ui/WorkspacePrimitives";

export type InspectionDomain = "institutional" | "volatility" | "global" | "breadth" | "sector" | "pcr" | "max_pain" | "strike" | "telemetry" | "market_context" | "market_level" | "membership";
export type InspectionSelection = { domain: InspectionDomain; title: string; payload?: any };
type InspectionApi = { openInspection: (selection: InspectionSelection) => void; closeInspection: () => void };
type InspectionModel = { source: any; rows: Array<[string, React.ReactNode]>; meta: any };
const Context = createContext<InspectionApi>({ openInspection: () => undefined, closeInspection: () => undefined });

function finiteSeries(value: any): Array<{ time?: string; value: number }> {
  const raw = safeArray(value?.history ?? value?.historical_series ?? value?.historical_observations ?? value?.observations ?? value?.series ?? value?.history_points);
  return raw.map((item: any) => ({ time: item?.observed_at ?? item?.timestamp ?? item?.date ?? item?.time, value: Number(item?.value ?? item?.price ?? item?.close ?? item?.change_pct ?? item?.net_value) })).filter(item => Number.isFinite(item.value));
}

export function CanonicalSparkline({ source, height = 56 }: { source: any; height?: number }) {
  const points = finiteSeries(source);
  if (points.length < 2) return null;
  const values = points.map(point => point.value), min = Math.min(...values), max = Math.max(...values), range = max - min || 1;
  const polyline = values.map((value, index) => `${(index / (values.length - 1)) * 300},${height - 5 - ((value - min) / range) * (height - 10)}`).join(" ");
  const positive = values.at(-1)! >= values[0];
  return <svg aria-label="Canonical historical observations" viewBox={`0 0 300 ${height}`} className="w-full" style={{ height }}><polyline fill="none" points={polyline} stroke={positive ? "#34d399" : "#fb7185"} strokeWidth="1.5" vectorEffect="non-scaling-stroke" /></svg>;
}

function displayValue(value: any) {
  if (value == null || value === "") return "—";
  if (typeof value === "number") return formatNumber(value, 2);
  if (typeof value === "object") return safeString(value.summary ?? value.status ?? value.regime ?? value.interpretation ?? "Available");
  return String(value);
}

function inspectionModel(selection: InspectionSelection, state: any, marketContext: any): InspectionModel {
  const macro = state?.macro_intelligence ?? {}, options = state?.options_intelligence ?? state?.option_intelligence ?? {}, quality = state?.data_quality ?? {};
  if (selection.domain === "global") {
    const quotes = Object.values(macro.quotes ?? {}) as any[];
    return { source: macro, rows: quotes.map(q => [safeString(q.name || q.symbol), `${displayValue(q.price ?? q.value ?? q.last_price)}${q.change_pct == null ? "" : ` · ${Number(q.change_pct) > 0 ? "+" : ""}${formatNumber(q.change_pct, 2)}%`}`] as [string, React.ReactNode]), meta: macro.provider_health };
  }
  if (selection.domain === "institutional") {
    const cash = selection.payload ?? macro.institutional_flows ?? macro.institutional_cash ?? {};
    const derivatives = macro.institutional_derivatives?.positioning ?? {};
    const cashRows = Array.isArray(cash) ? cash.map((row: any) => [safeString(row.dataset_type || row.name), displayValue(row.net_value ?? row.value)] as [string, React.ReactNode]) : Object.entries(cash).map(([key, value]) => [key.replaceAll("_", " "), displayValue(value)] as [string, React.ReactNode]);
    return { source: cash, rows: [...cashRows, ...Object.entries(derivatives).map(([key, value]: [string, any]) => [key.replaceAll("_", " "), displayValue(value?.net_position ?? value)] as [string, React.ReactNode])], meta: cash };
  }
  if (selection.domain === "volatility") {
    const vix = macro.india_vix ?? selection.payload ?? {};
    return { source: vix, rows: [["India VIX", displayValue(vix.value)], ["Change", displayValue(vix.change_pct)], ["Regime", displayValue(vix.regime)], ["ATM IV", displayValue(options.atm_iv ?? options.implied_volatility)], ["Expected move", displayValue(options.expected_move)]], meta: vix };
  }
  if (selection.domain === "breadth") {
    const breadth = marketContext?.breadth ?? state?.market_data?.breadth ?? {};
    return { source: breadth, rows: [["Advances", displayValue(breadth.advances)], ["Declines", displayValue(breadth.declines)], ["A/D ratio", displayValue(breadth.advance_decline_ratio)], ["Coverage", displayValue(breadth.coverage?.valid)], ["Status", displayValue(breadth.status)]], meta: breadth };
  }
  if (selection.domain === "sector") {
    const sector = selection.payload ?? {};
    return { source: sector, rows: [["Index", displayValue(sector.name)], ["Latest value", displayValue(sector.ltp)], ["Absolute change", displayValue(sector.change)], ["Change %", sector.change_pct == null ? "—" : `${Number(sector.change_pct) > 0 ? "+" : ""}${formatNumber(sector.change_pct, 2)}%`], ["Direction", sector.change_pct == null ? "—" : Number(sector.change_pct) > 0 ? "Positive" : Number(sector.change_pct) < 0 ? "Negative" : "Flat"], ["Session", displayValue(sector.observation_mode)]], meta: sector };
  }
  if (selection.domain === "strike") {
    const strike = selection.payload ?? {};
    return { source: strike, rows: Object.entries(strike).map(([key, value]) => [key.replaceAll(/([A-Z])/g, " $1"), displayValue(value)] as [string, React.ReactNode]), meta: quality.option_intelligence };
  }
  if (selection.domain === "pcr" || selection.domain === "max_pain") {
    const key = selection.domain === "pcr" ? "pcr" : "max_pain";
    return { source: options[key], rows: [[selection.title, displayValue(options[key] ?? marketContext?.[key])], ["ATM", displayValue(options.atm_strike)], ["Expiry", displayValue(options.expiry ?? options.current_weekly_expiry)], ["Options bias", displayValue(options.market_option_bias ?? options.options_bias)]], meta: quality.option_intelligence };
  }
  if (selection.domain === "market_context") {
    const unified = state?.unified_intelligence ?? {}, explanation = state?.explanation ?? {}, today = state?.session_story?.todays_analysis ?? {};
    return { source: state?.market_data, rows: [["Market state", displayValue(unified.market_state?.state ?? unified.market_state?.trend ?? today.trend_classification)], ["Confidence", displayValue(unified.confidence ?? today.conviction ?? state?.confidence?.confidence_level)], ["Analytical risk", displayValue(state?.deterministic_risk?.risk_level ?? unified.risk?.state)], ["Primary driver", displayValue(today.primary_driver)], ["Confirming signals", safeArray(explanation.confirming_signals).join(", ") || "—"], ["Opposing signals", safeArray(explanation.opposing_signals).join(", ") || "—"], ["Interpretation", displayValue(explanation.summary)], ["Invalidation", displayValue(today.invalidation_conditions?.view_weakens_if)]], meta: state?.data_quality?.market_data };
  }
  if (selection.domain === "market_level") {
    const structural = state?.session_story?.pre_market_report?.critical_levels?.structural_details ?? {};
    return { source: structural, rows: [["Pivot", displayValue(structural.pivot_level?.price ?? state?.option_intelligence?.atm_strike)], ["Immediate support", displayValue(state?.market_data?.support_levels?.[0])], ["Immediate resistance", displayValue(state?.market_data?.resistance_levels?.[0])], ["Max Pain", displayValue(state?.option_intelligence?.max_pain)], ["Methodology", displayValue(structural.methodology)], ["Pivot evidence", safeArray(structural.pivot_level?.sources).join(", ") || "—"], ["Confidence", displayValue(structural.pivot_level?.confidence)], ["Description", displayValue(structural.pivot_level?.description)]], meta: structural.pivot_level };
  }
  if (selection.domain === "membership") {
    const membership = selection.payload ?? state?.market_data?.constituent_instruments ?? {}, breadth = state?.market_data?.breadth ?? {};
    return { source: membership, rows: [["Official membership", membership.membership_count === 50 ? "Verified" : "—"], ["Official members", displayValue(membership.membership_count)], ["Kite instruments resolved", membership.resolved_count == null ? "—" : `${membership.resolved_count} / ${membership.expected_count}`], ["Constituent quotes observed", breadth.coverage?.valid == null ? "—" : `${breadth.coverage.valid} / ${breadth.coverage.expected}`], ["Membership source", displayValue(membership.membership_source)], ["Source attribution", displayValue(membership.source_attribution)], ["Breadth freshness", displayValue(breadth.freshness)], ["Breadth source", displayValue(breadth.source)]], meta: { source: membership.membership_source, observed_at: membership.retrieved_at ?? breadth.timestamp, freshness: breadth.freshness } };
  }
  const quote = selection.payload ?? {};
  const globalEvidence = safeArray(state?.explanation?.evidence?.global).find((item: any) => String(item).toUpperCase().includes(selection.title.toUpperCase().replace(" 500", "")));
  return { source: quote, rows: [["Instrument", selection.title], ["Latest eligible value", displayValue(quote.value ?? quote.price)], ["Absolute change", displayValue(quote.change)], ["Change %", quote.changePct == null && quote.change_pct == null ? "—" : `${Number(quote.changePct ?? quote.change_pct) > 0 ? "+" : ""}${formatNumber(quote.changePct ?? quote.change_pct, 2)}%`], ["Direction", (quote.changePct ?? quote.change_pct) == null ? "—" : Number(quote.changePct ?? quote.change_pct) > 0 ? "Positive" : Number(quote.changePct ?? quote.change_pct) < 0 ? "Negative" : "Flat"], ["Market session", displayValue(quote.sessionContext ?? quote.source_session)], ["NIFTY relevance", globalEvidence ?? "No additional deterministic interpretation available"]], meta: quote };
}

function supportsDeepDive(selection: InspectionSelection, model: InspectionModel, state: any) {
  if (finiteSeries(model.source).length > 1) return true;
  if (selection.domain === "institutional") return Object.keys(state?.macro_intelligence?.institutional_derivatives?.positioning ?? {}).length > 0;
  if (selection.domain === "breadth") return safeArray(state?.market_data?.breadth?.observations).length > 0;
  if (selection.domain === "market_context") return Boolean(state?.session_story?.todays_analysis || state?.unified_intelligence);
  if (selection.domain === "membership") return safeArray(selection.payload?.constituents).length === 50;
  return false;
}

function Provenance({ model }: { model: any }) {
  const meta = model.meta ?? {};
  const source = meta.source_name ?? meta.sourceName ?? meta.source ?? meta.provider_name;
  const observed = meta.observed_at ?? meta.observedAt ?? meta.observation_timestamp ?? meta.timestamp ?? meta.published_at;
  const freshness = meta.freshness_status ?? meta.freshness ?? meta.status;
  return <div className="mt-4 space-y-1 border-t border-[#292929] pt-3 text-[10px] text-[#737373]">{freshness && <div>Freshness: {safeString(freshness)}</div>}{observed && <div>Observed: {formatTimestampIST(observed)}</div>}{source && <div>Source: {safeString(source)}</div>}</div>;
}

export function MarketInspectionProvider({ children, onViewDetails }: { children: React.ReactNode; onViewDetails: (selection: InspectionSelection) => void }) {
  const { canonicalState, lastValidState, marketContext } = useWorkstationState() as any;
  const [selection, setSelection] = useState<InspectionSelection | null>(null);
  const drawerRef = useRef<HTMLElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const closeInspection = useCallback(() => setSelection(null), []);
  useEffect(() => { const handler = (event: KeyboardEvent) => { if (event.key === "Escape") closeInspection(); }; window.addEventListener("keydown", handler); return () => window.removeEventListener("keydown", handler); }, [closeInspection]);
  const openInspection = useCallback((next: InspectionSelection) => { previousFocus.current = document.activeElement as HTMLElement; setSelection(next); }, []);
  const api = useMemo(() => ({ openInspection, closeInspection }), [openInspection, closeInspection]);
  const model = selection ? inspectionModel(selection, canonicalState ?? lastValidState, marketContext) : null;
  useEffect(() => { if (selection) drawerRef.current?.focus(); else previousFocus.current?.focus(); }, [selection]);
  const deepDiveEligible = selection && model ? supportsDeepDive(selection, model, canonicalState ?? lastValidState) : false;
  return <Context.Provider value={api}>{children}{selection && model && <aside ref={drawerRef} tabIndex={-1} role="dialog" aria-modal="true" aria-label={`${selection.title} inspection`} className="fixed inset-0 z-[70] bg-[#151515] shadow-2xl sm:bottom-0 sm:left-auto sm:right-0 sm:top-14 sm:w-[min(460px,calc(100vw-1rem))] sm:border-l sm:border-[#292929]"><div className="flex h-full flex-col"><div className="flex items-center justify-between border-b border-[#292929] px-4 py-3"><div><h2 className="text-[14px] font-semibold text-[#f1f1f1]">{selection.title}</h2><p className="mt-0.5 text-[10px] text-[#737373]">Canonical inspection · why it matters now</p></div><button aria-label="Close inspection" onClick={closeInspection} className="rounded p-1 text-[#737373] hover:bg-[#202020] hover:text-white"><X size={17} /></button></div><div className="flex-1 overflow-y-auto p-4"><CanonicalSparkline source={model.source} height={90} /><Surface className="mt-3 overflow-hidden"><CompactRows rows={model.rows} /></Surface><Provenance model={model} /></div>{deepDiveEligible && <button onClick={() => { onViewDetails(selection); closeInspection(); }} className="m-4 rounded-md border border-[#343434] bg-[#191919] px-3 py-2 text-left text-[11px] font-medium text-[#d4d4d4] hover:bg-[#202020]">View Details →</button>}</div></aside>}</Context.Provider>;
}

export function MarketDeepDive({ selection, onBack }: { selection: InspectionSelection; onBack: () => void }) {
  const { canonicalState, lastValidState, marketContext } = useWorkstationState() as any;
  const state = canonicalState ?? lastValidState;
  const model = inspectionModel(selection, state, marketContext);
  const today = state?.session_story?.todays_analysis ?? {};
  const extraRows: Array<[string, React.ReactNode]> = selection.domain === "market_context" ? [
    ...safeArray(today.factor_breakdown).map((factor: any) => [safeString(factor.name), `${safeString(factor.direction)} · ${safeString(factor.description)}`] as [string, React.ReactNode]),
    ...safeArray(today.session_evolution).map((phase: any) => [safeString(phase.time_window), safeString(phase.headline)] as [string, React.ReactNode]),
  ] : selection.domain === "membership" ? safeArray(selection.payload?.constituents).map((member: any) => [safeString(member.symbol), `${safeString(member.company_name)} · ${safeString(member.resolution_status)}`] as [string, React.ReactNode]) : [];
  return <div className="space-y-3"><button onClick={onBack} className="text-[11px] text-[#a3a3a3] hover:text-white">← Back to NIFTY</button><Surface className="overflow-hidden"><SectionHeader title={`${selection.title} detail`} detail="Canonical observations, context and provenance" /><div className="p-4"><CanonicalSparkline source={model.source} height={190} /><div className="mt-4 grid gap-3 md:grid-cols-2"><Surface className="overflow-hidden"><SectionHeader title="Available data" /><CompactRows rows={model.rows} /></Surface><Surface className="overflow-hidden"><SectionHeader title={extraRows.length ? "Session evidence" : "Freshness & provenance"} />{extraRows.length ? <CompactRows rows={extraRows} /> : <div className="p-4"><Provenance model={model} /></div>}</Surface></div></div></Surface></div>;
}

export function useMarketInspection() { return useContext(Context); }
