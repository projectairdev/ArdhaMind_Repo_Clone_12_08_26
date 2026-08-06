from __future__ import annotations
import unittest
from unittest.mock import MagicMock, patch
import time

from src.broker.services.account_service import AccountService, AccountProfile
from src.broker.services.funds_service import FundsService, AccountFunds
from src.broker.services.holdings_service import HoldingsService
from src.broker.services.positions_service import PositionsService
from src.broker.services.orders_service import OrdersService
from src.broker.services.trades_service import TradesService
from src.models.live_portfolio_report import LivePortfolioReportBuilder, LivePortfolioReport
from src.broker.models.health import BrokerHealth


from unittest.mock import MagicMock, patch, PropertyMock
from src.workspace.workspace_manager import WorkspaceManager
from src.workspace.workspace_mode import WorkspaceMode

class TestSprint31LivePortfolio(unittest.TestCase):
    def setUp(self):
        # Patch workspace mode to prevent virtual execution leakage
        self.mode_patcher = patch.object(WorkspaceManager, 'current_mode', new_callable=PropertyMock)
        self.mock_current_mode = self.mode_patcher.start()
        self.mock_current_mode.return_value = WorkspaceMode.LIVE_TRADING

        self.mock_gateway = MagicMock()
        
        # Setup mock return values matching real Zerodha schemas
        self.mock_gateway.get_profile.return_value = {
            "client_id": "AB1234",
            "user_name": "John Doe",
            "email": "john.doe@example.com",
            "pan": "ABCDE1234F",
            "broker": "Zerodha",
            "user_type": "individual",
            "login_time": "2026-07-11 10:00:00"
        }
        
        self.mock_gateway.get_funds.return_value = {
            "equity": {
                "enabled": True,
                "net": 150000.0,
                "available": {
                    "cash": 100000.0,
                    "intraday_payin": 5000.0,
                    "collateral": 50000.0,
                    "opening_balance": 95000.0,
                    "live_balance": 150000.0
                },
                "utilised": {
                    "debits": 35000.0,
                    "payout": 0.0
                }
            },
            "commodity": {
                "enabled": True,
                "net": 50000.0,
                "available": {
                    "cash": 30000.0,
                    "intraday_payin": 0.0,
                    "collateral": 20000.0,
                    "opening_balance": 30000.0,
                    "live_balance": 50000.0
                },
                "utilised": {
                    "debits": 5000.0,
                    "payout": 0.0
                }
            }
        }
        
        self.mock_gateway.get_holdings.return_value = [
            {
                "tradingsymbol": "RELIANCE",
                "exchange": "NSE",
                "quantity": 10,
                "average_price": 2400.0,
                "last_price": 2450.0,
                "pnl": 500.0,
                "close_price": 2420.0
            },
            {
                "tradingsymbol": "INFY",
                "exchange": "NSE",
                "quantity": 5,
                "average_price": 1500.0,
                "last_price": 1480.0,
                "pnl": -100.0,
                "close_price": 1490.0
            }
        ]
        
        self.mock_gateway.get_positions.return_value = {
            "net": [
                {
                    "tradingsymbol": "NIFTY26JUL22000CE",
                    "product": "NRML",
                    "exchange": "NFO",
                    "quantity": 50,
                    "buy_quantity": 50,
                    "sell_quantity": 0,
                    "average_price": 125.50,
                    "last_price": 135.0,
                    "m2m": 475.0,
                    "unrealised": 475.0,
                    "realised": 0.0
                }
            ],
            "day": [
                {
                    "tradingsymbol": "NIFTY26JUL22200PE",
                    "product": "MIS",
                    "exchange": "NFO",
                    "quantity": 0,
                    "buy_quantity": 50,
                    "sell_quantity": 50,
                    "average_price": 85.20,
                    "last_price": 80.0,
                    "m2m": 260.0,
                    "unrealised": 0.0,
                    "realised": 260.0
                }
            ]
        }
        
        self.mock_gateway.get_orders.return_value = [
            {
                "order_id": "O001",
                "exchange_order_id": "E001",
                "tradingsymbol": "NIFTY26JUL22000CE",
                "exchange": "NFO",
                "transaction_type": "BUY",
                "quantity": 50,
                "filled_quantity": 50,
                "product": "NRML",
                "order_type": "LIMIT",
                "status": "COMPLETE",
                "price": 125.50,
                "average_price": 125.50,
                "order_timestamp": "2026-07-11 10:15:30",
                "validity": "DAY"
            },
            {
                "order_id": "O002",
                "exchange_order_id": "E002",
                "tradingsymbol": "NIFTY26JUL22200PE",
                "exchange": "NFO",
                "transaction_type": "SELL",
                "quantity": 50,
                "filled_quantity": 0,
                "product": "MIS",
                "order_type": "LIMIT",
                "status": "OPEN",
                "price": 85.20,
                "average_price": 0.0,
                "order_timestamp": "2026-07-11 14:15:30",
                "validity": "DAY"
            }
        ]
        
        self.mock_gateway.get_trades.return_value = [
            {
                "trade_id": "T001",
                "order_id": "O001",
                "tradingsymbol": "NIFTY26JUL22000CE",
                "exchange": "NFO",
                "transaction_type": "BUY",
                "quantity": 50,
                "average_price": 125.50,
                "fill_timestamp": "2026-07-11 10:15:30"
            }
        ]
        
        self.mock_gateway.health.return_value = BrokerHealth(
            broker_name="Zerodha KiteConnect",
            connection_status="CONNECTED",
            trading_mode="LIVE_ZERODHA",
            latency=12.5,
            authentication_state="AUTHENTICATED",
            last_heartbeat=time.strftime("%Y-%m-%d %H:%M:%S"),
            instrument_cache_status="VALID",
            market_status="OPEN",
            health_score=100.0,
            last_error=None,
            authentication_status="AUTHENTICATED",
            session_age_hours=2.5,
            token_expiry="N/A",
            last_login_time="N/A",
            session_valid=True,
            broker_version="KiteConnect v5.2",
            api_status="ONLINE"
        )

    def tearDown(self):
        self.mode_patcher.stop()

    def test_account_service(self):
        profile = AccountService.get_profile(self.mock_gateway)
        self.assertEqual(profile.client_id, "AB1234")
        self.assertEqual(profile.client_name, "John Doe")
        self.assertEqual(profile.email, "john.doe@example.com")
        self.assertEqual(profile.pan, "XXXXX1234F")  # PAN Masking check
        self.assertEqual(profile.broker_name, "Zerodha")
        self.assertEqual(profile.user_type, "individual")
        self.assertEqual(profile.login_time, "2026-07-11 10:00:00")

    def test_funds_service(self):
        funds = FundsService.get_funds(self.mock_gateway)
        # Equity
        self.assertEqual(funds.equity.available_cash, 100000.0)
        self.assertEqual(funds.equity.utilized_margin, 35000.0)
        self.assertEqual(funds.equity.available_margin, 150000.0)
        self.assertEqual(funds.equity.opening_balance, 95000.0)
        self.assertEqual(funds.equity.collateral, 50000.0)
        self.assertEqual(funds.equity.payin_amount, 5000.0)
        self.assertEqual(funds.equity.payout_amount, 0.0)
        # Commodity
        self.assertEqual(funds.commodity.available_cash, 30000.0)
        self.assertEqual(funds.commodity.utilized_margin, 5000.0)
        self.assertEqual(funds.commodity.available_margin, 50000.0)

    def test_holdings_service(self):
        holdings = HoldingsService.get_holdings(self.mock_gateway)
        self.assertEqual(len(holdings), 2)
        # RELIANCE
        self.assertEqual(holdings[0].symbol, "RELIANCE")
        self.assertEqual(holdings[0].quantity, 10)
        self.assertEqual(holdings[0].average_price, 2400.0)
        self.assertEqual(holdings[0].current_price, 2450.0)
        self.assertEqual(holdings[0].current_value, 24500.0)
        self.assertEqual(holdings[0].unrealized_pnl, 500.0)
        self.assertAlmostEqual(holdings[0].day_change, 30.0)
        self.assertAlmostEqual(holdings[0].day_change_pct, 1.2396694)

    def test_positions_service(self):
        positions = PositionsService.get_positions(self.mock_gateway)
        self.assertEqual(len(positions.net), 1)
        self.assertEqual(len(positions.day), 1)
        
        # Net Position
        net_pos = positions.net[0]
        self.assertEqual(net_pos.symbol, "NIFTY26JUL22000CE")
        self.assertEqual(net_pos.quantity, 50)
        self.assertEqual(net_pos.last_price, 135.0)
        self.assertEqual(net_pos.mtm, 475.0)
        self.assertEqual(net_pos.unrealized_pnl, 475.0)
        self.assertEqual(net_pos.realized_pnl, 0.0)

    def test_orders_service(self):
        orders = OrdersService.get_orders(self.mock_gateway)
        self.assertEqual(len(orders.all_orders), 2)
        self.assertEqual(len(orders.completed), 1)
        self.assertEqual(len(orders.open_orders), 1)
        
        # Completed Order
        co = orders.completed[0]
        self.assertEqual(co.order_id, "O001")
        self.assertEqual(co.status, "COMPLETE")
        self.assertEqual(co.price, 125.50)

    def test_trades_service(self):
        trades = TradesService.get_trades(self.mock_gateway)
        self.assertEqual(len(trades), 1)
        t = trades[0]
        self.assertEqual(t.trade_id, "T001")
        self.assertEqual(t.symbol, "NIFTY26JUL22000CE")
        self.assertEqual(t.quantity, 50)
        self.assertEqual(t.execution_price, 125.50)

    def test_live_portfolio_report_builder(self):
        report = LivePortfolioReportBuilder.generate(self.mock_gateway)
        self.assertEqual(report.sync_status, "SUCCESS")
        
        # Check derived stats
        self.assertEqual(report.statistics.total_holdings_value, 24500.0 + 7400.0) # 10 * 2450 + 5 * 1480
        # 500 (RELIANCE) - 100 (INFY) + 475 (NIFTY option) = 875
        self.assertEqual(report.statistics.total_unrealized_pnl, 875.0)
        self.assertEqual(report.statistics.today_mtm, 475.0)
        self.assertEqual(report.statistics.total_margin_utilized, 40000.0) # 35000 + 5000
        self.assertEqual(report.statistics.available_cash, 130000.0) # 100000 + 30000

    def test_report_builder_recovery_fallback(self):
        # Trigger an exception during generation
        self.mock_gateway.get_profile.side_effect = Exception("API Server Outage")
        report = LivePortfolioReportBuilder.generate(self.mock_gateway)
        self.assertEqual(report.sync_status, "FAILED")
        self.assertEqual(report.broker_health.connection_status, "ERROR")
        self.assertEqual(report.broker_health.last_error, "API Server Outage")
        self.assertEqual(report.statistics.total_holdings_value, 0.0)
