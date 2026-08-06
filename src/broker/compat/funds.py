from __future__ import annotations

import logging
from typing import Dict, Any
from src.models.execution_report import BrokerFunds
from src.broker.compat.connection import ConnectionManager

logger = logging.getLogger("BrokerFunds")


class FundsManager:
    """
    Manages retrieving funds and margin details from Zerodha KiteConnect.
    """
    @staticmethod
    def get_funds_info() -> BrokerFunds:
        """
        Retrieves cash, margins, utilized margin, and available margin details.
        """
        try:
            client = ConnectionManager().get_client()
            margins = client.margins()
            
            if not margins:
                return BrokerFunds(0.0, 0.0, 0.0, 0.0)

            # KiteConnect margins returns nested structure with "equity" and "commodity"
            equity = margins.get("equity", {}) if "equity" in margins else margins
            
            # Extract fields safely, handling both nested structures and flat responses
            available_cash = 0.0
            utilized_margin = 0.0
            net_margin = 0.0
            
            if isinstance(equity, dict):
                # available field nested dict
                available_dict = equity.get("available", {})
                if isinstance(available_dict, dict):
                    available_cash = float(available_dict.get("cash", available_dict.get("live_balance", 0.0)))
                else:
                    available_cash = float(available_dict)
                    
                # utilised field nested dict
                utilised_dict = equity.get("utilised", {})
                if isinstance(utilised_dict, dict):
                    utilized_margin = float(utilised_dict.get("debits", utilised_dict.get("used", 0.0)))
                else:
                    utilized_margin = float(utilised_dict)
                    
                net_margin = float(equity.get("net", available_cash - utilized_margin))
            
            available_margin = max(0.0, net_margin - utilized_margin)
            
            return BrokerFunds(
                available_cash=available_cash,
                margins=net_margin,
                utilized_margin=utilized_margin,
                available_margin=available_margin
            )
        except Exception as e:
            logger.error(f"Error fetching broker funds info: {e}")
            return BrokerFunds(0.0, 0.0, 0.0, 0.0)
