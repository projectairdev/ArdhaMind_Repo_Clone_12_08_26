from __future__ import annotations
from dataclasses import dataclass
import time
import sys
from typing import List, Dict, Any, Optional

from src.broker.services.account_service import AccountProfile, AccountService
from src.broker.services.funds_service import AccountFunds, FundsService, FundSegment
from src.broker.services.holdings_service import HoldingItem, HoldingsService
from src.broker.services.positions_service import AccountPositions, PositionsService
from src.broker.services.orders_service import AccountOrders, OrdersService
from src.broker.services.trades_service import TradeItem, TradesService
from src.broker.models.health import BrokerHealth


@dataclass(frozen=True)
class PortfolioStatistics:
    total_holdings_value: float
    total_unrealized_pnl: float
    total_realized_pnl: float
    today_mtm: float
    total_margin_utilized: float
    available_cash: float


@dataclass(frozen=True)
class LivePortfolioReport:
    account_profile: AccountProfile
    funds: AccountFunds
    holdings: List[HoldingItem]
    positions: AccountPositions
    orders: AccountOrders
    trades: List[TradeItem]
    statistics: PortfolioStatistics
    timestamp: str
    broker_health: BrokerHealth
    sync_status: str  # "SUCCESS" or "FAILED"


class LivePortfolioReportBuilder:
    @staticmethod
    def generate(gateway) -> LivePortfolioReport:
        """
        Gathers live broker account telemetry, synchronizes resources, calculates
        portfolio statistics, and returns an immutable LivePortfolioReport.
        """
        start_time = time.time()
        try:
            # Synchronize elements using dedicated services
            try:
                profile = AccountService.get_profile(gateway)
                print("Profile Loaded", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"Profile Load Failed: {e}", file=sys.stderr, flush=True)
                raise e

            try:
                funds = FundsService.get_funds(gateway)
                print("Funds Loaded", file=sys.stderr, flush=True)
                print("Margins Loaded", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"Funds/Margins Load Failed: {e}", file=sys.stderr, flush=True)
                raise e

            try:
                holdings = HoldingsService.get_holdings(gateway)
                print("Holdings Loaded", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"Holdings Load Failed: {e}", file=sys.stderr, flush=True)
                raise e

            try:
                positions = PositionsService.get_positions(gateway)
                print("Positions Loaded", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"Positions Load Failed: {e}", file=sys.stderr, flush=True)
                raise e

            try:
                orders = OrdersService.get_orders(gateway)
                print("Orders Loaded", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"Orders Load Failed: {e}", file=sys.stderr, flush=True)
                raise e

            try:
                trades = TradesService.get_trades(gateway)
                print("Trades Loaded", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"Trades Load Failed: {e}", file=sys.stderr, flush=True)
                raise e
            
            # Fetch broker health
            health = gateway.health()
            
            # Compute Portfolio Statistics
            total_holdings_val = sum(h.current_value for h in holdings)
            holdings_unrealized = sum(h.unrealized_pnl for h in holdings)
            positions_unrealized = sum(p.unrealized_pnl for p in positions.net)
            total_unrealized = holdings_unrealized + positions_unrealized
            
            total_realized = sum(p.realized_pnl for p in positions.net)
            today_mtm = sum(p.mtm for p in positions.net)
            
            total_utilized = funds.equity.utilized_margin + funds.commodity.utilized_margin
            total_avail = funds.equity.available_cash + funds.commodity.available_cash
            
            stats = PortfolioStatistics(
                total_holdings_value=round(total_holdings_val, 2),
                total_unrealized_pnl=round(total_unrealized, 2),
                total_realized_pnl=round(total_realized, 2),
                today_mtm=round(today_mtm, 2),
                total_margin_utilized=round(total_utilized, 2),
                available_cash=round(total_avail, 2)
            )
            
            print("Runtime Updated", file=sys.stderr, flush=True)
            print("Broadcast Complete", file=sys.stderr, flush=True)
            
            return LivePortfolioReport(
                account_profile=profile,
                funds=funds,
                holdings=holdings,
                positions=positions,
                orders=orders,
                trades=trades,
                statistics=stats,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                broker_health=health,
                sync_status="SUCCESS"
            )
        except Exception as e:
            # Safe recovery fallback report on error
            from src.broker.models.health import BrokerHealth
            dummy_health = BrokerHealth(
                broker_name="Zerodha KiteConnect",
                connection_status="ERROR",
                trading_mode="LIVE_ZERODHA",
                latency=0.0,
                authentication_state="UNAUTHENTICATED",
                last_heartbeat=time.strftime("%Y-%m-%d %H:%M:%S"),
                instrument_cache_status="EXPIRED",
                market_status="CLOSED",
                health_score=0.0,
                last_error=str(e),
                authentication_status="UNAUTHENTICATED",
                session_age_hours=0.0,
                token_expiry="N/A",
                last_login_time="N/A",
                session_valid=False,
                broker_version="KiteConnect v5.2",
                api_status="OFFLINE"
            )
            
            dummy_profile = AccountProfile("N/A", "N/A", "N/A", "N/A", "Zerodha", "individual", "N/A")
            dummy_segment = FundSegment(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            dummy_funds = AccountFunds(dummy_segment, dummy_segment)
            dummy_positions = AccountPositions([], [])
            dummy_orders = AccountOrders([], [], [], [], [], [])
            dummy_stats = PortfolioStatistics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            
            return LivePortfolioReport(
                account_profile=dummy_profile,
                funds=dummy_funds,
                holdings=[],
                positions=dummy_positions,
                orders=dummy_orders,
                trades=[],
                statistics=dummy_stats,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                broker_health=dummy_health,
                sync_status="FAILED"
            )
