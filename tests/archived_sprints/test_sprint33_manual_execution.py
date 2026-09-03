from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

from src.models import (
    ExecutionRequest,
    ExecutionOrder,
    ExecutionResult,
    ExecutionValidation,
    ExecutionConfirmation,
    ExecutionReceipt,
    ExecutionFailure,
    ExecutionAuditEntry,
    BrokerFunds,
)
from src.workspace import WorkspaceManager, WorkspaceMode
from src.broker.services.broker_service import BrokerService
from src.execution_engine.execution_validator import ExecutionValidator
from src.execution_engine.confirmation_manager import ConfirmationManager
from src.execution_engine.execution_manager import ExecutionManager


class TestSprint33ManualExecution(unittest.TestCase):
    """
    Unit test suite verifying the Manual Order Execution Engine (Sprint 33).
    Covers safety validations, operator confirmation states, immutable audit log
    trails, and full-path execution flow through BrokerService.
    """

    def setUp(self) -> None:
        # Clear states between tests
        ConfirmationManager.clear_all()
        ExecutionManager.clear_audit_log()
        ExecutionValidator.clear_recent_orders_cache()
        
        # Use a MagicMock for WorkspaceContext to avoid FrozenInstanceError
        self.mock_context = MagicMock()
        self.mock_context.current_mode = WorkspaceMode.LIVE_TRADING
        self.mock_context.broker_type = "ZERODHA"
        self.mock_context.authentication_status = "AUTHENTICATED"
        self.mock_context.market_status = "OPEN"
        self.mock_context.session_status = "ACTIVE"

        # Patch WorkspaceManager.get_context
        self.context_patcher = patch.object(WorkspaceManager, 'get_context', return_value=self.mock_context)
        self.mock_get_context = self.context_patcher.start()

        # Patch WorkspaceManager.current_mode property
        self.mode_patcher = patch.object(WorkspaceManager, 'current_mode', new_callable=PropertyMock)
        self.mock_current_mode = self.mode_patcher.start()
        self.mock_current_mode.side_effect = lambda: self.mock_context.current_mode

        # Build sufficient mock funds
        self.funds_mock = BrokerFunds(
            available_cash=10000000.0,
            margins=10000000.0,
            utilized_margin=0.0,
            available_margin=10000000.0
        )

        # Mock the active gateway adapter of the singleton instance
        self.broker_instance = BrokerService.get_instance()
        self.original_gateway = getattr(self.broker_instance, '_gateway', None)
        
        self.mock_gateway = MagicMock()
        self.mock_gateway.is_connected.return_value = True
        self.mock_gateway.validate_session.return_value = True
        self.mock_gateway.get_funds.return_value = self.funds_mock
        self.mock_gateway.place_order.return_value = "ORD_MOCK_12345"
        
        self.broker_instance._gateway = self.mock_gateway

    def tearDown(self) -> None:
        self.context_patcher.stop()
        self.mode_patcher.stop()
        # Restore original gateway
        if self.original_gateway is not None:
            self.broker_instance._gateway = self.original_gateway

    def test_execution_validator_live_vs_paper_modes(self) -> None:
        """
        Verify validation fails if workspace mode is not LIVE_TRADING (unless bypassed).
        """
        request = ExecutionRequest(
            request_id="REQ_100",
            decision_report_id="DEC_100",
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            orders=[
                ExecutionOrder(
                    candidate_id="C_1",
                    tradingsymbol="NIFTY26JUL24200CE",
                    exchange="NFO",
                    transaction_type="BUY",
                    quantity=500,
                    product="NRML",
                    order_type="MARKET",
                    price=0.0,
                    trigger_price=0.0
                )
            ]
        )

        # 1. Active LIVE_TRADING should pass
        self.mock_context.current_mode = WorkspaceMode.LIVE_TRADING
        ExecutionValidator.clear_recent_orders_cache()
        val_live = ExecutionValidator.validate_request(request)
        self.assertTrue(val_live.is_valid)
        self.assertEqual(len(val_live.errors), 0)

        # 2. Active LIVE_PRACTICE should fail by default due to safety violation
        self.mock_context.current_mode = WorkspaceMode.LIVE_PRACTICE
        ExecutionValidator.clear_recent_orders_cache()
        val_paper = ExecutionValidator.validate_request(request)
        self.assertFalse(val_paper.is_valid)
        self.assertTrue(any("Workspace Mode violation" in err for err in val_paper.errors))

        # 3. LIVE_PRACTICE with bypass safety flag should pass
        ExecutionValidator.clear_recent_orders_cache()
        val_bypassed = ExecutionValidator.validate_request(request, bypass_safety=True)
        self.assertTrue(val_bypassed.is_valid)

    def test_execution_validator_safeguard_limits(self) -> None:
        """
        Verify validation limits on single-order quantity and capital size.
        """
        self.mock_context.current_mode = WorkspaceMode.LIVE_TRADING

        # 1. Exceed single-order quantity limit (>50,000 as configured in validator)
        invalid_qty_order = ExecutionRequest(
            request_id="REQ_QTY",
            decision_report_id="DEC_QTY",
            timestamp="10:00:00",
            orders=[
                ExecutionOrder(
                    candidate_id="C_QTY",
                    tradingsymbol="NIFTY26JUL24200CE",
                    exchange="NFO",
                    transaction_type="BUY",
                    quantity=60000, # MAX limit 50,000
                    product="NRML",
                    order_type="MARKET",
                    price=0.0,
                    trigger_price=0.0
                )
            ]
        )
        ExecutionValidator.clear_recent_orders_cache()
        val_qty = ExecutionValidator.validate_request(invalid_qty_order)
        self.assertFalse(val_qty.is_valid)
        self.assertTrue(any("exceeds maximum allowed limit" in err for err in val_qty.errors))

        # 2. Exceed capital utilization limit (>10,000,000 INR)
        invalid_capital_order = ExecutionRequest(
            request_id="REQ_CAP",
            decision_report_id="DEC_CAP",
            timestamp="10:00:00",
            orders=[
                ExecutionOrder(
                    candidate_id="C_CAP",
                    tradingsymbol="NIFTY26JUL24200CE",
                    exchange="NFO",
                    transaction_type="BUY",
                    quantity=30000,
                    product="NRML",
                    order_type="LIMIT",
                    price=500.0, # 30000 * 500 = 15,000,000 (exceeds 10,000,000 limit)
                    trigger_price=0.0
                )
            ]
        )
        ExecutionValidator.clear_recent_orders_cache()
        val_cap = ExecutionValidator.validate_request(invalid_capital_order)
        self.assertFalse(val_cap.is_valid)
        self.assertTrue(any("estimated cost" in err.lower() or "limit" in err.lower() for err in val_cap.errors))

        # 3. Try to place frozen symbol order
        frozen_symbol_order = ExecutionRequest(
            request_id="REQ_FRZ",
            decision_report_id="DEC_FRZ",
            timestamp="10:00:00",
            orders=[
                ExecutionOrder(
                    candidate_id="C_FRZ",
                    tradingsymbol="SUSPENDED", # matches in FROZEN_INSTRUMENTS list
                    exchange="NFO",
                    transaction_type="BUY",
                    quantity=100,
                    product="NRML",
                    order_type="MARKET",
                    price=0.0,
                    trigger_price=0.0
                )
            ]
        )
        ExecutionValidator.clear_recent_orders_cache()
        val_frz = ExecutionValidator.validate_request(frozen_symbol_order)
        self.assertFalse(val_frz.is_valid)
        self.assertTrue(any("frozen/suspended" in err.lower() for err in val_frz.errors))

    def test_manual_confirmation_layer(self) -> None:
        """
        Verify ConfirmationManager correctly tracks pending states, approves confirmations,
        identifies operators, and blocks duplicate processed states.
        """
        request = ExecutionRequest(
            request_id="REQ_200",
            decision_report_id="DEC_200",
            timestamp="10:00:00",
            orders=[
                ExecutionOrder(
                    candidate_id="C_200",
                    tradingsymbol="NIFTY26JUL24200CE",
                    exchange="NFO",
                    transaction_type="BUY",
                    quantity=500,
                    product="NRML",
                    order_type="MARKET",
                    price=0.0,
                    trigger_price=0.0
                )
            ]
        )

        # Register request
        ConfirmationManager.register_request(request)
        
        # Verify it is in pending list
        self.assertEqual(len(ConfirmationManager.get_pending_requests()), 1)
        self.assertEqual(ConfirmationManager.get_pending_request("REQ_200"), request)

        # Confirm order with operator email
        conf = ConfirmationManager.confirm_request("REQ_200", operator_name="pvpk06@gmail.com")
        self.assertEqual(conf.status, "CONFIRMED")
        self.assertEqual(conf.confirmed_by, "pvpk06@gmail.com")

        # Verify it is removed from pending
        self.assertEqual(len(ConfirmationManager.get_pending_requests()), 0)

        # Assert duplicate confirmations are blocked (return None)
        conf_dup = ConfirmationManager.confirm_request("REQ_200", operator_name="pvpk06@gmail.com")
        self.assertIsNone(conf_dup)

        # Test cancel rejection path
        request_cancel = ExecutionRequest(
            request_id="REQ_CANCEL_ME",
            decision_report_id="DEC_CANCEL_ME",
            timestamp="10:00:00",
            orders=[
                ExecutionOrder(
                    candidate_id="C_CAN",
                    tradingsymbol="NIFTY26JUL24150PE",
                    exchange="NFO",
                    transaction_type="SELL",
                    quantity=100,
                    product="NRML",
                    order_type="MARKET",
                    price=0.0,
                    trigger_price=0.0
                )
            ]
        )
        ConfirmationManager.register_request(request_cancel)
        conf_cancel = ConfirmationManager.cancel_request("REQ_CANCEL_ME", operator_name="pvpk06@gmail.com")
        self.assertEqual(conf_cancel.status, "CANCELLED")
        self.assertEqual(len(ConfirmationManager.get_pending_requests()), 0)

    def test_execution_manager_full_path_is_rejected(self) -> None:
        """
        Verify end-to-end processing of a validated, operator-confirmed order.
        """
        request = ExecutionRequest(
            request_id="REQ_SUCCESS",
            decision_report_id="DEC_SUCCESS",
            timestamp="10:00:00",
            orders=[
                ExecutionOrder(
                    candidate_id="C_SUC_1",
                    tradingsymbol="NIFTY26JUL24200CE",
                    exchange="NFO",
                    transaction_type="BUY",
                    quantity=500,
                    product="NRML",
                    order_type="MARKET",
                    price=0.0,
                    trigger_price=0.0
                )
            ]
        )

        # 1. Validation and submission
        ExecutionValidator.clear_recent_orders_cache()
        val = ExecutionManager.submit_for_validation_and_confirmation(request)
        self.assertFalse(val.is_valid)
        self.assertIn("READ_ONLY_PRODUCT", val.errors[0])
        self.assertEqual(len(ConfirmationManager.get_pending_requests()), 0)

        # Clear duplicate cache right before execution to pass late-stage pre-execution validation
        ExecutionValidator.clear_recent_orders_cache()

        # 2. Explicit operator confirm triggers actual execution
        result = ExecutionManager.execute_confirmed_request("REQ_SUCCESS", operator="pvpk06@gmail.com")
        
        # The isolated legacy manager cannot cross the read-only broker boundary.
        self.mock_gateway.place_order.assert_not_called()
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(len(result.receipts), 0)
        self.assertEqual(len(result.failures), 1)

        # 3. Check Immutable Audit log records
        audit_trail = ExecutionManager.get_audit_log()
        self.assertEqual(len(audit_trail), 1)
        
        self.assertEqual(audit_trail[0].execution_outcome, "VALIDATION_FAILED")

    def test_execution_manager_cancel_path(self) -> None:
        """
        Verify execution logic when operator decides to cancel the order.
        """
        request = ExecutionRequest(
            request_id="REQ_CANCELLED",
            decision_report_id="DEC_CANCELLED",
            timestamp="10:00:00",
            orders=[
                ExecutionOrder(
                    candidate_id="C_CANCELLED_1",
                    tradingsymbol="NIFTY26JUL24200CE",
                    exchange="NFO",
                    transaction_type="BUY",
                    quantity=500,
                    product="NRML",
                    order_type="MARKET",
                    price=0.0,
                    trigger_price=0.0
                )
            ]
        )

        # Submit
        ExecutionValidator.clear_recent_orders_cache()
        val = ExecutionManager.submit_for_validation_and_confirmation(request)
        self.assertFalse(val.is_valid)
        self.assertIn("READ_ONLY_PRODUCT", val.errors[0])

        # Execute
        result = ExecutionManager.execute_confirmed_request("REQ_CANCELLED", operator="pvpk06@gmail.com")
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(len(result.receipts), 0)
        self.assertTrue(any("READ_ONLY_PRODUCT" in f.error_message for f in result.failures))


if __name__ == "__main__":
    unittest.main()
