import React from "react";
import { useWorkstationState } from "../context/WorkstationStateContext";
import { formatDate, formatNumber, safeArray, safeString } from "../utils/safeHelpers";

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 text-left">
    <h3 className="text-xs font-bold uppercase text-cyan-300">{title}</h3>
    <div className="mt-3 text-xs leading-relaxed text-slate-300">{children}</div>
  </section>;
}

export function ParticipantPositioningWidget({ compact = false }: { compact?: boolean }) {
  const { canonicalState } = useWorkstationState() as any;
  const derivatives = canonicalState?.macro_intelligence?.institutional_derivatives || {};
  const positioning = derivatives.positioning || {};
  const rows = Object.values(positioning) as any[];
  const selected = compact ? rows.filter(row => row.participant_type === "FII" && ["INDEX_FUTURES", "INDEX_CALLS", "INDEX_PUTS"].includes(row.instrument_category)) : rows;
  const latest = derivatives.open_interest?.trade_date;
  return <Panel title="Derivative Positioning">
    {selected.length ? <>
      <div className="mb-2 font-mono text-[10px] text-slate-500">Latest official session: {formatDate(latest)} · Units: contracts · NSE Clearing</div>
      <div className="space-y-1">{selected.slice(0, compact ? 3 : 12).map((row, index) =>
        <div key={`${row.participant_type}-${row.instrument_category}-${index}`} data-participant-positioning={`${row.participant_type}-${row.instrument_category}`}>
          <span className="font-semibold text-white">{safeString(row.participant_type)} {safeString(row.instrument_category).replaceAll("_", " ")}:</span>{" "}
          {safeString(row.positioning)} · net {Number(row.net_position) >= 0 ? "+" : ""}{formatNumber(row.net_position, 0)} contracts
        </div>)}
      </div>
    </> : <span className="text-amber-400">UNAVAILABLE — no validated participant-wise open-interest records.</span>}
  </Panel>;
}

export function VolatilityContextWidget() {
  const { canonicalState, optionContext } = useWorkstationState() as any;
  const macro = canonicalState?.macro_intelligence || {};
  const vix = macro.india_vix || canonicalState?.market_data?.india_vix_context || {};
  const rate = macro.risk_free_rate || optionContext?.risk_free_rate || {};
  const vixAvailable = ["AVAILABLE", "DEGRADED"].includes(safeString(vix.status).toUpperCase()) && vix.value != null && vix.observation_timestamp;
  const ivAvailable = safeString(optionContext?.iv_status).toUpperCase() === "AVAILABLE" && Number(optionContext?.iv_rows || 0) > 0;
  return <Panel title="Volatility">
    <div className="grid gap-3 sm:grid-cols-2">
      <div data-india-vix-status={vixAvailable ? "available" : "unavailable"}>
        <div className="font-semibold text-white">India VIX</div>
        {vixAvailable ? <>
          <div className="text-lg font-bold text-cyan-300">{formatNumber(vix.value, 2)}</div>
          <div className="font-mono text-[10px] text-slate-500">{safeString(vix.regime)} · {safeString(vix.freshness)} · {safeString(vix.source_symbol)}</div>
          <div className="font-mono text-[10px] text-slate-500">Observed {formatDate(vix.observation_timestamp)}</div>
        </> : <div className="text-amber-400">UNAVAILABLE — {safeString(vix.failure_reason || "no validated observation")}</div>}
      </div>
      <div data-option-iv-status={ivAvailable ? "available" : "unavailable"}>
        <div className="font-semibold text-white">NIFTY Option IV</div>
        {ivAvailable ? <>
          <div>ATM CE {formatNumber(optionContext.atm_ce_iv, 2)}% · ATM PE {formatNumber(optionContext.atm_pe_iv, 2)}%</div>
          <div className="text-lg font-bold text-cyan-300">ATM average {formatNumber(optionContext.atm_iv, 2)}%</div>
          <div className="font-mono text-[10px] text-slate-500">{safeString(rate.tenor)} {formatNumber(rate.rate_pct, 4)}% · {safeString(rate.source)} · {safeNumberRows(optionContext.iv_rows)} IV rows</div>
        </> : <div className="text-amber-400">UNAVAILABLE — {safeString(optionContext?.iv_reason || "no converged contract IV")}</div>}
      </div>
    </div>
  </Panel>;
}

function safeNumberRows(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? String(number) : "0";
}

export function SpecializedDataSummary() {
  const { canonicalState } = useWorkstationState() as any;
  const macro = canonicalState?.macro_intelligence || {};
  const oi = macro.institutional_derivatives?.open_interest || {};
  const volume = macro.institutional_derivatives?.volume || {};
  const contracts = macro.provider_contracts || {};
  const meta = macro.constituent_metadata || {};
  const rows = [
    ["Participant OI", oi ? safeArray(oi.records).length : 0, oi?.trade_date || "UNAVAILABLE"],
    ["Participant Volume", volume ? safeArray(volume.records).length : 0, volume?.trade_date || "UNAVAILABLE"],
    ["NIFTY Reconstitution", meta.reconstitution?.status || "UNAVAILABLE", meta.reconstitution?.review_schedule || "UNAVAILABLE"],
    ["GIFT Nifty", contracts.gift_nifty?.status || "NOT_CONFIGURED", contracts.gift_nifty?.failure_reason || "GENUINE_PROVIDER_NOT_CONFIGURED"],
    ["NIFTY Weights", contracts.nifty_weights?.status || "LICENSE_REQUIRED", contracts.nifty_weights?.failure_reason || "OFFICIAL_NIFTY_WEIGHTS_LICENSE_REQUIRED"],
  ];
  return <Panel title="Official / Specialized Data">
    <div className="space-y-2">{rows.map(([name, value, detail]) => <div key={String(name)} className="border-b border-slate-800 pb-2 last:border-0">
      <div className="font-semibold text-white">{String(name)}: <span className="text-cyan-300">{String(value)}</span></div>
      <div className="font-mono text-[10px] text-slate-500">{String(detail)}</div>
    </div>)}</div>
  </Panel>;
}
