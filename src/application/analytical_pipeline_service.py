from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

from src.application.pipeline_result import AnalyticalPipelineResult, PipelineStageResult
from src.application.runtime_inputs import RuntimeSnapshot
from src.models import MarketContext, OptionContext
from src.models.decision_support import DecisionSupportReport
from src.models.trade_context import SessionContext, ExpiryContext, MarketReadiness, ConfluenceContext
from src.trade_engine.context_builder import TradeContextBuilder
from src.pipeline.market_scoring_pipeline import MarketScoringPipeline
from src.pipeline.opportunity_pipeline import OpportunityPipeline
from src.pipeline.strategy_pipeline import StrategyPipeline
from src.pipeline.trade_planner_pipeline import TradePlannerPipeline
from src.pipeline.confidence_pipeline import ConfidencePipeline
from src.pipeline.risk_pipeline import RiskPipeline


class AnalyticalPipelineService:
    """One transport-neutral deterministic analytical orchestration path."""

    STAGE_ORDER = ("market", "options", "trade_context", "score", "opportunity", "strategy",
                   "scenarios", "confidence", "risk", "decision_support", "explanation", "news")

    @classmethod
    def run_daemon_snapshot(cls, market, options, *, market_state, broker_state, news=None, account=None):
        from src.application.runtime_input_builder import RuntimeInputBuilder
        snapshot = RuntimeInputBuilder.from_daemon(market, options, market_state=market_state,
                                                    broker_state=broker_state, news=news, account=account)
        return snapshot, cls().run(snapshot)

    def run(self, snapshot: RuntimeSnapshot) -> AnalyticalPipelineResult:
        stages: dict[str, PipelineStageResult] = {}
        market = self._market(snapshot, stages)
        options = self._options(snapshot, stages)
        news_status = "ready" if snapshot.news_context.usable else "unavailable"
        stages["news"] = PipelineStageResult(news_status, snapshot.news_context.payload,
                                              source=snapshot.news_context.source,
                                              blockers=[] if news_status == "ready" else ["real news provider"])
        if market is None:
            self._block(stages, "trade_context", "score", "opportunity", "strategy", "scenarios",
                        "confidence", "risk", "decision_support", "explanation",
                        reason="validated NIFTY market context")
            return self._result(snapshot, stages)
        if options is None:
            # Construct synthetic degraded option context from market spot to allow downstream price-action analysis
            expiry_str = market.current_expiry or date.today().isoformat()
            atm_calc = round(market.current_spot / 50.0) * 50 if market.current_spot > 0 else 24000.0
            options = OptionContext(
                current_spot=market.current_spot,
                atm_strike=atm_calc,
                current_weekly_expiry=expiry_str,
                current_monthly_expiry=expiry_str,
                time_to_expiry=1,
                pcr=1.0,
                max_pain=atm_calc,
                call_wall=atm_calc + 200,
                put_wall=atm_calc - 200,
                strike_universe=[],
                option_chain_summary={"chain_length": 0, "status": "DEGRADED_SYNTHETIC"},
            )
            stages["options"] = PipelineStageResult("degraded", self._dict(options), source="degraded_synthesizer", warnings=["option context unavailable; analysis operating in price-action degraded mode"])
        try:
            trade_context = self._trade_context(market, options, snapshot)
            stages["trade_context"] = self._ready(trade_context)
            score = MarketScoringPipeline().run(trade_context); stages["score"] = self._ready(score)
            opportunity = OpportunityPipeline().run(trade_context, score); stages["opportunity"] = self._ready(opportunity)
            strategy = StrategyPipeline().run(trade_context, score, opportunity); stages["strategy"] = self._ready(strategy)
            plan = TradePlannerPipeline().run(strategy, options, opportunity)
            closed = snapshot.market_session.freshness.value == "market_closed"
            option_degraded = stages["options"].status == "degraded"
            scenarios = self._scenarios(plan, market_closed=closed)
            stages["scenarios"] = PipelineStageResult("market_closed" if closed else "ready", scenarios)
            confidence = ConfidencePipeline().run(plan, strategy, opportunity, score)
            stages["confidence"] = PipelineStageResult(
                "degraded" if option_degraded else ("market_closed" if closed else "ready"),
                self._dict(confidence), warnings=["option input is partial or stale"] if option_degraded else [])
            risk = RiskPipeline().run(confidence, plan, trade_context, score); stages["risk"] = self._ready(risk)
            support = self._decision(market, options, score, opportunity, strategy, scenarios, confidence, risk,
                                     market_closed=closed)
            stages["decision_support"] = PipelineStageResult(
                "degraded" if option_degraded else ("market_closed" if closed else "ready"), support.to_dict())
            stages["explanation"] = PipelineStageResult("ready", self._explanation(support))
        except Exception as exc:
            missing = [name for name in self.STAGE_ORDER[2:11] if name not in stages]
            self._block(stages, *missing, reason=f"upstream canonical stage error: {type(exc).__name__}")
            return self._result(snapshot, stages, errors=[str(exc)])
        return self._result(snapshot, stages)

    def _market(self, snapshot, stages):
        item = snapshot.nifty_market
        if not item.usable or item.freshness.value == "stale":
            stages["market"] = PipelineStageResult("blocked", None, item.source,
                                                    item.errors or [item.freshness.value])
            return None
        p = item.payload
        required = ("current_spot", "timestamp", "trading_session", "current_expiry", "market_regime", "trend_direction", "trend_strength")
        missing = [name for name in required if p.get(name) is None]
        if missing:
            stages["market"] = PipelineStageResult("blocked", None, item.source,
                                                    [f"missing market field: {x}" for x in missing])
            return None
        market = MarketContext(**{name: p[name] for name in required},
            support_levels=p.get("support_levels", []), resistance_levels=p.get("resistance_levels", []),
            vwap=p.get("vwap", 0.0), atr=p.get("atr", 0.0), india_vix=p.get("india_vix"),
            volatility_state=p.get("volatility_state", "UNKNOWN"))
        status = "market_closed" if item.freshness.value == "market_closed" else "ready"
        stages["market"] = PipelineStageResult(status, self._dict(market), item.source)
        return market

    def _options(self, snapshot, stages):
        item = snapshot.option_quotes
        if not item.usable:
            status = "unavailable" if item.payload is None else "blocked"
            stages["options"] = PipelineStageResult(status, None, item.source, item.errors or [item.freshness.value])
            return None
        try:
            fields = OptionContext.__dataclass_fields__
            values = {k: item.payload[k] for k in fields if k in item.payload}
            required = [k for k, f in fields.items() if f.default is f.default_factory]
            # Dataclass construction is the final completeness/expiry/strike consistency gate.
            options = OptionContext(**values)
        except (TypeError, KeyError) as exc:
            stages["options"] = PipelineStageResult("blocked", None, item.source, [f"incomplete option context: {exc}"])
            return None
        chain_length = options.option_chain_summary.get("chain_length")
        status = "degraded" if item.freshness.value == "stale" or (chain_length is not None and chain_length < 2) else (
            "market_closed" if item.freshness.value == "market_closed" else "ready")
        stages["options"] = PipelineStageResult(status, self._dict(options), item.source,
                                                 warnings=["partial option chain"] if status == "degraded" else [])
        return options

    @staticmethod
    def _trade_context(market, options, snapshot):
        expiry_text = options.current_weekly_expiry
        try: days = max(0, (date.fromisoformat(expiry_text) - date.today()).days)
        except ValueError: days = max(0, int(options.time_to_expiry))
        closed = snapshot.market_session.payload.get("state", "").upper() in {"CLOSED", "POST_MARKET", "HOLIDAY"}
        session = SessionContext("POST_MARKET" if closed else "MARKET_OPEN", not closed, "CURRENT", False, False, False)
        expiry = ExpiryContext(expiry_text, days, "WEEKLY", days == 0, days == 1, days > 14,
                               "EXPIRY_DAY" if days == 0 else "WEEKLY_EXPIRY")
        confluence = ConfluenceContext(False, False, False, False, False, False, "Calculated by canonical stages")
        readiness = MarketReadiness(True, 50.0, [], not closed, True, True, True)
        return TradeContextBuilder.build(market, options, session, expiry, confluence, readiness,
                                         pipeline_version="phase3")

    @classmethod
    def _scenarios(cls, plan, *, market_closed: bool = False) -> list[dict[str, Any]]:
        scenarios = []
        for candidate in getattr(plan, "accepted_candidates", []):
            raw = cls._dict(candidate)
            scenarios.append({
                "scenario_name": raw.get("strategy_name") or raw.get("candidate_id", "Scenario"),
                "direction": raw.get("direction") or raw.get("option_type", "NEUTRAL"),
                "activation_condition": ("Evaluate at next session" if market_closed else
                                         raw.get("entry_condition", "Await required confirmations")),
                "confirmation_conditions": raw.get("confirmation_conditions", []),
                "missing_confirmations": [],
                "invalidation_condition": raw.get("invalidation_condition") or raw.get("stop_loss"),
                "target_zones": raw.get("targets", []), "risk_classification": "deterministic",
                "scenario_confidence": raw.get("ranking_score"),
                "status": "next_session_planning" if market_closed else "waiting",
            })
        return scenarios

    @staticmethod
    def _decision(market, options, score, opportunity, strategy, scenarios, confidence, risk, *, market_closed=False):
        interpretation = f"{market.market_regime} market with {market.trend_direction} trend"
        return DecisionSupportReport(interpretation, "next_session_planning" if market_closed else ("waiting" if scenarios else "no_qualified_scenario"),
            ["human review", "next-session validation" if market_closed else "scenario confirmation"], [] if scenarios else ["qualified trade scenario"],
            [str(s.get("invalidation_condition")) for s in scenarios if s.get("invalidation_condition")],
            [], [], True)

    @staticmethod
    def _explanation(report):
        return {"summary": report.market_interpretation, "scenario_status": report.current_scenario_status,
                "blocked_dependencies": report.blockers, "warnings": report.warnings,
                "human_decision_required": True, "ai_provider": None}

    @classmethod
    def _ready(cls, value): return PipelineStageResult("ready", cls._dict(value))

    @classmethod
    def _result(cls, snapshot, stages, errors=None):
        ordered = {name: stages[name] for name in cls.STAGE_ORDER}
        return AnalyticalPipelineResult(snapshot.snapshot_id, snapshot.generated_at, ordered, errors=errors or [])

    @staticmethod
    def _block(stages, *names, reason):
        for name in names: stages.setdefault(name, PipelineStageResult("blocked", blockers=[reason]))

    @classmethod
    def _dict(cls, value):
        if is_dataclass(value): value = asdict(value)
        if isinstance(value, Enum): return value.value
        if isinstance(value, dict): return {k: cls._dict(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)): return [cls._dict(v) for v in value]
        return value
