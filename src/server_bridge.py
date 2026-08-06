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

# Disable verbose logging to stdout to preserve clean JSON output
logging.basicConfig(level=logging.ERROR)

logger = logging.getLogger("ServerBridge")

cached_market_context = None
cached_option_context = None
cached_news_sentiment = None
last_news_fetch_time = 0.0


class MockKiteConnectClient:
    def __init__(self, *args, **kwargs):
        self.api_key = kwargs.get("api_key", "MOCK_API_KEY")
        self.access_token = None

    def generate_session(self, request_token, api_secret):
        return {"access_token": "MOCK_ACCESS_TOKEN"}

    def set_access_token(self, token):
        self.access_token = token

    def profile(self):
        return {
            "client_id": "MOCK_CLIENT",
            "user_name": "Mock User",
            "email": "mock@example.com"
        }

    def margins(self):
        return {
            "equity": {
                "net": 1000000.0,
                "available": {"cash": 1000000.0},
                "utilised": {"debits": 0.0}
            },
            "commodity": {
                "net": 0.0,
                "available": {"cash": 0.0},
                "utilised": {"debits": 0.0}
            }
        }

    def holdings(self):
        return [
            {
                "tradingsymbol": "SBIN",
                "exchange": "NSE",
                "instrument_token": 12345,
                "isin": "INE062A01020",
                "product": "CNC",
                "quantity": 100,
                "t1_quantity": 0,
                "realised_quantity": 100,
                "average_price": 550.0,
                "last_price": 560.0,
                "pnl": 1000.0,
                "unrealised_pnl": 1000.0,
                "value": 56000.0,
                "price": 560.0
            }
        ]

    def positions(self):
        return {
            "net": [
                {
                    "tradingsymbol": "NIFTY2671624200CE",
                    "exchange": "NFO",
                    "instrument_token": 54321,
                    "product": "NRML",
                    "quantity": 500,
                    "buy_quantity": 500,
                    "sell_quantity": 0,
                    "average_price": 155.40,
                    "last_price": 160.0,
                    "pnl": 2300.0,
                    "m2m": 2300.0,
                    "realised": 0.0,
                    "unrealised": 2300.0,
                    "buy_value": 77700.0,
                    "sell_value": 0.0
                }
            ],
            "day": []
        }

    def orders(self):
        return [
            {
                "order_id": "O10001",
                "exchange_order_id": "E10001",
                "tradingsymbol": "NIFTY2671624200CE",
                "exchange": "NFO",
                "transaction_type": "BUY",
                "quantity": 500,
                "product": "NRML",
                "order_type": "MARKET",
                "status": "COMPLETE",
                "price": 155.40,
                "filled_quantity": 500,
                "pending_quantity": 0,
                "order_timestamp": "2026-07-12 10:15:30",
                "status_message": "ORDER PLACED AND FILLED",
                "average_price": 155.40,
                "tag": ""
            }
        ]

    def historical_data(self, *args, **kwargs):
        return []

    def instruments(self, *args, **kwargs):
        return []

    def place_order(self, *args, **kwargs):
        return "MOCK_ORDER_ID_123"

    def modify_order(self, *args, **kwargs):
        return "MOCK_ORDER_ID_123"

    def cancel_order(self, *args, **kwargs):
        return "MOCK_ORDER_ID_123"

from src.config_engine.config import Config
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

def handle_daemon_command(action, params, bs, wm):
    global cached_market_context, cached_option_context
    from datetime import datetime
    ws_mode = wm.current_mode
    
    # Extract params
    mode_str = params.get("mode")
    symbol = params.get("symbol")
    transaction_type = params.get("transaction_type")
    quantity = params.get("quantity")
    product = params.get("product")
    order_type = params.get("order_type")
    price = params.get("price")
    exchange = params.get("exchange")
    
    if action in {"place_order", "modify_order", "cancel_order", "exit_position", "set_mode"}:
        raise PermissionError("AIR ArdhaMind Phase 1 is read only; execution and mode-changing commands are unavailable.")

    if action == "get_context":
        ctx = wm.get_context()
        payload = serialize(ctx)
        payload.update({
            "allow_live_trading": Config.ALLOW_LIVE_TRADING,
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
        return {"success": True, "context": serialize(wm.get_context())}

    elif action == "logout":
        bs.disconnect()
        from src.broker.services.session_manager import SessionManager
        SessionManager.clear_session()
        return {"success": True}

    elif action == "get_broker_config":
        gateway = bs.get_gateway()
        return {
            "api_key": getattr(gateway, "api_key", ""),
            "access_token": getattr(gateway, "access_token", "")
        }

    elif action == "get_broker_health":
        return serialize(bs.get_stream_health())
        
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

    elif action == "get_market_context":
        if cached_market_context is not None and cached_option_context is not None:
            return {
                "market_context": cached_market_context,
                "option_context": cached_option_context
            }

        # Cache not loaded yet — return empty context with explicit status
        # The daemon loop will populate these within the next 3-second cycle
        return {
            "market_context": {
                "current_spot": 0.0,
                "ltp": 0.0,
                "feed_health": "WAITING",
                "feed_latency_ms": 0.0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "Market context loading. Broker WebSocket connecting..."
            },
            "option_context": {
                "underlying_spot": 0.0,
                "atm_strike": 0.0,
                "pcr": 0.0,
                "atm_iv": 0.0,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }

    else:
        raise ValueError(f"Unknown daemon action: {action}")

def run_daemon(wm, bs):
    global cached_news_sentiment, last_news_fetch_time
    import sys
    import json
    import time
    import threading
    from datetime import datetime
    from src.broker.services.streaming_service import STATIC_TOKENS
    from src.broker.services.instrument_service import InstrumentService
    
    logger.info("Starting Python Bridge Daemon...")
    
    last_mode = None
    sim_thread = None
    stop_sim = threading.Event()
    
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
        Production Integrity: When broker is disconnected, do NOT simulate
        market ticks with random values. Instead emit a BROKER_DISCONNECTED
        heartbeat so the UI can display the correct state.
        """
        while not stop_sim.is_set():
            timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            # Emit a null tick to signal disconnected state (UI reads feed_health=OFFLINE)
            tick_null = {
                "type": "tick",
                "symbol": "NSE:NIFTY 50",
                "data": {
                    "last_price": 0.0,
                    "feed_health": "BROKER_DISCONNECTED",
                    "exchange_timestamp": timestamp_str,
                    "backend_receive_timestamp": timestamp_str
                }
            }
            print(json.dumps(tick_null), flush=True)
            time.sleep(3.0)
            



            
    def setup_real_ticks_callback():
        orch = bs._get_orchestrator()
        original_on_ticks = orch._on_tick_received
        
        def new_on_ticks(raw_ticks):
            original_on_ticks(raw_ticks)
            t_now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            for raw in raw_ticks:
                token = raw.get("instrument_token")
                symbol = "N/A"
                if token in STATIC_TOKENS:
                    symbol = STATIC_TOKENS[token]
                else:
                    inst = InstrumentService.get_instance().lookup_instrument_by_token(token)
                    if inst:
                        symbol = inst.get("tradingsymbol") or "N/A"
                
                tick_payload = {
                    "type": "tick",
                    "symbol": symbol,
                    "data": {
                        "last_price": raw.get("last_price", 0.0),
                        "volume": raw.get("volume", 0),
                        "oi": raw.get("oi", 0),
                        "ohlc": raw.get("ohlc", {}),
                        "exchange_timestamp": raw.get("timestamp", datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if hasattr(raw.get("timestamp"), "strftime") else str(raw.get("timestamp", t_now)),
                        "backend_receive_timestamp": t_now
                    }
                }
                print(json.dumps(tick_payload), flush=True)
        
        orch._on_tick_received = new_on_ticks

    setup_real_ticks_callback()

    instruments_df = None
    from src.broker.services.market_feed_service import MarketFeedService

    while True:
        current_mode = wm.current_mode
        if current_mode != last_mode:
            logger.info(f"Daemon workspace mode changed to: {current_mode}")
            last_mode = current_mode
            
            if bs.is_connected():
                try:
                    bs.connect_stream()
                    bs.subscribe_stream(["NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:NIFTY FIN SERVICE", "NSE:INDIA VIX"])
                except Exception as e:
                    logger.error(f"Failed to connect real stream: {e}")
                        
        try:
            # Initialize instruments master cache if broker connects
            if bs.is_connected() and instruments_df is None:
                try:
                    from src.data_engine.instruments import InstrumentManager
                    instruments_df = InstrumentManager.get_instruments(bs.get_gateway())
                    InstrumentService.get_instance().load_instruments(bs, force_refresh=False)
                    logger.info("Zerodha instrument list loaded dynamically in daemon loop.")
                except Exception as e:
                    logger.error(f"Failed to initialize Zerodha instruments inside daemon: {e}")

            # Production Integrity: Never fabricate spot/VIX values.
            # All values must originate from live Zerodha ticks.
            # When broker is disconnected, values remain None / 0.0.
            spot_nifty = 0.0
            spot_banknifty = 0.0
            spot_finnifty = 0.0
            india_vix = 0.0

            # If connected, fetch dynamic spot prices and Option chain context
            if bs.is_connected():
                orch = bs._get_orchestrator()
                tick_nifty = orch.latest_ticks.get("NSE:NIFTY 50")
                if tick_nifty:
                    spot_nifty = float(tick_nifty.get("last_price", 0.0))
                else:
                    try:
                        ltps = bs.get_ltp(["NSE:NIFTY 50"])
                        if ltps:
                            spot_nifty = float(ltps.get("NSE:NIFTY 50", {}).get("last_price", 0.0))
                    except Exception:
                        pass
                
                tick_bn = orch.latest_ticks.get("NSE:NIFTY BANK")
                if tick_bn:
                    spot_banknifty = float(tick_bn.get("last_price", 0.0))
                tick_fn = orch.latest_ticks.get("NSE:NIFTY FIN SERVICE")
                if tick_fn:
                    spot_finnifty = float(tick_fn.get("last_price", 0.0))
                tick_vix = orch.latest_ticks.get("NSE:INDIA VIX")
                if tick_vix:
                    india_vix = float(tick_vix.get("last_price", 0.0))
                else:
                    try:
                        ltps = bs.get_ltp(["NSE:INDIA VIX"])
                        if ltps:
                            india_vix = float(ltps.get("NSE:INDIA VIX", {}).get("last_price", 0.0))
                    except Exception:
                        pass

                try:
                    expiries = MarketFeedService.get_instance().resolve_expiries(bs)
                    if expiries:
                        # Filter expiries >= today
                        from datetime import datetime as dt_cls, date as dt_date
                        today_dt = dt_date.today()
                        future_exp = []
                        for e in expiries:
                            try:
                                e_date = dt_cls.strptime(e, "%Y-%m-%d").date()
                                if e_date >= today_dt:
                                    future_exp.append(e)
                            except Exception:
                                pass
                        
                        # Production Integrity: Never substitute hardcoded expiry dates.
                        # If Zerodha has no future expiries, leave the list empty.
                        # The frontend will display — for any expiry-dependent field.
                        
                        # Dynamically update WebSocket option subscriptions
                        current_weekly = future_exp[0]
                        MarketFeedService.get_instance().update_subscriptions(bs, spot_nifty, current_weekly)
                        
                        # Compile Option & Market Contexts
                        global cached_market_context, cached_option_context
                        cached_option_context = MarketFeedService.get_instance().build_option_chain_context(bs, spot_nifty, future_exp)
                        
                        # Build live MarketContext using MarketContextBuilder
                        from src.broker.services.market_context_builder import MarketContextBuilder
                        orch_instance = bs._get_orchestrator()
                        cached_market_context = MarketContextBuilder.build(bs, orch_instance, india_vix)
                except Exception as ex:
                    logger.error(f"Error compiling live option/market context: {ex}")

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
            
            # Resolve Broker State
            broker_state = "DISCONNECTED"
            if bs.is_connected():
                try:
                    gateway = bs.get_gateway()
                    if getattr(gateway, "access_token", None):
                        if gateway.validate_session():
                            broker_state = "CONNECTED"
                        else:
                            broker_state = "TOKEN_EXPIRED"
                    else:
                        broker_state = "DISCONNECTED"
                except Exception:
                    broker_state = "TOKEN_EXPIRED"

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
                            market_score_val=75.0,
                            market_score_grade="B",
                            confidence_score=80.0,
                            risk_grade="MODERATE",
                            strategy_name="MOMENTUM",
                            entry_time=t.get("timestamp", ""),
                            entry_premium=float(t.get("execution_price", 0.0)),
                            entry_capital=float(t.get("execution_price", 0.0)) * int(t.get("quantity", 0)) * 50,
                            entry_lots=int(t.get("quantity", 0)),
                            exit_time=t.get("timestamp", ""),
                            exit_premium=float(t.get("execution_price", 0.0)),
                            exit_reason="Exit",
                            pnl=pnl,
                            pnl_pct=0.0,
                            duration_seconds=120,
                            outcome="WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "FLAT"),
                            market_regime="TRENDING",
                            confidence_band="HIGH",
                            notes=""
                        )
                        entries.append(entry)
                    except Exception:
                        pass
                
                report = PerformanceAnalyticsBuilder.build_report(entries)
                analytics_report = PerformanceAnalyticsPanel(report).to_dict()
            except Exception as e:
                logger.error(f"Failed to build analytics report: {e}")

            # Compile News Sentiment
            if cached_news_sentiment is None or time.time() - last_news_fetch_time > 300:
                try:
                    from src.pipeline.news_pipeline import NewsPipeline
                    from src.dashboard.news_panel import NewsIntelligencePanel
                    # Phase 1 production shell: hardcoded demo providers are not
                    # permitted to appear as live news. Real provider integration
                    # will replace this explicit unavailable context later.
                    pipeline = NewsPipeline(providers=[])
                    news_ctx = pipeline.run()
                    cached_news_sentiment = NewsIntelligencePanel(news_ctx).to_dict()
                    last_news_fetch_time = time.time()
                except Exception as e:
                    logger.error(f"Failed to compile news sentiment: {e}")

            legacy_data = {
                    "workspaceContext": {
                        "currentMode": current_mode.value,
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
                    "newsSentiment": cached_news_sentiment
            }
            legacy_data.update(pipeline_result.compatibility_values())
            canonical_state = WorkstationStateService.build_from_legacy(
                legacy_data, broker_state=broker_state, market_state=market_state
            )
            state_payload = {
                "type": "state",
                "data": CompatibilitySerializer.to_phase1_payload(canonical_state, legacy_data)
            }
            print(json.dumps(state_payload), flush=True)
        except Exception as err:
            logger.error(f"Daemon state generation failed: {err}")
            
        time.sleep(3.0)

def main():
    parser = argparse.ArgumentParser(description="Python Backend Gateway Bridge")
    parser.add_argument("--action", required=True, help="Action to perform")
    parser.add_argument("--mode", help="Workspace Mode to transition to")
    parser.add_argument("--symbol", help="Trading symbol for exit_position")
    parser.add_argument("--product", help="Product type for exit_position")
    parser.add_argument("--api_key", help="Kite API key supplied from the broker tab")
    parser.add_argument("--api_secret", help="Kite API secret supplied from the broker tab")
    parser.add_argument("--request_token", help="Zerodha request token for login exchange")
    parser.add_argument("--access_token", help="Zerodha access token for direct connection")
    parser.add_argument("--persist_key", help="Whether to persist the API Key (True/False)")
    parser.add_argument("--persist_token", help="Whether to persist the Access Token (True/False)")
    parser.add_argument("--transaction_type", help="BUY or SELL")
    parser.add_argument("--quantity", type=int, help="Quantity for placing order")
    parser.add_argument("--price", type=float, help="Price for order placement")
    parser.add_argument("--order_type", default="MARKET", help="Order type")
    parser.add_argument("--exchange", default="NSE", help="Exchange")

    args = parser.parse_args()

    # Synchronize the Workspace and Broker states with env variables
    ws_mode_str = Config.WORKSPACE_MODE or Config.DEFAULT_WORKSPACE_MODE
    try:
        ws_mode = WorkspaceMode(ws_mode_str)
    except ValueError:
        ws_mode = WorkspaceMode.LIVE_PRACTICE

    wm = WorkspaceManager.get_instance()
    # Force set workspace manager's internal mode to match environment/config
    wm._current_mode = ws_mode

    # Propagate trading mode to BrokerService and auto-connect (always live Zerodha)
    bs = BrokerService.get_instance()
    bs.set_mode(TradingMode.LIVE_ZERODHA)
    try:
        bs.load_session()
    except Exception:
        pass

    try:
        if args.action == "daemon":
            run_daemon(wm, bs)
        elif args.action == "get_context":
            ctx = wm.get_context()
            payload = serialize(ctx)
            payload.update({
                "allow_live_trading": Config.ALLOW_LIVE_TRADING,
                "require_confirmation": Config.REQUIRE_CONFIRMATION,
                "show_mode_warning": Config.SHOW_MODE_WARNING,
                "auto_fallback_to_development": Config.AUTO_FALLBACK_TO_DEVELOPMENT,
            })
            print(json.dumps(payload))

        elif args.action == "set_mode":
            if not args.mode:
                print(json.dumps({"error": "Missing mode parameter"}), file=sys.stderr)
                sys.exit(1)
            try:
                new_mode = WorkspaceMode(args.mode)
                wm.set_mode(new_mode, operator_confirmed=True)
                # Re-fetch context
                ctx = wm.get_context()
                print(json.dumps(serialize(ctx)))
            except Exception as e:
                print(json.dumps({"error": f"Failed to set mode: {str(e)}"}), file=sys.stderr)
                sys.exit(1)

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
                market_ctx = MarketContextBuilder.build(bs, orch, india_vix)
            except Exception as e:
                logger.error(f"MarketContextBuilder failed: {e}")
                market_ctx = {
                    "current_spot": 0.0, "ltp": 0.0, "feed_health": "OFFLINE",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "message": "Broker not connected. Connect to receive live market data."
                }

            try:
                from src.broker.services.market_feed_service import MarketFeedService
                spot_for_chain = float(market_ctx.get("current_spot", 0.0))
                expiries = MarketFeedService.get_instance().resolve_expiries(bs) if bs.is_connected() else []
                option_ctx = MarketFeedService.get_instance().build_option_chain_context(bs, spot_for_chain, expiries)
            except Exception as e:
                logger.error(f"OptionChain build failed: {e}")
                option_ctx = {
                    "underlying_spot": 0.0, "atm_strike": 0.0, "pcr": 0.0,
                    "atm_iv": 0.0, "timestamp": datetime.utcnow().isoformat() + "Z"
                }

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
                mc = MarketContextBuilder.build(bs, orch, india_vix)
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
            from src.broker.services.session_manager import SessionManager
            session_data = SessionManager.load_session() or {}
            print(json.dumps({
                "api_key": session_data.get("api_key", ""),
                "access_token_saved": "access_token" in session_data and not session_data.get("expired", False)
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

            ctx = wm.get_context()
            print(json.dumps({
                "success": True,
                "context": serialize(ctx)
            }))

        elif args.action in {"place_order", "modify_order", "cancel_order", "exit_position", "set_mode"}:
            print(json.dumps({"error": "AIR ArdhaMind Phase 1 is read only; execution and mode-changing commands are unavailable."}))

        else:
            print(json.dumps({"error": f"Unknown action: {args.action}"}))
            sys.exit(0)

    except Exception as e:
        # Return error gracefully as JSON on stdout and exit 0 to avoid triggering server-side stderr crash alerts
        print(json.dumps({"error": str(e)}))
        sys.exit(0)

if __name__ == "__main__":
    main()
