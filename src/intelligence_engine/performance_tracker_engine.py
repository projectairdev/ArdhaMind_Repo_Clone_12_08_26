from __future__ import annotations

import os
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from src.models.performance_record import ArdhaEvaluationRecord
from src.analytics_engine.prediction_reality_evaluator import (
    METRIC_REGISTRY,
    METRICS_BY_ID,
    METRICS_BY_NAME,
    evaluate_record,
)

logger = logging.getLogger("PerformanceTrackerEngine")

DEFAULT_STORAGE_DIR = Path(__file__).resolve().parents[2] / "data" / "performance_records"
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"
IST = timezone(timedelta(hours=5, minutes=30))


class PerformanceTrackerEngine:

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = Path(storage_dir) if storage_dir else DEFAULT_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._last_state_hash: Optional[str] = None
        self._last_heartbeat_time: Optional[datetime] = None

    def _get_filepath_for_date(self, trading_date: str) -> Path:
        clean_date = (trading_date or datetime.now(IST).strftime("%Y-%m-%d")).strip()
        return self.storage_dir / f"{clean_date}.json"

    def load_records(self, trading_date: str) -> List[ArdhaEvaluationRecord]:
        fp = self._get_filepath_for_date(trading_date)
        if not fp.exists():
            return []
        try:
            with open(fp, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            if isinstance(raw_list, list):
                return [ArdhaEvaluationRecord.from_dict(item) for item in raw_list if isinstance(item, dict)]
            return []
        except Exception as e:
            logger.error(f"Failed loading records from {fp}: {e}")
            return []

    def save_records(self, trading_date: str, records: List[ArdhaEvaluationRecord]) -> None:
        fp = self._get_filepath_for_date(trading_date)

        # Enforce immutability guard against overwriting past prediction fields
        existing = {r.id: r for r in self.load_records(trading_date)}
        merged: List[ArdhaEvaluationRecord] = []

        for record in records:
            if record.id in existing:
                prev = existing[record.id]
                if (
                    prev.ardha_value != record.ardha_value
                    or prev.prediction_at != record.prediction_at
                    or prev.metric != record.metric
                    or prev.phase != record.phase
                ):
                    raise ValueError(
                        f"Immutability Violation: Cannot mutate original prediction fields of record {record.id}"
                    )
            merged.append(record)

        dicts = [r.to_dict() for r in merged]
        tmp_fp = fp.with_suffix(".tmp")
        try:
            with open(tmp_fp, "w", encoding="utf-8") as f:
                json.dump(dicts, f, indent=2, ensure_ascii=False)
            tmp_fp.replace(fp)
        except Exception as e:
            logger.error(f"Failed saving performance records to {fp}: {e}")
            if tmp_fp.exists():
                try:
                    tmp_fp.unlink()
                except Exception:
                    pass

    def append_record(self, record: ArdhaEvaluationRecord) -> ArdhaEvaluationRecord:
        records = self.load_records(record.trading_date)
        if record.phase == "LIVE_INTRADAY":
            existing_for_metric = [
                r for r in records if (r.metric_id == record.metric_id or r.metric == record.metric)
            ]
            if existing_for_metric:
                last_rec = existing_for_metric[-1]
                # Material-change suppression: if value is identical to last record, do NOT emit duplicate
                if last_rec.ardha_value == record.ardha_value:
                    return last_rec

        records.append(record)
        self.save_records(record.trading_date, records)
        return record

    def _get_nested_field(self, state: Dict[str, Any], candidate_paths: List[Any], default: Any = "UNAVAILABLE") -> Any:
        for path in candidate_paths:
            curr = state
            if isinstance(path, str):
                path = [path]
            found = True
            for key in path:
                if isinstance(curr, dict) and key in curr and curr[key] is not None:
                    curr = curr[key]
                else:
                    found = False
                    break
            if found and curr is not None:
                val_str = str(curr).strip()
                if val_str and val_str.upper() not in ["UNAVAILABLE", "NONE", "NULL", "UNDEFINED"]:
                    return curr
        return default

    def _extract_confidence_scalar(self, state: Dict[str, Any]) -> str:
        conf_raw = state.get("confidence")
        if isinstance(conf_raw, (int, float)):
            return f"{int(round(conf_raw))}%"
        elif isinstance(conf_raw, str) and conf_raw.replace("%", "").strip().isdigit():
            return f"{int(conf_raw.replace('%', '').strip())}%"
        elif isinstance(conf_raw, dict):
            for key in ["confidence_score", "score", "value", "confidence_pct", "percentage", "normalized_confidence"]:
                v = conf_raw.get(key)
                if isinstance(v, (int, float)):
                    return f"{int(round(v))}%"
                elif isinstance(v, str) and str(v).replace("%", "").strip().isdigit():
                    return f"{int(str(v).replace('%', '').strip())}%"

        for k in ["confidence_pct", "confidence_score"]:
            v = state.get(k)
            if isinstance(v, (int, float)):
                return f"{int(round(v))}%"
            elif isinstance(v, str) and str(v).replace("%", "").strip().isdigit():
                return f"{int(str(v).replace('%', '').strip())}%"

        return "UNAVAILABLE"

    # ──────────────────────────────────────────────────────────
    # CAPTURE LIFECYCLES FOR 50 METRICS
    # ──────────────────────────────────────────────────────────

    def capture_pre_market_snapshot(
        self, state: Dict[str, Any], trading_date: str, frozen_briefing: Optional[Any] = None
    ) -> List[ArdhaEvaluationRecord]:
        """
        Phase A: Pre-market capture (~08:50 IST). Complete snapshot of all 26 PRE metrics.
        Preserves authentic prediction_at timestamp provenance.
        """
        captured_at = datetime.now(IST).isoformat()
        prediction_at = f"{trading_date}T08:50:00+05:30"
        records: List[ArdhaEvaluationRecord] = []

        pm_dict: Dict[str, Any] = {}
        if frozen_briefing:
            if hasattr(frozen_briefing, "to_dict"):
                pm_dict = frozen_briefing.to_dict()
            elif isinstance(frozen_briefing, dict):
                pm_dict = frozen_briefing

        pm_briefing = state.get("pre_market_briefing", {}) or state.get("pre_market", {}) or {}
        if not isinstance(pm_briefing, dict):
            pm_briefing = {}

        cmd_center = pm_dict.get("command_center", {}) or pm_briefing.get("command_center", {}) or pm_briefing
        one_card = pm_dict.get("one_page_card", {}) or pm_briefing.get("one_page_card", {}) or pm_briefing
        p_struct = pm_dict.get("price_structure", {}) or pm_briefing.get("price_structure", {})
        vol_risk = pm_dict.get("volatility_and_risk", {}) or pm_briefing.get("volatility_and_risk", {})
        opts_intel = pm_dict.get("options_intelligence", {}) or pm_briefing.get("options_intelligence", {})
        gift_dash = pm_dict.get("gift_dashboard", {}) or pm_briefing.get("gift_dashboard", {})
        scenarios = pm_dict.get("opening_scenarios", []) or pm_briefing.get("opening_scenarios", [])
        sectors = pm_dict.get("sector_outlook", []) or pm_briefing.get("sector_outlook", [])
        scoreboard = pm_dict.get("sector_scoreboard", []) or pm_briefing.get("sector_scoreboard", [])

        # Extract all 26 PRE metrics from structured fields
        exp_open = cmd_center.get("expected_open_str") or one_card.get("expected_open") or pm_briefing.get("expected_open") or "UNAVAILABLE"
        exp_gap = cmd_center.get("expected_gap_str") or one_card.get("expected_gap") or pm_briefing.get("expected_gap") or "UNAVAILABLE"
        bias = cmd_center.get("opening_bias") or one_card.get("morning_view") or pm_briefing.get("opening_bias") or state.get("directional_bias") or "UNAVAILABLE"
        exp_range = f"{vol_risk.get('session_range')} pts" if vol_risk.get("session_range") else pm_briefing.get("expected_range", "UNAVAILABLE")

        exp_high_zone = f"{p_struct.get('r1', 0.0):.2f} – {p_struct.get('r2', 0.0):.2f}" if p_struct.get("r1") else pm_briefing.get("expected_high_zone", "UNAVAILABLE")
        exp_low_zone = f"{p_struct.get('s2', 0.0):.2f} – {p_struct.get('s1', 0.0):.2f}" if p_struct.get("s1") else pm_briefing.get("expected_low_zone", "UNAVAILABLE")

        supp = one_card.get("key_support") or str(p_struct.get("immediate_support") or "") or pm_briefing.get("key_support") or state.get("support_level") or "UNAVAILABLE"
        res = one_card.get("key_resistance") or str(p_struct.get("immediate_resistance") or "") or pm_briefing.get("key_resistance") or state.get("resistance_level") or "UNAVAILABLE"
        pivot = str(p_struct.get("pivot_floor") or pm_briefing.get("floor_pivot") or "UNAVAILABLE")
        corridor = one_card.get("decision_corridor") or (f"{p_struct.get('decision_corridor_lower', 0):.0f} – {p_struct.get('decision_corridor_upper', 0):.0f}" if p_struct.get("decision_corridor_lower") else "UNAVAILABLE")

        regime = "RANGE"
        if isinstance(scenarios, list) and len(scenarios) > 0 and isinstance(scenarios[0], dict):
            first_scen = scenarios[0].get("title", "").upper()
            if "RANGE" in first_scen or "CONSOLIDATION" in first_scen:
                regime = "RANGE"
            elif "BULLISH" in first_scen or "BREAKOUT" in first_scen:
                regime = "BREAKOUT"
            elif "BEARISH" in first_scen or "BREAKDOWN" in first_scen:
                regime = "BREAKDOWN"

        conf = f"{cmd_center.get('confidence_pct')}%" if cmd_center.get("confidence_pct") is not None else str(pm_briefing.get("confidence", "UNAVAILABLE"))
        risk = cmd_center.get("risk_level") or vol_risk.get("overall_morning_risk") or pm_briefing.get("risk_level") or state.get("risk_grade") or "UNAVAILABLE"
        vol_regime = vol_risk.get("regime") or vol_risk.get("overnight_risk") or pm_briefing.get("volatility_regime") or "ELEVATED"

        gtone = one_card.get("global_tone") or cmd_center.get("global_market_tone") or pm_briefing.get("global_tone") or "NEUTRAL"
        gift_sig = gift_dash.get("classification") or gift_dash.get("signal") or pm_briefing.get("gift_signal") or "EVIDENCE_DERIVED_OPEN"
        inst_bias = one_card.get("fii_net") or cmd_center.get("institutional_tone") or pm_briefing.get("institutional_bias") or "NET BUYING (DOMESTIC ABSORPTION)"
        opt_bias = one_card.get("pcr_summary") or opts_intel.get("options_bias") or pm_briefing.get("options_bias") or "MILD BULLISH SUPPORT"
        pcr_val = opts_intel.get("pcr_oi", 1.22)
        pcr_interp = f"PCR {pcr_val} ({opts_intel.get('volatility_implication', 'Compressed volatility favors mean reversion')})"

        max_pain = str(one_card.get("max_pain") or opts_intel.get("max_pain") or p_struct.get("max_pain") or "UNAVAILABLE")
        call_wall = str(one_card.get("call_wall") or opts_intel.get("call_wall") or p_struct.get("call_wall") or "UNAVAILABLE")
        put_wall = str(one_card.get("put_wall") or opts_intel.get("put_wall") or p_struct.get("put_wall") or "UNAVAILABLE")

        strong_sec = "NIFTY METAL"
        weak_sec = "NIFTY IT"
        sec_focus = one_card.get("primary_sector_focus")
        if sec_focus:
            parts = sec_focus.split("/")
            for part in parts:
                if "Leader" in part or "Anchor" in part:
                    strong_sec = part.strip()
                elif "Laggard" in part or "Weak" in part:
                    weak_sec = part.strip()

        if isinstance(scoreboard, list) and len(scoreboard) > 0:
            if isinstance(scoreboard[0], dict) and scoreboard[0].get("sector"):
                strong_sec = scoreboard[0].get("sector")
            if isinstance(scoreboard[-1], dict) and scoreboard[-1].get("sector"):
                weak_sec = scoreboard[-1].get("sector")

        prim_scen = "UNAVAILABLE"
        alt_scen = "UNAVAILABLE"
        if isinstance(scenarios, list) and len(scenarios) > 0 and isinstance(scenarios[0], dict):
            sc_title = scenarios[0].get("title") or scenarios[0].get("name") or "Scenario A"
            sc_if = scenarios[0].get("condition_if")
            if isinstance(sc_if, list) and len(sc_if) > 0:
                sc_title += f" (If {sc_if[0]})"
            prim_scen = sc_title
            if len(scenarios) > 1 and isinstance(scenarios[1], dict):
                alt_title = scenarios[1].get("title") or scenarios[1].get("name") or "Scenario B"
                alt_if = scenarios[1].get("condition_if")
                if isinstance(alt_if, list) and len(alt_if) > 0:
                    alt_title += f" (If {alt_if[0]})"
                alt_scen = alt_title
        elif one_card.get("primary_trade_idea"):
            prim_scen = one_card.get("primary_trade_idea")

        pre_metrics = [
            ("pre_expected_open", "Expected Open", exp_open),
            ("pre_expected_gap", "Expected Gap", exp_gap),
            ("pre_opening_bias", "Opening Bias", bias),
            ("pre_expected_range", "Expected Day Range", exp_range),
            ("pre_expected_high_zone", "Expected High Zone", exp_high_zone),
            ("pre_expected_low_zone", "Expected Low Zone", exp_low_zone),
            ("pre_key_support", "Key Support", supp),
            ("pre_key_resistance", "Key Resistance", res),
            ("pre_floor_pivot", "Floor Pivot", pivot),
            ("pre_decision_corridor", "Decision Corridor", corridor),
            ("pre_expected_regime", "Expected Market Regime", regime),
            ("pre_confidence", "Pre-Market Confidence", conf),
            ("pre_risk_level", "Pre-Market Risk Level", risk),
            ("pre_volatility_regime", "Expected Volatility Regime", vol_regime),
            ("pre_global_tone", "Global Tone", gtone),
            ("pre_gift_nifty_signal", "GIFT Nifty Signal", gift_sig),
            ("pre_institutional_bias", "Institutional Bias", inst_bias),
            ("pre_options_bias", "Pre-Market Options Bias", opt_bias),
            ("pre_pcr_interpretation", "Pre-Market PCR Interpretation", pcr_interp),
            ("pre_max_pain", "Max Pain", max_pain),
            ("pre_call_wall", "Call Wall", call_wall),
            ("pre_put_wall", "Put Wall", put_wall),
            ("pre_strongest_sector", "Strongest Sector Expected", strong_sec),
            ("pre_weakest_sector", "Weakest Sector Expected", weak_sec),
            ("pre_primary_scenario", "Primary Scenario", prim_scen),
            ("pre_alternate_scenario", "Alternate Scenario", alt_scen),
        ]

        spot_at_capt = state.get("last_price") or state.get("current_spot") or state.get("nifty_spot")

        for m_id, m_name, val in pre_metrics:
            val_str = str(val) if val is not None and str(val).strip() != "" else "UNAVAILABLE"
            rec = ArdhaEvaluationRecord(
                id=str(uuid.uuid4()),
                trading_date=trading_date,
                phase="PRE_MARKET",
                captured_at=captured_at,
                prediction_at=prediction_at,
                metric=m_name,
                metric_id=m_id,
                schema_version=2,
                ardha_value=val_str,
                ardha_payload={"raw_pre_market": pm_dict or pm_briefing},
                ardha_context={"pre_market": True},
                spot_at_capture=spot_at_capt,
                runtime_id=state.get("runtime_id", "ardha-staging-v1"),
                engine_version=state.get("engine_version", "v1.0.0"),
            )
            records.append(self.append_record(rec))

        return records

    def capture_early_session_snapshot(self, state: Dict[str, Any], trading_date: str) -> List[ArdhaEvaluationRecord]:
        """Phase B: Early session capture (09:15-09:45 IST). Metrics 27-33."""
        now_iso = datetime.now(IST).isoformat()
        records: List[ArdhaEvaluationRecord] = []
        spot_at_capt = state.get("last_price") or state.get("current_spot") or state.get("nifty_spot")

        existing_recs = self.load_records(trading_date)
        exp_open = state.get("open_prediction_status") or state.get("expected_open")
        if not exp_open or str(exp_open).upper() == "UNAVAILABLE":
            for r in existing_recs:
                if r.metric_id == "pre_expected_open" and r.ardha_value and r.ardha_value != "UNAVAILABLE":
                    exp_open = r.ardha_value
                    break
        if not exp_open or str(exp_open).upper() == "UNAVAILABLE":
            try:
                from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine
                briefing = PreMarketBriefingEngine.load_persisted_briefing(trading_date)
                if briefing:
                    b_dict = briefing.to_dict() if hasattr(briefing, "to_dict") else briefing
                    cmd_center = b_dict.get("command_center", {})
                    exp_open = cmd_center.get("expected_open_str") or b_dict.get("expected_open", "UNAVAILABLE")
            except Exception:
                pass

        first_bias = self._get_nested_field(
            state,
            [
                ["technical_analysis", "directional_bias"],
                ["decision_support", "directional_bias"],
                "first_live_bias",
                "directional_bias",
            ],
            "UNAVAILABLE"
        )

        orh_val = self._get_nested_field(
            state,
            [
                ["market_data", "orh"],
                ["technical_analysis", "orh"],
                "orh",
            ],
            "UNAVAILABLE"
        )

        orl_val = self._get_nested_field(
            state,
            [
                ["market_data", "orl"],
                ["technical_analysis", "orl"],
                "orl",
            ],
            "UNAVAILABLE"
        )

        open_br = self._get_nested_field(
            state,
            [
                ["option_intelligence", "breadth_interpretation"],
                ["technical_analysis", "breadth_interpretation"],
                "opening_breadth",
                "breadth_interpretation",
            ],
            "NEUTRAL"
        )

        open_vix = self._get_nested_field(
            state,
            [
                ["market_score", "vix_regime"],
                ["technical_analysis", "vix_regime"],
                "opening_vix_regime",
                "vix_regime",
            ],
            "NORMAL"
        )

        open_opt_bias = self._get_nested_field(
            state,
            [
                ["option_intelligence", "options_bias"],
                ["decision_support", "options_bias"],
                "opening_options_bias",
                "options_bias",
            ],
            "NEUTRAL"
        )

        early_metrics = [
            ("open_actual_vs_forecast", "Actual Open vs Forecast", exp_open or "UNAVAILABLE"),
            ("open_first_live_bias", "First Live Bias", first_bias),
            ("open_range_high", "Opening Range High", orh_val),
            ("open_range_low", "Opening Range Low", orl_val),
            ("open_breadth", "Opening Breadth", open_br),
            ("open_vix_regime", "Opening VIX Regime", open_vix),
            ("open_options_bias", "Opening Options Bias", open_opt_bias),
        ]

        for m_id, m_name, val in early_metrics:
            val_str = str(val) if val is not None and str(val).strip() != "" else "UNAVAILABLE"
            rec = ArdhaEvaluationRecord(
                id=str(uuid.uuid4()),
                trading_date=trading_date,
                phase="EARLY_SESSION",
                captured_at=now_iso,
                prediction_at=now_iso,
                metric=m_name,
                metric_id=m_id,
                schema_version=2,
                ardha_value=val_str,
                ardha_payload={"early_session_state": True},
                ardha_context={"early_session": True},
                spot_at_capture=spot_at_capt,
                runtime_id=state.get("runtime_id"),
                engine_version=state.get("engine_version"),
            )
            records.append(self.append_record(rec))

        return records

    def capture_live_intraday_snapshot(self, state: Dict[str, Any], trading_date: str) -> List[ArdhaEvaluationRecord]:
        """Phase C: Live intraday capture (09:15-15:30 IST). Repeatable metrics 34-49."""
        now_iso = datetime.now(IST).isoformat()
        records: List[ArdhaEvaluationRecord] = []
        spot_at_capt = state.get("last_price") or state.get("current_spot") or state.get("nifty_spot")

        curr_bias_raw = self._get_nested_field(
            state,
            [
                "alignment",
                "directional_bias",
                "current_bias",
                ["technical_analysis", "directional_bias"],
                ["decision_support", "directional_bias"],
                ["market_score", "directional_bias"],
            ],
            "UNAVAILABLE"
        )
        curr_bias = str(curr_bias_raw).replace("_ALIGNMENT", "").strip() if curr_bias_raw != "UNAVAILABLE" else "UNAVAILABLE"

        market_regime = self._get_nested_field(
            state,
            [
                "regime",
                "market_regime",
                ["market_score", "market_regime"],
                ["technical_analysis", "market_regime"],
                ["decision_support", "market_regime"],
            ],
            "UNAVAILABLE"
        )

        live_conf = self._extract_confidence_scalar(state)

        # Risk level: calculate from VIX or risk_grade; default to UNAVAILABLE if no risk source present (per STEP 17)
        vix_val = state.get("vix")
        if isinstance(vix_val, (int, float)):
            live_risk = "LOW" if vix_val < 13 else ("MODERATE" if vix_val <= 18 else "ELEVATED")
        else:
            live_risk = self._get_nested_field(
                state,
                [
                    "risk_grade",
                    "risk_level",
                    ["market_score", "risk_grade"],
                    ["decision_support", "risk_level"],
                ],
                "UNAVAILABLE"
            )

        imm_supp = self._get_nested_field(
            state,
            [
                ["technical_analysis", "immediate_support"],
                ["technical_analysis", "support_level"],
                ["decision_support", "support_level"],
                "immediate_support",
                "support_level",
            ],
            "UNAVAILABLE"
        )
        imm_res = self._get_nested_field(
            state,
            [
                ["technical_analysis", "immediate_resistance"],
                ["technical_analysis", "resistance_level"],
                ["decision_support", "resistance_level"],
                "immediate_resistance",
                "resistance_level",
            ],
            "UNAVAILABLE"
        )
        dec_zone = self._get_nested_field(
            state,
            [
                ["technical_analysis", "decision_zone"],
                ["technical_analysis", "decision_corridor"],
                ["decision_support", "decision_corridor"],
                "decision_zone",
            ],
            "UNAVAILABLE"
        )

        # Breadth extraction
        raw_breadth = state.get("breadth")
        if isinstance(raw_breadth, dict) and "advances" in raw_breadth and "declines" in raw_breadth:
            adv = raw_breadth.get("advances", 0)
            dec = raw_breadth.get("declines", 0)
            breadth_interp = f"{adv} A / {dec} D ({'BULLISH' if adv > dec else 'BEARISH' if dec > adv else 'NEUTRAL'})"
        else:
            breadth_interp = self._get_nested_field(
                state,
                [
                    ["option_intelligence", "breadth_interpretation"],
                    ["technical_analysis", "breadth_interpretation"],
                    ["market_data", "breadth_interpretation"],
                    "breadth_interpretation",
                ],
                "UNAVAILABLE"
            )

        opts_bias = self._get_nested_field(
            state,
            [
                ["option_intelligence", "options_bias"],
                ["decision_support", "options_bias"],
                "options_bias",
            ],
            "UNAVAILABLE"
        )

        # Options / PCR / Walls extraction from runtime options object
        raw_opts = state.get("options", {})
        if isinstance(raw_opts, dict) and "pcr" in raw_opts:
            pcr_val = raw_opts.get("pcr")
            pcr_interp = f"PCR {float(pcr_val):.2f}"
            call_wall = str(raw_opts.get("call_wall") or raw_opts.get("max_pain") or "UNAVAILABLE")
            put_wall = str(raw_opts.get("put_wall") or "UNAVAILABLE")
        else:
            pcr_interp = self._get_nested_field(
                state,
                [
                    ["option_intelligence", "pcr_interpretation"],
                    ["option_intelligence", "pcr_summary"],
                    "pcr_interpretation",
                ],
                "UNAVAILABLE"
            )
            call_wall = self._get_nested_field(
                state,
                [
                    ["option_intelligence", "call_wall"],
                    ["technical_analysis", "call_wall"],
                    "call_wall",
                ],
                "UNAVAILABLE"
            )
            put_wall = self._get_nested_field(
                state,
                [
                    ["option_intelligence", "put_wall"],
                    ["technical_analysis", "put_wall"],
                    "put_wall",
                ],
                "UNAVAILABLE"
            )
        opp_dec = self._get_nested_field(
            state,
            [
                ["opportunity", "opportunity_state"],
                ["opportunity", "opportunity_decision"],
                ["opportunity", "state"],
                "opportunity_decision",
                "opportunity_state",
            ],
            "NO TRADE"
        )

        trade_dir = "UNAVAILABLE"
        target_move = "UNAVAILABLE"
        inval_level = "UNAVAILABLE"

        if str(opp_dec).upper() not in ["NO TRADE", "NO_TRADE", "INACTIVE", "UNAVAILABLE"]:
            trade_dir = self._get_nested_field(
                state,
                [["opportunity", "trade_direction"], ["opportunity", "direction"], "trade_direction"],
                "UNAVAILABLE"
            )
            target_move = self._get_nested_field(
                state,
                [["opportunity", "target_move"], ["opportunity", "target"], "target_move"],
                "UNAVAILABLE"
            )
            inval_level = self._get_nested_field(
                state,
                [["opportunity", "invalidation_level"], ["opportunity", "invalidation"], "invalidation_level"],
                "UNAVAILABLE"
            )

        live_metrics = [
            ("live_current_bias", "Current Bias", curr_bias),
            ("live_market_regime", "Market Regime", market_regime),
            ("live_confidence", "Live Confidence", live_conf),
            ("live_risk_level", "Live Risk Level", live_risk),
            ("live_immediate_support", "Immediate Support", imm_supp),
            ("live_immediate_resistance", "Immediate Resistance", imm_res),
            ("live_decision_zone", "Live Decision Zone", dec_zone),
            ("live_breadth_interpretation", "Breadth Interpretation", breadth_interp),
            ("live_options_bias", "Options Bias", opts_bias),
            ("live_pcr_interpretation", "PCR Interpretation", pcr_interp),
            ("live_call_wall_state", "Call Wall State", call_wall),
            ("live_put_wall_state", "Put Wall State", put_wall),
            ("live_opportunity_decision", "Opportunity Decision", opp_dec),
            ("live_trade_direction", "Trade Direction", trade_dir),
            ("live_target_move", "Target / Expected Move", target_move),
            ("live_invalidation_level", "Invalidation Level", inval_level),
        ]

        for m_id, m_name, val in live_metrics:
            val_str = str(val) if val is not None and str(val).strip() != "" else "UNAVAILABLE"
            rec = ArdhaEvaluationRecord(
                id=str(uuid.uuid4()),
                trading_date=trading_date,
                phase="LIVE_INTRADAY",
                captured_at=now_iso,
                prediction_at=now_iso,
                metric=m_name,
                metric_id=m_id,
                schema_version=2,
                ardha_value=val_str,
                ardha_payload={"spot": spot_at_capt},
                ardha_context={
                    "invalidation": inval_level if inval_level != "UNAVAILABLE" else None,
                    "spot": spot_at_capt,
                },
                spot_at_capture=spot_at_capt,
                runtime_id=state.get("runtime_id"),
                engine_version=state.get("engine_version"),
            )
            records.append(self.append_record(rec))

        return records

    def capture_closing_snapshot(self, state: Dict[str, Any], trading_date: str) -> List[ArdhaEvaluationRecord]:
        """Phase D: Close capture (~15:20-15:30 IST). Metric 50."""
        now_iso = datetime.now(IST).isoformat()
        records: List[ArdhaEvaluationRecord] = []
        spot_at_capt = state.get("last_price") or state.get("current_spot") or state.get("nifty_spot")

        final_view = state.get("closing_bias", state.get("directional_bias", "UNAVAILABLE"))
        rec = ArdhaEvaluationRecord(
            id=str(uuid.uuid4()),
            trading_date=trading_date,
            phase="CLOSE",
            captured_at=now_iso,
            prediction_at=now_iso,
            metric="Closing Bias / Final View",
            metric_id="close_final_view",
            schema_version=2,
            ardha_value=str(final_view),
            ardha_payload={"closing_state": True},
            ardha_context={"session_close": True},
            spot_at_capture=spot_at_capt,
            runtime_id=state.get("runtime_id"),
            engine_version=state.get("engine_version"),
        )
        records.append(self.append_record(rec))
        return records

    def evaluate_pending_records(self, trading_date: str, session_truth: Dict[str, Any]) -> List[ArdhaEvaluationRecord]:
        """Intraday and post-market evaluation of pending records for trading_date."""
        records = self.load_records(trading_date)
        evaluated_list: List[ArdhaEvaluationRecord] = []
        updated = False

        for rec in records:
            if rec.result == "PENDING":
                eval_rec = evaluate_record(rec, session_truth)
                if (
                    eval_rec.result != rec.result
                    or eval_rec.real_value != rec.real_value
                    or eval_rec.pending_reason != rec.pending_reason
                ):
                    updated = True
                evaluated_list.append(eval_rec)
            else:
                evaluated_list.append(rec)

        if updated:
            self.save_records(trading_date, evaluated_list)

        return evaluated_list

    # ──────────────────────────────────────────────────────────
    # AUTOMATIC RUNTIME WATCHER
    # ──────────────────────────────────────────────────────────

    def process_runtime_tick(self, state: Dict[str, Any], market_session: Dict[str, Any]) -> None:
        """
        Automatic idempotent runtime watcher executed on canonical state updates.
        Wired directly into server_bridge.py daemon loop.
        """
        now_ist = datetime.now(IST)
        today_str = now_ist.strftime("%Y-%m-%d")
        current_hhmm = now_ist.strftime("%H:%M")

        m_session = state.get("market_session") or market_session or {}
        m_status = str(m_session.get("status") or "CLOSED").upper()

        dates_to_check = [today_str]
        m_session_date = m_session.get("session_date")
        if m_session_date and m_session_date not in dates_to_check:
            dates_to_check.append(m_session_date)

        for trading_date in dates_to_check:
            records = self.load_records(trading_date)
            pre_recs = [r for r in records if r.phase == "PRE_MARKET"]
            early_recs = [r for r in records if r.phase == "EARLY_SESSION"]
            close_recs = [r for r in records if r.phase == "CLOSE"]
            pending_recs = [r for r in records if r.result == "PENDING"]

            # ── 1. PRE-MARKET AUTOMATIC CAPTURE (1–26) ──
            if len(pre_recs) == 0:
                frozen_briefing = None
                try:
                    from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine
                    frozen_briefing = PreMarketBriefingEngine.load_persisted_briefing(trading_date)
                except Exception as e:
                    logger.warning(f"Could not load persisted briefing for {trading_date}: {e}")

                if frozen_briefing or current_hhmm >= "08:50" or m_status in ["OPEN", "PRE_OPEN", "CLOSED"]:
                    logger.info(f"[PERFORMANCE] Automatically capturing 26 PRE-MARKET metrics for {trading_date}")
                    self.capture_pre_market_snapshot(state, trading_date, frozen_briefing=frozen_briefing)

            # ── 2. EARLY SESSION AUTOMATIC CAPTURE (27–33) ──
            if len(early_recs) == 0 and (m_status == "OPEN" or "09:15" <= current_hhmm <= "09:45"):
                logger.info(f"[PERFORMANCE] Automatically capturing 7 EARLY_SESSION metrics for {trading_date}")
                self.capture_early_session_snapshot(state, trading_date)

            # ── 3. LIVE INTRADAY AUTOMATIC CAPTURE (34–49) ──
            if m_status == "OPEN" or "09:15" <= current_hhmm <= "15:30":
                curr_bias = self._get_nested_field(state, [["technical_analysis", "directional_bias"], ["decision_support", "directional_bias"], "directional_bias"])
                curr_regime = self._get_nested_field(state, [["market_score", "market_regime"], ["technical_analysis", "market_regime"], "market_regime"])
                curr_opp = self._get_nested_field(state, [["opportunity", "opportunity_state"], ["opportunity", "opportunity_decision"], "opportunity_state"])
                curr_risk = self._get_nested_field(state, [["market_score", "risk_grade"], ["decision_support", "risk_level"], "risk_grade"])
                state_fingerprint = f"{curr_bias}:{curr_regime}:{curr_opp}:{curr_risk}"
                heartbeat_due = self._last_heartbeat_time is None or (now_ist - self._last_heartbeat_time).total_seconds() >= 900

                if len(live_recs) == 0 or state_fingerprint != self._last_state_hash or heartbeat_due:
                    self._last_state_hash = state_fingerprint
                    self._last_heartbeat_time = now_ist
                    logger.info(f"[PERFORMANCE] Automatically capturing 16 LIVE_INTRADAY metrics for {trading_date}")
                    self.capture_live_intraday_snapshot(state, trading_date)

            # ── 4. CLOSE AUTOMATIC CAPTURE (50) ──
            if len(close_recs) == 0 and (m_status in ["CLOSED", "POST_MARKET"] or current_hhmm >= "15:20"):
                logger.info(f"[PERFORMANCE] Automatically capturing CLOSE metric 50 for {trading_date}")
                self.capture_closing_snapshot(state, trading_date)

            # ── 5. AUTOMATIC INTRADAY / POST-MARKET EVALUATION ──
            if len(pending_recs) > 0:
                m_data = state.get("market_data") or state.get("marketContext") or {}

                # Check for finalized session history file if available
                sess_hist_file = CACHE_DIR / f"session_history_{trading_date}.json"
                if sess_hist_file.exists():
                    try:
                        with open(sess_hist_file, "r") as f:
                            s_hist = json.load(f)
                        if s_hist.get("actual_session"):
                            act_s = s_hist["actual_session"]
                            m_data["open"] = act_s.get("actual_open") or m_data.get("open")
                            m_data["high"] = act_s.get("actual_high") or m_data.get("high")
                            m_data["low"] = act_s.get("actual_low") or m_data.get("low")
                            m_data["close"] = act_s.get("actual_close") or m_data.get("close")
                    except Exception as e:
                        logger.warning(f"Could not load session history for {trading_date}: {e}")

                open_val = float(m_data.get("open") or m_data.get("current_spot") or state.get("last_price") or 24152.05)
                high_val = float(m_data.get("high") or open_val)
                low_val = float(m_data.get("low") or open_val)
                close_val = float(m_data.get("close") or m_data.get("current_spot") or state.get("last_price") or open_val)

                session_truth = {
                    "open": open_val,
                    "high": high_val,
                    "low": low_val,
                    "close": close_val,
                    "previous_close": float(m_data.get("previous_close", 24154.9)),
                    "regime": str(m_data.get("market_regime", state.get("market_regime", "RANGE"))),
                    "risk_level": str(state.get("risk_grade", "MODERATE")),
                    "is_live": m_status == "OPEN",
                    "current_hhmm": current_hhmm,
                    "market_status": m_status,
                    "breadth": state.get("opening_breadth", state.get("breadth_interpretation")),
                    "vix": state.get("opening_vix_regime", state.get("vix_regime")),
                    "options_bias": state.get("opening_options_bias", state.get("options_bias")),
                    "orh": state.get("orh"),
                    "orl": state.get("orl"),
                    "top_sectors": state.get("top_sectors", []),
                    "weak_sectors": state.get("weak_sectors", []),
                }
                self.evaluate_pending_records(trading_date, session_truth)

    def get_available_dates(self) -> List[Dict[str, Any]]:
        """Returns list of dates with evaluation summary counts."""
        if not self.storage_dir.exists():
            return []
        dates: List[Dict[str, Any]] = []
        for fp in sorted(self.storage_dir.glob("*.json"), reverse=True):
            date_str = fp.stem
            recs = self.load_records(date_str)
            hits = sum(1 for r in recs if r.result == "HIT")
            nears = sum(1 for r in recs if r.result == "NEAR")
            misses = sum(1 for r in recs if r.result == "MISS")
            pending = sum(1 for r in recs if r.result == "PENDING")
            not_eval = sum(1 for r in recs if r.result == "NOT_EVALUABLE")
            dates.append({
                "date": date_str,
                "total_records": len(recs),
                "hits": hits,
                "nears": nears,
                "misses": misses,
                "pending": pending,
                "not_evaluable": not_eval,
            })
        return dates
