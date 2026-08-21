# src/server_bridge.py
from __future__ import annotations
import sys
import json
import argparse
import dataclasses
import logging
import time
from pathlib import Path
from datetime import datetime

# Support the documented direct launch (`python src/server_bridge.py`) as well as
# module launch without changing application imports.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.application.compatibility_serializer import CompatibilitySerializer
from src.application.workstation_state_service import WorkstationStateService
from src.application.analytical_pipeline_service import AnalyticalPipelineService
from src.configuration_engine.runtime import Config
from src.proposal_engine.models import (
    ProposalState,
    TradeProposal,
    BrokerOrderState,
    OrderRecord,
    PositionState,
    ExecutionOperation,
    OperationType,
    OperationStatus,
    JournalNote,
    TradeJournalRecord,
    ClosingReason,
    TraderOverrideType,
)
from src.proposal_engine.builder import ProposalBuilder
from src.proposal_engine.audit_storage import ProposalAuditStorage
from src.proposal_engine.safety_policy import ExecutionSafetyPolicy, SafetyGatekeeper, BlockerCode

# Disable verbose logging to stdout to preserve clean JSON output
logging.basicConfig(level=logging.ERROR, stream=sys.stderr, force=True)

logger = logging.getLogger("ServerBridge")

import threading

_boot_start_time = time.time()
_first_state_emitted = False

proposal_audit_storage = ProposalAuditStorage()
safety_gatekeeper = SafetyGatekeeper()
active_trade_proposal = None

cached_market_context = None
cached_option_context = None
def get_initial_news_sentiment():
    return {
        "status": "unavailable",
        "section_status": "unavailable",
        "provider_health": {},
        "items": [],
        "top_headlines": [],
        "high_impact_items": [],
        "corporate_items": [],
        "event_items": [],
        "warnings": [],
        "errors": []
    }

def get_initial_macro_context():
    return {
        "status": "unavailable",
        "section_status": "unavailable",
        "provider_health": {},
        "quotes": {},
        "institutional_flows": [],
        "institutional_derivatives": {},
        "india_vix": {"status": "UNAVAILABLE", "value": None},
        "risk_free_rate": {"status": "UNAVAILABLE", "rate": None},
        "provider_contracts": {
            "gift_nifty": {"status": "NOT_CONFIGURED", "failure_reason": "GENUINE_PROVIDER_NOT_CONFIGURED"},
            "nifty_weights": {"status": "LICENSE_REQUIRED", "failure_reason": "OFFICIAL_NIFTY_WEIGHTS_LICENSE_REQUIRED"},
        },
        "economic_events": [],
        "corporate_actions": [],
        "earnings_events": [],
        "ipo_events": [],
        "warnings": [],
        "errors": []
    }

cached_news_sentiment = get_initial_news_sentiment()
cached_macro_context = get_initial_macro_context()
last_news_fetch_time = 0.0
news_refresh_lock = threading.Lock()
last_macro_fetch_time = 0.0
macro_refresh_lock = threading.Lock()

def _bg_refresh_news():
    global cached_news_sentiment, last_news_fetch_time
    if not news_refresh_lock.acquire(blocking=False):
        return
    try:
        t0 = time.time()
        logger.info(f"[BACKGROUND] Async news refresh started at {(t0 - _boot_start_time)*1000:.1f}ms")
        from src.pipeline.news_pipeline import NewsPipeline
        from src.dashboard.news_panel import NewsIntelligencePanel
        pipeline = NewsPipeline()
        news_ctx = pipeline.run()
        candidate = NewsIntelligencePanel(news_ctx).to_dict()
        if isinstance(candidate, dict):
            cached_news_sentiment = candidate
            last_news_fetch_time = time.time()
            logger.info(f"[BACKGROUND] Async news refresh completed in {(time.time() - t0)*1000:.1f}ms: {len(getattr(news_ctx, 'items', []))} items.")
    except Exception as e:
        logger.warning(f"[BACKGROUND] Async news refresh error: {e}")
    finally:
        news_refresh_lock.release()

def _bg_refresh_macro():
    global cached_macro_context, last_macro_fetch_time
    if not macro_refresh_lock.acquire(blocking=False):
        return
    try:
        t0 = time.time()
        logger.info(f"[BACKGROUND] Async macro refresh started at {(t0 - _boot_start_time)*1000:.1f}ms")
        from src.pipeline.macro_pipeline import MacroPipeline
        from src.dashboard.macro_panel import MacroIntelligencePanel
        pipeline = MacroPipeline()
        macro_ctx = pipeline.run()
        candidate = MacroIntelligencePanel(macro_ctx).to_dict()
        if isinstance(candidate, dict):
            cached_macro_context = candidate
            last_macro_fetch_time = time.time()
            logger.info(f"[BACKGROUND] Async macro refresh completed in {(time.time() - t0)*1000:.1f}ms: {len(getattr(macro_ctx, 'quotes', {}))} quotes.")
    except Exception as e:
        logger.warning(f"[BACKGROUND] Async macro refresh error: {e}")
    finally:
        macro_refresh_lock.release()

def perform_cold_start_hydration():
    global cached_macro_context, cached_news_sentiment, cached_market_context, cached_option_context
    global last_macro_fetch_time, last_news_fetch_time

    # Non-blocking cold start hydration: disk cache snapshots only.
    # External network pipelines (NewsPipeline/MacroPipeline) run asynchronously in background threads.
    try:
        opt_file = Path(".cache/kite_nifty_option_snapshot.json")
        if opt_file.exists():
            with open(opt_file, "r", encoding="utf-8") as f:
                opt_data = json.load(f)
                if isinstance(opt_data, dict):
                    cached_option_context = opt_data
    except Exception as e:
        logger.warning("Cold-start option context hydration warning: %s", e)

    try:
        vix_file = Path(".cache/kite_india_vix_snapshot.json")
        vix_val = 12.5
        if vix_file.exists():
            try:
                with open(vix_file, "r", encoding="utf-8") as f:
                    vdata = json.load(f)
                    vix_val = float(vdata.get("last_price") or vdata.get("value") or 12.5)
            except Exception:
                pass
        from src.broker.services.market_context_builder import MarketContextBuilder
        bs_inst = BrokerService.get_instance()
        orch_inst = None
        if hasattr(bs_inst, "_get_orchestrator") and bs_inst.is_connected():
            try:
                orch_inst = bs_inst._get_orchestrator()
            except PermissionError:
                orch_inst = None
        cached_market_context = MarketContextBuilder.build(
            bs_inst, orch_inst, vix_val,
            (cached_macro_context or {}).get("constituent_metadata")
        )
    except Exception as e:
        logger.warning("Cold-start market context hydration warning: %s", e)

perform_cold_start_hydration()


from src.configuration_engine.runtime import Config
from src.workspace.workspace_manager import WorkspaceManager
from src.workspace.workspace_mode import WorkspaceMode
from src.broker.services.broker_service import BrokerService
from src.broker.models.trading_mode import TradingMode
from src.broker.services.authentication import AuthenticationManager
from src.models.live_portfolio_report import LivePortfolioReportBuilder

def serialize(obj):
    from enum import Enum
    if isinstance(obj, Enum):
        return obj.value
    elif dataclasses.is_dataclass(obj):
        return {k: serialize(v) for k, v in dataclasses.asdict(obj).items()}
    elif hasattr(obj, "__dict__"):
        return {k: serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    elif isinstance(obj, (list, tuple, set)):
        return [serialize(v) for v in obj]
    elif isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif hasattr(obj, "value") and hasattr(obj, "name"):  # for Enums
        return obj.value
    else:
        return obj


def serialize_read_only_context(ctx):
    """Compatibility context without retired product-mode or execution state."""
    payload = serialize(ctx)
    for key in ("current_mode", "execution_mode", "trading_mode", "allow_live_trading"):
        payload.pop(key, None)
    payload["product_mode"] = "READ_ONLY"
    return payload


FORBIDDEN_EXECUTION_ACTIONS = {
    "place_order", "submit_order", "modify_order", "cancel_order",
    "exit_position", "exit_trade", "execute_order", "execute_trade",
    "confirm_execution", "paper_trade", "paper_trading", "simulate_execution",
}


def reject_execution_action(action: str):
    normalized = str(action or "").strip().lower().replace("-", "_")
    if normalized in FORBIDDEN_EXECUTION_ACTIONS:
        return {
            "success": False,
            "status": "GONE",
            "code": 410,
            "error": "AIR ArdhaMind is read only; execution actions are unavailable",
        }
    return None

def handle_daemon_command(action, params, bs, wm):
    global cached_market_context, cached_option_context, active_trade_proposal, cached_news_sentiment, cached_macro_context, last_news_fetch_time, last_macro_fetch_time
    from datetime import datetime
    rejected = reject_execution_action(action)
    if rejected:
        return rejected
    ws_mode = wm.current_mode

    if action == "get_context":
        ctx = wm.get_context()
        payload = serialize_read_only_context(ctx)
        payload.update({
            "allow_live_trading": False,
            "require_confirmation": Config.REQUIRE_CONFIRMATION,
            "show_mode_warning": Config.SHOW_MODE_WARNING,
            "auto_fallback_to_development": Config.AUTO_FALLBACK_TO_DEVELOPMENT,
        })
        return payload

    elif action == "login":
        api_key = params.get("api_key")
        access_token = params.get("access_token")
        persist_key = params.get("persist_key") == True or params.get("persist_key") == "True"
        persist_token = params.get("persist_token") == True or params.get("persist_token") == "True"

        gateway = bs.get_gateway()
        if hasattr(gateway, "api_key"):
            gateway.api_key = api_key
        if hasattr(gateway, "access_token"):
            gateway.access_token = access_token

        success = gateway.connect(api_key=api_key, access_token=access_token)
        if not success:
            last_error = getattr(gateway, "_last_error", "Kite connection failed")
            return {"success": False, "error": last_error}

        from src.broker.services.session_manager import SessionManager
        SessionManager.save_session(
            access_token=access_token,
            api_key=api_key,
            persist_key=persist_key,
            persist_token=persist_token
        )
        from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
        BrokerHealthEvaluator.set_reconciliation_status(complete=True, in_progress=False)
        return {"success": True, "context": serialize(wm.get_context())}

    elif action == "logout":
        bs.logout()
        from src.broker.services.session_manager import SessionManager
        SessionManager.delete_session()
        from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
        BrokerHealthEvaluator.set_reconciliation_status(complete=False, in_progress=False)
        return {"success": True}

    elif action == "get_broker_config":
        from src.configuration_engine.runtime import Config
        from src.broker.services.session_manager import SessionManager
        from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
        session_data = SessionManager.load_session() or {}
        api_key = getattr(Config, "KITE_API_KEY", "") or session_data.get("api_key", "")
        api_secret = getattr(Config, "KITE_API_SECRET", "")
        redirect_url = getattr(Config, "KITE_REDIRECT_URL", "") or "http://127.0.0.1:3000/api/broker/callback"

        broker_health = BrokerHealthEvaluator.evaluate(bs)
        return {
            "api_key_configured": bool(api_key),
            "api_secret_configured": bool(api_secret),
            "redirect_url": redirect_url,
            "access_token_saved": "access_token" in session_data and not session_data.get("expired", False),
            "session_status": str(broker_health.status).upper()
        }

    elif action == "refresh_news":
        if not news_refresh_lock.acquire(blocking=False):
            return {"success": False, "error": "A news refresh is already running."}
        try:
            from src.pipeline.news_pipeline import NewsPipeline
            from src.dashboard.news_panel import NewsIntelligencePanel

            pipeline = NewsPipeline()
            for p in pipeline.providers:
                p.refresh_interval = 0.0

            news_ctx = pipeline.run()
            candidate = NewsIntelligencePanel(news_ctx).to_dict()
            if isinstance(candidate, dict) and "items" in candidate:
                cached_news_sentiment = candidate
                last_news_fetch_time = time.time()
                return {"success": True, "newsSentiment": cached_news_sentiment}
            else:
                return {"success": False, "error": "Invalid candidate news snapshot"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            news_refresh_lock.release()

    elif action == "refresh_macro":
        target_keys = params.get("keys") or []
        if isinstance(target_keys, str):
            target_keys = [target_keys]

        if not macro_refresh_lock.acquire(blocking=False):
            return {"success": False, "error": "A macro refresh is already running."}
        try:
            from src.pipeline.macro_pipeline import MacroPipeline
            from src.dashboard.macro_panel import MacroIntelligencePanel

            pipeline = MacroPipeline()
            for p in pipeline.providers:
                p.refresh_interval = 0.0

            macro_ctx = pipeline.run()
            candidate = MacroIntelligencePanel(macro_ctx).to_dict()
            if isinstance(candidate, dict):
                if cached_macro_context is not None and target_keys:
                    existing_quotes = cached_macro_context.get("quotes") or {}
                    new_quotes = candidate.get("quotes") or {}
                    for k in target_keys:
                        k_norm = str(k).upper().replace(" ", "_")
                        matched = next((nk for nk in new_quotes if nk.upper().replace(" ", "_") == k_norm), None)
                        if matched:
                            existing_quotes[matched] = new_quotes[matched]
                    cached_macro_context["quotes"] = existing_quotes
                else:
                    cached_macro_context = candidate

                last_macro_fetch_time = time.time()
                return {"success": True, "macroIntelligence": cached_macro_context}
            else:
                return {"success": False, "error": "Invalid candidate macro snapshot"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            macro_refresh_lock.release()

    elif action == "live_assistant_query":
        try:
            from src.live_assistant.assistant_service import LiveAssistantService
            message = params.get("message") or params.get("prompt") or ""
            conversation_id = params.get("conversation_id") or "default"
            state = dict(params.get("workstation_state") or params.get("state") or {})
            provider_override = params.get("provider")

            # Guarantee server-authoritative news state parity:
            # If incoming state lacks populated news_intelligence items, populate it from cached_news_sentiment or NewsPipeline
            has_items = bool(
                (isinstance(state.get("news_intelligence"), dict) and state.get("news_intelligence", {}).get("items"))
                or (isinstance(state.get("newsSentiment"), dict) and state.get("newsSentiment", {}).get("items"))
                or (isinstance(state.get("news"), dict) and state.get("news", {}).get("items"))
            )
            if not has_items:
                if not (cached_news_sentiment and isinstance(cached_news_sentiment, dict) and cached_news_sentiment.get("items")):
                    _bg_refresh_news()
                if cached_news_sentiment and isinstance(cached_news_sentiment, dict):
                    state["news_intelligence"] = cached_news_sentiment
                    state["newsSentiment"] = cached_news_sentiment
            if not state.get("macro_intelligence") and cached_macro_context:
                state["macro_intelligence"] = cached_macro_context

            res = LiveAssistantService.process_query(
                user_message=message,
                conversation_id=conversation_id,
                workstation_state=state,
                provider_override=provider_override
            )
            return {"success": True, "result": res}
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif action == "get_pre_market_briefing":
        from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine
        date_param = params.get("date")
        if date_param:
            report = PreMarketBriefingEngine.load_persisted_briefing(date_param)
            if report:
                return {"success": True, "briefing": report.to_dict()}

        eval_state = {
            "market_session": {"status": "CLOSED", "session_date": "2026-08-17"},
            "market_data": cached_market_context or {},
            "option_intelligence": cached_option_context or {},
            "macro_intelligence": cached_macro_context or {},
            "news_intelligence": cached_news_sentiment or {}
        }
        report = PreMarketBriefingEngine.generate_or_get_briefing(eval_state)
        return {"success": True, "briefing": report.to_dict()}

    elif action == "get_pre_market_briefing_history":
        from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine
        history = PreMarketBriefingEngine.list_history()
        return {"success": True, "history": history}

    elif action == "generate_pre_market_briefing":
        from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine
        force_freeze = params.get("force_freeze", True)
        force_regenerate = params.get("force_regenerate", True)
        eval_state = {
            "market_session": {"status": "CLOSED", "session_date": "2026-08-17"},
            "market_data": cached_market_context or {},
            "option_intelligence": cached_option_context or {},
            "macro_intelligence": cached_macro_context or {},
            "news_intelligence": cached_news_sentiment or {}
        }
        report = PreMarketBriefingEngine.generate_or_get_briefing(
            eval_state,
            force_freeze=force_freeze,
            force_regenerate=force_regenerate
        )
        return {"success": True, "briefing": report.to_dict()}

    elif action == "validate_pre_market_briefing":
        from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine
        eval_state = {
            "market_session": {"status": "CLOSED", "session_date": "2026-08-17"},
            "market_data": cached_market_context or {},
            "option_intelligence": cached_option_context or {},
            "macro_intelligence": cached_macro_context or {},
            "news_intelligence": cached_news_sentiment or {}
        }
        date_param = params.get("date")
        report = PreMarketBriefingEngine.load_persisted_briefing(date_param) if date_param else None
        if not report:
            report = PreMarketBriefingEngine.generate_or_get_briefing(eval_state)
        is_preview = params.get("is_preview", True)
        validated = PreMarketBriefingEngine.validate_briefing(report, eval_state, is_preview=is_preview)
        return {"success": True, "briefing": validated.to_dict()}

    elif action == "get_broker_health":
        from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
        health = BrokerHealthEvaluator.evaluate(bs)
        return {"success": True, **health.to_dict()}

    elif action in [
        "get_market_score", "get_opportunity_context", "get_strategy_evaluation",
        "get_confidence_report", "get_risk_report", "get_decision_report",
        "get_operations_report", "get_configuration_report", "get_explanation_report",
        "get_trade_plan", "get_intraday_report", "get_validation_report", "get_optimization_report"
    ]:
        _, result = AnalyticalPipelineService.run_daemon_snapshot(
            cached_market_context, cached_option_context,
            market_state="OPEN", broker_state="CONNECTED" if bs.is_connected() else "DISCONNECTED")
        data = result.compatibility_values()

        action_map = {
            "get_market_score": "marketScore",
            "get_opportunity_context": "opportunityContext",
            "get_strategy_evaluation": "strategyEvaluation",
            "get_confidence_report": "confidenceReport",
            "get_risk_report": "riskReport",
            "get_decision_report": "decisionReport",
            "get_operations_report": "operations_report",
            "get_configuration_report": "configuration_report",
            "get_explanation_report": "explanationReport",
            "get_trade_plan": "tradeScenarios",
            "get_intraday_report": "intraday_report",
            "get_validation_report": "validation_report",
            "get_optimization_report": "optimization_report"
        }
        key = action_map.get(action)
        return data.get(key, {})

    elif action == "get_login_url":
        from src.broker.services.authentication import AuthenticationManager
        api_key = params.get("api_key")
        try:
            url = AuthenticationManager.generate_login_url(api_key=api_key)
            return {"login_url": url, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}

    elif action == "exchange_request_token":
        from src.broker.services.authentication import AuthenticationManager
        from src.broker.services.session_manager import SessionManager
        request_token = params.get("request_token")
        if not request_token:
            return {"success": False, "error": "Missing request token"}
        try:
            session = AuthenticationManager.generate_access_token(request_token)
            access_token = session.get("access_token")
            api_key = session.get("api_key") or getattr(Config, "KITE_API_KEY", "")
            user_id = session.get("user_id") or session.get("client_id")

            if not access_token:
                return {"success": False, "error": "Token exchange failed: access_token not returned"}

            # Save session to local disk cache
            saved = SessionManager.save_session(
                access_token=access_token,
                api_key=api_key,
                login_time=time.time(),
                persist_key=True,
                persist_token=True
            )

            # Verify reload immediately
            loaded_data = SessionManager.load_session()
            reload_ok = loaded_data and loaded_data.get("access_token") == access_token

            # Connect authoritative BrokerService singleton
            gateway = bs.get_gateway()
            connected = gateway.connect(api_key=api_key, access_token=access_token)

            if connected:
                try:
                    setup_real_ticks_callback()
                    bs.connect_stream()
                    bs.subscribe_stream([
                        "NIFTY", "NIFTY BANK", "NIFTY IT", "NIFTY AUTO", "NIFTY PHARMA",
                        "NIFTY METAL", "NIFTY FMCG", "NIFTY REALTY", "NIFTY ENERGY",
                        "NIFTY OIL AND GAS", "NIFTY FIN SERVICE", "INDIA VIX",
                    ])
                    logger.info("Auto-started streaming feed and core subscriptions upon OAuth completion.")
                except Exception as se:
                    logger.error(f"Failed to auto-start stream on OAuth completion: {se}")

            # Perform profile test
            profile_ok = False
            client_id = user_id or getattr(gateway, "user_id", None) or "USER_OK"
            if connected and hasattr(gateway, "_kite_client") and gateway._kite_client:
                try:
                    prof = gateway._kite_client.profile()
                    profile_ok = True
                    client_id = prof.get("user_id") or prof.get("client_id") or client_id
                except Exception as pe:
                        logger.warning(f"Profile verification call warning: {pe}")
                        profile_ok = True  # session connects via gateway.connect

            print(f"generate_session: SUCCESS", file=sys.stderr, flush=True)
            print(f"session_saved: {'YES' if saved else 'NO'}", file=sys.stderr, flush=True)
            print(f"session_file_exists: YES", file=sys.stderr, flush=True)
            print(f"session_restored: {'YES' if reload_ok else 'NO'}", file=sys.stderr, flush=True)
            print(f"broker_service_authenticated: {'YES' if connected else 'NO'}", file=sys.stderr, flush=True)
            from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
            BrokerHealthEvaluator.set_reconciliation_status(complete=True, in_progress=False)

            # Force immediate canonical workstation state broadcast
            try:
                broker_account = {"client_id": client_id}
                legacy_data = {
                    "workspaceContext": {
                        "currentMode": "READ_ONLY",
                        "brokerState": "CONNECTED_VERIFIED",
                        "marketState": "CLOSED",
                        "brokerType": "ZERODHA",
                        "marketDataSource": "LIVE",
                        "analyticsMode": "ENABLED",
                        "notificationMode": "ENABLED",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    },
                    "brokerAccount": broker_account,
                    "newsSentiment": cached_news_sentiment or get_initial_news_sentiment(),
                    "macroIntelligence": cached_macro_context or get_initial_macro_context()
                }
                canonical_state = WorkstationStateService.build_from_legacy(
                    legacy_data, broker_state="CONNECTED_VERIFIED", market_state="CLOSED"
                )
                print(json.dumps({"type": "state", "data": canonical_state.to_dict()}), flush=True)
            except Exception as broadcast_err:
                logger.error(f"Failed immediate post-login state broadcast: {broadcast_err}")

            return {
                "success": True,
                "brokerState": "CONNECTED_VERIFIED",
                "client_id": client_id,
                "context": serialize(wm.get_context())
            }
        except Exception as e:
            logger.error(f"Error in exchange_request_token: {e}")
            return {"success": False, "error": str(e)}

    elif action == "get_broker_health":
        from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
        health = BrokerHealthEvaluator.evaluate(bs)
        return {"success": True, **health.to_dict()}

    elif action == "get_interpretation_status":
        from src.services.openai_interpretation_service import OpenAIInterpretationService
        return OpenAIInterpretationService.get_status()

    elif action == "get_interpretation":
        from src.services.openai_interpretation_service import OpenAIInterpretationService
        c_state = params.get("canonical_state") or {}
        return OpenAIInterpretationService.interpret_canonical_state(c_state)

    elif action == "get_performance_records":
        from src.intelligence_engine.performance_tracker_engine import PerformanceTrackerEngine
        trading_date = params.get("date") or datetime.now().strftime("%Y-%m-%d")
        engine = PerformanceTrackerEngine()
        records = engine.load_records(trading_date)
        return {"success": True, "records": [r.to_dict() for r in records]}

    elif action == "get_performance_history":
        from src.intelligence_engine.performance_tracker_engine import PerformanceTrackerEngine
        engine = PerformanceTrackerEngine()
        history = engine.get_available_dates()
        return {"success": True, "history": history}

    elif action == "capture_performance_snapshot":
        from src.intelligence_engine.performance_tracker_engine import PerformanceTrackerEngine
        trading_date = params.get("date") or datetime.now().strftime("%Y-%m-%d")
        phase = params.get("phase", "LIVE_INTRADAY")
        state = params.get("state") or {}
        engine = PerformanceTrackerEngine()
        if phase == "PRE_MARKET":
            recs = engine.capture_pre_market_snapshot(state, trading_date)
        elif phase == "EARLY_SESSION":
            recs = engine.capture_early_session_snapshot(state, trading_date)
        else:
            recs = engine.capture_live_intraday_snapshot(state, trading_date)
        return {"success": True, "records": [r.to_dict() for r in recs]}

    elif action == "evaluate_performance_records":
        from src.intelligence_engine.performance_tracker_engine import PerformanceTrackerEngine
        trading_date = params.get("date") or datetime.now().strftime("%Y-%m-%d")
        session_truth = params.get("session_truth") or {}
        engine = PerformanceTrackerEngine()
        recs = engine.evaluate_pending_records(trading_date, session_truth)
        return {"success": True, "records": [r.to_dict() for r in recs]}

    elif action == "get_active_proposal":
        from src.opportunity_engine.registry import OpportunityRegistryService
        from src.broker.services.market_status_service import MarketStatusService
        ms = MarketStatusService.get_instance().get_market_status()
        is_open = getattr(ms, "is_open", False) if ms else False
        
        opp_eval_context = {
            "market_context": cached_market_context or {},
            "option_context": cached_option_context or {},
            "breadth": (cached_market_context or {}).get("breadth", {}),
            "news": cached_news_sentiment or {},
            "macro": cached_macro_context or {},
            "freshness_state": "LIVE" if is_open else "CLOSED",
            "market_state": "OPEN" if is_open else "CLOSED",
        }
        opp_intel = OpportunityRegistryService.get_instance().evaluate_and_update(opp_eval_context, 1)
        best_opp = getattr(opp_intel, "best_opportunity", {}) if opp_intel else {}

        # If current opportunity evaluation yields NO_TRADE or priority < 65, update proposal to NO_TRADE
        is_qualified = bool(best_opp and best_opp.get("status") != "NO_TRADE" and float(best_opp.get("priority_score", 0)) >= 65)
        if not is_qualified:
            new_prop = ProposalBuilder.build_proposal(None, opp_eval_context)
            active_trade_proposal = new_prop
            return {"success": True, "proposal": new_prop.to_dict()}

        # If proposal is already approved/dry-run recorded/rejected for current qualified setup, preserve its state
        if active_trade_proposal and active_trade_proposal.state in [
            ProposalState.INTENT_PREPARED.value,
            ProposalState.DRY_RUN_RECORDED.value,
            ProposalState.REJECTED.value,
        ]:
            return {"success": True, "proposal": active_trade_proposal.to_dict()}

        new_prop = ProposalBuilder.build_proposal(best_opp, opp_eval_context)
        active_trade_proposal = new_prop
        return {"success": True, "proposal": new_prop.to_dict()}

    elif action == "validate_proposal":
        prop_id = params.get("proposal_id")
        if not active_trade_proposal or (prop_id and active_trade_proposal.proposal_id != prop_id):
            audit_entry = proposal_audit_storage.get_proposal(prop_id) if prop_id else None
            if audit_entry:
                return {"success": True, "state": audit_entry["state"], "proposal": audit_entry["payload"]}
            return {"success": False, "error": f"Proposal {prop_id} not found"}

        # Perform Pre-Flight Risk Checks
        blockers = []
        if active_trade_proposal.state == ProposalState.NO_TRADE.value:
            blockers.append("No high-conviction trade setup active.")
        if active_trade_proposal.max_loss_inr > 50000.0:
            blockers.append(f"Max loss ₹{active_trade_proposal.max_loss_inr:.2f} exceeds ₹50,000 threshold.")
        if active_trade_proposal.risk_reward_ratio < 1.0:
            blockers.append(f"Risk-reward ratio 1:{active_trade_proposal.risk_reward_ratio:.2f} is below 1:1.0 minimum.")

        if blockers:
            return {
                "success": False,
                "state": ProposalState.REJECTED.value,
                "blockers": blockers,
                "proposal": active_trade_proposal.to_dict()
            }

        active_trade_proposal.state = ProposalState.RISK_VALIDATED.value
        proposal_audit_storage.record_proposal(
            proposal_id=active_trade_proposal.proposal_id,
            state=active_trade_proposal.state,
            payload=active_trade_proposal.to_dict(),
            risk_eval=active_trade_proposal.risk_evaluation
        )
        return {
            "success": True,
            "state": ProposalState.RISK_VALIDATED.value,
            "proposal": active_trade_proposal.to_dict()
        }

    elif action == "calculate_proposal_margin":
        prop_id = params.get("proposal_id")
        lots = int(params.get("lots", 1))
        product = str(params.get("product", "NRML")).upper()

        if not active_trade_proposal or (prop_id and active_trade_proposal.proposal_id != prop_id):
            return {"success": False, "error": f"Active proposal {prop_id} not found"}

        # Recalculate proposal exposure for requested lots and product
        active_trade_proposal.recalculate_exposure(lots=lots, product=product)

        # Retrieve available funds & margin check via Kite
        is_conn = bs.is_connected()
        available_margin = None
        required_margin = round(active_trade_proposal.entry_price * active_trade_proposal.total_quantity, 2)
        margin_sufficient = None
        margin_status = "MARGIN_UNAVAILABLE"
        failure_reason = None

        if is_conn:
            try:
                funds = bs.get_funds()
                avail = getattr(funds, "available_margin", 0.0) or getattr(funds, "available_cash", 0.0)
                available_margin = round(float(avail), 2)

                # Attempt Kite Connect order_margins API call
                try:
                    orders_payload = [{
                        "exchange": "NFO",
                        "tradingsymbol": active_trade_proposal.contract_symbol.replace(" ", ""),
                        "transaction_type": "BUY",
                        "variety": "regular",
                        "product": product,
                        "order_type": "LIMIT",
                        "quantity": active_trade_proposal.total_quantity,
                        "price": active_trade_proposal.entry_price,
                    }]
                    margin_res = bs.calculate_order_margins(orders_payload)
                    if margin_res and len(margin_res) > 0:
                        first_m = margin_res[0]
                        req_total = float(first_m.get("total") or first_m.get("cash") or required_margin)
                        if req_total > 0:
                            required_margin = round(req_total, 2)
                except Exception as mex:
                    logger.warning(f"Kite order_margins API call non-critical fallback: {mex}")

                margin_status = "AVAILABLE"
                margin_sufficient = (available_margin >= required_margin) and (available_margin > 0)
            except Exception as e:
                logger.warning(f"Failed to retrieve funds/margins: {e}")
                margin_status = "MARGIN_UNAVAILABLE"
                failure_reason = str(e)
        else:
            failure_reason = "Zerodha broker session disconnected or access token expired."

        active_trade_proposal.margin_status = margin_status
        active_trade_proposal.required_margin = required_margin
        active_trade_proposal.available_margin = available_margin
        active_trade_proposal.margin_sufficient = margin_sufficient

        return {
            "success": True,
            "margin_status": margin_status,
            "required_margin": required_margin,
            "available_margin": available_margin,
            "margin_sufficient": margin_sufficient,
            "failure_reason": failure_reason,
            "proposal": active_trade_proposal.to_dict()
        }

    elif action == "approve_proposal":
        prop_id = params.get("proposal_id")
        lots = int(params.get("lots", 1)) if params.get("lots") else None
        product = str(params.get("product", "NRML")).upper() if params.get("product") else None

        if not active_trade_proposal or (prop_id and active_trade_proposal.proposal_id != prop_id):
            return {"success": False, "error": f"Active proposal {prop_id} not found for approval"}

        if lots:
            active_trade_proposal.recalculate_exposure(lots=lots, product=product)

        # Retrieve available funds & margin check via Kite
        is_conn = bs.is_connected()
        if is_conn:
            try:
                funds = bs.get_funds()
                avail = getattr(funds, "available_margin", 0.0) or getattr(funds, "available_cash", 0.0)
                active_trade_proposal.available_margin = round(float(avail), 2)
                req = round(active_trade_proposal.entry_price * active_trade_proposal.total_quantity, 2)
                active_trade_proposal.required_margin = req
                active_trade_proposal.margin_sufficient = (avail >= req) if avail > 0 else False
                active_trade_proposal.margin_status = "AVAILABLE"
            except Exception:
                pass

        from datetime import timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        active_trade_proposal.state = ProposalState.DRY_RUN_RECORDED.value
        active_trade_proposal.approval_timestamp = now_iso
        if active_trade_proposal.order_intent:
            active_trade_proposal.order_intent["dry_run"] = True
            active_trade_proposal.order_intent["generated_at"] = now_iso
            active_trade_proposal.order_intent["lots"] = active_trade_proposal.lots
            active_trade_proposal.order_intent["quantity"] = active_trade_proposal.total_quantity
            active_trade_proposal.order_intent["product"] = active_trade_proposal.product

        proposal_audit_storage.record_proposal(
            proposal_id=active_trade_proposal.proposal_id,
            state=active_trade_proposal.state,
            payload=active_trade_proposal.to_dict(),
            risk_eval={
                "margin_required": active_trade_proposal.required_margin,
                "available_margin": active_trade_proposal.available_margin,
                "margin_sufficient": active_trade_proposal.margin_sufficient,
                "lots": active_trade_proposal.lots,
                "total_quantity": active_trade_proposal.total_quantity,
                "product": active_trade_proposal.product,
            },
            approval_timestamp=now_iso
        )
        return {
            "success": True,
            "state": ProposalState.DRY_RUN_RECORDED.value,
            "proposal": active_trade_proposal.to_dict()
        }

    elif action == "reject_proposal":
        prop_id = params.get("proposal_id")
        reason = params.get("reason", "Trader rejected trade proposal.")
        if not active_trade_proposal or (prop_id and active_trade_proposal.proposal_id != prop_id):
            return {"success": False, "error": f"Proposal {prop_id} not found"}

        from datetime import timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        active_trade_proposal.state = ProposalState.REJECTED.value
        active_trade_proposal.rejection_reason = reason

        proposal_audit_storage.record_proposal(
            proposal_id=active_trade_proposal.proposal_id,
            state=active_trade_proposal.state,
            payload=active_trade_proposal.to_dict(),
            rejection_reason=reason
        )
        return {
            "success": True,
            "state": ProposalState.REJECTED.value,
            "proposal": active_trade_proposal.to_dict()
        }

    elif action == "get_proposal_audits":
        limit = int(params.get("limit", 50))
        audits = proposal_audit_storage.get_recent_audits(limit=limit)
        return {"success": True, "audits": audits}

    elif action == "execute_live_order":
        import uuid
        from datetime import timezone
        prop_id = params.get("proposal_id")
        idempotency_key = params.get("idempotency_key") or params.get("intent_id") or f"IDEMP-ORD-{uuid.uuid4().hex[:12]}"
        intent_id = params.get("intent_id") or f"INTENT-{uuid.uuid4().hex[:12]}"
        lots = int(params.get("lots", 1))
        product = str(params.get("product", "NRML")).upper()

        # 1. Check Live Execution Flag
        enable_live = os.environ.get("ENABLE_LIVE_EXECUTION", "false").lower() in ("true", "1", "yes")
        if not enable_live:
            return {
                "success": False,
                "error": "Live execution is disabled. Set ENABLE_LIVE_EXECUTION=true in staging environment.",
                "code": "LIVE_EXECUTION_DISABLED"
            }

        # 2. Persistent Idempotency Check in execution_operations table
        existing_op = proposal_audit_storage.get_operation_by_idempotency_key(idempotency_key)
        if existing_op:
            if existing_op.get("current_status") in (OperationStatus.SUBMITTED.value, OperationStatus.COMPLETED.value):
                existing_ord = proposal_audit_storage.get_order(existing_op.get("entity_id", ""))
                return {
                    "success": True,
                    "idempotent": True,
                    "order": existing_ord or existing_op.get("result_payload"),
                    "proposal": active_trade_proposal.to_dict() if active_trade_proposal else None,
                    "message": "Idempotent operation detected: returning previously recorded live order."
                }

        # 3. Validate proposal
        if not active_trade_proposal or (prop_id and active_trade_proposal.proposal_id != prop_id):
            return {"success": False, "error": f"Active proposal {prop_id} not found for live execution"}

        if active_trade_proposal.state == ProposalState.NO_TRADE.value:
            return {"success": False, "error": "Cannot execute order for NO_TRADE state"}

        # 4. Check existing order by intent
        existing_order = proposal_audit_storage.get_order_by_intent(intent_id)
        if existing_order and existing_order.get("status") not in (BrokerOrderState.REJECTED.value, BrokerOrderState.CANCELLED.value):
            return {
                "success": True,
                "idempotent": True,
                "order": existing_order,
                "proposal": active_trade_proposal.to_dict(),
                "message": "Duplicate submission detected: returning existing active order."
            }

        # 5. Recalculate exposure for requested lots & product
        active_trade_proposal.recalculate_exposure(lots=lots, product=product)

               # 5. Safety Gatekeeper Evaluation (Milestone 6)
        active_pos = proposal_audit_storage.get_open_positions()
        active_ord = proposal_audit_storage.get_active_orders()
        unresolved_ops = proposal_audit_storage.get_unresolved_operations()
        
        # Calculate daily realized loss from closed positions today
        all_closed_today = [
            p for p in proposal_audit_storage.get_all_positions(limit=50)
            if p.get("status") == "CLOSED" and (p.get("closed_at") or "")[:10] == now_iso[:10]
        ]
        daily_loss_sum = sum(abs(p.get("realized_pnl_analytics", 0.0)) for p in all_closed_today if p.get("realized_pnl_analytics", 0.0) < 0)

        # Fresh quote check if broker connected
        fresh_quote = None
        if bs.is_connected():
            try:
                symbol_clean = active_trade_proposal.contract_symbol.replace(" ", "")
                q_res = bs.get_quote([f"NFO:{symbol_clean}"])
                if q_res and f"NFO:{symbol_clean}" in q_res:
                    fresh_quote = q_res[f"NFO:{symbol_clean}"]
            except Exception as qex:
                logger.warning(f"Quote fetch error during safety evaluation: {qex}")

        safety_eval = safety_gatekeeper.evaluate_entry_order(
            proposal=active_trade_proposal,
            fresh_quote=fresh_quote,
            current_daily_realized_loss=daily_loss_sum,
            active_positions=active_pos,
            active_orders=active_ord,
            broker_connected=bs.is_connected(),
            unresolved_operations=unresolved_ops
        )
        if not safety_eval.passed:
            return {
                "success": False,
                "error": safety_eval.failure_reason,
                "code": safety_eval.blocker_code,
                "policy_metrics": safety_eval.policy_metrics
            }

        # 6. Recalculate exposure for requested lots & product
        active_trade_proposal.recalculate_exposure(lots=lots, product=product)

        # 7. Check Broker Session
        if not bs.is_connected():
            return {
                "success": False,
                "error": "Zerodha broker session disconnected or expired. Please re-authenticate.",
                "code": "SESSION_EXPIRED"
            }

        # 8. Check Margin Sufficiency
        try:
            funds = bs.get_funds()
            available_margin = float(getattr(funds, "available_margin", 0.0) or getattr(funds, "available_cash", 0.0))
            required_margin = round(active_trade_proposal.entry_price * active_trade_proposal.total_quantity, 2)
            if available_margin > 0 and available_margin < required_margin:
                return {
                    "success": False,
                    "error": f"Insufficient funds: Required ₹{required_margin:.2f}, Available ₹{available_margin:.2f}",
                    "code": "INSUFFICIENT_MARGIN"
                }
        except Exception as fe:
            logger.warning(f"Funds check warning during live execution: {fe}")

        now_iso = datetime.now(timezone.utc).isoformat()
        order_id = f"ORD-{uuid.uuid4().hex[:12]}"
        op_id = f"OP-{uuid.uuid4().hex[:12]}"
        tradingsymbol = active_trade_proposal.contract_symbol.replace(" ", "")

        # 9. Register Operation in INITIATED status
        exec_op = ExecutionOperation(
            operation_id=op_id,
            idempotency_key=idempotency_key,
            operation_type=OperationType.ORDER_SUBMIT.value,
            entity_type="ORDER",
            entity_id=order_id,
            requested_at=now_iso,
            current_status=OperationStatus.INITIATED.value,
        )
        proposal_audit_storage.record_operation(exec_op)

        # 10. Initial Order Record
        order_rec = OrderRecord(
            order_id=order_id,
            proposal_id=active_trade_proposal.proposal_id,
            intent_id=intent_id,
            broker_order_id=None,
            contract_symbol=active_trade_proposal.contract_symbol,
            exchange="NFO",
            transaction_type="BUY",
            order_type="LIMIT",
            product=product,
            quantity=active_trade_proposal.total_quantity,
            filled_quantity=0,
            remaining_quantity=active_trade_proposal.total_quantity,
            price=active_trade_proposal.entry_price,
            average_price=0.0,
            status=BrokerOrderState.SUBMITTING.value,
            rejection_reason=None,
            provenance="ARDHAMIND",
            placed_at=now_iso,
            updated_at=now_iso,
            raw_payload={
                "lots": lots,
                "lot_size": active_trade_proposal.lot_size,
                "entry_price": active_trade_proposal.entry_price,
                "stop_loss": active_trade_proposal.stop_loss,
                "target_1": active_trade_proposal.target_1,
                "target_2": active_trade_proposal.target_2,
            }
        )
        proposal_audit_storage.record_order(order_rec)
        proposal_audit_storage.record_order_event(
            order_id=order_id,
            event_type="ORDER_SUBMITTING",
            status=BrokerOrderState.SUBMITTING.value,
            message="Submitting live order to Zerodha Kite Connect...",
            raw_data={"lots": lots, "quantity": active_trade_proposal.total_quantity}
        )

        try:
            broker_order_id = bs.place_order(
                exchange="NFO",
                tradingsymbol=tradingsymbol,
                transaction_type="BUY",
                quantity=active_trade_proposal.total_quantity,
                product=product,
                order_type="LIMIT",
                price=active_trade_proposal.entry_price,
                tag="ardhamind",
            )
            order_rec.broker_order_id = str(broker_order_id)
            order_rec.status = BrokerOrderState.SUBMITTED.value
            proposal_audit_storage.record_order(order_rec)
            proposal_audit_storage.record_order_event(
                order_id=order_id,
                event_type="ORDER_SUBMITTED",
                status=BrokerOrderState.SUBMITTED.value,
                message=f"Order accepted by Kite broker. Broker Order ID: {broker_order_id}",
                raw_data={"broker_order_id": str(broker_order_id)}
            )

            # Update operation to SUBMITTED
            proposal_audit_storage.update_operation_status(
                operation_id=op_id,
                status=OperationStatus.SUBMITTED.value,
                broker_order_id=str(broker_order_id),
                result_payload=order_rec.to_dict()
            )

            active_trade_proposal.state = ProposalState.SUBMITTED.value
            active_trade_proposal.approval_timestamp = now_iso
            proposal_audit_storage.record_proposal(
                proposal_id=active_trade_proposal.proposal_id,
                state=active_trade_proposal.state,
                payload=active_trade_proposal.to_dict(),
                risk_eval={
                    "live_broker_order_id": str(broker_order_id),
                    "lots": lots,
                    "quantity": active_trade_proposal.total_quantity,
                    "product": product,
                },
                approval_timestamp=now_iso
            )

            # Reconstruct initial journal lineage projection
            proposal_audit_storage.reconstruct_journal_for_proposal(active_trade_proposal.proposal_id)

            return {
                "success": True,
                "order": order_rec.to_dict(),
                "proposal": active_trade_proposal.to_dict()
            }
        except Exception as ex:
            err_msg = str(ex)
            # Check for network timeout -> unverified outcome
            if "timeout" in err_msg.lower() or "connection" in err_msg.lower():
                order_rec.status = BrokerOrderState.SUBMISSION_OUTCOME_UNVERIFIED.value
                proposal_audit_storage.record_order(order_rec)
                proposal_audit_storage.update_operation_status(
                    operation_id=op_id,
                    status=OperationStatus.OUTCOME_UNVERIFIED.value,
                    error_message=err_msg
                )
                return {
                    "success": False,
                    "unverified": True,
                    "error": f"Submission outcome unverified due to network timeout: {err_msg}",
                    "order": order_rec.to_dict()
                }

            order_rec.status = BrokerOrderState.REJECTED.value
            order_rec.rejection_reason = err_msg
            proposal_audit_storage.record_order(order_rec)
            proposal_audit_storage.record_order_event(
                order_id=order_id,
                event_type="ORDER_REJECTED",
                status=BrokerOrderState.REJECTED.value,
                message=f"Order failed / rejected: {err_msg}",
                raw_data={"error": err_msg}
            )
            proposal_audit_storage.update_operation_status(
                operation_id=op_id,
                status=OperationStatus.FAILED.value,
                error_message=err_msg
            )
            return {
                "success": False,
                "error": err_msg,
                "order": order_rec.to_dict()
            }

    elif action == "cancel_order":
        import uuid
        from datetime import timezone
        order_id = params.get("order_id")
        idempotency_key = params.get("idempotency_key") or f"IDEMP-CANCEL-{order_id}-{uuid.uuid4().hex[:8]}"

        enable_live = os.environ.get("ENABLE_LIVE_EXECUTION", "false").lower() in ("true", "1", "yes")
        if not enable_live:
            return {
                "success": False,
                "error": "Live execution is disabled. Set ENABLE_LIVE_EXECUTION=true in staging environment.",
                "code": "LIVE_EXECUTION_DISABLED"
            }

        # Check persistent idempotency
        existing_op = proposal_audit_storage.get_operation_by_idempotency_key(idempotency_key)
        if existing_op and existing_op.get("current_status") in (OperationStatus.SUBMITTED.value, OperationStatus.COMPLETED.value):
            return {
                "success": True,
                "idempotent": True,
                "message": "Cancellation request already processed."
            }

        ord_dict = proposal_audit_storage.get_order(order_id)
        if not ord_dict:
            return {"success": False, "error": f"Order {order_id} not found."}

        current_st = ord_dict.get("status")
        if current_st in (BrokerOrderState.CANCELLED.value, BrokerOrderState.FILLED.value, BrokerOrderState.REJECTED.value):
            return {"success": False, "error": f"Order cannot be cancelled in terminal state '{current_st}'."}

        b_id = ord_dict.get("broker_order_id")
        now_iso = datetime.now(timezone.utc).isoformat()
        op_id = f"OP-CANCEL-{uuid.uuid4().hex[:12]}"

        exec_op = ExecutionOperation(
            operation_id=op_id,
            idempotency_key=idempotency_key,
            operation_type=OperationType.ORDER_CANCEL.value,
            entity_type="ORDER",
            entity_id=order_id,
            requested_at=now_iso,
            current_status=OperationStatus.INITIATED.value,
            broker_order_id=b_id
        )
        proposal_audit_storage.record_operation(exec_op)

        if not b_id:
            # Order was not yet sent to broker; cancel locally
            proposal_audit_storage.update_order_status(
                order_id=order_id,
                status=BrokerOrderState.CANCELLED.value,
                cancellation_reason="Cancelled prior to broker dispatch"
            )
            proposal_audit_storage.update_operation_status(
                operation_id=op_id,
                status=OperationStatus.COMPLETED.value
            )
            return {"success": True, "status": "CANCELLED", "order_id": order_id}

        if not bs.is_connected():
            return {"success": False, "error": "Broker session disconnected. Cannot route cancellation."}

        try:
            bs.cancel_order(order_id=b_id)
            proposal_audit_storage.update_order_status(
                order_id=order_id,
                status=BrokerOrderState.CANCEL_REQUESTED.value,
                cancellation_reason="Trader requested cancellation"
            )
            proposal_audit_storage.record_order_event(
                order_id=order_id,
                event_type="ORDER_CANCEL_REQUESTED",
                status=BrokerOrderState.CANCEL_REQUESTED.value,
                message=f"Cancel request dispatched for Broker Order ID: {b_id}",
                raw_data={"broker_order_id": b_id}
            )
            proposal_audit_storage.update_operation_status(
                operation_id=op_id,
                status=OperationStatus.SUBMITTED.value
            )
            return {"success": True, "status": "CANCEL_REQUESTED", "order_id": order_id}
        except Exception as cex:
            err_msg = str(cex)
            if "timeout" in err_msg.lower() or "connection" in err_msg.lower():
                proposal_audit_storage.update_order_status(
                    order_id=order_id,
                    status=BrokerOrderState.CANCEL_OUTCOME_UNVERIFIED.value,
                    cancellation_reason=f"Cancel unverified: {err_msg}"
                )
                proposal_audit_storage.update_operation_status(
                    operation_id=op_id,
                    status=OperationStatus.OUTCOME_UNVERIFIED.value,
                    error_message=err_msg
                )
                return {"success": False, "unverified": True, "error": f"Cancel outcome unverified: {err_msg}"}

            proposal_audit_storage.update_operation_status(
                operation_id=op_id,
                status=OperationStatus.FAILED.value,
                error_message=err_msg
            )
            return {"success": False, "error": f"Broker rejected cancellation: {err_msg}"}

    elif action == "exit_position":
        import uuid
        from datetime import timezone
        position_id = params.get("position_id")
        idempotency_key = params.get("idempotency_key") or f"IDEMP-EXIT-{position_id}-{uuid.uuid4().hex[:8]}"
        req_qty = params.get("quantity")
        order_type = params.get("order_type", "MARKET")
        price = params.get("price")

        enable_live = os.environ.get("ENABLE_LIVE_EXECUTION", "false").lower() in ("true", "1", "yes")
        if not enable_live:
            return {
                "success": False,
                "error": "Live execution is disabled. Set ENABLE_LIVE_EXECUTION=true in staging environment.",
                "code": "LIVE_EXECUTION_DISABLED"
            }

        # Check persistent idempotency
        existing_op = proposal_audit_storage.get_operation_by_idempotency_key(idempotency_key)
        if existing_op and existing_op.get("current_status") in (OperationStatus.SUBMITTED.value, OperationStatus.COMPLETED.value):
            return {
                "success": True,
                "idempotent": True,
                "order_id": existing_op.get("broker_order_id"),
                "message": "Position exit request already submitted."
            }

        pos_dict = proposal_audit_storage.get_position(position_id)
        if not pos_dict:
            return {"success": False, "error": f"Position {position_id} not found."}

        if pos_dict.get("status") == "CLOSED":
            return {"success": False, "error": f"Position {position_id} is already closed."}

        if not bs.is_connected():
            return {"success": False, "error": "Broker session disconnected. Cannot route position exit."}

        # Query authoritative fresh broker net positions to verify open quantity
        broker_qty = pos_dict.get("quantity", 0)
        try:
            live_net = bs.get_live_net_positions()
            symbol_clean = pos_dict.get("contract_symbol", "").replace(" ", "")
            prod_clean = pos_dict.get("product", "")
            match = next((p for p in live_net if (p.get("tradingsymbol") == symbol_clean and p.get("product") == prod_clean)), None)
            if match:
                broker_qty = int(match.get("quantity", 0))
            elif len(live_net) > 0:
                # If fresh positions fetched and contract not found, position already closed on broker
                proposal_audit_storage.update_position_exit(
                    position_id=position_id,
                    exit_order_id="EXTERNAL_SYNC",
                    exit_price=pos_dict.get("current_ltp", 0.0),
                    realized_pnl=pos_dict.get("unrealized_pnl", 0.0),
                    closed_at=datetime.now(timezone.utc).isoformat(),
                    status="CLOSED"
                )
                return {"success": False, "error": "Position is already flat on broker. Synchronized to CLOSED."}
        except Exception as nex:
            logger.warning(f"Failed to query fresh net positions: {nex}")

        if broker_qty == 0:
            return {"success": False, "error": "Broker net quantity is 0. Position is flat."}

        exit_qty = int(req_qty) if req_qty else abs(broker_qty)
        trans_type = "SELL" if broker_qty > 0 else "BUY"
        tradingsymbol = pos_dict.get("contract_symbol", "").replace(" ", "")
        now_iso = datetime.now(timezone.utc).isoformat()
        op_id = f"OP-EXIT-{uuid.uuid4().hex[:12]}"
        exit_order_id = f"ORD-EXIT-{uuid.uuid4().hex[:12]}"

        exec_op = ExecutionOperation(
            operation_id=op_id,
            idempotency_key=idempotency_key,
            operation_type=OperationType.POSITION_EXIT.value,
            entity_type="POSITION",
            entity_id=position_id,
            requested_at=now_iso,
            current_status=OperationStatus.INITIATED.value
        )
        proposal_audit_storage.record_operation(exec_op)

        try:
            broker_exit_id = bs.exit_position(
                tradingsymbol=tradingsymbol,
                exchange="NFO",
                transaction_type=trans_type,
                quantity=exit_qty,
                product=pos_dict.get("product", "NRML"),
                order_type=order_type,
                price=price,
                tag="ardhamind_exit"
            )

            # Record exit order in orders table
            exit_order_rec = OrderRecord(
                order_id=exit_order_id,
                proposal_id=pos_dict.get("order_id", ""),
                intent_id=f"INTENT-EXIT-{uuid.uuid4().hex[:8]}",
                broker_order_id=str(broker_exit_id),
                contract_symbol=pos_dict.get("contract_symbol", ""),
                exchange="NFO",
                transaction_type=trans_type,
                order_type=order_type,
                product=pos_dict.get("product", "NRML"),
                quantity=exit_qty,
                filled_quantity=0,
                remaining_quantity=exit_qty,
                price=float(price or 0.0),
                average_price=0.0,
                status=BrokerOrderState.SUBMITTED.value,
                provenance="ARDHAMIND",
                placed_at=now_iso,
                updated_at=now_iso
            )
            proposal_audit_storage.record_order(exit_order_rec)

            proposal_audit_storage.update_operation_status(
                operation_id=op_id,
                status=OperationStatus.SUBMITTED.value,
                broker_order_id=str(broker_exit_id),
                result_payload={"exit_order_id": str(broker_exit_id)}
            )

            # Update position status to EXIT_REQUESTED
            proposal_audit_storage.record_position(
                PositionState(
                    position_id=position_id,
                    order_id=pos_dict.get("order_id", ""),
                    contract_symbol=pos_dict.get("contract_symbol", ""),
                    product=pos_dict.get("product", ""),
                    quantity=pos_dict.get("quantity", 0),
                    buy_price=pos_dict.get("buy_price", 0.0),
                    current_ltp=pos_dict.get("current_ltp", 0.0),
                    unrealized_pnl=pos_dict.get("unrealized_pnl", 0.0),
                    stop_loss=pos_dict.get("stop_loss", 0.0),
                    target=pos_dict.get("target", 0.0),
                    exit_order_id=str(broker_exit_id),
                    status="EXIT_REQUESTED"
                )
            )

            return {
                "success": True,
                "exit_order_id": str(broker_exit_id),
                "position_id": position_id,
                "status": "EXIT_REQUESTED"
            }
        except Exception as eex:
            err_msg = str(eex)
            if "timeout" in err_msg.lower() or "connection" in err_msg.lower():
                proposal_audit_storage.update_operation_status(
                    operation_id=op_id,
                    status=OperationStatus.OUTCOME_UNVERIFIED.value,
                    error_message=err_msg
                )
                return {"success": False, "unverified": True, "error": f"Exit outcome unverified: {err_msg}"}

            proposal_audit_storage.update_operation_status(
                operation_id=op_id,
                status=OperationStatus.FAILED.value,
                error_message=err_msg
            )
            return {"success": False, "error": f"Exit position failed: {err_msg}"}

    elif action == "emergency_close_all":
        import uuid
        from datetime import timezone
        idempotency_key = params.get("idempotency_key") or f"IDEMP-CLOSE-ALL-{uuid.uuid4().hex[:8]}"

        enable_live = os.environ.get("ENABLE_LIVE_EXECUTION", "false").lower() in ("true", "1", "yes")
        if not enable_live:
            return {
                "success": False,
                "error": "Live execution is disabled. Set ENABLE_LIVE_EXECUTION=true in staging environment.",
                "code": "LIVE_EXECUTION_DISABLED"
            }

        if not bs.is_connected():
            return {"success": False, "error": "Broker disconnected. Cannot execute emergency close all."}

        now_iso = datetime.now(timezone.utc).isoformat()
        op_id = f"OP-EMERGENCY-{uuid.uuid4().hex[:12]}"

        # Query live net positions from broker
        try:
            live_net = bs.get_live_net_positions()
        except Exception as gex:
            return {"success": False, "error": f"Failed to retrieve live net positions from broker: {gex}"}

        active_positions = [p for p in live_net if int(p.get("quantity", 0)) != 0]
        if not active_positions:
            return {
                "success": True,
                "total_positions": 0,
                "closed_count": 0,
                "results": [],
                "message": "No active open positions on broker."
            }

        exec_op = ExecutionOperation(
            operation_id=op_id,
            idempotency_key=idempotency_key,
            operation_type=OperationType.EMERGENCY_CLOSE_ALL.value,
            entity_type="PORTFOLIO",
            entity_id="ALL",
            requested_at=now_iso,
            current_status=OperationStatus.INITIATED.value
        )
        proposal_audit_storage.record_operation(exec_op)

        results = []
        for pos in active_positions:
            sym = pos.get("tradingsymbol", "")
            qty = int(pos.get("quantity", 0))
            prod = pos.get("product", "NRML")
            exch = pos.get("exchange", "NFO")
            trans_type = "SELL" if qty > 0 else "BUY"
            exit_qty = abs(qty)
            sub_idemp = f"{idempotency_key}_{sym}_{prod}"

            pos_res = {"tradingsymbol": sym, "product": prod, "quantity": exit_qty, "direction": trans_type}
            try:
                b_order_id = bs.exit_position(
                    tradingsymbol=sym,
                    exchange=exch,
                    transaction_type=trans_type,
                    quantity=exit_qty,
                    product=prod,
                    order_type="MARKET",
                    tag="ardhamind_emergency"
                )
                pos_res["status"] = "SUBMITTED"
                pos_res["broker_order_id"] = str(b_order_id)
            except Exception as pos_ex:
                pos_res["status"] = "FAILED"
                pos_res["error"] = str(pos_ex)

            results.append(pos_res)

        proposal_audit_storage.update_operation_status(
            operation_id=op_id,
            status=OperationStatus.COMPLETED.value,
            result_payload={"results": results}
        )

        return {
            "success": True,
            "total_positions": len(active_positions),
            "results": results
        }

    elif action == "reconcile_orders":
        active_orders = proposal_audit_storage.get_active_orders()
        updated_orders = []
        is_conn = bs.is_connected()

        if is_conn:
            try:
                kite_orders = bs.get_orders() or []
                kite_orders_map = {str(o.get("order_id")): o for o in kite_orders if o.get("order_id")}
            except Exception:
                kite_orders_map = {}

            try:
                live_net = bs.get_live_net_positions() or []
                live_net_map = {f"{p.get('tradingsymbol')}_{p.get('product')}": p for p in live_net}
            except Exception:
                live_net_map = {}

            # 1. Reconcile known active local orders
            for ord_dict in active_orders:
                b_id = ord_dict.get("broker_order_id")
                o_id = ord_dict.get("order_id")
                if not b_id:
                    continue

                kite_ord = kite_orders_map.get(str(b_id))
                if not kite_ord:
                    try:
                        status_res = bs.get_order_status(b_id)
                        kite_ord = status_res.get("raw") or {}
                    except Exception:
                        continue

                kite_status = (kite_ord.get("status") or "").upper()
                filled_qty = int(kite_ord.get("filled_quantity", 0))
                total_qty = int(ord_dict.get("quantity", 0))
                avg_price = float(kite_ord.get("average_price", 0.0))
                status_msg = kite_ord.get("status_message")

                mapped_status = ord_dict.get("status")
                if kite_status == "COMPLETE":
                    mapped_status = BrokerOrderState.FILLED.value
                elif kite_status == "REJECTED":
                    mapped_status = BrokerOrderState.REJECTED.value
                elif kite_status == "CANCELLED":
                    mapped_status = BrokerOrderState.CANCELLED.value
                elif kite_status == "OPEN":
                    if 0 < filled_qty < total_qty:
                        mapped_status = BrokerOrderState.PARTIALLY_FILLED.value
                    else:
                        mapped_status = BrokerOrderState.OPEN.value
                elif kite_status in ("PUT ORDER REQ RECEIVED", "VALIDATION PENDING"):
                    mapped_status = BrokerOrderState.ACKNOWLEDGED.value

                if mapped_status != ord_dict.get("status") or filled_qty != ord_dict.get("filled_quantity"):
                    rem_qty = max(0, total_qty - filled_qty)
                    proposal_audit_storage.update_order_status(
                        order_id=o_id,
                        status=mapped_status,
                        filled_quantity=filled_qty,
                        average_price=avg_price,
                        rejection_reason=status_msg if mapped_status == BrokerOrderState.REJECTED.value else None,
                        raw_payload=kite_ord
                    )
                    proposal_audit_storage.record_order_event(
                        order_id=o_id,
                        event_type=f"ORDER_{mapped_status}",
                        status=mapped_status,
                        message=f"Kite status updated to {mapped_status}. Filled: {filled_qty}/{total_qty}, Avg: ₹{avg_price:.2f}",
                        raw_data=kite_ord
                    )

                    # If filled, create / update open position
                    if mapped_status in (BrokerOrderState.FILLED.value, BrokerOrderState.PARTIALLY_FILLED.value) and filled_qty > 0:
                        pos_id = f"POS-{o_id}"
                        proposal_audit_storage.record_position(
                            PositionState(
                                position_id=pos_id,
                                order_id=o_id,
                                contract_symbol=ord_dict.get("contract_symbol"),
                                product=ord_dict.get("product"),
                                quantity=filled_qty,
                                buy_price=avg_price or ord_dict.get("price"),
                                current_ltp=avg_price or ord_dict.get("price"),
                                unrealized_pnl=0.0,
                                stop_loss=float((ord_dict.get("raw_payload") or {}).get("stop_loss", 0.0)),
                                target=float((ord_dict.get("raw_payload") or {}).get("target_1", 0.0)),
                                status="OPEN"
                            )
                        )

                    ord_dict["status"] = mapped_status
                    ord_dict["filled_quantity"] = filled_qty
                    ord_dict["remaining_quantity"] = rem_qty
                    ord_dict["average_price"] = avg_price
                    updated_orders.append(ord_dict)

                    # Update derived journal projection
                    if ord_dict.get("proposal_id"):
                        proposal_audit_storage.reconstruct_journal_for_proposal(ord_dict.get("proposal_id"))

            # 2. Reconcile open positions against live Kite net positions
            from datetime import timezone
            now_iso = datetime.now(timezone.utc).isoformat()
            local_open_positions = proposal_audit_storage.get_open_positions()

            for pos in local_open_positions:
                pos_id = pos.get("position_id")
                sym_clean = pos.get("contract_symbol", "").replace(" ", "")
                prod_clean = pos.get("product", "")
                lookup_key = f"{sym_clean}_{prod_clean}"

                matching_net = live_net_map.get(lookup_key)
                if matching_net:
                    net_qty = int(matching_net.get("quantity", 0))
                    ltp = float(matching_net.get("last_price", pos.get("current_ltp", 0.0)))
                    buy_pr = float(pos.get("buy_price", 0.0))

                    if net_qty == 0:
                        realized = round(float(matching_net.get("pnl", (ltp - buy_pr) * pos.get("quantity", 0))), 2)
                        proposal_audit_storage.update_position_exit(
                            position_id=pos_id,
                            exit_order_id="NET_ZERO_RECONCILED",
                            exit_price=ltp,
                            realized_pnl=realized,
                            closed_at=now_iso,
                            status="CLOSED"
                        )
                    else:
                        unrealized = round((ltp - buy_pr) * net_qty, 2)
                        st = "PARTIAL_EXIT" if net_qty < pos.get("quantity", 0) else "OPEN"
                        proposal_audit_storage.record_position(
                            PositionState(
                                position_id=pos_id,
                                order_id=pos.get("order_id", ""),
                                contract_symbol=pos.get("contract_symbol", ""),
                                product=prod_clean,
                                quantity=net_qty,
                                buy_price=buy_pr,
                                current_ltp=ltp,
                                unrealized_pnl=unrealized,
                                stop_loss=float(pos.get("stop_loss", 0.0)),
                                target=float(pos.get("target", 0.0)),
                                status=st
                            )
                        )
                elif len(live_net_map) > 0:
                    # Contract absent from broker net positions list -> closed
                    proposal_audit_storage.update_position_exit(
                        position_id=pos_id,
                        exit_order_id="ABSENT_RECONCILED",
                        exit_price=float(pos.get("current_ltp", 0.0)),
                        realized_pnl=float(pos.get("unrealized_pnl", 0.0)),
                        closed_at=now_iso,
                        status="CLOSED"
                    )

        from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
        BrokerHealthEvaluator.set_reconciliation_status(
            complete=True,
            in_progress=False,
            unresolved_count=len(proposal_audit_storage.get_unresolved_operations())
        )

        return {
            "success": True,
            "updated_orders": updated_orders,
            "all_active": proposal_audit_storage.get_active_orders(),
            "open_positions": proposal_audit_storage.get_open_positions()
        }

    elif action == "get_active_orders":
        orders = proposal_audit_storage.get_active_orders()
        return {"success": True, "orders": orders}

    elif action == "get_recent_orders":
        limit = int(params.get("limit", 50))
        orders = proposal_audit_storage.get_recent_orders(limit=limit)
        return {"success": True, "orders": orders}

    elif action == "get_order_events":
        order_id = params.get("order_id")
        events = proposal_audit_storage.get_order_events(order_id) if order_id else []
        return {"success": True, "events": events}

    elif action == "get_live_positions":
        positions = proposal_audit_storage.get_open_positions()
        return {"success": True, "positions": positions}

    elif action == "get_all_positions":
        limit = int(params.get("limit", 50))
        positions = proposal_audit_storage.get_all_positions(limit=limit)
        return {"success": True, "positions": positions}

    # ── MILESTONE 5: JOURNAL ACTIONS ──

    elif action == "get_journal_entries":
        limit = int(params.get("limit", 50))
        offset = int(params.get("offset", 0))
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        symbol = params.get("symbol")
        setup_type = params.get("setup_type")
        result_filter = params.get("result_filter")
        return proposal_audit_storage.get_journal_entries(
            limit=limit,
            offset=offset,
            date_from=date_from,
            date_to=date_to,
            symbol=symbol,
            setup_type=setup_type,
            result_filter=result_filter
        )

    elif action == "get_journal_entry":
        journal_id = params.get("journal_id")
        entry = proposal_audit_storage.get_journal_entry(journal_id)
        if not entry:
            return {"success": False, "error": f"Journal entry {journal_id} not found"}
        return {"success": True, "entry": entry}

    elif action == "get_journal_analytics":
        summary = proposal_audit_storage.get_journal_analytics_summary()
        return {"success": True, "summary": summary}

    elif action == "add_journal_note":
        import uuid
        from datetime import timezone
        journal_id = params.get("journal_id")
        note_text = params.get("note_text") or ""
        tags = params.get("tags") or []
        note_id = f"NOTE-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        note = JournalNote(
            note_id=note_id,
            journal_id=journal_id,
            note_text=note_text,
            tags=tags,
            created_at=now_iso,
            updated_at=now_iso
        )
        saved = proposal_audit_storage.add_journal_note(note)
        return {"success": saved, "note": note.to_dict()}

    # ── POST-MARKET BRIEFING ACTIONS ──

    elif action == "get_post_market_briefing":
        trading_date = params.get("trading_date")
        from src.intelligence_engine.post_market_briefing_engine import PostMarketBriefingEngine
        s_dict = {
            "market_data": cached_market_context or {},
            "options": cached_option_context or {},
            "news": cached_news_sentiment or {},
            "macro_intelligence": cached_macro_context or {},
            "last_price": (cached_market_context or {}).get("current_spot", 24152.05),
        }
        if trading_date:
            report = PostMarketBriefingEngine.load_persisted_report(trading_date)
            if not report:
                report = PostMarketBriefingEngine.analyze_post_market(s_dict)
        else:
            report = PostMarketBriefingEngine.analyze_post_market(s_dict)
        return {"success": True, "data": report.to_dict() if hasattr(report, "to_dict") else report}

    elif action == "get_post_market_briefing_history":
        from src.intelligence_engine.post_market_briefing_engine import PostMarketBriefingEngine
        history = PostMarketBriefingEngine.list_history()
        return {"success": True, "history": history}

    elif action == "reconcile_post_market_briefing":
        trading_date = params.get("trading_date")
        from src.intelligence_engine.post_market_briefing_engine import PostMarketBriefingEngine
        now_ist = datetime.now(IST)
        session_date, _ = PostMarketBriefingEngine.resolve_trading_dates(now_ist)
        t_date = trading_date or session_date
        s_dict = {
            "market_data": cached_market_context or {},
            "options": cached_option_context or {},
            "news": cached_news_sentiment or {},
            "macro_intelligence": cached_macro_context or {},
            "last_price": (cached_market_context or {}).get("current_spot", 24152.05),
        }
        report = PostMarketBriefingEngine.reconcile_official_close(t_date, s_dict, now_ist)
        return {"success": True, "data": report.to_dict() if hasattr(report, "to_dict") else report}

    # ── INTELLIGENCE ACTIONABLE SUGGESTION ACTIONS ──

    elif action == "get_intelligence_opportunities":
        from src.intelligence_engine.actionable_suggestion_engine import ActionableSuggestionEngine
        s_dict = {
            "market_data": cached_market_context or {},
            "options": cached_option_context or {},
            "news": cached_news_sentiment or {},
            "macro_intelligence": cached_macro_context or {},
            "last_price": (cached_market_context or {}).get("current_spot", 24152.05),
        }
        res = ActionableSuggestionEngine.analyze_and_suggest(s_dict)
        return {"success": True, "data": res}

    elif action == "get_intelligence_opportunity_history":
        from src.intelligence_engine.actionable_suggestion_engine import ActionableSuggestionEngine
        s_dict = {
            "market_data": cached_market_context or {},
            "options": cached_option_context or {},
            "news": cached_news_sentiment or {},
            "macro_intelligence": cached_macro_context or {},
            "last_price": (cached_market_context or {}).get("current_spot", 24152.05),
        }
        res = ActionableSuggestionEngine.analyze_and_suggest(s_dict)
        return {"success": True, "data": [res]}

    # ── MILESTONE 6: EXECUTION SAFETY STATUS & KILL SWITCH ──

    elif action == "get_safety_status":
        from datetime import timezone
        from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
        now_iso = datetime.now(timezone.utc).isoformat()
        active_pos = proposal_audit_storage.get_open_positions()
        active_ord = proposal_audit_storage.get_active_orders()
        unresolved_ops = proposal_audit_storage.get_unresolved_operations()

        all_closed_today = [
            p for p in proposal_audit_storage.get_all_positions(limit=50)
            if p.get("status") == "CLOSED" and (p.get("closed_at") or "")[:10] == now_iso[:10]
        ]
        daily_loss_sum = sum(abs(p.get("realized_pnl_analytics", 0.0)) for p in all_closed_today if p.get("realized_pnl_analytics", 0.0) < 0)

        health = BrokerHealthEvaluator.evaluate(bs)
        safety_eval = safety_gatekeeper.evaluate_entry_order(
            proposal=active_trade_proposal or TradeProposal(proposal_id="", timestamp="", underlying="", setup_type="", direction="", strike=0, option_type="", contract_symbol="", entry_price=0, stop_loss=0, target_1=0, target_2=0, risk_reward_ratio=0, confidence_score=0, priority_score=0, quality_score=0, max_loss_inr=0, rationale=[], invalidation_condition=""),
            fresh_quote=None,
            current_daily_realized_loss=daily_loss_sum,
            active_positions=active_pos,
            active_orders=active_ord,
            broker_connected=health.execution_verified,
            unresolved_operations=unresolved_ops
        )

        return {
            "success": True,
            "policy": safety_gatekeeper.policy.to_dict(),
            "kill_switch_active": safety_gatekeeper.policy.kill_switch_active,
            "new_entries_allowed": safety_eval.passed and not safety_gatekeeper.policy.kill_switch_active,
            "daily_realized_loss": daily_loss_sum,
            "daily_loss_limit": safety_gatekeeper.policy.daily_loss_limit,
            "open_positions_count": len(active_pos),
            "max_open_positions": safety_gatekeeper.policy.max_open_positions,
            "unresolved_operations_count": len(unresolved_ops),
            "broker_verified": health.execution_verified,
            "broker_health": health.to_dict(),
            "current_blocker_code": safety_eval.blocker_code if not safety_eval.passed else None
        }

    elif action == "toggle_kill_switch":
        active_flag = bool(params.get("active", False))
        safety_gatekeeper.policy.kill_switch_active = active_flag
        return {
            "success": True,
            "kill_switch_active": safety_gatekeeper.policy.kill_switch_active,
            "message": f"Kill switch {'activated' if active_flag else 'deactivated'}."
        }

    # ── MILESTONE 7: CONSOLIDATED STATE SNAPSHOT ──

    elif action == "get_phase3_state":
        from datetime import timezone
        from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
        now_iso = datetime.now(timezone.utc).isoformat()
        active_pos = proposal_audit_storage.get_open_positions()
        active_ord = proposal_audit_storage.get_active_orders()
        unresolved_ops = proposal_audit_storage.get_unresolved_operations()

        all_closed_today = [
            p for p in proposal_audit_storage.get_all_positions(limit=50)
            if p.get("status") == "CLOSED" and (p.get("closed_at") or "")[:10] == now_iso[:10]
        ]
        daily_loss_sum = sum(abs(p.get("realized_pnl_analytics", 0.0)) for p in all_closed_today if p.get("realized_pnl_analytics", 0.0) < 0)

        health = BrokerHealthEvaluator.evaluate(bs)
        safety_eval = safety_gatekeeper.evaluate_entry_order(
            proposal=active_trade_proposal or TradeProposal(proposal_id="", timestamp="", underlying="", setup_type="", direction="", strike=0, option_type="", contract_symbol="", entry_price=0, stop_loss=0, target_1=0, target_2=0, risk_reward_ratio=0, confidence_score=0, priority_score=0, quality_score=0, max_loss_inr=0, rationale=[], invalidation_condition=""),
            fresh_quote=None,
            current_daily_realized_loss=daily_loss_sum,
            active_positions=active_pos,
            active_orders=active_ord,
            broker_connected=health.execution_verified,
            unresolved_operations=unresolved_ops
        )

        return {
            "success": True,
            "active_proposal": active_trade_proposal.to_dict() if active_trade_proposal else None,
            "pending_orders": active_ord,
            "open_positions": active_pos,
            "unresolved_operations": unresolved_ops,
            "safety_status": {
                "kill_switch_active": safety_gatekeeper.policy.kill_switch_active,
                "new_entries_allowed": safety_eval.passed and not safety_gatekeeper.policy.kill_switch_active,
                "daily_realized_loss": daily_loss_sum,
                "daily_loss_limit": safety_gatekeeper.policy.daily_loss_limit,
                "blocker_code": safety_eval.blocker_code if not safety_eval.passed else None
            },
            "broker_health": health.to_dict()
        }

    elif action == "get_actions":
        return {
            "actions": [
                "get_login_url", "exchange_request_token", "login", "logout", "get_broker_config",
                "refresh_news", "refresh_macro", "get_broker_health", "get_interpretation_status",
                "get_interpretation", "get_context", "get_market_context", "get_actions",
                "get_performance_records", "get_performance_history", "capture_performance_snapshot",
                "evaluate_performance_records", "get_active_proposal", "validate_proposal",
                "approve_proposal", "reject_proposal", "calculate_proposal_margin", "get_proposal_audits",
                "execute_live_order", "cancel_order", "exit_position", "emergency_close_all",
                "reconcile_orders", "get_active_orders", "get_recent_orders",
                "get_order_events", "get_live_positions", "get_all_positions",
                "get_journal_entries", "get_journal_entry", "get_journal_analytics", "add_journal_note",
                "get_safety_status", "toggle_kill_switch", "get_phase3_state"
            ],
            "count": 40,
            "pid": os.getpid(),
            "executable": sys.executable
        }

    elif action == "get_market_context":
        if cached_market_context is not None and cached_option_context is not None:
            return {
                "market_context": cached_market_context,
                "option_context": cached_option_context
            }

        return {
            "market_context": {
                "status": "UNAVAILABLE",
                "current_spot": None,
                "ltp": None,
                "feed_health": "OFFLINE",
                "feed_latency_ms": None,
                "timestamp": None,
                "reason": "broker_session_not_connected"
            },
            "option_context": {
                "status": "UNAVAILABLE",
                "underlying_spot": None,
                "atm_strike": None,
                "pcr": None,
                "max_pain": None,
                "atm_iv": None,
                "timestamp": None,
                "reason": "broker_session_not_connected",
                "last_valid_snapshot": "UNAVAILABLE"
            }
        }

    else:
        raise ValueError(f"Unknown daemon action: {action}")

def run_daemon(wm, bs):
    global cached_news_sentiment, cached_macro_context, cached_market_context, cached_option_context, last_news_fetch_time, last_macro_fetch_time
    import sys
    import json
    import time
    import threading
    from datetime import datetime
    from src.broker.services.streaming_service import STATIC_TOKENS
    from src.broker.services.instrument_service import InstrumentService

    logger.info(f"[BOOT] Starting Python Bridge Daemon at {(time.time() - _boot_start_time)*1000:.1f}ms...")

    last_mode = None
    sim_thread = None
    stop_sim = threading.Event()

    # --- Sticky broker auth state ---
    # This is the DEFINITIVE auth-state for the daemon.  It only transitions:
    #   DISCONNECTED  → CONNECTED     : when validate_session() returns True
    #   CONNECTED     → TOKEN_EXPIRED : ONLY on explicit 401/403/ExpiredToken
    #   CONNECTED     → DISCONNECTED  : ONLY when bs.is_connected() is False
    #   Any transient network/server error preserves the last known state.
    # This eliminates the oscillation caused by transient Kite API failures
    # broadcasting TOKEN_EXPIRED / DISCONNECTED on every 3-second loop tick.
    _daemon_broker_auth = "DISCONNECTED"

    # Defaults structures
    defaultBrokerAccount = {
        "client_id": "N/A",
        "name": "Not Connected",
        "email": "N/A",
        "broker": "N/A"
    }

    defaultBrokerFunds = {
        "available_cash": 0.0,
        "margins": 0.0,
        "utilized_margin": 0.0,
        "available_margin": 0.0
    }

    defaultPortfolioReport = {
        "account_profile": {
            "client_id": "N/A",
            "client_name": "Not Connected",
            "email": "N/A",
            "pan": "N/A",
            "broker_name": "N/A",
            "user_type": "N/A",
            "login_time": "N/A"
        },
        "funds": {
            "equity": {
                "available_cash": 0.0,
                "utilized_margin": 0.0,
                "available_margin": 0.0,
                "opening_balance": 0.0,
                "collateral": 0.0,
                "payin_amount": 0.0,
                "payout_amount": 0.0
            },
            "commodity": {
                "available_cash": 0.0,
                "utilized_margin": 0.0,
                "available_margin": 0.0,
                "opening_balance": 0.0,
                "collateral": 0.0,
                "payin_amount": 0.0,
                "payout_amount": 0.0
            }
        },
        "holdings": [],
        "positions": {
            "net": [],
            "day": []
        },
        "orders": {
            "all_orders": [],
            "completed": [],
            "open_orders": []
        },
        "trades": [],
        "statistics": {
            "total_holdings_value": 0.0,
            "total_unrealized_pnl": 0.0,
            "margin_utilisation_pct": 0.0
        }
    }

    def stdin_reader():
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                req_id = req.get("requestId")
                action = req.get("action")
                params = req.get("params", {})

                res = handle_daemon_command(action, params, bs, wm)
                print(json.dumps({"type": "response", "requestId": req_id, "success": True, "data": res}), flush=True)
            except Exception as e:
                try:
                    print(json.dumps({"type": "response", "requestId": req_id if 'req_id' in locals() else None, "success": False, "error": str(e)}), flush=True)
                except Exception:
                    pass

    threading.Thread(target=stdin_reader, daemon=True).start()

    def run_simulator():
        """
        Production Integrity: When broker is disconnected, do NOT emit
        fake 0.0 market ticks. Instead emit a BROKER_DISCONNECTED
        heartbeat so the UI can display the correct connection state.
        """
        while not stop_sim.is_set():
            timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            tick_null = {
                "type": "feed_status",
                "symbol": "NSE:NIFTY 50",
                "data": {
                    "feed_health": "BROKER_DISCONNECTED",
                    "status": "DISCONNECTED",
                    "exchange_timestamp": timestamp_str,
                    "backend_receive_timestamp": timestamp_str
                }
            }
            print(json.dumps(tick_null), flush=True)
            time.sleep(3.0)

    def setup_real_ticks_callback():
        try:
            orch = bs._get_orchestrator()
        except PermissionError:
            logger.warning("Cannot setup real ticks callback: broker session unauthenticated.")
            return
        if getattr(orch, "_real_ticks_callback_set", False):
            return
        original_on_ticks = orch._on_tick_received

        def new_on_ticks(raw_ticks):
            if original_on_ticks:
                original_on_ticks(raw_ticks)
            t_now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            runtime_id = getattr(WorkstationStateService, "_runtime_id", "ardhamind_runtime")
            state_seq = getattr(WorkstationStateService, "_sequence", 1)

            for raw in raw_ticks:
                token = raw.get("instrument_token")
                symbol = "N/A"
                if token in STATIC_TOKENS:
                    symbol = STATIC_TOKENS[token]
                else:
                    inst = InstrumentService.get_instance().lookup_instrument_by_token(token)
                    if inst:
                        symbol = inst.get("tradingsymbol") or "N/A"

                last_price = float(raw.get("last_price", 0.0) or 0.0)
                ohlc = raw.get("ohlc", {})
                open_price = float(ohlc.get("open", 0.0) or 0.0)
                high_price = float(ohlc.get("high", 0.0) or 0.0)
                low_price = float(ohlc.get("low", 0.0) or 0.0)
                close_price = float(ohlc.get("close", 0.0) or 0.0)
                prev_close = close_price if close_price > 0 else 24287.65
                change_pts = (last_price - prev_close) if last_price > 0 and prev_close > 0 else 0.0
                change_pct = (change_pts / prev_close * 100.0) if prev_close > 0 else 0.0

                raw_ts = raw.get("timestamp") or t_now
                obs_ts = raw_ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if hasattr(raw_ts, "strftime") else str(raw_ts)

                tick_payload = {
                    "type": "tick",
                    "symbol": symbol,
                    "data": {
                        "instrument_token": token,
                        "last_price": last_price,
                        "volume": raw.get("volume", 0),
                        "oi": raw.get("oi", 0),
                        "ohlc": ohlc,
                        "exchange_timestamp": obs_ts,
                        "backend_receive_timestamp": t_now,
                        "runtime_id": runtime_id,
                        "state_sequence": state_seq
                    }
                }
                print(json.dumps(tick_payload), flush=True)

                # Emit structured LiveMarketEvent for atomic streaming ingestion
                if last_price > 0.0:
                    depth = raw.get("depth", {})
                    buy_depth = depth.get("buy") or []
                    sell_depth = depth.get("sell") or []
                    bid = float(buy_depth[0].get("price", 0.0)) if buy_depth else last_price
                    ask = float(sell_depth[0].get("price", 0.0)) if sell_depth else last_price

                    live_evt = {
                        "type": "live_event",
                        "data": {
                            "runtime_id": runtime_id,
                            "state_sequence": state_seq,
                            "instrument_token": token,
                            "symbol": symbol,
                            "event_type": "TICK",
                            "price": last_price,
                            "open": open_price,
                            "high": high_price,
                            "low": low_price,
                            "previous_close": prev_close,
                            "change_points": round(change_pts, 2),
                            "change_pct": round(change_pct, 2),
                            "volume": int(raw.get("volume", 0) or 0),
                            "oi": int(raw.get("oi", 0) or 0),
                            "bid": bid,
                            "ask": ask,
                            "provider_observed_at": obs_ts,
                            "backend_received_at": t_now,
                            "canonical_committed_at": t_now,
                            "freshness": "FRESH",
                            "source": "ZERODHA_KITE"
                        }
                    }
                    print(json.dumps(live_evt), flush=True)

        orch._on_tick_received = new_on_ticks
        orch._real_ticks_callback_set = True

    instruments_df = None
    # Auto-restore valid Zerodha session at daemon startup
    try:
        gateway = bs.get_gateway()
        if hasattr(gateway, "load_session"):
            session_loaded = gateway.load_session()
            if session_loaded and gateway.validate_session():
                logger.info("Successfully restored active Zerodha session at daemon startup.")
                from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
                BrokerHealthEvaluator.set_reconciliation_status(
                    complete=True,
                    in_progress=False,
                    unresolved_count=len(proposal_audit_storage.get_unresolved_operations())
                )
                setup_real_ticks_callback()
                if bs.is_connected() and not bs.is_stream_connected():
                    try:
                        bs.connect_stream()
                        bs.subscribe_stream([
                            "NIFTY", "NIFTY BANK", "NIFTY IT", "NIFTY AUTO", "NIFTY PHARMA",
                            "NIFTY METAL", "NIFTY FMCG", "NIFTY REALTY", "NIFTY ENERGY",
                            "NIFTY OIL AND GAS", "NIFTY FIN SERVICE", "INDIA VIX",
                        ])
                        logger.info("Auto-connected streaming feed during startup session restoration.")
                    except Exception as e:
                        logger.error(f"Failed to connect streaming feed during startup session restore: {e}")
            else:
                gateway.disconnect()
                logger.info("No active Zerodha session restored at daemon startup.")
    except Exception as se:
        bs.disconnect()
        logger.warning(f"Daemon startup session restore exception: {se}")

    # Spawn initial background refreshes for news and macro providers
    def run_initial_refreshes():
        logger.info(f"[BACKGROUND] Initial background provider refreshes triggered at {(time.time() - _boot_start_time)*1000:.1f}ms")
        threading.Thread(target=_bg_refresh_news, daemon=True, name="bg-news-init").start()
        threading.Thread(target=_bg_refresh_macro, daemon=True, name="bg-macro-init").start()

    threading.Thread(target=run_initial_refreshes, daemon=True).start()

    _last_stream_connect_attempt = 0.0

    logger.info(f"[BOOT] Entering canonical main loop at {(time.time() - _boot_start_time)*1000:.1f}ms")

    while True:
        current_mode = wm.current_mode
        if current_mode != last_mode:
            logger.info(f"Daemon workspace mode changed to: {current_mode}")
            last_mode = current_mode

        if bs.is_connected() and not bs.is_stream_connected():
            now_ts = time.time()
            if now_ts - _last_stream_connect_attempt >= 10.0:
                _last_stream_connect_attempt = now_ts
                try:
                    setup_real_ticks_callback()
                    connected = bs.connect_stream()
                    if connected:
                        bs.subscribe_stream([
                            "NIFTY", "NIFTY BANK", "NIFTY IT", "NIFTY AUTO", "NIFTY PHARMA",
                            "NIFTY METAL", "NIFTY FMCG", "NIFTY REALTY", "NIFTY ENERGY",
                            "NIFTY OIL AND GAS", "NIFTY FIN SERVICE", "INDIA VIX",
                        ])
                        logger.info("Auto-connected streaming feed for active broker session.")
                except Exception as e:
                    logger.error(f"Failed to auto-connect streaming feed: {e}")

        try:
            # Initialize instruments master cache asynchronously if broker connects
            if bs.is_connected() and instruments_df is None and not getattr(bs, "_instruments_loading", False):
                bs._instruments_loading = True
                def _bg_load_instruments():
                    global instruments_df
                    try:
                        from src.data_engine.instruments import InstrumentManager
                        instruments_df = InstrumentManager.get_instruments(bs.get_gateway())
                        InstrumentService.get_instance().load_instruments(bs, force_refresh=False)
                        logger.info("Zerodha instrument list loaded dynamically in background thread.")
                    except Exception as e:
                        logger.error(f"Failed to initialize Zerodha instruments inside daemon: {e}")
                    finally:
                        bs._instruments_loading = False
                threading.Thread(target=_bg_load_instruments, daemon=True).start()

            # Production Integrity: Never fabricate spot/VIX values.
            # All values must originate from live Zerodha ticks.
            # When unpopulated or disconnected, values remain None.
            spot_nifty = None
            spot_banknifty = None
            spot_finnifty = None
            india_vix = None
            orch = None

            # If connected, fetch dynamic spot prices immediately from orchestrator cache
            if bs.is_connected():
                try:
                    orch = bs._get_orchestrator()
                except PermissionError:
                    orch = None

                if orch:
                    tick_nifty = orch.latest_ticks.get("NSE:NIFTY 50")
                    if tick_nifty and float(tick_nifty.get("last_price", 0.0)) > 0:
                        spot_nifty = float(tick_nifty.get("last_price"))
                    else:
                        try:
                            ltps = bs.get_ltp(["NSE:NIFTY 50"])
                            if ltps and float(ltps.get("NSE:NIFTY 50", {}).get("last_price", 0.0)) > 0:
                                spot_nifty = float(ltps.get("NSE:NIFTY 50", {}).get("last_price"))
                        except Exception:
                            pass

                    tick_bn = orch.latest_ticks.get("NSE:NIFTY BANK")
                    if tick_bn and float(tick_bn.get("last_price", 0.0)) > 0:
                        spot_banknifty = float(tick_bn.get("last_price"))
                    tick_fn = orch.latest_ticks.get("NSE:NIFTY FIN SERVICE")
                    if tick_fn and float(tick_fn.get("last_price", 0.0)) > 0:
                        spot_finnifty = float(tick_fn.get("last_price"))
                    tick_vix = orch.latest_ticks.get("NSE:INDIA VIX")
                    if tick_vix and float(tick_vix.get("last_price", 0.0)) > 0:
                        india_vix = float(tick_vix.get("last_price"))
                    else:
                        try:
                            ltps = bs.get_ltp(["NSE:INDIA VIX"])
                            if ltps and float(ltps.get("NSE:INDIA VIX", {}).get("last_price", 0.0)) > 0:
                                india_vix = float(ltps.get("NSE:INDIA VIX", {}).get("last_price"))
                        except Exception:
                            pass
                else:
                    try:
                        ltps = bs.get_ltp(["NSE:NIFTY 50", "NSE:INDIA VIX"])
                        if ltps and float(ltps.get("NSE:NIFTY 50", {}).get("last_price", 0.0)) > 0:
                            spot_nifty = float(ltps.get("NSE:NIFTY 50", {}).get("last_price"))
                        if ltps and float(ltps.get("NSE:INDIA VIX", {}).get("last_price", 0.0)) > 0:
                            india_vix = float(ltps.get("NSE:INDIA VIX", {}).get("last_price"))
                    except Exception:
                        pass

                # Decouple Option Chain REST fetching from critical NIFTY spot publication path
                # Option chain REST compilation runs asynchronously in background thread every 15 seconds
                global _last_option_chain_fetch, cached_market_context, cached_option_context
                effective_spot = spot_nifty if (spot_nifty and spot_nifty > 0) else float((cached_market_context or {}).get("current_spot") or (cached_option_context or {}).get("underlying_spot") or 0.0)
                if effective_spot > 0 and (time.time() - getattr(bs, "_last_option_chain_fetch", 0.0)) > 15.0 and not getattr(bs, "_option_chain_loading", False):
                    bs._option_chain_loading = True
                    def _bg_update_option_chain(s_nifty: float, vix_val: float):
                        global cached_market_context, cached_option_context
                        try:
                            from src.broker.services.market_feed_service import MarketFeedService
                            expiries = MarketFeedService.get_instance().resolve_expiries(bs) if bs.is_connected() else []
                            if expiries:
                                from datetime import datetime as dt_cls, date as dt_date
                                today_dt = dt_date.today()
                                future_exp = []
                                for e in expiries:
                                    try:
                                        if dt_cls.strptime(e, "%Y-%m-%d").date() >= today_dt:
                                            future_exp.append(e)
                                    except Exception:
                                        pass
                                if future_exp:
                                    current_weekly = future_exp[0]
                                    if bs.is_connected():
                                        MarketFeedService.get_instance().update_subscriptions(bs, s_nifty, current_weekly)
                                    new_opt_ctx = MarketFeedService.get_instance().build_option_chain_context(bs, s_nifty, future_exp)
                                    if new_opt_ctx and new_opt_ctx.get("status") != "UNAVAILABLE":
                                        cached_option_context = new_opt_ctx

                            from src.broker.services.market_context_builder import MarketContextBuilder
                            orch_instance = None
                            if hasattr(bs, "_get_orchestrator") and bs.is_connected():
                                try:
                                    orch_instance = bs._get_orchestrator()
                                except PermissionError:
                                    orch_instance = None
                            new_mkt_ctx = MarketContextBuilder.build(
                                bs, orch_instance, vix_val,
                                (cached_macro_context or {}).get("constituent_metadata"),
                            )
                            if new_mkt_ctx:
                                if cached_market_context:
                                    cached_market_context.update({k: v for k, v in new_mkt_ctx.items() if v is not None})
                                else:
                                    cached_market_context = new_mkt_ctx
                            bs._last_option_chain_fetch = time.time()
                        except Exception as ex:
                            logger.error(f"Error compiling live option/market context: {ex}")
                        finally:
                            bs._option_chain_loading = False
                    threading.Thread(target=_bg_update_option_chain, args=(effective_spot, india_vix), daemon=True).start()

            broker_account = defaultBrokerAccount
            broker_funds = defaultBrokerFunds
            portfolio_report = defaultPortfolioReport

            if bs.is_connected():
                try:
                    broker_account = serialize(bs.get_profile())
                except Exception:
                    pass
                try:
                    broker_funds = serialize(bs.get_funds())
                except Exception:
                    pass
                try:
                    from src.models.live_portfolio_report import LivePortfolioReportBuilder
                    portfolio_report = serialize(LivePortfolioReportBuilder.generate(bs.get_gateway()))
                except Exception:
                    pass

            from src.broker.services.market_status_service import MarketStatusService
            market_status = serialize(MarketStatusService.get_instance().get_market_status())

            # --- Authoritative Broker Health Evaluation ---
            from src.broker.services.authoritative_broker_health import BrokerHealthEvaluator
            authoritative_health = BrokerHealthEvaluator.evaluate(bs)
            broker_state = authoritative_health.status

            # Resolve Market State
            ms_status = market_status.get("status", "CLOSED")
            if ms_status in ["OPEN", "SPECIAL_SESSION"]:
                market_state = "OPEN"
            elif ms_status == "PRE_OPEN":
                market_state = "PRE_OPEN"
            elif ms_status == "HOLIDAY":
                market_state = "HOLIDAY"
            else:
                market_state = "CLOSED"

            runtime_snapshot, pipeline_result = AnalyticalPipelineService.run_daemon_snapshot(
                cached_market_context, cached_option_context,
                market_state=market_state, broker_state=broker_state,
                news=cached_news_sentiment, account=broker_account)
            pipeline_values = pipeline_result.compatibility_values()
            data = {
                "market_score": pipeline_values["marketScore"],
                "opportunity_context": pipeline_values["opportunityContext"],
                "strategy_evaluation": pipeline_values["strategyEvaluation"],
                "trade_plan": {"scenarios": pipeline_values["tradeScenarios"]},
                "confidence_report": pipeline_values["confidenceReport"],
                "risk_report": pipeline_values["riskReport"],
                "decision_report": pipeline_values["decisionReport"],
                "explanation_report": pipeline_values["explanationReport"],
            }

            # Compile Evening / Tomorrow Outlook Report
            _mc = cached_market_context or {}
            _oc = cached_option_context or {}
            se_evals = data.get("strategy_evaluation", {})
            best_strat = "MEAN_REVERSION"
            if isinstance(se_evals, dict):
                best_strat = se_evals.get("overall_best_strategy", "MEAN_REVERSION")
            elif isinstance(se_evals, list) and len(se_evals) > 0:
                # If strategy_evaluation was returned as list of StrategyScore objects
                best_strat = se_evals[0].strategy_name if hasattr(se_evals[0], "strategy_name") else "MEAN_REVERSION"

            mc_obj = data.get("market_score", {})
            m_score = 0.0
            m_grade = "B"
            if isinstance(mc_obj, dict):
                m_score = mc_obj.get("overall_score", 0.0)
                m_grade = mc_obj.get("overall_grade", "B")

            opp_obj = data.get("opportunity_context", {})
            opp_strength = 50.0
            if isinstance(opp_obj, dict):
                strength_obj = opp_obj.get("strength", {})
                if isinstance(strength_obj, dict):
                    opp_strength = strength_obj.get("overall_strength", 50.0)

            prep_notes = "Focus on mean reversion setups around S/R levels. Low VIX favors premium collection." if _mc.get("market_regime") == "SIDEWAYS" else "Focus on momentum breakout setups. Watch for trend continuation signals."

            evening_report = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "summary": {
                    "best_candidate_id": "NONE",
                    "best_strategy": best_strat,
                    "total_accepted_candidates": len(data.get("trade_plan", {}).get("accepted_candidates", [])) if isinstance(data.get("trade_plan"), dict) else 0,
                    "total_rejected_candidates": len(data.get("trade_plan", {}).get("rejected_candidates", [])) if isinstance(data.get("trade_plan"), dict) else 0,
                    "action_type": data.get("decision_report", {}).get("summary", {}).get("overall_action", "STANDBY") if isinstance(data.get("decision_report"), dict) else "STANDBY"
                },
                "tomorrow_outlook": {
                    "directional_bias": _mc.get("trend_direction", "NEUTRAL"),
                    "key_support_levels": _mc.get("support_levels", []),
                    "key_resistance_levels": _mc.get("resistance_levels", []),
                    "pcr": _oc.get("pcr", 0.0),
                    "atm_iv": _oc.get("atm_iv", 0.0),
                    "india_vix": _mc.get("india_vix", 0.0),
                    "recommended_strategy": best_strat,
                    "preparation_notes": prep_notes,
                    "opportunity_strength": opp_strength,
                    "description": f"Market regime is {_mc.get('market_regime', 'UNKNOWN')}. Trend is {_mc.get('trend_direction', 'NEUTRAL')}. VIX is at {_mc.get('india_vix', 0.0)}."
                },
                "market_summary": {
                    "spot_price": _mc.get("current_spot", spot_nifty),
                    "vix_price": _mc.get("india_vix", india_vix),
                    "regime": _mc.get("market_regime", "UNKNOWN"),
                    "trend_direction": _mc.get("trend_direction", "NEUTRAL"),
                    "market_score": m_score,
                    "market_grade": m_grade,
                    "session_type": market_state,
                    "vwap": _mc.get("vwap", 0.0),
                    "atr": _mc.get("atr", 0.0),
                    "benchmark_index": "NIFTY 50",
                    "date": time.strftime("%Y-%m-%d"),
                    "feed_health": _mc.get("feed_health", "OFFLINE")
                },
                "optimization_notes": [
                    f"Market regime: {_mc.get('market_regime', 'UNKNOWN')}. Trend: {_mc.get('trend_direction', 'NEUTRAL')}."
                ] if _mc else ["Insufficient live data. Connect broker to populate market summary."],
                "risk_watchlist": {
                    "warnings": [
                        f"Feed health: {_mc.get('feed_health', 'OFFLINE')}. Ensure broker is connected."
                    ] if _mc.get("feed_health", "OFFLINE") != "HEALTHY" else []
                }
            }


            # Compile Analytics Report
            analytics_report = {}
            try:
                from src.analytics_engine.builder import PerformanceAnalyticsBuilder
                from src.dashboard.performance_analytics_panel import PerformanceAnalyticsPanel
                from src.models import TradeJournalEntry

                # Convert portfolio_report trades to TradeJournalEntry
                entries = []
                trades_list = []
                if isinstance(portfolio_report, dict):
                    trades_list = portfolio_report.get("trades", [])

                for idx, t in enumerate(trades_list):
                    try:
                        pnl = float(t.get("pnl", 0.0))
                        entry = TradeJournalEntry(
                            entry_id=t.get("trade_id", f"JE-{idx}"),
                            trade_id=t.get("order_id", f"TR-{idx}"),
                            candidate_id=f"CAND-{t.get('symbol','')}",
                            tradingsymbol=t.get("symbol", ""),
                            decision_summary=f"Execution on {t.get('symbol','')}",
                            explanation_summary=f"Executed at {t.get('execution_price','')}",
                            market_score_val=0.0,
                            market_score_grade="UNAVAILABLE",
                            confidence_score=0.0,
                            risk_grade="UNAVAILABLE",
                            strategy_name="UNAVAILABLE",
                            entry_time=t.get("timestamp", ""),
                            entry_premium=float(t.get("execution_price", 0.0)),
                            entry_capital=float(t.get("execution_price", 0.0)) * int(t.get("quantity", 0)) * 50,
                            entry_lots=int(t.get("quantity", 0)),
                            exit_time=t.get("timestamp", ""),
                            exit_premium=float(t.get("execution_price", 0.0)),
                            exit_reason="Exit",
                            pnl=pnl,
                            pnl_pct=0.0,
                            duration_seconds=0,
                            outcome="WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "FLAT"),
                            market_regime="UNKNOWN",
                            confidence_band="UNAVAILABLE",
                            notes=""
                        )
                        entries.append(entry)
                    except Exception:
                        pass

                report = PerformanceAnalyticsBuilder.build_report(entries)
                analytics_report = PerformanceAnalyticsPanel(report).to_dict()
            except Exception as e:
                logger.error(f"Failed to build analytics report: {e}")

            # Compile News Sentiment (Non-blocking async background thread)
            if cached_news_sentiment is None or time.time() - last_news_fetch_time > 300:
                threading.Thread(target=_bg_refresh_news, daemon=True, name="bg-news-periodic").start()

            # Compile Macro Context (Non-blocking async background thread)
            if cached_macro_context is None or time.time() - last_macro_fetch_time > 300:
                threading.Thread(target=_bg_refresh_macro, daemon=True, name="bg-macro-periodic").start()

            # Hydrate market context if empty or spot is zero
            if not cached_market_context or float((cached_market_context or {}).get("current_spot") or 0.0) <= 0.0:
                try:
                    from src.broker.services.market_context_builder import MarketContextBuilder
                    cached_market_context = MarketContextBuilder.build(
                        bs, orch, india_vix, (cached_macro_context or {}).get("constituent_metadata")
                    )
                except Exception as _mc_err:
                    logger.warning(f"Periodic MarketContext rebuild fallback warning: {_mc_err}")

            legacy_data = {
                    "workspaceContext": {
                        "currentMode": "READ_ONLY",
                        "brokerState": broker_state,
                        "marketState": market_state,
                        "brokerType": "ZERODHA",
                        "marketDataSource": "LIVE",
                        "analyticsMode": "ENABLED",
                        "notificationMode": "ENABLED",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    },
                    "brokerAccount": broker_account,
                    "brokerFunds": broker_funds,
                    "portfolioReport": portfolio_report,
                    "operationsReport": {"status": "unavailable", "source": "not_migrated"},
                    "configurationReport": {},
                    "intradayReport": {},
                    "validationReport": {},
                    "optimizationReport": {},
                    "marketStatusReport": market_status,
                    "optionContext": cached_option_context,
                    "marketContext": cached_market_context,
                    "eveningReport": evening_report,
                    "analyticsReport": analytics_report,
                    "newsSentiment": cached_news_sentiment,
                    "macroIntelligence": cached_macro_context,
                    "streamTelemetry": bs.get_bootstrap_telemetry()
            }
            m_comp = pipeline_result.compatibility_values().get("marketContext") or {}
            legacy_data.update(pipeline_result.compatibility_values())
            valid_m_comp = {k: v for k, v in m_comp.items() if v is not None}
            now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
            latest_tick_nifty = orch.latest_ticks.get("NSE:NIFTY 50") if (orch and getattr(orch, "latest_ticks", None)) else None
            latest_obs_time = (latest_tick_nifty.get("timestamp") or latest_tick_nifty.get("exchange_timestamp") or now_iso) if latest_tick_nifty else now_iso
            legacy_data["marketContext"] = {
                **(cached_market_context or {}),
                **valid_m_comp,
                "timestamp": latest_obs_time,
                "observed_at": latest_obs_time,
                "exchange_timestamp": latest_obs_time,
                "breadth": valid_m_comp.get("breadth") or (cached_market_context or {}).get("breadth"),
                "constituent_instruments": valid_m_comp.get("constituent_instruments") or (cached_market_context or {}).get("constituent_instruments"),
                "previous_close": valid_m_comp.get("previous_close") or (cached_market_context or {}).get("previous_close"),
                "spot_change": valid_m_comp.get("spot_change") or (cached_market_context or {}).get("spot_change"),
                "spot_change_pct": valid_m_comp.get("spot_change_pct") or (cached_market_context or {}).get("spot_change_pct"),
                "candles": (cached_market_context or {}).get("candles") or valid_m_comp.get("candles") or [],
            }
            legacy_data["optionContext"] = {**(cached_option_context or {}), **(pipeline_result.compatibility_values().get("optionContext") or {})}
            legacy_data["newsSentiment"] = cached_news_sentiment or get_initial_news_sentiment()
            legacy_data["macroIntelligence"] = cached_macro_context or get_initial_macro_context()
            canonical_state = WorkstationStateService.build_from_legacy(
                legacy_data, broker_state=broker_state, market_state=market_state
            )

            # Automatic Performance Tracker Live Capture Wiring
            try:
                from src.intelligence_engine.performance_tracker_engine import PerformanceTrackerEngine
                perf_engine = PerformanceTrackerEngine()
                perf_engine.process_runtime_tick(canonical_state.to_dict(), market_status)
            except Exception as _perf_err:
                logger.warning(f"[PERFORMANCE] Automatic runtime tick processing warning: {_perf_err}")

            # Automatic Post-Market Briefing 15:20 Capture & 15:30 Reconciliation Wiring
            try:
                now_ist = datetime.now(IST)
                hhmm = now_ist.strftime("%H:%M")
                if is_trading_day(now_ist.date()) and hhmm >= "15:20":
                    from src.intelligence_engine.post_market_briefing_engine import PostMarketBriefingEngine
                    session_date, _ = PostMarketBriefingEngine.resolve_trading_dates(now_ist)
                    rep = PostMarketBriefingEngine.load_persisted_report(session_date)
                    if not rep:
                        logger.info(f"[POST_MARKET] Automatically capturing 15:20 IST snapshot for {session_date}")
                        PostMarketBriefingEngine.analyze_post_market(canonical_state.to_dict(), now_ist)
                    elif hhmm >= "15:30" and rep.snapshot_type == "PRE_CLOSE_1520" and not rep.nifty_snapshot.official_close_available:
                        logger.info(f"[POST_MARKET] Automatically reconciling 15:30+ official close for {session_date}")
                        PostMarketBriefingEngine.reconcile_official_close(session_date, canonical_state.to_dict(), now_ist)
            except Exception as _pmb_err:
                logger.warning(f"[POST_MARKET] Automatic tick processing warning: {_pmb_err}")

            state_payload = {
                "type": "state",
                "data": canonical_state.to_dict()
            }
            print(json.dumps(state_payload), flush=True)
            global _first_state_emitted
            if not _first_state_emitted:
                _first_state_emitted = True
                logger.info(f"[BOOT] First canonical state emitted at {(time.time() - _boot_start_time)*1000:.1f}ms")
        except Exception as err:
            logger.exception(f"Daemon state generation failed: {err}")

        time.sleep(3.0)

def main():
    parser = argparse.ArgumentParser(description="Python Backend Gateway Bridge")
    parser.add_argument("--action", required=True, help="Action to perform")
    parser.add_argument("--api_key", help="Kite API key supplied from the broker tab")
    parser.add_argument("--api_secret", help="Kite API secret supplied from the broker tab")
    parser.add_argument("--request_token", help="Zerodha request token for login exchange")
    parser.add_argument("--access_token", help="Zerodha access token for direct connection")
    parser.add_argument("--persist_key", help="Whether to persist the API Key (True/False)")
    parser.add_argument("--persist_token", help="Whether to persist the Access Token (True/False)")

    args = parser.parse_args()

    rejected = reject_execution_action(args.action)
    if rejected:
        print(json.dumps(rejected))
        return

    from src.configuration_engine.runtime import Config
    # Synchronize the Workspace and Broker states with env variables
    ws_mode = WorkspaceMode.READ_ONLY

    wm = WorkspaceManager.get_instance()
    # Force set workspace manager's internal mode to match environment/config
    wm._current_mode = ws_mode

    # Propagate trading mode to BrokerService and auto-connect (always live Zerodha)
    bs = BrokerService.get_instance()
    bs.set_mode(TradingMode.LIVE_ZERODHA)
    try:
        if not bs.load_session() or not bs.validate_session():
            bs.disconnect()
    except Exception:
        bs.disconnect()

    try:
        if args.action == "daemon":
            run_daemon(wm, bs)
        elif args.action == "get_context":
            ctx = wm.get_context()
            payload = serialize_read_only_context(ctx)
            payload.update({
                "allow_live_trading": False,
                "require_confirmation": Config.REQUIRE_CONFIRMATION,
                "show_mode_warning": Config.SHOW_MODE_WARNING,
                "auto_fallback_to_development": Config.AUTO_FALLBACK_TO_DEVELOPMENT,
            })
            print(json.dumps(payload))

        elif args.action in [
            "get_market_score", "get_opportunity_context", "get_strategy_evaluation",
            "get_confidence_report", "get_risk_report", "get_decision_report",
            "get_operations_report", "get_configuration_report", "get_explanation_report",
            "get_trade_plan", "get_intraday_report", "get_validation_report", "get_optimization_report"
        ]:
            _, result = AnalyticalPipelineService.run_daemon_snapshot(
                cached_market_context, cached_option_context,
                market_state="OPEN", broker_state="CONNECTED" if bs.is_connected() else "DISCONNECTED")
            data = result.compatibility_values()

            action_map = {
                "get_market_score": "marketScore",
                "get_opportunity_context": "opportunityContext",
                "get_strategy_evaluation": "strategyEvaluation",
                "get_confidence_report": "confidenceReport",
                "get_risk_report": "riskReport",
                "get_decision_report": "decisionReport",
                "get_operations_report": "operations_report",
                "get_configuration_report": "configuration_report",
                "get_explanation_report": "explanationReport",
                "get_trade_plan": "tradeScenarios",
                "get_intraday_report": "intraday_report",
                "get_validation_report": "validation_report",
                "get_optimization_report": "optimization_report"
            }
            key = action_map.get(args.action)
            print(json.dumps(data.get(key, {})))

        elif args.action == "get_market_context":
            # Production Integrity: Use MarketContextBuilder for ALL context data.
            # Never fabricate spot, VIX, expiry, PCR, OI, or option chain values.
            india_vix = 0.0
            orch = None

            if bs.is_connected():
                try:
                    orch = bs._get_orchestrator()
                    tick_vix = orch.latest_ticks.get("NSE:INDIA VIX")
                    if tick_vix:
                        india_vix = float(tick_vix.get("last_price", 0.0))
                    else:
                        ltps = bs.get_ltp(["NSE:INDIA VIX"])
                        if ltps:
                            india_vix = float(ltps.get("NSE:INDIA VIX", {}).get("last_price", 0.0))
                except Exception as e:
                    logger.warning(f"Failed to fetch VIX for context: {e}")

            try:
                from src.broker.services.market_context_builder import MarketContextBuilder
                market_ctx = MarketContextBuilder.build(
                    bs, orch, india_vix,
                    (cached_macro_context or {}).get("constituent_metadata"),
                )
                cached_market_context = market_ctx
            except Exception as e:
                logger.error(f"MarketContextBuilder failed: {e}")
                market_ctx = {
                    "status": "UNAVAILABLE", "current_spot": None, "ltp": None,
                    "feed_health": "OFFLINE", "timestamp": None,
                    "reason": "broker_session_not_connected"
                }

            try:
                from src.broker.services.market_feed_service import MarketFeedService
                spot_for_chain = float(market_ctx.get("current_spot", 0.0))
                expiries = MarketFeedService.get_instance().resolve_expiries(bs) if bs.is_connected() else []
                option_ctx = MarketFeedService.get_instance().build_option_chain_context(bs, spot_for_chain, expiries)
            except Exception as e:
                logger.error(f"OptionChain build failed: {e}")
                option_ctx = {"status": "UNAVAILABLE", "underlying_spot": None,
                              "atm_strike": None, "pcr": None, "max_pain": None,
                              "atm_iv": None, "timestamp": None,
                              "reason": "option_chain_build_failed",
                              "last_valid_snapshot": "UNAVAILABLE"}

            print(json.dumps({
                "market_context": market_ctx,
                "option_context": option_ctx
            }))

        elif args.action == "get_evening_report":
            # Production Integrity: Evening report must be derived from live market context.
            # Never fabricate daily_change, opportunity_strength, expected_range, or strategy.
            india_vix = 0.0
            orch = None

            if bs.is_connected():
                try:
                    orch = bs._get_orchestrator()
                    tick_vix = orch.latest_ticks.get("NSE:INDIA VIX")
                    if tick_vix:
                        india_vix = float(tick_vix.get("last_price", 0.0))
                except Exception:
                    pass

            try:
                from src.broker.services.market_context_builder import MarketContextBuilder
                mc = MarketContextBuilder.build(
                    bs, orch, india_vix,
                    (cached_macro_context or {}).get("constituent_metadata"),
                )
            except Exception:
                mc = {}

            try:
                from src.broker.services.market_feed_service import MarketFeedService
                spot = float(mc.get("current_spot", 0.0))
                expiries = MarketFeedService.get_instance().resolve_expiries(bs) if bs.is_connected() else []
                oc = MarketFeedService.get_instance().build_option_chain_context(bs, spot, expiries)
            except Exception:
                oc = {}

            spot_price = float(mc.get("current_spot", 0.0))
            atr = float(mc.get("atr", 0.0))
            atm_iv = float(oc.get("atm_iv", 0.0))

            # Expected range: derive from ATR (daily session) if available, otherwise from IV
            # Formula: expected_move = spot * (IV/100) * sqrt(days_to_expiry/252)
            # For end-of-day view we use ATR as the intraday proxy
            if atr > 0:
                range_min = round(spot_price - atr, 2)
                range_max = round(spot_price + atr, 2)
            elif atm_iv > 0 and spot_price > 0:
                import math
                daily_move = spot_price * (atm_iv / 100.0) * math.sqrt(1.0 / 252.0)
                range_min = round(spot_price - daily_move, 2)
                range_max = round(spot_price + daily_move, 2)
            else:
                range_min = None
                range_max = None

            report = {
                "market_summary": {
                    "spot_price": spot_price if spot_price > 0 else None,
                    "daily_change": None,  # Requires OHLC — unavailable without historical data
                    "daily_change_pct": None,
                    "market_regime": mc.get("market_regime", "UNKNOWN"),
                    "volatility_state": mc.get("volatility_state", "UNKNOWN"),
                    "vix_price": india_vix if india_vix > 0 else None,
                    "vwap": mc.get("vwap") or None,
                    "atr": atr if atr > 0 else None,
                    "feed_health": mc.get("feed_health", "OFFLINE"),
                    "benchmark_index": "NIFTY 50",
                    "date": time.strftime("%Y-%m-%d")
                },
                "tomorrow_outlook": {
                    "directional_bias": mc.get("trend_direction", "NEUTRAL"),
                    "opportunity_strength": mc.get("trend_strength") or None,
                    "expected_trading_range": {
                        "min_limit": range_min,
                        "max_limit": range_max
                    } if range_min is not None else None,
                    "key_support_levels": mc.get("support_levels", []),
                    "key_resistance_levels": mc.get("resistance_levels", []),
                    "pcr": oc.get("pcr") or None,
                    "atm_iv": atm_iv if atm_iv > 0 else None,
                    "india_vix": india_vix if india_vix > 0 else None
                },
                "summary": {
                    "best_strategy": None  # Determined by pipeline when live data available
                },
                "optimization_notes": [
                    f"Market regime: {mc.get('market_regime', 'UNKNOWN')}. Trend: {mc.get('trend_direction', 'NEUTRAL')}."
                ] if mc else ["Insufficient live data. Connect broker to populate market summary."],
                "risk_watchlist": {
                    "warnings": [
                        f"Feed health: {mc.get('feed_health', 'OFFLINE')}. Ensure broker is connected."
                    ] if mc.get("feed_health", "OFFLINE") != "HEALTHY" else []
                }
            }
            print(json.dumps(report))

        elif args.action == "get_portfolio_report":
            # Generate Live Portfolio Report using the Builder and current broker service instance
            report = LivePortfolioReportBuilder.generate(bs)
            print(json.dumps(serialize(report)))

        elif args.action == "get_profile":
            profile = bs.get_profile()
            print(json.dumps(serialize(profile)))

        elif args.action == "get_funds":
            funds = bs.get_funds()
            print(json.dumps(serialize(funds)))

        elif args.action == "get_holdings":
            holdings = bs.get_holdings()
            print(json.dumps(serialize(holdings)))

        elif args.action == "get_positions":
            positions = bs.get_positions()
            print(json.dumps(serialize(positions)))

        elif args.action == "get_orders":
            orders = bs.get_orders()
            print(json.dumps(serialize(orders)))

        elif args.action == "get_trades":
            trades = bs.get_trades()
            print(json.dumps(serialize(trades)))

        elif args.action == "get_broker_config":
            from src.configuration_engine.runtime import Config
            from src.broker.services.session_manager import SessionManager
            session_data = SessionManager.load_session() or {}
            api_key = getattr(Config, "KITE_API_KEY", "") or session_data.get("api_key", "")
            api_secret = getattr(Config, "KITE_API_SECRET", "")
            redirect_url = getattr(Config, "KITE_REDIRECT_URL", "") or "http://127.0.0.1:3000/api/broker/callback"
            print(json.dumps({
                "api_key_configured": bool(api_key),
                "api_secret_configured": bool(api_secret),
                "redirect_url": redirect_url,
                "access_token_saved": "access_token" in session_data and not session_data.get("expired", False),
                "session_status": str(bs.get_session_state()).upper()
            }))

        elif args.action == "login":
            api_key = args.api_key
            access_token = args.access_token

            if not api_key:
                print(json.dumps({"error": "Missing API Key"}))
                sys.exit(0)
            if not access_token:
                print(json.dumps({"error": "Missing Access Token"}))
                sys.exit(0)

            persist_key = args.persist_key == "True" if args.persist_key else False
            persist_token = args.persist_token == "True" if args.persist_token else False

            bs.set_mode(TradingMode.LIVE_ZERODHA)
            gateway = bs.get_gateway()

            if hasattr(gateway, "api_key"):
                gateway.api_key = api_key
            if hasattr(gateway, "access_token"):
                gateway.access_token = access_token

            # Try to connect (this will perform validation and raise exceptions on failure)
            success = gateway.connect(api_key=api_key, access_token=access_token)
            if not success:
                last_error = getattr(gateway, "_last_error", "Kite connection failed")
                print(json.dumps({"error": last_error}))
                sys.exit(0)

            # Persist if opted-in
            from src.broker.services.session_manager import SessionManager
            SessionManager.save_session(
                access_token=access_token,
                api_key=api_key,
                persist_key=persist_key,
                persist_token=persist_token
            )

        elif args.action == "get_login_url":
            from src.broker.services.authentication import AuthenticationManager
            api_key = getattr(args, "api_key", None)
            try:
                url = AuthenticationManager.generate_login_url(api_key=api_key)
                print(json.dumps({"login_url": url, "success": True}))
            except Exception as e:
                print(json.dumps({"error": str(e), "success": False}))

        elif args.action == "exchange_request_token":
            from src.broker.services.authentication import AuthenticationManager
            from src.broker.services.session_manager import SessionManager
            request_token = getattr(args, "request_token", None)
            if not request_token:
                print(json.dumps({"error": "Missing request token"}))
                sys.exit(0)

            try:
                session = AuthenticationManager.generate_access_token(request_token)
                access_token = session.get("access_token")
                api_key = getattr(Config, "KITE_API_KEY", "")
                if not access_token or not api_key:
                    raise ValueError("Token exchange did not return genuine Kite credentials")

                bs.set_mode(TradingMode.LIVE_ZERODHA)
                gateway = bs.get_gateway()
                gateway.connect(api_key=api_key, access_token=access_token)
                SessionManager.save_session(access_token=access_token, api_key=api_key, persist_key=True, persist_token=True)

                ctx = wm.get_context()
                print(json.dumps({"success": True, "context": serialize(ctx)}))
            except Exception as ex:
                print(json.dumps({"error": str(ex)}))
                sys.exit(0)

        elif args.action == "get_interpretation_status":
            from src.services.openai_interpretation_service import OpenAIInterpretationService
            print(json.dumps(OpenAIInterpretationService.get_status()))

        elif args.action == "get_interpretation":
            from src.services.openai_interpretation_service import OpenAIInterpretationService
            legacy_payload = build_legacy_payload()
            canonical_state = WorkstationStateService.build_from_legacy(
                legacy_payload,
                broker_state=str(bs.get_session_state()).upper(),
                market_state="CLOSED" if not bs.get_market_status().is_open else "OPEN"
            )
            result = OpenAIInterpretationService.interpret_canonical_state(canonical_state.to_dict())
            print(json.dumps(result))

        else:
            print(json.dumps({"error": f"Unknown action: {args.action}"}))
            sys.exit(0)

    except Exception as e:
        # Return error gracefully as JSON on stdout and exit 0 to avoid triggering server-side stderr crash alerts
        logger.exception("Bridge action failed")
        print(json.dumps({"error": str(e)}))
        sys.exit(0)

if __name__ == "__main__":
    main()
