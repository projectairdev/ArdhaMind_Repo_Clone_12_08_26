from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.models import (
    DecisionReport,
    CandidateDecision,
    BrokerFunds,
    BrokerPosition,
    BrokerOrder,
    BrokerAccount,
    ExecutionRequest,
    ExecutionOrder,
    ExecutionReport,
    ExecutionStatus,
)
from src.broker.compat.connection import ConnectionManager, BrokerConnectionError
from src.broker.compat.account import AccountManager
from src.broker.compat.funds import FundsManager
from src.broker.compat.positions import PositionsManager
from src.broker.compat.holdings import HoldingsManager
from src.broker.compat.orders import OrdersManager
from src.broker.compat.validator import BrokerValidator
from src.broker.compat.execution_builder import ExecutionBuilder
from src.dashboard.broker_panel import BrokerPanel


class TestBrokerIntegration(unittest.TestCase):
    """
    Comprehensive unit tests for Sprint 22 - Manual Broker Integration Layer.
    Mocks KiteConnect client and tests all stateless modules and immutable flows.
    """

    def setUp(self) -> None:
        # Reset ConnectionManager singleton for isolation
        ConnectionManager._instance = None

    @patch("src.broker.compat.connection.KiteConnect")
    def test_connection_manager_singleton_and_init(self, mock_kite_class):
        mock_kite_instance = MagicMock()
        mock_kite_instance.generate_session.return_value = {"access_token": "mock_token"}
        mock_kite_instance.profile.return_value = {"client_id": "MOCK_CLI"}
        mock_kite_class.return_value = mock_kite_instance

        cm = ConnectionManager()
        cm_again = ConnectionManager()
        self.assertIs(cm, cm_again)  # Must be a singleton

        # Initially disconnected
        self.assertFalse(cm.is_connected())

        # Initialize connection
        cm.connect(api_key="my_api_key", request_token="my_req_token", api_secret="my_secret")
        self.assertTrue(cm.is_connected())
        self.assertEqual(cm.get_status_report()["client_id"], "MOCK_CLI")

        # Confirm client returned
        client = cm.get_client()
        self.assertIs(client, mock_kite_instance)

    def test_connection_manager_uninitialized_error(self):
        cm = ConnectionManager()
        with self.assertRaises(BrokerConnectionError):
            cm.get_client()

    @patch("src.broker.compat.connection.ConnectionManager.get_client")
    def test_account_manager_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.profile.return_value = {
            "client_id": "AB1234",
            "user_name": "Dev Operator",
            "email": "operator@terminal.local"
        }

        acc = AccountManager.get_account_info()
        self.assertEqual(acc.client_id, "AB1234")
        self.assertEqual(acc.name, "Dev Operator")
        self.assertEqual(acc.email, "operator@terminal.local")
        self.assertEqual(acc.broker, "Zerodha")

    @patch("src.broker.compat.connection.ConnectionManager.get_client")
    def test_account_manager_error_handling(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.profile.side_effect = Exception("API failure")

        acc = AccountManager.get_account_info()
        self.assertEqual(acc.client_id, "ERROR")
        self.assertEqual(acc.name, "ERROR")

    @patch("src.broker.compat.connection.ConnectionManager.get_client")
    def test_funds_manager_parsing(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.margins.return_value = {
            "equity": {
                "net": 125000.0,
                "available": {
                    "cash": 100000.0
                },
                "utilised": {
                    "debits": 25000.0
                }
            }
        }

        funds = FundsManager.get_funds_info()
        self.assertEqual(funds.available_cash, 100000.0)
        self.assertEqual(funds.margins, 125000.0)
        self.assertEqual(funds.utilized_margin, 25000.0)
        self.assertEqual(funds.available_margin, 100000.0)

    @patch("src.broker.compat.connection.ConnectionManager.get_client")
    def test_positions_manager(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.positions.return_value = {
            "net": [
                {
                    "tradingsymbol": "NIFTY26NOV24200CE",
                    "exchange": "NFO",
                    "product": "NRML",
                    "quantity": 50,
                    "average_price": 110.0,
                    "last_price": 120.0,
                    "pnl": 500.0,
                    "m2m": 500.0
                },
                {
                    "tradingsymbol": "RELIANCE",
                    "exchange": "NSE",
                    "product": "MIS",
                    "quantity": 10,
                    "average_price": 2400.0,
                    "last_price": 2380.0,
                    "pnl": -200.0,
                    "m2m": -200.0
                }
            ]
        }

        positions = PositionsManager.get_positions()
        self.assertEqual(len(positions), 2)
        self.assertEqual(positions[0].tradingsymbol, "NIFTY26NOV24200CE")
        self.assertEqual(positions[0].today_mtm, 500.0)
        
        total_mtm = PositionsManager.get_today_mtm()
        self.assertEqual(total_mtm, 300.0)

    @patch("src.broker.compat.connection.ConnectionManager.get_client")
    def test_holdings_manager(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.holdings.return_value = [
            {
                "tradingsymbol": "TCS",
                "exchange": "NSE",
                "product": "CNC",
                "quantity": 15,
                "average_price": 3200.0,
                "last_price": 3400.0,
                "pnl": 3000.0
            }
        ]

        holdings = HoldingsManager.get_holdings()
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0].tradingsymbol, "TCS")
        self.assertEqual(holdings[0].pnl, 3000.0)

    @patch("src.broker.compat.connection.ConnectionManager.get_client")
    def test_orders_manager_retrieval(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.orders.return_value = [
            {
                "order_id": "ORD1001",
                "exchange_order_id": "EXCH1001",
                "tradingsymbol": "NIFTY26NOV24200CE",
                "exchange": "NFO",
                "transaction_type": "BUY",
                "quantity": 50,
                "product": "NRML",
                "order_type": "MARKET",
                "status": "OPEN",
                "price": 0.0,
                "filled_quantity": 0,
                "order_timestamp": "2026-11-09 10:00:00"
            },
            {
                "order_id": "ORD1002",
                "exchange_order_id": "EXCH1002",
                "tradingsymbol": "INFY",
                "exchange": "NSE",
                "transaction_type": "SELL",
                "quantity": 10,
                "product": "MIS",
                "order_type": "LIMIT",
                "status": "COMPLETE",
                "price": 1500.0,
                "filled_quantity": 10,
                "order_timestamp": "2026-11-09 10:15:00"
            }
        ]

        all_orders = OrdersManager.get_orders()
        self.assertEqual(len(all_orders), 2)
        
        pending = OrdersManager.get_pending_orders()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].order_id, "ORD1001")

        executed = OrdersManager.get_executed_orders()
        self.assertEqual(len(executed), 1)
        self.assertEqual(executed[0].order_id, "ORD1002")

    def test_execution_builder_and_validator(self):
        decision_report = DecisionReport(
            report_id="DEC_REP_001",
            risk_report_id="RISK_REP_001",
            candidate_decisions=[
                CandidateDecision(
                    candidate_id="SCALPING_1",
                    tradingsymbol="NIFTY26NOV24200CE",
                    strategy_name="SCALPING",
                    decision="BUY",
                    priority_score=0.85,
                    execution_priority=1,
                    explanation="Strong momentum",
                    allocated_lots=2,
                ),
                CandidateDecision(
                    candidate_id="SCALPING_2",
                    tradingsymbol="RELIANCE",
                    strategy_name="SCALPING",
                    decision="WATCH",
                    priority_score=0.45,
                    execution_priority=-1,
                    explanation="No trigger",
                    allocated_lots=0,
                )
            ]
        )

        req = ExecutionBuilder.build_execution_request(decision_report, lot_size=25)
        self.assertEqual(len(req.orders), 1)
        self.assertEqual(req.decision_report_id, "DEC_REP_001")
        
        order = req.orders[0]
        self.assertEqual(order.tradingsymbol, "NIFTY26NOV24200CE")
        self.assertEqual(order.exchange, "NFO")  # Deduced correctly as it's an option symbol
        self.assertEqual(order.quantity, 50)  # 2 lots * 25 lot_size

    @patch("src.broker.compat.connection.ConnectionManager.is_connected")
    def test_orders_manager_requires_manual_confirmation(self, mock_is_connected):
        mock_is_connected.return_value = True
        
        request = ExecutionRequest(
            request_id="REQ_100",
            decision_report_id="DEC_REP_001",
            orders=[
                ExecutionOrder(
                    candidate_id="CAND1",
                    tradingsymbol="NIFTY26NOV24200CE",
                    exchange="NFO",
                    transaction_type="BUY",
                    quantity=50,
                    product="NRML",
                    order_type="MARKET",
                    price=0.0,
                    trigger_price=0.0
                )
            ],
            timestamp="2026-11-09 10:00:00",
            status="PENDING"
        )

        # Calling without manual confirmation (confirmed=False)
        report = OrdersManager.execute_request(request, confirmed=False)
        self.assertEqual(report.status, "FAILED")
        self.assertIn("MANUAL_CONFIRMATION_REQUIRED", report.failure_reason)

    @patch("src.broker.compat.connection.ConnectionManager.is_connected")
    @patch("src.broker.compat.connection.ConnectionManager.get_client")
    @patch("src.broker.compat.funds.FundsManager.get_funds_info")
    def test_orders_manager_successful_placement_with_confirmation(
        self, mock_get_funds, mock_get_client, mock_is_connected
    ):
        mock_is_connected.return_value = True
        
        # Mock funds to pass pre-execution validation
        mock_get_funds.return_value = BrokerFunds(
            available_cash=50000.0,
            margins=50000.0,
            utilized_margin=0.0,
            available_margin=50000.0
        )
        
        # Mock broker place order call
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.place_order.return_value = "ZORD_ORD_77777"
        
        request = ExecutionRequest(
            request_id="REQ_100",
            decision_report_id="DEC_REP_001",
            orders=[
                ExecutionOrder(
                    candidate_id="CAND1",
                    tradingsymbol="NIFTY26NOV24200CE",
                    exchange="NFO",
                    transaction_type="BUY",
                    quantity=50,
                    product="NRML",
                    order_type="MARKET",
                    price=0.0,
                    trigger_price=0.0
                )
            ],
            timestamp="2026-11-09 10:00:00",
            status="PENDING"
        )

        # Call with manual operator confirmation
        report = OrdersManager.execute_request(request, confirmed=True)
        self.assertEqual(report.status, "COMPLETED")
        self.assertEqual(report.broker_order_id, "ZORD_ORD_77777")
        self.assertEqual(len(report.accepted_orders), 1)

    def test_broker_panel_to_dict_and_render(self):
        conn_status = {"connected": True}
        account = BrokerAccount(
            client_id="AB1234",
            name="Dev Operator",
            email="operator@terminal.local",
            broker="Zerodha"
        )
        funds = BrokerFunds(
            available_cash=100000.0,
            margins=120000.0,
            utilized_margin=20000.0,
            available_margin=100000.0
        )
        positions = [
            BrokerPosition(
                tradingsymbol="NIFTY26NOV24200CE",
                exchange="NFO",
                product="NRML",
                quantity=50,
                average_price=110.0,
                last_price=115.0,
                pnl=250.0,
                today_mtm=250.0
            )
        ]
        pending_orders = [
            BrokerOrder(
                order_id="ORD1001",
                exchange_order_id="",
                tradingsymbol="TCS",
                exchange="NSE",
                transaction_type="BUY",
                quantity=10,
                product="CNC",
                order_type="LIMIT",
                status="OPEN",
                price=3200.0,
                filled_quantity=0,
                order_timestamp="2026-11-09 10:00:00"
            )
        ]
        exec_status = ExecutionStatus(status="SUCCESS", message="Order placed cleanly")

        panel = BrokerPanel(
            connection_status=conn_status,
            funds=funds,
            positions=positions,
            pending_orders=pending_orders,
            execution_status=exec_status,
            account=account
        )

        dct = panel.to_dict()
        self.assertEqual(dct["connection"]["client_id"], "AB1234")
        self.assertEqual(dct["funds"]["available_margin"], 100000.0)
        self.assertEqual(dct["positions_summary"]["today_mtm"], 250.0)

        cli = panel.render_cli()
        self.assertIn("BROKER INTEGRATION PANEL", cli)
        self.assertIn("CONNECTED", cli)
        self.assertIn("AB1234", cli)
        self.assertIn("NIFTY26NOV24200CE", cli)
        self.assertIn("ORD1001", cli)
